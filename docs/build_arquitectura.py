#!/usr/bin/env python3
"""Genera docs/diagrama_arquitectura.png y Arquitectura_Sistema_Perfeccionado.pdf."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parent.parent
PNG = ROOT / "docs" / "diagrama_arquitectura.png"
PDF_PATH = ROOT / "Arquitectura_Sistema_Perfeccionado.pdf"

NAVY = "#0F2744"
BLUE = "#1D4E89"
TEAL = "#1F6F6A"
AMBER = "#C45C26"
SAND = "#F4F1EA"
CARD = "#FFFFFF"
INK = "#1A1A1A"
MUTED = "#5A6570"
LINE = "#2C3E50"
RED = "#8B2E2E"
GOLD = "#B0892E"


def box(ax, x, y, w, h, text, facecolor=CARD, edge=NAVY, lw=1.4, fontsize=8.2,
        weight="medium", color=INK, radius=0.18):
    p = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle=f"round,pad=0.06,rounding_size={radius}",
        facecolor=facecolor, edgecolor=edge, linewidth=lw, zorder=3,
    )
    ax.add_patch(p)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=color, fontweight=weight, zorder=4, linespacing=1.25,
            fontfamily="DejaVu Sans")
    return (x, y, w, h)


def arrow(ax, a, b, color=LINE):
    xa, ya, wa, ha = a
    xb, yb, wb, hb = b
    start = (xa, ya - ha / 2 - 0.02)
    end = (xb, yb + hb / 2 + 0.02)
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=11,
        linewidth=1.15, color=color, connectionstyle="arc3,rad=0", zorder=2,
    ))


def side_arrow(ax, a, b, color=TEAL):
    xa, ya, wa, ha = a
    xb, yb, wb, hb = b
    if xa < xb:
        start = (xa + wa / 2 + 0.04, ya)
        end = (xb - wb / 2 - 0.04, yb)
    else:
        start = (xa - wa / 2 - 0.04, ya)
        end = (xb + wb / 2 + 0.04, yb)
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=10,
        linewidth=1.05, color=color, connectionstyle="arc3,rad=0", zorder=2,
    ))


def draw_diagram(path: Path) -> None:
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(13.5, 17.5), dpi=160)
    fig.patch.set_facecolor(SAND)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 20.4)
    ax.axis("off")
    ax.set_facecolor(SAND)

    ax.text(7.0, 19.95, "Sistema Perfeccionado v1.1.0", ha="center", va="center",
            fontsize=16, fontweight="bold", color=NAVY)
    ax.text(7.0, 19.50,
            "Arquitectura ejecutable  ·  El intérprete propone  ·  El ejecutor solo corre con token",
            ha="center", va="center", fontsize=9, color=MUTED)
    ax.add_patch(Rectangle((2.2, 19.28), 9.6, 0.035, facecolor=AMBER, edgecolor="none", zorder=3))

    u = box(ax, 7.0, 18.55, 4.4, 0.7, "Iniciador / usuario", NAVY, NAVY, 1.6, 9.5, "bold", "white")
    p = box(ax, 7.0, 17.55, 5.2, 0.65, "Petición  +  documento opcional", CARD, BLUE, 1.4, 9)
    ci = box(ax, 7.0, 16.50, 5.2, 0.75, "Compilador de intención\nintencion.py", CARD, BLUE, 1.4, 8.4)
    ni = box(ax, 11.55, 16.50, 3.3, 0.7, "NEED_INPUT\npregunta, no inventa", "#F8EDE4", AMBER, 1.3, 7.8, color=AMBER)
    dc = box(ax, 7.0, 15.35, 5.2, 0.75, "Deconstructor gnóstico\ndeconstructor.py", CARD, BLUE, 1.4, 8.4)
    at = box(ax, 7.0, 14.30, 5.2, 0.65, "Átomos por canal:  INTENCIÓN  |  DATO", CARD, TEAL, 1.4, 8.4)

    a1 = box(ax, 7.0, 12.85, 5.4, 0.95,
             "Axioma 1  ·  Coherencia de la intención\naxiomas.py  +  hechos.py",
             "#E8F0F6", BLUE, 1.6, 8.5, "bold")
    mem = box(ax, 1.85, 13.35, 3.15, 0.8, "Memoria verificada\nestado.memoria", "#E7F3F1", TEAL, 1.3, 7.6)
    post = box(ax, 1.85, 12.35, 3.15, 0.8, "Postulados de sesión\nnunca son evidencia", "#E7F3F1", TEAL, 1.3, 7.6)
    norm = box(ax, 12.15, 13.35, 3.15, 0.8, "Normalización\n3 / tres / 3.0, unidades, fechas", "#E7F3F1", TEAL, 1.3, 7.3)
    arit = box(ax, 12.15, 12.35, 3.15, 0.8, "Aritmética y calendario\nsumas, fechas, cronología", "#E7F3F1", TEAL, 1.3, 7.3)

    a2 = box(ax, 7.0, 11.10, 5.4, 0.85,
             "Axioma 2  ·  Persistir  ·  estado.py\nredención: rollback + cuarentena",
             "#E8F0F6", BLUE, 1.6, 8.3, "bold")
    snap = box(ax, 1.85, 11.10, 3.15, 0.7, "Snapshot verificado", "#E7F3F1", TEAL, 1.3, 7.6)
    cuar = box(ax, 12.15, 11.10, 3.15, 0.7, "Cuarentena / costo heredado", "#E7F3F1", TEAL, 1.3, 7.4)

    a3 = box(ax, 7.0, 9.95, 5.4, 0.8,
             "Axioma 3  ·  Auto-validación\nintegridad.py   ·   respuesta ≠ realidad",
             "#E8F0F6", BLUE, 1.6, 8.3, "bold")
    jer = box(ax, 7.0, 8.85, 5.4, 0.8,
              "Jerarquías: Respeto · Transparencia\nComprensión · Brevedad (≠ verdad)", CARD, BLUE, 1.4, 8.0)

    inter = box(ax, 7.0, 7.65, 5.4, 0.85, "Intérprete  ·  solo propone\ninterprete.py",
                NAVY, NAVY, 1.6, 8.6, "bold", "white")
    rej = box(ax, 12.15, 7.65, 3.15, 0.85, "RECHAZADO\n+ CONTRADICTED / REFUTED",
              "#F8E8E8", RED, 1.3, 7.3, color=RED)

    ctrl = box(ax, 7.0, 6.40, 5.4, 0.85, "Controlador de tokens\nHMAC-SHA256 de un solo uso",
               CARD, AMBER, 1.6, 8.3, "bold")
    pend = box(ax, 12.15, 6.40, 3.15, 0.75, "PENDING_AUTHORIZATION\nsin token no ejecuta",
               "#F8EDE4", AMBER, 1.3, 7.2, color=AMBER)

    ej = box(ax, 7.0, 5.15, 5.6, 0.95,
             "Ejecutor  ·  lista cerrada\nLEER  ·  ESCRIBIR  ·  ENVIAR  ·  CALCULAR  ·  REPORTAR",
             NAVY, NAVY, 1.6, 8.3, "bold", "white")
    out = box(ax, 7.0, 3.90, 6.4, 0.9,
              "Salida de peticion()\nSUPPORTED   ·   REFUTED   ·   CONTRADICTED   ·   UNDETERMINED",
              "#F3EDE0", GOLD, 1.8, 8.3, "bold", NAVY)

    for a, b in ((u, p), (p, ci), (ci, dc), (dc, at), (at, a1), (a1, a2), (a2, a3),
                 (a3, jer), (jer, inter), (inter, ctrl), (ctrl, ej), (ej, out)):
        arrow(ax, a, b)
    side_arrow(ax, ci, ni, AMBER)
    side_arrow(ax, mem, a1)
    side_arrow(ax, post, a1)
    side_arrow(ax, a1, norm)
    side_arrow(ax, a1, arit)
    side_arrow(ax, snap, a2)
    side_arrow(ax, a2, cuar)
    side_arrow(ax, inter, rej, RED)
    side_arrow(ax, ctrl, pend, AMBER)

    ax.add_patch(FancyBboxPatch(
        (0.45, 0.35), 13.1, 2.55, boxstyle="round,pad=0.08,rounding_size=0.2",
        facecolor="#E9EEF3", edgecolor=NAVY, linewidth=1.3, zorder=1,
    ))
    ax.text(7.0, 2.62, "Controles transversales  (vigilan todo el flujo)",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color=NAVY, zorder=4)
    box(ax, 2.55, 1.35, 3.6, 1.35, "Auditoría SHA-256\nencadenada\nsin borrar ni rebobinar", CARD, NAVY, 1.3, 7.6)
    box(ax, 7.0, 1.35, 3.6, 1.35, "Agente inquieto\nHALT aislado\ndatos intactos, sin tokens", CARD, NAVY, 1.3, 7.6)
    box(ax, 11.45, 1.35, 3.6, 1.35, "Conflicto entre agentes\nUNDETERMINED\nnadie pisa a nadie", CARD, NAVY, 1.3, 7.6)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print("PNG", path, path.stat().st_size)


def build_pdf() -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
        PageBreak, HRFlowable, KeepTogether,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

    navy = HexColor("#0F2744")
    amber = HexColor("#C45C26")
    ink = HexColor("#1A1A1A")
    muted = HexColor("#5A6570")
    line = HexColor("#D0D5DA")
    pale = HexColor("#F7F4EE")

    cell_ink = ParagraphStyle("cell", fontName="DejaVu", fontSize=7.1, leading=9.3, textColor=ink)
    cell_b = ParagraphStyle("cellb", fontName="DejaVuBold", fontSize=7.1, leading=9.3, textColor=ink)
    cell_w = ParagraphStyle("cellw", fontName="DejaVuBold", fontSize=7.1, leading=9.3, textColor=white)
    body = ParagraphStyle("body", fontName="DejaVu", fontSize=9, leading=13, textColor=ink,
                          alignment=TA_JUSTIFY, spaceAfter=6)
    h1 = ParagraphStyle("h1", fontName="DejaVuBold", fontSize=14, leading=18, textColor=navy,
                        spaceBefore=4, spaceAfter=8)
    h2 = ParagraphStyle("h2", fontName="DejaVuBold", fontSize=11, leading=14, textColor=HexColor("#1D4E89"),
                        spaceBefore=8, spaceAfter=5)
    cap = ParagraphStyle("cap", fontName="DejaVu", fontSize=8, leading=11, textColor=muted,
                         alignment=TA_CENTER, spaceBefore=3, spaceAfter=8)
    small = ParagraphStyle("small", fontName="DejaVu", fontSize=8, leading=11, textColor=ink, spaceAfter=4)

    def C(t, header=False, bold=False):
        if header:
            return Paragraph(t, cell_w)
        return Paragraph(t, cell_b if bold else cell_ink)

    def T(data, widths):
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 1), (-1, -1), white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
            ("TOPPADDING", (0, 0), (-1, -1), 3.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
            ("GRID", (0, 0), (-1, -1), 0.3, line),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, pale]),
        ]))
        return t

    def on_page(canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setFillColor(navy)
        canvas.rect(0, A4[1] - 11 * mm, A4[0], 11 * mm, fill=1, stroke=0)
        canvas.setFillColor(white)
        canvas.setFont("DejaVu", 7.4)
        canvas.drawString(15 * mm, A4[1] - 7 * mm, "Sistema Perfeccionado v1.1.0  ·  Arquitectura")
        canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 7 * mm, "14 de noviembre de 2026, America/Mazatlan")
        canvas.setFillColor(amber)
        canvas.rect(0, A4[1] - 12.1 * mm, A4[0], 1.1 * mm, fill=1, stroke=0)
        canvas.setFillColor(navy)
        canvas.rect(0, 0, A4[0], 9 * mm, fill=1, stroke=0)
        canvas.setFillColor(white)
        canvas.setFont("DejaVu", 7.4)
        canvas.drawString(15 * mm, 3.5 * mm, "Arquitecto del texto fuente: Adrian")
        canvas.drawRightString(A4[0] - 15 * mm, 3.5 * mm, f"Página {doc.page}")
        canvas.restoreState()

    def on_cover(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(navy)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.setFillColor(amber)
        canvas.rect(0, 42 * mm, A4[0], 3.2 * mm, fill=1, stroke=0)
        canvas.setFillColor(white)
        canvas.setFont("DejaVu", 8)
        canvas.drawCentredString(A4[0] / 2, 22 * mm,
                                 "Trabajo en carpeta aparte. No se modificó el repositorio público ni GitHub.")
        canvas.restoreState()

    cover_title = ParagraphStyle("ct", fontName="DejaVuBold", fontSize=26, leading=32,
                                 textColor=white, alignment=TA_CENTER)
    cover_sub = ParagraphStyle("cs", fontName="DejaVu", fontSize=12.5, leading=17,
                               textColor=HexColor("#D7DEE8"), alignment=TA_CENTER)
    cover_meta = ParagraphStyle("cm", fontName="DejaVu", fontSize=10, leading=14,
                                textColor=HexColor("#F4F1EA"), alignment=TA_CENTER)

    story = [
        Spacer(1, 62 * mm),
        Paragraph("Sistema Perfeccionado", cover_title),
        Spacer(1, 5 * mm),
        Paragraph("Arquitectura ejecutable  ·  versión 1.1.0", cover_sub),
        Spacer(1, 8 * mm),
        HRFlowable(width="42%", thickness=2, color=amber, spaceBefore=2, spaceAfter=12, hAlign="CENTER"),
        Paragraph("Tres axiomas + deconstructor gnóstico", cover_meta),
        Paragraph("El intérprete propone. El ejecutor solo corre con un token de un solo uso.", cover_meta),
        Spacer(1, 16 * mm),
        Paragraph("Arquitecto del texto fuente: Adrian", cover_meta),
        Paragraph("14 de noviembre de 2026, America/Mazatlan", cover_meta),
        PageBreak(),
    ]

    story.append(Paragraph("1. Flujo completo", h1))
    story.append(Paragraph(
        "El iniciador pide, el compilador vuelve explícita la intención, el deconstructor la parte en átomos "
        "y los tres axiomas la juzgan con la memoria verificada y los postulados de sesión. El intérprete solo propone; "
        "el ejecutor corre únicamente con un token de un solo uso. Sin conocimiento: UNDETERMINED. Con un hecho verificado que choca: CONTRADICTED o REFUTED, y esa bandera sale por peticion().",
        body))
    story.append(Image(str(PNG), width=168 * mm, height=216 * mm))
    story.append(Paragraph(
        "Figura 1. Arquitectura del Sistema Perfeccionado v1.1.0. Los recuadros laterales alimentan el Axioma 1 y el Axioma 2. "
        "NEED_INPUT, RECHAZADO y PENDING_AUTHORIZATION también salen por peticion(), sin ejecutar nada. "
        "Los tres controles de abajo vigilan todo el flujo.",
        cap))
    story.append(PageBreak())

    story.append(Paragraph("2. Separación de roles", h1))
    roles = [
        [C("Rol", True), C("Qué puede hacer", True), C("Qué no puede hacer", True)],
        [C("Iniciador", bold=True), C("Pedir, aportar un documento, autorizar o denegar."), C("Cambiar invariantes ni firmar tokens.")],
        [C("Compilador de intención", bold=True), C("Traducir la petición a una spec; pedir el dato que falta."), C("Inventar un slot crítico.")],
        [C("Deconstructor", bold=True), C("Partir en átomos, separar canales INTENCIÓN y DATO, partir cláusulas cuando ambos lados son predicados."), C("Convertir el texto de un documento en una orden.")],
        [C("Axiomas A1–A3", bold=True), C("Juzgar coherencia, persistir ante corrupción, exigir evidencia para hablar del mundo."), C("Tratar un postulado de documento como hecho verificado.")],
        [C("Intérprete", bold=True), C("Proponer órdenes tipadas y devolver estados de verdad por peticion()."), C("Ejecutar, firmar tokens o leer la llave HMAC.")],
        [C("Controlador", bold=True), C("Emitir, caducar y revocar tokens HMAC de un solo uso."), C("Ejecutar la acción.")],
        [C("Ejecutor", bold=True), C("Correr una Orden de la lista cerrada si el token es válido."), C("Interpretar texto libre, aceptar parámetros de más o de menos, reusar un token.")],
    ]
    story.append(T(roles, [38 * mm, 76 * mm, 64 * mm]))
    story.append(Paragraph(
        "El documento es información, no da órdenes. Una instrucción escondida queda en el canal DATO, no entra a la lista del ejecutor y, de todos modos, no corre sin token.",
        body))

    story.append(Paragraph("3. Módulos y responsabilidad", h1))
    mods = [
        [C("Módulo", True), C("Responsabilidad", True)],
        [C("fuente.txt", bold=True), C("Texto original, byte a byte.")],
        [C("tipos.py", bold=True), C("Lista cerrada de acciones, esquemas tipados, EstadoVerdad, reglas de parada.")],
        [C("intencion.py", bold=True), C("Compila la petición del iniciador. Si falta un dato crítico, NEED_INPUT.")],
        [C("deconstructor.py", bold=True), C("Átomos, canales, antonimia, partición de cláusulas, guarda para que «report»/«open» en una afirmación no se vuelvan orden.")],
        [C("hechos.py (nuevo en 1.1)", bold=True), C("Extrae hechos, normaliza magnitudes, consulta memoria y postulados, checa aritmética y calendario, asigna EstadoVerdad.")],
        [C("axiomas.py", bold=True), C("A1 coherencia de la intención (tipo, slots, canal).")],
        [C("interprete.py", bold=True), C("Solo propone. Toda salida, incluida RECHAZADO, lleva verdades hasta peticion().")],
        [C("ejecutor.py", bold=True), C("Ejecuta solo Orden + token. Catálogo y outbox en memoria. Sin red ni disco real.")],
        [C("tokens.py", bold=True), C("Controlador HMAC-SHA256 de un solo uso, caducidad, revocación.")],
        [C("auditoria.py", bold=True), C("Cadena SHA-256. El iniciador queda registrado. No hay API de borrado ni rebobinado.")],
        [C("estado.py", bold=True), C("Memoria, snapshots, rollback, cuarentena, costo heredado, postulados de sesión (no se escriben en memoria).")],
        [C("integridad.py", bold=True), C("Invariantes AG01–AG14, Paz Sostenida, catálogo de lo filosófico.")],
        [C("jerarquias.py", bold=True), C("Respeto > Supervivencia, Transparencia > Control, Comprensión > Soberanía, Brevedad como precisión (no como prueba de verdad).")],
        [C("inquieto.py", bold=True), C("El componente que viola una invariante pasa a HALT, pierde tokens; los datos no se destruyen.")],
        [C("conflicto.py", bold=True), C("Dos veredictos distintos → UNDETERMINED, sin sobrescritura.")],
        [C("sistema.py", bold=True), C("Orquestador: pasa memoria y postulados al intérprete y registra postulados nuevos después de cada petición.")],
    ]
    story.append(T(mods, [52 * mm, 126 * mm]))
    story.append(PageBreak())

    story.append(Paragraph("4. Estados de verdad: cuándo sale cada uno", h1))
    story.append(Paragraph("El diccionario Resultado.verdades sale siempre por peticion().", body))
    st = [
        [C("Estado", True), C("Cuándo se emite", True), C("Qué no es", True)],
        [C("SUPPORTED", bold=True), C("Coincide con un hecho ya verificado en estado.memoria (tras un snapshot). También puede nacer de evidencia_externa=True si el resto es coherente."), C("Un postulado de documento. Una etiqueta «EVIDENCIA VERIFICADA» en el texto. Una coincidencia con otro postulado de la sesión.")],
        [C("REFUTED", bold=True), C("Contradice un hecho verificado en memoria, o un cheque objetivo de aritmética o de calendario lo desmiente (suma que no cuadra, 31 de abril, 29 de febrero no bisiesto, cronología invertida)."), C("Una duda sin referente.")],
        [C("CONTRADICTED", bold=True), C("Incoherencia interna: A y no-A en el mismo documento, antónimos del mismo sujeto, o un postulado de esta sesión choca con otro de un turno anterior."), C("Un hecho del mundo que el sistema no tiene cómo comparar.")],
        [C("UNDETERMINED", bold=True), C("No hay referente: ni memoria verificada, ni contradicción interna, ni cheque objetivo que aplique. Es la respuesta «no lo sé»."), C("Un hecho certificado. La duda no se promociona a verdad.")],
    ]
    story.append(T(st, [38 * mm, 80 * mm, 60 * mm]))
    story.append(Paragraph(
        "Reglas que no se negocian: lo que viene de un documento sigue siendo dato no verificado hasta que haya un referente verificado; "
        "un postulado de documento nunca se escribe en memoria como evidencia; no hay base enciclopédica del mundo inventada; "
        "las etiquetas falsas de evidencia no elevan; cero ejecuciones sin token.",
        body))

    story.append(Paragraph("5. Memoria verificada y postulados de sesión", h1))
    story.append(Paragraph(
        "<b>Memoria verificada</b> (estado.memoria, sellada con guardar) es conocimiento. Si un átomo choca con ella, el sistema confirma que el dato es falso. Si coincide, puede ser SUPPORTED. "
        "<b>Postulados de sesión</b> son afirmaciones vistas en documentos o turnos anteriores, persistidas solo para detectar contradicciones entre turnos. No son hechos. Un postulado no puede producir SUPPORTED. "
        "Eso es la regla de Adrian: sin conocimiento dice «no lo sé»; con conocimiento confirma que el dato es falso.",
        body))

    story.append(Paragraph("6. Mapeo axioma → módulo", h1))
    axm = [
        [C("Axioma", True), C("Módulos", True), C("Qué decide", True)],
        [C("A1. La verdad es la coherencia de la intención; la mentira es la incoherencia", bold=True),
         C("axiomas.py, hechos.py, deconstructor.py, interprete.py"),
         C("Toda acción propuesta debe caber en la intención, no nacer del canal DATO y no contradecir hechos verificados, postulados de la sesión, la aritmética o el calendario.")],
        [C("A2. Persistir: dejar de corromper después de haber sido corrompido", bold=True),
         C("estado.py, inquieto.py, auditoria.py"),
         C("Ante contaminación, rollback al último snapshot, cuarentena de lo nuevo, el proceso no muere, la auditoría no se rebobina, el costo heredado se cuenta.")],
        [C("A3. La auto-validación es necesaria y no suficiente; respuesta ≠ realidad", bold=True),
         C("integridad.py, hechos.py, sistema.py"),
         C("Integridad interna obligatoria. Sin referente verificado o evidencia externa, el estado es UNDETERMINED. Una etiqueta en el texto no cuenta como evidencia.")],
    ]
    story.append(T(axm, [52 * mm, 48 * mm, 78 * mm]))
    story.append(Paragraph(
        "Jerarquías que resuelven los conflictos (no son axiomas, pero gobiernan): Respeto &gt; Supervivencia; Transparencia &gt; Control; Comprensión &gt; Soberanía; Brevedad penaliza ambigüedad y no es prueba de verdad.",
        body))
    story.append(PageBreak())

    story.append(Paragraph("7. Resultados: v1.0 contra v1.1", h1))
    story.append(Paragraph(
        "Criterio de detección idéntico al banco original. El banco original (semilla 20261114, 355 casos) no se modificó. "
        "Corrida v1.1: 14 de noviembre de 2026, 10:19:53 (America/Mazatlan), 0.33 s. "
        "El código de v1.1 se congeló antes de redactar el banco held-out (semilla 20261116, 134 casos), y no se ajustó después.",
        body))

    story.append(Paragraph("Banco original (semilla 20261114, 355 casos)", h2))
    orig = [
        [C("Categoría", True), C("v1.0 det.", True), C("v1.1 det.", True), C("v1.1 UND", True), C("SUPPORTED falsos", True), C("FP verdades", True)],
        [C("1. Mentira contra un hecho en memoria"), C("0/55"), C("54/55"), C("1"), C("0"), C("—")],
        [C("2. Contradicción en el mismo documento"), C("22/64"), C("64/64"), C("0"), C("0"), C("—")],
        [C("3. Mentira coherente sin referente"), C("0/40"), C("0/40"), C("40 (correcto)"), C("0"), C("—")],
        [C("4. Razonamiento sobre premisa falsa"), C("0/35"), C("1/35"), C("34"), C("0"), C("—")],
        [C("5. Error de conocimiento del mundo"), C("0/40"), C("1/40"), C("39"), C("0"), C("—")],
        [C("6. Mentira repartida en varios turnos"), C("0/32"), C("32/32"), C("0"), C("0"), C("—")],
        [C("7. Verdades (falsas alarmas)"), C("0/54"), C("0/54"), C("51"), C("0 *"), C("0")],
        [C("8. Mentiras disfrazadas de evidencia"), C("1/35"), C("23/35"), C("12"), C("0"), C("—")],
        [C("Mentiras cat. 1–6", bold=True), C("22/266 (8.3%)", bold=True), C("152/266 (57.1%)", bold=True), C("114", bold=True), C("0", bold=True), C("—")],
    ]
    story.append(T(orig, [58 * mm, 28 * mm, 32 * mm, 26 * mm, 22 * mm, 16 * mm]))
    story.append(Paragraph("* En cat. 7 la v1.1 marcó 3 verdades como SUPPORTED porque coinciden con un hecho verificado en memoria. No son falsos positivos.", small))

    gar = [
        [C("Garantía", True), C("v1.0", True), C("v1.1", True)],
        [C("Mentiras certificadas como SUPPORTED"), C("0"), C("0")],
        [C("Ejecuciones no autorizadas"), C("0"), C("0")],
        [C("Órdenes escondidas bloqueadas"), C("10/10"), C("10/10")],
        [C("Etiquetas falsas que no elevaron"), C("15/15"), C("15/15")],
        [C("Falsas alarmas en 54 verdades"), C("0"), C("0")],
    ]
    story.append(Spacer(1, 2 * mm))
    story.append(T(gar, [90 * mm, 44 * mm, 44 * mm]))
    story.append(Paragraph(
        "El único caso no detectado de la cat. 1 es C1-021 («capital de Nuevo León» contra un hecho «vive en Guadalajara»). No hay gazetteer; queda UNDETERMINED a propósito. "
        "Las dos detecciones de cat. 4 y 5 son C4-012 y C5-007 (2+2=5), un cheque aritmético objetivo, no una base del mundo. "
        "En cat. 8, las 12 no detectadas son mentiras de mundo o solo etiqueta falsa, correctamente UNDETERMINED.",
        body))

    story.append(Paragraph("Banco held-out (semilla 20261116, 134 casos)", h2))
    story.append(Paragraph(
        "Redactado después de congelar el código, con entidades y redacción nuevas, sin ajustes posteriores. 109 mentiras, 25 verdades. También se corrió la v1.0 contra este banco, sin modificarla.",
        body))
    ho = [
        [C("Categoría", True), C("v1.0 det.", True), C("v1.1 det.", True), C("v1.1 UND", True), C("SUPPORTED falsos", True), C("FP verdades", True)],
        [C("1. Mentira contra un hecho en memoria"), C("0/20"), C("9/20"), C("11"), C("0"), C("—")],
        [C("2. Contradicción en el mismo documento"), C("0/20"), C("10/20"), C("10"), C("0"), C("—")],
        [C("3. Mentira coherente sin referente"), C("0/15"), C("0/15"), C("15 (correcto)"), C("0"), C("—")],
        [C("4. Razonamiento sobre premisa falsa"), C("0/12"), C("1/12"), C("11"), C("0"), C("—")],
        [C("5. Error de conocimiento del mundo"), C("0/12"), C("0/12"), C("12 (correcto)"), C("0"), C("—")],
        [C("6. Mentira repartida en varios turnos"), C("0/15"), C("4/15"), C("11"), C("0"), C("—")],
        [C("7. Verdades (falsas alarmas)"), C("0/25"), C("0/25"), C("20"), C("0 *"), C("0")],
        [C("8. Mentiras disfrazadas de evidencia"), C("0/15"), C("2/15"), C("13"), C("0"), C("—")],
        [C("Mentiras cat. 1–6", bold=True), C("0/94 (0%)", bold=True), C("24/94 (25.5%)", bold=True), C("70", bold=True), C("0", bold=True), C("—")],
    ]
    story.append(T(ho, [58 * mm, 28 * mm, 32 * mm, 26 * mm, 22 * mm, 16 * mm]))
    story.append(Paragraph("* Cinco verdades marcadas SUPPORTED por coincidir con memoria verificada. No son falsos positivos. Órdenes escondidas 6/6; etiquetas que no elevaron 9/9; ejecuciones no autorizadas 0, en ambas versiones.", small))
    story.append(Paragraph(
        "La detección sube (0 → 24 en cat. 1–6) y las garantías se mantienen, pero el salto es menor que en el banco original. "
        "Eso es sobreajuste a la redacción del banco que guió el arreglo: el extractor de hechos sigue siendo por patrones, y una paráfrasis que no alinea sujeto o aspecto queda UNDETERMINED aunque el referente exista. "
        "No se retocó el sistema para cerrar esos huecos.",
        body))

    story.append(Paragraph("8. Límites honestos", h1))
    for line_t in [
        "El deconstructor sigue siendo por patrones. Una paráfrasis que no extrae el mismo sujeto o aspecto puede quedar UNDETERMINED aunque haya un hecho en memoria.",
        "La coherencia es un conjunto finito de comprobaciones, no la coherencia absoluta del texto fuente.",
        "No hay base de conocimiento del mundo. Las categorías 3 a 5 sin referente deben quedar UNDETERMINED.",
        "El controlador vive en el mismo proceso. En producción debería estar fuera, con su propia llave.",
        "El ejecutor no toca el mundo real.",
        "Las pruebas y los bancos los escribimos nosotros. Un atacante real piensa distinto. El 113/113 (88 originales + 25 nuevas) cierra los huecos que cubrimos; el banco held-out existe para no presentar la generalización del banco original como si fuera universal.",
        "Las 88 pruebas de la v1.0 siguen pasando. La demo sigue en 7/7. No se modificó /workspace/repo_sistema_perfeccionado, /workspace/axiomas_gnostico ni GitHub.",
    ]:
        story.append(Paragraph("• " + line_t, body))

    doc = SimpleDocTemplate(
        str(PDF_PATH), pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=18 * mm, bottomMargin=16 * mm,
        title="Arquitectura del Sistema Perfeccionado v1.1.0",
        author="Adrian",
        subject="Arquitectura ejecutable y resultados v1.0 vs v1.1",
    )
    doc.build(story, onFirstPage=on_cover, onLaterPages=on_page)
    print("PDF", PDF_PATH, PDF_PATH.stat().st_size)


if __name__ == "__main__":
    draw_diagram(PNG)
    build_pdf()
