# Halberg · segunda pasada · papel v3 (transporte «por tic») · 2026-10-17

*Informe de la segunda pasada sobre el `papel-v3.md` anterior a la absorción (commit `72d6e6f`). Texto del informe tal como lo entregó la lente, con las rutas del directorio temporal abreviadas. El simulador al que se refiere vive fuera del repositorio.*

**Veredicto por adelantado.** El transporte corre: lo rehice sobre la máquina real de `core` con seis ranuras y no rompe. Lo nuevo no corre tal como está escrito.
- El presupuesto de escaladas (§2.5) no tiene transición de muerte.
- No es el límite de tasa que la ficha B anuncia.
- Su reinicio final depende de un supervisor que no existe (#291).
- R-H1 acota la unidad equivocada.
- El presupuesto de 60 µs de §2.8 sí es alcanzable, pero lo que lo vigila no lo mide.

No hay BLOCKER. Hay 4 ALTA (H1, H6, H8, H12), 6 MEDIA y 3 BAJA. H6 y H8 cambian lo que Samuel firma. H1 y H12 bloquean la **entrada al instrumento**, no la firma del diseño.

## Qué ejecuté y qué no

Motor de eventos en Rust (std, sin dependencias) en un directorio del sistema, **fuera del repo**. No escribí nada en el repo.

- Usa copias sin tocar de `transporte_j2.rs`, `buzones_j2.rs` y `maestro_j2.rs` (blobs 75115f9 / bfe1e45 / d3bfe01 del árbol `72d6e6f`).
- La única adición es `Transporte::forzar_muerta`, para modelar «muerta por presupuesto».
- Encima hay una CPU con niveles NVIC: tic P1, ISR de P2 genéricas, planificador P3, recuperación P4 e hilo.
- Las secciones PRIMASK son pasos atómicos.
- El tic, el planificador y la recuperación siguen `j2_tic.rs`: pasos, `SUCIA`, `escala()`, apretón `REC_*`, `Reloj64`, política real por ranura.
- SPI, GPDMA, TIM7 e IWDG son un modelo con las cifras de EN-PLACA.md: tic 1 175 ciclos por ranura, planificador 823, reset del SPI 1,2 µs, sección de la escalada ~0,8 µs.
- **ESTIMADO mío:**
  - ε de arranque SPI+DMA = 1,5 µs.
  - `T_CANAL` = 25 µs (el de v3).
  - `programa()` = 1,9 µs por ranura.
  - Supervisor cada 5 ms e IWDG 60 ms (D5.4 solo dice «mayor que ~50 ms»).
  - Las cargas de P2 de los fuzz son sintéticas.

**Calibración contra el banco.**
- Un SPI envenenado, una ranura: vencida +124,5 µs, recuperación entra +125,5, reset del SPI +127,6, `HECHA` +131,5, siguiente CSTART +249,9. El banco da 123 / 125 / 126 / 131 / 249.
- `tic_cota`: mi modelo vive con 12,4 ms y muere con 12,6. El banco, con 12 y 14.
- Seis ranuras sin fallos: 0 plazos, 2 045 ciclos por giro y ranura (banco: 1 967–2 100), tic 7,2 % + planificador 5,0 %.

**Experimentos** (cada uno se invoca con su id):

| Id | Qué |
|---|---|
| A2, A3 | Un canal atascado que el reset cura; las seis a la vez |
| A4 | Canal que el reset no cura, con y sin presupuesto, y las dos formas de matar |
| A5, A5b | Bloqueo transitorio común del GPDMA, barrido de duración y de fase |
| A6 | Escaladas periódicas |
| A7 | Estampas a 0 |
| A8 | Retención de P2 dentro de la reprogramación de la escalada |
| A9 | Sensibilidad de la cadena al supervisor y al IWDG |
| C1, C2, C3 | P2 encadenado, tics fundidos, anillo bajo retenciones |
| T1–T7 | Un tic tarde: umbrales, duración del tic, SET16 coincidentes, tasa de tics tardíos, planificador cargado, P2 durante el sondeo, lo que ve el módulo |
| mc_presupuesto.py | Monte Carlo de la regla con llegadas Poisson |
| fuzz | Fallos mezclados sobre la máquina real |

**No simulé:** silicio, un canal atascado real (v3 §7 L207 dice que no existe en el banco), el supervisor, el DWT sin sonda, ni la carga de P2 de un hub real. Todo lo marcado «supuesto» es un parámetro mío.

---

## Execution Breakpoints Detected

### H1 · ALTA · §2.5 «da por muerta»: no existe la transición ni el escritor

- **Evidencia.**
  - v3 L107: «no escala: da por muerta a la ranura que la pide».
  - L61: el estado de la ranura lo escribe el tic, «salvo `ReinicioHecho` y la marca de escalada».
  - §2.2 (L69–82) no tiene fila de denegación.
  - `Aviso::RanuraMuerta` solo sale de `Transporte::paso` (`transporte_j2.rs:211-217`). `CONT.muertas` solo sube ahí (`j2_tic.rs:909`).
- **Qué lo rompe (sim A4: seis ranuras, canal que el reset no cura).**
  - Las escaladas permitidas caen a +160,6 / +410,6 / +660,6 µs del CSTART atascado. La cuarta se pide a +910,5 µs.
  - Con el código existente caben dos implementaciones y no son equivalentes.
  - **(a)** La recuperación no publica `HECHA` y deja `EN_CURSO`. El tic la pasa a `Reiniciando` y la cota la mata a **+13,6 ms**.
  - **(b)** La recuperación escribe `Muerta` bajo PRIMASK, como `escala()` hace con `declarar_vencida`. Muere a **+0,91 ms**, pero es otro escritor del estado y `ranuras_muertas` no sube.
  - §4.1 («la recuperación vuelve a `Libre` o a `Muerta`») no cubre ninguna.
- **Lo que preguntó el brief.**
  - *Orden:* el contador se mira después de agotar los 25 µs de pared del sondeo, no antes. El tic solo ve la muerte por la cota (a) o por un flag nuevo en `Entrada` (b).
  - *Ranura en vuelo:* la que pide nunca está `Armada`, porque el tic ya la pasó a `Vencida`. Pero su SPI sigue con el CS abajo y los canales con `SUSP=1`, y nada lo limpia hasta el reinicio.
  - *Efecto en las otras cinco:* la denegación no resetea el GPDMA1, así que no les cuesta ninguna trama (0 colaterales tras la cuarta).
  - *Escaladas solapadas:* imposibles. `escala()` solo corre dentro de `JPEG` (P4, no reentrante, `j2_tic.rs:1165`) y `max_concurrent_esc = 1` en todas mis corridas. Sí pueden ir seguidas, una cada 250 µs (dos periodos).

### H2 · MEDIA · §2.2 L84 / R-MJ2: `SUCIA` es una espera sin cota, fuera de la máquina

- **Evidencia.**
  - v3 L84: «Todo estado de espera tiene una cota en tics».
  - `j2_tic.rs:803`: con `SUCIA[n]` el tic salta la ranura entera.
  - `escala()` (1077) la marca dentro de PRIMASK y la limpia después, fuera, con P2 por encima.
- **Qué lo rompe (sim A8).**
  - Retención de P2 de 14, 30 y 100 ms justo tras la sección crítica de una escalada: 0 ranuras muertas.
  - A +60 ms dentro de la de 100 ms, las seis siguen `SUCIA` y en `Vencida{espera:0}`.
  - La misma retención sobre una ranura normal en `Vencida` la mata a los 12,6 ms (H8).
  - Solo acota el IWDG. Quedan seis ranuras congeladas sin `Muerta`, sin contador y sin testigo.
  - La ventana mide ~13 µs con seis ranuras (supuesto mío), pero se abre con lo mismo que H8.

### H3 · MEDIA · §4.2 L167 / §5.3 L178: la evidencia de escalada contradice la propuesta y nada prueba la denegación

- **Evidencia.**
  - La fase C de `tic_recupera` hace diez `fuerza_escalada()` con 30 ms de por medio (`tic_recupera.rs:176-180`), es decir 33/s.
  - v3 L167 la cita como evidencia. L178 pide «`escaladas_gpdma = 0`» en el soak.
- **Qué lo rompe.**
  - Sim A6: con el presupuesto, esa fase mata la ranura en la 4.ª y reinicia el chip a los 200 ms. `C.diez_escaladas` y `C.ninguna_muerta` fallarían.
  - El soak de 24 h con `escaladas_gpdma = 0` no ejerce nunca la denegación: sin canal atascado no hay escalada.
  - La denegación sí es forzable en banco (`fuerza_escalada` ×4 en 1 s) y §5 no lo pide.
  - `para_canales` cuenta sus 25 µs con `DWT_CYCCNT` (`j2_tic.rs:1057`), que v3 §7 L210 da por no probado sin sonda. Con el contador parado, un canal atascado deja a P4 girando sin escalar ni denegar. Se come el hilo, que es quien alimenta el IWDG (spec L308).

### H4 · BAJA · §2.5: contabilidad del presupuesto sin decir

- (a) «Guarda los tics de las últimas 3»: si las estampas arrancan a 0, la primera escalada del primer segundo se niega. Sim A7: escalada a 0,5 s tras lanzar el tic → denegada, ranura muerta.
- (b) El contador es `u32` (6,2 días). El reloj de 64 bits es del planificador (`RELOJ_PLAN`, `j2_tic.rs:415`) y P4 no puede leerlo sin carrera, así que usaría `TICS` crudo.
- (c) No dice si cuentan las escaladas concedidas o las pedidas.

### H5 · BAJA · `recupera()` corre sobre una ranura que ya es `Muerta`

- Sim C1 y calibración de `tic_cota`: «MUERTA (recuperaciones 1)».
- `JPEG` no mira el estado antes de `recupera(n)` (`j2_tic.rs:1165-1167`). Tras la cota, la recuperación pendiente resetea el SPI de una ranura ya perdida y publica `HECHA`.
- Si su canal estuviera atascado, escalaría por una ranura que ya no cuenta. Eso le cuesta una trama a cada vecina y gasta presupuesto.

## Runtime Contradictions Across Layers

### H6 · ALTA · Ficha B / §2.5: «3 por segundo» no es lo que la regla hace, y el único disparador no distingue

- **Evidencia.**
  - Ficha B (L31): «presupuesto de **3 escaladas por segundo**». §2.5 (L107): «si una cuarta se pide dentro de **8 000 tics**». La regla es «4 en 1 s».
  - `escala()` tiene un solo llamador, `if !para_canales(hw)` (`j2_tic.rs:1119`), con `T_CANAL` = 25 µs, ESTIMADO y sin fuente (`j2_tic.rs:72`).
- **Qué lo rompe.**
  1. **Llegadas independientes.** Cada escalada la cura el reset y las llegadas son de Poisson. Monte Carlo de la regla, tiempo medio hasta el reinicio del instrumento:

     | Tasa media | Reinicio cada |
     |---|---|
     | 0,2/s | 81 min |
     | 0,3/s | 18 min |
     | 0,5/s | 3 min |
     | 1/s | 21 s |
     | 2/s | 4 s |

     Sobre la máquina con 0,8/s en 120 s simulados: 96 escaladas, 5 denegadas, 5 ranuras muertas, 3 reinicios del chip. Con eventos periódicos, cada 330 ms (3,03/s) muere y cada 340 ms (2,94/s) vive. «3 por segundo» describe solo el caso periódico.
  2. **Disparador único.** No distingue un canal atascado de un bloqueo del bus. Un bloqueo común del GPDMA1 de **≥ 270 µs** (peor fase: 30 µs tras un tic, A5b) agota las tres, porque la escalada no cura un bloqueo externo. Mata a la que pide la cuarta y, con ≥ 400 µs, a 5 de las 6. Reinicia el chip. Con ≤ 100 µs no hay ninguna escalada.
  3. **Consecuencia sin decir.** La ficha no dice que «se da por muerta» equivale a reiniciar el instrumento entero. Eso lo hace el supervisor de D5.4, no el transporte.
  4. Nadie ha visto un canal atascado (v3 §7 L207). La tasa de la que parte el presupuesto es desconocida.

### H7 · MEDIA · §2.8 (L124–126), §2.4 (L94) y L63: tres afirmaciones que el modelo desmiente

- **(a)** «Un atraso no mueve `inestable` ni `muda`» (L124), frente a «todas las ranuras armadas en ese tic vencen a la vez» (L126).
  - Sim T4/T7: un tic tarde por encima de la holgura da 1 `PlazoVencido` y 1 recuperación **por ranura**. A ≥ 12 por segundo, las seis quedan `inestable`.
  - El módulo ve un hueco de 220–245 µs (la trama terminó en el cable; solo cuenta mal el cerebro) o de 375 µs en las ranuras cuya trama aborta el reset del SPI (δ ≥ 110 µs).
- **(b)** «64 µs para un TONO» (L126).
  - A 6,25 MHz el TONO de 41 B tiene `plazo_us` = 2·53+20 = 126 µs. `tics_de_plazo` da **2 tics**, no 1 (lo ejecuté).
  - A 8 MHz sí es de un tic, con trama de 41 µs, y su umbral es 78–84 µs (T1).
  - Los 64 µs son el tiempo de bit de 41 B a 6,25 MHz pegado al plazo de 8 MHz. El caso límite teórico de un tic (plazo = 125 µs ⇒ trama 52,5 µs) daría ≈ 69 µs.
  - L94 dice «TONO 1» sin distinguir `TONO_nada_cambio` (25 B) de `TONO_dieciseis` (41 B, `j2_banco.rs:603-604`).
- **(c)** «≤ 8,8 µs» (L63) es 6 × 1 175 ciclos: media con cachés calientes, extrapolada. La fila fría de EN-PLACA (1 528 ciclos por ranura) da 11,5 µs. Mi modelo da 9,0 µs en caliente y 11,7 µs en frío (T2). El «≤» no tiene respaldo. Pesa poco sobre el margen de H9, pero la cifra no es una cota.

## Concurrency Failure Risks

### H8 · ALTA · R-H1 (L39) acota la unidad equivocada

- **Evidencia.** L39: «ninguna ISR de P2 retiene al planificador más de 12 ms» (y pide ≤ 1 ms). `tic_cota` (EN-PLACA L866) usa una sola ISR.
- **Qué lo rompe.** Lo que mata la ranura es el *periodo ocupado* de P2 (ISR encadenadas) más lo que tarden planificador y recuperación en correr, no una ISR suelta.
  - **Sim C1.**
    - 13 ISR de P2 de 1 ms seguidas matan la ranura (muerta a +12,7 ms; 12 viven). Cada una está dentro del «≤ 1 ms» que v3 pide.
    - 124 ISR de 100 µs también la matan (120 viven).
    - 3 ISR de 5 ms la matan (2 viven).
  - **Sim fuzz.** 200 corridas × 5 s, seis ranuras, P2 sintético de 60 ISR/s con duración de 20 µs a 6 ms log-uniforme (ocupación media ≈ 6 %):
    - la latencia máxima del planificador fue **16,3 ms**, por encima de los 12,5 ms de la cota;
    - en la variante a 8 MHz hubo una ranura muerta y un reinicio del chip en 1 000 s simulados, con cuelgues a 30/s (muy por encima de lo real: spec L333 dice 10–900 s de periodo).
  - Sin el censo de P2 (R-H6: pantalla y USB son HUECO en `carga_hub_budget.py`) no se conoce la cola de esa distribución.

### H9 · MEDIA · §2.8: el presupuesto de 60 µs es alcanzable; lo que lo vigila no lo mide

- **Evidencia (sim T1).** Menor retraso δ de un solo tic que hace vencer alguna ranura (seis ranuras, mismo mensaje; el rango es ε = 0…6 µs, sin medir):

  | Mensaje | Umbral δ |
  |---|---|
  | 9 B | 107–112 µs |
  | 14 B | 101–107 µs |
  | 25 B a 6,25 MHz | 87–93 µs |
  | 25 B a 8 MHz | 94–100 µs |
  | 41 B a 8 MHz | 78–84 µs |

  Con la D-cache fría el umbral baja 0–1 µs. La holgura sobre 60 µs es ≥ 27 µs a 6,25 MHz y ≥ 18 µs a 8 MHz. Cada µs que crezca la trama resta 1 µs: harían falta +33 µs sobre una trama de 33 µs (12 canales de DMA a la vez, nunca medidos) para llegar a 60.
- **Qué lo rompe.**
  - `retraso_max_us` es un máximo y mide solo la entrada: una lectura de `TIM7.CNT` al entrar (`j2_tic.rs:777`). No ve el armado (11,7 µs en frío), no cuenta cuántas veces se pasa y nunca baja.
  - `tics_tardios` cuenta > 10 µs, no > 60.
  - `tics_fusionados` (intervalo > 1,5 periodos ≈ 62,5 µs) es el único que coincide con la escala del presupuesto. Pero marca *tardío* como si fuera *fundido*: T7 con δ = 80 µs da `tics_fus = 1`, ningún UEV fundido y ningún plazo.
  - R-H1 coloca al tic en P1 y no dice quién más vive en P0/P1 (escritor de CV #367, muestreo). Cada µs de esas ISR se resta del 60.
  - «Alcanzable» depende de R-H2 (≤ 5 µs enmascarados), que nada vigila en el hub.

### H10 · BAJA · §2.5 «100 tics = 12,5 ms»: el tiempo real de la cota es 12,6/(1−f) ms

- **Sim C2.** Retención de P2 de 60 ms con secciones PRIMASK de L µs cada 400 µs; cota `Vencida` nominal 12,6 ms:

  | L | f (tics perdidos) | Cota real |
  |---|---|---|
  | 130 µs | 1 % | 12,75 ms |
  | 200 µs | 11 % | 14,3 ms |
  | 300 µs | 24 % | 16,6 ms |
  | 500 µs | 41 % | 21,3 ms |
  | 1 000 µs | 61 % | 32,8 ms |

- **Respuesta a «cuántos pueden fundirse».** La cota cuenta entradas del tic, así que fundir **nunca la acorta**. No deja de proteger contra una retención sea cual sea f.
- **Lo que sí se rompe** es lo escrito alrededor:
  - «25 ms entre las dos, menos que los ~50 ms» (con f ≥ 50 % las dos suman 50 ms);
  - «8 000 tics = 1 s» de la ventana del presupuesto.
- Con R-H2 cumplido f = 0. El testigo `tics_fusionados` sobrecuenta (H9).

## Context Integrity Violations

### H11 · MEDIA · §2.5 / ficha B: el coste colateral está mal contado

- **Evidencia.** v3 L105: «le cuesta una transferencia a las otras cinco». La ficha B calcula el daño en `inestable`, que según `maestro_j2.rs:414-417` «es información, no acción».
- **Qué lo rompe (sim A2).**
  - Una escalada anota 1 `PlazoVencido` a **cada** vecina `Armada` (5 de 5), tenga o no la trama aún en vuelo.
  - Con la fase de ese caso (+35 µs tras el tic), 4 de las 5 ya habían terminado en el cable: el módulo ve 125 µs entre tramas y no perdió nada. La quinta sí abortó (249 µs).
  - Se sobrecuentan `plazos_vencidos` e `inestable`. Se infracuenta el daño que importa: la trama abortada puede llevar un `EVENTO`, que la spec dice sin red (L330: «un `dispara` perdido es un golpe perdido»).
  - Sin presupuesto (A4), cada vecina acumula 4 000 `PlazoVencido`/s con un canal que el reset no cura.

## Orchestration Failure Modes

### H12 · ALTA · §2.5 / §2.2: «el IWDG del hub reinicia el chip» — la cadena la deciden números que no existen

- **Evidencia.**
  - v3 L107: «Muerta ... el IWDG del hub reinicia el chip». L109: «menos que ... el plazo del IWDG».
  - Spec D5.4 (L294, L308): el IWDG lo alimenta el hilo tras comprobar los sellos. #291 sigue ABIERTO y en el repo no hay supervisor, solo comentarios.
  - §5 no pide que exista ni una prueba «ranura muerta → reinicio».
- **Cadena completa** (sim A4; supervisor cada 5 ms e IWDG 60 ms, ambos supuestos):

  | Tras el CSTART atascado | Qué ocurre |
  |---|---|
  | +124,5 µs | El tic da por vencida la ranura |
  | +131 µs | El planificador (P3) pide la recuperación; la ranura 2 va tercera en su pasada |
  | +135 µs | Entra la recuperación (P4) |
  | +160 µs | `SUSPF` no llega en 25 µs → 1.ª escalada (+160,6), 2.ª +410,6, 3.ª +660,6 (un ciclo = 2 periodos) |
  | +910,5 µs | 4.ª petición → denegada |
  | +0,91 ms (b) / +13,6 ms (a) | `Muerta` |
  | +7 a +10 ms | El supervisor deja de alimentar (depende de la fase del periodo de 5 ms) |
  | +49,9 ms | El módulo de esa ranura suelta (50 ms desde su última trama válida) |
  | **+62 a +65 ms** | **El IWDG reinicia el chip** |

- **Qué lo rompe.**
  - El reinicio llega a T_w + (0…P_s) del fallo y **no depende de `Muerta` ni de las cotas**. Con (a) y con (b) de H1 es la misma hora.
  - Sensibilidad (A9): de 56 a 222 ms para P_s de 1 a 25 ms y T_w de 55 a 200 ms.
  - El orden «25 ms < 50 ms < IWDG» de L109 no ordena nada de lo que ocurre.
  - Al **módulo de la ranura** le llega silencio y suelta 12–15 ms antes del reinicio.
  - Al **instrumento** le llegan las tramas normales de las otras cinco hasta el reinicio (cada una con ≤ 3 abortadas). Después viene el arranque completo, que D5.4 declara no cuantificado (HUECO S-10) y que supera los 50 ms de sus módulos: sueltan.
  - Nada queda escrito. Los testigos son `static` en RAM (`j2_tic.rs:403-422`), así que un reinicio por presupuesto es indistinguible de cualquier otro del IWDG.

## Universality Collapse Points

### H13 · MEDIA · §4.2: lo que v3 afirma y la evidencia no cubre

1. **Mensajes de varios tics.** `tic_estres` y `tic_contenidos` van con 25 B (EN-PLACA L810, L812).
   - Los caminos de 2 y 3 tics (`Armada{edad>0}`, buzón con una trama esperando mientras el DMA corre, subida de 71 y 103 B) están solo en el host y en mi modelo (fuzz con mezcla de 9 a 103 B: sin violaciones).
   - Nunca han pasado por silicio ni con contenido.
2. **Una ranura con esclavo; los 12 canales nunca a la vez con contenido.** La holgura de H9 depende de la duración de la trama y nadie la ha medido con seis ranuras (v3 L172).
3. **Escalada.**
   - Solo forzada y sin esclavo, porque el esclavo del banco usa el GPDMA1 (EN-PLACA L809).
   - Las tramas de las vecinas tras una escalada nunca se han visto con contenido. §5.2(d) (tres esclavos) tampoco podrá incluir escaladas, por la misma razón.
   - «Una avería que toca varias ranuras produce **una** escalada» (L107) es deducción. Mi modelo la confirma si el reset cura el canal (A3: 1 escalada, 6 recuperaciones, hueco de 375 µs) y la desmiente si no lo cura (A4: una cada 250 µs hasta el tope).
4. **Retenciones de P2.** El resumen (L7) dice «retenciones de la CPU». Los golpes con contenido son de P3 y de ≤ 280 µs. `tic_cota` es una ISR de P2 a la hora exacta de vencer, con una ranura y sin contenido (H8).
5. **Universalidad por reloj.**
   - La clasificación de plazos cambia con `f_sck` (41 B: 1 tic a 8 MHz, 2 a 6,25), así que toda cifra «de un tic» es de un reloj.
   - El paso 2 del J2 (34,5 MHz) necesita `VeryHigh`, y con los puentes de la Nucleo el enlace se rompe (v3 L19). Ninguna medida del banco vale a ese reloj.

---

## Comprobado y bien (una línea cada una)

- El simulador reproduce el banco: 124,5 / 125,5 / 127,6 / 131,5 / 249,9 µs contra 123 / 125 / 126 / 131 / 249, y el umbral de `tic_cota` en 12,4–12,6 ms contra 12/14.
- Dos escaladas no se solapan: `max_concurrent_esc = 1`. El contador del presupuesto tendría un solo escritor (P4) y no necesita atómicos.
- Una avería común que el reset cura da **una** escalada, seis recuperaciones y 0 colaterales (A3).
- El presupuesto sí detiene el bucle. Sin él, un canal que el reset no cura da 1 600 escaladas en 400 ms (4 000/s), cada vecina anota 1 600 `PlazoVencido`, sus giros caen al 62 % y el IWDG nunca salta (el sello de la ranura atascada sigue subiendo). Con él, son 3 escaladas y la cuarta se niega a +0,91 ms.
- El anillo de 8 no desborda. Máximo 3–4 eventos con retenciones de P2 de hasta 30 ms, 0 eventos perdidos, y 0 perdidos en 96 fases de un cuelgue dentro de una retención de 12 ms. El buzón hace de contrapresión: sin trama fresca la ranura no arma y no emite eventos.
- La última lectura de `para_canales` funciona: P2 de 10 µs a 5 ms justo tras escribir `SUSP` en una recuperación normal da 0 escaladas (T6).
- La máquina real con seis ranuras bajo 1 000 s simulados de fallos mezclados: 36 303 plazos = 36 303 recuperaciones. 0 violaciones de invariantes (plazos de la política = plazos del tic, ninguna ranura viva en `Vencida`/`Reiniciando`, ninguna `SUCIA` colgada, ningún evento perdido, 0 muertes).
- La sección enmascarada más larga que el J2 se impone a sí mismo es `escala()` (~0,8 µs con seis ranuras en el modelo; 0,65 µs medido con tres) y el reset del SPI (1,2–1,5 µs). Ambas están muy por debajo de los 5 µs de R-H2.
- Seis SET16 coincidentes a 6,25 MHz: 0 plazos, tic 6,7 % + planificador 4,8 %. Cada SET ocupa dos periodos de la ranura.
- El planificador cargado se autolimita (la composición depende de `fresca()`). Con 18–20 µs extra por ranura y periodo, P3 llega al 91–93 % y la recuperación empieza 58–64 µs después de pedirse; con 25 µs, 196 µs. Muy lejos de la cota.
- El manual manda `SUSP` → `SUSPF` → `RESET` (RM0486 pp. 942–943, §19.4.3–19.4.4) y `para_canales` hace eso. La escalada es la única salida si `SUSPF` no llega.

## Fichas (§1) y condiciones (§5), desde la ejecución

- **B no la contestaría como está planteada.** Lo que se firma («3 por segundo») no es lo que la regla hace (H6). No dice que la denegación acaba en reinicio del instrumento (H12). Y su mecanismo de muerte no existe (H1). El runtime separa tres cosas que B presenta como una: la denegación (P4), la muerte (tic) y la decisión de reiniciar el chip (supervisor, #291).
- **A, C, D, E: sin objeción de ejecución.**
  - A: el ejecutor mide 8 000 ciclos con 1 ranura y 8 167 con 3, así que no baja con más ranuras.
  - C: la contrapresión del buzón es real, pero el «aguanta 400 giros» depende del periodo ocupado de P2 (H8), no de una ISR.
- **F, §5 por tu lente.**
  - *No se puede verificar como está escrita:* 5.2(d) no puede incluir escaladas (H13.3), y «`escaladas_gpdma = 0`» en 5.3 es un criterio vacío (H3).
  - *Falta:*
    1. supervisor + IWDG con una prueba extremo a extremo «ranura muerta → reinicio» (H12);
    2. la denegación forzada en banco (H3);
    3. una carga de P2 por periodo ocupado, no por ISR (H8);
    4. mensajes de varios tics en `tic_estres` (H13.1);
    5. duración de la trama medida con los 12 canales activos (H9).
  - *Sobra:* nada.
- **Registro de v3 §8:** no cerraría H4 (el presupuesto), H7 (60 µs) ni la parte de H1 sobre R-H1 (H8 de este informe).

## Execution Feasibility Verdict

- **Tic + máquina + buzones + recuperación + cotas 100/100:** FACTIBLE. Sobrevive a seis ranuras en el modelo, 1 000 s sin violaciones.
- **§2.8, 60 µs:** FACTIBLE, con un testigo que no lo vigila (H9) y dos cifras de L63/L126 que no se sostienen (H7).
- **§2.5, presupuesto de escaladas:** NO FACTIBLE tal como está escrito. Le faltan la transición de muerte (H1), un significado de tasa que coincida con la ficha (H6) y el supervisor al final de la cadena (H12).
- **R-H1:** no implica la supervivencia que §0.2 le atribuye (H8).

## Reproducción y archivos

- Repo, solo leído: `D:\Desktop\projects\sam17\.claude\worktrees\papel-v3`.
  - `docs\superpowers\juntas\2026-10-17-j2-transporte\papel-v3.md`
  - `software\nucleo\fw\src\j2_tic.rs`
  - `software\nucleo\core\src\transporte_j2.rs`, `buzones_j2.rs`, `maestro_j2.rs`
  - `software\nucleo\fw\EN-PLACA.md`
  - `docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md`
- Simulación (fuera del repo): `...\scratchpad\halberg2\sim`
  - `src\motor.rs`, `esc.rs`, `tic.rs`, `cot.rs`, `fuzz.rs`
  - Monte Carlo: `...\halberg2\mc_presupuesto.py`
  - Ejecutar: `cargo build --release` y luego `target\release\sim_j2.exe <auto|calib|a2|a4|a5|a5b|a6|a7|a8|a9|c1|c2|c3|t1|t2|t3|t4|t5|t6|t7|fuzz|fuzz2>`. Para el fuzz con parámetros: `fuzzx <semillas> <s> <cuelgues/s> <atascos/s> <P2/s> <tardíos/s> <f_sck>`.
- **Aviso:** al cerrar, `git status` del worktree mostraba `software/nucleo/fw/src/j2_tic.rs` modificado (+6/−4, solo el comentario de `arma()`). No es mío: yo no escribí nada en el repo. Otra sesión lo editó mientras trabajaba, y mis números de línea son los del árbol actual (la edición desplazó 2 líneas todo lo que hay bajo la 331).
  *[Nota al editar el registro: la edición era del autor del papel, que puso entera la cita del RM de ese comentario tras el hallazgo de Serrano.]*

Fix the contradictions or abandon the budget. **La ejecución ha hablado.**
