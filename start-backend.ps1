# Start Backend Server
Write-Host "Starting Instagram Manager Backend..." -ForegroundColor Cyan

Set-Location backend
.\venv\Scripts\Activate.ps1

# Use asyncio mode to allow Windows ProactorEventLoop
$env:PYTHONASYNCIODEBUG = "1"
uvicorn app.main:app --reload --port 8000 --loop asyncio
