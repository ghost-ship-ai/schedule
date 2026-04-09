#!/usr/bin/env python3
"""
Test to reproduce the specific DST fall-back scheduler bug.

The bug occurs when:
1. A job is scheduled at a time that occurs twice during DST fall-back (e.g., 2:30 AM)
2. The scheduler tries to calculate the next run time while in the ambiguous period
3. The _correct_utc_offset method doesn't properly handle the fold attribute
4. This causes the scheduler to either get stuck or schedule incorrectly
"""

import datetime
import os
import time
import schedule
import pytz


class mock_datetime:
    """Mock datetime context manager"""

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
    return "Job executed!"


def test_dst_fallback_scheduling_during_ambiguous_time():
    """
    Test the specific case where scheduling happens during the ambiguous time period.

    This is the scenario that causes the bug:
    1. Current time is 2:30 AM (second occurrence, fold=1)
    2. Job is scheduled for 2:30 AM daily
    3. Scheduler tries to calculate next run time
    4. Without proper fold handling, it might get confused about which 2:30 AM to use
    """
    print("Testing DST fall-back scheduling during ambiguous time...")

    schedule.clear()

    # Schedule a job at 2:30 AM in Europe/Berlin timezone
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

    # Simulate being at 2:30 AM during the second occurrence (after clocks fall back)
    # This is the critical moment where the bug occurs
    with mock_datetime(2023, 10, 29, 2, 30, fold=1):  # Second occurrence (CET)
        print(f"Current time: {datetime.datetime.now()} (fold=1, second occurrence)")

        # Force recalculation of next run time
        # This is where the bug manifests - the scheduler gets confused
        job._schedule_next_run()

        print(f"Next run scheduled for: {job.next_run}")

        if job.next_run is None:
            print("❌ BUG DETECTED: Next run is None - scheduler stopped!")
            return False

        # Check if the next run is properly scheduled for the next day
        next_run_date = job.next_run.date()
        current_date = datetime.datetime.now().date()
        expected_next_date = current_date + datetime.timedelta(days=1)

        print(f"Current date: {current_date}")
        print(f"Next run date: {next_run_date}")
        print(f"Expected next date: {expected_next_date}")

        if next_run_date != expected_next_date:
            print(f"❌ BUG DETECTED: Next run is scheduled for {next_run_date}, but should be {expected_next_date}")
            return False

        # Additional check: ensure the time is correct (should be 2:30 AM)
        if job.next_run.hour != 2 or job.next_run.minute != 30:
            print(f"❌ BUG DETECTED: Next run time is {job.next_run.hour:02d}:{job.next_run.minute:02d}, but should be 02:30")
            return False

        print("✅ Scheduling during ambiguous time works correctly")
        return True


def test_dst_fallback_continuous_loop():
    """
    Test the scenario where the scheduler runs in a continuous loop during DST transition.

    This simulates the real-world scenario where schedule.run_pending() is called
    repeatedly during the DST transition period.
    """
    print("\nTesting continuous loop during DST transition...")

    schedule.clear()
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

    # Simulate multiple calls to run_pending during the ambiguous hour
    # This tests if the scheduler gets stuck in an infinite loop

    test_times = [
        # First occurrence of 2:30 AM (CEST)
        (2023, 10, 29, 2, 30, 0),  # fold=0 (first occurrence)
        # Second occurrence of 2:30 AM (CET)
        (2023, 10, 29, 2, 30, 1),  # fold=1 (second occurrence)
        # After the transition
        (2023, 10, 29, 2, 35, 1),  # fold=1 (after second occurrence)
    ]

    for i, (year, month, day, hour, minute, fold) in enumerate(test_times):
        with mock_datetime(year, month, day, hour, minute, fold=fold):
            print(f"\nIteration {i+1}: {datetime.datetime.now()} (fold={fold})")

            # This is what happens in a typical scheduler loop
            pending_jobs = schedule.get_jobs()
            for pending_job in pending_jobs:
                if pending_job.should_run:
                    print(f"Job should run: {pending_job.should_run}")
                    pending_job.run()
                    print(f"After run, next run: {pending_job.next_run}")

                    # Check if we're stuck (next run is in the past or same time)
                    if pending_job.next_run:
                        next_run_dt = datetime.datetime.combine(
                            pending_job.next_run.date(),
                            pending_job.next_run.time()
                        )
                        current_dt = datetime.datetime.now()

                        if next_run_dt <= current_dt:
                            print(f"❌ BUG DETECTED: Next run {next_run_dt} is not in the future (current: {current_dt})")
                            return False
                else:
                    print(f"Job should not run yet. Next run: {pending_job.next_run}")

    print("✅ Continuous loop test passed")
    return True


def test_dst_fallback_edge_cases():
    """
    Test edge cases around DST fall-back transition.
    """
    print("\nTesting DST fall-back edge cases...")

    schedule.clear()

    # Test scheduling a job exactly at the transition time (3:00 AM -> 2:00 AM)
    job1 = schedule.every().day.at("03:00", "Europe/Berlin").do(mock_job)
    job2 = schedule.every().day.at("02:00", "Europe/Berlin").do(mock_job)

    # Test at the exact moment of transition
    with mock_datetime(2023, 10, 29, 3, 0):  # This becomes 2:00 AM when clocks fall back
        print(f"At transition time: {datetime.datetime.now()}")

        for i, job in enumerate([job1, job2], 1):
            job._schedule_next_run()
            print(f"Job {i} next run: {job.next_run}")

            if job.next_run is None:
                print(f"❌ BUG DETECTED: Job {i} next run is None")
                return False

    print("✅ Edge cases test passed")
    return True


if __name__ == "__main__":
    print("Testing DST fall-back scheduler bug scenarios...\n")

    try:
        test1 = test_dst_fallback_scheduling_during_ambiguous_time()
        test2 = test_dst_fallback_continuous_loop()
        test3 = test_dst_fallback_edge_cases()

        if test1 and test2 and test3:
            print("\n✅ All DST tests passed - no bugs detected")
        else:
            print("\n❌ DST bugs detected!")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
