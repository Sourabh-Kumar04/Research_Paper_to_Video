# Start RASO Backend on Port 8000
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting RASO Backend on Port 8000" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location src\backend

Write-Host "Setting PORT environment variable to 8000..." -ForegroundColor Yellow
$env:PORT = "8000"

Write-Host "Starting backend server..." -ForegroundColor Yellow
Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host ""

npm run dev
