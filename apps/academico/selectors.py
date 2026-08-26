"""
Consultas de lectura reutilizables para apps.academico.
Ninguna función de este módulo escribe en la base de datos.
"""
from apps.academico.models import Clase, InscripcionEstudiante


def listar_clases():
    return Clase.objects.order_by("-fecha_inicio", "nombre")


def obtener_clase_por_id(id_clase):
    return Clase.objects.filter(pk=id_clase).first()


def listar_inscripciones():
    """Queryset base de inscripciones, con estudiante/clase precargados."""
    return (
        InscripcionEstudiante.objects
        .select_related("estudiante", "clase")
        .order_by("-clase__fecha_inicio", "estudiante__apellido")
    )


def obtener_inscripcion_por_id(id_inscripcion):
    return (
        InscripcionEstudiante.objects
        .select_related("estudiante", "clase")
        .filter(pk=id_inscripcion)
        .first()
    )


def listar_estudiantes_disponibles_para_clase(id_clase, *, excluir_inscripcion_id=None):
    """
    Estudiantes que todavía NO están inscritos en `id_clase`, para
    poblar el <select> del formulario de InscripcionEstudiante. Uso
    exclusivo de presentación (UX preventiva): no reemplaza la
    validación real de "no doble inscripción", que sigue viviendo
    exclusivamente en el Service — mismo patrón que
    listar_matrimonios_con_cupo en apps.estudiantes.

    Fase 11: antes filtraba por edición (`edicion_id`); con la fusión
    de EdicionEscuela en Clase (Adenda 9), filtra directamente por
    `clase_id` — incluso el nombre del parámetro cambió, de
    `id_edicion` a `id_clase`, para que ninguna llamada quede
    describiendo un concepto que ya no existe.

    Si `excluir_inscripcion_id` se indica, se ignora esa inscripción
    puntual al calcular quién ya está inscrito — cubre el caso de
    edición, donde el estudiante de la inscripción que estás editando
    no debe autoexcluirse de su propia lista de opciones.
    """
    from apps.estudiantes.models import Estudiante

    inscritos_ids = InscripcionEstudiante.objects.filter(clase_id=id_clase)
    if excluir_inscripcion_id is not None:
        inscritos_ids = inscritos_ids.exclude(pk=excluir_inscripcion_id)
    inscritos_ids = inscritos_ids.values_list("estudiante_id", flat=True)

    return Estudiante.objects.exclude(pk__in=inscritos_ids).order_by("apellido", "nombre")


def contar_inscritos(id_clase):
    """Total de estudiantes inscritos en una clase."""
    return InscripcionEstudiante.objects.filter(clase_id=id_clase).count()
