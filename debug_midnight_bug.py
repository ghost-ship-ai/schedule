#!/usr/bin/env python3
"""
Debug script to understand the midnight timezone bug.
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
    print(f"Job executed at {datetime.datetime.now()}")
    return "job_executed"

def debug_midnight_scheduling():
    print("Debugging midnight timezone scheduling...")

    # Clear any existing jobs
    schedule.clear()

    # Test scenario: Current time is 15:00 Berlin time (past midnight)
    # We want to schedule a job for 00:00 Berlin time
    # The job should be scheduled for TOMORROW at 00:00, not today

    # Mock the current time to be 15:00 Berlin time
    # Berlin is UTC+2 in summer, so 15:00 Berlin = 13:00 UTC
    with mock_datetime(2023, 7, 15, 13, 0, 0):  # 1 PM UTC = 3 PM Berlin
        print(f"Mocked current time UTC: {datetime.datetime.now()}")

        # Get current time in Berlin timezone
        berlin_tz = pytz.timezone("Europe/Berlin")
        current_berlin = datetime.datetime.now().astimezone(berlin_tz)
        print(f"Current time in Berlin: {current_berlin}")

        # Schedule a job for midnight Berlin time
        job = every().day.at("00:00", "Europe/Berlin").do(test_job)

        print(f"Job next run (local): {job.next_run}")
        print(f"Job should run: {job.should_run}")

        # Convert next_run to Berlin time to see what it actually is
        if job.next_run:
            # job.next_run is naive local time, convert to Berlin time for comparison
            local_tz = pytz.timezone('Europe/Berlin')  # Assuming we're in Berlin timezone
            next_run_berlin = local_tz.localize(job.next_run)
            print(f"Job next run in Berlin: {next_run_berlin}")

        # Check if the job thinks it should run immediately
        print(f"\nBefore run_pending:")
        print(f"  should_run: {job.should_run}")

        # Call run_pending to see if it executes
        print("\nCalling run_pending()...")
        executed_jobs = run_pending()
        print(f"Executed jobs: {executed_jobs}")

        print(f"\nAfter run_pending:")
        print(f"  Job next run: {job.next_run}")
        print(f"  Job should run: {job.should_run}")

if __name__ == "__main__":
    debug_midnight_scheduling()
