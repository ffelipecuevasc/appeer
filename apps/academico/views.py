"""
Vistas HTTP delgadas de apps.academico. Toda regla de negocio vive en
selectors.py (lectura) o services.py (escritura); estas vistas solo
orquestan. Las vistas de InscripcionEstudiante llegan en el Paso B.
"""
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.academico import selectors, services
from apps.academico.forms import ClaseForm, EdicionEscuelaForm, InscripcionEstudianteForm
from apps.academico.serializers import ClaseDTO, EdicionEscuelaDTO, InscripcionEstudianteDTO
from core.mixins import AccessControlMixin


class EdicionEscuelaListView(AccessControlMixin, ListView):
    template_name = "academico/edicion_list.html"
    context_object_name = "ediciones"
    paginate_by = 20

    def get_queryset(self):
        return selectors.listar_ediciones()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ediciones"] = [EdicionEscuelaDTO.from_model(e) for e in context["ediciones"]]
        return context


class EdicionEscuelaDetailView(AccessControlMixin, DetailView):
    template_name = "academico/edicion_detail.html"
    context_object_name = "edicion"

    def get_object(self, queryset=None):
        edicion = selectors.obtener_edicion_por_id(self.kwargs["id_edicion"])
        if edicion is None:
            raise Http404("Edición no encontrada.")
        return edicion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edicion"] = EdicionEscuelaDTO.from_model(context["edicion"])
        context["inscripciones"] = [
            InscripcionEstudianteDTO.from_model(i)
            for i in selectors.listar_inscripciones().filter(edicion_id=self.kwargs["id_edicion"])
        ]
        return context


class EdicionEscuelaCreateView(AccessControlMixin, CreateView):
    form_class = EdicionEscuelaForm
    template_name = "academico/edicion_form.html"

    def form_valid(self, form):
        try:
            edicion = services.crear_edicion(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("academico:ediciones_detalle", id_edicion=edicion.pk)


class EdicionEscuelaUpdateView(AccessControlMixin, UpdateView):
    form_class = EdicionEscuelaForm
    template_name = "academico/edicion_form.html"

    def get_object(self, queryset=None):
        edicion = selectors.obtener_edicion_por_id(self.kwargs["id_edicion"])
        if edicion is None:
            raise Http404("Edición no encontrada.")
        return edicion

    def form_valid(self, form):
        try:
            edicion = services.actualizar_edicion(edicion=self.object, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("academico:ediciones_detalle", id_edicion=edicion.pk)


class EdicionEscuelaDeleteView(AccessControlMixin, DeleteView):
    template_name = "academico/edicion_confirm_delete.html"
    success_url = reverse_lazy("academico:ediciones_listado")

    def get_object(self, queryset=None):
        edicion = selectors.obtener_edicion_por_id(self.kwargs["id_edicion"])
        if edicion is None:
            raise Http404("Edición no encontrada.")
        return edicion

    def form_valid(self, form):
        try:
            services.eliminar_edicion(edicion=self.object)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect(self.success_url)


class ClaseListView(AccessControlMixin, ListView):
    template_name = "academico/clase_list.html"
    context_object_name = "clases"
    paginate_by = 20

    def get_queryset(self):
        return selectors.listar_clases()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clases"] = [ClaseDTO.from_model(c) for c in context["clases"]]
        return context


class ClaseDetailView(AccessControlMixin, DetailView):
    template_name = "academico/clase_detail.html"
    context_object_name = "clase"

    def get_object(self, queryset=None):
        clase = selectors.obtener_clase_por_id(self.kwargs["id_clase"])
        if clase is None:
            raise Http404("Clase no encontrada.")
        return clase

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = ClaseDTO.from_model(context["clase"])
        return context


class ClaseCreateView(AccessControlMixin, CreateView):
    form_class = ClaseForm
    template_name = "academico/clase_form.html"

    def form_valid(self, form):
        try:
            clase = services.crear_clase(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("academico:clases_detalle", id_clase=clase.pk)


class ClaseUpdateView(AccessControlMixin, UpdateView):
    form_class = ClaseForm
    template_name = "academico/clase_form.html"

    def get_object(self, queryset=None):
        clase = selectors.obtener_clase_por_id(self.kwargs["id_clase"])
        if clase is None:
            raise Http404("Clase no encontrada.")
        return clase

    def form_valid(self, form):
        try:
            clase = services.actualizar_clase(clase=self.object, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("academico:clases_detalle", id_clase=clase.pk)


class ClaseDeleteView(AccessControlMixin, DeleteView):
    template_name = "academico/clase_confirm_delete.html"
    success_url = reverse_lazy("academico:clases_listado")

    def get_object(self, queryset=None):
        clase = selectors.obtener_clase_por_id(self.kwargs["id_clase"])
        if clase is None:
            raise Http404("Clase no encontrada.")
        return clase

    def form_valid(self, form):
        try:
            services.eliminar_clase(clase=self.object)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect(self.success_url)


class InscripcionEstudianteCreateView(AccessControlMixin, CreateView):
    """
    Alta de una inscripción, siempre en el contexto de una Edición
    fija tomada de la URL (id_edicion). Decisión registrada en la
    Fase 2: el <select> de estudiantes se filtra server-side a quienes
    todavía no están inscritos en esa edición.
    """
    form_class = InscripcionEstudianteForm
    template_name = "academico/inscripcion_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Guard de autenticación ANTES de la consulta (Subfase 8.2,
        # ver AccessControlMixin.bloqueo_si_no_autenticado): esta
        # vista define su propio dispatch(), así que sin este guard
        # explícito el chequeo de sesión de AccessControlMixin nunca
        # correría antes que esta consulta.
        bloqueo = self.bloqueo_si_no_autenticado(request)
        if bloqueo is not None:
            return bloqueo
        self.edicion = selectors.obtener_edicion_por_id(self.kwargs["id_edicion"])
        if self.edicion is None:
            raise Http404("Edición no encontrada.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["edicion"] = self.edicion
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edicion"] = EdicionEscuelaDTO.from_model(self.edicion)
        return context

    def form_valid(self, form):
        try:
            services.crear_inscripcion(
                estudiante=form.cleaned_data["estudiante"],
                edicion=self.edicion,
                clase=form.cleaned_data["clase"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("academico:ediciones_detalle", id_edicion=self.edicion.pk)


class InscripcionEstudianteUpdateView(AccessControlMixin, UpdateView):
    """
    Edición de una inscripción existente. La Edición queda fija (mismo
    motivo que en el alta): solo se puede cambiar el estudiante o la
    clase asignados.
    """
    form_class = InscripcionEstudianteForm
    template_name = "academico/inscripcion_form.html"

    def get_object(self, queryset=None):
        inscripcion = selectors.obtener_inscripcion_por_id(self.kwargs["id_inscripcion"])
        if inscripcion is None:
            raise Http404("Inscripción no encontrada.")
        return inscripcion

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["edicion"] = self.object.edicion
        kwargs["excluir_inscripcion_id"] = self.object.pk
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edicion"] = EdicionEscuelaDTO.from_model(self.object.edicion)
        return context

    def form_valid(self, form):
        try:
            services.actualizar_inscripcion(
                inscripcion=self.object,
                estudiante=form.cleaned_data["estudiante"],
                clase=form.cleaned_data["clase"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("academico:ediciones_detalle", id_edicion=self.object.edicion_id)


class InscripcionEstudianteDeleteView(AccessControlMixin, DeleteView):
    template_name = "academico/inscripcion_confirm_delete.html"

    def get_object(self, queryset=None):
        inscripcion = selectors.obtener_inscripcion_por_id(self.kwargs["id_inscripcion"])
        if inscripcion is None:
            raise Http404("Inscripción no encontrada.")
        return inscripcion

    def get_success_url(self):
        return reverse("academico:ediciones_detalle", kwargs={"id_edicion": self.object.edicion_id})

    def form_valid(self, form):
        try:
            services.eliminar_inscripcion(inscripcion=self.object)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect(self.get_success_url())