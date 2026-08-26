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
Fase 11 (Adenda 9): reescrito sobre la estructura nueva
--------------------------------------------------------------------
EdicionEscuela desapareció; Clase absorbió sus fechas (ahora
obligatorias). Este script ya no crea ediciones — crea clases
directamente, con fecha_inicio/fecha_fin cargadas desde el principio,
tal como exige el modelo nuevo.

--------------------------------------------------------------------
Decisiones de diseño de este script (sin cambios respecto a la
versión anterior)
--------------------------------------------------------------------
1. Escribe a través de los SERVICES de cada app, nunca con el ORM
   directo. Es más lento que un `bulk_create`, pero a cambio el
   poblado ejercita exactamente las mismas validaciones que la
   aplicación real: máximo dos integrantes por matrimonio, no doble
   inscripción en la misma clase, estudiantes distintos en una
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

from django.db import transaction

from apps.academico import selectors as academico_selectors
from apps.academico import services as academico_services
from apps.academico.models import Clase, InscripcionEstudiante
from apps.asignaciones import services as asignaciones_services
from apps.asignaciones.models import Pareja
from apps.docencia import services as docencia_services
from apps.docencia.models import Instructor, Tema
from apps.estudiantes import services as estudiantes_services
from apps.estudiantes.models import Estudiante, Matrimonio, Responsabilidad
from apps.planificacion import services as planificacion_services
from apps.planificacion.models import ProgramacionClase

MASC = Estudiante.Genero.MASCULINO
FEM = Estudiante.Genero.FEMENINO

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]


# ─── Datos de origen ────────────────────────────────────────────────

MATRIMONIOS = [
    (date(2015, 3, 14), ("Jefferson", "Mercês", MASC), ("Joice", "Mercês", FEM)),
    (date(2017, 11, 4), ("Mateus", "Cunha", MASC), ("Jaqueline", "Cunha", FEM)),
    (date(2012, 6, 23), ("Oldeni", "Sodré", MASC), ("Karine", "Sodré", FEM)),
    (date(2019, 1, 26), ("Samuel", "Neri", MASC), ("Jocilene", "Neri", FEM)),
    (date(2014, 9, 6), ("Wanderson", "Monteiro", MASC), ("Marina", "Monteiro", FEM)),
    (date(2018, 4, 21), ("Igor", "Souza", MASC), ("Caroline", "Souza", FEM)),
    (date(2016, 12, 10), ("Gerlan", "Santos", MASC), ("Adelaide", "Santos", FEM)),
]

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
            Clase, InscripcionEstudiante,
            ProgramacionClase, Pareja,
        )
    )


# ─── Limpieza ───────────────────────────────────────────────────────

def limpiar(confirmar=True):
    """
    Borra todos los datos de negocio, en orden seguro respecto de las
    claves foráneas (de la hoja del grafo hacia la raíz).

    NO toca usuarios, sesiones ni el log del admin.

    Nota Fase 11: `Clase.delete()` se usa directamente acá, no
    `academico.services` (que ya no ofrece `eliminar_clase` — las
    clases nunca se eliminan desde la aplicación, Adenda 9, Decisión
    2). Este script de poblado NO es la aplicación: es una herramienta
    de desarrollo que opera fuera de esa regla de negocio, a
    propósito, para poder rehacer la demo de un día para otro.
    """
    if confirmar:
        print("Esto borrará TODOS los datos de negocio (no los usuarios).")
        respuesta = input("Escribe 'SI' para continuar: ").strip()
        if respuesta != "SI":
            print("Cancelado. No se borró nada.")
            return False

    with transaction.atomic():
        _titulo("Limpiando datos existentes")
        for etiqueta, modelo in (
            ("Parejas", Pareja),
            ("Programaciones de clase", ProgramacionClase),
            ("Inscripciones", InscripcionEstudiante),
            ("Estudiantes", Estudiante),
            ("Matrimonios", Matrimonio),
            ("Clases", Clase),
            ("Temas", Tema),
            ("Instructores", Instructor),
            # Responsabilidad NO se borra a propósito (Fase 12): la puebla
            # la migración de datos 0003, no este script. Borrarla dejaría
            # el catálogo vacío hasta volver a migrar desde cero, y además
            # se llevaría puestas las responsabilidades que el cliente
            # haya agregado a mano desde el panel de administración.
        ):
            borrados, _ = modelo.objects.all().delete()
            _ok(f"{etiqueta}: {borrados} registro(s) eliminado(s)")
    return True


# ─── Poblado ────────────────────────────────────────────────────────

@transaction.atomic
def poblar(limpiar_antes=False, limpiar=False):
    """
    Puebla la base con un conjunto completo y coherente de datos de
    demostración. `limpiar=True` borra lo existente antes de poblar.
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

    # ── Académico: clases (Fase 11: ya no hay ediciones separadas) ──
    _titulo("2/6 · Escuela")

    clase_206 = academico_services.crear_clase(
        nombre="Turma 206",
        fecha_inicio=date(2026, 3, 2),
        fecha_fin=date(2026, 6, 27),
    )
    clase_205 = academico_services.crear_clase(
        nombre="Turma 205",
        fecha_inicio=date(2025, 3, 3),
        fecha_fin=date(2025, 6, 28),
    )
    _ok("2 clases (con fechas obligatorias, Adenda 9)")

    # ── Estudiantes: matrimonios primero, luego solteros ────────────
    _titulo("3/6 · Estudiantes")

    indice = {}

    for fecha_matrimonio, conyuge_1, conyuge_2 in MATRIMONIOS:
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

    # Fase 12: responsabilidades sobre algunos varones, para que las
    # pastillas del detalle/listado se vean con datos reales en la demo.
    # Se leen del catálogo (cargado por la migración 0003), no se crean
    # acá: el script no debe inventar valores que la migración ya define.
    catalogo = {r.nombre: r for r in Responsabilidad.objects.all()}
    asignaciones_responsabilidad = {
        ("Jefferson", "Mercês"): ["Anciano"],
        ("Samuel", "Neri"): ["Anciano", "Precursor Regular"],
        ("Wanderson", "Monteiro"): ["Siervo Ministerial"],
        ("Bruno", "Santos"): ["Siervo Ministerial", "Precursor Regular"],
        ("Igor", "Souza"): ["Precursor Regular"],
        ("Oldeni", "Sodré"): ["Anciano"],
    }
    total_asignadas = 0
    for clave, nombres in asignaciones_responsabilidad.items():
        estudiante = indice.get(clave)
        if estudiante is None:
            continue
        for nombre_responsabilidad in nombres:
            responsabilidad = catalogo.get(nombre_responsabilidad)
            if responsabilidad is not None:
                estudiantes_services.asignar_responsabilidad(
                    estudiante=estudiante, responsabilidad=responsabilidad
                )
                total_asignadas += 1
    _ok(f"{total_asignadas} responsabilidades asignadas a {len(asignaciones_responsabilidad)} estudiantes")

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

    # ── Inscripciones (Fase 11: solo clase, sin edición) ─────────────
    _titulo("4/6 · Inscripciones")

    estudiantes_206 = list(indice.values())
    # Adenda 10: crear_inscripcion inscribe automáticamente al cónyuge.
    # Por eso se salta a quien ya quedó inscrito en la iteración de su
    # pareja — llamarlo igual no rompería nada (la operación es
    # idempotente), pero el conteo del log quedaría engañoso.
    for estudiante in estudiantes_206:
        if InscripcionEstudiante.objects.filter(
            estudiante=estudiante, clase=clase_206
        ).exists():
            continue
        academico_services.crear_inscripcion(estudiante=estudiante, clase=clase_206)
    _ok(
        f"{academico_selectors.contar_inscritos(clase_206.pk)} inscritos en "
        f"{clase_206.nombre} (los casados se inscribieron de a dos)"
    )

    for estudiante in estudiantes_2025:
        academico_services.crear_inscripcion(estudiante=estudiante, clase=clase_205)
    _ok(f"{len(estudiantes_2025)} inscritos en {clase_205.nombre}")

    # ── Planificación: horario de clases (Fase 11: cuelga de Clase) ─
    _titulo("5/6 · Planificación")

    programaciones_2026 = []
    contador = 0
    for semana in range(1, 5):
        for indice_dia, dia in enumerate(DIAS):
            tema = temas[contador]
            programacion = planificacion_services.crear_programacion(
                clase=clase_206,
                codigo_clase=f"C-{contador + 1:02d}",
                numero_semana=semana,
                dia_semana=dia,
                numero_aula=1 + (indice_dia % 2),
                instructor=instructores[contador % len(instructores)],
                tema=tema,
            )
            programaciones_2026.append(programacion)
            contador += 1
    _ok(f"{len(programaciones_2026)} clases programadas ({clase_206.nombre})")

    for indice_dia, dia in enumerate(DIAS):
        planificacion_services.crear_programacion(
            clase=clase_205,
            codigo_clase=f"A-{indice_dia + 1:02d}",
            numero_semana=1,
            dia_semana=dia,
            numero_aula=1,
            instructor=instructores[indice_dia % len(instructores)],
            tema=temas[indice_dia],
        )
    _ok(f"{len(DIAS)} clases programadas ({clase_205.nombre})")

    # ── Asignaciones: las 14 parejas de la Turma 206 ────────────────
    _titulo("6/6 · Asignaciones")

    for numero, (clave_1, clave_2) in enumerate(PAREJAS_TURMA_206):
        asignaciones_services.crear_pareja(
            clase=clase_206,
            estudiante_1=indice[clave_1],
            estudiante_2=indice[clave_2],
            programacion=programaciones_2026[numero],
        )
    _ok(f"{len(PAREJAS_TURMA_206)} parejas formadas ({len(MATRIMONIOS)} son matrimonios)")

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
        ("Responsabilidades", Responsabilidad.objects.count()),
        ("Instructores", Instructor.objects.count()),
        ("Temas", Tema.objects.count()),
        ("  · activos", Tema.objects.filter(activo=True).count()),
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
        "  3. Escuela — abre la Turma 206 y revisa sus estudiantes inscritos\n"
        "  4. Planificación — filtra el horario por clase\n"
        "  5. Asignaciones — entra a la Turma 206 y revisa las parejas\n"
    )
