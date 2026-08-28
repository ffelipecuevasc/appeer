"""
Rutas propias de apps.recordatorios, bajo su namespace 'recordatorios'.
"""
from django.urls import path

from apps.recordatorios import views

app_name = "recordatorios"

urlpatterns = [
    path("", views.LineaDeTiempoView.as_view(), name="linea_tiempo"),

    # Catálogo de tipos (Adenda 11). Va antes de las rutas con
    # <int:id_clase> para que "tipos" nunca se confunda con un id.
    path("tipos/", views.TipoRecordatorioListView.as_view(), name="tipos_listado"),
    path("tipos/nuevo/", views.TipoRecordatorioCreateView.as_view(), name="tipos_crear"),
    path("tipos/<int:id_tipo>/editar/", views.TipoRecordatorioUpdateView.as_view(), name="tipos_editar"),
    path("tipos/<int:id_tipo>/alternar-estado/", views.TipoRecordatorioToggleView.as_view(), name="tipos_alternar_estado"),

    path("clase/<int:id_clase>/nuevo/", views.RecordatorioCreateView.as_view(), name="crear"),
    path("clase/<int:id_clase>/form/", views.RecordatorioFormParcialView.as_view(), name="form_nuevo"),
    path("clase/<int:id_clase>/<int:id_recordatorio>/form/", views.RecordatorioFormParcialView.as_view(), name="form_editar"),
    path("clase/<int:id_clase>/<int:id_recordatorio>/editar/", views.RecordatorioUpdateView.as_view(), name="editar"),
    path("clase/<int:id_clase>/<int:id_recordatorio>/completar/", views.RecordatorioToggleView.as_view(), name="completar"),
    path("clase/<int:id_clase>/<int:id_recordatorio>/eliminar/", views.RecordatorioDeleteView.as_view(), name="eliminar"),
]
