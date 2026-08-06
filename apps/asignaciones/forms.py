"""
Formularios de apps.asignaciones para el CRUD público de Pareja.
"""
from django import forms

from apps.asignaciones import selectors
from apps.asignaciones.models import Pareja

INPUT_CLASSES = (
    "w-full px-4 py-2.5 rounded-xl border border-brand-border bg-white "
    "text-brand-text text-sm focus:outline-none focus:ring-2 "
    "focus:ring-brand-accent focus:border-brand-accent transition-shadow"
)


class ParejaForm(forms.ModelForm):
    """
    Siempre en el contexto de una Clase fija (pasada por la vista,
    nunca elegida en este formulario) — mismo motivo que
    InscripcionEstudianteForm en apps.academico: permite filtrar los
    <select> de estudiantes/programación server-side sin JavaScript.
    """

    class Meta:
        model = Pareja
        fields = ["estudiante_1", "estudiante_2", "programacion"]
        widgets = {
            "estudiante_1": forms.Select(attrs={"class": INPUT_CLASSES}),
            "estudiante_2": forms.Select(attrs={"class": INPUT_CLASSES}),
            "programacion": forms.Select(attrs={"class": INPUT_CLASSES}),
        }

    def __init__(self, *args, clase, **kwargs):
        super().__init__(*args, **kwargs)
        self.clase = clase
        estudiantes_de_la_clase = selectors.listar_estudiantes_de_clase(clase.pk)
        self.fields["estudiante_1"].queryset = estudiantes_de_la_clase
        self.fields["estudiante_2"].queryset = estudiantes_de_la_clase
        self.fields["programacion"].queryset = selectors.listar_programaciones_de_clase(clase.pk)
        self.fields["programacion"].required = False