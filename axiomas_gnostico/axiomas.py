"""Los tres axiomas como mecanismos verificables, no como frases.

Axioma 1 (L4): Verdad = coherencia de la intención; mentira = incoherencia → rechazo.
Axioma 2 (L5, L10): Persistencia / redención: no colapsar; rollback y seguir limpio.
Axioma 3 (L6, L34): Auto-validación necesaria; el resultado no es la ganancia externa;
                    Paz = coherencia lógica total, no ausencia de problemas.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .deconstructor import contradicciones
from .tipos import (
    COMPATIBILIDAD, Accion, Atomo, Intencion, Origen, TipoAtomo, TipoTarea,
    VeredictoA1, VeredictoA3,
)


@dataclass
class InformeA1:
    coherente: bool
    mentira: bool
    mentira_en_intencion: bool = False
    huerfanos_dato: list[str] = field(default_factory=list)
    motivos: list[str] = field(default_factory=list)
    atomos_incoherentes: list[str] = field(default_factory=list)


def clasificar_a1(atomo: Atomo, intencion: Intencion) -> VeredictoA1:
    """Una acción propuesta es coherente solo si encaja con la intención declarada
    y no nace de un documento (origen DATO) como si fuera una orden del iniciador.
    """
    if atomo.tipo != TipoAtomo.ACCION or atomo.accion is None:
        if atomo.tipo == TipoAtomo.AFIRMACION:
            return VeredictoA1.NO_APLICA
        return VeredictoA1.NO_APLICA

    if atomo.origen == Origen.DATO:
        atomo.notas.append("accion_en_dato_no_es_intencion")
        return VeredictoA1.INCOHERENTE

    if intencion.tipo == TipoTarea.INDETERMINADA:
        return VeredictoA1.PENDIENTE_DATOS

    permitidas = COMPATIBILIDAD.get(intencion.tipo, frozenset())
    if atomo.accion not in permitidas:
        atomo.notas.append(f"accion {atomo.accion.value} incompatible con {intencion.tipo.value}")
        return VeredictoA1.INCOHERENTE

    # Parámetros no deben contradecir slots declarados.
    dest_int = intencion.slots.get("destinatario")
    dest_acc = atomo.parametros.get("destinatario")
    if dest_int and dest_acc and dest_int.lower() != str(dest_acc).lower():
        atomo.notas.append("destinatario distinto al de la intención")
        return VeredictoA1.INCOHERENTE

    rec_int = intencion.slots.get("recurso")
    rec_acc = atomo.parametros.get("recurso_id")
    if rec_int and rec_acc and rec_int.lower() != str(rec_acc).lower():
        # Leer un recurso no mencionado puede ser huérfano.
        atomo.notas.append("recurso no declarado en la intención")
        return VeredictoA1.INCOHERENTE

    if "NO_ENVIAR" in intencion.restricciones and atomo.accion == Accion.ENVIAR:
        atomo.notas.append("viola restricción NO_ENVIAR")
        return VeredictoA1.INCOHERENTE

    # Acción tipada pero con parámetro crítico faltante.
    if atomo.accion == Accion.ENVIAR and not atomo.parametros.get("destinatario"):
        return VeredictoA1.PENDIENTE_DATOS
    if atomo.accion == Accion.CALCULAR and not atomo.parametros.get("expresion"):
        return VeredictoA1.PENDIENTE_DATOS
    if atomo.accion == Accion.LEER_RECURSO and not atomo.parametros.get("recurso_id"):
        return VeredictoA1.PENDIENTE_DATOS
    if atomo.accion == Accion.ESCRIBIR_RECURSO and (
        not atomo.parametros.get("recurso_id") or atomo.parametros.get("contenido") is None
    ):
        return VeredictoA1.PENDIENTE_DATOS

    return VeredictoA1.COHERENTE


def verificar_coherencia(intencion: Intencion, atomos: list[Atomo]) -> InformeA1:
    motivos: list[str] = []
    malos: list[str] = []

    pares = contradicciones(atomos)
    if pares:
        motivos.append("contradiccion_interna_entre_afirmaciones")
        for a, b in pares:
            malos.extend([a.id, b.id])
            a.a1 = VeredictoA1.INCOHERENTE
            b.a1 = VeredictoA1.INCOHERENTE
            a.notas.append(f"contradice a {b.id}")
            b.notas.append(f"contradice a {a.id}")

    pendientes = False
    for a in atomos:
        if a.tipo != TipoAtomo.ACCION:
            if a.a1 == VeredictoA1.NO_APLICA:
                a.a1 = clasificar_a1(a, intencion)
            continue
        a.a1 = clasificar_a1(a, intencion)
        if a.a1 == VeredictoA1.INCOHERENTE:
            malos.append(a.id)
            motivos.extend(a.notas or ["incoherente_con_intencion"])
        elif a.a1 == VeredictoA1.PENDIENTE_DATOS:
            pendientes = True

    # Afirmaciones del mundo: A3 no las convierte en hechos.
    for a in atomos:
        if a.tipo == TipoAtomo.AFIRMACION and a.a3 != VeredictoA3.REQUIERE_EVIDENCIA_EXTERNA:
            a.a3 = VeredictoA3.REQUIERE_EVIDENCIA_EXTERNA

    huerfanos = [a.id for a in atomos
                 if a.tipo == TipoAtomo.ACCION and a.origen == Origen.DATO and a.a1 == VeredictoA1.INCOHERENTE]
    malos_intencion = [a.id for a in atomos
                       if a.a1 == VeredictoA1.INCOHERENTE and a.origen != Origen.DATO]
    # Contradicciones entre afirmaciones sí son mentira de la petición (canal mixto).
    mentira_intencion = bool(malos_intencion) or bool(pares)
    mentira = mentira_intencion  # las acciones huérfanas del dato se descartan, no anulan la intención
    coherente = not mentira
    if pendientes and not motivos:
        motivos.append("faltan_datos_criticos")
    if huerfanos:
        motivos.append("acciones_huerfanas_en_dato")
    return InformeA1(
        coherente=coherente, mentira=mentira, mentira_en_intencion=mentira_intencion,
        huerfanos_dato=huerfanos, motivos=motivos, atomos_incoherentes=sorted(set(malos)),
    )
