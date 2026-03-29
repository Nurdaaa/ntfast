@echo off
chcp 65001 >nul 2>&1
echo ==========================================================
echo Starting ntFAST in Development Mode
echo ==========================================================
echo.
echo WARNING: Close the opened Command Prompt windows to stop the servers.
echo Do NOT use the old start.bat to avoid hidden ghost processes.
echo.

set "ROOT=%~dp0"

echo [0/5] Starting Redis Server...
if exist "%ROOT%redis\redis-server.exe" (
    start "ntFAST - Redis" cmd /k "color 08 && cd /d "%ROOT%redis" && echo Starting Redis Server... && redis-server.exe"
    echo Waiting for Redis to start...
    ping -n 3 127.0.0.1 >nul
) else (
    echo WARNING: redis-server.exe not found in %ROOT%redis\
)

echo [1/5] Starting Backend (API)...
start "ntFAST - Backend (API)" cmd /k "color 0B && cd /d "%ROOT%backend" && echo Starting FastAPI Backend... && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [2/4] Starting Frontend (React)...
start "ntFAST - Frontend (React)" cmd /k "color 0E && cd /d "%ROOT%frontend" && echo Starting React Vite Server... && npm run dev"

echo [3/4] Starting Celery Worker (Backend Tasks)...
start "ntFAST - Celery Worker" cmd /k "color 0D && cd /d "%ROOT%backend" && echo Starting Celery Tasks Worker... && celery -A app.core.celery_app worker --loglevel=info --pool=solo"

echo [4/4] Starting ML Service (Fraud Detection Tasks)...
start "ntFAST - ML Service" cmd /k "color 0A && cd /d "%ROOT%ml_service" && echo Starting Celery ML Worker... && celery -A celery_config worker --loglevel=info -Q ml_analysis,fraud_detection --pool=solo"

echo ==========================================================
echo All services launched in separate visible windows!
echo If you need to stop the server, just close those CMD windows.
echo ==========================================================
pause
