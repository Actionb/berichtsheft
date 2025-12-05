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


class TestUserProfileForm:
    @pytest.fixture
    def form_data(self):
        return {
            "start_date": "2024-01-01",
            "first_name": "Alice",
            "last_name": "Testman",
            "interval": _models.UserProfile.IntervalType.DAILY,
        }

    @pytest.fixture
    def user(self, create_user):
        return create_user(first_name="Bob", last_name="Builder")

    @pytest.mark.django_db
    def test_save_updates_user(self, user, form_data):
        """Assert that saving the form updates the user's first and last name."""
        form = _forms.UserProfileForm(instance=user.profile, data=form_data)
        assert form.is_valid(), form.errors
        form.save(commit=True)
        user.refresh_from_db()
        assert user.first_name == "Alice"
        assert user.last_name == "Testman"

    @pytest.mark.django_db
    def test_save_not_updates_user_commit_false(self, user, form_data):
        """
        Assert that saving the form with commit=False does not update the user's
        first and last name.
        """
        first_name, last_name = user.first_name, user.last_name
        form = _forms.UserProfileForm(instance=user.profile, data=form_data)
        assert form.is_valid(), form.errors
        form.save(commit=False)
        user.refresh_from_db()
        assert user.first_name == first_name
        assert user.last_name == last_name
