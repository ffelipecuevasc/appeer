"""
Rutas propias de apps.estudiantes, bajo su namespace 'estudiantes'.
"""
from django.urls import path

from apps.estudiantes import views

app_name = "estudiantes"

urlpatterns = [
    path("", views.EstudianteListView.as_view(), name="listado"),
    path("nuevo/", views.EstudianteCreateView.as_view(), name="crear"),
    path("<int:id_estudiante>/", views.EstudianteDetailView.as_view(), name="detalle"),
    path("<int:id_estudiante>/editar/", views.EstudianteUpdateView.as_view(), name="editar"),
    path("<int:id_estudiante>/eliminar/", views.EstudianteDeleteView.as_view(), name="eliminar"),
]