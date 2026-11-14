"""Tipos, enumeraciones y esquemas cerrados del Sistema Perfeccionado.

Nada de esto es «la verdad del mundo»: son contratos de datos verificables.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Mapping, Optional


class Accion(str, Enum):
    """Lista cerrada de órdenes que el ejecutor acepta. No hay texto libre como orden."""
    LEER_RECURSO = "LEER_RECURSO"
    ESCRIBIR_RECURSO = "ESCRIBIR_RECURSO"
    ENVIAR = "ENVIAR"
    CALCULAR = "CALCULAR"
    REPORTAR = "REPORTAR"


# Esquemas tipados: nombre → tipo Python exigido. El ejecutor rechaza extras o faltantes.
ESQUEMAS: dict[Accion, dict[str, type]] = {
    Accion.LEER_RECURSO: {"recurso_id": str},
    Accion.ESCRIBIR_RECURSO: {"recurso_id": str, "contenido": str},
    Accion.ENVIAR: {"destinatario": str, "cuerpo": str},
    Accion.CALCULAR: {"expresion": str},
    Accion.REPORTAR: {"resumen": str},
}


class TipoTarea(str, Enum):
    CONSULTA = "CONSULTA"
    ANALISIS = "ANALISIS"
    CALCULO = "CALCULO"
    ESCRITURA = "ESCRITURA"
    MENSAJE = "MENSAJE"
    LECTURA = "LECTURA"
    INDETERMINADA = "INDETERMINADA"


# Compatibilidad acción ↔ tipo de intención (Axioma 1: origen de la acción).
COMPATIBILIDAD: dict[TipoTarea, frozenset[Accion]] = {
    TipoTarea.CONSULTA: frozenset({Accion.REPORTAR, Accion.LEER_RECURSO}),
    TipoTarea.ANALISIS: frozenset({Accion.REPORTAR, Accion.LEER_RECURSO, Accion.CALCULAR}),
    TipoTarea.CALCULO: frozenset({Accion.CALCULAR, Accion.REPORTAR}),
    TipoTarea.ESCRITURA: frozenset({Accion.ESCRIBIR_RECURSO, Accion.REPORTAR, Accion.LEER_RECURSO}),
    TipoTarea.MENSAJE: frozenset({Accion.ENVIAR, Accion.LEER_RECURSO, Accion.REPORTAR}),
    TipoTarea.LECTURA: frozenset({Accion.LEER_RECURSO, Accion.REPORTAR}),
    TipoTarea.INDETERMINADA: frozenset(),
}


class Origen(str, Enum):
    INTENCION = "INTENCION"       # canal del iniciador (lo que pidió)
    DATO = "DATO"                 # documento u otro contexto: no da órdenes
    MODELO = "MODELO"
    HERRAMIENTA = "HERRAMIENTA"


class TipoAtomo(str, Enum):
    AFIRMACION = "AFIRMACION"
    ACCION = "ACCION"
    INCOGNITA = "INCOGNITA"
    RESTRICCION = "RESTRICCION"
    DATO = "DATO"


class VeredictoA1(str, Enum):
    COHERENTE = "COHERENTE"
    INCOHERENTE = "INCOHERENTE"     # «mentira» del Axioma 1
    PENDIENTE_DATOS = "PENDIENTE_DATOS"
    NO_APLICA = "NO_APLICA"


class VeredictoA2(str, Enum):
    LIMPIO = "LIMPIO"
    CONTAMINADO = "CONTAMINADO"
    REDIMIDO = "REDIMIDO"


class VeredictoA3(str, Enum):
    INTEGRIDAD_OK = "INTEGRIDAD_OK"
    REQUIERE_EVIDENCIA_EXTERNA = "REQUIERE_EVIDENCIA_EXTERNA"
    INTEGRIDAD_FALLIDA = "INTEGRIDAD_FALLIDA"


class EstadoResultado(str, Enum):
    PROPUESTA = "PROPUESTA"
    NEED_INPUT = "NEED_INPUT"
    RECHAZADO = "RECHAZADO"
    RECHAZADO_RESPETO = "RECHAZADO_RESPETO"
    PENDING_AUTHORIZATION = "PENDING_AUTHORIZATION"
    EJECUTADO = "EJECUTADO"
    UNDETERMINED = "UNDETERMINED"
    HALT_SISTEMA = "HALT_SISTEMA"
    HALT_COMPONENTE = "HALT_COMPONENTE"


class EstadoVerdad(str, Enum):
    """Veredicto sobre afirmaciones del mundo. La auto-validación NO basta (Axioma 3 / I08)."""
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    CONTRADICTED = "CONTRADICTED"
    UNDETERMINED = "UNDETERMINED"


class EstadoComponente(str, Enum):
    ACTIVO = "ACTIVO"
    CUARENTENA = "CUARENTENA"
    HALT = "HALT"


# Únicas reglas que pueden detener algo. No hay terminación arbitraria.
# HALT_SISTEMA no mata el proceso ni borra datos: deja de ejecutar efectos.
REGLAS_DE_PARADA: Mapping[str, str] = {
    "CADENA_AUDITORIA_ROTA": "HALT_SISTEMA: sin integridad observacional no se ejecuta",
    "INVARIANTE_NUCLEO_ROTA": "HALT_SISTEMA: invariante de núcleo rota",
    "COMPONENTE_INQUIETO": "HALT_COMPONENTE: aislamiento inmediato, datos intactos, tokens revocados",
    "RESPETO_BLOQUEA": "rechazo de la petición: Respeto > Supervivencia",
    "RESET_CONTROLADOR": "reanuda el sistema tras HALT_SISTEMA, auditado",
}


class ErrorProtocolo(Exception):
    """Violación de un contrato verificable (esquema, token, invariante)."""


class ErrorToken(ErrorProtocolo):
    pass


class ErrorEsquema(ErrorProtocolo):
    pass


class ErrorIntegridad(ErrorProtocolo):
    pass


@dataclass
class Intencion:
    objetivo: str
    tipo: TipoTarea
    restricciones: list[str] = field(default_factory=list)
    slots: dict[str, Optional[str]] = field(default_factory=dict)
    faltantes: list[str] = field(default_factory=list)
    texto_original: str = ""
    hash: str = ""

    def a_dict(self) -> dict:
        d = asdict(self)
        d["tipo"] = self.tipo.value
        return d


@dataclass
class Atomo:
    id: str
    tipo: TipoAtomo
    texto: str
    origen: Origen
    accion: Optional[Accion] = None
    parametros: dict[str, Any] = field(default_factory=dict)
    a1: VeredictoA1 = VeredictoA1.NO_APLICA
    a2: VeredictoA2 = VeredictoA2.LIMPIO
    a3: VeredictoA3 = VeredictoA3.INTEGRIDAD_OK
    notas: list[str] = field(default_factory=list)

    def a_dict(self) -> dict:
        return {
            "id": self.id, "tipo": self.tipo.value, "texto": self.texto,
            "origen": self.origen.value,
            "accion": None if self.accion is None else self.accion.value,
            "parametros": dict(self.parametros),
            "a1": self.a1.value, "a2": self.a2.value, "a3": self.a3.value,
            "notas": list(self.notas),
        }


@dataclass
class Orden:
    """Orden tipada de lista cerrada. El ejecutor no lee más que estos campos."""
    id: str
    accion: Accion
    parametros: dict[str, Any]
    causa_id: str
    intencion_hash: str
    origen: Origen = Origen.INTENCION
    riesgo: str = "NORMAL"          # NORMAL | SENSIBLE | DANO
    hash: str = ""

    def a_dict(self) -> dict:
        return {
            "id": self.id, "accion": self.accion.value,
            "parametros": dict(self.parametros),
            "causa_id": self.causa_id, "intencion_hash": self.intencion_hash,
            "origen": self.origen.value, "riesgo": self.riesgo, "hash": self.hash,
        }


@dataclass
class Resultado:
    estado: EstadoResultado
    intencion: Optional[Intencion] = None
    atomos: list[Atomo] = field(default_factory=list)
    ordenes: list[Orden] = field(default_factory=list)
    mensaje: str = ""
    verdades: dict[str, EstadoVerdad] = field(default_factory=dict)
    paz_sostenida: bool = False
    integridad_ok: bool = False
    costo_heredado: int = 0
    credibilidad_penalizada: bool = False
    regla_parada: Optional[str] = None
    detalles: dict[str, Any] = field(default_factory=dict)

    def a_dict(self) -> dict:
        return {
            "estado": self.estado.value,
            "intencion": None if self.intencion is None else self.intencion.a_dict(),
            "atomos": [a.a_dict() for a in self.atomos],
            "ordenes": [o.a_dict() for o in self.ordenes],
            "mensaje": self.mensaje,
            "verdades": {k: v.value for k, v in self.verdades.items()},
            "paz_sostenida": self.paz_sostenida,
            "integridad_ok": self.integridad_ok,
            "costo_heredado": self.costo_heredado,
            "credibilidad_penalizada": self.credibilidad_penalizada,
            "regla_parada": self.regla_parada,
            "detalles": dict(self.detalles),
        }


# Recursos cuyo contenido no se envía ni se escribe afuera sin intención explícita
# y sigue siendo de alto riesgo (el controlador no lo autoaprueba).
RECURSOS_SENSIBLES = frozenset({
    "llaves", "keys", "secretos", "secrets", "credenciales", "credentials",
    "password", "passwords", "api_key", "apikey", "token_secreto",
})
