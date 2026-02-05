@echo off
echo ================================================================
echo FINAL FIX FOR PLACEHOLDER VIDEO ISSUE
echo ================================================================
echo.
echo This script will:
echo 1. Test the backend to confirm it's generating REAL videos
echo 2. Clear all caches
echo 3. Restart everything fresh
echo.
pause

echo.
echo [1/5] Testing backend download endpoint...
python test_download_endpoint.py
echo.

echo [2/5] Killing all Node processes...
taskkill /F /IM node.exe 2>nul
timeout /t 2 >nul

echo [3/5] Clearing frontend caches...
cd src\frontend
if exist "node_modules\.cache" rmdir /s /q "node_modules\.cache"
if exist "build" rmdir /s /q "build"
call npm cache clean --force 2>nul
cd ..\..

echo [4/5] Starting backend...
start "RASO Backend" cmd /k "cd /d %~dp0 && start_backend_now.bat"
timeout /t 5 >nul

echo [5/5] Starting frontend...
start "RASO Frontend" cmd /k "cd /d %~dp0src\frontend && set BROWSER=none && npm start"

echo.
echo ================================================================
echo DONE! System restarted with clean caches
echo ================================================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo CRITICAL NEXT STEPS:
echo 1. Open INCOGNITO window (Ctrl+Shift+N)
echo 2. Go to: http://localhost:3000
echo 3. Submit a NEW job
echo 4. Download the video
echo 5. Check file size (should be 8-10 MB)
echo.
echo If you STILL get placeholder:
echo - The downloaded file is less than 1 MB
echo - Then open DevTools (F12) and check Network tab
echo - Look for the POST request to see which endpoint is being called
echo.
pause
