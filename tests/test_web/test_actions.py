from datetime import date
from unittest import mock
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.urls import path

from tests.test_web.model_factory import NachweisDummyFactory
from tests.test_web.models import NachweisDummy
from web import actions
from web import models as _models


def dummy_view(*_args, **_kwargs):
    return HttpResponse("test")  # pragma: no cover


urlpatterns = [
    path("test/list/action", dummy_view, name="list_action_test"),
    path("test/<path:pk>/model", dummy_view, name="model_action_test"),
    path("test/<path:pk>/change", dummy_view, name="change_perm_action_test"),
    path("test/nachweis/add", dummy_view, name="nachweis_add"),
]

pytestmark = pytest.mark.urls(__name__)


class TestListAction:
    def test_render(self, rf):
        """Assert the action link/button is rendered as expected."""
        action = actions.ListAction(url_name="list_action_test", label="Action Test", title="bar", css="foo")
        assert (
            action.render(request=rf.get("/"), row={})
            == '<a href="/test/list/action" class="foo" title="bar">Action Test</a>'
        )

    def test_render_empty_string_if_missing_perms(self, rf):
        """
        Assert that render returns an empty string if has_permission returns
        False.
        """
        action = actions.ListAction(url_name="list_action_test")
        with mock.patch.object(action, "has_permission", new=mock.Mock(return_value=False)):
            assert action.render(request=rf.get("/"), row={}) == ""


class TestModelAction:
    def test_render(self, rf):
        """Assert the action link/button is rendered as expected."""
        action = actions.ModelAction(url_name="model_action_test", label="Action Test", title="bar", css="foo")
        assert (
            action.render(request=rf.get("/"), row={"obj": mock.Mock(pk=42)})
            == '<a href="/test/42/model" class="foo" title="bar">Action Test</a>'
        )


@pytest.mark.usefixtures("login_user")
class TestChangePermAction:
    @pytest.fixture
    def obj(self):
        return NachweisDummyFactory(pk=42)

    @pytest.mark.parametrize("user_perms", [[("change", NachweisDummy)]])
    @pytest.mark.usefixtures("user_perms", "set_user_perms")
    def test_render_change_permission(self, get_user_req, obj):
        """
        Assert that the action button is rendered normally if the user has
        change permissions.
        """
        action = actions.ChangePermAction(url_name="change_perm_action_test", label="Action Test")
        assert (
            action.render(request=get_user_req, row={"obj": obj})
            == f'<a href="/test/42/change" class="{action.css}" title="">Action Test</a>'
        )

    def test_render_no_change_permission(self, get_user_req, obj):
        """
        Assert that the action button is rendered as an empty string if the
        user does not have change permissions.
        """
        action = actions.ChangePermAction(url_name="change_perm_action_test", label="Action Test")
        assert action.render(request=get_user_req, row={"obj": obj}) == ""


@pytest.mark.usefixtures("login_user")
class TestAddMissingAction:
    @pytest.fixture
    def action(self):
        return actions.AddMissingAction()

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
    def start_date(self):
        """The start_date of the user's Ausbildung."""
        return date(2025, 8, 1)

    @pytest.fixture
    def user(self, create_user, interval, start_date):
        user = create_user()
        # 'nummer' and other values are calculated from the start date:
        user.profile.start_date = start_date
        user.profile.interval = interval
        user.profile.save()
        return user

    @pytest.fixture
    def dates(self, interval):
        """Return start and end dates for a missing Nachweis."""
        match interval:
            case _models.UserProfile.IntervalType.DAILY:
                # The next business day after the start_date 2025-08-01:
                start = end = date(2025, 8, 4)
            case _models.UserProfile.IntervalType.WEEKLY:
                start = date(2025, 8, 4)
                end = date(2025, 8, 8)
            case _models.UserProfile.IntervalType.MONTHLY:
                start = date(2025, 9, 1)
                end = date(2025, 9, 30)
            case _:  # pragma: no cover
                raise Exception("Unknown interval.")
        return start, end

    @pytest.fixture
    def expected(self, interval, dates):
        """
        Return the expected initial data for given start and end dates of a
        missing Nachweis.
        """
        start, end = dates
        expected = {
            "nummer": 2,
            "jahr": start.year,
            "kalenderwoche": start.isocalendar()[1],
            "datum_start": start,
            "datum_ende": end,
        }
        match interval:
            case _models.UserProfile.IntervalType.DAILY:
                expected["ausbildungswoche"] = 2
            case _models.UserProfile.IntervalType.WEEKLY:
                expected["ausbildungswoche"] = 2
            case _models.UserProfile.IntervalType.MONTHLY:
                expected["ausbildungswoche"] = 6
            case _:  # pragma: no cover
                raise Exception("Unknown interval.")

        return expected

    @pytest.mark.parametrize(
        "user_perms, has_perms",
        [([("add", _models.Nachweis)], True), (None, False)],
    )
    @pytest.mark.usefixtures("user_perms", "set_user_perms")
    def test_requires_add_permission(self, get_user_req, action, has_perms, dates):
        """
        Assert that the action is only rendered for users that can add Nachweis
        objects.
        """
        start, end = dates
        assert bool(action.render(get_user_req, row={"start": start, "end": end})) == has_perms

    def test_get_initial_data(self, get_user_req, action, dates, expected):
        """
        Assert that get_initial_data returns the expected data for a given set
        of dates.
        """
        start, end = dates
        assert action.get_initial_data(request=get_user_req, row={"start": start, "end": end}) == expected

    @pytest.mark.parametrize("user_perms", [[("add", _models.Nachweis)]])
    @pytest.mark.usefixtures("user_perms", "set_user_perms")
    def test_render_querystring(self, get_user_req, action, dates, expected):
        """
        Assert that the initial data is added to the rendered link's URL as a
        query string.
        """
        start, end = dates
        soup = BeautifulSoup(action.render(request=get_user_req, row={"start": start, "end": end}), "html.parser")
        url = soup.find("a").attrs["href"]
        assert parse_qs(urlparse(url).query) == parse_qs(urlencode(expected))
