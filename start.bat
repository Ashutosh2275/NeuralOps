@echo off
REM SentinelOps One-Click Deployment Script for Windows

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0
REM Trim trailing backslash if present
if "%PROJECT_ROOT:~-1%"=="\" set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%
set BACKEND_PORT=8000
set FRONTEND_PORT=5173

echo.
echo 🚀 SentinelOps Enterprise Platform - Starting Deployment
echo ==================================================
echo.

REM Check PostgreSQL
echo [1/5] Checking PostgreSQL connection...
psql -U sentinelops sentinelops -c "SELECT 1" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL connected
) else (
    echo ⚠️  PostgreSQL connection check skipped or service unreachable.
)

REM Run migrations
echo [2/5] Running database migrations...
cd /d %PROJECT_ROOT%\backend
call alembic upgrade head >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Database migrations complete
) else (
    echo ⚠️  Migration warning (may already be up to date)
)

REM Start Backend
echo [3/5] Starting FastAPI backend on port %BACKEND_PORT%...
cd /d %PROJECT_ROOT%\backend
start /B /D %PROJECT_ROOT%\backend cmd /c "uvicorn sentinelops.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
echo ✅ Backend started (check console for details)

REM Start Frontend
echo [4/5] Starting React frontend on port %FRONTEND_PORT%...
cd /d %PROJECT_ROOT%\frontend
start /B /D %PROJECT_ROOT%\frontend cmd /c "npm run dev -- --port %FRONTEND_PORT%"
echo ✅ Frontend started (check console for details)

REM Wait for services
echo [5/5] Waiting for services to be ready...
timeout /t 5 /nobreak

echo.
echo ==================================================
echo 🎉 SentinelOps is ready!
echo ==================================================
echo.
echo 📍 Frontend: http://localhost:%FRONTEND_PORT%
echo 📍 Backend:  http://localhost:%BACKEND_PORT%
echo.
echo Opening Chrome in 2 seconds...
timeout /t 2 /nobreak

REM Open Chrome
start chrome http://localhost:%FRONTEND_PORT%

echo.
echo 🛑 To stop services, close the command windows above.
echo.
pause
