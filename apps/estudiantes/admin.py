from django.contrib import admin

from apps.estudiantes.models import Estudiante, Matrimonio


class EstudianteInline(admin.TabularInline):
    model = Estudiante
    extra = 0
    fields = ("nombre", "apellido", "genero")


@admin.register(Matrimonio)
class MatrimonioAdmin(admin.ModelAdmin):
    list_display = ("id_matrimonio", "fecha_matrimonio")
    ordering = ("-fecha_matrimonio",)
    inlines = [EstudianteInline]


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "genero", "matrimonio")
    list_filter = ("genero",)
    search_fields = ("nombre", "apellido")
    ordering = ("apellido", "nombre")