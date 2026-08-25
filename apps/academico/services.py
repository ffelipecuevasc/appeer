"""
Operaciones de escritura (alta, edición) para apps.academico.
Toda regla de negocio de escritura vive aquí, nunca en las vistas.

Fase 11 (Adenda 9): ya no existen crear_edicion/actualizar_edicion/
eliminar_edicion (la entidad que operaban desapareció) ni
eliminar_clase (Decisión 2 de la Adenda 9: las clases nunca se
eliminan — no hay operación de Service para eso, a propósito, no por
omisión).
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.academico.models import Clase, InscripcionEstudiante


# --- Clase ----------------------------------------------------------

@transaction.atomic
def crear_clase(*, nombre, fecha_inicio, fecha_fin):
    clase = Clase(nombre=nombre, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
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


# No existe eliminar_clase(): decisión de negocio explícita (Adenda 9,
# Decisión 2). Una clase se lista, se crea y se edita — nunca se borra.
# Esto no es un olvido: es la ausencia deliberada de una operación.


# --- InscripcionEstudiante -------------------------------------------

def _validar_no_doble_inscripcion(*, estudiante, clase, excluir_inscripcion_id=None):
    """
    Verifica que `estudiante` no tenga ya una inscripción en `clase`.
    Se valida acá explícitamente —no solo vía la UniqueConstraint de
    base de datos— para poder devolver un ValidationError legible al
    formulario en lugar de un IntegrityError crudo (criterio
    establecido en la Subfase 2.3 del Plan de Trabajo v1.0).

    Fase 11: la regla decía "no doble inscripción en la misma
    edición"; con la fusión de EdicionEscuela en Clase (Adenda 9), es
    la misma regla con un solo nombre en vez de dos — no es una regla
    nueva.
    """
    inscripciones = InscripcionEstudiante.objects.filter(estudiante=estudiante, clase=clase)
    if excluir_inscripcion_id is not None:
        inscripciones = inscripciones.exclude(pk=excluir_inscripcion_id)
    if inscripciones.exists():
        raise ValidationError(
            "Este estudiante ya está inscrito en la clase seleccionada."
        )


@transaction.atomic
def crear_inscripcion(*, estudiante, clase):
    _validar_no_doble_inscripcion(estudiante=estudiante, clase=clase)
    inscripcion = InscripcionEstudiante(estudiante=estudiante, clase=clase)
    inscripcion.full_clean()
    inscripcion.save()
    return inscripcion


@transaction.atomic
def actualizar_inscripcion(*, inscripcion, **campos):
    estudiante = campos.get("estudiante", inscripcion.estudiante)
    clase = campos.get("clase", inscripcion.clase)
    _validar_no_doble_inscripcion(
        estudiante=estudiante, clase=clase, excluir_inscripcion_id=inscripcion.pk
    )
    for campo, valor in campos.items():
        setattr(inscripcion, campo, valor)
    inscripcion.full_clean()
    inscripcion.save()
    return inscripcion


@transaction.atomic
def eliminar_inscripcion(*, inscripcion):
    """
    Elimina una inscripción de forma permanente. A diferencia de la
    clase a la que pertenece (que nunca se elimina), una inscripción
    individual sí puede darse de baja — es el historial de un
    estudiante puntual, no el registro de la clase misma. Ninguna
    tabla del script SQL auditado referencia a
    `inscripciones_estudiantes`, por lo que este borrado no tiene
    efectos colaterales.
    """
    inscripcion.delete()
