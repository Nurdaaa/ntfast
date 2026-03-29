@echo off
echo ═══════════════════════════════════════════════
echo   ntFAST — Docker Deployment
echo ═══════════════════════════════════════════════
echo.

:: Check Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

:: Check .env.docker
if not exist ".env.docker" (
    echo [WARNING] .env.docker not found!
    echo Creating from defaults...
    copy .env.docker.example .env.docker >nul 2>&1
)

echo.
echo [1/3] Building images...
docker compose build --parallel
if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Starting services...
docker compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services!
    pause
    exit /b 1
)

echo.
echo [3/3] Waiting for health checks...
timeout /t 10 /nobreak >nul

echo.
echo ═══════════════════════════════════════════════
echo   ntFAST is running!
echo.
echo   Frontend:  http://localhost
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   Health:    http://localhost:8000/health
echo.
echo   PostgreSQL: localhost:5432
echo   Redis:      localhost:6379
echo.
echo   Stop:  docker compose down
echo   Logs:  docker compose logs -f
echo ═══════════════════════════════════════════════
echo.

docker compose ps
pause
