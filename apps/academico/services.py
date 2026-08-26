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
from core.unit_of_work import UnitOfWork


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


def obtener_conyuge(estudiante):
    """
    Devuelve el cónyuge de `estudiante` como Estudiante registrado, o
    None si el estudiante no está casado.

    Lanza ValidationError si el estudiante SÍ está casado pero su
    cónyuge no está registrado como estudiante (Adenda 10, opción A):
    ese es un dato incompleto, no un caso válido. `Matrimonio` admite
    un solo integrante a nivel de modelo —la regla de la Fase 1 es
    "máximo dos", no "exactamente dos"—, así que este estado es
    alcanzable y hay que detectarlo explícitamente.
    """
    if estudiante.matrimonio_id is None:
        return None

    conyuges = list(
        estudiante.matrimonio.estudiantes.exclude(pk=estudiante.pk)
    )
    if not conyuges:
        raise ValidationError(
            f"{estudiante.nombre} {estudiante.apellido} está casado/a, pero su "
            f"cónyuge no está registrado/a como estudiante. Registra primero al "
            f"cónyuge para poder inscribir a ambos en la clase."
        )
    return conyuges[0]


@transaction.atomic
def crear_inscripcion(*, estudiante, clase):
    """
    Inscribe a un estudiante en una clase. Si está casado, inscribe
    TAMBIÉN a su cónyuge, en la misma operación atómica (Adenda 10).

    Por qué automático y no una validación que rechaza: la regla de
    negocio es que un casado solo asiste a la escuela invitado junto
    a su cónyuge. Inscribir a ambos de una vez hace que el estado
    inválido (un casado inscrito solo) sea INALCANZABLE, en vez de
    meramente prohibido — no queda ninguna puerta lateral por la que
    llegar a él.

    Devuelve la inscripción del estudiante indicado. La del cónyuge,
    si la hubo, se crea igual pero no se devuelve: quien llama pidió
    inscribir a esta persona, el cónyuge es consecuencia de la regla.
    """
    with UnitOfWork():
        conyuge = obtener_conyuge(estudiante)

        _validar_no_doble_inscripcion(estudiante=estudiante, clase=clase)
        inscripcion = InscripcionEstudiante(estudiante=estudiante, clase=clase)
        inscripcion.full_clean()
        inscripcion.save()

        if conyuge is not None:
            # Idempotente a propósito: si el cónyuge ya estaba inscrito
            # (por ejemplo, porque esta misma función se llamó antes con
            # los roles invertidos), no se duplica ni se lanza error —
            # el objetivo es que la pareja quede completa, no imponer
            # quién se inscribió primero.
            ya_inscrito = InscripcionEstudiante.objects.filter(
                estudiante=conyuge, clase=clase
            ).exists()
            if not ya_inscrito:
                inscripcion_conyuge = InscripcionEstudiante(estudiante=conyuge, clase=clase)
                inscripcion_conyuge.full_clean()
                inscripcion_conyuge.save()

        return inscripcion


@transaction.atomic
def actualizar_inscripcion(*, inscripcion, **campos):
    """
    Cambia el estudiante asignado a una inscripción existente.

    Adenda 10: si el estudiante SALIENTE o el ENTRANTE está casado,
    esta operación se rechaza. Reasignar una inscripción de un casado
    a otra persona rompería la pareja en la clase (dejaría al cónyuge
    solo), y esta operación no tiene forma de reacomodar ambas
    inscripciones sin volverse ambigua. Para esos casos el camino
    correcto es dar de baja la inscripción —que da de baja a la
    pareja completa— y volver a inscribir.
    """
    estudiante_saliente = inscripcion.estudiante
    estudiante = campos.get("estudiante", inscripcion.estudiante)
    clase = campos.get("clase", inscripcion.clase)

    cambia_estudiante = estudiante.pk != estudiante_saliente.pk
    if cambia_estudiante:
        for candidato, rol in ((estudiante_saliente, "actual"), (estudiante, "nuevo")):
            if candidato.matrimonio_id is not None:
                raise ValidationError(
                    f"No es posible reasignar esta inscripción: el estudiante "
                    f"{rol} ({candidato.nombre} {candidato.apellido}) está "
                    f"casado/a y debe inscribirse junto a su cónyuge. Da de "
                    f"baja la inscripción y vuelve a inscribir a la pareja."
                )

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
    Da de baja una inscripción. Si el estudiante está casado, da de
    baja TAMBIÉN la de su cónyuge en esa misma clase (Adenda 10).

    Es la contraparte necesaria de crear_inscripcion: sin esto, la
    regla del cónyuge tendría una puerta trasera — bastaría eliminar
    la inscripción de uno de los dos para dejar al otro casado y solo
    en la clase, justo el estado que la regla existe para impedir.

    A diferencia de la clase a la que pertenece (que nunca se
    elimina), una inscripción sí puede darse de baja: es el historial
    de una persona puntual, no el registro de la clase misma.
    """
    with UnitOfWork():
        estudiante = inscripcion.estudiante
        clase_id = inscripcion.clase_id

        # obtener_conyuge puede lanzar ValidationError si el cónyuge no
        # está registrado. En una BAJA eso no debe bloquear: el dato ya
        # es inconsistente y forzar al usuario a arreglarlo antes de
        # poder deshacer la inscripción sería dejarlo sin salida.
        try:
            conyuge = obtener_conyuge(estudiante)
        except ValidationError:
            conyuge = None

        inscripcion.delete()

        if conyuge is not None:
            InscripcionEstudiante.objects.filter(
                estudiante=conyuge, clase_id=clase_id
            ).delete()
