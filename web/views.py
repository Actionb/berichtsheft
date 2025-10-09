from django import forms

from django.views.generic import UpdateView, ListView

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
    fields = forms.ALL_FIELDS
    title = "Nachweis Bearbeiten"

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
