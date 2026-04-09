#!/usr/bin/env python3

import asyncio
import schedule
import datetime

async def test_async_job():
    print("Async job executed!")
    return "async_result"

def test_sync_job():
    print("Sync job executed!")
    return "sync_result"

# Test basic scheduling
scheduler = schedule.Scheduler()

# Schedule both types of jobs
async_job = scheduler.every(1).seconds.do(test_async_job)
sync_job = scheduler.every(1).seconds.do(test_sync_job)

print(f"Async job is_async: {async_job.is_async}")
print(f"Sync job is_async: {sync_job.is_async}")

print(f"Async job next_run: {async_job.next_run}")
print(f"Sync job next_run: {sync_job.next_run}")

print(f"Current time: {datetime.datetime.now()}")

print(f"Async job should_run: {async_job.should_run}")
print(f"Sync job should_run: {sync_job.should_run}")

# Test sync execution
print("\n--- Testing sync execution ---")
scheduler.run_pending()

# Test async execution
print("\n--- Testing async execution ---")
async def run_async_test():
    await scheduler.async_run_pending()

asyncio.run(run_async_test())
