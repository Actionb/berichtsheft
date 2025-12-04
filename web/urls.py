from django.contrib.auth.views import logout_then_login
from django.urls import path

from web import views

urlpatterns = [
    # Auth
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", logout_then_login, name="logout"),
    path("password_change/", views.PasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("profile/", views.UserProfileView.as_view(), name="user_profile"),
    # Model views
    path("nachweis/add/", views.NachweisEditView.as_view(extra_context={"add": True}), name="nachweis_add"),
    path(
        "nachweis/<int:pk>/change/",
        views.NachweisEditView.as_view(extra_context={"add": False}),
        name="nachweis_change",
    ),
    path("nachweis/<int:pk>/delete/", views.NachweisDeleteView.as_view(), name="nachweis_delete"),
    path("nachweis/<int:pk>/print/", views.NachweisPrintView.as_view(), name="nachweis_print"),
    path("nachweis/", views.NachweisListView.as_view(), name="nachweis_list"),
    path("abteilung/add/", views.AbteilungEditView.as_view(extra_context={"add": True}), name="abteilung_add"),
    path(
        "abteilung/<int:pk>/change/",
        views.AbteilungEditView.as_view(extra_context={"add": False}),
        name="abteilung_change",
    ),
    path("abteilung/<int:pk>/delete/", views.AbteilungDeleteView.as_view(), name="abteilung_delete"),
    path("abteilung/", views.AbteilungListView.as_view(), name="abteilung_list"),
    # Autocomplete
    path("abteilung_ac/", views.AbteilungAutocompleteView.as_view(), name="abteilung_ac"),
    # Other
    path("preview/", views.print_preview, name="print_preview"),
    path("trash/", views.PapierkorbView.as_view(), name="trash"),
    path("<str:model_name>/<int:pk>/restore/", views.restore_object, name="restore_object"),
    path("<str:model_name>/<int:pk>/hard_delete/", views.HardDeleteView.as_view(), name="hard_delete"),
    path("trash/empty/", views.empty_trash, name="empty_trash"),
]
