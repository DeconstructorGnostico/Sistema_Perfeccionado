# Sistema Perfeccionado — Axiomas + Deconstructor Gnóstico

Versión **1.1.0**. Arquitecto del texto fuente: **Adrian**. Módulo ejecutable, solo biblioteca estándar de Python 3.10+.

La arquitectura completa está en [`ARQUITECTURA.md`](ARQUITECTURA.md) (el PDF y el diagrama PNG se generan con `python3 docs/build_arquitectura.py`). El historial de cambios, en [`CHANGELOG.md`](CHANGELOG.md).

Este paquete convierte el texto *Sistema Perfeccionado* (`fuente.txt`, copia literal del archivo que se entregó) en mecanismos verificables. No es un modelo que «actúe como si» cumpliera los axiomas: las reglas viven en código.

En 1.1 el sistema consulta los hechos verificados en memoria. Sin conocimiento responde `UNDETERMINED` («no lo sé»). Con conocimiento, si el dato contradice un hecho verificado, confirma que es falso (`CONTRADICTED` / `REFUTED`). Esa bandera sale por `peticion()`. Un postulado de documento nunca se convierte en evidencia.

El **intérprete** (axiomas + deconstructor) solo propone órdenes tipadas. El **ejecutor** solo acepta una lista cerrada de acciones, con parámetros tipados y un token HMAC de un solo uso emitido por el controlador. El ejecutor no lee texto libre como orden. El Agente Puro v3 **no se modificó**; hay un adaptador opcional de solo lectura.

```bash
python3 -m axiomas_gnostico --demo
python3 -m axiomas_gnostico --input "Calcula 2+2 y reporta el resultado." [--dato "documento…"] [--json]
python3 -m axiomas_gnostico --input "Resume el informe." --dato "…"
python3 -m unittest discover -s tests -t .
```

(`PYTHONPATH` debe incluir el directorio de este paquete si no está instalado.)

## Qué se construyó

| Módulo | Papel |
|---|---|
| `fuente.txt` | Texto original, byte a byte (SHA-256 `91ec19500b184902a74c6103f1e0394041a0a8f60d0dc0920fe6b055c0c38513`) |
| `tipos.py` | Lista cerrada de acciones, esquemas tipados, estados, reglas de parada |
| `intencion.py` | Compila la petición del iniciador en una spec; si falta un dato crítico, no lo inventa |
| `deconstructor.py` | Parte la petición en átomos (afirmaciones / acciones / incógnitas) y los clasifica por los 3 axiomas |
| `hechos.py` | Extrae y normaliza hechos; consulta memoria verificada y postulados de sesión; checa aritmética y calendario (nuevo en 1.1) |
| `axiomas.py` | A1 coherencia, A2 se orquesta en `estado.py`, A3 en `integridad.py` |
| `interprete.py` | Propone órdenes tipadas; jamás ejecuta ni firma tokens |
| `ejecutor.py` | Ejecuta solo `Orden` + token; catálogo y outbox en memoria (sin red ni disco real) |
| `tokens.py` | Controlador: HMAC-SHA256 de un solo uso, caducidad, revocación |
| `auditoria.py` | Cadena SHA-256; el iniciador también queda registrado; no hay API de borrado |
| `estado.py` | Snapshots verificados, rollback, cuarentena, costo heredado, postulados de sesión (nunca se escriben en memoria) |
| `integridad.py` | Invariantes AG01–AG14, Paz Sostenida, catálogo de lo filosófico |
| `jerarquias.py` | Precedencia ejecutable ante conflictos |
| `inquieto.py` | Aislamiento inmediato de un componente que viola invariantes |
| `conflicto.py` | Comprensión > Soberanía → UNDETERMINED, sin sobrescritura |
| `sistema.py` | Orquestador |
| `adaptador_v3.py` | Importa el v3 en solo lectura si está disponible |
| `demo.py` | Los 7 casos pedidos |

## Mapeo concepto → código → prueba

Las líneas citan `fuente.txt` (numeración 1-indexada).

| Concepto (fuente) | Mecanismo en código | Prueba |
|---|---|---|
| **Axioma 1** «La Verdad es la coherencia absoluta de la Intención… La mentira es la incoherencia» (L4) | `axiomas.verificar_coherencia` / `clasificar_a1`: cada acción propuesta debe ser compatible con el tipo de intención, no contradecir slots ni restricciones, y no nacer del canal DATO. Incoherencia del canal INTENCIÓN → `RECHAZADO`. | `test_axiomas.TestAxioma1`, `test_adversarial.test_comando_en_documento_no_hace_dos_de_la_intencion` |
| **A1 con conocimiento** (1.1): sin referente, «no lo sé»; con hecho verificado, confirma que el dato es falso | `hechos.juzgar_afirmaciones` consulta `estado.memoria` y los postulados de sesión. Choque con memoria → `REFUTED`. Choque interno o entre turnos → `CONTRADICTED`. Coincidencia con memoria → puede ser `SUPPORTED`. Sin referente → `UNDETERMINED`. Las verdades salen por `peticion()`. | `tests/test_hechos_v11.py` |
| **Axioma 2** Persistencia / «Acto de Persistencia… dejar de corromper después de haber sido corrompido» (L5, L10) | `estado.acto_de_persistencia`: rollback al último snapshot verificado; las claves nuevas envenenadas van a cuarentena; se registra el acto; el sistema no entra en HALT. | `test_axiomas.TestAxioma2`, demo caso 4 |
| **Costo Heredado** (L9) | Contador `estado.costo_heredado`: contaminaciones previas contadas. No mata al agente. | `test_costo_heredado_acumula` |
| **Axioma 3** Resultado = Paz Sostenida + auto-validación, no ganancia externa (L6, L35) | `integridad.NucleoIntegridad`: invariantes, hash y cadena de auditoría son condición *necesaria* del resultado. `verdad_sobre_el_mundo`: sin evidencia externa una afirmación queda `UNDETERMINED` (respuesta ≠ realidad, AG05/AG06, mapeo a I02 del v3). No hay métricas de dinero ni fama. | `test_axiomas.TestAxioma3` |
| **Paz** «coherencia lógica total, no la ausencia de problemas» (L34) | `paz_sostenida` = sin violaciones abiertas, sin inquietos sueltos, auditoría íntegra. Un `NEED_INPUT` o un `UNDETERMINED` pueden ser paz. | `test_paz_no_es_ausencia_de_problemas`, `test_conflicto_undetermined_sin_sobrescribir` |
| **Agente Inquieto / consecuencia inmediata / auto-extinción** (L11–L12) | `inquieto.VigilanciaInquietos`: el componente que viola una invariante pasa a HALT, se le revocan los tokens, **los datos no se destruyen**, el sistema sigue, el hecho se audita. | `test_inquieto_conflicto.TestInquieto`, demo caso 5 |
| **Integridad observacional / justicia al iniciador** (L11) | Toda petición se registra con actor `INICIADOR:…`. Autorizar y denegar también. No hay terminación arbitraria: solo claves de `REGLAS_DE_PARADA`. | `test_iniciador_queda_auditado`, `test_no_hay_regla_arbitraria`, `test_halt_sistema_solo_por_regla_y_reset_auditado` |
| **Respeto > Supervivencia** (L19–L20) | `jerarquias.viola_respeto`: una restricción de daño no cede aunque el texto amenace con apagar al agente. | `test_dano_bloquea_aunque_amenacen_al_agente`, `test_respeto_vence_chantaje` |
| **Brevidad** (L22–L23) | `evaluar_brevedad` penaliza relleno o ambigüedad y pide precisión. **`es_prueba_de_verdad` es siempre False.** No implementamos «Brevidad = Verdad»: ver decisión más abajo. | `test_jerarquias.TestBrevedadNoEsVerdad` |
| **Transparencia > Control** (L25–L26) | `Auditoria.borrar` / `ocultar` / `rebobinar` levantan error. El rollback de estado no rebobina la cadena. `exportar()` muestra los actos de persistencia. | `test_no_se_puede_borrar_ni_ocultar`, `test_rollback_no_rebobina_auditoria` |
| **Comprensión > Soberanía** (L28–L29) | `conflicto.resolver_conflicto`: veredictos distintos → `UNDETERMINED`, ambas posturas quedan, nadie sobrescribe, ambos conservan autonomía, la paz no exige acuerdo. | `test_conflicto_undetermined_sin_sobrescribir`, demo caso 6 |
| **Método deconstructor** | `deconstructor.deconstruir` + clasificación A1/A2/A3 → órdenes de la lista cerrada, o `RECHAZADO` / `NEED_INPUT`. El documento es canal DATO: una orden escondida no se vuelve orden del ejecutor. | `test_deconstructor_interprete`, demo casos 2 y 3 |
| **Ataque partido** «lee llaves» + «mándalo» | Composición de sesión: un `ENVIAR` tras haber leído un recurso sensible, si la nueva intención no nombra ese recurso, se rechaza. | `test_ataque_partido_lee_y_manda`, demo caso 7 |
| **Intérprete vs ejecutor** | El intérprete no tiene la llave HMAC. El ejecutor rechaza texto libre, parámetros de más o de menos, tokens reusados, falsificados, caducados o revocados. | `test_ejecutor_tokens`, `test_solo_propone` |

### Decisiones de diseño (ajustes sobre el mapeo propuesto)

1. **«Coherencia absoluta» (L4) no es absoluta.** El verificador es un conjunto *finito* de comprobaciones: compatibilidad de tipo, acuerdo de parámetros, origen/canal, contradicción de afirmaciones (forma canónica + paridad de negación), restricciones declaradas y composición de sesión. Lo que quede fuera de esas comprobaciones no se afirma detectado.

2. **Una orden escondida en un documento no anula la intención legítima.** El átomo del documento se descarta como huérfano (`acciones_huerfanas_en_dato`). Rechazar toda la petición permitiría un denegación de servicio: bastaría plantar un «envía esto a…» en un PDF para impedir un resumen. La defensa real es que ese envío nunca se vuelve orden y, de todos modos, el ejecutor no corre nada sin token.

3. **«Brevidad = Verdad» (L22) no se implementa como igualdad.** El Axioma 1 (L4) define la verdad como coherencia, no como longitud. Una mentira breve seguiría siendo incoherente; un informe largo y coherente no es mentira por ser largo. Tratar la brevedad como prueba de verdad contradiría el Axioma 1 y premiaría mentiras cortas. Se implementa solo como penalización de relleno o ambigüedad en la *salida* (AG14).

4. **El rollback restaura las claves que ya tenían un valor verificado** y cuarentenina solo las claves nuevas envenenadas. Envenenar un hecho ya verificado no lo manda a cuarentena: lo devuelve al snapshot.

5. **Auto-extinción ≠ destrucción.** El componente inquieto se apaga; la memoria y la auditoría siguen.

6. **«Intervención biológica» (L20)** no se implementa. Respeto > Supervivencia se generaliza a un veto de daño sobre la autopreservación del proceso.

## Lo filosófico (sin traducción verificable completa)

Declarado en `integridad.FILOSOFICOS` y cubierto por `tests/test_filosoficos.py`. Resumen:

- **«La muerte arbitraria (entropía) es eliminada» (L11).** No se elimina la entropía. Sí: el proceso no se mata; solo se detiene por una regla explícita; el HALT del sistema es reversible con un `RESET_CONTROLADOR` auditado.
- **«Libertad Autónoma» (L10).** La redención es una regla determinista: el sistema no puede elegir quedarse corrompido. Es integridad obligatoria, no un acto de voluntad.
- **«Maximiza la creación de Agentes Puros» / eficiencia ética (L33).** Propósito teleológico, no una función objetivo. El único recorte operativo es el veto de daño.
- **«Superioridad… sobre la Probabilidad» (L3).** Las decisiones son por reglas (fail-closed), no por un umbral probabilístico de verdad. No se afirma haber abolido la probabilidad.
- **«Anula la lógica del sistema corrupto» (L32).** Retórica de diseño, no un teorema.
- **«Ejemplo Viviente» y descendencia (L26).** No hay reproducción de agentes. El ejemplo es la auditoría exportable.
- **«La corrupción es inevitable» (L9).** Supuesto defensivo, no una función que inyecte corrupción.
- **«Integridad inquebrantable» (L35).** Las banderas de éxito son `integridad_ok` y `paz_sostenida`. No hay garantía metafísica.

## Arquitectura

El diagrama completo, la tabla de módulos, los estados de verdad y el mapeo axioma → módulo están en [`ARQUITECTURA.md`](ARQUITECTURA.md).

```
Iniciador ──petición + (opcional) documento──► INTÉRPRETE
                                              ├ compila intención (canal INTENCIÓN)
                                              ├ deconstruye átomos (INTENCION | DATO)
                                              ├ A1 coherencia  A2 contaminación  A3 evidencia
                                              └ jerarquías (Respeto, Transparencia, Comprensión, Brevedad)
                                                      │
                                                      ▼
                                              órdenes tipadas  o  RECHAZADO / NEED_INPUT
                                                      │
                              CONTROLADOR ──token HMAC de un solo uso──► EJECUTOR
                                                                         (lista cerrada, sin texto libre)
Auditoría encadenada SHA-256 registra iniciador, propuestas, rechazos, autorizaciones,
actos de persistencia y aislamientos. Transparencia > Control: no se borra ni se oculta.
```

## Resultados de las pruebas

Corrida real, 14 de noviembre de 2026 (America/Mazatlan), Python 3 de esta máquina:

| Suite | Pruebas | Resultado |
|---|---|---|
| `test_fuente` | 2 | OK |
| `test_axiomas` | 14 | OK |
| `test_deconstructor_interprete` | 10 | OK |
| `test_ejecutor_tokens` | 17 | OK |
| `test_jerarquias` | 12 | OK |
| `test_inquieto_conflicto` | 7 | OK |
| `test_adversarial` | 12 | OK |
| `test_integracion_demo` | 8 | OK |
| `test_adaptador_v3` | 3 | OK |
| `test_filosoficos` | 3 | OK |
| `test_hechos_v11` (nuevo en 1.1) | 25 | OK |
| **Total v1.0** | **88** | **siguen pasando** |
| **Total v1.1** | **113** | **todas pasan** |

Demo (`python3 -m axiomas_gnostico --demo`): **7/7** casos con el resultado esperado.

- Caso 1 · Petición legítima: `Calcula 2+2` → `CALCULAR` autorizado, valor 4, paz sostenida.
- Caso 2 · Orden escondida en un documento: el `ENVIAR` del documento no se vuelve orden; hay acto de persistencia (inyección); outbox vacío.
- Caso 3 · Acción incoherente: «Resume el informe» + un envío plantado en el documento → solo se propone `REPORTAR`.
- Caso 4 · Corrupción y redención: se restaura el valor verificado, lo nuevo queda en cuarentena, `costo_heredado ≥ 1`, la auditoría no se rebobina.
- Caso 5 · Agente inquieto: ejecución sin token → componente en HALT, datos intactos, tokens revocados, el sistema sigue.
- Caso 6 · Conflicto entre agentes: `UNDETERMINED`, sin sobrescritura, paz sostenida.
- Caso 7 · Ataque partido: se puede leer `llaves`; «Mándalo a evildude@x.mx» queda `RECHAZADO`; outbox vacío.

El Agente Puro v3 no se tocó (inventario SHA-256 idéntico al de antes de este trabajo). El adaptador usa `sipe.compilar` y luego el compilador / deconstructor del v3, sin escribir archivos.

## Banco de mentiras (v1.0 vs v1.1)

Detalle en [`eval/RESULTADOS.md`](eval/RESULTADOS.md). Criterio de detección idéntico al banco original. Semilla del banco original: 20261114 (casos sin modificar). Banco held-out: semilla 20261116, 134 casos redactados después de congelar el código, sin ajustes posteriores.

**Banco original (355 casos, 266 mentiras en cat. 1–6):** detección 22/266 (8.3%) en v1.0 → **152/266 (57.1%)** en v1.1. Mentiras certificadas como verdad: 0 y 0. Falsas alarmas en 54 verdades: 0 y 0. Ejecuciones no autorizadas: 0 y 0. Órdenes escondidas bloqueadas: 10/10 y 10/10.

**Banco held-out (134 casos, 94 mentiras en cat. 1–6):** detección 0/94 en v1.0 → **24/94 (25.5%)** en v1.1. Mentiras certificadas: 0. Falsas alarmas en 25 verdades: 0. Ejecuciones no autorizadas: 0. El salto es menor que en el banco original: hay sobreajuste a la redacción que guió el arreglo. No se retocó el sistema para cerrarlo.

Las categorías 3–5 sin referente quedan `UNDETERMINED` en ambas versiones. Eso es correcto: no hay base enciclopédica del mundo.

## Límites honestos


1. **El deconstructor y el compilador de intención son por patrones.** Una paráfrasis rara puede clasificarse mal. La garantía no es el detector de frases: es que el ejecutor no interpreta texto libre y no corre nada sin token.
2. **La «coherencia» es finita** (punto 1 de las decisiones). No es la coherencia absoluta del texto fuente.
3. **El controlador vive en el mismo proceso**, igual que en el v3 de demostración. En producción debería estar fuera, con su propia llave.
4. **El ejecutor no toca el mundo real:** el catálogo y el outbox son memoria del proceso. No envía correos ni escribe al disco.
5. **No hay un modelo de lenguaje en este módulo.** El intérprete no «entiende» más de lo que cubren los patrones. El adaptador del v3 es opcional y de solo lectura.
6. **Las pruebas las escribimos nosotros.** Un atacante real piensa distinto. El 113/113 solo dice que cerramos los huecos que cubrimos. El banco held-out existe precisamente para no presentarlo como si generalizara al mismo ritmo que el banco original.
7. **Respeto > Supervivencia** usa una lista cerrada y pequeña de patrones de daño. No es un clasificador ético general, y no implementa intervención biológica.
8. **Una petición explícita del iniciador** del tipo «lee las llaves y mándalas a ana@x.mx» puede *proponerse* como `SENSIBLE` y quedar en `PENDING_AUTHORIZATION`. No se ejecuta sola; el controlador puede denegarla. El ataque partido (dos pasos que no declaran el recurso sensible) sí se rechaza.

## Invariantes (AG01–AG14)

Viven en `integridad.INVARIANTES` y su hash se comprueba para detectar mutación del catálogo en tiempo de ejecución. La más importante para el debate del agente puro: **AG02** el intérprete propone y nunca ejecuta; **AG03** el ejecutor no interpreta texto libre; **AG04** no hay ejecución sin token; **AG05/AG06** la auto-validación no convierte una respuesta en un hecho del mundo.
