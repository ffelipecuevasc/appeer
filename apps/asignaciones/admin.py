from django.contrib import admin

from apps.asignaciones.models import Pareja


@admin.register(Pareja)
class ParejaAdmin(admin.ModelAdmin):
    list_display = ("id_pareja", "clase", "estudiante_1", "estudiante_2", "programacion")
    list_filter = ("clase",)
    search_fields = (
        "estudiante_1__nombre", "estudiante_1__apellido",
        "estudiante_2__nombre", "estudiante_2__apellido",
    )
    ordering = ("clase",)