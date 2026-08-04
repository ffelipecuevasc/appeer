"""
Utilidad transaccional reutilizable entre Services. Envuelve
operaciones de escritura que tocan más de un modelo en una única
frontera atómica. Primer uso real en la Fase 4 (apps.asignaciones).
"""