"""
Pruebas de apps.planificacion. Fase 11, Subfase 11.10.

Cubre específicamente el repunte de ProgramacionClase de EdicionEscuela
a Clase (Adenda 9): que la FK apunte donde corresponde, que el filtro
de horario funcione por clase, y que el DTO exponga clase_nombre en
vez de edicion_nombre.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.academico import services as academico_services
from apps.docencia.models import Instructor, Tema
from apps.planificacion import services
from apps.planificacion.models import ProgramacionClase
from apps.planificacion.serializers import ProgramacionClaseDTO

U, C = "test_user", "Clave-De-Prueba-8020"


class ProgramacionClaseApuntaAClaseTests(TestCase):
    """El corazón de la Adenda 9 para este módulo: la FK correcta."""

    @classmethod
    def setUpTestData(cls):
        cls.clase = academico_services.crear_clase(
            nombre="Turma 206", fecha_inicio="2026-03-02", fecha_fin="2026-06-27"
        )
        cls.instructor = Instructor.objects.create(nombre="Marta", apellido="Rojas", cargo="Instructora")
        cls.tema = Tema.objects.create(titulo_tema="Lectura pública", activo=True)

    def test_crear_programacion_usa_clase_no_edicion(self):
        programacion = services.crear_programacion(
            clase=self.clase, codigo_clase="C-01", numero_semana=1,
            dia_semana="Martes", numero_aula=1,
            instructor=self.instructor, tema=self.tema,
        )
        self.assertEqual(programacion.clase_id, self.clase.pk)
        self.assertFalse(hasattr(programacion, "edicion_id"))

    def test_dto_expone_clase_nombre_no_edicion_nombre(self):
        programacion = services.crear_programacion(
            clase=self.clase, codigo_clase="C-02", numero_semana=1,
            dia_semana="Miércoles", numero_aula=2,
            instructor=self.instructor, tema=self.tema,
        )
        dto = ProgramacionClaseDTO.from_model(
            ProgramacionClase.objects.select_related("clase", "instructor", "tema").get(pk=programacion.pk)
        )
        self.assertEqual(dto.clase_nombre, "Turma 206")
        self.assertFalse(hasattr(dto, "edicion_nombre"))


class FiltroDeHorarioPorClaseTests(TestCase):
    """El filtro del listado de horario, antes por edición, ahora por clase."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)
        cls.clase_a = academico_services.crear_clase(
            nombre="Turma A", fecha_inicio="2026-01-01", fecha_fin="2026-06-01"
        )
        cls.clase_b = academico_services.crear_clase(
            nombre="Turma B", fecha_inicio="2026-07-01", fecha_fin="2026-11-01"
        )
        instructor = Instructor.objects.create(nombre="Marta", apellido="Rojas", cargo="Instructora")
        tema = Tema.objects.create(titulo_tema="Lectura pública", activo=True)
        services.crear_programacion(
            clase=cls.clase_a, codigo_clase="A-01", numero_semana=1,
            dia_semana="Lunes", numero_aula=1, instructor=instructor, tema=tema,
        )
        services.crear_programacion(
            clase=cls.clase_b, codigo_clase="B-01", numero_semana=1,
            dia_semana="Lunes", numero_aula=1, instructor=instructor, tema=tema,
        )

    def setUp(self):
        self.client.login(username=U, password=C)

    def test_sin_filtro_muestra_todas(self):
        r = self.client.get(reverse("planificacion:programaciones_listado"))
        self.assertContains(r, "A-01")
        self.assertContains(r, "B-01")

    def test_filtro_por_clase_a_muestra_solo_la_suya(self):
        r = self.client.get(
            reverse("planificacion:programaciones_listado"), {"clase": self.clase_a.pk}
        )
        self.assertContains(r, "A-01")
        self.assertNotContains(r, "B-01")
