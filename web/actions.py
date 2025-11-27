from django.urls import reverse
from django.utils.html import format_html

from web.utils import perms


class ListAction:
    """
    A helper object for a changelist view 'action'.

    Actions are operations the user can do on individual objects of a list view,
    like 'edit this' or 'delete this'.

    These actions must be registered with the list view using its 'actions'
    attribute. The items in 'actions' must be ListAction instances with an url
    and a label:

    class MyListView(ChangelistView):
        actions = [ListAction(url_name="nachweis_change", label="Bearbeiten")]

    The view then passes these actions to the template, which uses the
    ListAction.render method to render the button/link for each item in the
    list view's results.
    """

    url_name: str = ""
    label: str = ""
    css: str = "btn btn-primary"
    pk_url_kwarg: str = "pk"

    def __init__(self, url_name: str = "", label: str = "", css: str = "", pk_url_kwarg: str = ""):
        self.url_name = url_name or self.url_name
        if not self.url_name:
            raise TypeError("ListAction requires 'url_name'")
        self.label = label or self.label
        self.css = css or self.css
        self.pk_url_kwarg = pk_url_kwarg or self.pk_url_kwarg

    def has_permission(self, request, obj):  # pragma: no cover
        """
        Check whether the user has permission to perform the action on the
        given obj.

        Custom actions should overwrite this.
        """
        return True

    def get_url(self, request, obj):
        """Return the URL for the action on the given object."""
        return reverse(self.url_name, kwargs={self.pk_url_kwarg: obj.pk})

    def render(self, request, obj):
        """Render the action button."""
        if not self.has_permission(request, obj):
            return ""
        return format_html('<a href="{}" class="{}">{}</a>', self.get_url(request, obj), self.css, self.label)


class ChangePermAction(ListAction):
    """An action that checks if the user has 'change' permissions."""

    def has_permission(self, request, obj):
        return perms.has_change_permission(request.user, obj._meta)


class EditAction(ChangePermAction):
    """A generic 'edit' action."""

    label = "Bearbeiten"


class NachweisPrintAction(ChangePermAction):
    """The action for the print view of Nachweis objects."""

    url_name = "nachweis_print"
    label = "Drucken"
