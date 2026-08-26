"""
Operaciones de escritura (alta, edición, baja) para apps.estudiantes.
Toda regla de negocio de escritura vive aquí, nunca en las vistas.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from apps.estudiantes.models import Estudiante, Matrimonio, Responsabilidad

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
    responsabilidades=None,
):
    """
    Alta de un estudiante. `matrimonio` asocia a uno ya existente;
    `nueva_fecha_matrimonio` (mutuamente excluyente) crea uno nuevo
    en la misma operación atómica.

    Fase 12: `responsabilidades` acepta un iterable de Responsabilidad
    (o un queryset, como el que entrega un ModelMultipleChoiceField).
    Es opcional — un estudiante puede no tener ninguna.
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
    # exclude={"responsabilidades"}: full_clean() no puede validar una
    # relación muchos-a-muchos en una instancia que todavía no tiene
    # PK — la tabla intermedia necesita el id del estudiante para
    # existir. Por eso el .set() va DESPUÉS del save(), y no antes.
    # Ambos pasos viven dentro del mismo @transaction.atomic, así que
    # si el .set() fallara, el estudiante tampoco quedaría creado.
    estudiante.full_clean(exclude={"responsabilidades"})
    estudiante.save()
    if responsabilidades is not None:
        estudiante.responsabilidades.set(responsabilidades)
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

    # Fase 12: se saca del diccionario ANTES del bucle de setattr().
    # Una relación muchos-a-muchos no admite asignación directa
    # (`estudiante.responsabilidades = [...]` lanza TypeError): se
    # gestiona con .set(), y solo después de que el resto del modelo
    # esté guardado. El centinela es la ausencia de la clave, no None:
    # `responsabilidades=None` no llega desde el form (un
    # ModelMultipleChoiceField vacío entrega un queryset vacío, no
    # None), y distinguirlos permite que una edición parcial que no
    # menciona el campo deje las responsabilidades intactas, en vez de
    # borrarlas silenciosamente.
    tiene_responsabilidades = "responsabilidades" in campos
    responsabilidades = campos.pop("responsabilidades", None)

    if "matrimonio" in campos:
        _validar_capacidad_matrimonio(
            campos["matrimonio"], excluir_id_estudiante=estudiante.pk
        )
    for campo, valor in campos.items():
        setattr(estudiante, campo, valor)
    estudiante.full_clean(exclude={"responsabilidades"})
    estudiante.save()
    if tiene_responsabilidades:
        estudiante.responsabilidades.set(responsabilidades or [])
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

# --- Responsabilidades (Fase 12, Subfase 12.3) -----------------------

@transaction.atomic
def crear_responsabilidad(*, nombre):
    """
    Alta de una responsabilidad nueva en el catálogo. Existe para que
    el cliente pueda agregar responsabilidades sin esperar un
    despliegue — el motivo por el que esto es una tabla y no un
    TextChoices en código.
    """
    responsabilidad = Responsabilidad(nombre=nombre)
    responsabilidad.full_clean()
    responsabilidad.save()
    return responsabilidad


@transaction.atomic
def actualizar_responsabilidad(*, responsabilidad, **campos):
    for campo, valor in campos.items():
        setattr(responsabilidad, campo, valor)
    responsabilidad.full_clean()
    responsabilidad.save()
    return responsabilidad


@transaction.atomic
def asignar_responsabilidad(*, estudiante, responsabilidad):
    """
    Agrega UNA responsabilidad a un estudiante, sin tocar las que ya
    tenía. Complementa a crear/actualizar_estudiante, que reemplazan
    el conjunto completo vía .set().

    .add() es idempotente por definición en una relación M2M: llamarlo
    dos veces con la misma responsabilidad no duplica la fila de la
    tabla intermedia ni lanza error.
    """
    estudiante.responsabilidades.add(responsabilidad)
    return estudiante


@transaction.atomic
def quitar_responsabilidad(*, estudiante, responsabilidad):
    """
    Quita UNA responsabilidad de un estudiante. .remove() tampoco
    falla si el estudiante no la tenía asignada.
    """
    estudiante.responsabilidades.remove(responsabilidad)
    return estudiante
