from datetime import date
from unittest import mock

import pytest

from tests.model_factory import NachweisFactory
from web import models as _models

pytestmark = pytest.mark.django_db


@pytest.fixture
def year():
    return 2025


@pytest.fixture
def week():
    return 46


@pytest.fixture
def mock_get_current_year(year):
    with mock.patch("web.models._get_current_year") as m:
        m.return_value = year
        yield m


@pytest.fixture
def mock_get_current_week(week):
    with mock.patch("web.models._get_current_week") as m:
        m.return_value = week
        yield m


@pytest.mark.usefixtures("mock_get_current_year", "mock_get_current_week")
class TestNachweisModel:
    """Test the Nachweis model."""

    def test_str(self):
        """Assert that the string representation is as expected."""
        assert str(_models.Nachweis(nummer=42)) == "Nachweis #42"

    # Test the functions that generate the default values for the Nachweis model

    def test_nummer_default(self):
        """
        Assert that nummer_default returns the total count of all Nachweis
        objects plus one.
        """
        assert _models.nummer_default() == 1
        NachweisFactory()
        assert _models.nummer_default() == 2

    def test_ausbildungswoche_default(self):
        """
        Assert that ausbildungswoche_default returns the total count of all
        Nachweis objects plus one.
        """
        assert _models.ausbildungswoche_default() == 1
        NachweisFactory()
        assert _models.ausbildungswoche_default() == 2

    def test_jahr_default(self, year):
        """Assert that jahr_default returns the expected year."""
        assert _models.jahr_default() == year

    def test_kalenderwoche_default(self, week):
        """Assert that kalenderwoche_default returns the expected week."""
        assert _models.kalenderwoche_default() == week

    def test_datum_start_default(self, year, week):
        """Assert that datum_start_default returns the correct start date."""
        assert _models.datum_start_default() == str(date.fromisocalendar(year, week, 1))

    def test_datum_ende_default(self, year, week):
        """Assert that datum_ende_default returns the correct end date."""
        assert _models.datum_ende_default() == str(date.fromisocalendar(year, week, 5))


class TestAbteilungModel:
    """Test the Abteilung model."""

    def test_str(self):
        """Assert that the string representation is as expected."""
        assert str(_models.Abteilung(name="Testabteilung")) == "Testabteilung"
