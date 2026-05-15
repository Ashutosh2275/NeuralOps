import json
import re
from typing import Any

from sentinelops.ai.base import AIAgent, AIAgentContext, AIAgentResult
from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger

log = get_logger(__name__)


class CPUAgent(AIAgent):
    """Analyzes CPU anomalies and resource contention."""

    agent_type = "cpu"
    description = "CPU Anomaly Analysis Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        threshold = get_settings().anomaly_cpu_threshold_percent
        cpu_events = [
            e for e in context.events
            if e.payload.get("metric_name", "").lower().startswith("cpu")
            or (e.payload.get("cpu_percent", 0) > threshold)
        ]

        findings = []
        recommendations = []

        for e in cpu_events:
            pct = e.payload.get("cpu_percent") or e.payload.get("value", 0)
            pod = e.payload.get("pod_name", "unknown")
            if pct > threshold:
                findings.append(f"CPU saturation on {pod}: {pct:.1f}%")
                recommendations.append({
                    "title": f"Scale {pod} or reduce load",
                    "action_type": "scale",
                    "kubectl_command": f"kubectl top pod {pod} -n {context.namespace}",
                    "priority": 1,
                    "confidence": 0.85,
                })

        if get_settings().feature_ai_agents and findings:
            prompt = f"""Analyze this CPU anomaly:
Pod: {cpu_events[0].payload.get('pod_name', 'unknown')}
CPU Usage: {cpu_events[0].payload.get('cpu_percent', 0):.1f}%
Threshold: {threshold}%

Previous incidents: {len(context.previous_incidents)}
Topology: {len(context.topology.get('nodes', []))} nodes

Provide: impact assessment, likely causes, escalation risk."""
            response, metadata = await self._query_ollama(prompt)
            findings.append(f"AI Analysis: {response[:300]}")

            confidence = self._parse_confidence(response)
            more_recs = self._extract_recommendations(response)
            recommendations.extend(more_recs)
        else:
            confidence = 0.75 if findings else 0.3

        reasoning = f"Detected {len(cpu_events)} CPU anomalies above {threshold}% threshold"

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No CPU anomalies detected"],
            recommendations=recommendations,
            reasoning=reasoning,
            confidence=confidence,
            model_used=get_settings().ollama_model,
            latency_ms=0,
        )


class MemoryAgent(AIAgent):
    """Analyzes memory leaks, OOMKills, and heap pressure."""

    agent_type = "memory"
    description = "Memory Anomaly Analysis Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        threshold = get_settings().anomaly_memory_threshold_percent
        memory_events = [
            e for e in context.events
            if "memory" in e.payload.get("metric_name", "").lower()
            or (e.payload.get("memory_percent", 0) > threshold)
            or "OOMKill" in e.payload.get("reason", "")
        ]

        findings = []
        recommendations = []

        for e in memory_events:
            pct = e.payload.get("memory_percent", 0)
            pod = e.payload.get("pod_name", "unknown")
            reason = e.payload.get("reason", "")

            if "OOMKill" in reason:
                findings.append(f"OOMKilled: {pod}")
                recommendations.append({
                    "title": f"Increase memory limits for {pod}",
                    "action_type": "scale",
                    "priority": 1,
                    "confidence": 0.95,
                })
            elif pct > threshold:
                findings.append(f"Memory saturation on {pod}: {pct:.1f}%")
                recommendations.append({
                    "title": f"Monitor memory leak on {pod}",
                    "action_type": "investigate",
                    "priority": 2,
                    "confidence": 0.8,
                })

        if get_settings().feature_ai_agents and findings:
            prompt = f"""Analyze memory issue:
Findings: {'; '.join(findings)}
Pods Affected: {len(memory_events)}
Memory Threshold: {threshold}%

Provide: heap growth assessment, leak likelihood, recovery actions."""
            response, metadata = await self._query_ollama(prompt)
            findings.append(f"AI Analysis: {response[:300]}")
            confidence = self._parse_confidence(response)
        else:
            confidence = 0.8 if findings else 0.3

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No memory anomalies detected"],
            recommendations=recommendations,
            reasoning=f"Detected {len(memory_events)} memory anomalies",
            confidence=confidence,
            model_used=get_settings().ollama_model,
        )


class CorrelationAgent(AIAgent):
    """Correlates anomalies across CPU, memory, storage, logs."""

    agent_type = "correlation"
    description = "Cross-Resource Correlation Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        anomaly_types = {}
        for e in context.events:
            atype = e.payload.get("anomaly_type", "unknown")
            anomaly_types[atype] = anomaly_types.get(atype, 0) + 1

        findings = []
        for atype, count in anomaly_types.items():
            findings.append(f"{count} {atype} anomalies detected")

        correlation_score = len(anomaly_types) / max(len(context.events), 1)
        is_correlated = len(anomaly_types) > 1

        if is_correlated and get_settings().feature_ai_agents:
            prompt = f"""Correlate multi-resource anomalies:
Anomaly Types: {json.dumps(anomaly_types)}
Total Events: {len(context.events)}
Cascade Chain Depth: {len(context.cascade_chain)}
Affected Services: {len(context.dependencies)}

Provide: correlation theory, root cause hypothesis, confidence."""
            response, metadata = await self._query_ollama(prompt)
            findings.append(f"Correlation Analysis: {response[:400]}")
            confidence = self._parse_confidence(response)
        else:
            confidence = 0.5 + (0.2 * len(anomaly_types))

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings,
            reasoning=f"Correlated {len(anomaly_types)} anomaly types across {len(context.dependencies)} services",
            confidence=min(1.0, confidence),
            model_used=get_settings().ollama_model,
        )


class RCAAgent(AIAgent):
    """AI-enhanced Root Cause Analysis."""

    agent_type = "rca"
    description = "Root Cause Analysis Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        findings = []

        if context.rca_summary:
            findings.append(f"Deterministic RCA: {context.rca_summary}")

        if get_settings().feature_ai_agents:
            prompt = f"""Conduct root cause analysis:
Deterministic RCA: {context.rca_summary or 'N/A'}
Cascade Chain: {json.dumps(context.cascade_chain[:5]) if context.cascade_chain else '[]'}
Affected Services: {len(context.dependencies)}
Events: {len(context.events)}

Provide: AI-enhanced RCA, causal theory, alternative root causes, confidence."""
            response, metadata = await self._query_ollama(prompt, max_tokens=1500)
            findings.append(f"AI-Enhanced Analysis: {response[:500]}")
            confidence = self._parse_confidence(response)
        else:
            confidence = 0.7

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings,
            reasoning="AI-enhanced root cause analysis",
            confidence=confidence,
            model_used=get_settings().ollama_model,
        )


class RecommendationAgent(AIAgent):
    """Generates prioritized remediation recommendations."""

    agent_type = "recommendation"
    description = "Recommendation Generation Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        recommendations = []

        if context.cascade_chain:
            origin = context.cascade_chain[0].get("service", "unknown")
            recommendations.append({
                "title": f"Isolate cascading failure from {origin}",
                "description": "Prevent downstream propagation",
                "action_type": "mitigate",
                "priority": 1,
                "confidence": 0.9,
            })

        if get_settings().feature_ai_agents:
            prompt = f"""Generate remediation recommendations:
Cascade Chain: {len(context.cascade_chain)} hops
Blast Radius: {context.blast_radius.get('affected_count', 0)} services
Confidence: {context.rca_summary is not None}

Provide: top 3 prioritized actions, risks, expected impact."""
            response, metadata = await self._query_ollama(prompt)
            extracted = self._extract_recommendations(response)
            recommendations.extend(extracted[:3])
            confidence = self._parse_confidence(response)
        else:
            confidence = 0.7

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=[f"Generated {len(recommendations)} recommendations"],
            recommendations=recommendations[:5],
            reasoning="Prioritized remediation actions",
            confidence=confidence,
            model_used=get_settings().ollama_model,
        )


class SummarizationAgent(AIAgent):
    """Generates executive and technical summaries."""

    agent_type = "summarization"
    description = "Incident Summarization Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        findings = []

        prompt = f"""Summarize this infrastructure incident:
Duration: Unknown
Services Affected: {len(context.dependencies)}
Event Count: {len(context.events)}
Cascade Depth: {len(context.cascade_chain)}

Provide:
1. Executive summary (1-2 sentences)
2. Technical explanation
3. Impact assessment
4. Resolution timeline"""

        response, metadata = await self._query_ollama(prompt, max_tokens=2000)
        findings.append(response)

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings,
            reasoning="Generated incident summary",
            confidence=0.85,
            model_used=get_settings().ollama_model,
            raw_response=response,
        )


class NPLInfrastructureAssistant(AIAgent):
    """Natural language infrastructure query assistant."""

    agent_type = "npl_assistant"
    description = "Natural Language Infrastructure Assistant"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        findings = []

        query = "What is the current state of the infrastructure and what are the critical issues?"
        prompt = f"""You are an infrastructure assistant. Answer this query about the current incident:
Query: {query}

Context:
- Affected Services: {len(context.dependencies)}
- Event Count: {len(context.events)}
- Cascade Depth: {len(context.cascade_chain)}
- Namespace: {context.namespace}
- Root Cause: {context.rca_summary or 'Unknown'}

Provide:
1. Natural language summary of current state
2. Critical issues requiring immediate attention
3. Status of affected services
4. Recommended next steps"""

        response, metadata = await self._query_ollama(prompt, max_tokens=1500)
        findings.append(response)

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings,
            reasoning="Natural language infrastructure analysis",
            confidence=0.8,
            model_used=get_settings().ollama_model,
            raw_response=response,
        )


class StorageAgent(AIAgent):
    """Analyzes storage and PVC issues."""

    agent_type = "storage"
    description = "Storage and PVC Analysis Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        storage_events = [
            e for e in context.events
            if "storage" in e.payload.get("anomaly_type", "").lower()
            or "pvc" in e.payload.get("reason", "").lower()
            or "disk" in e.payload.get("metric_name", "").lower()
        ]

        findings = []
        recommendations = []

        for e in storage_events:
            pod = e.payload.get("pod_name", "unknown")
            reason = e.payload.get("reason", "")
            usage = e.payload.get("value", 0)

            if "PVC" in reason or "PersistentVolume" in reason:
                findings.append(f"Storage issue on {pod}: {reason}")
                recommendations.append({
                    "title": f"Investigate PVC for {pod}",
                    "action_type": "investigate",
                    "kubectl_command": f"kubectl describe pvc -n {context.namespace} | grep {pod}",
                    "priority": 2,
                    "confidence": 0.85,
                })
            elif usage > 85:
                findings.append(f"High disk usage on {pod}: {usage}%")
                recommendations.append({
                    "title": f"Free up disk space on {pod}",
                    "action_type": "mitigate",
                    "priority": 1,
                    "confidence": 0.9,
                })

        if get_settings().feature_ai_agents and findings:
            prompt = f"""Analyze storage and volume issues:
Findings: {'; '.join(findings)}
Pods Affected: {len(storage_events)}

Provide: storage growth trends, capacity planning, remediation timeline."""
            response, metadata = await self._query_ollama(prompt)
            findings.append(f"Storage Analysis: {response[:300]}")
            confidence = self._parse_confidence(response)
        else:
            confidence = 0.75 if findings else 0.3

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No storage anomalies detected"],
            recommendations=recommendations,
            reasoning=f"Detected {len(storage_events)} storage anomalies",
            confidence=confidence,
            model_used=get_settings().ollama_model,
        )


class NetworkAgent(AIAgent):
    """Analyzes network connectivity and DNS issues."""

    agent_type = "network"
    description = "Network Connectivity and DNS Analysis Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        network_events = [
            e for e in context.events
            if "network" in e.payload.get("anomaly_type", "").lower()
            or "dns" in e.payload.get("reason", "").lower()
            or "connection" in e.payload.get("reason", "").lower()
            or "timeout" in e.payload.get("reason", "").lower()
        ]

        findings = []
        recommendations = []

        for e in network_events:
            pod = e.payload.get("pod_name", "unknown")
            reason = e.payload.get("reason", "")

            if "DNS" in reason:
                findings.append(f"DNS resolution issue on {pod}: {reason}")
                recommendations.append({
                    "title": f"Check DNS configuration for {pod}",
                    "action_type": "investigate",
                    "kubectl_command": f"kubectl exec {pod} -n {context.namespace} -- nslookup kubernetes.default",
                    "priority": 2,
                    "confidence": 0.85,
                })
            elif "connection" in reason.lower() or "timeout" in reason.lower():
                findings.append(f"Network connectivity issue on {pod}: {reason}")
                recommendations.append({
                    "title": f"Inspect network policy for {pod}",
                    "action_type": "investigate",
                    "priority": 2,
                    "confidence": 0.8,
                })

        if get_settings().feature_ai_agents and findings:
            prompt = f"""Analyze network and connectivity issues:
Findings: {'; '.join(findings)}
Events: {len(network_events)}
Namespace: {context.namespace}

Provide: network topology analysis, service discovery issues, latency analysis."""
            response, metadata = await self._query_ollama(prompt)
            findings.append(f"Network Analysis: {response[:300]}")
            confidence = self._parse_confidence(response)
        else:
            confidence = 0.7 if findings else 0.3

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No network anomalies detected"],
            recommendations=recommendations,
            reasoning=f"Detected {len(network_events)} network anomalies",
            confidence=confidence,
            model_used=get_settings().ollama_model,
        )


class LogsAgent(AIAgent):
    """Analyzes logs for error patterns and issues."""

    agent_type = "logs"
    description = "Log Analysis and Pattern Recognition Agent"

    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        findings = []
        recommendations = []

        log_pattern_keywords = ["error", "exception", "panic", "fatal", "crash", "segfault", "oom"]
        event_log_count = len([
            e for e in context.events
            if any(keyword in str(e.payload).lower() for keyword in log_pattern_keywords)
        ])

        if event_log_count > 0:
            findings.append(f"Detected {event_log_count} error patterns in logs")
            recommendations.append({
                "title": "Review application logs for errors",
                "action_type": "investigate",
                "kubectl_command": f"kubectl logs -n {context.namespace} --all-containers=true --tail=100",
                "priority": 2,
                "confidence": 0.85,
            })

        if get_settings().feature_ai_agents:
            prompt = f"""Analyze application logs and error patterns:
Error Events: {event_log_count}
Services: {len(context.dependencies)}
Namespace: {context.namespace}

Provide: error categorization, root cause indicators, log anomalies, remediation actions."""
            response, metadata = await self._query_ollama(prompt, max_tokens=1200)
            findings.append(f"Log Analysis: {response[:400]}")
            confidence = self._parse_confidence(response)
        else:
            confidence = 0.75 if findings else 0.4

        return AIAgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No significant log anomalies detected"],
            recommendations=recommendations,
            reasoning=f"Analyzed {event_log_count} error events from logs",
            confidence=confidence,
            model_used=get_settings().ollama_model,
        )
