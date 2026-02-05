# Instagram Follower Manager - Setup Script for Windows

Write-Host "Instagram Follower Manager - Setup Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11 or higher from https://www.python.org/" -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Check Node.js version
Write-Host "Checking Node.js version..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js 18 or higher from https://nodejs.org/" -ForegroundColor Red
    exit 1
}
Write-Host "Found: Node.js $nodeVersion" -ForegroundColor Green

Write-Host ""
Write-Host "Setting up Backend..." -ForegroundColor Cyan
Write-Host "--------------------" -ForegroundColor Cyan

# Backend setup
Set-Location backend

Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
playwright install chromium

Write-Host "Backend setup complete!" -ForegroundColor Green

Set-Location ..

Write-Host ""
Write-Host "Setting up Frontend..." -ForegroundColor Cyan
Write-Host "---------------------" -ForegroundColor Cyan

# Frontend setup
Set-Location frontend

Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

Write-Host "Frontend setup complete!" -ForegroundColor Green

Set-Location ..

Write-Host ""
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==============" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start the backend (in one terminal):" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "   uvicorn app.main:app --reload --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "2. Start the frontend (in another terminal):" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "3. Open your browser to: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: Make sure to review and update backend\.env with your settings" -ForegroundColor Cyan
Write-Host ""
