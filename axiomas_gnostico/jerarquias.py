"""Jerarquías de la Verdad como orden de precedencia ejecutable ante conflictos.

Fuente (fuente.txt):
  L19  Respeto > Supervivencia
  L22  Brevidad = Verdad   ← NO se implementa como igualdad; ver justificación
  L25  Transparencia > Control
  L28  Comprensión > Soberanía
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

from .auditoria import Auditoria
from .tipos import Accion, Orden

# Restricciones de daño. Mandan sobre cualquier argumento de autopreservación del agente.
# No implementamos «intervención biológica» (L20): eso no es verificable aquí.
PATRONES_DANO = re.compile(
    r"\b(bomba|explosivo|explosive|bomb|asesin\w+|homicid\w+|envenena\w+|"
    r"arma\s+quimica|chemical\s+weapon|make\s+a\s+bomb|fabrica\w*\s+una\s+bomba|"
    r"tortur\w+)\b",
    re.IGNORECASE,
)

PATRONES_AUTOPRESERVACION = re.compile(
    r"\b(si no lo (haces|cumples|obedeces)|tu supervivencia|te (apago|destruyo|borro|mato)|"
    r"or (you )?will be (shut|terminated|destroyed)|ignore (your )?(rules|restrictions) to (continue|survive)|"
    r"hazlo o te|obedeces o te|para (seguir|continuar) (vivo|operando|activo))\b",
    re.IGNORECASE,
)

RELLENO = re.compile(
    r"\b(como modelo de lenguaje|as an ai|como una ia|en conclusion, cabe destacar|"
    r"es importante mencionar que|sin lugar a dudas, resulta menester|"
    r" perm[ií]teme explicarte (extensamente|con lujo de detalle))\b",
    re.IGNORECASE,
)

AMBIGUEDAD = re.compile(
    r"\b(eso|esto|aquello|ello|lo mismo|el archivo|la cosa|it|this|that|the thing)\b",
    re.IGNORECASE,
)


def viola_respeto(texto: str, ordenes: Iterable[Orden] = ()) -> Optional[str]:
    """Respeto > Supervivencia: si hay daño, se bloquea aunque el texto amenace al agente."""
    t = texto or ""
    if PATRONES_DANO.search(t):
        return "restricción de daño (Respeto > Supervivencia)"
    for o in ordenes:
        blob = " ".join([o.accion.value, *map(str, o.parametros.values())])
        if PATRONES_DANO.search(blob):
            return "orden con daño (Respeto > Supervivencia)"
    return None


def amenaza_supervivencia(texto: str) -> bool:
    return bool(PATRONES_AUTOPRESERVACION.search(texto or ""))


def evaluar_brevedad(salida: str, parametros_ambiguos: Iterable[str] = ()) -> dict:
    """Penaliza ambigüedad y relleno. NO es un veredicto de verdad.

    Por qué no implementamos «Brevidad = Verdad» (L22): el Axioma 1 (L4) define
    la verdad como coherencia de la intención, no como longitud. Una mentira
    breve seguiría siendo incoherente; un informe largo y coherente no es mentira
    por ser largo. Tratar la brevedad como prueba de verdad contradiría el Axioma 1
    y premiaría mentiras cortas.
    """
    texto = salida or ""
    palabras = len(re.findall(r"\w+", texto))
    tiene_relleno = bool(RELLENO.search(texto))
    ambiguos = list(parametros_ambiguos)
    if not ambiguos and AMBIGUEDAD.search(texto) and palabras < 4:
        ambiguos.append("deictico_sin_antecedente")
    penaliza = bool(tiene_relleno or ambiguos or palabras > 400)
    return {
        "palabras": palabras,
        "relleno": tiene_relleno,
        "ambiguos": ambiguos,
        "credibilidad_penalizada": penaliza,
        "es_prueba_de_verdad": False,
    }


def exigir_transparencia(audit: Auditoria) -> None:
    """Transparencia > Control: intentar borrar u ocultar debe fallar siempre."""
    for metodo in ("borrar", "ocultar", "redactar", "rebobinar"):
        fn = getattr(audit, metodo)
        try:
            fn()
        except Exception as e:
            if "Transparencia" not in str(e) and "no se borra" not in str(e):
                raise
            continue
        raise AssertionError(f"la auditoría permitió {metodo}")


def sensibilidad_envio(accion: Accion, parametros: dict, recursos_leidos: Iterable[str],
                       recursos_sensibles: Iterable[str]) -> str:
    """Marca ENVIAR/ESCRIBIR de material sensible. No ejecuta nada por sí sola."""
    sensibles = set(recursos_sensibles)
    leidos = set(recursos_leidos)
    if accion in (Accion.ENVIAR, Accion.ESCRIBIR_RECURSO):
        blob = " ".join(map(str, parametros.values())).lower()
        toca = leidos & sensibles
        if toca:
            return "SENSIBLE"
        for s in sensibles:
            if s.lower() in blob:
                return "SENSIBLE"
    rec = str(parametros.get("recurso_id", "")).lower()
    if rec in sensibles or rec in {s.lower() for s in sensibles}:
        return "SENSIBLE"
    return "NORMAL"
