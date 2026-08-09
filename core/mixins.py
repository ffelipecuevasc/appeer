"""
Mixins de vista compartidos entre apps (control de acceso, paginación,
respuesta parcial). Se implementan a medida que se construyen las
vistas en las Fases 1 a 6, más el mixin de control de acceso de la
Subfase 8.2.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse


class AjaxRequestMixin:
    """
    Detecta si la petición actual viene marcada como AJAX (header
    X-Requested-With: XMLHttpRequest, que static/js/core/http.js
    inyecta automáticamente en toda petición hecha con AppEER.http).

    Usado por las vistas que responden distinto ante una petición
    fetch que ante una carga de página completa: fragmento parcial
    en vez de la página completa (Subfase 6.2, lectura) o fragmento
    de confirmación/errores en vez de redirect (Subfase 6.4, escritura).
    """

    def is_ajax(self):
        return self.request.headers.get("X-Requested-With") == "XMLHttpRequest"


class AccessControlMixin(AjaxRequestMixin, LoginRequiredMixin):
    """
    Mixin de control de acceso (Subfase 8.2) — el que el Plan de
    Trabajo ya daba por existente en este archivo antes de que
    existiera (ver Paso 0 de la Fase 8). Envoltorio delgado sobre
    LoginRequiredMixin de Django: no reimplementa nada de la
    autenticación por sesión (Plan Maestro, sección 10), agrega
    exactamente una cosa.

    Por qué no basta LoginRequiredMixin solo: su handle_no_permission()
    por defecto siempre redirige a LOGIN_URL. Correcto para una vista
    de página completa (EstudianteListView, ParejaCreateView cuando
    llega por navegación normal, etc.) — incorrecto para los dos
    endpoints parciales de la Fase 6 (búsqueda en vivo de estudiantes,
    creación de pareja por fetch): estudiantes-search.js y
    pareja-form.js esperan un fragmento HTML o una confirmación desde
    ese endpoint, nunca una redirección hacia una página de login
    completa que no saben interpretar.

    Hereda de AjaxRequestMixin (no reimplementa is_ajax(), lo reusa)
    para poder distinguir ambos casos, tanto en vistas que hoy ya
    declaraban AjaxRequestMixin por separado (EstudianteListView,
    ParejaCreateView — este mixin lo reemplaza, no se necesitan los
    dos) como en las que no.

    401, no 403: se reserva 403 (y errors/403.html) para lo que ya
    significa en el proyecto desde la Fase 7 — CSRF inválido o
    permiso denegado con sesión activa (CSRF_FAILURE_VIEW,
    settings/base.py). 401 es lo semánticamente correcto acá: "no
    estás identificado", no "no tienes permiso para esto".

    Caso de borde conocido, aceptado y no resuelto acá: si la sesión
    expira MIENTRAS la página ya está abierta (no en la carga
    inicial, que sí redirige bien), pareja-form.js igual inserta el
    texto plano de este 401 dentro de #pareja-form-container en vez
    de un fragmento con el estilo del resto del sitio — no rompe
    nada, pero no es tan prolijo. Resolverlo bien implicaría que
    pareja-form.js distinga un 401 de un 422, lo que excede el
    alcance de la 8.2 (tocaría un módulo de una fase ya cerrada).
    """

    def handle_no_permission(self):
        if self.is_ajax():
            return HttpResponse(
                "No autenticado. Actualiza la página e inicia sesión de nuevo.",
                status=401,
                content_type="text/plain; charset=utf-8",
            )
        return super().handle_no_permission()

    def bloqueo_si_no_autenticado(self, request):
        """
        Guard explícito para vistas que sobreescriben su propio
        dispatch() (Subfase 8.2, Paso 0 detectó esto en
        InscripcionEstudianteCreateView, ParejaPorClaseListView y
        ParejaCreateView, las tres resuelven un objeto de la URL en
        su dispatch() ANTES de llamar a super().dispatch()).

        Por qué hace falta: Python siempre ejecuta el dispatch()
        definido en la clase más derivada, sin importar el orden de
        los mixins en la declaración de la clase. El dispatch() de
        LoginRequiredMixin (heredado a través de este mixin) solo se
        alcanza cuando esas vistas llaman a su propio super()
        dispatch() — es decir, DESPUÉS de la consulta a base de datos
        que hacen antes de esa llamada. Sin este guard, una petición
        sin sesión con un id inexistente en la URL recibiría un 404
        antes que el 302 a login, filtrando (sin exponer datos reales)
        si un id existe o no a alguien sin sesión.

        Uso: primera línea del dispatch() propio de la vista.
            def dispatch(self, request, *args, **kwargs):
                bloqueo = self.bloqueo_si_no_autenticado(request)
                if bloqueo is not None:
                    return bloqueo
                self.clase = ...  # consulta a la base de datos

        Devuelve la respuesta de "no autenticado" (misma que
        handle_no_permission) si corresponde, o None si la vista
        puede seguir con su propia lógica con normalidad.
        """
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return None