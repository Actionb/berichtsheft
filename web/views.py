from django.forms.models import ALL_FIELDS
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from web.models import Nachweis


class BaseViewMixin:
    title: str = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        return context


class NachweisEditView(BaseViewMixin, UpdateView):
    model = Nachweis
    template_name = "nachweis_edit.html"
    fields = ALL_FIELDS
    title = "Nachweis Bearbeiten"
    success_url = reverse_lazy("nachweis_list")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add = self.extra_context["add"]

    def get_object(self, queryset=None):
        if not self.add:
            return super().get_object(queryset)


class NachweisListView(BaseViewMixin, ListView):
    model = Nachweis
    template_name = "nachweis_list.html"
    title = "Nachweis Liste"


class NachweisPrintView(BaseViewMixin, DetailView):
    model = Nachweis
    template_name = "print.html"
