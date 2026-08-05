"""
Formularios de apps.academico para el CRUD público de EdicionEscuela
y Clase. El formulario de InscripcionEstudiante llega en el Paso B.
"""
from django import forms
from apps.academico import selectors
from apps.academico.models import Clase, EdicionEscuela, InscripcionEstudiante

INPUT_CLASSES = (
    "w-full px-4 py-2.5 rounded-xl border border-brand-border bg-white "
    "text-brand-text text-sm focus:outline-none focus:ring-2 "
    "focus:ring-brand-accent focus:border-brand-accent transition-shadow"
)


class EdicionEscuelaForm(forms.ModelForm):
    class Meta:
        model = EdicionEscuela
        fields = ["nombre_edicion", "fecha_inicio", "fecha_fin"]
        widgets = {
            "nombre_edicion": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "fecha_inicio": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
        }


class ClaseForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = ["anio", "nombre"]
        widgets = {
            "anio": forms.NumberInput(attrs={"class": INPUT_CLASSES}),
            "nombre": forms.TextInput(attrs={"class": INPUT_CLASSES}),
        }

class InscripcionEstudianteForm(forms.ModelForm):
    """
    Formulario de alta/edición de InscripcionEstudiante, siempre en el
    contexto de una Edición fija (pasada por la vista, nunca elegida
    en este formulario): así el <select> de estudiantes se puede
    filtrar server-side contra esa edición sin necesitar JavaScript
    (la interactividad en vivo llega recién en la Fase 6).
    """

    class Meta:
        model = InscripcionEstudiante
        fields = ["estudiante", "clase"]
        widgets = {
            "estudiante": forms.Select(attrs={"class": INPUT_CLASSES}),
            "clase": forms.Select(attrs={"class": INPUT_CLASSES}),
        }

    def __init__(self, *args, edicion, excluir_inscripcion_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.edicion = edicion
        self.fields["estudiante"].queryset = selectors.listar_estudiantes_disponibles_para_edicion(
            edicion.pk, excluir_inscripcion_id=excluir_inscripcion_id
        )
        self.fields["clase"].queryset = selectors.listar_clases()