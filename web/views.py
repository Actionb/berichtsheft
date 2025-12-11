from collections import OrderedDict
from datetime import date

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import linebreaksbr, truncatewords
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import MultipleObjectMixin
from mizdb_tomselect.views import AutocompleteView as BaseAutocompleteView
from mizdb_tomselect.views import PopupResponseMixin
from mizdb_tomselect.widgets import MIZSelect

from web import actions
from web import forms as _forms
from web import models as _models
from web.utils import perms
from web.utils.date import count_week_numbers
from web.utils.decorators import add_attrs
from web.utils.models import collect_deleted_objects, get_current_nachweis, get_missing_nachweise

# Decorator for list_display callables
list_display_callable = add_attrs


class AutocompleteView(BaseAutocompleteView):
    def has_add_permission(self, request):
        return perms.has_add_permission(request.user, self.model._meta)


class AbteilungAutocompleteView(AutocompleteView):
    def create_object(self, data):
        """Create a new object with the given data."""
        return self.model.objects.create(**{self.create_field: data[self.create_field], "user": self.request.user})


class BaseViewMixin:
    title: str = ""
    submit_button_text = "Weiter"
    mainclass: str = ""  # the CSS class for the main element

    def get_trash_count(self):
        """Return the number of items in the trash can for the current user."""
        if not self.request.user.is_authenticated:
            return 0
        return sum(qs.count() for qs in collect_deleted_objects(self.request.user))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        context["submit_button_text"] = self.submit_button_text
        context["trash_count"] = self.get_trash_count()
        context["mainclass"] = self.mainclass
        return context


class ModelViewMixin:
    model = None

    def __init__(self, *args, **kwargs):
        self.opts = self.model._meta
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opts"] = self.opts
        return context


class FilterUserMixin(MultipleObjectMixin):
    """A mixin for a list view that only includes objects of the current user."""

    _user_attr = "user"

    def get_queryset(self):
        # TODO: should this be implemented as a queryset manager?
        # -> model.user_objects.all()
        return super().get_queryset().filter(**{self._user_attr: self.request.user})


class SaveUserMixin(ModelFormMixin):
    """
    A mixin for an object view that sets a user attribute on the object before
    saving.
    """

    _user_attr = "user"

    def form_valid(self, form):
        # Add the current user to the form's instance which then becomes the
        # view's object when super().form_valid is called.
        setattr(form.instance, self._user_attr, self.request.user)
        return super().form_valid(form)


class RequireUserMixin(SingleObjectMixin):
    """
    A mixin for an object view that raises PermissionDenied if the current user
    is not the owner of the object.
    """

    _user_attr = "user"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj and getattr(obj, self._user_attr) != self.request.user:
            raise PermissionDenied(
                "Sie haben nicht die Berechtigung, dieses Objekt anzusehen. Sie sind nicht Besitzer dieses Objektes."
            )
        return obj


class BaseListView(BaseViewMixin, ListView):
    """Display a list of items in a table."""

    template_name = "list.html"
    paginate_by = 50
    actions = ()
    list_display = ()

    def get_result_headers(self):
        return self.list_display

    def get_result_rows(self, object_list):
        """
        For each result, return an OrderedDict where the keys are the items in
        `list_display` and the values are the values to display for a given row.
        """
        return [OrderedDict(zip(self.list_display, self.get_result_row(result))) for result in object_list]

    def get_result_row(self, result):
        """Return the values to display in the row for the given result."""
        return result

    def _get_default_actions(self, request):
        return []

    def get_actions(self, request):
        return [*self._get_default_actions(request), *self.actions]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_display"] = self.list_display
        ctx["result_rows"] = self.get_result_rows(ctx["object_list"])
        ctx["headers"] = self.get_result_headers()
        ctx["actions"] = self.get_actions(self.request)
        paginator = ctx["paginator"]
        ctx["page_range"] = list(paginator.get_elided_page_range(ctx["page_obj"].number))
        return ctx


class ChangelistView(PermissionRequiredMixin, FilterUserMixin, ModelViewMixin, BaseListView):
    template_name = "changelist.html"
    paginate_by = 10

    def get_permission_required(self):
        if self.permission_required is None:
            # Require 'view' permission for this model by default:
            return (perms.get_perm("view", self.model._meta),)
        return super().get_permission_required()

    def get_result_headers(self):
        """Return the table headers for the result list."""
        headers = []
        for name in self.list_display:
            if hasattr(self, name) and callable(getattr(self, name)):
                # A callable list_display item; use the label attr if available
                func = getattr(self, name)
                header = getattr(func, "label", name.replace("_", " ").capitalize())
            else:
                header = self.opts.get_field(name).verbose_name
                if not header[0].isupper():
                    # Assume that this is a default 'verbose_name'
                    header = header.replace("_", " ").capitalize()
            headers.append(header)
        return headers

    def get_result_rows(self, object_list) -> list[OrderedDict]:
        # Add an 'obj' item for the render_action tags to each row:
        rows = super().get_result_rows(object_list=object_list)
        for row, obj in zip(rows, object_list):
            row["obj"] = obj
        return rows

    def get_result_row(self, result):
        """Return the values to display in the row for the given result."""
        row = []
        for name in self.list_display:
            if hasattr(self, name) and callable(getattr(self, name)):
                # A callable list_display item; call it with the result
                value = getattr(self, name)(result)
            else:
                # Should be a model field then:
                field = self.opts.get_field(name)
                if isinstance(field, models.ForeignKey):
                    value = getattr(result, field.name)
                    if value is not None:
                        value = str(value)
                else:
                    value = getattr(result, field.attname)
                if getattr(field, "flatchoices", None):  # pragma: no cover
                    # The field has predefined choices; use the human-readable
                    # part of the choice:
                    value = dict(field.flatchoices).get(value, "")
                if isinstance(value, bool):
                    if value:
                        value = mark_safe('<i class="bi bi-check-circle fs-4 text-success"></i>')
                    else:
                        value = mark_safe('<i class="bi bi-x-circle fs-4 text-danger"></i>')
            row.append(value)
        return row

    def _get_default_actions(self, request):
        _actions = []
        if perms.has_change_permission(request.user, self.opts):
            _actions.append(actions.EditAction(url_name=f"{self.opts.model_name}_change"))
        return _actions

    def get_column_classes(self):
        """
        Provide additional CSS classes to apply to individual columns of the
        result list.

        Must be a mapping: {<column_name>: css} , where 'column_name' is a
        column as specified in view.list_display, and 'css' is the additional
        CSS classes as simple string.

        Example:

            list_display = ["foo", "bar"]

            def get_column_classes(self):
                return { "foo": "text-center align-middle"}
        """
        return {}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["has_add_permission"] = perms.has_add_permission(self.request.user, self.opts)
        ctx["add_url"] = f"{self.model._meta.model_name}_add"
        ctx["col_classes"] = self.get_column_classes()
        return ctx


class EditView(ModelViewMixin, BaseViewMixin, PermissionRequiredMixin, UpdateView):
    delete_url_name = ""
    restore_url_name = "restore_object"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add = self.extra_context["add"]
        if not self.title:
            self.title = f"{self.opts.verbose_name} {'erstellen' if self.add else 'bearbeiten'}"

    def get_object(self, queryset=None):
        if not self.add:
            return super().get_object(queryset)

    def has_permission(self):
        if self.add:
            perm_func = perms.has_add_permission
        else:
            perm_func = perms.has_change_permission
        return perm_func(self.request.user, self.opts)

    def get_permission_required(self):
        if self.add:
            return [perms.get_perm("add", self.opts)]
        return [perms.get_perm("change", self.opts)]

    def get_delete_url(self):
        return reverse(self.delete_url_name, kwargs=self.kwargs)

    def get_restore_url(self):
        kwargs = {"model_name": self.opts.model_name, **self.kwargs}
        return reverse(self.restore_url_name, kwargs=kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["add"] = self.add
        if not self.add and perms.has_delete_permission(self.request.user, self.opts):
            context["delete_url"] = self.get_delete_url()
            context["restore_url"] = self.get_restore_url()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            message=f"{self.opts.verbose_name} erfolgreich {'erstellt' if self.add else 'bearbeitet'}.",
        )
        return response


class NachweisEditView(RequireUserMixin, SaveUserMixin, EditView):
    model = _models.Nachweis
    template_name = "nachweis_edit.html"
    fields = forms.ALL_FIELDS
    success_url = reverse_lazy("nachweis_list")
    delete_url_name = "nachweis_delete"
    queryset = _models.Nachweis.global_objects

    def get_form_class(self):
        return forms.modelform_factory(
            _models.Nachweis,
            fields=self.fields,
            widgets={
                "datum_start": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                "datum_ende": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                "abteilung": MIZSelect(
                    _models.Abteilung,
                    url="abteilung_ac",
                    add_url="abteilung_add",
                    edit_url="abteilung_change",
                    create_field="name",
                ),
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["preview_url"] = reverse("print_preview")
        return context

    def get_initial(self):
        initial = super().get_initial()
        if self.add:
            now = date.today()
            last = _models.Nachweis.objects.filter(user=self.request.user).order_by("-nummer").first()
            initial.update(
                {
                    "jahr": now.year,
                    "kalenderwoche": now.isocalendar()[1],
                    "datum_start": str(date.fromisocalendar(now.year, now.isocalendar()[1], 1)),
                    "datum_ende": str(date.fromisocalendar(now.year, now.isocalendar()[1], 5)),
                    "nummer": last.nummer + 1 if last else 1,
                }
            )
            try:
                start_date = self.request.user.profile.start_date
            except _models.User.profile.RelatedObjectDoesNotExist:
                start_date = None
            if start_date:
                initial["ausbildungswoche"] = count_week_numbers(start_date, now)
            # Update initial data with GET parameters:
            initial.update(self.request.GET.dict())
        return initial


class NachweisListView(ChangelistView):
    model = _models.Nachweis
    title = "Meine Nachweise"
    list_display = ["jahr", "woche", "zeitraum", "betrieb", "schule", "fertig", "eingereicht_bei", "unterschrieben"]
    actions = [actions.NachweisPrintAction()]
    mainclass = "container-fluid px-5"

    def get_column_classes(self):
        return {
            "fertig": "text-center align-middle",
            "unterschrieben": "text-center align-middle",
        }

    @list_display_callable()
    def woche(self, obj):
        return obj.ausbildungswoche

    @list_display_callable()
    def zeitraum(self, obj):
        dates = list(map(lambda d: d.strftime("%d. %B %Y"), [obj.datum_start, obj.datum_ende]))
        return format_html('<span class="text-nowrap">{}</span> <br> <span class="text-nowrap">{}</span>', *dates)

    @list_display_callable(label="Betriebliche Tätigkeiten")
    def betrieb(self, obj):
        return truncatewords(linebreaksbr(obj.betrieb), 30)

    @list_display_callable(label="Berufsschule")
    def schule(self, obj):
        return truncatewords(linebreaksbr(obj.schule), 10)


class NachweisPrintView(BaseViewMixin, PermissionRequiredMixin, DetailView):
    model = _models.Nachweis
    template_name = "print.html"
    permission_required = perms.get_perm("change", _models.Nachweis._meta)


class AbteilungEditView(RequireUserMixin, SaveUserMixin, PopupResponseMixin, EditView):
    model = _models.Abteilung
    template_name = "base_form.html"
    fields = ["name"]
    success_url = reverse_lazy("abteilung_list")
    delete_url_name = "abteilung_delete"
    queryset = _models.Abteilung.global_objects


class AbteilungListView(ChangelistView):
    model = _models.Abteilung
    title = "Meine Abteilungen"
    list_display = ["name"]


def print_preview(request):
    """Preview the print layout for a Nachweis object."""
    form = forms.modelform_factory(_models.Nachweis, fields=forms.ALL_FIELDS)(data=request.GET.dict())
    # Validate the form. Without this step, form.instance will be missing data
    # for some fields.
    form.is_valid()
    form.instance.user = request.user
    return render(request, template_name="print.html", context={"object": form.instance})


def handler403(request, exception=None):
    message = "Sie haben nicht die Berechtigung, dieses Objekt anzusehen."
    if isinstance(exception, PermissionDenied) and exception.args:
        message = exception.args[0]
    return render(
        request,
        template_name="base.html",
        context={"content": message},
        status=403,
    )


class DashboardView(LoginRequiredMixin, BaseViewMixin, TemplateView):
    title = "Home"
    template_name = "dashboard.html"
    permission_required = [perms.get_perm("view", _models.Nachweis._meta)]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_nachweis"] = get_current_nachweis(self.request.user)
        ctx["missing_nachweise"] = [OrderedDict(start=s, end=e) for s, e in get_missing_nachweise(self.request.user)]
        ctx["action"] = actions.AddMisingDashboardAction()
        return ctx


class MissingView(LoginRequiredMixin, BaseListView):
    title = "Fehlende Nachweise"
    template_name = "missing.html"
    permission_required = [perms.get_perm("view", _models.Nachweis._meta)]
    actions = [actions.AddMissingAction()]
    list_display = ["Datum/Zeitraum"]

    def get_queryset(self) -> list[tuple[date, date]]:
        return get_missing_nachweise(self.request.user)

    def get_result_rows(self, object_list):
        rows = super().get_result_rows(object_list)
        for row, (start, end) in zip(rows, object_list):
            row["start"] = start
            row["end"] = end
        return rows

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_daily"] = self.request.user.profile.interval == _models.UserProfile.IntervalType.DAILY
        return ctx


################################################################################
# DELETE VIEWS & RECYCLE BIN
################################################################################


class DeleteView(SingleObjectMixin, View):
    """View for deleting objects via POST request."""

    success_url = None
    http_method_names = ["post"]  # only allow POST requests

    def delete_object(self, obj):
        """Delete the given object."""
        obj.delete()

    def delete_response(self, request, **kwargs):
        """Create a response after a succesful deletion."""
        return redirect(str(self.success_url))

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not perms.can_delete(request.user, obj):
            raise PermissionDenied
        self.delete_object(obj)
        messages.success(request, f"{obj._meta.verbose_name} '{obj}' erfolgreich gelöscht.")
        return self.delete_response(request)


class NachweisDeleteView(DeleteView):
    model = _models.Nachweis
    success_url = reverse_lazy("nachweis_list")


class AbteilungDeleteView(DeleteView):
    model = _models.Abteilung
    success_url = reverse_lazy("abteilung_list")


class HardDeleteView(DeleteView):
    """
    Hard-delete a model instance.

    Called from the trash can page with an AJAX request.

    Requires that the user has permissions and that the instance has been
    soft-deleted.
    """

    def delete_object(self, obj):
        obj.hard_delete()

    def delete_response(self, request, **kwargs):
        return HttpResponse()

    def get_object(self):
        """Return the object to be deleted."""
        model = apps.get_model("web", self.kwargs["model_name"])
        # Use deleted_objects to only look in the soft-deleted objects:
        return get_object_or_404(model.deleted_objects, pk=self.kwargs.get("pk"))


class PapierkorbView(BaseViewMixin, ListView):
    """Recycle bin from which the user can hard-delete objects or restore them."""

    template_name = "trashcan.html"
    title = "Papierkorb"

    def get_queryset(self):
        return collect_deleted_objects(self.request.user)

    def get_deleted_objects(self):
        """Return a list of deleted objects, plus additional info."""
        deleted_objects = []
        for qs in self.get_queryset():
            objects = []
            for obj in qs.all():
                objects.append((obj, self.get_obj_info(obj)))
            if objects:
                deleted_objects.append((qs.model._meta, qs.count(), objects))
        return deleted_objects

    def get_obj_info(self, obj):
        """
        Return some info for the overview about the given object.

        The info consists of a list of 2-tuples: [(<header>, <value>)].
        """
        match obj:
            case _models.Nachweis():
                betrieb_split = obj.betrieb.split(" ")
                betrieb = " ".join(betrieb_split[:10])
                if len(betrieb_split) > 10:
                    betrieb += " ..."
                if obj.datum_ende and obj.datum_ende != obj.datum_start:
                    datum = f"{obj.datum_start.strftime('%d. %b %Y')} - {obj.datum_ende.strftime('%d. %b %Y')}"
                else:  # pragma: no cover
                    datum = obj.datum_start.strftime("%d. %b %Y")
                return [
                    ("Nummer", obj.nummer),
                    ("Datum", datum),
                    ("Aktivität", betrieb),
                    ("Unterschrieben", "✅" if obj.unterschrieben else "❌"),
                ]
            case _:  # pragma: no cover
                return []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["deleted_objects"] = self.get_deleted_objects()
        return ctx


@require_POST
def empty_trash(request):
    """Empty the recycle bin of the current user."""
    deleted_objects = collect_deleted_objects(request.user)

    # Check that the user has delete permission for every deleted object:
    for qs in deleted_objects:
        if not perms.has_delete_permission(request.user, qs.model._meta):
            raise PermissionDenied

    for qs in deleted_objects:
        qs.hard_delete()
    messages.success(request, "Papierkorb geleert!")
    return redirect("nachweis_list")


@require_POST
def restore_object(request, model_name, pk):
    """Restore the model instance with the given pk."""
    model = apps.get_model("web", model_name)
    obj = get_object_or_404(model.deleted_objects, pk=pk)

    if obj.user != request.user or not perms.has_delete_permission(request.user, obj._meta):
        raise PermissionDenied

    obj.restore(strict=False)
    message = f"{obj._meta.verbose_name} '{obj}' wiederhergestellt!"
    messages.success(request, message)
    return JsonResponse(data={"message": message})


################################################################################
# AUTH
################################################################################


class LoginView(BaseViewMixin, auth_views.LoginView):
    template_name = "auth/login.html"
    success_url = next_page = reverse_lazy("nachweis_list")
    title = "Anmelden"


class PasswordChangeView(BaseViewMixin, auth_views.PasswordChangeView):
    template_name = "auth/auth_form.html"
    success_url = reverse_lazy("password_change_done")
    title = "Passwort ändern"


class PasswordChangeDoneView(BaseViewMixin, auth_views.PasswordChangeDoneView):
    template_name = "auth/password_change_done.html"
    title = "Passwort geändert"


class SignUpView(BaseViewMixin, CreateView):
    model = get_user_model()
    template_name = "auth/auth_form.html"
    success_url = reverse_lazy("nachweis_list")
    title = "Registrieren"
    form_class = _forms.UserCreationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        perms.add_azubi_permissions(self.object)
        login(self.request, self.object)
        return response


class UserProfileView(LoginRequiredMixin, BaseViewMixin, UpdateView):
    model = _models.UserProfile
    template_name = "auth/auth_form.html"
    success_url = reverse_lazy("user_profile")
    title = "Benutzerprofil bearbeiten"
    form_class = _forms.UserProfileForm
    submit_button_text = "Aktualisieren"

    def get_object(self, queryset=None):
        return _models.UserProfile.objects.get_or_create(user=self.request.user)[0]

    def get_initial(self):
        initial = super().get_initial()
        initial["first_name"] = self.request.user.first_name
        initial["last_name"] = self.request.user.last_name
        return initial
