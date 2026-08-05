"""
Operaciones de escritura (alta, edición, baja) para apps.academico.
Toda regla de negocio de escritura vive aquí, nunca en las vistas.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from apps.academico.models import Clase, EdicionEscuela, InscripcionEstudiante


# --- EdicionEscuela ---------------------------------------------------

@transaction.atomic
def crear_edicion(*, nombre_edicion, fecha_inicio=None, fecha_fin=None):
    edicion = EdicionEscuela(
        nombre_edicion=nombre_edicion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    edicion.full_clean()
    edicion.save()
    return edicion


@transaction.atomic
def actualizar_edicion(*, edicion, **campos):
    for campo, valor in campos.items():
        setattr(edicion, campo, valor)
    edicion.full_clean()
    edicion.save()
    return edicion


@transaction.atomic
def eliminar_edicion(*, edicion):
    """
    Elimina una edición de forma permanente. `inscripciones_estudiantes`
    referencia a `ediciones_escuela` con CASCADE (on_delete=CASCADE):
    este borrado elimina también las inscripciones de esa edición sin
    lanzar excepción — comportamiento esperado, coherente con la
    sección 6 del Plan Maestro.
    """
    edicion.delete()


# --- Clase --------------------------------------------------------------

@transaction.atomic
def crear_clase(*, anio, nombre):
    clase = Clase(anio=anio, nombre=nombre)
    clase.full_clean()
    clase.save()
    return clase


@transaction.atomic
def actualizar_clase(*, clase, **campos):
    for campo, valor in campos.items():
        setattr(clase, campo, valor)
    clase.full_clean()
    clase.save()
    return clase


@transaction.atomic
def eliminar_clase(*, clase):
    """
    Elimina una clase de forma permanente. `inscripciones_estudiantes`
    referencia a `clases` con RESTRICT (on_delete=PROTECT): si la
    clase tiene inscripciones activas, Django lanza ProtectedError,
    capturada acá con el mismo patrón que eliminar_instructor en
    docencia y eliminar_estudiante en estudiantes.
    """
    try:
        clase.delete()
    except ProtectedError as exc:
        raise ValidationError(
            "No es posible eliminar esta clase: tiene inscripciones activas "
            "que lo impiden."
        ) from exc


# --- InscripcionEstudiante ----------------------------------------------

def _validar_no_doble_inscripcion(*, estudiante, edicion, excluir_inscripcion_id=None):
    """
    Verifica que `estudiante` no tenga ya una inscripción en `edicion`.
    Se valida acá explícitamente —no solo vía la UniqueConstraint de
    base de datos— para poder devolver un ValidationError legible al
    formulario en lugar de un IntegrityError crudo (Subfase 2.3,
    Plan de Trabajo).
    """
    inscripciones = InscripcionEstudiante.objects.filter(estudiante=estudiante, edicion=edicion)
    if excluir_inscripcion_id is not None:
        inscripciones = inscripciones.exclude(pk=excluir_inscripcion_id)
    if inscripciones.exists():
        raise ValidationError(
            "Este estudiante ya está inscrito en la edición seleccionada."
        )


@transaction.atomic
def crear_inscripcion(*, estudiante, edicion, clase):
    _validar_no_doble_inscripcion(estudiante=estudiante, edicion=edicion)
    inscripcion = InscripcionEstudiante(estudiante=estudiante, edicion=edicion, clase=clase)
    inscripcion.full_clean()
    inscripcion.save()
    return inscripcion


@transaction.atomic
def actualizar_inscripcion(*, inscripcion, **campos):
    estudiante = campos.get("estudiante", inscripcion.estudiante)
    edicion = campos.get("edicion", inscripcion.edicion)
    _validar_no_doble_inscripcion(
        estudiante=estudiante, edicion=edicion, excluir_inscripcion_id=inscripcion.pk
    )
    for campo, valor in campos.items():
        setattr(inscripcion, campo, valor)
    inscripcion.full_clean()
    inscripcion.save()
    return inscripcion


@transaction.atomic
def eliminar_inscripcion(*, inscripcion):
    """
    Elimina una inscripción de forma permanente. Ninguna tabla del
    script SQL auditado referencia a `inscripciones_estudiantes`, por
    lo que hoy este borrado no tiene efectos colaterales.
    """
    inscripcion.delete()