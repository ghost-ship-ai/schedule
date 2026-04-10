#!/usr/bin/env python3
"""
Test script to reproduce the midnight timezone bug by mocking the current time.
"""
import datetime
import schedule
from schedule import every, run_pending
import pytz
from unittest.mock import patch

def test_job():
    print(f"Job executed at {datetime.datetime.now()}")
    return "job_executed"

def test_midnight_bug():
    print("Testing midnight timezone bug with mocked time...")

    # Clear any existing jobs
    schedule.clear()

    # Mock the current time to be 15:00 Berlin time
    berlin_tz = pytz.timezone("Europe/Berlin")
    mock_time = berlin_tz.localize(datetime.datetime(2026, 4, 10, 15, 0, 0))  # 3 PM Berlin time

    print(f"Mocked current time in Berlin: {mock_time}")

    # Patch datetime.now to return our mock time
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_time
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # Schedule a job for midnight Berlin time
        job = every().day.at("00:00", "Europe/Berlin").do(test_job)

        print(f"Job next run: {job.next_run}")
        print(f"Job should run: {job.should_run}")

        # First call to run_pending - this should NOT execute the job
        print("\nCalling run_pending()...")
        result = run_pending()

        print(f"After run_pending - Job next run: {job.next_run}")
        print(f"After run_pending - Job should run: {job.should_run}")

if __name__ == "__main__":
    test_midnight_bug()
