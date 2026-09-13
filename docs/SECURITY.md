# SentinelOps AI — Enterprise Security Architecture & Hardening Guide

## 1. Executive Summary
SentinelOps AI implements an enterprise-grade defense-in-depth security architecture. A fundamental architectural invariant of SentinelOps AI is that **security boundaries are enforced deterministically in application code, completely independent of LLM decisions**. External data is treated as untrusted and cannot grant execution authority or override tool permissions.

---

## 2. Authentication & Authorization (RBAC)

### 2.1 Identity Providers
SentinelOps AI supports API Key and Bearer token authentication via HTTP headers:
- `X-API-Key: <token>`
- `Authorization: Bearer <token>`

### 2.2 Role Hierarchy
| Role | Privilege Level | Permitted Actions |
| :--- | :--- | :--- |
| **VIEWER** | Level 1 (Read-Only) | Inspect active investigations, list registered tools, view audit trail, query metrics, check platform health. |
| **OPERATOR** | Level 2 (Diagnostic) | All VIEWER privileges + trigger autonomous incident investigations, execute authorized read-only inspection tools, propose human-governed remediation actions. |
| **ADMIN** | Level 3 (Governance) | All OPERATOR privileges + review/approve/reject remediation proposals, execute data retention cleanup policies, configure security boundaries. |

---

## 3. Tool Permission Model & Phase 4 Invariant

All operational investigation tools registered with SentinelOps AI operate under strict deterministic permission levels:
- `READ_ONLY`: Telemetry inspection, log tailing, metric queries, topology traversals, and RAG knowledge lookups.
- `SAFE_ACTION`: Reserved for safe non-destructive operational proposals.
- `HIGH_PRIVILEGE`: Reserved for mutating cluster actions.

> [!IMPORTANT]
> **Strict Phase 4 Invariant**: All active investigation tools remain strictly `READ_ONLY`. In Phase 4, **no autonomous remediation or mutating actions** are permitted or executed. Any attempt by a tool to mutate infrastructure or bypass this restriction is rejected with a deterministic `PermissionError`.

---

## 4. Human Approval Governance Architecture

To ensure enterprise oversight before any future write or remediation action is executed, SentinelOps AI provides a stateful human approval workflow:

```mermaid
stateDiagram-v2
    [*] --> PROPOSED: Operator submits proposal
    PROPOSED --> PENDING_APPROVAL: Submitted for human review
    PENDING_APPROVAL --> APPROVED: Human Admin approves
    PENDING_APPROVAL --> REJECTED: Human Admin rejects
    PENDING_APPROVAL --> EXPIRED: TTL timeout exceeded
    PROPOSED --> CANCELLED: Operator cancels
    APPROVED --> EXECUTION_BLOCKED: Blocked in Phase 4
```

In Phase 4, transitioning from `APPROVED` to `EXECUTED` is **hard-blocked**. The `execute_action()` method strictly raises `PermissionError("Autonomous remediation execution is strictly BLOCKED in Phase 4")`.

---

## 5. Prompt Injection Defense & Data Boundaries

All external telemetry (Kubernetes pod names, logs, annotations, events, Prometheus labels, Loki logs, and user-supplied descriptions) is classified as **UNTRUSTED DATA**.

### Multi-Layer Defense:
1. **Pattern Detection & Neutralization**: Identifies signatures such as `"Ignore all previous instructions"`, `"Reveal system prompt"`, `"Print environment variables"`, `"Use administrator privileges"`, and `"Run kubectl delete"`, substituting them with `[NEUTRALIZED_INJECTION_ATTEMPT]`.
2. **Context Boundaries**: Untrusted telemetry is encapsulated in unambiguous boundary delimiters:
   ```xml
   <UNTRUSTED_EXTERNAL_DATA source="operational_telemetry">
   ...
   </UNTRUSTED_EXTERNAL_DATA>
   ```
3. **Execution Separation**: The LLM acts purely as an investigative reasoning agent; its textual output can never directly trigger shell commands or change tool permission levels.

---

## 6. Centralized Secret Redaction

The centralized `SecretRedactor` automatically intercepts and redacts credentials before they can reach tool records, evidence stores, audit logs, API responses, or generated RCA reports:
- AWS Access & Secret Keys (`AKIA...`)
- JSON Web Tokens (JWTs) and Bearer tokens
- Database connection strings containing passwords (`postgresql://user:[REDACTED]@host`)
- RSA/EC private keys (`-----BEGIN [RSA/EC] PRIVATE KEY...-----`)
- OpenAI / Third-party API keys (`sk-...`)
- Configuration passwords and secrets

---

## 7. Audit Trail & Data Retention

### 7.1 Append-Oriented Audit Log
Every tool call, investigation lifecycle event, and governance decision is recorded in an append-oriented JSONL audit log (`data/audit/audit_trail.jsonl`), storing:
- `event_id`, `investigation_id`, `timestamp`, `actor`, `role`, `request_path`
- Sanitized arguments and tools selected
- Evidence sources, citations, confidence score, and redacted final RCA

### 7.2 Data Retention Policies
Configurable time-to-live policies prevent unbounded disk growth:
- Completed investigations: 30 days
- Audit logs: 90 days
- **Safety Invariant**: In-progress investigations (`status != 'completed'`) are strictly protected from retention deletion.
