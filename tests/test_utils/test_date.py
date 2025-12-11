from datetime import date

import pytest

from web.utils.date import count_business_days, count_months, count_week_numbers


@pytest.mark.parametrize(
    "start, end, expected",
    [
        (date(year=2025, month=8, day=1), date(year=2025, month=8, day=1), 1),
        (date(year=2025, month=8, day=1), date(year=2025, month=7, day=30), 0),
        (date(year=2025, month=8, day=1), date(year=2025, month=8, day=4), 2),
        (date(year=2025, month=8, day=1), date(year=2025, month=12, day=26), 22),
        (date(year=2025, month=8, day=1), date(year=2026, month=1, day=1), 23),
        (date(year=2025, month=8, day=1), date(year=2027, month=1, day=1), 75),
        (date(year=2025, month=8, day=1), date(year=2027, month=8, day=2), 106),
    ],
)
def test_count_week_numbers(start, end, expected):
    assert count_week_numbers(start, end) == expected


@pytest.mark.parametrize(
    "start, end, expected",
    [
        (date(year=2025, month=8, day=1), date(year=2025, month=8, day=1), 0),
        (date(year=2025, month=8, day=1), date(year=2025, month=7, day=30), 0),
        (date(year=2025, month=8, day=1), date(year=2025, month=9, day=1), 1),
        (date(year=2025, month=8, day=31), date(year=2025, month=9, day=1), 1),
        (date(year=2025, month=8, day=1), date(year=2026, month=1, day=1), 5),
        (date(year=2025, month=8, day=1), date(year=2027, month=1, day=1), 17),
    ],
)
def test_count_months(start, end, expected):
    assert count_months(start, end) == expected


@pytest.mark.parametrize(
    "start, end, expected",
    [
        (date(year=2025, month=8, day=2), date(year=2025, month=8, day=2), 0),  # 2025-08-02 is a Saturday
        (date(year=2025, month=8, day=1), date(year=2025, month=8, day=1), 1),
        (date(year=2025, month=8, day=1), date(year=2025, month=8, day=2), 1),
        (date(year=2025, month=8, day=1), date(year=2025, month=8, day=4), 2),
        (date(year=2025, month=8, day=1), date(year=2025, month=8, day=11), 7),
        (date(year=2025, month=8, day=1), date(year=2025, month=7, day=30), 0),
    ],
)
def test_count_business_days(start, end, expected):
    assert count_business_days(start, end) == expected
