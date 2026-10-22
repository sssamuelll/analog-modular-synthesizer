La fuente v4 sustituye el frente rectificador de la v3 por seis modulos Mean Well IRM, conserva intacta la cascada de reguladores lineales del instrumento y dimensiona los rieles de rack contra el liston de la A-100PSU3. La corriente de placa y la corriente sostenida son magnitudes distintas: el recinto y las curvas de derating deciden la segunda.

Esta carpeta reune las curvas leidas de las hojas, los presupuestos ejecutables, las comprobaciones y el bring-up propios de la v4; su argumento completo vive en el [papel del liston](../../../docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md) y su secuencia de trabajo en el [plan de presupuestos](../../../docs/superpowers/plans/2026-09-03-fuente-v4-presupuestos.md). La v3 queda como referencia historica y no se pide.

> ### ENMIENDA E16 — PRESUPUESTO TÉRMICO (#331, completada el 2026-10-22)
>
> D1 retiró la cadena WS2812. `calor_budget.py` incluye la carga digital sin
> cadena (**2,895 A / 14,475 W**), la pérdida en `PS6` (**2,86 W**), la franja de
> red (**3,70 W**) para **29,23 W** en el recinto (`P_RECINTO_MAX`), y la carga
> ultra de la Voz (**8,00 W**, `CAJON_ULTRA_W = 8,0016 W`) para **118,08 W** en
> el cajón (`P_CAJON_MAX`) y **147,31 W** totales (`87,7 °C` en caja cerrada,
> `146,8 °C` a placa sin derating, `21 000 mm²` de venteo nuevo en `P_BASE`).
>
> Desde el 2026-09-08 (**D-V1..D-V5** firmadas), la fuente que se construye es la
> **v5** (`../v5/`, [spec del ladrillo](../../../docs/superpowers/specs/2026-09-05-fuente-v5-ladrillo-design.md)),
> que saca la etapa AC-DC a un ladrillo externo de 24 V y adopta el techo de rack
> de **D-B2** (`0,5 / 0,5 / 0,5 A`). Esta carpeta `v4/` se conserva porque sus
> curvas, su modelo de margen/rizado/secuencia y sus puertas siguen siendo la
> referencia base de la cascada.
