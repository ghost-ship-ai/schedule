#!/usr/bin/env python3
"""
Test to examine potential timezone comparison issues in should_run.
"""

import schedule
import datetime
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
            time.tzset()

def test_timezone_comparison_issue():
    """
    Test if there's a timezone comparison issue in should_run.
    """

    schedule.clear()

    print("=== Testing timezone comparison in should_run ===")

    # Test with different local timezone settings
    test_scenarios = [
        ("UTC", "UTC timezone"),
        ("US/Eastern", "US Eastern timezone"),
        ("Asia/Tokyo", "Tokyo timezone"),
        ("Europe/London", "London timezone"),
    ]

    for tz_setting, description in test_scenarios:
        print(f"\n--- Testing with {description} ---")

        # Set local timezone
        original_tz = os.environ.get("TZ")
        os.environ["TZ"] = tz_setting
        time.tzset()

        try:
            # Mock current time to be 15:00 local time
            with mock_datetime(2024, 4, 8, 15, 0, 0):
                print(f"Local timezone: {tz_setting}")
                print(f"Current local time: {datetime.datetime.now()}")

                # Schedule a job for midnight Berlin time
                job = schedule.every().day.at("00:00", "Europe/Berlin").do(lambda: print("job"))

                print(f"Job next_run: {job.next_run}")
                print(f"Job next_run type: {type(job.next_run)}")
                print(f"Job next_run tzinfo: {getattr(job.next_run, 'tzinfo', 'No tzinfo')}")

                # Check the comparison values
                now = datetime.datetime.now()
                print(f"datetime.datetime.now(): {now}")
                print(f"datetime.datetime.now() type: {type(now)}")
                print(f"datetime.datetime.now() tzinfo: {getattr(now, 'tzinfo', 'No tzinfo')}")

                print(f"Comparison (now >= next_run): {now >= job.next_run}")
                print(f"should_run: {job.should_run}")

                # This could reveal the bug if timezone-naive vs timezone-aware comparison is problematic

        finally:
            # Restore original timezone
            if original_tz:
                os.environ["TZ"] = original_tz
            else:
                os.environ.pop("TZ", None)
            time.tzset()

def test_potential_edge_case():
    """
    Test a potential edge case where timezone conversion might cause issues.
    """

    schedule.clear()

    print("\n=== Testing potential edge case ===")

    # Set local timezone to something far from Berlin
    original_tz = os.environ.get("TZ")
    os.environ["TZ"] = "Pacific/Auckland"  # UTC+12/+13
    time.tzset()

    try:
        # Mock current time to be a time that might cause confusion
        # Let's say it's 11:00 AM in Auckland on April 9th
        # This would be 23:00 (11 PM) on April 8th in Berlin
        with mock_datetime(2024, 4, 9, 11, 0, 0):
            print(f"Current Auckland time: {datetime.datetime.now()}")

            # Schedule a job for midnight Berlin time
            job = schedule.every().day.at("00:00", "Europe/Berlin").do(lambda: print("job"))

            print(f"Job next_run: {job.next_run}")
            print(f"should_run: {job.should_run}")

            # In this scenario, midnight Berlin time on April 9th would be
            # 10:00 AM Auckland time on April 9th
            # Since it's currently 11:00 AM Auckland time, the job should run

            if job.should_run:
                print("WARNING: Job thinks it should run immediately!")
                print("This might be the bug we're looking for.")
            else:
                print("Job correctly scheduled for future.")

    finally:
        # Restore original timezone
        if original_tz:
            os.environ["TZ"] = original_tz
        else:
            os.environ.pop("TZ", None)
        time.tzset()

if __name__ == "__main__":
    test_timezone_comparison_issue()
    test_potential_edge_case()
