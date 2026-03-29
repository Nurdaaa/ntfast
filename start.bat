@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title ntFAST - Server Manager
color 0A

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "LOGS=%ROOT%\logs"

:: Create logs directory
if not exist "%LOGS%" mkdir "%LOGS%"

echo.
echo  ==========================================================
echo.
echo   ntFAST - Financial Analysis System for Transactions
echo   All-in-One Server Manager
echo.
echo  ==========================================================
echo.

:: ===========================================================
:: PHASE 1: KILL OLD PROCESSES
:: ===========================================================

echo  ----------------------------------------------------------
echo   Phase 1/4: Stopping old processes...
echo  ----------------------------------------------------------
echo.

set "KILLED=0"

:: Kill by port 5173 (Frontend)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    set /a KILLED+=1
)

:: Kill by port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    set /a KILLED+=1
)

:: Kill by window title
taskkill /FI "WINDOWTITLE eq ntFAST-Frontend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ntFAST-Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ntFAST-Celery*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ntFAST-ML*" /F >nul 2>&1

:: Kill orphan celery
taskkill /IM "celery.exe" /F >nul 2>&1

:: Double check ports are free
ping -n 2 127.0.0.1 >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1

if !KILLED! GTR 0 (
    echo   Stopped !KILLED! old processes
    ping -n 3 127.0.0.1 >nul 2>&1
) else (
    echo   No old processes found - clean start
)
echo.

:: ===========================================================
:: PHASE 2: INFRASTRUCTURE
:: ===========================================================

echo  ----------------------------------------------------------
echo   Phase 2/4: Checking infrastructure...
echo  ----------------------------------------------------------
echo.

:: --- PostgreSQL ---
netstat -an | findstr ":5432 " | findstr "LISTENING" >nul 2>&1
if !errorlevel!==0 (
    echo   [  OK  ] PostgreSQL - port 5432
) else (
    echo   [ START] PostgreSQL...
    net start postgresql-x64-17 >nul 2>&1
    if !errorlevel! NEQ 0 (
        net start postgresql-x64-16 >nul 2>&1
        if !errorlevel! NEQ 0 (
            net start postgresql >nul 2>&1
        )
    )
    ping -n 4 127.0.0.1 >nul 2>&1
    netstat -an | findstr ":5432 " | findstr "LISTENING" >nul 2>&1
    if !errorlevel!==0 (
        echo   [  OK  ] PostgreSQL - started
    ) else (
        echo   [ FAIL ] PostgreSQL not started! Run manually.
        pause
        goto :EOF
    )
)

:: --- Redis ---
netstat -an | findstr ":6379 " | findstr "LISTENING" >nul 2>&1
if !errorlevel!==0 (
    echo   [  OK  ] Redis - port 6379
) else (
    echo   [ START] Redis...
    if exist "%ROOT%\redis\redis-server.exe" (
        start "ntFAST-Redis" /MIN "%ROOT%\redis\redis-server.exe"
        ping -n 3 127.0.0.1 >nul 2>&1
        netstat -an | findstr ":6379 " | findstr "LISTENING" >nul 2>&1
        if !errorlevel!==0 (
            echo   [  OK  ] Redis - started
        ) else (
            echo   [ FAIL ] Redis not started! Run manually.
            pause
            goto :EOF
        )
    ) else (
        echo   [ FAIL ] redis-server.exe not found
        pause
        goto :EOF
    )
)

echo.

:: ===========================================================
:: PHASE 3: INSTALL DEPENDENCIES
:: ===========================================================

echo  ----------------------------------------------------------
echo   Phase 3/4: Installing dependencies...
echo  ----------------------------------------------------------
echo.

:: --- Backend deps ---
echo   [ .... ] Backend pip install...
pip install -r "%ROOT%\backend\requirements.txt" --quiet --disable-pip-version-check >nul 2>&1
if !errorlevel!==0 (
    echo   [  OK  ] Backend dependencies installed
) else (
    echo   [ WARN ] pip install had issues - trying anyway...
)

:: --- Frontend deps (only if node_modules missing) ---
if not exist "%ROOT%\frontend\node_modules" (
    echo   [ .... ] Frontend npm install...
    cd /d "%ROOT%\frontend"
    npm install --silent >nul 2>&1
    echo   [  OK  ] Frontend dependencies installed
    cd /d "%ROOT%"
) else (
    echo   [  OK  ] Frontend node_modules exists
)

echo.

:: ===========================================================
:: PHASE 4: START ALL SERVICES
:: ===========================================================

echo  ----------------------------------------------------------
echo   Phase 4/4: Starting services...
echo  ----------------------------------------------------------
echo.

:: Clear old logs
echo. > "%LOGS%\backend.log" 2>nul
echo. > "%LOGS%\celery.log" 2>nul
echo. > "%LOGS%\ml_service.log" 2>nul
echo. > "%LOGS%\frontend.log" 2>nul

:: Create launcher scripts to avoid nested quote issues
:: --- Backend launcher ---
(
    echo @echo off
    echo cd /d "%ROOT%\backend"
    echo python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 ^> "%LOGS%\backend.log" 2^>^&1
) > "%LOGS%\_run_backend.cmd"

:: --- Celery launcher ---
(
    echo @echo off
    echo cd /d "%ROOT%\backend"
    echo celery -A app.core.celery_app worker --loglevel=info --pool=solo ^> "%LOGS%\celery.log" 2^>^&1
) > "%LOGS%\_run_celery.cmd"

:: --- ML launcher ---
(
    echo @echo off
    echo cd /d "%ROOT%\ml_service"
    echo celery -A celery_config worker --loglevel=info -Q ml_analysis,fraud_detection --pool=solo ^> "%LOGS%\ml_service.log" 2^>^&1
) > "%LOGS%\_run_ml.cmd"

:: --- Frontend launcher ---
(
    echo @echo off
    echo cd /d "%ROOT%\frontend"
    echo npm run dev ^> "%LOGS%\frontend.log" 2^>^&1
) > "%LOGS%\_run_frontend.cmd"

:: Start all services
echo   [ START] Backend - port 8000
start "ntFAST-Backend" /MIN cmd /c "%LOGS%\_run_backend.cmd"

echo   [ START] Celery Worker
start "ntFAST-Celery" /MIN cmd /c "%LOGS%\_run_celery.cmd"

echo   [ START] ML Service
start "ntFAST-ML" /MIN cmd /c "%LOGS%\_run_ml.cmd"

echo   [ START] Frontend - port 5173
start "ntFAST-Frontend" /MIN cmd /c "%LOGS%\_run_frontend.cmd"

echo.
echo   All services launching...
echo.

:: ===========================================================
:: WAIT FOR BACKEND HEALTH CHECK (real HTTP request, not just port)
:: ===========================================================

echo  ----------------------------------------------------------
echo   Waiting for backend API to respond...
echo  ----------------------------------------------------------
echo.

set "BACKEND_READY=0"
set "ATTEMPT=0"

:wait_loop
if !ATTEMPT! GEQ 40 goto :wait_done
set /a ATTEMPT+=1

:: Wait 2 seconds
ping -n 3 127.0.0.1 >nul 2>&1

:: Real HTTP health check using python
python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/health',timeout=3); exit(0) if r.status==200 else exit(1)" >nul 2>&1
if !errorlevel!==0 (
    set "BACKEND_READY=1"
    goto :wait_done
)

:: Show progress dots
<nul set /p "=."
goto :wait_loop

:wait_done
echo.

if !BACKEND_READY!==1 (
    echo   [  OK  ] Backend API is healthy!
) else (
    echo.
    echo   [ FAIL ] Backend did not respond in 80 seconds!
    echo.
    echo   === Last 20 lines of backend.log ===
    echo.
    powershell -Command "Get-Content '%LOGS%\backend.log' -Tail 20" 2>nul
    echo.
    echo   ====================================
    echo.
)

:: Wait for frontend port
echo   [ .... ] Waiting for frontend...
set "FE_READY=0"
for /L %%i in (1,1,15) do (
    if !FE_READY!==0 (
        ping -n 2 127.0.0.1 >nul 2>&1
        netstat -an | findstr ":5173 " | findstr "LISTENING" >nul 2>&1
        if !errorlevel!==0 (
            set "FE_READY=1"
        )
    )
)

if !FE_READY!==1 (
    echo   [  OK  ] Frontend is ready!
) else (
    echo   [ WARN ] Frontend still starting...
)

echo.

:: ===========================================================
:: STATUS REPORT
:: ===========================================================

set "ERRORS=0"

netstat -an | findstr ":5432 " | findstr "LISTENING" >nul 2>&1
if !errorlevel!==0 (echo   [  OK  ] PostgreSQL      port 5432) else (echo   [ FAIL ] PostgreSQL & set /a ERRORS+=1)

netstat -an | findstr ":6379 " | findstr "LISTENING" >nul 2>&1
if !errorlevel!==0 (echo   [  OK  ] Redis           port 6379) else (echo   [ FAIL ] Redis & set /a ERRORS+=1)

netstat -an | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if !errorlevel!==0 (echo   [  OK  ] Backend         port 8000) else (echo   [ FAIL ] Backend & set /a ERRORS+=1)

netstat -an | findstr ":5173 " | findstr "LISTENING" >nul 2>&1
if !errorlevel!==0 (echo   [  OK  ] Frontend        port 5173) else (echo   [ .... ] Frontend starting...)

tasklist /FI "IMAGENAME eq celery.exe" 2>nul | findstr /I "celery.exe" >nul 2>&1
if !errorlevel!==0 (echo   [  OK  ] Celery Workers  running) else (echo   [ .... ] Celery starting...)

echo.
echo  ==========================================================
echo.
echo   ntFAST is running!
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Logs dir:  %LOGS%\
echo.
echo  ==========================================================

:: Open browser ONLY when backend is actually responding
if !BACKEND_READY!==1 (
    start "" http://localhost:5173
    echo.
    echo   Browser opened.
) else (
    echo.
    echo   Browser NOT opened - backend is not healthy.
    echo   Check logs\backend.log for errors.
    echo   After fixing, open http://localhost:5173 manually.
)

echo.
echo  ==========================================================
echo   Press ANY KEY to STOP all services and exit
echo  ==========================================================
echo.
pause >nul

:: ===========================================================
:: SHUTDOWN: Kill all services
:: ===========================================================

echo.
echo   Stopping all services...

:: Kill by port
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1

:: Kill celery
taskkill /IM "celery.exe" /F >nul 2>&1

:: Kill by window title
taskkill /FI "WINDOWTITLE eq ntFAST-Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ntFAST-Frontend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ntFAST-Celery*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ntFAST-ML*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ntFAST-Redis*" /F >nul 2>&1

:: Kill remaining on our ports
ping -n 2 127.0.0.1 >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do taskkill /PID %%a /F >nul 2>&1

:: Clean up launcher scripts
del "%LOGS%\_run_backend.cmd" >nul 2>&1
del "%LOGS%\_run_celery.cmd" >nul 2>&1
del "%LOGS%\_run_ml.cmd" >nul 2>&1
del "%LOGS%\_run_frontend.cmd" >nul 2>&1

echo   [  OK  ] All services stopped
echo.
echo   Redis and PostgreSQL are still running.
echo.

endlocal
exit /b 0
