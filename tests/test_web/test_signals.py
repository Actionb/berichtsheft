import pytest
from django.contrib.auth.models import Group

from web.signals import create_azubi_group


@pytest.fixture
def azubi_group_name():
    return "Azubi_Test_Group"


@pytest.fixture
def azubi_permissions():
    return {"Nachweis": ["add"]}


@pytest.fixture
def modified_settings(settings, azubi_group_name, azubi_permissions):
    """Modify settings for the test."""
    settings.AZUBI_GROUP_NAME = azubi_group_name
    settings.AZUBI_PERMISSIONS = azubi_permissions
    return settings


@pytest.fixture(autouse=True)
def mock_assure_permissions_created(monkeypatch):
    """Mock the _assure_permissions_created function."""
    return monkeypatch.setattr("web.signals._assure_permissions_created", lambda: None)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "codename, expected",
    [
        ("add_nachweis", True),
        ("change_nachweis", False),
    ],
)
def test_create_azubi_group(modified_settings, codename, expected):
    """
    Assert that create_azubi_group adds the expected permissions to the Azubi
    group.
    """
    create_azubi_group()
    group = Group.objects.get(name=modified_settings.AZUBI_GROUP_NAME)
    assert group.permissions.filter(codename=codename).exists() == expected
