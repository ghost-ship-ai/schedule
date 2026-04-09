#!/usr/bin/env python3
"""
Test improved multi-week scheduling logic
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

def _move_to_next_weekday_with_interval_improved(moment: datetime.datetime, weekday: str, interval: int):
    """
    Improved logic for multi-week scheduling that uses the current moment as reference
    instead of an arbitrary epoch.
    """
    if interval == 1:
        return _move_to_next_weekday(moment, weekday)

    # Find the next occurrence of the target weekday
    next_weekday = _move_to_next_weekday(moment, weekday)

    # For multi-week intervals, we want to ensure consistent scheduling
    # Use the current moment as the reference point for the cycle

    # Calculate how many days since the start of the week (Monday = 0)
    days_since_monday = moment.weekday()
    week_start = moment - datetime.timedelta(days=days_since_monday)

    # Calculate how many weeks have passed since a reference point
    # Use a fixed reference that's far enough in the past but not arbitrary
    # Let's use the start of the current year as a more meaningful reference
    year_start = datetime.datetime(moment.year, 1, 1)

    # Find the first Monday of the year (or before)
    days_to_first_monday = (0 - year_start.weekday()) % 7
    first_monday_of_year = year_start + datetime.timedelta(days=days_to_first_monday)

    # Calculate weeks since the first Monday of the year
    weeks_since_reference = (next_weekday.date() - first_monday_of_year.date()).days // 7

    # Check if this week aligns with our interval
    if weeks_since_reference % interval == 0:
        return next_weekday

    # If not, move to the next aligned week
    weeks_to_add = interval - (weeks_since_reference % interval)
    return next_weekday + datetime.timedelta(weeks=weeks_to_add)

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

# Test both approaches
def test_approaches():
    # Test with current time
    now = datetime.datetime.now()
    print(f"Current time: {now} ({now.strftime('%A')})")

    for interval in [1, 2, 3, 4]:
        print(f"\n--- Interval: {interval} weeks ---")

        current_result = _move_to_next_weekday_with_interval_current(now, "monday", interval)
        improved_result = _move_to_next_weekday_with_interval_improved(now, "monday", interval)

        print(f"Current approach:  {current_result.date()} ({current_result.strftime('%A')})")
        print(f"Improved approach: {improved_result.date()} ({improved_result.strftime('%A')})")

        if current_result != improved_result:
            print(f"DIFFERENCE: {(improved_result - current_result).days} days")

if __name__ == "__main__":
    test_approaches()
