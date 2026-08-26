"""
DTOs de salida de apps.estudiantes hacia la capa de presentación.
"""
from dataclasses import dataclass, field
from datetime import date

from core.dto import DTOBase


@dataclass(frozen=True)
class ResponsabilidadDTO(DTOBase):
    id_responsabilidad: int
    nombre: str


@dataclass(frozen=True)
class EstudianteDTO(DTOBase):
    id_estudiante: int
    nombre: str
    apellido: str
    genero: str
    fecha_nacimiento: date | None
    fecha_bautismo: date | None
    fecha_inicio_servicio_tiempo_completo: date | None
    matrimonio_id: int | None
    # Fase 12: las responsabilidades viajan ya resueltas dentro del DTO.
    # tuple y no list porque el dataclass es frozen: una lista sería
    # mutable y rompería esa garantía. default_factory permite que el
    # DTO se siga construyendo sin responsabilidades donde no importen.
    responsabilidades: tuple = field(default_factory=tuple)

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    @classmethod
    def from_model(cls, instance):
        """
        Override de DTOBase.from_model: una relación muchos-a-muchos no
        es un atributo simple que se pueda copiar, hay que recorrerla.

        Requiere que el queryset venga con
        prefetch_related("responsabilidades") —
        selectors.listar_estudiantes() y obtener_estudiante_por_id() ya
        lo hacen— o cada estudiante del listado dispararía su propia
        consulta.
        """
        return cls(
            id_estudiante=instance.id_estudiante,
            nombre=instance.nombre,
            apellido=instance.apellido,
            genero=instance.genero,
            fecha_nacimiento=instance.fecha_nacimiento,
            fecha_bautismo=instance.fecha_bautismo,
            fecha_inicio_servicio_tiempo_completo=instance.fecha_inicio_servicio_tiempo_completo,
            matrimonio_id=instance.matrimonio_id,
            responsabilidades=tuple(
                ResponsabilidadDTO(
                    id_responsabilidad=r.id_responsabilidad, nombre=r.nombre
                )
                for r in instance.responsabilidades.all()
            ),
        )
