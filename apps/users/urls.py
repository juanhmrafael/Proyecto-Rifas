from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = "users"
urlpatterns = [
    path(
        "profile/update/", views.CurrentUserUpdateView.as_view(), name="profile_update"
    ),
    path("users/", views.UserListView.as_view(), name="list"),
    path("users/<int:pk>/details/", views.UserDetailView.as_view(), name="detail"),
    path("user/create/", views.UserCreateView.as_view(), name="create"),
    path("user/<int:pk>/edit/", views.UserUpdateView.as_view(), name="edit"),
    path(
        "user/<int:pk>/delete/", views.UserDeleteView.as_view(), name="delete"
    ),  # Eliminar usuario
    path("login/", views.login_view, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
