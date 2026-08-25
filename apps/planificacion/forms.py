"""
Formularios de apps.planificacion para el CRUD público de
ProgramacionClase.
"""
from django import forms

from apps.academico.models import Clase
from apps.planificacion import selectors
from apps.planificacion.models import ProgramacionClase

INPUT_CLASSES = (
    "w-full px-4 py-2.5 rounded-xl border border-brand-border bg-white "
    "text-brand-text text-sm focus:outline-none focus:ring-2 "
    "focus:ring-brand-accent focus:border-brand-accent transition-shadow"
)

DIAS_SEMANA = [
    ("Lunes", "Lunes"),
    ("Martes", "Martes"),
    ("Miércoles", "Miércoles"),
    ("Jueves", "Jueves"),
    ("Viernes", "Viernes"),
    ("Sábado", "Sábado"),
    ("Domingo", "Domingo"),
]


class ProgramacionClaseForm(forms.ModelForm):
    """
    dia_semana sigue siendo un CharField libre a nivel de modelo; acá
    se restringe a un <select> de 7 valores solo a nivel de
    formulario, sin necesitar una nueva migración.

    Fase 11: el campo `edicion` se renombra a `clase` (Adenda 9 — la
    FK apunta ahora a academico.Clase directamente, no a una edición
    que ya no existe).
    """

    dia_semana = forms.ChoiceField(
        choices=DIAS_SEMANA, widget=forms.Select(attrs={"class": INPUT_CLASSES})
    )

    class Meta:
        model = ProgramacionClase
        fields = ["clase", "codigo_clase", "numero_semana", "dia_semana", "numero_aula", "instructor", "tema"]
        widgets = {
            "clase": forms.Select(attrs={"class": INPUT_CLASSES}),
            "codigo_clase": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "numero_semana": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 0}),
            "numero_aula": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 0}),
            "instructor": forms.Select(attrs={"class": INPUT_CLASSES}),
            "tema": forms.Select(attrs={"class": INPUT_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["clase"].queryset = Clase.objects.order_by("-fecha_inicio", "nombre")
        self.fields["instructor"].queryset = selectors.listar_instructores()
        tema_actual_id = self.instance.tema_id if self.instance and self.instance.pk else None
        self.fields["tema"].queryset = selectors.listar_temas_disponibles(incluir_tema_id=tema_actual_id)
