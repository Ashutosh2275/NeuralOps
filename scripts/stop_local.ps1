# SentinelOps AI — Local Environment Shutdown Script
Write-Host "============================================================" -ForegroundColor Red
Write-Host "  SENTINELOPS AI — LOCAL SERVICES SHUTDOWN" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red

# Stop uvicorn/backend
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "uvicorn" -or $_.CommandLine -match "sentinelops.main" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop node/frontend
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "vite" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop Prometheus
Get-Process -Name "prometheus" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop Loki
Get-Process -Name "loki-windows-amd64" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop Redis
& "d:\NeuralOps\infra\redis-5\redis-cli.exe" -p 6380 shutdown nosave 2>$null
Get-Process -Name "redis-server" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop PostgreSQL 18
& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" stop -D "d:\NeuralOps\infra\pg_data" -m fast 2>$null
Get-Process -Name "postgres" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop k3s in WSL
wsl.exe -d docker-desktop -e /bin/sh -c "pkill -f k3s" 2>$null

Write-Host "[OK] All local background services stopped cleanly." -ForegroundColor Green
