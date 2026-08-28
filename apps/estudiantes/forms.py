"""
Formularios de apps.estudiantes para el CRUD público de Estudiante.
"""
from django import forms

from apps.estudiantes import selectors
from apps.estudiantes.models import Estudiante, Responsabilidad

INPUT_CLASSES = (
    "w-full px-4 py-2.5 rounded-xl border border-brand-border bg-white "
    "text-brand-text text-sm focus:outline-none focus:ring-2 "
    "focus:ring-brand-accent focus:border-brand-accent transition-shadow"
)


class EstudianteForm(forms.ModelForm):
    """
    Formulario público de alta/edición de Estudiante.

    `matrimonio` ofrece los matrimonios con cupo disponible (ver
    selectors.listar_matrimonios_con_cupo). `nueva_fecha_matrimonio`
    permite, en la misma pantalla, cargar la fecha de un matrimonio
    nuevo en lugar de elegir uno existente. Son mutuamente
    excluyentes a nivel de formulario (ver clean()); la resolución
    real —crear uno nuevo o asociar el elegido— queda a cargo del
    Service, nunca de este formulario.

    Fase 12: `responsabilidades` es un campo de selección múltiple
    opcional. El Service se encarga de persistirlo con .set() después
    del save(), porque una relación muchos-a-muchos necesita que el
    estudiante ya tenga PK.
    """

    nueva_fecha_matrimonio = forms.DateField(
        required=False,
        label="O fecha de un matrimonio nuevo",
        help_text=(
            "Completa este campo solo si el matrimonio del estudiante "
            "todavía no está cargado en el sistema."
        ),
        widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
    )

    class Meta:
        model = Estudiante
        fields = [
            "nombre",
            "apellido",
            "genero",
            "fecha_nacimiento",
            "fecha_bautismo",
            "fecha_inicio_servicio_tiempo_completo",
            "matrimonio",
            "responsabilidades",
        ]
        labels = {
            "fecha_inicio_servicio_tiempo_completo": "Inicio de servicio a tiempo completo",
            "matrimonio": "Matrimonio existente",
            "responsabilidades": "Responsabilidades",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "apellido": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "genero": forms.Select(attrs={"class": INPUT_CLASSES}),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
            "fecha_bautismo": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
            "fecha_inicio_servicio_tiempo_completo": forms.DateInput(
                attrs={"type": "date", "class": INPUT_CLASSES}
            ),
            "matrimonio": forms.Select(attrs={"class": INPUT_CLASSES}),
            # CheckboxSelectMultiple y no el <select multiple> nativo:
            # el catálogo es corto (3 valores) y un usuario no técnico
            # no tiene por qué saber que hay que mantener Ctrl apretado
            # para marcar varias opciones. Sin INPUT_CLASSES: esas
            # clases están pensadas para un campo de una sola línea y
            # deformarían la lista de casillas.
            "responsabilidades": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        matrimonio_actual_id = (
            self.instance.matrimonio_id if self.instance and self.instance.pk else None
        )
        self.fields["matrimonio"].required = False
        self.fields["matrimonio"].empty_label = "— Sin matrimonio asociado —"
        self.fields["matrimonio"].queryset = selectors.listar_matrimonios_con_cupo(
            excluir_matrimonio_id=matrimonio_actual_id
        )
        # Fase 12: opcional — un estudiante puede no tener ninguna
        # responsabilidad. El queryset sale del Selector, no de
        # Responsabilidad.objects, para respetar el patrón de capas.
        self.fields["responsabilidades"].required = False
        # Solo activas, más las que este estudiante ya tenga aunque
        # estén desactivadas (Adenda 11) — de lo contrario, editarlo
        # se las quitaría en silencio.
        ya_asignadas = (
            list(self.instance.responsabilidades.values_list("pk", flat=True))
            if self.instance and self.instance.pk else None
        )
        self.fields["responsabilidades"].queryset = selectors.listar_responsabilidades_disponibles(
            incluir_ids=ya_asignadas
        )

    def clean(self):
        cleaned_data = super().clean()
        matrimonio = cleaned_data.get("matrimonio")
        nueva_fecha_matrimonio = cleaned_data.get("nueva_fecha_matrimonio")
        if matrimonio and nueva_fecha_matrimonio:
            self.add_error(
                "nueva_fecha_matrimonio",
                "Elige un matrimonio existente o carga uno nuevo, no ambas cosas.",
            )
        return cleaned_data

class ResponsabilidadForm(forms.ModelForm):
    """
    Formulario del catálogo de responsabilidades (Adenda 11).

    `activo` no es campo del formulario: se cambia con el botón
    Activar/Desactivar del listado — una sola forma de cambiar ese
    estado, igual que en el catálogo de tipos de recordatorio.
    """

    class Meta:
        model = Responsabilidad
        fields = ["nombre"]
        widgets = {"nombre": forms.TextInput(attrs={"class": INPUT_CLASSES})}
