"""
Consultas de lectura reutilizables para apps.estudiantes.
Ninguna función de este módulo escribe en la base de datos.
"""
from django.db.models import Count, Q

from apps.estudiantes.models import Estudiante, Matrimonio

# Duplica intencionalmente el "2" de MAX_INTEGRANTES_POR_MATRIMONIO
# (services.py): el Selector no debe importar del Service (la capa
# de lectura es más básica que la de escritura, nunca al revés). La
# regla de negocio real se sigue validando únicamente en el Service;
# esto es solo para no ofrecer, en la UI, una opción inválida.
_MAX_INTEGRANTES_POR_MATRIMONIO_UI = 2


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


def listar_matrimonios_con_cupo(*, excluir_matrimonio_id=None):
    """
    Matrimonios con menos de dos integrantes, para poblar el <select>
    del formulario público de Estudiante. Uso exclusivo de
    presentación: no reemplaza la validación de capacidad que hace
    el Service al guardar (esa sigue siendo la autoridad real, y
    cubre además cualquier condición de carrera entre que se arma el
    formulario y se envía).

    Si `excluir_matrimonio_id` se indica, ese matrimonio se incluye
    igual aunque esté "lleno" — cubre el caso de edición, donde el
    estudiante que estás editando ya cuenta como uno de sus dos
    integrantes.
    """
    matrimonios = Matrimonio.objects.annotate(num_integrantes=Count("estudiantes"))
    filtro = Q(num_integrantes__lt=_MAX_INTEGRANTES_POR_MATRIMONIO_UI)
    if excluir_matrimonio_id is not None:
        filtro |= Q(pk=excluir_matrimonio_id)
    return matrimonios.filter(filtro).order_by("-fecha_matrimonio")