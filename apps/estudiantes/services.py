"""
Operaciones de escritura (alta, edición, baja) para apps.estudiantes.
Toda regla de negocio de escritura vive aquí, nunca en las vistas.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from apps.estudiantes.models import Estudiante, Matrimonio

MAX_INTEGRANTES_POR_MATRIMONIO = 2


def _validar_capacidad_matrimonio(matrimonio, excluir_id_estudiante=None):
    """
    Verifica que asignar un estudiante a `matrimonio` no supere el
    máximo de dos integrantes. Si `excluir_id_estudiante` se indica,
    se excluye ese estudiante del conteo (caso: edición de un
    estudiante que ya pertenece a ese mismo matrimonio).
    """
    if matrimonio is None:
        return
    integrantes = matrimonio.estudiantes.all()
    if excluir_id_estudiante is not None:
        integrantes = integrantes.exclude(pk=excluir_id_estudiante)
    if integrantes.count() >= MAX_INTEGRANTES_POR_MATRIMONIO:
        raise ValidationError(
            "El matrimonio seleccionado ya tiene el máximo de dos integrantes."
        )


@transaction.atomic
def crear_matrimonio(*, fecha_matrimonio):
    """Alta de un matrimonio nuevo, sin integrantes todavía."""
    matrimonio = Matrimonio(fecha_matrimonio=fecha_matrimonio)
    matrimonio.full_clean()
    matrimonio.save()
    return matrimonio


def _resolver_matrimonio(matrimonio, nueva_fecha_matrimonio):
    """
    Resuelve cuál Matrimonio asociar a un Estudiante a partir de dos
    entradas mutuamente excluyentes del form: un matrimonio existente
    ya seleccionado, o la fecha de un matrimonio nuevo a crear en el
    momento. Nunca deben llegar ambas cargadas a la vez.
    """
    if matrimonio is not None and nueva_fecha_matrimonio is not None:
        raise ValidationError(
            "Elegí un matrimonio existente o cargá uno nuevo, no ambas cosas."
        )
    if nueva_fecha_matrimonio is not None:
        return crear_matrimonio(fecha_matrimonio=nueva_fecha_matrimonio)
    return matrimonio


@transaction.atomic
def crear_estudiante(
    *,
    nombre,
    apellido,
    genero,
    fecha_nacimiento=None,
    fecha_bautismo=None,
    fecha_inicio_servicio_tiempo_completo=None,
    matrimonio=None,
    nueva_fecha_matrimonio=None,
):
    """
    Alta de un estudiante. `matrimonio` asocia a uno ya existente;
    `nueva_fecha_matrimonio` (mutuamente excluyente) crea uno nuevo
    en la misma operación atómica.
    """
    matrimonio = _resolver_matrimonio(matrimonio, nueva_fecha_matrimonio)
    _validar_capacidad_matrimonio(matrimonio)
    estudiante = Estudiante(
        nombre=nombre,
        apellido=apellido,
        genero=genero,
        fecha_nacimiento=fecha_nacimiento,
        fecha_bautismo=fecha_bautismo,
        fecha_inicio_servicio_tiempo_completo=fecha_inicio_servicio_tiempo_completo,
        matrimonio=matrimonio,
    )
    estudiante.full_clean()
    estudiante.save()
    return estudiante


@transaction.atomic
def actualizar_estudiante(*, estudiante, **campos):
    """
    Edición parcial de un estudiante. Acepta cualquier subconjunto de
    atributos del modelo, más el pseudo-campo `nueva_fecha_matrimonio`
    (mutuamente excluyente con `matrimonio`) para crear un matrimonio
    nuevo en el mismo movimiento.
    """
    nueva_fecha_matrimonio = campos.pop("nueva_fecha_matrimonio", None)
    if nueva_fecha_matrimonio is not None:
        campos["matrimonio"] = _resolver_matrimonio(
            campos.get("matrimonio"), nueva_fecha_matrimonio
        )

    if "matrimonio" in campos:
        _validar_capacidad_matrimonio(
            campos["matrimonio"], excluir_id_estudiante=estudiante.pk
        )
    for campo, valor in campos.items():
        setattr(estudiante, campo, valor)
    estudiante.full_clean()
    estudiante.save()
    return estudiante

@transaction.atomic
def eliminar_estudiante(*, estudiante):
    """
    Elimina un estudiante de forma permanente.

    Efecto colateral hoy (Fase 1): ninguno, no hay tablas que
    referencien todavía a `estudiantes`.

    A partir de la Fase 2, `inscripciones_estudiantes` referencia a
    `estudiantes` con ON DELETE CASCADE: este borrado eliminará el
    historial de inscripciones sin lanzar excepción (comportamiento
    esperado, advertido al usuario en la pantalla de confirmación).

    A partir de la Fase 4, `parejas` referencia a `estudiantes` con
    ON DELETE RESTRICT en ambas FKs (según el script SQL auditado):
    si el estudiante integra una pareja, Django puede lanzar
    ProtectedError. Se captura acá con el mismo patrón que
    eliminar_instructor en docencia, aunque hoy —sin esa relación
    construida todavía— la captura es inerte.
    """
    try:
        estudiante.delete()
    except ProtectedError as exc:
        raise ValidationError(
            "No es posible eliminar este estudiante: tiene relaciones activas "
            "que lo impiden (por ejemplo, una pareja asignada)."
        ) from exc