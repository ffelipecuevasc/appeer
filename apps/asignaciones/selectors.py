"""
Consultas de lectura reutilizables para apps.asignaciones.
Ninguna función de este módulo escribe en la base de datos.
"""
from django.db.models import Q
from apps.academico.models import InscripcionEstudiante
from apps.estudiantes.models import Estudiante
from apps.planificacion.models import ProgramacionClase

from apps.asignaciones.models import Pareja


def listar_parejas():
    """Queryset base de parejas, con clase/programación/estudiantes precargados."""
    return Pareja.objects.select_related("clase", "programacion", "estudiante_1", "estudiante_2")


def obtener_pareja_por_id(id_pareja):
    return listar_parejas().filter(pk=id_pareja).first()


def listar_parejas_por_clase(id_clase):
    """Todas las parejas asignadas dentro de una clase puntual."""
    return listar_parejas().filter(clase_id=id_clase)


def listar_parejas_por_estudiante(id_estudiante):
    """
    Todas las parejas donde el estudiante participa, sin importar si
    quedó registrado como estudiante_1 o estudiante_2 — las dos FKs
    apuntan al mismo modelo con related_names distintos (Subfase 4.1),
    así que acá se consultan ambas con un Q() para no exponerle esa
    asimetría técnica a quien llame a este Selector.
    """
    return listar_parejas().filter(
        Q(estudiante_1_id=id_estudiante) | Q(estudiante_2_id=id_estudiante)
    )

def listar_estudiantes_de_clase(id_clase):
    """
    Estudiantes inscritos en una clase puntual (vía InscripcionEstudiante,
    apps.academico), para poblar el <select> del formulario de Pareja.
    Uso de presentación: la validación real de "estudiantes distintos"
    sigue viviendo en el Service — mismo patrón que en Fases 2 y 3.
    """
    ids = InscripcionEstudiante.objects.filter(clase_id=id_clase).values_list("estudiante_id", flat=True)
    return Estudiante.objects.filter(pk__in=ids).order_by("apellido", "nombre")


def listar_programaciones_de_clase(id_clase):
    """
    Programaciones cuya edición coincide con alguna edición en la que
    esta clase tiene inscripciones — mismo criterio de coherencia que
    usa services._validar_coherencia_con_programacion, aplicado acá
    como filtro de UX para el <select>.
    """
    ediciones_ids = (
        InscripcionEstudiante.objects
        .filter(clase_id=id_clase)
        .values_list("edicion_id", flat=True)
        .distinct()
    )
    return ProgramacionClase.objects.filter(edicion_id__in=ediciones_ids).select_related("edicion")