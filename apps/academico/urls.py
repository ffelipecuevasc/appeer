"""
Rutas propias de apps.academico, bajo su namespace 'academico'.
"""
from django.urls import path

from apps.academico import views

app_name = "academico"

urlpatterns = [
    path("", views.EdicionEscuelaListView.as_view(), name="ediciones_listado"),
    path("nueva/", views.EdicionEscuelaCreateView.as_view(), name="ediciones_crear"),
    path("<int:id_edicion>/", views.EdicionEscuelaDetailView.as_view(), name="ediciones_detalle"),
    path("<int:id_edicion>/editar/", views.EdicionEscuelaUpdateView.as_view(), name="ediciones_editar"),
    path("<int:id_edicion>/eliminar/", views.EdicionEscuelaDeleteView.as_view(), name="ediciones_eliminar"),

    path("clases/", views.ClaseListView.as_view(), name="clases_listado"),
    path("clases/nueva/", views.ClaseCreateView.as_view(), name="clases_crear"),
    path("clases/<int:id_clase>/", views.ClaseDetailView.as_view(), name="clases_detalle"),
    path("clases/<int:id_clase>/editar/", views.ClaseUpdateView.as_view(), name="clases_editar"),
    path("clases/<int:id_clase>/eliminar/", views.ClaseDeleteView.as_view(), name="clases_eliminar"),

    path("<int:id_edicion>/inscribir/", views.InscripcionEstudianteCreateView.as_view(), name="inscripciones_crear"),
    path("inscripciones/<int:id_inscripcion>/editar/", views.InscripcionEstudianteUpdateView.as_view(), name="inscripciones_editar"),
    path("inscripciones/<int:id_inscripcion>/eliminar/", views.InscripcionEstudianteDeleteView.as_view(), name="inscripciones_eliminar"),
]