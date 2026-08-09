from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.docencia import selectors, services
from apps.docencia.forms import InstructorForm, TemaForm
from apps.docencia.serializers import InstructorDTO, TemaDTO
from core.mixins import AccessControlMixin


class InstructorListView(AccessControlMixin, ListView):
    template_name = "docencia/instructor_list.html"
    context_object_name = "instructores"
    paginate_by = 20

    def get_queryset(self):
        return selectors.listar_instructores()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["instructores"] = [
            InstructorDTO.from_model(i) for i in context["instructores"]
        ]
        return context


class InstructorDetailView(AccessControlMixin, DetailView):
    template_name = "docencia/instructor_detail.html"
    context_object_name = "instructor"

    def get_object(self, queryset=None):
        instructor = selectors.obtener_instructor_por_id(self.kwargs["id_instructor"])
        if instructor is None:
            raise Http404("Instructor no encontrado.")
        return instructor

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["instructor"] = InstructorDTO.from_model(context["instructor"])
        return context


class InstructorCreateView(AccessControlMixin, CreateView):
    form_class = InstructorForm
    template_name = "docencia/instructor_form.html"

    def form_valid(self, form):
        try:
            instructor = services.crear_instructor(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("docencia:detalle", id_instructor=instructor.pk)


class InstructorUpdateView(AccessControlMixin, UpdateView):
    form_class = InstructorForm
    template_name = "docencia/instructor_form.html"

    def get_object(self, queryset=None):
        instructor = selectors.obtener_instructor_por_id(self.kwargs["id_instructor"])
        if instructor is None:
            raise Http404("Instructor no encontrado.")
        return instructor

    def form_valid(self, form):
        try:
            instructor = services.actualizar_instructor(instructor=self.object, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("docencia:detalle", id_instructor=instructor.pk)


class InstructorDeleteView(AccessControlMixin, DeleteView):
    template_name = "docencia/instructor_confirm_delete.html"
    success_url = reverse_lazy("docencia:listado")

    def get_object(self, queryset=None):
        instructor = selectors.obtener_instructor_por_id(self.kwargs["id_instructor"])
        if instructor is None:
            raise Http404("Instructor no encontrado.")
        return instructor

    def form_valid(self, form):
        try:
            services.eliminar_instructor(instructor=self.object)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect(self.success_url)


class TemaListView(AccessControlMixin, ListView):
    template_name = "docencia/tema_list.html"
    context_object_name = "temas"
    paginate_by = 20

    def get_queryset(self):
        return selectors.listar_temas()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["temas"] = [TemaDTO.from_model(t) for t in context["temas"]]
        return context


class TemaCreateView(AccessControlMixin, CreateView):
    form_class = TemaForm
    template_name = "docencia/tema_form.html"

    def form_valid(self, form):
        try:
            tema = services.crear_tema(**form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("docencia:temas_listado")


class TemaUpdateView(AccessControlMixin, UpdateView):
    form_class = TemaForm
    template_name = "docencia/tema_form.html"

    def get_object(self, queryset=None):
        tema = selectors.obtener_tema_por_id(self.kwargs["id_tema"])
        if tema is None:
            raise Http404("Tema no encontrado.")
        return tema

    def form_valid(self, form):
        try:
            tema = services.actualizar_tema(tema=self.object, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        return redirect("docencia:temas_listado")


class TemaToggleEstadoView(AccessControlMixin, View):
    """
    Alterna activo/inactivo mediante un POST simple sin JS, para que
    quede correctamente preparado como progressive enhancement de cara
    a la Fase 6 (donde este mismo botón se podrá potenciar con fetch
    sin cambiar el contrato de la URL).
    """
    http_method_names = ["post"]

    def post(self, request, id_tema):
        tema = selectors.obtener_tema_por_id(id_tema)
        if tema is None:
            raise Http404("Tema no encontrado.")
        if tema.activo:
            services.desactivar_tema(tema=tema)
        else:
            services.activar_tema(tema=tema)
        return redirect("docencia:temas_listado")