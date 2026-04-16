# Módulo 3 — VCO (×3)

> Referencia: tesis, *Módulo VCO* (Gráficos 25, 26).

## Objetivo

Generar las señales periódicas que serán esculpidas por el resto del
sintetizador. Tres osciladores idénticos basados en **CEM3340**, cada uno
capaz de producir tres formas de onda simultáneamente.

## Por qué el CEM3340

- Mismo chip empleado en el clásico **Sequential Prophet 5**.
- Estándar 1 V/octava nativo.
- Genera sierra, triangular y cuadrada con PWM.
- Disponible aún (en variantes re-fabricadas).

## Entradas / Salidas (por VCO)

| Pin | Tipo | Notas |
|-----|------|-------|
| `CV-IN`  | Entrada | 0 – 12 V, escala 1 V/octava |
| `TUNE`   | Pot. panel | Afinación gruesa (~±2 octavas) |
| `PWM-CTL`| Pot. panel | Ancho de pulso 2 % – 98 % (50 % = onda cuadrada) |
| `SAW-OUT`| Salida | Diente de sierra |
| `TRI-OUT`| Salida | Triangular |
| `SQR-OUT`| Salida | Cuadrada (con PWM ajustable) |

## Resultados del prototipo (tesis, Gráficos 62–66, Tabla 11)

- VCO1: variación 1 V/oct = **+0.45 %** (excelente).
- VCO2: variación 1 V/oct = **−3.32 %** (aceptable).
- VCO3: variación 1 V/oct = **−18.62 %** (mal afinado, sólo 5 octavas
  utilizables).
- La onda triangular sale con menor amplitud que sierra y cuadrada.

## Mejoras propuestas

- **Calibrar el VCO3** ajustando los trimmers de offset y escala 1 V/oct
  (procedimiento de calibración a documentar en este módulo).
- Buffer de salida con misma ganancia para las tres formas de onda
  (compensar el bajo nivel de la triangular).
- Añadir **entrada de FM lineal** y **PWM CV-IN** (modulación del ancho
  por voltaje).
- Añadir **sync** (hard sync entre VCOs) — clásico de Prophet 5.
- Documentar tolerancia de los condensadores de tempo (afecta directamente
  la afinación).
