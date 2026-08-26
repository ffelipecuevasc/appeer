from django.contrib import admin

from apps.estudiantes.models import Estudiante, Matrimonio, Responsabilidad


class EstudianteInline(admin.TabularInline):
    model = Estudiante
    extra = 0
    fields = ("nombre", "apellido", "genero")


@admin.register(Matrimonio)
class MatrimonioAdmin(admin.ModelAdmin):
    list_display = ("id_matrimonio", "fecha_matrimonio")
    ordering = ("-fecha_matrimonio",)
    inlines = [EstudianteInline]


@admin.register(Responsabilidad)
class ResponsabilidadAdmin(admin.ModelAdmin):
    """
    Catálogo editable (Fase 12): el cliente agrega responsabilidades
    nuevas desde acá, sin necesitar un cambio de código ni un
    despliegue. `cantidad_estudiantes` evita el error de borrar una
    responsabilidad sin darse cuenta de a cuánta gente afecta.
    """
    list_display = ("nombre", "cantidad_estudiantes")
    search_fields = ("nombre",)
    ordering = ("nombre",)

    @admin.display(description="Estudiantes")
    def cantidad_estudiantes(self, obj):
        return obj.estudiantes.count()


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "genero", "matrimonio")
    list_filter = ("genero", "responsabilidades")
    search_fields = ("nombre", "apellido")
    ordering = ("apellido", "nombre")
    # Widget de doble columna, más cómodo que el <select multiple>
    # nativo cuando el catálogo crece.
    filter_horizontal = ("responsabilidades",)
