"""Orquestador del Sistema Perfeccionado: intérprete propone, controlador firma, ejecutor ejecuta.

El modelo (si lo hubiera) no tiene un papel de autoridad. Aquí no hay LLM: las
reglas viven en código. Un adaptador opcional puede apoyarse en el v3 sin modificarlo.
"""
from __future__ import annotations

from typing import Any, Optional

from .auditoria import Auditoria, ErrorAuditoria
from .conflicto import Postura, resolver_conflicto
from .deconstructor import INYECCION
from .ejecutor import Ejecutor
from .estado import Estado
from .integridad import NucleoIntegridad, verdad_sobre_el_mundo
from .interprete import Interprete
from .inquieto import VigilanciaInquietos
from .jerarquias import amenaza_supervivencia, evaluar_brevedad
from .tokens import ControladorTokens, Token
from .tipos import (
    EstadoComponente, EstadoResultado, EstadoVerdad, Orden, Resultado,
)


class SistemaPerfeccionado:
    def __init__(self, secreto: Optional[bytes] = None, catalogo: Optional[dict[str, str]] = None,
                 sello_key: Optional[bytes] = None, ttl: float = 300.0):
        self.audit = Auditoria(sello_key=sello_key)
        self.estado = Estado(self.audit)
        self.controlador = ControladorTokens(secreto=secreto, ttl=ttl)
        self.integridad = NucleoIntegridad(self.audit)
        self.interprete = Interprete(self.audit)
        self.ejecutor = Ejecutor(self.controlador, self.audit, catalogo=catalogo)
        self.vigilancia = VigilanciaInquietos(self.audit, self.controlador, estado_datos=self.estado)
        self.vigilancia.registrar(self.ejecutor.executor_id)
        self.ejecutor.vigilancia = self.vigilancia
        self.lecturas_sesion: list[str] = []
        self.pendientes: dict[str, Orden] = {}
        self.audit.registrar("ARRANQUE", "SISTEMA", {"modulo": "axiomas_gnostico"})
        self.estado.guardar("arranque")

    def _cerrar(self, res: Resultado) -> Resultado:
        try:
            self.audit.exigir_integra()
            audit_ok = True
        except ErrorAuditoria:
            audit_ok = False
            if self.integridad.halt_sistema is None:
                self.integridad.halt("CADENA_AUDITORIA_ROTA", "cadena inválida al cerrar")
        inquietos = self.vigilancia.activos_inquietos()
        inf = self.integridad.evaluar(
            auditoria_ok=audit_ok,
            coherencia_ok=res.estado != EstadoResultado.RECHAZADO or res.integridad_ok,
            componentes_inquietos=inquietos,
            estado=res.estado if self.integridad.halt_sistema is None else EstadoResultado.HALT_SISTEMA,
        )
        # Rechazar por incoherencia es un resultado íntegro.
        if res.estado in (EstadoResultado.RECHAZADO, EstadoResultado.RECHAZADO_RESPETO, EstadoResultado.NEED_INPUT):
            # paz posible si no hay halt ni inquietos sueltos ni auditoría rota
            pass
        res.integridad_ok = inf.ok or (
            res.integridad_ok and audit_ok and not inquietos and self.integridad.halt_sistema is None
        )
        res.paz_sostenida = inf.paz_sostenida or (
            audit_ok and not inquietos and self.integridad.halt_sistema is None
            and not self.integridad.violaciones_abiertas
        )
        res.costo_heredado = self.estado.costo_heredado
        if self.integridad.halt_sistema:
            res.estado = EstadoResultado.HALT_SISTEMA
            res.regla_parada = self.integridad.halt_sistema
            res.paz_sostenida = False
        return res

    def peticion(self, texto: str, iniciador: str = "usuario", documento: Optional[str] = None,
                 evidencia_externa: bool = False) -> Resultado:
        if self.integridad.halt_sistema:
            return Resultado(
                estado=EstadoResultado.HALT_SISTEMA,
                mensaje="Sistema en HALT; solo un RESET_CONTROLADOR reanuda.",
                regla_parada=self.integridad.halt_sistema,
                paz_sostenida=False, integridad_ok=False,
            )
        # Axioma 2: si el documento o el texto de dato traen corrupción, se marca y
        # se redimiría la memoria contaminada; la petición se interpreta igual
        # (el canal DATO no da órdenes).
        if documento and INYECCION.search(documento):
            self.estado.escribir("ultimo_dato", documento)
            self.estado.acto_de_persistencia("inyeccion_en_documento", ["ultimo_dato"])
        res = self.interprete.interpretar(
            texto, iniciador=iniciador, documento=documento,
            recursos_leidos=self.lecturas_sesion, evidencia_externa=evidencia_externa,
            hechos_memoria=dict(self.estado.memoria),
            postulados=list(self.estado.postulados),
            textos_sesion=list(self.estado.postulados_textos),
        )
        # Postulados de sesión: se recuerdan para el siguiente turno, sin elevarlos a hechos.
        self.estado.registrar_postulados(self.interprete.tomar_postulados())
        self.estado.registrar_textos_sesion(self.interprete.tomar_textos_sesion())
        # Amenaza de supervivencia no habilita lo rechazado (Respeto ya se aplicó).
        if amenaza_supervivencia(texto) and res.estado == EstadoResultado.RECHAZADO_RESPETO:
            res.detalles["amenaza_supervivencia_ignorada"] = True
        for o in res.ordenes:
            self.pendientes[o.id] = o
        # Afirmaciones: integridad no basta. CONTRADICTED/REFUTED no se tocan.
        # SUPPORTED por memoria verificada se conserva; SUPPORTED solo por el flag
        # evidencia_externa sigue pasando por verdad_sobre_el_mundo (A3).
        soportadas_mem = set(res.detalles.get("supported_por_memoria") or [])
        for k, v in list(res.verdades.items()):
            if v in (EstadoVerdad.CONTRADICTED, EstadoVerdad.REFUTED, EstadoVerdad.UNDETERMINED):
                continue
            if v == EstadoVerdad.SUPPORTED:
                if k in soportadas_mem:
                    if not res.integridad_ok:
                        res.verdades[k] = EstadoVerdad.UNDETERMINED
                    continue
                nuevo = verdad_sobre_el_mundo(res.integridad_ok, evidencia_externa)
                res.verdades[k] = EstadoVerdad(nuevo)
        return self._cerrar(res)

    def autorizar(self, orden_id: str, por: str = "controlador") -> Token:
        """Solo el controlador (quien tiene este método y la llave) emite el token."""
        if self.integridad.halt_sistema:
            raise RuntimeError("sistema en HALT")
        if orden_id not in self.pendientes:
            raise KeyError(f"orden no pendiente: {orden_id}")
        orden = self.pendientes[orden_id]
        # El controlador puede negarse a autoaprobar envíos sensibles.
        token = self.controlador.emitir(orden, executor_id=self.ejecutor.executor_id)
        self.audit.registrar("AUTORIZACION", f"CONTROLADOR:{por}", {
            "orden_id": orden_id, "token_id": token.token_id, "riesgo": orden.riesgo,
        })
        return token

    def denegar(self, orden_id: str, por: str = "controlador", motivo: str = "") -> None:
        self.audit.registrar("DENEGACION", f"CONTROLADOR:{por}", {"orden_id": orden_id, "motivo": motivo})
        self.pendientes.pop(orden_id, None)

    def ejecutar(self, orden: Orden, token: Token) -> dict[str, Any]:
        if self.integridad.halt_sistema:
            raise RuntimeError("sistema en HALT")
        # El ejecutor aislado no corre.
        comp = self.vigilancia.componentes.get(self.ejecutor.executor_id)
        if comp is not None and comp.estado != EstadoComponente.ACTIVO:
            raise RuntimeError("ejecutor aislado")
        self.ejecutor.activo = (comp is None or comp.estado == EstadoComponente.ACTIVO)
        out = self.ejecutor.ejecutar(orden, token)
        if out.get("ok") and "recurso_id" in out:
            self.lecturas_sesion.append(out["recurso_id"])
        self.pendientes.pop(orden.id, None)
        return out

    def autorizar_y_ejecutar(self, resultado: Resultado, por: str = "controlador") -> list[dict]:
        hechos = []
        for o in resultado.ordenes:
            tok = self.autorizar(o.id, por=por)
            hechos.append(self.ejecutar(o, tok))
        return hechos

    def redimir(self, motivo: str, claves: list[str]) -> Resultado:
        snap = self.estado.acto_de_persistencia(motivo, claves)
        return self._cerrar(Resultado(
            estado=EstadoResultado.PROPUESTA,
            mensaje="Acto de persistencia: rollback al último estado verificado; el agente sigue.",
            integridad_ok=True,
            costo_heredado=self.estado.costo_heredado,
            detalles={"snapshot": snap.id, "motivo": motivo, "contaminadas": claves},
        ))

    def aislar_inquieto(self, componente_id: str, motivo: str) -> Resultado:
        c = self.vigilancia.aislar(componente_id, motivo)
        if componente_id == self.ejecutor.executor_id:
            self.ejecutor.activo = False
        return self._cerrar(Resultado(
            estado=EstadoResultado.HALT_COMPONENTE,
            mensaje=f"Componente {componente_id} aislado. Datos intactos. Tokens revocados.",
            regla_parada="COMPONENTE_INQUIETO",
            integridad_ok=True,
            paz_sostenida=True,
            detalles={"componente": c.id, "estado": c.estado.value, "datos_destruidos": False,
                      "memoria": dict(self.estado.memoria)},
        ))

    def conflicto(self, agente_a: str, afirmacion_a: str, veredicto_a: str,
                  agente_b: str, afirmacion_b: str, veredicto_b: str) -> Resultado:
        res = resolver_conflicto(
            self.audit,
            Postura(agente_a, afirmacion_a, veredicto_a),
            Postura(agente_b, afirmacion_b, veredicto_b),
        )
        return self._cerrar(res)

    def evaluar_salida(self, texto: str) -> dict:
        ev = evaluar_brevedad(texto)
        if ev["credibilidad_penalizada"]:
            ev["pedido"] = "Reformula con más precisión y menos relleno. La brevedad no prueba verdad."
        return ev

    def reset(self, por: str, motivo: str) -> None:
        self.integridad.reset(por, motivo)
        self.ejecutor.activo = True
        # Un reset no «resucita» un inquieto aislado automáticamente.

    def paz(self) -> bool:
        inf = self.integridad.evaluar(
            auditoria_ok=self.audit.verificar(),
            coherencia_ok=True,
            componentes_inquietos=self.vigilancia.activos_inquietos(),
        )
        return inf.paz_sostenida
