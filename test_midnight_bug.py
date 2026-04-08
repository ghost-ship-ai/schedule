#!/usr/bin/env python3
"""
Test case to reproduce the midnight timezone bug described in the issue.
"""

import schedule
import datetime
import os
import time
import unittest

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

class TestMidnightTimezoneBug(unittest.TestCase):

    def setUp(self):
        schedule.clear()

    def test_midnight_job_should_not_run_immediately_when_past_midnight(self):
        """
        Test that a job scheduled for midnight doesn't run immediately
        when the current time is past midnight.
        """
        executed = []

        def test_job():
            executed.append(datetime.datetime.now())
            return "executed"

        # Mock current time to be 15:00 (3 PM) Berlin time on April 8, 2024
        with mock_datetime(2024, 4, 8, 15, 0, 0):
            # Schedule a job for midnight Berlin time
            job = schedule.every().day.at("00:00", "Europe/Berlin").do(test_job)

            # The job should be scheduled for the next midnight, not today's midnight
            # Since it's 15:00, today's midnight has already passed
            self.assertFalse(job.should_run, "Job should not run immediately when scheduled after midnight")

            # Run pending jobs - this should NOT execute the job
            schedule.run_pending()

            # Verify the job didn't execute
            self.assertEqual(len(executed), 0, "Job should not have executed when run_pending() was called")

            # Verify the next run is scheduled for tomorrow's midnight (in local time)
            # Berlin time 00:00 = Local time 22:00 (during DST)
            expected_next_run = datetime.datetime(2024, 4, 8, 22, 0, 0)
            self.assertEqual(job.next_run, expected_next_run,
                           f"Next run should be {expected_next_run}, but was {job.next_run}")

    def test_midnight_job_should_not_run_immediately_when_just_past_midnight(self):
        """
        Test that a job scheduled for midnight doesn't run immediately
        when the current time is just past midnight (e.g., 00:30).
        """
        executed = []

        def test_job():
            executed.append(datetime.datetime.now())
            return "executed"

        # Mock current time to be 00:30 (30 minutes past midnight) Berlin time
        with mock_datetime(2024, 4, 8, 0, 30, 0):
            # Schedule a job for midnight Berlin time
            job = schedule.every().day.at("00:00", "Europe/Berlin").do(test_job)

            # The job should be scheduled for the next midnight, not run immediately
            self.assertFalse(job.should_run, "Job should not run immediately when scheduled 30 minutes after midnight")

            # Run pending jobs - this should NOT execute the job
            schedule.run_pending()

            # Verify the job didn't execute
            self.assertEqual(len(executed), 0, "Job should not have executed when run_pending() was called")

    def test_midnight_job_edge_case_exactly_at_midnight(self):
        """
        Test the edge case where a job is scheduled exactly at midnight.
        """
        executed = []

        def test_job():
            executed.append(datetime.datetime.now())
            return "executed"

        # Mock current time to be exactly midnight Berlin time
        with mock_datetime(2024, 4, 8, 0, 0, 0):
            # Schedule a job for midnight Berlin time
            job = schedule.every().day.at("00:00", "Europe/Berlin").do(test_job)

            # This is a tricky case - the job might run immediately or wait until tomorrow
            # Let's see what the current behavior is
            print(f"Job scheduled at exactly midnight - should_run: {job.should_run}")
            print(f"Next run: {job.next_run}")

            # Run pending jobs
            schedule.run_pending()

            # Document the current behavior
            print(f"Job executed: {len(executed) > 0}")

if __name__ == "__main__":
    unittest.main()
