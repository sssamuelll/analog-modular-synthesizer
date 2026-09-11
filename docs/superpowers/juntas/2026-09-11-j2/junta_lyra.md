## Lyra — coste de oportunidad, junta del 2026-09-11

Leí el brief completo, el hub §2.2/§10/§11, el issue #231, y fui al repo a contar lo que de verdad existe. Dos hallazgos cambian la forma del problema antes de llegar a las opciones.

---

## 1. Inventario honesto: qué sobrevive y qué muere

**Primer hallazgo: ningún esquemático ni PCB del repo nombra al N657.** Los seis `.kicad_sch` que existen son de la fuente, el VCO, el bus y el módulo 2 — y el del módulo 2 sigue siendo el del RP2350 y el Raspberry Pi (#111 abierto). Un cambio de chip hoy **no tira una sola línea de cobre**. La parte cara del proyecto es intacta porque nunca se dibujó.

### Sobrevive a cualquier chip

| Activo | Tamaño / evidencia | Por qué sobrevive |
|---|---|---|
| Política en `core` (19 módulos) | 11.971 líneas, **232 tests** (cuerpo de #250) | `no_std`, cero dependencias de silicio; el N657 solo aparece en comentarios |
| `maestro_j2.rs` (fase A, mergeada) | 678 líneas, 14 tests | plazo/reinicio/cuenta es política, no registro |
| Frontera fw↔core (D8) | `j2_spi.rs` 77 líneas | «`fw` cloca bytes, `core` sabe qué son» es arquitectura |
| Presupuestos del enlace | `trama_j2_budget.py` 448, `recuperacion_j2_budget.py` 216 | el reloj entra como parámetro, no está cableado |
| Case completo | **0 menciones de N657 en `case/`** | desacoplado entero |
| Cobre | **0 menciones de N657 en los 6 `.kicad_sch`/`.kicad_pcb`** | no hay nada que rehacer |
| El aprendizaje del bloque SPI de ST | ES0396 §2.14.2 + 3 hilos del foro | vale para `spi_v4` y `spi_v5`; sirve igual si te vas al H7 |
| `stm32-data#911` (mergeada) | crédito público | ya cobrado, no se devuelve |

### Muere con un cambio de chip

| Activo | Tamaño / evidencia | Coste de rehacer |
|---|---|---|
| Censo de pines del hub | `micro_budget.py` 1.362 líneas + `check_pinout_n657.py` 252 | entero, contra otro paquete (hoy VFBGA264, +33 GPIO peor caso) |
| Árbol de relojes | `reloj_budget.py` 634 líneas, **A-11 firmada** (dos cristales, sin PLL fraccional), #150 abierto | las PLL son del chip |
| Censo de SRAM del hub | `sram_hub_budget.py` 340 líneas, 82.280 B medidos en `c521302` | los 4.200.000 B son del N657 |
| Carga del motor | `carga_motor_budget.py` 346 líneas | ciclos del M55 |
| Arranque (escrito **hoy**, `e0fbc86`) | `ARRANQUE.md` 220 líneas; FSBL de embassy 17.432 B + app 19.288 B | ROM, FSBL y cabecera son del N6 |
| Pase a `embassy-stm32` + el fork | `fw/Cargo.toml:24` apunta a `sssamuelll/embassy` rama `n6-usb`; #250 abierto | el puerto se repite y el fork se tira |
| Tres firmas | A-1 (26-08, motor), D1 (30-08, hub), maestro del J2 (03-09, firmada 10-09) | se reabren las tres |
| D8 = 34,5 MHz | `j2-punto-a-punto` §497: `1/(2×14,5 ns)` de la fila eléctrica del esclavo | el techo del enlace se recalcula contra otra tabla |
| `embassy#6939` (abierta) | — | queda huérfana |
| El reparto de cuatro N657 | acta 09-09: hub, Voz, mago, interfaz | **el cambio se multiplica por 4**, no por 1 |

Subtotal de lo que muere en guiones: **2.934 líneas de censos**, 23 specs, 3 firmas, 4 chips. Cero cobre.

---

## 2. Coste de continuación por opción

Mi reparto de probabilidad, con su base (juicio, no medición): **driver/carrera de la errata ≈ 0,7** (la errata del gemelo existe documentada; el repro de jake-taf cae dentro de su condición; el H743 se curó con `Abort` por software; los dos reportantes usan `TSIZE=0`, que el diseño firmado prohíbe; nadie probó NSS hw ni el HAL de C) · **otra cosa ≈ 0,2** (el H723 terminó siendo arnés) · **silicio sin cura ≈ 0,1** (ST publica tres mitigaciones para el gemelo; una ya está aplicada).

| Opción | Semanas de escritorio | $ | Si es del DRIVER (~0,7) | Si es del SILICIO (~0,1) |
|---|---|---|---|---|
| **A** driver hoy, placa cuando haya plata | 1-2 (fase B + enmienda de 2 líneas a D2) | 0 | gana todo: el driver está y la enmienda bastaba | pierde 1-2 semanas de driver y el papel firmado encima; y la placa ni se ha pedido |
| **B** placa a prioridad 1, soak en C primero | 1 (compra + banco) + las mismas 1-2 del driver | 224 en lista | gana lo de A **más** un número propio; descarta embassy en un día | gana el veredicto **antes** de firmar papel de cuatro chips |
| **C** cambiar de chip ahora | **4-8** (23 specs, 4 chips, 3 firmas, 2.934 líneas de censos, el puerto otra vez) | 0 cash, el trimestre entero | pierde 4-8 semanas contra un defecto de software | gana **solo si** el destino no trae su gemelo; el H7 lo trae en ES0396 Rev 9, sin corregir en **todas** las revisiones (A A A) |
| **D** J2 fuera del SPI (USART síncrono) | 3-5 (cabecera, punto a punto, censo) | 0 | baja el techo de 34,5 MHz a cambio de nada | **no escapa**: la Voz gasta **3 SPI en el CV** (hub §2.3). Si el bloque está roto, el CV también. Y el modo síncrono maestro del USART del N657 está **SIN VERIFICAR** (hub §10.3) |

**C y D están muertas.** C gasta un trimestre contra un escenario de 0,1 y aterriza en un chip cuyo defecto gemelo está documentado y sin corregir. D paga 3-5 semanas por una salida que deja el CV — lo que hace sonido — en el mismo periférico sospechoso, y se apoya en una capacidad que nadie verificó en la hoja.

**Asimetría:** A y B comparten el 80% del trabajo (el driver) y se diferencian en **el orden**, no en el diseño. Eso significa que el debate de hoy no vale 4 semanas: vale una.

---

## 3. Los $224 contra las semanas de papel

Segundo hallazgo, y es el que reordena la compra: **el papel no está bloqueado.** Hito 3 tiene 6 abiertos, hito 4 tiene 31, y ninguno de los 31 se acerca al bloque SPI. Lo único que el defecto bloquea es la puerta dura que la spec ya puso: *soak ≥ 24 h antes de fabricar cualquier PCB con N657*. O sea, **los $224 no compran «reducir riesgo ya»: compran el derecho a fabricar.** Su urgencia es una función de una fecha que nadie ha escrito.

Escalera de costo, de lo gratis a lo caro:

| # | Gasto | $ | Tiempo | Qué puede cerrar |
|---|---|---|---|---|
| 1 | **ES0620 Rev 1** (N6), HUECO desde §3.4 | **0** | 1-2 h + que Samuel lo baje (st.com no contesta a curl) | convierte «defecto sin diagnosticar» en «limitación conocida con tres mitigaciones, una ya aplicada». Mayor retorno por dólar del proyecto |
| 2 | **Pedir en #5607** la corrida del HAL de C y la prueba de NSS hw | **0** | 20 min | jake-taf tiene la DK y dijo el 03-09 que no probó NSS. Si el cuelgue muere con NSS hw, la spec nació curada. No calendarizable: se pide y se sigue |
| 3 | **NUCLEO-N657X0-Q** | **75,72** (584 en stock, #231) | — | **mismo STM32N657X0H3Q en VFBGA264** que la DK (#231). Dirime silicio vs driver completo. 3× más barato |
| 4 | **STM32N6570-DK** | **223,67** (1.511 en stock) | — | lo del Nucleo **+** LTDC/contención (riesgo 5), PSRAM, cámara→NPU, FSBL firmado. 5 filas de riesgo abiertas por una compra: ~$45 por fila |

Tres cosas que nadie ha puesto en la mesa:

1. **Si la pregunta urgente es el J2, el instrumento de medida cuesta $75,72, no $223,67.** Los $148 de diferencia compran pantalla, PSRAM y cámara — que no son la pregunta de hoy.
2. **Los $223,67 son precio de lista de DigiKey.** Nadie ha escrito el costo puesto en la puerta: envío internacional + aduana/IVA. El 28-08 se aplazó contra una cifra incompleta. **HUECO: dame el costo landed antes de llamarlo $224.**
3. **Si los dos extremos del J2 caben en la misma placa** (SPI1↔SPI5, los dos bloques que #5607 ya vio colgarse), una sola placa compra el soak entero y no la mitad. Verificar contra UM3300 antes de pagar — no está verificado aquí.

---

## 4. Reparto concreto

Case en 0% en los cuatro escenarios. Es el único trabajo del repo con cero acoplamiento al chip (0 menciones en `case/`) — y por eso mismo es el único que **no pierde nada esperando**. No es una línea del presupuesto; es el relleno de los bloqueos.

### Bajo A (driver primero)

| | Driver fase B | ES0620 + #5607 | Hub (§10.3 USART) | Discovery | Case |
|---|---|---|---|---|---|
| **2 semanas** | 60% | 25% | 15% | 0% | 0% |
| **1 mes** | 50% | 20% | 30% (filas 1,2,3,6,8 de §10) | 0% | 0% |

El 15% del USART no es papel de adorno: hoy es el plan B del escenario de 0,1 y está **sin verificar**. Si esa fila queda verde, D deja de ser una fantasía y pasa a ser un seguro con precio.

### Bajo B (placa primero)

| | Driver fase B | ES0620 + #5607 | Compra + banco | Soak | Case |
|---|---|---|---|---|---|
| **2 semanas** | 40% | 30% | 30% (landed, Nucleo vs DK, criterio escrito **antes** de medir) | 0% | 0% |
| **1 mes** | 30% | 10% | 0% | 50% (C primero, Rust después) | 10% |

El driver nunca baja de 30% en ninguna columna: el 80% de él sobrevive a cualquier veredicto, y detenerlo por una medición que tarda semanas en llegar regala calendario sin comprar información.

---

## 5. La pregunta incómoda

Si el veredicto fuera «el silicio se cuelga cada 30 minutos y no hay cura en software», ¿matarías el SAM17, o lo fabricarías igual con la recuperación de 490 µs contra un watchdog de 50 ms — 102× de margen, ya firmado? Contéstalo **hoy**, antes de gastar un dólar: si la respuesta es la segunda, la medición no compra una decisión, compra tranquilidad, y la tranquilidad se programa barata. Si es la primera, $224 es el dólar mejor gastado del proyecto y llevas seis meses sin gastarlo.

---

**Reparto recomendado: esta semana 0% de compra — ES0620 y el hilo #5607 (gratis) al 30%, driver al 60%, USART del hub al 10%; la placa se paga la semana siguiente si la errata no cierra la pregunta, y es el Nucleo de $75,72 si la restricción sigue siendo la plata del mes — y lo cambio a la DK de $223,67 comprada de una el día que aparezca en el calendario una fecha de pedido de PCB con N657 a menos de ocho semanas, porque ahí la placa deja de ser gasto de investigación y pasa a ser gasto de fabricación.**
