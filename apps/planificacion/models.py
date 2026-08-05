from django.db import models


class ProgramacionClase(models.Model):
    """
    Calendario transaccional: una sesión de clase concreta, ubicada en
    una edición, semana, día y bloque de aula específicos, dictada por
    un instructor sobre un tema. Consolida en una sola entidad las
    referencias hacia apps.academico (edicion) y apps.docencia
    (instructor, tema) — primera app de Nivel 2 del proyecto.

    `codigo_clase` es un atributo de negocio (ej. "1101"), no la
    identidad técnica del registro: la PK real sigue siendo
    `id_programacion`, sin unicidad declarada sobre `codigo_clase` en
    el script SQL auditado.
    """

    id_programacion = models.AutoField(primary_key=True, db_column="id_programacion")
    edicion = models.ForeignKey(
        "academico.EdicionEscuela",
        on_delete=models.CASCADE,
        db_column="id_edicion",
        related_name="programaciones",
    )
    codigo_clase = models.CharField(max_length=10)
    numero_semana = models.PositiveSmallIntegerField()
    dia_semana = models.CharField(max_length=20)
    numero_aula = models.PositiveSmallIntegerField()
    instructor = models.ForeignKey(
        "docencia.Instructor",
        on_delete=models.PROTECT,
        db_column="id_instructor",
        related_name="programaciones",
    )
    tema = models.ForeignKey(
        "docencia.Tema",
        on_delete=models.PROTECT,
        db_column="id_tema",
        related_name="programaciones",
    )

    class Meta:
        db_table = "programacion_clases"
        verbose_name = "Programación de clase"
        verbose_name_plural = "Programaciones de clase"
        ordering = ["edicion", "numero_semana", "dia_semana", "numero_aula"]

    def __str__(self):
        return f"{self.codigo_clase} — Semana {self.numero_semana} ({self.dia_semana})"