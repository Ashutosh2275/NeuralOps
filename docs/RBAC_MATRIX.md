# SentinelOps AI - Role-Based Access Control (RBAC) Matrix

This document defines the strict, authoritative permission model enforced across the SentinelOps AI platform. Permissions are validated at the FastAPI security middleware and route dependency layers, returning standard HTTP 403 Forbidden responses for unauthorized attempts.

---

## 1. Role Definitions

| Role | Scope | Intended Persona |
| :--- | :--- | :--- |
| **Viewer** | Read-only inspection across all dashboards, telemetry, topology, and historical investigations. | Auditors, stakeholders, read-only SRE observers. |
| **Operator** | Full operational access to acknowledge/resolve incidents, trigger autonomous investigations, execute remediation proposals, and run chaos simulations. | On-call SREs, Incident Commanders, Operations Engineers. |
| **Admin** | Full system governance including retention execution, credential rotation, configuration override, and audit clearance. | Platform Leads, Security Administrators. |

---

## 2. API Endpoint Authorization Contract

| Category | Endpoint / Action | Method | Minimum Role | Viewer | Operator | Admin |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Health & Telemetry** | /health | GET | None | ALLOW | ALLOW | ALLOW |
| **Workloads** | /api/v1/workloads/overview | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Workloads** | /api/v1/workloads/pods | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Workloads** | /api/v1/workloads/logs | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Workloads** | /api/v1/workloads/metrics | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Topology** | /api/v1/topology/graph | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Topology** | /api/v1/topology/snapshot | POST | Operator | **DENY (403)** | ALLOW | ALLOW |
| **Incidents** | /api/v1/incidents | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Incidents** | /api/v1/incidents/{id} | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Incidents** | /api/v1/incidents/{id}/acknowledge | POST | Operator | **DENY (403)** | ALLOW | ALLOW |
| **Incidents** | /api/v1/incidents/{id}/resolve | POST | Operator | **DENY (403)** | ALLOW | ALLOW |
| **Investigations** | /api/v1/investigations/active | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Investigations** | /api/v1/investigations/trigger | POST | Operator | **DENY (403)** | ALLOW | ALLOW |
| **Remediation** | /api/v1/remediations/proposals | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Remediation** | /api/v1/remediations/{id}/approve | POST | Operator | **DENY (403)** | ALLOW | ALLOW |
| **Remediation** | /api/v1/remediations/{id}/execute | POST | Operator | **DENY (403)** | ALLOW | ALLOW |
| **Simulation** | /api/v1/simulations/run | POST | Operator | **DENY (403)** | ALLOW | ALLOW |
| **Knowledge / RAG** | /api/v1/knowledge/search | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **Knowledge / RAG** | /api/v1/knowledge/upload | POST | Admin | **DENY (403)** | **DENY (403)** | ALLOW |
| **Audit Trail** | /api/v1/audit/logs | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **System Settings** | /api/v1/settings | GET | Viewer | ALLOW | ALLOW | ALLOW |
| **System Settings** | /api/v1/settings/retention/execute | POST | Admin | **DENY (403)** | **DENY (403)** | ALLOW |
| **System Settings** | /api/v1/settings/config/override | POST | Admin | **DENY (403)** | **DENY (403)** | ALLOW |

---

## 3. UI/UX Role-Adaptive Controls

The frontend dashboard inspects the active role from the authenticated session context (useAuth()):
1. **Viewer Mode**:
   - Remediation action buttons are disabled with tooltip *"Requires Operator or Admin role"*.
   - Acknowledge and Resolve incident controls are hidden or disabled.
   - Simulation launch triggers are read-only.
   - Retention policy execution triggers are hidden.
2. **Operator Mode**:
   - Operational controls (Investigate, Acknowledge, Execute Remediation, Chaos Simulation) are interactive and enabled.
   - Admin-only retention execution button displays *"Admin role required"*.
3. **Admin Mode**:
   - All operational controls and administrative triggers (retention purging, system overrides) are active.

---

## 4. Audit Logging Guarantee

Every security-sensitive operation writes an AuditEvent record with:
- ctor: Authenticated user email or client ID.
- ole: Effective role evaluated by the security engine (dmin, operator, iewer, or system).
- ction: Specific operation performed.
- equest_path: Full API URI.
- execution_status: success or denied (with HTTP 403).
- 	imestamp: UTC timestamp with microsecond precision.
