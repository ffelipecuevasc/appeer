"""
Consultas de lectura reutilizables para apps.estudiantes.
Ninguna función de este módulo escribe en la base de datos.
"""
from apps.estudiantes.models import Estudiante


def listar_estudiantes():
    """Queryset base de estudiantes, con el matrimonio precargado."""
    return Estudiante.objects.select_related("matrimonio").order_by("apellido", "nombre")


def obtener_estudiante_por_id(id_estudiante):
    """Retorna un Estudiante por su PK, o None si no existe."""
    return (
        Estudiante.objects
        .select_related("matrimonio")
        .filter(pk=id_estudiante)
        .first()
    )


def listar_estudiantes_por_matrimonio(id_matrimonio):
    """Estudiantes asociados a un matrimonio dado (0, 1 o 2 resultados)."""
    return Estudiante.objects.filter(matrimonio_id=id_matrimonio)