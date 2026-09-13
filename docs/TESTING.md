# SentinelOps AI — Testing Strategy & Verification Guide

This document describes the automated test architecture, test suites, and regression gates maintained for SentinelOps AI.

---

## 1. Test Architecture Overview

The testing framework covers four concentric rings of verification:

1. **Unit & Integration Suite (Backend)**:
   - Pytest test cases validating data collectors, event normalization, causality engines, RCA algorithms, RAG embeddings, security redactors, and RBAC authorization decorators.
2. **Frontend Type & Bundle Compilation**:
   - TypeScript project references (`tsc -b`) and Vite production bundler validating component type safety and asset packaging.
3. **Cross-Screen Data Consistency**:
   - Automated multi-subsystem probe validating that database state, Kubernetes state, telemetry, and RAG vector stores are synchronized across all routes.
4. **Browser End-to-End Suite (Playwright)**:
   - Headless Chromium automated suite testing all 13 primary routes, deep workflows, interactive role-based access control, responsive viewports, and console error cleanliness.

---

## 2. Test Commands Reference

### A. Frontend Production Build
```powershell
cd frontend
npm run build
```
- **Target**: TypeScript 5.6.2 and Vite 5.4.21.
- **Success Criteria**: Exit code 0, 0 type errors, production bundle generated in `frontend/dist/`.

### B. Backend Unit & Integration Tests
```powershell
pytest backend/tests -q
```
- **Target**: All pytest test modules in `backend/tests/`.
- **Current Baseline**: 123 passed, 0 failed, 0 skipped, 0 xfail.

### C. Live Real Environment Health Probes
```powershell
python scripts/verify_real_environment.py
```
- **Probes**: PostgreSQL (5433), Redis (6380), Prometheus (9090), Loki (3100), Ollama (11434), Kubernetes k3s (6443), Pod Log Shipper, FastAPI Backend (8000), React Frontend (5173).
- **Success Criteria**: All 9 services report healthy.

### D. Backend API Contract Verification
```powershell
python scripts/verify_backend_contracts.py
```
- **Validates**: All 20 API endpoints including schemas, 404 responses, and data integrity.

### E. Cross-Screen Consistency Suite
```powershell
python scripts/test_cross_screen_consistency.py
```
- **Validates**: 7 cross-screen consistency checks covering telemetry, topology, incidents, RAG, and RBAC.

### F. Playwright End-to-End Browser Suite
```powershell
python scripts/test_phase13_browser_certification.py
```
- **Coverage**:
  - All 13 routes (`/`, `/incidents`, `/incidents/:id`, `/investigations`, `/investigations/:id`, `/topology`, `/workloads`, `/workloads/:ns/:pod`, `/knowledge`, `/knowledge/:doc`, `/tools`, `/audit`, `/settings`).
  - Interactive deep workflows (Search, Filter, Detail views, Tool execution).
  - 3-tier RBAC enforcement (Viewer, Operator, Admin).
  - 4 viewports (1920x1080, 1440x900, 1280x800, 1024x768).
  - Console error monitoring (0 errors allowed).
  - Screenshot capture into `data/screenshots/phase12/`.

### G. Live Autonomous Investigation Traces
```powershell
d:\NeuralOps\.venv\Scripts\python.exe scripts/test_live_crashloop_e2e.py
d:\NeuralOps\.venv\Scripts\python.exe scripts/test_live_oom_e2e.py
```
- **Validates**: Full autonomous tool execution loop, hypothesis generation, and RCA against real live Kubernetes workloads (`crashloop-service` and `oom-service`).
