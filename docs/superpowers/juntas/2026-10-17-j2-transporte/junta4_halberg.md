# Halberg · cuarta pasada · fichas B, C y H del papel v3 (`86b830c`) · 2026-10-19

**En llano.** La espera entre escaladas hace lo que promete: un bloqueo del GPDMA1 de 1 ms ya no reinicia el chip. El problema es que esa espera vive dentro de la cota de `Reiniciando`, y la cota se calculó contra R-H1 sin contar con ella. Una retención legal del hub (11 a 12 ms) que coincida con ese mismo bloqueo de 1 ms reinicia el chip con espera, y sin espera no lo reinicia. Esto acopla las fichas B y C: hoy no se pueden firmar por separado. La espera tiene además un costo que la ficha no lista: retiene a las seis ranuras sin tramas hasta su borde, 2,4 ms en lugar de 1,4. En `fw` la espera choca con un reloj de P4 que nadie extiende. La cifra de R-H4 es la huella del binario de banco, no una obligación del hub. Hay 1 ALTA, 4 MEDIA y 2 BAJA; ningún BLOCKER.

## Qué ejecuté

- **El modelo.** Copié `software/nucleo` de `espera` (`0f396f7`), sin `target`, a `C:\Users\simon\AppData\Local\Temp\claude\D--Desktop-projects-sam17\97597003-c1ef-4ca9-97e1-b0199192ff5f\scratchpad\halberg4\`. Reproduje el barrido de la espera, el canal incurable y los dos fuzz: cifras idénticas a las del brief. `junta.rs` da 8/8 y `espera.rs` 2/2.
- **Mis experimentos.** Están en `...\scratchpad\halberg4\modelo\tests\halberg4.rs` (x1 a x6). En `...\scratchpad\halberg4\modelo\src\motor.rs` añadí un campo, `Cfg::desfase_plan_us`, que solo suma en la comparación de `plan_drain`. Vale 0 por defecto y con 0 el comportamiento es idéntico. Se corren con `cargo test -p sam17-nucleo-modelo --release --test halberg4 <x1|x3|x5|x6> -- --ignored --nocapture`; x2 no está ignorada.
- **La TCM, sin reproducir.** Intenté compilar `carga_j2` con `j2-tcm` desde una copia de `huella` (`...\scratchpad\halberg4_huella\`). `rustc` cayó tres veces (0xc0000409, y luego metadatos incompletos) porque la máquina se quedó sin memoria comprometida: hasta `fork` falló, con 0xC000012D. No reproduje los bytes; los cito de `EN-PLACA.md`.
- **La rama `j2/huella-tcm` se movió durante la revisión.** A las 12:32 entró `638e844`, que cambia `j2_tcm.x` y añade `tcm_cierre.py`. Juzgo R-H4 contra ese commit.
- **No modifiqué ningún archivo de ningún worktree.**

---

## Execution Breakpoints Detected

### N1 · ALTA · B × C: la espera no cabe en la cota de `Reiniciando` junto con R-H1

**Evidencia en el papel:**
- Ficha C, L69: «La espera de la ficha B corre dentro de `Reiniciando` y no mueve el mayor hueco de sello».
- R-H1, L80: «Se pide **≤ 12 ms**».

**x1.** Regla 6 en 1 s y bloqueo del GPDMA1 de 1 ms. Inyecto una P2 no atómica de duración L que arranca en cualquier punto de los 4 ms siguientes al bloqueo, cada 25 µs (161 arranques). La tabla da los reinicios del chip:

| espera | L ≤ 10,5 ms | 11 ms | 11,5 ms | 12 ms |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 (máximo en `Reiniciando`: 97 periodos de 101) |
| 1 ms | 0 | 0 | 0 | 13 |
| 2 ms | 0 | 12 | 33 | 53 |

Con 3 en 1 s y con 2 en 100 ms y 2 ms de espera salen los mismos 12, 33 y 53: el problema es la espera, no `E`. Sin espera, esas dos reglas reinician el chip con el bloqueo solo (125 y 135 de 161).

**x6, la traza.** 2 ms de espera y P2 de 12 ms a +850 µs:
- Seis aplazadas entre +399 y +525 µs, todas hasta +2 115 µs.
- El planificador repide las seis a +13 092 µs.
- r0 y r1 llegan a `HECHA` (+13 102 y +13 108 µs).
- r2, r3 y r4 pasan a `Muerta` a +13 118 µs, en la cola serie de P4.
- El IWDG reinicia el chip a +115 ms.
- Sin espera: tres escaladas, la cuarta recuperación espera a la P2, `HECHA` entre +13 104 y +13 143 µs, y las seis siguen vivas (12,4 ms de 12,625 posibles).

**Qué rompe:**
- La espera son 2 ms en los que P4 no trabaja en la ranura y la cota sigue contando.
- La cota de 12,5 ms tenía de 0,2 a 0,6 ms de margen sobre R-H1. Cualquier espera mayor de unos 0,5 ms se lo come.
- Con eso, un bloqueo de 1 ms junto con una retención legal reinicia el chip.
- La espera de B y la cota de C son un solo número, y el papel las presenta como dos.
- Ningún fuzz lo ve: el fuzz retiene P2 «de 20 us a 6 ms» (`modelo/src/fuzz.rs:35`) y no produce ninguna aplazada.

### N2 · MEDIA · B: la espera alarga el apagón de las seis ranuras hasta su borde, y la ficha no lo cuenta

**Evidencia.** La columna de costo de la ficha B (L68) lista tres costos: el canal incurable, la avería que vuelve y el mecanismo nuevo. El apagón no está.

**x3.** Regla 6 en 1 s, en las cinco fases:

| bloqueo | espera | escaladas | plazos propios por ranura | mayor hueco sin tramas válidas, por ranura |
|---|---|---|---|---|
| 1 ms | 0 | 4 | 4 o 5 | 1 124 a 1 374 µs |
| 1 ms | 2 ms | 1 (6 aplazadas) | 1 o 2 | 2 249 a 2 374 µs, en las seis |
| 3 ms | 0 | 6 | — | reinicio del chip |
| 3 ms | 2 ms | 2 (12 aplazadas) | — | 4 249 a 4 374 µs, sin reinicio |

**Qué rompe.** El bloqueo acaba a +1 ms, pero las seis ranuras siguen aparcadas en `Reiniciando` hasta +2,1 ms. Samuel cambia 3 escaladas y la mitad de los plazos propios por 1 ms más (8 tramas) sin tramas en los seis módulos. El límite de cero artefactos audibles se mide por ese hueco, no por las escaladas.

## Concurrency Failure Risks

### N3 · MEDIA · B en `fw`: el planificador repediría con un reloj que P4 no mantiene

**Evidencia:**
- `fw/src/j2_tic.rs:1239`: `RELOJ_REC` solo se extiende dentro de `if !para_canales(hw)`, o sea, solo al pedir una escalada.
- `core/src/transporte_j2.rs:136`: «Hay que llamarla al menos una vez por vuelta de 32 bits».
- P3 extiende `RELOJ_PLAN` en cada pasada (`j2_tic.rs:1070`).
- El modelo lo tapa: P4 usa `self.tics` crudo (`modelo/src/motor.rs:1169`) y `plan_drain` usa el reloj extendido. Por debajo de 2³² tics los dos dan el mismo número.

**Por qué ocurre.** Una ranura sana no escala durante días. Tras una vuelta de 32 bits (6,2 días) sin pedir escaladas, `RELOJ_REC` pierde épocas: `extiende` detecta como mucho una vuelta, y solo si `bajo < ultimo`. Entonces `hasta_us` nace en un reloj atrasado, y P3, con el suyo, lo ve ya cumplido en cada pasada.

**Variante.** `desfase_plan_us` igual a una vuelta de 32 bits:

| bloqueo | aplazadas | P4 ocupada | muertes |
|---|---|---|---|
| 1 ms | de 6 a 24 | de 255 a 702 µs | 0 |
| 3 ms | de 12 a 92 | de 474 a 2 416 µs | 0 |

Es el reintento en cada tic que rompió la tercera pasada (N4b), acotado por el bloqueo y por la espera.

**Además:**
- Hoy no existe ningún canal de P4 a P3. Lo que hay es `REC_PEDIDA` y `REC_INCIDENTE_PEDIDO`, de P3 a P4.
- `thumbv8m.main` no tiene atómicos de 64 bits, y P3 lee `hasta_us` interrumpiendo a P4.
- Sin espera, el mismo atraso hace que la ventana vea reciente una concesión vieja. La probabilidad de una negada falsa es de unos 2·10⁻⁶ por primera petición tras el hueco (A).

**Lo que costaría llevarla a `fw`:**
- `solicita` en `recupera`, con una rama que vuelve sin `RESET` y sin `HECHA`.
- Una publicación nueva por ranura de P4 a P3, con orden `Release` y `Acquire`.
- Unas seis comparaciones por pasada de P3 (unos 5 ciclos por ranura).
- Que `hasta_us` se compare en el mismo reloj que lo fechó.

### N7 · BAJA · B: la aplazada deja el canal con `SUSP` pedido y el SPI sin resetear hasta 2 ms, y nadie sabe qué hace el bus en ese intervalo

**Evidencia.** `modelo/src/motor.rs:1178-1183`: `Aplazada` no toca el hardware modelado. En `fw`, la aplazada saldría de `recupera` antes del `RESET`.

**Qué rompe.** Sin espera, la transferencia a medias dura como mucho `T_CANAL` (25 µs) antes del reset. Con espera dura hasta 2 ms. Si el bloqueo se levanta dentro de la espera, no está modelado ni medido, ni hay página del RM, qué hace un canal con `SUSP` pendiente y un SPI maestro con `TSIZE` a medias. Lo que está en juego es si la trama abortada sale al cable tarde, y §4.2 promete «ninguna vieja».

## Context Integrity Violations

### N4 · MEDIA · C: el aserto no cuenta lo que la máquina hace

**Evidencia.**
- `core/src/transporte_j2.rs:361` y `:373` comparan `espera.saturating_add(periodos) > self.cota_…`, así que cada estado aguanta cota más 1 periodo.
- **x2** (puro, sobre `Transporte::con_cotas(200, 100)`, plazo 3, con `en_curso` y `hecho` en el último tic que no mata): de sello a sello hay **305 periodos = 38,125 ms**, no 37,875.
- Con el término de 12 ms del papel la suma es **50,125 ms > 50**: el aserto escrito es falso.

**El término de 12 ms no lo produce `fw`.**
- `compone` solo mira `fresca()` (`fw/src/j2_tic.rs:1032-1035`).
- `DMA2D` la llama para cada ranura en la misma pasada en que pide la recuperación (`j2_tic.rs:1107-1128`).
- Así que al llegar la `HECHA` la trama ya está en el buzón. La cola de R-H1 es la de una ranura `Libre` que espera al planificador (ficha D), y no se suma a las cotas.
- El hueco real de una ranura que sobrevive es de unos 38,1 ms más el retraso del tic.

**Qué falta además.** No hay término de tolerancia del oscilador del módulo sobre un 50 ms ESTIMADO (Voronov N2 lo pidió en la tercera pasada). Los 0,125 ms de margen son un 0,25 %.

**Qué rompe.** El aserto que la ficha C propone como puerta no describe ni el hueco real (38,1 ms) ni el del papel (49,875 ms). Su margen de 0,125 ms se apoya en una suma que se pasa 0,25 ms por arriba y sobra 12 ms por abajo.

## Orchestration Failure Modes

### N5 · MEDIA · H / R-H4: la cifra es la huella del binario de banco, y la comprobación que la sostiene no ve lo que se llama por puntero

**Evidencia:**
- `EN-PLACA.md:908`: «Dentro, el juez del banco (`juez_del_banco`, 38 B, y `memcmp`, 116 B)».
- `fw/j2_tcm.x:25-29` (worktree `huella`): los vectores del banco (`.text.TIM7 .text.DMA2D .text.JPEG`) y `j2_banco*`.
- Llamadas por puntero en `fw/src/j2_tic.rs` (worktree `huella`): `(p.bajada_fn)` en `:1038`, `(p.juez)` en `:1096` y `(hw.resetear)` en `:1259`.
- `fw/tcm_cierre.py` (worktree `huella`, `638e844`) solo sigue `bl|blx|b|b.w` con dirección inmediata, y nada del build lo llama.

**Qué rompe:**
- En el hub, el juez será el CRC (#267) y el compositor será el real. Los dos van por puntero y fuera de los patrones `*_j2`.
- Con eso, `tcm_cierre.py` pasa, y los 8 120 B y los 2 063 ciclos dejan de describir el binario.
- El `.rodata` del J2 (una tabla de CRC, por ejemplo; `EN-PLACA.md:879`: «Lo que queda fuera de la TCM son las constantes de `.rodata`») no está ni en los bytes ni en ninguna región.
- Este mecanismo ya falló en silencio una vez (§0.4, punto 26: la división de 64 bits). Lo encontraron los ciclos, no una comprobación.
- Lo bueno: `638e844` quitó el patrón de todo `sam17_nucleo_core`. En el hub habría llevado a la ITCM el USB-MIDI, el SysEx y los presets (`core` tiene 34 módulos, 6 del J2).

### N6 · BAJA · H / R-H4: lo que la obligación de memoria no nombra

**Evidencia:**
- `EN-PLACA.md:908`: la pila del anidamiento, «unos 0,85 KB» (E).
- `EN-PLACA.md:886`: «La tabla de vectores sigue en la AXISRAM2».
- `EN-PLACA.md:890`: el DWT «**no incluye** el apilado ni el desapilado».
- `fw/src/j2_tcm.rs` (worktree `huella`, `__pre_init`) escribe la DTCM entera, de `0x30000000` a `0x30020000`, por un ECC que se sospecha y no está verificado.

**Qué rompe:**
- La entrada y la salida de la excepción con la pila y los vectores fríos caen en los 337 ciclos entre el DWT (2 063) y el medidor (2 400), y nadie los ha separado.
- Con el CRC estimado, el medidor da del 15,2 al 16,5 % (papel, §3).
- «La caché fría deja de decidir la fila del J2» vale para los ciclos dentro del manejador, no para el tic tal como lo paga el hub.
- Inicializar la DTCM entera es una obligación para todo lo que viva en la DTCM, no solo para los 4 616 B del J2.

## Runtime Contradictions Across Layers

Es N1: B dice que la espera no mueve el hueco, y C dimensiona la cota contra R-H1 sin la espera. Las dos cosas son ciertas por separado, y juntas matan la ranura. Es también N4: el aserto de C contra la máquina de `core`.

## Universality Collapse Points

No hay hallazgo nuevo. N1 no depende de la regla (las tres dan 12, 33 y 53 de 161). N3 depende del tiempo de encendido, no del reloj del SPI.

---

## Comprobado y bien

- **Quién vuelve a pedir.** `plan_drain` repide una vez por aplazada. Lo hace con el mismo incidente (`rec_inc_pedido` no se toca) y se salta las ranuras `Muerta`.
- **Otra ranura aplazada a la vez.** Las seis aplazadas comparten el mismo `hasta`. P4, en serie, escala con la primera y las demás encuentran `IDLEF`: queda una escalada, no seis.
- **Otra escalada dentro de la espera.** Es imposible por construcción: toda petición dentro de la espera se aplaza al mismo instante. Al cumplirse, la negada es el camino K1 previsto.
- **El mismo incidente no se aplaza dos veces** en el modelo: con bloqueos de 1 y de 3 ms, `Reiniciando` llega como mucho a 13 periodos. Sin hambre del planificador, la espera no empuja a ninguna ranura más allá de su cota.
- **Escaladas solapadas:** ninguna en todo el barrido (`max_concurrent_esc` ≤ 1).
- **K2 a K5:** nada roto. `junta.rs` da 8/8 y `espera.rs` 2/2 en la copia.

## Execution Feasibility Verdict

- **B:**
  - **La regla.** Firmaría **6 en 1 s**. Frente a 2 en 100 ms aguanta bloqueos de hasta unos 11 ms (contra 5), y acota la avería que vuelve a 6 escaladas por segundo (contra 20). Sus 4 tramas de más por vecina solo existen con un canal incurable, que acaba en el mismo reinicio del chip 10 ms después.
  - **La pregunta de Samuel: sí, un bloqueo de 1 ms necesita espera entre reset y reset.** Un reset dentro de un bloqueo activo no cura nada (la reprogramación se vuelve a colgar a los 250–300 µs) y solo gasta presupuesto, tramas de las vecinas y plazos propios. Sin espera, el presupuesto mide cuánto dura un único suceso, no cuántos fallos hay.
  - **Pero no con estas cifras.** No firmaría 2 ms de espera junto con `Reiniciando` de 12,5 ms y R-H1 de 12 ms (N1). El costo del apagón (N2) y el de `fw` (N3) tienen que entrar en la ficha.
- **C: no se cierra.** Faltan tres cosas.
  - Un aserto que meta la espera: `cota_reiniciando > espera + inanición + recuperación`. Hoy es 12,5 contra unos 14,03 (N1).
  - El aserto de 50 ms contado como cuenta la máquina, con cota más 1 periodo por estado, y la decisión de si la cola de 12 ms existe: con ella, 50,125 > 50; sin ella, 38,125. Hace falta también la tolerancia del oscilador del módulo (N4).
  - El barrido de cotas × espera × R-H1 × duración del bloqueo, que no existe; x1 es una rebanada. Además, `fw` sigue con 100 y 100 tics.
- **R-H4: la cifra vale como huella del binario de banco** (8 120 y 4 616 B), **no como obligación del hub.**
  - Lleva dentro el juez y el compositor del banco.
  - Deja fuera el CRC y su `.rodata`, la pila (unos 0,85 KB, E) y la tabla de vectores.
  - La comprobación que la sostiene es un script manual que no ve las llamadas por puntero, que es por donde entrarán el CRC y el compositor reales (N5, N6).

El reloj de la recuperación y la cota de `Reiniciando` no leen la intención de la espera, solo sus microsegundos. **La ejecución ha hablado.**
