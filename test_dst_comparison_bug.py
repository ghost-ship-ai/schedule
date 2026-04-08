#!/usr/bin/env python3
"""
Test to reproduce the DST comparison bug in the while loop.

The issue is in the `while next_run <= now:` loop in _schedule_next_run.
During DST fall-back, this comparison might not work correctly when
dealing with ambiguous times.
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
                    # Create timezone-aware datetime
                    if hasattr(tz, 'localize'):
                        # pytz timezone
                        try:
                            return tz.localize(mock_date, is_dst=None)
                        except pytz.AmbiguousTimeError:
                            # Handle ambiguous time based on fold
                            return tz.localize(mock_date, is_dst=(self.fold == 0))
                    else:
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


def test_dst_comparison_issue():
    """
    Test the specific comparison issue during DST fall-back.

    This test simulates the scenario where the while loop in _schedule_next_run
    might not work correctly due to ambiguous time comparisons.
    """
    print("Testing DST comparison issue in _schedule_next_run...")

    def mock_job():
        return "job_executed"

    schedule.clear()

    # Test at the exact moment of DST transition
    # We're at 2:30 AM, second occurrence (after clocks fall back)
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=1):
        print(f"Current time: {datetime.datetime.now()} (second occurrence)")

        # Get the timezone-aware current time
        berlin_tz = pytz.timezone('Europe/Berlin')
        now_tz = datetime.datetime.now(berlin_tz)
        print(f"Current time (timezone-aware): {now_tz}")
        print(f"UTC offset: {now_tz.utcoffset()}")

        # Create a job that should run at 2:30
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

        print(f"Job next_run: {job.next_run}")

        # Let's manually test the comparison that happens in _schedule_next_run
        # This is where the bug might occur

        # Simulate what happens in _schedule_next_run
        print("\nSimulating _schedule_next_run logic:")

        # Get the current time in the job's timezone
        now = datetime.datetime.now(job.at_time_zone)
        print(f"now (in job timezone): {now}")

        # Create a next_run time for today at 2:30
        next_run = now.replace(hour=2, minute=30, second=0, microsecond=0)
        print(f"next_run (before correction): {next_run}")

        # Test the comparison
        print(f"next_run <= now: {next_run <= now}")
        print(f"next_run == now: {next_run == now}")
        print(f"next_run < now: {next_run < now}")

        # The issue might be that during the second occurrence,
        # next_run and now have the same local time but different UTC offsets

        # Let's test with both occurrences
        first_occurrence = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=True)
        second_occurrence = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=False)

        print(f"\nFirst occurrence: {first_occurrence}")
     

    # Simulate multiple calls to _schedule_next_run during the transition
    # This is where the bug might manifest as an infinite loop or wrong calculation
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=0):
        print(f"\nAt first occurrence of 2:30 AM")

        # Force recalculation of next run
        job._schedule_next_run()
        print(f"After _schedule_next_run: {job.next_run}")

        # Run the job
        job.run()
        print(f"After job.run(): {job.next_run}")

        # Force another recalculation
        job._schedule_next_run()
        print(f"After second _schedule_next_run: {job.next_run}")

        # The next run should be stable and point to the next day
        if job.next_run.day != 30:
            print(f"❌ Unstable scheduling: expected day 30, got {job.next_run.day}")
            return False

    print("✓ Edge case handled correctly")
    return True


def test_correct_utc_offset_with_fold():
    """
    Test the _correct_utc_offset method directly with fold scenarios.
    """
    print("\nTesting _correct_utc_offset method with fold scenarios...")

    def mock_job():
        return "job_executed"

    schedule.clear()

    with mock_datetime(2023, 10, 29, 1, 0, zone="Europe/Berlin"):
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

        # Test the _correct_utc_offset method directly
        berlin_tz = pytz.timezone('Europe/Berlin')

        # Create a time during the ambiguous period
        ambiguous_time = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=True)
        print(f"Ambiguous time (first occurrence): {ambiguous_time}")

        # Test _correct_utc_offset with this time
        corrected_time = job._correct_utc_offset(ambiguous_time, fixate_time=True)
        print(f"Corrected time: {corrected_time}")

        # The corrected time should be valid and not cause issues
        if corrected_time.hour != 2 or corrected_time.minute != 30:
            print(f"❌ _correct_utc_offset changed the time unexpectedly")
            return False

        # Test with the second occurrence
        ambiguous_time_2 = berlin_tz.localize(datetime.datetime(2023, 10, 29, 2, 30), is_dst=False)
        print(f"Ambiguous time (second occurrence): {ambiguous_time_2}")

        corrected_time_2 = job._correct_utc_offset(ambiguous_time_2, fixate_time=True)
        print(f"Corrected time 2: {corrected_time_2}")

        # Both should be valid but potentially different UTC offsets
        print(f"First occurrence UTC offset: {corrected_time.utcoffset()}")
        print(f"Second occurrence UTC offset: {corrected_time_2.utcoffset()}")

    print("✓ _correct_utc_offset method works correctly")
    return True


if __name__ == "__main__":
    print("Testing specific DST fall-back bugs in schedule library")
    print("=" * 60)

    try:
        success1 = test_dst_fallback_during_transition()
        success2 = test_dst_fallback_edge_case()
        success3 = test_correct_utc_offset_with_fold()

        if success1 and success2 and success3:
            print("\n✓ All tests passed - no bugs detected")
        else:
            print("\n❌ Bugs detected!")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
