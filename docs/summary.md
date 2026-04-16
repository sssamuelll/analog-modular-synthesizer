# Resumen de la tesis

> *Sintetizador Analógico Modular* — Trabajo de Grado para optar al título de
> Ingeniero Electrónico en Computación. Universidad Yacambú, Vicerrectorado
> Académico, Facultad de Ingeniería. Barquisimeto, Agosto de 2020.
> Autor: **Samuel Darío Ballesteros García**. Tutor: **Douglas Domínguez**.

## Objetivo

Construir un **sintetizador analógico modular económico de uso profesional** que
combine la libertad creativa de un sistema modular con la portabilidad de un
controlador MIDI, capaz de competir en calidad sonora con instrumentos de gama
alta (Korg MS-20, Moog Minimoog, Prophet 5, etc.) a una fracción del costo.

## Planteamiento

En Venezuela los sintetizadores analógicos comerciales son inaccesibles (1 000 –
35 000 USD). La alternativa habitual —simulación por software— sacrifica calidad
de sonido. La propuesta es fabricar un sintetizador analógico modular local
cuyo costo total de componentes se estima en **≈ 720 USD**.

## Arquitectura

7 módulos interconectables, de los cuales **uno es digital** (MIDI/CV con
Raspberry Pi) y **seis son analógicos**:

1. **Alimentación** — fuente regulada 5 V / +12 V / −12 V desde 110 VAC.
2. **MIDI/CV** — Raspberry Pi 3B+ + DAC AD5686R: 3 salidas CV (1 V/oct, 84
   notas) + 1 salida GATE.
3. **VCO** — 3 osciladores CEM3340 (sierra, triangular, cuadrada con PWM).
4. **Mixer** — sumador de 3 canales con TL074.
5. **VCF** — filtro pasa-bajo OTA tipo Korg MS-20 (LM13700 + TL074), 24 dB/oct,
   resonancia auto-oscilante.
6. **ADSR** — generador de envolvente con ICM7555 en modo monoestable.
7. **VCA** — amplificador controlado por voltaje con LM13700 (etapa final).

Todo se ensambla en un cajón de madera de **950 × 440 × 100–200 mm** con
paneles de lámina galvanizada de 0.5 mm.

## Software (módulo MIDI/CV)

Escrito en **Python 3** sobre Raspbian, ejecutado en un Raspberry Pi 3B+.
Librerías: `mido` (MIDI), `python-spidev` (SPI al DAC), `RPi.GPIO`, `pyudev`
(detección USB), `Adafruit_CharLCD` (LCD 16×2), `multiprocessing`, `threading`.

Modos de ejecución:

- **standard** — conversión MIDI → CV monofónica con pitch-bend.
- **tune** — afinación interactiva de cada VCO con guía en LCD.
- **glide**, **arp**, **step sequencer** — declarados en el diseño original
  como modos a desarrollar.

El menú se navega con 4 botones (back, enter, up, down) en una pantalla LCD
16×2. La salida CV usa los canales A, B, C del AD5686R (direcciones SPI
`0x11`, `0x12`, `0x14`); el canal D queda libre.

## Resultados de la tesis

| Módulo | Encendido | Calentamiento | Funcionalidad |
|--------|-----------|---------------|---------------|
| Alimentación | OK | — | 5 V / +12 V / −12 V correctos |
| MIDI/CV | OK (14 s arranque) | Normal | Tiempos óptimos, apto para uso en vivo |
| VCO | OK | — | Onda triangular con menor amplitud que sierra/cuadrada |
| Mixer | OK | — | Mezcla limpia sin ruido |
| VCF | OK | — | Frecuencia de corte espectacular, auto-oscila |
| VCA | OK | — | Funcionamiento perfecto |
| ADSR | OK | — | Cumple los requerimientos |

Variación de la curva 1 V/oct medida sobre 73 notas:

- VCO1: **+0.45 %**
- VCO2: **−3.32 %**
- VCO3: **−18.62 %** (sólo 5 octavas útiles, requiere recalibración)

## Conclusiones del autor

El proyecto demuestra la viabilidad técnica y económica de fabricar
instrumentos analógicos modulares en Venezuela. El prototipo entrega calidad
sonora comparable a equipos de gama alta a un costo significativamente menor.

## Mejoras posibles ya identificadas en la tesis

- Recalibrar VCO3 (curva 1 V/oct con −18.6 % de error).
- Reemplazar cables jumper por cableado dedicado: la tesis identificó
  conexiones intermitentes como principal fuente de fallos.
- Añadir 2 envolventes ADSR adicionales (la especificación final menciona 2,
  pero el prototipo entregó 1).
- Implementar los modos `glide`, `arp` y `step sequencer` declarados.

Estas y otras propuestas se documentan en cada README de módulo bajo la
sección *Mejoras propuestas*.
