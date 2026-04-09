#!/usr/bin/env python3
import schedule
import datetime

def job():
    print("job executed")

print("Today is:", datetime.datetime.now().strftime('%A, %Y-%m-%d %H:%M:%S'))

# Test different multi-week intervals
test_cases = [
    (1, "monday"),  # every week
    (2, "monday"),  # every 2 weeks
    (3, "monday"),  # every 3 weeks
    (4, "monday"),  # every 4 weeks
    (2, "friday"),  # every 2 weeks on Friday
]

for interval, day in test_cases:
    schedule.clear()

    if interval == 1:
        job_obj = getattr(schedule.every(), day).at("10:00").do(job)
    else:
        job_obj = getattr(schedule.every(interval).weeks, day).at("10:00").do(job)

    print(f"\nEvery {interval} week(s) on {day}:")
    print(f"  Next run: {job_obj.next_run}")

    # Calculate expected next run manually
    today = datetime.datetime.now()
    target_weekday = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].index(day)
    days_ahead = target_weekday - today.weekday()

    if days_ahead < 0:  # Target day already passed this week
        days_ahead += 7

    expected_next = today + datetime.timedelta(days=days_ahead)
    expected_next = expected_next.replace(hour=10, minute=0, second=0, microsecond=0)

    if interval > 1:
        # For multi-week intervals, we need to add additional weeks
        expected_next += datetime.timedelta(weeks=interval-1)

    print(f"  Expected: {expected_next}")
    print(f"  Match: {job_obj.next_run.date() == expected_next.date() and job_obj.next_run.time() == expected_next.time()}")
