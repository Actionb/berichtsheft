from django.db import models


class AbteilungDummy(models.Model):
    """Dummy version of the Abteilung model for use in testing."""

    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Abteilung"
        verbose_name_plural = "Abteilungen"

    def __str__(self):
        return self.name


class NachweisDummy(models.Model):
    """Dummy version of the Nachweis model for use in testing."""

    nummer = models.PositiveSmallIntegerField(verbose_name="Nummer", null=False)
    abteilung = models.ForeignKey("AbteilungDummy", on_delete=models.SET_NULL, blank=True, null=True)

    fertig = models.BooleanField(verbose_name="Fertig geschrieben", default=False)
    unterschrieben = models.BooleanField(verbose_name="Unterschrieben?", default=False)

    class Meta:
        verbose_name = "Nachweis"
        verbose_name_plural = "Nachweise"

    def __str__(self):
        return f"Nachweis #{self.nummer}"
