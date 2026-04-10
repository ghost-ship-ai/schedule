#!/usr/bin/env python3
"""
Test script to reproduce the midnight timezone bug using the existing test framework.
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

def test_midnight_bug():
    print("Testing midnight timezone bug...")

    # Clear any existing jobs
    schedule.clear()

    # Mock the current time to be 15:00 UTC (which is 17:00 Berlin time in summer)
    with mock_datetime(2023, 7, 15, 15, 0, 0):  # 3 PM UTC
        print(f"Mocked current time UTC: {datetime.datetime.now()}")

        # Schedule a job for midnight Berlin time
        job = every().day.at("00:00", "Europe/Berlin").do(test_job)

        print(f"Job next run: {job.next_run}")
        print(f"Job should run: {job.should_run}")

        # First call to run_pending - this should NOT execute the job
        print("\nCalling run_pending()...")
        run_pending()

        print(f"After run_pending - Job next run: {job.next_run}")
        print(f"After run_pending - Job should run: {job.should_run}")

if __name__ == "__main__":
    test_midnight_bug()
