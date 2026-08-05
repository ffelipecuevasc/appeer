"""
Consultas de lectura reutilizables para apps.academico.
Ninguna función de este módulo escribe en la base de datos.
"""
from apps.academico.models import Clase, EdicionEscuela, InscripcionEstudiante


def listar_ediciones():
    """Queryset base de ediciones, más recientes primero."""
    return EdicionEscuela.objects.order_by("-fecha_inicio", "nombre_edicion")


def obtener_edicion_por_id(id_edicion):
    return EdicionEscuela.objects.filter(pk=id_edicion).first()


def listar_clases():
    return Clase.objects.order_by("-anio", "nombre")


def obtener_clase_por_id(id_clase):
    return Clase.objects.filter(pk=id_clase).first()


def listar_inscripciones():
    """Queryset base de inscripciones, con estudiante/edición/clase precargados."""
    return (
        InscripcionEstudiante.objects
        .select_related("estudiante", "edicion", "clase")
        .order_by("-edicion__fecha_inicio", "estudiante__apellido")
    )


def obtener_inscripcion_por_id(id_inscripcion):
    return (
        InscripcionEstudiante.objects
        .select_related("estudiante", "edicion", "clase")
        .filter(pk=id_inscripcion)
        .first()
    )


def listar_estudiantes_disponibles_para_edicion(id_edicion, *, excluir_inscripcion_id=None):
    """
    Estudiantes que todavía NO están inscritos en `id_edicion`, para
    poblar el <select> del formulario de InscripcionEstudiante. Uso
    exclusivo de presentación (UX preventiva): no reemplaza la
    validación real de "no doble inscripción", que sigue viviendo
    exclusivamente en el Service — mismo patrón que
    listar_matrimonios_con_cupo en apps.estudiantes.

    Si `excluir_inscripcion_id` se indica, se ignora esa inscripción
    puntual al calcular quién ya está inscrito — cubre el caso de
    edición, donde el estudiante de la inscripción que estás editando
    no debe autoexcluirse de su propia lista de opciones.
    """
    from apps.estudiantes.models import Estudiante

    inscritos_ids = InscripcionEstudiante.objects.filter(edicion_id=id_edicion)
    if excluir_inscripcion_id is not None:
        inscritos_ids = inscritos_ids.exclude(pk=excluir_inscripcion_id)
    inscritos_ids = inscritos_ids.values_list("estudiante_id", flat=True)

    return Estudiante.objects.exclude(pk__in=inscritos_ids).order_by("apellido", "nombre")