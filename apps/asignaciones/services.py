"""
Operaciones de escritura (alta) para apps.asignaciones.
"""
from django.core.exceptions import ValidationError

from apps.academico.models import InscripcionEstudiante
from apps.asignaciones.models import Pareja
from core.unit_of_work import UnitOfWork


def _validar_estudiantes_distintos(*, estudiante_1, estudiante_2):
    """
    Refuerza en Python la misma regla que el script SQL auditado
    protege con dos triggers de MySQL (trg_parejas_bi/bu), deliberadamente
    no replicados en la migración de la Subfase 4.1 (decisión registrada
    en el Paso 0 de la Fase 4): esta validación corre siempre antes de
    cualquier escritura, cubriendo el mismo caso sin necesitar SQL crudo.
    """
    if estudiante_1.pk == estudiante_2.pk:
        raise ValidationError("Una pareja debe estar formada por dos estudiantes diferentes.")


def _validar_coherencia_con_programacion(*, clase, estudiante_1, estudiante_2, programacion):
    """
    Si se indicó una programación, ambos estudiantes deben estar
    inscritos (InscripcionEstudiante) en esa clase.

    Fase 11 (Adenda 9): con ProgramacionClase.clase como FK directa
    hacia Clase, la validación se simplifica a UNA condición en vez de
    dos — antes había que cruzar clase + edición de la programación
    por separado, porque ProgramacionClase no conocía la clase
    directamente. Se aprovecha para agregar una verificación de
    sanidad que antes no se podía hacer: que la programación indicada
    efectivamente pertenezca a la clase de la pareja, no a otra.
    """
    if programacion is None:
        return

    if programacion.clase_id != clase.pk:
        raise ValidationError(
            "La programación indicada no pertenece a la clase seleccionada."
        )

    inscritos_en_clase = set(
        InscripcionEstudiante.objects
        .filter(clase=clase)
        .values_list("estudiante_id", flat=True)
    )

    faltantes = [
        estudiante for estudiante in (estudiante_1, estudiante_2)
        if estudiante.pk not in inscritos_en_clase
    ]
    if faltantes:
        nombres = ", ".join(f"{e.nombre} {e.apellido}" for e in faltantes)
        raise ValidationError(
            f"No es posible asignar esta programación: {nombres} no está(n) "
            f"inscrito(s) en la clase {clase}."
        )


def crear_pareja(*, clase, estudiante_1, estudiante_2, programacion=None):
    """
    Crea una Pareja como unidad atómica, usando la utilidad de Unit of
    Work de core/ (primer uso real del proyecto, sección 9.2 del Plan
    Maestro): valida en la misma transacción que ambos estudiantes
    sean distintos y que la clase sea coherente con la programación
    indicada (si se indicó alguna), antes de persistir.
    """
    with UnitOfWork():
        _validar_estudiantes_distintos(estudiante_1=estudiante_1, estudiante_2=estudiante_2)
        _validar_coherencia_con_programacion(
            clase=clase, estudiante_1=estudiante_1, estudiante_2=estudiante_2, programacion=programacion
        )
        pareja = Pareja(
            clase=clase,
            programacion=programacion,
            estudiante_1=estudiante_1,
            estudiante_2=estudiante_2,
        )
        pareja.full_clean()
        pareja.save()
        return pareja

def actualizar_pareja(*, pareja, **campos):
    """
    Actualiza una pareja existente, revalidando las mismas reglas que
    crear_pareja() contra los valores finales (nuevos o heredados del
    registro actual) — mismo criterio ya usado en
    academico.actualizar_inscripcion.
    """
    estudiante_1 = campos.get("estudiante_1", pareja.estudiante_1)
    estudiante_2 = campos.get("estudiante_2", pareja.estudiante_2)
    clase = campos.get("clase", pareja.clase)
    programacion = campos.get("programacion", pareja.programacion)

    with UnitOfWork():
        _validar_estudiantes_distintos(estudiante_1=estudiante_1, estudiante_2=estudiante_2)
        _validar_coherencia_con_programacion(
            clase=clase, estudiante_1=estudiante_1, estudiante_2=estudiante_2, programacion=programacion
        )
        for campo, valor in campos.items():
            setattr(pareja, campo, valor)
        pareja.full_clean()
        pareja.save()
        return pareja


def eliminar_pareja(*, pareja):
    """
    Elimina una pareja de forma permanente. Pareja es la última hoja
    del grafo de dependencias del proyecto (Nivel 3): ningún otro
    modelo la referencia, así que este borrado no tiene efectos
    colaterales y no necesita capturar ninguna excepción.
    """
    pareja.delete()