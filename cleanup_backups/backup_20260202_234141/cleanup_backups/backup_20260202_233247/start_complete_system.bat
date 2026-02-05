@echo off
echo ============================================================
echo RASO Platform - Complete System Startup
echo ============================================================
echo.

REM Check if backend is already running
netstat -ano | findstr ":8000" >nul
if %errorlevel% == 0 (
    echo Backend is already running on port 8000
) else (
    echo Starting Backend Server...
    start "RASO Backend" cmd /k "cd src\backend && npm install && npm run dev"
    timeout /t 5 /nobreak >nul
)

REM Check if frontend is already running
netstat -ano | findstr ":3002" >nul
if %errorlevel% == 0 (
    echo Frontend is already running on port 3002
) else (
    echo Starting Frontend Server...
    start "RASO Frontend" cmd /k "cd src\frontend && set PORT=3002 && npm install && npm start"
    timeout /t 5 /nobreak >nul
)

echo.
echo ============================================================
echo System Startup Complete!
echo ============================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3002
echo Health:   http://localhost:8000/health
echo API:      http://localhost:8000/api/v1
echo.
echo Press any key to open the application in your browser...
pause >nul

start http://localhost:3002

echo.
echo System is running. Close this window to stop monitoring.
echo To stop servers, close their respective windows.
pause
