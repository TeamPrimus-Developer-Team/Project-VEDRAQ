# ================================================================
# LIFELINE — Windows 11 Start Script (PowerShell)
# Run this from inside the LIFELINE_FINAL folder
# ================================================================

Write-Host ""
Write-Host "  ██╗     ██╗███████╗███████╗██╗     ██╗███╗   ██╗███████╗" -ForegroundColor Cyan
Write-Host "  ██║     ██║██╔════╝██╔════╝██║     ██║████╗  ██║██╔════╝" -ForegroundColor Cyan
Write-Host "  ██║     ██║█████╗  █████╗  ██║     ██║██╔██╗ ██║█████╗  " -ForegroundColor Cyan
Write-Host "  ██║     ██║██╔══╝  ██╔══╝  ██║     ██║██║╚██╗██║██╔══╝  " -ForegroundColor Cyan
Write-Host "  ███████╗██║██║     ███████╗███████╗██║██║ ╚████║███████╗" -ForegroundColor Cyan
Write-Host "  ╚══════╝╚═╝╚═╝     ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Humanitarian Intelligence & Resource Optimization" -ForegroundColor White
Write-Host "  Smart India Hackathon — Demo Prototype" -ForegroundColor DarkGray
Write-Host ""

# ── Step 1: Check Python ─────────────────────────────────────────
Write-Host "[1/4] Checking Python version..." -ForegroundColor Yellow
$pyver = python --version 2>&1
Write-Host "      Found: $pyver" -ForegroundColor Green

# ── Step 2: Create venv if not exists ────────────────────────────
if (-Not (Test-Path "backend\.venv")) {
    Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv backend\.venv
    Write-Host "      Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "[2/4] Virtual environment already exists." -ForegroundColor Green
}

# ── Step 3: Install dependencies ─────────────────────────────────
Write-Host "[3/4] Installing dependencies (no Rust/Cargo needed)..." -ForegroundColor Yellow
& backend\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& backend\.venv\Scripts\pip.exe install -r backend\requirements.txt --quiet
Write-Host "      Dependencies installed." -ForegroundColor Green

# ── Step 4: Start server ──────────────────────────────────────────
Write-Host "[4/4] Starting LIFELINE server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  Dashboard → http://0.0.0.0:8001              ║" -ForegroundColor Cyan
Write-Host "  ║  API Docs  → http://0.0.0.0:8001/docs         ║" -ForegroundColor Cyan
Write-Host "  ║                                                  ║" -ForegroundColor Cyan
Write-Host "  ║  Press Ctrl+C to stop the server                ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$env:PYTHONPATH = "backend"
& backend\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001 --reload --app-dir backend
