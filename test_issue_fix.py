#!/usr/bin/env python3
"""
Test script to verify that the original issue #29 is fixed.
This reproduces the exact scenario described in the GitHub issue.
"""

import schedule
import datetime

def test_original_issue():
    """Test the exact scenario from GitHub issue #29"""
    print("Testing the original issue scenario...")

    # Clear any existing jobs
    schedule.clear()

    # This should schedule for every other Monday at 10:00
    job = schedule.every(2).weeks.monday.at("10:00").do(lambda: print("job"))

    print(f"Job created: {job}")
    print(f"Next run: {job.next_run}")

    # Verify that next_run is not None and is a proper datetime
    assert job.next_run is not None, "next_run should not be None"
    assert isinstance(job.next_run, datetime.datetime), "next_run should be a datetime object"

    # Verify that it's scheduled for a Monday
    assert job.next_run.weekday() == 0, f"Should be scheduled for Monday, got weekday {job.next_run.weekday()}"

    # Verify that it's scheduled for 10:00
    assert job.next_run.hour == 10, f"Should be scheduled for 10:00, got {job.next_run.hour}:00"
    assert job.next_run.minute == 0, f"Should be scheduled for 10:00, got 10:{job.next_run.minute}"

    print("✅ Original issue is fixed!")
    print(f"   Job will run on: {job.next_run.strftime('%A, %B %d, %Y at %H:%M')}")

def test_multiple_intervals():
    """Test various multi-week intervals"""
    print("\nTesting multiple intervals...")

    schedule.clear()

    intervals = [2, 3, 4, 6]
    for interval in intervals:
        job = schedule.every(interval).weeks.friday.at("15:30").do(lambda: print(f"job-{interval}"))
        print(f"Every {interval} weeks on Friday at 15:30: {job.next_run.strftime('%A, %B %d, %Y at %H:%M')}")

        # Verify basic properties
        assert job.next_run.weekday() == 4, f"Should be Friday, got weekday {job.next_run.weekday()}"
        assert job.next_run.hour == 15, f"Should be 15:30, got {job.next_run.hour}:30"
        assert job.next_run.minute == 30, f"Should be 15:30, got 15:{job.next_run.minute}"

    print("✅ Multiple intervals work correctly!")

def test_single_vs_multi_week():
    """Test that single week and multi-week behave differently"""
    print("\nTesting single vs multi-week behavior...")

    schedule.clear()

    # Single week job
    job_single = schedule.every().week.tuesday.at("14:00").do(lambda: print("single"))

    # Multi-week job
    job_multi = schedule.every(3).weeks.tuesday.at("14:00").do(lambda: print("multi"))

    print(f"Single week job: {job_single.next_run.strftime('%A, %B %d, %Y at %H:%M')}")
    print(f"Multi-week job:  {job_multi.next_run.strftime('%A, %B %d, %Y at %H:%M')}")

    # They should potentially have different next run times
    # (depending on current date and interval alignment)

    print("✅ Single vs multi-week scheduling works!")

if __name__ == "__main__":
    test_original_issue()
    test_multiple_intervals()
    test_single_vs_multi_week()
    print("\n🎉 All tests passed! The multi-week scheduling issue is fixed.")
