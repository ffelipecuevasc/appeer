"""
Utilidad transaccional reutilizable entre Services. Envuelve
operaciones de escritura que tocan más de un modelo en una única
frontera atómica. Primer uso real en la Fase 4 (apps.asignaciones).
"""
from django.db import transaction


class UnitOfWork:
    """
    Envoltorio delgado sobre transaction.atomic() de Django (sección
    9.2 del Plan Maestro), para Services cuya operación de negocio
    escribe en más de un modelo —potencialmente de más de una app—
    como una sola unidad atómica.

    No reimplementa el patrón clásico de Unit of Work con registro
    manual de objetos nuevos/sucios/eliminados: Django ya aplica ese
    seguimiento internamente dentro de una transacción. El valor de
    esta clase es un punto de entrada único y explícitamente nombrado
    —en vez de que cada Service importe transaction.atomic()
    directamente— para dejar clara la intención en el código, y un
    solo lugar donde agregar a futuro comportamiento transversal
    (logging de operaciones multi-modelo, hooks post-commit) sin
    tocar cada Service uno por uno.

    Uso:
        with UnitOfWork():
            ...operaciones sobre más de un modelo...
    """

    def __init__(self, using=None):
        self._atomic = transaction.atomic(using=using)

    def __enter__(self):
        self._atomic.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._atomic.__exit__(exc_type, exc_value, traceback)