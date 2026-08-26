"""
Pruebas de apps.estudiantes.

Fase 12, Subfase 12.5: cubre la entidad Responsabilidad, su relación
muchos-a-muchos con Estudiante, la carga inicial vía migración de
datos, y la no-regresión de la regla crítica de matrimonios.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.estudiantes import selectors, services
from apps.estudiantes.models import Estudiante, Matrimonio, Responsabilidad
from apps.estudiantes.serializers import EstudianteDTO

U, C = "test_user", "Clave-De-Prueba-8020"
MASC = Estudiante.Genero.MASCULINO
FEM = Estudiante.Genero.FEMENINO


class CatalogoInicialTests(TestCase):
    """La migración de datos 0003 debe dejar el catálogo poblado."""

    def test_los_tres_valores_iniciales_existen(self):
        nombres = set(Responsabilidad.objects.values_list("nombre", flat=True))
        self.assertTrue({"Anciano", "Siervo Ministerial", "Precursor Regular"} <= nombres)

    def test_el_nombre_es_unico(self):
        with self.assertRaises(Exception):
            with transaction.atomic():
                Responsabilidad.objects.create(nombre="Anciano")

    def test_la_tabla_intermedia_tiene_el_nombre_acordado(self):
        """
        Sin db_table explícito, Django generaría
        `estudiantes_estudiante_responsabilidades`, rompiendo la
        disciplina de nombres del script SQL auditado.
        """
        tabla = Estudiante.responsabilidades.through._meta.db_table
        self.assertEqual(tabla, "estudiantes_responsabilidades")

    def test_la_tabla_del_catalogo_tiene_el_nombre_acordado(self):
        self.assertEqual(Responsabilidad._meta.db_table, "responsabilidades")


class RelacionEstudianteResponsabilidadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anciano = Responsabilidad.objects.get(nombre="Anciano")
        cls.precursor = Responsabilidad.objects.get(nombre="Precursor Regular")

    def test_estudiante_sin_responsabilidades_es_valido(self):
        estudiante = services.crear_estudiante(nombre="Ana", apellido="Pérez", genero=FEM)
        self.assertEqual(estudiante.responsabilidades.count(), 0)

    def test_estudiante_puede_acumular_varias(self):
        """Un anciano puede ser además precursor regular."""
        estudiante = services.crear_estudiante(
            nombre="Luis", apellido="Soto", genero=MASC,
            responsabilidades=[self.anciano, self.precursor],
        )
        self.assertEqual(estudiante.responsabilidades.count(), 2)

    def test_una_responsabilidad_la_tienen_muchos_estudiantes(self):
        for nombre in ("Luis", "Pedro", "Juan"):
            services.crear_estudiante(
                nombre=nombre, apellido="Soto", genero=MASC,
                responsabilidades=[self.anciano],
            )
        self.assertEqual(self.anciano.estudiantes.count(), 3)

    def test_asignar_la_misma_dos_veces_no_duplica(self):
        estudiante = services.crear_estudiante(nombre="Luis", apellido="Soto", genero=MASC)
        services.asignar_responsabilidad(estudiante=estudiante, responsabilidad=self.anciano)
        services.asignar_responsabilidad(estudiante=estudiante, responsabilidad=self.anciano)
        self.assertEqual(estudiante.responsabilidades.count(), 1)

    def test_quitar_una_que_no_tiene_no_falla(self):
        estudiante = services.crear_estudiante(nombre="Luis", apellido="Soto", genero=MASC)
        services.quitar_responsabilidad(estudiante=estudiante, responsabilidad=self.anciano)
        self.assertEqual(estudiante.responsabilidades.count(), 0)

    def test_actualizar_reemplaza_el_conjunto_completo(self):
        estudiante = services.crear_estudiante(
            nombre="Luis", apellido="Soto", genero=MASC,
            responsabilidades=[self.anciano, self.precursor],
        )
        services.actualizar_estudiante(estudiante=estudiante, responsabilidades=[self.anciano])
        self.assertEqual(
            list(estudiante.responsabilidades.values_list("nombre", flat=True)), ["Anciano"]
        )

    def test_actualizar_sin_mencionar_el_campo_no_las_borra(self):
        """
        El centinela del Service es la AUSENCIA de la clave, no None:
        una edición parcial que no toca responsabilidades debe dejarlas
        intactas, no vaciarlas en silencio.
        """
        estudiante = services.crear_estudiante(
            nombre="Luis", apellido="Soto", genero=MASC, responsabilidades=[self.anciano],
        )
        services.actualizar_estudiante(estudiante=estudiante, nombre="Luis Alberto")
        self.assertEqual(estudiante.responsabilidades.count(), 1)

    def test_actualizar_con_lista_vacia_si_las_borra(self):
        estudiante = services.crear_estudiante(
            nombre="Luis", apellido="Soto", genero=MASC, responsabilidades=[self.anciano],
        )
        services.actualizar_estudiante(estudiante=estudiante, responsabilidades=[])
        self.assertEqual(estudiante.responsabilidades.count(), 0)

    def test_borrar_un_estudiante_no_borra_la_responsabilidad_del_catalogo(self):
        estudiante = services.crear_estudiante(
            nombre="Luis", apellido="Soto", genero=MASC, responsabilidades=[self.anciano],
        )
        services.eliminar_estudiante(estudiante=estudiante)
        self.assertTrue(Responsabilidad.objects.filter(nombre="Anciano").exists())


class SelectorsResponsabilidadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anciano = Responsabilidad.objects.get(nombre="Anciano")
        cls.precursor = Responsabilidad.objects.get(nombre="Precursor Regular")
        cls.con = services.crear_estudiante(
            nombre="Luis", apellido="Soto", genero=MASC, responsabilidades=[cls.anciano],
        )
        cls.sin = services.crear_estudiante(nombre="Ana", apellido="Pérez", genero=FEM)

    def test_listar_responsabilidades_devuelve_el_catalogo(self):
        self.assertGreaterEqual(selectors.listar_responsabilidades().count(), 3)

    def test_listar_estudiantes_por_responsabilidad_filtra(self):
        resultado = selectors.listar_estudiantes_por_responsabilidad(self.anciano.pk)
        self.assertIn(self.con, resultado)
        self.assertNotIn(self.sin, resultado)

    def test_responsabilidad_sin_estudiantes_devuelve_vacio(self):
        self.assertEqual(
            selectors.listar_estudiantes_por_responsabilidad(self.precursor.pk).count(), 0
        )

    def test_listado_no_dispara_consulta_por_estudiante(self):
        """
        prefetch_related debe evitar el N+1 al pintar las pastillas.
        Con 3 estudiantes: 2 consultas (estudiantes + responsabilidades),
        no 4.
        """
        for i in range(3):
            services.crear_estudiante(
                nombre=f"E{i}", apellido="Test", genero=MASC,
                responsabilidades=[self.anciano],
            )
        with self.assertNumQueries(2):
            [EstudianteDTO.from_model(e) for e in selectors.listar_estudiantes()]


class EstudianteDTOTests(TestCase):
    def test_dto_expone_las_responsabilidades(self):
        anciano = Responsabilidad.objects.get(nombre="Anciano")
        services.crear_estudiante(
            nombre="Luis", apellido="Soto", genero=MASC, responsabilidades=[anciano],
        )
        dto = EstudianteDTO.from_model(selectors.listar_estudiantes().first())
        self.assertEqual(len(dto.responsabilidades), 1)
        self.assertEqual(dto.responsabilidades[0].nombre, "Anciano")

    def test_dto_es_inmutable(self):
        estudiante = services.crear_estudiante(nombre="Ana", apellido="Pérez", genero=FEM)
        dto = EstudianteDTO.from_model(selectors.obtener_estudiante_por_id(estudiante.pk))
        self.assertIsInstance(dto.responsabilidades, tuple)


class FormularioYVistasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)
        cls.anciano = Responsabilidad.objects.get(nombre="Anciano")

    def setUp(self):
        self.client.login(username=U, password=C)

    def test_formulario_ofrece_el_campo(self):
        r = self.client.get(reverse("estudiantes:crear"))
        self.assertContains(r, "Responsabilidades")
        self.assertContains(r, "Anciano")

    def test_alta_por_http_persiste_las_responsabilidades(self):
        r = self.client.post(reverse("estudiantes:crear"), {
            "nombre": "Luis", "apellido": "Soto", "genero": MASC,
            "fecha_nacimiento": "", "fecha_bautismo": "",
            "fecha_inicio_servicio_tiempo_completo": "",
            "matrimonio": "", "nueva_fecha_matrimonio": "",
            "responsabilidades": [self.anciano.pk],
        })
        self.assertEqual(r.status_code, 302)
        estudiante = Estudiante.objects.get(nombre="Luis")
        self.assertEqual(estudiante.responsabilidades.count(), 1)

    def test_alta_sin_responsabilidades_funciona(self):
        r = self.client.post(reverse("estudiantes:crear"), {
            "nombre": "Ana", "apellido": "Pérez", "genero": FEM,
            "fecha_nacimiento": "", "fecha_bautismo": "",
            "fecha_inicio_servicio_tiempo_completo": "",
            "matrimonio": "", "nueva_fecha_matrimonio": "",
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Estudiante.objects.get(nombre="Ana").responsabilidades.count(), 0)

    def test_detalle_muestra_las_pastillas(self):
        estudiante = services.crear_estudiante(
            nombre="Luis", apellido="Soto", genero=MASC, responsabilidades=[self.anciano],
        )
        r = self.client.get(reverse("estudiantes:detalle", kwargs={"id_estudiante": estudiante.pk}))
        self.assertContains(r, "Anciano")


class NoRegresionMatrimonioTests(TestCase):
    """La regla crítica de la Fase 1 sigue vigente tras los cambios."""

    def test_maximo_dos_integrantes_por_matrimonio(self):
        matrimonio = services.crear_matrimonio(fecha_matrimonio="2015-03-14")
        services.crear_estudiante(nombre="Luis", apellido="Soto", genero=MASC, matrimonio=matrimonio)
        services.crear_estudiante(nombre="Ana", apellido="Soto", genero=FEM, matrimonio=matrimonio)
        with self.assertRaises(ValidationError):
            services.crear_estudiante(
                nombre="Pedro", apellido="Soto", genero=MASC, matrimonio=matrimonio
            )
        self.assertEqual(matrimonio.estudiantes.count(), 2)
