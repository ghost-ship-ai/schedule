#!/usr/bin/env python3
import schedule
import datetime
from unittest.mock import patch

def job():
    print("job executed")

# Test the behavior by simulating job execution over time
def test_multi_week_execution():
    schedule.clear()

    # Schedule a job for every 2 weeks on Monday at 10:00
    job_obj = schedule.every(2).weeks.monday.at("10:00").do(job)

    print("=== Testing every(2).weeks.monday execution pattern ===")
    print(f"Job scheduled. First run: {job_obj.next_run}")

    # Simulate running the scheduler over several weeks
    current_time = datetime.datetime(2026, 4, 9, 20, 0)  # Thursday
    execution_times = []

    for week in range(8):  # Test over 8 weeks
        # Check each day of the week
        for day in range(7):
            test_time = current_time + datetime.timedelta(weeks=week, days=day, hours=10)

            # Mock the current time
            with patch('schedule.datetime') as mock_dt:
                mock_dt.datetime.now.return_value = test_time
                mock_dt.datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

                # Check if job should run
                if job_obj.should_run:
                    execution_times.append(test_time)
                    print(f"Job would execute at: {test_time.strftime('%A, %Y-%m-%d %H:%M')}")

                    # Simulate running the job (this updates next_run)
                    job_obj.run()
                    print(f"Next run after execution: {job_obj.next_run}")

    print(f"\nTotal executions in 8 weeks: {len(execution_times)}")

    if len(execution_times) >= 2:
        interval_days = (execution_times[1] - execution_times[0]).days
        print(f"Interval between first two executions: {interval_days} days")
        print(f"Expected interval: 14 days (2 weeks)")
        print(f"Correct interval: {interval_days == 14}")

if __name__ == "__main__":
    test_multi_week_execution()
