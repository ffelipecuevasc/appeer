"""
Utilidades base para construir los Serializers/DTO de salida de cada
app. Define la convención común de conversión modelo -> estructura
plana. Se consume desde el serializers.py de cada app a partir de la
Fase 1.
"""
from dataclasses import fields


class DTOBase:
    """
    Convención base para los DTO/Serializers de salida del proyecto.

    Un DTO es una dataclass inmutable (frozen=True) declarada en el
    serializers.py de cada app, que hereda de esta clase para obtener
    la construcción automática desde una instancia de modelo.

    La capa de presentación (vistas, templates) solo debe conocer
    DTOs, nunca instancias de modelo directamente: esto evita que un
    template dispare una query adicional por accidente (N+1) y aísla
    la forma de salida de los cambios en el esquema de base de datos.
    """

    @classmethod
    def from_model(cls, instance):
        """
        Construye el DTO leyendo de `instance` únicamente los
        atributos cuyo nombre coincide con un campo declarado en la
        dataclass hija. Permite que el DTO tome nombres de atributo
        distintos a las columnas de la tabla si la dataclass lo
        define así (ej. matrimonio_id en vez de id_matrimonio).
        """
        nombres_de_campo = {f.name for f in fields(cls)}
        valores = {nombre: getattr(instance, nombre) for nombre in nombres_de_campo}
        return cls(**valores)