"""
Rutas propias de apps.estudiantes, bajo su namespace 'estudiantes'.
"""
from django.urls import path

from apps.estudiantes import views

app_name = "estudiantes"

urlpatterns = [
    path("", views.EstudianteListView.as_view(), name="listado"),
    path("nuevo/", views.EstudianteCreateView.as_view(), name="crear"),

    # Catálogo de responsabilidades (Adenda 11). Antes de las rutas
    # con <int:id_estudiante> para que "responsabilidades" no se
    # confunda con un id.
    path("responsabilidades/", views.ResponsabilidadListView.as_view(), name="responsabilidades_listado"),
    path("responsabilidades/nueva/", views.ResponsabilidadCreateView.as_view(), name="responsabilidades_crear"),
    path("responsabilidades/<int:id_responsabilidad>/editar/", views.ResponsabilidadUpdateView.as_view(), name="responsabilidades_editar"),
    path("responsabilidades/<int:id_responsabilidad>/alternar-estado/", views.ResponsabilidadToggleView.as_view(), name="responsabilidades_alternar_estado"),

    path("<int:id_estudiante>/", views.EstudianteDetailView.as_view(), name="detalle"),
    path("<int:id_estudiante>/editar/", views.EstudianteUpdateView.as_view(), name="editar"),
    path("<int:id_estudiante>/eliminar/", views.EstudianteDeleteView.as_view(), name="eliminar"),
]