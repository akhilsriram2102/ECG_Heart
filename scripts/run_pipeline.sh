#!/usr/bin/env bash
# scripts/run_pipeline.sh
# Run the ETL pipeline from the project root.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Heart Disease ETL Pipeline ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Create required directories if they don't exist
mkdir -p data/processed data/reports logs

# Run pipeline
python -m etl.pipeline

echo ""
echo "Pipeline finished. Check data/processed/ and data/reports/ for outputs."
