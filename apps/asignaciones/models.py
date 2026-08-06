from django.db import models


class Pareja(models.Model):
    """
    Asignación dinámica de dos estudiantes dentro de una clase, con
    referencia opcional a la programación vigente (permite rotar
    parejas según tema/semana). Cierra el grafo de dependencias del
    proyecto: apps.asignaciones depende de apps.academico (clase),
    apps.planificacion (programacion) y apps.estudiantes (los dos
    integrantes) — primera app de Nivel 3.

    Resolución del Pendiente 1 heredado de la Adenda 3 (Paso 0 de esta
    fase): parejas → estudiantes se mapea como on_delete=PROTECT, a
    favor del script SQL auditado (RESTRICT), no de lo que todavía
    dice la sección 6 del Plan Maestro (CASCADE) — corrección a
    registrar formalmente en la Adenda de cierre de esta fase.

    La regla de "estudiantes distintos" vive exclusivamente en el
    Service (Subfase 4.2). El script SQL auditado también la aplica
    vía dos triggers de MySQL (trg_parejas_bi/bu, BEFORE INSERT/UPDATE
    sobre esta tabla) que deliberadamente NO se replican en esta
    migración (decisión registrada en el Paso 0 de esta fase): la
    validación de Service cubre el mismo caso antes de que cualquier
    escritura llegue a la base de datos, y el proyecto evita SQL
    crudo salvo excepción justificada (sección 7 del Plan Maestro).
    """

    id_pareja = models.AutoField(primary_key=True, db_column="id_pareja")
    clase = models.ForeignKey(
        "academico.Clase",
        on_delete=models.CASCADE,
        db_column="id_clase",
        related_name="parejas",
    )
    programacion = models.ForeignKey(
        "planificacion.ProgramacionClase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_programacion",
        related_name="parejas",
    )
    estudiante_1 = models.ForeignKey(
        "estudiantes.Estudiante",
        on_delete=models.PROTECT,
        db_column="id_estudiante_1",
        related_name="parejas_como_estudiante_1",
    )
    estudiante_2 = models.ForeignKey(
        "estudiantes.Estudiante",
        on_delete=models.PROTECT,
        db_column="id_estudiante_2",
        related_name="parejas_como_estudiante_2",
    )

    class Meta:
        db_table = "parejas"
        verbose_name = "Pareja"
        verbose_name_plural = "Parejas"

    def __str__(self):
        return f"Pareja #{self.id_pareja} — Clase {self.clase_id}"