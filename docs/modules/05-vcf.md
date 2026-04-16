# Módulo 5 — VCF (filtro pasa-bajo OTA tipo MS-20)

> Referencia: tesis, *Módulo VCF* (Gráficos 29–35). Filtro inspirado en el
> Korg MS-20 y desarrollado a partir del estudio de Stinchcombe (2006).

## Objetivo

Implementar un filtro pasa-bajo controlado por voltaje con resonancia
auto-oscilante, adecuado para síntesis sustractiva.

## Topología

Filtro **OTA pasa-bajo de 24 dB/oct** con dos celdas en serie. Las
resistencias variables de cada celda RC se sustituyen por la
transconductancia de un OTA, controlada por la corriente `Iabc`. Esto
permite barrer la frecuencia de corte con una entrada de voltaje.

### Ecuación clave

```
fc = (19.2 · k) / (2π · C1) · Iabc
```

Donde `k = R2/R1` (red de atenuación a la entrada del OTA) y `Iabc` es la
corriente de control. Con un convertidor exponencial estándar, una entrada
1 V/oct mueve la frecuencia de corte una octava por voltio.

### Componentes

| Componente | Cantidad | Rol |
|------------|----------|-----|
| LM13700 (doble OTA) | 1 | Núcleo del filtro (X1 + X2) |
| TL074 (cuádruple op-amp) | 1 | Buffers, sumador de realimentación, conversores |

## Entradas / Salidas

| Pin | Tipo | Notas |
|-----|------|-------|
| `AUDIO-IN` | Entrada | ±5 V típico |
| `CV-IN`    | Entrada | 1 V/octava |
| `CUTOFF`   | Pot. panel | Ajuste manual de la frecuencia de corte |
| `RESONANCE`| Pot. panel | 0 a auto-oscilación |
| `CV-MOD`   | Pot. panel | Atenuador de la entrada CV |
| `AUDIO-OUT`| Salida | Señal filtrada |

## Notas de implementación

- En la realimentación de resonancia se incluyen **LEDs** para añadir una
  ligera distorsión deseada (Gráfico 65 muestra los armónicos extra).
- La banda pasante presenta respuesta máxima plana, transición rápida y
  fase lineal.
- Seleccionar **C1 = C2** y **Iabc** simétricas en ambos OTAs.

## Mejoras propuestas

- Añadir entradas adicionales **CV-IN 2** y **CV-IN 3** sumadas
  ponderadamente.
- Conmutador **24 dB / 12 dB / 6 dB** por octava.
- Variante en **2-pole multimode** (LP/BP/HP) reutilizando el mismo OTA.
- Aislar térmicamente el LM13700 para reducir deriva.
- Documentar el procedimiento de calibración del trim de simetría.
