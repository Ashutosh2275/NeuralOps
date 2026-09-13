# ==============================================================================
# SentinelOps AI - Reset Demo State & Database Hygiene Script
# Idempotently deduplicates incidents, cleans RAG vector store, and verifies daemons.
# ==============================================================================

Write-Host "
=== SentinelOps AI Demo State Reset ===" -ForegroundColor Cyan

# 1. Run Python database & RAG cleaner
$env:PYTHONPATH = "d:\NeuralOps\backend\src"
& "d:\NeuralOps\.venv\Scripts\python.exe" "d:\NeuralOps\scripts\clean_state.py"

# 2. Check all primary subsystems
Write-Host "
Verifying Subsystems..." -ForegroundColor Yellow
& "d:\NeuralOps\.venv\Scripts\python.exe" -c "
import socket
ports = {'Postgres': 5433, 'Redis': 6380, 'Prometheus': 9090, 'Loki': 3100, 'Ollama': 11434, 'Backend': 8000, 'Frontend': 5173}
for name, port in ports.items():
    s = socket.socket()
    s.settimeout(0.5)
    st = 'HEALTHY (OPEN)' if s.connect_ex(('127.0.0.1', port)) == 0 else 'UNAVAILABLE (CLOSED)'
    s.close()
    print(f'  - {name} (port {port}): {st}')
"

# 3. Check Live Workload Count
Write-Host "
Verifying Live Workloads..." -ForegroundColor Yellow
& "d:\NeuralOps\.venv\Scripts\python.exe" -c "
import httpx
try:
    r = httpx.get('http://127.0.0.1:8000/api/v1/workloads/overview', timeout=3.0)
    print('  Workloads Overview:', r.json())
except Exception as e:
    print('  Workloads API unavailable:', e)
"

Write-Host "
=== Reset & Hygiene Check Complete ===
" -ForegroundColor Green
