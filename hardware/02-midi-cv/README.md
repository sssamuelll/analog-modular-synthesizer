# Hardware — Módulo 2: MIDI/CV

> [!IMPORTANT]
> ## Este diseño está SUPERADO — 2026-08-17
>
> Lo que hay en esta carpeta es el módulo 2 **v1**: Raspberry Pi 3B+, DAC
> AD5686R a bordo, LCD 16×2 y cuatro pulsadores. Tres decisiones posteriores lo
> invalidaron:
>
> | Lo que esta placa asume | Lo que se decidió después |
> |---|---|
> | El Pi dentro del instrumento | La computadora se queda **fuera** — `architecture-compute.md` §1 |
> | El DAC aquí, un cable por CV | Los DAC **viven en cada módulo** — `architecture-poly.md` §8 |
> | LCD 16×2 + 4 pulsadores + cabecera de 40 pines | Cabeza mínima y pantalla inalámbrica |
>
> **No se rutea, se reemplaza.** El sucesor es el **módulo 2 v2** sobre
> **RP2350B**, especificado en
> [`docs/superpowers/specs/2026-08-17-nucleo-digital-design.md`](../../docs/superpowers/specs/2026-08-17-nucleo-digital-design.md).
> El respin **disuelve el issue #22** en vez de resolverlo: la congestión que
> dejó 17 redes al aire eran justo las seis líneas del LCD, los cuatro botones y
> la cabecera del Pi.
>
> **Qué sobrevive y no hay que re-derivar:** el presupuesto de afinación
> ([`tuning_budget.py`](tuning_budget.py)), el de autoafinado
> ([`autotune_budget.py`](autotune_budget.py) — ya actualizado al PIO del
> RP2350, ver §5.1 de la spec), la lección de las masas partidas, y el gate de
> dos MOSFET para que el reposo al arrancar sea bajo.
>
> **Qué muere con el Pi:** la PCB, y el firmware de
> [`software/midi-cv/`](../../software/midi-cv), que es Python con `RPi.GPIO`,
> `spidev` y `RPLCD`. Eso deja sin objeto la mitad del issue #18.

> Documentación funcional: [`docs/modules/02-midi-cv.md`](../../docs/modules/02-midi-cv.md).
> Firmware: [`software/midi-cv/`](../../software/midi-cv).

## Resumen

El único módulo digital del sintetizador. Combina un Raspberry Pi 3B+ con un
DAC AD5686R (16-bit, cuádruple) para generar 3 salidas CV (1 V/oct) y 1
GATE digital (10 V) a partir de mensajes MIDI USB.

## Componentes principales

| Función | Componente |
|---------|------------|
| Procesamiento + USB MIDI | Raspberry Pi 3B+ |
| Conversión D/A (4 canales 16-bit) | AD5686R |
| Buffer/escalado CV | TL074 (op-amp) |
| Pantalla menú | LCD 16×2 (HD44850 / HD44780 compat.) |
| Navegación | 4 pulsadores táctiles |

## Pinout (ver `docs/modules/02-midi-cv.md`)

GPIO BCM: UP=4, DOWN=17, BACK=16, ENTER=26, GATE=27, DAC RESET=6.
LCD: RS=25, EN=24, D4=23, D5=18, D6=15, D7=14.
SPI: bus 0, device 1, mode `0b01`, max 50 MHz.

## Qué decide este módulo

Es la fuente del CV de tono, así que su error se suma al de la masa del bus.
El presupuesto está en [`tuning_budget.py`](tuning_budget.py) y sale a
**1.68 cents**, de los cuales **1.21 siguen siendo la masa** del bus board.

Lo que no era obvio: los errores **estáticos** suman **103 cents** y no cuenta
ninguno, porque la tabla de afinación (`tuning.json`) los absorbe enteros. Solo
importa lo que deriva *después* de calibrar. De ahí salen las tres decisiones
del módulo — ver [`notes/design-notes.md`](notes/design-notes.md).

| | |
|---|---|
| Rango del CV | **0–7 V** (la tesis usa 3–10; §3 de las notas) |
| Resolución | 1 LSB = **0.128 cents** |
| Amplificador | **TL074H**, no TL074 — la deriva es 9× mejor |
| Masas | **`GNDA` y `GNDD` separadas**, se unen solo en la estrella del módulo 1 |
| `VLOGIC` del DAC | **+3V3**, no +5 V: si no, V_IH = 3.5 V y el Pi da 3.3 |
| GATE | dos MOSFET, para que el reposo al arrancar sea **bajo** |

## Estructura del directorio

```
02-midi-cv/
├── README.md
├── bom.csv
├── tuning_budget.py     Presupuesto de afinación, ejecutable y con aserciones
├── kicad/
│   ├── build_schematic.py   Genera sam17-midicv.kicad_sch (sin MCP: kicad-cli)
│   ├── check_netlist.py     Conectividad contra el diseño declarado
│   ├── check_bom.py         Cruce esquemático <-> bom.csv
│   └── sam17.kicad_sym      Símbolo propio del AD5686R (KiCad no lo trae)
├── schematics/
├── pcb/        (pendiente)
└── notes/design-notes.md
```

## Estado

- [x] Presupuesto de afinación cerrado — **1.68 cents** de 5
- [x] Piezas verificadas contra datasheet primario: pinout TSSOP del AD5686R
      (que **no** es el del LFCSP), recorrido y deriva del TL074H, `VLOGIC`
- [x] Esquemático en KiCad — 42 componentes, **ERC 0 infracciones**
- [x] Netlist verificado: 63 redes, masas separadas, gate no inversor
- [x] `bom.csv` cuadra designador a designador (42/42)
- [~] **PCB congelada con 17 redes sin rutear** — colocación cerrada y
      verificada, las dos masas partidas con **4.00 mm de hueco medido**, plano
      analógico entero en una sola isla, DRC **0 infracciones**. `build_pcb.py`
      sale con error a propósito ([§10](notes/design-notes.md)).
      **Ya no se va a cerrar**: la sustituye el respin en RP2350B
- [x] ~~Firmware: el cambio de rango a 0–7 V~~ — sin objeto, el firmware del Pi
      muere con el Pi (issue #18)
- [x] ~~Diseño térmico del Raspberry Pi~~ — sin objeto, no hay Pi
- [ ] ~~Medir la deriva del CV con la temperatura~~ · ~~Validación SPI con
      osciloscopio~~ — se heredan al bring-up del **v2**, no a esta placa
