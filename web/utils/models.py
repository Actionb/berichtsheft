import calendar
from datetime import date, timedelta
from typing import Optional

from django.apps import apps

from web import models as _models
from web.utils import date as date_utils
from web.utils.date import count_week_numbers, get_week_friday, get_week_monday


def _get_soft_delete_models(app_label="web"):
    for model in apps.get_app_config(app_label).get_models():
        if hasattr(model, "deleted_objects"):
            yield model


def collect_deleted_objects(user):
    """
    Collect all soft-deleted items for the current user

    Returns a list of deleted_objects querysets for every model.
    """
    objects = []
    for model in _get_soft_delete_models(app_label="web"):
        queryset = model.deleted_objects.filter(user=user)
        if queryset.exists():
            objects.append(queryset)
    return objects


def get_current_nachweis(user: _models.User) -> Optional[_models.Nachweis]:
    """
    Return the user's Nachweis object for the current interval.

    If the user has not created a Nachweis for the current interval or if no
    interval is set, return None.
    """
    user_nachweise = _models.Nachweis.objects.filter(user=user)
    today = date.today()
    match user.profile.interval:
        case user.profile.IntervalType.DAILY:
            start = end = today
        case user.profile.IntervalType.WEEKLY:
            start = get_week_monday(today)
            end = get_week_friday(today)
            # TODO: use an annotation to filter for Nachweis objects that lie
            # in the week's range instead?
            #   annotate(?=).filter(?__range=(start, end))
        case user.profile.IntervalType.MONTHLY:
            start = today.replace(day=1)
            end = today.replace(day=calendar.monthrange(today.year, today.month)[-1])
        case _:
            return
    return user_nachweise.filter(datum_start=start, datum_ende=end).first()


def get_missing_nachweise(user: _models.User) -> list[tuple[date, date]]:
    """
    Look for any gaps in the Nachweis chain and return the dates of missing
    Nachweis objects, with the most recent gap first.
    """
    user_nachweise = _models.Nachweis.objects.filter(user=user)
    start = user.profile.start_date  # TODO: handle no start date
    today = date.today()
    nachweis_dates = user_nachweise.values_list("datum_start", flat=True)
    match user.profile.interval:
        case user.profile.IntervalType.DAILY:
            # To determine the gaps in a DAILY schedule, compare the set of
            # Nachweis dates with a set of all business days since the start of
            # the user's Ausbildung.

            # Create a set of all business days since the start of the Ausbildung:
            # https://www.geeksforgeeks.org/python/python-program-to-get-total-business-days-between-two-dates/
            bdays = set()
            for day_delta in range((today - start).days):
                d = start + timedelta(days=day_delta)
                if d.isoweekday() < 6:
                    bdays.add(d)

            # Subtract all Nachweis dates to get the gaps:
            missing = bdays.difference(nachweis_dates)
            return [(d, d) for d in sorted(missing, reverse=True)]
        case user.profile.IntervalType.WEEKLY:
            # To determine the gaps in a WEEKLY schedule, compare a set of
            # Mondays since the start of the Ausbildung with the Mondays of
            # Nachweis objects (datum_start).
            mondays = set()

            start_monday = get_week_monday(start + timedelta(weeks=1))
            # Exclude the current week (handled by get_current_nachweis):
            end_monday = get_week_monday(today - timedelta(weeks=1))

            for week_delta in range(count_week_numbers(start_monday, end_monday)):
                mondays.add(start_monday + timedelta(weeks=week_delta))
            missing = mondays.difference(nachweis_dates)

            # Check if there is a Nachweis for the very first week
            # (which may not have started on a Monday):
            if not nachweis_dates.filter(datum_start=start).exists():
                missing.add(start)

            return [(d, get_week_friday(d)) for d in sorted(missing, reverse=True)]
        case user.profile.IntervalType.MONTHLY:
            # To determine the gaps in a MONTHLY schedule, compare a set of
            # first days of a month since the start of the Ausbildung with the
            # first days of Nachweis objects.
            firsts = set()
            month = timedelta(days=31)

            # Start on the month after the first; Nachweis for the first month
            # must be handled differently since it is not guaranteed that the
            # Ausbildung began on the 1st exactly.
            d = (start + month).replace(day=1)
            while d < today:
                firsts.add(d)
                d = (d + month).replace(day=1)
            missing = firsts.difference(nachweis_dates)

            # Check if there is a Nachweis for the very first month:
            if not nachweis_dates.filter(datum_start=start).exists():
                missing.add(start)

            return [
                (d, date(d.year, d.month, calendar.monthrange(d.year, d.month)[1]))
                for d in sorted(missing, reverse=True)
            ]
        case _:
            return []


def initial_data_for_date(user: _models.User, d: date) -> dict:
    """Create useful initial data for Nachweis forms for the given date and user."""
    # Determine the date ranges for the given interval:
    match user.profile.interval:
        case _models.UserProfile.IntervalType.DAILY:
            start = end = d
        case _models.UserProfile.IntervalType.WEEKLY:
            start = date.fromisocalendar(d.year, d.isocalendar()[1], day=1)
            end = date.fromisocalendar(d.year, d.isocalendar()[1], day=5)
        case _models.UserProfile.IntervalType.MONTHLY:
            start = d.replace(day=1)
            end = d.replace(day=calendar.monthrange(d.year, d.month)[1])
        case _:  # pragma: no cover
            return {}

    initial = {
        "jahr": start.year,
        "kalenderwoche": start.isocalendar()[1],
        "datum_start": start,
        "datum_ende": end,
    }
    user_start_date = user.profile.start_date
    if user_start_date:
        # Derive additional initial data from the user's start date:
        initial["ausbildungswoche"] = date_utils.count_week_numbers(user_start_date, start)
        match user.profile.interval:
            case _models.UserProfile.IntervalType.DAILY:
                initial["nummer"] = date_utils.count_business_days(user_start_date, start)
            case _models.UserProfile.IntervalType.WEEKLY:
                initial["nummer"] = initial["ausbildungswoche"]
            case _models.UserProfile.IntervalType.MONTHLY:
                initial["nummer"] = date_utils.count_months(user_start_date, start) + 1
    return initial
