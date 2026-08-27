"""
Rutas propias de apps.recordatorios, bajo su namespace 'recordatorios'.
"""
from django.urls import path

from apps.recordatorios import views

app_name = "recordatorios"

urlpatterns = [
    path("", views.LineaDeTiempoView.as_view(), name="linea_tiempo"),
    path("clase/<int:id_clase>/nuevo/", views.RecordatorioCreateView.as_view(), name="crear"),
    path("clase/<int:id_clase>/form/", views.RecordatorioFormParcialView.as_view(), name="form_nuevo"),
    path("clase/<int:id_clase>/<int:id_recordatorio>/form/", views.RecordatorioFormParcialView.as_view(), name="form_editar"),
    path("clase/<int:id_clase>/<int:id_recordatorio>/editar/", views.RecordatorioUpdateView.as_view(), name="editar"),
    path("clase/<int:id_clase>/<int:id_recordatorio>/completar/", views.RecordatorioToggleView.as_view(), name="completar"),
    path("clase/<int:id_clase>/<int:id_recordatorio>/eliminar/", views.RecordatorioDeleteView.as_view(), name="eliminar"),
]
