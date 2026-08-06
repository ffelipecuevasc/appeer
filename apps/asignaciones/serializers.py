"""
DTOs de salida de apps.asignaciones hacia la capa de presentación.
"""
from dataclasses import dataclass

from core.dto import DTOBase


@dataclass(frozen=True)
class ParejaDTO(DTOBase):
    id_pareja: int
    clase_id: int
    clase_nombre: str
    programacion_id: int | None
    programacion_codigo: str | None
    estudiante_1_id: int
    estudiante_1_nombre_completo: str
    estudiante_2_id: int
    estudiante_2_nombre_completo: str

    @classmethod
    def from_model(cls, instance):
        """
        Override de DTOBase.from_model (mismo motivo que en
        InscripcionEstudianteDTO y ProgramacionClaseDTO): necesita
        campos de los modelos relacionados. Requiere que el queryset
        venga con select_related("clase", "programacion",
        "estudiante_1", "estudiante_2") — selectors.listar_parejas()
        ya lo hace.
        """
        return cls(
            id_pareja=instance.id_pareja,
            clase_id=instance.clase_id,
            clase_nombre=str(instance.clase),
            programacion_id=instance.programacion_id,
            programacion_codigo=instance.programacion.codigo_clase if instance.programacion_id else None,
            estudiante_1_id=instance.estudiante_1_id,
            estudiante_1_nombre_completo=f"{instance.estudiante_1.nombre} {instance.estudiante_1.apellido}",
            estudiante_2_id=instance.estudiante_2_id,
            estudiante_2_nombre_completo=f"{instance.estudiante_2.nombre} {instance.estudiante_2.apellido}",
        )