#!/usr/bin/env python3
"""
Debug script to understand the DST issue better.
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


def debug_dst_issue():
    """Debug the DST issue step by step."""

    schedule.clear()
    job = schedule.every().day.at("02:30", "Europe/Berlin").do(lambda: "test")

    print("=== Debugging DST Fall-back Issue ===")

    # Test during the ambiguous time
    with mock_datetime(2023, 10, 29, 2, 30, fold=1):
        print(f"\nCurrent time: {datetime.datetime.now()} (fold=1)")

        # Get the timezone
        berlin_tz = pytz.timezone("Europe/Berlin")
        current_time = datetime.datetime.now(berlin_tz)
        print(f"Current time with timezone: {current_time}")
        print(f"Current time UTC offset: {current_time.utcoffset()}")
        print(f"Current time DST: {current_time.dst()}")

        # Check what the mock is actually producing
        mock_now = datetime.datetime.now()
        print(f"Mock now: {mock_now}")
        print(f"Mock now fold: {mock_now.fold}")

        # Try to create the correct timezone-aware datetime manually
        try:
            # This should be the second occurrence (CET, +01:00)
            correct_current = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=False)
            print(f"Correct current time (second occurrence): {correct_current}")
        except Exception as e:
            print(f"Error creating correct current time: {e}")

        # Test the ambiguous time detection
        naive_time = datetime.datetime(2023, 10, 29, 2, 30)
        print(f"\nTesting ambiguous time detection for: {naive_time}")
        print(f"Is ambiguous: {job._is_ambiguous_time(naive_time)}")

        # Test both fold values
        try:
            dt_fold0 = berlin_tz.localize(naive_time, is_dst=True)
            dt_fold1 = berlin_tz.localize(naive_time, is_dst=False)
            print(f"Fold=0 (first occurrence): {dt_fold0} (UTC: {dt_fold0.utctimetuple()})")
            print(f"Fold=1 (second occurrence): {dt_fold1} (UTC: {dt_fold1.utctimetuple()})")
            print(f"Are they different? {dt_fold0.utctimetuple() != dt_fold1.utctimetuple()}")
        except Exception as e:
            print(f"Error localizing: {e}")

        # Test the _schedule_next_run method
        print(f"\nBefore _schedule_next_run: {job.next_run}")
        job._schedule_next_run()
        print(f"After _schedule_next_run: {job.next_run}")

        # Test the _correct_utc_offset method directly
        test_moment = berlin_tz.localize(datetime.datetime(2023, 10, 30, 2, 30), is_dst=False)
        print(f"\nTesting _correct_utc_offset with: {test_moment}")
        corrected = job._correct_utc_offset(test_moment, fixate_time=True)
        print(f"Corrected moment: {corrected}")

        # Debug the current time detection
        print(f"\nDebugging current time detection:")
        now_with_tz = datetime.datetime.now(berlin_tz)
        now_naive = now_with_tz.replace(tzinfo=None)
        print(f"Now with timezone: {now_with_tz}")
        print(f"Now naive: {now_naive}")
        print(f"Is now ambiguous: {job._is_ambiguous_time(now_naive)}")

        # Test the specific case that's failing
        print(f"\nTesting the specific failing case:")
        failing_moment = datetime.datetime(2023, 10, 30, 2, 30)  # Next day, same time
        print(f"Failing moment (naive): {failing_moment}")
        print(f"Is failing moment ambiguous: {job._is_ambiguous_time(failing_moment)}")

        # Test _correct_utc_offset with the failing moment
        failing_moment_tz = berlin_tz.localize(failing_moment, is_dst=False)
        print(f"Failing moment with tz: {failing_moment_tz}")
        corrected_failing = job._correct_utc_offset(failing_moment_tz, fixate_time=True)
        print(f"Corrected failing moment: {corrected_failing}")


if __name__ == "__main__":
    debug_dst_issue()
