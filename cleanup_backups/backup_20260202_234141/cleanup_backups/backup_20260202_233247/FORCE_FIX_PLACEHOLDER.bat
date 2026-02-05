@echo off
echo ========================================
echo FORCE FIX PLACEHOLDER VIDEO ISSUE
echo ========================================
echo.

echo Step 1: Stopping all Node processes...
taskkill /F /IM node.exe 2>nul
timeout /t 2 >nul

echo Step 2: Clearing npm cache...
cd src\frontend
call npm cache clean --force
cd ..\..

echo Step 3: Deleting node_modules build cache...
if exist "src\frontend\node_modules\.cache" (
    rmdir /s /q "src\frontend\node_modules\.cache"
    echo   - Deleted .cache folder
)

echo Step 4: Deleting React build folder...
if exist "src\frontend\build" (
    rmdir /s /q "src\frontend\build"
    echo   - Deleted build folder
)

echo Step 5: Starting backend on port 8000...
start "RASO Backend" cmd /k "cd /d %~dp0 && start_backend_now.bat"
timeout /t 5 >nul

echo Step 6: Starting frontend on port 3000...
start "RASO Frontend" cmd /k "cd /d %~dp0src\frontend && npm start"

echo.
echo ========================================
echo DONE!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo IMPORTANT: When browser opens, press Ctrl+Shift+R to hard refresh!
echo.
pause
