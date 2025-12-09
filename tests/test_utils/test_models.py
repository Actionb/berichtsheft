from calendar import monthrange
from datetime import date, timedelta
from unittest import mock

import pytest

from tests.model_factory import NachweisFactory
from web import models as _models
from web.utils import models as utils

from .models import SoftDeleteTestModel


@pytest.fixture
def obj(user):
    return SoftDeleteTestModel.objects.create(name="Foo", user=user)


@pytest.fixture
def deleted_obj(user):
    """Create an object that has been deleted."""
    obj = SoftDeleteTestModel.objects.create(name="Bar", user=user)
    obj.delete()
    return obj


@pytest.fixture
def not_user_obj(superuser):
    """Create an object that has also been deleted, but belongs to another user."""
    obj = SoftDeleteTestModel.objects.create(name="Baz", user=superuser)
    obj.delete()
    return obj


def test_get_soft_delete_models():
    """Assert that _get_soft_delete_models returns the expected models."""
    assert list(utils._get_soft_delete_models("test_utils")) == [SoftDeleteTestModel]


def test_collect_deleted_objects(user, obj, deleted_obj, not_user_obj):
    """Assert that collect_deleted_objects returns the expected items."""
    with mock.patch("web.utils.models._get_soft_delete_models", new=mock.Mock(return_value=[SoftDeleteTestModel])):
        objs = utils.collect_deleted_objects(user)
    queryset = objs[0]
    assert deleted_obj in queryset
    assert obj not in queryset
    assert not_user_obj not in queryset


class TestGetCurrentNachweis:
    @pytest.fixture
    def today(self):
        """The date that marks 'today' in regard to the Nachweis fetching tests."""
        return date(2025, 12, 4)

    @pytest.fixture(autouse=True)
    def mock_today(self, today):
        """Mock out the built-in date.today function."""
        # https://stackoverflow.com/a/55187924
        with mock.patch("web.utils.models.date", wraps=date) as m:
            m.today.return_value = today
            yield m

    @pytest.fixture(
        params=[
            _models.UserProfile.IntervalType.DAILY,
            _models.UserProfile.IntervalType.WEEKLY,
            _models.UserProfile.IntervalType.MONTHLY,
        ]
    )
    def interval(self, request):
        """The interval between Nachweis objects."""
        return request.param

    @pytest.fixture
    def user(self, create_user, interval):
        user = create_user()
        user.profile.interval = interval
        user.profile.save()
        return user

    @pytest.fixture(autouse=True)
    def control_obj(self, user):
        """A control object that should not turn up as a result."""
        return NachweisFactory(user=user)

    @pytest.fixture
    def current_obj(self, user, today, interval):
        """Create and return the 'current' object according to the given interval."""
        match interval:
            case _models.UserProfile.IntervalType.DAILY:
                start = end = today
            case _models.UserProfile.IntervalType.WEEKLY:
                start = date(2025, 12, 1)
                end = date(2025, 12, 5)
            case _models.UserProfile.IntervalType.MONTHLY:
                start = date(2025, 12, 1)
                end = date(2025, 12, 31)
        return NachweisFactory(user=user, datum_start=start, datum_ende=end)

    def test_current_nachweis(self, user, current_obj):
        """
        Assert that get_current_nachweis returns the user's current Nachweis
        object, according to the user-specified interval.
        """
        assert utils.get_current_nachweis(user) == current_obj

    def test_current_nachweis_no_nachweis(self, user):
        """
        Assert that get_current_nachweis returns None if the user has not
        created a Nachweis object within the current interval.
        """
        assert utils.get_current_nachweis(user) is None

    @pytest.mark.parametrize("interval", [_models.UserProfile.IntervalType.OTHER])
    def test_current_nachweis_no_interval(self, user):
        """
        Assert that get_current_nachweis returns None if the user has set a
        different interval.
        """
        assert utils.get_current_nachweis(user) is None


class TestGetMissingNachweise:
    @pytest.fixture
    def today(self):
        """The date that marks 'today' in regard to the Nachweis fetching tests."""
        return date(2025, 12, 4)

    @pytest.fixture(autouse=True)
    def mock_today(self, today):
        """Mock out the built-in date.today function."""
        # https://stackoverflow.com/a/55187924
        with mock.patch("web.utils.models.date", wraps=date) as m:
            m.today.return_value = today
            yield m

    @pytest.fixture(
        params=[
            _models.UserProfile.IntervalType.DAILY,
            _models.UserProfile.IntervalType.WEEKLY,
            _models.UserProfile.IntervalType.MONTHLY,
        ]
    )
    def interval(self, request):
        """The interval between Nachweis objects."""
        return request.param

    @pytest.fixture
    def start_date(self, today):
        """The start_date of the user's Ausbildung."""
        # Use the "previous" week's Monday:
        return date.fromisocalendar(today.year, today.isocalendar()[1] - 1, 1)

    @pytest.fixture
    def user(self, create_user, interval, start_date):
        user = create_user()
        user.profile.start_date = start_date
        user.profile.interval = interval
        user.profile.save()
        return user

    @pytest.mark.parametrize("interval", [_models.UserProfile.IntervalType.DAILY])
    @pytest.mark.parametrize("start_date", [date(2025, 11, 24)])
    @pytest.mark.parametrize("today", [date(2025, 12, 9)])
    def test_get_missing_daily(self, user, start_date, today):
        """
        Assert that get_missing_nachweise returns the dates for the missing
        Nachweis objects when using a DAILY schedule.
        """
        # Calendar for the test time frame, with the gap dates noted:
        # Mo | Tu | We | Th | Fr
        # 24   25                  November
        #       2          4       December
        #   8   today
        missing = [
            date(2025, 11, 24),
            date(2025, 11, 25),
            date(2025, 12, 2),
            date(2025, 12, 4),
            date(2025, 12, 8),
        ]

        for day_delta in range((today - start_date).days + 1):
            d = start_date + timedelta(days=day_delta)
            if d not in missing:
                NachweisFactory(user=user, datum_start=d, datum_ende=d)
        missing = [(d, d) for d in sorted(missing, reverse=True)]

        assert utils.get_missing_nachweise(user) == missing

    @pytest.mark.parametrize("interval", [_models.UserProfile.IntervalType.WEEKLY])
    @pytest.mark.parametrize("start_date", [date(2025, 11, 24)])
    @pytest.mark.parametrize("today", [date(2025, 12, 18)])
    def test_get_missing_weekly(self, user):
        """
        Assert that get_missing_nachweise returns the dates for the missing
        Nachweis objects when using a WEEKLY schedule.
        """
        # Calendar for the test time frame, with the gap weeks noted:
        # Mo | Tu | We | Th | Fr
        # 24                  28 Nachweis missing
        #  1                   5 ✅ - December
        #  8                  12 Nachweis missing
        # 15                  19 today
        missing = [
            (date(2025, 12, 8), date(2025, 12, 12)),
            (date(2025, 11, 24), date(2025, 11, 28)),
        ]
        NachweisFactory(user=user, datum_start=date(2025, 12, 1), datum_ende=date(2025, 12, 5))
        assert utils.get_missing_nachweise(user) == missing

    @pytest.mark.parametrize("interval", [_models.UserProfile.IntervalType.MONTHLY])
    @pytest.mark.parametrize("start_date", [date(2025, 9, 1)])
    @pytest.mark.parametrize("today", [date(2025, 12, 1)])
    def test_get_missing_monthly(self, user):
        """
        Assert that get_missing_nachweise returns the dates for the missing
        Nachweis objects when using a MONTHLY schedule.
        """
        missing = [
            (date(2025, 11, 1), date(2025, 11, monthrange(2025, 11)[1])),
            (date(2025, 9, 1), date(2025, 9, monthrange(2025, 9)[1])),
        ]
        NachweisFactory(user=user, datum_start=date(2025, 10, 1), datum_ende=date(2025, 10, monthrange(2025, 11)[1]))
        assert utils.get_missing_nachweise(user) == missing

    @pytest.mark.parametrize("interval", [_models.UserProfile.IntervalType.OTHER])
    def test_no_interval(self, user):
        """
        Assert that get_missing_nachweise returns None if the user did not set
        a usable interval.
        """
        assert utils.get_missing_nachweise(user) is None
