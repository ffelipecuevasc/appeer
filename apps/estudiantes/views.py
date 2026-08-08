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
from core.mixins import AjaxRequestMixin


class EstudianteListView(AjaxRequestMixin, ListView):
    """
    Subfase 6.2: expone búsqueda por ?q= (funciona con GET normal,
    sin JS — mejora progresiva) y, cuando la petición viene marcada
    como AJAX (AjaxRequestMixin, core/mixins.py — Subfase 6.4),
    responde solo con el fragmento de filas en vez de la página
    completa. La Subfase 6.3 conecta el <input> de búsqueda a esto
    vía fetch.
    """
    template_name = "estudiantes/estudiante_list.html"
    context_object_name = "estudiantes"
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()
        return selectors.listar_estudiantes(query=query or None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estudiantes"] = [
            EstudianteDTO.from_model(e) for e in context["estudiantes"]
        ]
        context["query"] = self.request.GET.get("q", "").strip()
        return context

    def get_template_names(self):
        if self.is_ajax():
            return ["estudiantes/_estudiante_rows.html"]
        return [self.template_name]


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
