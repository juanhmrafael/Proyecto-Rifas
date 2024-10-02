from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class):
    """
    Agrega una clase CSS a un campo de formulario.
    """
    return field.as_widget(attrs={"class": css_class})


@register.filter
def get_last_param(value):
    # Dividir la cadena por '|' y tomar el último elemento
    return value.split("|")[-1].strip()

@register.filter
def multiply(value, arg):
    return value * arg
