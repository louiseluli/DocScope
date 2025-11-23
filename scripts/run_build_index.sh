#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "[run_build_index] Building embeddings index..."
python -m src.indexing.build_embeddings_index
