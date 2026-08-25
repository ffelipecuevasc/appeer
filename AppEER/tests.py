"""
Pruebas de AppEER/ (vista raíz + regresión de la Fase 8 sobre la
estructura reestructurada en la Fase 11). Subfase 11.10.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

U, C = "test_user", "Clave-De-Prueba-8020"


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)

    def setUp(self):
        self.client.login(username=U, password=C)

    def test_inicio_muestra_total_clases_no_total_ediciones(self):
        r = self.client.get(reverse("inicio"))
        self.assertIn("total_clases", r.context)
        self.assertNotIn("total_ediciones", r.context)

    def test_inicio_responde_200(self):
        self.assertEqual(self.client.get(reverse("inicio")).status_code, 200)


class RegresionControlDeAccesoTests(TestCase):
    """
    Las 37 vistas de negocio deben seguir protegidas tras la
    reestructuración de la Fase 11 (2 menos que las 39 de la Fase 8:
    se fueron las 5 de EdicionEscuela y ClaseDeleteView, entraron 0
    nuevas — ClaseListView/DetailView/CreateView/UpdateView y las 3 de
    InscripcionEstudiante ya estaban contadas en la Fase 8).
    """
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(U, "", C)

    def test_escuela_protegida_sin_sesion(self):
        anon = self.client_class()
        r = anon.get("/escuela/")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.startswith(reverse("login")))

    def test_escuela_accesible_con_sesion(self):
        self.client.login(username=U, password=C)
        self.assertEqual(self.client.get("/escuela/").status_code, 200)

    def test_no_quedan_rutas_de_edicion_activas(self):
        for nombre in ("academico:ediciones_listado", "academico:ediciones_crear",
                       "academico:clases_eliminar"):
            with self.assertRaises(Exception):
                reverse(nombre)
