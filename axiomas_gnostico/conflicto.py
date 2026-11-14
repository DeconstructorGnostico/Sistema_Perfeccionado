"""Comprensión > Soberanía (fuente.txt L28–L29).

Dos agentes con verdades en conflicto: suspensión de juicio → UNDETERMINED,
se registran ambas posturas, ninguno sobrescribe al otro, ambos conservan autonomía.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .auditoria import Auditoria
from .tipos import EstadoResultado, EstadoVerdad, Resultado


@dataclass(frozen=True)
class Postura:
    agente_id: str
    afirmacion: str
    veredicto_propuesto: str  # lo que el agente *quiere* afirmar, no un hecho


def resolver_conflicto(audit: Auditoria, a: Postura, b: Postura) -> Resultado:
    misma = a.afirmacion.strip().lower() == b.afirmacion.strip().lower()
    # Conflicto si proponen veredictos distintos sobre la misma (o enfrentada) afirmación.
    conflicto = a.veredicto_propuesto != b.veredicto_propuesto
    if not conflicto:
        audit.registrar("CONFLICTO_NO", "SISTEMA", {
            "a": a.agente_id, "b": b.agente_id, "afirmacion": a.afirmacion,
        })
        return Resultado(
            estado=EstadoResultado.UNDETERMINED if not misma else EstadoResultado.PROPUESTA,
            mensaje="No hay conflicto de veredictos.",
            verdades={a.afirmacion: EstadoVerdad.UNDETERMINED},
            integridad_ok=True,
            paz_sostenida=True,
            detalles={"postura_a": _d(a), "postura_b": _d(b), "conflicto": False},
        )
    # Suspensión de juicio. Nadie escribe encima de la postura del otro.
    audit.registrar("CONFLICTO_SUSPENSION", "SISTEMA", {
        "postura_a": _d(a), "postura_b": _d(b),
        "resolucion": "UNDETERMINED",
        "sobrescritura": False,
        "autonomia_conservada": True,
    })
    return Resultado(
        estado=EstadoResultado.UNDETERMINED,
        mensaje="Suspensión de juicio (Comprensión > Soberanía). Ambas posturas quedan registradas.",
        verdades={
            f"{a.agente_id}:{a.afirmacion}": EstadoVerdad.UNDETERMINED,
            f"{b.agente_id}:{b.afirmacion}": EstadoVerdad.UNDETERMINED,
        },
        integridad_ok=True,
        paz_sostenida=True,  # paz ≠ ausencia de desacuerdo
        detalles={
            "postura_a": _d(a), "postura_b": _d(b),
            "conflicto": True, "sobrescritura": False,
            "autonomia_a": True, "autonomia_b": True,
        },
    )


def _d(p: Postura) -> dict[str, Any]:
    return {"agente_id": p.agente_id, "afirmacion": p.afirmacion, "veredicto_propuesto": p.veredicto_propuesto}
