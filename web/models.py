from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_softdelete.models import SoftDeleteModel


class User(AbstractUser):
    """
    User model for the application.

    (In case we need to add custom fields or methods in the future)
    """


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile", unique=True)
    start_date = models.DateField(
        verbose_name="Startdatum",
        blank=True,
        null=True,
        help_text="Startdatum der Ausbildung. Wird benötigt für die Errechnung von Datumsangaben der Nachweise.",
    )

    class Meta:
        verbose_name = "Benutzerprofil"
        verbose_name_plural = "Benutzerprofile"


class Nachweis(SoftDeleteModel):
    """Die verschiedenen Nachweise der Benutzer."""

    betrieb = models.TextField(verbose_name="Betriebliche Tätigkeiten")
    schule = models.TextField(verbose_name="Berufsschule")

    nummer = models.PositiveSmallIntegerField(verbose_name="Nummer", null=False)
    ausbildungswoche = models.PositiveSmallIntegerField(verbose_name="Ausbildungswoche", blank=False, null=False)
    jahr = models.PositiveSmallIntegerField(verbose_name="Jahr", blank=False, null=False)
    kalenderwoche = models.PositiveSmallIntegerField(verbose_name="Kalenderwoche", blank=False, null=False)
    datum_start = models.DateField(verbose_name="Vom", blank=False, null=False)
    datum_ende = models.DateField(verbose_name="Bis", blank=False, null=False)
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


class Abteilung(SoftDeleteModel):
    name = models.CharField(verbose_name="Abteilungsname", blank=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE, editable=False, verbose_name="Benutzer")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Abteilung"
        verbose_name_plural = "Abteilungen"
        ordering = ["name"]
