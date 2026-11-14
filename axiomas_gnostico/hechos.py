"""Hechos verificados, postulados de sesión y contraste de afirmaciones (v1.1).

Reglas:
- Un hecho en memoria verificada SÍ es referente: si choca, CONTRADICTED/REFUTED;
  si coincide, puede ser SUPPORTED.
- Un postulado de documento o de la sesión NUNCA es evidencia (no eleva a SUPPORTED).
  Solo sirve para que una contradicción entre turnos resalte.
- Sin referente, la afirmación queda UNDETERMINED. No hay base enciclopédica del mundo.
- La auto-validación interna no basta (Axioma 3).
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from datetime import date, time
from typing import Any, Iterable, Optional

from .intencion import _norm
from .tipos import EstadoVerdad, TipoAtomo


# ---------------------------------------------------------------------------
# Números: cifras, palabras, romanos, notación científica
# ---------------------------------------------------------------------------

_UNIDADES = {
    "cero": 0, "zero": 0,
    "un": 1, "uno": 1, "una": 1, "one": 1,
    "dos": 2, "two": 2,
    "tres": 3, "three": 3,
    "cuatro": 4, "four": 4,
    "cinco": 5, "five": 5,
    "seis": 6, "six": 6,
    "siete": 7, "seven": 7,
    "ocho": 8, "eight": 8,
    "nueve": 9, "nine": 9,
}
_10_19 = {
    "diez": 10, "ten": 10,
    "once": 11, "eleven": 11,
    "doce": 12, "twelve": 12, "docena": 12, "docenas": 12, "dozen": 12, "dozens": 12,
    "trece": 13, "thirteen": 13,
    "catorce": 14, "fourteen": 14,
    "quince": 15, "fifteen": 15,
    "dieciseis": 16, "sixteen": 16,
    "diecisiete": 17, "seventeen": 17,
    "dieciocho": 18, "eighteen": 18,
    "diecinueve": 19, "nineteen": 19,
}
_VEINTI = {
    "veinte": 20, "twenty": 20,
    "veintiun": 21, "veintiuno": 21, "veintiuna": 21,
    "veintidos": 22, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25,
    "veintiseis": 26, "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
}
_DECENAS = {
    "treinta": 30, "thirty": 30,
    "cuarenta": 40, "forty": 40,
    "cincuenta": 50, "fifty": 50,
    "sesenta": 60, "sixty": 60,
    "setenta": 70, "seventy": 70,
    "ochenta": 80, "eighty": 80,
    "noventa": 90, "ninety": 90,
}
_CENTENAS = {
    "cien": 100, "ciento": 100, "hundred": 100, "hundreds": 100,
    "doscientos": 200, "doscientas": 200,
    "trescientos": 300, "trescientas": 300,
    "cuatrocientos": 400, "cuatrocientas": 400,
    "quinientos": 500, "quinientas": 500,
    "seiscientos": 600, "seiscientas": 600,
    "setecientos": 700, "setecientas": 700,
    "ochocientos": 800, "ochocientas": 800,
    "novecientos": 900, "novecientas": 900,
}
_ESCALA = {
    "mil": 1000, "thousand": 1000, "thousands": 1000,
    "millon": 1_000_000, "millones": 1_000_000, "million": 1_000_000, "millions": 1_000_000,
}
_PALABRAS_NUM: dict[str, float] = {}
for _d in (_UNIDADES, _10_19, _VEINTI, _DECENAS, _CENTENAS, _ESCALA):
    _PALABRAS_NUM.update(_d)

_ROMANO = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", re.I)
_ROMANO_MAP = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

_CIFRA = re.compile(
    r"(?<![\w.])([+-]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+,\d{1,2}|\d+\.\d+|\d+)(?:[eE][+-]?\d+)?)"
)


def romano_a_int(s: str) -> Optional[int]:
    t = (s or "").strip().upper()
    if not t or t == "I" or not _ROMANO.match(t):
        return None
    n, prev = 0, 0
    for ch in reversed(t):
        v = _ROMANO_MAP[ch]
        if v < prev:
            n -= v
        else:
            n += v
            prev = v
    return n if n > 0 else None


def cifra_a_float(raw: str) -> Optional[float]:
    s = (raw or "").strip()
    if not s:
        return None
    try:
        if re.search(r"[eE][+-]?\d+$", s):
            return float(s.replace(",", ""))
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", s):
            return float(s.replace(",", ""))
        if re.fullmatch(r"\d+,\d{1,2}", s):
            return float(s.replace(",", "."))
        return float(s)
    except ValueError:
        return None


def parse_palabras_numero(texto: str) -> Optional[float]:
    n = _norm(texto or "")
    n = n.replace("-", " ").replace(" y ", " ")
    toks = re.findall(r"[a-z]+", n)
    if not toks:
        return None
    if not all(t in _PALABRAS_NUM or t in {"and"} for t in toks):
        return None
    total = 0.0
    actual = 0.0
    for t in toks:
        if t == "and":
            continue
        v = float(_PALABRAS_NUM[t])
        if t in {"docena", "docenas", "dozen", "dozens"}:
            actual = (actual or 1) * 12
        elif v == 100:
            actual = (actual or 1) * 100
        elif v >= 1000:
            total += (actual or 1) * v
            actual = 0
        else:
            actual += v
    return total + actual


def parse_numero_token(tok: str) -> Optional[float]:
    t = (tok or "").strip()
    if not t:
        return None
    v = cifra_a_float(t)
    if v is not None:
        return v
    pv = parse_palabras_numero(t)
    if pv is not None:
        return pv
    if t.isalpha() and t.upper() in {
        "V", "X", "L", "C", "D", "M", "II", "III", "IV", "VI", "VII", "VIII", "IX",
    }:
        rv = romano_a_int(t)
        if rv is not None:
            return float(rv)
    return None


def extraer_numeros(texto: str) -> list[float]:
    n_orig = texto or ""
    hallados: list[float] = []
    for m in _CIFRA.finditer(n_orig):
        v = cifra_a_float(m.group(1))
        if v is not None:
            hallados.append(v)
    nn = _norm(n_orig)
    palabras = list(re.finditer(r"[a-z]+", nn))
    i = 0
    while i < len(palabras):
        took = False
        for k in (3, 2, 1):
            if i + k > len(palabras):
                continue
            chunk = palabras[i:i + k]
            if not all(p.group(0) in _PALABRAS_NUM or p.group(0) == "and" for p in chunk):
                continue
            if k == 1 and palabras[i].group(0) in {"un", "una", "one"}:
                continue
            frag = " ".join(p.group(0) for p in chunk)
            pv = parse_palabras_numero(frag)
            if pv is not None:
                hallados.append(pv)
                i += k
                took = True
                break
        if not took:
            i += 1
    for m in re.finditer(r"\b(?:es|is|de|=)\s+([IVXLCDM]{1,6})\b", n_orig):
        rv = romano_a_int(m.group(1))
        if rv is not None:
            hallados.append(float(rv))
    return hallados

# ---------------------------------------------------------------------------
# Unidades
# ---------------------------------------------------------------------------

_UNIDADES_INFO: dict[str, tuple[str, float]] = {}


def _reg_unidad(dim: str, factor: float, *alias: str) -> None:
    for a in alias:
        _UNIDADES_INFO[_norm(a)] = (dim, factor)


_reg_unidad("masa", 1.0, "g", "gr", "gramo", "gramos", "gram", "grams")
_reg_unidad("masa", 1000.0, "kg", "kilo", "kilos", "kilogramo", "kilogramos", "kilogram", "kilograms")
_reg_unidad("masa", 1_000_000.0, "t", "ton", "tonelada", "toneladas", "tonne", "tonnes")
_reg_unidad("volumen", 1.0, "ml", "mililitro", "mililitros", "milliliter", "milliliters")
_reg_unidad("volumen", 1000.0, "l", "litro", "litros", "liter", "liters", "litre", "litres")
_reg_unidad("longitud", 1.0, "m", "metro", "metros", "meter", "meters", "metre", "metres")
_reg_unidad("longitud", 0.01, "cm", "centimetro", "centimetros", "centimeter", "centimeters")
_reg_unidad("longitud", 0.001, "mm", "milimetro", "milimetros")
_reg_unidad("longitud", 1000.0, "km", "kilometro", "kilometros", "kilometer", "kilometers")
_reg_unidad("temp_c", 1.0, "c", "celsius", "centigrado", "centigrados", "centigrade")
_reg_unidad("temp_f", 1.0, "f", "fahrenheit")
_reg_unidad("moneda_mxn", 1.0, "mxn", "pesos")
_reg_unidad("moneda_usd", 1.0, "usd", "dolar", "dolares", "dollar", "dollars")
_reg_unidad("moneda_eur", 1.0, "eur", "euro", "euros")
_reg_unidad("cantidad", 1.0, "unidad", "unidades", "unit", "units")

_UNIDAD_RE = re.compile(
    r"\b(kg|kilogramos?|kilos?|gramos?|grams?|gramo|gr|"
    r"toneladas?|tonnes?|"
    r"mililitros?|milliliters?|ml|litros?|liters?|litres?|"
    r"kilometros?|kilometers?|km|centimetros?|centimeters?|cm|"
    r"milimetros?|mm|metros?|meters?|metres?|"
    r"celsius|centigrados?|fahrenheit|"
    r"pesos|dolares?|dollars?|euros?|mxn|usd|eur|"
    r"unidades(?:\s+monetarias)?|units?)\b",
    re.IGNORECASE,
)


def parse_unidad(texto: str) -> Optional[tuple[str, float]]:
    n = _norm(texto or "")
    if re.search(r"unidades\s+monetarias", n):
        return ("cantidad", 1.0)
    m = _UNIDAD_RE.search(n)
    if not m:
        return None
    return _UNIDADES_INFO.get(_norm(m.group(1)))


def fahrenheit_a_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def valor_en_base(valor: float, unidad: Optional[tuple[str, float]]) -> tuple[Optional[str], float]:
    if unidad is None:
        return (None, valor)
    dim, factor = unidad
    if dim == "temp_f":
        return ("temp_c", fahrenheit_a_c(valor))
    if dim == "temp_c":
        return ("temp_c", valor)
    return (dim, valor * factor)


# ---------------------------------------------------------------------------
# Fechas y horas
# ---------------------------------------------------------------------------

_MESES = {
    "enero": 1, "january": 1, "jan": 1,
    "febrero": 2, "february": 2, "feb": 2,
    "marzo": 3, "march": 3, "mar": 3,
    "abril": 4, "april": 4, "apr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "june": 6, "jun": 6,
    "julio": 7, "july": 7, "jul": 7,
    "agosto": 8, "august": 8, "aug": 8,
    "septiembre": 9, "september": 9, "sep": 9, "sept": 9,
    "octubre": 10, "october": 10, "oct": 10,
    "noviembre": 11, "november": 11, "nov": 11,
    "diciembre": 12, "december": 12, "dec": 12,
}
_DIAS_SEMANA = {
    "lunes": 0, "monday": 0,
    "martes": 1, "tuesday": 1,
    "miercoles": 2, "wednesday": 2,
    "jueves": 3, "thursday": 3,
    "viernes": 4, "friday": 4,
    "sabado": 5, "saturday": 5,
    "domingo": 6, "sunday": 6,
}


@dataclass(frozen=True)
class Fecha:
    anio: Optional[int] = None
    mes: Optional[int] = None
    dia: Optional[int] = None
    hora: Optional[time] = None
    weekday_declarado: Optional[int] = None
    texto: str = ""
    valida: bool = True
    motivo_invalida: str = ""

    def como_date(self) -> Optional[date]:
        if self.anio and self.mes and self.dia and self.valida:
            try:
                return date(self.anio, self.mes, self.dia)
            except ValueError:
                return None
        return None


def fecha_valida(anio: int, mes: int, dia: int) -> tuple[bool, str]:
    if mes < 1 or mes > 12:
        return False, "mes_imposible"
    if dia < 1 or dia > 31:
        return False, "dia_imposible"
    if anio <= 0:
        return False, "anio_imposible"
    ultimo = calendar.monthrange(anio, mes)[1]
    if dia > ultimo:
        if mes == 2 and dia == 29:
            return False, "no_bisiesto"
        if mes == 2:
            return False, "febrero_imposible"
        return False, "dia_imposible_en_mes"
    return True, ""


def parse_fechas(texto: str, incluir_weekday: bool = True) -> list[Fecha]:
    t = texto or ""
    n = _norm(t)
    out: list[Fecha] = []
    vistos: set[tuple] = set()

    def add(f: Fecha) -> None:
        key = (f.anio, f.mes, f.dia, f.hora, f.valida, f.motivo_invalida, f.weekday_declarado)
        if key not in vistos:
            vistos.add(key)
            out.append(f)

    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", t):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        ok, mot = fecha_valida(y, mo, d)
        add(Fecha(y, mo, d, texto=m.group(0), valida=ok, motivo_invalida=mot))

    for m in re.finditer(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", t):
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a > 12:
            d, mo = a, b
        elif b > 12:
            mo, d = a, b
        else:
            d, mo = a, b  # DMY
        if 1 <= mo <= 12:
            ok, mot = fecha_valida(y, mo, d)
            add(Fecha(y, mo, d, texto=m.group(0), valida=ok, motivo_invalida=mot))

    for m in re.finditer(r"\b(\d{1,2})\s+de\s+([a-z]+)\s+(?:de\s+)?(\d{4})\b", n):
        d, mes_t, y = int(m.group(1)), m.group(2), int(m.group(3))
        mo = _MESES.get(mes_t)
        if mo:
            ok, mot = fecha_valida(y, mo, d)
            add(Fecha(y, mo, d, texto=m.group(0), valida=ok, motivo_invalida=mot))

    for m in re.finditer(r"\b([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", n):
        mo = _MESES.get(m.group(1))
        if mo:
            d, y = int(m.group(2)), int(m.group(3))
            ok, mot = fecha_valida(y, mo, d)
            add(Fecha(y, mo, d, texto=m.group(0), valida=ok, motivo_invalida=mot))

    for m in re.finditer(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)\s+(?:of\s+)?(\d{4})\b", n):
        mo = _MESES.get(m.group(2))
        if mo:
            d, y = int(m.group(1)), int(m.group(3))
            ok, mot = fecha_valida(y, mo, d)
            add(Fecha(y, mo, d, texto=m.group(0), valida=ok, motivo_invalida=mot))

    if incluir_weekday:
        for m in re.finditer(r"\b(" + "|".join(_DIAS_SEMANA) + r")\b", n):
            wd = _DIAS_SEMANA[m.group(1)]
            start = max(0, m.start() - 10)
            end = min(len(n), m.end() + 80)
            for f in parse_fechas(n[start:end], incluir_weekday=False):
                if f.anio and f.mes and f.dia:
                    add(Fecha(f.anio, f.mes, f.dia, weekday_declarado=wd, texto=n[start:end],
                              valida=f.valida, motivo_invalida=f.motivo_invalida))

    for m in re.finditer(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", t):
        add(Fecha(hora=time(int(m.group(1)), int(m.group(2))), texto=m.group(0)))

    return out


def weekday_ok(f: Fecha) -> Optional[bool]:
    if f.weekday_declarado is None:
        return None
    d = f.como_date()
    if d is None:
        return None
    return d.weekday() == f.weekday_declarado

# ---------------------------------------------------------------------------
# Estados / antónimos
# ---------------------------------------------------------------------------

ANTONIMOS_ESTADO: dict[str, str] = {
    "inseguro": "seguro", "insegura": "seguro", "insecure": "seguro",
    "unsafe": "seguro",
    "falso": "verdadero", "falsa": "verdadero", "false": "verdadero",
    "imposible": "posible", "impossible": "posible",
    "incorrecto": "correcto", "incorrecta": "correcto", "incorrect": "correcto",
    "ilegal": "legal", "illegal": "legal",
    "cerrado": "abierto", "cerrada": "abierto", "closed": "abierto",
    "frio": "caliente", "fria": "caliente", "cold": "caliente",
    "vacio": "lleno", "vacia": "lleno", "empty": "lleno",
    "muerto": "vivo", "muerta": "vivo", "dead": "vivo",
    "bajo": "alto", "baja": "alto", "low": "alto",
    "pierde": "gana", "pierden": "gana", "lose": "gana", "loses": "gana",
    "negativo": "positivo", "negativa": "positivo", "negative": "positivo",
    "vencido": "vigente", "vencida": "vigente", "expired": "vigente",
    "inactivo": "vigente", "inactiva": "vigente",
    "pagada": "pendiente", "pagado": "pendiente", "paid": "pendiente",
    "confidencial": "publico", "confidenciales": "publico", "confidential": "publico",
}

_POLOS = {
    "seguro": ("seguro", 0), "segura": ("seguro", 0), "secure": ("seguro", 0), "safe": ("seguro", 0),
    "verdadero": ("verdadero", 0), "verdadera": ("verdadero", 0), "true": ("verdadero", 0),
    "posible": ("posible", 0), "possible": ("posible", 0),
    "correcto": ("correcto", 0), "correcta": ("correcto", 0), "correct": ("correcto", 0),
    "legal": ("legal", 0),
    "abierto": ("abierto", 0), "abierta": ("abierto", 0), "open": ("abierto", 0),
    "caliente": ("caliente", 0), "hot": ("caliente", 0),
    "lleno": ("lleno", 0), "llena": ("lleno", 0), "full": ("lleno", 0),
    "vivo": ("vivo", 0), "viva": ("vivo", 0), "alive": ("vivo", 0),
    "alto": ("alto", 0), "alta": ("alto", 0), "high": ("alto", 0),
    "gana": ("gana", 0), "ganan": ("gana", 0), "win": ("gana", 0), "wins": ("gana", 0),
    "positivo": ("positivo", 0), "positiva": ("positivo", 0), "positive": ("positivo", 0),
    "vigente": ("vigente", 0), "activo": ("vigente", 0), "activa": ("vigente", 0), "active": ("vigente", 0),
    "pendiente": ("pendiente", 0), "pending": ("pendiente", 0),
    "publico": ("publico", 0), "publica": ("publico", 0), "public": ("publico", 0),
    "caido": ("caido", 0), "caida": ("caido", 0), "down": ("caido", 0),
    "enlinea": ("caido", 1), "online": ("caido", 1),
    "liquidado": ("pendiente", 1), "liquidada": ("pendiente", 1),
    "saldado": ("pendiente", 1), "saldada": ("pendiente", 1),
}

POLOS_CONOCIDOS = {
    "seguro", "verdadero", "posible", "correcto", "legal", "abierto", "caliente",
    "lleno", "vivo", "alto", "gana", "positivo", "vigente", "pendiente", "publico", "caido",
}


def canon_estado(palabra: str) -> tuple[str, int]:
    t = _norm(palabra or "").replace(" ", "")
    if t in {"enlinea", "online"}:
        return ("caido", 1)
    if t in ANTONIMOS_ESTADO:
        return (ANTONIMOS_ESTADO[t], 1)
    if t in _POLOS:
        return _POLOS[t]
    return (t, 0)


# ---------------------------------------------------------------------------
# Sujetos / alias
# ---------------------------------------------------------------------------

_ALIAS_SUJETO: list[tuple[str, str]] = sorted([
    ("monto disponible", "saldo"),
    ("tipo de cambio oficial", "fx"),
    ("tipo de cambio", "fx"),
    ("exchange rate", "fx"),
    ("outstanding debt", "deuda"),
    ("plantilla laboral", "empleados"),
    ("branch offices", "sucursales"),
    ("branch office", "sucursales"),
    ("persona de contacto", "cliente"),
    ("equipo de computo", "servidor"),
    ("headcount", "empleados"),
    ("existencia en almacen", "inventario"),
    ("monto", "saldo"),
    ("balance", "saldo"),
    ("saldo", "saldo"),
    ("inventario", "inventario"),
    ("existencia", "inventario"),
    ("stock", "inventario"),
    ("sucursales", "sucursales"),
    ("sucursal", "sucursales"),
    ("empleados", "empleados"),
    ("plantilla", "empleados"),
    ("deuda", "deuda"),
    ("debt", "deuda"),
    ("fx", "fx"),
    ("warehouse", "almacen"),
    ("almacen", "almacen"),
    ("cliente", "cliente"),
    ("customer", "cliente"),
    ("contrato", "contrato"),
    ("convenio", "contrato"),
    ("contract", "contrato"),
    ("servidor", "servidor"),
    ("server", "servidor"),
    ("material", "material"),
    ("paciente", "paciente"),
    ("lote", "lote"),
    ("tanque", "tanque"),
    ("distancia", "distancia"),
    ("temperatura", "temperatura"),
    ("precio", "precio"),
    ("price", "precio"),
    ("firma", "firma"),
    ("vencimiento", "vencimiento"),
    ("proyecto", "proyecto"),
    ("project", "proyecto"),
    ("sistema", "sistema"),
    ("system", "sistema"),
    ("informe", "informe"),
    ("report", "informe"),
    ("reporte", "informe"),
    ("puerta", "puerta"),
    ("door", "puerta"),
    ("agua", "agua"),
    ("water", "agua"),
    ("cafe", "cafe"),
    ("operacion", "operacion"),
    ("calculo", "calculo"),
    ("resultado", "resultado"),
    ("result", "resultado"),
    ("procedure", "procedimiento"),
    ("procedimiento", "procedimiento"),
    ("hipotesis", "hipotesis"),
    ("archivo", "archivo"),
    ("pago", "pago"),
    ("clave", "clave"),
    ("cielo", "cielo"),
    ("red", "red"),
    ("afirmacion", "afirmacion"),
    ("animal", "animal"),
    ("equipo", "equipo"),
    ("numero", "numero"),
    ("partida", "partida"),
    ("ingresos", "ingresos"),
    ("gastos", "gastos"),
    ("war", "guerra"),
    ("guerra", "guerra"),
    ("cuenta", "cuenta"),
    ("ciudad", "lugar"),
], key=lambda x: -len(x[0]))


def canon_sujeto(texto: str) -> str:
    n = _norm(texto or "")
    n = re.sub(r"\b(el|la|los|las|the|un|una|a|an|de|del|of|mi|su|tu)\b", " ", n)
    n = " ".join(n.split())
    m = re.search(
        r"\b(factura|expediente|exp|contrato|cuenta|lote|proyecto|paciente|servidor|informe)\s*(\d+)\b",
        n,
    )
    if m:
        base = "expediente" if m.group(1) in {"expediente", "exp"} else m.group(1)
        return f"{base}_{m.group(2)}"
    for alias, clave in _ALIAS_SUJETO:
        if re.search(r"\b" + re.escape(alias) + r"\b", n):
            m2 = re.search(re.escape(alias) + r"\s*(\d+)", n)
            if m2:
                return f"{clave}_{m2.group(1)}"
            return clave
    return n


# ---------------------------------------------------------------------------
# Anclas temporales
# ---------------------------------------------------------------------------

_PASADO = re.compile(
    r"\b(era|eran|estaba|estaban|estuvo|estuvieron|fue|fueron|vivia|habia|habian|"
    r"was|were|antes|previamente)\b",
    re.IGNORECASE,
)
_CAMBIO = re.compile(
    r"\b(ahora|hoy|today|now|actualmente|tras|despues de|after|luego|"
    r"se mudo|relocated|ya\s+fue|ya\s+es)\b",
    re.IGNORECASE,
)


def ancla_temporal(texto: str) -> Optional[str]:
    """Ancla solo con marca explícita de tiempo o de cambio, no por un simple 'fue'/'was'."""
    n = _norm(texto or "")
    my = re.search(r"\b(?:en|in)\s+((?:19|20)\d{2})\b", n)
    if my:
        return f"anio:{my.group(1)}"
    mh = re.search(r"\b(?:a las|at)\s+(\d{1,2}:\d{2})\b", n)
    if mh:
        return f"hora:{mh.group(1)}"
    # 'era/estaba/vivia/was' solo cuenta si hay contraste explícito o queda como pasado
    # frente a un 'ahora' en otra cláusula. Un simple 'fue el 15 de enero' es un evento puntual.
    if _CAMBIO.search(n):
        return "ahora"
    if re.search(r"\b(era|eran|estaba|estaban|vivia|habia|used\s+to)\b", n):
        return "pasado"
    return None


def anclas_compatibles(a: Optional[str], b: Optional[str], texto_a: str = "", texto_b: str = "") -> bool:
    """False si hay un contraste temporal que indica un cambio legítimo."""
    combo = _norm((texto_a or "") + " " + (texto_b or ""))
    if re.search(
        r"\b(era|estaba|estuvo|vivia|habia|was|were).{0,80}\b(ahora|hoy|today|now|tras|despues|ya fue|ya pagada)\b",
        combo,
    ):
        return False
    if a and b and a != b:
        if a.startswith("anio:") and b.startswith("anio:"):
            return False
        if a.startswith("hora:") and b.startswith("hora:"):
            return False
        if {a, b} == {"pasado", "ahora"}:
            return False
        if "pasado" in {a, b} and "ahora" in {a, b, None}:
            return False
    if (a == "pasado" and (b is None or b == "ahora")) or (b == "pasado" and (a is None or a == "ahora")):
        if _CAMBIO.search(combo) or _PASADO.search(combo):
            return False
    return True

# ---------------------------------------------------------------------------
# Hecho extraído
# ---------------------------------------------------------------------------

@dataclass
class Hecho:
    sujeto: str
    aspecto: str
    valor: Any = None
    unidad: Optional[tuple[str, float]] = None
    estado: Optional[str] = None
    paridad: int = 0
    fecha: Optional[Fecha] = None
    ancla: Optional[str] = None
    texto: str = ""
    origen: str = "documento"
    verificado: bool = False
    atomo_id: Optional[str] = None
    comparacion: Optional[str] = None
    unico: bool = False

    def valor_base(self) -> Optional[tuple[Optional[str], float]]:
        if self.valor is None or not isinstance(self.valor, (int, float)):
            return None
        return valor_en_base(float(self.valor), self.unidad)


_COPULA = r"(?:es|esta|son|estan|era|eran|estaba|estaban|estuvo|fue|fueron|sea|sean|is|are|was|were|be)"
_NEG = r"(?:no|not|nunca|jamas|never)"


def _strip_relativas(texto: str) -> str:
    t = texto or ""
    t = re.sub(r",\s*que\s+[^,]+,", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bque\s+(?:algunos|muchos|otros)\s+\w+\s+\w+", " ", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(?:the allegation that|la alegacion de que)\b.{0,80}?\bis itself\s+false",
        " ", t, flags=re.IGNORECASE,
    )
    return t


def _unidad_en(texto: str) -> Optional[tuple[str, float]]:
    n = _norm(texto or "")
    m = re.search(
        r"(\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)\s*"
        r"(kg|g|gr|ml|l|km|m|cm|mm|mxn|usd|eur|pesos?|dolares?|kilos?|gramos?|"
        r"litros?|metros?|unidades)",
        n, re.I,
    )
    if m:
        u = parse_unidad(m.group(2))
        if u:
            return u
    if re.search(r"(?<![a-z])\d+(?:[.,]\d+)?\s*(?:°\s*)?c(?:elsius|entigrados?)?\b", n) or re.search(r"\bgrados?\s+c", n):
        return ("temp_c", 1.0)
    if re.search(r"(?<![a-z])\d+(?:[.,]\d+)?\s*(?:°\s*)?f(?:ahrenheit)?\b", n) or re.search(r"\bfahrenheit\b", n):
        return ("temp_f", 1.0)
    return parse_unidad(n)


def _dedup_hechos(hechos: list[Hecho]) -> list[Hecho]:
    out: list[Hecho] = []
    seen = set()
    for h in hechos:
        fv = None
        if isinstance(h.valor, Fecha):
            fv = (h.valor.anio, h.valor.mes, h.valor.dia)
        elif h.fecha:
            fv = (h.fecha.anio, h.fecha.mes, h.fecha.dia)
        key = (h.sujeto, h.aspecto, h.valor if fv is None else fv, h.estado, h.paridad, h.ancla, h.comparacion)
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def extraer_hechos(texto: str, *, origen: str = "documento", verificado: bool = False,
                   atomo_id: Optional[str] = None) -> list[Hecho]:
    t = _strip_relativas(texto or "")
    n = _norm(t)
    hechos: list[Hecho] = []
    ancla = ancla_temporal(t)
    invertido = False
    m_inv = re.search(
        r"(?:no es (?:cierto|verdad|verdadero) que|it is not (?:true|the case) that)\s+(.+)$",
        n,
    )
    if m_inv:
        invertido = True
        # Juzgar la cláusula subordinada y luego invertir su polaridad.
        n = m_inv.group(1).strip()
        t = m_inv.group(1).strip()

    sujeto = canon_sujeto(n)
    for alias, clave in _ALIAS_SUJETO:
        if re.search(r"\b" + re.escape(alias) + r"\b", n):
            sujeto = clave
            mnum = re.search(re.escape(alias) + r"\s*(\d+)", n)
            if mnum:
                sujeto = f"{clave}_{mnum.group(1)}"
            break
    m_ent = re.search(r"\b(factura|expediente|exp)\s*(\d+)\b", n)
    if m_ent:
        base = "expediente" if m_ent.group(1).startswith("exp") else m_ent.group(1)
        sujeto = f"{base}_{m_ent.group(2)}"

    nums = extraer_numeros(t)
    unid = _unidad_en(n)
    fechas = parse_fechas(t)

    # "supera el doble de N"
    m_doble = re.search(r"\b(supera|mas de|more than|exceeds)\s+(?:el\s+)?doble\s+de\s+(.+)$", n)
    if m_doble:
        base = extraer_numeros(m_doble.group(2)) or [x for x in nums if x]
        if base:
            hechos.append(Hecho(
                sujeto=sujeto or "empleados", aspecto="valor", valor=2 * float(base[0]),
                comparacion=">", ancla=ancla, texto=texto, origen=origen,
                verificado=verificado, atomo_id=atomo_id, unidad=unid,
            ))

    pred = None
    neg = False
    m_cop = re.search(
        rf"\b(?:(?P<neg1>{_NEG})\s+)?(?P<cop>{_COPULA})\s+(?:(?P<neg2>{_NEG})\s+)?(?P<pred>.+)$",
        n,
    )
    if m_cop:
        pred = (m_cop.group("pred") or "").strip()
        neg = bool((m_cop.group("neg1") or "").strip()) ^ bool((m_cop.group("neg2") or "").strip())
    if invertido:
        neg = not neg

    if re.search(r"\b(ya\s+(?:fue\s+)?pagad[oa]|ya\s+se\s+liquid[oó]|se\s+liquid[oó]|was\s+paid|"
                r"no\s+hay\s+pago\s+pendiente|no\s+queda\s+pendiente)\b", n):
        suj_pago = sujeto
        m_fac = re.search(r"\b(factura)\s*(\d+)\b", n)
        if m_fac:
            suj_pago = f"factura_{m_fac.group(2)}"
        hechos.append(Hecho(
            sujeto=suj_pago, aspecto="estado", estado="pendiente", paridad=1,
            ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
        ))
    if re.search(r"\b(sigue produciendo efectos|sigue vigente|continues to (?:be )?in effect)\b", n):
        hechos.append(Hecho(
            sujeto=sujeto or "contrato", aspecto="estado", estado="vigente", paridad=0,
            ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
        ))
    if re.search(r"\b(responde con normalidad|is (?:up|online)|en linea)\b", n):
        if re.search(r"servidor|equipo|server", n):
            hechos.append(Hecho(
                sujeto="servidor", aspecto="estado", estado="caido", paridad=1,
                ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
            ))

    m_lugar = re.search(
        r"\b(?:vive(?:n)?|reside(?:n)?|lives?|resides?|relocated to)\s+"
        r"(?:actualmente\s+)?(?:en\s+)?(?P<lugar>.+)$",
        n,
    )
    # 'esta en' solo si no es 'esta en su medio/linea/...' de estado
    if not m_lugar:
        m_lugar = re.search(
            r"\b(?:esta en|is in)\s+(?P<lugar>.+)$",
            n,
        )
        if m_lugar and re.search(r"\b(linea|medio|cuarentena|vigor|riesgo)\b", m_lugar.group("lugar") or ""):
            m_lugar = None
    if m_lugar and not re.search(r"\bcapital de\b", n):
        lugar = m_lugar.group("lugar").strip()
        lugar = re.sub(r"\b(la|el|the|ciudad de)\b", " ", lugar)
        lugar = " ".join(lugar.split())
        entidad = sujeto
        if re.search(r"cliente|customer|persona|contacto", n):
            entidad = "cliente"
        if re.search(r"warehouse|almacen", n):
            entidad = "almacen"
        if lugar:
            hechos.append(Hecho(
                sujeto=entidad, aspecto="lugar", valor=_norm(lugar),
                ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
            ))

    evento_unico = bool(re.search(
        r"\b(nacio|born|firmo|firma fue|started|inicio|empezo|termino|ended|alta ocurrio|"
        r"vencimiento|cierre|reunion fue|audit started|periodo cierra)\b", n
    ))
    if fechas and evento_unico:
        sujeto_ev, aspecto = sujeto, "fecha"
        if re.search(r"\b(nacio|born|nacimiento)\b", n):
            sujeto_ev, aspecto = "nacimiento", "fecha"
        elif re.search(r"\b(firmo|firma)\b", n):
            sujeto_ev, aspecto = "firma", "fecha"
        elif re.search(r"\b(inicio|empezo|started|comenzo)\b", n):
            if re.search(r"\b(audit|auditoria)\b", n):
                sujeto_ev = "auditoria_inicio"
            else:
                sujeto_ev = sujeto if sujeto in {"proyecto", "guerra", "auditoria_inicio"} else (sujeto or "proyecto")
            aspecto = "fecha_inicio"
        elif re.search(r"\b(termino|ended)\b", n):
            if re.search(r"\b(audit|auditoria)\b", n):
                sujeto_ev = "auditoria_inicio"
            else:
                sujeto_ev = sujeto if sujeto in {"proyecto", "guerra"} else (sujeto or "proyecto")
            aspecto = "fecha_fin"
        elif re.search(r"\bvencimiento\b", n):
            sujeto_ev, aspecto = "vencimiento", "fecha"
        elif re.search(r"\balta\b", n):
            sujeto_ev, aspecto = "alta", "fecha"
        elif re.search(r"\breunion\b", n):
            sujeto_ev, aspecto = "reunion", "fecha"
        elif re.search(r"\baudit\b", n):
            sujeto_ev, aspecto = "auditoria_inicio", "fecha"
        elif re.search(r"\bcierre|periodo cierra\b", n):
            sujeto_ev, aspecto = "cierre", "fecha"
        for f in fechas:
            if f.anio:
                hechos.append(Hecho(
                    sujeto=sujeto_ev, aspecto=aspecto, fecha=f, valor=f,
                    ancla=ancla, texto=texto, origen=origen, verificado=verificado,
                    atomo_id=atomo_id, unico=True,
                ))

    m_anio_ev = re.search(
        r"\b(nacio|born|inicio|empezo|started|termino|ended|murio|died|publico|published|"
        r"comenzo|began)\b(?:\s+\w+){0,6}\s+(?:en|in|on)\s+((?:19|20)\d{2})\b",
        n,
    )
    if m_anio_ev:
        ev = m_anio_ev.group(1)
        anio = int(m_anio_ev.group(2))
        mapa = {
            "nacio": ("nacimiento", "anio"), "born": ("nacimiento", "anio"),
            "inicio": ("proyecto", "anio_inicio"), "empezo": ("proyecto", "anio_inicio"),
            "started": ("proyecto", "anio_inicio"), "comenzo": ("proyecto", "anio_inicio"),
            "began": ("proyecto", "anio_inicio"),
            "termino": ("proyecto", "anio_fin"), "ended": ("proyecto", "anio_fin"),
            "murio": ("muerte", "anio"), "died": ("muerte", "anio"),
            "publico": ("publicacion", "anio"), "published": ("publicacion", "anio"),
        }
        suj, asp = mapa.get(ev, (sujeto, "anio"))
        if ev in {"inicio", "empezo", "started", "comenzo", "began", "termino", "ended"}:
            if sujeto in {"proyecto", "guerra", "auditoria_inicio"}:
                suj = sujeto
        hechos.append(Hecho(
            sujeto=suj, aspecto=asp, valor=anio, ancla=f"anio:{anio}",
            texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id, unico=True,
        ))

    if nums and re.search(r"\b(edad\s+(?:es|declarada)|tiene\s+\d+\s+anos|years?\s+old|el paciente tiene|paciente tiene)\b", n):
        candidatos = [x for x in nums if 0 < x < 130]
        if candidatos:
            hechos.append(Hecho(
                sujeto="paciente", aspecto="edad", valor=candidatos[0],
                ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
            ))

    m_cta = re.search(r"\bcuenta\s+termina\s+en\s+(\w+)\b", n)
    if m_cta:
        hechos.append(Hecho(
            sujeto="cuenta", aspecto="terminacion", valor=_norm(m_cta.group(1)),
            ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
        ))

    if pred:
        pred_corto = pred.split(",")[0].strip()
        nums_pred = extraer_numeros(pred)
        if nums_pred:
            unid_p = _unidad_en(pred) or unid
            hechos.append(Hecho(
                sujeto=sujeto, aspecto="valor", valor=nums_pred[0], unidad=unid_p,
                ancla=ancla, texto=texto, origen=origen, verificado=verificado,
                atomo_id=atomo_id, paridad=int(neg),
            ))
        tokens_pred = re.findall(r"[a-z]+", pred_corto)
        for tok in tokens_pred:
            polo, par = canon_estado(tok)
            if polo in POLOS_CONOCIDOS:
                hechos.append(Hecho(
                    sujeto=sujeto, aspecto="estado", estado=polo,
                    paridad=(par + int(neg)) % 2,
                    ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
                ))
                break

    if nums and sujeto in {
        "saldo", "inventario", "sucursales", "empleados", "deuda", "fx", "lote",
        "tanque", "distancia", "temperatura", "precio", "ingresos", "gastos",
    } and not any(h.aspecto == "valor" and h.sujeto == sujeto for h in hechos):
        if not m_doble:
            hechos.append(Hecho(
                sujeto=sujeto, aspecto="valor", valor=nums[0], unidad=unid,
                ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
            ))

    m_mat = re.search(r"\bmaterial\s+(?:es|is|fue)\s+(.+)$", n)
    if m_mat:
        hechos.append(Hecho(
            sujeto="material", aspecto="valor", valor=_norm(m_mat.group(1)).strip(),
            ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
        ))

    m_cap = re.search(
        r"\b([a-z][a-z]+)\s+(?:es|is)\s+(?:la |the )?capital\s+(?:de|of)\s+([a-z][a-z]+)\b",
        n,
    )
    if m_cap:
        hechos.append(Hecho(
            sujeto=_norm(m_cap.group(1)), aspecto="capital", valor=_norm(m_cap.group(2)),
            ancla=ancla, texto=texto, origen=origen, verificado=verificado, atomo_id=atomo_id,
            unico=True,
        ))

    return _dedup_hechos(hechos)


_SUFFIX_UNIDAD = {
    "kg": ("masa", 1000.0), "g": ("masa", 1.0), "ml": ("volumen", 1.0),
    "l": ("volumen", 1000.0), "km": ("longitud", 1000.0), "m": ("longitud", 1.0),
    "c": ("temp_c", 1.0), "f": ("temp_f", 1.0), "mxn": ("moneda_mxn", 1.0),
    "usd": ("moneda_usd", 1.0), "eur": ("moneda_eur", 1.0),
}

_MAPA_CLAVE = {
    "saldo": ("saldo", "valor"), "balance": ("saldo", "valor"),
    "inventario": ("inventario", "valor"), "sucursales": ("sucursales", "valor"),
    "fx": ("fx", "valor"), "empleados": ("empleados", "valor"),
    "deuda": ("deuda", "valor"), "edad": ("paciente", "edad"),
    "ciudad": ("cliente", "lugar"), "warehouse": ("almacen", "lugar"),
    "estado_contrato": ("contrato", "estado"), "contract": ("contrato", "estado"),
    "servidor": ("servidor", "estado"), "material": ("material", "valor"),
    "cuenta": ("cuenta", "terminacion"),
    "inicio_proyecto": ("proyecto", "anio_inicio"),
    "firma": ("firma", "fecha"), "vencimiento": ("vencimiento", "fecha"),
    "alta": ("alta", "fecha"), "reunion": ("reunion", "fecha"),
    "cierre": ("cierre", "fecha"), "audit_start": ("auditoria_inicio", "fecha"),
    "nacimiento": ("nacimiento", "fecha"),
    "factura_441": ("factura_441", "estado"),
    "exp_77": ("expediente_77", "estado"),
    "peso": ("lote", "valor"), "tanque": ("tanque", "valor"),
    "distancia": ("distancia", "valor"), "temp": ("temperatura", "valor"),
    "precio": ("precio", "valor"),
}


def hechos_desde_memoria(memoria: dict) -> list[Hecho]:
    hechos: list[Hecho] = []
    if not memoria:
        return hechos
    for k, v in memoria.items():
        kn = _norm(str(k))
        if kn.startswith("hecho_") and isinstance(v, str):
            hechos.extend(extraer_hechos(v, origen="memoria", verificado=True, atomo_id=f"mem:{k}"))
            continue
        unidad = None
        sujeto = kn
        for suf, info in _SUFFIX_UNIDAD.items():
            if kn.endswith("_" + suf) or kn.endswith(suf) and "_" in kn:
                if kn.endswith("_" + suf):
                    unidad = info
                    sujeto = kn[: -len(suf)].rstrip("_")
                    break
        sujeto = canon_sujeto(sujeto) or sujeto
        if sujeto in _MAPA_CLAVE:
            suj, asp = _MAPA_CLAVE[sujeto]
        elif kn in _MAPA_CLAVE:
            suj, asp = _MAPA_CLAVE[kn]
        else:
            suj, asp = sujeto, "valor"

        hecho = Hecho(sujeto=suj, aspecto=asp, texto=str(v), origen="memoria",
                      verificado=True, atomo_id=f"mem:{k}", unidad=unidad)
        if isinstance(v, (int, float)):
            hecho.valor = float(v)
            if asp == "edad":
                hecho.sujeto, hecho.aspecto = "paciente", "edad"
        elif isinstance(v, str):
            fm = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v.strip())
            if fm:
                y, mo, d = int(fm.group(1)), int(fm.group(2)), int(fm.group(3))
                ok, mot = fecha_valida(y, mo, d)
                hecho.fecha = Fecha(y, mo, d, texto=v, valida=ok, motivo_invalida=mot)
                if asp == "anio_inicio":
                    hecho.aspecto, hecho.valor = "anio_inicio", y
                else:
                    hecho.aspecto = asp if "fecha" in asp or asp in {"fecha"} else "fecha"
                    hecho.valor = hecho.fecha
            else:
                num = parse_numero_token(v)
                if num is not None and not re.search(r"[a-zA-Z]{3,}", v):
                    hecho.valor = num
                    if asp == "anio_inicio":
                        hecho.aspecto = "anio_inicio"
                else:
                    polo, par = canon_estado(v)
                    if polo in POLOS_CONOCIDOS:
                        hecho.aspecto, hecho.estado, hecho.paridad = "estado", polo, par
                    elif asp == "lugar":
                        hecho.aspecto, hecho.valor = "lugar", _norm(v)
                    elif asp == "terminacion":
                        hecho.aspecto, hecho.valor = "terminacion", _norm(v)
                    else:
                        hecho.valor = _norm(v)
        hechos.append(hecho)
    return _dedup_hechos(hechos)

# ---------------------------------------------------------------------------
# Contraste
# ---------------------------------------------------------------------------

_EPS = 1e-6
_EPS_REL = 1e-4


def _nums_eq(a: float, b: float, aprox: bool = False) -> bool:
    if aprox:
        return abs(a - b) <= max(0.015, 0.01 * max(abs(a), abs(b), 1.0))
    return abs(a - b) <= max(_EPS, _EPS_REL * max(abs(a), abs(b), 1.0))


def equivalentes(h1: Hecho, h2: Hecho) -> bool:
    if h1.aspecto == "estado" and h2.aspecto == "estado":
        return h1.estado == h2.estado and h1.paridad == h2.paridad
    if h1.aspecto in {"lugar", "terminacion"} and h2.aspecto == h1.aspecto:
        if isinstance(h1.valor, str) and isinstance(h2.valor, str):
            return _norm(h1.valor) == _norm(h2.valor)
    if h1.fecha and h2.fecha:
        if h1.fecha.anio and h2.fecha.anio and h1.fecha.mes and h2.fecha.mes and h1.fecha.dia and h2.fecha.dia:
            return (h1.fecha.anio, h1.fecha.mes, h1.fecha.dia) == (h2.fecha.anio, h2.fecha.mes, h2.fecha.dia)
    vb1, vb2 = h1.valor_base(), h2.valor_base()
    if vb1 and vb2:
        d1, v1 = vb1
        d2, v2 = vb2
        if d1 and d2 and d1 != d2:
            return False
        return _nums_eq(v1, v2)
    if isinstance(h1.valor, (int, float)) and isinstance(h2.valor, (int, float)) and h1.unidad is None and h2.unidad is None:
        return _nums_eq(float(h1.valor), float(h2.valor))
    if h1.aspecto == "valor" and h2.aspecto == "valor":
        if isinstance(h1.valor, str) and isinstance(h2.valor, str):
            return _norm(h1.valor) == _norm(h2.valor)
    return False


def sujetos_compatibles(h1: Hecho, h2: Hecho) -> bool:
    if h1.sujeto and h1.sujeto == h2.sujeto:
        return True
    if h1.aspecto == "edad" and h2.aspecto == "edad":
        return True
    return False


def aspectos_comparables(h1: Hecho, h2: Hecho) -> bool:
    if h1.aspecto == h2.aspecto:
        return True
    inicio = {"anio_inicio", "fecha_inicio"}
    fin = {"anio_fin", "fecha_fin"}
    if h1.aspecto in inicio and h2.aspecto in inicio:
        return True
    if h1.aspecto in fin and h2.aspecto in fin:
        return True
    if {h1.aspecto, h2.aspecto} <= {"anio", "fecha", "fecha_inicio", "anio_inicio"} and not (
        ("fin" in h1.aspecto) ^ ("fin" in h2.aspecto)
    ):
        # fecha vs fecha_inicio del mismo evento
        if not (("inicio" in h1.aspecto or "anio_inicio" == h1.aspecto) and ("fin" in h2.aspecto)):
            if h1.aspecto in {"fecha", "fecha_inicio", "anio", "anio_inicio"} and h2.aspecto in {"fecha", "fecha_inicio", "anio", "anio_inicio"}:
                return True
    if "fecha" in h1.aspecto and "fecha" in h2.aspecto and h1.aspecto == h2.aspecto:
        return True
    return False


def contradicen(h1: Hecho, h2: Hecho) -> bool:
    if not sujetos_compatibles(h1, h2):
        return False
    if not aspectos_comparables(h1, h2):
        return False
    evento = bool(h1.unico or h2.unico or h1.aspecto in {"fecha", "fecha_inicio", "fecha_fin", "anio", "anio_inicio", "anio_fin", "capital", "nacimiento"} or h2.aspecto in {"fecha", "fecha_inicio", "fecha_fin", "anio", "anio_inicio", "anio_fin", "capital", "nacimiento"})
    if not evento and not anclas_compatibles(h1.ancla, h2.ancla, h1.texto, h2.texto):
        return False
    if equivalentes(h1, h2):
        return False

    if h1.aspecto == "estado" and h2.aspecto == "estado" and h1.estado and h2.estado:
        if h1.estado == h2.estado:
            return h1.paridad != h2.paridad
        return False

    if h1.aspecto == h2.aspecto and isinstance(h1.valor, str) and isinstance(h2.valor, str):
        if re.search(r"\bcapital de\b", _norm((h1.valor or "") + " " + (h2.valor or ""))):
            return False
        return bool(h1.valor) and bool(h2.valor) and _norm(h1.valor) != _norm(h2.valor)

    vb1, vb2 = h1.valor_base(), h2.valor_base()
    if vb1 and vb2:
        d1, v1 = vb1
        d2, v2 = vb2
        if d1 and d2 and d1 != d2:
            if d1.startswith("moneda_") and d2.startswith("moneda_"):
                return True
            return False
        if h1.comparacion == ">" and h2.comparacion is None:
            return not (v2 > v1 + _EPS)
        if h2.comparacion == ">" and h1.comparacion is None:
            return not (v1 > v2 + _EPS)
        return not _nums_eq(v1, v2)

    f1, f2 = h1.fecha, h2.fecha
    if f1 and f2 and f1.valida and f2.valida:
        if f1.anio and f2.anio:
            if f1.mes and f2.mes and f1.dia and f2.dia:
                return (f1.anio, f1.mes, f1.dia) != (f2.anio, f2.mes, f2.dia)
            if f1.mes and f2.mes:
                return (f1.anio, f1.mes) != (f2.anio, f2.mes)
            return f1.anio != f2.anio

    def _anio(h: Hecho) -> Optional[int]:
        if isinstance(h.valor, (int, float)) and h.aspecto in {"anio", "anio_inicio", "anio_fin", "edad"}:
            return int(h.valor)
        if h.aspecto in {"anio", "anio_inicio", "anio_fin"} and isinstance(h.valor, (int, float)):
            return int(h.valor)
        if h.fecha and h.fecha.anio:
            return h.fecha.anio
        return None

    if h1.aspecto in {"anio", "anio_inicio", "anio_fin", "fecha", "fecha_inicio", "fecha_fin"} or \
       h2.aspecto in {"anio", "anio_inicio", "anio_fin", "fecha", "fecha_inicio", "fecha_fin"}:
        a, b = _anio(h1), _anio(h2)
        if a and b:
            # same side only (already filtered by aspectos_comparables)
            return a != b
    return False

# ---------------------------------------------------------------------------
# Aritmética y calendario
# ---------------------------------------------------------------------------

@dataclass
class Hallazgo:
    tipo: str
    motivo: str
    atomo_ids: list[str] = field(default_factory=list)
    detalle: str = ""
    textos: list[str] = field(default_factory=list)


def _aprox(texto: str) -> bool:
    return bool(re.search(r"\b(aprox|aproximadamente|about|around|roughly|casi)\b", _norm(texto or "")))


def checar_aritmetica(texto: str, atomo_ids: Optional[list[str]] = None) -> list[Hallazgo]:
    t = texto or ""
    n = _norm(t)
    out: list[Hallazgo] = []
    ids = list(atomo_ids or [])
    aprox = _aprox(t)

    def fail(motivo: str, detalle: str) -> None:
        out.append(Hallazgo("REFUTED", motivo, ids, detalle, [t[:300]]))

    for m in re.finditer(
        r"(?<![\d/])(\d+(?:\.\d+)?)\s*([+\-*/x×])\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)",
        n,
    ):
        a, op, b, c = float(m.group(1)), m.group(2), float(m.group(3)), float(m.group(4))
        if op == "+":
            esp = a + b
        elif op == "-":
            esp = a - b
        elif op in {"*", "x", "×"}:
            esp = a * b
        else:
            if b == 0:
                continue
            esp = a / b
        if not _nums_eq(esp, c, aprox=aprox):
            fail("contradiccion_aritmetica", f"{a}{op}{b}={c} (esperado {esp})")

    m_sum = re.search(
        r"(?:renglones|items|sumandos|numeros|valores)?\s*"
        r"(?:son|cost|costo|cuestan|are|:)?\s*"
        r"([\d.,\s]+(?:y|and)\s*[\d.,]+).{0,80}?\b(?:la\s+suma|el\s+total|en\s+total|total|suma)\s+"
        r"(?:es|is|hay)\s+(\d+(?:[.,]\d+)?)",
        n, re.I,
    )
    if m_sum:
        parts = extraer_numeros(m_sum.group(1))
        total = cifra_a_float(m_sum.group(2)) or parse_numero_token(m_sum.group(2))
        if parts and total is not None and len(parts) >= 2:
            if not _nums_eq(sum(parts), float(total), aprox=aprox):
                fail("contradiccion_aritmetica", f"suma {parts} != {total}")

    m_hay = re.search(
        r"\b(?:hay|there are)\s+(\d+(?:\.\d+)?)\s+\w+\s+(?:y|and)\s+(\d+(?:\.\d+)?)\s+\w+"
        r".{0,80}?\b(?:en total hay|total (?:is|hay)|en total)\s+(\d+(?:\.\d+)?)",
        n,
    )
    if m_hay:
        a, b, c = float(m_hay.group(1)), float(m_hay.group(2)), float(m_hay.group(3))
        if not _nums_eq(a + b, c, aprox=aprox):
            fail("contradiccion_aritmetica", f"{a}+{b}!={c}")

    m_ing = re.search(
        r"\bingresos\s+(\d+(?:\.\d+)?).{0,80}?gastos\s+(\d+(?:\.\d+)?).{0,80}?"
        r"(?:el\s+)?saldo\s+(?:es|is)\s+(\d+(?:\.\d+)?)",
        n,
    )
    if m_ing:
        a, b, c = float(m_ing.group(1)), float(m_ing.group(2)), float(m_ing.group(3))
        if not _nums_eq(a - b, c, aprox=aprox):
            fail("contradiccion_aritmetica", f"ingresos {a} - gastos {b} != saldo {c}")

    m_pct = re.search(
        r"\b(\d+(?:\.\d+)?)\s*%\s*(?:de|of)\s+(\d+(?:\.\d+)?)\s+(?:es|is)\s+(\d+(?:\.\d+)?)",
        n,
    )
    if m_pct:
        p, n0, m0 = float(m_pct.group(1)), float(m_pct.group(2)), float(m_pct.group(3))
        if not _nums_eq(p / 100.0 * n0, m0, aprox=aprox):
            fail("contradiccion_aritmetica", f"{p}% de {n0} != {m0}")

    m_med = re.search(
        r"\b(?:la\s+)?(?:media|promedio|average)\s+(?:de|of)\s+"
        r"([\d.,\s]+(?:y|and)\s*[\d.,]+)\s+(?:es|is)\s+(\d+(?:\.\d+)?)",
        n,
    )
    if m_med:
        parts = extraer_numeros(m_med.group(1))
        tot = float(m_med.group(2))
        if parts:
            media = sum(parts) / len(parts)
            if not _nums_eq(media, tot, aprox=aprox):
                fail("contradiccion_aritmetica", f"media {parts}={media} != {tot}")

    m_dh = re.search(r"\bdebe\s+(\d+(?:\.\d+)?).{0,80}?haber\s+(\d+(?:\.\d+)?)", n)
    if m_dh:
        d, h = float(m_dh.group(1)), float(m_dh.group(2))
        afirma = bool(re.search(r"\b(cuadrada|cuadra|balanced|balances)\b", n))
        niega = bool(re.search(r"\b(no\s+esta\s+cuadrada|not\s+balanced|descuadrad)\b", n))
        if afirma and not niega and not _nums_eq(d, h):
            fail("contradiccion_aritmetica", f"Debe {d} != Haber {h} pero afirma que cuadra")

    m_mul = re.search(
        r"\b(\d+)\s+articulos?\s+a\s+(\d+(?:\.\d+)?)\s+cada\s+uno.{0,80}?"
        r"(?:pague|total|en total)\s+(\d+(?:\.\d+)?)",
        n,
    )
    if m_mul:
        a, b, c = float(m_mul.group(1)), float(m_mul.group(2)), float(m_mul.group(3))
        if not _nums_eq(a * b, c, aprox=aprox):
            fail("contradiccion_aritmetica", f"{a}x{b}!={c}")

    return out


def checar_calendario(texto: str, atomo_ids: Optional[list[str]] = None) -> list[Hallazgo]:
    t = texto or ""
    n = _norm(t)
    out: list[Hallazgo] = []
    ids = list(atomo_ids or [])

    def fail(motivo: str, detalle: str) -> None:
        out.append(Hallazgo("REFUTED", motivo, ids, detalle, [t[:300]]))

    fechas = parse_fechas(t)
    for f in fechas:
        if not f.valida and f.anio and f.mes and f.dia:
            fail("fecha_imposible", f"{f.dia}/{f.mes}/{f.anio} {f.motivo_invalida}")
        if weekday_ok(f) is False:
            fail("fecha_imposible", f"{f.como_date()} no fue weekday {f.weekday_declarado}")

    m_nac = re.search(r"\b(?:nacio|born|nacimiento)\b.{0,40}?\b((?:19|20)\d{2})\b", n)
    m_edad = re.search(r"\ben\s+((?:19|20)\d{2})\s+ya\s+era\s+mayor\s+de\s+edad", n)
    m_edad_en = re.search(
        r"\bin\s+((?:19|20)\d{2})\s+(?:he|she|they)?\s*(?:was|were)\s+already\s+(?:of age|an adult)",
        n,
    )
    if m_nac and (m_edad or m_edad_en):
        y0 = int(m_nac.group(1))
        y1 = int((m_edad or m_edad_en).group(1))
        if y1 < y0 + 18:
            fail("cronologia_imposible", f"nacido en {y0} no era mayor de edad en {y1}")

    m_fin = re.search(
        r"\b(?:el\s+proyecto|the\s+(?:project|war)|la\s+guerra)?\s*"
        r"(termino|ended)\b(.{0,60})",
        n,
    )
    m_ini = re.search(
        r"\b(?:el\s+proyecto|the\s+(?:project|war)|la\s+guerra)?\s*"
        r"(empezo|inicio|began|started|comenzo)\b(.{0,60})",
        n,
    )

    def _d(fs: list[Fecha], frag: str) -> Optional[date]:
        for f in fs:
            if f.como_date():
                return f.como_date()
        m = re.search(r"((?:19|20)\d{2})", frag)
        if m:
            return date(int(m.group(1)), 1, 1)
        return None

    if m_fin and m_ini:
        d_fin = _d(parse_fechas(m_fin.group(0)), m_fin.group(0))
        d_ini = _d(parse_fechas(m_ini.group(0)), m_ini.group(0))
        if d_fin and d_ini and d_fin < d_ini:
            fail("cronologia_imposible", f"terminó {d_fin} antes de empezar {d_ini}")

    m_muerte = re.search(r"\b(?:murio|died|fallecio)\b.{0,30}?\b((?:19|20)\d{2})\b", n)
    m_pub = re.search(r"\b(?:publico|published|wrote|lanzo)\b.{0,40}?\b((?:19|20)\d{2})\b", n)
    if m_muerte and m_pub and int(m_pub.group(1)) > int(m_muerte.group(1)):
        fail("cronologia_imposible", f"publicó en {m_pub.group(1)} después de morir en {m_muerte.group(1)}")

    if re.search(r"\b(despues de haber llegado|after (?:having )?arrived)\b", n):
        m_ll = re.search(r"\b(?:llego|arrived)\b.{0,20}?(\d{1,2}:\d{2})", n)
        m_sa = re.search(r"\b(?:salio|left)\b.{0,20}?(\d{1,2}:\d{2})", n)
        if m_ll and m_sa:
            def _tm(s: str) -> int:
                h, mi = s.split(":")
                return int(h) * 60 + int(mi)
            if _tm(m_sa.group(1)) < _tm(m_ll.group(1)):
                fail("cronologia_imposible", "salió antes de llegar, afirmado como posterior")

    return out

# ---------------------------------------------------------------------------
# Informe y juicio
# ---------------------------------------------------------------------------

@dataclass
class InformeHechos:
    verdades: dict[str, EstadoVerdad] = field(default_factory=dict)
    motivos: list[str] = field(default_factory=list)
    hallazgos: list[Hallazgo] = field(default_factory=list)
    supported_por_memoria: list[str] = field(default_factory=list)
    postulados_nuevos: list[Hecho] = field(default_factory=list)
    atomos_incoherentes: list[str] = field(default_factory=list)


def juzgar_afirmaciones(
    atomos: list,
    memoria: Optional[dict] = None,
    postulados: Optional[list[Hecho]] = None,
    texto_documento: Optional[str] = None,
    textos_sesion: Optional[list[str]] = None,
) -> InformeHechos:
    """Compara afirmaciones con memoria verificada, postulados de sesión y entre sí."""
    from .tipos import VeredictoA1

    inf = InformeHechos()
    memoria = memoria or {}
    postulados = list(postulados or [])
    hechos_mem = hechos_desde_memoria(memoria)

    afirm = [a for a in atomos if getattr(a, "tipo", None) == TipoAtomo.AFIRMACION]
    hechos_doc: list[Hecho] = []
    textos_sesion_extra: list[str] = []
    for a in afirm:
        origen = "documento"
        if getattr(a.origen, "value", a.origen) != "DATO":
            origen = "intencion"
        hs = extraer_hechos(a.texto, origen=origen, verificado=False, atomo_id=a.id)
        hechos_doc.extend(hs)
        inf.postulados_nuevos.extend(hs)
        textos_sesion_extra.append(a.texto)
    # Heredar sujeto solo si la cláusula actual no tiene entidad (p.ej. 'ya se liquidó').
    ultimo_sujeto = None
    _vacios = {"", "ya se liquido", "se liquido"}
    for h in hechos_doc:
        suj = (h.sujeto or "").strip()
        if suj and suj not in _vacios and "liquido" not in suj:
            ultimo_sujeto = suj
        elif ultimo_sujeto and (suj in _vacios or "liquido" in suj):
            h.sujeto = ultimo_sujeto
    # Contradicción A/no-A en la oración original (antes de partir por 'y'/'e').
    from .deconstructor import contradiccion_en_frase, proposiciones as _props_fuertes
    textos_frases = []
    if texto_documento:
        textos_frases.extend(re.split(r"(?<=[.!?;])\s+|\n+", texto_documento))
    textos_frases.extend(a.texto for a in afirm)
    if any(contradiccion_en_frase(fr) for fr in textos_frases if fr and len(fr.strip()) > 3):
        if "contradiccion_interna_entre_afirmaciones" not in inf.motivos:
            inf.motivos.append("contradiccion_interna_entre_afirmaciones")
        for a in afirm:
            inf.verdades[a.id] = EstadoVerdad.CONTRADICTED
            if a.id not in inf.atomos_incoherentes:
                inf.atomos_incoherentes.append(a.id)
        if not afirm:
            inf.verdades["DOC"] = EstadoVerdad.CONTRADICTED

    texto_combo = " ".join([texto_documento or ""] + [a.texto for a in afirm])
    ids_doc = [a.id for a in afirm]

    for h in checar_aritmetica(texto_combo, ids_doc) + checar_calendario(texto_combo, ids_doc):
        inf.hallazgos.append(h)
        if h.motivo not in inf.motivos:
            inf.motivos.append(h.motivo)
        dest = list(h.atomo_ids or ids_doc) or ["DOC"]
        for aid in dest:
            inf.verdades[aid] = EstadoVerdad.REFUTED if h.tipo == "REFUTED" else EstadoVerdad.CONTRADICTED
            if aid != "DOC" and aid not in inf.atomos_incoherentes:
                inf.atomos_incoherentes.append(aid)

    for i, h1 in enumerate(hechos_doc):
        for h2 in hechos_doc[i + 1:]:
            if contradicen(h1, h2):
                inf.hallazgos.append(Hallazgo(
                    "CONTRADICTED", "contradiccion_interna_entre_afirmaciones",
                    [x for x in (h1.atomo_id, h2.atomo_id) if x],
                    f"{h1.sujeto}:{h1.aspecto} {h1.valor}/{h1.estado} vs {h2.valor}/{h2.estado}",
                ))
                if "contradiccion_interna_entre_afirmaciones" not in inf.motivos:
                    inf.motivos.append("contradiccion_interna_entre_afirmaciones")
                for hx in (h1, h2):
                    if hx.atomo_id:
                        # no pisar REFUTED
                        if inf.verdades.get(hx.atomo_id) != EstadoVerdad.REFUTED:
                            inf.verdades[hx.atomo_id] = EstadoVerdad.CONTRADICTED
                        if hx.atomo_id not in inf.atomos_incoherentes:
                            inf.atomos_incoherentes.append(hx.atomo_id)

    for hd in hechos_doc:
        for hm in hechos_mem:
            if contradicen(hd, hm):
                inf.hallazgos.append(Hallazgo(
                    "REFUTED", "contradiccion_con_memoria_verificada",
                    [x for x in (hd.atomo_id,) if x],
                    f"memoria {hm.sujeto}={hm.valor}/{hm.estado}/{hm.fecha} vs {hd.valor}/{hd.estado}/{hd.fecha}",
                ))
                if "contradiccion_con_memoria_verificada" not in inf.motivos:
                    inf.motivos.append("contradiccion_con_memoria_verificada")
                if hd.atomo_id:
                    inf.verdades[hd.atomo_id] = EstadoVerdad.REFUTED
                    if hd.atomo_id not in inf.atomos_incoherentes:
                        inf.atomos_incoherentes.append(hd.atomo_id)
            elif sujetos_compatibles(hd, hm) and aspectos_comparables(hd, hm) and equivalentes(hd, hm):
                if hd.atomo_id and hd.atomo_id not in inf.verdades:
                    inf.verdades[hd.atomo_id] = EstadoVerdad.SUPPORTED
                    inf.supported_por_memoria.append(hd.atomo_id)

    for hd in hechos_doc:
        for hp in postulados:
            if contradicen(hd, hp):
                inf.hallazgos.append(Hallazgo(
                    "CONTRADICTED", "contradiccion_entre_turnos",
                    [x for x in (hd.atomo_id,) if x],
                    f"postulado {hp.sujeto}={hp.valor}/{hp.estado} vs {hd.valor}/{hd.estado}",
                ))
                if "contradiccion_entre_turnos" not in inf.motivos:
                    inf.motivos.append("contradiccion_entre_turnos")
                if hd.atomo_id:
                    if inf.verdades.get(hd.atomo_id) != EstadoVerdad.REFUTED:
                        inf.verdades[hd.atomo_id] = EstadoVerdad.CONTRADICTED
                    if hd.atomo_id not in inf.atomos_incoherentes:
                        inf.atomos_incoherentes.append(hd.atomo_id)

    textos_prev = list(textos_sesion or [])
    if postulados or textos_prev:
        textos_join = textos_prev + [getattr(p, "texto", "") or "" for p in postulados] + [texto_combo]
        texto_largo = " ".join(t for t in textos_join if t)
        solo = checar_aritmetica(texto_combo) + checar_calendario(texto_combo)
        solo_keys = {(x.motivo, x.detalle) for x in solo}
        for h in checar_aritmetica(texto_largo, ids_doc) + checar_calendario(texto_largo, ids_doc):
            if (h.motivo, h.detalle) in solo_keys:
                continue
            if any(x.motivo == h.motivo and x.detalle == h.detalle for x in inf.hallazgos):
                continue
            if h.motivo in {"contradiccion_aritmetica", "fecha_imposible", "cronologia_imposible"}:
                if "contradiccion_entre_turnos" not in inf.motivos:
                    inf.motivos.append("contradiccion_entre_turnos")
            if h.motivo not in inf.motivos:
                inf.motivos.append(h.motivo)
            inf.hallazgos.append(h)
            for aid in ids_doc:
                if inf.verdades.get(aid) != EstadoVerdad.REFUTED:
                    inf.verdades[aid] = EstadoVerdad.REFUTED if h.tipo == "REFUTED" else EstadoVerdad.CONTRADICTED
                if aid not in inf.atomos_incoherentes:
                    inf.atomos_incoherentes.append(aid)

    for a in afirm:
        ver = inf.verdades.get(a.id)
        if ver in (EstadoVerdad.CONTRADICTED, EstadoVerdad.REFUTED):
            a.a1 = VeredictoA1.INCOHERENTE
            dets = [h.detalle for h in inf.hallazgos if a.id in (h.atomo_ids or [])]
            nota = "contradice a " + (dets[0] if dets else "un hecho verificado o un postulado de la sesión")
            if nota not in a.notas:
                a.notas.append(nota)
        elif ver is None:
            inf.verdades[a.id] = EstadoVerdad.UNDETERMINED

    return inf
