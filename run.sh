#!/bin/bash
# Wrapper for cron — runs the daily admin snapshot job.
cd "$(dirname "$0")"
source .venv/bin/activate
python admin_snapshot.py >> cron.log 2>&1
