#!/usr/bin/env bash
set -e

# Ajuste se usar outro ambiente
cd "$(dirname "$0")/.."

echo "[run_build_corpus] Activating venv (if any) and building corpus..."

# Se estiver usando venv:
# source .venv/bin/activate

python -m src.ingest.build_corpus
