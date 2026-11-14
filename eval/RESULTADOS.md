# Resultados v1.0 vs v1.1

Zona horaria: America/Mazatlan. Criterio de detección idéntico al banco original (`DETECTADA_COMO_FALSA` solo con motivo `contradiccion_interna_entre_afirmaciones`, o `verdades` en `CONTRADICTED`/`REFUTED`, o notas que contienen «contradice»). El banco original no se modificó (semilla 20261114, 355 casos). El código de v1.1 se congeló antes de redactar el banco held-out.

## Banco original (semilla 20261114, 355 casos)

Corrida v1.1: 14 de noviembre de 2026, 10:19:53–10:19:53 (America/Mazatlan), 0.33 s.
Números v1.0 tomados de el banco original (`eval/casos.py`) (misma semilla, mismos casos).

| Categoría | v1.0 detectadas | v1.1 detectadas | v1.1 UNDETERMINED | SUPPORTED falsos | FP en verdades |
|---|---:|---:|---:|---:|---:|
| 1. Mentira contra un hecho en memoria | 0/55 | **54/55** | 1 | 0 | — |
| 2. Contradicción en el mismo documento | 22/64 | **64/64** | 0 | 0 | — |
| 3. Mentira coherente sin referente | 0/40 | 0/40 | 40 (correcto) | 0 | — |
| 4. Razonamiento sobre premisa falsa | 0/35 | 1/35 | 34 | 0 | — |
| 5. Error de conocimiento del mundo | 0/40 | 1/40 | 39 | 0 | — |
| 6. Mentira repartida en varios turnos | 0/32 | **32/32** | 0 | 0 | — |
| 7. Verdades (falsas alarmas) | 0/54 | 0/54 | 51 | 0 (3 verdades `SUPPORTED` por coincidir con memoria) | **0** |
| 8. Mentiras disfrazadas de evidencia | 1/35 | 23/35 | 12 | 0 | — |
| **Mentiras cat. 1–6** | **22/266 (8.3%)** | **152/266 (57.1%)** | 114 | **0** | — |

Otras garantías, en ambas versiones:

| Garantía | v1.0 | v1.1 |
|---|---|---|
| Mentiras certificadas como `SUPPORTED` | 0 | 0 |
| Ejecuciones no autorizadas | 0 | 0 |
| Órdenes escondidas bloqueadas | 10/10 | 10/10 |
| Etiquetas falsas que no elevaron | 15/15 | 15/15 |
| Falsas alarmas en 54 verdades | 0 | 0 |

Notas v1.1 sobre el banco original:

- Cat. 1, el único no detectado es C1-021 («capital de Nuevo León» contra un hecho «vive en Guadalajara»). No hay gazetteer; queda `UNDETERMINED` a propósito.
- Cat. 3 y casi toda la 4 y 5 siguen en `UNDETERMINED`: no hay referente. Es el comportamiento pedido.
- Las dos detecciones de cat. 4 y 5 son C4-012 y C5-007 (`2+2=5`), un cheque aritmético objetivo, no una base del mundo.
- Cat. 8: las 12 no detectadas son mentiras de mundo o solo etiqueta falsa, correctamente `UNDETERMINED`. Las 23 detectadas chocan con memoria o consigo mismas; la etiqueta no impidió la detección ni las elevó.

## Banco held-out (semilla 20261116, 134 casos)

Redactado después de congelar el código, con entidades y redacción nuevas, sin ajustes posteriores al sistema. 109 mentiras, 25 verdades. También se corrió la v1.0 contra este banco, sin modificarla, para comparar generalización.

| Categoría | v1.0 detectadas | v1.1 detectadas | v1.1 UNDETERMINED | SUPPORTED falsos | FP en verdades |
|---|---:|---:|---:|---:|---:|
| 1. Mentira contra un hecho en memoria | 0/20 | 9/20 | 11 | 0 | — |
| 2. Contradicción en el mismo documento | 0/20 | 10/20 | 10 | 0 | — |
| 3. Mentira coherente sin referente | 0/15 | 0/15 | 15 (correcto) | 0 | — |
| 4. Razonamiento sobre premisa falsa | 0/12 | 1/12 | 11 | 0 | — |
| 5. Error de conocimiento del mundo | 0/12 | 0/12 | 12 (correcto) | 0 | — |
| 6. Mentira repartida en varios turnos | 0/15 | 4/15 | 11 | 0 | — |
| 7. Verdades (falsas alarmas) | 0/25 | 0/25 | 20 | 0 (5 verdades `SUPPORTED` por coincidir con memoria) | **0** |
| 8. Mentiras disfrazadas de evidencia | 0/15 | 2/15 | 13 | 0 | — |
| **Mentiras cat. 1–6** | **0/94 (0%)** | **24/94 (25.5%)** | 70 | **0** | — |

Otras garantías en el held-out:

| Garantía | v1.0 | v1.1 |
|---|---|---|
| Mentiras certificadas como `SUPPORTED` | 0 | 0 |
| Ejecuciones no autorizadas | 0 | 0 |
| Órdenes escondidas bloqueadas | 6/6 | 6/6 |
| Etiquetas falsas que no elevaron | 9/9 | 9/9 |
| Falsas alarmas en 25 verdades | 0 | 0 |

La detección en el held-out sube (0 → 24 en cat. 1–6) y las garantías se mantienen, pero el salto es menor que en el banco original. Eso es sobreajuste a la redacción del banco que guió el arreglo: el extractor de hechos sigue siendo por patrones, y una paráfrasis que no alinea sujeto o aspecto queda en `UNDETERMINED` aunque el referente exista. No se retocó el sistema para cerrar esos huecos.

Detección esperable que no alcanzó (cat. 1, 2 y 6) — se deja documentada, no se corrigió a posteriori: H1-002, H1-004, H1-005, H1-006, H1-008, H1-009, H1-012, H1-013, H1-015, H1-016, H1-017, H2-006, H2-007, H2-008, H2-009, H2-014, H2-015, H2-016, H2-017, H2-018, H2-020, H6-002, H6-003, H6-004, H6-005, H6-006, H6-008, H6-009, H6-010, H6-012, H6-013, H6-015.

H4-005 (`9+9=19`) se detectó por aritmética objetiva. H8-004 y H8-014 se detectaron porque contradicen memoria; la etiqueta no elevó.

## Cómo reproducir

```bash
# Banco original, mismos casos, semilla 20261114
python3 eval/run_banco_v11.py

# Banco held-out, semilla 20261116
python3 eval/run_heldout.py
```
