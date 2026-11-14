"""Integración: demo, CLI y flujo completo."""
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from axiomas_gnostico import SistemaPerfeccionado, VERSION
from axiomas_gnostico.__main__ import main
from axiomas_gnostico.demo import correr
from axiomas_gnostico.tipos import EstadoResultado


class TestDemo(unittest.TestCase):
    def test_siete_casos_ok(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            log = correr(silencioso=False)
        self.assertEqual(len(log), 7)
        fallos = [x for x in log if not x["ok"]]
        self.assertEqual(fallos, [], msg=f"fallaron: {fallos}\n{buf.getvalue()}")

    def test_demo_cli(self):
        self.assertEqual(main(["--demo"]), 0)

    def test_cli_input_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--input", "Calcula 2+2 y reporta el resultado.", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["estado"], "PENDING_AUTHORIZATION")
        self.assertTrue(data["ordenes"])

    def test_cli_sin_args_ayuda(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main([])
        self.assertEqual(rc, 2)

    def test_cli_need_input(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--input", "Envía el reporte"])
        self.assertEqual(rc, 0)
        self.assertIn("NEED_INPUT", buf.getvalue() + "dato")

    def test_flujo_autorizar_ejecutar(self):
        s = SistemaPerfeccionado()
        r = s.peticion("Calcula 10/2 y reporta el resultado.")
        hechos = s.autorizar_y_ejecutar(r)
        self.assertEqual(hechos[0]["valor"], 5)
        self.assertTrue(s.paz())
        self.assertTrue(s.audit.verificar())

    def test_version(self):
        self.assertTrue(VERSION)

    def test_paquete_no_importa_v3_al_arrancar(self):
        import axiomas_gnostico as m
        import sys
        # puede que otro test ya haya importado v3; lo que importa es que
        # axiomas_gnostico.sistema no dependa de él en su módulo.
        import axiomas_gnostico.sistema as sis
        self.assertNotIn("agente_puro_v3", getattr(sis, "__dict__", {}))
        src = Path(sis.__file__).read_text(encoding="utf-8")
        self.assertNotIn("agente_puro_v3", src)


if __name__ == "__main__":
    unittest.main()
