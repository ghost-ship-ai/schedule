#!/usr/bin/env python3
"""
Test script to reproduce the DST fall-back bug.

This script demonstrates the issue where jobs scheduled with timezone-aware .at() times
can stop running entirely when DST ends and clocks fall back.
"""

import datetime
import schedule
import pytz
import os
import time


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


def test_dst_fallback_bug():
    """
    Test that reproduces the DST fall-back bug.

    When DST ends and clocks fall back, a job scheduled at an ambiguous time
    (e.g., 2:30 AM which occurs twice) should continue to be scheduled correctly
    and not get stuck.
    """
    print("Testing DST fall-back bug...")

    def mock_job():
        print("Job executed!")
        return "job_executed"

    # Clear any existing jobs
    schedule.clear()

    # Test scenario: October 29, 2023 - DST ends in Europe/Berlin
    # At 3:00 AM CEST, clocks fall back to 2:00 AM CET
    # This means 2:30 AM occurs twice

    # Simulate being at 1:30 AM on October 29, 2023 (before the transition)
    with mock_datetime(2023, 10, 29, 1, 30, zone="Europe/Berlin"):
        # Schedule a job to run at 2:30 AM Berlin time
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

        print(f"Job scheduled: {job}")
        print(f"Current time: {datetime.datetime.now()}")
        print(f"Next run: {job.next_run}")
        print(f"Next run hour: {job.next_run.hour}")
        print(f"Next run minute: {job.next_run.minute}")
        print(f"Next run day: {job.next_run.day}")

        # Debug: Let's see what timezone the job thinks it's in
        print(f"Job at_time_zone: {job.at_time_zone}")
        print(f"Job at_time: {job.at_time}")

        # The job should be scheduled to run at 2:30 AM (first occurrence)
        if job.next_run.hour != 2 or job.next_run.minute != 30 or job.next_run.day != 29:
            print(f"❌ Unexpected scheduling: Expected 2023-10-29 02:30, got {job.next_run}")
            return False

        print("✓ Job correctly scheduled for first occurrence of 2:30 AM")

    # Simulate running the job at the first occurrence of 2:30 AM
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=0):
        print(f"\nCurrent time: {datetime.datetime.now()} (first occurrence)")

        # Run the job
        result = job.run()
        print(f"Job run result: {result}")

        # Check what the next run is scheduled for
        print(f"Next run after execution: {job.next_run}")

        # The next run should be scheduled for the next day at 2:30 AM
        # NOT for the second occurrence of 2:30 AM on the same day
        expected_next_day = datetime.datetime(2023, 10, 30, 2, 30)

        if job.next_run.day == 29:
            print("❌ BUG: Job is scheduled for the second occurrence on the same day!")
            print(f"   Expected: {expected_next_day}")
            print(f"   Actual: {job.next_run}")
            return False
        elif job.next_run.day == 30:
            print("✓ Job correctly scheduled for next day")
            return True
        else:
            print(f"❌ UNEXPECTED: Job scheduled for day {job.next_run.day}")
            return False


def test_dst_fallback_continuous_scheduling():
    """
    Test that the scheduler continues to work correctly across multiple DST transitions.
    """
    print("\nTesting continuous scheduling across DST transition...")

    def mock_job():
        return "job_executed"

    schedule.clear()
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

    # Start a few days before DST transition
    test_dates = [
        (2023, 10, 27, 2, 30),  # Normal day
        (2023, 10, 28, 2, 30),  # Day before DST transition
        (2023, 10, 29, 2, 30),  # DST transition day (first occurrence)
        (2023, 10, 30, 2, 30),  # Day after DST transition
    ]

    for i, (year, month, day, hour, minute) in enumerate(test_dates):
        with mock_datetime(year, month, day, hour, minute, zone="Europe/Berlin"):
            print(f"Day {i+1}: {datetime.datetime.now()}")

            # Run the job
            job.run()

            # Check next run
            next_run = job.next_run
            print(f"  Next run: {next_run}")

            # Verify next run is scheduled for the next day
            expected_next_day = day + 1
            if day == 31:  # Handle month boundary
                expected_next_day = 1

            if next_run.day != expected_next_day:
                print(f"❌ BUG: Expected next run on day {expected_next_day}, got {next_run.day}")
                return False

    print("✓ Continuous scheduling works correctly")
    return True


if __name__ == "__main__":
    print("Testing DST fall-back bug in schedule library")
    print("=" * 50)

    try:
        success1 = test_dst_fallback_bug()
        success2 = test_dst_fallback_continuous_scheduling()

        if success1 and success2:
            print("\n✓ All tests passed - no bug detected")
        else:
            print("\n❌ Bug detected!")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
