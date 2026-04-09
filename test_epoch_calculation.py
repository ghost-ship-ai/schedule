#!/usr/bin/env python3
"""
Test the epoch calculation logic in _move_to_next_weekday_with_interval
"""

import datetime

def test_epoch_calculation():
    # Current implementation uses this epoch
    epoch = datetime.datetime(1970, 1, 5)  # Monday, Jan 5, 1970
    print(f"Epoch: {epoch} ({epoch.strftime('%A')})")

    # Current time
    now = datetime.datetime.now()
    print(f"Now: {now} ({now.strftime('%A')})")

    # Find next Monday
    weekday_index = 0  # Monday = 0
    days_ahead = weekday_index - now.weekday()
    if days_ahead < 0:
        days_ahead += 7
    next_monday = now + datetime.timedelta(days=days_ahead)
    print(f"Next Monday: {next_monday}")

    # Calculate weeks since epoch for next Monday
    weeks_since_epoch = (next_monday - epoch).days // 7
    print(f"Weeks since epoch for next Monday: {weeks_since_epoch}")

    # Test different intervals
    for interval in [1, 2, 3, 4]:
        remainder = weeks_since_epoch % interval
        print(f"Interval {interval}: weeks_since_epoch % {interval} = {remainder}")

        if remainder == 0:
            aligned_monday = next_monday
            print(f"  -> Next Monday ({next_monday.date()}) is aligned for interval {interval}")
        else:
            weeks_to_add = interval - remainder
            aligned_monday = next_monday + datetime.timedelta(weeks=weeks_to_add)
            print(f"  -> Need to add {weeks_to_add} weeks -> {aligned_monday.date()}")

if __name__ == "__main__":
    test_epoch_calculation()
