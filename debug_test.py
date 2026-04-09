#!/usr/bin/env python3
import schedule
import datetime

def job():
    print("job executed")

print("Today is:", datetime.datetime.now().strftime('%A, %Y-%m-%d %H:%M:%S'))

# Clear any existing jobs
schedule.clear()

# Test 1: Multi-week scheduling
print("\n=== Test 1: Multi-week scheduling ===")
try:
    job1 = schedule.every(2).weeks.monday.at("10:00").do(job)
    print("SUCCESS: Multi-week scheduling worked!")
    print(f"Next run: {job1.next_run}")
    print(f"Interval: {job1.interval}")
    print(f"Unit: {job1.unit}")
    print(f"Start day: {job1.start_day}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Clear for next test
schedule.clear()

# Test 2: Single week scheduling
print("\n=== Test 2: Single week scheduling ===")
try:
    job2 = schedule.every().monday.at("10:00").do(job)
    print("SUCCESS: Single week scheduling works")
    print(f"Next run: {job2.next_run}")
    print(f"Interval: {job2.interval}")
    print(f"Unit: {job2.unit}")
    print(f"Start day: {job2.start_day}")
except Exception as e:
    print(f"ERROR with single week: {e}")
    import traceback
    traceback.print_exc()
