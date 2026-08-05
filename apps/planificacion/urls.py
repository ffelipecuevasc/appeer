"""
Rutas propias de apps.planificacion, bajo su namespace 'planificacion'.
"""
from django.urls import path

from apps.planificacion import views

app_name = "planificacion"

urlpatterns = [
    path("", views.ProgramacionClaseListView.as_view(), name="programaciones_listado"),
    path("nueva/", views.ProgramacionClaseCreateView.as_view(), name="programaciones_crear"),
    path("<int:id_programacion>/", views.ProgramacionClaseDetailView.as_view(), name="programaciones_detalle"),
    path("<int:id_programacion>/editar/", views.ProgramacionClaseUpdateView.as_view(), name="programaciones_editar"),
    path("<int:id_programacion>/eliminar/", views.ProgramacionClaseDeleteView.as_view(), name="programaciones_eliminar"),
]