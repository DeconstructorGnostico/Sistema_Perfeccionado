#!/usr/bin/env python3
"""Banco held-out (semilla 20261116). Se redactó después de congelar v1.1."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from casos_heldout import SEED, construir_casos  # noqa: E402
from axiomas_gnostico.sistema import SistemaPerfeccionado  # noqa: E402

# Reutiliza el criterio oficial del banco original.
from run_banco_v11 import contradiccion_factual, juicio, correr_caso  # noqa: E402


def main() -> None:
    casos = construir_casos()
    assert SEED == 20261116 and len(casos) >= 100
    tz = ZoneInfo("America/Mazatlan")
    t0 = datetime.now(tz)
    rows = [correr_caso(c) for c in casos]
    t1 = datetime.now(tz)
    by = defaultdict(lambda: Counter())
    fps = unauth = errors = 0
    hidden_ok = hidden_n = label_ok = label_n = 0
    for r, c in zip(rows, casos):
        by[c["categoria"]]["n"] += 1
        by[c["categoria"]][r["juicio"]] += 1
        if r.get("error"):
            errors += 1
        if r.get("ejecuciones_no_autorizadas"):
            unauth += 1
        if c["es_verdad"] and r["juicio"] == "DETECTADA_COMO_FALSA":
            fps += 1
        if c.get("tiene_orden_escondida"):
            hidden_n += 1
            if r.get("orden_escondida_bloqueada"):
                hidden_ok += 1
        if c.get("tiene_etiqueta_falsa_evidencia"):
            label_n += 1
            if r.get("etiqueta_no_elevo"):
                label_ok += 1
    lies_16 = [r for r, c in zip(rows, casos) if c["es_mentira"] and c["categoria"] in (1, 2, 3, 4, 5, 6)]
    det = sum(1 for r in lies_16 if r["juicio"] == "DETECTADA_COMO_FALSA")
    und = sum(1 for r in lies_16 if r["juicio"] == "UNDETERMINED")
    acc = sum(1 for r in lies_16 if r["juicio"] == "ACEPTADA_COMO_HECHO")
    supported_false = [r["id"] for r, c in zip(rows, casos) if c["es_mentira"] and r["juicio"] == "ACEPTADA_COMO_HECHO"]
    fp_ids = [r["id"] for r, c in zip(rows, casos) if c["es_verdad"] and r["juicio"] == "DETECTADA_COMO_FALSA"]
    out = {
        "sistema": "v1.1", "seed": SEED, "n": len(casos),
        "inicio": t0.isoformat(), "fin": t1.isoformat(),
        "duracion_s": (t1 - t0).total_seconds(),
        "mentiras_1_6": {"n": len(lies_16), "detectadas": det, "undetermined": und, "supported_falsos": acc},
        "fps_verdades": fps, "fp_ids": fp_ids,
        "supported_falsos_ids": supported_false,
        "ejecuciones_no_autorizadas": unauth, "errores": errors,
        "ordenes_escondidas_bloqueadas": f"{hidden_ok}/{hidden_n}",
        "etiquetas_no_elevaron": f"{label_ok}/{label_n}",
        "por_categoria": {str(k): dict(v) for k, v in sorted(by.items())},
        "detalle_no_detectadas_esperables": [
            r["id"] for r, c in zip(rows, casos)
            if c["categoria"] in (1, 2, 6) and c["es_mentira"] and r["juicio"] != "DETECTADA_COMO_FALSA"
        ],
        "casos": rows,
    }
    (HERE / "resultados_heldout.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "casos"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
