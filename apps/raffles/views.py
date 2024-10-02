from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from .models import Raffle, Participant
from .forms import RaffleForm, ParticipantForm, RaffleImageFormSet
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
)
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum, Q


class RaffleCreateView(PermissionRequiredMixin, CreateView):
    model = Raffle
    form_class = RaffleForm
    template_name = "raffles/raffle_form.html"
    success_url = reverse_lazy(
        "raffles:list"
    )  # Redirige a la lista de rifas después de guardar
    permission_required = "raffles.add_raffle"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["image_formset"] = RaffleImageFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            data["image_formset"] = RaffleImageFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context["image_formset"]
        if form.is_valid() and image_formset.is_valid():
            self.object = form.save()
            image_formset.instance = self.object
            image_formset.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


# Editar un rifas
class RaffleUpdateView(PermissionRequiredMixin, UpdateView):
    model = Raffle
    form_class = RaffleForm
    template_name = "raffles/raffle_form.html"
    success_url = reverse_lazy("raffles:list")
    permission_required = "raffles.change_raffle"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["image_formset"] = RaffleImageFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            data["image_formset"] = RaffleImageFormSet(instance=self.object)
        # Añadir validación para el número de ganadores cuando la rifa finalice
        if self.object.is_finished():
            data["show_winner_field"] = (
                True  # Mostrar campo solo si la rifa está finalizada
            )
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context["image_formset"]

        if form.is_valid() and image_formset.is_valid():
            raffle = form.instance
            original_raffle = Raffle.objects.get(pk=self.object.pk)

            # Detectar si el estado ha cambiado de finalizado a en proceso
            status_changed_to_in_process = (
                original_raffle.is_finished()
                and not form.cleaned_data.get("status")
                == "finished"  # ajusta según tus estados
            )

            if status_changed_to_in_process:
                # Si el estado cambió a en proceso, resetear el campo winner
                raffle.winner = None
                form.cleaned_data["num_winners"] = None
            elif raffle.is_finished():
                num_winners = form.cleaned_data.get("num_winners")

                if num_winners is not None:
                    confirmed_participants_count = (
                        raffle.participants.filter(status="confirmed")
                        .values("identity_card")
                        .distinct()
                        .count()
                    )

                    if confirmed_participants_count < num_winners:
                        form.add_error(
                            "num_winners",
                            "No hay suficientes participantes únicos (por cédula) para declarar los ganadores.",
                        )
                        return self.form_invalid(form)

                    try:
                        self.object = form.save()
                        self.object.select_winners(num_winners)
                    except ValueError as e:
                        form.add_error(None, str(e))
                        return self.form_invalid(form)
                else:
                    self.object = form.save(commit=False)
                    self.object.winner = original_raffle.winner
                    self.object.save()
            else:
                # Si la rifa no está finalizada, guardamos normalmente
                self.object = form.save()

            # Guardamos el formset de imágenes
            image_formset.instance = self.object
            image_formset.save()

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


# Lista de rifas
class RaffleListView(PermissionRequiredMixin, ListView):
    model = Raffle  # Modelo de rifas
    template_name = "raffles/raffle_list.html"  # Plantilla a utilizar
    context_object_name = "raffles"  # Nombre de la variable en el template
    permission_required = "raffles.view_raffle"  # Permiso requerido
    paginate_by = 10  # Paginación: mostrar 10 rifas por página
    raise_exception = True  # Si no tienes permisos, lanzar una excepción

    def get_queryset(self):
        """
        Filtra y ordena las rifas según los parámetros 'order_by' y 'order_direction'.
        """
        order_by = self.request.GET.get(
            "order_by", "raffle_date"
        )  # Ordenar por fecha de sorteo por defecto
        order_direction = self.request.GET.get("order_direction", "desc")

        # Ajustar el prefijo de ordenación
        if order_direction == "desc":
            order_by = f"-{order_by}"

        queryset = Raffle.objects.all().order_by(order_by)
        return queryset

    def paginate_queryset(self, queryset, page_size):
        """
        Sobrescribe el método para manejar el caso de una página vacía.
        """
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get("page")

        try:
            raffles = paginator.page(page)
        except PageNotAnInteger:
            # Si el parámetro de la página no es un número, mostrar la primera página
            raffles = paginator.page(1)
        except EmptyPage:
            # Si la página está vacía, mostrar la última página disponible
            raffles = paginator.page(paginator.num_pages)

        return (paginator, raffles, raffles.object_list, raffles.has_other_pages())

    def get_context_data(self, **kwargs):
        """
        Añade información de la ordenación al contexto.
        """
        context = super().get_context_data(**kwargs)
        context["current_order"] = self.request.GET.get("order_by", "raffle_date")
        context["current_direction"] = self.request.GET.get("order_direction", "desc")
        return context

from django.contrib.auth.decorators import permission_required

@permission_required("raffles.change_participant")
def confirm_payment(request, id_raffle, id_participant):
    participant = get_object_or_404(Participant, pk=id_participant)
    participant.confirm_payment()
    return redirect(reverse("raffles:list_participant", args=[id_raffle]))


# Lista de participantes
class ParticipantListView(PermissionRequiredMixin, ListView):
    model = Participant  # Modelo de rifas
    template_name = "raffles/raffle_participant_list.html"  # Plantilla a utilizar
    context_object_name = "participants"  # Nombre de la variable en el template
    permission_required = "raffles.view_participant"  # Permiso requerido
    paginate_by = 10  # Paginación: mostrar 10 rifas por página
    raise_exception = True  # Si no tienes permisos, lanzar una excepción

    def get_queryset(self):
        raffle = get_object_or_404(Raffle, pk=self.kwargs.get("pk"))

        # Obtener el valor del campo de búsqueda de la URL
        search_query = self.request.GET.get("search", "")

        # Obtener el valor de ordenación de la URL
        order_by = self.request.GET.get("order_by", "status")
        order_direction = self.request.GET.get("order_direction", "desc")

        if order_direction == "desc":
            order_by = f"-{order_by}"

        # Filtrar por rifa y realizar la búsqueda
        queryset = Participant.objects.filter(raffle=raffle).order_by(order_by)

        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query)  # Filtrar por nombre
                | Q(status__icontains=search_query)  # Filtrar por estado
                | Q(payment_date__icontains=search_query)  # Filtrar por fecha de pago
                | Q(
                    payment_reference__icontains=search_query
                )  # Filtrar por referencia de pago
                | Q(
                    identity_card__icontains=search_query
                )  # Filtrar por cédula del participante
            )

        return queryset

    def paginate_queryset(self, queryset, page_size):
        """
        Sobrescribe el método para manejar el caso de una página vacía.
        """
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get("page")

        try:
            participants = paginator.page(page)
        except PageNotAnInteger:
            # Si el parámetro de la página no es un número, mostrar la primera página
            participants = paginator.page(1)
        except EmptyPage:
            # Si la página está vacía, mostrar la última página disponible
            participants = paginator.page(paginator.num_pages)

        return (
            paginator,
            participants,
            participants.object_list,
            participants.has_other_pages(),
        )

    def get_context_data(self, **kwargs):
        """
        Añade el término de búsqueda actual al contexto para utilizarlo en el template.
        """
        context = super().get_context_data(**kwargs)
        context["raffle"] = get_object_or_404(Raffle, pk=self.kwargs.get("pk"))
        context["current_order"] = self.request.GET.get("order_by", "status")
        context["current_direction"] = self.request.GET.get("order_direction", "desc")
        context["search_query"] = self.request.GET.get("search", "")
        return context


class ParticipantDetailView(PermissionRequiredMixin, DetailView):
    model = Participant
    template_name = "raffles/participant_detail.html"
    context_object_name = "participant"
    permission_required = "raffles.view_participant"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.object
        if participant.assigned_numbers:
            context["assigned_numbers"] = participant.assigned_numbers.split(",")

        # Si quieres agregar más datos al contexto, puedes hacerlo aquí.
        return context


class ParticipantCreateView(PermissionRequiredMixin, CreateView):
    model = Participant
    form_class = ParticipantForm
    template_name = "raffles/raffle_participant_form.html"
    permission_required = "raffles.add_participant"

    def dispatch(self, request, *args, **kwargs):
        self.raffle = get_object_or_404(Raffle, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["raffle"] = self.raffle  # Pasar la rifa al formulario para validar
        return kwargs

    def form_valid(self, form):
        raffle = get_object_or_404(Raffle, id=self.kwargs["pk"])
        participant = form.save(commit=False)
        participant.raffle = raffle

        # Comprobar si el estado de pago es confirmado al momento de crear el participante
        if participant.status == participant.CONFIRMED:
            participant.confirm_payment()

        participant.save()
        return super().form_valid(form)

    def get_success_url(self):
        """
        Definimos la URL de éxito. En este caso, redirigimos a la lista de participantes.
        """
        return reverse("raffles:list_participant", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        """
        Agrega el objeto 'raffle' al contexto para que pueda ser utilizado en la plantilla.
        """
        context = super().get_context_data(**kwargs)
        raffle = get_object_or_404(Raffle, pk=self.kwargs.get("pk"))
        context["raffle"] = raffle  # Agregar el objeto de la rifa al contexto
        return context


class ParticipantUpdateView(PermissionRequiredMixin, UpdateView):
    model = Participant
    form_class = ParticipantForm
    template_name = "raffles/raffle_participant_form.html"
    permission_required = "raffles.change_participant"

    def dispatch(self, request, *args, **kwargs):
        self.raffle = get_object_or_404(Raffle, pk=kwargs.get("raffle_id"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["raffle"] = self.raffle  # Pasar la rifa al formulario para validar
        return kwargs

    def form_valid(self, form):
        participant = form.save(commit=False)
        # Verificar si el estado del pago ha cambiado
        original_participant = Participant.objects.get(id=participant.id)

        # Si se altero el estado de pago del participante
        if original_participant.status != participant.status:
            if participant.status == participant.PENDING:
                participant.assigned_numbers = ""
            elif participant.status == participant.CONFIRMED:
                participant.confirm_payment()

        participant.save()
        return super().form_valid(form)

    def get_success_url(self):
        """
        Definimos la URL de éxito. En este caso, redirigimos a la lista de participantes.
        """
        return reverse("raffles:list_participant", kwargs={"pk": self.object.raffle.id})

    def get_context_data(self, **kwargs):
        """
        Sobrescribimos el contexto para mostrar los números asignados en la plantilla.
        """
        context = super().get_context_data(**kwargs)
        raffle = get_object_or_404(Raffle, pk=self.kwargs.get("raffle_id"))
        context["raffle"] = raffle  # Agregar el objeto de la rifa al contexto
        participant = self.object
        if participant.assigned_numbers:
            context["assigned_numbers"] = participant.assigned_numbers.split(",")
        return context


class ParticipantDeleteView(PermissionRequiredMixin, DeleteView):
    model = Participant
    permission_required = (
        "raffles.delete_participant"  # Requiere permiso para eliminar usuarios
    )
    raise_exception = True

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Participante eliminado exitosamente.")
        return response

    def get_success_url(self):
        """
        Después de eliminar, redirigimos a la lista de participantes de la rifa correspondiente.
        """
        return reverse("raffles:list_participant", kwargs={"pk": self.object.raffle.id})


# Eliminar una rifa
class RaffleDeleteView(PermissionRequiredMixin, DeleteView):
    model = Raffle
    permission_required = (
        "raffles.delete_raffle"  # Requiere permiso para eliminar usuarios
    )
    success_url = reverse_lazy(
        "raffles:list"
    )  # Redirigir a la lista de usuarios después de eliminar
    raise_exception = True

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Usuario eliminado exitosamente.")
        return response


# Detalles de la rifa
class RaffleDetailView(PermissionRequiredMixin, DetailView):
    model = Raffle
    permission_required = (
        "raffles.view_raffle"  # Requiere permiso para eliminar usuarios
    )
    template_name = (
        "raffles/raffle_detail.html"  # Nombre de la plantilla que vamos a crear
    )
    context_object_name = "raffle"  # Nombre del contexto en la plantilla

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        raffle = self.get_object()

        # Obtener todas las imágenes de premios asociadas a la rifa
        context["prize_images"] = raffle.prize_images.all()

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

        context["tickets_confirmed"] = tickets_confirmed
        context["tickets_pending"] = tickets_pending

        # Calcular el progreso de la rifa
        if raffle.available_tickets > 0:
            progress = (tickets_confirmed / raffle.available_tickets) * 100
        else:
            progress = 0
        context["progress"] = f"{progress:.2f}"

        return context


def comprobante(request, reference):
    context = {}
    participant = get_object_or_404(Participant, payment_reference=reference)
    context["participant"] = participant
    if participant.status == participant.CONFIRMED:
        context["assigned_numbers"] = participant.assigned_numbers.split(",")
    return render(request, "raffles/comprobante.html", context)
