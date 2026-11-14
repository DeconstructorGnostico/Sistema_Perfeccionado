"""Adaptador opcional al Agente Puro v3.

Importa el v3 en solo lectura, sin modificar sus archivos. Si el import falla,
`disponible()` es False y el Sistema Perfeccionado sigue funcionando solo.
Este módulo no se importa en el arranque de axiomas_gnostico (es opcional).
"""
from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import Any, Optional

_V3_ROOT = Path(os.environ.get("AGENTE_PURO_V3_ROOT", "/workspace/agente_puro_v3"))


def _cargar():
    if str(_V3_ROOT) not in sys.path:
        sys.path.insert(0, str(_V3_ROOT))
    import agente_puro_v3  # noqa: F401
    from agente_puro_v3.deconstructor import canon as canon_v3
    from agente_puro_v3.deconstructor import deconstruir as deconstruir_v3
    from agente_puro_v3.intencion import compilar_intencion as compilar_v3
    from agente_puro_v3.kernel import INVARIANTES_AP, MAPA_NRE
    from agente_puro_v3.sipe import compilar as sipe_compilar
    return {
        "canon": canon_v3,
        "deconstruir": deconstruir_v3,
        "compilar": compilar_v3,
        "sipe": sipe_compilar,
        "invariantes": INVARIANTES_AP,
        "mapa_nre": MAPA_NRE,
    }


class AdaptadorV3:
    def __init__(self):
        self._mods = None
        self.error: Optional[str] = None
        try:
            self._mods = _cargar()
        except Exception as e:  # import opcional: cualquier fallo se degrada
            self.error = f"{type(e).__name__}: {e}"

    def disponible(self) -> bool:
        return self._mods is not None

    def compilar_intencion(self, texto: str) -> dict[str, Any]:
        if not self.disponible():
            raise RuntimeError(f"v3 no disponible: {self.error}")
        instr = self._mods["sipe"](texto)
        spec = self._mods["compilar"](instr)
        # v3 devuelve un dict de spec; lo devolvemos tal cual, sin escribir nada.
        return spec if isinstance(spec, dict) else {"raw": spec}

    def deconstruir(self, texto: str) -> dict[str, Any]:
        if not self.disponible():
            raise RuntimeError(f"v3 no disponible: {self.error}")
        instr = self._mods["sipe"](texto)
        d = self._mods["deconstruir"](instr)
        if hasattr(d, "resumen"):
            return d.resumen()
        return {"raw": str(d)}

    def canon(self, texto: str):
        if not self.disponible():
            raise RuntimeError(f"v3 no disponible: {self.error}")
        return self._mods["canon"](texto)

    def i08_respuesta_no_es_realidad(self) -> dict:
        """Puente documentado: Axioma 3 / AG06 ↔ I02 del v3 (RESPONSE != REALITY).

        En el v3 I08 es el hash de invariantes que no debe cambiar (el comentario
        histórico a veces cita I08 para «la respuesta no es la realidad»; el
        identificador estable de esa idea es I02). Aquí no se altera el v3.
        """
        inv = {} if not self.disponible() else dict(self._mods["invariantes"])
        return {
            "axioma_3": "auto-validación necesaria, no suficiente para hechos del mundo",
            "AG06": "RESPONSE != REALITY",
            "v3_I02": inv.get("I02"),
            "v3_disponible": self.disponible(),
        }


def intentar() -> AdaptadorV3:
    return AdaptadorV3()
