from django.db.models.signals import post_migrate
from django.dispatch import receiver

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.apps import apps


@receiver(post_migrate)
def traducir_permisos(sender, **kwargs):
    # Diccionario de traducciones
    traducciones = {
        "Can add": "Puede agregar",
        "Can change": "Puede modificar",
        "Can delete": "Puede eliminar",
        "Can view": "Puede ver",
        # Agrega más traducciones según sea necesario
    }

    # Obtener todos los permisos
    permisos = Permission.objects.all()

    for permiso in permisos:
        nombre_original = permiso.name
        nombre_traducido = nombre_original

        # Verificar si el permiso necesita traducción
        for ingles, español in traducciones.items():
            if ingles in nombre_original:
                nombre_traducido = nombre_original.replace(ingles, español)
                break

        # Si se ha traducido, actualizar el permiso
        if nombre_traducido != nombre_original:
            permiso.name = nombre_traducido
            permiso.save()
            print(f"Permiso traducido: {nombre_original} -> {nombre_traducido}")
