#!/usr/bin/env python3
"""Final verification that the float interval fix works correctly"""

import schedule
import time

def test_job():
    print("Job executed at", time.strftime("%H:%M:%S"))

print("Testing float intervals with schedule library...")

# Test 1: Basic float interval creation
print("\n1. Testing basic float interval creation:")
try:
    job1 = schedule.every(0.5).to(1.5).seconds.do(test_job)
    print(f"✓ SUCCESS: Created job with interval {job1.interval} to {job1.latest}")
    print(f"  Next run: {job1.next_run}")
except Exception as e:
    print(f"✗ FAILED: {e}")

# Test 2: Different float values
print("\n2. Testing different float values:")
try:
    job2 = schedule.every(2.5).to(3.7).minutes.do(test_job)
    print(f"✓ SUCCESS: Created job with interval {job2.interval} to {job2.latest}")
except Exception as e:
    print(f"✗ FAILED: {e}")

# Test 3: Mixed integer and float
print("\n3. Testing mixed integer and float:")
try:
    job3 = schedule.every(1).to(2.5).seconds.do(test_job)
    print(f"✓ SUCCESS: Created job with interval {job3.interval} to {job3.latest}")
except Exception as e:
    print(f"✗ FAILED: {e}")

# Test 4: Verify randomness
print("\n4. Testing randomness of intervals:")
intervals = []
for i in range(10):
    job = schedule.every(0.5).to(1.5).seconds.do(test_job)
    # Calculate interval from next_run
    import datetime
    now = datetime.datetime.now()
    interval_used = (job.next_run.replace(tzinfo=None) - now).total_seconds()
    intervals.append(round(interval_used, 2))
    schedule.clear()  # Clear for next iteration

print(f"Generated intervals: {intervals}")
print(f"Min: {min(intervals)}, Max: {max(intervals)}")
print(f"Unique values: {len(set(intervals))}")

if len(set(intervals)) > 1 and all(0.5 <= i <= 1.5 for i in intervals):
    print("✓ SUCCESS: Intervals are random and within expected range")
else:
    print("✗ FAILED: Intervals are not properly randomized or out of range")

print("\n5. Testing backward compatibility with integers:")
try:
    job4 = schedule.every(5).to(10).seconds.do(test_job)
    print(f"✓ SUCCESS: Integer intervals still work: {job4.interval} to {job4.latest}")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nAll tests completed!")
