from django.contrib import admin

from web import models as _models


@admin.register(_models.Nachweis)
class NachweisAdmin(admin.ModelAdmin):
    list_display = [
        "jahr",
        "ausbildungswoche",
        "datum_start",
        "datum_ende",
        "abteilung",
        "fertig",
        "eingereicht_bei",
        "unterschrieben",
    ]
    autocomplete_fields = ["abteilung"]


@admin.register(_models.Abteilung)
class AbteilungAdmin(admin.ModelAdmin):
    search_fields = ["name"]
