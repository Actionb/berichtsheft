import calendar
from datetime import date
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
