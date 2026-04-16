# Módulo 7 — VCA (amplificador controlado por voltaje)

> Referencia: tesis, *Módulo VCA* (Gráficos 42–49). Diseño basado en
> Wiltshire, *Design a Eurorack Vintage VCA with the LM13700* y Chamberlin,
> *Musical Applications of Microprocessors* (CA3080).

## Objetivo

Etapa final del sintetizador: amplifica o atenúa la señal proveniente del
VCF según el nivel de la entrada CV (típicamente alimentada por la salida
del ADSR).

## Topología

Núcleo basado en el **LM13700 (OTA)** sin diodos de linealización para
preservar el carácter "soft drive" característico de los sintetizadores
clásicos.

### Cadena de señal

1. **Atenuador de entrada** — divisor 100 kΩ / 620 Ω para reducir 10 Vpp a
   ~60 mVpp (zona de baja distorsión del OTA, ~2–3 %).
2. **OTA LM13700** con `Iabc` máx. 500 µA → corriente de salida hasta
   576 µA.
3. **Convertidor I a V** (transimpedancia) con resistencia de
   realimentación 18 kΩ → salida de hasta ±10 V.
4. **Convertidor V a I** activo (op-amp + transistor PNP) que transforma el
   CV de entrada (0 – 5 V o 0 – 10 V) en `Iabc`.
5. Mezclador de CV con capacitor de smoothing (`C1` + `R10`) para reducir
   ruido en la línea de control.

### Cálculos clave (de la tesis)

- Atenuador: `R2/(R1+R2) = 620/(100k+620) ≈ 0.0062 → 10 V × 0.0062 ≈ 62 mV`.
- Salida del OTA: `Iout = 19.2 · Iabc · Vin = 19.2 · 500 µA · 60 mV ≈ 576 µA`.
- Conversor I→V: `Rf = 10 V / 576 µA ≈ 17.36 kΩ → 18 kΩ valor estándar`.
- Conversor V→I: `Rin = 5 V / 500 µA = 10 kΩ`.
- Protección Iabc: `R = 12 V / 2 mA = 6 kΩ → 6.8 kΩ valor estándar`.

## Entradas / Salidas

| Pin | Tipo | Notas |
|-----|------|-------|
| `AUDIO-IN`  | Entrada | ±5 V típico |
| `ENV-IN`    | Entrada CV | 0 – 5 V (envolvente del ADSR) |
| `VOLUME`    | Pot. panel | Atenuador master |
| `AUDIO-OUT` | Salida | Salida principal del sintetizador (a TS 3.5 mm) |

> ⚠️ **No usar cable TRS (estéreo)** en la salida: causa cancelación de
> fase y señal muy débil.

## Mejoras propuestas

- Versión con **diodos de linealización** habilitados/deshabilitados por
  jumper o switch — comparar carácter sonoro.
- Añadir **respuesta exponencial** del CV (más musical) además de la lineal.
- Considerar el **SSI2164** o **SSI2162** para mejor THD y signal-to-noise.
- Salida balanceada TRS opcional para conexión a interfaces de audio.
- Buffer de salida de baja impedancia con protección contra cortocircuitos.
