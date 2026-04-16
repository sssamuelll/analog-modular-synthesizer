# Módulo 6 — ADSR (generador de envolvente)

> Referencia: tesis, *Módulo de Envolvente* (Gráficos 36–41) y Schmitz Bits
> *Third ADSR* schematic.

## Objetivo

Generar una señal de control en forma de envolvente ADSR (Attack – Decay
– Sustain – Release) que pueda modular el VCA, el VCF u otros parámetros
del sintetizador.

## Topología

Núcleo basado en el **timer ICM7555** en configuración monoestable. La
carga y descarga de un único condensador electrolítico atraviesa cuatro
caminos diferentes según la etapa, controlados por una red de transistores
y diodos.

### Etapas

| Etapa | Mecanismo |
|-------|-----------|
| Attack | El pin `OUTPUT` del 7555 sube → corriente carga el cap a través del pot ATTACK. |
| Decay | Al alcanzar el `THRESHOLD`, `OUTPUT` baja → el cap descarga a través del pot DECAY hacia un op-amp drenador. |
| Sustain | El op-amp deja de drenar cuando el voltaje del cap iguala al setpoint del pot SUSTAIN. |
| Release | Cuando GATE baja, el transistor de release se polariza → el cap se vacía a través del pot RELEASE hasta resetear el 7555. |

## Entradas / Salidas

| Pin | Tipo | Notas |
|-----|------|-------|
| `GATE-IN`  | Entrada | Pulso 0/10 V del módulo MIDI/CV |
| `ATTACK`   | Pot. panel | Tiempo de ataque |
| `DECAY`    | Pot. panel | Tiempo de caída |
| `SUSTAIN`  | Pot. panel | Nivel de sostenimiento |
| `RELEASE`  | Pot. panel | Tiempo de liberación |
| `ENV-OUT`  | Salida | Señal de control 0 – ~10 V |

## Mejoras propuestas

- **Duplicar** el módulo: la especificación final menciona 2 envolventes
  pero el prototipo entregó 1.
- Añadir LED indicador de la magnitud de la envolvente.
- Modo **looping** (envolvente como LFO complejo).
- Versión digital con MCU para envolventes multietapa (DAHDSR, MSEG).
- Salida invertida adicional.
- Trigger por *velocity* MIDI mediante CV adicional.
