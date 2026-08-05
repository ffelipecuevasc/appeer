from django.contrib import admin

from apps.planificacion.models import ProgramacionClase


@admin.register(ProgramacionClase)
class ProgramacionClaseAdmin(admin.ModelAdmin):
    list_display = ("codigo_clase", "edicion", "numero_semana", "dia_semana", "numero_aula", "instructor", "tema")
    list_filter = ("edicion", "dia_semana", "instructor", "tema")
    search_fields = ("codigo_clase",)
    ordering = ("edicion", "numero_semana", "dia_semana", "numero_aula")