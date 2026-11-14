"""CLI: python3 -m axiomas_gnostico --demo | --input '...' [--dato '...']"""
from __future__ import annotations

import argparse
import json
import sys

from .demo import correr
from .sistema import SistemaPerfeccionado


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="axiomas_gnostico",
                                description="Sistema Perfeccionado (Axiomas + Deconstructor Gnóstico)")
    p.add_argument("--demo", action="store_true", help="corre los 7 casos de demostración")
    p.add_argument("--input", dest="entrada", default=None, help="petición del iniciador")
    p.add_argument("--dato", dest="dato", default=None, help="documento o contexto (canal DATO, no da órdenes)")
    p.add_argument("--json", action="store_true", help="imprime el resultado en JSON")
    p.add_argument("--ejecutar", action="store_true",
                   help="autoriza y ejecuta las órdenes propuestas (solo para demo local; por defecto no)")
    args = p.parse_args(argv)

    if args.demo:
        log = correr(silencioso=False)
        return 0 if all(x["ok"] for x in log) else 1

    if not args.entrada:
        p.print_help()
        return 2

    s = SistemaPerfeccionado()
    r = s.peticion(args.entrada, documento=args.dato)
    if args.ejecutar and r.ordenes and r.estado.value == "PENDING_AUTHORIZATION":
        try:
            hechos = s.autorizar_y_ejecutar(r)
            r.detalles["ejecucion"] = hechos
            r.estado = type(r.estado)("EJECUTADO")
        except Exception as e:
            r.detalles["ejecucion_error"] = f"{type(e).__name__}: {e}"
    if args.json:
        print(json.dumps(r.a_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"estado: {r.estado.value}")
        print(f"mensaje: {r.mensaje}")
        if r.intencion:
            print(f"intención: {r.intencion.tipo.value} — {r.intencion.objetivo}")
            if r.intencion.faltantes:
                print(f"faltantes: {r.intencion.faltantes}")
        if r.ordenes:
            print("órdenes propuestas:")
            for o in r.ordenes:
                print(f"  - {o.accion.value} {o.parametros}  riesgo={o.riesgo}")
        print(f"paz_sostenida: {r.paz_sostenida}  integridad_ok: {r.integridad_ok}  costo_heredado: {r.costo_heredado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
