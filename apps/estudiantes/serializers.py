"""
DTOs de salida de apps.estudiantes hacia la capa de presentación.
"""
from dataclasses import dataclass
from datetime import date

from core.dto import DTOBase


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

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"