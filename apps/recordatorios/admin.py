from django.contrib import admin

from apps.recordatorios.models import Recordatorio, TipoRecordatorio


@admin.register(TipoRecordatorio)
class TipoRecordatorioAdmin(admin.ModelAdmin):
    """Catálogo editable: el cliente agrega tipos nuevos desde acá."""
    list_display = ("nombre", "color", "cantidad_recordatorios")
    list_filter = ("color",)
    search_fields = ("nombre",)

    @admin.display(description="Recordatorios")
    def cantidad_recordatorios(self, obj):
        return obj.recordatorios.count()


@admin.register(Recordatorio)
class RecordatorioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "numero_semana", "descripcion", "tipo", "clase", "completado")
    list_filter = ("clase", "tipo", "completado", "numero_semana")
    search_fields = ("descripcion",)
    filter_horizontal = ("responsables",)
    date_hierarchy = "fecha"
