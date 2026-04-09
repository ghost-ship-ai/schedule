#!/usr/bin/env python3
"""
Test script that reproduces the exact example from the problem statement.
This should demonstrate that the issue is fixed.
"""

import schedule
import threading
import time
from datetime import datetime

def do_task():
    print(f"{datetime.now().isoformat()} - task execution - thread {threading.current_thread().name}")

schedule.every(5).seconds.do(do_task)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Two threads sharing the default scheduler
t1 = threading.Thread(target=run_scheduler, name="Thread-1", daemon=True)
t2 = threading.Thread(target=run_scheduler, name="Thread-2", daemon=True)
t1.start()
t2.start()

time.sleep(30)

print("Test completed. The task should have run approximately every 5 seconds (6 times in 30 seconds).")
print("If you see duplicate executions at the same timestamp, the thread safety issue still exists.")
print("If you see executions roughly every 5 seconds from different threads (but not simultaneously), the fix is working.")
