"""
Poblado de datos de demostración para AppEER.
=============================================

Uso desde la Python Console de Django (`python manage.py shell`):

    from scripts.seed_demo import poblar
    poblar()

Para rehacer el poblado desde cero (borra SOLO los datos de negocio,
nunca los usuarios ni las sesiones):

    from scripts.seed_demo import poblar
    poblar(limpiar=True)

Para borrar sin volver a poblar:

    from scripts.seed_demo import limpiar
    limpiar()

--------------------------------------------------------------------
Decisiones de diseño de este script
--------------------------------------------------------------------
1. Escribe a través de los SERVICES de cada app, nunca con el ORM
   directo. Es más lento que un `bulk_create`, pero a cambio el
   poblado ejercita exactamente las mismas validaciones que la
   aplicación real: máximo dos integrantes por matrimonio, no doble
   inscripción en la misma edición, estudiantes distintos en una
   pareja, tema activo para poder programarse, y la coherencia entre
   pareja y programación vía Unit of Work. Si el script corre
   completo, es porque los datos son válidos según las reglas de
   negocio del proyecto — no solo según las restricciones de MySQL.

2. Es idempotente por defecto: si detecta que ya hay datos, avisa y
   no hace nada, en lugar de duplicar todo. `limpiar=True` es la
   forma explícita de rehacerlo.

3. Todo ocurre dentro de una única transacción. Si algo falla a mitad
   de camino, la base queda exactamente como estaba — nunca a medias.

4. NO toca la tabla de usuarios. El superusuario `felipe_cuevas` y
   cualquier sesión abierta sobreviven a `limpiar()`.

Los nombres, matrimonios y la conformación de las 14 parejas
reproducen la planilla real de la Turma 206 que entregó el cliente,
para que la demo se vea con datos reconocibles.
"""
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.academico import services as academico_services
from apps.academico.models import Clase, EdicionEscuela, InscripcionEstudiante
from apps.asignaciones import services as asignaciones_services
from apps.asignaciones.models import Pareja
from apps.docencia import services as docencia_services
from apps.docencia.models import Instructor, Tema
from apps.estudiantes import services as estudiantes_services
from apps.estudiantes.models import Estudiante, Matrimonio
from apps.planificacion import services as planificacion_services
from apps.planificacion.models import ProgramacionClase

MASC = Estudiante.Genero.MASCULINO
FEM = Estudiante.Genero.FEMENINO

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]


# ─── Datos de origen ────────────────────────────────────────────────

# Los 7 matrimonios de la Turma 206. Cada tupla es
# (fecha de matrimonio, cónyuge 1, cónyuge 2), y cada cónyuge es
# (nombre, apellido, género).
MATRIMONIOS = [
    (date(2015, 3, 14), ("Jefferson", "Mercês", MASC), ("Joice", "Mercês", FEM)),
    (date(2017, 11, 4), ("Mateus", "Cunha", MASC), ("Jaqueline", "Cunha", FEM)),
    (date(2012, 6, 23), ("Oldeni", "Sodré", MASC), ("Karine", "Sodré", FEM)),
    (date(2019, 1, 26), ("Samuel", "Neri", MASC), ("Jocilene", "Neri", FEM)),
    (date(2014, 9, 6), ("Wanderson", "Monteiro", MASC), ("Marina", "Monteiro", FEM)),
    (date(2018, 4, 21), ("Igor", "Souza", MASC), ("Caroline", "Souza", FEM)),
    (date(2016, 12, 10), ("Gerlan", "Santos", MASC), ("Adelaide", "Santos", FEM)),
]

# Los 14 solteros de la Turma 206: (nombre, apellido, género).
SOLTEROS = [
    ("Bruno", "Santos", MASC),
    ("Ana", "Cristina", FEM),
    ("Jefferson", "Pires", MASC),
    ("Eliza", "Oliveira", FEM),
    ("Jeorge", "Silva", MASC),
    ("Jaquelinne", "Santos", FEM),
    ("João Paulo", "Lima", MASC),
    ("Stefany", "Almeida", FEM),
    ("Ronaldo", "Silva", MASC),
    ("Cinara", "Ferreira", FEM),
    ("Alex", "Silva", MASC),
    ("Ana", "Carolina", FEM),
    ("Álvaro", "Ramos", MASC),
    ("María", "Vitória", FEM),
]

# Turma anterior (edición 2025), para que el filtro por edición del
# horario tenga más de una opción real que mostrar.
TURMA_ANTERIOR = [
    ("Rodrigo", "Fuentes", MASC),
    ("Camila", "Navarrete", FEM),
    ("Matías", "Cárcamo", MASC),
    ("Javiera", "Sepúlveda", FEM),
    ("Sebastián", "Villagrán", MASC),
    ("Antonia", "Riquelme", FEM),
    ("Tomás", "Bustamante", MASC),
    ("Fernanda", "Cárdenas", FEM),
    ("Ignacio", "Möller", MASC),
    ("Valentina", "Paredes", FEM),
]

INSTRUCTORES = [
    ("Gabriel", "Folador", "Instructor titular"),
    ("Bruno", "Roberto", "Instructor auxiliar"),
]

# 24 temas activos (uno por cada clase programada de la edición 2026)
# más 3 desactivados, para que la pantalla de Temas muestre ambos
# estados y el filtro de temas disponibles tenga algo que filtrar.
TEMAS_ACTIVOS = [
    "Lectura pública con sentido",
    "Cómo iniciar conversaciones",
    "El uso eficaz de las preguntas",
    "Razonar a partir de las Escrituras",
    "Ilustraciones que enseñan",
    "La importancia del contacto visual",
    "Modulación y énfasis",
    "Preparación de la presentación",
    "Cómo despertar interés",
    "Volver a visitar con propósito",
    "Dirigir un curso bíblico",
    "Enseñar con tacto",
    "El aseo y la presencia personal",
    "Cómo vencer el miedo escénico",
    "Escuchar con empatía",
    "Responder objeciones con bondad",
    "El valor del testimonio informal",
    "Organizar el territorio",
    "Trabajar en equipo con la pareja",
    "La constancia en el ministerio",
    "Uso de publicaciones digitales",
    "Adaptarse al auditorio",
    "Conclusiones que motivan",
    "Repaso general del curso",
]

TEMAS_INACTIVOS = [
    "Uso del retroproyector (obsoleto)",
    "Distribución de casetes",
    "Formulario S-4 en papel",
]

# Las 14 parejas (pupitres) de la Turma 206, en el mismo orden en que
# aparecen en la planilla del cliente. Se identifican por apellido
# porque no hay dos personas con el mismo apellido y nombre distinto
# fuera de los matrimonios.
PAREJAS_TURMA_206 = [
    (("Ronaldo", "Silva"), ("Cinara", "Ferreira")),
    (("Álvaro", "Ramos"), ("Alex", "Silva")),
    (("João Paulo", "Lima"), ("Stefany", "Almeida")),
    (("Samuel", "Neri"), ("Jocilene", "Neri")),
    (("Wanderson", "Monteiro"), ("Marina", "Monteiro")),
    (("Jefferson", "Mercês"), ("Joice", "Mercês")),
    (("Mateus", "Cunha"), ("Jaqueline", "Cunha")),
    (("Oldeni", "Sodré"), ("Karine", "Sodré")),
    (("Bruno", "Santos"), ("Ana", "Cristina")),
    (("Jefferson", "Pires"), ("Eliza", "Oliveira")),
    (("Jeorge", "Silva"), ("Jaquelinne", "Santos")),
    (("Ana", "Carolina"), ("María", "Vitória")),
    (("Gerlan", "Santos"), ("Adelaide", "Santos")),
    (("Igor", "Souza"), ("Caroline", "Souza")),
]


# ─── Utilidades internas ────────────────────────────────────────────

def _titulo(texto):
    print(f"\n{texto}")
    print("─" * len(texto))


def _ok(texto):
    print(f"  ✓ {texto}")


def _hay_datos():
    return any(
        modelo.objects.exists()
        for modelo in (
            Estudiante, Matrimonio, Instructor, Tema,
            EdicionEscuela, Clase, InscripcionEstudiante,
            ProgramacionClase, Pareja,
        )
    )


# ─── Limpieza ───────────────────────────────────────────────────────

def limpiar(confirmar=True):
    """
    Borra todos los datos de negocio, en orden seguro respecto de las
    claves foráneas (de la hoja del grafo hacia la raíz), para no
    chocar con los PROTECT/RESTRICT definidos en los modelos.

    NO toca usuarios, sesiones ni el log del admin.
    """
    if confirmar:
        print("Esto borrará TODOS los datos de negocio (no los usuarios).")
        respuesta = input("Escribe 'SI' para continuar: ").strip()
        if respuesta != "SI":
            print("Cancelado. No se borró nada.")
            return False

    with transaction.atomic():
        _titulo("Limpiando datos existentes")
        # Orden: primero lo que referencia a otros, al final lo
        # referenciado. Pareja es la hoja del grafo (Nivel 3).
        for etiqueta, modelo in (
            ("Parejas", Pareja),
            ("Programaciones de clase", ProgramacionClase),
            ("Inscripciones", InscripcionEstudiante),
            ("Estudiantes", Estudiante),
            ("Matrimonios", Matrimonio),
            ("Clases", Clase),
            ("Ediciones", EdicionEscuela),
            ("Temas", Tema),
            ("Instructores", Instructor),
        ):
            borrados, _ = modelo.objects.all().delete()
            _ok(f"{etiqueta}: {borrados} registro(s) eliminado(s)")
    return True


# ─── Poblado ────────────────────────────────────────────────────────

@transaction.atomic
def poblar(limpiar_antes=False, limpiar=False):
    """
    Puebla la base con un conjunto completo y coherente de datos de
    demostración. `limpiar=True` borra lo existente antes de poblar
    (ambos nombres de parámetro funcionan, por comodidad).

    Todo ocurre en una sola transacción: si algo falla, la base queda
    intacta.
    """
    debe_limpiar = limpiar_antes or limpiar

    if debe_limpiar:
        globals()["limpiar"](confirmar=False)
    elif _hay_datos():
        print(
            "La base ya tiene datos de negocio. No se hizo nada.\n"
            "Si quieres rehacer el poblado desde cero, ejecuta:\n"
            "    poblar(limpiar=True)"
        )
        return

    # ── Docencia: instructores y temas ──────────────────────────────
    _titulo("1/6 · Docencia")

    instructores = [
        docencia_services.crear_instructor(nombre=n, apellido=a, cargo=c)
        for n, a, c in INSTRUCTORES
    ]
    _ok(f"{len(instructores)} instructores")

    temas = [
        docencia_services.crear_tema(titulo_tema=titulo, activo=True)
        for titulo in TEMAS_ACTIVOS
    ]
    for titulo in TEMAS_INACTIVOS:
        docencia_services.crear_tema(titulo_tema=titulo, activo=False)
    _ok(f"{len(TEMAS_ACTIVOS)} temas activos + {len(TEMAS_INACTIVOS)} desactivados")

    # ── Académico: ediciones y clases ───────────────────────────────
    _titulo("2/6 · Académico")

    edicion_2026 = academico_services.crear_edicion(
        nombre_edicion="Escuela para Evangelizadores del Reino 2026",
        fecha_inicio=date(2026, 3, 2),
        fecha_fin=date(2026, 6, 27),
    )
    edicion_2025 = academico_services.crear_edicion(
        nombre_edicion="Escuela para Evangelizadores del Reino 2025",
        fecha_inicio=date(2025, 3, 3),
        fecha_fin=date(2025, 6, 28),
    )
    _ok("2 ediciones")

    clase_206 = academico_services.crear_clase(anio=2026, nombre="Turma 206")
    clase_205 = academico_services.crear_clase(anio=2025, nombre="Turma 205")
    _ok("2 clases")

    # ── Estudiantes: matrimonios primero, luego solteros ────────────
    _titulo("3/6 · Estudiantes")

    # Índice nombre+apellido -> Estudiante, para armar las parejas
    # después sin volver a consultar la base.
    indice = {}

    for fecha_matrimonio, conyuge_1, conyuge_2 in MATRIMONIOS:
        # El matrimonio se crea primero y se pasa a AMBOS cónyuges:
        # el Service valida que no se supere el máximo de dos
        # integrantes, así que este es el camino correcto.
        matrimonio = estudiantes_services.crear_matrimonio(
            fecha_matrimonio=fecha_matrimonio
        )
        for nombre, apellido, genero in (conyuge_1, conyuge_2):
            estudiante = estudiantes_services.crear_estudiante(
                nombre=nombre,
                apellido=apellido,
                genero=genero,
                fecha_nacimiento=date(1988, 5, 12),
                fecha_bautismo=date(2006, 7, 15),
                matrimonio=matrimonio,
            )
            indice[(nombre, apellido)] = estudiante
    _ok(f"{len(MATRIMONIOS)} matrimonios ({len(MATRIMONIOS) * 2} estudiantes casados)")

    for nombre, apellido, genero in SOLTEROS:
        indice[(nombre, apellido)] = estudiantes_services.crear_estudiante(
            nombre=nombre,
            apellido=apellido,
            genero=genero,
            fecha_nacimiento=date(1996, 2, 9),
            fecha_bautismo=date(2013, 4, 20),
        )
    _ok(f"{len(SOLTEROS)} estudiantes solteros")

    estudiantes_2025 = [
        estudiantes_services.crear_estudiante(
            nombre=nombre,
            apellido=apellido,
            genero=genero,
            fecha_nacimiento=date(1994, 8, 3),
            fecha_bautismo=date(2011, 10, 8),
        )
        for nombre, apellido, genero in TURMA_ANTERIOR
    ]
    _ok(f"{len(TURMA_ANTERIOR)} estudiantes de la turma anterior")

    # ── Inscripciones ───────────────────────────────────────────────
    _titulo("4/6 · Inscripciones")

    estudiantes_206 = list(indice.values())
    for estudiante in estudiantes_206:
        academico_services.crear_inscripcion(
            estudiante=estudiante, edicion=edicion_2026, clase=clase_206
        )
    _ok(f"{len(estudiantes_206)} inscritos en {clase_206.nombre} (edición 2026)")

    for estudiante in estudiantes_2025:
        academico_services.crear_inscripcion(
            estudiante=estudiante, edicion=edicion_2025, clase=clase_205
        )
    _ok(f"{len(estudiantes_2025)} inscritos en {clase_205.nombre} (edición 2025)")

    # ── Planificación: horario de clases ────────────────────────────
    _titulo("5/6 · Planificación")

    programaciones_2026 = []
    contador = 0
    for semana in range(1, 5):            # 4 semanas
        for indice_dia, dia in enumerate(DIAS):   # 6 días por semana
            tema = temas[contador]        # un tema distinto por clase
            programacion = planificacion_services.crear_programacion(
                edicion=edicion_2026,
                codigo_clase=f"C-{contador + 1:02d}",
                numero_semana=semana,
                dia_semana=dia,
                numero_aula=1 + (indice_dia % 2),
                # Alterna instructor A / B, como en la planilla real.
                instructor=instructores[contador % len(instructores)],
                tema=tema,
            )
            programaciones_2026.append(programacion)
            contador += 1
    _ok(f"{len(programaciones_2026)} clases programadas (edición 2026)")

    for semana in range(1, 2):            # una semana de muestra
        for indice_dia, dia in enumerate(DIAS):
            planificacion_services.crear_programacion(
                edicion=edicion_2025,
                codigo_clase=f"A-{indice_dia + 1:02d}",
                numero_semana=semana,
                dia_semana=dia,
                numero_aula=1,
                instructor=instructores[indice_dia % len(instructores)],
                tema=temas[indice_dia],
            )
    _ok(f"{len(DIAS)} clases programadas (edición 2025)")

    # ── Asignaciones: las 14 parejas de la Turma 206 ────────────────
    _titulo("6/6 · Asignaciones")

    for numero, (clave_1, clave_2) in enumerate(PAREJAS_TURMA_206):
        asignaciones_services.crear_pareja(
            clase=clase_206,
            estudiante_1=indice[clave_1],
            estudiante_2=indice[clave_2],
            # Se asigna una programación distinta a cada pareja. El
            # Service valida, dentro del Unit of Work, que ambos
            # estudiantes estén inscritos en esa clase y edición.
            programacion=programaciones_2026[numero],
        )
    _ok(f"{len(PAREJAS_TURMA_206)} parejas formadas ({len(MATRIMONIOS)} son matrimonios)")

    # Parejas de la turma anterior, sin programación asociada, para
    # mostrar también ese caso (el campo es opcional).
    for i in range(0, len(estudiantes_2025), 2):
        asignaciones_services.crear_pareja(
            clase=clase_205,
            estudiante_1=estudiantes_2025[i],
            estudiante_2=estudiantes_2025[i + 1],
        )
    _ok(f"{len(estudiantes_2025) // 2} parejas de la turma anterior (sin programación)")

    _resumen()


def _resumen():
    _titulo("Resumen final")
    filas = [
        ("Matrimonios", Matrimonio.objects.count()),
        ("Estudiantes", Estudiante.objects.count()),
        ("Instructores", Instructor.objects.count()),
        ("Temas", Tema.objects.count()),
        ("  · activos", Tema.objects.filter(activo=True).count()),
        ("Ediciones", EdicionEscuela.objects.count()),
        ("Clases", Clase.objects.count()),
        ("Inscripciones", InscripcionEstudiante.objects.count()),
        ("Programaciones", ProgramacionClase.objects.count()),
        ("Parejas", Pareja.objects.count()),
    ]
    for etiqueta, total in filas:
        print(f"  {etiqueta:.<28} {total:>4}")

    print(
        "\n¡Listo! Abre la aplicación e inicia sesión para ver los datos.\n"
        "Sugerencia de recorrido para la demo:\n"
        "  1. Inicio — las tarjetas de resumen ya muestran los totales\n"
        "  2. Estudiantes — prueba el buscador en vivo (escribe 'San')\n"
        "  3. Planificación — filtra el horario por edición\n"
        "  4. Asignaciones — entra a la Turma 206 y revisa las parejas\n"
    )