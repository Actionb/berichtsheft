import contextlib
from unittest import mock

import pytest
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

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
    def inner(func, ret):
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
def user(django_user_model, username):
    """Create a user for testing."""
    return django_user_model.objects.create(username=username)


@pytest.fixture
def login_user(client, user):
    """Login the test user."""
    client.force_login(user)


@pytest.fixture
def add_permission(reload_user):
    """Add a permission to the test user."""

    def inner(user, action, opts, reload=True):
        perm, _ = Permission.objects.get_or_create(
            codename=get_permission_codename(action, opts),
            content_type=ContentType.objects.get_for_model(opts.model),
        )
        user.user_permissions.add(perm)
        if reload:
            return reload_user(user)
        return user

    return inner


@pytest.fixture
def reload_user(django_user_model):
    """Reload user from database and return it. This resets the permission cache."""

    def inner(user):
        return django_user_model.objects.get(pk=user.pk)

    return inner
