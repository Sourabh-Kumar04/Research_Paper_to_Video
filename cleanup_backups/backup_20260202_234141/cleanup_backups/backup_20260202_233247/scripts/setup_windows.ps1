# setup_windows.ps1

Write-Host "Starting Raso Youtube Automation Setup..." -ForegroundColor Green

# 1. Check Python
$pythonVersion = python --version
if ($?) {
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Cyan
} else {
    Write-Host "Error: Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# 2. Create Virtual Environment
Write-Host "Creating Virtual Environment (.venv)..." -ForegroundColor Yellow
python -m venv .venv
if ($?) {
    Write-Host "Virtual Environment created successfully." -ForegroundColor Green
} else {
    Write-Host "Failed to create Virtual Environment." -ForegroundColor Red
    exit 1
}

# 3. Install Backend Dependencies
Write-Host "Installing Backend Dependencies..." -ForegroundColor Yellow
# Activate venv for this session just to run pip
& .\.venv\Scripts\Activate.ps1
if ($LastExitCode -ne 0) {
     # Fallback if execution policy blocks script
     Write-Host "Note: If activation failed, we use direct path to pip." -ForegroundColor Gray
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt

if ($?) {
    Write-Host "Backend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "Failed to install backend dependencies." -ForegroundColor Red
    exit 1
}

# 4. Install Frontend Dependencies
Write-Host "Installing Frontend Dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
if ($?) {
    Write-Host "Frontend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "Failed to install frontend dependencies." -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

Write-Host "Setup Complete! You can now run the project." -ForegroundColor Green
Write-Host "To run backend: .\.venv\Scripts\Activate.ps1; python backend/main.py" -ForegroundColor Cyan
Write-Host "To run frontend: cd frontend; npm run dev" -ForegroundColor Cyan
