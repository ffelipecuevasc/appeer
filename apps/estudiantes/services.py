"""
Operaciones de escritura (alta, edición) para apps.estudiantes.
Toda regla de negocio de escritura vive aquí, nunca en las vistas.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.estudiantes.models import Estudiante

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
def crear_estudiante(
    *,
    nombre,
    apellido,
    genero,
    fecha_nacimiento=None,
    fecha_bautismo=None,
    fecha_inicio_servicio_tiempo_completo=None,
    matrimonio=None,
):
    """Alta de un estudiante, validando la capacidad del matrimonio si se indica."""
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
    Edición parcial de un estudiante. `campos` acepta cualquier
    subconjunto de los atributos del modelo, ej.:
    actualizar_estudiante(estudiante=e, nombre="Nuevo", matrimonio=m)
    """
    if "matrimonio" in campos:
        _validar_capacidad_matrimonio(
            campos["matrimonio"], excluir_id_estudiante=estudiante.pk
        )
    for campo, valor in campos.items():
        setattr(estudiante, campo, valor)
    estudiante.full_clean()
    estudiante.save()
    return estudiante