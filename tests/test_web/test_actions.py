from unittest import mock

import pytest
from django.http import HttpResponse
from django.urls import path

from tests.test_web.model_factory import NachweisDummyFactory
from tests.test_web.models import NachweisDummy
from web import actions


def dummy_view(*_args, **_kwargs):
    return HttpResponse("test")  # pragma: no cover


urlpatterns = [
    path("test/<path:pk>/action", dummy_view, name="list_action_test"),
]

pytestmark = pytest.mark.urls(__name__)


class TestListAction:
    def test_render(self, rf):
        """Assert the action link/button is rendered as expected."""
        action = actions.ListAction(url_name="list_action_test", label="Action Test", css="foo bar")
        assert (
            action.render(request=rf.get("/"), obj=mock.Mock(pk=42))
            == '<a href="/test/42/action" class="foo bar">Action Test</a>'
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
        action = actions.ChangePermAction(url_name="list_action_test", label="Action Test")
        assert (
            action.render(request=get_user_req, obj=obj)
            == f'<a href="/test/42/action" class="{action.css}">Action Test</a>'
        )

    def test_render_no_change_permission(self, get_user_req, obj):
        """
        Assert that the action button is rendered as an empty string if the
        user does not have change permissions.
        """
        action = actions.ChangePermAction(url_name="list_action_test", label="Action Test")
        assert action.render(request=get_user_req, obj=obj) == ""
