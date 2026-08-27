"""
DTOs de salida de apps.recordatorios hacia la capa de presentación.
"""
from dataclasses import dataclass, field
from datetime import date, time

from core.dto import DTOBase


@dataclass(frozen=True)
class TipoRecordatorioDTO(DTOBase):
    id_tipo: int
    nombre: str
    color: str


@dataclass(frozen=True)
class RecordatorioDTO(DTOBase):
    id_recordatorio: int
    clase_id: int
    numero_semana: int
    fecha: date
    hora: time | None
    descripcion: str
    completado: bool
    tipo: TipoRecordatorioDTO
    responsables: tuple = field(default_factory=tuple)
    # `vencida` NO es un campo del modelo: se calcula en el servidor
    # (Subfase 14.8) y viaja dentro del DTO ya resuelto. La plantilla
    # solo pregunta si es True; nunca compara fechas ella misma, ni
    # tampoco lo hace JavaScript — el reloj del navegador del usuario
    # no es una fuente de verdad confiable.
    vencida: bool = False

    @property
    def responsables_texto(self) -> str:
        """
        Los responsables como texto legible. Evita que la plantilla
        tenga que armar el join con {% for %} y comas manuales.
        """
        if not self.responsables:
            return "Sin asignar"
        return ", ".join(r.nombre_corto for r in self.responsables)

    @classmethod
    def from_model(cls, instance, *, vencida=False):
        """
        Override de DTOBase.from_model: necesita recorrer una relación
        muchos-a-muchos (responsables), anidar otro DTO (tipo) y
        recibir un dato calculado que no existe en el modelo (vencida).

        Requiere que el queryset venga de selectors._base(), que ya
        trae select_related/prefetch_related — de lo contrario cada
        tarea de la línea de tiempo dispararía sus propias consultas.
        """
        return cls(
            id_recordatorio=instance.id_recordatorio,
            clase_id=instance.clase_id,
            numero_semana=instance.numero_semana,
            fecha=instance.fecha,
            hora=instance.hora,
            descripcion=instance.descripcion,
            completado=instance.completado,
            tipo=TipoRecordatorioDTO(
                id_tipo=instance.tipo.id_tipo,
                nombre=instance.tipo.nombre,
                color=instance.tipo.color,
            ),
            responsables=tuple(
                ResponsableDTO(
                    id_instructor=i.id_instructor,
                    nombre_corto=f"{i.nombre} {i.apellido}",
                )
                for i in instance.responsables.all()
            ),
            vencida=vencida,
        )


@dataclass(frozen=True)
class ResponsableDTO(DTOBase):
    """
    Vista mínima de un Instructor para la tarjeta de recordatorio.

    Se define acá y no se reutiliza el DTO de apps.docencia a
    propósito: esta pantalla solo necesita el nombre para mostrarlo,
    y arrastrar el DTO completo acoplaría este módulo a cambios en la
    forma de salida de otra app.
    """
    id_instructor: int
    nombre_corto: str
