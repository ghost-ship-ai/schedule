#!/usr/bin/env python3
"""
Test script to reproduce the thread safety issue described in the problem statement.
This should demonstrate the issue before the fix and pass after the fix.
"""

import schedule
import threading
import time
from datetime import datetime
import sys


def test_thread_safety_issue():
    """
    Reproduce the thread safety issue where jobs fire too often when
    scheduler is used across multiple threads.
    """
    print("Testing thread safety issue...")

    # Clear any existing jobs
    schedule.clear()

    execution_count = 0
    execution_lock = threading.Lock()

    def do_task():
        nonlocal execution_count
        with execution_lock:
            execution_count += 1
            print(
                f"{datetime.now().isoformat()} - task execution #{execution_count} - thread {threading.current_thread().name}"
            )

    # Schedule a job to run every 1 second
    schedule.every(1).seconds.do(do_task)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(
                0.01
            )  # Check very frequently to increase chance of race condition

    # Four threads sharing the default scheduler to increase contention
    threads = []
    for i in range(4):
        t = threading.Thread(target=run_scheduler, name=f"Thread-{i+1}", daemon=True)
        threads.append(t)

    start_time = time.time()
    for t in threads:
        t.start()

    # Run for 8 seconds
    time.sleep(8)

    end_time = time.time()
    duration = end_time - start_time

    print(f"\nTest completed after {duration:.1f} seconds")
    print(f"Total executions: {execution_count}")
    print(f"Expected executions (every 1 second): ~{int(duration / 1)}")

    # Clear jobs for cleanup
    schedule.clear()

    # If we have significantly more executions than expected, we have the thread safety issue
    expected_executions = int(duration / 1)
    if execution_count > expected_executions * 1.3:  # Allow some tolerance
        print(
            f"❌ THREAD SAFETY ISSUE DETECTED: {execution_count} executions vs expected ~{expected_executions}"
        )
        return False
    else:
        print(
            f"✅ Thread safety appears to be working: {execution_count} executions vs expected ~{expected_executions}"
        )
        return True


if __name__ == "__main__":
    success = test_thread_safety_issue()
    sys.exit(0 if success else 1)
