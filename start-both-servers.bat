@echo off
echo Starting Open WebUI - Backend and Frontend
echo ==========================================

REM Kill any existing processes on our ports
echo Stopping any existing servers...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul

REM Start backend in a new window
echo Starting backend server on port 8000...
start "Open WebUI Backend" cmd /k "cd backend && py -m uvicorn open_webui.main:app --host 127.0.0.1 --port 8000"

REM Wait a moment for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Set environment variable and start frontend
echo Starting frontend server on port 5173...
set VITE_API_URL=http://localhost:8000
npm run dev

pause 