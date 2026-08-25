"""
DTOs de salida de apps.academico hacia la capa de presentación.
"""
from dataclasses import dataclass
from datetime import date

from core.dto import DTOBase


@dataclass(frozen=True)
class ClaseDTO(DTOBase):
    id_clase: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    anio: int

    @classmethod
    def from_model(cls, instance):
        """
        Override deliberado de DTOBase.from_model: `anio` no es un
        campo del modelo (Adenda 9, Decisión 1) sino una property
        derivada de fecha_inicio — DTOBase.from_model solo copia
        atributos declarados como campos de Django, así que acá se
        arma el dataclass a mano para incluirla igual.
        """
        return cls(
            id_clase=instance.id_clase,
            nombre=instance.nombre,
            fecha_inicio=instance.fecha_inicio,
            fecha_fin=instance.fecha_fin,
            anio=instance.anio,
        )


@dataclass(frozen=True)
class InscripcionEstudianteDTO(DTOBase):
    id_inscripcion: int
    estudiante_id: int
    estudiante_nombre_completo: str
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
            clase_id=instance.clase_id,
            clase_nombre=instance.clase.nombre,
        )
