from django.db import models


class EdicionEscuela(models.Model):
    """
    Edición/promoción temporal de la escuela de capacitación. El rango
    de fechas es opcional: permite calcular vigencia cuando está
    cargado, sin bloquear el alta de una edición cuyas fechas todavía
    no están definidas.
    """

    id_edicion = models.AutoField(primary_key=True, db_column="id_edicion")
    nombre_edicion = models.CharField(max_length=100)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "ediciones_escuela"
        verbose_name = "Edición de escuela"
        verbose_name_plural = "Ediciones de escuela"

    def __str__(self):
        return self.nombre_edicion


class Clase(models.Model):
    """
    Grupo/turma de la escuela (ej. "Clase 206"). Sin relaciones
    todavía: las referencias hacia InscripcionEstudiante (Subfase 2.2)
    y hacia ProgramacionClase/Pareja (Fases 3 y 4) se agregan más
    adelante como FKs entrantes desde esas otras tablas.
    """

    id_clase = models.AutoField(primary_key=True, db_column="id_clase")
    anio = models.IntegerField()
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = "clases"
        verbose_name = "Clase"
        verbose_name_plural = "Clases"

    def __str__(self):
        return f"{self.nombre} ({self.anio})"

class InscripcionEstudiante(models.Model):
    """
    Vincula a un Estudiante con una Edición y una Clase concretas.
    La regla de "no doble inscripción en la misma edición" se
    refuerza a nivel de Service (Subfase 2.3); acá solo se declara
    la restricción de unicidad a nivel de base de datos, como
    segunda barrera.
    """

    id_inscripcion = models.AutoField(primary_key=True, db_column="id_inscripcion")
    estudiante = models.ForeignKey(
        "estudiantes.Estudiante",
        on_delete=models.CASCADE,
        db_column="id_estudiante",
        related_name="inscripciones",
    )
    edicion = models.ForeignKey(
        EdicionEscuela,
        on_delete=models.CASCADE,
        db_column="id_edicion",
        related_name="inscripciones",
    )
    clase = models.ForeignKey(
        Clase,
        on_delete=models.PROTECT,
        db_column="id_clase",
        related_name="inscripciones",
    )

    class Meta:
        db_table = "inscripciones_estudiantes"
        verbose_name = "Inscripción de estudiante"
        verbose_name_plural = "Inscripciones de estudiantes"
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante", "edicion"],
                name="uq_estudiante_edicion",
            )
        ]

    def __str__(self):
        return f"{self.estudiante} — {self.edicion}"    