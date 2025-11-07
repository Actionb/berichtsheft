from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from web import models as _models


class UserCreationForm(BaseUserCreationForm):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

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


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label=get_user_model()._meta.get_field("first_name").verbose_name, required=False)
    last_name = forms.CharField(label=get_user_model()._meta.get_field("last_name").verbose_name, required=False)

    class Meta:
        model = _models.UserProfile
        fields = ["first_name", "last_name", "start_date"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def save(self, commit=True):
        user_profile = super().save(commit=commit)
        if commit:
            user_profile.user.first_name = self.cleaned_data["first_name"]
            user_profile.user.last_name = self.cleaned_data["last_name"]
            user_profile.user.save()
        return user_profile
