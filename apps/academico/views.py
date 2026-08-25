"""
Vistas HTTP delgadas de apps.academico. Toda regla de negocio vive en
selectors.py (lectura) o services.py (escritura); estas vistas solo
orquestan.

Fase 11 (Adenda 9): las 5 vistas de EdicionEscuela (List/Detail/Create/
Update/Delete) desaparecen junto con la entidad. ClaseDeleteView
también desaparece — no por fusión, sino por decisión de negocio
explícita: las clases nunca se eliminan (Decisión 2).
"""
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.academico import selectors, services
from apps.academico.forms import ClaseForm, InscripcionEstudianteForm
from apps.academico.serializers import ClaseDTO, InscripcionEstudianteDTO
from core.mixins import AccessControlMixin


class ClaseListView(AccessControlMixin, ListView):
    """
    Fase 11: pasa a ser la vista raíz del módulo (antes lo era el
    listado de ediciones) — ver academico/urls.py.
    """
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
        context["inscripciones"] = [
            InscripcionEstudianteDTO.from_model(i)
            for i in selectors.listar_inscripciones().filter(clase_id=self.kwargs["id_clase"])
        ]
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


# No existe ClaseDeleteView: las clases nunca se eliminan (Adenda 9,
# Decisión 2). No hay ruta, no hay vista, no hay template de
# confirmación — ausencia deliberada, no un olvido.


class InscripcionEstudianteCreateView(AccessControlMixin, CreateView):
    """
    Alta de una inscripción, siempre en el contexto de una Clase fija
    tomada de la URL (id_clase). Fase 11: antes el contexto fijo era
    la Edición (id_edicion); con la fusión (Adenda 9) es directamente
    la Clase.
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
        self.clase = selectors.obtener_clase_por_id(self.kwargs["id_clase"])
        if self.clase is None:
            raise Http404("Clase no encontrada.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["clase"] = self.clase
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = ClaseDTO.from_model(self.clase)
        return context

    def form_valid(self, form):
        try:
            services.crear_inscripcion(
                estudiante=form.cleaned_data["estudiante"],
                clase=self.clase,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("academico:clases_detalle", id_clase=self.clase.pk)


class InscripcionEstudianteUpdateView(AccessControlMixin, UpdateView):
    """
    Edición de una inscripción existente. La Clase queda fija (mismo
    motivo que en el alta): solo se puede cambiar el estudiante
    asignado.
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
        kwargs["clase"] = self.object.clase
        kwargs["excluir_inscripcion_id"] = self.object.pk
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = ClaseDTO.from_model(self.object.clase)
        return context

    def form_valid(self, form):
        try:
            services.actualizar_inscripcion(
                inscripcion=self.object,
                estudiante=form.cleaned_data["estudiante"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("academico:clases_detalle", id_clase=self.object.clase_id)


class InscripcionEstudianteDeleteView(AccessControlMixin, DeleteView):
    """
    Borra una inscripción puntual — no la clase. Sigue existiendo tal
    cual (una inscripción individual no está sujeta a la regla de "las
    clases nunca se eliminan").
    """
    template_name = "academico/inscripcion_confirm_delete.html"

    def get_object(self, queryset=None):
        inscripcion = selectors.obtener_inscripcion_por_id(self.kwargs["id_inscripcion"])
        if inscripcion is None:
            raise Http404("Inscripción no encontrada.")
        return inscripcion

    def get_success_url(self):
        return reverse("academico:clases_detalle", kwargs={"id_clase": self.object.clase_id})

    def form_valid(self, form):
        try:
            services.eliminar_inscripcion(inscripcion=self.object)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect(self.get_success_url())
