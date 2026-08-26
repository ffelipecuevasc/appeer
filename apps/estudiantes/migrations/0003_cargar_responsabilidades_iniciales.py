"""
Carga inicial del catálogo de responsabilidades (Fase 12, Subfase 12.4).

Es una migración de datos y no un script manual a propósito: garantiza
que CUALQUIER entorno nuevo —el de otro desarrollador, el de pruebas,
producción— arranque con el catálogo poblado, sin depender de que
alguien se acuerde de ejecutar algo después de migrar.
"""
from django.db import migrations

RESPONSABILIDADES_INICIALES = [
    "Anciano",
    "Siervo Ministerial",
    "Precursor Regular",
]


def cargar_responsabilidades(apps, schema_editor):
    """
    get_or_create y no create: hace la migración segura de re-aplicar
    si alguien la revierte y la vuelve a correr, sin chocar contra la
    restricción de unicidad de `nombre`.

    apps.get_model() y no el import directo del modelo: es la forma
    correcta dentro de una migración — usa la versión HISTÓRICA del
    modelo, tal como existía en este punto de la historia, así esta
    migración sigue funcionando aunque el modelo real cambie después.
    """
    Responsabilidad = apps.get_model("estudiantes", "Responsabilidad")
    for nombre in RESPONSABILIDADES_INICIALES:
        Responsabilidad.objects.get_or_create(nombre=nombre)


def revertir_responsabilidades(apps, schema_editor):
    """
    Reversa: borra SOLO las tres responsabilidades iniciales, nunca las
    que el cliente haya agregado después desde el panel de
    administración. Borrar el catálogo completo sería destruir datos
    del usuario al revertir una migración de código.
    """
    Responsabilidad = apps.get_model("estudiantes", "Responsabilidad")
    Responsabilidad.objects.filter(nombre__in=RESPONSABILIDADES_INICIALES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("estudiantes", "0002_responsabilidad_estudiante_responsabilidades"),
    ]

    operations = [
        migrations.RunPython(cargar_responsabilidades, revertir_responsabilidades),
    ]
