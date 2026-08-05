"""
Consultas de lectura reutilizables para apps.planificacion.
Ninguna función de este módulo escribe en la base de datos.
"""
from apps.docencia.models import Instructor, Tema
from apps.planificacion.models import ProgramacionClase


def listar_programaciones():
    """Queryset base de programaciones, con edición/instructor/tema precargados."""
    return ProgramacionClase.objects.select_related("edicion", "instructor", "tema")


def obtener_programacion_por_id(id_programacion):
    return (
        ProgramacionClase.objects
        .select_related("edicion", "instructor", "tema")
        .filter(pk=id_programacion)
        .first()
    )


def listar_programaciones_por_edicion(id_edicion):
    """
    Horario completo de una edición, ordenado por semana/día/aula
    (orden ya definido en Meta.ordering) — la consulta de horario que
    pide explícitamente la Subfase 3.2 del Plan de Trabajo.
    """
    return listar_programaciones().filter(edicion_id=id_edicion)


def listar_temas_disponibles(*, incluir_tema_id=None):
    """
    Temas con activo=True, para poblar el <select> del formulario de
    ProgramacionClase. Si `incluir_tema_id` se indica (edición de una
    programación existente), se incluye también ese tema aunque esté
    inactivo — para no romper el formulario de una programación cuyo
    tema fue desactivado después de haberse creado. La validación real
    de disponibilidad sigue en el Service, que solo bloquea *asignar*
    un tema inactivo, no mantener uno ya asignado.
    """
    from django.db.models import Q

    filtro = Q(activo=True)
    if incluir_tema_id is not None:
        filtro |= Q(pk=incluir_tema_id)
    return Tema.objects.filter(filtro).order_by("titulo_tema")


def listar_instructores():
    """
    Instructores para el <select> del formulario. Sin filtro
    adicional: el script SQL auditado no define ningún campo de
    disponibilidad para Instructor (decisión ya registrada en el
    Paso 0 de esta fase — "disponible" solo aplica a Tema).
    """
    return Instructor.objects.order_by("apellido", "nombre")