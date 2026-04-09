#!/usr/bin/env python3
import schedule
import datetime

def job():
    print("job executed")

# Test what happens when we manually advance time
schedule.clear()

print("Today is Thursday, April 9, 2026")

# Schedule every 2 weeks on Monday
job_obj = schedule.every(2).weeks.monday.at("10:00").do(job)
print(f"Scheduled every 2 weeks on Monday. Next run: {job_obj.next_run}")

# What should happen:
# - Next Monday (April 13) should be the first run
# - Then 2 weeks later (April 27) should be the second run
# - Then 2 weeks later (May 11) should be the third run

expected_runs = [
    datetime.datetime(2026, 4, 13, 10, 0),  # Next Monday
    datetime.datetime(2026, 4, 27, 10, 0),  # 2 weeks later
    datetime.datetime(2026, 5, 11, 10, 0),  # 2 weeks later
]

print("\nExpected execution pattern:")
for i, run_time in enumerate(expected_runs):
    print(f"Run {i+1}: {run_time.strftime('%A, %Y-%m-%d %H:%M')}")

print(f"\nActual first run: {job_obj.next_run}")
print(f"Matches expected: {job_obj.next_run == expected_runs[0]}")

# Test single week for comparison
schedule.clear()
job_obj2 = schedule.every().monday.at("10:00").do(job)
print(f"\nSingle week Monday job next run: {job_obj2.next_run}")
print(f"Same as multi-week first run: {job_obj2.next_run == job_obj.next_run}")
