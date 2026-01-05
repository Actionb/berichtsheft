from collections import OrderedDict
from typing import Any
from urllib.parse import urlencode

from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

from web import models as _models
from web.utils import models as model_utils
from web.utils import perms


class ListAction:
    """
    A helper object for a list view 'action'.

    Actions are operations the user can do on an individual result/row of a
    list view - like 'edit this' or 'delete this'.

    These actions must be registered with the list view using its 'actions'
    attribute. The items in 'actions' must be ListAction instances with a label:

        class MyListView(ChangelistView):
            actions = [ListAction(label="Bearbeiten")]

    The view then passes these actions to the template, which uses the render
    action template tag to render the button/link for each item in the list
    view's results:

        {% render_action action request row=result_row %}

    """

    url_name: str = ""
    title: str = ""
    label: str = ""
    css: str = "btn btn-primary btn-sm w-100"

    def __init__(self, label: str = "", css: str = "", title: str = ""):
        self.label = label or self.label
        self.css = css or self.css
        self.title = title or self.title

    def get_title(self, row: OrderedDict) -> str:
        return self.title

    def has_permission(self, request: HttpRequest, row: OrderedDict) -> bool:  # pragma: no cover
        """
        Check whether the user has permission to perform the action on the
        given result row.

        Custom actions should overwrite this.
        """
        return True

    def render(self, request: HttpRequest, row: OrderedDict) -> SafeString:
        """Render the action button for the given result row."""
        if not self.has_permission(request, row):
            return ""
        return format_html(
            '<button type="button" class="{css}" title="{title}">{label}</button>',
            css=self.css,
            title=self.get_title(row),
            label=self.label,
        )


class LinkAction(ListAction):
    """
    A list view action that renders a link.

    Instantiate with an url_name and a label:

        class MyListView(ChangelistView):
            actions = [LinkAction(url_name="nachweis_change", label="Bearbeiten")]
    """

    url_name: str = ""

    def __init__(self, url_name: str = "", *args, **kwargs):
        self.url_name = url_name or self.url_name
        if not self.url_name:  # pragma: no cover
            raise TypeError("LinkAction requires 'url_name'")
        super().__init__(*args, **kwargs)

    def get_url(self, request: HttpRequest, row: OrderedDict) -> str:
        """Return the URL for the action on the given result row."""
        return reverse(self.url_name)

    def render(self, request: HttpRequest, row: OrderedDict) -> SafeString:
        """Render the action button for the given result row."""
        if not self.has_permission(request, row):
            return ""
        return format_html(
            '<a href="{url}" class="{css}" title="{title}">{label}</a>',
            url=self.get_url(request, row),
            css=self.css,
            title=self.get_title(row),
            label=self.label,
        )


class ModelAction(LinkAction):
    """A list view action that acts on a model object."""

    pk_url_kwarg: str = "pk"

    def __init__(self, pk_url_kwarg: str = "", **kwargs: Any):
        super().__init__(**kwargs)
        self.pk_url_kwarg = pk_url_kwarg or self.pk_url_kwarg

    def get_url(self, request: HttpRequest, row: OrderedDict) -> str:
        """Return the URL for the action on the given object."""
        return reverse(self.url_name, kwargs={self.pk_url_kwarg: row["obj"].pk})


class ChangePermActionMixin:
    """An action mixin that checks if the user has 'change' permissions."""

    def has_permission(self, request: HttpRequest, row: OrderedDict) -> bool:
        return perms.has_change_permission(request.user, row["obj"]._meta)


class EditAction(ChangePermActionMixin, ModelAction):
    """A generic 'edit' action."""

    label = "Bearbeiten"

    def get_title(self, row: OrderedDict) -> str:
        return f"{row['obj']._meta.verbose_name} bearbeiten"


class NachweisPrintAction(ChangePermActionMixin, ModelAction):
    """The action for the print view of Nachweis objects."""

    url_name = "nachweis_print"
    label = "Drucken"

    def get_title(self, row: OrderedDict) -> str:
        return f"Druckansicht für diesen {row['obj']._meta.verbose_name} anzeigen"


class AddMissingAction(LinkAction):
    """
    A link that sends the user to the Nachweis add page from the
    'missing Nachweise' page.
    """

    label = "Hinzufügen"
    url_name = "nachweis_add"

    def get_title(self, row: OrderedDict) -> str:
        return "Fehlenden Nachweis erstellen"

    def has_permission(self, request: HttpRequest, row: OrderedDict) -> bool:
        return perms.has_add_permission(request.user, _models.Nachweis._meta)

    def get_initial_data(self, request: HttpRequest, row: OrderedDict) -> dict:
        """Return initial data for the missing Nachweis."""
        return model_utils.initial_data_for_date(request.user, row["start"])

    def get_url(self, request: HttpRequest, row: OrderedDict):
        return f"{super().get_url(request, row)}?{urlencode(self.get_initial_data(request, row))}"


class AddMisingDashboardAction(AddMissingAction):
    """The 'add missing Nachweis' action but for the Dashboard."""

    label = mark_safe('<i class="bi bi-file-earmark-plus"></i>')
    css = "btn btn-outline-success ms-3"


class FinishNachweisAction(ChangePermActionMixin, ListAction):
    """The action finish or complete a Nachweis object."""

    label = mark_safe('<i class="bi bi-check-circle"></i>')
    title = "Nachweis abschließen"
    css = "btn btn-outline-success btn-sm w-100 finish-btn"

    def render(self, request: HttpRequest, row: OrderedDict) -> SafeString:
        """Render the action button for the given result row."""
        if not self.has_permission(request, row):
            return ""
        return format_html(
            '<button type="button" class="{css}" title="{title}" data-bs-toggle="modal" data-bs-target="#finishModal">{label}</button>',
            css=self.css,
            title=self.get_title(row),
            label=self.label,
        )
