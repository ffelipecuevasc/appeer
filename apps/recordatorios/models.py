from django.db import models


class TipoRecordatorio(models.Model):
    """
    Tipo de tarea del cronograma (Fase 14, Subfase 14.2).

    La planilla original del cliente codifica las tareas por color
    según su naturaleza: reuniones, impresiones, ayuda personal, envíos
    a Betel, etc. Esta entidad traslada esa codificación al sistema.

    Es un CATÁLOGO EDITABLE y no una lista fija en código (decisión
    confirmada por el cliente), por el mismo motivo que
    Responsabilidad en la Fase 12: durante una escuela surgen tipos
    que hoy no existen, y el cliente debe poder agregarlos sin
    esperar un despliegue.

    Se gestiona desde la propia aplicación (Escuela ▸ Recordatorios ▸
    Gestionar tipos), no desde el panel de administración de Django:
    ese panel es una herramienta técnica, no parte del producto
    (Adenda 11).

    `color` guarda el nombre del tono, no un hexadecimal: así la
    plantilla decide cómo pintarlo dentro del sistema de diseño
    (Tailwind + paleta brand.*) en vez de que la base de datos imponga
    un color suelto que no pertenezca a la identidad visual.
    """

    class Color(models.TextChoices):
        AZUL = "AZUL", "Azul"
        VERDE = "VERDE", "Verde"
        AMBAR = "AMBAR", "Ámbar"
        ROJO = "ROJO", "Rojo"
        VIOLETA = "VIOLETA", "Violeta"
        GRIS = "GRIS", "Gris"

    id_tipo = models.AutoField(primary_key=True, db_column="id_tipo")
    nombre = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=10, choices=Color.choices, default=Color.GRIS)
    # Adenda 11: un tipo que deja de usarse se DESACTIVA, no se borra.
    # Recordatorio.tipo está en PROTECT, así que la base de datos ya
    # impide eliminar un tipo en uso; ofrecer un botón "Eliminar" que
    # falla sería peor que no ofrecerlo. Desactivar además preserva el
    # historial: los recordatorios pasados conservan su etiqueta.
    # Mismo criterio que Tema en apps.docencia (Fase 1).
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "tipos_recordatorio"
        verbose_name = "Tipo de recordatorio"
        verbose_name_plural = "Tipos de recordatorio"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Recordatorio(models.Model):
    """
    Tarea del cronograma de instructores (Fase 14, Subfase 14.2),
    modelada a partir de la "Lista de Procedimientos" real del cliente.

    Cuelga de la CLASE: cada turma tiene su propio cronograma, igual
    que su propio horario y sus propias parejas.

    `numero_semana` empieza en CERO a propósito: en la planilla, la
    semana 0 es la previa al inicio de la escuela (preparación de sala,
    designaciones iniciales). Por eso es PositiveSmallIntegerField y no
    tiene un mínimo de 1.

    `hora` es opcional porque en la planilla hay tareas sin hora fija
    ("Preparar esbozo de ayuda personal"), a diferencia de las que sí
    la tienen ("8:00", "13:00").

    `responsables` es muchos-a-muchos y no una clave foránea simple
    (decisión confirmada por el cliente): la planilla marca "A / B",
    es decir, a veces la tarea es de un instructor y a veces de ambos.
    Un M2M cubre los dos casos sin un campo booleano extra, y sigue
    funcionando el día que haya un tercer instructor.
    """

    id_recordatorio = models.AutoField(primary_key=True, db_column="id_recordatorio")
    clase = models.ForeignKey(
        "academico.Clase",
        on_delete=models.CASCADE,
        db_column="id_clase",
        related_name="recordatorios",
    )
    tipo = models.ForeignKey(
        TipoRecordatorio,
        on_delete=models.PROTECT,
        db_column="id_tipo",
        related_name="recordatorios",
    )
    responsables = models.ManyToManyField(
        "docencia.Instructor",
        blank=True,
        related_name="recordatorios",
        # Nombre explícito, como en estudiantes_responsabilidades:
        # el proyecto no acepta los nombres que Django genera solo.
        db_table="recordatorios_responsables",
    )
    numero_semana = models.PositiveSmallIntegerField()
    fecha = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    descripcion = models.CharField(max_length=255)
    completado = models.BooleanField(default=False)

    class Meta:
        db_table = "recordatorios"
        verbose_name = "Recordatorio"
        verbose_name_plural = "Recordatorios"
        # Orden cronológico dentro de cada semana. `hora` va con F() y
        # nulls_last porque una tarea sin hora no debe colarse antes de
        # las que sí la tienen: en la planilla, lo que no tiene hora es
        # "en algún momento de ese día", no "a primera hora".
        ordering = ["numero_semana", "fecha", models.F("hora").asc(nulls_last=True)]

    def __str__(self):
        return f"S{self.numero_semana} · {self.fecha} · {self.descripcion[:40]}"
