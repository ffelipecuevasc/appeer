"""
Consultas de lectura reutilizables para apps.estudiantes.
Ninguna función de este módulo escribe en la base de datos.
"""
from django.db.models import Count, Q

from apps.estudiantes.models import Estudiante, Matrimonio, Responsabilidad

# Duplica intencionalmente el "2" de MAX_INTEGRANTES_POR_MATRIMONIO
# (services.py): el Selector no debe importar del Service (la capa
# de lectura es más básica que la de escritura, nunca al revés). La
# regla de negocio real se sigue validando únicamente en el Service;
# esto es solo para no ofrecer, en la UI, una opción inválida.
_MAX_INTEGRANTES_POR_MATRIMONIO_UI = 2


def listar_estudiantes(*, query=None):
    """
    Queryset base de estudiantes, con el matrimonio precargado.
    Si `query` viene informado (Subfase 6.2, buscador en vivo),
    filtra por coincidencia parcial case-insensitive en nombre o
    apellido. Parámetro opcional: el único call-site previo a esta
    subfase sigue funcionando sin pasar nada.
    """
    qs = (
        Estudiante.objects
        .select_related("matrimonio")
        # Fase 12: prefetch_related (no select_related — es una relación
        # muchos-a-muchos) para que pintar las pastillas de
        # responsabilidades en el listado no dispare una consulta por
        # estudiante. Sin esto, un listado de 38 alumnos haría 39
        # consultas en vez de 2.
        .prefetch_related("responsabilidades")
        .order_by("apellido", "nombre")
    )
    if query:
        qs = qs.filter(Q(nombre__icontains=query) | Q(apellido__icontains=query))
    return qs


def obtener_estudiante_por_id(id_estudiante):
    """Retorna un Estudiante por su PK, o None si no existe."""
    return (
        Estudiante.objects
        .select_related("matrimonio")
        .prefetch_related("responsabilidades")
        .filter(pk=id_estudiante)
        .first()
    )


def listar_estudiantes_por_matrimonio(id_matrimonio):
    """Estudiantes asociados a un matrimonio dado (0, 1 o 2 resultados)."""
    return Estudiante.objects.filter(matrimonio_id=id_matrimonio)


def listar_matrimonios_con_cupo(*, excluir_matrimonio_id=None):
    """
    Matrimonios con menos de dos integrantes, para poblar el <select>
    del formulario público de Estudiante. Uso exclusivo de
    presentación: no reemplaza la validación de capacidad que hace
    el Service al guardar (esa sigue siendo la autoridad real, y
    cubre además cualquier condición de carrera entre que se arma el
    formulario y se envía).

    Si `excluir_matrimonio_id` se indica, ese matrimonio se incluye
    igual aunque esté "lleno" — cubre el caso de edición, donde el
    estudiante que estás editando ya cuenta como uno de sus dos
    integrantes.
    """
    matrimonios = Matrimonio.objects.annotate(num_integrantes=Count("estudiantes"))
    filtro = Q(num_integrantes__lt=_MAX_INTEGRANTES_POR_MATRIMONIO_UI)
    if excluir_matrimonio_id is not None:
        filtro |= Q(pk=excluir_matrimonio_id)
    return matrimonios.filter(filtro).order_by("-fecha_matrimonio")


# --- Responsabilidades (Fase 12, Subfase 12.3) -----------------------

def listar_responsabilidades():
    """
    Catálogo completo, activas e inactivas. Lo consume la pantalla de
    gestión (Adenda 11), que necesita ver ambas para poder reactivar.
    """
    return Responsabilidad.objects.order_by("nombre")


def listar_responsabilidades_disponibles(*, incluir_ids=None):
    """
    Solo responsabilidades activas, para el formulario de Estudiante.

    `incluir_ids` agrega las que el estudiante YA tiene asignadas
    aunque estén desactivadas: sin esto, editar a un anciano después
    de desactivar "Anciano" le quitaría la responsabilidad en
    silencio al guardar.
    """
    from django.db.models import Q

    filtro = Q(activo=True)
    if incluir_ids:
        filtro |= Q(pk__in=list(incluir_ids))
    return Responsabilidad.objects.filter(filtro).order_by("nombre")


def contar_estudiantes_por_responsabilidad(id_responsabilidad):
    """Para que nadie desactive una responsabilidad a ciegas."""
    return Estudiante.objects.filter(responsabilidades__pk=id_responsabilidad).count()


def obtener_responsabilidad_por_id(id_responsabilidad):
    return Responsabilidad.objects.filter(pk=id_responsabilidad).first()


def listar_estudiantes_por_responsabilidad(id_responsabilidad):
    """
    Estudiantes que tienen una responsabilidad puntual.

    No lo consume ninguna pantalla todavía: se construye acá porque
    los módulos ya declarados en el Plan de Trabajo Maestro 2.0 lo
    van a necesitar — las oraciones de inicio y fin (Fase 18) suelen
    asignarse a ancianos, y las asignaciones de sala (Fase 19)
    distinguen por responsabilidad. Es el mismo criterio con el que
    la Fase 1 dejó selectors listos antes de tener vistas que los
    usaran.
    """
    return (
        Estudiante.objects
        .filter(responsabilidades__pk=id_responsabilidad)
        .select_related("matrimonio")
        .prefetch_related("responsabilidades")
        .order_by("apellido", "nombre")
    )


# --- Agrupación para el listado por clase (Fase 13, Subfase 13.1) ----

def listar_estudiantes_de_clase(id_clase, *, query=None):
    """
    Estudiantes inscritos en UNA clase. Base del listado de la Fase 13,
    que exige elegir clase antes de mostrar nada.

    Vive acá y no en apps.academico porque devuelve Estudiantes: el
    criterio del proyecto es que el Selector pertenece a la app del
    modelo que retorna, no a la del filtro que aplica.
    """
    qs = (
        Estudiante.objects
        .filter(inscripciones__clase_id=id_clase)
        .select_related("matrimonio")
        .prefetch_related("responsabilidades")
        .order_by("apellido", "nombre")
    )
    if query:
        qs = qs.filter(Q(nombre__icontains=query) | Q(apellido__icontains=query))
    return qs


def agrupar_estudiantes(estudiantes):
    """
    Reparte una colección de Estudiante en los tres grupos que pide la
    Fase 13: matrimonios, hombres solteros y mujeres solteras.

    La agrupación es responsabilidad del Selector, NUNCA de la
    plantilla: el patrón del proyecto es que la vista recibe datos ya
    listos para pintar (Plan Maestro, sección 9).

    Devuelve un dict con:
      - "matrimonios": lista de listas de Estudiante (los cónyuges
        juntos, ordenados con el varón primero para que la tarjeta de
        matrimonio se lea siempre igual).
      - "hombres_solteros" / "mujeres_solteras": listas de Estudiante.

    Sobre matrimonios incompletos: la Adenda 10 garantiza que un casado
    no puede estar inscrito sin su cónyuge, así que dentro de una clase
    todo matrimonio llega completo. Aun así, esta función NO asume dos
    integrantes — agrupa por matrimonio_id y devuelve lo que haya. Dos
    razones: se la puede llamar sobre una colección ya filtrada por
    búsqueda (donde el cónyuge puede no coincidir con el término
    buscado), y un invariante que se cumple hoy no debería producir un
    IndexError el día que alguien cargue datos por otra vía.
    """
    matrimonios = {}
    hombres_solteros = []
    mujeres_solteras = []

    for estudiante in estudiantes:
        if estudiante.matrimonio_id is not None:
            matrimonios.setdefault(estudiante.matrimonio_id, []).append(estudiante)
        elif estudiante.genero == Estudiante.Genero.MASCULINO:
            hombres_solteros.append(estudiante)
        else:
            mujeres_solteras.append(estudiante)

    def _ordenar_conyuges(conyuges):
        # Varón primero: la tarjeta de matrimonio se lee siempre en el
        # mismo orden, en vez de depender del orden alfabético del
        # queryset (que pondría a la esposa primera unas veces sí y
        # otras no).
        return sorted(
            conyuges, key=lambda e: e.genero != Estudiante.Genero.MASCULINO
        )

    return {
        "matrimonios": [
            _ordenar_conyuges(conyuges)
            for _, conyuges in sorted(
                matrimonios.items(),
                key=lambda par: (par[1][0].apellido, par[1][0].nombre),
            )
        ],
        "hombres_solteros": hombres_solteros,
        "mujeres_solteras": mujeres_solteras,
    }
