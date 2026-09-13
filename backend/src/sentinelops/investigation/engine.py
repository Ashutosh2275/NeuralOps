"""
Autonomous Investigation Engine orchestrator for SentinelOps AI.
Coordinates tool calling, dynamic planning, evidence correlation, deterministic RCA,
operational RAG retrieval, and AI enrichment into grounded root cause analysis.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.core.logging import get_logger
from sentinelops.engines.rca import RCAEngine
from sentinelops.events.schemas import BaseEvent, EventType, PodEvent, Severity
from sentinelops.investigation.correlator import EvidenceCorrelator
from sentinelops.investigation.planner import InvestigationPlanner
from sentinelops.investigation.state import (
    EvidenceItem,
    EvidenceType,
    HypothesisStatus,
    InvestigationState,
)
from sentinelops.tools import register_default_tools
from sentinelops.tools.registry import ToolRegistry, get_tool_registry

log = get_logger(__name__)


class InvestigationEngine:
    """End-to-end multi-step autonomous incident investigation engine."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        ollama_client: OllamaClient | None = None,
        rca_engine: RCAEngine | None = None,
    ) -> None:
        self.registry = registry or get_tool_registry()
        register_default_tools(self.registry)

        self.planner = InvestigationPlanner(self.registry)
        self.correlator = EvidenceCorrelator()
        self.ollama = ollama_client or OllamaClient()
        self.rca_engine = rca_engine or RCAEngine()

        # In-memory store for investigation records
        self._investigations: dict[str, InvestigationState] = {}

    def get_investigation(self, investigation_id: str) -> Optional[InvestigationState]:
        if investigation_id in self._investigations:
            return self._investigations[investigation_id]

        # Check disk persistence
        try:
            from pathlib import Path
            import json
            snap_path = Path("data/investigations") / f"{investigation_id}.json"
            if snap_path.exists():
                data = json.loads(snap_path.read_text(encoding="utf-8"))
                state = InvestigationState.from_dict(data)
                self._investigations[investigation_id] = state
                return state
        except Exception as e:
            log.warning("investigation_restore_failed", id=investigation_id, error=str(e))
        return None

    def list_investigations(self, limit: int = 50) -> list[InvestigationState]:
        # Sync disk investigations if directory exists
        try:
            from pathlib import Path
            import json
            dump_dir = Path("data/investigations")
            if dump_dir.exists():
                for snap_file in dump_dir.glob("*.json"):
                    inv_id = snap_file.stem
                    if inv_id not in self._investigations:
                        try:
                            data = json.loads(snap_file.read_text(encoding="utf-8"))
                            self._investigations[inv_id] = InvestigationState.from_dict(data)
                        except Exception:
                            pass
        except Exception as e:
            log.warning("list_investigations_disk_sync_failed", error=str(e))

        return sorted(
            self._investigations.values(),
            key=lambda x: x.created_at,
            reverse=True,
        )[:limit]

    async def investigate(
        self,
        incident_id: Optional[str] = None,
        target_service: Optional[str] = None,
        target_pod: Optional[str] = None,
        namespace: str = "default",
        trigger_reason: str = "Incident trigger",
        max_steps: int = 8,
    ) -> InvestigationState:
        """Runs an autonomous multi-step investigation loop."""
        state = InvestigationState(
            incident_id=incident_id,
            target_service=target_service,
            target_pod=target_pod,
            namespace=namespace,
            initial_trigger=trigger_reason,
            max_steps=max_steps,
        )
        self._investigations[state.investigation_id] = state

        log.info(
            "investigation_started",
            investigation_id=state.investigation_id,
            service=target_service,
            pod=target_pod,
            namespace=namespace,
        )

        # 1. Autonomous tool calling loop
        while state.step_count < state.max_steps:
            next_step = await self.planner.plan_next_step_autonomous(state, llm=self.ollama)
            if not next_step:
                break

            state.step_count += 1
            record = await self.registry.execute(next_step.tool_name, next_step.arguments)
            state.record_tool_call(record)

            # Ingest result into evidence collection
            if record.result and record.result.success:
                ev_item = self._create_evidence_from_result(record.tool_name, record.result.data)
                if ev_item:
                    state.add_evidence(ev_item)

        # 2. Evidence Correlation & Hypotheses evaluation
        hypotheses = self.correlator.correlate(state)
        confidence = self.correlator.compute_composite_confidence(state)
        state.confidence = confidence

        # 3. Deterministic RCA execution
        deterministic_events = self._synthesize_events_for_rca(state)
        rca_res = self.rca_engine.analyze(deterministic_events)

        # 4. Extract topology, RAG, and evidence IDs
        affected_svcs: set[str] = set()
        prop_path: list[str] = []
        rag_srcs: list[dict[str, Any]] = []

        for e in state.evidence:
            if e.evidence_type == EvidenceType.TOPOLOGY_IMPACT and isinstance(e.raw_data, dict):
                for svc in e.raw_data.get("affected_services", []):
                    affected_svcs.add(svc)
                for svc in e.raw_data.get("cascade_path", []):
                    if svc not in prop_path:
                        prop_path.append(svc)
            elif e.evidence_type == EvidenceType.RUNBOOK_KNOWLEDGE and isinstance(e.raw_data, dict):
                rag_srcs.append({
                    "query": e.raw_data.get("query"),
                    "citations": e.raw_data.get("citations", []),
                    "chunk_count": e.raw_data.get("chunk_count", 0),
                })

        state.affected_services = sorted(affected_svcs)
        state.propagation_path = prop_path
        state.rag_sources = rag_srcs

        # 5. Synthesize Final Root Cause & Deterministic Cross-Check
        confirmed_hypotheses = [h for h in hypotheses if h.status == HypothesisStatus.CONFIRMED]
        supporting_ids: list[str] = []
        contradicting_ids: list[str] = []

        for h in hypotheses:
            if h.status == HypothesisStatus.CONFIRMED:
                supporting_ids.extend(h.supporting_evidence_ids)
            elif h.status == HypothesisStatus.REFUTED:
                contradicting_ids.extend(h.refuting_evidence_ids)

        state.supporting_evidence_ids = list(dict.fromkeys(supporting_ids))
        state.contradicting_evidence_ids = list(dict.fromkeys(contradicting_ids))

        if confirmed_hypotheses:
            top_hypothesis = confirmed_hypotheses[0]
            root_cause_text = f"{top_hypothesis.description}. {top_hypothesis.reasoning}"
        elif rca_res.root_cause:
            root_cause_text = rca_res.root_cause
        else:
            root_cause_text = f"Degradation detected on {target_service or target_pod or namespace}: {trigger_reason}"

        # Deterministic RCA Cross-Check:
        # If deterministic RCA indicates a specific failure mode (e.g. OOM or CrashLoop)
        # while hypothesis/LLM claims something contradictory (e.g. network latency),
        # flag the conflict and let deterministic telemetry take precedence.
        if rca_res.root_cause and confirmed_hypotheses:
            det_rca_lower = rca_res.root_cause.lower()
            hyp_desc_lower = top_hypothesis.description.lower()
            conflict = False
            if ("oom" in det_rca_lower or "137" in det_rca_lower) and ("network" in hyp_desc_lower or "timeout" in hyp_desc_lower):
                conflict = True
            elif ("crash" in det_rca_lower or "backoff" in det_rca_lower) and ("network" in hyp_desc_lower):
                conflict = True

            if conflict:
                warning_msg = (
                    f"Deterministic RCA cross-check conflict: Deterministic engine identified '{rca_res.root_cause}' "
                    f"which contradicts hypothesis '{top_hypothesis.description}'. Telemetry ground truth takes precedence."
                )
                state.warnings.append(warning_msg)
                root_cause_text = f"{rca_res.root_cause}. (Deterministic cross-check prioritized over conflicting inference)"
                state.confidence = max(0.2, state.confidence - 0.25)

        state.final_root_cause = root_cause_text

        # 6. Epistemic Classification (FACT / INFERENCE / UNCERTAINTY)
        facts = [
            e.summary for e in state.evidence
            if e.evidence_type in (EvidenceType.K8S_STATUS, EvidenceType.POD_LOGS, EvidenceType.METRIC_ANOMALY, EvidenceType.K8S_EVENT)
        ]
        inferences = [
            f"{h.description}: {h.reasoning}" for h in confirmed_hypotheses
        ]
        uncertainties = list(state.warnings)
        if not confirmed_hypotheses:
            uncertainties.append("No definitive hypothesis confirmed; operational state requires further telemetry.")

        state.epistemic_breakdown = {
            "facts": facts,
            "inferences": inferences,
            "uncertainties": uncertainties,
        }

        # Extract recommendations from runbook citations and deterministic knowledge
        recommendations = []
        citations_list = []
        for e in state.evidence:
            if e.evidence_type == EvidenceType.RUNBOOK_KNOWLEDGE and isinstance(e.raw_data, dict):
                cits = e.raw_data.get("citations", [])
                for c in cits:
                    citations_list.append(c)
                ctx = e.raw_data.get("context_text", "")
                if "Immediate Actions:" in ctx or "Remediation" in ctx:
                    # Extract high level recommendation
                    lines = [line.strip("- *# ") for line in ctx.split("\n") if line.strip().startswith(("-", "*", "1.", "2."))]
                    recommendations.extend(lines[:3])

        # Domain-grounded recommendations
        if "pvc" in root_cause_text.lower() or "volume" in root_cause_text.lower() or "storage" in root_cause_text.lower() or "pvc" in state.initial_trigger.lower():
            recommendations.append("Expand Persistent Volume Claim capacity via storageClass volumeBindingMode")
            recommendations.append("Purge rotated log archives and temporary cache files from PVC storage")
        elif "oom" in root_cause_text.lower() or "memory" in root_cause_text.lower() or "oom" in state.initial_trigger.lower() or "137" in state.initial_trigger:
            recommendations.append(f"Increase memory limits for container in {target_pod or target_service}")
            recommendations.append("Inspect application heap profiling for memory leaks")
        elif "crash" in root_cause_text.lower():
            recommendations.append("Inspect recent git commit or container image tag changes")
            recommendations.append("Verify database connection credentials and environment variables")

        if not recommendations:
            recommendations.extend([
                f"Inspect logs and events for {target_service or target_pod}",
                "Review dependency service latencies and network connectivity",
                "Validate deployment rollout history and rollback if necessary",
            ])

        state.final_recommendations = recommendations[:5]
        state.citations = citations_list
        state.status = "completed"
        state.completed_at = datetime.now(timezone.utc)
        self._persist_snapshot(state)

        log.info(
            "investigation_completed",
            investigation_id=state.investigation_id,
            evidence_count=len(state.evidence),
            confidence=state.confidence,
        )

        return state

    def _persist_snapshot(self, state: InvestigationState) -> None:
        """Persists completed investigation state to disk snapshot."""
        try:
            from pathlib import Path
            import json
            dump_dir = Path("data/investigations")
            dump_dir.mkdir(parents=True, exist_ok=True)
            snapshot_path = dump_dir / f"{state.investigation_id}.json"
            snapshot_path.write_text(json.dumps(state.to_dict(), indent=2, default=str), encoding="utf-8")
            log.debug("investigation_snapshot_saved", path=str(snapshot_path))
        except Exception as e:
            log.warning("investigation_snapshot_save_failed", error=str(e))

    def _create_evidence_from_result(self, tool_name: str, data: Any) -> Optional[EvidenceItem]:
        """Maps tool output into structured EvidenceItem."""
        if not data:
            return None

        if tool_name == "get_pod_status":
            pod_name = data.get("name", "pod")
            phase = data.get("phase", "Unknown")
            restarts = data.get("restart_count", 0)
            reason = data.get("reason", "None")
            return EvidenceItem(
                evidence_type=EvidenceType.K8S_STATUS,
                source_tool=tool_name,
                summary=f"Pod {pod_name} is in phase '{phase}' with {restarts} restarts (Reason: {reason})",
                raw_data=data,
                confidence_contribution=0.25,
            )

        if tool_name in ("get_pod_details", "get_container_status", "get_workload_health", "get_deployment_status"):
            return EvidenceItem(
                evidence_type=EvidenceType.K8S_STATUS,
                source_tool=tool_name,
                summary=f"K8s inspection via {tool_name}: status={data.get('status', data.get('phase', 'Collected'))}",
                raw_data=data,
                confidence_contribution=0.20,
            )

        if tool_name == "get_pod_logs":
            logs = data.get("logs", "")
            return EvidenceItem(
                evidence_type=EvidenceType.POD_LOGS,
                source_tool=tool_name,
                summary=f"Extracted tail logs for {data.get('pod_name')}: {len(logs)} characters",
                raw_data=data,
                confidence_contribution=0.20,
            )

        if tool_name == "get_k8s_events":
            events = data.get("events", [])
            return EvidenceItem(
                evidence_type=EvidenceType.K8S_EVENT,
                source_tool=tool_name,
                summary=f"Discovered {len(events)} warning/error events in namespace",
                raw_data=data,
                confidence_contribution=0.15,
            )

        if tool_name in ("query_prometheus_metric", "get_resource_usage"):
            metrics = data.get("metrics", [])
            breached = [m for m in metrics if m.get("breached")]
            return EvidenceItem(
                evidence_type=EvidenceType.METRIC_ANOMALY,
                source_tool=tool_name,
                summary=f"Metrics returned ({len(breached)} breached threshold)",
                raw_data=data,
                confidence_contribution=0.20,
            )

        if tool_name == "query_loki_logs":
            logs = data.get("logs", [])
            return EvidenceItem(
                evidence_type=EvidenceType.POD_LOGS,
                source_tool=tool_name,
                summary=f"Loki log query returned {len(logs)} matched log entries",
                raw_data=data,
                confidence_contribution=0.15,
            )

        if tool_name in ("get_service_dependencies", "calculate_blast_radius", "get_namespace_resources", "get_service_details"):
            return EvidenceItem(
                evidence_type=EvidenceType.TOPOLOGY_IMPACT,
                source_tool=tool_name,
                summary=f"Topology and service architecture mapped via {tool_name}",
                raw_data=data,
                confidence_contribution=0.15,
            )

        if tool_name == "search_operational_knowledge":
            cits = data.get("citations", [])
            return EvidenceItem(
                evidence_type=EvidenceType.RUNBOOK_KNOWLEDGE,
                source_tool=tool_name,
                summary=f"RAG retrieved {len(cits)} runbook sections matching symptoms",
                raw_data=data,
                confidence_contribution=0.15,
            )

        if tool_name == "search_past_incidents":
            incs = data.get("incidents", [])
            return EvidenceItem(
                evidence_type=EvidenceType.HISTORICAL_INCIDENT,
                source_tool=tool_name,
                summary=f"Found {len(incs)} historical incidents for service",
                raw_data=data,
                confidence_contribution=0.10,
            )

        return None

    def _synthesize_events_for_rca(self, state: InvestigationState) -> list[BaseEvent]:
        """Translates gathered evidence into BaseEvents for RCAEngine."""
        events: list[BaseEvent] = []
        for e in state.evidence:
            if e.evidence_type == EvidenceType.K8S_STATUS and isinstance(e.raw_data, dict):
                events.append(
                    PodEvent(
                        event_id=uuid4(),
                        source=e.source_tool,
                        cluster_id="default",
                        namespace=state.namespace,
                        severity=Severity.CRITICAL if e.raw_data.get("restart_count", 0) > 0 else Severity.INFO,
                        payload=e.raw_data,
                    )
                )
            elif e.evidence_type == EvidenceType.METRIC_ANOMALY and isinstance(e.raw_data, dict):
                for m in e.raw_data.get("metrics", [])[:3]:
                    events.append(
                        BaseEvent(
                            event_id=uuid4(),
                            event_type=EventType.METRIC,
                            source=e.source_tool,
                            cluster_id="default",
                            namespace=state.namespace,
                            severity=Severity.WARNING if m.get("breached") else Severity.INFO,
                            payload=m,
                        )
                    )
        return events


# Global singleton
_global_engine: Optional[InvestigationEngine] = None


def get_investigation_engine() -> InvestigationEngine:
    """Retrieve or initialize global InvestigationEngine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = InvestigationEngine()
    return _global_engine
