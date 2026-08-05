from django.core.exceptions import ValidationError
from django.db import models

class Instructor(models.Model):
    id_instructor = models.AutoField(primary_key=True, db_column="id_instructor")
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    cargo = models.CharField(max_length=50)

    class Meta:
        db_table = "instructores"
        verbose_name = "Instructor"
        verbose_name_plural = "Instructores"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Tema(models.Model):
    id_tema = models.AutoField(primary_key=True, db_column="id_tema")
    titulo_tema = models.CharField(max_length=255)
    activo = models.BooleanField(default=True, null=True, db_default=True)

    class Meta:
        db_table = "temas"
        verbose_name = "Tema"
        verbose_name_plural = "Temas"

    def __str__(self):
        return self.titulo_tema

    def clean(self):
        super().clean()
        if self.activo is None:
            raise ValidationError(
                {"activo": "Este campo no admite valores nulos: debe ser Verdadero o Falso."}
            )