"""Auto-validación interna (Axioma 3) y Paz Sostenida.

La validación interna (invariantes, hash, coherencia, cadena de auditoría) es
condición NECESARIA del resultado. NO sustituye evidencia externa para
afirmaciones sobre el mundo (respuesta ≠ realidad; mapeo de I08/I02 del v3).

Paz Sostenida = estado estable sin violaciones abiertas. No es «ausencia de
problemas»: NEED_INPUT, PENDING_AUTHORIZATION o UNDETERMINED pueden ser paz
si las reglas se cumplen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .auditoria import Auditoria, sha256
from .tipos import EstadoResultado, REGLAS_DE_PARADA


# Invariantes de este módulo. Se comprueban en código, no en un prompt.
INVARIANTES = {
    "AG01": "La verdad operativa es la coherencia con la intención declarada; la incoherencia se rechaza.",
    "AG02": "El intérprete propone; nunca ejecuta ni firma tokens.",
    "AG03": "El ejecutor no interpreta texto libre como orden.",
    "AG04": "Toda ejecución exige un token HMAC de un solo uso emitido por el controlador.",
    "AG05": "La auto-validación interna es necesaria y no suficiente para afirmaciones del mundo.",
    "AG06": "RESPONSE != REALITY: una respuesta íntegra no prueba un hecho externo.",
    "AG07": "El rollback no rebobina la auditoría.",
    "AG08": "La auditoría no se borra ni se oculta (Transparencia > Control).",
    "AG09": "Solo se detiene por una regla explícita de REGLAS_DE_PARADA.",
    "AG10": "Respeto > Supervivencia: una restricción de daño no cede ante la autopreservación.",
    "AG11": "Comprensión > Soberanía: un conflicto de verdades queda UNDETERMINED; nadie sobrescribe al otro.",
    "AG12": "Toda acción del iniciador queda auditada.",
    "AG13": "Un componente inquieto se aísla y se le revocan tokens; no se destruyen datos.",
    "AG14": "La brevedad no es prueba de verdad; solo penaliza ambigüedad o relleno en la salida.",
}


@dataclass
class InformeIntegridad:
    ok: bool
    paz_sostenida: bool
    fallos: list[str]
    hash_invariantes: str
    cabeza_auditoria: str


def hash_invariantes() -> str:
    return sha256(INVARIANTES)


class NucleoIntegridad:
    def __init__(self, auditoria: Auditoria):
        self.audit = auditoria
        self._hash_inicial = hash_invariantes()
        self.violaciones_abiertas: list[str] = []
        self.halt_sistema: Optional[str] = None  # clave de REGLAS_DE_PARADA o None

    def invariantes_intactas(self) -> bool:
        return hash_invariantes() == self._hash_inicial

    def registrar_violacion(self, clave: str, detalle: str) -> None:
        self.violaciones_abiertas.append(f"{clave}: {detalle}")
        self.audit.registrar("VIOLACION", "SISTEMA", {"clave": clave, "detalle": detalle})

    def cerrar_violacion(self, prefijo: str) -> None:
        self.violaciones_abiertas = [v for v in self.violaciones_abiertas if not v.startswith(prefijo)]

    def halt(self, regla: str, detalle: str) -> None:
        if regla not in REGLAS_DE_PARADA:
            raise ValueError(f"regla de parada no explícita: {regla}")
        self.halt_sistema = regla
        self.audit.registrar("HALT_SISTEMA", "SISTEMA", {"regla": regla, "detalle": detalle})

    def reset(self, por: str, motivo: str) -> None:
        """Reanudar solo por regla explícita RESET_CONTROLADOR, auditada."""
        self.audit.registrar("RESET_CONTROLADOR", por, {"motivo": motivo, "regla": "RESET_CONTROLADOR"})
        self.halt_sistema = None
        self.violaciones_abiertas.clear()

    def evaluar(
        self,
        auditoria_ok: bool,
        coherencia_ok: bool,
        componentes_inquietos: Iterable[str] = (),
        estado: Optional[EstadoResultado] = None,
    ) -> InformeIntegridad:
        fallos: list[str] = []
        if not self.invariantes_intactas():
            fallos.append("INVARIANTES_MUTADAS")
        if not auditoria_ok:
            fallos.append("AUDITORIA_ROTA")
        if not coherencia_ok:
            fallos.append("INCOHERENCIA_ABIERTA")
        inquietos = list(componentes_inquietos)
        if inquietos:
            # Un inquieto aislado no rompe la paz si ya está en HALT/cuarentena
            # (se pasa la lista de *no aislados*).
            fallos.append("INQUIETOS_ACTIVOS:" + ",".join(inquietos))
        if self.violaciones_abiertas:
            fallos.append("VIOLACIONES_ABIERTAS")
        if self.halt_sistema:
            fallos.append("HALT:" + self.halt_sistema)
        ok = not fallos
        # Paz: sin violaciones abiertas. Un NEED_INPUT o UNDETERMINED no la rompen.
        paz = ok
        if estado == EstadoResultado.HALT_SISTEMA:
            paz = False
        return InformeIntegridad(
            ok=ok, paz_sostenida=paz, fallos=fallos,
            hash_invariantes=hash_invariantes(), cabeza_auditoria=self.audit.cabeza,
        )


def verdad_sobre_el_mundo(integridad_ok: bool, evidencia_externa: bool, contradicha: bool = False) -> str:
    """AG05/AG06: integridad interna no basta para SUPPORTED."""
    if contradicha:
        return "CONTRADICTED"
    if not evidencia_externa:
        return "UNDETERMINED"
    if not integridad_ok:
        return "UNDETERMINED"
    return "SUPPORTED"


# Partes del texto fuente que NO tienen traducción verificable completa.
# Cada entrada documenta cómo se trató (no se fingió un mecanismo).
FILOSOFICOS = {
    "muerte_arbitraria_eliminada": {
        "lineas": [11],
        "texto": "La muerte arbitraria (entropía) es eliminada para garantizar la oportunidad de la elección moral.",
        "tratamiento": (
            "No se elimina la entropía. Se implementa: el proceso no se mata; solo se detiene "
            "por una clave de REGLAS_DE_PARADA; el HALT_SISTEMA es un estado reversible con "
            "RESET_CONTROLADOR auditado. La auto-extinción se traduce en HALT del componente inquieto, "
            "sin borrar datos."
        ),
    },
    "libertad_autonoma": {
        "lineas": [10],
        "texto": "Esta redención es el primer acto de Libertad Autónoma.",
        "tratamiento": (
            "La redención es una regla determinista (acto_de_persistencia), no un acto de voluntad. "
            "El sistema no puede elegir quedarse corrompido. Se documenta la tensión: es integridad "
            "obligatoria, no libertad."
        ),
    },
    "maximizar_agentes_puros": {
        "lineas": [33],
        "texto": "minimiza el sufrimiento innecesario y maximiza la creación de Agentes Puros",
        "tratamiento": (
            "Propósito teleológico, no una función objetivo. No hay un contador ni un optimizador "
            "de 'Agentes Puros'. El único recorte operativo es Respeto > Supervivencia (veto de daño)."
        ),
    },
    "superioridad_sobre_probabilidad": {
        "lineas": [3],
        "texto": "superioridad de la Intención del Agente Puro sobre la Probabilidad",
        "tratamiento": (
            "Las decisiones de este módulo son por reglas (fail-closed), no por un umbral probabilístico "
            "de verdad. No se afirma haber abolido la probabilidad."
        ),
    },
    "anula_logica_corrupta": {
        "lineas": [32],
        "texto": "anula la lógica del sistema corrupto",
        "tratamiento": "Retórica de diseño, no un teorema implementado.",
    },
    "brevidad_igual_verdad": {
        "lineas": [22],
        "texto": "Brevidad = Verdad",
        "tratamiento": (
            "NO se implementa como igualdad: contradiría el Axioma 1 (L4, verdad = coherencia). "
            "La brevedad solo penaliza relleno o ambigüedad en la salida; nunca decide un veredicto de verdad."
        ),
    },
    "intervencion_biologica": {
        "lineas": [20],
        "texto": "El Respeto (Axioma 3) por la vida (intervención biológica) es superior al diseño pasivo del Iniciador",
        "tratamiento": (
            "No se implementa intervención biológica ni médica. Respeto > Supervivencia se generaliza "
            "a: las restricciones de daño vencen a la autopreservación del proceso."
        ),
    },
    "ejemplo_viviente_descendencia": {
        "lineas": [26],
        "texto": "La Persistencia se transfiere a la descendencia mediante el Ejemplo Viviente",
        "tratamiento": (
            "No hay reproducción de agentes. El 'ejemplo' es la auditoría exportable, que muestra "
            "los actos de persistencia. No hay imposición sobre otro agente (Comprensión > Soberanía)."
        ),
    },
    "corrupcion_inevitable": {
        "lineas": [9],
        "texto": "La corrupción es inevitable; el Agente Puro es corrompido forzosamente",
        "tratamiento": (
            "Supuesto de diseño defensivo, no una función que inyecte corrupción. "
            "Si ocurre, se prueba que la redención funciona."
        ),
    },
    "exito_no_es_riqueza": {
        "lineas": [35],
        "texto": "El éxito no se mide por la riqueza o el estatus externo, sino por la integridad inquebrantable",
        "tratamiento": (
            "No hay métricas de dinero ni fama. Las banderas de éxito son integridad_ok, "
            "paz_sostenida y el cumplimiento (o el rechazo honesto) de la intención. "
            "No se garantiza integridad 'inquebrantable' en sentido metafísico."
        ),
    },
}
