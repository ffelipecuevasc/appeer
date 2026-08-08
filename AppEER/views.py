"""
Vista del proyecto (no de una app de negocio, no transversal de core/):
compone datos de resumen de las cinco apps para la página de inicio.

Deliberadamente NO vive en core/: core/ es agnóstico de apps de negocio
(principio establecido desde la Fase 0 — ningún módulo de core/
importa de apps/ hasta ahora) y esta vista sí necesita conocerlas
todas. Vive junto a AppEER/urls.py porque es, literalmente, la vista
raíz del proyecto.

Solo usa selectors ya existentes desde las Fases 1-4, en modo lectura.
No se creó ni se modificó ningún selector para esto.
"""
from django.shortcuts import render

from apps.academico import selectors as academico_selectors
from apps.asignaciones import selectors as asignaciones_selectors
from apps.docencia import selectors as docencia_selectors
from apps.estudiantes import selectors as estudiantes_selectors
from apps.planificacion import selectors as planificacion_selectors
from apps.planificacion.serializers import ProgramacionClaseDTO


def inicio(request):
    """
    Página de inicio (Adenda 7): tarjetas de resumen por app + las
    próximas programaciones. Mismo patrón que cualquier ListView del
    proyecto — Selector para leer, DTO para exponer al template —
    solo que compone varias apps en vez de una sola.
    """
    proximas_programaciones = [
        ProgramacionClaseDTO.from_model(p)
        for p in planificacion_selectors.listar_programaciones()[:5]
    ]

    context = {
        "total_estudiantes": estudiantes_selectors.listar_estudiantes().count(),
        "total_instructores": docencia_selectors.listar_instructores().count(),
        "total_ediciones": academico_selectors.listar_ediciones().count(),
        "total_parejas": asignaciones_selectors.listar_parejas().count(),
        "proximas_programaciones": proximas_programaciones,
    }
    return render(request, "index.html", context)