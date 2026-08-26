"""
Pruebas de apps.academico.

Fase 11, Subfase 11.10: primeras pruebas VERSIONADAS del proyecto.
Hasta esta fase, toda verificación se hizo con harnesses desechables
(creados y borrados en la misma sesión de trabajo) — el repositorio no
tenía ni un solo test. A partir de acá, cada fase entrega los suyos
como parte del código, no como un paso aparte (Principio 8 del Plan de
Trabajo Maestro 2.0).

Cubre específicamente lo que cambió en esta fase (Adenda 9): la fusión
de EdicionEscuela en Clase, la regla de no doble inscripción
reformulada, y la decisión de negocio "las clases nunca se eliminan".
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.academico import services
from apps.academico.models import Clase, InscripcionEstudiante
from apps.estudiantes import services as estudiantes_services
from apps.estudiantes.models import Estudiante

U, C = "test_user", "Clave-De-Prueba-8020"


class ClaseModeloTests(TestCase):
    """La entidad fusionada: fechas obligatorias, año derivado, rango válido."""

    def test_fecha_inicio_y_fin_son_obligatorias(self):
        clase = Clase(nombre="Turma X")
        with self.assertRaises(ValidationError):
            clase.full_clean()

    def test_anio_se_deriva_de_fecha_inicio(self):
        clase = services.crear_clase(
            nombre="Turma 300", fecha_inicio="2027-03-01", fecha_fin="2027-06-30"
        )
        self.assertEqual(clase.anio, 2027)

    def test_fecha_fin_debe_ser_posterior_a_fecha_inicio(self):
        with self.assertRaises(ValidationError):
            services.crear_clase(
                nombre="Turma Y", fecha_inicio="2027-06-30", fecha_fin="2027-03-01"
            )

    def test_fecha_fin_igual_a_inicio_tambien_se_rechaza(self):
        with self.assertRaises(ValidationError):
            services.crear_clase(
                nombre="Turma Z", fecha_inicio="2027-03-01", fecha_fin="2027-03-01"
            )

    def test_no_existe_operacion_eliminar_clase(self):
        """Decisión de negocio (Adenda 9, Decisión 2), no un olvido."""
        self.assertFalse(hasattr(services, "eliminar_clase"))


class ClaseNuncaSeEliminaTests(TestCase):
    """La regla de negocio de punta a punta: app pública + admin."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)
        cls.clase = services.crear_clase(
            nombre="Turma 206", fecha_inicio="2026-03-02", fecha_fin="2026-06-27"
        )

    def setUp(self):
        self.client.login(username=U, password=C)

    def test_no_existe_ruta_de_borrado_de_clase(self):
        with self.assertRaises(Exception):
            reverse("academico:clases_eliminar", kwargs={"id_clase": self.clase.pk})

    def test_listado_no_ofrece_eliminar(self):
        r = self.client.get(reverse("academico:clases_listado"))
        self.assertNotContains(r, "eliminar/")

    def test_detalle_no_ofrece_eliminar_la_clase(self):
        r = self.client.get(reverse("academico:clases_detalle", kwargs={"id_clase": self.clase.pk}))
        self.assertNotContains(r, f"/escuela/{self.clase.pk}/eliminar/")

    def test_admin_bloquea_el_borrado(self):
        r = self.client.get(f"/admin/academico/clase/{self.clase.pk}/delete/")
        self.assertEqual(r.status_code, 403)

    def test_orm_directo_si_puede_borrar(self):
        """
        La regla vive en la capa de aplicación (Service + Admin), no
        como una restricción de base de datos — es una decisión de
        negocio, no una imposibilidad técnica. Confirma que el borrado
        directo (fuera de la app) sigue siendo posible; lo que no
        existe es un CAMINO desde la interfaz para llegar a él.
        """
        clase = services.crear_clase(nombre="Desechable", fecha_inicio="2020-01-01", fecha_fin="2020-06-01")
        clase.delete()
        self.assertFalse(Clase.objects.filter(pk=clase.pk).exists())


class NoDobleInscripcionTests(TestCase):
    """La regla crítica del Plan Maestro, reformulada sobre Clase (Adenda 9)."""

    @classmethod
    def setUpTestData(cls):
        cls.clase = services.crear_clase(
            nombre="Turma 206", fecha_inicio="2026-03-02", fecha_fin="2026-06-27"
        )
        cls.otra_clase = services.crear_clase(
            nombre="Turma 207", fecha_inicio="2026-07-01", fecha_fin="2026-11-01"
        )
        cls.estudiante = Estudiante.objects.create(
            nombre="Ana", apellido="Pérez", genero=Estudiante.Genero.FEMENINO
        )

    def test_primera_inscripcion_se_acepta(self):
        inscripcion = services.crear_inscripcion(estudiante=self.estudiante, clase=self.clase)
        self.assertEqual(InscripcionEstudiante.objects.count(), 1)
        self.assertEqual(inscripcion.clase_id, self.clase.pk)

    def test_segunda_inscripcion_en_la_misma_clase_se_rechaza(self):
        services.crear_inscripcion(estudiante=self.estudiante, clase=self.clase)
        with self.assertRaises(ValidationError):
            services.crear_inscripcion(estudiante=self.estudiante, clase=self.clase)
        self.assertEqual(InscripcionEstudiante.objects.count(), 1)

    def test_el_mismo_estudiante_si_puede_inscribirse_en_otra_clase(self):
        """No doble inscripción es POR CLASE, no una regla global."""
        services.crear_inscripcion(estudiante=self.estudiante, clase=self.clase)
        services.crear_inscripcion(estudiante=self.estudiante, clase=self.otra_clase)
        self.assertEqual(InscripcionEstudiante.objects.count(), 2)

    def test_uniqueconstraint_de_base_de_datos_como_segunda_barrera(self):
        from django.db import IntegrityError, transaction
        services.crear_inscripcion(estudiante=self.estudiante, clase=self.clase)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InscripcionEstudiante.objects.create(estudiante=self.estudiante, clase=self.clase)


class InscripcionEstudianteClaseProtegeTests(TestCase):
    """Clase.InscripcionEstudiante sigue en PROTECT (Adenda 9, Decisión 2)."""

    def test_borrar_una_clase_con_inscripciones_esta_protegido(self):
        from django.db.models.deletion import ProtectedError

        clase = services.crear_clase(nombre="Turma P", fecha_inicio="2026-01-01", fecha_fin="2026-06-01")
        estudiante = Estudiante.objects.create(
            nombre="Luis", apellido="Soto", genero=Estudiante.Genero.MASCULINO
        )
        services.crear_inscripcion(estudiante=estudiante, clase=clase)
        with self.assertRaises(ProtectedError):
            clase.delete()


class RutaEscuelaTests(TestCase):
    """El prefijo de URL visible cambió de /academico/ a /escuela/ (Subfase 11.8)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)

    def setUp(self):
        self.client.login(username=U, password=C)

    def test_escuela_responde_200(self):
        self.assertEqual(self.client.get("/escuela/").status_code, 200)

    def test_academico_ya_no_existe(self):
        self.assertEqual(self.client.get("/academico/").status_code, 404)

    def test_clases_listado_es_la_raiz_del_modulo(self):
        self.assertEqual(reverse("academico:clases_listado"), "/escuela/")


class InscripcionEnParejaTests(TestCase):
    """
    Adenda 10 (Fase 12.5): un estudiante casado solo puede estar
    inscrito en una clase junto a su cónyuge. La regla se implementa
    haciendo el estado inválido INALCANZABLE, no solo prohibido.
    """

    @classmethod
    def setUpTestData(cls):
        cls.clase = services.crear_clase(
            nombre="Turma 206", fecha_inicio="2026-03-02", fecha_fin="2026-06-27"
        )
        cls.otra_clase = services.crear_clase(
            nombre="Turma 207", fecha_inicio="2026-07-01", fecha_fin="2026-11-01"
        )

    def _matrimonio_completo(self, apellido="Neri"):
        matrimonio = estudiantes_services.crear_matrimonio(fecha_matrimonio="2019-01-26")
        esposo = estudiantes_services.crear_estudiante(
            nombre="Samuel", apellido=apellido,
            genero=Estudiante.Genero.MASCULINO, matrimonio=matrimonio,
        )
        esposa = estudiantes_services.crear_estudiante(
            nombre="Jocilene", apellido=apellido,
            genero=Estudiante.Genero.FEMENINO, matrimonio=matrimonio,
        )
        return esposo, esposa

    def _soltero(self, nombre="Bruno"):
        return estudiantes_services.crear_estudiante(
            nombre=nombre, apellido="Santos", genero=Estudiante.Genero.MASCULINO
        )

    # --- Alta -------------------------------------------------------

    def test_inscribir_a_un_casado_inscribe_tambien_al_conyuge(self):
        esposo, esposa = self._matrimonio_completo()
        services.crear_inscripcion(estudiante=esposo, clase=self.clase)
        self.assertEqual(InscripcionEstudiante.objects.count(), 2)
        self.assertTrue(
            InscripcionEstudiante.objects.filter(estudiante=esposa, clase=self.clase).exists()
        )

    def test_da_igual_cual_de_los_dos_se_inscriba(self):
        esposo, esposa = self._matrimonio_completo()
        services.crear_inscripcion(estudiante=esposa, clase=self.clase)
        self.assertTrue(
            InscripcionEstudiante.objects.filter(estudiante=esposo, clase=self.clase).exists()
        )

    def test_inscribir_al_segundo_conyuge_despues_no_duplica(self):
        """Idempotente: la pareja ya está completa, no se rompe nada."""
        esposo, esposa = self._matrimonio_completo()
        services.crear_inscripcion(estudiante=esposo, clase=self.clase)
        with self.assertRaises(ValidationError):
            services.crear_inscripcion(estudiante=esposa, clase=self.clase)
        self.assertEqual(InscripcionEstudiante.objects.count(), 2)

    def test_un_soltero_se_inscribe_solo(self):
        services.crear_inscripcion(estudiante=self._soltero(), clase=self.clase)
        self.assertEqual(InscripcionEstudiante.objects.count(), 1)

    def test_conyuge_no_registrado_bloquea_con_mensaje_claro(self):
        """Adenda 10, opción A: dato incompleto, no caso válido."""
        matrimonio = estudiantes_services.crear_matrimonio(fecha_matrimonio="2019-01-26")
        solo = estudiantes_services.crear_estudiante(
            nombre="Samuel", apellido="Neri",
            genero=Estudiante.Genero.MASCULINO, matrimonio=matrimonio,
        )
        with self.assertRaises(ValidationError) as ctx:
            services.crear_inscripcion(estudiante=solo, clase=self.clase)
        self.assertIn("cónyuge no está registrado", str(ctx.exception))
        self.assertEqual(InscripcionEstudiante.objects.count(), 0)

    def test_el_bloqueo_es_atomico_no_deja_nada_a_medias(self):
        matrimonio = estudiantes_services.crear_matrimonio(fecha_matrimonio="2019-01-26")
        solo = estudiantes_services.crear_estudiante(
            nombre="Samuel", apellido="Neri",
            genero=Estudiante.Genero.MASCULINO, matrimonio=matrimonio,
        )
        with self.assertRaises(ValidationError):
            services.crear_inscripcion(estudiante=solo, clase=self.clase)
        self.assertFalse(InscripcionEstudiante.objects.filter(estudiante=solo).exists())

    # --- Baja -------------------------------------------------------

    def test_dar_de_baja_a_un_casado_da_de_baja_al_conyuge(self):
        """Sin esto, la regla tendría una puerta trasera."""
        esposo, esposa = self._matrimonio_completo()
        services.crear_inscripcion(estudiante=esposo, clase=self.clase)
        inscripcion = InscripcionEstudiante.objects.get(estudiante=esposo, clase=self.clase)
        services.eliminar_inscripcion(inscripcion=inscripcion)
        self.assertEqual(InscripcionEstudiante.objects.count(), 0)

    def test_baja_de_un_soltero_no_afecta_a_nadie_mas(self):
        soltero = self._soltero()
        otro = self._soltero(nombre="Jefferson")
        services.crear_inscripcion(estudiante=soltero, clase=self.clase)
        services.crear_inscripcion(estudiante=otro, clase=self.clase)
        inscripcion = InscripcionEstudiante.objects.get(estudiante=soltero)
        services.eliminar_inscripcion(inscripcion=inscripcion)
        self.assertEqual(InscripcionEstudiante.objects.count(), 1)

    def test_baja_con_conyuge_no_registrado_no_queda_bloqueada(self):
        """
        Un dato ya inconsistente no debe dejar al usuario sin salida:
        la baja procede igual, sin exigir arreglar el dato primero.
        """
        matrimonio = estudiantes_services.crear_matrimonio(fecha_matrimonio="2019-01-26")
        esposo = estudiantes_services.crear_estudiante(
            nombre="Samuel", apellido="Neri",
            genero=Estudiante.Genero.MASCULINO, matrimonio=matrimonio,
        )
        esposa = estudiantes_services.crear_estudiante(
            nombre="Jocilene", apellido="Neri",
            genero=Estudiante.Genero.FEMENINO, matrimonio=matrimonio,
        )
        services.crear_inscripcion(estudiante=esposo, clase=self.clase)
        # El cónyuge deja de ser estudiante después de inscribirse.
        esposa.delete()
        inscripcion = InscripcionEstudiante.objects.get(estudiante=esposo)
        services.eliminar_inscripcion(inscripcion=inscripcion)
        self.assertEqual(InscripcionEstudiante.objects.count(), 0)

    # --- Edición ----------------------------------------------------

    def test_reasignar_la_inscripcion_de_un_casado_se_rechaza(self):
        esposo, _ = self._matrimonio_completo()
        soltero = self._soltero()
        services.crear_inscripcion(estudiante=esposo, clase=self.clase)
        inscripcion = InscripcionEstudiante.objects.get(estudiante=esposo)
        with self.assertRaises(ValidationError):
            services.actualizar_inscripcion(inscripcion=inscripcion, estudiante=soltero)

    def test_reasignar_hacia_un_casado_tambien_se_rechaza(self):
        esposo, _ = self._matrimonio_completo()
        soltero = self._soltero()
        services.crear_inscripcion(estudiante=soltero, clase=self.otra_clase)
        inscripcion = InscripcionEstudiante.objects.get(estudiante=soltero)
        with self.assertRaises(ValidationError):
            services.actualizar_inscripcion(inscripcion=inscripcion, estudiante=esposo)

    def test_reasignar_entre_solteros_sigue_funcionando(self):
        soltero = self._soltero()
        otro = self._soltero(nombre="Jefferson")
        services.crear_inscripcion(estudiante=soltero, clase=self.clase)
        inscripcion = InscripcionEstudiante.objects.get(estudiante=soltero)
        services.actualizar_inscripcion(inscripcion=inscripcion, estudiante=otro)
        inscripcion.refresh_from_db()
        self.assertEqual(inscripcion.estudiante_id, otro.pk)

    # --- Invariante -------------------------------------------------

    def test_ninguna_clase_queda_con_un_casado_solo(self):
        """El invariante que toda la Adenda 10 existe para garantizar."""
        esposo, esposa = self._matrimonio_completo()
        self._soltero()
        services.crear_inscripcion(estudiante=esposo, clase=self.clase)
        services.crear_inscripcion(estudiante=self._soltero("Alex"), clase=self.clase)

        for inscripcion in InscripcionEstudiante.objects.filter(clase=self.clase):
            estudiante = inscripcion.estudiante
            if estudiante.matrimonio_id is None:
                continue
            conyuges = estudiante.matrimonio.estudiantes.exclude(pk=estudiante.pk)
            for conyuge in conyuges:
                self.assertTrue(
                    InscripcionEstudiante.objects.filter(
                        estudiante=conyuge, clase=self.clase
                    ).exists(),
                    f"{estudiante} quedó inscrito sin su cónyuge",
                )
