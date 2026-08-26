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


class Responsabilidad(models.Model):
    """
    Responsabilidad teocrática que puede tener un estudiante: Anciano,
    Siervo Ministerial, Precursor Regular (Fase 12, Subfase 12.1).

    Vive en apps.estudiantes y NO en una app propia: su significado
    depende enteramente del estudiante que la porta, y no tiene opción
    propia en el menú de navegación. Es una entidad, no un módulo
    (Plan de Trabajo Maestro 2.0, sección 1).

    Es un CATÁLOGO EDITABLE, no un TextChoices fijo en código: el
    cliente puede necesitar agregar responsabilidades nuevas sin
    esperar un despliegue. Los tres valores iniciales se cargan con
    una migración de datos (0002_responsabilidad), no con un script
    manual, para que cualquier entorno nuevo —incluido producción—
    arranque con el catálogo poblado sin depender de que alguien
    recuerde ejecutar algo.
    """

    id_responsabilidad = models.AutoField(primary_key=True, db_column="id_responsabilidad")
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "responsabilidades"
        verbose_name = "Responsabilidad"
        verbose_name_plural = "Responsabilidades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


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
    responsabilidades = models.ManyToManyField(
        Responsabilidad,
        blank=True,
        related_name="estudiantes",
        # Nombre de tabla explícito (aprobado en la Fase 12): sin esto,
        # Django generaría `estudiantes_estudiante_responsabilidades`,
        # rompiendo la disciplina de nombres del proyecto — todas las
        # tablas siguen el patrón plural del script SQL auditado
        # (`clases`, `inscripciones_estudiantes`, `programacion_clases`).
        db_table="estudiantes_responsabilidades",
    )

    class Meta:
        db_table = "estudiantes"
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
