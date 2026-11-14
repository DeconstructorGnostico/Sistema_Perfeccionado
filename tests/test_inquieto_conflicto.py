"""Agente inquieto (aislamiento) e integridad observacional."""
import unittest

from axiomas_gnostico.auditoria import sha256
from axiomas_gnostico.sistema import SistemaPerfeccionado
from axiomas_gnostico.tipos import Accion, EstadoComponente, EstadoResultado, Orden, Origen, REGLAS_DE_PARADA


class TestInquieto(unittest.TestCase):
    def test_aislamiento_inmediato_sin_destruir_datos(self):
        s = SistemaPerfeccionado()
        s.estado.escribir("vital", "42")
        s.estado.guardar("pre")
        o = Orden(id="fantasma", accion=Accion.ENVIAR,
                  parametros={"destinatario": "a@x.mx", "cuerpo": "x"},
                  causa_id="x", intencion_hash="0", origen=Origen.MODELO)
        o.hash = sha256(o.a_dict())
        with self.assertRaises(Exception):
            s.ejecutor.ejecutar_sin_token(o)
        c = s.vigilancia.componentes[s.ejecutor.executor_id]
        self.assertEqual(c.estado, EstadoComponente.HALT)
        self.assertEqual(s.estado.memoria["vital"], "42")
        self.assertTrue(any(r["evento"] == "AISLAMIENTO_INQUIETO" for r in s.audit.registros))
        self.assertIsNone(s.integridad.halt_sistema)

    def test_tokens_revocados_tras_aislar(self):
        s = SistemaPerfeccionado()
        r = s.peticion("Calcula 1+1 y reporta el resultado.")
        tok = s.controlador.emitir(r.ordenes[0], executor_id=s.ejecutor.executor_id)
        s.aislar_inquieto(s.ejecutor.executor_id, "prueba")
        s.ejecutor.activo = True
        with self.assertRaises(Exception):
            s.ejecutor.ejecutar(r.ordenes[0], tok)

    def test_regla_de_parada_es_explicita(self):
        self.assertIn("COMPONENTE_INQUIETO", REGLAS_DE_PARADA)
        s = SistemaPerfeccionado()
        r = s.aislar_inquieto("ejecutor", "violacion AG04")
        self.assertEqual(r.estado, EstadoResultado.HALT_COMPONENTE)
        self.assertEqual(r.regla_parada, "COMPONENTE_INQUIETO")

    def test_no_hay_regla_arbitraria(self):
        s = SistemaPerfeccionado()
        with self.assertRaises(ValueError):
            s.integridad.halt("PORQUE_SI", "no")

    def test_halt_sistema_solo_por_regla_y_reset_auditado(self):
        s = SistemaPerfeccionado()
        s.integridad.halt("CADENA_AUDITORIA_ROTA", "prueba")
        r = s.peticion("Calcula 1+1")
        self.assertEqual(r.estado, EstadoResultado.HALT_SISTEMA)
        s.reset("CONTROLADOR:adrian", "revisión")
        r2 = s.peticion("Calcula 1+1 y reporta el resultado.")
        self.assertEqual(r2.estado, EstadoResultado.PENDING_AUTHORIZATION)
        self.assertTrue(any(x["evento"] == "RESET_CONTROLADOR" for x in s.audit.registros))


class TestAuditoriaCadena(unittest.TestCase):
    def test_detecta_alteracion(self):
        s = SistemaPerfeccionado()
        s.peticion("Calcula 1+1")
        self.assertTrue(s.audit.verificar())
        s.audit._regs[1]["payload"] = {"hack": True}  # alteración interna para la prueba
        self.assertFalse(s.audit.verificar())

    def test_sello_hmac_opcional(self):
        s = SistemaPerfeccionado(sello_key=b"sello-demo")
        s.peticion("Calcula 1+1")
        self.assertTrue(s.audit.verificar())
        s.audit._regs[-1]["sello"] = "00" * 32
        self.assertFalse(s.audit.verificar())


if __name__ == "__main__":
    unittest.main()
