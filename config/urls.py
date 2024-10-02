from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", include("home.urls", namespace="home")),
    path("", include("users.urls", namespace="users")),
    path("", include("raffles.urls", namespace="raffles")),
    path("tinymce/", include("tinymce.urls")),
]

# Añadir configuración para servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
