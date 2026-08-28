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
from apps.academico import services as academico_services
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


class AgrupacionTests(TestCase):
    """Fase 13, Subfase 13.1: los tres grupos del listado."""

    @classmethod
    def setUpTestData(cls):
        cls.clase = academico_services.crear_clase(
            nombre="Turma 206", fecha_inicio="2026-03-02", fecha_fin="2026-06-27"
        )
        matrimonio = services.crear_matrimonio(fecha_matrimonio="2019-01-26")
        cls.esposo = services.crear_estudiante(
            nombre="Samuel", apellido="Neri", genero=MASC, matrimonio=matrimonio
        )
        cls.esposa = services.crear_estudiante(
            nombre="Jocilene", apellido="Neri", genero=FEM, matrimonio=matrimonio
        )
        cls.soltero = services.crear_estudiante(nombre="Bruno", apellido="Santos", genero=MASC)
        cls.soltera = services.crear_estudiante(nombre="Ana", apellido="Cristina", genero=FEM)
        for e in (cls.esposo, cls.soltero, cls.soltera):
            academico_services.crear_inscripcion(estudiante=e, clase=cls.clase)

    def _agrupar(self, query=None):
        return selectors.agrupar_estudiantes(
            selectors.listar_estudiantes_de_clase(self.clase.pk, query=query)
        )

    def test_reparte_en_los_tres_grupos(self):
        g = self._agrupar()
        self.assertEqual(len(g["matrimonios"]), 1)
        self.assertEqual(len(g["matrimonios"][0]), 2)
        self.assertEqual(len(g["hombres_solteros"]), 1)
        self.assertEqual(len(g["mujeres_solteras"]), 1)

    def test_los_casados_no_caen_en_solteros(self):
        g = self._agrupar()
        solteros = g["hombres_solteros"] + g["mujeres_solteras"]
        self.assertNotIn(self.esposo, solteros)
        self.assertNotIn(self.esposa, solteros)

    def test_el_varon_va_primero_en_la_tarjeta_de_matrimonio(self):
        """Orden estable, no dependiente del orden alfabético."""
        g = self._agrupar()
        self.assertEqual(g["matrimonios"][0][0], self.esposo)

    def test_solo_incluye_a_los_inscritos_en_esa_clase(self):
        services.crear_estudiante(nombre="Externo", apellido="Zeta", genero=MASC)
        g = self._agrupar()
        nombres = [e.nombre for e in g["hombres_solteros"]]
        self.assertNotIn("Externo", nombres)

    def test_busqueda_puede_dejar_un_matrimonio_incompleto(self):
        """
        Caso de borde real: la Adenda 10 garantiza parejas completas en
        la clase, pero una búsqueda puede coincidir con uno solo. No
        debe romperse ni reclasificarlo como soltero.
        """
        g = self._agrupar(query="Samuel")
        self.assertEqual(len(g["matrimonios"]), 1)
        self.assertEqual(len(g["matrimonios"][0]), 1)
        self.assertEqual(g["hombres_solteros"], [])

    def test_clase_vacia_devuelve_los_tres_grupos_vacios(self):
        otra = academico_services.crear_clase(
            nombre="Turma 999", fecha_inicio="2027-01-01", fecha_fin="2027-06-01"
        )
        g = selectors.agrupar_estudiantes(selectors.listar_estudiantes_de_clase(otra.pk))
        self.assertEqual(g["matrimonios"], [])
        self.assertEqual(g["hombres_solteros"], [])
        self.assertEqual(g["mujeres_solteras"], [])


class ListadoPorClaseTests(TestCase):
    """Subfases 13.4 a 13.6: la pantalla completa."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)
        cls.clase = academico_services.crear_clase(
            nombre="Turma 206", fecha_inicio="2026-03-02", fecha_fin="2026-06-27"
        )
        cls.soltero = services.crear_estudiante(nombre="Bruno", apellido="Santos", genero=MASC)
        academico_services.crear_inscripcion(estudiante=cls.soltero, clase=cls.clase)

    def setUp(self):
        self.client.login(username=U, password=C)

    def test_sin_clase_pide_elegir_una(self):
        r = self.client.get(reverse("estudiantes:listado"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Selecciona una clase")
        self.assertIsNone(r.context["grupos"])

    def test_sin_clase_no_muestra_estudiantes(self):
        r = self.client.get(reverse("estudiantes:listado"))
        self.assertNotContains(r, "Bruno")

    def test_con_clase_muestra_los_grupos(self):
        r = self.client.get(reverse("estudiantes:listado"), {"clase": self.clase.pk})
        self.assertContains(r, "Bruno")
        self.assertContains(r, "Hombres solteros")
        self.assertEqual(r.context["total"], 1)

    def test_clase_inexistente_da_404(self):
        r = self.client.get(reverse("estudiantes:listado"), {"clase": 999999})
        self.assertEqual(r.status_code, 404)

    def test_el_listado_ya_no_ofrece_editar_ni_eliminar(self):
        """Subfase 13.6: esas acciones viven solo en el detalle."""
        r = self.client.get(reverse("estudiantes:listado"), {"clase": self.clase.pk})
        self.assertNotContains(r, f"/estudiantes/{self.soltero.pk}/editar/")
        self.assertNotContains(r, f"/estudiantes/{self.soltero.pk}/eliminar/")

    def test_el_detalle_si_ofrece_editar_y_eliminar(self):
        r = self.client.get(reverse("estudiantes:detalle", kwargs={"id_estudiante": self.soltero.pk}))
        self.assertContains(r, f"/estudiantes/{self.soltero.pk}/editar/")
        self.assertContains(r, f"/estudiantes/{self.soltero.pk}/eliminar/")

    def test_la_tarjeta_enlaza_al_detalle(self):
        r = self.client.get(reverse("estudiantes:listado"), {"clase": self.clase.pk})
        self.assertContains(r, f"/estudiantes/{self.soltero.pk}/")

    def test_busqueda_ajax_devuelve_el_fragmento_de_grupos(self):
        r = self.client.get(
            reverse("estudiantes:listado"),
            {"clase": self.clase.pk, "q": "Bruno"},
            headers={"X-Requested-With": "XMLHttpRequest", "Origin": "http://testserver"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "estudiantes/_estudiante_grupos.html")
        self.assertContains(r, "Bruno")

    def test_busqueda_sin_coincidencias_lo_dice(self):
        r = self.client.get(
            reverse("estudiantes:listado"), {"clase": self.clase.pk, "q": "zzzz"}
        )
        self.assertContains(r, "No se encontraron estudiantes")

    def test_sigue_protegido_sin_sesion(self):
        anon = self.client_class()
        r = anon.get(reverse("estudiantes:listado"), {"clase": self.clase.pk})
        self.assertEqual(r.status_code, 302)


class CatalogoResponsabilidadesCRUDTests(TestCase):
    """Adenda 11: gestión del catálogo desde la propia aplicación."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)
        cls.anciano = Responsabilidad.objects.get(nombre="Anciano")

    def setUp(self):
        self.client.login(username=U, password=C)

    def test_listado_muestra_las_responsabilidades_y_su_uso(self):
        services.crear_estudiante(nombre="Luis", apellido="Soto", genero=MASC,
                                  responsabilidades=[self.anciano])
        r = self.client.get(reverse("estudiantes:responsabilidades_listado"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Anciano")
        self.assertContains(r, "1 estudiante")

    def test_crear_desde_la_app(self):
        r = self.client.post(reverse("estudiantes:responsabilidades_crear"),
                             {"nombre": "Precursor Especial"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Responsabilidad.objects.filter(nombre="Precursor Especial").exists())

    def test_editar_desde_la_app(self):
        r = self.client.post(
            reverse("estudiantes:responsabilidades_editar",
                    kwargs={"id_responsabilidad": self.anciano.pk}),
            {"nombre": "Anciano de congregación"},
        )
        self.assertEqual(r.status_code, 302)
        self.anciano.refresh_from_db()
        self.assertEqual(self.anciano.nombre, "Anciano de congregación")

    def test_nombre_duplicado_se_rechaza(self):
        r = self.client.post(reverse("estudiantes:responsabilidades_crear"),
                             {"nombre": "Anciano"})
        self.assertEqual(r.status_code, 200)

    def test_alternar_estado(self):
        url = reverse("estudiantes:responsabilidades_alternar_estado",
                      kwargs={"id_responsabilidad": self.anciano.pk})
        self.client.post(url)
        self.anciano.refresh_from_db()
        self.assertFalse(self.anciano.activo)
        self.client.post(url)
        self.anciano.refresh_from_db()
        self.assertTrue(self.anciano.activo)

    def test_alternar_no_acepta_get(self):
        url = reverse("estudiantes:responsabilidades_alternar_estado",
                      kwargs={"id_responsabilidad": self.anciano.pk})
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_no_existe_ruta_de_borrado(self):
        with self.assertRaises(Exception):
            reverse("estudiantes:responsabilidades_eliminar",
                    kwargs={"id_responsabilidad": self.anciano.pk})

    def test_una_inactiva_no_se_ofrece_al_registrar(self):
        services.alternar_activo_responsabilidad(responsabilidad=self.anciano)
        self.assertNotIn(self.anciano, selectors.listar_responsabilidades_disponibles())

    def test_editar_un_estudiante_conserva_su_responsabilidad_desactivada(self):
        """Sin esto, guardar se la quitaría en silencio."""
        estudiante = services.crear_estudiante(nombre="Luis", apellido="Soto", genero=MASC,
                                               responsabilidades=[self.anciano])
        services.alternar_activo_responsabilidad(responsabilidad=self.anciano)
        disponibles = selectors.listar_responsabilidades_disponibles(
            incluir_ids=[self.anciano.pk]
        )
        self.assertIn(self.anciano, disponibles)
        # Y el estudiante la conserva tras una edición que no la menciona.
        services.actualizar_estudiante(estudiante=estudiante, nombre="Luis Alberto")
        self.assertEqual(estudiante.responsabilidades.count(), 1)

    def test_catalogo_protegido_sin_sesion(self):
        anon = self.client_class()
        self.assertEqual(
            anon.get(reverse("estudiantes:responsabilidades_listado")).status_code, 302
        )
