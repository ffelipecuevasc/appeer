"""
Rutas propias de apps.academico, bajo su namespace 'academico'.

Fase 11 (Adenda 9): las rutas de ediciones desaparecen; el listado de
clases pasa a ser la raíz del módulo (antes lo era el de ediciones).
No existe ruta de borrado de clase (Decisión 2).
"""
from django.urls import path

from apps.academico import views

app_name = "academico"

urlpatterns = [
    path("", views.ClaseListView.as_view(), name="clases_listado"),
    path("nueva/", views.ClaseCreateView.as_view(), name="clases_crear"),
    path("<int:id_clase>/", views.ClaseDetailView.as_view(), name="clases_detalle"),
    path("<int:id_clase>/editar/", views.ClaseUpdateView.as_view(), name="clases_editar"),

    path("<int:id_clase>/inscribir/", views.InscripcionEstudianteCreateView.as_view(), name="inscripciones_crear"),
    path("inscripciones/<int:id_inscripcion>/editar/", views.InscripcionEstudianteUpdateView.as_view(), name="inscripciones_editar"),
    path("inscripciones/<int:id_inscripcion>/eliminar/", views.InscripcionEstudianteDeleteView.as_view(), name="inscripciones_eliminar"),
]
