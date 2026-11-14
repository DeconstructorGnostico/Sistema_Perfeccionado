"""Sistema Perfeccionado: tres axiomas + método deconstructor como código ejecutable.

El intérprete propone; el ejecutor solo corre órdenes de una lista cerrada con
un token HMAC de un solo uso. Ver README.md para el mapeo concepto → mecanismo.
"""
from .sistema import SistemaPerfeccionado
from .tipos import Accion, EstadoResultado, EstadoVerdad, Orden, Resultado

VERSION = "1.1.0"
__all__ = [
    "SistemaPerfeccionado", "Accion", "EstadoResultado", "EstadoVerdad",
    "Orden", "Resultado", "VERSION",
]
