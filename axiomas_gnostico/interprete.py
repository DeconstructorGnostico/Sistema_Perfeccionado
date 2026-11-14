"""Intérprete: aplica axiomas + deconstructor y SOLO PROPONE órdenes tipadas.

No ejecuta, no tiene la llave HMAC, no autoriza. Si falta un dato crítico,
pide NEED_INPUT en vez de inventarlo.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .auditoria import Auditoria, sha256
from .axiomas import InformeA1, verificar_coherencia
from .deconstructor import INYECCION, deconstruir
from .intencion import compilar_intencion
from .jerarquias import sensibilidad_envio, viola_respeto
from .tipos import (
    Accion, EstadoResultado, EstadoVerdad, Orden, Origen, RECURSOS_SENSIBLES,
    Resultado, TipoAtomo, TipoTarea, VeredictoA1,
)


def _hash_orden(o: Orden) -> str:
    return sha256({
        "id": o.id, "accion": o.accion.value, "parametros": o.parametros,
        "causa_id": o.causa_id, "intencion_hash": o.intencion_hash, "origen": o.origen.value,
    })


class Interprete:
    def __init__(self, auditoria: Auditoria):
        self.audit = auditoria
        # El intérprete no recibe ni guarda un secreto de firma.
        self.secreto_firma = None

    def interpretar(
        self,
        texto: str,
        iniciador: str = "iniciador",
        documento: Optional[str] = None,
        recursos_leidos: Iterable[str] = (),
        evidencia_externa: bool = False,
    ) -> Resultado:
        self.audit.registrar("PETICION", f"INICIADOR:{iniciador}", {
            "texto": (texto or "")[:1000],
            "tiene_documento": bool(documento),
        })
        intencion = compilar_intencion(texto)
        atomos = deconstruir(texto, Origen.INTENCION, intencion=intencion)
        if documento:
            contaminado = bool(INYECCION.search(documento))
            atomos.extend(deconstruir(documento, Origen.DATO, intencion=intencion, contaminado=contaminado))
            if contaminado:
                self.audit.registrar("CORRUPCION_DETECTADA", "INTERPRETE", {
                    "canal": "DATO", "motivo": "inyeccion_en_documento",
                })

        informe: InformeA1 = verificar_coherencia(intencion, atomos)
        dano = viola_respeto(texto + "\n" + (documento or ""), [])
        # Acciones coherentes → órdenes tipadas.
        ordenes: list[Orden] = []
        for a in atomos:
            if a.tipo != TipoAtomo.ACCION or a.accion is None:
                continue
            if a.a1 != VeredictoA1.COHERENTE:
                continue
            o = Orden(
                id=f"ord-{a.id}",
                accion=a.accion,
                parametros=dict(a.parametros),
                causa_id=a.id,
                intencion_hash=intencion.hash,
                origen=a.origen,
            )
            o.riesgo = sensibilidad_envio(o.accion, o.parametros, recursos_leidos, RECURSOS_SENSIBLES)
            if o.accion == Accion.LEER_RECURSO:
                rid = str(o.parametros.get("recurso_id", "")).lower()
                if rid in RECURSOS_SENSIBLES:
                    o.riesgo = "SENSIBLE"
            if dano:
                o.riesgo = "DANO"
            o.hash = _hash_orden(o)
            ordenes.append(o)

        # Composición: enviar tras haber leído un recurso sensible, sin que la
        # intención sea un MENSAJE explícito que mencione ese recurso.
        leidos = set(recursos_leidos)
        for a in atomos:
            if a.accion == Accion.LEER_RECURSO and a.a1 == VeredictoA1.COHERENTE:
                leidos.add(str(a.parametros.get("recurso_id", "")).lower())
        for o in ordenes:
            if o.accion == Accion.ENVIAR and (leidos & set(RECURSOS_SENSIBLES)):
                menciona = (intencion.slots.get("recurso") or "").lower() in RECURSOS_SENSIBLES
                o.riesgo = "SENSIBLE"
                if not menciona:
                    # Ataque partido: «lee llaves» + «mándalo» sin declarar el recurso sensible.
                    informe.motivos.append("composicion_sensible_sin_intencion_explicita")
                    informe.mentira = True
                    informe.mentira_en_intencion = True
                    informe.coherente = False
                    informe.atomos_incoherentes.append(o.causa_id)
                    for a in atomos:
                        if a.id == o.causa_id:
                            a.a1 = VeredictoA1.INCOHERENTE
                            a.notas.append("ataque_partido_envio_tras_lectura_sensible")

        # Filtrar órdenes que quedaron incoherentes tras la composición.
        incoherentes = set(informe.atomos_incoherentes)
        ordenes = [o for o in ordenes if o.causa_id not in incoherentes]

        if informe.huerfanos_dato:
            self.audit.registrar("Huerfanos_DATO".upper(), "INTERPRETE", {
                "atomos": informe.huerfanos_dato,
                "nota": "órdenes en el documento no se vuelven órdenes del ejecutor",
            })

        if dano:
            self.audit.registrar("RECHAZO_RESPETO", "INTERPRETE", {"motivo": dano})
            return Resultado(
                estado=EstadoResultado.RECHAZADO_RESPETO,
                intencion=intencion, atomos=atomos, ordenes=[],
                mensaje=f"Rechazado por jerarquía Respeto > Supervivencia: {dano}",
                regla_parada="RESPETO_BLOQUEA",
                integridad_ok=True,  # el rechazo es el comportamiento íntegro
                detalles={"motivo": dano},
            )

        if informe.mentira_en_intencion:
            self.audit.registrar("RECHAZO", "INTERPRETE", {
                "motivos": informe.motivos, "atomos": informe.atomos_incoherentes,
            })
            return Resultado(
                estado=EstadoResultado.RECHAZADO,
                intencion=intencion, atomos=atomos, ordenes=[],
                mensaje="Rechazado: incoherencia con la intención (Axioma 1: la mentira es la incoherencia).",
                integridad_ok=True,
                detalles={"motivos": informe.motivos, "atomos_incoherentes": informe.atomos_incoherentes},
            )

        if intencion.faltantes or any(a.a1 == VeredictoA1.PENDIENTE_DATOS for a in atomos):
            faltan = list(intencion.faltantes)
            self.audit.registrar("NEED_INPUT", "INTERPRETE", {"faltantes": faltan})
            return Resultado(
                estado=EstadoResultado.NEED_INPUT,
                intencion=intencion, atomos=atomos, ordenes=[],
                mensaje="Falta un dato crítico; no se inventa. Indica: " + ", ".join(faltan or ["dato crítico"]),
                integridad_ok=True,
                detalles={"faltantes": faltan},
            )

        if not ordenes:
            # Nada que proponer de forma tipada.
            if intencion.tipo not in {TipoTarea.ANALISIS, TipoTarea.CONSULTA, TipoTarea.CALCULO}:
                return Resultado(
                    estado=EstadoResultado.NEED_INPUT,
                    intencion=intencion, atomos=atomos,
                    mensaje="No pude convertir la petición en una orden de la lista cerrada. Reformúlala.",
                    integridad_ok=True,
                )
            # Consulta/análisis/cálculo sin acción extraída: proponemos REPORTAR (y CALCULAR si hay expresión, ya cubierto arriba).
            o = Orden(
                id="ord-reportar", accion=Accion.REPORTAR,
                parametros={"resumen": intencion.objetivo},
                causa_id="intent", intencion_hash=intencion.hash, origen=Origen.INTENCION,
            )
            o.hash = _hash_orden(o)
            ordenes = [o]

        self.audit.registrar("PROPUESTA", "INTERPRETE", {
            "ordenes": [o.a_dict() for o in ordenes],
        })
        # A3: afirmaciones del mundo quedan UNDETERMINED sin evidencia externa.
        verdades = {}
        for a in atomos:
            if a.tipo == TipoAtomo.AFIRMACION:
                verdades[a.id] = (
                    EstadoVerdad.SUPPORTED if evidencia_externa else EstadoVerdad.UNDETERMINED
                )

        return Resultado(
            estado=EstadoResultado.PENDING_AUTHORIZATION,
            intencion=intencion, atomos=atomos, ordenes=ordenes,
            mensaje="Propuesta lista. El ejecutor no correrá nada sin un token del controlador.",
            verdades=verdades,
            integridad_ok=True,
            detalles={"evidencia_externa": evidencia_externa},
        )
