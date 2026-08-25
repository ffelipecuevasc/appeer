from django.contrib import admin

from apps.academico.models import Clase, InscripcionEstudiante


class InscripcionEstudianteInline(admin.TabularInline):
    model = InscripcionEstudiante
    extra = 0
    fields = ("estudiante",)


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fecha_inicio", "fecha_fin")
    list_filter = ("fecha_inicio",)
    ordering = ("-fecha_inicio", "nombre")
    inlines = [InscripcionEstudianteInline]

    def has_delete_permission(self, request, obj=None):
        """
        Las clases nunca se eliminan (Adenda 9, Decisión 2) — decisión
        de negocio explícita del cliente, no una omisión. Sin esto, un
        superusuario podría seguir borrando clases desde /admin/ aunque
        la app pública ya no ofrezca esa opción en ningún lado, lo que
        volvería la regla real solo a medias. Se bloquea acá también
        para que sea real en todo el sistema, no solo en la interfaz.
        """
        return False


@admin.register(InscripcionEstudiante)
class InscripcionEstudianteAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "clase")
    list_filter = ("clase",)
    search_fields = ("estudiante__nombre", "estudiante__apellido")
    ordering = ("-clase__fecha_inicio",)
