# Módulo 1 — Alimentación

> **Estado real desde el 2026-09-04: se construye la v4.**
> `hardware/01-power-supply/v4/` con
> `docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md`: seis módulos
> Mean Well IRM encapsulados sustituyen al toroide, la cascada lineal se queda
> igual, y el instrumento estrena **rieles de rack propios** para una fila
> Eurorack de invitados. La v3 (`v3/README.md`) conserva la cascada y sus
> puertas y **no se pide**.
>
> Diseño detallado de lo que la v4 hereda:
> `docs/superpowers/specs/2026-08-18-fuente-chasis-telemetria.md` (chasis y
> telemetría, con su enmienda de la misma fecha) sobre
> `docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md` (topología de
> regulación). Este documento es el resumen de entrada; no repite la
> aritmética, solo el estado.
>
> **Lo que hoy está abierto y decide**, con su guion: el margen de entrada de
> la cascada (`v4/margen_budget.py`, HUECO), el umbral del secuenciador de
> D-F4 que depende de él (`v4/secuencia_budget.py`, HUECO), la pieza del SCR
> del crowbar (`v4/check_absmax.py`, HUECO), la hoja del fusible cerámico
> (`v4/fusible_budget.py`, HUECO) y la cifra de fuga de IEC 62368-1
> (`v4/fuga_budget.py`, HUECO). Ninguno bloquea la puerta; los cinco están
> declarados.

## Objetivo

Generar las tensiones reguladas requeridas por el bus SAM17:

- **±12 V** — módulos analógicos (VCO, VCF, VCA, op-amps, OTAs), 650 mA/riel
  de envolvente de diseño, **174 mA/riel** de censo real medido (#70).
- **+5 V** (`U3`, local a esta placa) — solo el módulo 2 (STM32N657), por `J6`.
  El +5 V digital **no pasa por esta placa**: lo pone una SMPS externa y es
  responsabilidad del módulo 2. Era una **Mean Well IRM-15-5**; desde la
  fuente v4 es `PS6`, una **IRM-45-5** de 8 A de placa (D-F7, 03-09), y su
  techo lo importa `hardware/02-midi-cv/power_budget.py` de `calor_budget.py`
  en vez de transcribirlo.

## Entrada

- Transformador toroidal **120 VA** (Nuvotem Talema 0120P1-2-012), no el
  transformador de 2 A de la tesis original — el censo real y el margen de
  regulación lo exigen (ver spec v2 §16.5, §16.12).
- `TR1` sin fusible térmico embebido no se compra: es criterio de aceptación
  del BOM, no una mejora opcional.

## Topología (v3, la única que se construye)

Cascada de dos etapas por riel — **no un solo 78xx/79xx**:

| Riel | Pre-regulador | Post-regulador |
|------|---------------|-----------------|
| +12 V | **LT1963A** (era LM2941; D-F8, 04-09) | LT3045 ×2 |
| −12 V | **LT3015** (era LM2991; D-F9, 06-09) | LT3094 ×2 |
| +5 V (`U3`, módulo 2) | 7805 | — |

Las dos piezas de la izquierda cambiaron en la v4 y **no por gusto**: con las
viejas, `margen_budget.py` daba **−388 mV** de margen de entrada en el +12 y
**−170** en el −12, o sea que ninguno de los dos rieles tenía garantizado que
el pre-regulador siguiera regulando en el peor caso. Con las nuevas son
**+330** y **+536 mV**. El razonamiento vive en el papel de la v4 y en el
docstring de `margen_budget.py`.

Objetivo de ruido: **0,8 µVrms (10 Hz–100 kHz)**. Sin crowbar en ningún
riel — la cascada protege sola contra cualquier fallo simple del
pre-regulador (§16.8, reescrita); lo que exige el análisis en su lugar es el
fusible térmico de `TR1`.

## El chasis

**Acero, cerrado, sin ventilación** — decisión de 2026-08-18. El toroide, la
PCB completa y la entrada de red viven dentro de un recinto de acero soldado
al espárrago de PE; los tres TO-220 disipan contra su pared en vez de
disipadores Fischer individuales (Tj de `U2`: 101 → 61 °C). Vive como
parámetro en `case/cad/params.scad` / `case/cad/sam17_case.scad`, no como
archivo suelto.

## Telemetría

Cinco chips I²C (~12 USD), aislados de GNDD por un ISO1541: 2× INA226
(+12 V y +5 V, tensión y corriente), ADS1115 (−12 V, VRAW+, VRAW−, solo
tensión) y TMP1075 (temperatura del recinto). Mide, por primera vez, el
valle de VRAW que hasta ahora solo existía simulado.

## Distribución

Bus de 4 hilos (+12/GND/GND/−12) por conector KK-254 (`J2`) hacia los
módulos — **no lleva 5 V**. El bus de telemetría I²C es un conector JST-PH
de 2,00 mm (`J8`) a propósito: con ese paso el cable de I²C no entra en
ningún conector de potencia.

## Qué falta

- **Fase E (validación física).** Todo lo de arriba está diseñado, ruteado
  (DRC en cero) y con gerbers listos para JLC — nada está pedido ni
  montado. Bring-up, LNA de medida (#58) y la primera lectura real del
  valle de VRAW son trabajo pendiente.
- Presupuesto de la pantalla electrostática del toroide (Talema) — acción
  de Samuel, no de análisis.
- Hueco del IEC C14 en la chapa (#130) — pieza elegida, falta acotarlo en
  `params.scad`.
