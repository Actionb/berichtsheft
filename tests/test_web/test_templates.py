from collections import OrderedDict
from unittest import mock

import pytest
from bs4 import BeautifulSoup
from django import forms
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import path

from tests.model_factory import NachweisFactory
from web import models as _models
from web.actions import ModelAction


def dummy_view(*_args, **_kwargs):
    return HttpResponse("test")  # pragma: no cover


urlpatterns = [
    path("test/<path:pk>/action", dummy_view, name="test"),
    path("test/add", dummy_view, name="add_url"),
    # Templates require these for rendering:
    path("login/", dummy_view, name="login"),
    path("logout/", dummy_view, name="logout"),
    path("password_change/", dummy_view, name="password_change"),
    path("password_change/done/", dummy_view, name="password_change_done"),
    path("signup/", dummy_view, name="signup"),
    path("profile/", dummy_view, name="user_profile"),
]

pytestmark = pytest.mark.urls(__name__)


@pytest.fixture
def template_name():
    """
    Name of the template to render.

    Use test parametrization to specify the name.
    """
    return ""  # pragma: no cover


@pytest.fixture
def render_template(template_name):
    """Render a template with the given context."""

    def inner(context, request=None):
        return get_template(template_name).render(context, request)

    return inner


@pytest.fixture
def soup():
    """Parse HTML and return a BeautifulSoup object."""

    def inner(html):
        return BeautifulSoup(html, "html.parser")

    return inner


@pytest.mark.django_db
@pytest.mark.parametrize("template_name", ["changelist.html"])
class TestChangelistTemplate:
    @pytest.fixture
    def list_display(self):
        return ["foo", "bar", "baz"]

    @pytest.fixture
    def headers(self):
        return ["Foo", "Bar", "Baz"]

    @pytest.fixture
    def result_row(self):
        return ["Spam", "Eels", "Hovercraft"]

    @pytest.fixture
    def result_obj(self):
        return mock.Mock(pk=42)

    @pytest.fixture
    def col_classes(self):
        return {"bar": "text-danger"}

    @pytest.fixture
    def context(self, rf, list_display, headers, result_row, result_obj, col_classes):
        row = OrderedDict(zip(list_display, result_row))
        row["obj"] = result_obj
        return {
            "request": rf.get("/"),
            "list_display": list_display,
            "headers": headers,
            "result_rows": [row],
            "col_classes": col_classes,
        }

    def test_adds_additional_col_classes(self, render_template, context, soup):
        """Assert that additional CSS classes for <td> elements are inserted."""
        td = soup(render_template(context)).find("tbody").find("tr").find_all("td")[1]
        assert "text-danger" in td["class"]

    def test_adds_col_names(self, render_template, context, soup):
        """
        Assert that the <td> elements for the result items include their
        respective 'name' from the list_display list.
        """
        td = soup(render_template(context)).find("tbody").find("tr").find("td")
        assert "td-foo" in td["class"]

    def test_renders_action_buttons(self, render_template, context, soup):
        """Assert that the expected action buttons are rendered."""
        action = ModelAction(url_name="test", label="Template Test", css="foo")
        context["actions"] = [action]
        link = soup(render_template(context)).find("tbody").find("tr").find("a")
        assert link["href"] == "/test/42/action"
        assert link["class"] == ["foo"]
        assert link.contents[0] == "Template Test"

    @pytest.mark.parametrize("has_add_permission", [True, False])
    def test_add_button(self, render_template, context, soup, has_add_permission):
        """Assert that an add button is added if has_add_permission is True."""
        context["has_add_permission"] = has_add_permission
        context["add_url"] = "add_url"
        btn = soup(render_template(context)).find("a", class_="btn-success")
        assert bool(btn) == has_add_permission

    def test_pagination(self, render_template, context, soup, user):
        """Assert that the pagination is rendered as expected."""
        # create enough objects for an elided pagination:
        for _ in range(100):
            NachweisFactory(user=user)

        paginator = Paginator(object_list=_models.Nachweis.objects.filter(user=user), per_page=5)
        context["paginator"] = paginator
        context["page_obj"] = paginator.page(1)
        context["page_range"] = list(paginator.get_elided_page_range(context["page_obj"].number))

        pagination = soup(render_template(context)).find("ul", class_="pagination")
        page_items = pagination.find_all("li", class_="page-item")
        assert page_items[0].find("a").text == "1"
        assert "disabled" in page_items[0].find("a").attrs["class"]
        assert page_items[1].find("a").text == "2"
        assert page_items[4].find("span").text == "…"


@pytest.mark.django_db
@pytest.mark.parametrize("template_name", ["nachweis_edit.html"])
class TestNachweisEditTemplate:
    @pytest.fixture
    def form(self):
        """Create a Nachweis model form instance without any data."""

        def inner(**data):
            return forms.modelform_factory(_models.Nachweis, fields=forms.ALL_FIELDS)(**data)

        return inner

    def test_submit_row_contains_preview_button(self, render_template, soup, form):
        """Assert that the submit row contains a preview button."""
        context = {"preview_url": "/foo/bar", "form": form()}
        rendered = render_template(context)
        submit_row = soup(rendered).find(id="submit-row")
        assert submit_row
        preview_button = submit_row.find("button", string="Vorschau")
        assert preview_button
        assert preview_button.attrs["data-preview-url"] == "/foo/bar"

    def test_head_loads_preview_script(self, render_template, soup, form):
        """Assert that the head loads the preview script."""
        context = {"preview_url": "/foo/bar", "form": form()}
        rendered = render_template(context)
        head = soup(rendered).find("head")
        assert head
        assert head.find("script", src="/static/web/js/preview.js")
