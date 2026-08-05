"""
Operaciones de escritura (alta, edición, baja lógica) para
apps.docencia.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from apps.docencia.models import Instructor, Tema


@transaction.atomic
def crear_instructor(*, nombre, apellido, cargo):
    instructor = Instructor(nombre=nombre, apellido=apellido, cargo=cargo)
    instructor.full_clean()
    instructor.save()
    return instructor


@transaction.atomic
def actualizar_instructor(*, instructor, **campos):
    for campo, valor in campos.items():
        setattr(instructor, campo, valor)
    instructor.full_clean()
    instructor.save()
    return instructor


@transaction.atomic
def eliminar_instructor(*, instructor):
    """
    Elimina un instructor de forma permanente. A partir de la Fase 3,
    Django puede lanzar ProtectedError si el instructor tiene
    programaciones asociadas (on_delete=PROTECT en ProgramacionClase).
    Hoy, sin esa relación todavía construida, esta captura es inerte.
    """
    try:
        instructor.delete()
    except ProtectedError as exc:
        raise ValidationError(
            "No es posible eliminar este instructor: tiene programaciones asociadas."
        ) from exc


@transaction.atomic
def crear_tema(*, titulo_tema, activo=True):
    tema = Tema(titulo_tema=titulo_tema, activo=activo)
    tema.full_clean()
    tema.save()
    return tema


@transaction.atomic
def actualizar_tema(*, tema, **campos):
    for campo, valor in campos.items():
        setattr(tema, campo, valor)
    tema.full_clean()
    tema.save()
    return tema


@transaction.atomic
def desactivar_tema(*, tema):
    """Baja lógica: el tema deja de estar disponible para nueva programación."""
    tema.activo = False
    tema.full_clean()
    tema.save()
    return tema


@transaction.atomic
def activar_tema(*, tema):
    """Revierte la baja lógica de un tema."""
    tema.activo = True
    tema.full_clean()
    tema.save()
    return tema