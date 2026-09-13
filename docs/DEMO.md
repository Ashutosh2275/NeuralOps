# SentinelOps AI — Human Operator Demonstration Runbook

**Audience**: Technical Reviewers, Interviewers, SRE Evaluators, Portfolio Reviewers  
**Target Duration**: 3–5 minutes  
**Target Workload**: `crashloop-service` & `oom-service` in `sentinelops-e2e` namespace  

---

## Scenario 1: CrashLoopBackOff Triage (3 Minutes)

Follow this deterministic 14-step flow from failure detection to operational resolution:

### 1. Start Environment
Ensure all infrastructure daemons (k3s, PostgreSQL, Redis, Prometheus, Loki, Ollama, FastAPI, React) are active:
```powershell
python scripts/verify_real_environment.py
```

### 2. Verify Environment
Confirm that all 9 subsystems report operational status. Probes confirm PostgreSQL, Redis, Prometheus, Loki, and Ollama connectivity.

### 3. Open Overview
Open `http://localhost:5173/` in your browser.  
Observe the compact **System Health** row displaying 7/7 operational services with real-time health indicators.

### 4. Show Incident
Locate the `CrashLoopBackOff detected in crashloop-service` incident listed with `CRITICAL` severity in the **Active Incidents** table.

### 5. Open Incident Detail
Click the incident title or the **Investigate** action to navigate to `/incidents/:id`.

### 6. Start / View Investigation
Observe the autonomous investigation record linked to this incident. Notice that the investigation was triggered automatically by the correlation engine.

### 7. Show Tool Execution
Scroll to **Diagnostic Tool Execution Trace**:  
Expand `get_pod_details`, `get_pod_logs`, `get_container_status`, and `get_k8s_events`.  
Observe the sanitized arguments and redacted live outputs from the cluster.

### 8. Show Evidence
Inspect the **Epistemic Evidence Breakdown**:
- **Observed Facts**: Raw container log tail (`FATAL: NullPointerException in TransactionRouter: unable to bind port 8080`), repeated container restarts, and `BackOff` events.
- **AI Inferences**: Causal deduction that port contention on startup prevents the HTTP listener from initializing.
- **Uncertainties**: Explicit disclaimers regarding potential transient network issues.

### 9. Show RAG Source
Inspect **Knowledge Runbook Citations**:  
Notice the citation for `runbook-crashloopbackoff` with cosine similarity $> 85\%$.  
Click the link to open the full runbook in `/knowledge/runbook-crashloopbackoff`.

### 10. Show Root Cause Analysis (RCA)
View the primary **Root Cause Conclusion** banner at the top of the detail screen:
> *"Application crash loop / configuration defect on crashloop-service. Container continuously failing immediately after startup; verified via repeated restarts and K8s BackOff events."*  
> **Confidence: 88%**.

### 11. Show Topology
Click **Inspect in Topology Graph** to navigate to `/topology`:  
Observe `crashloop-service` highlighted in red. Inspect incoming caller edges from `checkout-service` and outgoing store edges to `payment-db`. Review the blast radius calculation confirming cascading checkout degradation.

### 12. Show Workload
Navigate to `/workloads`:  
Click on `crashloop-service` to view the 6-tab Workload Inspector:
- **Overview**: Phase `Running`, Ready `0/1`, Restart Count $> 0$.
- **Logs**: Live stream from Loki displaying the `NullPointerException` port bind failure.
- **Metrics**: Real-time Prometheus CPU and memory series.
- **Events**: Kubernetes warning events (`BackOff`, `FailedSync`).

### 13. Show Recommendation
Return to the incident detail view and review the **Autonomous Remediation Recommendation**:  
Action: Workload Restart & Port Reconfiguration via `kubectl rollout restart deployment/crashloop-service -n sentinelops-e2e`.

### 14. Restore Healthy State
Confirm that `healthy-service` in the cluster remains in `Running` phase, with `Ready: 1/1` and `0 restarts`, verifying that the correlation engine generates zero false incidents for healthy workloads.

---

## Scenario 2: OOMKilled vs. CrashLoopBackOff (1 Minute)

Demonstrate that SentinelOps reaches a distinctly different root cause for memory exhaustion:

1. Navigate to **Investigation Workspace** (`/investigations`).
2. Select the `oom-service` investigation:
   - **Memory Evidence**: Prometheus metrics showing memory threshold ceiling reached (`container_memory_working_set_bytes`).
   - **Container State**: Exit code `137` recorded in container termination status by Kubernetes API.
   - **Confidence**: **92%**.
   - **Relevant Runbook**: Dynamically retrieves `runbook-oomkilled` with memory limit sizing recommendations.
   - **RCA Conclusion**: *"Out of Memory (OOMKilled) container termination on oom-service. Memory limit reached or kernel OOM killer triggered termination. Verified across metrics and container exit codes."*
   - **Distinction**: The platform clearly differentiates between memory exhaustion and startup application crashes.

---

## Scenario 3: 3-Tier Role Governance Demo (1 Minute)

Demonstrate authoritative 3-tier security enforcement directly in the browser:

1. **Viewer Mode (Read-Only)**:
   - In the top-right header, select role **viewer**.
   - In `/investigations`, the **Launch Investigation** button is disabled with tooltip *"Requires Operator or Admin role"*.
   - In `/tools`, **Run Tool** buttons are disabled.
   - In `/settings`, **Execute Retention** is disabled.
2. **Operator Mode (Triage & Diagnostics)**:
   - Select role **operator**.
   - In `/investigations`, **Launch Investigation** is interactive.
   - In `/tools`, execute `get_pod_details` with live parameters and observe the redacted JSON response.
   - In `/settings`, **Execute Retention** remains disabled (Admin required).
3. **Admin Mode (Governance)**:
   - Select role **admin**.
   - In `/settings`, toggle **Dry Run** and click **Execute Retention**.
   - Observe the retention summary and navigate to `/audit` to verify the immutable audit event logged for the action.

---

## Verification & Reset Scripts

- **Reset Demo State**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/reset_demo_state.ps1
  ```
- **One-Command Master Gate Verification**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/final_verify.ps1
  ```
