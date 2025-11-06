from datetime import date, datetime

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    User model for the application.

    (In case we need to add custom fields or methods in the future)
    """


def _get_current_year():
    """Gebe das aktuelle Jahr zurück."""
    return datetime.now().year


def _get_current_week():
    """Gebe die aktuelle Kalenderwoche zurück."""
    return datetime.now().isocalendar()[1]


def ausbildungswoche_default():
    """Erzeuge einen Standardwert für das Feld 'ausbildungswoche'."""
    return Nachweis.objects.count() + 1


def jahr_default():
    """Erzeuge einen Standardwert für das Feld 'jahr'."""
    return _get_current_year()


def datum_start_default():
    """Erzeuge einen Standardwert für das Feld 'datum_start'."""
    return str(date.fromisocalendar(_get_current_year(), _get_current_week(), 1))


def datum_ende_default():
    """Erzeuge einen Standardwert für das Feld 'datum_ende'."""
    return str(date.fromisocalendar(_get_current_year(), _get_current_week(), 5))


def kalenderwoche_default():
    """Erzeuge einen Standardwert für das Feld 'kalenderwoche'."""
    return _get_current_week()


def nummer_default():
    """Erzeuge einen Standardwert für das Feld 'nummer'."""
    return Nachweis.objects.count() + 1


class Nachweis(models.Model):
    """Die verschiedenen Nachweise des Benutzers."""

    betrieb = models.TextField(verbose_name="Betriebliche Tätigkeiten")
    schule = models.TextField(verbose_name="Berufsschule")

    nummer = models.PositiveSmallIntegerField(verbose_name="Nummer", null=False, editable=False, default=nummer_default)
    ausbildungswoche = models.PositiveSmallIntegerField(
        verbose_name="Ausbildungswoche", blank=False, null=False, default=ausbildungswoche_default
    )
    jahr = models.PositiveSmallIntegerField(verbose_name="Jahr", blank=False, null=False, default=jahr_default)
    kalenderwoche = models.PositiveSmallIntegerField(
        verbose_name="Kalenderwoche", blank=False, null=False, default=kalenderwoche_default
    )
    datum_start = models.DateField(verbose_name="Vom", blank=False, null=False, default=datum_start_default)
    datum_ende = models.DateField(verbose_name="Bis", blank=False, null=False, default=datum_ende_default)
    abteilung = models.ForeignKey("Abteilung", on_delete=models.PROTECT)

    fertig = models.BooleanField(verbose_name="Fertig geschrieben", default=False)
    # TODO: eingereicht_bei: ForeignKey -> Person?
    eingereicht_bei = models.CharField(verbose_name="Eingereicht bei", max_length=100, blank=True)
    unterschrieben = models.BooleanField(verbose_name="Unterschrieben?", default=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE, editable=False, verbose_name="Benutzer")

    class Meta:
        verbose_name = "Nachweis"
        verbose_name_plural = "Nachweise"
        ordering = ["ausbildungswoche"]

    def __str__(self):
        return f"Nachweis #{self.nummer}"


class Abteilung(models.Model):
    name = models.CharField(verbose_name="Abteilungsname", blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Abteilung"
        verbose_name_plural = "Abteilungen"
        ordering = ["name"]
