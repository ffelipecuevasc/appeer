"""
DTOs de salida de apps.planificacion hacia la capa de presentación.
"""
from dataclasses import dataclass

from core.dto import DTOBase


@dataclass(frozen=True)
class ProgramacionClaseDTO(DTOBase):
    id_programacion: int
    edicion_id: int
    edicion_nombre: str
    codigo_clase: str
    numero_semana: int
    dia_semana: str
    numero_aula: int
    instructor_id: int
    instructor_nombre_completo: str
    tema_id: int
    tema_titulo: str

    @classmethod
    def from_model(cls, instance):
        """
        Override de DTOBase.from_model (mismo motivo que
        InscripcionEstudianteDTO en apps.academico): necesita campos
        de los tres modelos relacionados para armar la vista de
        horario. Requiere que el queryset venga con
        select_related("edicion", "instructor", "tema") —
        selectors.listar_programaciones() ya lo hace.
        """
        return cls(
            id_programacion=instance.id_programacion,
            edicion_id=instance.edicion_id,
            edicion_nombre=instance.edicion.nombre_edicion,
            codigo_clase=instance.codigo_clase,
            numero_semana=instance.numero_semana,
            dia_semana=instance.dia_semana,
            numero_aula=instance.numero_aula,
            instructor_id=instance.instructor_id,
            instructor_nombre_completo=f"{instance.instructor.nombre} {instance.instructor.apellido}",
            tema_id=instance.tema_id,
            tema_titulo=instance.tema.titulo_tema,
        )