#!/usr/bin/env python3
"""
Script to reproduce the midnight timezone bug.
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

def test_job():
    print("Midnight job executed!")
    return "executed"

def main():
    # Clear any existing jobs
    schedule.clear()

    print("Testing the exact scenario from the bug report...")
    print("Reproducing: Jobs scheduled at midnight (00:00) with timezone execute immediately on first run")

    # Let's try to reproduce the exact issue by examining the internal state
    # Mock current time to be 15:00 (3 PM) Berlin time on April 8, 2024
    with mock_datetime(2024, 4, 8, 15, 0, 0):
        print("Current time (mocked): 15:00 Berlin time")

        # Schedule a job for midnight Berlin time
        job = schedule.every().day.at("00:00", "Europe/Berlin").do(test_job)

        print(f"Job scheduled: {job}")
        print(f"Next run: {job.next_run}")
        print(f"Should run: {job.should_run}")

        # Let's examine the internal state more carefully
        import pytz
        berlin_tz = pytz.timezone("Europe/Berlin")
        current_berlin_time = datetime.datetime.now(berlin_tz)
        print(f"Current Berlin time: {current_berlin_time}")
        print(f"Next run (raw): {job.next_run}")

        # Check if the job thinks it should run
        print(f"datetime.datetime.now(): {datetime.datetime.now()}")
        print(f"job.next_run: {job.next_run}")
        print(f"Comparison (now >= next_run): {datetime.datetime.now() >= job.next_run}")

        # This should NOT execute the job since it's 15:00, not midnight
        print("\nCalling run_pending()...")
        schedule.run_pending()

        print(f"After run_pending - Should run: {job.should_run}")

    # Let's also test with a different approach - using the exact example from the issue
    print("\n" + "="*50)
    print("Testing with the exact code from the issue...")
    schedule.clear()

    # Use the exact code from the issue
    from schedule import every, run_pending
    import time

    # Schedule a job for midnight Berlin time
    job = every().day.at("00:00", "Europe/Berlin").do(lambda: print("midnight job"))

    print(f"Job scheduled: {job}")
    print(f"Next run: {job.next_run}")
    print(f"Should run: {job.should_run}")

    # First call at e.g. 15:00 — job fires immediately instead of waiting until next midnight
    print("\nCalling run_pending() - this should NOT execute the job...")
    run_pending()

if __name__ == "__main__":
    main()
