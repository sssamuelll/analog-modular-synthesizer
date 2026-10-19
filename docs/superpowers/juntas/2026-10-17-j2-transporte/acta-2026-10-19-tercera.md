# Acta — 2026-10-19 — el transporte del J2, tercera firma

Firmada por Samuel el **2026-10-19**, por escrito. La página de firma (un artifact con las cinco fichas del papel v3, la recomendación marcada en cada una y el costo de las otras) no guardó el documento `acta/j2-transporte-tercera`: su base está vacía. La firma es el mensaje de Samuel, que se copia entero:

> Signed with all five recommended options (B: 6/s, 1 ms apart, woken by tick; C: 25 ms to start, 14 ms to finish, with two checks; H: Yes, in TCM with checks; I: 256-entry table in DTCM; J: Counter plus measured entry at 14.1–14.5%).
>
> Three notes for the next steps:
> 1. On J: Measure the interrupt exit and the planner's chained entry next on the bench; keep the ~300-cycle optimisation pass parked unless that measured total crosses 15.0%.
> 2. On C: When amending the spec, explicitly record both dependencies outside J2's repo boundaries—the voice team's 50 ms (±2%) module silence ceiling and the hub census ruling out sustained (~94%) interrupt saturation that could chain incidents.
> 3. For the USB hub-load measurement (#443): Let me know as soon as the test harness is ready whenever you need the board's user USB port physically plugged into the PC.

Delante tenía el papel v3 (`papel-v3.md`, commit `7a369f3`, rama `docs/junta4-fichas-b-c`), los informes de la cuarta pasada (`junta4_halberg.md`, `junta4_serrano.md`, `junta4_voronov.md`), los de la quinta (`junta5_halberg.md`, `junta5_serrano.md`, `junta5_voronov.md`), el de la sexta (`junta6_halberg.md`), los experimentos de Halberg (`sim/junta4` a `sim/junta6`), el modelo de seis ranuras (PR #450, `555d65f`) y las medidas en placa de la huella en TCM (PR #449), del CRC (PR #451) y de la entrada de la excepción del tic (PR #453).

## Las cinco fichas

| Ficha | Pregunta | Respuesta firmada |
|---|---|---|
| B | ¿Quién autoriza la escalada del GPDMA1, que resetea las seis ranuras, y cada cuánto? (§2.5) | **La recuperación, con el presupuesto del controlador (K1): como mucho 6 escaladas en cualquier ventana de 1 s, y entre dos concedidas una espera de 1 ms, que despierta el tic.** La escalada pedida dentro de la espera se aplaza y la ranura sigue en `Reiniciando`. Con las dos condiciones de la sexta pasada: el tic lleva la cuenta de 64 bits, que el presupuesto lee, y compara el instante de despertar, que le llega en los 32 bits bajos, por diferencia con vuelta; y la recuperación lee el reloj, pide al presupuesto y publica el instante dentro de una sola sección crítica. |
| C | ¿Cuándo se rinde una ranura que no se recupera? (cotas, §2.5) | **`Vencida` 25 ms (200 periodos) y `Reiniciando` 14 ms (112), en periodos del reloj de K2, con R-H1 contado por nivel, de pendiente a terminado, y dos asertos en `lanzar`:** el de R-H1 (2 × 12 < 25,125 ms; 1 + 12 + 0,25 < 14,125 ms) y el del módulo (`hueco_de_recuperacion` más un periodo, 39,75 ms con el plazo más largo, contra 49 ms). El del módulo vale por incidente. |
| H | ¿Se enmienda R-H4 para que el enlace del J2 viva en TCM, como una obligación por símbolos con sus puertas? (§3, R-H4) | **Sí:** los tres manejadores del J2 y todo lo que alcanzan, también por los punteros del juez (con el CRC del sobre) y del reset de cada ranura, en la ITCM, y sus estáticos en la DTCM; el compositor no entra. Dos puertas (`tcm_cierre.py --raices` en el pre-push y la aseveración de `lanzar`) y, para los datos de solo lectura, la medida en frío. La huella del banco, ITCM 8 224 B y DTCM 5 128 B, como referencia. |
| I | En el cerebro, ¿el CRC del sobre de la subida se calcula con una tabla en la DTCM en vez de con la unidad CRC? (cabecera del J2, D2 y D9) | **Sí, con una tabla de 256 entradas en la DTCM, y solo en el cerebro.** El receptor del módulo decide con su propia medida. |
| J | ¿Qué cifra lleva la fila del J2 en el censo de CPU (R-H6)? (§3) | **El DWT más la entrada de la excepción medida y una estimación de lo que falta: del 14,1 al 14,5 % de un núcleo con seis ranuras (E)**, con TCM, las dos cachés frías y el CRC por tabla. |

## Lo que fija la firma para lo que sigue

1. **Ficha J.** Lo siguiente en el banco es medir la salida de la excepción y la entrada del planificador, que se encadena al tic. La pasada de optimización de ~300 ciclos sigue aparcada, salvo que el total medido pase del 15,0 %.
2. **Ficha C.** Al enmendar la spec, quedan escritas por su nombre las dos dependencias que están fuera del J2: el techo de silencio del módulo, que es de voz-total (50 ms, ± 2 %), y que el censo del hub excluya la saturación sostenida de interrupciones (~94 %) que encadena incidentes.
3. **La medida del USB del hub (#443).** Avisar en cuanto el arnés esté listo para conectar el puerto USB de usuario de la placa. *Hecho el mismo día: el arnés (`carga_j2 --features con-usb` y `trafico_midi.py`) está listo, y el puerto es CN8, con un cable que pase datos.*

## Lo que esta acta enmienda

- **R-H4** del papel v3 pasa a ser la de la ficha H (§1 del papel).
- **La cabecera del J2**, D2 y D9: el CRC del sobre se calcula en el cerebro con la tabla (enmienda del 2026-10-19 en D2).
- **La spec del maestro del J2**: un bloque con las dos actas del 19-10 en D5.1, con las dos dependencias de la nota 2, y sus filas en el mapa de enmiendas (§10).

## Lo que esta acta no decide

- Cuándo entra el transporte en el instrumento: siguen las doce condiciones de §5.2 del papel (ficha G del acta de la mañana).
- La pasada de optimización del tic, salvo por la condición de la nota 1.
- Qué hace el bus si el bloqueo se levanta con `SUSP` pedido durante la espera (Halberg N7): sigue abierto.
- La regla de R-H8(2), «armé y alguno de los últimos N terminó», que el modelo aún no tiene.
- Si las exposiciones bajo fallo de §2.10 del papel cuentan contra «cero artefactos audibles».
