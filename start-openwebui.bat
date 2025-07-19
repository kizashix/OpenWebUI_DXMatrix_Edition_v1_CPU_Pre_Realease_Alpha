@echo off
setlocal enabledelayedexpansion

REM Open WebUI Startup Script for Windows (Batch Version)
REM This script starts both backend and frontend servers

echo.
echo ========================================
echo    Open WebUI Startup Script
echo ========================================
echo.

REM Set default ports
set BACKEND_PORT=8080
set FRONTEND_PORT=5173

REM Check if ports are provided as arguments
if not "%1"=="" set BACKEND_PORT=%1
if not "%2"=="" set FRONTEND_PORT=%2

echo Backend port: %BACKEND_PORT%
echo Frontend port: %FRONTEND_PORT%
echo.

REM Check if we're in the right directory
if not exist "backend" (
    echo ERROR: Backend directory not found. Are you in the correct Open WebUI directory?
    pause
    exit /b 1
)

if not exist "package.json" (
    echo ERROR: package.json not found. Are you in the correct Open WebUI directory?
    pause
    exit /b 1
)

REM Check if Python is available
echo Checking Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ from python.org
    pause
    exit /b 1
) else (
    echo ✓ Python found
)

REM Check if Node.js is available
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 18+ from nodejs.org
    pause
    exit /b 1
) else (
    echo ✓ Node.js found
)

REM Check if npm is available
echo Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found
    pause
    exit /b 1
) else (
    echo ✓ npm found
)

echo.
echo ========================================
echo    Starting Servers
echo ========================================
echo.

REM Kill any existing processes on the ports
echo Checking for existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%BACKEND_PORT%') do (
    echo Killing process on backend port %BACKEND_PORT% (PID: %%a)
    taskkill /f /pid %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%FRONTEND_PORT%') do (
    echo Killing process on frontend port %FRONTEND_PORT% (PID: %%a)
    taskkill /f /pid %%a >nul 2>&1
)

REM Start backend server
echo Starting backend server on port %BACKEND_PORT%...
start "Open WebUI Backend" cmd /k "cd backend && py -m uvicorn open_webui.main:app --host 127.0.0.1 --port %BACKEND_PORT% --reload"

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend server
echo Starting frontend server on port %FRONTEND_PORT%...
start "Open WebUI Frontend" cmd /k "npm run dev -- --port %FRONTEND_PORT%"

echo.
echo ========================================
echo    Open WebUI Status
echo ========================================
echo.
echo ✓ Backend: http://127.0.0.1:%BACKEND_PORT%
echo ✓ Frontend: http://localhost:%FRONTEND_PORT%
echo.

echo ========================================
echo    Next Steps
echo ========================================
echo.
echo 1. Open your browser and go to: http://localhost:%FRONTEND_PORT%
echo 2. The frontend will automatically connect to the backend
echo 3. If you see 'Backend Required' error, wait a few more seconds and refresh
echo 4. To stop the servers, close the command prompt windows
echo.

echo ========================================
echo    Troubleshooting
echo ========================================
echo.
echo • If you get 'localhost refused to connect', check Windows Firewall
echo • If you get 'Backend Required', wait a moment and refresh the page
echo • If you get port conflicts, run: start-openwebui.bat 8888 3000
echo • To stop all servers, close the command prompt windows
echo.

echo 🎉 Open WebUI should now be running! 🎉
echo.
pause 