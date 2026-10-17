# Brief de junta — tercera pasada, acotada — 2026-10-17 — el papel v3 absorbido

## 1. La pregunta

La segunda pasada (`junta2_serrano.md`, `junta2_halberg.md`, `junta2_voronov.md`) juzgó el `papel-v3.md` del commit `72d6e6f`. El papel se reescribió para absorberla (commit `4c639f0`), y la reescritura **introduce mecanismos que ninguna junta ha visto**. Esta pasada es corta y tiene dos preguntas, nada más:

1. **¿Los mecanismos nuevos tienen el mecanismo equivocado?** Son cuatro, y el papel los marca como no construidos:
   - §2.5: el **permiso de escalada** que da la política (`Accion::Reiniciar { escalar }`, `umbral_escalada` = 3 plazos propios en la ventana de D7.3), la **denegación** que acaba, si los canales no paran, en la cota de `Reiniciando`, y **`Evento::PlazoAjeno`** para las vecinas que cruza una escalada (no puntúa en su salud).
   - §2.7: **el tic cuenta periodos, no entradas** (suma `max(1, round(Δciclos / periodo))` del contador de ciclos libre; la máquina avanza `edad` y `espera` en ese número).
   - §2.2: la **identidad retirada** (la limpieza la pide el planificador cuando la política pasa a `Vacia`), **`SUCIA` como entrada con cota**, `Muerta` sin salida, las precedencias.
   - §2.11 y R-H8: el **supervisor del IWDG** como requisito, con la relación entre su ventana, los 37,5 ms de las cotas (25 + 12,5 ms, en µs con aserto) y `T_IWDG`.
2. **¿Tu informe de la segunda pasada quedó resuelto?** El papel lo dice en §9, hallazgo por hallazgo. Di cuáles no, y por qué, en una línea cada uno.

No se reabre nada más: ni la adopción (ficha A) ni lo que la segunda pasada dio por bueno.

## 2. Cómo responder

Máximo **8 hallazgos nuevos**, cada uno con evidencia (cita de ≤ 25 palabras o `archivo:línea`), gravedad (BLOCKER / ALTA / MEDIA / BAJA) y qué lo rompe en concreto. Después, la lista de tus hallazgos de la segunda pasada que **no** quedaron resueltos. No reescribas el papel.

## 3. Archivos

Repo `D:\Desktop\projects\sam17\.claude\worktrees\papel-v3` (rama `docs/papel-v3-transporte-tic`): `docs/superpowers/juntas/2026-10-17-j2-transporte/papel-v3.md` (el papel absorbido), tu informe `junta2_*.md`, el código bajo `software/nucleo/` y la spec en `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`. El simulador de la segunda pasada (Halberg) está fuera del repo, en el directorio temporal de la sesión, en `...\scratchpad\halberg2\sim`.
