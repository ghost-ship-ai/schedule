#!/usr/bin/env python3
"""
Test to reproduce the DST fall-back bug where jobs stop running entirely.
This test demonstrates the issue described in the feedback.
"""

import datetime
import schedule
import time
import os

# Set timezone to Europe/Berlin for testing
TZ_BERLIN = "CET-1CEST,M3.5.0,M10.5.0/3"
os.environ["TZ"] = TZ_BERLIN
time.tzset()

def test_job():
    print(f"Job ran at {datetime.datetime.now()}")
    return "job_executed"

class mock_datetime:
    """
    Monkey-patch datetime for predictable results
    """

    def __init__(self, year, month, day, hour, minute, second=0, zone=None, fold=0):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.zone = zone
        self.fold = fold
        self.original_datetime = None
        self.original_zone = None

    def __enter__(self):
        class MockDate(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                mock_date = datetime.datetime(
                    self.year,
                    self.month,
                    self.day,
                    self.hour,
                    self.minute,
                    self.second,
                    fold=self.fold,
                )
                if tz:
                    return mock_date.astimezone(tz)
                return mock_date

        self.original_datetime = datetime.datetime
        datetime.datetime = MockDate

        if self.zone:
            self.original_zone = os.environ.get("TZ")
            os.environ["TZ"] = self.zone
            time.tzset()

        return self

    def __exit__(self, *args):
        datetime.datetime = self.original_datetime
        if self.zone and self.original_zone:
            os.environ["TZ"] = self.original_zone
            time.tzset()

def test_dst_fallback_bug():
    """
    Test that reproduces the DST fall-back bug.

    When clocks fall back from 3:00 to 2:00 on the last Sunday of October,
    jobs scheduled at times like 2:30 AM should continue running properly.
    """
    try:
        import pytz
    except ImportError:
        print("pytz not available, skipping test")
        return

    schedule.clear()

    # Schedule a job at 2:30 AM in Europe/Berlin timezone
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(test_job)

    # First, let's see what happens on a normal day
    print("=== Testing normal day (before DST transition) ===")
    with mock_datetime(2023, 10, 28, 1, 0):  # Oct 28, 1:00 AM
        job._schedule_next_run()
        print(f"Normal day - Next run: {job.next_run}")

    # Now test during DST fall-back
    print("\n=== Testing DST fall-back day (October 29, 2023) ===")

    # Start at 1:30 AM on Oct 29 (before the transition)
    with mock_datetime(2023, 10, 29, 1, 30):
        job._schedule_next_run()
        print(f"Before transition (1:30 AM) - Next run: {job.next_run}")
        first_next_run = job.next_run

    # Simulate the job running at 2:30 AM (first occurrence, during DST)
    if first_next_run:
        print(f"Job would run at: {first_next_run}")

        # Simulate time advancing to after the job runs (2:31 AM, first occurrence)
        # This is during the fold period where 2:30 exists twice
        with mock_datetime(2023, 10, 29, 2, 31, fold=0):  # First occurrence (DST time)
            job.last_run = first_next_run
            job._schedule_next_run()
            print(f"After first job run (fold=0) - Next scheduled run: {job.next_run}")
            second_next_run = job.next_run

        # Now simulate being in the second occurrence of the same time
        with mock_datetime(2023, 10, 29, 2, 31, fold=1):  # Second occurrence (standard time)
            job.last_run = first_next_run
            job._schedule_next_run()
            print(f"After job run (fold=1) - Next scheduled run: {job.next_run}")

            # The bug: next_run might be None or set to a time that never comes
            if job.next_run is None:
                print("BUG DETECTED: next_run is None - job will never run again!")
            elif second_next_run and job.next_run <= second_next_run:
                print("BUG DETECTED: next_run is not advancing properly!")
            else:
                print("Job scheduling appears to work correctly")

    # Test what happens when we start from the second occurrence
    print("\n=== Testing starting from second occurrence (fold=1) ===")
    with mock_datetime(2023, 10, 29, 2, 30, fold=1):  # Second occurrence
        job._schedule_next_run()
        print(f"Starting from fold=1 - Next run: {job.next_run}")

        if job.next_run:
            # Check if it's scheduled for the next day properly
            expected_next_day = datetime.datetime(2023, 10, 30, 2, 30)
            if job.next_run.day == expected_next_day.day:
                print("SUCCESS: Job correctly scheduled for next day")
            else:
                print(f"POTENTIAL BUG: Job scheduled for {job.next_run}, expected around {expected_next_day}")

if __name__ == "__main__":
    test_dst_fallback_bug()
