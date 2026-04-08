#!/usr/bin/env python3
"""
Temporary script to analyze the current scheduling logic.
This will be deleted after understanding the issue.
"""

import schedule
import datetime
import pytz

# Mock the current time to be 15:00 on April 8, 2024
class MockDateTime:
    def __init__(self, year, month, day, hour, minute, second=0):
        self.mock_time = datetime.datetime(year, month, day, hour, minute, second)

    def __enter__(self):
        self.original_datetime = datetime.datetime

        class MockDate(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                mock_time = datetime.datetime(2024, 4, 8, 15, 0, 0)
                if tz:
                    # Convert to the specified timezone
                    local_tz = pytz.timezone('UTC')  # Assume we're in UTC for simplicity
                    mock_time = local_tz.localize(mock_time)
                    return mock_time.astimezone(tz)
                return mock_time

        datetime.datetime = MockDate
        return MockDate

    def __exit__(self, *args):
        datetime.datetime = self.original_datetime

def test_job():
    print("Job executed!")

# Test the current behavior
schedule.clear()

print("=== Current Behavior Analysis ===")
with MockDateTime(2024, 4, 8, 15, 0, 0):
    print(f"Current time (mocked): {datetime.datetime.now()}")

    # Schedule a job for midnight Berlin time
    berlin_tz = pytz.timezone('Europe/Berlin')
    print(f"Current time in Berlin: {datetime.datetime.now(berlin_tz)}")

    job = schedule.every().day.at("00:00", "Europe/Berlin").do(test_job)

    print(f"Job should_run: {job.should_run}")
    print(f"Job next_run: {job.next_run}")
    print(f"Job next_run day: {job.next_run.day}")

    # Let's also check what midnight Berlin time would be in local time
    berlin_midnight = berlin_tz.localize(datetime.datetime(2024, 4, 8, 0, 0, 0))
    local_midnight = berlin_midnight.astimezone()
    print(f"Berlin midnight (2024-04-08 00:00) in local time: {local_midnight}")

    berlin_midnight_tomorrow = berlin_tz.localize(datetime.datetime(2024, 4, 9, 0, 0, 0))
    local_midnight_tomorrow = berlin_midnight_tomorrow.astimezone()
    print(f"Berlin midnight (2024-04-09 00:00) in local time: {local_midnight_tomorrow}")
