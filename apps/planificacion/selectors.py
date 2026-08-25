"""
Consultas de lectura reutilizables para apps.planificacion.
Ninguna función de este módulo escribe en la base de datos.
"""
from apps.docencia.models import Instructor, Tema
from apps.planificacion.models import ProgramacionClase


def listar_programaciones():
    """Queryset base de programaciones, con clase/instructor/tema precargados."""
    return ProgramacionClase.objects.select_related("clase", "instructor", "tema")


def obtener_programacion_por_id(id_programacion):
    return (
        ProgramacionClase.objects
        .select_related("clase", "instructor", "tema")
        .filter(pk=id_programacion)
        .first()
    )


def listar_programaciones_por_clase(id_clase):
    """
    Horario completo de una clase, ordenado por semana/día/aula (orden
    ya definido en Meta.ordering).

    Fase 11: antes se llamaba listar_programaciones_por_edicion y
    filtraba por edicion_id. Con ProgramacionClase.clase como FK
    directa (Adenda 9), el filtro es igual de directo, solo que ahora
    describe lo que realmente es: el horario de UNA clase, no de una
    edición que la contenía.
    """
    return listar_programaciones().filter(clase_id=id_clase)


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
    disponibilidad para Instructor.
    """
    return Instructor.objects.order_by("apellido", "nombre")
