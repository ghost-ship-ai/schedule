#!/usr/bin/env python3
"""
Debug script to understand the multi-week scheduling issue described in #29
"""

import schedule
import datetime

def test_job():
    print("Job executed")

# Test the original issue: every(2).weeks.monday.at("10:00")
print("=== Testing multi-week scheduling issue ===")

current_time = datetime.datetime.now()
print(f"Current time: {current_time} ({current_time.strftime('%A')})")

# Clear any existing jobs
schedule.clear()

# Test 1: Single week scheduling (should work correctly)
print("\n--- Test 1: every().week.monday.at('10:00') ---")
try:
    job1 = schedule.every().week.monday.at("10:00").do(test_job)
    print(f"Next run: {job1.next_run}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Multi-week scheduling (the problematic case)
print("\n--- Test 2: every(2).weeks.monday.at('10:00') ---")
try:
    job2 = schedule.every(2).weeks.monday.at("10:00").do(test_job)
    print(f"Next run: {job2.next_run}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Check if IntervalError is raised for every(2).week (without monday)
print("\n--- Test 3: every(2).week (should raise IntervalError) ---")
try:
    job3 = schedule.every(2).week.do(test_job)
    print(f"Unexpected success: {job3}")
except Exception as e:
    print(f"Expected error: {e}")

# Test 4: Check current behavior vs expected behavior
print("\n--- Test 4: Comparing different intervals ---")
for interval in [1, 2, 3]:
    try:
        schedule.clear()
        job = schedule.every(interval).weeks.monday.at("10:00").do(test_job)
        print(f"every({interval}).weeks.monday.at('10:00') -> Next run: {job.next_run}")

        # Calculate days until next run
        if job.next_run:
            days_diff = (job.next_run - current_time).days
            print(f"  -> Days from now: {days_diff}")
    except Exception as e:
        print(f"every({interval}).weeks.monday.at('10:00') -> Error: {e}")

# Test 5: Test the specific issue mentioned in #29
print("\n--- Test 5: Reproducing issue #29 scenario ---")
try:
    schedule.clear()
    # This should schedule for every other Monday at 10:00
    job = schedule.every(2).weeks.monday.at("10:00").do(lambda: print("job"))
    print(f"every(2).weeks.monday.at('10:00') -> Next run: {job.next_run}")

    # Check if this is actually every other Monday
    next_run = job.next_run
    if next_run:
        # Calculate what the next run after that should be
        # It should be 14 days later (2 weeks)
        expected_second_run = next_run + datetime.timedelta(days=14)
        print(f"Expected second run (14 days later): {expected_second_run}")

        # Let's see what the scheduler calculates
        # We can't easily test this without advancing time, but we can check the logic
        print(f"Next Monday from now: {next_run}")
        print(f"Is this the correct 2-week boundary? Need to verify against epoch calculation")

except Exception as e:
    print(f"Error: {e}")

print("\n=== Analysis ===")
print("The issue described in #29 is about incorrect calculation of next_run times")
print("for multi-week intervals. The logic should ensure that jobs run on the")
print("correct week boundary according to the interval.")
