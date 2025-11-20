from datetime import date, datetime
from unittest import mock

import pytest
from django.contrib.auth import SESSION_KEY
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.urls import path, reverse

from tests.model_factory import AbteilungFactory, NachweisFactory
from web import models as _models
from web import views as _views


def dummy_view(*_args, **_kwargs):
    return HttpResponse("test")  # pragma: no cover


urlpatterns = [
    path("test/print_preview", dummy_view, name="print_preview"),
    path("nachweis/", _views.NachweisListView.as_view(), name="nachweis_list"),
    path("nachweis/add/", _views.NachweisEditView.as_view(extra_context={"add": True}), name="nachweis_add"),
    path(
        "nachweis/<path:pk>/change/",
        _views.NachweisEditView.as_view(extra_context={"add": False}),
        name="nachweis_change",
    ),
    path("nachweis/<path:pk>/delete/", _views.NachweisDeleteView.as_view(), name="nachweis_delete"),
    path("abteilung/<path:pk>/delete/", _views.AbteilungDeleteView.as_view(), name="abteilung_delete"),
    path("nachweis/<path:pk>/print/", _views.NachweisPrintView.as_view(), name="nachweis_print"),
    path("trash/", _views.PapierkorbView.as_view(), name="trash"),
    path("<str:model_name>/<int:pk>/restore/", _views.restore_object, name="restore_object"),
    path("<str:model_name>/<int:pk>/hard_delete/", _views.HardDeleteView.as_view(), name="hard_delete"),
    # Templates require these for rendering:
    path("login/", dummy_view, name="login"),
    path("logout/", dummy_view, name="logout"),
    path("password_change/", dummy_view, name="password_change"),
    path("password_change/done/", dummy_view, name="password_change_done"),
    path("signup/", _views.SignUpView.as_view(), name="signup"),
    path("profile/", dummy_view, name="user_profile"),
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


class TestAbteilungAutocompleteView:
    @pytest.mark.usefixtures("login_superuser")
    def test_create_object_user(self, rf, superuser):
        """Assert that the created object is associated with the current user."""
        view = _views.AbteilungAutocompleteView()
        view.model = _models.Abteilung
        view.create_field = "name"
        view.request = rf.get("/")
        view.request.user = superuser
        obj = view.create_object(data={"name": "Foo"})
        assert obj.user == superuser


class TestBaseViewMixin:
    @pytest.fixture
    def mock_collect(self, deleted_objects):
        """Mock the collect_deleted_objects function."""
        with mock.patch("web.views.collect_deleted_objects") as m:
            querysets = deleted_objects[1]
            m.return_value = [(qs.model, qs) for qs in querysets]

    def test_get_context_data(self, mock_super_method):
        """Assert that the expected items are added to the context data."""
        view = _views.BaseViewMixin()
        view.title = "foo"
        view.submit_button_text = "bar"
        with mock_super_method(_views.BaseViewMixin.get_context_data, {}):
            with mock.patch.object(view, "get_trash_count", new=mock.Mock(return_value=42)):
                context = view.get_context_data()
                assert context["title"] == "foo"
                assert context["submit_button_text"] == "bar"
                assert context["trash_count"] == 42

    @pytest.mark.usefixtures("mock_collect")
    def test_get_trash_count(self, user, deleted_objects):
        """Assert that get_trash_count counts the number of deleted objects."""
        view = _views.BaseViewMixin()
        view.request = mock.Mock(user=user)
        assert view.get_trash_count() == deleted_objects[0]


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


class TestFilterUserMixin:
    @pytest.fixture
    def view_class(self):
        return type("DummyView", (_views.FilterUserMixin,), {"model": _models.Nachweis})

    def test_get_queryset(self, mock_super_method, view_class, user):
        """Assert that get_queryset filters by the current user."""
        user_obj = NachweisFactory(user=user)
        not_user_obj = NachweisFactory()
        view = view_class()
        view.request = mock.Mock(user=user)
        with mock_super_method(view.get_queryset, _models.Nachweis.objects.all()):
            queryset = view.get_queryset()
            assert user_obj in queryset
            assert not_user_obj not in queryset


class TestRequireUserMixin:
    @pytest.fixture
    def view_class(self):
        return type("DummyView", (_views.RequireUserMixin,), {"model": _models.Nachweis})

    def test_get_object_raises_permission_denied(self, mock_super_method, user, superuser, view_class):
        """
        Assert that get_object raises PermissionDenied if the current user is
        not the owner of the object.
        """
        obj = NachweisFactory(user=superuser)
        view = view_class()
        view.request = mock.Mock(user=user)
        with mock_super_method(view.get_object, obj):
            with pytest.raises(PermissionDenied):
                view.get_object()

    def test_get_object_returns_user_object(self, mock_super_method, user, view_class):
        """
        Assert that get_object returns the object if the current user is the
        owner of the object.
        """
        obj = NachweisFactory(user=user)
        view = view_class()
        view.request = mock.Mock(user=user)
        with mock_super_method(view.get_object, obj):
            assert view.get_object() == obj


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
    def obj(self, user):
        return NachweisFactory(user=user)

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
    def test_get_object_edit(self, rf, user, edit_view, obj):
        """Assert that get_object returns the expected object when editing."""
        edit_view.request = rf.get("/")
        edit_view.request.user = user
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

    @mock.patch("web.views.perms.has_delete_permission", mock.Mock(return_value=True))
    def test_get_context_data_delete_url(self, edit_view, mock_super_method, rf, user):
        """
        Assert that get_context_data includes calls get_delete_url if the user
        has the required permissions and the view is an edit view.
        """
        edit_view.request = mock.Mock(user=None)
        with mock_super_method(edit_view.get_context_data, {}):
            with mock.patch.object(edit_view, "get_delete_url") as delete_url_mock:
                edit_view.get_context_data()
                delete_url_mock.assert_called()

    @mock.patch("web.views.perms.has_delete_permission", mock.Mock(return_value=True))
    def test_get_context_data_delete_url_add(self, add_view, mock_super_method):
        """
        Assert get_context_data does not call get_delete_url if the view is an
        add view.
        """
        with mock_super_method(add_view.get_context_data, {}):
            with mock.patch.object(add_view, "get_delete_url") as delete_url_mock:
                add_view.get_context_data()
                delete_url_mock.assert_not_called()

    @mock.patch("web.views.perms.has_delete_permission", mock.Mock(return_value=False))
    def test_get_context_data_delete_url_no_perms(self, edit_view, mock_super_method):
        """
        Assert that get_context_data does not call get_delete_url if the user
        does not have the required permissions.
        """
        edit_view.request = mock.Mock(user=None)
        with mock_super_method(edit_view.get_context_data, {}):
            with mock.patch.object(edit_view, "get_delete_url") as delete_url_mock:
                edit_view.get_context_data()
                delete_url_mock.assert_not_called()


class TestNachweisEditView:
    @pytest.fixture
    def add_view(self):
        return _views.NachweisEditView(extra_context={"add": True})

    @pytest.fixture
    def edit_view(self, obj):
        return _views.NachweisEditView(extra_context={"add": False}, kwargs={"pk": obj.pk})

    @pytest.fixture
    def add_url(self):
        def inner():
            return reverse("nachweis_add")

        return inner

    @pytest.fixture
    def edit_url(self):
        def inner(obj):
            return reverse("nachweis_change", kwargs={"pk": obj.pk})

        return inner

    @pytest.fixture
    def form_data(self, superuser):
        abteilung = AbteilungFactory()
        return {
            "betrieb": "Testbetrieb",
            "schule": "Testschule",
            "nummer": 42,
            "ausbildungswoche": 1,
            "jahr": 2023,
            "kalenderwoche": 32,
            "datum_start": "2023-01-01",
            "datum_ende": "2023-12-31",
            "abteilung": abteilung.pk,
            "user": superuser.pk,
        }

    @pytest.fixture
    def form_fields(self, add_view):
        form_class = add_view.get_form_class()
        return form_class().fields

    @pytest.fixture
    def obj(self, user):
        # TODO: move into conftest.py
        return NachweisFactory(user=user)

    @pytest.mark.usefixtures("login_superuser")
    def test_add_get(self, client, add_url):
        """Assert that the superuser can request the page with the add form."""
        response = client.get(add_url())
        assert response.status_code == 200

    @pytest.mark.usefixtures("login_superuser")
    def test_add_post(self, client, add_url, form_data):
        """Assert that the superuser can create a new Nachweis with the add form."""
        assert not _models.Nachweis.objects.exists()
        response = client.post(add_url(), data=form_data, follow=True)
        assert response.status_code == 200
        assert _models.Nachweis.objects.filter(betrieb=form_data["betrieb"]).exists()

    @pytest.mark.usefixtures("login_superuser")
    def test_edit_get(self, client, edit_url, superuser):
        """Assert that the superuser can request the page with the edit form."""
        obj = NachweisFactory(user=superuser)
        response = client.get(edit_url(obj))
        assert response.status_code == 200

    @pytest.mark.usefixtures("login_superuser")
    def test_edit_post(self, client, edit_url, form_data, superuser):
        """
        Assert that the superuser can edit an existing Nachweis with the edit
        form.
        """
        obj = NachweisFactory(user=superuser)
        response = client.post(edit_url(obj), data=form_data, follow=True)
        assert response.status_code == 200
        obj.refresh_from_db()
        assert obj.betrieb == form_data["betrieb"]

    @pytest.mark.django_db
    @pytest.mark.parametrize("field_name", ["datum_start", "datum_ende"])
    def test_get_form_class_date_widgets(self, field_name, form_fields):
        """Assert that the date widgets use the correct type and format."""
        assert form_fields[field_name].widget.input_type == "date"
        assert form_fields[field_name].widget.format == "%Y-%m-%d"

    def test_get_context_data_print_preview(self, add_view, mock_super_method):
        """Assert that the context data contains the URL for the print preview."""
        with mock_super_method(add_view.get_context_data, {}):
            context = add_view.get_context_data()
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
    def test_add_permission_required(self, client, expected_code, add_url):
        """Assert that certain permissions are required to access the add view."""
        assert client.get(add_url()).status_code == expected_code

    @pytest.mark.django_db
    @pytest.mark.usefixtures("login_user", "user_perms", "set_user_perms")
    @pytest.mark.parametrize(
        "user_perms, expected_code",
        [
            (None, 403),  # expect 403 if no permissions
            ([("change", _models.Nachweis)], 200),
        ],
    )
    def test_change_permission_required(self, client, expected_code, obj, edit_url):
        """Assert that certain permissions are required to access the change view."""
        assert client.get(edit_url(obj)).status_code == expected_code

    def test_can_not_edit_other_users_nachweise(self, client, superuser, edit_url, obj):
        """Assert that a user can not edit Nachweise that do not belong to them."""
        client.force_login(superuser)
        assert client.get(edit_url(obj)).status_code == 403

    @pytest.mark.usefixtures("login_superuser")
    def test_view_object_saved_with_user(self, client, superuser, form_data, add_url):
        """Assert that the view's object is saved with the current user."""
        del form_data["user"]
        response = client.post(add_url(), data=form_data, follow=True)
        assert response.status_code == 200
        assert _models.Nachweis.objects.get().user == superuser

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("jahr", datetime.now().year),
            ("kalenderwoche", datetime.now().isocalendar()[1]),
            ("datum_start", str(date.fromisocalendar(datetime.now().year, datetime.now().isocalendar()[1], 1))),
            ("datum_ende", str(date.fromisocalendar(datetime.now().year, datetime.now().isocalendar()[1], 5))),
        ],
    )
    def test_form_initial(self, rf, user, add_view, field, expected):
        """Assert that the view provides sensible initial data for the form."""
        add_view.request = rf.get("/")
        add_view.request.user = user
        initial_data = add_view.get_initial()
        assert initial_data[field] == expected

    def test_form_initial_nummer(self, rf, user, add_view, obj):
        """Assert that the initial value of 'nummer' is as expected."""
        add_view.request = rf.get("/")
        add_view.request.user = user
        initial_data = add_view.get_initial()
        assert initial_data["nummer"] == obj.nummer + 1

    def test_form_initial_ausbildungswoche(self, rf, user, add_view):
        """Assert that the initial value of 'ausbildungswoche' is as expected."""
        user.profile.start_date = date(year=2025, month=8, day=1)
        user.profile.save()
        add_view.request = rf.get("/")
        add_view.request.user = user
        with mock.patch("web.views.date") as m:
            m.today.return_value = date(year=2027, month=1, day=1)
            initial_data = add_view.get_initial()
            assert initial_data["ausbildungswoche"] == 75

    def test_form_initial_ausbildungswoche_start_date_not_set(self, rf, user, add_view):
        """
        Assert that no initial value for 'ausbildungswoche' is provided if no
        start_date is set in the profile.
        """
        user.profile.start_datum = None
        add_view.request = rf.get("/")
        add_view.request.user = user
        initial_data = add_view.get_initial()
        assert "ausbildungswoche" not in initial_data

    def test_form_initial_ausbildungswoche_no_user_profile(self, rf, user, add_view):
        """
        Assert that no initial value for 'ausbildungswoche' is provided if the
        user has no profile.
        """
        _models.UserProfile.objects.filter(user=user).delete()
        add_view.request = rf.get("/")
        add_view.request.user = user
        initial_data = add_view.get_initial()
        assert "ausbildungswoche" not in initial_data

    def test_form_initial_edit_no_initial(self, edit_view):
        """Assert that the view does not provide initial data when editing."""
        assert not edit_view.get_initial()


class TestPrintPreview:
    @pytest.fixture
    def request_data(self):
        return {"betrieb": "foo", "jahr": 2025, "datum_start": "2025-10-22", "fertig": False}

    @pytest.fixture
    def preview_url(self):
        return reverse("print_preview")

    @pytest.fixture
    def mock_render(self):
        with mock.patch("web.views.render") as mock_render:
            yield mock_render

    @pytest.fixture
    def preview_request(self, rf, request_data, preview_url, user):
        request = rf.get(preview_url, query_params=request_data)
        request.user = user
        return request

    @pytest.fixture
    def preview_object(self, preview_request, mock_render):
        """Return the 'object' context item of the preview request."""
        _views.print_preview(preview_request)
        _, kwargs = mock_render.call_args
        return kwargs["context"]["object"]

    @pytest.mark.django_db
    def test_print_preview_form_object(self, preview_object, request_data):
        """
        Assert that the preview is rendered with the expected 'object' context
        item.
        """
        assert preview_object.betrieb == request_data["betrieb"]
        assert preview_object.jahr == request_data["jahr"]
        assert preview_object.datum_start == date.fromisoformat(request_data["datum_start"])
        assert preview_object.fertig == request_data["fertig"]

    @pytest.mark.django_db
    def test_print_preview_adds_user(self, preview_object, user):
        """Assert that the print_preview object includes the current user."""
        assert preview_object.user == user


class TestSignUpView:
    @pytest.fixture
    def signup_data(self):
        return {"username": "alice", "password1": "foobarbaz", "password2": "foobarbaz"}

    @pytest.fixture
    def sign_up(self, client, signup_data):
        """Use SignUpView to create a new user."""
        return client.post(reverse("signup"), data=signup_data)

    @pytest.fixture
    def sign_up_user(self, sign_up):
        """Use SignUpView to create a new user and return it."""
        return sign_up.wsgi_request.user

    @pytest.mark.django_db
    def test_form_valid_sets_permissions(self, sign_up_user, nachweis_permission):
        """
        Assert that, after successfully signing up, the user has the necessary
        permissions to work with the app.
        """
        assert sign_up_user.has_perm(nachweis_permission)

    @pytest.mark.django_db
    def test_creates_user_profile(self, sign_up_user):
        """Assert that a user profile is created for the new user."""
        assert _models.UserProfile.objects.filter(user=sign_up_user).exists()

    @pytest.mark.django_db
    def test_redirects_to_nachweis_list(self, sign_up):
        """Assert that the user is redirected to the nachweis list after signing up."""
        assert sign_up.status_code == 302
        assert sign_up.url == reverse("nachweis_list")

    @pytest.mark.django_db
    def test_signed_up_user_has_session_key(self, client, sign_up_user):
        """Assert that the user has a session key after signing up."""
        assert client.session[SESSION_KEY] == str(sign_up_user.pk)


class TestNachweisListView:
    @pytest.mark.django_db
    @pytest.mark.usefixtures("login_user", "user_perms", "set_user_perms")
    @pytest.mark.parametrize(
        "user_perms, expected_code",
        [
            (None, 403),  # expect 403 if no permissions
            ([("view", _models.Nachweis)], 200),
        ],
    )
    def test_view_permission_required(self, client, expected_code):
        """Assert that certain permissions are required to access the list view."""
        assert client.get(reverse("nachweis_list")).status_code == expected_code

    @pytest.mark.django_db
    def test_only_lists_user_nachweise(self, rf, user, superuser):
        """Assert that only Nachweis objects belonging to the user are listed."""
        nachweis_1 = NachweisFactory(user=superuser)
        nachweis_2 = NachweisFactory(user=user)  # belongs to a different user
        view = _views.NachweisListView()
        view.request = rf.get(reverse("nachweis_list"))
        view.request.user = superuser
        queryset = view.get_queryset()
        assert nachweis_1 in queryset
        assert nachweis_2 not in queryset


class TestUserProfileView:
    @pytest.fixture
    def user(self, create_user):
        return create_user(first_name="Alice", last_name="Testman", add_profile=True)

    @pytest.mark.usefixtures("login_user")
    def test_get_object(self, rf, user):
        """Assert that get_object returns the UserProfile of the current user."""
        view = _views.UserProfileView()
        view.request = rf.get("/")
        view.request.user = user
        assert view.get_object() == user.profile

    @pytest.mark.usefixtures("login_user")
    def test_get_object_creates_profile(self, rf, user):
        """
        Assert that get_object creates a profile if the current user does not
        already have one.
        """
        user.profile.delete()
        user.refresh_from_db()
        view = _views.UserProfileView()
        view.request = rf.get("/")
        view.request.user = user
        assert view.get_object() == user.profile

    def test_get_initial(self, rf, user):
        """Assert that get_initial includes the user's first and last name."""
        view = _views.UserProfileView()
        view.request = rf.get("/")
        view.request.user = user
        initial_data = view.get_initial()
        assert initial_data["first_name"] == user.first_name
        assert initial_data["last_name"] == user.last_name


class TestHandler403:
    @pytest.mark.parametrize(
        "exception, expected",
        [
            (None, "Sie haben nicht die Berechtigung, dieses Objekt anzusehen."),
            (PermissionDenied, "Sie haben nicht die Berechtigung, dieses Objekt anzusehen."),
            (PermissionDenied(), "Sie haben nicht die Berechtigung, dieses Objekt anzusehen."),
            (PermissionDenied("Foo"), "Foo"),
        ],
    )
    def test_uses_exception_message(self, rf, exception, expected):
        """
        Assert that the handler view passes any existing exception message as
        template context.
        """
        request = rf.get("/")
        with mock.patch("web.views.render") as mock_render:
            _views.handler403(request, exception)
            mock_render.assert_called()
            _args, kwargs = mock_render.call_args
            assert kwargs["context"]["content"] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("model", [_models.Nachweis, _models.Abteilung])
class TestDeleteNachweisView:
    @pytest.fixture
    def obj(self, user, model):
        if model == _models.Nachweis:
            return NachweisFactory(user=user)
        elif model == _models.Abteilung:
            return AbteilungFactory(user=user)

    @pytest.fixture
    def delete_url(self, obj, model):
        url_name = ""
        if model == _models.Nachweis:
            url_name = "nachweis_delete"
        elif model == _models.Abteilung:
            url_name = "abteilung_delete"
        return reverse(url_name, kwargs={"pk": obj.pk})

    @pytest.fixture
    def set_user_perms(self, user, add_permission, model):
        add_permission(user, "delete", model._meta)

    @pytest.mark.usefixtures("set_user_perms", "login_user")
    def test_can_delete(self, client, obj, delete_url):
        """Assert that a user can delete their own objects."""
        response = client.post(delete_url)
        assert response.status_code == 302
        assert not _models.Nachweis.objects.filter(pk=obj.pk).exists()
        assert response.url == reverse("nachweis_list")

    @pytest.mark.usefixtures("set_user_perms", "login_superuser")
    def test_cannot_delete_others(self, client, delete_url, obj):
        """Assert that a user cannot delete the objects of other users."""
        response = client.post(delete_url)
        assert response.status_code == 403
        obj.refresh_from_db()

    @pytest.mark.usefixtures("login_user")
    def test_delete_requires_permission(self, client, delete_url, obj):
        """Assert that only users with delete permission can delete."""
        response = client.post(delete_url)
        assert response.status_code == 403
        obj.refresh_from_db()

    @pytest.mark.usefixtures("set_user_perms", "login_user")
    def test_requires_post(self, client, delete_url, obj):
        """Assert that GET requests are not allowed."""
        response = client.get(delete_url)
        assert response.status_code == 405
        obj.refresh_from_db()


@pytest.mark.django_db
@pytest.mark.parametrize("model", [_models.Nachweis, _models.Abteilung])
class TestHardDelete:
    @pytest.fixture
    def delete_object(self):
        """Whether the test object should already be deleted."""
        return True

    @pytest.fixture
    def obj(self, user, model, delete_object):
        if model == _models.Nachweis:
            obj = NachweisFactory(user=user)
        elif model == _models.Abteilung:
            obj = AbteilungFactory(user=user)
        else:
            raise Exception("No factory for model:", model)
        if delete_object:
            obj.delete()
        return obj

    @pytest.fixture
    def hard_delete_url(self, obj, model):
        return reverse("hard_delete", kwargs={"model_name": model._meta.model_name, "pk": obj.pk})

    @pytest.fixture
    def set_user_perms(self, user, add_permission, model):
        add_permission(user, "delete", model._meta)

    @pytest.mark.usefixtures("set_user_perms", "login_user")
    def test_can_hard_delete(self, client, obj, hard_delete_url):
        """Assert that the object is removed permanently from the database."""
        response = client.post(hard_delete_url)
        assert response.status_code == 200
        assert not _models.Nachweis.global_objects.filter(pk=obj.pk).exists()

    @pytest.mark.usefixtures("login_user")
    def test_requires_permission(self, client, hard_delete_url, obj):
        """Assert that hard deletion requires delete permission."""
        response = client.post(hard_delete_url)
        assert response.status_code == 403
        obj.refresh_from_db()

    @pytest.mark.usefixtures("set_user_perms", "login_superuser")
    def test_cannot_delete_others(self, client, hard_delete_url, obj):
        """Assert that a user cannot delete objects of another user."""
        response = client.post(hard_delete_url)
        assert response.status_code == 403
        obj.refresh_from_db()

    @pytest.mark.parametrize("delete_object", [False])
    @pytest.mark.usefixtures("set_user_perms", "login_user")
    def test_can_only_hard_delete_deleted_objects(self, client, hard_delete_url, obj):
        """
        Assert that only objects that have been soft-deleted can be
        hard-deleted.
        """
        response = client.post(hard_delete_url)
        assert response.status_code == 404
        obj.refresh_from_db()

    @pytest.mark.usefixtures("set_user_perms", "login_user")
    def test_get_not_allowed(self, client, hard_delete_url, obj):
        """Assert that GET requests are not allowed."""
        response = client.get(hard_delete_url)
        assert response.status_code == 405
        obj.refresh_from_db()


class TestPapierkorbView:
    @pytest.mark.usefixtures("login_user")
    def test(self, client):
        """Assert that the view can be accessed."""
        response = client.get(reverse("trash"))
        assert response.status_code == 200

    def test_get_context_data_deleted_objects(self, mock_super_method, deleted_objects):
        """Assert that get_context_data adds the deleted_objects item."""
        view = _views.PapierkorbView()
        with mock_super_method(view.get_context_data, {}):
            with mock.patch.object(view, "get_queryset") as mock_get_queryset:
                mock_get_queryset.return_value = deleted_objects[1]
                ctx = view.get_context_data()
                assert ctx["deleted_objects"] == [(qs.model._meta, qs) for qs in deleted_objects[1]]


class TestRestoreObject:
    @pytest.fixture
    def obj(self, user):
        return NachweisFactory(user=user)

    @pytest.fixture
    def delete_obj(self, obj):
        obj.delete()

    @pytest.fixture
    def restore_url(self, obj):
        return reverse("restore_object", kwargs={"model_name": obj._meta.model_name, "pk": obj.pk})

    @pytest.fixture
    def restore_response(self, client, restore_url):
        """Request to restore the test object and return the response."""
        return client.get(restore_url)

    @pytest.mark.parametrize("user_perms", [[("delete", _models.Nachweis)]])
    @pytest.mark.usefixtures("login_user", "user_perms", "set_user_perms", "delete_obj")
    def test(self, client, restore_url, obj):
        """Assert that restore_object restores the expected object."""
        response = client.get(restore_url)
        obj.refresh_from_db()
        assert response.status_code == 200
        assert not obj.is_deleted

    @pytest.mark.usefixtures("login_superuser", "delete_obj")
    def test_user_can_only_restore_own(self, client, restore_url):
        """Assert that user can only restore their own objects."""
        assert client.get(restore_url).status_code == 403

    @pytest.mark.usefixtures("login_user", "delete_obj")
    def test_requires_permissions(self, client, restore_url):
        """Assert that restoring requires the user to have certain permissions."""
        assert client.get(restore_url).status_code == 403

    @pytest.mark.parametrize("user_perms", [[("delete", _models.Nachweis)]])
    @pytest.mark.usefixtures("login_user", "user_perms", "set_user_perms")
    def test_can_only_restore_deleted_objects(self, client, restore_url):
        """Assert that only soft-deleted objects can be restored."""
        assert client.get(restore_url).status_code == 404
