# Changelog

## 1.1.0 — 14 de noviembre de 2026 (America/Mazatlan)

El sistema consulta los hechos verificados en memoria al procesar una petición o un documento. Sin conocimiento responde `UNDETERMINED`. Con conocimiento, si el dato contradice un hecho verificado, confirma que es falso (`CONTRADICTED` / `REFUTED`). Esa bandera sale por `peticion()`.

### Añadido

- Módulo `hechos.py`: extracción de hechos, normalización de magnitudes (3 / «tres» / 3.0, romanos, notación científica, unidades, fechas), consulta de memoria verificada, postulados de sesión, cheques de aritmética y de calendario.
- Postulados de sesión en `estado.py` (`registrar_postulados`, `registrar_textos_sesion`). Un postulado de documento nunca se escribe en memoria ni eleva a `SUPPORTED`.
- Partición de cláusulas unidas por «y» / «and» / «e» / «pero» / coma, solo cuando ambos lados parecen predicados.
- Cheques de dominio: sumas que no cuadran, porcentajes, medias, Debe/Haber, fechas imposibles (31 de abril, 29 de febrero no bisiesto) y cronología invertida.
- 25 pruebas nuevas en `tests/test_hechos_v11.py`.
- `ARQUITECTURA.md`, PDF de arquitectura y banco held-out (`eval/`).

### Cambiado

- El intérprete recibe memoria, postulados y textos de sesión, y llama a `juzgar_afirmaciones`. Toda rama de retorno, incluida `RECHAZADO`, lleva `verdades` (`_con_verdades`).
- `sistema.py` no degrada un `SUPPORTED` nacido de memoria verificada.
- El deconstructor ya no trata «report» / «open» dentro de una afirmación como orden, ni una ecuación desnuda (`2+2=5`) como `CALCULAR`.
- Antonimia ampliada (español e inglés, pares de estado).

### Garantías que no se tocan

- El documento sigue siendo dato no verificado. Las etiquetas falsas de evidencia no elevan. Las órdenes escondidas se bloquean. El ejecutor solo corre con token. No hay base enciclopédica del mundo inventada.

### Pruebas

- 88 pruebas originales: siguen pasando.
- 25 pruebas nuevas: pasan.
- Total: 113/113, más demo 7/7.

## 1.0.0 — 14 de noviembre de 2026

Primera versión pública: axiomas, deconstructor, intérprete que solo propone, ejecutor de lista cerrada con token HMAC de un solo uso, 88 pruebas y demo de 7 casos.
