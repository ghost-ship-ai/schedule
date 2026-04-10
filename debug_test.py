#!/usr/bin/env python3

import datetime
import schedule
from test_schedule import mock_datetime, make_mock_job

def debug_test():
    """Debug the DST test case."""

    # Clear any existing jobs
    schedule.clear()

    mock_job = make_mock_job()

    print("=== Test case 1: fold=0 ===")
    with mock_datetime(2023, 10, 29, 2, 30, fold=0):
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)
        print(f"Next run: {job.next_run}")
        print(f"Day: {job.next_run.day}, Hour: {job.next_run.hour}, Minute: {job.next_run.minute}")
        print(f"Should run: {job.should_run}")

    print("\n=== Test case 2: fold=1 ===")
    with mock_datetime(2023, 10, 29, 2, 30, fold=1):
        job = schedule.every().day.at("02:30", "Europe/Berlin").do(mock_job)
        print(f"Next run: {job.next_run}")
        print(f"Day: {job.next_run.day}, Hour: {job.next_run.hour}, Minute: {job.next_run.minute}")
        print(f"Should run: {job.should_run}")

if __name__ == "__main__":
    debug_test()
