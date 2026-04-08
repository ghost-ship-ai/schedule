#!/usr/bin/env python3
"""
Debug script to understand what's happening in _correct_utc_offset during DST transitions.
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


def debug_dst_transition():
    """
    Debug the DST transition behavior step by step.
    """

    def mock_job():
        return "executed"

    schedule.clear()

    # Create a job scheduled at 2:30 in Europe/Berlin timezone
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

    print("=== Debugging DST Transition ===")

    # Test at the first occurrence of 2:30 (CEST, fold=0)
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=0):
        print(f"Current time: {datetime.datetime.now()}")
        print(f"Current time with timezone: {datetime.datetime.now(pytz.timezone('Europe/Berlin'))}")

        # Let's manually trace through _schedule_next_run
        print("\n--- Tracing _schedule_next_run ---")

        # Get the current time in the job's timezone
        now = datetime.datetime.now(job.at_time_zone)
        print(f"now (in job timezone): {now}")
        print(f"now.utcoffset(): {now.utcoffset()}")
        print(f"now.fold: {getattr(now, 'fold', 'N/A')}")

        # Calculate next_run
        next_run = now
        print(f"initial next_run: {next_run}")

        # Move to at_time
        next_run = job._move_to_at_time(next_run)
        print(f"after _move_to_at_time: {next_run}")
        print(f"next_run.utcoffset(): {next_run.utcoffset()}")

        # Add the interval (1 day)
        period = datetime.timedelta(days=1)
        next_run += period
        print(f"after adding 1 day: {next_run}")
        print(f"next_run.utcoffset(): {next_run.utcoffset()}")

        # Check if next_run <= now
        print(f"next_run <= now: {next_run <= now}")

        while next_run <= now:
            print(f"  In while loop: next_run={next_run}, now={now}")
            next_run += period
            print(f"  After adding period: next_run={next_run}")

        # Apply _correct_utc_offset
        print(f"before _correct_utc_offset: {next_run}")
        corrected_next_run = job._correct_utc_offset(next_run, fixate_time=True)
        print(f"after _correct_utc_offset: {corrected_next_run}")
        print(f"corrected_next_run.utcoffset(): {corrected_next_run.utcoffset()}")

        # Convert back to local timezone
        if job.at_time_zone is not None:
            local_next_run = corrected_next_run.astimezone()
            print(f"after astimezone(): {local_next_run}")
            local_next_run = local_next_run.replace(tzinfo=None)
            print(f"after removing tzinfo: {local_next_run}")

        print(f"\nFinal next_run would be: {local_next_run}")

        # Now let's see what the actual method produces
        job._schedule_next_run()
        print(f"Actual job.next_run: {job.next_run}")

    schedule.clear()


def debug_correct_utc_offset():
    """
    Debug the _correct_utc_offset method specifically.
    """

    def mock_job():
        return "executed"

    schedule.clear()

    # Create a job scheduled at 2:30 in Europe/Berlin timezone
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

    print("\n=== Debugging _correct_utc_offset ===")

    berlin_tz = pytz.timezone("Europe/Berlin")

    # Test with a time during the DST overlap
    test_time = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=True)
    print(f"Test time (CEST): {test_time}")
    print(f"Test time UTC offset: {test_time.utcoffset()}")

    # Add one day
    next_day = test_time + datetime.timedelta(days=1)
    print(f"Next day: {next_day}")
    print(f"Next day UTC offset: {next_day.utcoffset()}")

    # Apply _correct_utc_offset
    corrected = job._correct_utc_offset(next_day, fixate_time=True)
    print(f"After _correct_utc_offset: {corrected}")
    print(f"Corrected UTC offset: {corrected.utcoffset()}")

    # Test with the second occurrence
    test_time_2 = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=False)
    print(f"\nTest time (CET): {test_time_2}")
    print(f"Test time UTC offset: {test_time_2.utcoffset()}")

    # Add one day
    next_day_2 = test_time_2 + datetime.timedelta(days=1)
    print(f"Next day: {next_day_2}")
    print(f"Next day UTC offset: {next_day_2.utcoffset()}")

    # Apply _correct_utc_offset
    corrected_2 = job._correct_utc_offset(next_day_2, fixate_time=True)
    print(f"After _correct_utc_offset: {corrected_2}")
    print(f"Corrected UTC offset: {corrected_2.utcoffset()}")

    schedule.clear()


if __name__ == "__main__":
    debug_dst_transition()
    debug_correct_utc_offset()
