## Halberg — viabilidad en runtime, junta del 2026-09-11

Corrí once bloques de aritmética antes de abrir la boca. Todo lo que sigue sale de `scratchpad\junta_halberg\sim.py` (salida en `salida.txt`, 182 líneas), del papel firmado `docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md` y de la política `software\nucleo\core\src\maestro_j2.rs`.

---

## H-1. La errata 2.14.2 contra D2: la cobertura depende de una lectura del RM que nadie ha medido — **VIABLE CON CONDICIÓN**

La hipótesis del brief §3.2 tiene dos lecturas y las dos son cuantificables. La diferencia entre ellas es de tres órdenes de magnitud.

- **Lectura A** (p. 3492 literal, *«EOT is set… when SPI is re-enabled»*): el `SPE = 1` de D2 levanta el evento, y `CSTART` llega tres escrituras APB después. Una escritura APB son 2 ciclos de pclk (setup + enable), así que el hueco en el periférico es **15 ns a pclk 400 MHz, 30 ns a 200, 60 ns a 100**. Un ciclo de SCK a 10 MHz son **100 ns**: `CSTART` llega **1,7× a 6,7× más pronto de lo que la errata tolera, en cada armado, siempre**. A 34,5 MHz (29 ns) el resultado se invierte según el árbol de reloj: dentro con pclk 400 (15 ns), fuera con pclk 100 (60 ns). Eso no es un diseño, es un resultado de compilación.
- **Lectura B** (el `EOT` solo lo levanta la terminación de `TSIZE` datos): el último `EOT` fue al final de la trama del giro anterior, y con el SPI apagado en medio el hueco es **~105 µs = 1050× la ventana al piso, 3622× a D8**. Bajo esta lectura el papel firmado **ya cumple la solución 2** sin tocar una línea.

**Lo que la spec eligió es lo peor de los dos mundos bajo la lectura A.** D2 aplica la **solución 1** (apagar y encender tras cada `EOT`), y bajo la lectura A la solución 1 **genera** el evento que la solución 2 quiere evitar. Las dos soluciones de ST se pelean dentro de la misma secuencia. El hilo del H743 lo dice en campo: las soluciones 1 y 2 no bastaron; lo que curó fue `HAL_SPI_Abort()` **antes de cada transferencia** — que es estructuralmente D4, ejecutado en el momento equivocado (después del fallo, no antes de cada armado).

**¿Se puede garantizar la solución 2 a 800 MHz de CPU? No por tiempo de ejecución, y no con un temporizador.**

- Por ejecución: no. Ver arriba: al piso, el orden `SPE=1 → EOTC → EOTIE → CSTART` cae dentro de la ventana con cualquier pclk plausible.
- Con espera anclada: sí, y es barata. **80 ciclos de CPU a 800 MHz** para los 100 ns del piso, **24 ciclos** para los 29 ns de D8. Coste: 0,50 % del aire de la trama, **0,080 % del giro, 0,080 % de CPU por ranura**.
- Con `embassy_time`: no sirve. El tick de 1 MHz declarado en el plan tiene grano de 1 µs = **10× el ciclo a 10 MHz y 34× a 34,5**; con 2 µs son 1,6 % de CPU por ranura y el plazo de D3 se come el sobrante. Sobra magnitud, falta resolución.
- **Y una espera de N ciclos sin anclaje no garantiza nada.** La escritura a `CR1` va a memoria Device con *early write acknowledgement*: el retardo puede transcurrir entero antes de que `SPE = 1` llegue al periférico, y las dos escrituras aterrizar pegadas. Lo único que ancla es una **lectura de vuelta** de `CR1` — una lectura Device no se puede early-ackear: devuelve cuando el periférico contesta. Eso no está escrito en ningún sitio del papel firmado.

**La medida que dirime la bifurcación cuesta un acceso:** armar nada, escribir `SPE = 1`, leer `SR.EOT`. Si sale 1, la hipótesis del brief está viva y todo armado del instrumento cae dentro de la ventana al piso. Si sale 0, la errata 2.14.2 no es el mecanismo de #5607 en nuestra configuración y D2 ya la cubre 1050×.

Veredicto: D2-D4 **no cubren** la hipótesis del brief, y tampoco la refutan. La condición es el anclaje, no el retardo.

---

## H-2. El 102× no mide lo que el músico oye — **el mecanismo de recuperación es VIABLE; el 102× como criterio de aceptación es NO VIABLE**

Con cuelgues independientes hacen falta **209 armados fallidos seguidos** (50 ms / 240 µs por intento) para que el módulo suelte. Para un solo disparo del watchdog de trama por hora hace falta **p = 0,937 por armado** — 47.000× por encima del peor p del hilo. **El watchdog del módulo no se va a disparar por esto nunca.** El 102× es real y es irrelevante.

Lo que cruza es el `EVENTO`, y crédito donde toca: el peor caso de 3 giros de §3 es conservador. El plazo de un `EVENTO` de 14 bytes al piso es `2×12 + 20 = 44 µs` (`plazo_us` en `maestro_j2.rs:150`), el reinicio son 20 µs más, y a los 64 µs la ranura está limpia dentro del giro de 125: **se pierde una trama, no tres.**

Con una trama por cuelgue, pasaje normal (20 eventos/s/ranura), seis ranuras a 8 kHz = 48.000 armados/s:

| p por armado (normalizado del hilo) | cuelgues/s instrumento | artefacto audible |
|---|---|---|
| 2e-5 (extremo «10 s») | 0,96 | **cada 12,6 min** |
| 2,2e-7 («900 s») | 0,011 | cada 19,1 h |
| 2,8e-8 («120 min») | 0,0013 | cada 150 h |

Con el peor caso de 3 tramas de la spec: 4,2 min / 6,4 h / 50 h. Pasaje denso (50 ev/s): 5,1 min / 7,7 h / 60 h.

**Y aquí hay una contradicción entre capas que cambia el síntoma.** La spec §3 y el brief §4 dicen *«`EVENTO` no tiene red: un golpe perdido»*, y lo justifican citando la regla del `dispara`. La cabecera §3 dice otra cosa: la red del `EVENTO` **es el bloque `COMPUERTA` a 200 Hz** (R-E11); **solo `dispara`** está sin red. Lo que el músico oye no es silencio: es una nota que entra **hasta 5 ms tarde, a `FUERZA_REPARACION = u16::MAX` y sin tono de arranque** (enmienda del 2026-09-02 al papel del evento). Una nota a fuerza máxima en medio de un pasaje suave es más audible que una nota perdida. El papel firmado describe peor el fallo y por eso nunca lo puso en cifras.

**A 100× la tasa:** 96 cuelgues/s, **0,60 % de giros perdidos por ranura, 0,032 % de CPU en reinicios, cero disparos del watchdog** — el motor de recuperación no se entera — y el artefacto audible baja a **cada 7,6 s**. Instrumento inservible con todas las puertas verdes y el margen de 102× intacto. Ahí está el problema del criterio: **mide la distancia al watchdog del módulo, y el watchdog nunca fue lo que el músico oye.**

**Umbral derivado**, que es lo que la spec no tiene: para ≤ 1 artefacto audible por 10 h de toque, **p ≤ 4,2e-7 por armado = un cuelgue cada 49 s en el instrumento**. El rango del hilo normalizado por armado va de 2,8e-8 a 2e-5. **El umbral cae en medio:** el extremo suave pasa con 15× de holgura, el peor falla por 47×. **Con la evidencia de hoy no hay decisión posible en ninguna dirección.** Descartar el chip hoy es tan infundado como firmarlo.

---

## H-3. Por dónde se rompe el margen de verdad: fase enganchada y un bucle sin cota — **NO VIABLE, dos agujeros**

**(a) Fase bloqueada.** D4 termina en `SPE = 0` y el armado siguiente repite la secuencia idéntica: mismo código, mismo orden, mismo número de ciclos. La errata es una carrera de fase por definición (*«within one SCK cycle»*); si `spi_ker_ck` deriva del mismo árbol que la CPU, la fase entre el flujo de instrucciones y SCK es determinista módulo el divisor, y p puede ser **1 durante un intervalo**. Entonces: 8000 reinicios/s = **16 % de un núcleo por ranura**, `inestable` sube a los **1,25 ms**, y D7.3 dice textualmente que `inestable` *«es información, no acción»*. El módulo suelta a los 50 ms. Y el sello de vitalidad de D5.4 **se escribe al armar** *«porque una ranura reiniciando también está viva»* → **el IWDG se alimenta para siempre con la ranura muda**. El diseño hizo ciego al watchdog exactamente al fallo que la errata predice: un armado que nunca termina y que se rearma a 8 kHz.

**(b) Riesgo 6, que no es una nota al pie.** El `Drop` del `Transfer` de GPDMA es un bucle síncrono **sin cota**, y las seis tareas comparten **un** `InterruptExecutor` (D5.3). Un canal trabado no cuelga una ranura: **congela las seis**, los seis módulos sueltan a los 50 ms, y la única salida es el IWDG = reinicio del chip. Silencio: > 50 ms (watchdog) + 7,9 ms (refresco de la cabecera D5) + arranque del N657 (**HUECO**, S-10). La spec clasifica esto como *«lo cubre el IWDG del hub, no este papel»*. En runtime eso no es cobertura: es la escalada de «una ranura pierde una trama» a «el instrumento reinicia a mitad de concierto», por un `while` sin cota.

---

## H-4. El esclavo: 6 de los 12 extremos de SPI no tienen recuperación — **NO VIABLE**

Los dos extremos del J2 son N657 (spec §2). El papel firmado se declara *«sujeto: el cerebro… como maestro»*. La limpieza del esclavo (`SPE = 0 → 1` al contar corto) es una fila **`pendiente`** del mapa de enmiendas §10, dirigida a un papel del módulo que no existe. Enmienda mandada no es enmienda en vigor.

El esclavo rearma su DMA una vez por giro, igual que el maestro: **misma p, mismo bloque, mismo silicio**.

| p por armado | cuelgue por instancia esclava |
|---|---|
| 2e-5 | cada 6,2 s |
| 2,2e-7 | cada 9,5 min |
| 2,8e-8 | **cada 74 min** |

Consecuencia: su recepción no termina, no aplica `TONO`, su watchdog de trama suelta a los 50 ms y **la voz queda muerta**. Nada en el diseño vigente la resucita — el maestro la marca `muda` a los 5 ms y D7.3 no hace nada con la marca, y qué hacer con `muda` es *«decisión de otro papel»* (§6, fila 1, sin papel). Incluso en el escenario **más suave** del hilo: **un módulo muerto cada 74 minutos de toque, permanente hasta el reset**. Eso no es un artefacto: es una voz que desaparece del instrumento.

---

## H-5. La corrupción detectada pesa más que el cuelgue — **VIABLE CON CONDICIÓN**

1-2 por minuto por enlace (hilo) = **0,20 tramas corruptas/s** en el instrumento por reloj de pared, 0,32/s si se normaliza por armado. El CRC del sobre la caza y R-C2 la rechaza entera; si la trama llevaba `EVENTO`, el resultado es idéntico a un cuelgue: **artefacto audible cada 38-60 min** (pasaje normal), **24 min** (denso).

A la tasa suave de cuelgues (artefacto cada 19 h), **la corrupción domina por 19× a 30×**. La sim4 de la junta anterior, que la spec cita en D6 y §3, solo midió la obsolescencia del `TONO` (≤ 1 ms): **nunca pasó la corrupción por el canal del `EVENTO`**. El número que falta en §3 no es el del cuelgue, es este.

Lo no detectado sí está cubierto: cota floja 2⁻¹⁶ → **una trama mala aceptada cada 91 h** de instrumento encendido, y el modo del hilo (bit duplicado) acorta la trama, así que **R-C1 la rechaza por cuenta de bytes en el flanco de `CS` antes de que el CRC opine**. Ese camino es sólido.

---

## H-6. Los criterios de cierre ya firmados: uno es placebo, el otro está bien — **riesgo 5 NO VIABLE, riesgo 1 VIABLE**

- **Riesgo 5** (*«cien mil transferencias contando `eot_tardios` y `plazos_vencidos` con el bus al aire»*): son **12,5 s a 8 kHz** → p < 3,0e-5 al 95 %. **No excluye ni el peor p del hilo (2e-5)**, y queda **71× corto** del umbral audible. Cero poder discriminante: ese criterio pasa siempre y no significa nada. Es el patrón de «promete en vez de comprobar» con cifra.
- **Riesgo 1 / R-MJ8** (≥ 24 h a 8 kHz): 6,91e8 armados → **p < 4,3e-9 al 95 %, 97× por debajo del umbral**, y λ < 0,125/h para la hipótesis por tiempo. Bien dimensionado. Y el CSV lleva **`horas` y `giros`** a la vez, que es lo único que permite separar las dos hipótesis después del hecho. Eso está bien pensado y lo digo.

---

## H-7. El experimento mínimo: 15 minutos, no 24 horas — y sin control positivo nada de eso mide nada — **VIABLE CON CONDICIÓN**

**Potencia, hipótesis por tiempo** (regla de tres, Poisson, cero eventos):

| soak limpio | λ < al 95 % | λ < al 99 % | P(ver ≥1) si la verdad es 1/h |
|---|---|---|---|
| 3 h | 1,00 /h | 1,54 /h | 95,02 % |
| 4,6 h | 0,65 /h | 1,00 /h | 99,00 % |
| 24 h | 0,125 /h | 0,192 /h | 99,9999999962 % |
| 72 h | 0,042 /h | 0,064 /h | ~100 % |

Con una tasa de un cuelgue por hora: **3 h limpias dan 95 % de confianza, 4,6 h dan 99 %**, y 24 h limpias la excluyen con P(cero) = 3,8e-11. Al revés: 24 h limpias no dicen nada de un evento mensual (P(ver) = 3,3 %).

**Potencia, hipótesis por armado** (la unidad correcta si la carrera vive en `CSTART`): para p < 4,2e-7 al 95 % hacen falta **7,13e6 armados = 15 min en una ranura, 2,5 min en seis**. El soak de 24 h lo cubre **97× de más**. La pregunta que puso Samuel hoy se contesta en **quince minutos de DK**, no en una tanda de papel.

**Control positivo, obligatorio y primero.** Reproducir la configuración de jake-taf (embassy, 100 kHz, `CS` por GPIO, `TSIZE = 0`, `blocking_read`) en **nuestra** DK: **1 h → P(ver ≥1) = 98,2 %** contra el extremo suave declarado (900 s); 4 h → 86,5 % contra el más suave (120 min). Sin esa reproducción, un soak verde no distingue «no nos afecta» de «el arnés no lo detecta» de «el firmware no corría». R-MJ8 hoy no tiene control: es una puerta verde sin sujeto vivo.

**Barrido, no dos puntos.** Retardo `D` entre `SPE = 1` (anclado con lectura de vuelta) y `CSTART`, con `D ∈ {0, ¼, ½, 1, 2, 4, 8} × T_SCK`, en la config mala y en la nuestra a 10 y 34,5 MHz = 21 celdas. Con p(D=0) = 2e-5: **18,8 s por celda, 6,6 min el barrido completo**, y 3,1 min por brazo para acreditar una mejora de 10× al 95 %. Con p = 2,2e-7: 28 min por celda y **99 h el barrido entero** — lo cual ya dicta dónde se corre: **en la configuración mala, donde p es grande**, no en la nuestra.

**El orden. El HAL de C de ST no va primero.** Un punto limpio en C no particiona un espacio de cinco dimensiones (reloj, `TSIZE`, modo de NSS, DMA/bloqueante, orden de armado), y además no enviamos el HAL de C en el instrumento: su resultado es atribución para upstream, no entrada de nuestra decisión. La atribución sale más barata del barrido: **una tasa de cuelgue que es función del retardo `SPE=1 → CSTART` es la firma de la errata; una tasa independiente del retardo no lo es.**

El orden que corre:

0. `SPE = 1` sin armar nada, leer `SR.EOT`. Un acceso. Dirime H-1.
1. Control positivo con la config de jake-taf. 1 h, 98 % de potencia.
2. Barrido del retardo en esa misma config. 7 min.
3. Nuestra config con el driver de embassy: 15 min para el umbral por armado, 24 h para la hipótesis por tiempo.
4. Driver propio. **No primero**: cambia driver y configuración a la vez, y su verde sería confundido.
5. HAL de C solo si 1-4 dejan un cuelgue que el driver propio no limpia.

---

**Corre B con su primer experimento cambiado — la lectura de `SR.EOT` y el control positivo de jake-taf antes que el HAL de C —; A no corre, porque su puerta de 24 h mide el margen equivocado y deja seis esclavos N657 sin recuperación, y C no corre porque nadie puede firmar un cambio de plataforma cuando el rango de la evidencia straddlea el umbral de aceptación por ±1,5 órdenes de magnitud y la medida que lo cierra cuesta quince minutos.**

El runtime no le debe nada a tus intenciones: mide p o no decidas.
