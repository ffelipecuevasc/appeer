"""
Formularios de apps.docencia para el CRUD público de Instructor y Tema.
"""
from django import forms

from apps.docencia.models import Instructor, Tema

INPUT_CLASSES = (
    "w-full px-4 py-2.5 rounded-xl border border-brand-border bg-white "
    "text-brand-text text-sm focus:outline-none focus:ring-2 "
    "focus:ring-brand-accent focus:border-brand-accent transition-shadow"
)


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = ["nombre", "apellido", "cargo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "apellido": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "cargo": forms.TextInput(attrs={"class": INPUT_CLASSES}),
        }


class TemaForm(forms.ModelForm):
    activo = forms.TypedChoiceField(
        choices=((True, "Activo"), (False, "Inactivo")),
        coerce=lambda valor: valor == "True",
        widget=forms.RadioSelect,
        label="Estado",
        help_text="Determina si el tema está disponible para nueva programación.",
    )

    class Meta:
        model = Tema
        fields = ["titulo_tema", "activo"]
        widgets = {
            "titulo_tema": forms.TextInput(attrs={"class": INPUT_CLASSES}),
        }