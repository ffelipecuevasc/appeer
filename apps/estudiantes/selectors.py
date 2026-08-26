"""
Consultas de lectura reutilizables para apps.estudiantes.
Ninguna función de este módulo escribe en la base de datos.
"""
from django.db.models import Count, Q

from apps.estudiantes.models import Estudiante, Matrimonio, Responsabilidad

# Duplica intencionalmente el "2" de MAX_INTEGRANTES_POR_MATRIMONIO
# (services.py): el Selector no debe importar del Service (la capa
# de lectura es más básica que la de escritura, nunca al revés). La
# regla de negocio real se sigue validando únicamente en el Service;
# esto es solo para no ofrecer, en la UI, una opción inválida.
_MAX_INTEGRANTES_POR_MATRIMONIO_UI = 2


def listar_estudiantes(*, query=None):
    """
    Queryset base de estudiantes, con el matrimonio precargado.
    Si `query` viene informado (Subfase 6.2, buscador en vivo),
    filtra por coincidencia parcial case-insensitive en nombre o
    apellido. Parámetro opcional: el único call-site previo a esta
    subfase sigue funcionando sin pasar nada.
    """
    qs = (
        Estudiante.objects
        .select_related("matrimonio")
        # Fase 12: prefetch_related (no select_related — es una relación
        # muchos-a-muchos) para que pintar las pastillas de
        # responsabilidades en el listado no dispare una consulta por
        # estudiante. Sin esto, un listado de 38 alumnos haría 39
        # consultas en vez de 2.
        .prefetch_related("responsabilidades")
        .order_by("apellido", "nombre")
    )
    if query:
        qs = qs.filter(Q(nombre__icontains=query) | Q(apellido__icontains=query))
    return qs


def obtener_estudiante_por_id(id_estudiante):
    """Retorna un Estudiante por su PK, o None si no existe."""
    return (
        Estudiante.objects
        .select_related("matrimonio")
        .prefetch_related("responsabilidades")
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


# --- Responsabilidades (Fase 12, Subfase 12.3) -----------------------

def listar_responsabilidades():
    """
    Catálogo completo de responsabilidades, para poblar el widget de
    selección múltiple del formulario de Estudiante y el filtro del
    listado.
    """
    return Responsabilidad.objects.order_by("nombre")


def obtener_responsabilidad_por_id(id_responsabilidad):
    return Responsabilidad.objects.filter(pk=id_responsabilidad).first()


def listar_estudiantes_por_responsabilidad(id_responsabilidad):
    """
    Estudiantes que tienen una responsabilidad puntual.

    No lo consume ninguna pantalla todavía: se construye acá porque
    los módulos ya declarados en el Plan de Trabajo Maestro 2.0 lo
    van a necesitar — las oraciones de inicio y fin (Fase 18) suelen
    asignarse a ancianos, y las asignaciones de sala (Fase 19)
    distinguen por responsabilidad. Es el mismo criterio con el que
    la Fase 1 dejó selectors listos antes de tener vistas que los
    usaran.
    """
    return (
        Estudiante.objects
        .filter(responsabilidades__pk=id_responsabilidad)
        .select_related("matrimonio")
        .prefetch_related("responsabilidades")
        .order_by("apellido", "nombre")
    )
