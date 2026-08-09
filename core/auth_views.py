"""
Vistas de autenticación por sesión del proyecto (Subfase 8.1).

Por qué un archivo propio y no core/views.py: ese archivo tiene una
responsabilidad única y bien delimitada (los handlers de error
globales 403/404/500 + CSRF_FAILURE_VIEW). Mezclar el flujo de
sesión ahí lo convertiría en un cajón de "vistas sueltas". Se sigue
el mismo criterio de un-archivo-una-responsabilidad que ya rige en
core/middleware/ (Plan Maestro, sección 14).

Por qué en core/ y no en AppEER/: core/ es agnóstico de apps de
negocio, y estas vistas lo respetan — no importan nada de apps/.
Usan exclusivamente django.contrib.auth, que ya está en
INSTALLED_APPS desde el esqueleto original (Plan Maestro, sección
10: "sin necesidad de una app adicional dedicada a usuarios"). La
excepción documentada sigue siendo AppEER/views.py::inicio, que sí
conoce las cinco apps.

Por qué subclases y no LoginView/LogoutView directas en urls.py: la
única razón es el checkbox "Recordarme" (duración de la sesión) y el
mensaje de confirmación al cerrar sesión. Todo lo demás —validación
de credenciales, cycling de la sesión al autenticar, protección
CSRF, manejo del parámetro `next`— lo resuelve Django nativo y no se
reimplementa, por el mismo criterio con el que UnitOfWork es un
envoltorio delgado sobre transaction.atomic() en vez de un patrón
reimplementado desde cero.
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView


class AppEERLoginView(LoginView):
    """
    Inicio de sesión sobre templates/login.html (la plantilla visual
    de la Adenda 7, que ya traía method="post", {% csrf_token %} y
    los campos username/password con los nombres que AuthenticationForm
    espera — no hubo que rehacer el HTML, solo conectarlo).

    Reemplaza al TemplateView temporal en la MISMA ruta y con el
    MISMO name="login", así que ningún enlace existente cambia.
    """

    template_name = "login.html"

    # Un usuario ya autenticado que llega a /login/ es rebotado a
    # LOGIN_REDIRECT_URL en vez de ver el formulario otra vez.
    # Django advierte del riesgo de bucle de redirección con esta
    # opción: solo ocurre si LOGIN_REDIRECT_URL apunta al propio
    # login, que no es el caso acá (apunta a `inicio`). Si alguna vez
    # se cambia ese setting, revisar esta línea.
    redirect_authenticated_user = True

    # Nombre del checkbox en templates/login.html. No es un campo de
    # AuthenticationForm (no participa de la validación de
    # credenciales): es una preferencia de duración de sesión, que es
    # responsabilidad de la vista, no del formulario.
    REMEMBER_FIELD = "remember"

    def form_valid(self, form):
        """
        Credenciales válidas. Se llama primero a super(), que es
        quien ejecuta auth_login() —y por lo tanto quien rota el
        identificador de sesión para prevenir session fixation—, y
        recién DESPUÉS se fija la expiración: hacerlo antes sería
        escribir sobre una sesión que Django está por reemplazar.
        """
        response = super().form_valid(form)

        if self.request.POST.get(self.REMEMBER_FIELD):
            # Sesión persistente: sobrevive al cierre del navegador
            # hasta agotar SESSION_COOKIE_AGE (settings/base.py).
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            # set_expiry(0) = cookie de sesión pura: el navegador la
            # descarta al cerrarse. Es el default más conservador y
            # el comportamiento que un usuario espera cuando NO marcó
            # "Recordarme" (por ejemplo, en un computador compartido
            # de la escuela).
            self.request.session.set_expiry(0)

        messages.success(
            self.request,
            f"Sesión iniciada como {form.get_user().get_username()}.",
        )
        return response


class AppEERLogoutView(LogoutView):
    """
    Cierre de sesión. Solo acepta POST — es el comportamiento nativo
    de LogoutView desde Django 5, y es lo correcto: un GET permitiría
    cerrarle la sesión a un usuario con solo hacerle abrir un enlace
    o cargar una imagen apuntando a /logout/. Por eso el header usa
    un <form method="post"> con su token CSRF y no un <a href>.
    """

    def post(self, request, *args, **kwargs):
        # El mensaje se agrega DESPUÉS de super(), no antes: super()
        # ejecuta auth_logout(), que vacía la sesión por completo. Un
        # mensaje agregado antes se perdería en ese vaciado; agregado
        # después, viaja en la sesión nueva y limpia, y lo renderiza
        # partials/alerts.html en la página de destino.
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Cerraste sesión correctamente.")
        return response
