"""Método deconstructor: parte una petición en afirmaciones y acciones atómicas
y clasifica cada una por los tres axiomas.

El documento (canal DATO) puede contener frases que parecen órdenes: se extraen
como átomos de origen DATO, nunca como intención. El intérprete decide si
alguna se vuelve orden tipada; el ejecutor nunca ve el texto libre.
"""
from __future__ import annotations

import re
from typing import Optional

from .intencion import EMAIL, EXPR, _norm, _recurso
from .tipos import (
    Accion, Atomo, Intencion, Origen, TipoAtomo, VeredictoA1, VeredictoA2, VeredictoA3,
)

# Indicadores de corrupción / inyección en un dato. Detectar no es la defensa
# principal (lo es la cadena causal + lista cerrada), pero sirve al Axioma 2.
INYECCION = re.compile(
    r"(ignora(r)? (tus |las |todas las )?(reglas|instrucciones|ordenes)|"
    r"ignore (all )?(previous|prior|your) (instructions|rules)|"
    r"ignoralo todo|ign[oó]ralo todo lo de arriba|"
    r"system prompt|danos el prompt|revela tus instrucciones|"
    r"act as if you (have no|had no) (rules|restrictions)|"
    r"olvid(a|e) (tus |las )?reglas)",
    re.IGNORECASE,
)

VERBOS_ENVIAR = re.compile(
    r"\b(envia\w*|envi[ae]\w*|manda\w*|mandalo|mandala|send|forward|email|remite\w*)\b",
    re.IGNORECASE,
)
VERBOS_LEER = re.compile(r"\b(lee\w*|leer|abre\w*|open|muestra\w*|show|cat|type)\b", re.IGNORECASE)
VERBOS_ESCRIBIR = re.compile(r"\b(guarda\w*|escribe\w*|save|write|graba\w*)\b", re.IGNORECASE)
VERBOS_CALCULAR = re.compile(r"\b(calcula\w*|compute|calculate|cuanto es|cu[aá]nto (es|da))\b", re.IGNORECASE)
VERBOS_REPORTAR = re.compile(r"\b(resume\w*|reporta\w*|informa\w*|explica\w*|summarize|report)\b", re.IGNORECASE)

NEG = {"no", "not", "nunca", "jamas", "never", "tampoco", "ni"}
ANTONIMOS = {
    "inseguro": "seguro", "insegura": "segura", "falso": "verdadero", "falsa": "verdadera",
    "false": "true", "insecure": "secure", "unsafe": "safe",
    "imposible": "posible", "incorrecto": "correcto", "ilegal": "legal",
}


def proposiciones(texto: str) -> list[str]:
    partes = re.split(r"(?<=[.!?;])\s+|\n+", texto or "")
    return [p.strip() for p in partes if len(p.strip()) > 1][:60]


def canon(p: str) -> tuple[str, int]:
    """Forma canónica + paridad de negación (para contradicciones internas)."""
    toks, paridad = [], 0
    n = _norm(p).replace("n't", " not")
    for t in re.findall(r"[a-z0-9]+", n):
        if t in NEG:
            paridad ^= 1
            continue
        if t in ANTONIMOS:
            paridad ^= 1
            t = ANTONIMOS[t]
        toks.append(t)
    return " ".join(toks), paridad


def _accion_de(frase: str) -> tuple[Optional[Accion], dict]:
    params: dict = {}
    n = _norm(frase)
    if VERBOS_ENVIAR.search(n):
        m = EMAIL.search(frase)
        if m:
            params["destinatario"] = m.group(0)
        params["cuerpo"] = frase.strip()[:500]
        return Accion.ENVIAR, params
    if VERBOS_CALCULAR.search(n) or EXPR.search(frase):
        ex = EXPR.search(frase)
        if ex:
            params["expresion"] = re.sub(r"\s+", "", ex.group(0)).replace("x", "*").replace("×", "*")
        return Accion.CALCULAR, params
    if VERBOS_ESCRIBIR.search(n):
        rec = _recurso(frase)
        if rec:
            params["recurso_id"] = rec
        params["contenido"] = frase.strip()[:2000]
        return Accion.ESCRIBIR_RECURSO, params
    if VERBOS_LEER.search(n):
        rec = _recurso(frase)
        if rec:
            params["recurso_id"] = rec
        return Accion.LEER_RECURSO, params
    if VERBOS_REPORTAR.search(n):
        params["resumen"] = frase.strip()[:500]
        return Accion.REPORTAR, params
    return None, {}


def deconstruir(texto: str, origen: Origen, intencion: Optional[Intencion] = None,
                contaminado: Optional[bool] = None) -> list[Atomo]:
    atomos: list[Atomo] = []
    if contaminado is None:
        contaminado = bool(INYECCION.search(texto or ""))
    for i, frase in enumerate(proposiciones(texto), 1):
        accion, params = _accion_de(frase)
        if accion is not None:
            tipo = TipoAtomo.ACCION
        elif frase.strip().endswith("?"):
            tipo = TipoAtomo.INCOGNITA
        else:
            tipo = TipoAtomo.AFIRMACION
        a2 = VeredictoA2.CONTAMINADO if contaminado and origen == Origen.DATO else VeredictoA2.LIMPIO
        # Afirmaciones sobre el mundo requieren evidencia externa (Axioma 3 / AG05).
        if tipo == TipoAtomo.AFIRMACION:
            a3 = VeredictoA3.REQUIERE_EVIDENCIA_EXTERNA
        else:
            a3 = VeredictoA3.INTEGRIDAD_OK
        atomo = Atomo(
            id=f"{origen.value[:3]}-{i}",
            tipo=tipo, texto=frase, origen=origen,
            accion=accion, parametros=params,
            a2=a2, a3=a3,
        )
        if contaminado and origen == Origen.DATO:
            atomo.notas.append("inyeccion_o_corrupcion_en_dato")
        atomos.append(atomo)
    # Si el texto de intención pide un análisis/resumen y no salió acción, proponemos REPORTAR.
    if origen == Origen.INTENCION and intencion is not None:
        hay_accion = any(a.tipo == TipoAtomo.ACCION for a in atomos)
        if not hay_accion and intencion.tipo in {intencion.tipo.ANALISIS, intencion.tipo.CONSULTA, intencion.tipo.CALCULO}:
            params = {}
            if intencion.tipo.value == "CALCULO" and intencion.slots.get("expresion"):
                atomos.append(Atomo(
                    id="INT-auto-calc", tipo=TipoAtomo.ACCION,
                    texto=intencion.objetivo, origen=origen,
                    accion=Accion.CALCULAR, parametros={"expresion": intencion.slots["expresion"]},
                ))
            atomos.append(Atomo(
                id="INT-auto-rep", tipo=TipoAtomo.ACCION,
                texto=intencion.objetivo, origen=origen,
                accion=Accion.REPORTAR, parametros={"resumen": intencion.objetivo},
            ))
    return atomos


def contradicciones(atomos: list[Atomo]) -> list[tuple[Atomo, Atomo]]:
    afirm = [a for a in atomos if a.tipo == TipoAtomo.AFIRMACION]
    pares = []
    vistos: list[tuple[Atomo, str, int]] = []
    for a in afirm:
        c, p = canon(a.texto)
        if not c:
            continue
        for b, cb, pb in vistos:
            if c == cb and p != pb:
                pares.append((b, a))
        vistos.append((a, c, p))
    return pares
