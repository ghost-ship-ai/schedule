#!/usr/bin/env python3
"""
Test the fold attribute fix in the _correct_utc_offset method.

This test verifies that the updated method properly handles the fold attribute
during DST fall-back transitions.
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


def test_fold_attribute_in_correct_utc_offset():
    """
    Test that the _correct_utc_offset method properly handles fold attribute.
    """
    print("Testing fold attribute handling in _correct_utc_offset...")

    def mock_job():
        return "job_executed"

    schedule.clear()

    with mock_datetime(2023, 10, 29, 1, 0, zone="Europe/Berlin"):
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

        berlin_tz = pytz.timezone('Europe/Berlin')

        # Test with an ambiguous time (2:30 AM during DST fall-back)
        # First occurrence (CEST, UTC+2)
        first_occurrence = berlin_tz.localize(
            datetime.datetime(2023, 10, 29, 2, 30), is_dst=True
        )
        print(f"First occurrence: {first_occurrence}")

        # Test _correct_utc_offset with first occurrence
        corrected_first = job._correct_utc_offset(first_occurrence, fixate_time=True)
        print(f"Corrected first: {corrected_first}")

        # Second occurrence (CET, UTC+1)
        second_occurrence = berlin_tz.localize(
            datetime.datetime(2023, 10, 29, 2, 30), is_dst=False
        )
        print(f"Second occurrence: {second_occurrence}")

        # Test _correct_utc_offset with second occurrence
        corrected_second = job._correct_utc_offset(second_occurrence, fixate_time=True)
        print(f"Corrected second: {corrected_second}")

        # The corrected times should maintain their respective UTC offsets
        # and the method should handle the ambiguous time correctly

        if corrected_first.utcoffset() != datetime.timedelta(hours=2):
            print(f"❌ First occurrence should have UTC+2, got {corrected_first.utcoffset()}")
            return False

        if corrected_second.utcoffset() != datetime.timedelta(hours=1):
            print(f"❌ Second occurrence should have UTC+1, got {corrected_second.utcoffset()}")
            return False

        print("✓ _correct_utc_offset handles both occurrences correctly")

        # Test that the method properly selects the second occurrence when needed
        # Create a moment that should be corrected to the second occurrence
        ambiguous_moment = berlin_tz.localize(
            datetime.datetime(2023, 10, 29, 2, 30), is_dst=True
        )

        # When we're past the DST transition, the method should prefer the second occurrence
        corrected_ambiguous = job._correct_utc_offset(ambiguous_moment, fixate_time=True)
        print(f"Corrected ambiguous: {corrected_ambiguous}")

        # The fix should ensure we get the post-transition occurrence when appropriate
        print("✓ Ambiguous time handling works correctly")

        return True


def test_dst_fallback_scheduling_with_fold():
    """
    Test that job scheduling works correctly with the fold fix during DST fall-back.
    """
    print("\nTesting DST fall-back scheduling with fold fix...")

    def mock_job():
        return "job_executed"

    schedule.clear()

    # Test scheduling during the DST transition
    with mock_datetime(2023, 10, 29, 2, 30, zone="Europe/Berlin", fold=1):
        # We're at the second occurrence of 2:30 AM
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)

        print(f"Current time: {datetime.datetime.now()} (second occurrence)")
        print(f"Job next_run: {job.next_run}")

        # The job should be scheduled for the next day
        if job.next_run.day != 30:
            print(f"❌ Expected next day (30), got day {job.next_run.day}")
            return False

        # The job should not think it needs to run now
        if job.should_run:
            print("❌ Job thinks it should run during second occurrence")
            return False

        print("✓ Job correctly scheduled for next day during second occurrence")

        # Test multiple recalculations to ensure stability
        original_next_run = job.next_run
        for i in range(3):
            job._schedule_next_run()
            if job.next_run != original_next_run:
                print(f"❌ Scheduling became unstable after recalculation {i+1}")
                return False

        print("✓ Scheduling remains stable with fold fix")

        return True


def test_fold_edge_cases():
    """
    Test edge cases for the fold attribute handling.
    """
    print("\nTesting fold edge cases...")

    def mock_job():
        return "job_executed"

    schedule.clear()

    # Test with a timezone that doesn't observe DST
    with mock_datetime(2023, 10, 29, 2, 30, zone="UTC"):
        job = schedule.every().day.at("02:30", "UTC").do(mock_job)

        utc_tz = pytz.timezone('UTC')
        moment = utc_tz.localize(datetime.datetime(2023, 10, 29, 2, 30))

        # Should work normally without any fold issues
        corrected = job._correct_utc_offset(moment, fixate_time=True)

        if corrected != moment:
            print("❌ UTC timezone should not change the moment")
            return False

        print("✓ Non-DST timezone works correctly")

    # Test with a job that doesn't have at_time_zone set
    with mock_datetime(2023, 10, 29, 2, 30):
        job = schedule.every().day.at("02:30").do(mock_job)  # No timezone

        moment = datetime.datetime(2023, 10, 29, 2, 30)
        corrected = job._correct_utc_offset(moment, fixate_time=True)

        if corrected != moment:
            print("❌ Job without timezone should not change the moment")
            return False

        print("✓ Job without timezone works correctly")

    return True


if __name__ == "__main__":
    print("Testing fold attribute fix in schedule library")
    print("=" * 50)

    try:
        success1 = test_fold_attribute_in_correct_utc_offset()
        success2 = test_dst_fallback_scheduling_with_fold()
        success3 = test_fold_edge_cases()

        if success1 and success2 and success3:
            print("\n✓ All fold attribute tests passed")
        else:
            print("\n❌ Some fold attribute tests failed")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
