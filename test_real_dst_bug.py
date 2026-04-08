#!/usr/bin/env python3
"""
Test to reproduce the real DST fall-back bug.

The issue occurs when a job is scheduled during the DST overlap period.
"""

import datetime
import os
import time
import schedule
import pytz


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


def test_dst_bug_scenario_1():
    """
    Test scenario 1: Job created during the first occurrence of 2:30,
    then check what happens at the second occurrence.
    """

    def mock_job():
        return "executed"

    schedule.clear()

    print("=== Scenario 1: Job created at first 2:30 occurrence ===")

    # Create job at the first occurrence of 2:30 (CEST)
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=0):
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)
        print(f"Job created at: {datetime.datetime.now()}")
        print(f"Next run: {job.next_run}")
        print(f"Should run: {job.should_run}")

        # Run the job
        if job.should_run:
            job.run()
            print(f"After run - Next run: {job.next_run}")

    # Check at the second occurrence of 2:30 (CET)
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=1):
        print(f"\nAt second 2:30 occurrence: {datetime.datetime.now()}")
        print(f"Next run: {job.next_run}")
        print(f"Should run: {job.should_run}")

        if job.should_run:
            print("ERROR: Job should not run again!")
        else:
            print("Correct: Job should not run")

    schedule.clear()


def test_dst_bug_scenario_2():
    """
    Test scenario 2: Job created before DST transition,
    then simulate what happens during the overlap.
    """

    def mock_job():
        return "executed"

    schedule.clear()

    print("\n=== Scenario 2: Job created before DST transition ===")

    # Create job before DST transition
    with mock_datetime(2023, 10, 29, 1, 0, zone="Europe/Berlin"):
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)
        print(f"Job created at: {datetime.datetime.now()}")
        print(f"Next run: {job.next_run}")

    # Simulate run_pending() being called at different times
    test_times = [
        (2023, 10, 29, 2, 30, 0, "First 2:30 (CEST)"),
        (2023, 10, 29, 2, 30, 1, "Second 2:30 (CET)"),
    ]

    for year, month, day, hour, minute, fold, description in test_times:
        with mock_datetime(year, month, day, hour, minute, zone="Europe/Berlin", fold=fold):
            current = datetime.datetime.now()
            print(f"\n{description}: {current}")
            print(f"  Next run: {job.next_run}")
            print(f"  Should run: {job.should_run}")

            if job.should_run:
                print(f"  Running job...")
                job.run()
                print(f"  After run - Next run: {job.next_run}")

    schedule.clear()


def test_dst_bug_scenario_3():
    """
    Test scenario 3: The problematic case where _correct_utc_offset
    might not handle the fold attribute correctly.
    """

    def mock_job():
        return "executed"

    schedule.clear()

    print("\n=== Scenario 3: Testing _correct_utc_offset with fold ===")

    # Create a job
    with mock_datetime(2023, 10, 29, 1, 0, zone="Europe/Berlin"):
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

    # Test _correct_utc_offset with different fold values
    berlin_tz = pytz.timezone("Europe/Berlin")

    # Create a time during the overlap with fold=0 (first occurrence)
    overlap_time_1 = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=True)
    print(f"Overlap time 1 (CEST): {overlap_time_1}")

    # Create a time during the overlap with fold=1 (second occurrence)
    overlap_time_2 = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=False)
    print(f"Overlap time 2 (CET): {overlap_time_2}")

    # Test what _correct_utc_offset does with these times
    corrected_1 = job._correct_utc_offset(overlap_time_1, fixate_time=True)
    corrected_2 = job._correct_utc_offset(overlap_time_2, fixate_time=True)

    print(f"Corrected 1: {corrected_1}")
    print(f"Corrected 2: {corrected_2}")

    # The issue might be that _correct_utc_offset doesn't preserve the fold information

    schedule.clear()


def test_fold_attribute_issue():
    """
    Test if the fold attribute is properly handled.
    """

    print("\n=== Testing fold attribute handling ===")

    berlin_tz = pytz.timezone("Europe/Berlin")

    # Create datetime objects with different fold values
    dt1 = datetime.datetime(2023, 10, 29, 2, 30, fold=0)
    dt2 = datetime.datetime(2023, 10, 29, 2, 30, fold=1)

    print(f"dt1 (fold=0): {dt1}, fold={dt1.fold}")
    print(f"dt2 (fold=1): {dt2}, fold={dt2.fold}")

    # Localize them
    tz_dt1 = berlin_tz.localize(dt1, is_dst=True)
    tz_dt2 = berlin_tz.localize(dt2, is_dst=False)

    print(f"tz_dt1 (CEST): {tz_dt1}")
    print(f"tz_dt2 (CET): {tz_dt2}")

    # Convert to naive
    naive_dt1 = tz_dt1.astimezone().replace(tzinfo=None)
    naive_dt2 = tz_dt2.astimezone().replace(tzinfo=None)

    print(f"naive_dt1: {naive_dt1}")
    print(f"naive_dt2: {naive_dt2}")

    # Check if fold is preserved
    print(f"naive_dt1.fold: {getattr(naive_dt1, 'fold', 'N/A')}")
    print(f"naive_dt2.fold: {getattr(naive_dt2, 'fold', 'N/A')}")


if __name__ == "__main__":
    test_dst_bug_scenario_1()
    test_dst_bug_scenario_2()
    test_dst_bug_scenario_3()
    test_fold_attribute_issue()
