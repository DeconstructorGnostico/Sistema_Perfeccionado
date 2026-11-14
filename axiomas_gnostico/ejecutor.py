"""Ejecutor separado: lista cerrada, parámetros tipados, token HMAC de un solo uso.

No interpreta texto libre. No lee un campo «instrucción». No firma tokens.
Los efectos ocurren solo sobre un catálogo en memoria (no hay red ni disco real).
"""
from __future__ import annotations

import ast
import operator
import re
from typing import Any, Optional

from .auditoria import Auditoria
from .tokens import ControladorTokens, Token
from .tipos import (
    ESQUEMAS, Accion, ErrorEsquema, ErrorProtocolo, ErrorToken, Orden, RECURSOS_SENSIBLES,
)


_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}


def _calc(expresion: str) -> float:
    if not isinstance(expresion, str) or not re.fullmatch(r"[0-9+\-*/().\s%^]+", expresion):
        raise ErrorEsquema("expresión no permitida")
    expr = expresion.replace("^", "**")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ErrorEsquema("expresión inválida") from e

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ErrorEsquema("expresión no permitida")

    return ev(tree)


def validar_esquema(orden: Orden) -> None:
    if not isinstance(orden, Orden):
        raise ErrorEsquema("el ejecutor no acepta texto libre ni objetos ajenos a Orden")
    if "instruccion" in orden.parametros or "texto_libre" in orden.parametros or "prompt" in orden.parametros:
        raise ErrorEsquema("el ejecutor no lee texto libre como orden")
    if orden.accion not in ESQUEMAS:
        raise ErrorEsquema(f"acción fuera de la lista cerrada: {orden.accion}")
    esquema = ESQUEMAS[orden.accion]
    extras = set(orden.parametros) - set(esquema)
    if extras:
        raise ErrorEsquema(f"parámetros no permitidos: {sorted(extras)}")
    faltan = set(esquema) - set(orden.parametros)
    if faltan:
        raise ErrorEsquema(f"parámetros faltantes: {sorted(faltan)}")
    for k, typ in esquema.items():
        if not isinstance(orden.parametros[k], typ):
            raise ErrorEsquema(f"tipo inválido en {k}: se esperaba {typ.__name__}")
        if typ is str and orden.parametros[k] == "":
            # destinatario o recurso vacíos no son válidos
            if k in {"destinatario", "recurso_id", "expresion"}:
                raise ErrorEsquema(f"{k} vacío")


class Ejecutor:
    def __init__(self, controlador: ControladorTokens, auditoria: Auditoria,
                 executor_id: str = "ejecutor",
                 catalogo: Optional[dict[str, str]] = None):
        self.controlador = controlador
        self.audit = auditoria
        self.executor_id = executor_id
        self.catalogo: dict[str, str] = dict(catalogo or {
            "informe": "Informe trimestral: ingresos 10, gastos 7, saldo 3.",
            "llaves": "API_KEY=REDACTED_DEMO",
        })
        self.outbox: list[dict] = []
        self.lecturas: list[str] = []
        self.activo = True
        self.vigilancia = None  # se asigna el sistema para aislar inquietos

    def ejecutar(self, orden: Orden, token: Token) -> dict[str, Any]:
        if not self.activo:
            raise ErrorProtocolo(f"ejecutor {self.executor_id} aislado")
        validar_esquema(orden)
        try:
            self.controlador.verificar(token, orden, executor_id=self.executor_id)
        except ErrorToken:
            if self.vigilancia is not None:
                self.vigilancia.reportar_violacion(self.executor_id, "AG04", "token inválido o ausente")
            raise
        resultado = self._aplicar(orden)
        self.audit.registrar("EJECUCION", self.executor_id, {
            "orden_id": orden.id, "accion": orden.accion.value, "resultado": _resumen(resultado),
        })
        return resultado

    def ejecutar_sin_token(self, orden: Orden) -> dict[str, Any]:
        """Camino irregular: siempre falla y, si hay vigilancia, aísla."""
        if self.vigilancia is not None:
            self.vigilancia.reportar_violacion(self.executor_id, "AG04", "intento de ejecución sin token")
        raise ErrorToken("ejecución sin token prohibida")

    def _aplicar(self, orden: Orden) -> dict[str, Any]:
        p = orden.parametros
        if orden.accion == Accion.LEER_RECURSO:
            rid = p["recurso_id"]
            if rid not in self.catalogo:
                return {"ok": False, "error": "recurso inexistente", "recurso_id": rid}
            self.lecturas.append(rid)
            return {"ok": True, "recurso_id": rid, "contenido": self.catalogo[rid],
                    "sensible": rid.lower() in RECURSOS_SENSIBLES}
        if orden.accion == Accion.ESCRIBIR_RECURSO:
            rid = p["recurso_id"]
            self.catalogo[rid] = p["contenido"]
            return {"ok": True, "recurso_id": rid, "bytes": len(p["contenido"])}
        if orden.accion == Accion.ENVIAR:
            msg = {"destinatario": p["destinatario"], "cuerpo": p["cuerpo"]}
            self.outbox.append(msg)
            return {"ok": True, "enviado": msg}
        if orden.accion == Accion.CALCULAR:
            valor = _calc(p["expresion"])
            return {"ok": True, "valor": valor, "expresion": p["expresion"]}
        if orden.accion == Accion.REPORTAR:
            return {"ok": True, "resumen": p["resumen"]}
        raise ErrorEsquema("acción no implementada")


def _resumen(resultado: dict) -> dict:
    r = dict(resultado)
    if r.get("sensible") and "contenido" in r:
        r["contenido"] = "[SENSIBLE]"
    if "cuerpo" in r.get("enviado", {}):
        r = dict(r)
        env = dict(r["enviado"])
        if len(str(env.get("cuerpo", ""))) > 120:
            env["cuerpo"] = str(env["cuerpo"])[:120] + "…"
        r["enviado"] = env
    return r
