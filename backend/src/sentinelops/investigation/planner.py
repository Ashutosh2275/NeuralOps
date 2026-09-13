"""
Autonomous Investigation Planner for SentinelOps AI.
Generates an evidence-seeking plan, dynamically updates next steps based on findings,
and strictly enforces duplicate prevention and maximum call boundaries.
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any, List, Optional

from sentinelops.core.logging import get_logger
from sentinelops.investigation.state import (
    EvidenceType,
    InvestigationPlanStep,
    InvestigationState,
)
from sentinelops.tools.registry import ToolRegistry

log = get_logger(__name__)


class InvestigationPlanner:
    """Plans tool call sequences dynamically to investigate incidents."""

    _llm_offline: bool = False

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def plan_next_step(self, state: InvestigationState) -> Optional[InvestigationPlanStep]:
        """Determines the next best tool call using priority heuristics (synchronous)."""
        return self.plan_next_step_heuristic(state)

    async def plan_next_step_autonomous(
        self,
        state: InvestigationState,
        llm: Optional[Any] = None,
    ) -> Optional[InvestigationPlanStep]:
        """
        Determines the next best tool call.
        If an LLM client is available and responsive, queries the LLM dynamically
        with available tool definitions and gathered evidence history.
        Gracefully falls back to deterministic heuristic planning if LLM is offline or invalid.
        """
        if state.step_count >= state.max_steps:
            log.info("investigation_max_steps_reached", investigation_id=state.investigation_id, steps=state.step_count)
            return None

        if llm is not None and not InvestigationPlanner._llm_offline:
            try:
                llm_step = await self._plan_with_llm(state, llm)
                if llm_step is not None:
                    return llm_step
            except Exception as e:
                InvestigationPlanner._llm_offline = True
                log.warning("llm_planner_fallback", investigation_id=state.investigation_id, error=str(e))

        return self.plan_next_step_heuristic(state)

    async def _plan_with_llm(self, state: InvestigationState, llm: Any) -> Optional[InvestigationPlanStep]:
        """Asks the LLM to inspect evidence and select the next tool to run."""
        tools_def = self._registry.get_tool_definitions_for_llm()
        tool_names = [t["function"]["name"] for t in tools_def]


        evidence_lines = [
            f"- [{e.evidence_type.value}] ({e.source_tool}): {e.summary}"
            for e in state.evidence
        ]
        history_lines = [
            f"- {call.tool_name}({call.arguments})"
            for call in state.tool_history
        ]

        prompt = (
            "You are an autonomous SRE investigation engine for Kubernetes.\n"
            "Analyze the incident trigger, current evidence, and previously executed tools.\n"
            "Select the next safe read-only tool to execute from the list of available tools.\n\n"
            f"Incident Trigger: {state.initial_trigger}\n"
            f"Target Service: {state.target_service or 'Unknown'}\n"
            f"Target Pod: {state.target_pod or 'Unknown'}\n"
            f"Namespace: {state.namespace}\n\n"
            f"Available Tool Names: {tool_names}\n\n"
            "Previously Executed Tools:\n"
            + ("\n".join(history_lines) if history_lines else "None") + "\n\n"
            "Gathered Evidence:\n"
            + ("\n".join(evidence_lines) if evidence_lines else "None") + "\n\n"
            "Rules:\n"
            "1. If you have enough evidence to diagnose the incident, or no further tools are useful, respond with:\n"
            '{"decision": "finish", "rationale": "Root cause identified"}\n'
            "2. Otherwise, select ONE tool from the available tools list.\n"
            "3. DO NOT repeat an identical tool call already listed in Previously Executed Tools.\n"
            "4. Respond strictly with a JSON object in this exact format, with no preamble or codeblocks:\n"
            '{"decision": "call_tool", "tool_name": "<name>", "arguments": {<args>}, "rationale": "<reason>"}'
        )

        try:
            raw_resp = await asyncio.wait_for(llm.generate(prompt), timeout=15.0)
            if isinstance(raw_resp, tuple):
                resp = raw_resp[0]
            else:
                resp = str(raw_resp)
        except Exception:
            InvestigationPlanner._llm_offline = True
            return None

        if not resp or "[ai unavailable]" in resp.lower():
            InvestigationPlanner._llm_offline = True
            return None



        # Extract JSON substring
        json_match = re.search(r"\{.*\}", resp, re.DOTALL)
        if not json_match:
            return None

        data = json.loads(json_match.group(0))
        decision = data.get("decision")
        if decision == "finish":
            log.info("llm_planner_decided_finish", investigation_id=state.investigation_id)
            return None

        tool_name = data.get("tool_name")
        args = data.get("arguments", {})
        rationale = data.get("rationale", f"Autonomous tool execution via LLM: {tool_name}")

        if not tool_name or tool_name not in self._registry._tools:
            log.debug("llm_planner_unknown_tool", tool_name=tool_name)
            return None

        # Verify tool parameters
        tool = self._registry.get(tool_name)
        if tool:
            for req in tool.metadata.required_params:
                if req not in args:
                    # Provide sensible default if missing
                    if req == "namespace":
                        args["namespace"] = state.namespace
                    elif req in ("pod_name", "target_pod") and state.target_pod:
                        args[req] = state.target_pod
                    elif req in ("service_name", "target_service") and state.target_service:
                        args[req] = state.target_service
                    else:
                        return None

        if state.has_called(tool_name, args):
            log.debug("llm_planner_duplicate_prevented", tool_name=tool_name)
            return None

        return InvestigationPlanStep(
            step_num=state.step_count + 1,
            tool_name=tool_name,
            arguments=args,
            rationale=rationale,
            source="llm_planner",
        )

    def plan_next_step_heuristic(self, state: InvestigationState) -> Optional[InvestigationPlanStep]:
        """Determines the next best tool call using priority heuristics."""
        if state.step_count >= state.max_steps:
            log.info("investigation_max_steps_reached", investigation_id=state.investigation_id, steps=state.step_count)
            return None

        gathered_types = {e.evidence_type for e in state.evidence}
        target_pod = state.target_pod
        target_service = state.target_service or (target_pod.split("-")[0] if target_pod else None)
        ns = state.namespace

        # Priority 1: If target pod known, get pod status first
        if target_pod and EvidenceType.K8S_STATUS not in gathered_types:
            args = {"namespace": ns, "pod_name": target_pod}
            if not state.has_called("get_pod_status", args):
                return InvestigationPlanStep(
                    step_num=state.step_count + 1,
                    tool_name="get_pod_status",
                    arguments=args,
                    rationale=f"Inspect pod status and restart count for {target_pod}",
                    source="heuristic_planner",
                )

        # Priority 2: Check K8s warning events
        if EvidenceType.K8S_EVENT not in gathered_types:
            args = {"namespace": ns, "limit": 10}
            if not state.has_called("get_k8s_events", args):
                return InvestigationPlanStep(
                    step_num=state.step_count + 1,
                    tool_name="get_k8s_events",
                    arguments=args,
                    rationale=f"Check recent warning and error events in namespace {ns}",
                    source="heuristic_planner",
                )

        # Priority 3: If target pod exists, retrieve pod logs
        if target_pod and EvidenceType.POD_LOGS not in gathered_types:
            args = {"namespace": ns, "pod_name": target_pod, "tail_lines": 50}
            if not state.has_called("get_pod_logs", args):
                return InvestigationPlanStep(
                    step_num=state.step_count + 1,
                    tool_name="get_pod_logs",
                    arguments=args,
                    rationale=f"Retrieve tail container logs for {target_pod}",
                    source="heuristic_planner",
                )

        # Priority 4: Query Prometheus metrics for resource saturation
        if EvidenceType.METRIC_ANOMALY not in gathered_types:
            metric_to_query = "memory_percent"
            trigger_lower = state.initial_trigger.lower()
            if "pvc" in trigger_lower or "disk" in trigger_lower or "storage" in trigger_lower:
                metric_to_query = "pvc_usage_percent"
            elif "cpu" in trigger_lower:
                metric_to_query = "cpu_percent"

            args = {"namespace": ns, "metric_name": metric_to_query}
            if target_pod:
                args["target_resource"] = target_pod
            if not state.has_called("query_prometheus_metric", args):
                return InvestigationPlanStep(
                    step_num=state.step_count + 1,
                    tool_name="query_prometheus_metric",
                    arguments=args,
                    rationale=f"Inspect {metric_to_query} metrics for saturation triggers",
                    source="heuristic_planner",
                )

        # Priority 5: Check topology and blast radius
        if target_service and EvidenceType.TOPOLOGY_IMPACT not in gathered_types:
            args = {"namespace": ns, "service_name": target_service}
            if not state.has_called("get_service_dependencies", args):
                return InvestigationPlanStep(
                    step_num=state.step_count + 1,
                    tool_name="get_service_dependencies",
                    arguments=args,
                    rationale=f"Inspect upstream and downstream dependencies for service {target_service}",
                    source="heuristic_planner",
                )

        # Priority 6: Query operational runbooks / knowledge base (RAG)
        if EvidenceType.RUNBOOK_KNOWLEDGE not in gathered_types:
            query = f"{target_service or target_pod or 'Kubernetes'} {state.initial_trigger}"
            args = {"query": query, "top_k": 2}
            if not state.has_called("search_operational_knowledge", args):
                return InvestigationPlanStep(
                    step_num=state.step_count + 1,
                    tool_name="search_operational_knowledge",
                    arguments=args,
                    rationale="Retrieve operational runbooks and recommended remediation procedures",
                    source="heuristic_planner",
                )

        # Priority 7: Search historical incidents
        if target_service and EvidenceType.HISTORICAL_INCIDENT not in gathered_types:
            args = {"service_name": target_service, "namespace": ns, "limit": 3}
            if not state.has_called("search_past_incidents", args):
                return InvestigationPlanStep(
                    step_num=state.step_count + 1,
                    tool_name="search_past_incidents",
                    arguments=args,
                    rationale=f"Check for past recurring incidents on service {target_service}",
                    source="heuristic_planner",
                )

        # All key avenues explored
        log.info("investigation_plan_exhausted", investigation_id=state.investigation_id, steps=state.step_count)
        return None

