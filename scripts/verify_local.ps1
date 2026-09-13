# SentinelOps AI — Full Local Platform Verification Script
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host '  SENTINELOPS AI — FULL PLATFORM VERIFICATION' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

$env:PYTHONPATH = "d:\NeuralOps\backend\src"

# 1. Run Doctor
Write-Host "`n[STEP 1/4] Running SentinelOps System Doctor..." -ForegroundColor Yellow
& "d:\NeuralOps\.venv\Scripts\python.exe" -m sentinelops.cli doctor
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] Doctor detected degraded subsystems!' -ForegroundColor Red
    exit 1
}

# 2. Run Live Workload E2E Tests
Write-Host "`n[STEP 2/4] Running Live Kubernetes Autonomous Investigation Tests..." -ForegroundColor Yellow
& "d:\NeuralOps\.venv\Scripts\python.exe" "d:\NeuralOps\scripts\test_live_crashloop_e2e.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] CrashLoop investigation test failed!' -ForegroundColor Red
    exit 1
}

& "d:\NeuralOps\.venv\Scripts\python.exe" "d:\NeuralOps\scripts\test_live_oom_e2e.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] OOM investigation test failed!' -ForegroundColor Red
    exit 1
}

# 3. Run Dependency & Blast Radius Test
Write-Host "`n[STEP 3/4] Running Live Topology and Blast Radius Test..." -ForegroundColor Yellow
& "d:\NeuralOps\.venv\Scripts\python.exe" "d:\NeuralOps\scripts\test_live_dependency_failure.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] Dependency failure test failed!' -ForegroundColor Red
    exit 1
}

# 4. Run Full Automatic Source-to-Web End-to-End Audit
Write-Host "`n[STEP 4/4] Running Full Automatic Source-to-Web End-to-End Chain Audit..." -ForegroundColor Yellow
& "d:\NeuralOps\.venv\Scripts\python.exe" "d:\NeuralOps\scripts\test_complete_automatic_chain.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] Automatic end-to-end chain audit failed!' -ForegroundColor Red
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host '  ALL LOCAL VERIFICATION GATES PASSED (100% HEALTHY)' -ForegroundColor Green
Write-Host '============================================================' -ForegroundColor Green
