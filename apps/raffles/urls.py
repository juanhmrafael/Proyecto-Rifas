from django.urls import path
from . import views


app_name = "raffles"
urlpatterns = [
    path("raffles/", views.RaffleListView.as_view(), name="list"),
    path("raffle/create", views.RaffleCreateView.as_view(), name="create"),
    path("raffle/<int:pk>/", views.RaffleDetailView.as_view(), name="detail"),
    path("raffle/<int:pk>/edit/", views.RaffleUpdateView.as_view(), name="edit"),
    path("raffle/<int:pk>/delete/", views.RaffleDeleteView.as_view(), name="delete"),
    path(
        "raffle/<int:pk>/participants",
        views.ParticipantListView.as_view(),
        name="list_participant",
    ),
    path(
        "raffle/<int:id_raffle>/participant/<int:id_participant>",
        views.confirm_payment,
        name="confirm_participant",
    ),
    path(
        "raffle/<int:raffle_id>/participant/<int:pk>/",
        views.ParticipantDetailView.as_view(),
        name="detail_participant",
    ),
    path(
        "raffle/<int:pk>/participant/add/",
        views.ParticipantCreateView.as_view(),
        name="add_participant",
    ),
    path(
        "raffle/<int:raffle_id>/participant/<int:pk>/edit/",
        views.ParticipantUpdateView.as_view(),
        name="edit_participant",
    ),
    path(
        "raffle/<int:raffle_id>/participant/<int:pk>/delete/",
        views.ParticipantDeleteView.as_view(),
        name="delete_participant",
    ),
]
