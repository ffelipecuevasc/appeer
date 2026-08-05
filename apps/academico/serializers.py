"""
DTOs de salida de apps.academico hacia la capa de presentación.
"""
from dataclasses import dataclass
from datetime import date

from core.dto import DTOBase


@dataclass(frozen=True)
class EdicionEscuelaDTO(DTOBase):
    id_edicion: int
    nombre_edicion: str
    fecha_inicio: date | None
    fecha_fin: date | None


@dataclass(frozen=True)
class ClaseDTO(DTOBase):
    id_clase: int
    anio: int
    nombre: str


@dataclass(frozen=True)
class InscripcionEstudianteDTO(DTOBase):
    id_inscripcion: int
    estudiante_id: int
    estudiante_nombre_completo: str
    edicion_id: int
    clase_id: int
    clase_nombre: str

    @classmethod
    def from_model(cls, instance):
        """
        Override deliberado de DTOBase.from_model: acá necesitamos
        campos de modelos relacionados (estudiante.nombre, clase.nombre),
        no solo atributos directos de InscripcionEstudiante. Requiere
        que el queryset venga con select_related("estudiante", "clase")
        —selectors.listar_inscripciones() ya lo hace— para no generar
        una consulta N+1 por cada fila.
        """
        return cls(
            id_inscripcion=instance.id_inscripcion,
            estudiante_id=instance.estudiante_id,
            estudiante_nombre_completo=f"{instance.estudiante.nombre} {instance.estudiante.apellido}",
            edicion_id=instance.edicion_id,
            clase_id=instance.clase_id,
            clase_nombre=instance.clase.nombre,
        )