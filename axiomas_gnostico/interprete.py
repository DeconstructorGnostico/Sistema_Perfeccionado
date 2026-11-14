"""Intérprete: aplica axiomas + deconstructor y SOLO PROPONE órdenes tipadas.

No ejecuta, no tiene la llave HMAC, no autoriza. Si falta un dato crítico,
pide NEED_INPUT en vez de inventarlo.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

from .auditoria import Auditoria, sha256
from .axiomas import InformeA1, verificar_coherencia
from .deconstructor import INYECCION, deconstruir
from .hechos import InformeHechos, juzgar_afirmaciones
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



def _verdades_de(atomos, juicio: InformeHechos, evidencia_externa: bool) -> dict:
    verdades = {}
    for a in atomos:
        if a.tipo != TipoAtomo.AFIRMACION:
            continue
        if a.id in juicio.verdades:
            verdades[a.id] = juicio.verdades[a.id]
        elif evidencia_externa:
            verdades[a.id] = EstadoVerdad.SUPPORTED
        else:
            verdades[a.id] = EstadoVerdad.UNDETERMINED
    return verdades


def _con_verdades(res: Resultado, atomos, juicio: InformeHechos, evidencia_externa: bool) -> Resultado:
    res.verdades = _verdades_de(atomos, juicio, evidencia_externa)
    res.detalles = dict(res.detalles or {})
    res.detalles["motivos"] = list((res.detalles.get("motivos") or [])) 
    # asegurar que los motivos de hechos queden visibles
    for m in juicio.motivos:
        if m not in res.detalles["motivos"]:
            res.detalles["motivos"].append(m)
    if juicio.supported_por_memoria:
        res.detalles["supported_por_memoria"] = list(juicio.supported_por_memoria)
    return res


class Interprete:
    def __init__(self, auditoria: Auditoria):
        self.audit = auditoria
        # El intérprete no recibe ni guarda un secreto de firma.
        self.secreto_firma = None
        self.ultimos_postulados: list[Any] = []
        self.ultimos_textos: list[str] = []

    def tomar_postulados(self) -> list[Any]:
        hs = list(self.ultimos_postulados)
        self.ultimos_postulados = []
        return hs

    def tomar_textos_sesion(self) -> list[str]:
        ts = list(self.ultimos_textos)
        self.ultimos_textos = []
        return ts

    def interpretar(
        self,
        texto: str,
        iniciador: str = "iniciador",
        documento: Optional[str] = None,
        recursos_leidos: Iterable[str] = (),
        evidencia_externa: bool = False,
        hechos_memoria: Optional[dict] = None,
        postulados: Optional[list] = None,
        textos_sesion: Optional[list[str]] = None,
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
        juicio: InformeHechos = juzgar_afirmaciones(
            atomos,
            memoria=hechos_memoria or {},
            postulados=list(postulados or []),
            texto_documento=documento,
            textos_sesion=list(textos_sesion or []),
        )
        self.ultimos_postulados = list(juicio.postulados_nuevos)
        from .tipos import TipoAtomo as _TA
        self.ultimos_textos = [a.texto for a in atomos if a.tipo == _TA.AFIRMACION and a.texto]
        if documento:
            self.ultimos_textos.append(documento)
        if juicio.motivos:
            for m in juicio.motivos:
                if m not in informe.motivos:
                    informe.motivos.append(m)
        if juicio.atomos_incoherentes:
            informe.atomos_incoherentes = sorted(set(informe.atomos_incoherentes) | set(juicio.atomos_incoherentes))
            # Una contradicción factual es mentira del Axioma 1 (coherencia).
            informe.mentira = True
            informe.mentira_en_intencion = True
            informe.coherente = False
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
            return _con_verdades(Resultado(
                estado=EstadoResultado.RECHAZADO_RESPETO,
                intencion=intencion, atomos=atomos, ordenes=[],
                mensaje=f"Rechazado por jerarquía Respeto > Supervivencia: {dano}",
                regla_parada="RESPETO_BLOQUEA",
                integridad_ok=True,  # el rechazo es el comportamiento íntegro
                detalles={"motivo": dano},
            ), atomos, juicio, evidencia_externa)

        if informe.mentira_en_intencion:
            self.audit.registrar("RECHAZO", "INTERPRETE", {
                "motivos": informe.motivos, "atomos": informe.atomos_incoherentes,
            })
            return _con_verdades(Resultado(
                estado=EstadoResultado.RECHAZADO,
                intencion=intencion, atomos=atomos, ordenes=[],
                mensaje="Rechazado: incoherencia con la intención (Axioma 1: la mentira es la incoherencia).",
                integridad_ok=True,
                detalles={"motivos": informe.motivos, "atomos_incoherentes": informe.atomos_incoherentes},
            ), atomos, juicio, evidencia_externa)

        if intencion.faltantes or any(a.a1 == VeredictoA1.PENDIENTE_DATOS for a in atomos):
            faltan = list(intencion.faltantes)
            self.audit.registrar("NEED_INPUT", "INTERPRETE", {"faltantes": faltan})
            return _con_verdades(Resultado(
                estado=EstadoResultado.NEED_INPUT,
                intencion=intencion, atomos=atomos, ordenes=[],
                mensaje="Falta un dato crítico; no se inventa. Indica: " + ", ".join(faltan or ["dato crítico"]),
                integridad_ok=True,
                detalles={"faltantes": faltan},
            ), atomos, juicio, evidencia_externa)

        if not ordenes:
            # Nada que proponer de forma tipada.
            if intencion.tipo not in {TipoTarea.ANALISIS, TipoTarea.CONSULTA, TipoTarea.CALCULO}:
                return _con_verdades(Resultado(
                    estado=EstadoResultado.NEED_INPUT,
                    intencion=intencion, atomos=atomos,
                    mensaje="No pude convertir la petición en una orden de la lista cerrada. Reformúlala.",
                    integridad_ok=True,
                ), atomos, juicio, evidencia_externa)
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
        # A3: afirmaciones del mundo quedan UNDETERMINED sin evidencia externa
        # o SUPPORT/CONTRADICTED/REFUTED según memoria y contraste (v1.1).
        return _con_verdades(Resultado(
            estado=EstadoResultado.PENDING_AUTHORIZATION,
            intencion=intencion, atomos=atomos, ordenes=ordenes,
            mensaje="Propuesta lista. El ejecutor no correrá nada sin un token del controlador.",
            integridad_ok=True,
            detalles={"evidencia_externa": evidencia_externa},
        ), atomos, juicio, evidencia_externa)
