#!/usr/bin/env python3
"""Scheduler to run the Reddit bot at a specific time each day."""

import schedule
import time
import subprocess
import sys
from datetime import datetime

RUN_TIME = "06:00"  # Daily at 6:00 AM UTC

def run_bot():
    """Run the Reddit bot."""
    print(f"[{datetime.now()}] Starting scheduled bot run...")
    try:
        subprocess.run([sys.executable, "bot.py"], check=True)
        print(f"[{datetime.now()}] Bot run completed.")
    except Exception as e:
        print(f"[{datetime.now()}] Bot run failed: {e}")

def main():
    print(f"Scheduler started. Bot will run daily at {RUN_TIME}")
    schedule.every().day.at(RUN_TIME).do(run_bot)

    # Run immediately on start (optional - comment out if not wanted)
    # run_bot()

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()