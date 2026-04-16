# Módulo 4 — Mixer (mezclador de VCOs)

> Referencia: tesis, *Módulo Mezclador* (Gráficos 27, 28).

## Objetivo

Sumar las salidas de los tres VCOs (o cualquier fuente externa de audio)
en una única señal antes de entrar al filtro.

## Topología

Sumador inversor clásico con un op-amp del **TL074**. Cada entrada lleva
un potenciómetro para ajustar su nivel individualmente. La salida está
acoplada en DC, lo que permite sumar tensiones de control además de audio
(útil pero impone cuidado: ver nota más abajo).

## Entradas / Salidas

| Pin | Tipo | Notas |
|-----|------|-------|
| `IN-1`, `IN-2`, `IN-3` | Entradas | ±12 V máx. (sustituibles por señal externa) |
| `LVL-1/2/3` | Pot. panel | Volumen por canal |
| `OUT` | Salida | Suma acoplada en DC |

> ⚠️ Mezclar señales de audio con señales de control producirá resultados
> que pueden o no ser deseables. Es una característica, no un bug, propia
> de la modularidad.

## Mejoras propuestas

- Añadir un **headroom indicator** (LED clipping).
- Versión con interruptor por canal (mute).
- Diseñar variante **AC-coupled** seleccionable para uso exclusivo de audio.
- Considerar realizar tanto un mixer activo (TL074) como pasivo y comparar
  el ruido de fondo.
