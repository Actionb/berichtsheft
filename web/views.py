from datetime import date

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import MultipleObjectMixin
from mizdb_tomselect.views import AutocompleteView as BaseAutocompleteView
from mizdb_tomselect.views import PopupResponseMixin
from mizdb_tomselect.widgets import MIZSelect

from web import forms as _forms
from web import models as _models
from web.utils import perms
from web.utils.date import count_week_numbers


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        context["submit_button_text"] = self.submit_button_text
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
            last = _models.Nachweis.objects.filter(user=self.request.user).last()
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


class NachweisListView(BaseViewMixin, PermissionRequiredMixin, FilterUserMixin, ListView):
    model = _models.Nachweis
    template_name = "nachweis_list.html"
    title = "Nachweis Liste"
    permission_required = perms.get_perm("view", _models.Nachweis._meta)


class NachweisPrintView(BaseViewMixin, PermissionRequiredMixin, DetailView):
    model = _models.Nachweis
    template_name = "print.html"
    permission_required = perms.get_perm("change", _models.Nachweis._meta)


class AbteilungEditView(PopupResponseMixin, EditView):
    model = _models.Abteilung
    template_name = "base_form.html"
    fields = ["name"]
    success_url = reverse_lazy("nachweis_list")
    delete_url_name = "abteilung_delete"
    queryset = _models.Abteilung.global_objects


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


################################################################################
# DELETE VIEWS & RECYCLE BIN
################################################################################


def _delete(request, pk, opts):
    """Soft-delete a model instance when the user passes permission checks."""
    if request.method.lower() != "post":
        return HttpResponseNotAllowed(["post"])
    if not perms.has_delete_permission(request.user, opts):
        raise PermissionDenied
    obj = get_object_or_404(opts.model.global_objects, pk=pk)
    if obj.user != request.user:
        raise PermissionDenied
    obj.delete()
    return redirect(reverse("nachweis_list"))


def delete_nachweis(request, pk):
    """Delete a Nachweis instance."""
    return _delete(request, pk, _models.Nachweis._meta)


def delete_abteilung(request, pk):
    """Delete an Abteilung instance."""
    return _delete(request, pk, _models.Abteilung._meta)


def hard_delete(request, model_name, pk):
    """
    Hard-delete a model instance.

    Called from the trash can page with an AJAX request.

    Requires that the user has permissions and that the instance has already
    been soft-deleted.
    """
    if request.method.lower() != "post":
        return HttpResponseNotAllowed(["post"])
    model = apps.get_model("web", model_name)
    opts = model._meta
    if not perms.has_delete_permission(request.user, opts):
        raise PermissionDenied
    obj = get_object_or_404(model.deleted_objects, pk=pk)
    if obj.user != request.user:
        raise PermissionDenied
    obj.hard_delete()
    messages.success(request, f"{opts.verbose_name} '{obj}' erfolgreich gelöscht.")
    return HttpResponse()


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


class UserProfileView(BaseViewMixin, UpdateView):
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
