# Serrano · tercera pasada · papel-v3 absorbido (commit `4c639f0`) · 2026-10-17

*Informe de la tercera pasada, acotada a los cuatro mecanismos nuevos (§2.2, §2.5, §2.7, §2.11/R-H8) y al estado de mis hallazgos de la segunda pasada.*

**Referencias.** Al papel lo cito por sección. A la spec y al código, por línea. No modifiqué ningún archivo.
- `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v3.md`
- `.../2026-10-17-j2-transporte/junta2_serrano.md`, `junta2_halberg.md`, `acta-2026-10-17.md`
- `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`
- `software/nucleo/core/src/maestro_j2.rs` y `transporte_j2.rs`
- `software/nucleo/fw/src/j2_tic.rs` y `fw/src/bin/tic_estres.rs`

## A) Diagnóstico

- **Qué es.** Un papel de decisión con siete fichas. Su respuesta a la segunda pasada son cuatro mecanismos que no están construidos.
- **Implementabilidad.**
  - La tabla de plazos (§2.4) y el paso 1 de §2.5 cuadran con el código.
  - Tres de los mecanismos nuevos (`SUCIA` como entrada, la limpieza por identidad y el reintento tras una denegación) no dicen cómo se combinan con el intercambio de banderas entre el tic y la recuperación (`REC_PEDIDA`/`REC_EN_CURSO`/`REC_HECHA`) ni con la reprogramación de `escala()` fuera de su sección crítica.
  - R-H8(3) no se puede convertir en una prueba de pasa o falla sin elegir antes entre dos modelos del supervisor.
- **Hallazgos nuevos.** 0 BLOCKER, 5 ALTA, 3 MEDIA.
- **Método.** Leí el código y los textos y busqué con grep. La aritmética es a mano. No ejecuté nada.
- **Límite.** No verifiqué en el RM qué hace `CR.RESET` sobre un canal que no llegó a `SUSPF`/`IDLEF`. Tampoco verifiqué si `DWT_CYCCNT` cuenta durante `WFI`/`WFE` en el M55.

## B) Hallazgos nuevos

**1. [ALTA] [CONTRA, GAP, OPS] R-H8(3): el «mayor hueco de sello» está mal contado, y la relación entre la ventana y `T_IWDG` admite dos modelos con latencias distintas**
- **Evidencia.**
  - R-H8(3): «su ventana es mayor que el mayor hueco de sello del diseño (`Vencida` + `Reiniciando`, 37,5 ms, más el periodo del supervisor)».
  - §2.5: «`cota_vencida + cota_reiniciando + 12 ms < T_WATCHDOG_TRAMA_US`».
  - §2.2: «La espera de `Libre` sin bajada fresca no tiene cota en la máquina: es la espera del planificador, y la vigila el sello».
  - §2.6: «Tras una recuperación está vacío hasta que el planificador compone otra trama».
  - §2.11: «con 5 ms y 60 ms, a los 62–65 ms». `junta2_halberg.md:230`: «+7 a +10 ms | El supervisor deja de alimentar».
  - Spec l.308 (el IWDG lo alimenta el hilo), que §2.9 mantiene.
- **Problema.**
  - (a) Con las piezas del propio papel, el hueco de sello máximo es: último armado, plazo (≤ 3 tics), `Vencida` ≤ 25 ms, `Reiniciando` ≤ 12,5 ms y `Libre` esperando al planificador (R-H1 admite 12 ms). Suma **~49,9 ms (A)**, no 37,5. El aserto de §2.5 ya suma ese término de 12 ms. R-H8(3) y la fila D5.4 de §6 («hasta ~37,5 ms») lo dejan fuera, aunque es la espera que §2.2 y la ficha D encargan al sello.
  - (b) Hay dos modelos posibles:
    - Si la ventana del supervisor va **en serie** con `T_IWDG` (deja de alimentar pasada la ventana), el reinicio llega a ventana + `T_IWDG`. Con los mínimos que permite (3), eso da ≥ 42,5 + 55 = **97,5 ms (A)**.
    - Si la ventana **es** `T_IWDG`, que es el modelo de Halberg (deja de alimentar a los 7–10 ms y absorbe el IWDG), la condición «ventana > 37,5 + P_s» sobra.
    - §2.11 cita la latencia del segundo modelo. R-H8(3) escribe el primero.
  - (c) §2.11 dice que el reinicio «no depende de `Muerta` ni de las cotas», pero (3) deriva la ventana de las cotas.
  - (d) La inanición del hilo, que es quien alimenta el IWDG, no entra en (3).
- **Qué rompe.**
  - Con la ventana mínima que (3) permite (42,5 ms), un cuelgue seguido de una retención del planificador ≤ 12 ms después de `HECHA` reinicia el chip, y todo eso está dentro de R-H1.
  - O bien Samuel lee 62–65 ms donde la configuración que exige (3) da ≥ ~97 ms.
  - §5.2(g) no tiene un criterio que se pueda escribir.
- **Falta decidir.** ¿La ventana y `T_IWDG` van en serie o son lo mismo? ¿El hueco que las acota incluye `Libre` esperando al planificador? ¿Qué inanición del hilo entra?

**2. [ALTA] [CONTRA, SCOPE, UX] R-H8(2) deja que el supervisor reinicie el chip por `inestable`/`muda`: revive H-6 y contradice el objetivo de §2.2**
- **Evidencia.**
  - R-H8(2): «o las marcas `inestable`/`muda`, porque «armé» solo no ve una ranura que se rearma para siempre».
  - §6, fila D7: «qué hace el instrumento con una ranura `inestable` o `muda`» sigue siendo del supervisor».
  - Spec l.350: «toca la política de partes y voces (`partes.rs`, `Repartidor`) y es decisión de otro papel».
  - Spec l.294: «con una ranura sin módulo lo habría disparado diez veces por segundo (H-6)».
  - §2.8: «a 12 por segundo o más las seis quedan `inestable`».
- **Problema.**
  - La spec define las marcas como «información, no acción» (l.344). La fila de §6 atribuye mal la decisión: la spec se la da a partes y voces, no al supervisor.
  - Camino `muda` (40 subidas malas, 5 ms):
    - Al desenchufar un módulo, la identidad se retira según la cadencia del descubrimiento I²C, que no está especificada. Si tarda más de 5 ms, `muda` llega antes y el instrumento se reinicia.
    - Es el caso que §2.2 evita por la vía de la cota («el instrumento se reiniciaría por quitar un módulo»), y es H-6.
    - Un módulo que se cuelga o reinicia también reinicia el instrumento.
  - Camino `inestable`: §2.8 hace puntuar el tic tardío en las seis ranuras, así que una sobrecarga fuera de R-H2 acaba en reinicio.
  - La fila pendiente de la spec (l.619) ya traía la opción. v3 la sube a requisito y a condición §5.2(g) sin elegir.
- **Qué rompe.** Desenchufar un módulo en directo, o que uno muera, reinicia el instrumento entero, y los seis módulos sueltan las notas. Una sobrecarga deja de ser un contador y pasa a ser un reinicio.
- **Falta decidir.** ¿R-H8(2) usa el sello «armé y alguno de los últimos N terminó» o las marcas? Si son las marcas, ¿quién firma que un módulo mudo reinicie el instrumento?

**3. [ALTA] [STATE, GAP] `SUCIA` como entrada solo está definida en `Vencida`, pero la escalada marca todas las ranuras; falta su precedencia frente a `reinicio_hecho`**
- **Evidencia.**
  - §2.2, fila: «`Vencida` | `sucia` (escalada en curso) | `espera += periodos`; no se lee ni se arma».
  - §2.2: «Ahora la espera sigue contando contra la cota».
  - `j2_tic.rs:1085-1090`: marca toda ranura con `HW`. `:1099-1105`: reprograma fuera de la sección crítica. `:803-805`: hoy el tic se salta la ranura.
  - `j2_tic.rs:220-263`: `programa()` escribe `TR1`, `TR2`/`REQSEL` y la dirección del periférico. `:340-345`: `arma()` solo escribe `BR1`, la dirección de memoria y `CR`.
- **Problema.**
  - `Libre`, `Reiniciando` y `Muerta` con `sucia` no tienen fila.
  - `Libre` + `sucia`:
    - Si rigen las filas de `Libre`, el tic (nivel 1 sobre el 4) arma durante el bucle de reprogramación sobre canales que el reset por RCC dejó con dirección de periférico 0, `REQSEL` 0 y `TR1` a cero.
    - Si se conserva el salto, no hay cota, y la congelación H2/A8 sigue intacta para las ranuras `Libre`, que es justo lo que §2.2 dice haber arreglado.
  - Las recuperaciones van en serie dentro de `JPEG` (`j2_tic.rs:1165-1168`). Una ranura B puede quedar en `Vencida` o en `Reiniciando` con `HECHA` ya publicada cuando la ranura A escala en la misma pasada. Para `Reiniciando` no hay fila. El párrafo de precedencias no menciona `sucia`. En el orden de la tabla, `reinicio_hecho` va primero, y B arma antes de que `escala()` la reprograme.
- **Qué rompe.** Un DMA con el lado del periférico en sus valores de reset: escritura o lectura en la dirección 0, o un error de bus. O bien unas ranuras `Libre` congeladas sin cota hasta que actúa el supervisor.
- **Falta decidir.** ¿En qué estados entra `sucia`? ¿Gana a `reinicio_hecho`? ¿Qué acota `Libre` + `sucia`?

**4. [ALTA] [STATE, CONTRA] La limpieza por identidad retirada pide la recuperación «en vuelo», y el intercambio de banderas tic-recuperación (`REC_*`) no tiene cómo invalidarse fuera de `Vencida`/`Reiniciando`**
- **Evidencia.**
  - §2.2: «la pide el planificador cuando la política pasa a `Vacia` con una transferencia en vuelo o vencida; la ranura vuelve a `Libre` sin armar».
  - `j2_tic.rs:821-832`: `REC_*` solo se leen en `Vencida`/`Reiniciando`. `:913-918`: solo se limpian al salir de ahí.
  - `j2_tic.rs:356-357`: «la recuperacion solo lo toca dentro de la seccion critica de la escalada».
  - `transporte_j2.rs:225-251`: `Armada` no tiene ninguna entrada de la recuperación.
- **Problema.**
  - «En vuelo» es `Armada`, y no hay fila para `Armada` con recuperación.
  - Basta una retención de P2 que cruce un tic: el tic ve terminar la transferencia (`GiroOk` → `Libre`) antes de que corra P4. La limpieza deja entonces `REC_EN_CURSO` y `REC_HECHA` en verdadero para siempre.
  - Cuando el módulo vuelve y la ranura vence más tarde, el tic lee ese `reinicio_hecho` viejo y rearma sobre un SPI colgado sin recuperación. La recuperación de verdad cae después sobre la transferencia siguiente, ya armada. Son dos manos sobre el mismo canal, lo que D5 mató.
  - La política solo conoce `Vacia`/`Activa`, así que no sabe si hay algo «en vuelo o vencida». El planificador tendría que leer `Transporte`, que el código reserva al tic. No está especificado.
  - Una ranura `Muerta` sin identidad «no cuenta para el supervisor». Queda muerta hasta apagar el instrumento, y reenchufar un módulo la vuelve activa sin sello, así que el chip se reinicia al enchufar. Ninguna ficha lo dice.
- **Qué rompe.** Desenchufar un módulo desfasa el intercambio de banderas. Un cuelgue posterior se da por recuperado sin que haya recuperación. Hay reinicio al reenchufar.
- **Falta decidir.** ¿A qué estados se aplica la limpieza? ¿Quién lee el estado del transporte, y cómo? ¿Cómo se invalidan `REC_*` fuera de `Vencida`/`Reiniciando`? ¿Qué pasa al enchufar un módulo en una ranura `Muerta`?

**5. [ALTA] [ASSUMP, CONTRA, OPS] El permiso de escalada cuenta plazos de cualquier causa, no escaladas, y el reintento tras la denegación no tiene disparador**
- **Evidencia.**
  - §2.5: «concede `escalar` mientras la ranura que pide no tenga más de `umbral_escalada` plazos vencidos propios en la ventana de salud».
  - Ficha B: «hasta 3 escaladas seguidas en ~1 ms (E) antes de perder el permiso».
  - §2.8: «Un tic tardío **sí** puntúa en la salud».
  - §2.5: «no publica `HECHA`, reintenta parar cada tic» y «ninguna transición nueva ni escritor nuevo».
  - `j2_tic.rs:1000-1009, 1165-1168`.
- **Problema.**
  - El permiso cuenta los plazos propios del cuelgue del SPI (#5607), de `error_dma` y del tic tardío. «3 escaladas» solo es cierto si cada plazo escala.
  - Tres o cuatro tics tardíos en 1 s niegan la escalada a las seis ranuras durante hasta 1 s. Que sean tres o cuatro depende de si cuenta el plazo que pide, y §2.5 no lo dice. Un canal que ignore `SUSP` en ese segundo acaba así: `Reiniciando`, 12,5 ms, `Muerta` y reinicio del chip. Con permiso habría costado 650 ns.
  - «Reintenta cada tic» no tiene disparador:
    - `REC_PEDIDA` se consume con `swap`, y solo `PlazoVencido` la vuelve a poner. Una ranura en `Reiniciando` no emite ninguno.
    - O nadie reintenta, o hace falta una vía nueva que despierte P4 cada tic.
    - El propio `escalar` es un noveno elemento compartido (lo escribe el nivel 3 y lo lee el 4) que §2.1 no lista.
  - Reintentar cuesta hasta `T_CANAL` por tic y ranura: el **20 % de un núcleo por ranura denegada (A)**. Eso no está ni en D7.2 ni en §3.
  - «Hace el `RESET` por canal; si los canales no paran» no dice si se escribe `RESET` sobre un canal sin `SUSPF`. El código no lo hace (`j2_tic.rs:1065-1069`).
  - La ficha B no dice que la denegación acaba en reinicio del instrumento (Halberg H6.3).
- **Qué rompe.** Una sobrecarga fuera del presupuesto convierte un fallo curable en un reinicio del instrumento. Además, quien lo implemente no tiene un camino de reintento definido.
- **Falta decidir.** ¿El permiso cuenta plazos propios o escaladas propias? ¿Quién reintenta, y con qué coste? ¿La ficha B declara el reinicio?

**6. [MEDIA] [CONTRA, ASSUMP] §2.7: la fórmula no sigue a la pared «a ±1 periodo», y su error tiene un solo signo**
- **Evidencia.**
  - §2.7: «suma `max(1, round(Δciclos / ciclos_por_periodo))`» y «sigue a la pared a ±1 periodo, y el error deja de tener un solo signo».
  - §2.7: «Si el contador de ciclos está parado o la diferencia es absurda, suma 1».
  - `transporte_j2.rs:95` (`edad: u8`).
- **Problema.**
  - Redondear intervalo a intervalo no telescopa. Contraejemplo (A): latencias de entrada 0; 0,7 p; 0; 0,7 p… dan intervalos de 1,7 p y 0,3 p, que cuentan 2 y `max(1, 0)` = 1. Son 3 por cada 2 periodos reales (+50 %), sin cota.
  - Toda entrada con latencia ≥ 0,5 p seguida de una normal suma +1, y nada resta. El reloj adelanta.
  - Dentro de R-H2 (≤ 60 µs < 62,5) la suma es exacta. El mecanismo solo se aparta de contar entradas fuera del presupuesto, y ahí se equivoca.
  - Efectos de ese adelanto:
    - Las cotas duran menos en tiempo de pared: 25 ms caen hasta 16,7 ms.
    - La ventana de D7.3 se acorta, y con ella `inestable` y el permiso se vuelven menos sensibles.
  - Otros puntos:
    - «Absurda» no está definida.
    - R-H9 no dice si `CYCCNT` cuenta en `WFI`/`WFE` (no especificado). Si no cuenta, todo vuelve en silencio a contar entradas, y la cota de tiempo de `T_CANAL` tampoco vale. A la cota por número de lecturas no le ponen cifra.
    - `edad += periodos` con `edad: u8` desborda con un bloqueo de más de ~32 ms. El papel solo ensancha «los contadores de espera».
- **Qué rompe.** La propiedad que justifica el mecanismo es falsa, y las cotas en µs de la ficha C no son µs de pared justo donde el cambio importa.
- **Falta decidir.** ¿Qué error máximo se acepta en el reloj reconstruido, en qué régimen y con qué prueba? ¿Qué es «absurda»?

**7. [MEDIA] [CONTRA, AMB] Ficha C: dos versiones del aserto y dos cifras de inanición en la misma celda**
- **Evidencia.**
  - Ficha C: «la suma menos 12 ms de margen es menor que la ventana del módulo (~50 ms)».
  - §2.5: «`cota_vencida + cota_reiniciando + 12 ms < T_WATCHDOG_TRAMA_US`».
  - Ficha C, «Otra»: «vio un máximo de 16,3 ms de inanición del planificador, que mataría la ranura».
  - R-H1: «Se pide **≤ 12 ms**».
  - `maestro_j2.rs:27-32`: `T_WATCHDOG_TRAMA_US` es ESTIMADO, con techo HUECO.
- **Problema.**
  - Las dos versiones no dicen lo mismo:
    - La de la ficha: 25,5 < 50, con 24,5 ms de holgura.
    - La de §2.5: 49,5 < 50, con **0,5 ms (1 %)** sobre un ESTIMADO.
  - Si 16,3 ms es plausible con un 6 % de ocupación de P2 (`junta2_halberg.md:158-159`), R-H1 no se cumple en un hub modesto y el aserto falla: 25 + 12,5 + 16,3 = 53,8 > 50 (A).
  - Si R-H1 se cumple, la alternativa 12,5 + 12,5 sobrevive a 12 ms (`tic_cota`: sobrevive a 12, muere con 14) y desaparece la razón para los 25 ms.
  - Repetir `tic_cota` (una ranura, sin contenido, retención a la hora exacta) no ejerce el P2 encadenado (C1), que es lo que R-H1 mide ahora.
- **Qué rompe.** Samuel firma una cota justificada con 16,3 ms y aseverada con 12 ms, con una puerta que depende de la tercera cifra de un ESTIMADO.
- **Falta decidir.** ¿Qué inanición dimensiona las cotas? ¿Cuál de las dos desigualdades es el aserto?

**8. [MEDIA] [AMB, OPS] El estatus de las cifras: la leyenda no tiene «simulado», el simulador no está en el repo, y el cumplimiento de «cero artefactos» cita la evidencia equivocada**
- **Evidencia.**
  - §0: «**(M)** medida en el banco, **(A)** aritmética sobre lo medido, **(E)** estimada».
  - `junta3-brief.md` §3: el simulador «está fuera del repo, en el directorio temporal de la sesión».
  - §2.8: «a 12 por segundo o más las seis quedan `inestable`». `maestro_j2.rs:418-426`.
  - §2.10: «En funcionamiento normal v3 lo cumple en lo medido (4,8 millones de giros, ninguno perdido; M)».
- **Problema.**
  - Hay cifras simuladas que sostienen decisiones:
    - ficha B: 4 000/s y 38 %;
    - ficha C: 16,3 ms;
    - los 60 µs de R-H2 (umbrales de δ marcados «A/E»);
    - §2.11: 62–65 ms y 56–222 ms;
    - §4.1: 36 303.
  - El simulador vive en un directorio temporal. Cuando se limpie, la evidencia de tres fichas no se podrá reproducir.
  - Cifras sin etiqueta o con la etiqueta equivocada:
    - «12 por segundo»: con umbral 10 y ventana de 1 s, el código da ≥ 9/s con eventos periódicos.
    - «~50 ms», `umbral_inestable` = 10 y «1 s»: son ESTIMADO en el código.
    - «~1 µs más de enmascarado» (§2.5).
    - «los primeros 120 (M)» es un ajuste sobre medidas, o sea (A).
  - §2.10 cita como cumplimiento el soak de 600 s con patrón regular a `VeryHigh`, que §4.2 declara inválido para el contenido. Los marcos numerados fueron con una ranura y a `Medium`.
- **Qué rompe.** Hay decisiones apoyadas en evidencia que no se puede reproducir, y el cumplimiento de un límite firmado se apoya en una corrida que el propio papel invalida.
- **Falta decidir.** ¿Qué estatus llevan las cifras simuladas, y dónde se versiona el simulador?

## Mis hallazgos de la segunda pasada que no quedaron resueltos

- **S3: parcial.** R-H8 existe, pero la relación entre ventana, 37,5 ms y `T_IWDG` está mal planteada (hallazgo nuevo 1).
- **S5: parcial.** §2.10 lista las exposiciones, pero no decide si las que ocurren bajo fallo violan «cero artefactos». `Muerta` va con «—» en «Cuánto», D6 sigue con cuatro valores y el cumplimiento cita el soak equivocado (8).
- **S6: parcial.** El presupuesto de 60 µs sale de la simulación, y ninguna condición de §5.2 provoca en banco un tic tardío.
- **S7: parcial.** La aritmética está, pero no hay latencia máxima aceptada ni medida. El porcentaje de la ficha E usa la diferencia peor contra peor (65–90 µs), cuando la media (+140) es mayor.
- **S8: parcial.** §5.2(a) añade `transporte` y `regimen_cache`, pero la puerta sigue sin filtrar por `ranuras` (2 200 frente a 1 967) ni por `periodo`. El `return 2` fijo (#369) no aparece.
- **S10: parcial.** Hay leyenda, pero quedan cifras sin etiqueta o con la etiqueta equivocada (8).
- **S11: parcial.** La unidad de R-H1 está corregida, pero el reloj reconstruido no cumple lo que promete (6) y las cotas se sostienen con dos cifras de inanición (7).
- **S12: parcial.** En (d), el esclavo sigue siendo una tarea de P2 sobre el GPDMA1 compartido: no puede cubrir ni la escalada ni los golpes de P2, y el papel no lo dice.
- **S13: parcial.** `tic_estres` no compila con `VeryHigh` (`tic_estres.rs:34-36`), así que en la ficha F «con sus bordes» solo vale si el arnés va a `Medium`. Los 16 contenidos elegidos a mano siguen sin cubrir contenido arbitrario.
- **S15: parcial.** La fila D7 de §6 atribuye mal la decisión (2). D7.2 (`T_REINICIO` 20 frente a 6 µs medidos, «16 % por ranura») no tiene fila. Las constantes de R-MJ4 siguen siendo una promesa («en `Umbrales` o en una estructura con aserto»).
- **Resueltos:** S1, S2, S4 (el mecanismo nuevo tiene sus propios problemas, hallazgo 5), S9 y S14 (salvo 3 y 4).

## Las fichas, sin leer el resto

| Ficha | ¿Se contesta sola? | Qué falta en la celda |
|---|---|---|
| A | No se reabre (brief §1) | — |
| B | No | Que la denegación acaba en reinicio del chip (§2.11), y que «3 plazos propios» no es «3 escaladas» (5) |
| C | Casi | Dos asertos y dos cifras de inanición en la misma celda (7) |
| D | No | «Pone en juego al supervisor» remite a §2.11 y R-H8, y R-H8(3) deja fuera esta espera (1) |
| E | Sí | El porcentaje es peor contra peor (línea S7) |
| F | Sí | Ver la línea S13 |
| G | Por remisión | (g) hereda la ambigüedad de R-H8 (1, 2) |

## Comprobado y correcto

- La tabla de §2.4 cuadra en sus doce celdas con `plazo_us` (`maestro_j2.rs:150-154`) y `tics_de_plazo` (`transporte_j2.rs:35-44`). `TONO` de 41 B a 6,25 MHz: 126 µs, 2 tics.
- Las precedencias error DMA > giro > plazo y hecho > en curso > cota coinciden con `transporte_j2.rs:225-275`.
- §2.5 paso 1 (`SUSPF` o `IDLEF`, con una relectura antes de rendirse) coincide con `j2_tic.rs:1048-1066`.
- La descripción del riesgo H2/A8 (marca dentro de la sección crítica, reprogramación fuera) es fiel a `j2_tic.rs:1081-1105`.
- Las cifras de Halberg que se citan (4 000/s, 38 %, 16,3 ms, 62–65 ms, 56–222 ms, umbrales de δ, 18 µs) coinciden con `junta2_halberg.md`.
- Aritmética: 250 − 185 = 65, 250 − 160 = 90 y 250 − 110 = 140. 25 + 12,5 + 12 = 49,5. El ajuste «125 µs sobre 120» reproduce 1,44, 7,04 y 23,0 giros por golpe.
- La cita del acta en §1 es fiel.

## C) Preguntas que el documento evita

1. ¿La ventana del supervisor y `T_IWDG` van en serie o son lo mismo, y qué hueco de sello las acota? (1)
2. ¿Puede un módulo desenchufado, mudo o colgado reiniciar el instrumento? (2, 4)
3. ¿En qué estados entra `SUCIA`, y qué gana entre `sucia` y `reinicio_hecho`? (3)
4. ¿Cómo se invalidan `REC_*` cuando la recuperación cae fuera de `Vencida`/`Reiniciando`? (4)
5. ¿El permiso cuenta plazos o escaladas, y quién reintenta tras la denegación? (5)

## D) Riesgos por categoría

- **Técnico:** 3, 4, 6 (y 5).
- **Producto:** 1, 2, 5 (reinicios del instrumento que ninguna ficha declara) y 7.
- **Ejecución y operaciones:** 1 y 8.

## E) Aclaraciones inmediatas

No hay BLOCKER. Las ALTA 1 a 5 cambian lo que firman las fichas B, C, D y G, o abren reinicios del instrumento que ninguna ficha declara. Conviene cerrarlas antes de la firma.
