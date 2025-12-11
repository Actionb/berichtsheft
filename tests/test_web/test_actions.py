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
    path("test/list/action", dummy_view, name="list_action_test"),
    path("test/<path:pk>/model", dummy_view, name="model_action_test"),
    path("test/<path:pk>/change", dummy_view, name="change_perm_action_test"),
]

pytestmark = pytest.mark.urls(__name__)


class TestListAction:
    def test_render(self, rf):
        """Assert the action link/button is rendered as expected."""
        action = actions.ListAction(url_name="list_action_test", label="Action Test", css="foo")
        assert action.render(request=rf.get("/")) == '<a href="/test/list/action" class="foo">Action Test</a>'

    def test_render_empty_string_if_missing_perms(self, rf):
        """
        Assert that render returns an empty string if has_permission returns
        False.
        """
        action = actions.ListAction(url_name="list_action_test")
        with mock.patch.object(action, "has_permission", new=mock.Mock(return_value=False)):
            assert action.render(request=rf.get("/")) == ""


class TestModelAction:
    def test_render(self, rf):
        """Assert the action link/button is rendered as expected."""
        action = actions.ModelAction(url_name="model_action_test", label="Action Test", css="foo")
        assert (
            action.render(request=rf.get("/"), obj=mock.Mock(pk=42))
            == '<a href="/test/42/model" class="foo">Action Test</a>'
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
            action.render(request=get_user_req, obj=obj)
            == f'<a href="/test/42/change" class="{action.css}">Action Test</a>'
        )

    def test_render_no_change_permission(self, get_user_req, obj):
        """
        Assert that the action button is rendered as an empty string if the
        user does not have change permissions.
        """
        action = actions.ChangePermAction(url_name="change_perm_action_test", label="Action Test")
        assert action.render(request=get_user_req, obj=obj) == ""
