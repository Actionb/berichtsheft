import calendar
from datetime import date, timedelta
from typing import Optional

from django.apps import apps

from web import models as _models
from web.utils.date import get_week_friday, get_week_monday


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
    Nachweis objects.
    """
    user_nachweise = _models.Nachweis.objects.filter(user=user)
    start = user.profile.start_date  # TODO: handle no start date
    today = date.today()
    missing = []
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
            missing = bdays.difference(user_nachweise.values_list("datum_start", flat=True))
            # Return with the most recent gaps first:
            return [(d, d) for d in sorted(missing, reverse=True)]
        case _:
            pass
    # TODO: needs to be able to account for holidays, etc.
    # TODO: this requires a calendar of sorts where users can enter their holidays
