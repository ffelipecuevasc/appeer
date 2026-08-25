"""
Pruebas de apps.asignaciones. Fase 11, Subfase 11.10.

Cubre la simplificación de _validar_coherencia_con_programacion tras
la fusión de EdicionEscuela en Clase (Adenda 9): antes cruzaba clase +
edición de la programación por separado; ahora es una sola condición,
más una verificación de sanidad nueva (que la programación pertenezca
a la clase de la pareja).
"""
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.academico import services as academico_services
from apps.asignaciones import services
from apps.asignaciones.models import Pareja
from apps.docencia.models import Instructor, Tema
from apps.estudiantes.models import Estudiante
from apps.planificacion import services as planificacion_services


class CoherenciaParejaProgramacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.clase = academico_services.crear_clase(
            nombre="Turma 206", fecha_inicio="2026-03-02", fecha_fin="2026-06-27"
        )
        cls.otra_clase = academico_services.crear_clase(
            nombre="Turma 207", fecha_inicio="2026-07-01", fecha_fin="2026-11-01"
        )
        cls.ana = Estudiante.objects.create(nombre="Ana", apellido="Pérez", genero=Estudiante.Genero.FEMENINO)
        cls.luis = Estudiante.objects.create(nombre="Luis", apellido="Soto", genero=Estudiante.Genero.MASCULINO)
        academico_services.crear_inscripcion(estudiante=cls.ana, clase=cls.clase)
        academico_services.crear_inscripcion(estudiante=cls.luis, clase=cls.clase)

        instructor = Instructor.objects.create(nombre="Marta", apellido="Rojas", cargo="Instructora")
        tema = Tema.objects.create(titulo_tema="Lectura pública", activo=True)
        cls.programacion = planificacion_services.crear_programacion(
            clase=cls.clase, codigo_clase="C-01", numero_semana=1,
            dia_semana="Martes", numero_aula=1, instructor=instructor, tema=tema,
        )
        cls.programacion_de_otra_clase = planificacion_services.crear_programacion(
            clase=cls.otra_clase, codigo_clase="D-01", numero_semana=1,
            dia_semana="Jueves", numero_aula=1, instructor=instructor, tema=tema,
        )

    def test_pareja_con_programacion_de_su_propia_clase_se_acepta(self):
        pareja = services.crear_pareja(
            clase=self.clase, estudiante_1=self.ana, estudiante_2=self.luis,
            programacion=self.programacion,
        )
        self.assertEqual(Pareja.objects.count(), 1)
        self.assertEqual(pareja.programacion_id, self.programacion.pk)

    def test_verificacion_de_sanidad_nueva_rechaza_programacion_de_otra_clase(self):
        """
        La verificación que la fusión hizo posible (Adenda 9): antes no
        se podía comprobar directamente si una programación pertenecía
        a la clase de la pareja, porque ProgramacionClase no conocía su
        clase. Ahora sí, y el Service la rechaza.
        """
        with self.assertRaises(ValidationError):
            services.crear_pareja(
                clase=self.clase, estudiante_1=self.ana, estudiante_2=self.luis,
                programacion=self.programacion_de_otra_clase,
            )
        self.assertEqual(Pareja.objects.count(), 0)

    def test_estudiante_no_inscrito_en_la_clase_se_rechaza(self):
        externo = Estudiante.objects.create(
            nombre="Pedro", apellido="Gómez", genero=Estudiante.Genero.MASCULINO
        )
        with self.assertRaises(ValidationError):
            services.crear_pareja(
                clase=self.clase, estudiante_1=self.ana, estudiante_2=externo,
                programacion=self.programacion,
            )

    def test_pareja_sin_programacion_no_valida_coherencia(self):
        """programacion=None sigue siendo válido — no exige coherencia si no se indicó."""
        pareja = services.crear_pareja(clase=self.clase, estudiante_1=self.ana, estudiante_2=self.luis)
        self.assertIsNone(pareja.programacion)
