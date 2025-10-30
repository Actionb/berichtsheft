from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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


admin.site.register(_models.User, UserAdmin)
