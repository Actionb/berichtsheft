from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from web import models as _models


class UserCreationForm(BaseUserCreationForm):
    start_date = forms.DateField(required=False)

    class Meta(BaseUserCreationForm.Meta):
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "start_date", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start = self.fields["start_date"]
        start.label = _models.UserProfile._meta.get_field("start_date").verbose_name
        start.help_text = _models.UserProfile._meta.get_field("start_date").help_text

    def save(self, commit=True):
        user = super().save(commit=commit)
        start_date = self.cleaned_data["start_date"]
        profile = _models.UserProfile(user=user, start_date=start_date)
        if commit:
            profile.save()
        return user
