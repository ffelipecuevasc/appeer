"""
DTOs de salida de apps.docencia hacia la capa de presentación.
"""
from dataclasses import dataclass

from core.dto import DTOBase


@dataclass(frozen=True)
class InstructorDTO(DTOBase):
    id_instructor: int
    nombre: str
    apellido: str
    cargo: str

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"


@dataclass(frozen=True)
class TemaDTO(DTOBase):
    id_tema: int
    titulo_tema: str
    activo: bool