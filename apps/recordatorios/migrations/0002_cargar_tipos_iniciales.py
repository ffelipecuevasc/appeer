"""
Carga inicial del catálogo de tipos de recordatorio (Subfase 14.2).

Migración de datos y no script manual, por el mismo motivo que las
responsabilidades de la Fase 12: cualquier entorno nuevo arranca con el
catálogo poblado, sin depender de que alguien recuerde ejecutar algo.

Los seis tipos salen de los colores que la planilla real del cliente ya
usa para clasificar sus tareas. El catálogo es editable desde el panel
de administración, así que estos son un punto de partida, no una lista
cerrada.
"""
from django.db import migrations

TIPOS_INICIALES = [
    ("Reunión", "AZUL"),
    ("Designaciones", "VIOLETA"),
    ("Ayuda personal", "VERDE"),
    ("Impresión", "GRIS"),
    ("Envío a Betel", "AMBAR"),
    ("Preparación de sala", "ROJO"),
]


def cargar(apps, schema_editor):
    Tipo = apps.get_model("recordatorios", "TipoRecordatorio")
    for nombre, color in TIPOS_INICIALES:
        Tipo.objects.get_or_create(nombre=nombre, defaults={"color": color})


def revertir(apps, schema_editor):
    """Borra solo los iniciales, nunca los que el cliente agregó después."""
    Tipo = apps.get_model("recordatorios", "TipoRecordatorio")
    Tipo.objects.filter(nombre__in=[n for n, _ in TIPOS_INICIALES]).delete()


class Migration(migrations.Migration):
    dependencies = [("recordatorios", "0001_initial")]
    operations = [migrations.RunPython(cargar, revertir)]
