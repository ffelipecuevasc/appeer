"""
Vistas HTTP delgadas de apps.planificacion. Toda regla de negocio
vive en selectors.py (lectura) o services.py (escritura).
"""
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.academico.models import EdicionEscuela
from apps.planificacion import selectors, services
from apps.planificacion.forms import ProgramacionClaseForm
from apps.planificacion.serializers import ProgramacionClaseDTO


class ProgramacionClaseListView(ListView):
    """
    Vista de horario: lista todas las programaciones ordenadas por
    edición/semana/día/aula (Meta.ordering del modelo), con filtro
    opcional por edición vía querystring — sin JavaScript, un <select>
    con botón "Filtrar" que envía un GET normal.
    """
    template_name = "planificacion/programacion_list.html"
    context_object_name = "programaciones"
    paginate_by = 30

    def get_queryset(self):
        queryset = selectors.listar_programaciones()
        id_edicion = self.request.GET.get("edicion")
        if id_edicion:
            queryset = queryset.filter(edicion_id=id_edicion)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["programaciones"] = [ProgramacionClaseDTO.from_model(p) for p in context["programaciones"]]
        context["ediciones"] = EdicionEscuela.objects.order_by("-fecha_inicio", "nombre_edicion")
        context["edicion_seleccionada"] = self.request.GET.get("edicion", "")
        return context


class ProgramacionClaseDetailView(DetailView):
    template_name = "planificacion/programacion_detail.html"
    context_object_name = "programacion"

    def get_object(self, queryset=None):
        programacion = selectors.obtener_programacion_por_id(self.kwargs["id_programacion"])
        if programacion is None:
            raise Http404("Programación no encontrada.")
        return programacion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["programacion"] = ProgramacionClaseDTO.from_model(context["programacion"])
        return context


class ProgramacionClaseCreateView(CreateView):
    form_class = ProgramacionClaseForm
    template_name = "planificacion/programacion_form.html"

    def form_valid(self, form):
        try:
            programacion = services.crear_programacion(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("planificacion:programaciones_detalle", id_programacion=programacion.pk)


class ProgramacionClaseUpdateView(UpdateView):
    form_class = ProgramacionClaseForm
    template_name = "planificacion/programacion_form.html"

    def get_object(self, queryset=None):
        programacion = selectors.obtener_programacion_por_id(self.kwargs["id_programacion"])
        if programacion is None:
            raise Http404("Programación no encontrada.")
        return programacion

    def form_valid(self, form):
        try:
            programacion = services.actualizar_programacion(programacion=self.object, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("planificacion:programaciones_detalle", id_programacion=programacion.pk)


class ProgramacionClaseDeleteView(DeleteView):
    template_name = "planificacion/programacion_confirm_delete.html"
    success_url = reverse_lazy("planificacion:programaciones_listado")

    def get_object(self, queryset=None):
        programacion = selectors.obtener_programacion_por_id(self.kwargs["id_programacion"])
        if programacion is None:
            raise Http404("Programación no encontrada.")
        return programacion

    def form_valid(self, form):
        try:
            services.eliminar_programacion(programacion=self.object)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect(self.success_url)