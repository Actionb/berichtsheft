import pytest

from tests.test_utils.models import PermsTestModel
from web.utils.perms import add_azubi_permissions, has_add_permission, has_change_permission, has_delete_permission


@pytest.fixture
def opts():
    return PermsTestModel._meta


def test_has_add_permission(user, opts, add_permission):
    assert not has_add_permission(user, opts)
    user = add_permission(user, "add", opts)
    assert has_add_permission(user, opts)


def test_has_change_permission(user, opts, add_permission):
    assert not has_change_permission(user, opts)
    user = add_permission(user, "change", opts)
    assert has_change_permission(user, opts)


def test_has_delete_permission(user, opts, add_permission):
    assert not has_delete_permission(user, opts)
    user = add_permission(user, "delete", opts)
    assert has_delete_permission(user, opts)


@pytest.fixture
def user_with_permissions(create_user):
    """Create a user with the default permissions."""
    user = create_user()
    add_azubi_permissions(user)
    return user


@pytest.mark.django_db
def test_add_azubi_permissions(user_with_permissions, nachweis_permission):
    """Assert that add_azubi_permissions adds the expected permissions."""
    assert user_with_permissions.has_perm(nachweis_permission)
