#!/usr/bin/env python3
"""
Reproduce the exact bug described in the issue.
"""
import datetime
import schedule
from schedule import every, run_pending
import pytz
import sys
import os

# Add the workspace to the path to import test utilities
sys.path.insert(0, '/workspace')
from test_schedule import mock_datetime

def test_job():
    print(f"MIDNIGHT JOB EXECUTED at {datetime.datetime.now()}")
    return "job_executed"

def reproduce_bug():
    print("Reproducing the exact midnight timezone bug...")

    # Clear any existing jobs
    schedule.clear()

    # The bug occurs when:
    # 1. We schedule a job for 00:00 in a timezone
    # 2. The current time is past 00:00 in that timezone (e.g., 15:00)
    # 3. The job executes immediately on first run_pending() call

    # Set up the scenario: Current time is 15:00 Berlin time
    # Berlin is UTC+2 in summer (July), so 15:00 Berlin = 13:00 UTC
    with mock_datetime(2023, 7, 15, 13, 0, 0):  # 13:00 UTC = 15:00 Berlin
        print(f"Current time UTC: {datetime.datetime.now()}")

        # Get current time in Berlin
        berlin_tz = pytz.timezone("Europe/Berlin")
        current_berlin = datetime.datetime.now().astimezone(berlin_tz)
        print(f"Current time Berlin: {current_berlin}")

        # Schedule a job for midnight Berlin time
        print("\nScheduling job for 00:00 Europe/Berlin...")
        job = every().day.at("00:00", "Europe/Berlin").do(test_job)

        print(f"Job next_run: {job.next_run}")
        print(f"Job should_run: {job.should_run}")

        # This is where the bug should manifest - the job should NOT run
        # because it's currently 15:00 Berlin time, and the next 00:00 is tomorrow
        print(f"\nCalling run_pending() at 15:00 Berlin time...")
        print("Expected: Job should NOT execute (should wait until tomorrow 00:00)")
        print("Bug: Job executes immediately")

        # Count jobs before
        jobs_before = len(schedule.jobs)

        # Call run_pending
        result = run_pending()

        # Count jobs after
        jobs_after = len(schedule.jobs)

        print(f"\nResult: {result}")
        print(f"Jobs before: {jobs_before}, Jobs after: {jobs_after}")

        if jobs_after < jobs_before:
            print("BUG REPRODUCED: Job was executed and removed from schedule!")
        else:
            print("No bug: Job correctly waiting for next occurrence")

        print(f"Job next_run after: {job.next_run}")
        print(f"Job should_run after: {job.should_run}")

if __name__ == "__main__":
    reproduce_bug()
