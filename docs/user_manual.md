# Manual de usuario, instalación y mantenimiento — SAM17 v1.0

> Este manual reproduce y reorganiza el manual de usuario incluido en el
> Capítulo III de la tesis. Sigue las advertencias de seguridad antes de
> manipular el equipo.

## 1. Instrucciones de seguridad

> ⚠️ **Advertencia**

1. Toma precauciones para usar el equipo de manera segura. Si tienes dudas,
   pide asesoramiento profesional.
2. **No exponer** el equipo a contacto con agua o cualquier líquido. Si ocurre,
   desconecta la alimentación eléctrica de inmediato.
3. El equipo genera sonido capaz de **dañar el sistema auditivo**. Usa volúmenes
   seguros y haz pausas.
4. Las piezas internas **no las puede reparar el usuario**. Acude a un técnico
   calificado, especialmente si:
   - el equipo se ha caído y dejado de funcionar,
   - le ha caído líquido,
   - los cables de alimentación se han dañado,
   - no funciona correctamente según este manual.

## 2. Componentes incluidos

- Sintetizador analógico modular SAM17.
- Manual del usuario.
- Cables de conexión (jack 3.5 mm mono).

Necesitarás adicionalmente:

- Mesa o superficie estable.
- Controlador MIDI con cable USB.
- Altavoz amplificado o audífonos con conector 1/8" (3.5 mm).
- Toma de 110 VAC con cableado adecuado (60 Hz).

> ⚠️ Usa cable **TS** (mono) para la salida de línea. Un cable TRS (estéreo)
> causará cancelación de fase y señal muy débil.

## 3. Conexiones básicas

1. Conecta el cable de alimentación a la red 110 VAC.
2. Conecta tu controlador MIDI al puerto USB del módulo MIDI/CV.
3. En el módulo MIDI/CV, espera a que la pantalla LCD muestre el menú
   principal (~14 s tras encendido, mientras arranca el Raspberry Pi).
4. Conecta los módulos entre sí con cables de 3.5 mm. Conexión sugerida:
   `VCO1/2/3 → MIXER → VCF → VCA → AUDIO OUT`.
5. Conecta `MIDI/CV CV` a `VCO CV-IN` y `MIDI/CV GATE` a `ADSR GATE`.
   Enruta `ADSR OUT` a `VCA CV-IN`.
6. Conecta tu altavoz/audífonos a `VCA AUDIO OUT`.

Diagrama: ver Gráfico 61 de la tesis.

## 4. Módulos y controles

### 4.1 Alimentación
Interna. No tiene controles en el panel. Genera 5 V, +12 V y −12 V para
todo el sistema.

### 4.2 MIDI/CV
Pantalla LCD 16×2 con menú navegable por 4 botones (Back / Enter / Up / Down).
Entradas: USB (controlador MIDI). Salidas: 3 × CV (1 V/oct, 84 notas) y 1 ×
GATE (10 V).

Modos disponibles:
- **Standard**: conversión MIDI → CV monofónica.
- **Tune**: afinación interactiva por nota y por VCO.
- **Glide / Arp / Step Sequencer**: modos previstos en el diseño original
  (en desarrollo).

### 4.3 VCO (×3)
- **CV-IN**: entrada de control por voltaje.
- **TUNE**: afinación gruesa.
- **PWM-CTL**: ancho de pulso (~2 % a ~98 %, 50 % = onda cuadrada).
- Salidas: **SAW**, **TRI**, **SQR/PWM**.

### 4.4 Mixer
Tres entradas (VCO1/2/3 o señal externa ±12 V), cada una con su control de
volumen. Salida sumada acoplada en DC (puede sumar señales de control además
de audio).

### 4.5 VCF
Filtro pasa-bajo 24 dB/oct con resonancia auto-oscilante.
- **CUTOFF**: frecuencia de corte (20 Hz – 20 kHz).
- **RESONANCE**: realimentación / pico en la frecuencia de corte.
- **CV-MOD**: intensidad de modulación por CV.
- **AUDIO-IN / CV-IN / AUDIO-OUT**.

### 4.6 VCA
Etapa final de amplificación. Entradas: AUDIO-IN, ENV-IN (envolvente),
control de VOLUME. Salida: AUDIO-OUT.

### 4.7 ADSR
- **GATE-IN**: pulso del módulo MIDI/CV.
- **ATTACK / DECAY / SUSTAIN / RELEASE**: 4 potenciómetros.
- **OUT**: señal de control hacia VCA y/o VCF.

## 5. Especificaciones

| Parámetro | Valor |
|-----------|-------|
| Tipo | Sintetizador analógico modular |
| Motor de sonido | Analógico |
| Polifonía | Monofónica |
| Fuentes de sonido | 3 VCOs (sierra, triangular, cuadrada con PWM) |
| Filtro VCF | Pasa-bajo, resonancia auto-oscilante |
| Envolventes | 2 ADSR (especificación; prototipo: 1) |
| Puntos de conexión | 40 jacks 3.5 mm (15 in / 25 out) |
| MIDI | USB |
| Dimensiones | 950 × 440 × 200 mm (37.4 × 17.25 × 8 in) |
| Alimentación | 110 VAC 60 Hz |
| Peso | 7.25 kg (16 lbs) |

## 6. Mantenimiento

- Limpia los paneles con un paño seco; evita disolventes.
- Revisa periódicamente las soldaduras de los jacks de 3.5 mm: la tesis
  reporta que los cables jumper son la principal fuente de fallos.
- No abras la unidad si no estás cualificado.
- Si un VCO pierde afinación, usa el modo **Tune** del módulo MIDI/CV con
  un afinador externo (vocal pitch monitor o similar).
