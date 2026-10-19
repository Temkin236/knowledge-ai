#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "Knowledge AI — Full Test Suite & Evaluation Runner"
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -d "/home/temkin/.local/share/mise/installs/node/26.8.2/bin" ]; then
    export PATH="/home/temkin/.local/share/mise/installs/node/26.8.2/bin:$PATH"
fi

echo ""
echo "[1/3] Running Backend Pytest Suite..."
cd "${ROOT_DIR}/backend"
"${ROOT_DIR}/backend/.venv/bin/pytest" tests/ -v

echo ""
echo "[2/3] Running Frontend Vitest Suite..."
cd "${ROOT_DIR}/frontend"
npm test

echo ""
echo "[3/3] Running RAG Quality & Grounding Benchmark..."
cd "${ROOT_DIR}"
"${ROOT_DIR}/backend/.venv/bin/python" scripts/evaluate_rag.py

echo ""
echo "=========================================================="
echo "ALL TESTS & EVALUATIONS PASSED SUCCESSFULLY!"
echo "=========================================================="
