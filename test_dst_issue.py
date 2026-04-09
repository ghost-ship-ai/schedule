#!/usr/bin/env python3
"""
Test script to reproduce the DST fall-back scheduler bug.

This script demonstrates the issue where jobs scheduled with timezone-aware .at() times
can stop running entirely when DST ends and clocks fall back.
"""

import datetime
import os
import time
import schedule
import pytz


class mock_datetime:
    """Mock datetime context manager similar to the one in test_schedule.py"""

    def __init__(self, year, month, day, hour=0, minute=0, second=0, zone=None, fold=0):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.zone = zone
        self.fold = fold

    def __enter__(self):
        class MockDate(datetime.datetime):
            @classmethod
            def today(cls):
                return cls(self.year, self.month, self.day)

            @classmethod
            def now(cls, tz=None):
                mock_date = cls(
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

        self.original_zone = os.environ.get("TZ")
        if self.zone:
            os.environ["TZ"] = self.zone
            time.tzset()

        return MockDate(
            self.year, self.month, self.day, self.hour, self.minute, self.second
        )

    def __exit__(self, *args, **kwargs):
        datetime.datetime = self.original_datetime
        if self.original_zone:
            os.environ["TZ"] = self.original_zone
        elif "TZ" in os.environ:
            del os.environ["TZ"]
        time.tzset()


def mock_job():
    """A simple mock job function."""
    print("Job executed!")


def test_dst_fallback_issue():
    """
    Test that reproduces the DST fall-back issue.

    When clocks fall back from 3:00 to 2:00 on the last Sunday of October,
    a job scheduled at 2:30 AM should continue to run properly and not get stuck.
    """
    print("Testing DST fall-back issue...")

    # Clear any existing jobs
    schedule.clear()

    # Schedule a job at 2:30 AM in Europe/Berlin timezone
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

    # Simulate the time during DST fall-back transition
    # On October 29, 2023, clocks fall back from 3:00 to 2:00 in Europe/Berlin
    # This means 2:30 AM occurs twice - once in CEST and once in CET

    # Test case: After the job runs in the first occurrence, simulate being in the second occurrence
    with mock_datetime(2023, 10, 29, 2, 35, fold=1):  # Second occurrence (CET)
        print(f"Current time (second 2:35 AM): {datetime.datetime.now()}")

        # Simulate running the job
        job.run()

        print(f"Job next run after execution: {job.next_run}")

        # The job should be scheduled for the next day, not stuck in the same day
        # This is where the bug occurs - the scheduler might get stuck
        if job.next_run is None:
            print("BUG DETECTED: Next run is None - scheduler stopped!")
            return False

        next_run_date = job.next_run.date()
        current_date = datetime.datetime.now().date()

        print(f"Current date: {current_date}")
        print(f"Next run date: {next_run_date}")

        # The next run should be on the next day (October 30)
        expected_next_date = current_date + datetime.timedelta(days=1)

        if next_run_date != expected_next_date:
            print(f"BUG DETECTED: Next run is scheduled for {next_run_date}, but should be {expected_next_date}")
            print("The scheduler appears to be stuck due to DST fall-back transition!")
            return False
        else:
            print("Scheduler correctly advanced to next day")
            return True


def test_dst_fallback_continuous():
    """
    Test continuous scheduling through DST transition.
    """
    print("\nTesting continuous scheduling through DST transition...")

    schedule.clear()
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

    # Test multiple days around the DST transition
    test_dates = [
        (2023, 10, 28),  # Day before DST transition
        (2023, 10, 29),  # DST transition day
        (2023, 10, 30),  # Day after DST transition
    ]

    for year, month, day in test_dates:
        with mock_datetime(year, month, day, 3, 0):  # 3:00 AM (after 2:30)
            print(f"\nTesting date: {year}-{month:02d}-{day:02d}")
            print(f"Current time: {datetime.datetime.now()}")

            # Run the job
            job.run()

            print(f"Next run scheduled for: {job.next_run}")

            # Check if next run is properly scheduled
            if job.next_run is None:
                print("BUG: Next run is None - scheduler stopped!")
                return False

            # Check if we're progressing properly
            next_run_date = job.next_run.date()
            expected_next_date = datetime.date(year, month, day) + datetime.timedelta(days=1)

            if next_run_date != expected_next_date:
                print(f"BUG: Next run is {next_run_date}, expected {expected_next_date}")
                return False

    print("Continuous scheduling test passed")
    return True


if __name__ == "__main__":
    print("Reproducing DST fall-back scheduler bug...\n")

    try:
        result1 = test_dst_fallback_issue()
        result2 = test_dst_fallback_continuous()

        if result1 and result2:
            print("\n✅ All tests passed - no DST bug detected")
        else:
            print("\n❌ DST bug reproduced successfully")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
