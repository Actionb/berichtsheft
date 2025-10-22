import pytest
from bs4 import BeautifulSoup
from django import forms
from django.template.loader import get_template

from tests.model_factory import NachweisFactory
from web import models as _models


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
@pytest.mark.parametrize("template_name", ["nachweis_list.html"])
class TestNachweisListTemplate:
    def assert_is_checkmark(self, svg):
        """Assert that the given SVG is a checkmark."""
        assert "feather-check-circle" in svg["class"]
        assert "text-success" in svg["class"]

    def assert_is_x(self, svg):
        """Assert that the given SVG is an X."""
        assert "feather-x-circle" in svg["class"]
        assert "text-danger" in svg["class"]

    @pytest.mark.parametrize("field", ["fertig", "unterschrieben"])
    @pytest.mark.parametrize("checked", [True, False])
    def test_boolean_field_svgs(self, render_template, soup, field, checked, **_):
        """
        Assert that the boolean values for the 'fertig' and 'unterschrieben'
        fields are rendered as svg checkmarks and Xs.
        """
        context = {"object_list": [NachweisFactory(**{field: checked})]}
        rendered = render_template(context)
        svg = soup(rendered).find("td", class_=f"td-{field}").find("svg")
        assert svg
        if checked:
            self.assert_is_checkmark(svg)
        else:
            self.assert_is_x(svg)

    @pytest.mark.parametrize("unterschrieben", [True, False])
    def test_tr_warning(self, render_template, soup, unterschrieben, **_):
        """
        Assert that a table row is rendered with warning class if the Nachweis
        is not signed.
        """
        context = {"object_list": [NachweisFactory(**{"unterschrieben": unterschrieben})]}
        tr = soup(render_template(context)).find("tbody").find("tr")
        assert tr
        classes = tr.attrs.get("class", [])
        if unterschrieben:
            assert "table-warning" not in classes
        else:
            assert "table-warning" in classes


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
