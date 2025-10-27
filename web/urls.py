from django.urls import path

from web import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("nachweis/add/", views.NachweisEditView.as_view(extra_context={"add": True}), name="nachweis_add"),
    path(
        "nachweis/<path:pk>/change/",
        views.NachweisEditView.as_view(extra_context={"add": False}),
        name="nachweis_change",
    ),
    path("nachweis/<path:pk>/print/", views.NachweisPrintView.as_view(), name="nachweis_print"),
    path("nachweis/", views.NachweisListView.as_view(), name="nachweis_list"),
    path("abteilung/add/", views.AbteilungEditView.as_view(extra_context={"add": True}), name="abteilung_add"),
    path(
        "abteilung/<path:pk>/change/",
        views.AbteilungEditView.as_view(extra_context={"add": False}),
        name="abteilung_change",
    ),
    path("abteilung_ac/", views.AutocompleteView.as_view(), name="abteilung_ac"),
    path("preview/", views.print_preview, name="print_preview"),
]
