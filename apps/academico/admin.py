from django.contrib import admin

from apps.academico.models import Clase, EdicionEscuela, InscripcionEstudiante


class InscripcionEstudianteInline(admin.TabularInline):
    model = InscripcionEstudiante
    extra = 0
    fields = ("estudiante", "clase")


@admin.register(EdicionEscuela)
class EdicionEscuelaAdmin(admin.ModelAdmin):
    list_display = ("nombre_edicion", "fecha_inicio", "fecha_fin")
    ordering = ("-fecha_inicio",)
    inlines = [InscripcionEstudianteInline]


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio")
    list_filter = ("anio",)
    ordering = ("-anio", "nombre")


@admin.register(InscripcionEstudiante)
class InscripcionEstudianteAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "edicion", "clase")
    list_filter = ("edicion", "clase")
    search_fields = ("estudiante__nombre", "estudiante__apellido")
    ordering = ("-edicion__fecha_inicio",)