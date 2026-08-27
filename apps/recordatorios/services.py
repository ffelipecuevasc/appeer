"""
Operaciones de escritura para apps.recordatorios.
Toda regla de negocio de escritura vive aquí, nunca en las vistas.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.recordatorios.models import Recordatorio, TipoRecordatorio


def _validar_fecha_dentro_de_la_clase(*, clase, fecha):
    """
    La fecha de un recordatorio debe caer dentro del período de su
    clase, con holgura hacia atrás: la semana 0 de la planilla es la
    PREVIA al inicio (preparar la sala, imprimir designaciones), así
    que una fecha algo anterior a `fecha_inicio` es legítima.

    Se permite hasta 30 días antes del inicio. Más atrás que eso casi
    siempre es un error de tipeo en el año, que es justo lo que esta
    validación existe para atrapar.
    """
    from datetime import timedelta

    if fecha > clase.fecha_fin:
        raise ValidationError(
            {"fecha": f"La fecha no puede ser posterior al término de la clase "
                      f"({clase.fecha_fin})."}
        )
    limite_previo = clase.fecha_inicio - timedelta(days=30)
    if fecha < limite_previo:
        raise ValidationError(
            {"fecha": f"La fecha es demasiado anterior al inicio de la clase "
                      f"({clase.fecha_inicio}). Revisa el año."}
        )


@transaction.atomic
def crear_recordatorio(*, clase, tipo, numero_semana, fecha, descripcion,
                       hora=None, responsables=None, completado=False):
    _validar_fecha_dentro_de_la_clase(clase=clase, fecha=fecha)
    recordatorio = Recordatorio(
        clase=clase, tipo=tipo, numero_semana=numero_semana, fecha=fecha,
        hora=hora, descripcion=descripcion, completado=completado,
    )
    # exclude={"responsables"}: igual que en Estudiante (Fase 12), una
    # relación muchos-a-muchos no se puede validar ni guardar antes de
    # que la fila tenga PK. Por eso el .set() va después del save(),
    # ambos dentro de la misma transacción.
    recordatorio.full_clean(exclude={"responsables"})
    recordatorio.save()
    if responsables is not None:
        recordatorio.responsables.set(responsables)
    return recordatorio


@transaction.atomic
def actualizar_recordatorio(*, recordatorio, **campos):
    # Mismo centinela que en actualizar_estudiante: se comprueba la
    # AUSENCIA de la clave, no que valga None. Una edición parcial que
    # no menciona responsables debe dejarlos intactos, no vaciarlos.
    tiene_responsables = "responsables" in campos
    responsables = campos.pop("responsables", None)

    clase = campos.get("clase", recordatorio.clase)
    fecha = campos.get("fecha", recordatorio.fecha)
    _validar_fecha_dentro_de_la_clase(clase=clase, fecha=fecha)

    for campo, valor in campos.items():
        setattr(recordatorio, campo, valor)
    recordatorio.full_clean(exclude={"responsables"})
    recordatorio.save()
    if tiene_responsables:
        recordatorio.responsables.set(responsables or [])
    return recordatorio


@transaction.atomic
def alternar_completado(*, recordatorio):
    """
    Marca o desmarca una tarea como completada.

    Es una operación propia y no un `actualizar_recordatorio(completado=X)`
    por dos razones: es la acción más frecuente del módulo (un clic,
    sin formulario), y debe ser reversible sin fricción — no pasa por
    la validación de fecha, porque completar una tarea vencida es
    exactamente lo que uno hace cuando se pone al día.
    """
    recordatorio.completado = not recordatorio.completado
    recordatorio.save(update_fields=["completado"])
    return recordatorio


@transaction.atomic
def eliminar_recordatorio(*, recordatorio):
    """
    Borra una tarea. Ninguna otra tabla referencia a `recordatorios`,
    así que el borrado no tiene efectos colaterales.
    """
    recordatorio.delete()


# --- Catálogo de tipos ----------------------------------------------

@transaction.atomic
def crear_tipo(*, nombre, color=TipoRecordatorio.Color.GRIS):
    tipo = TipoRecordatorio(nombre=nombre, color=color)
    tipo.full_clean()
    tipo.save()
    return tipo


@transaction.atomic
def actualizar_tipo(*, tipo, **campos):
    for campo, valor in campos.items():
        setattr(tipo, campo, valor)
    tipo.full_clean()
    tipo.save()
    return tipo
