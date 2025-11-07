import pytest

from web import forms as _forms
from web import models as _models


class TestUserCreationForm:
    @pytest.fixture
    def form_data(self):
        return {
            "username": "testuser",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
            "start_date": "2024-01-01",
        }

    @pytest.mark.django_db
    def test_start_date_field_label(self):
        """Assert that the start_date field has the expected label."""
        form = _forms.UserCreationForm()
        assert form.fields["start_date"].label == "Startdatum"

    @pytest.mark.django_db
    def test_start_date_field_help_text(self):
        """Assert that the start_date field has the expected help text."""
        form = _forms.UserCreationForm()
        assert (
            form.fields["start_date"].help_text
            == "Startdatum der Ausbildung. Wird benötigt für die Errechnung von Datumsangaben der Nachweise."
        )

    @pytest.mark.django_db
    def test_save_creates_user_profile(self, form_data):
        """Assert that saving the form creates a UserProfile for the user."""
        form = _forms.UserCreationForm(data=form_data)
        assert form.is_valid(), form.errors
        user = form.save()
        assert user.profile
        assert user.profile.start_date.isoformat() == "2024-01-01"

    @pytest.mark.django_db
    def test_save_no_commit(self, form_data):
        """
        Assert that no profile is created if save was called with commit=False.
        """
        form = _forms.UserCreationForm(data=form_data)
        assert form.is_valid(), form.errors
        form.save(commit=False)
        assert not _models.UserProfile.objects.exists()
