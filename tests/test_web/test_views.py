from datetime import date
from unittest import mock

import pytest
from django.http import HttpResponse
from django.urls import path, reverse

from tests.model_factory import NachweisFactory
from web import models as _models
from web import views as _views


def dummy_view(*_args, **_kwargs):
    return HttpResponse("test")  # pragma: no cover


urlpatterns = [
    path("test/print_preview", dummy_view, name="print_preview"),
    path("nachweis/add/", _views.NachweisEditView.as_view(extra_context={"add": True}), name="nachweis_add"),
    path(
        "nachweis/<path:pk>/change/",
        _views.NachweisEditView.as_view(extra_context={"add": False}),
        name="nachweis_change",
    ),
    path("nachweis/<path:pk>/print/", _views.NachweisPrintView.as_view(), name="nachweis_print"),
    path("nachweis/", _views.NachweisListView.as_view(), name="nachweis_list"),
    # Templates require these for rendering:
    path("login/", dummy_view, name="login"),
    path("logout/", dummy_view, name="logout"),
    path("password_change/", dummy_view, name="password_change"),
    path("password_change/done/", dummy_view, name="password_change_done"),
    path("signup/", _views.SignUpView.as_view(), name="signup"),
]

pytestmark = pytest.mark.urls(__name__)


class TestAutocompleteView:
    @pytest.mark.django_db
    @pytest.mark.usefixtures("login_user", "user_perms", "set_user_perms")
    @pytest.mark.parametrize(
        "user_perms, expected",
        [
            (None, False),
            ([("add", _models.Nachweis)], True),
        ],
    )
    def test_has_add_permission(self, rf, user, expected):
        """
        Assert that has_add_permission requires the user to have the
        appropriate 'add' permission.
        """
        view = _views.AutocompleteView()
        view.model = _models.Nachweis
        request = rf.get("/")
        request.user = user
        assert view.has_add_permission(request) == expected


class TestBaseViewMixin:
    def test_get_context_data(self, mock_super_method):
        """Assert that the title is added to the context data."""
        view = _views.BaseViewMixin()
        view.title = "foo"
        with mock_super_method(_views.BaseViewMixin.get_context_data, {}):
            context = view.get_context_data()
            assert context["title"] == "foo"


class TestModelViewMixin:
    @pytest.fixture
    def opts(self):
        return mock.Mock()

    @pytest.fixture
    def model(self, opts):
        return mock.Mock(_meta=opts)

    @pytest.fixture
    def view_class(self, model):
        return type("DummyView", (_views.ModelViewMixin,), {"model": model})

    def test_get_context_data(self, mock_super_method, view_class, opts):
        """Assert that the model options are added to the context data."""
        view = view_class()
        with mock_super_method(view.get_context_data, {}):
            context = view.get_context_data()
            assert context["opts"] == opts


class TestEditView:
    @pytest.fixture
    def model(self):
        return _models.Nachweis

    @pytest.fixture
    def view_class(self, model):
        return type("DummyView", (_views.EditView,), {"model": model})

    @pytest.fixture
    def add_view(self, view_class):
        return view_class(extra_context={"add": True})

    @pytest.fixture
    def edit_view(self, view_class, obj):
        return view_class(extra_context={"add": False}, kwargs={"pk": obj.pk})

    @pytest.fixture
    def obj(self):
        return NachweisFactory()

    def test_init_add(self, add_view, model):
        """Assert that init sets the add flag and title correctly when adding."""
        assert add_view.add
        assert add_view.title == f"{model._meta.verbose_name} erstellen"

    @pytest.mark.django_db
    def test_init_edit(self, edit_view, model):
        """Assert that init sets the add flag and title correctly when editing."""
        assert not edit_view.add
        assert edit_view.title == f"{model._meta.verbose_name} bearbeiten"

    def test_get_object_add(self, add_view):
        """Assert that get_object returns None when adding."""
        assert add_view.get_object() is None

    @pytest.mark.django_db
    def test_get_object_edit(self, edit_view, obj):
        """Assert that get_object returns the expected object when editing."""
        assert edit_view.get_object() == obj

    def test_init_title(self, view_class):
        """Assert that init does not overwrite a title set on the view class."""
        view_class.title = "foo"
        view = view_class(extra_context={"add": True})
        assert view.title == "foo"

    @pytest.mark.django_db
    @pytest.mark.usefixtures("user_perms", "set_user_perms")
    @pytest.mark.parametrize(
        "user_perms, expected_value",
        [
            (None, False),
            ([("add", _models.Nachweis)], True),
        ],
    )
    def test_has_permission_add(self, add_view, expected_value, user):
        """Assert that has_permission checks for 'add' permission when adding."""
        add_view.request = mock.Mock(user=user)
        assert add_view.has_permission() == expected_value

    @pytest.mark.django_db
    @pytest.mark.usefixtures("user_perms", "set_user_perms")
    @pytest.mark.parametrize(
        "user_perms, expected_value",
        [
            (None, False),
            ([("change", _models.Nachweis)], True),
        ],
    )
    def test_has_permission_change(self, edit_view, expected_value, user):
        """Assert that has_permission checks for 'change' permission when editing."""
        edit_view.request = mock.Mock(user=user)
        assert edit_view.has_permission() == expected_value

    def test_get_permission_required_add(self, add_view, model):
        """Assert that get_permission_required returns the expected permission."""
        assert add_view.get_permission_required() == [f"{model._meta.app_label}.add_{model._meta.model_name}"]

    @pytest.mark.django_db
    def test_get_permission_required_change(self, edit_view, model):
        """Assert that get_permission_required returns the expected permission."""
        assert edit_view.get_permission_required() == [f"{model._meta.app_label}.change_{model._meta.model_name}"]


class TestNachweisEditView:
    @pytest.fixture
    def view(self):
        return _views.NachweisEditView(extra_context={"add": True})

    @pytest.fixture
    def form_fields(self, view):
        form_class = view.get_form_class()
        return form_class().fields

    @pytest.fixture
    def obj(self):
        # TODO: move into conftest.py
        return NachweisFactory()

    @pytest.mark.django_db
    @pytest.mark.parametrize("field_name", ["datum_start", "datum_ende"])
    def test_get_form_class_date_widgets(self, field_name, form_fields):
        """Assert that the date widgets use the correct type and format."""
        assert form_fields[field_name].widget.input_type == "date"
        assert form_fields[field_name].widget.format == "%Y-%m-%d"

    def test_get_context_data_print_preview(self, view, mock_super_method):
        """Assert that the context data contains the URL for the print preview."""
        with mock_super_method(view.get_context_data, {}):
            context = view.get_context_data()
            assert context["preview_url"] == "/test/print_preview"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "user_perms, expected_code",
        [
            (None, 403),  # expect 403 if no permissions
            ([("add", _models.Nachweis)], 200),
        ],
    )
    @pytest.mark.usefixtures("login_user", "user_perms", "set_user_perms")
    def test_add_permission_required(self, client, expected_code):
        """Assert that certain permissions are required to access the add view."""
        assert client.get(reverse("nachweis_add")).status_code == expected_code

    @pytest.mark.django_db
    @pytest.mark.usefixtures("login_user", "user_perms", "set_user_perms")
    @pytest.mark.parametrize(
        "user_perms, expected_code",
        [
            (None, 403),  # expect 403 if no permissions
            ([("change", _models.Nachweis)], 200),
        ],
    )
    def test_change_permission_required(self, client, expected_code, obj):
        """Assert that certain permissions are required to access the change view."""
        assert client.get(reverse("nachweis_change", kwargs={"pk": obj.pk})).status_code == expected_code


@pytest.mark.django_db
def test_print_preview_form_object(rf):
    """Assert that print_preview is called with the expected Nachweis object."""
    data = {"betrieb": "foo", "jahr": 2025, "datum_start": "2025-10-22", "fertig": False}
    request = rf.get(reverse("print_preview"), query_params=data)
    with mock.patch("web.views.render") as mock_render:
        _views.print_preview(request)
        mock_render.assert_called()
        _, kwargs = mock_render.call_args
        request_obj = kwargs["context"]["object"]
        assert request_obj.betrieb == data["betrieb"]
        assert request_obj.jahr == data["jahr"]
        assert request_obj.datum_start == date.fromisoformat(data["datum_start"])
        assert request_obj.fertig == data["fertig"]


class TestSignUpView:
    @pytest.fixture
    def sign_up_user(self):
        """Use SignUpView to create a new user and return it."""
        form_data = {"username": "alice", "password1": "foobarbaz", "password2": "foobarbaz"}
        view = _views.SignUpView()
        form = view.get_form_class()(data=form_data)
        view.form_valid(form)
        return view.object

    @pytest.mark.django_db
    def test_form_valid_sets_permissions(self, sign_up_user, nachweis_permission):
        """
        Assert that, after successfully signing up, the user has the necessary
        permissions to work with the app.
        """
        assert sign_up_user.has_perm(nachweis_permission)
