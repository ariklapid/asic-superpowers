#!/usr/bin/env bash
# Test: Bootstrap Content Caching (#1202)
# Verifies the OpenCode transform caches bootstrap content between agent steps.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Test: Bootstrap Content Caching (#1202) ==="

source "$SCRIPT_DIR/setup.sh"
trap cleanup_test_env EXIT

if ! command -v node >/dev/null 2>&1; then
    echo "  [SKIP] node not installed - skipping bootstrap cache test"
    exit 0
fi

run_present_file_check() {
    node "$SCRIPT_DIR/test-bootstrap-caching.mjs" "$SUPERPOWERS_PLUGIN_FILE" present
}

run_missing_file_check() {
    mv "$SUPERPOWERS_SKILLS_DIR/using-asic-superpowers/SKILL.md" "$TEST_HOME/using-asic-superpowers.SKILL.md.bak"

    node "$SCRIPT_DIR/test-bootstrap-caching.mjs" "$SUPERPOWERS_PLUGIN_FILE" missing
}

echo "Test 1: Caches bootstrap after the first successful transform..."
run_present_file_check
echo "  [PASS] Bootstrap content is cached while fresh message arrays still receive injection"

echo "Test 2: Caches missing SKILL.md result..."
run_missing_file_check
echo "  [PASS] Missing bootstrap file is cached and not re-probed every transform"

echo ""
echo "=== All bootstrap caching tests passed ==="
