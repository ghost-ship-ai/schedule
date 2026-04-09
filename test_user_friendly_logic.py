#!/usr/bin/env python3
"""
Test a more user-friendly multi-week scheduling logic
"""

import datetime

def _move_to_next_weekday(moment: datetime.datetime, weekday: str):
    """Original logic for finding next weekday"""
    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    weekday_index = weekdays.index(weekday)

    days_ahead = weekday_index - moment.weekday()
    if days_ahead < 0:
        # Target day already happened this week, move to next week
        days_ahead += 7
    return moment + datetime.timedelta(days=days_ahead)

def _move_to_next_weekday_with_interval_user_friendly(moment: datetime.datetime, weekday: str, interval: int):
    """
    User-friendly logic: The first occurrence is the next occurrence of the weekday,
    and subsequent occurrences are exactly `interval` weeks apart from that.

    This is more intuitive because:
    1. If I schedule every(2).weeks.monday on a Thursday, it will run next Monday
    2. Then it will run exactly 2 weeks after that Monday
    3. The schedule is predictable and doesn't depend on arbitrary reference points
    """
    if interval == 1:
        return _move_to_next_weekday(moment, weekday)

    # For multi-week intervals, simply find the next occurrence of the weekday
    # The interval will be handled by the scheduling logic that adds the period
    return _move_to_next_weekday(moment, weekday)

def _move_to_next_weekday_with_interval_current(moment: datetime.datetime, weekday: str, interval: int):
    """Current implementation from the codebase"""
    if interval == 1:
        return _move_to_next_weekday(moment, weekday)

    # Find the next occurrence of the weekday
    next_weekday = _move_to_next_weekday(moment, weekday)

    # For multi-week intervals, we need to ensure we're on the right week boundary
    # We'll use a reference point (epoch) and calculate weeks from there
    epoch = datetime.datetime(1970, 1, 5)  # Monday, Jan 5, 1970 (first Monday after epoch)

    # Calculate how many weeks have passed since the epoch
    weeks_since_epoch = (next_weekday - epoch).days // 7

    # Check if this week aligns with our interval
    if weeks_since_epoch % interval == 0:
        return next_weekday

    # If not, move to the next aligned week
    weeks_to_add = interval - (weeks_since_epoch % interval)
    return next_weekday + datetime.timedelta(weeks=weeks_to_add)

# Test the user-friendly approach
def test_user_friendly_approach():
    # Test with different starting days
    test_dates = [
        datetime.datetime(2026, 4, 7, 10, 0),   # Monday
        datetime.datetime(2026, 4, 8, 10, 0),   # Tuesday
        datetime.datetime(2026, 4, 9, 10, 0),   # Wednesday
        datetime.datetime(2026, 4, 10, 10, 0),  # Thursday
        datetime.datetime(2026, 4, 11, 10, 0),  # Friday
        datetime.datetime(2026, 4, 12, 10, 0),  # Saturday
        datetime.datetime(2026, 4, 13, 10, 0),  # Sunday
    ]

    for test_date in test_dates:
        print(f"\n--- Starting from {test_date.date()} ({test_date.strftime('%A')}) ---")

        for interval in [1, 2, 3]:
            current_result = _move_to_next_weekday_with_interval_current(test_date, "monday", interval)
            user_friendly_result = _move_to_next_weekday_with_interval_user_friendly(test_date, "monday", interval)

            print(f"Interval {interval}: Current={current_result.date()}, User-friendly={user_friendly_result.date()}")

            if current_result != user_friendly_result:
                print(f"  DIFFERENCE: {(current_result - user_friendly_result).days} days")

if __name__ == "__main__":
    test_user_friendly_approach()
