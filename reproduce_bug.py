#!/usr/bin/env python3
"""
Reproduction script for the midnight timezone bug.
"""
import datetime
import schedule
from schedule import every, run_pending
import pytz

def test_job():
    print(f"Job executed at {datetime.datetime.now()}")

def main():
    print("Testing midnight timezone bug...")

    # Clear any existing jobs
    schedule.clear()

    # Schedule a job for midnight Berlin time
    job = every().day.at("00:00", "Europe/Berlin").do(test_job)

    # Get current time in Berlin
    berlin_tz = pytz.timezone("Europe/Berlin")
    now_berlin = datetime.datetime.now(berlin_tz)
    print(f"Current time in Berlin: {now_berlin}")

    # Check the job's next run time
    print(f"Job next run: {job.next_run}")
    print(f"Job should run: {job.should_run}")

    # First call to run_pending - this should NOT execute the job if it's past midnight
    print("\nCalling run_pending()...")
    run_pending()

    print(f"After run_pending - Job next run: {job.next_run}")
    print(f"After run_pending - Job should run: {job.should_run}")

if __name__ == "__main__":
    main()
