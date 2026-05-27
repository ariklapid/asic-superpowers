#!/usr/bin/env bash
# Run a repository Python script with a modern interpreter.
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 SCRIPT [ARGS...]" >&2
  exit 2
fi

MIN_VERSION="3.7"

if [ -n "${PYTHON:-}" ]; then
  candidates=("$PYTHON")
else
  candidates=(python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3)
fi

for candidate in "${candidates[@]}"; do
  if ! command -v "$candidate" >/dev/null 2>&1; then
    continue
  fi

  if "$candidate" - "$MIN_VERSION" >/dev/null 2>&1 <<'PY'
import sys

minimum = tuple(int(part) for part in sys.argv[1].split("."))
raise SystemExit(0 if sys.version_info[:2] >= minimum else 1)
PY
  then
    exec "$candidate" "$@"
  fi
done

echo "ERROR: ASIC Superpowers validation requires Python ${MIN_VERSION}+." >&2
echo "Set PYTHON=/path/to/python3.11 or install python3.11/python3.10/python3.9/python3.8/python3.7." >&2
exit 1
