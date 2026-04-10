#!/usr/bin/env python3
"""
Test to reproduce the original midnight timezone bug.
This script will be deleted after debugging.
"""

import datetime
import schedule
import pytz

def test_original_bug_scenario():
    """Test the exact scenario described in the original bug report."""
    print("=== Testing original bug scenario ===")

    # Clear any existing jobs
    schedule.clear()

    # The bug report says: "When scheduling a daily job at midnight (00:00) with a timezone,
    # the job executes immediately on the first run_pending() call, even if the current time
    # is well past midnight (e.g., 15:00)."

    # Let's simulate this by mocking the time to be 15:00 Berlin time
    berlin_tz = pytz.timezone("Europe/Berlin")

    # Create a job for midnight Berlin time
    job = schedule.every().day.at("00:00", "Europe/Berlin").do(lambda: print("midnight job"))

    print(f"Job created at current time")
    print(f"Job next_run: {job.next_run}")
    print(f"Job should_run: {job.should_run}")

    # Get current Berlin time
    now_berlin = datetime.datetime.now(berlin_tz)
    print(f"Current Berlin time: {now_berlin}")

    # The bug would manifest as job.should_run being True when it should be False
    if now_berlin.hour > 0:  # If it's past midnight
        if job.should_run:
            print("❌ BUG REPRODUCED: Job should_run is True when it should be False!")
            print("This means the job would execute immediately instead of waiting for next midnight")
            return False
        else:
            print("✅ No bug: Job correctly scheduled for next midnight")
            return True
    else:
        print("Current time is at midnight, immediate execution is expected")
        return True

def test_with_original_logic():
    """Test what would happen with the original (buggy) logic."""
    print("\n=== Testing with original logic simulation ===")

    berlin_tz = pytz.timezone("Europe/Berlin")

    # Simulate the original _schedule_next_run logic
    now = datetime.datetime.now(berlin_tz)
    next_run = now

    print(f"1. now: {now}")
    print(f"2. next_run = now: {next_run}")

    # Move to midnight (00:00)
    next_run = next_run.replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"3. After moving to 00:00: {next_run}")

    # Original logic: simple comparison
    print(f"4. Original comparison: next_run <= now")
    print(f"   {next_run} <= {now}")
    print(f"   Result: {next_run <= now}")

    # If next_run <= now, advance by one day
    if next_run <= now:
        print("5. Original logic would advance by one day")
        period = datetime.timedelta(days=1)
        next_run += period
        print(f"   After advancing: {next_run}")

    # Check if this would cause the bug
    # The bug would occur if the comparison fails to advance properly

    return True

if __name__ == "__main__":
    test_original_bug_scenario()
    test_with_original_logic()
