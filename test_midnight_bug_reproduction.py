#!/usr/bin/env python3
"""
Test script to reproduce the midnight timezone scheduling bug.
This script will be deleted after debugging.
"""

import datetime
import schedule
import pytz

def debug_timezone_conversion():
    """Debug the timezone conversion logic in detail."""
    print("=== Debugging timezone conversion logic ===")

    # Clear any existing jobs
    schedule.clear()

    # Create a job to examine its internal state
    job = schedule.every().day.at("00:00", "Europe/Berlin").do(lambda: print("midnight job"))

    print(f"Job at_time_zone: {job.at_time_zone}")
    print(f"Job at_time: {job.at_time}")
    print(f"Job next_run: {job.next_run}")
    print(f"Job next_run type: {type(job.next_run)}")

    # Let's manually trace through the _schedule_next_run logic
    berlin_tz = pytz.timezone("Europe/Berlin")

    # Simulate the logic from _schedule_next_run
    print("\n--- Simulating _schedule_next_run logic ---")

    # Step 1: Create 'now' in target timezone
    now = datetime.datetime.now(berlin_tz)
    print(f"1. now = datetime.datetime.now(berlin_tz): {now}")
    print(f"   now.tzinfo: {now.tzinfo}")

    # Step 2: next_run starts as now
    next_run = now
    print(f"2. next_run = now: {next_run}")
    print(f"   next_run.tzinfo: {next_run.tzinfo}")

    # Step 3: Move to at_time (00:00)
    # This is what _move_to_at_time does
    next_run = next_run.replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"3. After _move_to_at_time: {next_run}")
    print(f"   next_run.tzinfo: {next_run.tzinfo}")

    # Step 4: Check if next_run <= now (this is the problematic comparison)
    print(f"4. Comparison: next_run <= now")
    print(f"   {next_run} <= {now}")
    print(f"   Result: {next_run <= now}")

    # Step 5: If true, we need to advance by one day
    if next_run <= now:
        print("5. Advancing by one day...")
        period = datetime.timedelta(days=1)
        next_run += period
        print(f"   After advancing: {next_run}")
        print(f"   next_run.tzinfo: {next_run.tzinfo}")

    # Step 6: The current "fix" - timezone conversion
    print("\n--- Current 'fix' - timezone conversion ---")
    comparison_now = now.astimezone(berlin_tz)
    comparison_next_run = next_run.astimezone(berlin_tz)
    print(f"comparison_now = now.astimezone(berlin_tz): {comparison_now}")
    print(f"comparison_next_run = next_run.astimezone(berlin_tz): {comparison_next_run}")
    print(f"Are they the same as original? now == comparison_now: {now == comparison_now}")
    print(f"Are they the same as original? next_run == comparison_next_run: {next_run == comparison_next_run}")

    return True

def test_midnight_bug():
    """Reproduce the midnight scheduling bug."""
    print("Testing midnight timezone scheduling bug...")

    # Clear any existing jobs
    schedule.clear()

    # Create a job scheduled for midnight Berlin time
    job = schedule.every().day.at("00:00", "Europe/Berlin").do(lambda: print("midnight job"))

    print(f"Job created: {job}")
    print(f"Job next_run: {job.next_run}")
    print(f"Job should_run: {job.should_run}")

    # Get current time in Berlin
    berlin_tz = pytz.timezone("Europe/Berlin")
    now_berlin = datetime.datetime.now(berlin_tz)
    print(f"Current time in Berlin: {now_berlin}")

    # The job should NOT run immediately if current time is past midnight
    if now_berlin.hour > 0:
        print(f"Current hour is {now_berlin.hour}, so job should NOT run immediately")
        if job.should_run:
            print("❌ BUG: Job should_run is True when it should be False!")
            return False
        else:
            print("✅ Job correctly scheduled for next midnight")
            return True
    else:
        print("Current time is at midnight, so immediate execution is expected")
        return True

if __name__ == "__main__":
    debug_timezone_conversion()
    print("\n" + "="*50 + "\n")
    test_midnight_bug()
