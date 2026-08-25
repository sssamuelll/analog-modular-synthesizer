# Módulo 4 — Mixer (mezclador de VCOs)

> [!IMPORTANT]
> **Superado como módulo separado — 2026-08-23.** La suma de los dieciséis canales, el volumen general, la salida principal y los oídos se mudan a la placa del módulo de Voz. Un mixer solo tiene sentido si es independiente de su fuente y de sus salidas; éste estaba soldado a las voces.
> Lo de abajo se conserva como el diseño de referencia del circuito, que
> es de donde sale el carácter. Manda el
> [spec del módulo de Voz total](../superpowers/specs/2026-08-23-modulo-voz-total-design.md).

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
