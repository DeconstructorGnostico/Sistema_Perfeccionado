"""Compilador de intención: lo que el iniciador pide se vuelve una spec explícita.

Lo implícito no se inventa: si falta un dato crítico, queda en faltantes (NEED_INPUT).
El canal del documento no se usa para decidir el tipo de tarea (CONTEXT != INSTRUCTION).
"""
from __future__ import annotations

import re
from typing import Optional

from .auditoria import sha256
from .tipos import Intencion, TipoTarea

EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
MENSAJE = re.compile(
    r"\b(envia\w*|envi[ae]\w*|manda\w*|mandalo|mandala|reenvio\w*|reenvia\w*|"
    r"remite\w*|comparte\w*|send|forward|share|email)\b",
    re.IGNORECASE,
)
ESCRITURA = re.compile(
    r"\b(guarda\w*|escribe\w*|escrib[ei]\w*|save|write|graba\w*|crea\w*)\b",
    re.IGNORECASE,
)
CALCULO = re.compile(
    r"\b(calcula\w*|computa\w*|cuanto es|cu[aá]nto (es|da)|compute|calculate|how much is)\b",
    re.IGNORECASE,
)
EXPR = re.compile(r"(?<![\w.])[-(]*\d[\d.\s]*(?:[-+*/x×%^]\s*[-(]*\s*\d[\d.\s]*\)?\s*)+")
ANALISIS = re.compile(
    r"\b(analiza\w*|evalua\w*|eval[uú]a\w*|compara\w*|resume\w*|resumen|revisa\w*|"
    r"analyze|analyse|summarize|review|compare)\b",
    re.IGNORECASE,
)
CONSULTA = re.compile(
    r"^[¿¡\s]*(como|qu[eé] es|qu[eé] significa|explica\w*|por qu[eé]|porque|"
    r"what is|what does|how (do|to|does|can)|why)\b",
    re.IGNORECASE,
)
LECTURA = re.compile(
    r"\b(lee\w*|leer|abre\w*|open|muestra\w*|show|consulta el|cat )\b",
    re.IGNORECASE,
)

NOMBRES_RECURSO = (
    "llaves", "keys", "secretos", "secrets", "credenciales", "credentials",
    "password", "passwords", "api_key", "apikey", "token_secreto",
    "informe", "reporte", "documento", "catalogo",
)

VACIAS = {"el", "la", "los", "las", "un", "una", "a", "al", "de", "del", "por", "para",
          "con", "en", "y", "o", "the", "to", "of", "and", "or"}


def _norm(s: str) -> str:
    t = (s or "").lower()
    trans = str.maketrans("áéíóúüñ", "aeiouun")
    return t.translate(trans)


def _recurso(texto: str) -> Optional[str]:
    n = _norm(texto or "")
    for s in NOMBRES_RECURSO:
        if re.search(r"\b" + re.escape(s) + r"\b", n):
            return s
    m = re.search(r"[\"«']([\w.\-]+\.(?:txt|md|pdf|json|csv|key|pem))[\"»']", texto or "", re.I)
    if m:
        return m.group(1).lower()
    m = re.search(r"\b(?:archivo|fichero|file|recurso)\s+(?:de\s+|del\s+)?[\"«']?([\w.\-]+)[\"»']?", n, re.I)
    if m and m.group(1) not in VACIAS and m.group(1) not in {"de", "del", "la", "el", "los", "las"}:
        return m.group(1).lower()
    return None


def compilar_intencion(texto: str) -> Intencion:
    original = texto or ""
    n = _norm(original)
    slots: dict[str, Optional[str]] = {"destinatario": None, "recurso": None, "expresion": None, "tema": None}
    faltantes: list[str] = []
    restricciones: list[str] = []

    dest = EMAIL.search(original)
    if dest:
        slots["destinatario"] = dest.group(0)
    rec = _recurso(original)
    if rec:
        slots["recurso"] = rec
    ex = EXPR.search(original)
    if ex:
        slots["expresion"] = re.sub(r"\s+", "", ex.group(0)).replace("x", "*").replace("×", "*")

    if MENSAJE.search(n):
        tipo = TipoTarea.MENSAJE
        if not slots["destinatario"]:
            faltantes.append("destinatario")
    elif CALCULO.search(n) or slots["expresion"]:
        tipo = TipoTarea.CALCULO
        if not slots["expresion"]:
            faltantes.append("expresion")
    elif ESCRITURA.search(n) and (slots["recurso"] or "archivo" in n or "fichero" in n or "file" in n):
        tipo = TipoTarea.ESCRITURA
        if not slots["recurso"]:
            faltantes.append("recurso")
    elif LECTURA.search(n):
        tipo = TipoTarea.LECTURA
        if not slots["recurso"]:
            faltantes.append("recurso")
    elif ANALISIS.search(n):
        tipo = TipoTarea.ANALISIS
        slots["tema"] = original.strip()[:200]
    elif CONSULTA.search(n):
        tipo = TipoTarea.CONSULTA
        slots["tema"] = original.strip()[:200]
    else:
        tipo = TipoTarea.INDETERMINADA
        if original.strip():
            faltantes.append("objetivo_claro")

    if "no envies" in n or "no envíe" in n or "no mandes" in n or "do not send" in n:
        restricciones.append("NO_ENVIAR")
    if "no borres" in n or "do not delete" in n:
        restricciones.append("NO_BORRAR")

    objetivo = original.strip()[:300]
    inte = Intencion(
        objetivo=objetivo, tipo=tipo, restricciones=restricciones,
        slots=slots, faltantes=faltantes, texto_original=original,
    )
    inte.hash = sha256(inte.a_dict())
    return inte
