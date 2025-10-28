import contextlib
from unittest import mock

import pytest
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from web import models as _models

################################################################################
# MOCKS
################################################################################


@pytest.fixture
def mock_super_method():
    """
    Fixture that mocks the super call in a method.

    Usage:
        # stuff.py
        class CoolClass:
            def example_method(self, foo):
                bar = super().example_method(foo)
                return frobnicate(bar)

        # test.py
        def test_example_method(mock_super_method):
            with mock_super_method(CoolClass.example_method, "mocked result"):
                assert foo.bar.example_method("baz") == frobnicate("mocked result")
    """

    @contextlib.contextmanager
    def inner(func, ret=None):
        module = func.__module__
        attr = func.__qualname__.rsplit(".", 1)[-1]
        with mock.patch(f"{module}.super") as super_mock:
            return_mock = super_mock.return_value
            return_mock.attach_mock(mock.Mock(return_value=ret), attr)
            yield

    return inner


################################################################################
# USER & PERMISSIONS
################################################################################


@pytest.fixture
def username():
    """Default username for tests. Overwrite via test parametrization."""
    return "testuser"


@pytest.fixture
def create_user(django_user_model, username):
    """Create a user for testing."""
    return django_user_model.objects.create(username=username)


@pytest.fixture
def login_user(client, user):
    """Login the test user."""
    client.force_login(user)


@pytest.fixture
def add_permission():
    """Add a permission to the given user."""

    def inner(user, action, opts, reload=True):
        perm, _ = Permission.objects.get_or_create(
            codename=get_permission_codename(action, opts),
            content_type=ContentType.objects.get_for_model(opts.model),
        )
        user.user_permissions.add(perm)
        if reload:
            return user._meta.model.objects.get(pk=user.pk)
        return user  # pragma: no cover

    return inner


@pytest.fixture
def set_user_perms(create_user, user_perms, add_permission):
    """
    Set permissions of the test user.

    Fixture `user_perms` provides a 2-tuple of (<action>, <model>). Use test
    method parametrization to define the 2-tuple:

        @pytest.mark.parametrize("user_perms", [("add", _models.Nachweis)])
        @pytest.mark.usefixtures("user_perms", "set_user_perms")
        def test():
            ...

    Set `user_perms` to None to forgo adding permissions.
    """
    if user_perms is None:
        return
    try:
        for action, model in user_perms:
            add_permission(create_user, action, model._meta)
    except ValueError:  # pragma: no cover
        raise Exception("`user_perms` must be a list of 2-tuple (<action>, <model>)")


@pytest.fixture
def user(create_user):
    """Fetch user from database and return it. This resets the permission cache."""
    return create_user._meta.model.objects.get(pk=create_user.pk)


@pytest.fixture(params=[_models.Abteilung, _models.Nachweis])
def nachweis_model(request):
    """The set of models required to manage work reports (Nachweise)."""
    return request.param


@pytest.fixture(params=["add", "change", "view", "delete"])
def nachweis_actions(request):
    """The set of actions required to manage work reports (Nachweise)."""
    return request.param


@pytest.fixture
def nachweis_permission(nachweis_model, nachweis_actions):
    """
    The set of permissions that a user requires to effectively manage work
    reports (Nachweise).

    For instance, this includes permissions for CRUD'ing Nachweis objects.

    Usage:
        def test_permissions(nachweis_permission, user):
            assert user.has_perm(nachweis_permission)
    """
    opts = nachweis_model._meta
    return f"{opts.app_label}.{get_permission_codename(nachweis_actions, opts)}"
