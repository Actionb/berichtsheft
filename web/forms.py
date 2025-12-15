from typing import Any, Iterable, Optional

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import QuerySet

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
        fields = ["first_name", "last_name", "start_date", "interval"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def save(self, commit=True):
        user_profile = super().save(commit=commit)
        if commit:
            user_profile.user.first_name = self.cleaned_data["first_name"]
            user_profile.user.last_name = self.cleaned_data["last_name"]
            user_profile.user.save()
        return user_profile


class RangeWidget(forms.MultiWidget):
    """
    A MultiWidget that takes one widget and duplicates it for the purposes
    of __range lookups.
    """

    template_name = "widgets/rangewidget.html"

    def __init__(self, widget: forms.Widget, attrs: Optional[dict] = None) -> None:
        super().__init__(widgets=[widget] * 2, attrs=attrs)

    def decompress(self, value: Optional[str]) -> str:
        # Split value into two values (start, end).
        # NOTE:
        # decompress is only used to prepare single values fetched from the
        # database, either for use as initial values or as data if the field
        # is disabled (see MultiValueField methods has_changed and clean).
        # But RangeWidget is only used in search forms and only interacts with
        # data put in by the user, and never database data, so this method is
        # never called.
        return [None, None]


class RangeFormField(forms.MultiValueField):
    """
    A MultiValueField wrapper around a formfield that duplicates the field for
    use in a __range lookup (start, end).
    """

    widget = RangeWidget

    def __init__(self, formfield: forms.Field, require_all_fields: bool = False, **kwargs: Any) -> None:
        if not kwargs.get("widget"):
            # Create a RangeWidget from the formfield's default widget.
            kwargs["widget"] = RangeWidget(formfield.widget)
        self.empty_values = formfield.empty_values
        super().__init__(fields=[formfield] * 2, require_all_fields=require_all_fields, **kwargs)

    def get_initial(self, initial: dict, name: Any) -> list:
        return self.widget.value_from_datadict(data=initial, files=None, name=name)

    def compress(self, data_list: list) -> list:
        if not data_list:
            # Return two empty values, one for each field.
            return [None, None]
        return data_list


class SearchForm(forms.Form):
    """
    Default form class for list view search forms.

    The form derives filter parameters for querysets from the form data via the
    `get_filters` and `get_text_search_filters` methods. These filters can then
    be applied to a queryset via the `apply_filters` method.

    Search Parameters:
    The data from the formfields (excluding the text search formfield) is
    transformed into queryset filter parameters via the `get_filters` method.
    The dict `lookups` maps formfield names to django queryset lookups to use
    with that formfield. Uses the exact lookup if no lookup is defined for a
    field.

        Example:

            foo = forms.IntegerField(...)
            bar = forms.CharField(...)

            lookups = {"foo": "range"}

            ==> queryset.filter(foo__range=?, bar=?)

    Text Search:
    The form provides one field by default; the user can use the field 'q' to
    input their search terms for text search. The data from that field is then
    applied to each field listed in `text_search_fields` using the lookup
    defined with `text_search_lookup` (default: "icontains"). These filters are
    then combined into a Q object with logical OR. `get_text_search_filters`
    returns that Q object.

        Example:

            text_search_fields = ["foo", "bar"]
            text_search_lookup = "contains"

            ==> queryset.filter(Q(foo__contains=?) | Q(bar__contains=?))
    """

    q = forms.CharField(label="Textsuche", required=False)

    lookups: dict
    text_search_fields: Iterable = ()
    text_search_lookup: str = "icontains"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, "lookups"):
            self.lookups = {}

    def get_text_search_filters(self) -> Q:
        """Create a filter from the data of the text search formfield."""
        q = Q()
        if self.is_valid() and self.cleaned_data["q"]:
            for field in self.text_search_fields:
                q |= Q(**{"".join([field, LOOKUP_SEP, self.text_search_lookup]): self.cleaned_data["q"]})
        return q

    def get_filters(self) -> dict:
        """Turn the form data into parameters for queryset.filter()."""
        if not self.is_valid():
            return {}

        params = {}
        for name, value in self.cleaned_data.items():
            if name == "q":
                continue

            formfield = self.fields[name]
            param_value = value
            if name in self.lookups:
                param_key = "".join([name, LOOKUP_SEP, self.lookups[name]])
            else:
                param_key = name

            if isinstance(formfield, RangeFormField):
                start, end = value
                start_empty = start in formfield.empty_values
                end_empty = end in formfield.empty_values
                if start_empty and end_empty:
                    # start and end are empty: just skip it.
                    continue
                elif not start_empty and end_empty:
                    # start but no end: exact lookup for start
                    param_key = name
                    param_value = start
                elif start_empty and not end_empty:
                    # no start but end: lte lookup for end
                    param_key = "".join([name, LOOKUP_SEP, "lte"])
                    param_value = end
            elif value in formfield.empty_values or isinstance(value, QuerySet) and not value.exists():
                # Don't want empty values as filter parameters!
                continue
            else:
                param_value = value
            params[param_key] = param_value
        return params

    def apply_filters(self, queryset: QuerySet) -> QuerySet:
        """Apply the filters from the search form's data on the given queryset."""
        if not self.is_valid() or not self.cleaned_data:
            return queryset
        return queryset.filter(self.get_text_search_filters(), **self.get_filters())
