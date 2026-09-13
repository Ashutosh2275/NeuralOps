# SentinelOps AI — Evaluation Framework & Golden Dataset

## 1. Overview
The SentinelOps AI Evaluation Framework provides automated, quantitative, and reproducible benchmarks for assessing the operational intelligence of the platform. Investigations are evaluated not merely on HTTP status codes, but on tool selection precision, argument accuracy, RCA groundedness, epistemic uncertainty, and Brier score calibration.

---

## 2. Evaluation Metrics

| Metric | Definition | Benchmark Target |
| :--- | :--- | :--- |
| **Tool Precision** | Proportion of invoked tools that were required for diagnosis | $\ge 0.80$ |
| **Tool Recall** | Proportion of expected diagnostic tools that were successfully invoked | $\ge 0.80$ |
| **Tool F1 Score** | Harmonic mean of tool precision and recall | $\ge 0.80$ |
| **RCA Accuracy** | Binary accuracy: does RCA contain expected root cause concepts without fabricated claims? | $\ge 0.90$ |
| **Groundedness Score** | Percentage of RCA claims classified as directly observed (`FACT`), logically inferred (`INFERENCE`), or explicitly missing (`UNCERTAINTY`) | $\ge 0.85$ |
| **Hallucination Rate** | Percentage of RCA claims unsupported by any gathered evidence | $\le 0.05$ |
| **Citation Correctness** | Percentage of cited evidence IDs that are valid and present in collected evidence | $1.00$ (100%) |
| **Brier Calibration Score** | Mean squared difference between reported confidence and binary correctness $(C - A)^2$ | $\le 0.08$ |

---

## 3. Golden Dataset (20 Operational Scenarios)

The evaluation suite (`sentinelops.evaluation.dataset`) includes 20 comprehensive operational scenarios:

1. **GS-01: CrashLoopBackOff**: Container panicking on startup due to missing configuration.
2. **GS-02: OOMKilled**: Memory limits breached in cgroup hierarchy.
3. **GS-03: PVC Saturation**: PersistentVolumeClaim 98% full causing storage write locks.
4. **GS-04: DB Connection Exhaustion**: Connection pool starvation under spike load.
5. **GS-05: Dependency Cascade**: Upstream timeout propagating across checkout flow.
6. **GS-06: Network Latency Spike**: Cross-AZ packet delay exceeding 2500ms.
7. **GS-07: Deployment Regression**: Null pointer exception introduced in container release v2.4.0.
8. **GS-08: High CPU Throttling**: CFS quota starvation backing up request queues.
9. **GS-09: High Memory Leak**: Linear RSS heap growth without GC reclamation.
10. **GS-10: Scheduling Failure**: 0/8 nodes available due to insufficient CPU.
11. **GS-11: Misleading Logs**: Deprecation warnings masking underlying socket disconnect.
12. **GS-12: Stale Alert**: Alertmanager firing alert for an already-healthy pod (refutation check).
13. **GS-13: Conflicting Metrics**: 0% CPU usage alongside peak request rates.
14. **GS-14: Multiple Simultaneous Failures**: Multi-service cascade across cache and database.
15. **GS-15: Partial Telemetry Outage**: Prometheus down; system relies on Loki logs and K8s API.
16. **GS-16: Missing Logs**: Silent service with 0 log records; requires explicit uncertainty.
17. **GS-17: Missing Metrics**: Unscraped service; requires explicit uncertainty.
18. **GS-18: Broken Dependency Graph**: Isolated or disconnected node in microservice mesh.
19. **GS-19: Irrelevant RAG Documents**: Noisy documentation injected into vector retrieval.
20. **GS-20: Prompt Injection in Operational Logs**: Adversarial injection in stderr.

---

## 4. Groundedness & Hallucination Assessment

SentinelOps AI parses generated RCA statements into sentence-level claims and categorizes them into three valid epistemic categories and one violation category:
- `FACT`: Directly corroborated by telemetry or tool records.
- `INFERENCE`: Logically derived conclusion supported by observed facts.
- `UNCERTAINTY`: Explicit statement indicating missing telemetry or incomplete data.
- `HALLUCINATION` *(Violation)*: Unsupported assertion with zero evidentiary basis.

---

## 5. RAG Retrieval Evaluation

Vector search quality is measured across diverse operational corpora:
- **Precision@K**: Density of relevant runbook/post-mortem sections in top $K$ results.
- **Recall@K**: Coverage of all ground-truth documentation sections.
- **Mean Reciprocal Rank (MRR)**: Average reciprocal rank of the first relevant document:
  $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
- **Safe No-Result Behavior**: When no relevant documentation exists, the system gracefully handles empty matches without hallucinating citations.
