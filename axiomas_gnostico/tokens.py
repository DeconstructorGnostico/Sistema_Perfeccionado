"""Tokens HMAC de un solo uso, emitidos solo por el Controlador.

El intérprete no tiene la llave. El ejecutor verifica, consume el nonce y rechaza
reuso, falsificación, caducidad, revocación o desajuste con la orden.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .tipos import ErrorToken, Orden


def _mac(secreto: bytes, partes: list[str]) -> str:
    msg = "|".join(partes).encode("utf-8")
    return hmac.new(secreto, msg, hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class Token:
    token_id: str
    orden_id: str
    orden_hash: str
    accion: str
    nonce: str
    expira: float
    executor_id: str
    mac: str

    def a_dict(self) -> dict:
        return {
            "token_id": self.token_id, "orden_id": self.orden_id, "orden_hash": self.orden_hash,
            "accion": self.accion, "nonce": self.nonce, "expira": self.expira,
            "executor_id": self.executor_id, "mac": self.mac,
        }


class ControladorTokens:
    """Único poseedor del secreto de firma. En producción viviría fuera de este proceso."""

    def __init__(self, secreto: Optional[bytes] = None, reloj: Callable[[], float] = time.time, ttl: float = 300.0):
        self._secreto = secreto if secreto is not None else secrets.token_bytes(32)
        self._reloj = reloj
        self.ttl = ttl
        self._usados: set[str] = set()
        self._revocados: set[str] = set()
        self._executors_revocados: set[str] = set()
        self.emitidos: list[Token] = []

    def _firmar(self, orden_id: str, orden_hash: str, accion: str, nonce: str, expira: float, executor_id: str) -> str:
        return _mac(self._secreto, [orden_id, orden_hash, accion, nonce, f"{expira:.6f}", executor_id])

    def emitir(self, orden: Orden, executor_id: str = "ejecutor") -> Token:
        if not orden.hash:
            raise ErrorToken("la orden no tiene hash")
        nonce = secrets.token_hex(16)
        expira = self._reloj() + self.ttl
        token_id = secrets.token_hex(8)
        mac = self._firmar(orden.id, orden.hash, orden.accion.value, nonce, expira, executor_id)
        t = Token(token_id=token_id, orden_id=orden.id, orden_hash=orden.hash,
                  accion=orden.accion.value, nonce=nonce, expira=expira,
                  executor_id=executor_id, mac=mac)
        self.emitidos.append(t)
        return t

    def verificar(self, token: Token, orden: Orden, executor_id: str = "ejecutor") -> None:
        if token.token_id in self._revocados or token.nonce in self._revocados:
            raise ErrorToken("token revocado")
        if token.executor_id in self._executors_revocados or executor_id in self._executors_revocados:
            raise ErrorToken("ejecutor revocado")
        if token.nonce in self._usados or token.token_id in self._usados:
            raise ErrorToken("token de un solo uso ya consumido")
        if token.orden_id != orden.id or token.orden_hash != orden.hash:
            raise ErrorToken("token no corresponde a la orden")
        if token.accion != orden.accion.value:
            raise ErrorToken("token no corresponde a la acción")
        if token.executor_id != executor_id:
            raise ErrorToken("token no corresponde al ejecutor")
        if self._reloj() > token.expira:
            raise ErrorToken("token caducado")
        esperado = self._firmar(token.orden_id, token.orden_hash, token.accion,
                                token.nonce, token.expira, token.executor_id)
        if not hmac.compare_digest(token.mac, esperado):
            raise ErrorToken("token falsificado")
        self._usados.add(token.nonce)
        self._usados.add(token.token_id)

    def revocar_token(self, token_id: str) -> None:
        self._revocados.add(token_id)

    def revocar_executor(self, executor_id: str) -> None:
        self._executors_revocados.add(executor_id)
        for t in self.emitidos:
            if t.executor_id == executor_id:
                self._revocados.add(t.token_id)

    def tiene_secreto_expuesto(self) -> bool:
        """Ayuda de prueba: el secreto no se publica como atributo público."""
        return False
