from django import forms

from django.views.generic import UpdateView, ListView

from web.models import Nachweis


class NachweisEditView(UpdateView):
    model = Nachweis
    template_name = "nachweis_edit.html"
    fields = forms.ALL_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add = self.extra_context["add"]

    def get_object(self, queryset=None):
        if not self.add:
            return super().get_object(queryset)

