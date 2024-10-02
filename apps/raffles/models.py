from django.db import models
from datetime import datetime
from tinymce.models import HTMLField
import random
import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


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


# Modelo de la Rifa
class Raffle(models.Model):
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    STATUS_CHOICES = [
        (IN_PROGRESS, "En progreso"),
        (FINISHED, "Finalizada"),
    ]
    # Opciones de tipo de moneda
    VEF = "VEF"
    USD = "USD"
    CURRENCY_CHOICES = [
        (VEF, "Bolívares (VEF)"),
        (USD, "Dólares (USD)"),
    ]

    title = models.CharField(max_length=255, verbose_name="Título de la Rifa")
    raffle_date = models.DateField(verbose_name="Fecha de la Rifa")
    prizes = HTMLField()
    ticket_cost = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Costo por Boleto"
    )
    currency_type = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=VEF,  # Valor predeterminado si no se especifica
        verbose_name="Tipo de Moneda",
    )
    min_tickets = models.IntegerField(verbose_name="Mínimo de Boletos para Participar")
    available_tickets = models.IntegerField(verbose_name="Boletos Disponibles")
    winner = HTMLField(blank=True, null=True, verbose_name="Ganadores de la Rifa")
    payment_info = HTMLField()

    # Nuevo campo para el estado de la rifa
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=IN_PROGRESS,
        verbose_name="Estado de la Rifa",
    )
    date_creation = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.raffle_date}"

    def finalize_raffle(self):
        """Marcar la rifa como finalizada"""
        self.status = self.FINISHED
        self.save()

    def is_finished(self):
        """Verificar si la rifa ha finalizado"""
        return self.status == self.FINISHED

    def delete(self, *args, **kwargs):
        # Eliminar todas las imágenes de los premios manualmente
        for prize_image in self.prize_images.all():
            prize_image.delete()  # Esto llamará al método delete de RafflePrizeImage

        # Eliminar todas las capturas de pago de los participantes
        for participant in self.participants.all():
            if participant.payment_receipt:
                participant.payment_receipt.delete()  # Asegúrate de que `payment_capture` sea el campo correcto

        # Llamar al método delete original de Django
        super().delete(*args, **kwargs)


    def select_winners(self, num_winners):
        """Seleccionar ganadores aleatoriamente y devolver sus IDs junto con el número con el que ganaron,
        asegurando que un participante con la misma cédula no gane más de una vez.
        """
        # Recopilar todos los participantes confirmados y sus números asignados
        participants = self.participants.filter(status="confirmed")

        # Crear un diccionario para almacenar los números y los participantes
        participant_dict = {}
        for participant in participants:
            numbers = participant.assigned_numbers.split(",")
            for number in numbers:
                if number not in participant_dict:
                    participant_dict[number] = participant

        # Lista para almacenar los ganadores
        winners = []
        excluded_identity_cards = set()  # Cédulas ya ganadoras

        available_numbers = list(participant_dict.keys())

        while len(winners) < num_winners and available_numbers:
            # Elegir un número de boleto ganador aleatorio
            winning_number = random.choice(available_numbers)
            winning_participant = participant_dict[winning_number]

            # Evitar que una persona con la misma cédula gane más de una vez
            if winning_participant.identity_card not in excluded_identity_cards:
                winners.append(
                    (winning_participant, winning_number)
                )  # Almacenar ganador y número

                # Excluir la cédula ganadora
                excluded_identity_cards.add(winning_participant.identity_card)

                # Eliminar todos los números de ese participante de la lista de disponibles
                numbers_to_remove = [
                    num
                    for num in participant_dict.keys()
                    if participant_dict[num] == winning_participant
                ]
                for number in numbers_to_remove:
                    available_numbers.remove(number)

        # Formatear la salida HTML para los ganadores
        winner_html = "<br>".join(
            [
                f"Ganador {i + 1}: {winner[0].full_name}, Cédula: {winner[0].identity_card}, Número: {winner[1]}"
                for i, winner in enumerate(winners)
            ]
        )
        self.winner = winner_html

        # Marcar la rifa como finalizada
        self.save()

        return [
            {"winner_id": winner[0].id, "winning_number": winner[1]} for winner in winners
        ]

    class Meta:
        db_table = "raffle"  # Nombre con el que se guarda en la base de datos
        verbose_name = "Rifa"  # Nombre en singular
        verbose_name_plural = "Rifas"  # Nombre en plural


class RafflePrizeImage(models.Model, ImageManagementMixin):
    raffle = models.ForeignKey(
        "Raffle", related_name="prize_images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="prizes/")

    # Configuración para los campos de imagen
    image_fields = {
        "image": {
            "max_size": 5,  # Tamaño máximo en MB
            "dimensions": (1280, 720),  # Dimensiones de optimización
            "quality": 100,  # Calidad de compresión JPEG
        }
    }

    def __str__(self):
        return f"Premio de {self.raffle.title} - {self.description or 'Imagen'}"

    class Meta:
        db_table = "prize_image"  # Nombre con el que se guarda en la base de datos
        verbose_name = "Imagen de premio"  # Nombre en singular
        verbose_name_plural = "Imagenes de los premios"  # Nombre en plural

    def delete(self, *args, **kwargs):
        # Procesar eliminación de imágenes usando el mixin
        ImageManagementMixin.delete(self, *args, **kwargs)
        # Llamar al delete del modelo de Django
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Procesar imágenes usando el mixin
        ImageManagementMixin.save(self, *args, **kwargs)
        # Llamar al save del modelo de Django
        super().save(*args, **kwargs)


def payments_picture_path(instance, filename):
    # Obtener la extensión del archivo original
    ext = os.path.splitext(filename)[1]
    referencia = instance.payment_reference
    # Generar el nuevo nombre de archivo
    timestamp = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    filename = f"{referencia}_{timestamp}{ext}"

    # Retornar la ruta completa
    return os.path.join("payments/", filename)


# Modelo para los Participantes de la Rifa
class Participant(models.Model, ImageManagementMixin):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    STATUS_CHOICES = [
        (PENDING, "Pendiente"),
        (CONFIRMED, "Confirmado"),
    ]

    raffle = models.ForeignKey(
        Raffle, on_delete=models.CASCADE, related_name="participants"
    )
    full_name = models.CharField(max_length=100, verbose_name="Nombre Completo")
    identity_card = models.CharField(max_length=15, verbose_name="Cédula de Identidad")
    email = models.EmailField(verbose_name="Correo Electrónico")
    phone_number = models.CharField(max_length=15, verbose_name="Número de Teléfono")
    tickets_purchased = models.IntegerField(verbose_name="Número de Boletos Comprados")

    # Datos de Pago
    assigned_numbers = models.TextField(
        verbose_name="Números Asignados", blank=True, null=True
    )
    payment_date = models.DateField(default=datetime.now, verbose_name="Fecha del Pago")
    payment_reference = models.CharField(
        max_length=15, verbose_name="Referencia del Pago", unique=True
    )
    payment_receipt = models.ImageField(
        upload_to=payments_picture_path,
        verbose_name="Captura del Pago",
    )

    # Estado de confirmación del pago
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name="Estado del Pago",
    )

    # Configuración para los campos de imagen
    image_fields = {
        "payment_receipt": {
            "max_size": 5,  # Tamaño máximo en MB
            "dimensions": (1280, 720),  # Dimensiones de optimización
            "quality": 100,  # Calidad de compresión JPEG
        }
    }

    def __str__(self):
        return f"{self.full_name} - {self.raffle.title}"

    def confirm_payment(self):
        """Confirmar el pago y asignar números de boletos aleatorios"""
        self.status = self.CONFIRMED
        self.assigned_numbers = self.__assign_random_ticket_numbers()
        self.save()

    def __assign_random_ticket_numbers(self):
        """Asignar números de boletos aleatorios y únicos"""
        # Definir un rango grande para los números de boletos, por ejemplo, entre 1000 y 9999
        ticket_numbers = []
        all_assigned_numbers = set(
            number
            for participant in self.raffle.participants.filter(status=self.CONFIRMED)
            for number in participant.assigned_numbers.split(",")
            if participant.assigned_numbers
        )

        while len(ticket_numbers) < self.tickets_purchased:
            random_number = random.randint(1000, 9999 + self.raffle.available_tickets)
            if str(random_number) not in all_assigned_numbers:
                ticket_numbers.append(str(random_number))
                all_assigned_numbers.add(str(random_number))

        return ",".join(ticket_numbers)

    class Meta:
        db_table = "participant"  # Nombre con el que se guarda en la base de datos
        verbose_name = "Participante"  # Nombre en singular
        verbose_name_plural = "Participantes"  # Nombre en plural

    def delete(self, *args, **kwargs):
        # Procesar eliminación de imágenes usando el mixin
        ImageManagementMixin.delete(self, *args, **kwargs)
        # Llamar al delete del modelo de Django
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Procesar imágenes usando el mixin
        ImageManagementMixin.save(self, *args, **kwargs)
        # Llamar al save del modelo de Django
        super().save(*args, **kwargs)
