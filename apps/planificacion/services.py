"""
Operaciones de escritura (alta, edición, baja) para apps.planificacion.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.planificacion.models import ProgramacionClase


def _validar_tema_disponible(*, tema):
    """
    Verifica que el tema esté activo antes de programarlo. Decisión
    registrada en el Paso 0 de la Fase 3: la única validación de
    "disponibilidad" exigida por el Plan de Trabajo en esta fase es
    la bandera Tema.activo; no se valida choque de horario del
    instructor.
    """
    if not tema.activo:
        raise ValidationError(
            f'El tema "{tema.titulo_tema}" está desactivado y no puede programarse.'
        )


@transaction.atomic
def crear_programacion(*, clase, codigo_clase, numero_semana, dia_semana, numero_aula, instructor, tema):
    """Fase 11: `edicion` se renombró a `clase` (Adenda 9 — misma FK, otro nombre)."""
    _validar_tema_disponible(tema=tema)
    programacion = ProgramacionClase(
        clase=clase,
        codigo_clase=codigo_clase,
        numero_semana=numero_semana,
        dia_semana=dia_semana,
        numero_aula=numero_aula,
        instructor=instructor,
        tema=tema,
    )
    programacion.full_clean()
    programacion.save()
    return programacion


@transaction.atomic
def actualizar_programacion(*, programacion, **campos):
    tema = campos.get("tema", programacion.tema)
    if tema.pk != programacion.tema_id:
        _validar_tema_disponible(tema=tema)
    for campo, valor in campos.items():
        setattr(programacion, campo, valor)
    programacion.full_clean()
    programacion.save()
    return programacion


@transaction.atomic
def eliminar_programacion(*, programacion):
    """
    Elimina una programación de clase de forma permanente. Ningún
    modelo construido hasta esta fase referencia a ProgramacionClase.
    A partir de la Fase 4, Pareja.programacion la referenciará con
    ON DELETE SET NULL (según el script SQL auditado): eliminar una
    programación no bloqueará el borrado ni arrastrará parejas
    consigo, solo desvinculará esa referencia opcional. No hace falta
    capturar ninguna excepción para ese caso futuro.
    """
    programacion.delete()