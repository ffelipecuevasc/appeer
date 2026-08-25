"""
Formularios de apps.academico para el CRUD público de Clase e
InscripcionEstudiante.

Fase 11: EdicionEscuelaForm desapareció junto con la entidad que
representaba (Adenda 9).
"""
from django import forms
from apps.academico import selectors
from apps.academico.models import Clase, InscripcionEstudiante

INPUT_CLASSES = (
    "w-full px-4 py-2.5 rounded-xl border border-brand-border bg-white "
    "text-brand-text text-sm focus:outline-none focus:ring-2 "
    "focus:ring-brand-accent focus:border-brand-accent transition-shadow"
)


class ClaseForm(forms.ModelForm):
    """
    Fase 11: `anio` salió de los campos del formulario (ya no es un
    campo del modelo, es una property derivada — Adenda 9, Decisión 1)
    y entraron `fecha_inicio`/`fecha_fin`, ambas obligatorias.
    """

    class Meta:
        model = Clase
        fields = ["nombre", "fecha_inicio", "fecha_fin"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "fecha_inicio": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
        }


class InscripcionEstudianteForm(forms.ModelForm):
    """
    Formulario de alta/edición de InscripcionEstudiante, siempre en el
    contexto de una Clase fija (pasada por la vista, nunca elegida en
    este formulario): así el <select> de estudiantes se puede filtrar
    server-side contra esa clase sin necesitar JavaScript.

    Fase 11: antes recibía `edicion` como kwarg fijo y `clase` como
    campo elegible dentro del propio formulario (una inscripción
    apuntaba a las dos). Con la fusión (Adenda 9), la única referencia
    académica es `clase`, así que pasa a ser el kwarg fijo — ya no hay
    nada que elegir aparte del estudiante.
    """

    class Meta:
        model = InscripcionEstudiante
        fields = ["estudiante"]
        widgets = {
            "estudiante": forms.Select(attrs={"class": INPUT_CLASSES}),
        }

    def __init__(self, *args, clase, excluir_inscripcion_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.clase = clase
        self.fields["estudiante"].queryset = selectors.listar_estudiantes_disponibles_para_clase(
            clase.pk, excluir_inscripcion_id=excluir_inscripcion_id
        )
