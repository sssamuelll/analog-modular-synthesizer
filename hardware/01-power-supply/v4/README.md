La fuente v4 sustituye el frente rectificador de la v3 por seis modulos Mean Well IRM, conserva intacta la cascada de reguladores lineales del instrumento y dimensiona los rieles de rack contra el liston de la A-100PSU3. La corriente de placa y la corriente sostenida son magnitudes distintas: el recinto y las curvas de derating deciden la segunda.

Esta carpeta reune las curvas leidas de las hojas, los presupuestos ejecutables, las comprobaciones y el bring-up propios de la v4; su argumento completo vive en el [papel del liston](../../../docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md) y su secuencia de trabajo en el [plan de presupuestos](../../../docs/superpowers/plans/2026-09-03-fuente-v4-presupuestos.md). La v3 queda como referencia historica y no se pide.

> ### ENMIENDA E16 — PRESUPUESTO TÉRMICO (#331, 2026-09-08)
>
> D1 retiró la cadena WS2812. `calor_budget.py`, ejecutado en este worktree,
> da **2,895 A / 14,475 W** de carga digital, **2,86 W** de pérdida en
> `PS6` y **29,23 W** en el recinto, incluida la franja de red.
> Las constantes se imprimieron importando el guion, sin modificarlo;
> el papel firmado conserva tachados los valores anteriores.
>
> **E16 queda parcial:** el guion aún no incluye la carga ultra de la Voz
> en el cajón y no reproduce la temperatura cerrada solicitada. Esas celdas
> y el total del cajón quedan pendientes, con evidencia en `REPORTE.md`
> en la raíz. Los rieles de rack se declaran según D-B2 **si se firma**.
