from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from mizdb_tomselect.views import AutocompleteView as BaseAutocompleteView
from mizdb_tomselect.views import PopupResponseMixin
from mizdb_tomselect.widgets import MIZSelect

from web.forms import UserCreationForm
from web.models import Abteilung, Nachweis
from web.utils import perms


class AutocompleteView(BaseAutocompleteView):
    def has_add_permission(self, request):
        return perms.has_add_permission(request.user, self.model._meta)


class BaseViewMixin:
    title: str = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
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


class NachweisEditView(EditView):
    model = Nachweis
    template_name = "nachweis_edit.html"
    fields = forms.ALL_FIELDS
    success_url = reverse_lazy("nachweis_list")

    def get_form_class(self):
        return forms.modelform_factory(
            Nachweis,
            fields=self.fields,
            widgets={
                "datum_start": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                "datum_ende": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                "abteilung": MIZSelect(
                    Abteilung,
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


class NachweisListView(BaseViewMixin, PermissionRequiredMixin, ListView):
    model = Nachweis
    template_name = "nachweis_list.html"
    title = "Nachweis Liste"
    permission_required = perms.get_perm("view", Nachweis._meta)


class NachweisPrintView(BaseViewMixin, PermissionRequiredMixin, DetailView):
    model = Nachweis
    template_name = "print.html"
    permission_required = perms.get_perm("change", Nachweis._meta)


class AbteilungEditView(PopupResponseMixin, EditView):
    model = Abteilung
    template_name = "base_form.html"
    fields = forms.ALL_FIELDS
    success_url = reverse_lazy("nachweis_list")


def print_preview(request):
    """Preview the print layout for a Nachweis object."""
    form = forms.modelform_factory(Nachweis, fields=forms.ALL_FIELDS)(data=request.GET.dict())
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
    success_url = reverse_lazy("login")
    title = "Registrieren"
    form_class = UserCreationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        perms.add_azubi_permissions(self.object)
        return response
