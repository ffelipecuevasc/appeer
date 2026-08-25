from django.core.exceptions import ValidationError
from django.db import models


class Clase(models.Model):
    """
    Grupo/turma de la escuela de capacitación (ej. "Turma 206"), con su
    propio período de ejecución. Fusiona lo que hasta la Fase 10 eran
    dos entidades separadas — Clase (identidad del grupo) y
    EdicionEscuela (su período) — en una sola (Adenda 9, Fase 11): el
    cliente nunca distinguió ambas cosas, y mantenerlas separadas
    impedía que el horario de clases (apps.planificacion) supiera a
    qué grupo pertenecía cada sesión programada.

    `fecha_inicio` y `fecha_fin` son OBLIGATORIAS — a diferencia de
    EdicionEscuela, donde eran opcionales. Decisión explícita del
    cliente (Adenda 9): estas fechas van a alimentar reportes en PDF
    enviados a la central que supervisa las escuelas, así que no
    pueden quedar sin cargar.

    Sin campo `anio` propio: se decidió no mantenerlo (Adenda 9,
    Decisión 1) porque, con fechas obligatorias, derivar el año desde
    `fecha_inicio` no tiene el problema de nulidad que sí tenía cuando
    las fechas eran opcionales. Ver la property `anio` más abajo.

    Las clases NUNCA se eliminan (Adenda 9, Decisión 2): pueden
    listarse, crearse y editarse, pero no borrarse — ni desde la app
    (no existe vista ni ruta de borrado) ni desde el panel
    administrativo (ver ClaseAdmin.has_delete_permission en admin.py).
    Es una decisión de negocio explícita del cliente, no un olvido.
    """

    id_clase = models.AutoField(primary_key=True, db_column="id_clase")
    nombre = models.CharField(max_length=50)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        db_table = "clases"
        verbose_name = "Clase"
        verbose_name_plural = "Clases"
        ordering = ["-fecha_inicio", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.anio})"

    @property
    def anio(self):
        """
        Año de la clase, derivado de fecha_inicio — no almacenado
        (Adenda 9, Decisión 1). Seguro porque fecha_inicio es
        obligatoria: nunca hay un `None` del que derivar.
        """
        return self.fecha_inicio.year

    def clean(self):
        """
        fecha_fin debe ser posterior a fecha_inicio. Validación nueva
        que EdicionEscuela nunca tuvo (sus fechas, al ser opcionales,
        rara vez se cargaban juntas) — con fechas ahora obligatorias
        y destinadas a reportes oficiales, un rango invertido o vacío
        produciría un reporte con datos absurdos.
        """
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError(
                {"fecha_fin": "La fecha de término debe ser posterior a la fecha de inicio."}
            )


class InscripcionEstudiante(models.Model):
    """
    Vincula a un Estudiante con una Clase. Antes de la Fase 11 vinculaba
    también con una EdicionEscuela separada; la fusión de esa entidad en
    Clase (Adenda 9) deja esta relación con una sola referencia
    académica, no dos.

    La regla de "no doble inscripción" (antes "en la misma edición",
    ahora "en la misma clase") se refuerza a nivel de Service
    (`academico.services._validar_no_doble_inscripcion`); acá solo se
    declara la restricción de unicidad a nivel de base de datos, como
    segunda barrera — mismo criterio que regía para la edición.
    """

    id_inscripcion = models.AutoField(primary_key=True, db_column="id_inscripcion")
    estudiante = models.ForeignKey(
        "estudiantes.Estudiante",
        on_delete=models.CASCADE,
        db_column="id_estudiante",
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
                fields=["estudiante", "clase"],
                name="uq_estudiante_clase",
            )
        ]

    def __str__(self):
        return f"{self.estudiante} — {self.clase}"
