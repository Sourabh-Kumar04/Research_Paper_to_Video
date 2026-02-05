@echo off
echo ============================================================
echo Starting RASO Backend on Port 8000
echo ============================================================
echo.

cd src\backend

echo Setting PORT environment variable to 8000...
set PORT=8000

echo Installing dependencies...
call npm install

echo.
echo Starting backend server...
echo Backend will be available at: http://localhost:8000
echo.

call npm run dev

pause
