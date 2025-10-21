from django.urls import path

from web.views import (
    AbteilungEditView,
    AutocompleteView,
    NachweisEditView,
    NachweisListView,
    NachweisPrintView,
    print_preview,
)

urlpatterns = [
    path("nachweis/add/", NachweisEditView.as_view(extra_context={"add": True}), name="nachweis_add"),
    path("nachweis/<path:pk>/change/", NachweisEditView.as_view(extra_context={"add": False}), name="nachweis_change"),
    path("nachweis/<path:pk>/print/", NachweisPrintView.as_view(), name="nachweis_print"),
    path("nachweis/", NachweisListView.as_view(), name="nachweis_list"),
    path("abteilung/add/", AbteilungEditView.as_view(extra_context={"add": True}), name="abteilung_add"),
    path(
        "abteilung/<path:pk>/change/", AbteilungEditView.as_view(extra_context={"add": False}), name="abteilung_change"
    ),
    path("abteilung_ac/", AutocompleteView.as_view(), name="abteilung_ac"),
    path("preview/", print_preview, name="print_preview"),
]
