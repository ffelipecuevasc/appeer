"""
Consultas de lectura reutilizables para apps.docencia.
Ninguna función de este módulo escribe en la base de datos.
"""
from apps.docencia.models import Instructor, Tema


def listar_instructores():
    return Instructor.objects.order_by("apellido", "nombre")


def obtener_instructor_por_id(id_instructor):
    return Instructor.objects.filter(pk=id_instructor).first()


def listar_temas(*, solo_activos=False):
    """Por defecto lista todos los temas. `solo_activos=True` filtra
    los ya dados de baja — útil desde la Fase 3 al armar programación."""
    qs = Tema.objects.order_by("titulo_tema")
    if solo_activos:
        qs = qs.filter(activo=True)
    return qs


def obtener_tema_por_id(id_tema):
    return Tema.objects.filter(pk=id_tema).first()