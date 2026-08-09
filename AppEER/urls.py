"""
URL configuration for AppEER project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from AppEER import views
from core.auth_views import AppEERLoginView, AppEERLogoutView

urlpatterns = [
    path("", views.bienvenida, name="bienvenida"),
    path("inicio/", views.inicio, name="inicio"),
    path("login/", AppEERLoginView.as_view(), name="login"),
    path("logout/", AppEERLogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("estudiantes/", include("apps.estudiantes.urls")),
    path("docencia/", include("apps.docencia.urls")),
    path("academico/", include("apps.academico.urls")),
    path("planificacion/", include("apps.planificacion.urls")),
    path("asignaciones/", include("apps.asignaciones.urls")),
]

handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"