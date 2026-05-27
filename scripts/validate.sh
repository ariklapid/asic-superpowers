#!/usr/bin/env bash
# Run deterministic repository validation without requiring npm.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"$SCRIPT_DIR/run-python.sh" "$SCRIPT_DIR/check_skill_contracts.py"
"$SCRIPT_DIR/run-python.sh" "$SCRIPT_DIR/check_links.py"
"$SCRIPT_DIR/run-python.sh" "$SCRIPT_DIR/check_trigger_metadata.py"
"$SCRIPT_DIR/run-python.sh" "$SCRIPT_DIR/run_asic_evals.py"
