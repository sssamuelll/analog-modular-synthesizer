# Módulo 1 — Alimentación

> **Estado real desde el 2026-09-08 (D-V1..D-V5 firmadas): se construye la v5.**
> `hardware/01-power-supply/v5/` con
> [`docs/superpowers/specs/2026-09-05-fuente-v5-ladrillo-design.md`](../superpowers/specs/2026-09-05-fuente-v5-ladrillo-design.md)
> y el [censo D-V4](../superpowers/specs/2026-09-08-censo-dv4-resolucion.md):
> la conversión AC-DC sale de la caja de madera a un **ladrillo externo de 24 V**
> (D-V1), dentro quedan convertidores DC-DC (`THN 30-2422WI` para ±12 V de rack,
> `URB2405YMD-20WR3` aislado para +5 V digital bajo `M1`, `2 × THN 20-2413WI`
> recortados a ±15,5 V crudos bajo D-V3, y `K7805T-1000R3` para +5 V de rack),
> y **la cascada lineal se queda intacta**. La `v4/` conserva las curvas y
> presupuestos de los módulos Mean Well IRM; la `v3/` conserva la placa del
> toroide y no se pide.
>
> Diseño detallado de lo que la v5 hereda de la v4 y la v3:
> - [`docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md`](../superpowers/specs/2026-09-03-fuente-v4-liston-design.md) (listón, cascada con `LT1963A`/`LT3015`, `D-F2`, `D-F4`, `D-F6`)
> - [`docs/superpowers/specs/2026-08-18-fuente-chasis-telemetria.md`](../superpowers/specs/2026-08-18-fuente-chasis-telemetria.md) (telemetría)
> - [`docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md`](../superpowers/specs/2026-08-16-psu-v2-goat-design.md) (topología de regulación de la cascada)

> ### ENMIENDA E16 — PRESUPUESTO TÉRMICO (#331, completada el 2026-10-22)
>
> D1 retiró la cadena WS2812. En la `v4/`, `calor_budget.py` incluye la carga
> digital sin cadena (**2,895 A / 14,475 W**), la pérdida en `PS6` (**2,86 W**),
> la franja de red (**3,70 W**) para **29,23 W** en el recinto (`P_RECINTO_MAX`),
> y la carga ultra de la Voz (**8,00 W**, `CAJON_ULTRA_W = 8,0016 W`) para
> **118,08 W** en el cajón (`P_CAJON_MAX`) y **147,31 W** totales (`87,7 °C` en
> caja cerrada, `146,8 °C` a placa sin derating, `21 000 mm²` de venteo nuevo en
> `P_BASE`). En la `v5/`, con los rieles de rack declarados según **D-B2**
> (`0,5 / 0,5 / 0,5 A`) y la conversión AC-DC fuera de la caja, el calor del
> cajón lo gobierna `hardware/01-power-supply/v5/ladrillo_budget.py`
> (`calor_del_cajon_w()`), cruzado por `case/clearance_budget.py::guarda_potencia_vigente()`.

## Objetivo

Generar las tensiones reguladas requeridas por el instrumento SAM17 y por la
fila Eurorack de invitados (52 HP, D-B2):

- **±12 V ultra (cascada del instrumento)** — módulos analógicos propios (Voz,
  filtro, VCA, bahía), **650 mA/riel** declarados (D-F1), **334 mA/riel** de
  censo (`consumo_total_budget.py`), rizado y ruido **≤ 0,8 µVrms (10 Hz–100 kHz)**.
- **+5 V auxiliar (`+5V_AUX`)** — **100 mA** hacia el módulo 2 por `J6`. En la v5 sale
  del +5 V de rack (`PS3`, `K7805T-1000R3`) por el shunt `R20` que mide `U12`; no hay
  `U3`/LM7805 propio.
- **±12 V y +5 V de rack (fila B de invitados)** — **500 mA/riel** de techo duro
  (D-B2; censo comercial de 300 mA/riel), con protección crowbar (`D-F6`,
  `BT151-500R` + `TL431BI`, `R_GK` = 100 Ω para el dV/dt de 200 V/µs de la hoja) y
  habilitación conjunta (`D-F4`).
- **+5 V digital aislado (`M1`)** — **2,895 A** de techo de diseño (`Max TJ = 125 °C`
  de los 4 STM32N657 más USB host, `0,965 A` típico) mediante convertidor DC-DC
  aislado (`URB2405YMD-20WR3`, 4 A, 1500 VDC, ≥ 88 % mín.), conservando `GNDD`
  fuera de la estrella analógica (> 1 MΩ dentro de la fuente).

## Entrada y vigilancia (`M5` / `D-V1` / `D-V2`)

- **Ladrillo externo de 24 V** (`AE TE90A2403F01` / `Mean Well GST120A24-R7B` /
  `GSM120A24-R7B`), entrando al chasis por conector de 4 polos **Kycon KPJX-PM-4S**
  (`KPPX-4P` en el cordón, 2 pines por polo en paralelo).
- **Bloqueo de inversión de polaridad**: controlador **TI LM74502** + MOSFET
  en la entrada de 24 V (H-V5-INVERSION).
- **Vigilante de entrada (`M5`)**: eFuse **TI TPS26631** (`tps2663.pdf`; la
  «TPS26630PWPR» de #474 no existe: TI solo vende el TPS26630 en VQFN-24) gobernado
  por **TI MSP430FR2111** con FRAM no volátil (`msp430fr2111.pdf`): 3 reintentos
  (4 intentos totales) con espera de 1,0 s, filtro de rebote de 100 ms y
  enclavamiento en abandono persistente hasta rearme manual por botón dedicado ≥ 2 s.
  `SHDN` de `U16` con pull-down (`R83`, 47 kΩ): sin el MCU vivo, el eFuse queda
  apagado. El `FLT` del tope `U19` entra al MCU por P1.2 (`R84`): sobretensión de
  riel = abandono en el primer pulso, ignorándolo los primeros 100 ms, que es
  cuando el propio `U19` lo baja por UVLO al arrancar. El MCU se alimenta por
  `TPS709` tras `R64` (1 kΩ) y un zener de 24 V (`D2`): con `D1` en 42,1 V su
  entrada no pasa de 26,4 V (`check_absmax.py`).

## Topología de la cascada (`v4`/`v5`)

Cascada de dos etapas por riel alimentada desde ±15,5 V crudos (`2 × THN 20-2413WI`
recortados +3,3 %, D-V3):

| Riel | Tope OVP (`M3` / #334) | Pre-regulador | Post-regulador |
|------|------------------------|---------------|----------------|
| +12 V ultra | `TPS26631` (`U19`, sin UVLO y con Schottky de rueda libre `D19`) + `SMBJ16A` + LC 22 µH / 47 µF (`U1` ve 18,11 V ≤ 20 V ante un fallo de 36 V, `check_absmax.py`) | **LT1963A** `LT1963AEQ` (D-F8) | LT3045 ×2 |
| −12 V ultra | Diodo Schottky de enclavamiento (LT3015 soporta ±33 V) | **LT3015** `LT3015EQ` (D-F9; DD-PAK, la aleta es IN) | LT3094 ×2 |
| +5 V aux (módulo 2) | — (del +5 V de rack, `PS3` por el shunt `R20`) | — | — |

Con crudos de **±15,5 V** (D-V3) e incluyendo la resistencia de paso del
`TPS26631` (`53 mΩ` máx.) y la corriente de tierra máxima del `LT1963A` a 1,5 A
en temperatura (`120 mA`, #343), el margen de regulación garantizado en el peor
caso sube a **+760 mV** en `U1` y **+1017 mV** en `U2`, y la ventana útil del
detector analógico de `D-F4` (`LM393B` + `TL431BI`) pasa a **+802 mV**.

## Telemetría (`D-F2`)

Aislada de `GNDD` por un **ISO1541** (`U9`) sobre una tira de 4 pines a 2,54 mm
(`J8`: +3,3 V digital, SDA, SCL, `GNDD`):
- `U8` (**INA226**, `0x40`): +12 V ultra (tensión y corriente).
- `U12` (**INA226**, `0x41`): +5 V auxiliar (tensión y corriente, shunt `R20`).
- `U13` (**INA226**, `0x44`, D-F2): +12 V de rack a la salida del convertidor.
- `U14` (**INA226**, `0x45`, D-F2): +5 V de rack a la salida del convertidor.
- `U10` (**ADS1115**, `0x48`): −12 V ultra, `VRAW+`, `VRAW−` y −12 V de rack.
- `U11` (**TMP1075**, `0x49`): temperatura local de la placa.

## Qué falta

- **Fase E (validación física en banco).** Todas las puertas de presupuesto,
  esquemático, netlist, PCB y paquete de fabricación de `v5/` corren en
  `python hardware/tools/gates.py`; las medidas físicas de banco (`v5/medidas.csv`
  con `v5/check_bringup.py`) y las consultas de fabricante (`pliego §7`) quedan
  declaradas como `HUECO` hasta recibir las placas y el ladrillo.
