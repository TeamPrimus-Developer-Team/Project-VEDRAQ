#!/bin/bash
# ═══════════════════════════════════════════════════════
# VEDRAQ — Humanitarian Intelligence Platform (macOS)
# ═══════════════════════════════════════════════════════

cd "$(dirname "$0")"

echo ""
echo "  ===================================================="
echo "   VEDRAQ — Humanitarian Intelligence Platform"
echo "   Smart India Hackathon (macOS Launcher)"
echo "  ===================================================="
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.10+."
    exit 1
fi

# Check/Create virtual environment
if [ ! -d "backend/.venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv backend/.venv
    ./backend/.venv/bin/pip install --upgrade pip --quiet
    ./backend/.venv/bin/pip install -r backend/requirements.txt
else
    echo "[1/3] Virtual environment found: backend/.venv"
fi

echo "[2/3] Environment ready (.env configured with Groq AI)"
echo "[3/3] Starting VEDRAQ server..."
echo ""
echo "  🌐 Dashboard : http://0.0.0.0:8001"
echo "  📖 API Docs  : http://0.0.0.0:8001/docs"
echo "  ⏹  Press Ctrl+C to stop"
echo ""

export PYTHONPATH=backend
exec ./backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload --app-dir backend
