#!/usr/bin/env bash
# Daily: fetch AFDC snapshot, diff, rebuild site. Cron example (06:00 daily):
# 0 6 * * * /workspace/plugprice/run.sh >> /workspace/plugprice/data/run.log 2>&1
set -euo pipefail
cd "$(dirname "$0")"
echo "== $(date -Is)"
python3 fetch.py
python3 build.py
