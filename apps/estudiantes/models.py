from django.db import models


class Matrimonio(models.Model):
    """
    Representa la unidad matrimonial a la que puede pertenecer un
    Estudiante. La regla de "máximo dos integrantes" se valida en la
    capa de Service (Fase 1.2), no aquí: el modelo por sí solo permite
    N estudiantes apuntando al mismo matrimonio.
    """

    id_matrimonio = models.AutoField(primary_key=True, db_column="id_matrimonio")
    fecha_matrimonio = models.DateField()

    class Meta:
        db_table = "matrimonios"
        verbose_name = "Matrimonio"
        verbose_name_plural = "Matrimonios"

    def __str__(self):
        return f"Matrimonio #{self.pk} ({self.fecha_matrimonio})"


class Estudiante(models.Model):

    class Genero(models.TextChoices):
        MASCULINO = "MASCULINO", "Masculino"
        FEMENINO = "FEMENINO", "Femenino"

    id_estudiante = models.AutoField(primary_key=True, db_column="id_estudiante")
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    genero = models.CharField(max_length=10, choices=Genero.choices)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_bautismo = models.DateField(null=True, blank=True)
    fecha_inicio_servicio_tiempo_completo = models.DateField(null=True, blank=True)
    matrimonio = models.ForeignKey(
        Matrimonio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estudiantes",
        db_column="id_matrimonio",
    )

    class Meta:
        db_table = "estudiantes"
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"