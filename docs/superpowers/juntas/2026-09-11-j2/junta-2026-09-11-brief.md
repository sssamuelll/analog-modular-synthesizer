# Brief de junta — 2026-09-11 — ¿Se puede confiar el J2 al SPI del STM32N657?

## 1. La pregunta que pone Samuel (textual, hoy)

> «si el chip que usamos tiene un defecto reportado por otra gente en internet en el que el
> diálogo por este bus se cuelga y puede pasar una vez cada varios minutos o cada varias horas
> no podemos seleccionarlo. nunca podríamos confiar en él. un instrumento de audio del calibre
> del que estamos construyendo no se puede permitir este tipo de defectos.»

La junta contesta tres cosas, en este orden:

1. ¿El defecto abierto es razón suficiente para descartar el N657 como plataforma HOY, sin placa?
2. Si no lo es: ¿cuál es el criterio de cierre MEDIBLE que convierte «confiamos en el chip» en una
   decisión y no en una apuesta, y en qué orden se consigue?
3. ¿Qué se hace hoy con la tarea 7 (el driver `j2_spi.rs`)?

Corrección previa del orquestador: en la conversación dije «el chip tiene un defecto». Los papeles
dicen «el chip **o su driver**, sin diagnosticar» (spec §0). La junta parte de la frase correcta.

## 2. Lo que está firmado y lo que arrastra

- Spec `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`, firmada por Samuel
  el 2026-09-10 («firmo formalmente», D1-D8 en vigor). §0: «hay un defecto abierto en el silicio o
  en su driver». Acta del 03-09: *«vamos a resolver esto pero como fabricantes de la nueva
  generación. el sam17 será el mejor sintetizador construido jamás»*. Lectura aplicada: el
  silicio nuevo y el Rust se quedan; la recuperación es propia; lo aprendido vuelve upstream.
- Plan `docs/superpowers/plans/2026-09-04-maestro-j2-recuperacion.md`: fase A (política en `core`,
  `maestro_j2.rs`, 14 tests verdes) HECHA y mergeada; fase B (driver + ejecutor) es la tarea 7-8.
- El N657 es la plataforma del instrumento ENTERO, no solo del hub:
  - hub: `2026-08-30-hub-n657-y-radios-design.md` D1 firmada (§2.2: «el mismo de la Voz»);
  - Voz: `2026-08-26-motor-digital-design.md` A-1 («El chip de la Voz es el STM32N657»), sellado
    el 26-08 (commit c542cd4);
  - tercer N657 para cámara/IA (hub D3', firmada 09-09); cuarto para interfaz de audio (pendiente).
  - Los DOS extremos del J2 son N657: maestro (hub) y esclavo (Voz).
- Tamaño de lo que arrastra un cambio de chip: 70 archivos nombran al N657 (23 specs, 3 planes,
  26 en hardware/, 12 en software/); 43 commits; el pase de `fw` a `embassy-stm32` (#250, fase A)
  cerrado el 08-09; contribuciones upstream ya hechas: stm32-data#911 (mergeada), embassy#6939.
- La única forma de medir: la Discovery STM32N6570-DK, $223,67 (#231), **aplazada el 28-08 por
  decisión de Samuel: no hay plata**. Hitos: 3 «El cerebro arranca» (6 abiertos), 4 «Kit de
  pruebas: cerebro + una voz» (31 abiertos).

## 3. La evidencia sobre el defecto, al 2026-09-11

### 3.1 embassy-rs/embassy#5607 «STM32N6 SPI Hanging» (abierto 05-03, 28 comentarios, último 03-09)
Texto completo: `5607-body.md` y `5607-comments.md` en esta misma carpeta.

- **Dos reportantes**, los dos con embassy (Rust):
  - jake-taf, Discovery DK: bloqueante a **100 kHz**, CS por **GPIO** (`SSM=1`), **`TSIZE=0`**
    (transferencia sin fin), cuelga «10-900 s» y luego «cada 30-120 min». Con DMA también
    (esperando `EOT`). Escribir a `TXDR` lo destraba en bloqueante, no en DMA. Visto en **SPI5 y
    SPI1**. Corrupción 1-2 veces por minuto: un bit duplicado, el CS sube antes de terminar.
    Probó `critical_section` (no era interrupciones), distintas velocidades (no cambia).
  - stefkoriz: ADC de 16 bit a 352 kHz disparado desde una ISR de timer, «freeze» tras 1-2 s,
    sale solo reiniciando el SPI. Su volcado: `SR=0x12017` (CTSIZE≠0, **RXP=1**), distinto
    del de jake-taf (`RXP=0`). No se sabe si usa embassy o C.
- **La comparación con el HAL de C de ST NUNCA se corrió** (jake-taf, 03-09: *«We wrote some
  small test firmware for C, but had issues getting probe-rs working on C»*). Hoy no existe
  ninguna evidencia fuera de embassy para el N6.
- **Nadie probó NSS por hardware** (jake-taf, 03-09: *«I haven't tried that mode»*).
- Los mantenedores (xoviat) no tienen diagnóstico; probaron esperar `TXC` tras `read`: no bastó.

### 3.2 La errata publicada por ST para el MISMO bloque SPI en el H7 — `es0396-h7-spi-2.14.2.md`
ES0396 Rev 9 §2.14.2 **«Master data transfer stall at system clock much faster than SCK»**:
> *«SPI/I2S master data transfer can stall upon setting the CSTART bit within one SCK cycle
> after the EOT event (EOT flag raise) signaling the end of the previous transfer.»*
Soluciones que ST documenta: (1) apagar y encender el SPI tras cada EOT; (2) esperar ≥ 1 ciclo de
SCK entre el EOT y CSTART; (3) evitar EOT (TSIZE=0 y arrancar solo por escrituras al TxFIFO).
Presente en TODAS las revisiones de silicio del H750/H753 (A A A). El H7 es `spi_v4`; el N6 es
`spi_v5`; registros y driver comunes.

**Por qué importa para #5607 (hipótesis del orquestador, no diagnóstico):** RM0486 p. 3492 dice
que `EOT` «is set by hardware as soon as a full transfer is complete, that is when SPI is
re-enabled». El driver de embassy hace `SPE=0 → SPE=1 → CSTART` en cada llamada, con nanosegundos
entre `SPE=1` (que levanta `EOT`) y `CSTART`. A 100 kHz un ciclo de SCK son 10 µs: el repro de
jake-taf cae DENTRO de la condición de la errata en cada transferencia. Que cuelgue solo a veces
es coherente con una carrera. Falta: leer si ES0620 (N6) lista este ítem, y medirlo.

### 3.3 Tres hilos del foro de ST, en C, mismo bloque
- **H743** (community.st.com td-p/200091): el maestro deja de dar reloj tras horas; el usuario
  identificó la errata 2.14.2; las soluciones 1 y 2 no bastaron; **lo curó `HAL_SPI_Abort()`
  antes de cada transferencia**, o sea un reinicio completo antes de cada arranque.
- **H7** (td-p/404683): `EOT`/`TXC` se disparan justo tras `SPE=1`, sin datos; solución del
  usuario: armar `EOTIE` después de arrancar. Es el orden `SPE=1 → EOTC → EOTIE` de la spec D2.
- **H723** (td-p/774693): «SPI stop working randomly»; resultó ser hardware o arnés, no el
  periférico («The SPI is not known to start and stop working randomly»).

### 3.4 La errata del N6: ES0620 Rev 1 (dic 2024), «STM32N6xxxx device errata»
Existe (st.com/resource/en/errata_sheet/es0620-stm32n6xxxx-device-errata-stmicroelectronics.pdf).
st.com no contesta a curl. **NO LEÍDA. HUECO: pedirle el PDF a Samuel.** Sin ella no se sabe si el
N6 lista el gemelo del 2.14.2 ni qué otras limitaciones del SPI reconoce ST.

### 3.5 Lo que NO hay
- No hay reporte de cuelgue del SPI del N6 en C en el foro de ST (búsqueda del 11-09; puede ser
  por juventud del chip: sale en «full production» en 2025-2026).
- No hay tasa medida en NUESTRO montaje (reloj 10-34,5 MHz, NSS hw, TSIZE>0, 8 kHz).

## 4. Lo que el diseño firmado YA aplica (spec D1-D4, resumen)

- SPI apagado entre transferencias (= solución 1 de la errata), `TSIZE > 0` siempre (R-MJ1), NSS
  por hardware (D1), `EOTC` después de `SPE=1` y antes de `EOTIE` (D2), plazo por mensaje sobre las
  DOS esperas (D2, D3; ≤ 220 µs), reinicio completo según el manual al vencer (D4, ocho pasos; es
  lo que el hilo del H743 hace con `HAL_SPI_Abort`), cuenta y marcas `inestable`/`muda` (D7).
- Margen: recuperación peor caso 490 µs contra el watchdog del módulo de ~50 ms: **102×**.
- Corrupción (bit duplicado, CS antes): CRC del sobre la caza; lo que tiene red se repara en
  ≤ 1 ms; `EVENTO` no tiene red: un golpe perdido por cuelgue (§3, función sin cifra).
- **NO aplica todavía:** «esperar ≥ 1 ciclo de SCK entre `SPE=1` y `CSTART`» (solución 2).
  Costo: ~100 ns al piso de 10 MHz, 29 ns a 34,5 MHz. Sería una enmienda de dos líneas a D2.

## 5. Las opciones sobre la mesa

- **A.** Seguir con el N657 y el diseño firmado. Escribir el driver hoy (tarea 7) añadiendo la
  solución 2 de la errata. La Discovery cuando haya plata. Puerta dura: soak ≥ 24 h a 8 kHz con
  NSS hw + TSIZE > 0 (`resistencia_j2.csv`) **antes de fabricar cualquier PCB** con N657.
- **B.** Como A, pero la Discovery sube a prioridad 1 (antes de más papel del J2), y el primer
  experimento es el soak con el **HAL de C de ST** (dirime silicio vs driver en un día); el segundo,
  el driver propio. Cambia el orden, no el diseño.
- **C.** Cambiar de chip ahora. Arrastra hub, Voz, mago, interfaz de audio, 70 archivos, tres
  papeles firmados y el pase a embassy-stm32; sin evidencia de que otro chip no traiga su propia
  errata (el H7, el candidato «maduro» obvio, la trae documentada y sin corregir).
- **D.** Quedarse con el N657 pero sacar el J2 del bloque SPI (USART síncrono ya previsto para 2
  ranuras). Límite: el peldaño 2 de 34,5 MHz no lo alcanza un USART; rehacer cabecera, punto a
  punto y censo de pines.
- **E.** Otra que la junta proponga, con su costo.

## 6. Archivos que la junta puede leer (rutas absolutas)

- Esta carpeta (`C:\Users\simon\AppData\Local\Temp\claude\D--Desktop-projects-sam17\b88958db-8a0e-482e-a76f-f31fa9e9cc5d\scratchpad\`):
  `5607-body.md`, `5607-comments.md`, `es0396-h7-spi-2.14.2.md`.
- Repo `D:\Desktop\projects\sam17`:
  - `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md` (la spec firmada)
  - `docs/superpowers/plans/2026-09-04-maestro-j2-recuperacion.md`
  - `docs/superpowers/specs/2026-08-30-hub-n657-y-radios-design.md` (§2.2, §11)
  - `docs/superpowers/specs/2026-08-26-motor-digital-design.md` (A-1, §10 riesgos 6 y 9)
  - `software/nucleo/core/src/maestro_j2.rs` (la política, con tests)
  - `software/nucleo/fw/src/j2_spi.rs` (cabecera del driver), `software/nucleo/fw/EN-PLACA.md`
  - `docs/reference/datasheets/stm32n6-rm0486-rev4.pdf` (RM; las citas de la spec ya están en texto)
