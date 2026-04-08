#!/usr/bin/env python3
"""
Debug the time comparison issue during DST transitions.
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


def debug_time_comparison():
    """
    Debug time comparison during DST transition.
    """

    def mock_job():
        return "executed"

    schedule.clear()

    print("=== Debugging Time Comparison During DST ===")

    # Create a job and schedule it for 2:30
    with mock_datetime(2023, 10, 29, 1, 0, zone="Europe/Berlin"):
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)
        print(f"Job created. Next run: {job.next_run}")

    # Test at the first occurrence of 2:30 (CEST, fold=0)
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=0):
        current_time = datetime.datetime.now()
        next_run = job.next_run

        print(f"\nFirst 2:30 occurrence (CEST):")
        print(f"  Current time: {current_time}")
        print(f"  Next run: {next_run}")
        print(f"  current_time >= next_run: {current_time >= next_run}")
        print(f"  Should run: {job.should_run}")

        # Run the job
        job.run()
        print(f"  After running - Next run: {job.next_run}")

    # Test at the second occurrence of 2:30 (CET, fold=1)
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=1):
        current_time = datetime.datetime.now()
        next_run = job.next_run

        print(f"\nSecond 2:30 occurrence (CET):")
        print(f"  Current time: {current_time}")
        print(f"  Next run: {next_run}")
        print(f"  current_time >= next_run: {current_time >= next_run}")
        print(f"  Should run: {job.should_run}")

    # Test what happens if we create a new job at the second occurrence
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=1):
        job2 = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)
        current_time = datetime.datetime.now()
        next_run = job2.next_run

        print(f"\nNew job at second 2:30 occurrence (CET):")
        print(f"  Current time: {current_time}")
        print(f"  Next run: {next_run}")
        print(f"  current_time >= next_run: {current_time >= next_run}")
        print(f"  Should run: {job2.should_run}")

    schedule.clear()


def debug_timezone_aware_comparison():
    """
    Debug timezone-aware time comparison.
    """

    print("\n=== Debugging Timezone-Aware Comparison ===")

    berlin_tz = pytz.timezone("Europe/Berlin")

    # Create the two occurrences of 2:30
    first_occurrence = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=True)
    second_occurrence = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=False)

    print(f"First occurrence (CEST): {first_occurrence}")
    print(f"Second occurrence (CET): {second_occurrence}")
    print(f"First == Second: {first_occurrence == second_occurrence}")
    print(f"First < Second: {first_occurrence < second_occurrence}")
    print(f"First > Second: {first_occurrence > second_occurrence}")

    # Convert to naive datetimes (like the scheduler does)
    first_naive = first_occurrence.astimezone().replace(tzinfo=None)
    second_naive = second_occurrence.astimezone().replace(tzinfo=None)

    print(f"\nNaive first: {first_naive}")
    print(f"Naive second: {second_naive}")
    print(f"Naive first == Naive second: {first_naive == second_naive}")
    print(f"Naive first < Naive second: {first_naive < second_naive}")
    print(f"Naive first > Naive second: {first_naive > second_naive}")

    # This is the problem! Both naive times are identical, so comparison doesn't work


if __name__ == "__main__":
    debug_time_comparison()
    debug_timezone_aware_comparison()
