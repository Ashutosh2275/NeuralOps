# SentinelOps AI — Local Environment Startup Script
param(
    [switch]$NoFrontend,
    [switch]$NoBackend
)

$repoRoot = "d:\NeuralOps"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SENTINELOPS AI — LOCAL RUNTIME ENVIRONMENT STARTUP" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. PostgreSQL 18
$pg = & "C:\Program Files\PostgreSQL\18\bin\pg_isready.exe" -p 5433 2>$null
if ($pg -notmatch "accepting connections") {
    Write-Host "[*] Starting PostgreSQL 18 on port 5433..." -ForegroundColor Yellow
    Start-Process -FilePath "C:\Program Files\PostgreSQL\18\bin\postgres.exe" -ArgumentList "-D", "d:\NeuralOps\infra\pg_data", "-p", "5433" -WindowStyle Hidden
    Start-Sleep -Seconds 2
} else {
    Write-Host "[OK] PostgreSQL 18 running on port 5433" -ForegroundColor Green
}

# 2. Redis 5
$redis = & "d:\NeuralOps\infra\redis-5\redis-cli.exe" -p 6380 ping 2>$null
if ($redis -ne "PONG") {
    Write-Host "[*] Starting Redis on port 6380..." -ForegroundColor Yellow
    Start-Process -FilePath "d:\NeuralOps\infra\redis-5\redis-server.exe" -ArgumentList "--port", "6380", "--bind", "127.0.0.1" -WindowStyle Hidden
    Start-Sleep -Seconds 1
} else {
    Write-Host "[OK] Redis running on port 6380" -ForegroundColor Green
}

# 3. Prometheus
try {
    $prom = Invoke-RestMethod -Uri "http://127.0.0.1:9090/-/healthy" -TimeoutSec 1
    Write-Host "[OK] Prometheus running on port 9090" -ForegroundColor Green
} catch {
    Write-Host "[*] Starting Prometheus on port 9090..." -ForegroundColor Yellow
    $promData = "d:\NeuralOps\infra\prom-data"
    if (-not (Test-Path $promData)) { New-Item -ItemType Directory -Path $promData -Force | Out-Null }
    Start-Process -FilePath "d:\NeuralOps\infra\prometheus-bin\prometheus-3.14.0.windows-amd64\prometheus.exe" -ArgumentList "--config.file=d:\NeuralOps\infra\prometheus\prometheus-local.yml", "--storage.tsdb.path=$promData", "--web.listen-address=127.0.0.1:9090" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# 4. Loki
try {
    $loki = Invoke-RestMethod -Uri "http://127.0.0.1:3100/ready" -TimeoutSec 1
    Write-Host "[OK] Loki running on port 3100" -ForegroundColor Green
} catch {
    Write-Host "[*] Starting Loki on port 3100..." -ForegroundColor Yellow
    Start-Process -FilePath "d:\NeuralOps\infra\loki-bin\loki-windows-amd64.exe" -ArgumentList "-config.file=d:\NeuralOps\infra\loki\loki-local.yml" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# 5. Ollama
try {
    $ol = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 1
    Write-Host "[OK] Ollama running on port 11434 (v$($ol.version))" -ForegroundColor Green
} catch {
    Write-Host "[*] Starting Ollama serve..." -ForegroundColor Yellow
    Start-Process -FilePath "C:\Users\ASUS\AppData\Local\Programs\Ollama\ollama.exe" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 6. Kubernetes (k3s via WSL2)
$k8sOk = $false
try {
    $k8sNode = kubectl get nodes --no-headers 2>$null
    if ($k8sNode -match "Ready") {
        $k8sOk = $true
        Write-Host "[OK] Kubernetes cluster running ($k8sNode)" -ForegroundColor Green
    }
} catch {}

if (-not $k8sOk) {
    Write-Host "[*] Starting k3s server on WSL2 bridge..." -ForegroundColor Yellow
    Start-Process -FilePath "wsl.exe" -ArgumentList "-d", "docker-desktop", "-e", "/bin/sh", "-c", "/mnt/host/d/NeuralOps/infra/k3s-bin/k3s server --data-dir /run/k3s --disable traefik --disable servicelb --write-kubeconfig-mode 644 --tls-san 127.0.0.1" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

# 7. Backend
if (-not $NoBackend) {
    Write-Host "[*] Checking SentinelOps Backend..." -ForegroundColor Yellow
    try {
        $be = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 1
        Write-Host "[OK] SentinelOps Backend already running on port 8000" -ForegroundColor Green
    } catch {
        Write-Host "[*] Starting SentinelOps Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
        $env:PYTHONPATH = "d:\NeuralOps\backend\src"
        Start-Process -FilePath "d:\NeuralOps\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "sentinelops.main:app", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory "d:\NeuralOps" -WindowStyle Hidden
        Start-Sleep -Seconds 3
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ALL LOCAL SERVICES READY. Run .\scripts\verify_local.ps1" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
