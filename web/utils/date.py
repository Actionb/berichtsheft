from datetime import date


def count_week_numbers(start, end):
    """Count the week numbers from the start date to the end date."""
    if end < start:
        return 0
    # Use the first day of the start week as the beginning, and the first day
    # of the end week as the end:
    first_day_of_start_week = date.fromisocalendar(start.isocalendar()[0], start.isocalendar()[1], 1)
    first_day_of_end_week = date.fromisocalendar(end.isocalendar()[0], end.isocalendar()[1], 1)
    # Now convert the timedelta in days to weeks (+1):
    return (first_day_of_end_week - first_day_of_start_week).days // 7 + 1
