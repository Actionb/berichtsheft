from datetime import date, timedelta

import pytest
from django import forms
from django.db.models import Q

from tests.model_factory import AbteilungFactory, NachweisFactory
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


class TestSearchForm:
    @pytest.fixture
    def form_class(self):
        class Form(_forms.SearchForm):
            no_lookup = forms.CharField(required=False)
            lookup = forms.CharField(required=False)
            empty = forms.CharField(required=False)
            range = _forms.RangeFormField(forms.DateField(widget=forms.DateInput, required=False), required=False)
            queryset = forms.ModelChoiceField(queryset=_models.Abteilung.objects, required=False)

            lookups = {
                "lookup": "icontains",
                "range": "range",
            }
            text_search_fields = ["text_search_1", "text_search_2"]

        return Form

    @pytest.fixture
    def abteilung(self):
        return AbteilungFactory()

    @pytest.fixture
    def form_data(self, test_case, abteilung):
        match test_case:
            case "no_lookup":
                return {"no_lookup": "foo"}
            case "lookup":
                return {"lookup": "bar"}
            case "empty":
                return {"empty": ""}
            case "range":
                return {"range_0": date(2025, 12, 12), "range_1": date(2025, 12, 13)}
            case "queryset":
                return {"queryset": abteilung.pk}
            case "range_no_start":
                return {"range_1": date(2025, 12, 13)}
            case "range_no_end":
                return {"range_0": date(2025, 12, 12)}
            case "invalid":
                return {"range_0": "f"}

    @pytest.fixture
    def expected(self, test_case, abteilung):
        match test_case:
            case "no_lookup":
                return {"no_lookup": "foo"}
            case "lookup":
                return {"lookup__icontains": "bar"}
            case "empty":
                return {}
            case "range":
                return {"range__range": [date(2025, 12, 12), date(2025, 12, 13)]}
            case "queryset":
                return {"queryset": abteilung}
            case "range_no_start":
                return {"range__lte": date(2025, 12, 13)}
            case "range_no_end":
                return {"range": date(2025, 12, 12)}
            case "invalid":
                return {}

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "test_case",
        [
            "no_lookup",
            "lookup",
            "empty",
            "range",
            "queryset",
            "range_no_start",
            "range_no_end",
            "invalid",
        ],
    )
    def test_get_filters(self, test_case, form_class, form_data, expected):
        """Assert that get_filters returns the expected queryset filter."""
        form = form_class(data=form_data)
        if test_case != "invalid":
            assert not form.errors
        assert form.get_filters() == expected

    def test_get_text_search_filters(self, form_class):
        """Assert that get_text_search_filters returns the expected filter."""
        form = form_class(data={"q": "foo"})
        assert form.get_text_search_filters() == Q(text_search_1__icontains="foo") | Q(text_search_2__icontains="foo")


class TestNachweisSearchForm:
    @pytest.fixture
    def abteilung(self, user):
        return AbteilungFactory(user=user)

    @pytest.fixture
    def not_user_abteilung(self, superuser):
        return AbteilungFactory(user=superuser)

    @pytest.fixture
    def result(self, user, abteilung):
        """The object that should come up as a search result."""
        return NachweisFactory(betrieb="foo bar baz", abteilung=abteilung, user=user, eingereicht_bei="Bob")

    @pytest.fixture
    def not_result(self, user):
        """An object that should NOT be included in the search results."""
        return NachweisFactory(user=user)

    @pytest.mark.usefixtures("not_user_abteilung")
    def test_abteilung_user_only(self, user, abteilung):
        """
        Assert that the choices for the 'abteilung' field are restricted to
        those of the current user.
        """
        form = _forms.NachweisSearchForm(user=user)
        assert list(form.fields["abteilung"].queryset) == [abteilung]

    @pytest.fixture
    def form_data(self, test_case, result):
        match test_case:
            case "text_search":
                return {"q": "foo"}
            case "datum":
                return {
                    "datum_start_0": result.datum_start - timedelta(weeks=1),
                    "datum_start_1": result.datum_start + timedelta(weeks=1),
                }
            case "jahr":
                return {"jahr": result.jahr}
            case "kalenderwoche":
                return {"kalenderwoche_0": result.kalenderwoche - 1, "kalenderwoche_1": result.kalenderwoche + 1}
            case "ausbildungswoche":
                return {
                    "ausbildungswoche_0": result.ausbildungswoche - 1,
                    "ausbildungswoche_1": result.ausbildungswoche + 1,
                }
            case "abteilung":
                return {"abteilung": result.abteilung.pk}
            case "nummer":
                return {"nummer": result.nummer}
            case "eingereicht_bei":
                return {"eingereicht_bei": result.eingereicht_bei}

    @pytest.mark.usefixtures("not_result")
    @pytest.mark.parametrize(
        "test_case",
        [
            "text_search",
            "datum",
            "jahr",
            "kalenderwoche",
            "ausbildungswoche",
            "abteilung",
            "nummer",
            "eingereicht_bei",
        ],
    )
    def test_apply_filters(self, user, form_data, result):
        """Assert that the form filters the queryset as expected."""
        form = _forms.NachweisSearchForm(data=form_data, user=user)
        assert not form.errors
        assert list(form.apply_filters(_models.Nachweis.objects.all())) == [result]

    @pytest.mark.parametrize("test_case, form_data", [("invalid", {"jahr": "foo"}), ("empty", {})])
    @pytest.mark.usefixtures("test_case")
    def test_apply_filters_invalid(self, user, result, not_result, form_data):
        """
        Assert that the form does not filter the queryset when the form is
        invalid or empty.
        """
        form = _forms.NachweisSearchForm(data=form_data, user=user)
        queryset = form.apply_filters(_models.Nachweis.objects.all())
        assert queryset.count() == 2
        assert result in queryset
        assert not_result in queryset
