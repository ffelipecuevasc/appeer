"""
Middleware de validación de peticiones a endpoints parciales.
Responsabilidad: confirmar el origen de las peticiones fetch del JS
vanilla antes de que lleguen a la vista. Se implementa en la Fase 7.
"""
from urllib.parse import urlparse

from django.http import HttpResponseForbidden


class PartialRequestValidationMiddleware:
    """
    Valida el origen de toda petición marcada como parcial/AJAX
    (header X-Requested-With: XMLHttpRequest — la misma marca que
    static/js/core/http.js inyecta automáticamente, y que
    AjaxRequestMixin usa para decidir si una vista responde con un
    fragmento en vez de la página completa).

    Por qué hace falta además de CSRF: CSRF ya valida el Origin en
    peticiones HTTPS de escritura (POST/PUT/PATCH/DELETE) — pero por
    diseño no cubre peticiones GET, que es exactamente el caso de la
    búsqueda en vivo de la Subfase 6.2. X-Requested-With, solo, no
    prueba nada: cualquier cliente (curl, Postman, otro sitio) puede
    mandarlo sin ser realmente nuestro propio JS corriendo en una
    página nuestra. Este middleware cierra ese hueco para ambos
    métodos, exigiendo que el Origin o el Referer de la petición
    coincidan con el host que la está sirviendo.

    Se ubica después de AuthenticationMiddleware (posición que pide
    el Plan de Trabajo para esta subfase), aunque no depende de
    sesión ni de usuario autenticado.
    """

    AJAX_HEADER = "X-Requested-With"
    AJAX_HEADER_VALUE = "XMLHttpRequest"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.headers.get(self.AJAX_HEADER) == self.AJAX_HEADER_VALUE:
            if not self._origen_confiable(request):
                return HttpResponseForbidden(
                    "Origen no válido para una petición parcial."
                )
        return self.get_response(request)

    def _origen_confiable(self, request):
        origin = request.headers.get("Origin")
        if origin:
            return self._host_coincide(origin, request)

        referer = request.headers.get("Referer")
        if referer:
            return self._host_coincide(referer, request)

        # Sin Origin ni Referer: una petición fetch genuina, hecha
        # por AppEER.http desde una página nuestra, casi siempre trae
        # al menos una de las dos. Su ausencia total es sospechosa
        # para una petición que se anuncia como AJAX — se rechaza.
        return False

    @staticmethod
    def _host_coincide(url_value, request):
        parsed = urlparse(url_value)
        if not parsed.netloc:
            return False
        return parsed.netloc == request.get_host()
