import calendar
from datetime import date
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
    def user(self, create_user, interval):
        user = create_user()
        user.profile.interval = interval
        user.profile.save()
        return user

    @pytest.fixture
    def missing(self, interval, user, today):
        """
        Create Nachweis objects with "gaps".

        Return a list specifying the gaps as 2-tuples (<gap_start>, <gap_end>).
        """
        year = today.isocalendar()[0]
        week = today.isocalendar()[1]
        missing = []
        match interval:
            case _models.UserProfile.IntervalType.DAILY:
                # Create Nachweise for Monday, Wednesday and Friday of the week
                # "before" today:
                week -= 1
                for weekday in range(1, 6):
                    d = date.fromisocalendar(year, week, weekday)
                    if weekday % 2:
                        missing.append((d, d))
                    else:
                        NachweisFactory(user=user, datum_start=d, datum_ende=d)
            case _models.UserProfile.IntervalType.WEEKLY:
                # Create Nachweis objects for the last few weeks except for the
                # week before last:
                for i, week_ in enumerate(range(week - 3, week)):
                    start = date.fromisocalendar(year, week_, 1)
                    end = date.fromisocalendar(year, week_, 5)
                    if i == 1:
                        missing.append((start, end))
                    else:
                        NachweisFactory(user=user, datum_start=start, datum_ende=end)
            case _models.UserProfile.IntervalType.MONTHLY:
                # Create Nachweis objects for the last months except for the
                # month before last:
                for i, month in enumerate(range(today.month - 3, today.month)):
                    last_day = calendar.monthrange(year, month)[-1]
                    start = date(year, month, 1)
                    end = date(year, month, last_day)
                    if i == 1:
                        missing.append((start, end))
                    else:
                        NachweisFactory(user=user, datum_start=start, datum_ende=end)
        return missing

    def test_get_missing_nachweise(self, user, missing):
        """
        Assert that get_missing_nachweise returns the dates for the missing
        Nachweis objects.
        """
        assert utils.get_missing_nachweise(user) == missing

    @pytest.mark.usefixtures("missing")
    @pytest.mark.parametrize("interval", [_models.UserProfile.IntervalType.OTHER])
    def test_no_interval(self, user):
        """
        Assert that get_missing_nachweise returns None if the user did not set
        a usable interval.
        """
        assert utils.get_missing_nachweise(user) is None
