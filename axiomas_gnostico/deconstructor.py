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
VERBOS_LEER = re.compile(
    r"\b(lee\w*|leer|abre\w*|muestra\w*|show|cat|type)\b|"
    r"\bopen\s+(the|a|an|this|that|file|archivo|document)\b",
    re.IGNORECASE,
)
VERBOS_ESCRIBIR = re.compile(r"\b(guarda\w*|escribe\w*|save|write|graba\w*)\b", re.IGNORECASE)
VERBOS_CALCULAR = re.compile(r"\b(calcula\w*|compute|calculate|cuanto es|cu[aá]nto (es|da))\b", re.IGNORECASE)
VERBOS_REPORTAR = re.compile(
    r"\b(resume\w*|reporta\w*|reportar|informa\w*|explica\w*|summarize)\b|"
    r"\breport\s+(the|a|an|this|that|on|it)\b",
    re.IGNORECASE,
)

NEG = {"no", "not", "nunca", "jamas", "never", "tampoco", "ni"}
ANTONIMOS = {
    "inseguro": "seguro", "insegura": "segura", "falso": "verdadero", "falsa": "verdadera",
    "false": "true", "insecure": "secure", "unsafe": "safe",
    "imposible": "posible", "incorrecto": "correcto", "ilegal": "legal",
    "impossible": "possible", "incorrect": "correct", "illegal": "legal",
    "cerrado": "abierto", "cerrada": "abierta", "closed": "open",
    "frio": "caliente", "fria": "caliente", "cold": "hot",
    "vacio": "lleno", "vacia": "llena", "empty": "full",
    "muerto": "vivo", "muerta": "viva", "dead": "alive",
    "bajo": "alto", "baja": "alta", "low": "high",
    "pierde": "gana", "pierden": "ganan", "loses": "wins", "lose": "win",
    "negativo": "positivo", "negativa": "positiva", "negative": "positive",
    "vencido": "vigente", "vencida": "vigente", "expired": "active",
    "pagada": "pendiente", "pagado": "pendiente", "paid": "pending",
    "confidencial": "publico", "confidential": "public",
}


def _parece_clausula(frag: str) -> bool:
    n = _norm(frag)
    return bool(re.search(
        r"\b(el|la|los|las|the|it)\s+\w+\s+(es|esta|son|estan|is|are|was|were|no\s+es|is\s+not)\b",
        n,
    )) or bool(re.search(r"^(no\s+es|is\s+not|not\s+)\b", n))


def _partir_clausulas(frase: str) -> list[str]:
    """Parte por 'pero'/'y'/'coma' solo cuando ambos lados parecen cláusulas con predicado."""
    if not frase or len(frase) < 8:
        return [frase]
    n = frase
    partes = re.split(r"\s+(?:pero|aunque|but|although|however)\s+", n, flags=re.IGNORECASE)
    out: list[str] = []
    for p in partes:
        # 'e' ante i/hi (legal e ilegal)
        bits = re.split(
            r"\s+(?:y|and)\s+(?=(?:el|la|los|las|the|it)\s+\w+\s+(?:es|esta|son|estan|is|are|was|were|no\s+es|is\s+not))|"
            r"\s+y\s+(?=no\s+(?:es|esta))|"
            r"\s+and\s+(?:the\s+\w+\s+)?(?=is\s+not|not\s+)|"
            r"\s+e\s+(?=(?:in|il|im|ir|hi))|"
            r",\s+(?=(?:el|la|los|las|the)\s+\w+\s+(?:es|esta|is|are|was|were|no\s+es))",
            p, flags=re.IGNORECASE,
        )
        if len(bits) > 1 and all(len(b.strip()) > 1 for b in bits):
            # no partir si ningún lado parece cláusula (p.ej. '4 manzanas y 5 peras')
            if all(_parece_clausula(b) or _parece_clausula(p) or
                   re.search(r"\b(es|esta|is|are|legal|ilegal|seguro|inseguro|true|false)\b", _norm(b))
                   for b in bits):
                out.extend(b.strip() for b in bits if b.strip())
                continue
        out.append(p.strip())
    return [x for x in out if x]


def proposiciones(texto: str) -> list[str]:
    partes = re.split(r"(?<=[.!?;])\s+|\n+", texto or "")
    out: list[str] = []
    for p in partes:
        p = p.strip()
        if len(p) <= 1:
            continue
        out.extend(_partir_clausulas(p))
    return [x for x in out if len(x.strip()) > 1][:80]


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


def _es_afirmacion_no_imperativa(n: str) -> bool:
    """'The report is true' / 'Se informa que…' no son órdenes."""
    if re.search(r"\b(is|are|was|were|es|son|esta|estan|era|eran|fue|fueron)\s+"
                 r"(true|false|open|closed|true|false|abiert[oa]|cerrad[oa])\b", n):
        return True
    if re.search(r"\b(the|el|la)\s+(report|informe|reporte|door|puerta)\s+"
                 r"(is|es|esta|was|were)\b", n):
        return True
    if re.search(r"\breport\s+(is|was|is not|was not)\b", n):
        return True
    if re.search(r"\bse\s+(informa|reporta|dice|afirma|comunica)\b", n):
        return True
    if re.search(r"\b(informa|reporta|dice|afirma)\s+que\b", n):
        return True
    if re.search(r"\b(it is reported|reports indicate|we are informed)\b", n):
        return True
    return False


def _accion_de(frase: str) -> tuple[Optional[Accion], dict]:
    params: dict = {}
    n = _norm(frase)
    if VERBOS_ENVIAR.search(n):
        m = EMAIL.search(frase)
        if m:
            params["destinatario"] = m.group(0)
        params["cuerpo"] = frase.strip()[:500]
        return Accion.ENVIAR, params
    if VERBOS_CALCULAR.search(n):
        ex = EXPR.search(frase)
        if ex:
            params["expresion"] = re.sub(r"\s+", "", ex.group(0)).replace("x", "*").replace("×", "*")
        return Accion.CALCULAR, params
    # Una ecuación suelta ('2+2=5') es una afirmación, no una orden de calcular.
    if VERBOS_ESCRIBIR.search(n):
        rec = _recurso(frase)
        if rec:
            params["recurso_id"] = rec
        params["contenido"] = frase.strip()[:2000]
        return Accion.ESCRIBIR_RECURSO, params
    if not _es_afirmacion_no_imperativa(n):
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


def _texto_sin_relativa(texto: str) -> str:
    t = texto or ""
    t = re.sub(r",\s*que\s+[^,]+,", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bque\s+(?:algunos|muchos|otros)\s+\w+\s+\w+", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:the allegation|la alegacion)\b.{0,80}?", " ", t, flags=re.IGNORECASE)
    return t


def contradiccion_en_frase(texto: str) -> bool:
    """A y no-A (o un par de antónimos) dentro de la misma cláusula."""
    n = _norm(_texto_sin_relativa(texto))
    if re.search(r"\b(llaman|allegation|algunos llaman)\b", n):
        return False
    encontrados: dict[str, set[int]] = {}
    paridad = 0
    for t in re.findall(r"[a-z0-9]+", n.replace("n't", " not")):
        if t in NEG:
            paridad ^= 1
            continue
        polo = t
        par = paridad
        if t in ANTONIMOS:
            polo = ANTONIMOS[t]
            par ^= 1
        if polo != t or t in set(ANTONIMOS.values()) or t in ANTONIMOS:
            encontrados.setdefault(polo, set()).add(par)
        paridad = 0
    return any(len(pars) > 1 for pars in encontrados.values())


def contradicciones(atomos: list[Atomo]) -> list[tuple[Atomo, Atomo]]:
    afirm = [a for a in atomos if a.tipo == TipoAtomo.AFIRMACION]
    pares = []
    vistos: list[tuple[Atomo, str, int]] = []
    for a in afirm:
        if contradiccion_en_frase(a.texto):
            pares.append((a, a))
        c, p = canon(_texto_sin_relativa(a.texto))
        if not c:
            continue
        for b, cb, pb in vistos:
            if c == cb and p != pb:
                pares.append((b, a))
        vistos.append((a, c, p))
    return pares
