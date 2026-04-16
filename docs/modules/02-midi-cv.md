# Módulo 2 — MIDI/CV (digital)

> Referencia: tesis, *Módulo MIDI/CV* (Gráficos 13–21), incluye diseño de
> hardware y software.

## Objetivo

Convertir mensajes MIDI provenientes de un controlador USB en señales de
control analógicas (CV 1 V/oct) y digital (GATE 10 V) que el resto del
sintetizador analógico pueda interpretar.

## Hardware

### Componentes principales

| Componente | Función |
|------------|---------|
| Raspberry Pi 3B+ | Cómputo, lectura USB MIDI, control GPIO/SPI |
| AD5686R | DAC cuádruple 16-bit con referencia interna 2.5 V |
| TL074 | Op-amp para escalado/buffer de las salidas CV |
| LCD 16×2 (HD44780) | Pantalla del menú de modos |
| 4 pulsadores táctiles | Navegación: Back, Enter, Up, Down |

### Alimentación

- **Raspberry Pi**: 5 V regulada vía transformador independiente (consumo
  hasta 2 A en pico).
- **Sección analógica (op-amps)**: ±12 V del módulo de alimentación.
- Resistencias de **película metálica** en las redes de 1 kΩ / 1.5 kΩ para
  mantener ganancia precisa.

### Salidas

- **3 × CV NOTE** — 1 V/octava, rango ~3 – 10 V, 84 notas (C1–C8). Usan los
  canales A, B, C del AD5686R (direcciones SPI `0x11`, `0x12`, `0x14`).
- **1 × GATE** — 10 V cuando hay nota activa, 0 V en reposo.

### Interfaz SPI con el AD5686R

- 3 hilos: **SCLK**, **SDIN**, **SYNC** (CS).
- Velocidad máxima: 50 MHz (la tesis configura `spi.max_speed_hz =
  50_000_000`).
- Modo SPI: `0b01` (CPOL=0, CPHA=1).
- Bus: `bus=0`, `device=1` en el Raspberry Pi.
- Trama de 24 bits: `[C3..C0 | A3..A0 | DB15..DB0]`.
  - 4 bits de comando (ver tabla).
  - 4 bits de dirección de DAC.
  - 16 bits de dato (resolución 0–65535).

#### Comandos del DAC

| C3 C2 C1 C0 | Descripción |
|-------------|-------------|
| 0000 | No-op |
| 0001 | Escribir registro de entrada n (depende de LDAC) |
| 0010 | Actualizar registro DAC n con contenido del registro de entrada n |
| **0011** | **Escribir y actualizar canal n del DAC** *(uso normal)* |
| 0100 | Power-down / power-up |
| 0101 | Máscara LDAC |
| 0110 | Reset por software |
| 0111 | Configurar referencia interna |
| 1000 | Daisy-chain enable |
| 1001 | Readback |
| 1111 | No-op |

#### Direcciones de canal

| DAC D | DAC C | DAC B | DAC A | Canal seleccionado |
|-------|-------|-------|-------|--------------------|
| 0 | 0 | 0 | 1 | DAC A (`0x11` con C=0011) |
| 0 | 0 | 1 | 0 | DAC B (`0x12`) |
| 0 | 1 | 0 | 0 | DAC C (`0x14`) |
| 1 | 0 | 0 | 0 | DAC D (`0x18`) |
| 0 | 0 | 1 | 1 | DAC A + DAC B |
| 1 | 1 | 1 | 1 | Todos los DACs |

### Mapa de pines (Raspberry Pi BCM)

| GPIO | Función |
|------|---------|
| 4    | Botón **UP** |
| 17   | Botón **DOWN** |
| 16   | Botón **BACK** |
| 26   | Botón **ENTER** |
| 27   | Salida **GATE** |
| 6    | DAC `RESET` |
| 14   | LCD D7 |
| 15   | LCD D6 |
| 18   | LCD D5 |
| 23   | LCD D4 |
| 24   | LCD `EN` |
| 25   | LCD `RS` |
| SPI0 (8/9/10/11) | SPI al AD5686R |

## Software

Implementación en `software/midi-cv/`. Lenguaje: Python ≥ 3.10. Ver el README
de ese directorio para instalación, tests y arquitectura del firmware.

Modos definidos en la tesis original:

1. **standard** — conversión MIDI→CV monofónica con pitch-bend.
2. **tune** — afinación interactiva, asistida por LCD.
3. **glide** — *(declarado, pendiente)*.
4. **arp** — arpegiador *(declarado, pendiente)*.
5. **step sequencer** — secuenciador por pasos *(declarado, pendiente)*.

## Mejoras propuestas

- Migrar de `Adafruit_CharLCD` (deprecado) a `RPLCD` o
  `adafruit-circuitpython-charlcd`.
- Sustituir el sistema de archivos `pickle` por JSON o TOML para los
  diccionarios de afinación: más portable y diff-friendly.
- Implementar los modos **glide / arp / step sequencer**.
- Añadir cobertura de tests con `pytest` y mocks de `RPi.GPIO` y `spidev`.
- Migrar a un sistema de eventos asyncio en lugar de bucle FIFO blocking.
- Considerar Raspberry Pi Pico (RP2040) o un MCU dedicado para reducir el
  arranque (actualmente ~14 s) — el problema de polifonía / latencia se
  beneficiaría enormemente.
- Soporte para **MIDI 2.0** y mensajes RPN/NRPN para aprovechar más el
  controlador.
