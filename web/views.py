from datetime import date

from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
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
            raise PermissionDenied
        return obj


class EditView(ModelViewMixin, BaseViewMixin, PermissionRequiredMixin, UpdateView):
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


class NachweisEditView(RequireUserMixin, SaveUserMixin, EditView):
    model = _models.Nachweis
    template_name = "nachweis_edit.html"
    fields = forms.ALL_FIELDS
    success_url = reverse_lazy("nachweis_list")

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
    fields = forms.ALL_FIELDS
    success_url = reverse_lazy("nachweis_list")


def print_preview(request):
    """Preview the print layout for a Nachweis object."""
    form = forms.modelform_factory(_models.Nachweis, fields=forms.ALL_FIELDS)(data=request.GET.dict())
    # Validate the form. Without this step, form.instance will be missing data
    # for some fields.
    form.is_valid()
    return render(request, template_name="print.html", context={"object": form.instance})


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
