from django import forms
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView
from mizdb_tomselect.views import AutocompleteView as BaseAutocompleteView
from mizdb_tomselect.views import PopupResponseMixin
from mizdb_tomselect.widgets import MIZSelect

from web.models import Abteilung, Nachweis


class AutocompleteView(BaseAutocompleteView):
    def has_add_permission(self, request):
        return True


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
        return super().get_context_data(opts=self.opts, **kwargs)


class EditView(ModelViewMixin, BaseViewMixin, UpdateView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add = self.extra_context["add"]
        if not self.title:
            self.title = f"{self.opts.verbose_name} {'erstellen' if self.add else 'bearbeiten'}"

    def get_object(self, queryset=None):
        if not self.add:
            return super().get_object(queryset)


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


class NachweisListView(BaseViewMixin, ListView):
    model = Nachweis
    template_name = "nachweis_list.html"
    title = "Nachweis Liste"


class NachweisPrintView(BaseViewMixin, DetailView):
    model = Nachweis
    template_name = "print.html"


class AbteilungEditView(PopupResponseMixin, EditView):
    model = Abteilung
    template_name = "base_form.html"
    fields = forms.ALL_FIELDS
    success_url = reverse_lazy("nachweis_list")
