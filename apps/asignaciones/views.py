"""
Vistas HTTP delgadas de apps.asignaciones. Toda regla de negocio vive
en selectors.py (lectura) o services.py (escritura).
"""
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.academico import selectors as academico_selectors
from apps.academico.serializers import ClaseDTO
from apps.asignaciones import selectors, services
from apps.asignaciones.forms import ParejaForm
from apps.asignaciones.serializers import ParejaDTO
from core.mixins import AccessControlMixin


class ParejaListView(AccessControlMixin, ListView):
    """
    Listado general de apps.asignaciones (Subfase 5.2, registrado en
    Adenda 7): a diferencia de ParejaPorClaseListView, no depende de
    una Clase en la URL. Reutiliza el mismo Selector/Serializer ya
    existentes desde la Fase 4 (selectors.listar_parejas /
    ParejaDTO), sin alterarlos.
    """
    template_name = "asignaciones/pareja_list.html"
    context_object_name = "parejas"
    paginate_by = 20

    def get_queryset(self):
        return selectors.listar_parejas()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parejas"] = [ParejaDTO.from_model(p) for p in context["parejas"]]
        return context


class ParejaPorClaseListView(AccessControlMixin, ListView):
    """
    Vista de asignación por clase (entregable explícito de la Subfase
    4.4 del Plan de Trabajo): lista las parejas de una Clase puntual,
    tomada de la URL.
    """
    template_name = "asignaciones/pareja_por_clase.html"
    context_object_name = "parejas"

    def dispatch(self, request, *args, **kwargs):
        # Ver AccessControlMixin.bloqueo_si_no_autenticado (Subfase 8.2):
        # esta vista define su propio dispatch(), el guard explícito es
        # necesario para que la sesión se valide ANTES de la consulta.
        bloqueo = self.bloqueo_si_no_autenticado(request)
        if bloqueo is not None:
            return bloqueo
        self.clase = academico_selectors.obtener_clase_por_id(self.kwargs["id_clase"])
        if self.clase is None:
            raise Http404("Clase no encontrada.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return selectors.listar_parejas_por_clase(self.kwargs["id_clase"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parejas"] = [ParejaDTO.from_model(p) for p in context["parejas"]]
        context["clase"] = ClaseDTO.from_model(self.clase)
        return context


class ParejaCreateView(AccessControlMixin, CreateView):
    """
    Subfase 6.4: ante una petición fetch de escritura (mismo header
    X-Requested-With que detecta AjaxRequestMixin), responde con un
    fragmento en vez de un redirect/página completa — de confirmación
    si se creó (201) o del formulario con errores si no (422). Sin
    JS, el comportamiento es exactamente el de antes: redirect a la
    clase si se creó, página completa con errores si no.

    Solo esta vista (creación). ParejaUpdateView queda fuera del
    alcance de esta subfase — el Plan de Trabajo la especifica para
    "vista de creación de pareja" puntualmente.
    """
    form_class = ParejaForm
    template_name = "asignaciones/pareja_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Ver AccessControlMixin.bloqueo_si_no_autenticado (Subfase 8.2):
        # esta vista define su propio dispatch(), el guard explícito es
        # necesario para que la sesión se valide ANTES de la consulta.
        bloqueo = self.bloqueo_si_no_autenticado(request)
        if bloqueo is not None:
            return bloqueo
        self.clase = academico_selectors.obtener_clase_por_id(self.kwargs["id_clase"])
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
            pareja = services.crear_pareja(
                clase=self.clase,
                estudiante_1=form.cleaned_data["estudiante_1"],
                estudiante_2=form.cleaned_data["estudiante_2"],
                programacion=form.cleaned_data.get("programacion"),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        if self.is_ajax():
            context = self.get_context_data(form=form)
            context["pareja"] = ParejaDTO.from_model(pareja)
            return render(
                self.request, "asignaciones/_pareja_confirmacion.html", context, status=201
            )
        return redirect("asignaciones:parejas_por_clase", id_clase=self.clase.pk)

    def form_invalid(self, form):
        if self.is_ajax():
            context = self.get_context_data(form=form)
            return render(
                self.request, "asignaciones/_pareja_form_inner.html", context, status=422
            )
        return super().form_invalid(form)


class ParejaDetailView(AccessControlMixin, DetailView):
    template_name = "asignaciones/pareja_detail.html"
    context_object_name = "pareja"

    def get_object(self, queryset=None):
        pareja = selectors.obtener_pareja_por_id(self.kwargs["id_pareja"])
        if pareja is None:
            raise Http404("Pareja no encontrada.")
        return pareja

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pareja"] = ParejaDTO.from_model(context["pareja"])
        return context


class ParejaUpdateView(AccessControlMixin, UpdateView):
    form_class = ParejaForm
    template_name = "asignaciones/pareja_form.html"

    def get_object(self, queryset=None):
        pareja = selectors.obtener_pareja_por_id(self.kwargs["id_pareja"])
        if pareja is None:
            raise Http404("Pareja no encontrada.")
        return pareja

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["clase"] = self.object.clase
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = ClaseDTO.from_model(self.object.clase)
        return context

    def form_valid(self, form):
        try:
            services.actualizar_pareja(
                pareja=self.object,
                estudiante_1=form.cleaned_data["estudiante_1"],
                estudiante_2=form.cleaned_data["estudiante_2"],
                programacion=form.cleaned_data.get("programacion"),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("asignaciones:parejas_por_clase", id_clase=self.object.clase_id)


class ParejaDeleteView(AccessControlMixin, DeleteView):
    template_name = "asignaciones/pareja_confirm_delete.html"

    def get_object(self, queryset=None):
        pareja = selectors.obtener_pareja_por_id(self.kwargs["id_pareja"])
        if pareja is None:
            raise Http404("Pareja no encontrada.")
        return pareja

    def get_success_url(self):
        return reverse("asignaciones:parejas_por_clase", kwargs={"id_clase": self.object.clase_id})

    def form_valid(self, form):
        try:
            services.eliminar_pareja(pareja=self.object)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect(self.get_success_url())
