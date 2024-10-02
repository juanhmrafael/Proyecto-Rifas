from django.urls import path
from . import views

app_name = "home"
urlpatterns = [
    path("", views.RaffleListView.as_view(), name="index"),
    path("check_reference", views.comprobar, name="check_reference"),
    path(
        "raffle/<int:pk>/participant/compete/",
        views.ParticipantCreateView.as_view(),
        name="raffle",
    ),
]
