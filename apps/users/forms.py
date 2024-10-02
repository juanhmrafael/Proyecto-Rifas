from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm as DjangoUserCreationForm,
    UserChangeForm as DjangoUserChangeForm
)
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.password_validation import validate_password

def style(fields):
    for field_name, field in fields.items():
        # Aplicar clases específicas según el tipo de widget
        if isinstance(field.widget, forms.Select):
            field.widget.attrs["class"] = ""

        elif isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = (
                "w-4 h-4 border border-gray-300 rounded bg-gray-50 focus:ring-3 focus:ring-pink-300 dark:bg-gray-600 dark:border-gray-500 dark:focus:ring-pink-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800"
            )

        elif isinstance(field.widget, forms.CheckboxSelectMultiple):
            field.widget.attrs["class"] = (
                "w-4 h-4 border border-gray-300 rounded bg-gray-50 focus:ring-3 focus:ring-pink-300 dark:bg-gray-600 dark:border-gray-500 dark:focus:ring-pink-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800"
            )

        elif isinstance(field.widget, forms.DateInput):
            field.widget.format = "%Y-%m-%d"  # Establece el formato de fecha


        elif isinstance(
            field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)
        ):
            field.widget.attrs["class"] = (
                "w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-500"
            )

        elif isinstance(field.widget, forms.FileInput):
            field.widget.attrs["class"] = (
                "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-white focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
            )


class UserCreateForm(DjangoUserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo electrónico")
    is_active = forms.BooleanField(required=False, initial=True, label="Activo")
    is_superuser = forms.BooleanField(
        required=False, initial=False, label="Superusuario"
    )
    profile_picture = forms.ImageField(required=False, label="Imagen de perfil")

    password1 = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña",
        validators=[validate_password],  # Usa validaciones predeterminadas de Django
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput, label="Confirmar contraseña"
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().select_related("content_type"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos del Usuario",
    )

    class Meta:
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "is_active",
            "is_superuser",
            "profile_picture",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self.fields)

        # Obtener content types para los modelos que quieres incluir
        user_content_type = ContentType.objects.get(model="useraccount")
        raffles_content_type = ContentType.objects.get(model="raffle")
        participant_content_type = ContentType.objects.get(model="participant")
        # Filtrar permisos que pertenecen al modelo 'User' y otros modelos deseados
        self.fields["user_permissions"].queryset = Permission.objects.filter(
            content_type__in=[
                user_content_type,
                raffles_content_type,
                participant_content_type,
            ]
        ).order_by("content_type__model", "name")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden")
        return cleaned_data

    def clean_user_permissions(self):
        permissions = self.cleaned_data.get("user_permissions")
        if permissions:
            return permissions
        return []


class UserUpdateForm(DjangoUserChangeForm):
    # Reutiliza los campos del formulario de creación, pero ajusta las contraseñas
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo electrónico")
    is_active = forms.BooleanField(required=False, initial=True, label="Activo")
    is_superuser = forms.BooleanField(
        required=False, initial=False, label="Superusuario"
    )
    profile_picture = forms.ImageField(required=False, label="Imagen de perfil")

    # Contraseñas no obligatorias en la edición
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        label="Nueva Contraseña (opcional)",
        required=False,  # No requerido en edición
        validators=[validate_password],  # Usa validaciones predeterminadas de Django
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirmar Nueva Contraseña (opcional)",
        required=False,  # No requerido en edición
    )

    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().select_related("content_type"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos del Usuario",
    )

    class Meta:
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "is_active",
            "is_superuser",
            "profile_picture",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self.fields)

        # Obtener content types para los modelos que quieres incluir
        user_content_type = ContentType.objects.get(model="useraccount")
        raffles_content_type = ContentType.objects.get(model="raffle")
        participant_content_type = ContentType.objects.get(model="participant")

        # Filtrar permisos que pertenecen al modelo 'User' y otros modelos deseados
        self.fields["user_permissions"].queryset = Permission.objects.filter(
            content_type__in=[
                user_content_type,
                raffles_content_type,
                participant_content_type,
            ]
        ).order_by("content_type__model", "name")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Validar si las contraseñas son iguales solo si el usuario las ingresó
        if password1 or password2:
            if password1 != password2:
                raise ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Solo establecer una nueva contraseña si el usuario ingresó una nueva
        password1 = self.cleaned_data.get("password1")
        if password1:
            user.set_password(password1)
        if commit:
            user.save()
        return user
