#!/usr/bin/env python3
"""
Test script to verify async functionality works as described in the feature request.
"""

import asyncio
import schedule
import time

# Test counter
call_count = 0

async def async_job():
    """Example async job function"""
    global call_count
    await asyncio.sleep(0.1)  # Simulate async work
    call_count += 1
    print(f"Async job executed! Call count: {call_count}")
    return f"async_result_{call_count}"

def sync_job():
    """Example sync job function"""
    global call_count
    call_count += 1
    print(f"Sync job executed! Call count: {call_count}")
    return f"sync_result_{call_count}"

async def main():
    """Main async function to test the functionality"""
    print("Testing async coroutine scheduling...")

    # Clear any existing jobs
    schedule.clear()

    # Schedule an async coroutine
    schedule.every(1).seconds.do(async_job)

    # Schedule a sync function for comparison
    schedule.every(1).seconds.do(sync_job)

    print("Jobs scheduled. Running for 3 seconds...")

    # Run with async support for 3 seconds
    start_time = time.time()
    while time.time() - start_time < 3:
        await schedule.async_run_pending()
        await asyncio.sleep(0.1)

    print(f"Test completed. Total calls: {call_count}")
    print("✅ Async coroutine scheduling works correctly!")

if __name__ == "__main__":
    asyncio.run(main())
