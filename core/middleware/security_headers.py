"""
Middleware de cabeceras de seguridad adicionales.
Responsabilidad: añadir cabeceras HTTP complementarias a las que ya
provee SecurityMiddleware de Django. Se implementa en la Fase 7.
"""


class SecurityHeadersMiddleware:
    """
    Agrega cabeceras HTTP que Django no cubre por defecto:
    Content-Security-Policy, Permissions-Policy y
    X-Permitted-Cross-Domain-Policies. No reemplaza nada de
    SecurityMiddleware ni de XFrameOptionsMiddleware — HSTS, nosniff,
    Referrer-Policy y X-Frame-Options siguen a su cargo. Este
    middleware solo agrega lo que esos dos no resuelven.

    El CSP está armado a partir de un inventario real de todo lo que
    el proyecto carga desde fuera (auditado contra el código, no
    adivinado): Tailwind vía CDN (script) y Google Fonts (hoja de
    estilos + tipografías, que a su vez sirve los archivos de fuente
    desde fonts.gstatic.com aunque ese host no aparezca en ningún
    <link> directamente).

    script-src y style-src necesitan 'unsafe-inline' por el enfoque
    "Tailwind sin build" del proyecto: base.html, login.html y
    errors/500.html traen <script> inline con tailwind.config, y el
    propio CDN de Tailwind inyecta un <style> dinámico al compilar
    las clases utilitarias en el navegador. No hay forma de evitar
    'unsafe-inline' en ninguna de las dos directivas sin abandonar
    esa arquitectura (nonces no sirven aquí: el <style> lo inyecta un
    script de terceros que no conoce ningún nonce nuestro). Aun así
    el CSP sigue aportando valor real: bloquea que un XSS cargue
    script, estilos o imágenes desde cualquier dominio que no esté
    explícitamente permitido acá.
    """

    CSP_DIRECTIVES = (
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data:",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    )

    # Sin cámara, micrófono, geolocalización, etc. — el proyecto no usa
    # ninguna de estas APIs. interest-cohort=() además opta fuera de
    # FLoC/Topics (rastreo de Chrome), sin costo funcional alguno.
    PERMISSIONS_POLICY = (
        "camera=(), microphone=(), geolocation=(), payment=(), "
        "usb=(), interest-cohort=()"
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self._csp_value = "; ".join(self.CSP_DIRECTIVES)

    def __call__(self, request):
        response = self.get_response(request)
        # setdefault, no asignación directa: si alguna vista puntual
        # ya hubiera fijado su propia cabecera (caso hoy inexistente,
        # pero por si acaso a futuro), no se la pisa.
        response.headers.setdefault("Content-Security-Policy", self._csp_value)
        response.headers.setdefault("Permissions-Policy", self.PERMISSIONS_POLICY)
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        return response
