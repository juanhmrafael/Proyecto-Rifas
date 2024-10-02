from raffles.models import Participant
from django import forms
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
            "payment_date",
            "payment_reference",
            "payment_receipt",
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
