"""
Formularios de apps.recordatorios.

El camino sin JavaScript (mejora progresiva, requisito no negociable
de la Subfase 14.6) usa estos mismos formularios en páginas propias;
el camino con JavaScript los usa para renderizar el fragmento parcial.
Una sola definición sirve a los dos, así no hay dos validaciones que
mantener sincronizadas.
"""
from django import forms

from apps.docencia.models import Instructor
from apps.recordatorios import selectors
from apps.recordatorios.models import Recordatorio, TipoRecordatorio

INPUT_CLASSES = (
    "w-full px-4 py-2.5 rounded-xl border border-brand-border bg-white "
    "text-brand-text text-sm focus:outline-none focus:ring-2 "
    "focus:ring-brand-accent focus:border-brand-accent transition-shadow"
)


class RecordatorioForm(forms.ModelForm):
    """
    La clase NO es un campo del formulario: viene fija desde la URL,
    igual que en InscripcionEstudianteForm. Un recordatorio siempre se
    crea dentro del cronograma de una clase concreta, así que ofrecerla
    como opción abriría la puerta a moverlo de turma por accidente.
    """

    class Meta:
        model = Recordatorio
        fields = ["tipo", "numero_semana", "fecha", "hora", "descripcion", "responsables"]
        labels = {
            "numero_semana": "Semana",
            "hora": "Hora (opcional)",
            "responsables": "Instructor(es) responsable(s)",
        }
        widgets = {
            "tipo": forms.Select(attrs={"class": INPUT_CLASSES}),
            "numero_semana": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 0}),
            "fecha": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASSES}),
            "hora": forms.TimeInput(attrs={"type": "time", "class": INPUT_CLASSES}),
            "descripcion": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "responsables": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, clase, **kwargs):
        super().__init__(*args, **kwargs)
        self.clase = clase
        # Solo tipos activos, más el actual si quedó desactivado
        # después de crearse este recordatorio (Adenda 11).
        tipo_actual_id = self.instance.tipo_id if self.instance and self.instance.pk else None
        self.fields["tipo"].queryset = selectors.listar_tipos_disponibles(
            incluir_tipo_id=tipo_actual_id
        )
        self.fields["responsables"].required = False
        self.fields["responsables"].queryset = Instructor.objects.order_by("apellido", "nombre")
        self.fields["responsables"].label_from_instance = (
            lambda i: f"{i.nombre} {i.apellido}"
        )


class TipoRecordatorioForm(forms.ModelForm):
    """
    Formulario del catálogo de tipos (Adenda 11).

    `activo` no es un campo del formulario: se cambia con el botón
    Activar/Desactivar del listado, no editando el registro. Así hay
    UNA sola forma de cambiar ese estado, y no dos que puedan
    contradecirse.
    """

    class Meta:
        model = TipoRecordatorio
        fields = ["nombre", "color"]
        labels = {"color": "Color de la etiqueta"}
        widgets = {
            "nombre": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "color": forms.Select(attrs={"class": INPUT_CLASSES}),
        }
