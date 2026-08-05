from django.http import Http404
from django.views.generic import DetailView, ListView

from apps.estudiantes import selectors
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