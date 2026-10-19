#!/usr/bin/env bash
set -e

# Knowledge AI — Local Development Startup Script
echo "=========================================================="
echo "Starting Knowledge AI — Precision RAG Assistant (Local Dev)"
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Node environment path fallback if mise is present
if [ -d "/home/temkin/.local/share/mise/installs/node/26.8.2/bin" ]; then
    export PATH="/home/temkin/.local/share/mise/installs/node/26.8.2/bin:$PATH"
fi

# Ensure Python Virtualenv exists
if [ ! -d "${ROOT_DIR}/backend/.venv" ]; then
    echo "[*] Creating backend virtual environment..."
    python3 -m venv "${ROOT_DIR}/backend/.venv"
    "${ROOT_DIR}/backend/.venv/bin/python" -m ensurepip
    "${ROOT_DIR}/backend/.venv/bin/pip" install -r "${ROOT_DIR}/backend/requirements.txt"
fi

# Start Backend
echo "[*] Starting FastAPI Backend on http://localhost:8000..."
cd "${ROOT_DIR}/backend"
"${ROOT_DIR}/backend/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start Frontend
echo "[*] Starting Vite Frontend on http://localhost:5173..."
cd "${ROOT_DIR}/frontend"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "Knowledge AI is running:"
echo " -> Frontend: http://localhost:5173"
echo " -> Backend API: http://localhost:8000"
echo " -> Interactive API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to terminate both servers."

trap "kill ${BACKEND_PID} ${FRONTEND_PID} 2>/dev/null; exit 0" INT TERM
wait
