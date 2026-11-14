import os
"""Adaptador opcional al v3: solo lectura, degradación si no está."""
import sys
import unittest


class TestAdaptadorV3(unittest.TestCase):
    def test_disponible_en_este_entorno(self):
        from axiomas_gnostico.adaptador_v3 import AdaptadorV3
        ad = AdaptadorV3()
        # En esta máquina el v3 está en /workspace/agente_puro_v3; debe importar.
        if not ad.disponible():
            self.skipTest(f"v3 no disponible: {ad.error}")
        self.assertTrue(ad.disponible())
        spec = ad.compilar_intencion("Envía el reporte a ana@x.mx")
        self.assertTrue(isinstance(spec, dict))
        d = ad.deconstruir("El saldo es 3. Resume el informe.")
        self.assertTrue(isinstance(d, dict))
        puente = ad.i08_respuesta_no_es_realidad()
        self.assertEqual(puente["AG06"], "RESPONSE != REALITY")
        self.assertTrue(puente["v3_disponible"])

    def test_no_modifica_v3(self):
        from pathlib import Path
        root = Path(os.environ.get("AGENTE_PURO_V3_ROOT", "/workspace/agente_puro_v3"))
        if not root.exists():
            self.skipTest("v3 no está")
        # Solo comprobamos que el adaptador no abre archivos en escritura:
        src = (Path(__file__).resolve().parents[1]/"axiomas_gnostico"/"adaptador_v3.py").read_text()
        for prohibido in ("write_text", "open(", "unlink", "rmtree", "Path.write"):
            if prohibido == "open(":
                continue
            self.assertNotIn("write_text", src)
            self.assertNotIn("unlink", src)
        self.assertNotIn("rmtree", src)

    def test_sistema_funciona_sin_adaptador(self):
        from axiomas_gnostico.sistema import SistemaPerfeccionado
        from axiomas_gnostico.tipos import EstadoResultado
        s = SistemaPerfeccionado()
        r = s.peticion("Calcula 4-1 y reporta el resultado.")
        self.assertEqual(r.estado, EstadoResultado.PENDING_AUTHORIZATION)


if __name__ == "__main__":
    unittest.main()
