from .base import *  # noqa

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS (Subfase 7.5): le dice al navegador "usa siempre HTTPS con este
# host, ni intentes HTTP", cerrando la ventana que SECURE_SSL_REDIRECT
# solo no cubre — el redirect protege desde la SEGUNDA visita en
# adelante, pero la primera petición (o una interceptada activamente)
# igual podría viajar en HTTP antes de que el redirect actúe. HSTS
# hace que, después de la primera respuesta, el navegador ya ni
# intente HTTP en las siguientes.
#
# Arranca en 1 hora a propósito, no en el año que suelen recomendar
# las checklists: si algo del certificado/HTTPS estuviera mal
# configurado, un valor alto deja a cualquiera que ya haya visitado
# el sitio sin poder entrar por HTTP durante ese tiempo, sin forma de
# revertirlo del lado del servidor. Subir el valor gradualmente
# (1 hora -> 1 día -> 1 semana -> el año estándar) después de
# confirmar que HTTPS funciona sólido en producción es el camino
# responsable, no un atajo.
SECURE_HSTS_SECONDS = 3600
# Deliberadamente NO se activan todavía (requieren HSTS ya probado y
# estable en producción; includeSubDomains puede tumbar subdominios
# que hoy no sirven HTTPS, y preload es prácticamente irreversible):
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# CSRF_COOKIE_HTTPONLY: se deja en su default de Django (False) A
# PROPÓSITO — no es un descuido. static/js/core/http.js necesita leer
# la cookie csrftoken desde document.cookie para mandar el header
# X-CSRFToken en cada escritura por fetch (Subfase 6.1). Si esto se
# pusiera en True acá, cada escritura de la Fase 6 (crear pareja,
# etc.) empezaría a fallar con 403 en producción — y solo en
# producción, porque development.py nunca setea esto. Queda este
# comentario para que nadie lo "endurezca" sin saber por qué está así.

# PENDIENTE (Subfase 7.5, decisión abierta al 2026-08-08 — resolver
# antes de la Fase 10, Preparación para Despliegue): falta
# SECURE_PROXY_SSL_HEADER. Si el despliegue final queda detrás de un
# proxy reverso que termina HTTPS (Nginx, load balancer, Railway/
# Render/Heroku, etc.), SECURE_SSL_REDIRECT sin este setting entra en
# loop infinito de redirects — Django ve la conexión interna como
# HTTP y redirige, el proxy la reenvía como HTTP de nuevo, sin fin.
# Pero configurarlo SIN un proxy de confianza delante es un agujero
# real: cualquiera podría falsificar X-Forwarded-Proto y saltarse la
# detección de HTTPS. Por eso queda sin definir hasta saber el
# destino real del despliegue — no es un olvido.
#
# Cuando se decida, agregar UNA de estas dos líneas (nunca ambas, y
# nunca la primera sin confirmar que el proxy es realmente el único
# camino de entrada — si el proxy no filtra X-Forwarded-Proto que
# venga del cliente, esta línea abre la puerta que se quería cerrar):
#
#   SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # con proxy reverso
#   # (sin proxy reverso: no agregar nada, Django ya confía en la conexión directa)
