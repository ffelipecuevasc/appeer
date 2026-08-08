"""
Vistas de error globales del proyecto (Subfase 5.3). No pertenecen a
ninguna app de negocio — se registran como handler403/handler404/
handler500 en AppEER/urls.py, y Django los usa automáticamente
cuando DEBUG = False.

Nota de diseño importante: error_500() NO usa render() ni pasa
`request` al renderizar. Es intencional: ante un error 500 real, no
sabemos qué fue lo que falló — podría ser la propia base de datos, y
los context processors de auth/messages hacen consultas a la BD. Si
uno de ellos fallara al intentar renderizar la página de error,
perderíamos incluso la página de error. Es el mismo criterio que usa
internamente django.views.defaults.server_error, y es la razón por
la que errors/500.html es una página autocontenida que no extiende
base.html ni depende de partials/header.html o alerts.html.

error_403() y error_404() sí pueden usar render() con normalidad:
ocurren durante una petición que sí completó (o casi completó) su
ciclo normal, así que el contexto está disponible sin este riesgo.
"""
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template import loader


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    template = loader.get_template("errors/500.html")
    return HttpResponseServerError(template.render())