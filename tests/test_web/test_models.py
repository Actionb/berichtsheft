import pytest

from web import models as _models

pytestmark = pytest.mark.django_db


class TestNachweisModel:
    """Test the Nachweis model."""

    def test_str(self):
        """Assert that the string representation is as expected."""
        assert str(_models.Nachweis(nummer=42)) == "Nachweis #42"


class TestAbteilungModel:
    """Test the Abteilung model."""

    def test_str(self):
        """Assert that the string representation is as expected."""
        assert str(_models.Abteilung(name="Testabteilung")) == "Testabteilung"
