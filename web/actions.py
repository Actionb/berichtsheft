from datetime import date
from typing import Any
from urllib.parse import urlencode

from django.db.models import Model
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from web import models as _models
from web.utils import date as date_utils
from web.utils import perms


class ListAction:
    """
    A helper object for a list view 'action'.

    Actions are operations the user can do on individual results or rows of a
    list view - like 'edit this' or 'delete this'.

    These actions must be registered with the list view using its 'actions'
    attribute. The items in 'actions' must be ListAction instances with an url
    and a label:

    class MyListView(ChangelistView):
        actions = [ListAction(url_name="nachweis_change", label="Bearbeiten")]

    The view then passes these actions to the template, which uses the render
    action template tag to render the button/link for each item in the list
    view's results:

        {% render_action action request foo=bar %}

    """

    url_name: str = ""
    label: str = ""
    css: str = "btn btn-primary btn-sm w-100"

    def __init__(self, url_name: str = "", label: str = "", css: str = "", title: str = ""):
        self.url_name = url_name or self.url_name
        if not self.url_name:  # pragma: no cover
            raise TypeError("ListAction requires 'url_name'")
        self.label = label or self.label
        self.css = css or self.css
        self.title = title or self.title

    def get_title(self, **kwargs):
        return self.title

    def has_permission(self, request: HttpRequest, **kwargs: Any) -> bool:  # pragma: no cover
        """
        Check whether the user has permission to perform the action on the
        given result item.

        Custom actions should overwrite this.
        """
        return True

    def get_url(self, request: HttpRequest, **kwargs: Any) -> str:
        """Return the URL for the action on the given result item."""
        return reverse(self.url_name)

    def render(self, request: HttpRequest, **kwargs: Any) -> SafeString:
        """Render the action button."""
        if not self.has_permission(request, **kwargs):
            return ""
        return format_html(
            '<a href="{url}" class="{css}" title="{title}">{label}</a>',
            url=self.get_url(request, **kwargs),
            css=self.css,
            title=self.get_title(**kwargs),
            label=self.label,
        )


class ModelAction(ListAction):
    """A list view action that acts on a model object."""

    pk_url_kwarg: str = "pk"

    def __init__(self, pk_url_kwarg: str = "", **kwargs: Any):
        super().__init__(**kwargs)
        self.pk_url_kwarg = pk_url_kwarg or self.pk_url_kwarg

    def get_url(self, request: HttpRequest, obj: Model) -> str:
        """Return the URL for the action on the given object."""
        return reverse(self.url_name, kwargs={self.pk_url_kwarg: obj.pk})


class ChangePermAction(ModelAction):
    """An action that checks if the user has 'change' permissions."""

    def has_permission(self, request: HttpRequest, obj: Model) -> bool:
        return perms.has_change_permission(request.user, obj._meta)


class EditAction(ChangePermAction):
    """A generic 'edit' action."""

    label = "Bearbeiten"

    def get_title(self, obj):
        return f"{obj._meta.verbose_name} bearbeiten"


class NachweisPrintAction(ChangePermAction):
    """The action for the print view of Nachweis objects."""

    url_name = "nachweis_print"
    label = "Drucken"

    def get_title(self, obj):
        return f"Druckansicht für diesen {obj._meta.verbose_name} anzeigen"


class AddMissingAction(ListAction):
    """
    A link that sends the user to the Nachweis add page from the
    'missing Nachweise' page.
    """

    label = "Hinzufügen"
    url_name = "nachweis_add"

    def get_title(self, **kwargs):
        return "Fehlenden Nachweis erstellen"

    def has_permission(self, request: HttpRequest, **kwargs: Any) -> bool:
        return perms.has_add_permission(request.user, _models.Nachweis._meta)

    def get_initial_data(self, request: HttpRequest, start: date, end: date) -> dict:
        """Return initial data for the missing Nachweis."""
        user_start_date = request.user.profile.start_date
        if not user_start_date:  # pragma: no cover
            return {}
        initial = {
            "datum_start": start,
            "datum_ende": end,
            "jahr": start.year,
            "ausbildungswoche": date_utils.count_week_numbers(user_start_date, start),
            "kalenderwoche": start.isocalendar()[1],
        }
        match request.user.profile.interval:
            case _models.UserProfile.IntervalType.DAILY:
                initial["nummer"] = date_utils.count_business_days(user_start_date, start)
            case _models.UserProfile.IntervalType.WEEKLY:
                initial["nummer"] = initial["ausbildungswoche"]
            case _models.UserProfile.IntervalType.MONTHLY:
                initial["nummer"] = date_utils.count_months(user_start_date, start) + 1
        return initial

    def get_url(self, request: HttpRequest, **kwargs: Any):
        return f"{super().get_url(request, **kwargs)}?{urlencode(self.get_initial_data(request, **kwargs))}"
