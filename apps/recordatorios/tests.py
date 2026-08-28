"""
Pruebas de apps.recordatorios (Fase 14, Subfase 14.9).

Cubre el dominio (modelo, selectors, services), los endpoints
parciales (fragmento correcto + código de estado correcto) y la
mejora progresiva (que el camino sin JavaScript siga existiendo).
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.academico import services as academico_services
from apps.docencia.models import Instructor
from apps.recordatorios import selectors, services
from apps.recordatorios.models import Recordatorio, TipoRecordatorio
from apps.recordatorios.serializers import RecordatorioDTO

U, C = "test_user", "Clave-De-Prueba-8020"
AJAX = {"X-Requested-With": "XMLHttpRequest", "Origin": "http://testserver"}


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)
        cls.clase = academico_services.crear_clase(
            nombre="Turma 206", fecha_inicio=date(2026, 3, 2), fecha_fin=date(2026, 6, 27)
        )
        cls.tipo = TipoRecordatorio.objects.get(nombre="Reunión")
        cls.instructor_a = Instructor.objects.create(nombre="Gabriel", apellido="Folador", cargo="Titular")
        cls.instructor_b = Instructor.objects.create(nombre="Bruno", apellido="Roberto", cargo="Auxiliar")

    def _crear(self, **kw):
        datos = dict(
            clase=self.clase, tipo=self.tipo, numero_semana=1,
            fecha=date(2026, 3, 10), descripcion="Imprimir designaciones",
        )
        datos.update(kw)
        return services.crear_recordatorio(**datos)


class CatalogoTiposTests(Base):
    def test_los_tipos_iniciales_se_cargan_con_la_migracion(self):
        nombres = set(TipoRecordatorio.objects.values_list("nombre", flat=True))
        self.assertTrue({"Reunión", "Ayuda personal", "Impresión"} <= nombres)

    def test_el_nombre_del_tipo_es_unico(self):
        with self.assertRaises(Exception):
            services.crear_tipo(nombre="Reunión")

    def test_el_catalogo_es_editable(self):
        """El motivo de que sea tabla y no lista fija en código."""
        tipo = services.crear_tipo(nombre="Visita de zona", color="VERDE")
        self.assertTrue(TipoRecordatorio.objects.filter(pk=tipo.pk).exists())


class ModeloTests(Base):
    def test_la_semana_cero_es_valida(self):
        """La semana previa al inicio de la escuela (planilla real)."""
        r = self._crear(numero_semana=0, fecha=date(2026, 2, 25))
        self.assertEqual(r.numero_semana, 0)

    def test_la_hora_es_opcional(self):
        self.assertIsNone(self._crear(hora=None).hora)

    def test_puede_tener_dos_responsables(self):
        """La planilla marca "A / B": a veces la tarea es de ambos."""
        r = self._crear(responsables=[self.instructor_a, self.instructor_b])
        self.assertEqual(r.responsables.count(), 2)

    def test_puede_no_tener_responsable(self):
        self.assertEqual(self._crear().responsables.count(), 0)

    def test_orden_cronologico_con_las_sin_hora_al_final(self):
        self._crear(descripcion="Sin hora", hora=None)
        self._crear(descripcion="Temprano", hora="08:00")
        descripciones = list(
            selectors.listar_por_clase(self.clase.pk).values_list("descripcion", flat=True)
        )
        self.assertEqual(descripciones, ["Temprano", "Sin hora"])

    def test_los_recordatorios_cuelgan_de_la_clase(self):
        otra = academico_services.crear_clase(
            nombre="Turma 207", fecha_inicio=date(2026, 7, 1), fecha_fin=date(2026, 11, 1)
        )
        self._crear()
        self.assertEqual(selectors.listar_por_clase(otra.pk).count(), 0)
        self.assertEqual(selectors.listar_por_clase(self.clase.pk).count(), 1)


class ValidacionFechaTests(Base):
    def test_rechaza_fecha_posterior_al_fin_de_la_clase(self):
        with self.assertRaises(ValidationError):
            self._crear(fecha=date(2026, 12, 1))

    def test_rechaza_fecha_absurdamente_anterior(self):
        """Atrapa el error de tipeo en el año."""
        with self.assertRaises(ValidationError):
            self._crear(fecha=date(2025, 3, 10))

    def test_acepta_fecha_previa_al_inicio_dentro_del_margen(self):
        """La semana 0 ocurre ANTES de que empiece la clase."""
        r = self._crear(numero_semana=0, fecha=date(2026, 2, 20))
        self.assertEqual(r.fecha, date(2026, 2, 20))


class AgrupacionPorSemanaTests(Base):
    def test_agrupa_y_ordena_por_numero_de_semana(self):
        self._crear(numero_semana=2, fecha=date(2026, 3, 17))
        self._crear(numero_semana=0, fecha=date(2026, 2, 25))
        self._crear(numero_semana=1)
        bloques = selectors.agrupar_por_semana(selectors.listar_por_clase(self.clase.pk))
        self.assertEqual([b["numero_semana"] for b in bloques], [0, 1, 2])

    def test_cuenta_completadas_y_vencidas_por_bloque(self):
        hoy = date(2026, 4, 1)
        self._crear(descripcion="Vencida", fecha=date(2026, 3, 10))
        r = self._crear(descripcion="Hecha", fecha=date(2026, 3, 11))
        services.alternar_completado(recordatorio=r)
        bloque = selectors.agrupar_por_semana(
            selectors.listar_por_clase(self.clase.pk), hoy=hoy
        )[0]
        self.assertEqual(bloque["total"], 2)
        self.assertEqual(bloque["completadas"], 1)
        self.assertEqual(bloque["vencidas"], 1)

    def test_una_completada_nunca_cuenta_como_vencida(self):
        r = self._crear(fecha=date(2026, 3, 5))
        services.alternar_completado(recordatorio=r)
        bloque = selectors.agrupar_por_semana(
            selectors.listar_por_clase(self.clase.pk), hoy=date(2026, 4, 1)
        )[0]
        self.assertEqual(bloque["vencidas"], 0)

    def test_la_fecha_de_referencia_es_inyectable(self):
        """
        Subfase 14.8: la comparación ocurre en el servidor y `hoy` se
        recibe como parámetro, para que la prueba no dependa del día en
        que se ejecuta.
        """
        self._crear(fecha=date(2026, 3, 10))
        antes = selectors.agrupar_por_semana(
            selectors.listar_por_clase(self.clase.pk), hoy=date(2026, 3, 1)
        )[0]
        despues = selectors.agrupar_por_semana(
            selectors.listar_por_clase(self.clase.pk), hoy=date(2026, 4, 1)
        )[0]
        self.assertEqual(antes["vencidas"], 0)
        self.assertEqual(despues["vencidas"], 1)


class ServicesTests(Base):
    def test_alternar_completado_es_reversible(self):
        r = self._crear()
        services.alternar_completado(recordatorio=r)
        self.assertTrue(r.completado)
        services.alternar_completado(recordatorio=r)
        self.assertFalse(r.completado)

    def test_completar_una_vencida_no_valida_la_fecha(self):
        """Ponerse al día con lo atrasado es justamente el caso de uso."""
        r = self._crear(fecha=date(2026, 3, 3))
        services.alternar_completado(recordatorio=r)
        self.assertTrue(r.completado)

    def test_actualizar_sin_mencionar_responsables_no_los_borra(self):
        r = self._crear(responsables=[self.instructor_a])
        services.actualizar_recordatorio(recordatorio=r, descripcion="Otra cosa")
        self.assertEqual(r.responsables.count(), 1)

    def test_actualizar_con_lista_vacia_si_los_borra(self):
        r = self._crear(responsables=[self.instructor_a])
        services.actualizar_recordatorio(recordatorio=r, responsables=[])
        self.assertEqual(r.responsables.count(), 0)

    def test_eliminar(self):
        r = self._crear()
        services.eliminar_recordatorio(recordatorio=r)
        self.assertEqual(Recordatorio.objects.count(), 0)


class DTOTests(Base):
    def test_el_dto_trae_vencida_ya_calculada(self):
        r = self._crear()
        dto = RecordatorioDTO.from_model(selectors.obtener_por_id(r.pk), vencida=True)
        self.assertTrue(dto.vencida)

    def test_responsables_texto_sin_asignar(self):
        r = self._crear()
        dto = RecordatorioDTO.from_model(selectors.obtener_por_id(r.pk))
        self.assertEqual(dto.responsables_texto, "Sin asignar")

    def test_responsables_texto_con_dos(self):
        r = self._crear(responsables=[self.instructor_a, self.instructor_b])
        dto = RecordatorioDTO.from_model(selectors.obtener_por_id(r.pk))
        self.assertIn("Gabriel", dto.responsables_texto)
        self.assertIn("Bruno", dto.responsables_texto)


class LineaDeTiempoViewTests(Base):
    def setUp(self):
        self.client.login(username=U, password=C)

    def test_sin_clase_pide_elegir_una(self):
        r = self.client.get(reverse("recordatorios:linea_tiempo"))
        self.assertContains(r, "Selecciona una clase")
        self.assertIsNone(r.context["semanas"])

    def test_con_clase_muestra_los_bloques(self):
        self._crear()
        r = self.client.get(reverse("recordatorios:linea_tiempo"), {"clase": self.clase.pk})
        self.assertContains(r, "Imprimir designaciones")
        self.assertContains(r, "Semana 1")

    def test_semana_cero_se_muestra_como_semana_previa(self):
        self._crear(numero_semana=0, fecha=date(2026, 2, 25))
        r = self.client.get(reverse("recordatorios:linea_tiempo"), {"clase": self.clase.pk})
        self.assertContains(r, "Semana previa")

    def test_usa_details_para_los_bloques_colapsables(self):
        """HTML5 puro: colapsa sin una línea de JavaScript."""
        self._crear()
        r = self.client.get(reverse("recordatorios:linea_tiempo"), {"clase": self.clase.pk})
        self.assertContains(r, "<details")

    def test_clase_inexistente_da_404(self):
        r = self.client.get(reverse("recordatorios:linea_tiempo"), {"clase": 999999})
        self.assertEqual(r.status_code, 404)

    def test_protegido_sin_sesion(self):
        anon = self.client_class()
        self.assertEqual(anon.get(reverse("recordatorios:linea_tiempo")).status_code, 302)


class EndpointsParcialesTests(Base):
    def setUp(self):
        self.client.login(username=U, password=C)

    def _url(self, nombre, **kw):
        return reverse(f"recordatorios:{nombre}", kwargs={"id_clase": self.clase.pk, **kw})

    def test_form_parcial_devuelve_solo_los_campos(self):
        r = self.client.get(self._url("form_nuevo"), headers=AJAX)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "recordatorios/_form_inner.html")
        self.assertNotContains(r, "<html")

    def test_alta_ajax_valida_devuelve_la_tarjeta(self):
        r = self.client.post(self._url("crear"), {
            "tipo": self.tipo.pk, "numero_semana": 1, "fecha": "2026-03-10",
            "hora": "", "descripcion": "Nueva tarea",
        }, headers=AJAX)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "recordatorios/_tarjeta.html")
        self.assertContains(r, "Nueva tarea")

    def test_alta_ajax_invalida_devuelve_422_con_el_formulario(self):
        """El contrato que la Fase 6 ya estableció para datos inválidos."""
        r = self.client.post(self._url("crear"), {
            "tipo": self.tipo.pk, "numero_semana": 1, "fecha": "2026-12-31",
            "hora": "", "descripcion": "Fuera de rango",
        }, headers=AJAX)
        self.assertEqual(r.status_code, 422)
        self.assertTemplateUsed(r, "recordatorios/_form_inner.html")
        self.assertEqual(Recordatorio.objects.count(), 0)

    def test_completar_ajax_devuelve_la_tarjeta_actualizada(self):
        rec = self._crear()
        r = self.client.post(
            self._url("completar", id_recordatorio=rec.pk), {}, headers=AJAX
        )
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "recordatorios/_tarjeta.html")
        rec.refresh_from_db()
        self.assertTrue(rec.completado)

    def test_completar_no_acepta_get(self):
        """Cambia estado: un GET no debe poder dispararlo."""
        rec = self._crear()
        r = self.client.get(self._url("completar", id_recordatorio=rec.pk))
        self.assertEqual(r.status_code, 405)

    def test_eliminar_ajax_devuelve_204(self):
        rec = self._crear()
        r = self.client.post(
            self._url("eliminar", id_recordatorio=rec.pk), {}, headers=AJAX
        )
        self.assertEqual(r.status_code, 204)
        self.assertEqual(Recordatorio.objects.count(), 0)

    def test_endpoints_parciales_dan_401_sin_sesion(self):
        """AccessControlMixin: 401, no redirect, en peticiones fetch."""
        anon = self.client_class()
        r = anon.get(self._url("form_nuevo"), headers=AJAX)
        self.assertEqual(r.status_code, 401)

    def test_guard_bloquea_antes_de_consultar_la_clase(self):
        """Sin sesión y con clase inexistente: 302 al login, no 404."""
        anon = self.client_class()
        r = anon.get(reverse("recordatorios:form_nuevo", kwargs={"id_clase": 999999}))
        self.assertEqual(r.status_code, 302)


class MejoraProgresivaTests(Base):
    """
    Requisito no negociable de la Subfase 14.6: todo el CRUD debe
    funcionar sin JavaScript.
    """

    def setUp(self):
        self.client.login(username=U, password=C)

    def _url(self, nombre, **kw):
        return reverse(f"recordatorios:{nombre}", kwargs={"id_clase": self.clase.pk, **kw})

    def test_existe_pagina_de_alta_sin_js(self):
        r = self.client.get(self._url("crear"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "recordatorios/recordatorio_form.html")

    def test_alta_sin_js_redirige(self):
        r = self.client.post(self._url("crear"), {
            "tipo": self.tipo.pk, "numero_semana": 1, "fecha": "2026-03-10",
            "hora": "", "descripcion": "Sin JavaScript",
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Recordatorio.objects.filter(descripcion="Sin JavaScript").exists())

    def test_existe_pagina_de_borrado_sin_js(self):
        rec = self._crear()
        r = self.client.get(self._url("eliminar", id_recordatorio=rec.pk))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "recordatorios/recordatorio_confirm_delete.html")

    def test_completar_sin_js_redirige(self):
        rec = self._crear()
        r = self.client.post(self._url("completar", id_recordatorio=rec.pk), {})
        self.assertEqual(r.status_code, 302)
        rec.refresh_from_db()
        self.assertTrue(rec.completado)


class CatalogoTiposCRUDTests(Base):
    """
    Adenda 11: gestión del catálogo desde la propia aplicación, sin
    depender del panel de administración de Django.
    """

    def setUp(self):
        self.client.login(username=U, password=C)

    def test_listado_muestra_los_tipos_y_su_uso(self):
        self._crear()
        r = self.client.get(reverse("recordatorios:tipos_listado"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Reunión")
        self.assertContains(r, "1 recordatorio")

    def test_crear_tipo_desde_la_app(self):
        r = self.client.post(reverse("recordatorios:tipos_crear"),
                             {"nombre": "Visita de zona", "color": "VERDE"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(TipoRecordatorio.objects.filter(nombre="Visita de zona").exists())

    def test_editar_tipo_desde_la_app(self):
        r = self.client.post(
            reverse("recordatorios:tipos_editar", kwargs={"id_tipo": self.tipo.pk}),
            {"nombre": "Reunión general", "color": "AZUL"},
        )
        self.assertEqual(r.status_code, 302)
        self.tipo.refresh_from_db()
        self.assertEqual(self.tipo.nombre, "Reunión general")

    def test_nombre_duplicado_se_rechaza(self):
        r = self.client.post(reverse("recordatorios:tipos_crear"),
                             {"nombre": "Reunión", "color": "AZUL"})
        self.assertEqual(r.status_code, 200)

    def test_alternar_estado(self):
        url = reverse("recordatorios:tipos_alternar_estado", kwargs={"id_tipo": self.tipo.pk})
        self.client.post(url)
        self.tipo.refresh_from_db()
        self.assertFalse(self.tipo.activo)
        self.client.post(url)
        self.tipo.refresh_from_db()
        self.assertTrue(self.tipo.activo)

    def test_alternar_no_acepta_get(self):
        url = reverse("recordatorios:tipos_alternar_estado", kwargs={"id_tipo": self.tipo.pk})
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_no_existe_ruta_de_borrado(self):
        """Se desactiva, no se borra (ver services.alternar_activo_tipo)."""
        with self.assertRaises(Exception):
            reverse("recordatorios:tipos_eliminar", kwargs={"id_tipo": self.tipo.pk})

    def test_un_tipo_inactivo_no_se_ofrece_al_crear(self):
        services.alternar_activo_tipo(tipo=self.tipo)
        disponibles = selectors.listar_tipos_disponibles()
        self.assertNotIn(self.tipo, disponibles)

    def test_editar_un_recordatorio_conserva_su_tipo_desactivado(self):
        """Sin esto, guardar borraría el tipo en silencio."""
        rec = self._crear()
        services.alternar_activo_tipo(tipo=self.tipo)
        disponibles = selectors.listar_tipos_disponibles(incluir_tipo_id=rec.tipo_id)
        self.assertIn(self.tipo, disponibles)

    def test_catalogo_protegido_sin_sesion(self):
        anon = self.client_class()
        self.assertEqual(anon.get(reverse("recordatorios:tipos_listado")).status_code, 302)
