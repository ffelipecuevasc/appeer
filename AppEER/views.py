"""
Vista del proyecto (no de una app de negocio, no transversal de core/):
compone datos de resumen de las cinco apps para la página de inicio.

Deliberadamente NO vive en core/: core/ es agnóstico de apps de negocio
(principio establecido desde la Fase 0 — ningún módulo de core/
importa de apps/) y esta vista sí necesita conocerlas
todas. Vive junto a AppEER/urls.py porque es, literalmente, la vista
raíz del proyecto.

Solo usa selectors ya existentes desde las Fases 1-4, en modo lectura.
No se creó ni se modificó ningún selector para esto.

Adenda 8: se suma `bienvenida`, la página pública de aterrizaje. Vive
acá por decisión explícita (podría haber ido en core/, ya que no
importa nada de apps/, pero se prefirió mantener juntas las dos vistas
"del proyecto" en un solo archivo).
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.academico import selectors as academico_selectors
from apps.asignaciones import selectors as asignaciones_selectors
from apps.docencia import selectors as docencia_selectors
from apps.estudiantes import selectors as estudiantes_selectors
from apps.planificacion import selectors as planificacion_selectors
from apps.planificacion.serializers import ProgramacionClaseDTO

# Marca de "esta pestaña ya vio la bienvenida" (Adenda 8, decisión 2:
# mostrarla una vez por sesión de navegador, no en cada visita).
COOKIE_BIENVENIDA = "appeer_bienvenida"


def bienvenida(request):
    """
    Página pública de aterrizaje (Adenda 8). Es la ÚNICA vista del
    proyecto sin control de acceso, y puede serlo porque no expone
    ningún dato de negocio: solo una imagen, el logotipo y un botón.
    Si alguna vez se le agrega un conteo, un nombre o cualquier dato
    del dominio, pasa a ser vista de negocio y debe protegerse como
    las demás — ese es el límite que la deja fuera del criterio de
    aceptación de la Fase 8, no una excepción concedida.

    El destino se decide ACÁ, en el servidor, nunca en JavaScript: la
    plantilla recibe una URL ya resuelta y no sabe nada sobre sesiones.
    "Recordar el inicio de sesión" no requirió lógica nueva — es
    request.user.is_authenticated leyendo la sesión que la Subfase 8.1
    ya sabe hacer durar 14 días con "Recordarme", o hasta cerrar el
    navegador sin él.

    Por qué una cookie propia y no una marca en request.session:
    escribir en la sesión de un usuario autenticado solo para anotar
    que vio esta página implicaría tocar el mismo objeto cuya
    expiración administra "Recordarme" (Subfase 8.1) — un riesgo
    innecesario sobre algo que recién quedó funcionando. Además,
    forzaría a crear una sesión completa en base de datos para cada
    visitante anónimo. Esta cookie se emite SIN max_age, que es
    exactamente la definición de "cookie de sesión de navegador":
    muere al cerrar el navegador, que es el comportamiento pedido, y
    lo hace con independencia de cuánto dure la sesión de login.
    """
    destino = reverse("inicio") if request.user.is_authenticated else reverse("login")
    etiqueta = "Ir al inicio" if request.user.is_authenticated else "Iniciar sesión"

    # Segunda visita o posterior dentro de la misma sesión de
    # navegador: no se vuelve a mostrar, se deriva directo.
    if request.COOKIES.get(COOKIE_BIENVENIDA):
        return redirect(destino)

    response = render(
        request,
        "appeer.html",
        {"destino": destino, "etiqueta_destino": etiqueta},
    )
    response.set_cookie(
        COOKIE_BIENVENIDA,
        "1",
        max_age=None,  # sin max_age = cookie de sesión de navegador
        httponly=True,  # nada de JS necesita leerla; la decide el servidor
        samesite="Lax",
        # Sigue automáticamente el entorno: False en desarrollo, True en
        # producción, donde settings/production.py ya lo activa.
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response


@login_required
def inicio(request):
    """
    Página de inicio (Adenda 7): tarjetas de resumen por app + las
    próximas programaciones. Mismo patrón que cualquier ListView del
    proyecto — Selector para leer, DTO para exponer al template —
    solo que compone varias apps en vez de una sola.

    Subfase 8.2: agrega datos agregados de las cinco apps de negocio
    (conteos de estudiantes, instructores, ediciones, parejas), así
    que es tan "vista de negocio" como cualquier ListView — se
    protege igual. No usa AccessControlMixin (es una función, no una
    clase) ni tiene variante AJAX: @login_required de Django nativo
    alcanza, y redirige a LOGIN_URL con ?next= como cualquier vista
    de página completa.
    """
    proximas_programaciones = [
        ProgramacionClaseDTO.from_model(p)
        for p in planificacion_selectors.listar_programaciones()[:5]
    ]

    context = {
        "total_estudiantes": estudiantes_selectors.listar_estudiantes().count(),
        "total_instructores": docencia_selectors.listar_instructores().count(),
        # Fase 11 (Adenda 9): total_ediciones -> total_clases. EdicionEscuela
        # desapareció; Clase es ahora la única entidad que cuenta acá.
        "total_clases": academico_selectors.listar_clases().count(),
        "total_parejas": asignaciones_selectors.listar_parejas().count(),
        "proximas_programaciones": proximas_programaciones,
    }
    return render(request, "index.html", context)