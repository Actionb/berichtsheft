from django.db import models
from datetime import datetime, date


def _get_current_year():
    return datetime.now().year


def _get_current_week():
    return datetime.now().isocalendar()[1]


def ausbildungswoche_default():
    """Erzeuge einen Standardwert für das Feld 'ausbildungswoche'."""
    if not Nachweis.objects.exists():
        return 1
    return Nachweis.objects.last().ausbildungswoche + 1


def jahr_default():
    """Erzeuge einen Standardwert für das Feld 'jahr'."""
    return _get_current_year


def datum_start_default():
    """Erzeuge einen Standardwert für das Feld 'datum_start'."""
    return str(date.fromisocalendar(_get_current_year(), _get_current_week(), 1))


def datum_end_default():
    """Erzeuge einen Standardwert für das Feld 'datum_end'."""
    return str(date.fromisocalendar(_get_current_year(), _get_current_week(), 5))


def kalenderwoche_default():
    """Erzeuge einen Standardwert für das Feld 'kalenderwoche'."""
    return _get_current_week()


class Nachweis(models.Model):
    """Die verschiedenen Nachweise des Benutzers."""

    betrieb = models.TextField(verbose_name="Betriebliche Tätigkeiten")
    schule = models.TextField(verbose_name="Berufsschule")

    ausbildungswoche = models.PositiveSmallIntegerField(
        verbose_name="Ausbildungswoche", blank=False, null=False, default=ausbildungswoche_default
    )
    jahr = models.PositiveSmallIntegerField(verbose_name="Jahr", blank=False, null=False)
    kalenderwoche = models.PositiveSmallIntegerField(
        verbose_name="Kalenderwoche", blank=False, null=False, default=kalenderwoche_default
    )
    datum_start = models.DateField(verbose_name="Vom", blank=False, null=False, default=datum_start_default)
    datum_end = models.DateField(verbose_name="Bis", blank=False, null=False, default=datum_end_default)
    abteilung = models.ForeignKey("Abteilung", on_delete=models.PROTECT)

    fertig = models.BooleanField(verbose_name="Fertig geschrieben", default=False)
    # TODO: eingereicht_bei: ForeignKey -> Person?
    eingereicht_bei = models.CharField(verbose_name="Eingereicht bei", max_length=100, blank=False)
    unterschrieben = models.BooleanField(verbose_name="Unterschrieben?", default=False)

    class Meta:
        verbose_name = "Nachweis"
        verbose_name_plural = "Nachweise"

    def __str__(self):
        return f"Nachweis #{self.ausbildungswoche}"


class Abteilung(models.Model):
    name = models.CharField(verbose_name="Abteilungsname", blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Abteilung"
        verbose_name_plural = "Abteilungen"
