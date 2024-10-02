from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    
    def ready(self):
        import users.signals  # Importa la señal aquí para que se registre automáticamente
