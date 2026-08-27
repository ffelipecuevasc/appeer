"""
Vistas HTTP delgadas de apps.estudiantes. Toda regla de negocio vive
en selectors.py (lectura) o services.py (escritura); estas vistas
solo orquestan.
"""
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView

from apps.academico import selectors as academico_selectors
from apps.estudiantes import selectors, services
from apps.estudiantes.forms import EstudianteForm
from apps.estudiantes.serializers import EstudianteDTO
from core.mixins import AccessControlMixin


class EstudianteListView(AccessControlMixin, TemplateView):
    """
    Listado de estudiantes agrupado en tarjetas (Fase 13).

    Cambios respecto a la versión de la Fase 6:

    - Deja de ser un ListView. La pantalla ya no muestra una lista
      plana paginada sino TRES grupos (matrimonios, hombres solteros,
      mujeres solteras); la paginación de Django, que opera sobre un
      queryset único, no tiene forma de repartir páginas entre grupos
      sin cortarlos por la mitad. Por eso se pagina por CLASE —que es
      la unidad natural, unas decenas de alumnos— en vez de por
      cantidad de filas.

    - Exige elegir una clase antes de mostrar nada (?clase=...).
      Decisión del cliente: con dos turmas da igual, pero en dos años
      serán cientos de estudiantes y un listado global deja de ser
      útil. Sin ?clase= la página muestra el selector y nada más.

    - La búsqueda por ?q= sigue funcionando exactamente igual
      (Subfase 6.2) y sigue respondiendo un fragmento parcial ante
      peticiones AJAX — solo cambió el fragmento: antes filas de
      tabla, ahora los tres grupos de tarjetas.
    """
    template_name = "estudiantes/estudiante_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        id_clase = self.request.GET.get("clase", "").strip()

        context["query"] = query
        context["clases"] = academico_selectors.listar_clases()
        context["clase_seleccionada"] = id_clase
        context["clase"] = None
        context["grupos"] = None

        if not id_clase:
            # Sin clase elegida no se consulta nada: es el estado
            # "elige una clase", no un listado vacío.
            return context

        clase = academico_selectors.obtener_clase_por_id(id_clase)
        if clase is None:
            raise Http404("Clase no encontrada.")
        context["clase"] = clase

        estudiantes = selectors.listar_estudiantes_de_clase(clase.pk, query=query or None)
        agrupados = selectors.agrupar_estudiantes(estudiantes)

        # El DTO se arma acá, no en el template: la plantilla recibe
        # datos listos para pintar (patrón del proyecto).
        context["grupos"] = {
            "matrimonios": [
                [EstudianteDTO.from_model(e) for e in conyuges]
                for conyuges in agrupados["matrimonios"]
            ],
            "hombres_solteros": [
                EstudianteDTO.from_model(e) for e in agrupados["hombres_solteros"]
            ],
            "mujeres_solteras": [
                EstudianteDTO.from_model(e) for e in agrupados["mujeres_solteras"]
            ],
        }
        context["total"] = (
            len(context["grupos"]["matrimonios"]) * 2
            + len(context["grupos"]["hombres_solteros"])
            + len(context["grupos"]["mujeres_solteras"])
        )
        return context

    def get_template_names(self):
        if self.is_ajax():
            return ["estudiantes/_estudiante_grupos.html"]
        return [self.template_name]


class EstudianteDetailView(AccessControlMixin, DetailView):
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


class EstudianteCreateView(AccessControlMixin, CreateView):
    form_class = EstudianteForm
    template_name = "estudiantes/estudiante_form.html"

    def form_valid(self, form):
        try:
            estudiante = services.crear_estudiante(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("estudiantes:detalle", id_estudiante=estudiante.pk)


class EstudianteUpdateView(AccessControlMixin, UpdateView):
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


class EstudianteDeleteView(AccessControlMixin, DeleteView):
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
