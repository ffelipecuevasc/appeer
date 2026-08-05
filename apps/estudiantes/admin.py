from django.contrib import admin

from apps.docencia.forms import TemaForm
from apps.docencia.models import Instructor, Tema


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "cargo")
    search_fields = ("nombre", "apellido")
    ordering = ("apellido", "nombre")


@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    form = TemaForm
    list_display = ("titulo_tema", "activo")
    list_filter = ("activo",)
    search_fields = ("titulo_tema",)
    ordering = ("titulo_tema",)
    actions = ["marcar_como_activo", "marcar_como_inactivo"]

    @admin.action(description="Marcar temas seleccionados como activos")
    def marcar_como_activo(self, request, queryset):
        queryset.update(activo=True)

    @admin.action(description="Marcar temas seleccionados como inactivos")
    def marcar_como_inactivo(self, request, queryset):
        queryset.update(activo=False)