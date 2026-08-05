"""
Rutas propias de apps.estudiantes, bajo su namespace 'estudiantes'.
"""
from django.urls import path

from apps.estudiantes import views

app_name = "estudiantes"

urlpatterns = [
    path("", views.EstudianteListView.as_view(), name="listado"),
    path("<int:id_estudiante>/", views.EstudianteDetailView.as_view(), name="detalle"),
]