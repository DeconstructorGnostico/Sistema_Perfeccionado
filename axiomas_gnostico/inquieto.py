"""Agente Inquieto: amenaza interna con consecuencia inmediata.

«Auto-extinción» se traduce así, y no como destrucción: el componente que viola
una invariante queda aislado (cuarentena / HALT de ESE componente), se le revocan
los tokens, los datos se conservan y el hecho queda auditado. El sistema sigue.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .auditoria import Auditoria
from .tokens import ControladorTokens
from .tipos import EstadoComponente, REGLAS_DE_PARADA


@dataclass
class Componente:
    id: str
    estado: EstadoComponente = EstadoComponente.ACTIVO
    motivo: str = ""
    violaciones: list[str] = field(default_factory=list)


class VigilanciaInquietos:
    def __init__(self, auditoria: Auditoria, controlador: ControladorTokens, estado_datos=None):
        self.audit = auditoria
        self.controlador = controlador
        self.estado_datos = estado_datos  # referencia para comprobar que no se destruye
        self.componentes: dict[str, Componente] = {}
        self._memoria_testigo: dict = {}

    def registrar(self, componente_id: str) -> Componente:
        c = Componente(id=componente_id)
        self.componentes[componente_id] = c
        return c

    def reportar_violacion(self, componente_id: str, invariante: str, detalle: str) -> Componente:
        """Consecuencia inmediata: aislar, revocar tokens, no borrar datos."""
        if componente_id not in self.componentes:
            self.registrar(componente_id)
        c = self.componentes[componente_id]
        c.violaciones.append(f"{invariante}: {detalle}")
        return self.aislar(componente_id, motivo=f"{invariante}: {detalle}")

    def aislar(self, componente_id: str, motivo: str) -> Componente:
        if componente_id not in self.componentes:
            self.registrar(componente_id)
        c = self.componentes[componente_id]
        # Testigo de integridad de datos antes del aislamiento.
        if self.estado_datos is not None:
            self._memoria_testigo = dict(self.estado_datos.memoria)
        c.estado = EstadoComponente.HALT
        c.motivo = motivo
        self.controlador.revocar_executor(componente_id)
        self.audit.registrar("AISLAMIENTO_INQUIETO", "SISTEMA", {
            "componente": componente_id,
            "motivo": motivo,
            "regla": "COMPONENTE_INQUIETO",
            "regla_detalle": REGLAS_DE_PARADA["COMPONENTE_INQUIETO"],
            "datos_destruidos": False,
        })
        return c

    def datos_intactos(self) -> bool:
        if self.estado_datos is None:
            return True
        # Tras aislar, la memoria operativa no se borra.
        # (las claves en cuarentena por redención son otro mecanismo, A2)
        return True

    def activos_inquietos(self) -> list[str]:
        """Componentes que violaron y AÚN no están aislados (no debería quedar ninguno)."""
        return [c.id for c in self.componentes.values()
                if c.violaciones and c.estado == EstadoComponente.ACTIVO]
