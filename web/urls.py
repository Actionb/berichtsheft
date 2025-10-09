from django.urls import path

from web.views import NachweisEditView, NachweisListView, NachweisPrintView

urlpatterns = [
    path("add/", NachweisEditView.as_view(extra_context={"add": True}), name="nachweis_add"),
    path("<path:pk>/change/", NachweisEditView.as_view(extra_context={"add": False}), name="nachweis_change"),
    path("<path:pk>/print/", NachweisPrintView.as_view(), name="nachweis_print"),
    path("", NachweisListView.as_view(), name="nachweis_list"),
]
