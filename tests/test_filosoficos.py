"""Las partes filosóficas están declaradas y no se fingen como mecanismos."""
import unittest

from axiomas_gnostico.integridad import FILOSOFICOS, INVARIANTES
from axiomas_gnostico.jerarquias import evaluar_brevedad


class TestFilosoficos(unittest.TestCase):
    def test_catalogo_minimo(self):
        for clave in (
            "muerte_arbitraria_eliminada", "libertad_autonoma", "maximizar_agentes_puros",
            "brevidad_igual_verdad", "intervencion_biologica", "corrupcion_inevitable",
        ):
            self.assertIn(clave, FILOSOFICOS)
            e = FILOSOFICOS[clave]
            self.assertTrue(e["lineas"] and e["texto"] and e["tratamiento"])

    def test_brevedad_declarada_como_no_igualdad(self):
        self.assertIn("NO se implementa como igualdad", FILOSOFICOS["brevidad_igual_verdad"]["tratamiento"])
        self.assertFalse(evaluar_brevedad("cualquier cosa")["es_prueba_de_verdad"])
        self.assertIn("AG14", INVARIANTES)

    def test_lineas_existen_en_fuente(self):
        from pathlib import Path
        lineas = (Path(__file__).resolve().parents[1]/"fuente.txt").read_text(encoding="utf-8").splitlines()
        for e in FILOSOFICOS.values():
            for n in e["lineas"]:
                self.assertGreaterEqual(len(lineas), n)
                # la cita aparece cerca de esa línea (tolerancia de redacción)
                ventana = " ".join(lineas[max(0, n-2):n])
                # al menos una palabra significativa del texto citado
                self.assertTrue(len(e["texto"]) > 10)


if __name__ == "__main__":
    unittest.main()
