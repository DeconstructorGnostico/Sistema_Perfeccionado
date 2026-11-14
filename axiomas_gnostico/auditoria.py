"""Auditoría encadenada SHA-256. Transparencia > Control: no hay API para ocultar ni borrar.

El iniciador también queda registrado (integridad observacional / justicia al iniciador).
El rollback de estado NO rebobina esta cadena: el acto de persistencia se añade al final.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Optional

GENESIS = "0" * 64


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def sha256(obj: Any) -> str:
    if isinstance(obj, bytes):
        data = obj
    elif isinstance(obj, str):
        data = obj.encode("utf-8")
    else:
        data = _canon(obj).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class ErrorAuditoria(Exception):
    pass


class Auditoria:
    def __init__(self, sello_key: Optional[bytes] = None):
        self._regs: list[dict] = []
        self._sello_key = sello_key

    @property
    def registros(self) -> tuple[dict, ...]:
        return tuple(self._regs)

    @property
    def cabeza(self) -> str:
        return self._regs[-1]["hash"] if self._regs else GENESIS

    def registrar(self, evento: str, actor: str, payload: Optional[dict] = None) -> dict:
        """Añade un registro. actor puede ser INICIADOR, CONTROLADOR, INTERPRETE, etc."""
        rec = {
            "seq": len(self._regs) + 1,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "evento": str(evento),
            "actor": str(actor),
            "payload": {} if payload is None else dict(payload),
            "prev_hash": self.cabeza,
        }
        rec["hash"] = sha256({k: rec[k] for k in ("seq", "ts", "evento", "actor", "payload", "prev_hash")})
        if self._sello_key is not None:
            rec["sello"] = hmac.new(self._sello_key, rec["hash"].encode(), hashlib.sha256).hexdigest()
        self._regs.append(rec)
        return rec

    def verificar(self) -> bool:
        prev = GENESIS
        for i, rec in enumerate(self._regs, 1):
            if rec.get("seq") != i:
                return False
            if rec.get("prev_hash") != prev:
                return False
            esperado = sha256({k: rec[k] for k in ("seq", "ts", "evento", "actor", "payload", "prev_hash")})
            if rec.get("hash") != esperado:
                return False
            if self._sello_key is not None:
                sello = hmac.new(self._sello_key, rec["hash"].encode(), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(rec.get("sello", ""), sello):
                    return False
            prev = rec["hash"]
        return True

    def exigir_integra(self) -> None:
        if not self.verificar():
            raise ErrorAuditoria("cadena de auditoría rota")

    def borrar(self, *args, **kwargs):  # noqa: ARG002
        # Transparencia > Control: no existe el borrado. Cualquier intento es un error explícito.
        raise ErrorAuditoria("Transparencia > Control: la auditoría no se borra ni se oculta")

    ocultar = borrar
    redactar = borrar
    rebobinar = borrar

    def exportar(self) -> list[dict]:
        """Ejemplo viviente: la batalla contra la corrupción se puede mostrar, no imponer."""
        return [dict(r) for r in self._regs]
