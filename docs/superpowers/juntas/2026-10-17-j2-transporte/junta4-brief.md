# Brief de junta — cuarta pasada — 2026-10-19 — las fichas B y C y la enmienda de R-H4

## 1. La pregunta

Samuel firmó las fichas A, D, E, F y G el 19-10 (`acta-2026-10-19.md`). B (quién autoriza la escalada del GPDMA1) y C (cuándo se rinde una ranura) salieron de la firma hasta que el modelo de seis ranuras de §5.2(h) corriera las candidatas y una junta lo revisara. Eso ya existe: el modelo es el crate `software/nucleo/modelo` sobre la máquina real de `core` (PR #447, en `main`), K1 a K5 están en `core` y en `fw`, la escalada denegada ha corrido en placa, y el banco del J2 en TCM (PR #448, en `main`) mide lo que pide R-H4. El papel (§0.4, fichas B, C y H, §2.5, R-H4 y §3) propone cómo cerrar las tres cosas. Esta pasada juzga eso y nada más:

1. **Ficha B, la escalada.** La propuesta es K1 con 6 escaladas en cualquier ventana de 1 s y una **espera mínima de 2 ms entre dos escaladas concedidas** (candidata nueva: `Presupuesto::con_espera`; la escalada pedida dentro de la espera se aplaza, la ranura sigue en `Reiniciando` con su cota y el planificador la vuelve a pedir al cumplirse). Pon al lado las dos reglas de presupuesto que la propuesta compara, **6 en 1 s y 2 en 100 ms**, junto al hallazgo del barrido: **el presupuesto lo gasta la duración de un bloqueo, no el número de fallos**, y sin espera un bloqueo de 1 ms del GPDMA1 reinicia el chip en las cinco fases con la regla de `fw` (3 en 1 s). Samuel pide que la junta **decida explícitamente** una cosa: **durante un solo bloqueo de 1 ms, las escaladas seguidas ¿necesitan una espera entre reset y reset, o un bloqueo de 1 ms debe gastar el presupuesto sin más?** Contesta esa pregunta con un sí o un no y su porqué, aunque no estés de acuerdo con la propuesta.
2. **Ficha C, las cotas.** `Vencida` 25 ms y `Reiniciando` 12,5 ms, en µs sobre el reloj de K2, con el aserto `plazo + cota_vencida + cota_reiniciando + inanición (R-H1, 12 ms) < T_WATCHDOG_TRAMA_US`. ¿Se puede cerrar con la evidencia que hay, o qué falta exactamente?
3. **R-H4: el texto y los estáticos del J2 pasan de «en RAM» a «en TCM»**, con la huella en bytes para que la tabla de obligaciones del hub (R-H6) tenga una obligación de memoria concreta. ¿La cifra mide lo que dice, y qué le falta?

No se reabre nada de lo firmado (A, D, E, F, G), ni el diseño de K2 a K5, que el modelo dio por bueno contra lo que el papel afirma (`modelo/tests/junta.rs`). Si ves que algo de eso está roto, dilo en una línea y sigue.

## 2. La evidencia

Cada cifra con su estatus: **(S)** simulada en el modelo, **(M)** medida en placa, **(A)** aritmética.

**El modelo** (`software/nucleo/modelo`, en `main` más la rama `j2/modelo-espera`):

- `v3a4`, un canal que el reset no cura: con 3 en 1 s, tres escaladas, la cuarta negada a los 0,91 ms, la ranura muere a los 13,62 ms y el supervisor reinicia el chip a los 115 ms; cada vecina pierde exactamente tres tramas, todas como plazo ajeno (S).
- `v3a5`, un bloqueo del GPDMA1 de duración `D` (todos los canales, cinco fases): sin espera, 100, 270 y 400 µs gastan 0, 1 y 2 escaladas, y 1 000 µs o más reinician el chip en las cinco fases (S).
- El barrido de `E` y su ventana con el fuzz de la junta (30 corridas de 4 s; cuelgues 15/s, atascos curables 0,8/s, P2 30/s, tics tardíos 5/s), reinicios del chip: 3 en 1 s, 4 de 30; 6 en 1 s, 0; 2 en 100 ms, 0; 1 en 100 ms, 7; 3 en 10 s, 13; escalar siempre, 0 (pero un canal incurable escala 1 400 veces en 350 ms) (S). `modelo/tests/barrido.rs`.
- **La espera** (`modelo/tests/espera.rs`, rama `j2/modelo-espera`). Bloqueo de `D`: escaladas máximas / reinicios del chip en 5 fases (S):

| regla | espera | 400 µs | 1 ms | 2 ms | 3 ms | 5 ms | 10 ms |
|---|---|---|---|---|---|---|---|
| 3 en 1 s | 0 | 2 / 0 | 3 / 5 | 3 / 5 | 3 / 5 | 3 / 5 | 3 / 5 |
| 3 en 1 s | 2 ms | 1 / 0 | 1 / 0 | 1 / 0 | 2 / 0 | 3 / 0 | 3 / 5 |
| 6 en 1 s | 0 | 2 / 0 | 4 / 0 | 6 / 5 | 6 / 5 | 6 / 5 | 6 / 5 |
| 6 en 1 s | 2 ms | 1 / 0 | 1 / 0 | 1 / 0 | 2 / 0 | 3 / 0 | 5 / 0 |
| 2 en 100 ms | 0 | 2 / 0 | 2 / 5 | 2 / 5 | 2 / 5 | 2 / 5 | 2 / 5 |
| 2 en 100 ms | 2 ms | 1 / 0 | 1 / 0 | 1 / 0 | 2 / 0 | 2 / 5 | 2 / 5 |

  Con 1 ms y 5 ms de espera, y el canal incurable con cada regla, en la salida completa del barrido. En el bloqueo, cada ranura pierde como mucho una trama como plazo ajeno; las demás son plazos propios del bloqueo. Con el canal incurable la espera no cambia nada salvo el momento: `E` tramas por vecina y el reinicio entre los 115 y los 140 ms (125 ms con 6 en 1 s y 2 ms de espera). En los dos fuzz la espera no actúa (0 aplazadas): sus atascos curables los cura la primera escalada y llegan separados, así que los reinicios del fuzz los arregla el tamaño del presupuesto y no la espera.
- Las cotas: con K2, la de 25 ms vence entre 25,12 y 25,32 ms con uno de cada dos o cuatro tics hasta 200 µs tarde (antes, a los 16,75 ms); retenciones del planificador de 5 y 14 ms se aguantan, y con 30 ms mueren las seis ranuras a los 25,2 ms (S, `v3a8`). Las cotas no se han barrido.

**El banco** (`software/nucleo/fw/EN-PLACA.md`, «Recuperación con el presupuesto de escaladas y el incidente», firmware `5963841`): diez escaladas forzadas separadas 400 ms, ninguna negada, cada vecina con 10 plazos ajenos y ningún plazo propio; con la ventana vacía, cuatro escaladas seguidas dan tres concedidas y una negada, la ranura 3 muere por su cota y la ranura 2 sigue sellando (M). La espera no está en `fw`.

**El J2 en TCM** (rama `j2/huella-tcm`): la huella y la CPU están en el papel, §3 y R-H4. Lo nuevo de esta rama: el reloj de K2 divide en 64 bits en cada entrada del tic, y el cuerpo de esa división se quedaba fuera de la ITCM.

## 3. Cómo responder

Máximo **8 hallazgos**, cada uno con evidencia (cita de ≤ 25 palabras o `archivo:línea`), gravedad (BLOCKER / ALTA / MEDIA / BAJA) y qué lo rompe en concreto. Después, **un veredicto por pregunta**, en tres líneas como mucho cada uno:

- **B:** qué regla firmarías (6 en 1 s, 2 en 100 ms u otra), y la respuesta explícita a la pregunta de Samuel sobre la espera durante un bloqueo de 1 ms: sí o no, y por qué.
- **C:** se cierra o no; si no, qué falta exactamente.
- **R-H4:** la cifra vale o no; si no, qué le falta.

No reescribas el papel.

**Halberg** puede correr el modelo (desde `D:\Desktop\projects\sam17\.claude\worktrees\espera\software\nucleo`):

```bash
cargo test -p sam17-nucleo-modelo --release --test espera -- --ignored --nocapture   # el barrido de la espera
cargo test -p sam17-nucleo-modelo --release --test barrido -- --ignored --nocapture  # E y su ventana
cargo test -p sam17-nucleo-modelo --release --test junta -- --nocapture             # los escenarios de la tercera pasada
```

Si cambias algo para probar una variante, hazlo en una copia y di qué cambiaste y qué dio.

## 4. Archivos

- El papel: `D:\Desktop\projects\sam17\.claude\worktrees\junta4\docs\superpowers\juntas\2026-10-17-j2-transporte\papel-v3.md` (rama `docs/junta4-fichas-b-c`), con el acta del 19-10 y tus informes de las pasadas anteriores en la misma carpeta.
- El modelo y la espera: `D:\Desktop\projects\sam17\.claude\worktrees\espera\software\nucleo` (rama `j2/modelo-espera`): `core/src/escaladas_j2.rs`, `modelo/src/motor.rs` (`RecDecide`, `plan_drain`), `modelo/tests/espera.rs`, `modelo/tests/junta.rs`, `modelo/tests/barrido.rs`.
- La TCM: `D:\Desktop\projects\sam17\.claude\worktrees\huella\software\nucleo\fw` (rama `j2/huella-tcm`): `j2_tcm.x`, `src/j2_tcm.rs`, `src/j2_tic.rs` (los `link_section`), `EN-PLACA.md`.
- La spec: `docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`.
