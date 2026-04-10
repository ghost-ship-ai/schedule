#!/usr/bin/env python3
"""
Trace through the _schedule_next_run method to understand the bug.
"""
import datetime
import schedule
from schedule import every
import pytz
import sys
import os

# Add the workspace to the path to import test utilities
sys.path.insert(0, '/workspace')
from test_schedule import mock_datetime

def test_job():
    print(f"MIDNIGHT JOB EXECUTED at {datetime.datetime.now()}")
    return "job_executed"

def trace_scheduling():
    print("Tracing through _schedule_next_run method...")

    # Clear any existing jobs
    schedule.clear()

    # Test with different scenarios to find when the bug occurs
    scenarios = [
        # (current_utc_time, description)
        ((2023, 7, 15, 13, 0, 0), "15:00 Berlin time (13:00 UTC)"),
        ((2023, 7, 15, 22, 30, 0), "00:30 Berlin time next day (22:30 UTC)"),
        ((2023, 7, 15, 22, 0, 0), "00:00 Berlin time next day (22:00 UTC)"),
        ((2023, 7, 15, 21, 59, 59), "23:59:59 Berlin time (21:59:59 UTC)"),
    ]

    for utc_time, description in scenarios:
        print(f"\n{'='*60}")
        print(f"Scenario: {description}")
        print(f"{'='*60}")

        schedule.clear()

        with mock_datetime(*utc_time):
            print(f"Current time UTC: {datetime.datetime.now()}")

            # Get current time in Berlin
            berlin_tz = pytz.timezone("Europe/Berlin")
            current_berlin = datetime.datetime.now().astimezone(berlin_tz)
            print(f"Current time Berlin: {current_berlin}")

            # Create the job but don't schedule it yet
            job = schedule.Job(1, schedule.default_scheduler)
            job.unit = "days"
            job.at_time = datetime.time(0, 0)  # midnight
            job.at_time_zone = berlin_tz
            job.job_func = test_job

            print(f"\nBefore _schedule_next_run:")
            print(f"  job.next_run: {job.next_run}")

            # Call _schedule_next_run and trace what happens
            job._schedule_next_run()

            print(f"\nAfter _schedule_next_run:")
            print(f"  job.next_run: {job.next_run}")
            print(f"  job.should_run: {job.should_run}")

            # Add to scheduler and check if it runs
            schedule.default_scheduler.jobs.append(job)

            print(f"\nCalling run_pending()...")
            jobs_before = len(schedule.jobs)
            result = schedule.run_pending()
            jobs_after = len(schedule.jobs)

            if jobs_after < jobs_before:
                print(f"  BUG: Job executed immediately! (jobs: {jobs_before} -> {jobs_after})")
            else:
                print(f"  OK: Job waiting for next occurrence (jobs: {jobs_before} -> {jobs_after})")

if __name__ == "__main__":
    trace_scheduling()
