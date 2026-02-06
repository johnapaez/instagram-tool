#!/usr/bin/env pwsh
# Kill All Processes Script
# Stops backend, clears queue, and kills all Chrome instances

Write-Host "Clearing Unfollow Queue and Killing Processes..." -ForegroundColor Yellow
Write-Host ""

# Try to clear the queue (if backend is running)
Write-Host "Attempting to clear unfollow queue..." -ForegroundColor Cyan
try {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/queue/clear" -Method Post -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Queue cleared: $($result.cleared) items" -ForegroundColor Green
} catch {
    Write-Host "✗ Could not clear queue (backend may be down)" -ForegroundColor Yellow
}

Write-Host ""

# Kill Python processes
Write-Host "Stopping Python processes..." -ForegroundColor Cyan
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    $pythonProcs | Stop-Process -Force
    Write-Host "✓ Stopped $($pythonProcs.Count) Python process(es)" -ForegroundColor Green
} else {
    Write-Host "✓ No Python processes running" -ForegroundColor Green
}

# Kill uvicorn processes
Write-Host "Stopping Uvicorn processes..." -ForegroundColor Cyan
$uvicornProcs = Get-Process uvicorn -ErrorAction SilentlyContinue
if ($uvicornProcs) {
    $uvicornProcs | Stop-Process -Force
    Write-Host "✓ Stopped $($uvicornProcs.Count) Uvicorn process(es)" -ForegroundColor Green
} else {
    Write-Host "✓ No Uvicorn processes running" -ForegroundColor Green
}

# Kill Chrome processes
Write-Host "Stopping Chrome processes..." -ForegroundColor Cyan
$chromeProcs = Get-Process chrome -ErrorAction SilentlyContinue
if ($chromeProcs) {
    $chromeProcs | Stop-Process -Force
    Write-Host "✓ Stopped $($chromeProcs.Count) Chrome process(es)" -ForegroundColor Green
} else {
    Write-Host "✓ No Chrome processes running" -ForegroundColor Green
}

# Wait a moment for cleanup
Start-Sleep -Seconds 1

# Verify everything is stopped
Write-Host ""
Write-Host "Verifying cleanup..." -ForegroundColor Cyan
$remaining = Get-Process python,uvicorn,chrome -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "⚠ Warning: $($remaining.Count) process(es) still running" -ForegroundColor Yellow
    $remaining | Select-Object Id, ProcessName | Format-Table -AutoSize
} else {
    Write-Host "✓ All processes stopped successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done! You can restart with .\start-backend.ps1" -ForegroundColor Green
