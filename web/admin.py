from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse_lazy

from web import models as _models

admin.site.site_url = reverse_lazy("home")


class EingereichtFilter(admin.AllValuesFieldListFilter):
    def choices(self, changelist):
        # Add an option to filter for Nachweise that have not been submitted to
        # anybody.
        display = "Nicht eingereicht"
        queryset = changelist.get_queryset(self.request, exclude_parameters=self.expected_parameters())
        if changelist.add_facets:
            display = f"{display} ({queryset.filter(eingereicht_bei='').count()})"
        yield {
            "selected": bool(self.lookup_val == ""),
            "query_string": changelist.get_query_string({self.lookup_kwarg: ""}),
            "display": display,
        }
        for choice in super().choices(changelist):
            yield choice


@admin.register(_models.Nachweis)
class NachweisAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "nummer",
        "jahr",
        "ausbildungswoche",
        "datum_start",
        "datum_ende",
        "abteilung",
        "fertig",
        "eingereicht_bei",
        "unterschrieben",
    ]
    list_display_links = ["nummer"]
    list_editable = ["fertig", "unterschrieben"]
    list_filter = ["user", "fertig", ("eingereicht_bei", EingereichtFilter), "unterschrieben"]
    exclude = ["deleted_at", "restored_at", "transaction_id"]
    autocomplete_fields = ["abteilung"]


@admin.register(_models.Abteilung)
class AbteilungAdmin(admin.ModelAdmin):
    search_fields = ["name"]


admin.site.register(_models.User, UserAdmin)
