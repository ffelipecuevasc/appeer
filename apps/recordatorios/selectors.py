"""
Consultas de lectura reutilizables para apps.recordatorios.
Ninguna función de este módulo escribe en la base de datos.
"""
from datetime import date

from apps.recordatorios.models import Recordatorio, TipoRecordatorio


def _base():
    """
    Queryset base con las relaciones precargadas.

    select_related para clase/tipo (uno-a-muchos: se resuelven con un
    JOIN) y prefetch_related para responsables (muchos-a-muchos: no se
    puede resolver con JOIN sin duplicar filas). Sin esto, pintar 30
    tareas dispararía decenas de consultas extra.
    """
    return (
        Recordatorio.objects
        .select_related("clase", "tipo")
        .prefetch_related("responsables")
    )


def listar_por_clase(id_clase):
    return _base().filter(clase_id=id_clase)


def obtener_por_id(id_recordatorio):
    return _base().filter(pk=id_recordatorio).first()


def agrupar_por_semana(recordatorios, *, hoy=None):
    """
    Reparte los recordatorios en bloques de semana para la línea de
    tiempo (Subfase 14.4).

    La agrupación es responsabilidad del Selector, nunca de la
    plantilla — mismo criterio que `agrupar_estudiantes` en la Fase 13.

    `hoy` se recibe como parámetro en vez de leerse acá dentro para
    que las pruebas puedan fijar una fecha y no depender del día en
    que se ejecutan. Es el mismo motivo por el que la comparación de
    vencidas ocurre en el servidor y no en JavaScript (Subfase 14.8):
    el reloj debe ser una fuente de verdad controlada.

    Devuelve una lista de dicts ordenada por número de semana, con el
    resumen que la plantilla necesita para pintar la cabecera del
    bloque sin tener que recorrer las tareas ella misma.
    """
    hoy = hoy or date.today()
    semanas = {}

    for recordatorio in recordatorios:
        bloque = semanas.setdefault(
            recordatorio.numero_semana,
            {"numero_semana": recordatorio.numero_semana, "tareas": [],
             "total": 0, "completadas": 0, "vencidas": 0},
        )
        vencida = (not recordatorio.completado) and recordatorio.fecha < hoy
        bloque["tareas"].append((recordatorio, vencida))
        bloque["total"] += 1
        if recordatorio.completado:
            bloque["completadas"] += 1
        elif vencida:
            bloque["vencidas"] += 1

    return [semanas[numero] for numero in sorted(semanas)]


def listar_tipos():
    return TipoRecordatorio.objects.order_by("nombre")


def listar_pendientes_y_vencidas(id_clase, *, hoy=None, limite=None):
    """
    Tareas sin completar, ordenadas por fecha. Base del tablero de la
    Fase 15: lo vencido primero, después lo que viene.

    No lo consume ninguna pantalla todavía — se construye acá porque
    la Fase 15 ya está declarada y este es su punto de entrada
    natural. Mismo criterio con el que la Fase 1 dejó selectors listos
    antes de tener vistas que los usaran.
    """
    hoy = hoy or date.today()
    qs = _base().filter(clase_id=id_clase, completado=False).order_by("fecha", "hora")
    if limite is not None:
        qs = qs[:limite]
    return qs
