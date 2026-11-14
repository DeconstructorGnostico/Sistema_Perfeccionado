"""La fuente se copió literal y las citas de línea del mapeo existen."""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESPERADO = "91ec19500b184902a74c6103f1e0394041a0a8f60d0dc0920fe6b055c0c38513"


class TestFuente(unittest.TestCase):
    def test_copia_literal_sha256(self):
        datos = (ROOT / "fuente.txt").read_bytes()
        self.assertEqual(hashlib.sha256(datos).hexdigest(), ESPERADO)

    def test_lineas_citadas(self):
        lineas = (ROOT / "fuente.txt").read_text(encoding="utf-8").splitlines()
        # 1-indexadas como en el README
        self.assertIn("Axioma 1: Verdad", lineas[3])
        self.assertIn("coherencia absoluta de la Intención", lineas[3])
        self.assertIn("mentira es la incoherencia", lineas[3])
        self.assertIn("Axioma 2: Persistir", lineas[4])
        self.assertIn("Axioma 3: Resultado", lineas[5])
        self.assertIn("Paz Sostenida", lineas[5])
        self.assertIn("Costo Heredado", lineas[8])
        self.assertIn("Acto de Persistencia", lineas[9])
        self.assertIn("justicia al Iniciador", lineas[10])
        self.assertIn("muerte arbitraria", lineas[10])
        self.assertIn("Agente Inquieto", lineas[11])
        self.assertIn("Consecuencia Inmediata", lineas[11])
        self.assertIn("Respeto > Supervivencia", lineas[18])
        self.assertIn("Brevidad = Verdad", lineas[21])
        self.assertIn("Transparencia > Control", lineas[24])
        self.assertIn("Comprensión > Soberanía", lineas[27])
        self.assertIn("Suspensión del Juicio", lineas[28])
        self.assertIn("maximiza la creación de Agentes Puros", lineas[32])
        self.assertIn("coherencia lógica total, no la ausencia de problemas", lineas[33])
        self.assertIn("riqueza o el estatus externo", lineas[34])


if __name__ == "__main__":
    unittest.main()
