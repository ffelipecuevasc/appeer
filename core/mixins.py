"""
Mixins de vista compartidos entre apps (control de acceso, paginación,
respuesta parcial). Se implementan a medida que se construyen las
vistas en las Fases 1 a 6.
"""


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