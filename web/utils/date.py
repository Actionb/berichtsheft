from datetime import date, timedelta


def get_week_monday(d: date) -> date:  # pragma: no cover
    """Return the date object for the Monday in given date's `d` week."""
    return date.fromisocalendar(d.isocalendar()[0], d.isocalendar()[1], 1)


def get_week_friday(d: date) -> date:  # pragma: no cover
    """Return the date object for the Friday in given date's `d` week."""
    return date.fromisocalendar(d.isocalendar()[0], d.isocalendar()[1], 5)


def count_week_numbers(start: date, end: date) -> int:
    """Count the week numbers from the start date to the end date."""
    if end < start:
        return 0
    # Use the first day of the start week as the beginning, and the first day
    # of the end week as the end:
    first_day_of_start_week = date.fromisocalendar(start.isocalendar()[0], start.isocalendar()[1], 1)
    first_day_of_end_week = date.fromisocalendar(end.isocalendar()[0], end.isocalendar()[1], 1)
    # Now convert the timedelta in days to weeks (+1):
    return (first_day_of_end_week - first_day_of_start_week).days // 7 + 1


def count_months(start: date, end: date) -> int:
    """Count the number of months between the given start and end date."""
    if end < start:
        return 0
    start = start.replace(day=1)
    end = end.replace(day=1)
    return (end.year - start.year) * 12 + end.month - start.month


def count_business_days(start: date, end: date) -> int:
    """
    Count the number of business days between the given start and (inclusive)
    end date.
    """
    if end < start:
        return 0
    c = 0
    for day_delta in range((end - start).days + 1):
        d = start + timedelta(days=day_delta)
        if d.isoweekday() < 6:
            c += 1
    return c
