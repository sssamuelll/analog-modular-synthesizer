# Simulador del transporte por tic (junta del 2026-10-17)

Lo escribió Halberg durante la junta: modela la máquina de `core::transporte_j2` y la política de `core::maestro_j2` (copias en `src/`, con las reglas de cada pasada), el tic, el planificador, la recuperación, el GPDMA1, P2 y el supervisor del IWDG. **Modela, no mide:** las cifras que salen de aquí llevan (S) en `papel-v3.md`. Calibrado contra el banco con el SPI envenenado (124,5 / 125,5 / 127,6 / 131,5 / 249,9 µs simulados frente a 123 / 125 / 126 / 131 / 249 medidos).

| Carpeta | Pasada | Reglas |
|---|---|---|
| `junta2/` | segunda (`junta2_halberg.md`) | el v3 anterior a la junta, con el presupuesto de escaladas que se retiró |
| `junta3/` | tercera (`junta3_halberg.md`) | el v3 absorbido: permiso de la política, periodos reconstruidos, `SUCIA` en `Vencida`, supervisor de R-H8 |

No es parte del workspace de `software/nucleo` ni lo compilan las puertas. Para correrlo:

```
cd junta3
cargo run --release -- v3perm
```

Los escenarios de cada pasada están en `src/main.rs`; los de la tercera, en `src/v3.rs`.
