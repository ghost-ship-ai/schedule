#!/usr/bin/env python3
"""
Reproduction script for the weekly job interval > 1 issue.
This demonstrates the current bug where multi-week intervals fail.
"""

import schedule
import datetime

def job():
    print("job executed")

# This should work but currently raises an IntervalError
try:
    schedule.every(2).weeks.monday.at("10:00").do(job)
    print("SUCCESS: Multi-week scheduling worked!")

    # Check the next run time
    for job in schedule.get_jobs():
        print(f"Next run: {job.next_run}")

except Exception as e:
    print(f"ERROR: {e}")
    print("This demonstrates the current limitation.")

# Clear for next test
schedule.clear()

# Test single week (should work)
try:
    schedule.every().monday.at("10:00").do(job)
    print("SUCCESS: Single week scheduling works")

    for job in schedule.get_jobs():
        print(f"Next run: {job.next_run}")

except Exception as e:
    print(f"ERROR with single week: {e}")
