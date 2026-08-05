"""
Vistas HTTP delgadas de apps.estudiantes. Toda regla de negocio vive
en selectors.py (lectura) o services.py (escritura); estas vistas
solo orquestan.
"""
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.estudiantes import selectors, services
from apps.estudiantes.forms import EstudianteForm
from apps.estudiantes.serializers import EstudianteDTO


class EstudianteListView(ListView):
    template_name = "estudiantes/estudiante_list.html"
    context_object_name = "estudiantes"
    paginate_by = 20

    def get_queryset(self):
        return selectors.listar_estudiantes()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estudiantes"] = [
            EstudianteDTO.from_model(e) for e in context["estudiantes"]
        ]
        return context


class EstudianteDetailView(DetailView):
    template_name = "estudiantes/estudiante_detail.html"
    context_object_name = "estudiante"

    def get_object(self, queryset=None):
        estudiante = selectors.obtener_estudiante_por_id(self.kwargs["id_estudiante"])
        if estudiante is None:
            raise Http404("Estudiante no encontrado.")
        return estudiante

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estudiante"] = EstudianteDTO.from_model(context["estudiante"])
        return context


class EstudianteCreateView(CreateView):
    form_class = EstudianteForm
    template_name = "estudiantes/estudiante_form.html"

    def form_valid(self, form):
        try:
            estudiante = services.crear_estudiante(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("estudiantes:detalle", id_estudiante=estudiante.pk)


class EstudianteUpdateView(UpdateView):
    form_class = EstudianteForm
    template_name = "estudiantes/estudiante_form.html"

    def get_object(self, queryset=None):
        estudiante = selectors.obtener_estudiante_por_id(self.kwargs["id_estudiante"])
        if estudiante is None:
            raise Http404("Estudiante no encontrado.")
        return estudiante

    def form_valid(self, form):
        try:
            estudiante = services.actualizar_estudiante(estudiante=self.object, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("estudiantes:detalle", id_estudiante=estudiante.pk)


class EstudianteDeleteView(DeleteView):
    template_name = "estudiantes/estudiante_confirm_delete.html"
    success_url = reverse_lazy("estudiantes:listado")

    def get_object(self, queryset=None):
        estudiante = selectors.obtener_estudiante_por_id(self.kwargs["id_estudiante"])
        if estudiante is None:
            raise Http404("Estudiante no encontrado.")
        return estudiante

    def form_valid(self, form):
        try:
            services.eliminar_estudiante(estudiante=self.object)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect(self.success_url)