# models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import os
from datetime import datetime
import re
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email debe ser proporcionado")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


def sanitize_filename(filename):
    # Eliminar caracteres no alfanuméricos (excepto puntos, guiones y guiones bajos)
    return re.sub(r"[^\w\-_\.]", "", filename)


class ImageManagementMixin:
    def save(self, *args, **kwargs):
        """
        Guarda la instancia y maneja la optimización y eliminación de imágenes.
        """
        # Verifica si la instancia es nueva o está siendo editada
        is_new_instance = not self.pk

        for field_name, settings in self.image_fields.items():
            image_field = getattr(self, field_name, None)

            if is_new_instance and image_field:
                # Nueva instancia con imagen, optimiza la imagen
                # print(f"Procesando nueva imagen para {field_name}")
                self._optimize_image(
                    image_field, settings["dimensions"], settings["quality"]
                )

            elif not is_new_instance:
                # Instancia existente, verifica si la imagen ha cambiado
                if self._image_changed(field_name):
                    # print(f"Imagen {field_name} ha cambiado: True")

                    old_instance = self.__class__.objects.get(pk=self.pk)
                    old_image = getattr(old_instance, field_name, None)

                    if old_image:
                        # print(f"Eliminando imagen previa para {field_name}")
                        self._delete_image(old_image)

                    if image_field:
                        # Optimiza la nueva imagen
                        # print(f"Optimizando nueva imagen para {field_name}")
                        self._optimize_image(
                            image_field, settings["dimensions"], settings["quality"]
                        )
                # else:
                #     # Imagen no ha cambiado
                #     print(
                #         f"Imagen {field_name} no ha cambiado, no se realiza ninguna acción."
                #     )

            elif image_field is None and not is_new_instance:
                # Campo vacío en una instancia existente
                old_instance = self.__class__.objects.get(pk=self.pk)
                old_image = getattr(old_instance, field_name, None)

                if old_image:
                    # print(
                    #     f"Eliminando imagen previa para {field_name} porque el campo está vacío"
                    # )
                    self._delete_image(old_image)

        # No llamamos a super().save() aquí

    def delete(self, *args, **kwargs):
        """
        Elimina las imágenes asociadas antes de eliminar la instancia.
        """
        for field_name in self.image_fields:
            image_field = getattr(self, field_name, None)
            if image_field:
                # print(f"Eliminando imagen para el campo {field_name}")
                self._delete_image(image_field)

    def _image_changed(self, field_name):
        """
        Comprueba si la imagen ha cambiado en una instancia existente.
        """
        if not self.pk:
            return False  # Si el objeto no está guardado, no se ha cambiado la imagen
        old_instance = self.__class__.objects.get(pk=self.pk)
        old_image = getattr(old_instance, field_name)
        new_image = getattr(self, field_name)
        return old_image != new_image

    def _optimize_image(self, image, dimensions, quality):
        """
        Función para optimizar la imagen.
        """
        img = Image.open(image)
        img.thumbnail(dimensions, Image.LANCZOS)

        if img.mode != "RGB":
            img = img.convert("RGB")

        output = BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)

        image.save(image.name, ContentFile(output.getvalue()), save=False)

    def _delete_image(self, image):
        """
        Elimina la imagen si existe en el sistema de archivos.
        """
        if image and os.path.isfile(image.path):
            # print(f"Eliminando archivo de imagen: {image.path}")
            os.remove(image.path)


def user_profile_picture_path(instance, filename):
    # Obtener la extensión del archivo original
    ext = os.path.splitext(filename)[1]

    # Sanitizar el correo electrónico para usarlo como parte del nombre del archivo
    safe_email = sanitize_filename(instance.email.split("@")[0])

    # Generar el nuevo nombre de archivo
    timestamp = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    filename = f"{safe_email}_{timestamp}{ext}"

    # Retornar la ruta completa
    return os.path.join("profile_pictures", filename)


class UserAccount(AbstractUser, ImageManagementMixin):
    username = None  # Eliminamos el campo de username
    email = models.EmailField(
        unique=True, verbose_name="correo electrónico"
    )  # Hacemos que el email sea único
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path,
        blank=True,
        null=True,
        verbose_name="imagen de perfil",
    )

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="user_set",  # Evitar colisión con auth.User.groups
        blank=True,
        help_text="Los grupos a los que pertenece este usuario.",
        verbose_name="grupos",
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="user_set",  # Evitar colisión con auth.User.user_permissions
        blank=True,
        help_text="Permisos específicos para este usuario.",
        verbose_name="permisos de usuario",
    )

    USERNAME_FIELD = "email"  # Indicamos que el campo de identificación es el email
    REQUIRED_FIELDS = []  # No se requiere ningún otro campo

    objects = UserManager()

    # Configuración para los campos de imagen
    image_fields = {
        "profile_picture": {
            "max_size": 5,  # Tamaño máximo en MB
            "dimensions": (300, 300),  # Dimensiones de optimización
            "quality": 100,  # Calidad de compresión JPEG
        }
    }

    class Meta:
        db_table = "user_account"  # Nombre con el que se guarda en la base de datos
        verbose_name = "usuario"  # Nombre en singular
        verbose_name_plural = "usuarios"  # Nombre en plural
        permissions = [
            (
                "change_permissions_user",
                "Puede gestionar permisos de usuario",
            ),
        ]
    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Procesar imágenes usando el mixin
        ImageManagementMixin.save(self, *args, **kwargs)
        # Llamar al save del modelo de Django
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Procesar eliminación de imágenes usando el mixin
        ImageManagementMixin.delete(self, *args, **kwargs)
        # Llamar al delete del modelo de Django
        super().delete(*args, **kwargs)
