"""
Vistas HTTP delgadas de apps.recordatorios.

Cada vista de escritura sirve a DOS caminos con el mismo código:
  - Sin JavaScript: página propia con su formulario, redirect al
    terminar. Es el camino de respaldo, requisito no negociable de la
    mejora progresiva (criterio de aceptación de la Fase 6).
  - Con JavaScript: la misma vista detecta la petición parcial
    (AccessControlMixin hereda is_ajax) y responde un FRAGMENTO —la
    tarjeta actualizada o el formulario con errores— en vez de la
    página completa.

Que ambos caminos compartan la misma vista y el mismo formulario evita
el error clásico de tener dos implementaciones que se desincronizan: si
una regla cambia, cambia para los dos a la vez.
"""
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from apps.academico import selectors as academico_selectors
from apps.recordatorios import selectors, services
from apps.recordatorios.forms import RecordatorioForm, TipoRecordatorioForm
from apps.recordatorios.serializers import RecordatorioDTO
from core.mixins import AccessControlMixin


class _ClaseDesdeUrlMixin(AccessControlMixin):
    """
    Resuelve la clase de la URL y bloquea si no hay sesión.

    El guard explícito es necesario porque estas vistas definen su
    propio dispatch(): sin él, una petición sin sesión con un id
    inexistente recibiría un 404 antes que el redirect al login (mismo
    problema que la Subfase 8.2 detectó en apps.academico y
    apps.asignaciones).
    """

    def dispatch(self, request, *args, **kwargs):
        bloqueo = self.bloqueo_si_no_autenticado(request)
        if bloqueo is not None:
            return bloqueo
        self.clase = academico_selectors.obtener_clase_por_id(self.kwargs["id_clase"])
        if self.clase is None:
            raise Http404("Clase no encontrada.")
        return super().dispatch(request, *args, **kwargs)


def _fragmento_tarjeta(request, recordatorio, *, vencida):
    """Renderiza una sola tarjeta, para devolverla por fetch."""
    return render(
        request,
        "recordatorios/_tarjeta.html",
        {"tarea": RecordatorioDTO.from_model(recordatorio, vencida=vencida)},
    )


def _esta_vencida(recordatorio):
    """
    Comparación SIEMPRE en el servidor (Subfase 14.8). Ver el comentario
    de RecordatorioDTO.vencida.
    """
    from datetime import date
    return (not recordatorio.completado) and recordatorio.fecha < date.today()


class LineaDeTiempoView(AccessControlMixin, TemplateView):
    """
    Subfase 14.4: la línea de tiempo. Exige elegir una clase antes de
    mostrar nada, igual que el listado de estudiantes de la Fase 13 —
    cada turma tiene su propio cronograma y un listado global no
    significaría nada.
    """
    template_name = "recordatorios/linea_tiempo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id_clase = self.request.GET.get("clase", "").strip()

        context["clases"] = academico_selectors.listar_clases()
        context["clase_seleccionada"] = id_clase
        context["clase"] = None
        context["semanas"] = None

        if not id_clase:
            return context

        clase = academico_selectors.obtener_clase_por_id(id_clase)
        if clase is None:
            raise Http404("Clase no encontrada.")
        context["clase"] = clase

        bloques = selectors.agrupar_por_semana(selectors.listar_por_clase(clase.pk))
        # El DTO se arma acá: la plantilla recibe datos listos para
        # pintar, incluido el flag `vencida` ya calculado.
        context["semanas"] = [
            {
                **bloque,
                "tareas": [
                    RecordatorioDTO.from_model(r, vencida=v) for r, v in bloque["tareas"]
                ],
            }
            for bloque in bloques
        ]
        context["total"] = sum(b["total"] for b in bloques)
        context["vencidas"] = sum(b["vencidas"] for b in bloques)
        return context


class RecordatorioCreateView(_ClaseDesdeUrlMixin, CreateView):
    form_class = RecordatorioForm
    template_name = "recordatorios/recordatorio_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["clase"] = self.clase
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = self.clase
        return context

    def form_valid(self, form):
        try:
            recordatorio = services.crear_recordatorio(clase=self.clase, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        if self.is_ajax():
            return _fragmento_tarjeta(
                self.request, recordatorio, vencida=_esta_vencida(recordatorio)
            )
        return redirect(f"/recordatorios/?clase={self.clase.pk}")

    def form_invalid(self, form):
        if self.is_ajax():
            # 422 y no 400: el contrato que la Fase 6 ya estableció
            # para "la petición llegó bien pero los datos no pasan las
            # reglas de negocio". pareja-form.js ya lo interpreta así.
            respuesta = render(
                self.request, "recordatorios/_form_inner.html",
                {"form": form, "clase": self.clase},
            )
            respuesta.status_code = 422
            return respuesta
        return super().form_invalid(form)


class RecordatorioUpdateView(_ClaseDesdeUrlMixin, UpdateView):
    form_class = RecordatorioForm
    template_name = "recordatorios/recordatorio_form.html"

    def get_object(self, queryset=None):
        recordatorio = selectors.obtener_por_id(self.kwargs["id_recordatorio"])
        if recordatorio is None:
            raise Http404("Recordatorio no encontrado.")
        return recordatorio

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["clase"] = self.clase
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = self.clase
        return context

    def form_valid(self, form):
        try:
            recordatorio = services.actualizar_recordatorio(
                recordatorio=self.object, **form.cleaned_data
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        if self.is_ajax():
            return _fragmento_tarjeta(
                self.request, recordatorio, vencida=_esta_vencida(recordatorio)
            )
        return redirect(f"/recordatorios/?clase={self.clase.pk}")

    def form_invalid(self, form):
        if self.is_ajax():
            respuesta = render(
                self.request, "recordatorios/_form_inner.html",
                {"form": form, "clase": self.clase, "object": self.object},
            )
            respuesta.status_code = 422
            return respuesta
        return super().form_invalid(form)


class RecordatorioToggleView(_ClaseDesdeUrlMixin, View):
    """
    Subfase 14.7: marcar/desmarcar completado.

    Solo POST: cambia el estado del servidor, así que un GET no debe
    poder dispararlo (el mismo criterio por el que /logout/ es POST-only
    desde la Subfase 8.1).
    """

    def post(self, request, *args, **kwargs):
        recordatorio = selectors.obtener_por_id(self.kwargs["id_recordatorio"])
        if recordatorio is None:
            raise Http404("Recordatorio no encontrado.")
        services.alternar_completado(recordatorio=recordatorio)
        if self.is_ajax():
            return _fragmento_tarjeta(
                request, recordatorio, vencida=_esta_vencida(recordatorio)
            )
        return redirect(f"/recordatorios/?clase={self.clase.pk}")


class RecordatorioDeleteView(_ClaseDesdeUrlMixin, DeleteView):
    template_name = "recordatorios/recordatorio_confirm_delete.html"

    def get_object(self, queryset=None):
        recordatorio = selectors.obtener_por_id(self.kwargs["id_recordatorio"])
        if recordatorio is None:
            raise Http404("Recordatorio no encontrado.")
        return recordatorio

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = self.clase
        return context

    def form_valid(self, form):
        services.eliminar_recordatorio(recordatorio=self.object)
        if self.is_ajax():
            # 204 Sin Contenido: la tarjeta se borró, no hay fragmento
            # que devolver. El módulo JS la quita del DOM al recibirlo.
            return HttpResponse(status=204)
        return redirect(f"/recordatorios/?clase={self.clase.pk}")


class RecordatorioFormParcialView(_ClaseDesdeUrlMixin, View):
    """
    Devuelve SOLO el formulario de una tarjeta, para que el módulo JS
    la convierta en formulario en el mismo lugar donde está (Subfase
    14.6) sin tener que construir el HTML del formulario en JavaScript.

    Es lectura, así que responde a GET. Que el formulario lo renderice
    Django y no el navegador significa que hay una sola definición de
    los campos: si mañana se agrega uno, aparece en los dos caminos
    solo.
    """

    def get(self, request, *args, **kwargs):
        id_recordatorio = self.kwargs.get("id_recordatorio")
        instancia = None
        if id_recordatorio is not None:
            instancia = selectors.obtener_por_id(id_recordatorio)
            if instancia is None:
                raise Http404("Recordatorio no encontrado.")
        form = RecordatorioForm(instance=instancia, clase=self.clase)
        return render(
            request, "recordatorios/_form_inner.html",
            {"form": form, "clase": self.clase, "object": instancia},
        )


# --- Catálogo de tipos (Adenda 11) ----------------------------------
# Reemplaza la gestión vía panel de administración de Django. Sigue el
# mismo patrón que apps.docencia usa para Tema: listado, alta, edición
# y alternar estado. Sin borrado, a propósito (ver services).

class TipoRecordatorioListView(AccessControlMixin, ListView):
    template_name = "recordatorios/tipo_list.html"
    context_object_name = "tipos"

    def get_queryset(self):
        return selectors.listar_tipos()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # El conteo de uso se resuelve acá, no en la plantilla: así la
        # vista entrega datos listos para pintar y el template no
        # dispara una consulta por fila.
        context["tipos"] = [
            {"tipo": tipo, "en_uso": selectors.contar_recordatorios_por_tipo(tipo.pk)}
            for tipo in context["tipos"]
        ]
        return context


class TipoRecordatorioCreateView(AccessControlMixin, CreateView):
    form_class = TipoRecordatorioForm
    template_name = "recordatorios/tipo_form.html"

    def form_valid(self, form):
        try:
            services.crear_tipo(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("recordatorios:tipos_listado")


class TipoRecordatorioUpdateView(AccessControlMixin, UpdateView):
    form_class = TipoRecordatorioForm
    template_name = "recordatorios/tipo_form.html"

    def get_object(self, queryset=None):
        tipo = selectors.obtener_tipo_por_id(self.kwargs["id_tipo"])
        if tipo is None:
            raise Http404("Tipo no encontrado.")
        return tipo

    def form_valid(self, form):
        try:
            services.actualizar_tipo(tipo=self.object, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("recordatorios:tipos_listado")


class TipoRecordatorioToggleView(AccessControlMixin, View):
    """POST-only: cambia estado, así que un GET no debe dispararlo."""
    http_method_names = ["post"]

    def post(self, request, id_tipo):
        tipo = selectors.obtener_tipo_por_id(id_tipo)
        if tipo is None:
            raise Http404("Tipo no encontrado.")
        services.alternar_activo_tipo(tipo=tipo)
        return redirect("recordatorios:tipos_listado")
