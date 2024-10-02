from django.shortcuts import render
from raffles.models import Raffle, Participant
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import ParticipantForm
from raffles.models import Participant, Raffle
from django.utils import timezone

class ParticipantCreateView(CreateView):
    model = Participant
    form_class = ParticipantForm
    template_name = "home/participant_form.html"
    success_url = reverse_lazy("home:index")

    def dispatch(self, request, *args, **kwargs):
        self.raffle = get_object_or_404(Raffle, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["raffle"] = self.raffle  # Pasar la rifa al formulario para validar
        return kwargs

    def form_valid(self, form):
        participant = form.save(commit=False)
        participant.raffle = self.raffle
        participant.status = Participant.PENDING  # Estado predeterminado
        participant.save()

        self.raffle.save()

        messages.success(
            self.request,
            "¡Felicidades por tu compra! 🎉 Gracias por participar en nuestra rifa. Esté atento a nuestra página (Comprobar Pago), donde podrá verificar el estado de su compra en las próximas 24 horas. Recuerde que al adquirir más boletos, aumenta sus posibilidades de ganar. ¡Buena suerte! 🍀",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["raffle"] = self.raffle

        # Si la rifa ha finalizado, redirigimos a la vista de resumen
        if self.raffle.is_finished() or self.raffle.raffle_date < timezone.now().date():
            context["summary"] = True
            # Agregar datos del resumen (ejemplo: ganadores)
            context["winners"] = (
                self.raffle.winner
                if self.raffle.winner
                else "No se han asignado ganadores aún."
            )
        else:
            context["summary"] = False

        return context


class RaffleListView(ListView):
    model = Raffle
    template_name = "home/index.html"
    context_object_name = "raffles"  # Nombre en el contexto para las rifas
    paginate_by = 3  # Configura cuántas rifas mostrar por página

    def get_queryset(self):
        """
        Filtra las rifas excluyendo la más reciente.
        """
        # Obtener la rifa más reciente por fecha de sorteo
        latest_raffle = Raffle.objects.order_by('-raffle_date').first()

        # Filtrar todas las rifas, excluyendo la última
        if latest_raffle:
            return Raffle.objects.exclude(id=latest_raffle.id).order_by('-raffle_date')
        return Raffle.objects.order_by("-raffle_date")

    def paginate_queryset(self, queryset, page_size):
        """
        Sobrescribe el método para manejar la paginación.
        """
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get("page")

        try:
            raffles = paginator.page(page)
        except PageNotAnInteger:
            # Si la página no es un número, mostrar la primera página
            raffles = paginator.page(1)
        except EmptyPage:
            # Si la página está vacía, mostrar la última página disponible
            raffles = paginator.page(paginator.num_pages)

        return (
            paginator,
            raffles,
            raffles.object_list,
            raffles.has_other_pages(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener la última rifa por fecha de sorteo
        latest_raffle = Raffle.objects.order_by("-raffle_date").first()
        if latest_raffle:
            # Calcular el progreso de la última rifa
            latest_raffle_progress = self.calculate_progress(latest_raffle)
            if latest_raffle_progress>=100:
                latest_raffle_progress = 99.10
            # Agregar ambas listas al contexto
            context["latest_raffle"] = latest_raffle
            context["latest_raffle_progress"] = f"{latest_raffle_progress:.2f}"

        return context

    def calculate_progress(self, raffle):
        """Calcula el porcentaje de boletos vendidos en una rifa"""
        # Calcular cuántos boletos confirmados se han vendido
        tickets_confirmed = (
            Participant.objects.filter(
                raffle=raffle, status=Participant.CONFIRMED
            ).aggregate(total_tickets_confirmed=Sum("tickets_purchased"))[
                "total_tickets_confirmed"
            ]
            or 0
        )

        # Calcular cuántos boletos no confirmados (pendientes) hay
        tickets_pending = (
            Participant.objects.filter(
                raffle=raffle, status=Participant.PENDING
            ).aggregate(total_tickets_pending=Sum("tickets_purchased"))[
                "total_tickets_pending"
            ]
            or 0
        )

        # Obtener los boletos comprados (boletos vendidos)
        tickets_sold = tickets_confirmed + tickets_pending

        # Calcular el porcentaje de progreso
        if raffle.available_tickets > 0:
            progress = (tickets_sold / raffle.available_tickets) * 100
        else:
            progress = 0
        return round(progress, 2)  # Redondear a dos decimales

def comprobar(request):
    search_result = None
    context = {}

    if request.method == "GET" and "search" in request.GET:
        payment_reference = request.GET["search"]
        try:
            # Filtrar el pago por la referencia ingresada
            search_result = Participant.objects.get(payment_reference=payment_reference)
            if search_result.status == search_result.CONFIRMED:
                context["assigned_numbers"] = search_result.assigned_numbers.split(",")
        except Participant.DoesNotExist:
            # Si no se encuentra el pago, search_result será None
            search_result = "No existe"

    context["search_result"] = search_result
    
    return render(request, "home/comprobar.html", context)
