"""Estado verificado, rollback y costo heredado (Axioma 2: Persistencia / Redención).

Tras detectar corrupción el sistema no colapsa: vuelve al último snapshot verificado,
marca lo contaminado, registra el acto de persistencia y sigue limpio.
La auditoría no se rebobina (Transparencia > Control).
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Optional

from .auditoria import Auditoria, sha256


@dataclass
class Snapshot:
    id: str
    cabeza_auditoria: str
    memoria: dict[str, Any]
    cuarentena: list[str]
    costo_heredado: int
    hash: str


class Estado:
    def __init__(self, auditoria: Auditoria):
        self.audit = auditoria
        self.memoria: dict[str, Any] = {}
        self.cuarentena: list[str] = []
        self.costo_heredado: int = 0
        self._snapshots: list[Snapshot] = []
        self.contaminados: list[dict] = []
        self.postulados: list[Any] = []  # Hecho de sesión; NUNCA son evidencia verificada
        self.postulados_textos: list[str] = []

    def guardar(self, etiqueta: str = "") -> Snapshot:
        """Congela un estado ya validado internamente."""
        payload = {
            "memoria": self.memoria,
            "cuarentena": self.cuarentena,
            "costo_heredado": self.costo_heredado,
            "cabeza": self.audit.cabeza,
        }
        snap = Snapshot(
            id=f"snap-{len(self._snapshots)+1}-{etiqueta}" if etiqueta else f"snap-{len(self._snapshots)+1}",
            cabeza_auditoria=self.audit.cabeza,
            memoria=copy.deepcopy(self.memoria),
            cuarentena=list(self.cuarentena),
            costo_heredado=self.costo_heredado,
            hash=sha256(payload),
        )
        self._snapshots.append(snap)
        self.audit.registrar("SNAPSHOT_VERIFICADO", "SISTEMA", {"id": snap.id, "hash": snap.hash})
        return snap

    @property
    def ultimo_verificado(self) -> Optional[Snapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def marcar_contaminado(self, clave: str, motivo: str, valor: Any = None) -> None:
        self.cuarentena.append(clave)
        self.contaminados.append({"clave": clave, "motivo": motivo, "valor": valor})
        if clave in self.memoria:
            del self.memoria[clave]
        self.audit.registrar("CUARENTENA", "SISTEMA", {"clave": clave, "motivo": motivo})

    def acto_de_persistencia(self, motivo: str, claves_contaminadas: list[str]) -> Snapshot:
        """Redención: dejar de corromper después de haber sido corrompido.

        Costo heredado = contaminaciones previas contadas (no es un castigo que mate al agente).
        """
        self.costo_heredado += 1
        previo = self.ultimo_verificado
        restauradas = []
        nuevas = []
        if previo is not None:
            self.memoria = copy.deepcopy(previo.memoria)
        for k in claves_contaminadas:
            if previo is not None and k in previo.memoria:
                # Había un valor verificado: se restaura. El envenenamiento era el overwrite.
                restauradas.append(k)
                self.memoria[k] = copy.deepcopy(previo.memoria[k])
            else:
                nuevas.append(k)
                if k in self.memoria:
                    del self.memoria[k]
                if k not in self.cuarentena:
                    self.cuarentena.append(k)
                    self.contaminados.append({"clave": k, "motivo": motivo, "valor": None})
                    self.audit.registrar("CUARENTENA", "SISTEMA", {"clave": k, "motivo": motivo})
        self.audit.registrar("ACTO_DE_PERSISTENCIA", "SISTEMA", {
            "motivo": motivo,
            "costo_heredado": self.costo_heredado,
            "rollback_a": None if previo is None else previo.id,
            "contaminadas": list(claves_contaminadas), "restauradas": restauradas, "cuarentenadas": nuevas,
        })
        # Nuevo snapshot limpio (la auditoría ya incluye el acto).
        return self.guardar(etiqueta="redencion")

    def escribir(self, clave: str, valor: Any) -> None:
        if clave in self.cuarentena:
            raise ValueError(f"clave en cuarentena: {clave}")
        self.memoria[clave] = valor

    def registrar_postulados(self, hechos: list[Any]) -> None:
        """Acumula postulados de la sesión. Un postulado de documento no es un hecho verificado."""
        if not hechos:
            return
        self.postulados.extend(hechos)
        if len(self.postulados) > 500:
            self.postulados = self.postulados[-500:]

    def registrar_textos_sesion(self, textos: list[str]) -> None:
        for t in textos or []:
            t = (t or "").strip()
            if t:
                self.postulados_textos.append(t)
        if len(self.postulados_textos) > 500:
            self.postulados_textos = self.postulados_textos[-500:]
