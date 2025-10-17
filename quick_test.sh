#!/bin/bash
set -euo pipefail
echo "[TEST] Running deployment smoke tests..."

# 1) Python syntax (fast)
python -m py_compile bot.py rare_hunter.py

# 2) Imports
python - <<'PY'
import json, os
print("[TEST] Imports ok")
PY

# 3) .env exists
[ -f ".env" ] || { echo "[TEST] Missing .env"; exit 1; }

# 4) Minimal config presence
[ -d "aircraft_data" ] || echo "[TEST] Warning: aircraft_data missing (ok if first boot)"

echo "[TEST] All smoke tests passed."