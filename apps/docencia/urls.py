"""
Rutas propias de apps.docencia, bajo su namespace 'docencia'.
"""
from django.urls import path

from apps.docencia import views

app_name = "docencia"

urlpatterns = [
    path("", views.InstructorListView.as_view(), name="listado"),
    path("nuevo/", views.InstructorCreateView.as_view(), name="crear"),
    path("<int:id_instructor>/", views.InstructorDetailView.as_view(), name="detalle"),
    path("<int:id_instructor>/editar/", views.InstructorUpdateView.as_view(), name="editar"),
    path("<int:id_instructor>/eliminar/", views.InstructorDeleteView.as_view(), name="eliminar"),

    path("temas/", views.TemaListView.as_view(), name="temas_listado"),
    path("temas/nuevo/", views.TemaCreateView.as_view(), name="temas_crear"),
    path("temas/<int:id_tema>/editar/", views.TemaUpdateView.as_view(), name="temas_editar"),
    path("temas/<int:id_tema>/alternar-estado/", views.TemaToggleEstadoView.as_view(), name="temas_alternar_estado"),
]