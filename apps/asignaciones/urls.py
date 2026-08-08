"""
Rutas propias de apps.asignaciones, bajo su namespace 'asignaciones'.
"""
from django.urls import path

from apps.asignaciones import views

app_name = "asignaciones"

urlpatterns = [
    path("", views.ParejaListView.as_view(), name="listado"),  # <- NUEVA
    path("clases/<int:id_clase>/", views.ParejaPorClaseListView.as_view(), name="parejas_por_clase"),
    path("clases/<int:id_clase>/nueva/", views.ParejaCreateView.as_view(), name="parejas_crear"),
    path("parejas/<int:id_pareja>/", views.ParejaDetailView.as_view(), name="parejas_detalle"),
    path("parejas/<int:id_pareja>/editar/", views.ParejaUpdateView.as_view(), name="parejas_editar"),
    path("parejas/<int:id_pareja>/eliminar/", views.ParejaDeleteView.as_view(), name="parejas_eliminar"),
]