#!/usr/bin/env python3
"""
Debug script to understand the _schedule_next_run logic for midnight jobs.
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

def debug_schedule_next_run():
    """Debug the _schedule_next_run method step by step"""

    # Clear any existing jobs
    schedule.clear()

    # Mock current time to be 15:00 (3 PM) Berlin time on April 8, 2024
    with mock_datetime(2024, 4, 8, 15, 0, 0):
        print("=== Debugging _schedule_next_run for midnight job ===")
        print("Current time (mocked): 15:00 Berlin time")

        # Create a job but don't schedule it yet
        job = schedule.Job(1)
        job.unit = "days"
        job.at_time = datetime.time(0, 0, 0)  # midnight

        import pytz
        job.at_time_zone = pytz.timezone("Europe/Berlin")

        print(f"Job unit: {job.unit}")
        print(f"Job at_time: {job.at_time}")
        print(f"Job at_time_zone: {job.at_time_zone}")

        # Step through _schedule_next_run logic manually
        print("\n--- Step-by-step _schedule_next_run logic ---")

        # Step 1: Get current time in timezone
        now = datetime.datetime.now(job.at_time_zone)
        print(f"1. now = datetime.datetime.now(at_time_zone): {now}")

        # Step 2: Start with current time
        next_run = now
        print(f"2. next_run = now: {next_run}")

        # Step 3: Move to at_time (midnight)
        if job.at_time is not None:
            next_run = job._move_to_at_time(next_run)
            print(f"3. next_run after _move_to_at_time: {next_run}")

        # Step 4: Check interval logic
        interval = job.interval
        print(f"4. interval: {interval}")

        period = datetime.timedelta(**{job.unit: interval})
        print(f"5. period: {period}")

        if interval != 1:
            next_run += period
            print(f"6. next_run after adding period (interval != 1): {next_run}")
        else:
            print(f"6. interval == 1, no period added yet")

        # Step 7: The critical while loop
        print(f"7. Before while loop - next_run: {next_run}, now: {now}")
        print(f"   Comparison (next_run <= now): {next_run <= now}")

        loop_count = 0
        while next_run <= now:
            loop_count += 1
            next_run += period
            print(f"   Loop {loop_count}: next_run after adding period: {next_run}")
            if loop_count > 5:  # Safety break
                print("   Breaking after 5 loops to avoid infinite loop")
                break

        print(f"8. Final next_run before timezone conversion: {next_run}")

        # Step 8: Timezone conversion
        next_run = job._correct_utc_offset(next_run, fixate_time=(job.at_time is not None))
        print(f"9. next_run after _correct_utc_offset: {next_run}")

        if job.at_time_zone is not None:
            # Convert back to the local timezone
            next_run = next_run.astimezone()
            next_run = next_run.replace(tzinfo=None)
            print(f"10. next_run after timezone conversion: {next_run}")

        # Now let's compare with the actual method
        print("\n--- Actual _schedule_next_run method ---")
        job._schedule_next_run()
        print(f"Actual next_run: {job.next_run}")

        # Check should_run
        print(f"\nshould_run: {job.should_run}")

if __name__ == "__main__":
    debug_schedule_next_run()
