from django import forms
from .models import Raffle, RafflePrizeImage, Participant
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

def style(fields):
    for field_name, field in fields.items():
        # Aplicar clases específicas según el tipo de widget
        if isinstance(field.widget, forms.Select):
            field.widget.attrs["class"] = (
                "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-pink-500 focus:border-pink-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-pink-500 dark:focus:border-pink-500"
            )

        elif isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = (
                "w-4 h-4 border border-gray-300 rounded bg-gray-50 focus:ring-3 focus:ring-pink-300 dark:bg-gray-600 dark:border-gray-500 dark:focus:ring-pink-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800"
            )

        elif isinstance(field.widget, forms.CheckboxSelectMultiple):
            field.widget.attrs["class"] = (
                "w-4 h-4 border border-gray-300 rounded bg-gray-50 focus:ring-3 focus:ring-pink-300 dark:bg-gray-600 dark:border-gray-500 dark:focus:ring-pink-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800"
            )

        elif isinstance(field.widget, forms.DateInput):
            field.widget.format = "%d/%m/%Y"  # Establece el formato de fecha

        elif isinstance(field.widget, forms.NumberInput):
            field.widget.attrs["class"] = (
                "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 dark:text-white focus:border-pink-500 focus:ring-2 focus:ring-pink-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
            )

        elif isinstance(
            field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)
        ):
            field.widget.attrs["class"] = (
                "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 dark:text-white focus:border-pink-500 focus:ring-2 focus:ring-pink-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
            )

        elif isinstance(field.widget, forms.FileInput):
            field.widget.attrs["class"] = (
                "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-white focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
            )


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            "full_name",
            "identity_card",
            "email",
            "phone_number",
            "tickets_purchased",
            "payment_reference",
            "payment_receipt",
            "payment_date",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        self.raffle = kwargs.pop("raffle", None)
        super().__init__(*args, **kwargs)
        style(self.fields)

    def clean_tickets_purchased(self):
        tickets_purchased = self.cleaned_data["tickets_purchased"]
        if tickets_purchased < self.raffle.min_tickets:
            raise forms.ValidationError(
                f"Debes comprar al menos {self.raffle.min_tickets} boletos."
            )
        return tickets_purchased

    def clean_payment_reference(self):
        payment_reference = self.cleaned_data.get("payment_reference")

        # Verifica que la referencia tenga exactamente 9 dígitos
        if not payment_reference.isdigit():
            raise ValidationError(
                "La referencia de pago debe ser completamente númerica."
            )

        if len(payment_reference) != 9:
            raise ValidationError(
                "La referencia de pago debe tener exactamente 9 dígitos."
            )

        return payment_reference


class RaffleForm(forms.ModelForm):
    num_winners = forms.IntegerField(
        label="Número de Ganadores",
        min_value=1,  # Validación para asegurar que sea mayor o igual que 1
        widget=forms.NumberInput(attrs={"min": "1"}),
        required=False,  # Es opcional hasta que la rifa esté finalizada
        help_text="Especifique cuántos ganadores deseas seleccionar aleatoriamente.",
    )

    class Meta:
        model = Raffle
        fields = [
            "title",
            "raffle_date",
            "prizes",
            "ticket_cost",
            "currency_type",
            "min_tickets",
            "available_tickets",
            "winner",
            "payment_info",
            "status",
            "num_winners",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self.fields)
        self.fields["currency_type"].widget.attrs.update(
            {
                "class": "flex-shrink-0 z-10 inline-flex items-center py-2.5 px-4 text-sm font-medium text-center text-gray-900 bg-gray-100 border border-gray-300 rounded-e-lg hover:bg-gray-200 focus:ring-4 focus:outline-none focus:ring-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600 dark:focus:ring-gray-700 dark:text-white dark:border-gray-600"
            }
        )
        self.fields[
            "payment_info"
        ].initial = """\
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Datos del Beneficiario</h3>
            <p class="text-sm text-gray-900 dark:text-white">
                Móvil: <strong class="font-semibold">Teléfono</strong>
            </p>
            <p class="text-sm text-gray-900 dark:text-white">
                C.I.: <strong class="font-semibold">V-Cédula</strong>
            </p>
            <p class="text-sm text-gray-900 dark:text-white">
                Banco: <strong class="font-semibold">Banco (Código de banco)</strong>
            </p>
            <p class="text-sm text-gray-900 dark:text-white">
                Costo por boleto: <strong class="font-semibold">Monto Bs ó $ (Si es $ colocar aquí la tasa de referencia, paralelo o central)</strong>
            </p>
        """

        self.fields[
            "prizes"
        ].initial = """\
            <li class="flex items-center">
                <span class="text-lg mr-2">🥇</span> Premio 1
            </li>
            <li class="flex items-center">
                <span class="text-lg mr-2">🥈</span> Premio 2
            </li>
            <li class="flex items-center">
                <span class="text-lg mr-2">🥉</span> Premio 3
            </li>
        """

    def clean(self):
        cleaned_data = super().clean()
        num_winners = cleaned_data.get("num_winners")

        # Si el campo está vacío o es None, establecemos explícitamente num_winners a None
        if num_winners == "" or num_winners is None:
            cleaned_data["num_winners"] = None

        return cleaned_data


# Crear un formset para RaffleImage
RaffleImageFormSet = inlineformset_factory(
    Raffle, RafflePrizeImage, fields=("image", ), extra=1, can_delete=True
)
