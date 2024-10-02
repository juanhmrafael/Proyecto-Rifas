from django.shortcuts import redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages

from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    UserPassesTestMixin,
    LoginRequiredMixin,
)
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.models import Permission
from .forms import UserCreateForm, UserUpdateForm


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")  # Obtén el correo electrónico
        password = request.POST.get("password")  # Obtén la contraseña
        remember_me = request.POST.get("remember_me")  # Obtén el estado del checkbox

        # Autenticación usando el correo electrónico
        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            if remember_me:
                request.session.set_expiry(1209600)  # 2 semanas en segundos
            else:
                request.session.set_expiry(0)  # La sesión expira al cerrar el navegador
            messages.success(request, "Inicio de sesión exitoso.")
        else:
            messages.error(
                request, "Credenciales incorrectas. Por favor, intenta de nuevo."
            )
    return redirect(
        "home:index"
    )  # Redirige a la página principal o a una página de éxito


# Lista de usuarios
class UserListView(PermissionRequiredMixin, ListView):
    model = get_user_model()  # Modelo de usuarios
    template_name = "users/user_list.html"  # Plantilla a utilizar
    context_object_name = "users"  # Nombre de la variable en el template
    permission_required = [
        "users.view_useraccount",
        "users.add_useraccount",
    ]  # Permiso requerido
    paginate_by = 10  # Paginación: mostrar 10 usuarios por página
    raise_exception = True  # Si no tienes permisos, lanzar una excepción

    def get_permission_required(self):
        """
        Permitir acceso si el usuario tiene al menos uno de los permisos.
        """
        # Retornar la lista de permisos
        return self.permission_required

    def has_permission(self):
        """
        Verifica si el usuario tiene al menos uno de los permisos.
        """
        # Retorna True si el usuario tiene al menos uno de los permisos requeridos
        return any(self.request.user.has_perm(perm) for perm in self.permission_required)
    
    def get_queryset(self):
        """
        Sobrescribe el queryset para excluir al usuario autenticado.
        """
        queryset = super().get_queryset()
        return queryset.exclude(id=self.request.user.id)

    def get_ordering(self):
        """
        Define el criterio de ordenación dinámico.
        """
        ordering = self.request.GET.get(
            "orderby", "email"
        )  # Por defecto, ordena por email
        return ordering

    def paginate_queryset(self, queryset, page_size):
        """
        Sobrescribe el método para manejar el caso de una página vacía.
        """
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get("page")

        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            # Si el parámetro de la página no es un número, mostrar la primera página
            users = paginator.page(1)
        except EmptyPage:
            # Si la página está vacía, mostrar la última página disponible
            users = paginator.page(paginator.num_pages)

        return (paginator, users, users.object_list, users.has_other_pages())


# Crear un usuario
class UserCreateView(PermissionRequiredMixin, CreateView):
    model = get_user_model()
    form_class = UserCreateForm
    template_name = "users/form.html"
    success_url = reverse_lazy("users:list")
    permission_required = "users.add_useraccount"
    
    def get_form(self, *args, **kwargs):
        # Obtener el formulario
        form = super().get_form(*args, **kwargs)

        # Verificar si el usuario tiene permiso para cambiar permisos
        if not self.request.user.has_perm("users.change_permissions_user"):
            # Deshabilitar los campos de is_active, is_superuser y user_permissions
            form.fields["is_active"].disabled = True
            form.fields["is_superuser"].disabled = True
            form.fields["user_permissions"].disabled = True

        return form

    def form_valid(self, form):
        # print("Datos del formulario:", form.cleaned_data)
        response = super().form_valid(form)
        user = self.object

        user_permissions = form.cleaned_data.get("user_permissions", [])
        # print("Permisos seleccionados:", user_permissions)

        user.user_permissions.set(user_permissions)

        # print(f"Permisos asignados al usuario: {user_permissions}")
        # print(f"Permisos del usuario después de asignar: {user.user_permissions.all()}")
        messages.success(self.request, "Usuario creado exitosamente.")
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object:
            kwargs["instance"] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtenemos todos los permisos y agrupamos por ContentType (modelo relacionado)
        permissions = Permission.objects.all().select_related("content_type")
        models_plural = {
            permission.content_type.model: permission.content_type.model_class()._meta.verbose_name_plural
            for permission in permissions
        }
        context["models_plural"] = models_plural

        return context


# Actualizar cuenta
class CurrentUserUpdateView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "users/account.html"
    success_url = reverse_lazy(
        "users:profile_update"
    )  # Cambia esto si tienes una URL específica para el perfil
    login_url = reverse_lazy(
        "users:login"
    )  # Asegúrate de tener una URL de inicio de sesión configurada

    def get_form(self, *args, **kwargs):
        # Obtener el formulario
        form = super().get_form(*args, **kwargs)

        # Verificar si el usuario tiene permiso para cambiar permisos
        if not self.request.user.has_perm("users.change_permissions_user"):
            # Deshabilitar los campos de is_active, is_superuser y user_permissions
            form.fields["is_active"].disabled = True
            form.fields["is_superuser"].disabled = True
            form.fields["user_permissions"].disabled = True

        return form

    def get_object(self, queryset=None):
        # Retorna el usuario actual para la vista de actualización
        return self.request.user

    def form_valid(self, form):
        # Guarda el usuario actualizado y muestra un mensaje de éxito
        response = super().form_valid(form)
        user = self.object

        # Obtener los permisos seleccionados
        user_permissions = form.cleaned_data.get("user_permissions", [])
        # Asignar los permisos al usuario
        user.user_permissions.set(user_permissions)
        messages.success(self.request, "Tu cuenta ha sido actualizada exitosamente.")
        return response

    def get_initial(self):
        # Cargar permisos actuales del usuario para el formulario
        initial = super().get_initial()
        initial["user_permissions"] = self.object.user_permissions.all()
        return initial


# Editar un usuario
class UserUpdateView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "users/form.html"
    success_url = reverse_lazy("users:list")
    permission_required = "users.change_useraccount"

    def test_func(self):
        # Verificar si el usuario a editar no es el usuario actual
        return self.get_object() != self.request.user

    def handle_no_permission(self):
        # Si el usuario intenta editarse a sí mismo, redirigir y mostrar un mensaje
        if not self.test_func():
            messages.error(
                self.request, "No puedes editar tu propio usuario desde esta vista."
            )
            return redirect(
                "users:list"
            )  # Asume que 'users:list' es la URL de la lista de usuarios
        return super().handle_no_permission()

    def form_valid(self, form):
        # print("Errores del formulario:", form.errors)
        # print("Datos del formulario:", form.cleaned_data)
        response = super().form_valid(form)
        user = self.object

        # Obtener los permisos seleccionados
        user_permissions = form.cleaned_data.get("user_permissions", [])
        # Asignar los permisos al usuario
        user.user_permissions.set(user_permissions)
        messages.success(self.request, "Usuario actualizado exitosamente.")
        # print(f"Permisos del usuario después de editar: {user.user_permissions.all()}")
        return response

    def get_initial(self):
        # Cargar permisos actuales del usuario para el formulario
        initial = super().get_initial()
        initial["user_permissions"] = self.object.user_permissions.all()
        return initial

    def get_form(self, *args, **kwargs):
        # Obtener el formulario
        form = super().get_form(*args, **kwargs)

        # Verificar si el usuario tiene permiso para cambiar permisos
        if not self.request.user.has_perm("auth.change_permissions_user"):
            # Deshabilitar los campos de is_active, is_superuser y user_permissions
            form.fields["is_active"].disabled = True
            form.fields["is_superuser"].disabled = True
            form.fields["user_permissions"].disabled = True

        return form


# Eliminar un usuario
class UserDeleteView(PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    model = get_user_model()
    permission_required = (
        "users.delete_useraccount"  # Requiere permiso para eliminar usuarios
    )
    success_url = reverse_lazy(
        "users:list"
    )  # Redirigir a la lista de usuarios después de eliminar
    raise_exception = True

    def test_func(self):
        # Verificar si el usuario a editar no es el usuario actual
        return self.get_object() != self.request.user

    def handle_no_permission(self):
        # Si el usuario intenta editarse a sí mismo, redirigir y mostrar un mensaje
        if not self.test_func():
            messages.error(self.request, "No puedes eliminar tu propio usuario.")
            return redirect(
                "users:list"
            )  # Asume que 'users:list' es la URL de la lista de usuarios
        return super().handle_no_permission()

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Usuario eliminado exitosamente.")
        return response


# Detalles de usuario
class UserDetailView(PermissionRequiredMixin, UserPassesTestMixin, DetailView):
    model = get_user_model()
    template_name = "users/user_detail.html"
    permission_required = (
        "users.view_useraccount"  # Permiso para ver detalles del usuario
    )
    raise_exception = True

    def test_func(self):
        # Verificar si el usuario a editar no es el usuario actual
        return self.get_object() != self.request.user

    def handle_no_permission(self):
        # Si el usuario intenta editarse a sí mismo, redirigir y mostrar un mensaje
        if not self.test_func():
            messages.error(self.request, "No puedes detallar tu propio usuario.")
            return redirect(
                "users:list"
            )  # Asume que 'users:list' es la URL de la lista de usuarios
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Puedes añadir datos adicionales al contexto aquí si es necesario
        return context
