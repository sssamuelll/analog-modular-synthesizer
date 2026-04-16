# Módulo 1 — Alimentación

> Referencia: tesis, *Módulo de Alimentación* (Gráficos 22, 23, 24).

## Objetivo

Generar las tensiones reguladas requeridas por todo el sistema:

- **+5 V** — alimentación digital (Raspberry Pi, LCD, lógica).
- **+12 V** — op-amps, OTAs, CEM3340.
- **−12 V** — op-amps, OTAs.

## Entrada

- Transformador externo **12 VAC / 2 A** conectado a 110 VAC 60 Hz.
- Recomendado usar protector de voltaje upstream del transformador.

## Topología (a partir de la tesis)

Rectificador de onda completa (puente) → filtrado por condensadores
electrolíticos → reguladores lineales **78xx / 79xx**.

| Riel | Regulador | Capacidad mínima sugerida |
|------|-----------|---------------------------|
| +12 V | 7812 | 1 A |
| −12 V | 7912 | 0.5 A |
| +5 V  | 7805 | 2 A (para Raspberry Pi) |

> El prototipo original usa un transformador independiente para alimentar el
> Raspberry Pi por su consumo (≤ 2 A) y mantener limpio el riel analógico.
> Se recomienda mantener esta separación o, alternativamente, dimensionar
> filtros y disipadores adecuados en el módulo único.

## Distribución

Las tres salidas se reparten por un **bus interno** del cajón, con pin
headers o conector tipo Eurorack (ver `docs/architecture.md`).

## Mejoras propuestas

- Sustituir reguladores lineales por DC-DC para mejor eficiencia (con
  filtrado adecuado para no inyectar ruido en los rieles analógicos).
- Añadir LEDs indicadores por riel.
- Añadir fusibles térmicos en el primario del transformador.
- Documentar cálculos de disipación térmica de los reguladores.
- Considerar un rail bus tipo **Eurorack ±12 V / +5 V** estándar para
  compatibilidad con módulos comerciales.
