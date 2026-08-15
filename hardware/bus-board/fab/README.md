# Ficheros de fabricación — bus board

Generados por `kicad/build_pcb.py` + `kicad-cli`. **Se piden DOS unidades
idénticas** (dos segmentos).

## Especificación

| | |
|---|---|
| Dimensiones | 320 × 60 mm |
| Capas | 2 |
| Cobre | **1 oz (35 µm)** — el presupuesto de masa está calculado con ese espesor |
| Espesor | 1.6 mm |
| Acabado | HASL o ENIG, indiferente |
| Vías | **ninguna** |

El cobre de 1 oz no es negociable a la baja. Con 0.5 oz la resistencia del
plano se dobla; el margen sigue alcanzando, pero deja de haberlo.

## Antes de pedir

1. **Verificar el orden de filas del peine Eurorack con un polímetro** contra un
   cable Doepfer o un módulo real. De fuente primaria está confirmado que la
   franja roja es −12 V y va abajo; el orden del bloque central (GND×3 y luego
   +12 V) viene de fuentes secundarias coincidentes, no de una tabla oficial.
   **Equivocar esa fila destruye cualquier módulo que se enchufe.** Ver
   [`../notes/design-notes.md` §12.1](../notes/design-notes.md).
2. Comprobar en el visor de gerbers que el silk pone `-12V` **junto al par de
   abajo** de cada peine `J1..J6`.

## Al montar

- **Separadores de nylon**, no metálicos ([`../README.md`](../README.md)).
- Los PTC tienen el **pad 2 duplicado**: dos taladros para dos encapsulados
  distintos (Bourns en línea, Bel Fuse escalonado). Se puebla **uno solo**.
- Los LED van con el ánodo hacia el lado que está a más potencial: en la franja
  de arriba hacia +12 V, en la de abajo hacia el módulo. La serigrafía lo marca.
