**Resumen.** Los cuatro mecanismos corren en el modelo: el permiso para el bucle, no hay escaladas solapadas y `SUCIA` ya cuenta contra la cota. Hay un problema serio: el permiso se decide con el contador equivocado. Es ALTA y cambia lo que Samuel firma en la ficha B. No hay BLOCKER. Debajo va el informe completo.

# Halberg · tercera pasada · papel v3 absorbido (commit `4c639f0`) · 2026-10-17

**Veredicto por adelantado.** Los cuatro mecanismos corren en el modelo. Tres no corren como están escritos:
- **§2.5 (ALTA).** El permiso de escalada se decide con el contador equivocado. Cuenta los plazos propios de *cualquier* causa: cuelgues, tics tardíos, errores del DMA. No cuenta el uso del recurso compartido. Tres tics tardíos en el segundo anterior bastan: una avería del GPDMA que el reset curaría acaba en reinicio del instrumento.
- **§2.5.** «Reintenta parar cada tic» no tiene planificador. Sus dos lecturas fallan de forma distinta.
- **§2.7.** El tic reconstruido no hace nada mientras se cumpla R-H2. Fuera de R-H2 acumula periodos fantasma: la cota de 25 ms vence a los 16,75 ms.
- **§2.2.** `SUCIA` solo tiene fila en `Vencida`. Con la tabla literal, el tic arma una vecina sobre un canal que el reset por RCC dejó a cero, y la vecina se apunta un plazo **propio**.

No hay BLOCKER. Hay 1 ALTA, 3 MEDIA y 2 BAJA.

## Qué ejecuté

**Estado del simulador.** La copia `halberg3\sim` que dejó la sesión cortada era idéntica byte a byte a `halberg2\sim` (`diff -r` vacío). `rep.py` era solo un reemplazador de cadenas. No había nada implementado. La reutilicé como base y le añadí las reglas del papel absorbido, que no están construidas (el código de `4c639f0` solo cambió un comentario de `j2_tic.rs`).

**Lo que modelé:**
- **Máquina:** `periodos` (avanzan `edad` y `espera`), esperas de 16 bits, cotas de 200 y 100 tics.
- **`SUCIA`:**
  - En la lectura literal, solo tiene fila en `Vencida`, y ahí le gana a `reinicio_hecho`. Es la lectura más caritativa: es la única en que esa fila hace algo.
  - La variante «`SUCIA` bloquea armar en todo estado» queda como contraste.
- **Tic:** suma `max(1, round(Δciclos/100 000))`.
- **Permiso:** plazos propios de la ranura en la ventana deslizante de 1 s, contando el que pide. Concede `escalar` si son ≤ 3.
- **`PlazoAjeno`:** no puntúa en la salud y manda una limpieza con `escalar = false`. Lo modelé reutilizando `EotTardio`, que este transporte no emite.
- **Denegación:** no publica `HECHA` y reintenta. Tiene dos lecturas:
  - *EnSitio:* P4 espera dentro de la rutina al tic siguiente.
  - *CadaTic:* el tic vuelve a pedir P4.

  En las dos el reintento para si la ranura está `Muerta` (decisión mía).
- **Hardware:**
  - `IDLEF`: un canal con `EN = 0` para.
  - `programa()` empieza con `CR.RESET` y mata lo que esté en vuelo.
  - Armar sobre un SPI sin resetear cuelga la transferencia (ESTIMADO mío).
- **Identidad:** la procesa el planificador, y sin identidad no compone.
- **Supervisor R-H8:**
  - Ventana de 45 ms, `P_s` de 5 ms y `T_IWDG` de 60 ms: los mínimos compatibles con R-H8(3), ESTIMADO mío.
  - El sello es el armado, y las ranuras sin identidad no cuentan.
- **Fuente P0:** una ISR por encima del tic, para provocar tics tardíos.

**Calibración, sin cambios:**
- SPI envenenado: 124,5 / 125,5 / 127,6 / 131,5 / 249,9 µs. El banco da 123 / 125 / 126 / 131 / 249.
- `tic_cota` con 200+100 tics: sobrevive a 25,0 ms y muere con 25,2 ms.
- `Reiniciando`: sobrevive a 12,6 ms y muere con 13,0 ms.

No escribí nada en el repo. `git status` muestra `junta3_serrano.md` y `junta3_voronov.md` sin seguir; no son míos.

---

## Execution Breakpoints Detected

### N1 · ALTA · §2.5 / ficha B: el permiso lo decide la salud de la ranura, no el uso del recurso compartido

**Evidencia en el papel:**
- L149: «concede `escalar` mientras la ranura que pide no tenga más de `umbral_escalada` plazos vencidos propios en la ventana de salud».
- La misma línea: «Es un permiso sobre un recurso compartido, no una marca de salud».
- L171: «Un tic tardío **sí** puntúa en la salud».

**`v3perm`** (determinista). Tres tics de 110 µs tarde a 50, 150 y 250 ms: cada uno hace vencer a las seis ranuras. A 600 ms, un canal atascado que el reset del GPDMA1 **sí** cura.

| K tics tardíos | Escaladas | Qué ocurre (desde el CSTART atascado) |
|---|---|---|
| 0 | 1 | La avería se cura |
| 3 | 0 | Denegada a +0,160 ms; `Muerta` a +12,874 ms; el supervisor deja de alimentar a +45,0 ms; IWDG a +100,0 ms |

**Fuzz.** Mismos parámetros y semillas que el `fuzz2` de la segunda pasada: 30 × 4 s, cuelgues 15/s, atascos curables 0,8/s, P2 30/s, tardíos 5/s, 6,25 MHz.

| Configuración | Reinicios del chip | Ranuras muertas |
|---|---|---|
| Presupuesto retirado (binario de `halberg2`) | 3/30 | 5 |
| Permiso del papel | **27/30** | **48** |
| Permiso, sin tics tardíos | 24/30 | 41 |
| Permiso a 8 MHz | 28/30 | 54 |
| Permiso, con el techo de la spec (0,1 cuelgues/s por ranura) y tardíos 5/s | 3/30 | 3 |
| Lo mismo, sin tardíos | 1/30 | 1 |

**Lo que lo explica.** La probabilidad de que se deniegue un atasco curable es la de tener ≥ 3 plazos propios en el segundo previo (Poisson):

| Plazos propios por ranura | P(denegar) |
|---|---|
| 0,1/s | 0,02 % |
| 0,5/s | 1,4 % |
| 1/s | 8,0 % |
| 2,5/s | 45,6 % |

**Qué rompe:**
- Una avería que el reset cura se convierte en reinicio del instrumento según la historia de la ranura en averías que no tienen nada que ver con ella.
- Una causa común del hub, tres tics tardíos (R-H2), retira el permiso a las seis ranuras a la vez.
- La columna de costo de la ficha B no lo dice.
- §5.2(e) («cuatro seguidas en menos de 1 s») solo ejerce plazos que vienen de escaladas, así que no lo puede ver.

La gravedad real depende de la tasa de atascos, que nadie tiene (§7).

### N4 · MEDIA · §2.5: «reintenta parar cada tic» no tiene quien lo ejecute

**Evidencia:**
- L150: «no publica `HECHA`, reintenta parar cada tic, y la ranura muere por la cota de `Reiniciando`», y la misma línea dice «ninguna transición nueva ni escritor nuevo».
- P4 es una sola rutina serie sobre `REC_PEDIDA` (`j2_tic.rs:1165-1169`).
- En `Reiniciando` el tic no emite eventos (`transporte_j2.rs:266-275`), así que el planificador nunca vuelve a pedir.
- El IWDG lo alimenta el hilo (spec L308).

**Las dos lecturas:**

| Lectura | Evidencia | Qué falla |
|---|---|---|
| (a) P4 sigue dentro de la rutina | `v3a4` EnSitio: P4 ocupa el 90,9 % de un núcleo durante 12,7 ms; el hilo, 8,64 ms sin correr. `v3a4x2` EnSitio (canales que el reset no cura en r1 y r4, cuelgue ordinario en r5 a +1 ms): la recuperación de r5 espera 25,25 ms y **r5, sana, muere por su cota de `Vencida`** a +26,25 ms | Una ranura sana muere en la cola de dos denegaciones |
| (b) Alguien vuelve a pedir P4 en cada tic | `v3a4` CadaTic: 22,3 % de un núcleo por ranura denegada (`T_CANAL` de 25 µs por periodo). `v3a5`, D = 14 ms: seis denegadas piden 150 µs por periodo de 125; P4 gasta 12,4 ms y el hilo pasa 8,9 ms sin correr | Hace falta el disparador nuevo que el papel dice que no existe |

**Qué rompe.** El papel no fija ninguna de las dos. Ninguna dice que un reintento ya en marcha pare al pasar la ranura a `Muerta`: L113 cubre un pedido nuevo, no un bucle en curso.

## Runtime Contradictions Across Layers

### N3 · MEDIA · §2.2: `SUCIA` solo tiene fila en `Vencida`; la tabla arma sobre canales que el reset dejó a cero

**Evidencia en el papel y el código:**
- L99: «| `Vencida` | `sucia` (escalada en curso) | `espera += periodos`; no se lee ni se arma |».
- Las precedencias de L105 no ordenan `sucia`.
- `escala()` reprograma fuera de su sección crítica, expuesta al tic (`j2_tic.rs:1099-1105`).
- `programa()` empieza con `CR.RESET` (`j2_tic.rs:223`).
- El tic de hoy salta la ranura entera (`j2_tic.rs:803`): la tabla es una regresión del código.

**`v3sucia2`** (determinista). Atasco curable en r5. P2 retiene D µs desde 50,130 ms, así que r0–r4 quedan `Libre` sin bajada. Al acabar, el planificador compone y P4 escala.
- Con D de 561 a 570 µs (10 de 126 desfases), el tic arma una vecina **antes** de su `programa()`.
- Primer caso: escalada a 50,7401 ms; el tic arma r4 a 50,7563; `programa()` la aborta en vuelo a 50,7630; r4 vence a 50,8817 con un plazo **propio**.
- En esos 10 casos, r0–r4 suman 30 plazos propios.
- Con «`SUCIA` bloquea armar en todo estado»: 0/126.
- `v3sucia` (cuelgue en r4 y atasco en r5 en el mismo tic, D de 0 a 129 µs): 0 casos. Con la lectura caritativa, `Vencida` está protegida; el agujero está en `Libre` y en `Reiniciando`.

**Qué rompe:**
- La vecina sana puntúa justo lo que `PlazoAjeno` debía sacar de su salud, y además alimenta N1.
- Entre el armado y `programa()` el canal corre con `TR1`, `TR2` y la dirección del periférico a cero por el reset del RCC. No modelé lo que hace el DMA en esos ~7 µs.

## Context Integrity Violations

### N2 · MEDIA · §2.7: el reloj reconstruido no hace nada dentro de R-H2 y fuera de R-H2 inventa periodos

**Evidencia en el papel.** L165: «`tics × 125 µs` sigue a la pared a ±1 periodo, y el error deja de tener un solo signo».

**Cómo se produce.**
- Una entrada δ ∈ (62,5, 125) µs tarde da Δ = 125 + δ, que redondea a 2.
- La siguiente, en hora, da 125 − δ < 62,5, que redondea a 0, y `max(1, ·)` lo sube a 1.
- Cada tic tardío y no fundido suma un periodo fantasma.
- El error tiene un solo signo y se acumula.
- Con δ ≤ 60 µs (R-H2), Δ siempre redondea a 1, así que el mecanismo no hace nada.

**`v3late` (a).** Una ISR P0 retrasa uno de cada K tics; 1 s, sin fallos; 8 000 periodos reales.

| K | δ | Periodos contados | Plazos |
|---|---|---|---|
| 2 | 40 y 60 µs | 8 000 | 0 |
| 2 | 63 a 124 µs | **12 000 (×1,5)** | 0 con δ de 63 a 80 µs |
| 2 | 130 y 200 µs | 7 998 a 7 999 (fundidos, bien) | — |
| 4 | 63 a 124 µs | ×1,25 | — |

**`v3late` (b).** Ranura colgada, con el planificador y la recuperación retenidos 120 ms. Con uno de cada dos tics entre 63 y 124 µs tarde, va de `Vencida` a `Muerta` en **16,75 ms de pared**, frente a los 25 nominales. Con δ de 0, 60, 130 o 200 µs tarda de 25,12 a 25,32 ms.

**`v3c2`.** Secciones PRIMASK de L µs cada 400 µs:
- L = 130 µs: 22,62 ms reconstruido, frente a 25,37 ms sin reconstruir.
- L = 1 000 µs: 24,12 ms, frente a 65,37 ms.

**Qué rompe:**
- Las cotas «en µs» dejan de ser µs justo donde la reconstrucción debía trabajar. `Reiniciando` baja a ~8,3 ms de pared, por debajo de la ventana de 12 ms de R-H1. Lo mismo para quien escala, que pasa la reprogramación en `Reiniciando` (`v3a8`: P2 de 14 ms la mata a 12,9 ms).
- La ventana de D7.3 y la del permiso encogen a 0,67 s.
- `periodos_saltados` cuenta los fantasmas como saltados.

### N5 · BAJA · §2.2: la limpieza por identidad deja colgado el apretón de manos de la recuperación

**Evidencia.**
- L111: «la pide el planificador cuando la política pasa a `Vacia` con una transferencia en vuelo o vencida».
- `REC_HECHA` y `REC_EN_CURSO` solo se borran al salir de `Vencida` o `Reiniciando` (`j2_tic.rs:913-918`).

**`v3ident2`** (r3 con HOLA de 9 B):
- La pérdida de identidad la procesa el planificador tras el tic de 50,000 ms.
- Si una ISR de P2 de 150 µs entra entre 50,013 y 50,016 ms (una ventana de 4 µs), P4 corre después del tic que cierra el giro.
- Resultado a 65 ms: `Libre` con `REC_HECHA` y `REC_EN_CURSO` a `true`.
- El módulo vuelve a 70 ms. Un cuelgue a 110 ms, con P2 de 300 µs al vencer, hace que el tic **rearme a 110,2525 ms con la `HECHA` rancia**: antes de su recuperación y sobre un SPI sin resetear. Deja 2 plazos propios en vez de 1.
- Fuera de esa ventana, el rastro queda limpio.

**Qué rompe.** El invariante de D4, no armar sobre un SPI colgado sin reset. Suma además un plazo propio, que alimenta N1. La ventana es diminuta.

## Orchestration Failure Modes

**Cadena completa hasta el IWDG** (`v3a4`, canal que el reset no cura en r2, reintento CadaTic):

| Desde el CSTART atascado | Qué ocurre |
|---|---|
| +0,161 / +0,411 / +0,661 ms | Escaladas 1.ª, 2.ª y 3.ª |
| +0,910 ms | 4.ª petición, denegada |
| +13,624 ms | `Muerta`, por la cota de `Reiniciando`, escrita por el tic |
| +49,9 ms | El módulo de r2 suelta |
| +50,0 ms | El supervisor (ventana de 45 ms) deja de alimentar |
| **+105,0 ms** | **El IWDG reinicia el chip** |

Las vecinas acaban con 3 `PlazoAjeno` cada una, 0 plazos propios, y siguen vivas. Con el reintento EnSitio la cadena es la misma, y el hilo pasa 8,64 ms sin correr.

### N6 · BAJA · §2.11 frente a R-H8(3): los tiempos citados son de un supervisor que R-H8 prohíbe

**Evidencia en el papel:**
- L197: «con 5 ms y 60 ms, a los 62–65 ms; con otros valores plausibles, de 56 a 222 ms».
- L199: la ventana «es mayor que el mayor hueco de sello del diseño (`Vencida` + `Reiniciando`, 37,5 ms, más el periodo del supervisor)».
- Esas cifras salen de mi supervisor de la segunda pasada, que miraba «sello desde la última mirada» (ventana = `P_s`).

**Simulación.** Con los mínimos que cumplen R-H8(3) (45 / 5 / 60 ms), el reinicio llega a +105,0 ms (`v3a4`) y a +100,0 ms (`v3c1`, `v3perm`). El módulo de la ranura muerta suelta a +49,9 ms, y el instrumento sigue ~55 ms con una ranura muerta.

**Además:**
- La ficha C (L47) dice «la suma menos 12 ms de margen es menor que la ventana del módulo».
- §2.5 (L154) escribe `cota_vencida + cota_reiniciando + 12 ms < T_WATCHDOG_TRAMA_US`.
- Leída al pie de la letra, la ficha admite 62 ms de cotas.

**Qué rompe.** Las cifras que Samuel lee al firmar, y el signo del aserto que firma. El runtime no se rompe.

## Universality Collapse Points

No hay hallazgo nuevo. N1 se reproduce a 8 MHz (28/30 reinicios). N2 depende de la fuente de retraso, no del reloj del SPI.

---

## Comprobado y bien

- **Escaladas solapadas:** imposibles. `concurrentes_max = 1` en todas las corridas: A4, A4x2, A5 y 300 s de fuzz.
- **Ficha B, «hasta 3 escaladas seguidas en ~1 ms»:** sí. Caen a +0,161, +0,411 y +0,661 ms, y la 4.ª se deniega a +0,910 ms.
- **H1 resuelto:** la muerte la da la cota de `Reiniciando`, que ya existía, y la escribe el tic. Ocurre con las dos lecturas del reintento.
- **Una avería común que el reset cura da una escalada:** `v3perm` K = 0.
- **Bloqueo transitorio del bus** (`v3a5`): hasta 13 ms se cura sin muertes (en la segunda pasada, el límite era 270 µs). Con ≥ 14 ms hay reinicio en todas las fases.
- **Vecina sana muerta por escaladas ajenas:** no ocurre en A4, en A5 ni en el fuzz con reintento por tic. Solo ocurre con N4(a); N3 le cuesta un plazo, no la vida.
- **Cotas de 25 y 12,5 ms:**
  - 24 ISR de P2 de 1 ms seguidas: vive. Con 25, muere.
  - Fuzz con P2 a 60/s (200 × 5 s): el planificador pasa como mucho 16,33 ms sin correr, con 0 ranuras muertas.
- **`SUCIA` cuenta contra la cota** (`v3a8`): con retenciones de 30 y 100 ms dentro de la reprogramación, las ranuras mueren por su cota. Ya no quedan congeladas.
- **Invariantes del fuzz:** 0 semillas con violación. Los plazos de la política coinciden con los del tic; ninguna ranura viva se queda en `Vencida` o `Reiniciando`; no se pierden eventos del anillo.

## Hallazgos de la segunda pasada que no quedaron resueltos

- **H2 (parcial):** `SUCIA` ya cuenta contra la cota, pero solo en `Vencida`. En `Libre` y `Reiniciando` se arma durante la reprogramación (N3).
- **H6 (parcial):** el bloqueo transitorio ya no reinicia por debajo de 13 ms. Pero el umbral sigue sin tasa que lo apoye, y la denegación ahora depende de la tasa de plazos propios de cualquier causa (N1).
- **H9 (parcial):** `tics_fuera_de_presupuesto` sí mide el presupuesto. `periodos_saltados` hereda la mezcla de tardío y fundido: con K = 2 y δ = 63 µs cuenta 4 000 «saltados» sin un solo periodo perdido.
- **H10:** el estiramiento desapareció (de 65,4 a 24,1 ms) y lo sustituyó el error contrario (N2: 16,75 ms donde la cota son 25).
- **H11 (parcial):** `PlazoAjeno` saca el daño de la salud, pero sigue anotando como perdidas tramas que llegaron. En A4 hay 15 `PlazoAjeno` y una sola trama perdida en el módulo (hueco de 250 µs en r5, de 125 µs en r0–r4). La fila de §2.10 «una trama por vecina con bajada» lo sobrecuenta.
- **H12 (parcial):** R-H8 y §5.2(g) existen. Los tiempos de §2.11 no son los que produce R-H8 (N6).
- **H13.3:** la escalada sigue sin verse con contenido ni con esclavo. §5.2(e) no dice en qué configuración se fuerza la denegación, y el esclavo del banco usa el GPDMA1.
- **Resueltos:** H1, H3, H4, H5 (el pedido nuevo), H7, H8, H13.1 y H13.2 (como condiciones de §5.2).

## Execution Feasibility Verdict

- **§2.5, permiso:** FACTIBLE como freno, porque acota el bucle y no hay solapes. NO FACTIBLE como criterio: decide con la salud de la ranura (N1), y su rama de denegación no tiene planificador (N4).
- **§2.7:** FACTIBLE dentro de R-H2, donde no hace nada. Fuera de R-H2 la reconstrucción se equivoca hacia arriba hasta ×1,5 (N2).
- **§2.2:** FACTIBLE salvo `SUCIA` en `Libre` y `Reiniciando` (N3) y el apretón de manos tras la limpieza por identidad (N5).
- **§2.11 / R-H8:** el requisito es coherente; las cifras de la cadena no son las suyas (N6).

## Archivos

Todo en `sim/`, junto a este informe:
- **Experimentos:** `sim/junta3/src/v3.rs`
- **Motor y máquina:** `sim/junta3/src/motor.rs` y `sim/junta3/src/transporte_j2.rs`, con las reglas del papel absorbido; `sim/junta3/src/fuzz.rs` (`montar_con`).
- **Parches aplicados sobre la copia de la segunda pasada:** `tools/p_maquina.py`, `tools/p_motor1.py` a `tools/p_motor4.py`, `tools/p_fuzz.py`, `tools/p_dbg*.py`.
- **Ejecutar:** desde `sim/junta3`, `cargo run --release -- <v3cota|v3a4|v3a4x2|v3a5|v3a8|v3c1|v3c2|v3late|v3perm|v3sucia|v3sucia2|v3ident2|v3fuzz>`.
- **Fuzz con parámetros:** `v3fuzzx <semillas> <s> <cuelgues/s> <atascos/s> <P2/s> <tardíos/s> <f_sck> <0 = CadaTic | 1 = EnSitio>`.
- **Comparación con la segunda pasada:** desde `sim/junta2`, `cargo run --release -- fuzz2`.

El runtime no lee la intención del permiso, solo el contador que le dieron. **La ejecución ha hablado.**

*Nota editorial: el simulador vivía en el directorio temporal de la sesión (`scratchpad\halberg2\sim` y `scratchpad\halberg3\sim`); las rutas de «Archivos» se cambiaron por la copia versionada en `sim/junta2` y `sim/junta3`. Los parches `tools/p_*.py` no se versionan: su resultado es `sim/junta3`.*
