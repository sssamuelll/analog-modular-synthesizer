# Fuente v4 — el listón de la PSU3, seis módulos encapsulados y la cascada intacta — firmada (v3, tras la junta y la firma)

**Fecha**: 2026-09-03 · **Estado**: **firmado — D-F1 a D-F9 decididas (§14, el bloque de D-F8 de 2026-09-04 y el de D-F9 de 2026-09-06); `calor_budget.py` corrió y la columna «sostenido» de §1 está rellena; `margen_budget.py` salió de HUECO al firmarse D-F9. Lo que queda abierto en este papel es el máximo absoluto de entrada de `U1` (#334); lo que queda de otros papeles, el venteo mínimo (#289) y la bahía (#290)** ·
**Listón firmado**: 2026-09-03 («firmo el listón», Samuel) — como **corriente de placa**; y **re-firmado el mismo día como corriente sostenida** por `calor_budget.py` con D-F3 = A y D-F7: **2,0 / 2,0 / 4,0 A de rack y 4,2 A digital con 22 200 mm² de venteo nuevo**, el mínimo que el modelo despeja (16 900 → 20 600 el 03-09; → 22 200 el 04-09, al contar la franja de red: §6 y el bloque de enmiendas de la tanda A) ·
**Cierra**: nada todavía. **Entrega**: los rieles de #169 (§4.3) ·
**Mata por desaparición del sujeto**: #141, #280, #106, #56, #57. **Ejecutado el 2026-09-04**, antes de la adopción: Samuel decidió cerrarlos ya tomando este papel firmado como certificado, en vez de esperar a que la v4 se fabrique. Los cuatro abiertos (#141, #106, #56, #57) se cerraron *not planned* con previsto/encontrado y cita a esta línea; #280 ya estaba cerrado como completado. **Esta es la única lista de defunción del árbol**: nada más muere por parecerse a la v3 ·
**Reabre**: `design-notes` §13 y §18, la spec del chasis (§3.1, §3.2, §3.3), `clearance_budget.py::guarda_aire()`, `consumo_total_budget.py`, `power_budget.py`, `ground_budget.py`, el papel de la bahía

> ### ENMIENDAS DE LA TANDA A DE PRESUPUESTOS (2026-09-04)
>
> Los guiones de `hardware/01-power-supply/v4/` corrieron por primera vez y
> **movieron ocho cosas de este papel**. Nada de esto invalida las decisiones
> firmadas D-F1 a D-F7; lo que hace es ponerles cifra, y en dos sitios abrir
> una decisión nueva. Cada punto dice qué guion lo sostiene y dónde cae.
>
> | # | Dónde | Qué decía | Qué dice el guion |
> |---|---|---|---|
> | 1 | §4.2 | el margen de entrada de `U1` es **+0,30 V** | **NO HAY MARGEN: −388 mV en `U1` y −170 en `U2`** con lo que la hoja GARANTIZA, y **+2,8 mV** en el mejor caso imaginable (ajustar placa a placa Y suponer que la unidad conserva su sitio en la ventana de Vref al calentarse, cosa que la hoja no promete). Y la incertidumbre del propio modelo son 127 mV: un margen más pequeño que su barra de error no es un margen. El +0,30 es el margen de una placa cuyo setpoint cae exactamente en 13,1 V, y la ventana del setpoint sale de la **referencia del propio pre-regulador**: LM2941 ±3,0 % de dispersión y ±2,0 % más de deriva (p. 5). Aun ajustando placa a placa —el mejor caso— quedan ±267 mV en `U1` y ±384 en `U2`. `margen_budget.py`, HUECO, con cuatro salidas y su precio |
> | 2 | §4.2 (D-F4) | el detector de ventana habilita entre 14,1 V y lo que el IRM da | **el umbral no cabe**: entre lo que `U1` necesita (14,758 V) y lo que un IRM de tolerancia mala da (14,370) hay **−388 mV**, contra ±132 de tolerancia del comparador y 31 de histéresis mínima. que es el punto 1 visto desde el secuenciador. Y cuando se cierre, el detector tiene que **sensar DESPUÉS del LC**: en el borne del módulo la histéresis mínima son 230 mV y ninguna ventana de este riel los aguanta. `secuencia_budget.py`, HUECO |
> | 3 | §5 | la corriente de red son **3,9 A rms** y el inrush 285 A | **4,4 A y 320 A.** La fila AC CURRENT de la IRM-45 es una celda única para toda la serie (0,9 A/230 Vac también para la de 5 V), y D-F7 subió `PS5` de IRM-20-5 a IRM-45-5: §5 seguía sumando el 0,4 de la pieza retirada. A la carga del listón son 3,25 A. `fusible_budget.py` |
> | 4 | §5, §11 | **4 A T** como hipótesis de fusible | **6,3 A T**, y no llega por ninguno de los dos caminos: ni el permanente (piden 5,34 A al 70 % del calibre y con el derratado del recinto) ni el rearranque en caliente (17,4 A²s contra 15,3 admisibles de un 4 A T). **Y la pieza la decide otra cosa: el PODER DE CORTE.** Un 5×20 de vidrio corta 63 A y en el enchufe hay ~490 A disponibles; hace falta cerámico de alto poder de corte. `fusible_budget.py`, HUECO por esa hoja |
> | 5 | §4.1 | la fuga a PE es «el no-problema», un orden de magnitud bajo el límite | **el 87 % del límite de trabajo** (3,05 de 3,5 mA), con las condiciones de medida de la norma: 1,1 × la nominal y 60 Hz. El **Y2 máximo por módulo son 2,99 nF**. `fuga_budget.py`, HUECO por la cifra de IEC 62368-1, que es de pago |
> | 6 | §4.2 (D-F5) | el Y2 local cierra el lazo de modo común **a 65 kHz** | **es un mecanismo de MEGAHERCIOS, y con letra pequeña.** Los dos caminos van en paralelo y la corriente se reparte: a 65 kHz los 300 mm de hilo pesan 0,12 Ω contra 1113 del Y2 y sólo desvía 1,5 veces; a 20 MHz desvía 14,2. **Y en 7,48 MHz hay una ANTIRRESONANCIA donde el Y2 local MULTIPLICA POR 62 la corriente que se vuelve por la estrella**: la rama larga ya es inductiva, la local sigue capacitiva, y donde las dos reactancias se cancelan la corriente circula entre ellas. No se arregla amortiguando el Y2 (harían falta 9 Ω y eso mata su trabajo a 20 MHz): se arregla **acortando el hilo de la estrella**, y se mide. La decisión sigue siendo buena; el motivo escrito no es el que la sostiene |
> | 7 | §4.2, §12.4 | la nota EMI de Mean Well documenta el mecanismo de D-F5 | **la nota no habla de condensadores Y.** Habla de montar el módulo sobre «a defined metal plate» y de que el cable de salida vaya «twisted and flatly placed on and within the range of the metal plate», y de que la EMC sólo se comprueba con el equipo entero. Son **dos requisitos de montaje** de los que depende la Clase B de la hoja, y no estaban escritos en ningún sitio. Ya está en el árbol: `meanwell-emi-statement-2023-12-20.pdf`. §12.4 hecho |
> | 8 | §6 | la tabla de calor del recinto suma 27,5 W | **le falta la franja de red, y no es un detalle: son 31,25 W.** La NTC de arranque disipa 2,75 W dentro y el choke 0,95 (ESTIMADO); el MOV no, porque en marcha normal conduce microamperios. Con esos 3,70 W **el venteo mínimo sube de 20 525 a 22 148 mm²** — sin ellos el listón del rack se cumplía por 3,5 mA. Ya están dentro de `calor_budget.py`, y `fusible_budget.py` asevera la cifra de la NTC contra la suya |
>
> **Dos cosas más que los guiones añadieron y el papel no tenía:**
>
> - **El rizado necesita amortiguar DOS veces, no una** (§4.2 pedía sólo el LC).
>   El 22 µH / 47 µF sin amortiguar pica +21 dB en 4,9 kHz, dentro de la banda
>   de 10 Hz–100 kHz en la que se mide el riel; con `Rd` = 0,68 Ω + `Cd` =
>   220 µF queda en +2,6. **Y la receta «perla + cerámico» trae su propio LC**:
>   955 nH con 100 nF resuenan en 516 kHz con Q ~ 300 y **amplifican +34 dB**.
>   Se amortigua con 2,2 Ω + 2,2 µF y queda en +0,6. `rizado_budget.py`. Ese
>   segundo hallazgo salió de barrer fino: con 241 puntos se veían 24 dB donde
>   hay 34.
> - **El crowbar que aprieta es el del +5 V de rack, no el de ±12** (§4.3 los
>   trataba igual). El OVP de la IRM-45-5 llega a 6,75 V y un electrolítico de
>   6,3 —el estándar de ese riel— está por debajo: la banda admisible para el
>   disparo son **0,27 V**, contra 2,67 en ±12. Y el **+5 V digital no lleva
>   crowbar**: que lo que reciba `PS6` aguante 6,75 V pasa a ser requisito al
>   módulo 2. `check_absmax.py`, HUECO por la hoja del SCR.
>
> ### D-F8 — `U1` PASA A LT1963A. FIRMADA POR SAMUEL EL 2026-09-04
>
> Sobre la tabla del bloque siguiente, y con ella delante. **`U1` deja de ser
> un LM2941 y pasa a ser un LT1963A Rev G.** El riel ultra recupera margen de
> entrada: **de −388 mV a +330**, que son 2,6× la incertidumbre del propio
> modelo.
>
> Ya está en el árbol: `margen_budget.py` lleva la referencia
> (1,174–1,246 V sobre temperatura, p. 5) y el dropout (0,55 V garantizado a
> 1,5 A, p. 5) leídos de tabla.
>
> **Y trajo un coste que no estaba en su precio, que es lo que hay que leer
> antes de dar esto por cerrado:**
>
> **La polaridad de habilitación es la contraria.** El `SHDN` del LT1963A
> **habilita en ALTO** (p. 5: *Off to On* con ≤ 2 V, *On to Off* con ≥ 0,25 V);
> el ON/OFF del LM2991 habilita en BAJO. Hasta hoy los dos habilitaban en bajo
> y **un solo hilo gobernaba los dos** — y eso no era una comodidad de
> cableado:
>
> > **era la razón por la que ningún fallo simple dejaba un riel solo**, que es
> > exactamente lo que D-F4 existe para impedir. Un hilo roto los apagaba a los
> > dos, por construcción.
>
> Ahora hay que **invertir una de las dos señales**, y el inversor es un punto
> de fallo nuevo **cuyo modo de fallo es el prohibido**. Requisito que este
> papel le pasa a la tanda B, escrito antes de elegir la pieza y no después:
> **el inversor tiene que fallar hacia AMBOS APAGADOS.** Y se mide: el
> bring-up gana dos puntos nuevos en el paso 2b (`check_bringup.py`),
> *cortar la señal del secuenciador apaga LOS DOS* y *quitar alimentación al
> inversor apaga LOS DOS*.
>
> **Lo demás que arrastra, y es menos:**
>
> - **La ventana de ESR del `COUT` cambia de dueño.** El LM2941 exigía ESR de
>   **al menos** 100 mΩ (p. 12) — la trampa clásica: un cerámico X7R moderno lo
>   hacía oscilar. El LT1963A no tiene cota inferior y sube el techo a **3 Ω**
>   (Rev G p. 14). El aserto se reescribió con cuidado de no dejar una
>   comparación que no puede fallar: `lo == 0.0` se comprueba **aparte**, para
>   que si algún día vuelve una pieza con ESR mínima, la puerta lo diga en vez
>   de ignorarlo.
> - **No mueve el chasis.** El LT1963A es 5-lead TO-220 con tab, así que
>   `chasis_to220_*` y `revisar_to220_coplanares()` siguen igual.
> - **`U2` no cambia** y sigue en −170 mV. Ver el bloque siguiente: lo que
>   necesita es una pieza 300 mV mejor que el LM2991 en la suma de ventana y
>   dropout, y **`margen_budget.py` sigue saliendo en HUECO por ella** — un
>   hueco que ya no se cierra decidiendo, se cierra con una hoja de datos.
>
> ### LA OPCIÓN (b) YA TIENE CIFRAS, Y SÓLO ARREGLA MEDIA CADENA (2026-09-04)
>
> El punto 1 de arriba dejaba la (b) como un adjetivo — *«otro pre-regulador
> con referencia mejor y menos dropout»*. Ya tiene candidatos con hoja
> declarada (`docs/references.md`, PR #317) y **leída de tabla**, y con eso la
> decisión deja de ser de gusto.
>
> El requisito, dicho al revés: con `V_SET` = 13,100 V y los 14,370 V que le
> llegan a `U1` en el peor caso, **ventana de referencia + dropout garantizado
> no pueden pasar de 1,270 V**.
>
> | pieza | ventana | dropout gar. | pide | margen en `U1` |
> |---|---|---|---|---|
> | **LM2941** (hoy) | 0,658 V | 1,00 V a 1 A | 14,758 V | **−388 mV** |
> | **LT1963A** Rev G | 0,390 V | 0,55 V a 1,5 A | 14,040 V | **+330 mV** |
> | **MIC29152** DS20005685A | 0,391 V | 0,60 V a 1,5 A | 14,091 V | **+279 mV** |
>
> Calculado con `margen_budget.py` — **el mismo apilamiento que ya está en
> verde**, cambiando sólo las dos entradas que la (b) cambia. Y los dos
> márgenes pasan la prueba que este papel puso en el punto 1: son **2,6× y 2,2×
> la incertidumbre del propio modelo** (127 mV), no más pequeños que ella.
>
> **Tres cosas que la tabla no dice y deciden igual:**
>
> - **`U2` se queda sin arreglo.** La (b) cierra `U1` con holgura, pero el
>   riel negativo sigue en **−170 mV** y ninguno de los dos candidatos es una
>   pieza negativa. Firmar «vamos con (b)» **cierra media cadena**: la otra
>   mitad necesita su propia respuesta, y son 170 mV, no 388.
>   *(Cerrada dos días después: D-F9, LT3015, +536 mV. La especificación que
>   este párrafo dejó escrita —bajar de 1,343 V en la suma— fue exactamente lo
>   que la búsqueda usó de filtro.)*
>
>   **Lo que hay que comprar para `U2`, dicho como especificación y no como
>   queja:** su presupuesto de ventana + dropout son **1,470 V** y el LM2991
>   gasta 1,640. Para que el margen valga más que la incertidumbre del modelo
>   hay que **bajar de 1,343 V**. O sea que no hace falta un LDO negativo
>   excepcional: hace falta uno **300 mV mejor que el LM2991** en la suma de
>   las dos cifras. Y el reparto importa — todo el desajuste de hoy sale del
>   dropout **sobre temperatura** (0,8 V a 25 °C, 1,0 V garantizado), no de la
>   referencia.
> - **Ninguna de las tres garantiza el dropout a los 710 mA de la cascada.**
>   El LT1963A salta de 500 mA (0,35 V) a 1,5 A (0,55); el MIC29152 publica el
>   típico a 750 mA y el máximo sólo a 1,5 A. La tabla toma **la cota de la
>   corriente mayor**, que es la única honesta y la que deja la comparación
>   pesimista para los dos candidatos por igual.
> - **La DS20005685A no es la última** (existe una **B**, 2016–2019, sin ver) y
>   **se contradice consigo misma sobre el encapsulado**. Mientras el disipador
>   sea la pared del chasis, sin TO-220 con TAB la pieza no sirve, y eso se
>   cierra con el sufijo de pedido. El LT1963A **sí** es 5-lead TO-220 con tab
>   confirmado, así que **no hace falta mover `chasis_to220_*` para resolver la
>   (b)** — y eso retira una de las razones que la propuesta del recinto
>   partido (PR #316) se apuntaba.
>
> **El aserto de la ventana de ESR del `COUT` muere con el LM2941.** Es de su
> hoja (p. 12, 0,1–1,0 Ω) y no es transferible: la pieza que entre trae la suya,
> y hay que volver a escribirlo. Hoy `margen_budget.py` lo asevera y **daría
> verde sobre un sujeto muerto** el día que se cambie el chip.

> ### D-F9: `U2` PASA A LT3015, Y CON ELLO CIERRAN TRES COSAS (2026-09-06)
>
> El bloque de arriba dejaba `U2` en **−170 mV** con un requisito escrito como
> especificación y no como queja: *ventana de referencia + dropout garantizado
> por debajo de 1,343 V*. **La pieza existe y estaba a dos hojas de distancia.**
>
> **`U2` = LT3015 (`LT3015IT#PBF`), LDO negativo ajustable de 1,5 A en TO-220
> de 5 patas.** Firmado por Samuel el 2026-09-06 con esta tabla delante:
>
> | pieza | ventana | dropout gar. | suma (tope 1,343) | margen en `U2` |
> |---|---|---|---|---|
> | **LM2991** (hasta hoy) | 0,640 V | 1,00 V a 1 A | 1,640 | **−170 mV** |
> | TPS7A3301 | 0,322 V | 0,80 V a 1 A | 1,122 | +347 mV |
> | **LT3015** | **0,254 V** | **0,68 V a 1,5 A** | **0,934** | **+536 mV** |
>
> Calculado con `margen_budget.py`, el mismo apilamiento de siempre, cambiando
> sólo lo que la pieza cambia. **El guion pasa de HUECO a verde** y su peor
> riel vuelve a ser `U1` (+330 mV). El margen es **4,2×** la incertidumbre del
> propio modelo (127 mV).
>
> **Por qué el LT3015 y no el TPS7A3301, que también pasaba:** el TI dibuja un
> TO-220 en su hoja pero **su *Package Option Addendum* (p. 27) sólo lista
> VQFN-20**. No hay part number en TO-220 que pedir, así que `U2` habría dejado
> de ser un tab contra la pared del chasis — y eso mueve `chasis_to220_*` en
> `clearance_budget.py`, `check_dxf.py` y el pliego. El LT3015 no mueve nada.
>
> **Las cuatro cifras, todas de tabla y ninguna de curva** (`lt3015-rev-b.pdf`):
> `ADJ Pin Voltage` −1,196/−1,244 V en la fila marcada con `l` —que en Linear
> es todo el rango de temperatura, y cuyas condiciones incluyen −30 V < VIN <
> −2,3 V y −1,5 A < ILOAD < −1 mA, o sea que **línea y carga ya están dentro**
> de esos 48 mV—; `Dropout Voltage` 0,68 V máx a −1,5 A **en la fila del
> DD-PAK/TO-220**, que es peor que la del DFN (0,50) y es la nuestra;
> `IN Pin Voltage` ±33 V; y `Shutdown Threshold` *Off-to-On (Positive)* 1,35 V
> máx. **Pedir el grado `I`**: la Nota 9 sólo garantiza el rango entero al `I`
> y al `MP`, no al `E`.
>
> **Lo que cierra, y es más que su propio issue:**
>
> - **El inversor del ON/OFF se queda sin motivo (#323).** El `SHDN` del LT3015
>   **habilita en ALTO**, igual que el del LT1963A. Vuelve el hilo único, y con
>   un pulldown al común **cortar el hilo apaga los DOS por construcción** —que
>   era exactamente la propiedad que D-F4 necesita y que D-F8 había roto sin
>   querer. No hay inversor que pueda quedarse sin alimentación. El punto del
>   bring-up que medía eso (*quitar alimentación al inversor apaga LOS DOS*)
>   **se retira por falta de sujeto**; el otro (*cortar la señal apaga LOS DOS*)
>   se queda, porque «por construcción» es un argumento y no una medida.
> - **El umbral del detector de ventana vuelve a tener dónde vivir (#324).**
>   Era el mismo −170 mV visto desde el secuenciador: entre lo que el peor riel
>   necesitaba y lo que un IRM de tolerancia mala entrega no había hueco.
>   Ahora `secuencia_budget.py` publica **+330 mV de ventana** y, después de
>   pagar histéresis y error de umbral, **+40 mV útiles**. Es estrecho y hay
>   que dibujar el circuito con eso delante, pero existe.
> - **`U2` deja de necesitar ajuste placa a placa.** Su ventana de referencia
>   (0,254 V) es **más estrecha** que los ±0,3 V con los que el bring-up de la
>   v3 acepta TP8: el −12,9 V cabe con divisor fijo. Eso rompió un aserto de
>   `margen_budget.py` que daba por sentado lo contrario, y romperlo era lo
>   correcto — exigía que la pieza nueva fuera tan mala como la vieja.
>
> **Lo que arrastra, y hay que respetar:**
>
> - **La `CFF` de 10 nF de `ADJ` a `OUT` NO es opcional.** La G41 de la p. 11
>   dibuja tres trazas y a 65 kHz —la conmutación del IRM, o sea la frecuencia
>   que decide `rizado_budget.py`— valen ~41 dB (47 µF + CFF), ~38 (10 µF +
>   CFF) y ~15 (10 µF **sin** CFF). **Sin ese condensador el LT3015 rechaza
>   menos que el LM2991 al que sustituye** (24,5 dB) y el cambio de pieza
>   saldría al revés. Las dos piezas se declaran en `rizado_budget.py` y un
>   aserto comprueba que la cita de la curva sigue siendo la de esos valores.
> - **La lectura de 41 dB a 65 kHz es la más floja de la tabla de curvas.**
>   Cae en una pendiente fuerte, entre un pico de ~46,5 dB a 41 kHz y un mínimo
>   de ~39 a 110 kHz: ahí 10 kHz de error de lectura mueven 3 dB. Declarada
>   como duda en `curvas.py`.
>
> **Lo que NO cierra, y sale de aquí:** el máximo absoluto de entrada de `U1`.
> El LT1963A aguanta **±20 V** (Rev G p. 2) y el OVP de `PS1` clampa a **20,25 V
> sostenidos** (IRM-20 p. 2). Faltan 250 mV, y tres sitios seguían en verde
> porque nombraban al LM2941. Es la **#334**, y **no se decide en esta tanda**:
> cambiar el número pone `check_absmax.py` en rojo, y qué hacer con eso —otra
> pieza, atajar el OVP, o aceptarlo por escrito— es una decisión, no una
> corrección. El **MIC29152** (rev B ya en el árbol) admite **+26 V** de
> entrada operacional y es la salida más obvia.
>
> **HABÍA OTRO CAMINO EN EL ÁRBOL, Y NO SE PUSO SOBRE LA MESA (2026-09-07).**
> El papel de la **fuente v5** (`2026-09-05-…-ladrillo-design.md`, §5), mergeado
> el 05-09 y presente en el árbol de esta misma rama, proponía cerrar `U2`
> **sin cambiar la pieza**: con un DC-DC propio la tensión cruda se elige, y a
> 15,5 V el LM2991 llega a +311 mV. Su §7.1 daba el **#322** por muerto «por
> desaparición del sujeto». Cuando se buscó la pieza no se leyó ese papel, así
> que D-F9 se firmó sin esa alternativa delante. **La firma se sostiene igual, y
> por tres razones que no dependen de cuál se prefiera:**
>
> 1. **La v5 no está firmada** («ninguno de los tres se toca aquí: este papel no
>    está firmado»). Mientras no lo esté, el crudo es el de un IRM de catálogo y
>    D-F9 es la única salida vigente.
> 2. **La v5 no reabre la cascada** (§7), así que con el LM2991 el `ON/OFF`
>    seguiría habilitando al revés que el LT1963A y el **#323 seguiría abierto**.
>    Ninguna tensión cruda compra eso.
> 3. **Las dos se suman en la dirección buena.** Con el LT3015 dentro, D-V3 deja
>    de comprar un cierre y pasa a comprar holgura en `U1` (+330 → +811 mV), y
>    sus **+0,33 W** se vuelven negociables en un papel que va de bajar calor.
>
> Lo que sí hizo D-F9 fue moverle las cifras al papel de la v5 sin avisar:
> `ladrillo_budget.py` importa `margen_budget.py` entero, así que su tabla de §5
> **cambió sola**. Enmendada allí con esta misma fecha.

> **Lo que la tanda A dejó cerrado y verde:** el sostenido (§1, §6), el censo
> de invitados en cuatro columnas (`invitados_budget.py`), el desfase
> rack↔instrumento con N patches (`ground_budget.py`), los 75 puntos del
> bring-up con sus predicciones importadas (`check_bringup.py`) y el hueco de
> `consumo_total_budget.py`, que se cerró solo al aterrizar su relevo.

> **Lo que la junta cambió (Serrano, Halberg, Voronov, 03-09).** La v1 de este
> papel tenía tres errores que movían decisiones, y los tres estaban en hojas
> que ya estaban en el árbol: (1) las corrientes del listón son de placa, y las
> curvas de derating de la p. 3 de cada hoja las dejan a la mitad o menos dentro
> de un recinto cerrado a 45 °C de ambiente de diseño; (2) la corriente de red
> es la fila «AC CURRENT» de la hoja —**3,9 A rms** típicos con los seis a
> nominal—, no los 0,94 A que salían de dividir vatios entre voltios; (3) la
> masa es un solo nodo, y una regla sobre una rama no gobierna por dónde vuelve
> la corriente de un invitado. Además: la frecuencia de conmutación **sí está
> publicada** (65 kHz), el «LC de la v3» era un choke de red y no un filtro DC,
> el inrush de la IRM-30 son 45 A y no 4, y el rendimiento de la IRM-45 se lee
> sin ambigüedad. Todo eso está corregido abajo; lo que la junta no pudo cerrar
> es decisión de Samuel (§14).

> **Lo que Samuel firmó (03-09).** Las seis, en el orden en que se toman:
>
> | | Qué | Dónde vive |
> |---|---|---|
> | **D-F1** | el listón, **como corriente de placa**: 3,8 / 2,5 / 4,0 A de rack, 8,0 A digital, 650 mA de ultra | §1 |
> | **D-F3** | **A: ventilar** el recinto y el cajón por convección natural, **sin ventilador** | §6 |
> | **D-F2** | telemetría de rack **poblada**: `U13` y `U14` montados en R, no `DNP` | §7 |
> | **D-F4** | **secuenciador** por los pines ON/OFF, en la cascada y en el rack | §4.2, §4.3 |
> | **D-F5** | **Y2 de modo común** por módulo, del borne de ★ al chasis | §5 |
> | **D-F6** | **crowbar** en los rieles de rack, y solo ahí | §4.3 |
> | **D-F7** | `PS5` pasa de IRM-20-5 a **IRM-45-5**; el listón del +5 V de rack sigue en 4,0 A declarados | §3, §6 |
>
> Y una séptima que no es ninguna de esas seis: **cuando `calor_budget.py`
> corra con el recinto ventilado, el listón se vuelve a firmar en corriente
> sostenida**, que es la que el instrumento promete a quien le enchufa un
> módulo. La columna «sostenido» de §1 sigue vacía a propósito hasta entonces:
> se firma un número calculado y medido, no una intención.
>
> D-F4, D-F5 y D-F6 se firman **como consecuencia, no como mejora**. Los tres
> son modos de falla que la v3 no tenía porque tenía un solo transformador, y
> los tres se pagan en céntimos. Lo caro es no ponerlos: un riel crudo solo en
> cada encendido y cada microcorte (D-F4), el modo común de seis conmutadores
> volviendo por los hilos de la cascada (D-F5), y 16,2 V sobre una fila de
> módulos ajenos (D-F6).

---

## 0. Por qué existe este papel

La v3 está dibujada, ruteada y con DRC en cero, y **no se pide**. No porque le
falte una puerta: porque el listón cambió.

El 2026-09-03 salieron tres cosas a la vez, y las tres tienen número:

1. **El instrumento es digital y su +5 V ya está en rojo.** `power_budget.py`
   (módulo 2) importa un techo **derrateado** de **14,1 W a 52,3 °C** —2,82 A de
   la IRM-15-5, y 2,50 A de tope de arbitraje— y con cuatro N657 a máximo más
   el host USB las cargas duras solas son **2,895 A**. Con la cadena de LEDs al
   tope del #104 son **4,935 A**. Y eso sin la NPU, que no tiene cifra en
   DS14791.
2. **La fila de abajo es rack de verdad (#169) y no tiene corriente.**
   `consumo_total_budget.py` deja **160 mA por riel** para invitados. Un solo
   Disting EX come 229 mA en +12 V (expert-sleepers.co.uk, leído 2026-09-03).
3. **Samuel fijó el listón: «a la altura de la A-100PSU3 o superior».** La PSU3
   da +12 V/2000 mA, −12 V/1200 mA, +5 V/4000 mA (doepfer.de/a100_man/a100t_e.htm,
   leído 2026-09-03). La v3 da 650/650 en ±12 V —**exactamente lo que daba la
   primera fuente de Doepfer, la A-100NT12, retirada en el año 2000**— y ningún
   +5 V de rack.

La topología lineal de red de la v3 —toroide de 120 VA, puente, 9400 µF— no
puede crecer hasta ahí sin volverse un ladrillo de dos kilos, y el propio §18 de
la v1 midió que **el mayor emisor de zumbido de la caja es el mazo del
secundario del toroide** (~40 cm², ~29 µV inducidos). Este papel cambia la
entrada de red por módulos AC-DC encapsulados y **deja la cascada de regulación
como está**, porque es de la cascada de donde sale el 0,8 µVrms, no del toroide.

> **Sobre la regla «nunca con una v4» de la v3.** Se escribió para que lo
> indeciso saliera con huella y `DNP` en vez de con otra versión de papel. Este
> papel **no la reexpide**: sus huecos (§6, §12) no son huellas —son chapa,
> fusible, una placa entera— y una regla que no puede aplicarse a sí misma no
> gobierna. Lo que este papel se impone en su lugar es más duro y verificable:
> **nada de la v4 se manda a fabricar con un ítem de §12 abierto**, y eso lo
> hacen cumplir las puertas de §9, no una frase.

---

## 1. El listón (D-F1, FIRMADO 2026-09-03 como corriente de placa)

| Riel | A-100PSU3 | SAM17 v4, **de placa** (firmado) | **Sostenido** en el recinto | Masa |
|---|---|---|---|---|
| **±12 V ultra** — Voz, VCF, VCA, envolventes, bahía | no tiene | **650 mA/riel, 0,8 µVrms**, cascada intacta | 650 mA: los IRM de 15 V van al 24 % de carga | `GNDA` |
| **+12 V invitados** — fila de abajo, 104 HP | 2,0 A | **3,8 A** | **2,0 A** con el venteo mínimo (22 200 mm² nuevos, §6); es el riel que fija ese mínimo | rack |
| **−12 V invitados** | 1,2 A | **2,5 A** (3,8 de placa del módulo) | **2,0 A** | rack |
| **+5 V invitados** | 4,0 A | **4,0 A** declarados (8,0 de placa del módulo, D-F7) | **4,0 A**: la IRM-45-5 da 4,2 a esa temperatura y se declara 4,0 | rack |
| **+5 V digital** — N657 ×4, pantalla, LEDs, host USB | (dentro de los 4 A) | **8,0 A** | **4,2 A** = 21 W: **el techo nuevo que `power_budget.py` importa** (era 14,1 W) | `GNDD` |
| **1,8 V** de los N657 | — | del 3,3 V, aguas abajo del +5 V digital; **no se decide aquí** (§4.5) | | `GNDD` |

La columna «de placa» es lo que se compra. La columna «sostenido» es lo que el
instrumento **promete**, y la rellenó `calor_budget.py` el 03-09 con D-F3 = A
y D-F7: es la corriente en el **punto fijo** —la que el rack puede dar
calienta el cajón, y el calor recorta la que puede dar— con el **venteo
mínimo** que el modelo despeja, **22 200 mm² nuevos**; a esa abertura el aire
del recinto son 68,9 °C. Con más abertura, más corriente; con la caja de hoy,
cerrada, **cero**: a 86,7 °C se acabó la curva de la hoja y no opera ningún
módulo del rack. El modelo es pesimista a sabiendas (§6): hereda de
`guarda_aire()` que el cajón solo evacúa por chimenea. Lo que sí es cierto con cualquier venteo:

**El instrumento y los invitados no se prestan un miliamperio de suministro.**
El riel ultra sigue en 650 mA con su 30 % de margen (`consumo_total_budget.py`:
peor riel 340,2 mA → OK), y no reserva nada para la fila de abajo. Un módulo
ajeno con su conmutado no toca el riel de 0,8 µV, y la NPU del mago no deja sin
corriente a un delay de BBD. Lo que **sí** comparten es la masa: §4.1.

**Lo digital del instrumento no carga los ±12 V.** Carga el +5 V digital, y de
ahí baja a 3,3 y a 1,8. Por eso el riel que más crece contra la PSU3 es ese:
**8 A de placa contra 4**, y aun así la cadena de LEDs a blanco pleno (**9,60 A**,
`power_budget.py`) no cabe. El tope por firmware se queda.

---

## 2. Qué se va y qué se queda respecto de la v3

| | v3 | v4 | por qué |
|---|---|---|---|
| **Entrada de red** | toroide Talema 120 VA + `BR1` + 9400 µF | **seis módulos Mean Well IRM** (§3) | el listón; y el toroide era el emisor mayor (§0) |
| **Cascada ±12 V** | LM2941/LM2991 → LT3045 ×2 / LT3094 ×2 | **la misma**, más un secuenciador por sus pines ON/OFF (§4.2) | el 0,8 µVrms sale de ahí; el secuenciador es porque ahora los dos rieles crudos son dos fuentes |
| **Lo que ve la cascada** | VRAW ±20,54 V en vacío, ±15,70 V a 650 mA, rizado de 100 Hz | **±15 V DC ±2,5 % ±0,03 %/°C, rizado de 65 kHz ≤ 200 mVp-p** | §4.2 |
| **El valle de VRAW** | el número del que dependía todo | **no existe** | no hay rectificador |
| **`TR1` con fusible térmico** | condición de compra (#118) | **no hay `TR1`** | los 642 W de un corto del secundario ya no tienen dónde ocurrir |
| **Crowbar** | ninguno (#118) | ninguno en el ultra; **en los rieles de rack** (§4.3, D-F6 firmado) | #118 lo rechazó porque el fusible de red no abría; ahí el interruptor es el *hiccup* del IRM |
| **Fusible de red** | 1,6 A T en el IEC (#130) | en el IEC; **sube** (§5) | 3,9 A rms típicos a nominal, no 0,72 |
| **`NT1`, `L_F`** | 2 A; 0,2 A | **se redimensionan** (§5) | ídem |
| **Disipación** | tres TO-220 contra la pared | los mismos tres contra la pared, con la mitad de calor | entran a 15 V, no a 20 |
| **Chasis** | acero, cerrado, sin ventilación, para un toroide Ø93 × 46 | acero, sin toroide, **ventilado por convección natural, sin ventilador** (D-F3 = A) | §6 |
| **Telemetría** | 5 chips, mide el valle | 5 chips (+2 opcionales, §7), mide los ±15 V y el −12 V de rack | |
| **+5 V digital** | IRM-15-5 «montada fuera de esta placa» (spec v2 §7), 3 A | **IRM-45-5 en la placa de red, 8 A de placa** | #151 sigue abierto: §4.4 dice por qué |
| **Fila de abajo** | 160 mA/riel prestados | **rieles propios** por un bus board de invitados | #169 |
| **Placas** | una, 200 × 150 | **dos** + el bus board de invitados | §8 |

---

## 3. Los seis módulos, contra la hoja

Las cuatro hojas están en el árbol desde esta tanda:
`docs/reference/datasheets/meanwell-irm-{15,20,30,45}-spec-*.pdf` (15, 20 y 45 W
fechadas 2025-11-21; 30 W, 2026-04-03). Todo lo de abajo es de la tabla de
especificación (p. 2) y del diagrama de bloques y la curva de derating (p. 3),
salvo donde se marca.

| Ref. | Módulo | Riel | I placa | Rizado máx. (20 MHz) | Rend. | Inrush frío 230 V | I red típ. a nominal | L × W × H | Peso |
|---|---|---|---|---|---|---|---|---|---|
| `PS1` | IRM-20-15 | +15 V → `U1` | 1,4 A | 200 mVp-p | 84 % (†) | 40 A | 0,4 A | 52,4 × 27,2 × 24 | 50 g |
| `PS2` | IRM-20-15 | −15 V → `U2` (apilada, §4.2) | 1,4 A | 200 mVp-p | 84 % (†) | 40 A | 0,4 A | 52,4 × 27,2 × 24 | 50 g |
| `PS3` | IRM-45-12 | +12 V rack | 3,8 A | 150 mVp-p | 87,5 % | 60 A | 0,9 A | 87 × 52 × 29,5 | 195 g |
| `PS4` | **IRM-45-12** | −12 V rack (apilada) | 3,8 A (2,5 declarados) | 150 mVp-p | 87,5 % | 60 A | 0,9 A | 87 × 52 × 29,5 | 195 g |
| `PS5` | **IRM-45-5** (D-F7) | +5 V rack | 8,0 A (**4,0 declarados**) | **80 mVp-p** | 83,5 % | 60 A | 0,9 A | 87 × 52 × 29,5 | 195 g |
| `PS6` | IRM-45-5 | +5 V digital | 8,0 A | **80 mVp-p** | 83,5 % | 60 A | 0,9 A | 87 × 52 × 29,5 | 195 g |

**`PS5` cambia de IRM-20-5 a IRM-45-5 (D-F7, firmada 2026-09-03).** Motivo:
`calor_budget.py` corrió por primera vez con la IRM-20-5 y el listón del +5 V
de rack **no existía con ningún venteo**: la IRM-20-5 son 20 W a 5 V = **4,0 A
de placa, exactamente la PSU3**, cero margen de derating, y su curva «3.3V,5V»
tiene el codo a **45 °C**, justo la sala de diseño. Con la IRM-45-5 —la misma
pieza que `PS6`, una referencia menos— el riel tiene 8 A de placa y codo a
50 °C; el listón declarado se queda en 4,0 A, y a esa carga la IRM-45-5
disipa **menos** que la IRM-20-5 a placa (3,95 W contra 5,32). Cuesta ~13 €
más y 87 × 52 en R en vez de 52 × 27. **Desde D-F7 el papel distingue dos
números que mezclaba: la placa del módulo (lo que puede dar) y el listón
declarado (lo que el instrumento promete); el sostenido es el menor de los
dos.** El −12 V ya venía así sin decirlo (3,8 A de placa, 2,5 declarados).

(†) La tabla de la IRM-20 da 84 % para 12 V y 15 V. La IRM-45 se lee sin
ambigüedad ya (la v1 de este papel la tenía cruzada): 5 V 83,5 %, 12 V 87,5 %,
15 V 88,5 %, 24 V 89,5 %, 48 V 90,5 %, monótono con la tensión como todo
flyback.

**`PS4` cambia de IRM-30-12 a IRM-45-12** respecto de la v1. Motivo: la IRM-30
entra en *hiccup* al **105 %** de su nominal (p. 2, OVERLOAD «105 ~ 160 %»), o
sea a 2,63 A contra 2,5 A declarados —menos que el arranque de un módulo
digital—; la IRM-45 al 115 %, y con 3,8 A de placa el −12 V de rack queda con
1,3 A de aire sobre lo declarado.

Lo que comparten los seis, de las mismas hojas:

- **Clase II sin pin de tierra** («no FG pin»), aislamiento I/P-O/P **4,2 kVac**.
  Las salidas son flotantes: por eso se pueden apilar (§4.2).
- **Frecuencia de conmutación: 65 kHz**, en el diagrama de bloques de la p. 3
  de las cuatro hojas («fosc : 65KHz»). El repo ya la usaba: `design-notes` v1
  §18.7 y el commit `fec315e`. La v1 de este papel la declaró HUECO por no
  haber leído la p. 3.
- **Curva de derating (p. 3), leída con los ojos el 03-09 (§12.1 hecho,
  `curvas.py`)**: **100 % hasta 50 °C**, **50 % a 70 °C**, y **no acaba ahí**:
  la IRM-45 sigue a 33 % a 80 °C y 25 % a 85; la IRM-20 a 20 % y 5 %. Por
  encima de 85 °C el módulo no opera. Las salidas de **5 V** de la IRM-20 y la
  IRM-30 quiebran a **45 °C** (y la IRM-20-5 está ya al 80 % a 50); **la
  IRM-45 dibuja una sola curva para toda la serie**, también para su 5 V. La
  lectura de la junta («hasta el 50 % a 70 °C», y «las de 5 V a 45 °C» sin
  distinguir familia) era incompleta en los dos sentidos, y es lo que hizo
  nacer D-F7 (§3, `PS5`). Es el número que gobierna §6.
- **EMI Clase B conducida y radiada «sin componentes adicionales»** — para el
  módulo solo; la nota 5 manda re-verificar el equipo final. Aquí son seis
  compartiendo NTC, MOV, choke y PE, con un riel de 0,8 µV al lado: §4.2.
- **Corriente de fuga < 0,25 mA a 277 Vac**, las cuatro hojas.
- **Protecciones**: corto en *hiccup* con recuperación automática; sobrecarga
  105–160 % (IRM-30), 115–160 % (IRM-20/45), 115–190 % (IRM-15); **OVP** que
  corta la salida y la clampa con zéner en **17,25–20,25 V** (modelos de 15 V),
  **12,6–16,2 V** (12 V), **5,25–6,75 V** (5 V).
- **Arranque**: setup **1000 ms típico, sin máximo** (rise 20 ms IRM-20, 30 ms
  IRM-30/45); **hold-up 40 ms** (IRM-20/30) y **50 ms** (IRM-45) a 230 V. Dos
  módulos apilados **no arrancan ni caen juntos por construcción**: §4.2 y §4.3.
- **Consumo sin carga** < 0,1 W (IRM-15/20) y < 0,15 W (IRM-45).
- **Refrigeración «por convección natural»**. Un módulo encapsulado a su
  máximo se calienta **+35 a +80 K sobre su aire** (junta, §6): la curva de
  derating es sobre el aire, y el aire dentro de un recinto cerrado no es el de
  la sala.

Los seis pesan **735 g** y ocupan **178 cm²** de huella; ninguno pasa de
29,5 mm de alto. El toroide de la v3 pesaba 1,20 kg y medía 46 + 4 de alto.

---

## 4. Arquitectura

### 4.1 La masa es un nodo, y el rack la comparte

La v1 de este papel decía «tres dominios de masa y un punto» y dibujaba una
estrella. La junta lo desmontó con una frase que ahora es **el invariante de
esta fuente**:

> **El potencial contra el que se mide la cadena de tono lo fija una sola
> corriente —la del instrumento— para cualquier patch y cualquier chasis.**

Dos subsistemas que se pasan señal asimétrica por un cable de 3,5 mm —cuya
malla es masa en las dos puntas— **son un solo dominio de masa**. Separar la
alimentación no separa la masa. Y la corriente de retorno de un invitado no
obedece a la regla que uno le escriba: vuelve por **todas** las ramas en
paralelo, repartida por impedancia:

| Rama | Qué es | Impedancia |
|---|---|---|
| (a) | el retorno del rack: bus board de invitados → cable → nodo ★ | 2,5 mm² × 300 mm + dos bornes: **~4,2 mΩ** (`ground_budget.py`: 1 mΩ por borne; con sus 10 mΩ por crimpado, 22 mΩ) |
| (b) | N cables de patch → jacks de la bahía → plano del instrumento → `J2` → ★ | ~120 mΩ por cable (dos jacks y un hilo fino), **÷ N** |
| (c) | panel del invitado → riel → anillo → espárrago | indefinida: «la conductividad de los raíles no está confirmada» (case README) |

Con diez patches, (b) son 12 mΩ contra 4,2 de (a): **1,4 A de un retorno de
5,3 A vuelven por el plano del instrumento**; con veinte, 2,2 A. Y aunque
volviera todo por (a), la fila entera queda **I × 4,2 mΩ** por encima de
`GNDA`: a 5,3 A netos (3,8 + 4,0 − 2,5) son **22 mV = 27 cents** de desfase en
cualquier CV que cruce de la fila al 1 V/oct del instrumento; a 1 A, 5 cents.
«Grueso y directo» no lo arregla: para 1 mV a 5,3 A haría falta 0,19 mΩ, que
es una pletina, no un cable.

**Lo que sí cumple el invariante, y es de construcción, no de regla:**

1. **La bahía es el único cruce de señal entre rack e instrumento** (E-4, #167:
   «el frente se unifica»). Si es así —y §12.9 lo verifica: **ningún módulo del
   instrumento expone un jack**—, entonces el problema tiene un solo sitio.
2. **En la bahía, los jacks viven en una isla de masa del rack.** Sus casquillos
   no tocan `GNDA`: tocan la masa del rack, que es la del panel, que es la del
   chasis. La corriente de un patch vuelve por donde vino —al bus board de
   invitados y a ★— y **no existe conductor de `GNDA` que un jack del rack
   pueda tocar**. La rama (b) desaparece, no se calcula.
3. **Cada señal que cruza la bahía hacia el instrumento se recibe en
   diferencial**: un amplificador de diferencia por entrada, que mide el jack
   **contra la masa del rack en ese jack** y lo re-referencia a `GNDA`. Los
   22 mV de desfase se restan en vez de sumarse. Es un amplificador por CV;
   para audio el desfase no importa y puede ir sin él.
4. **El chasis es la masa del rack.** Conduce corriente del rack —a amperios—
   y **nunca del instrumento**, salvo fuga y falta. La regla de la spec del
   chasis §3.2 («conduce calor, nunca corriente») **se reescribe**: era cierta
   para un instrumento cerrado y deja de serlo con un rack dentro. `GNDA` toca
   el chasis en **un** punto: el espárrago, por `J5`, como §13 de la v1.

Los puntos 2 y 3 son **requisitos que este papel entrega al papel de la bahía**
(§10), no mecanismos que diseña. Y el punto 1 es una condición: si aparece un
segundo cruce (un jack en un módulo del instrumento, una toma trasera de CV),
tiene que cumplir la misma isla y el mismo diferencial, o el invariante cae.

**Dónde está ★, y qué es.** Es un **nodo de cobre en la placa R** (§8), donde
aterrizan por pista corta los retornos de `PS1`–`PS5` y el retorno del rack, y
de donde sale `J5` al espárrago M4. §13.3 de la v1 se cumple tal cual: el
espárrago recibe dos anillos, el de PE y el de `J5`. La `GNDA` de la placa C
llega a ★ por **su propio par grueso** (§8), que lleva la corriente de C y
nada más; y **los segmentos del bus board del instrumento salen del nodo
`GNDREF` de C**, como hoy salen «del punto de estrella». Dos nodos de cobre y
un par entre ellos: la junta lo llamó «una barra», y tiene razón en el nombre
y no en la consecuencia. **El invariante es diferencial, no absoluto**: lo que
desafina es una corriente ajena en un conductor **entre dos módulos de la
cadena de tono**, no una caída común a todos ellos. Los dos crimpados del par
C→R están en el camino común de todo el instrumento, y su caída se resta sola.
Lo que no podía estar ahí —una corriente del rack— ya no está, por el punto 2.

**`GNDD` no está en ★.** El +5 V digital de `PS6` sale **flotante**, como salía
la IRM-15-5, y `GNDD` se une a `GNDA` donde el papel del cerebro lo decida, en
un punto. El bring-up de la v3 asevera > 1 MΩ entre `GNDA` y `GNDD` dentro de
la fuente (paso 6.2) y **sigue aseverándolo**: la v1 de este papel dibujó
`GNDD` en la estrella y contradecía esa puerta.

**La fuga de 50 Hz de cada módulo** sale por **el borne que toca ★**, no «por
el negativo»: en `PS2` y `PS4`, apiladas, el borne que toca ★ es el positivo.
Sale por ahí porque es el único camino de baja impedancia a PE; el otro borne
solo tiene condensadores hacia masa (≥ 300 Ω a 50 Hz para 10 µF). El
bring-up lo mide (§9.1). Y esa fuga —seis × < 0,25 mA más las Y2 del filtro,
**~1,4 mA**— es el no-problema: el límite de IEC 62368-1 para Clase I
enchufable está un orden de magnitud por encima (**cifra a leer en la norma**,
§12.5). El problema es lo que vuelve por esos mismos conductores a **65 kHz**:
§4.2.

### 4.2 El riel ultra: ±15 V DC a la misma cascada, con secuenciador

`PS1` y `PS2` se apilan: el negativo de `PS1` y el positivo de `PS2` van a ★
como `GNDA`; el positivo de `PS1` es +15 V y el negativo de `PS2` es −15 V.
Legítimo porque cada salida es flotante (§3).

**Margen de entrada de los pre-reguladores**, contra las hojas del árbol
(`lm2941-snvs770i-2015-01.pdf`, `lm2991-snvs099i-2016-10.pdf`; dropout **máximo
garantizado 1,0 V a 1 A** en los dos, v2 §1.1/§1.2):

```
+15 V  − 2,5 % (tolerancia, nota 3)                = 14,625 V
       − 0,03 %/°C × 50 K (tempco, 25 → 75 °C)     = 14,40 V
setpoint de U1 + dropout máx. a 1 A                = 13,1 + 1,0 = 14,1 V
margen a 1 A, antes del filtro                     = +0,30 V
−15 V: mismo cálculo contra −12,9 − 1,0 = −13,9    = +0,50 V
```

Menos la caída DC del filtro de §4.2 (`DCR × I`) y ±0,1 V de rizado. A 650 mA
el dropout es menor que a 1 A (Fig. 1 de cada hoja), así que el margen real es
mayor; **el número lo pone `margen_budget.py`** (§9), que sustituye a
`valle_budget.py` con un problema sin 100 Hz que integrar.

**El secuenciador (D-F4, FIRMADO 2026-09-03).** Con el toroide, ±VRAW subían y
caían juntos. Ahora son dos módulos con setup de 1000 ms **típico, sin
máximo**, hold-up de 40 ms cada uno, y *hiccup* independiente: en cada
encendido, cada apagado y cada microcorte hay una ventana de **un riel crudo
sin el otro**, de longitud indefinida. Un bus de ±12 V con un solo riel deja
el otro nodo donde lo pongan los clamps de los op-amps. La v3 no tenía este
caso porque no podía tenerlo.

Los dos pre-reguladores traen el pin para esto: **LM2941 `ON/OFF` activo-bajo**
(< 0,8 V habilita; p. 11 de su hoja) y **LM2991 `ON/OFF` activo-alto deshabilita**
(> 2,4 V; p. 9). Un detector de ventana sobre **los dos** rieles crudos —+15
por encima de 14,1 V **y** −15 por debajo de −13,9 V— habilita a `U1` y `U2`
**a la vez**, y los deshabilita a la vez en cuanto uno falta. La cascada sube
junta y cae junta, como con el toroide, y el *hiccup* de un módulo apaga los
dos rieles en vez de dejar uno vivo. Las piezas del detector se nombran en el
plan con hoja; el mecanismo es éste.

**Sobretensión.** Si `PS1` o `PS2` fallan a su OVP, clampan en **20,25 V** como
máximo: el LM2941/LM2991 admiten 26 V de entrada (hojas), y los LT3045/LT3094
no ven nada porque siguen entrando desde los pre-reguladores. `check_absmax.py`
**se reescribe** con ese sujeto (§9): hoy asevera contra un VRAW de 20,54 V que
ya no existe.

**El camino del rizado.** La v3 atenuaba **voltios a 100 Hz**; la v4 atenúa
**200 mVp-p a 65 kHz y sus flancos**. La junta hizo la cuenta que la v1 de este
papel prometía: para dejar ≤ 0,3 µVrms de 71 mVrms (200 mVp-p senoidal) a
65 kHz hacen falta **107 dB**. En serie:

1. **Un filtro LC nuevo a la salida de cada IRM** —la v3 **no tenía ninguno**;
   `fec315e` metió un choke de modo común de 10 mH en la **red de 230 V** hacia
   `J7`, que es otra pieza al otro lado de la barrera. Este LC se diseña en el
   plan: esquina ≤ fosc/10 (un 22 µH / 47 µF da 4,9 kHz y ~45 dB ideales a
   65 kHz), **amortiguado** —un LC sin amortiguar delante de la impedancia de
   entrada negativa de un regulador lineal es el problema de Middlebrook, y
   la v1 de este papel no lo nombraba—, y con su `DCR` en `margen_budget.py`.
2. **El PSRR del pre-regulador**: garantizado solo a 120 Hz (tabla eléctrica);
   a 65 kHz, la curva típica «Ripple Rejection» (Fig. 9 del LM2941, Fig. 8 del
   LM2991): **decenas de dB típicos, cero garantizados**.
3. **El PSRR del LT3045/LT3094** (`lt3045-rev-d.pdf`, `lt3094-rev-b.pdf`, en el
   árbol desde esta tanda): **76 dB / 74 dB a 1 MHz** en portada, y más a
   65 kHz en la curva —**condicionada al headroom**, que aquí es 1,1 V nominal
   (13,1 − 12,0) y no puede bajar (v2 §1.5.1).

Suma típica: **150–170 dB contra 107**. Para el fundamental sobra en papel.
**Lo que no sobra son los flancos**: los 200 mVp-p están medidos a 20 MHz de
ancho de banda, y son sobre todo picos de 1–20 MHz, donde el LC vive por
encima de su resonancia propia, el pre-regulador da ≈ 0 dB y el LT3045 baja de
76 dB. Veinte milivoltios de pico ahí con 60–80 dB totales son **2–20 µV de RF
en el riel**. Y eso queda **fuera** de la banda de 10 Hz–100 kHz de los
0,8 µVrms: **el LNA de #58 puede dar verde con RF entrando a cada op-amp**.

De ahí tres cosas que la v1 no tenía:

- **Ferrita + cerámico en la entrada de cada regulador** para los flancos (el
  LC cuida los 65 kHz; la ferrita, los MHz). Piezas en el plan.
- **El enlace R → C va trenzado y con choke de modo común**: es un lazo de
  cuatro hilos que lleva 200 mVp-p de conmutación hasta `U1`/`U2`, o sea **el
  mismo mazo que §18.3 midió como emisor mayor**, a una frecuencia donde
  dI/dt es peor.
- **El modo común no lo rechaza ningún PSRR** (`design-notes` v1 §18.7: «el
  PSRR no lo rechaza… llega como una corriente que circula por la masa»). La
  corriente de modo común de seis conmutadores a 65 kHz vuelve por ★ y por el
  propio espárrago, y **una estrella es un concepto de DC y 50 Hz: a 65 kHz el
  retorno lo fija la inductancia**. El mecanismo (D-F5, FIRMADO
  2026-09-03): **un condensador Y2 del borne de ★ de cada módulo al chasis, junto al módulo**,
  para que el lazo de modo común se cierre en centímetros (módulo → Y2 →
  chasis → PE → primario) y no por los hilos de ★. No es un puente de masa:
  a 50 Hz son cientos de kΩ. Mean Well lo documenta en «EMI testing of
  component power supplies» (§12.4, hoja por leer).

Nada de esto se presume. La v2 escribió que el 0,8 µVrms «no se presume hasta
medir con el LNA»; la v4 añade que **el LNA no basta**: hace falta mirar el
riel con 20 MHz de ancho de banda (§9.1).

### 4.3 Los rieles de rack

`PS3` (+12 V) y `PS4` (−12 V) apiladas como en §4.2; `PS5` (+5 V) referida al
mismo retorno. Los tres con su LC, y por un conector dimensionado (§8) hacia
**el bus board de invitados** (#169), que es una placa nueva y **no** el bus
board del instrumento: aquél tiene el +5 V «NC a propósito» y **PTC de 0,25 A
por riel y slot**, y un solo Disting EX (229 mA) lo dispararía.

Por qué 3,8 A de placa y no los 2 A de la PSU3, con la fila medida en HP:

| Fila de 104 HP hecha de… | mA/HP en +12 V | Total |
|---|---|---|
| filtros Doepfer (A-101-1: 30 mA / 16 HP) | 1,9 | ~200 mA |
| Clouds (120 mA / 18 HP) | 6,7 | ~690 mA |
| Morphagene (165 mA / 20 HP) | 8,3 | ~860 mA |
| **Disting EX (229 mA / 8 HP)** | 28,6 | **~3,0 A** |

Una fila entera de Disting EX es absurda, y cabe **en placa**. Cuánto cabe
**sostenido** lo dice §6, y ésa es la decisión.

Tres mecanismos que la v1 no tenía, todos por la misma causa —dos fuentes
independientes y un bus ajeno sin límite de falta—:

- **Secuenciador de ±12 V de rack**, mismo detector de ventana que §4.2, sobre
  interruptores de carga en +12 y −12: **los dos o ninguno**. Sin él, un
  *hiccup* de `PS4` deja la fila con +12 V fijo y −12 V ciclando a ~1 Hz.
- **Crowbar en los rieles de rack (D-F6, FIRMADO 2026-09-03).** Si `PS3` falla a su OVP
  clampa hasta **16,2 V** sobre una fila de módulos ajenos con máximos
  absolutos desconocidos. #118 rechazó el crowbar del ultra porque el fusible
  de red de un toroide no abría a tiempo; aquí el interruptor es el propio
  módulo: un SCR a ~14 V pone el riel en corto y el IRM entra en *hiccup* en
  microsegundos. El lazo que en #118 no cerraba, aquí cierra.
- **Corriente de falta por slot: requisito a #169.** Una IRM-45-12 entrega
  **4,4–6,1 A** antes de entrar en *hiccup* (115–160 % × 45 W / 12 V). Un cable
  Eurorack invertido —el fallo habitual— en un slot ve eso, y su cinta no lo
  aguanta. El bus board de invitados **lleva PTC por slot y riel**, de *hold*
  ≥ 2× el módulo más glotón del censo (≥ 0,5 A para 229 mA, ESTIMADO); el
  valor exacto y el sitio son del papel de #169, con su censo. El bus del
  instrumento protege por slot; el de invitados no puede proteger menos.

### 4.4 El +5 V digital: 8 A de placa, y qué cabe

`PS6` (IRM-45-5) sustituye a la IRM-15-5 y **es el riel de menor rizado de la
familia** (80 mVp-p). Sale **flotante** hacia el módulo 2, como hoy.

Contra `power_budget.py`, corrido el 2026-09-03:

| Escenario | Duras | Cadena | Total | Contra 8 A de placa |
|---|---|---|---|---|
| Typ, 4 N657, host USB a tope | 0,965 A | 2,04 A | 3,005 A | sobran 5,0 A |
| Max TJ = 125 °C, 4 N657, host a tope | 2,895 A | 2,04 A | 4,935 A | sobran 3,1 A |
| Blanco pleno de la cadena | — | 9,60 A | — | **no cabe** |

Tres cosas que la junta corrigió:

1. **El techo que `power_budget.py` importa no es de placa: es sostenido a la
   temperatura del recinto.** Hoy son 14,1 W a 52,3 °C. La enmienda (§10) no es
   «8 A menos margen»: es **la corriente sostenida de `PS6` que dé
   `calor_budget.py`** (§6). Con el recinto cerrado y el listón a máximo, la
   junta la estima en **2,33 A**: por debajo de las 2,895 A de cargas duras.
   **#151 sigue abierto**, y ahora se sabe quién responde por su techo: este
   papel, con ese guion.
2. **8 A no pasan por un KK-254** (4 A por contacto) ni por 22 AWG: 20–40 cm de
   ida y vuelta más cuatro contactos son 41–62 mΩ, **0,33–0,50 V** de caída, y
   el módulo 2 recibe 4,4–4,5 V partiendo de 4,875 (−2,5 %). **El host USB
   exige ≥ 4,75 V en el puerto** y el IRM no tiene *sense* remoto. Conector y
   cable dimensionados en §8, y **requisito al módulo 2**: el VBUS del host se
   regula allí, no se fía de la fuente.
3. **Dos medidas del mismo riel no miden lo mismo.** La v1 ponía un INA226 en
   `GNDD` a la salida de `PS6` para «contrastarlo» con el sensor S9.1 del
   cerebro; S9.1 mide **la cadena**, el INA mediría **el riel entero**, y una
   puerta que exige que coincidan falla siempre o se arregla. **Fuera**: el
   cerebro mide su cadena; la fuente entrega el riel y responde por su techo.

**El HUECO #256 deja de bloquear el dimensionado** (se compra para el máximo
a 125 °C: 761 mA/chip) y **pasa a bloquear el calor** de §4.5.

### 4.5 El 1,8 V: no se decide aquí, pero su calor sí se declara

`alimentacion-n657-design.md` §3.2 propone el 1,8 V como **LDO desde el 3,3 V**
y calcula su calor con el típico: (3,3 − 1,8) × 0,413 = **620 mW**. Con el
listón se dimensiona a máximo, y a máximo son 4 × 761,4 mA = 3,046 A:

```
(3,3 − 1,8) × 3,046 = 4,57 W
```

Siete veces más, y **más que todo lo que disipa la cascada a 650 mA**. Eso
puede voltear D-R1 hacia un buck contenido, y **es decisión de aquel papel**.
Este papel carga con las dos cifras en §6 y no elige. Dónde vive físicamente
ese regulador tampoco es de aquí.

---

## 5. La red

Lo que entra por la pared es lo de #130: **IEC C14 Schurter `KM00.1105.11`** con
portafusible cerrado, y tras él, en la placa R, la cadena de la v3 —`RV1` MOV
S20K275, `NT1` NTC, `L_F` choke de modo común con sus Y2— alimentando a los seis
módulos en paralelo. **Las tres piezas se redimensionan**, porque el número que
las gobierna cambió de orden de magnitud:

**La corriente de red es la fila «AC CURRENT (Typ.)» de la hoja, no vatios
entre voltios.** Un flyback con rectificador y condensador tiene factor de
potencia **0,25–0,30**; la fila lo lleva dentro: 0,4 A (IRM-20), 0,5 A (IRM-30),
0,9 A (IRM-45), a 230 V y carga nominal. Con los seis de §3:

```
0,4 + 0,4 + 0,9 + 0,9 + 0,9 + 0,9  =  4,4 A rms      a placa, los seis a nominal
escalado a la carga del listón      =  3,25 A rms     (fusible_budget.py)
caso típico (§6, ~30 W de entrada)  ≈  0,5 A rms
```

La v1 de este papel decía 0,94 A y «1,7× de margen» para el 1,6 A T. **Es al
revés**: a la carga del listón son **1,7 × In**, y IEC 60127-2 hoja III solo
obliga a un T a abrir por debajo de 30 min a 2,1 In. El 1,6 A T de la v2 se
dimensionó para un toroide de 0,72 A y una IRM: **se va**.

- **Fusible**: clase T, valor de `fusible_budget.py` (§9) con dos términos: el
  permanente de arriba, y el **I²t de rearranque en caliente**, que es el que
  manda y la v1 no tenía. En frío `NT1` limita: seis bancos de entrada (unos
  205 µF ESTIMADO por el hold-up, 10,9 J) a 5 Ω dan ~50 A de pico, τ 1,3 ms,
  **1,66 A²s** —el inrush de placa (320 A sumados, con la IRM-45-5 de D-F7) no se ve nunca—. Pero un
  microcorte con `NT1` caliente da un pico enorme, y **ése es el que
  dimensiona**.

  > **CORREGIDO el 2026-09-04 por `fusible_budget.py`.** Las cifras del
  > párrafo de arriba son las de la v1 y **no** las del modelo: con la NTC
  > real (Ametherm SL22 5R012, 5 Ω ±20 % en frío y 0,05 al 100 % de su
  > corriente máxima) y la I²t exacta del RC (`Vpico²·C/2R`), el arranque
  > frío da **71 A y 2,37 A²s** y el rearranque caliente **523 A y
  > 17,44 A²s**. Y el **4 A T de hipótesis no llega por ninguno de los dos
  > caminos**: ni el permanente (3,25 A rms al 70 % del calibre y con el
  > derratado del recinto piden **5,34 A**) ni el rearranque (17,4 A²s
  > contra 15,3 admisibles de sus 77 de fusión). **Sale 6,3 A T.**
  >
  > Y la PIEZA la decide otra cosa: el **poder de corte**. Un 5×20 de
  > vidrio corta 63 A y en el enchufe hay ~490 disponibles (230 V sobre la
  > impedancia de referencia de IEC 61000-3-3). Hace falta uno **cerámico
  > de alto poder de corte**, y esa hoja no está: es el HUECO de
  > `fusible_budget.py`.
- **`NT1`**: el SL10 5R002 está a 2 A de régimen y aquí son 2,7–3,9. Pasa a la
  talla de **≥ 4 A** de la misma familia (Ametherm SL22, hoja por leer, §12.6),
  y con dos números que hoy no están en ningún papel: **la energía que absorbe
  en cada arranque frío (~8,3 J)** y **la capacidad máxima que admite a 230 V**
  contra esos 205 µF.
- **`L_F`**: el choke de `fec315e` estaba dimensionado «230 V a 0,2 A» para una
  IRM. Pasa a **≥ 4 A**. Su función cambia: ya no hay capacidad entre devanados
  de un toroide que filtrar; es el filtro de conducida de seis módulos, y la
  nota 5 de sus hojas dice que el equipo final tiene que medirlo.
- **Los carriles de 230 V de la v3** (`rutear_red`, 0,72 A) se recalculan para
  3,9 A en `build_pcb.py` de R.

**Crowbar: ninguno en el ultra**, como en #118 y por una razón más: cada IRM
lleva OVP propio. **Uno en cada riel de rack** (§4.3, D-F6).

**`TR1` con fusible térmico: ya no existe la pieza.** Los IRM llevan protección
de corto en *hiccup* y encapsulado UL 94V-0.

**La fuga a PE** (§4.1): ~1,4 mA contra el límite de la norma, `fuga_budget.py`.

---

## 6. Térmica: el listón se compró en un eje que el recinto no tiene

La PSU3 entrega 2 A **en un case abierto, al aire de la sala**. La v4 entrega
3,8 A **en la hoja**, y en un recinto de acero cerrado entrega lo que la curva
de derating diga al aire que haya dentro. Una corriente sostenible no es
propiedad de un módulo: lo es de la terna (módulo, recinto, ambiente). **La v1
de este papel midió «superior» en el eje equivocado**, y la junta lo enseñó con
la cadena entera:

```
sala de diseño                 45 °C     (spec del chasis §3.1: «la habitación para la
                                          que se dimensionó todo lo demás»; NO 25)
+ aire del cajón               +X K      (clearance_budget.py::guarda_aire(): techo de
                                          20 K de subida —era 15, PR #311, 04-09—,
                                          hoy con 151,55 W de todo el cajón)
+ aire del recinto             +Y K      (spec del chasis §3.1: 0,1453 m² × 9 W/m²K)
+ el propio módulo             +35..80 K sobre su aire, a su máximo (junta)
→ curva de derating (p. 3)     100 % hasta 50 °C; −2,5 %/°C hasta el 50 % a 70 °C
```

Las fuentes de calor, con los rendimientos ya corregidos de §3:

| | Típico (instrumento a censo, digital a 3,0 A, rack vacío) | Máximo (todo a placa a la vez) |
|---|---|---|
| `PS1` + `PS2` | (15 × 0,340 + 15 × 0,327) × (1/0,84 − 1) = 1,91 W | 19,5 × 0,19 = 3,71 W |
| `PS6` | 5 × 3,005 × (1/0,835 − 1) = 2,97 W | 24,7 × 0,198 = 4,88 W |
| `PS3` | < 0,15 W | 45,6 × (1/0,875 − 1) = 6,51 W |
| `PS4` | < 0,15 W | 30 × 0,143 = 4,29 W |
| `PS5` (IRM-45-5 desde D-F7, a los 4,0 A declarados) | < 0,1 W | 20 × (1/0,835 − 1) = **3,95 W** (era 5,32 con la IRM-20-5) |
| `U1`, `U2` a 15 V de entrada | 0,65 + 0,69 W | 1,24 + 1,37 W |
| LT ×4 + `U3` | 0,35 + 0,30 W | 1,30 + 0,30 W |
| **Total en el recinto** | **7,2 W** | **27,5 W** (28,9 con la IRM-20-5 en `PS5`, antes de D-F7) |
| + el 1,8 V si vive dentro | +0,62 W | +4,57 W |

Y **fuera del recinto pero dentro del cajón**, lo que el listón permite y
`guarda_aire()` no tiene: la fila de invitados a placa disipa **95,6 W** y el
digital **24,7 W**. El case se cerró (techo macizo, trasera capturada) con 9 W
de fuente en su presupuesto de aire.

**Lo que da el lazo** (junta, sobre el modelo del case y del recinto de hoy;
`calor_budget.py` lo hace suyo en §9):

| Situación | Aire del recinto | Rack sostenido (+12 / −12 / +5) | `PS6` sostenido |
|---|---|---|---|
| Recinto cerrado, solo la fuente en el cajón | ~64 °C | **1,97 / 1,29 / 2,07 A** (52 % del listón) | — |
| Recinto cerrado, con los 120 W de fila y digital en el cajón | ~78 °C | **0,63 / 0,42 / 0,67 A** (17 %) | **2,33 A** < 2,895 A de cargas duras |
| Al 49 °C que la v1 de este papel escribía (con sala a 25) | 49 °C | `PS5` ya en 3,6 A | — |

Las dos primeras filas son **por debajo de la PSU3**. La segunda es por debajo
de la v3.

**Lo que da `calor_budget.py`** (03-09, con las curvas leídas con los ojos,
D-F3 = A y D-F7; **punto fijo**, no carga a placa):

| Situación | Aire del recinto | Rack sostenido (+12 / −12 / +5) | Digital sostenido |
|---|---|---|---|
| Caja de hoy (cerrada), todo lo que el rack pueda dar | **86,7 °C** | **0 / 0 / 0 A** — no hay punto de trabajo | 0 A |
| **Venteo mínimo: 22 200 mm² nuevos** (D-F3 = A; 20 600 antes de contar la franja de red) | **68,9 °C** | **2,0 / 2,0 / 4,0 A** — el +12 fija el mínimo | **4,2 A** |
| A placa sin derating, caja de hoy (no es un estado alcanzable) | 145,7 °C | — | — |

Con la IRM-20-5 en `PS5` la segunda fila **no existía**: ningún venteo daba
4,0 A en el +5 V, y de ahí D-F7. Dos cosas del modelo que hay que decir: la
constante que más mueve el sostenido es **`CD_TIRO`** (el coeficiente de
descarga del venteo, supuesto y no medido), y el modelo **hereda de
`guarda_aire()` que el cajón solo evacúa por chimenea** —ignora la convección
de las paredes exteriores—, así que los 22 200 mm² son **pesimistas**.

**Y NO SON EL ENCARGO (Tarea 4, 03-09).** Al meter los 147,83 W en
`guarda_aire()` —27,53 del recinto + 120,3 de fila y digital— salió que el
listón del rack y el criterio del propio case piden cosas distintas, y manda
el segundo:

| Quién pregunta | Qué exige | Venteo **nuevo** | Venteo **total** |
|---|---|---|---|
| `calor_budget.py` | que los rieles den el listón con la sala a 45 °C | **22 148 mm²** | 25 447 mm² |
| `guarda_aire()` | los **20 K sobre ambiente** que la afinación ya suponía | **22 446 mm²** | 25 745 mm² |

**Las dos columnas están porque la confusión entre ellas es fácil y ya se
cometió dos veces el 04-09.** `calor_budget.py` toma `area_venteo_mm2` como
área ADICIONAL —la suma a los 3 299 mm² efectivos que el case ya tiene, ver
`_k(A_EF_BASE_MM2 + area_venteo_mm2, …)`— y `guarda_aire()` publica el TOTAL.
Comparar una con otra da un 14 % de diferencia que no existe.

**Y desde el 04-09 los dos criterios casi coinciden.** Dos cosas se movieron el
mismo día y en sentidos contrarios: el techo del case pasó de 15 a **20 K**
(PR #311: `tuning_budget.py` llevaba semanas calculando la deriva de afinación
con 20 y pasando con 1,68 cents de 5,0; el 15 era «SUPUESTO de diseño» sin
fuente, y de los dos techos el que tenía argumento era el de la afinación), y
la potencia del cajón subió de 147,83 a **151,55 W** al contar la franja de red
que la tabla de arriba no llevaba. Resultado:

En la misma unidad, **los dos criterios piden lo mismo dentro del 1,3 %**:
22 148 mm² nuevos la fuente y 22 446 el case, **297 mm² de diferencia**. Con
los 22 148, el case sube **20,2 K** contra un techo de 20: los rieles llegan y
el condensador se queda a un 1 % de su criterio.

Eso no es una coincidencia cómoda, es evidencia. Son **dos criterios físicos
independientes** —«el aire no sube de 20 K», que sale de la deriva de
afinación de `tuning_budget.py`, y «el listón se sostiene», que sale de las
curvas de derating de las hojas Mean Well— resueltos por dos modelos que sólo
comparten la ecuación de tiro. Que pidan la misma abertura dentro de un 1 %
dice que los dos están bien. Y para **#289** significa que quien dibuje el
venteo tiene **un solo número** que satisface a los dos, no dos encargos que
negociar.

El encargo sigue siendo el mayor de los dos, **25 745 mm² totales**, y con dos
cifras que lo acotan: la pared exterior (0,507 m² de envolvente sin el suelo) se lleva
otros **30,4 W** a ese techo con `U = 3 W/m²K` supuesto —más que los 19,4 de
la chimenea de hoy—, y contándola bajan a **20 575**; con `C_D = 0,55` suben a
**30 426**. Y el
**tiro** es la variable barata: `k` va con la **raíz** de la altura y hoy son
105 mm en un case de 256, así que subir la salida vale más que ensanchar la
rejilla. `guarda_aire()` ya no asevera ese techo —lo publica como HUECO— y se
pone verde sola el día que el papel del case dibuje el venteo.

**Esto no era un hueco: era la decisión (D-F3), y Samuel la tomó el 03-09.**
El listón se firmó como corriente de placa; sostenido, dentro de un recinto
cerrado y este cajón, **no existía**. De los tres caminos se firmó el **A:
ventilar el recinto y el cajón por convección natural, sin ventilador**.

| | A. Ventilar | B. Cerrado y honesto | C. Forzado |
|---|---|---|---|
| **Qué** | el recinto **y el cajón** ganan convección natural: entrada baja, chimenea alta, rejilla; sin ventilador | el recinto sigue cerrado; el listón sostenido es el que dé `calor_budget.py` | ventilador en el recinto |
| **Rack sostenido** | lo que la curva dé al aire de la sala + un salto pequeño: **cerca de placa** | ~1,3–2 A: **nivel PSU2** | cerca de placa |
| **Precio** | revierte la decisión del 18-08 (cerrado); polvo; el papel del case rediseña techo y trasera con un presupuesto de aire nuevo | «superior a la PSU3» se queda en la caja, no en el rack | ruido en un instrumento; un motor que falla |
| **Quién** | el papel del case, con `guarda_aire()` reescrito | este papel, con la columna «sostenido» de §1 rellena | — |

**FIRMADO: A** (Samuel, 2026-09-03). El listón era el punto: un rack que el
calor recorta al 17 % no es «a la altura de la PSU3 o superior», es una cifra
de catálogo. El cerrado se decidió el 18-08 con **9 W** de fuente dentro, y
hoy son **29 W** en el recinto más **120 W** de fila y digital en el cajón: la
decisión vieja se tomó sobre un número que ya no existe. Ni la PSU3 vive en
una caja cerrada.

**Por qué no B ni C.** **B** (cerrado y honesto) deja el listón firmado
significando nivel PSU2 en el rack, que es la mitad de lo que este papel
existe para comprar. **C** (forzado) mete un motor —ruido, y una pieza que
falla— dentro de un instrumento que hasta hoy es silencioso por construcción;
es un precio peor que el de abrir rejillas. Lo que **A** cuesta y se paga: el
papel del case rediseña techo y trasera con un presupuesto de aire nuevo, y
entra polvo. Esos dos se pagan una vez; un rack recortado se paga cada vez que
se enchufa un módulo.

**Lo que ventila y lo que no.** Respiran la zona de los módulos, la cascada y
el cajón. **La franja de 230 V no**: su barrera de 6 mm y su tapa siguen
cerradas, y ninguna abertura puede dar acceso con el dedo de prueba a nada de
la franja de red — es aserción de `check_red_chasis.py` (§9), no una nota. **Con A firmado, además, hay que mirar si los
módulos se montan con la cara contra la pared de acero**: son bloques encapsulados y la
hoja solo habla de convección; conducir por el encapsulado a la chapa es lo
que hoy hacen los TO-220 y podría valer para ellos (§12.7, pregunta a Mean
Well o medida).

Los tres TO-220 **siguen contra la pared** en cualquier camino.

---

## 7. La telemetría

Los cinco chips de la v3 se quedan y **cambian de pregunta**:

| Chip | v3 | v4 |
|---|---|---|
| `U8` INA226 0x40 | +12 V ultra, V e I | igual |
| `U9` INA226 0x41 | +5 V de `U3`, V e I | igual |
| `U10` ADS1115 0x49 | −12 V, VRAW+, VRAW− (V) | −12 V, **+15 V, −15 V**, y el cuarto canal, libre hasta hoy, a **−12 V de rack** |
| `U11` TMP1075 0x48 | aire del recinto | igual, y ahora **es el que vigila la curva de derating** |
| `U12` ISO1541 | barrera GNDA/GNDD | igual |

Los divisores son los de la spec del chasis §4.4: 100 k / 20 k al 0,1 %, 1/6, y
**los canales negativos referidos al +5 V**, no a masa —el ADS1115 tiene
máximo absoluto de −0,3 V en el pin—: −15 V da 5 × 5/6 − 15/6 = **1,67 V**;
+15 V con su divisor a masa, **2,5 V**. El −12 V de rack necesita **su
divisor y su clamp** (hoy AIN3 está «atado a GNDA»); van en el plan. Lo que
muere es la frase «mide por primera vez el valle de VRAW». Lo que nace es
**medir los ±15 V con carga**, que es donde se ve un IRM saliéndose de su
curva.

**D-F2 (FIRMADO 2026-09-03): dos INA226 en los rieles de rack, poblados.** `U13` en
+12 V y `U14` en +5 V de rack, 0x44 y 0x45 (`check_telemetria.py` vigila las
colisiones), **en la placa R**, donde están los shunts. Dan lo que ningún case
Eurorack da: el instrumento le dice al dueño cuánto come su rack. **Cuestan
cuatro hilos más en el enlace R ↔ C** (SDA, SCL y la alimentación de 5 V del
lado `GNDA` de la telemetría, §8), y ese enlace ya los lleva.

Lo que compran no es un adorno. Junto con `U11` (TMP1075), la corriente de
rack es lo que convierte la curva de derating de §6 en algo que el instrumento
**vigila en marcha**: el firmware puede avisar cuando el rack se acerca a su
techo sostenido a la temperatura que hay dentro, en vez de que el dueño lo
descubra por un módulo que se reinicia. Es la contrapartida en telemetría de
haber firmado el listón en corriente sostenida.

**El +5 V digital no se mide en la fuente** (§4.4). Sale flotante; lo mide
quien lo reparte.

---

## 8. Las placas y los conectores

**Dos placas más el bus board de invitados.** La v1 de este papel lo
justificaba con los «≥ 80 mm» de `revisar_diagonal()`; la junta señaló que ese
número se derivó para un lazo rectificador de 6,81 cm² a 100 Hz, y transplantarlo
a seis conmutadores encapsulados de 65 kHz es conservar la cifra y cambiar la
física. Las razones que quedan son otras, y son mejores:

1. **R se prueba sola.** Con cargas ficticias, antes de conectarle un solo
   nodo sensible (§9.1, paso 1). La v3 no podía: su entrada de red y su
   cascada eran la misma placa.
2. **El campo de un IRM encapsulado no lo publica nadie.** Con dos placas, la
   distancia a la isla ultra **se fija al montar y se mide con el LNA**, en vez
   de fijarse en un layout que ya no se puede mover. `params.scad` declara
   dónde va cada placa, y **la puerta del chasis mide la distancia entre las
   dos**; `revisar_diagonal()` en C **se retira** —no hay lazo rectificador que
   medir— y en su lugar C lleva un *keep-out* declarado alrededor de su
   conector de entrada.
3. **C es la v3 menos la red**, y sus puertas valen con cambios de nombre.

| Placa | Lleva | Hereda de |
|---|---|---|
| **R — red** | IEC en la pared, `RV1`, `NT1`, `L_F` + Y2 redimensionados, la franja de 230 V con su barrera, **`PS1`–`PS6`**, seis LC amortiguados, los Y2 de modo común (D-F5), el detector de ventana ×2 y los interruptores de rack, el crowbar de rack (D-F6), `U13`/`U14` (D-F2), el nodo ★ y `J5`; salidas: ±15 V a C, ±12/+5 al bus board de invitados, +5 V digital al módulo 2 | la franja de red de la v3 (`rutear_red`, `NETS_RED`, barrera de 6 mm), recalculada a 3,9 A |
| **C — cascada** | `U1`/`U2` con su ON/OFF cableado al detector, en fila contra la pared; la isla LT3045/LT3094 con `GNDREF`; ferritas de entrada; `U3`; la isla de telemetría; `J2`, `J6`, `J8`; entrada: ±15 V | **la v3 entera menos `TR1`, `BR1`, `C_bulk` y la franja de red** |
| **Bus board de invitados** | #169: peines, PTC por slot, su sitio | el bus board del instrumento, con otro presupuesto de PTC |

**Los conectores los dimensiona la corriente, y de paso se protegen por
geometría** (la doctrina de la spec del chasis §4.3: dos cables que no deben
cruzarse no caben en el mismo conector):

| Enlace | Corriente | Hilos | Familia (a nombrar en el plan con hoja) |
|---|---|---|---|
| R → C, ±15 V | 1,4 A | +15, −15, `GNDA` ×2, **trenzados**; +4 por D-F2 (SDA, SCL, +5 V tele, retorno) | KK-396 o similar: distinto de los KK-254 de C |
| R → bus board de invitados | 3,8 / 3,8 / 4,0 A | +12, −12, +5, retorno ×2, en 2,5 mm² | Mini-Fit Jr o bornera; **no** KK-254 (4 A por contacto) |
| R → módulo 2, +5 V digital | 8,0 A | +5, `GNDD`, en ≥ 16 AWG y corto | Mini-Fit Jr con dos contactos por polo; **no** el KK-254 de `J6` |
| C → módulo 2, `J6` +5 V de `U3` | 30 mA | como hoy | KK-254, como hoy |

Los dos 5 V que llegan al módulo 2 van en **familias distintas** por necesidad
de corriente, y con eso la protección geométrica que la v1 de este papel
abandonaba sin decirlo vuelve sola.

**Tamaños**: los seis IRM ocupan 209 cm² (178 antes de D-F7: la IRM-45-5 de `PS5` son 45 cm² donde la IRM-20-5 eran 14); R con su franja de red, sus filtros y
sus interruptores anda por **200 × 150 (ESTIMADO)**; C, sin rectificador ni
toroide, **por debajo de 200 × 100 (ESTIMADO)**. Los ponen los `build_pcb.py`.

**El chasis** pierde el toroide (Ø93 × 46 en `chasis_toroide_x = 273,5`) y gana
una placa; y con D-F3 = A gana aberturas. Todo eso es del papel del case (§10).
Lo que este papel le exige: **las dos placas dentro del mismo recinto de
acero**, porque R lleva 230 V y C lleva los tres tabs contra la pared.

---

## 9. Las puertas

Principio II: un presupuesto es un guion con aserciones. Éstas son las de la
v4, y **cada una nace con la entrada que la junta dijo que le faltaba** —sin
eso nacen verdes por vacías (Principio VIII)—:

| Puerta | Estado | Qué pregunta, y con qué entrada |
|---|---|---|
| `check_absmax.py` | **se reescribe** | el sujeto ya no es VRAW = 20,54 V: es el **OVP máximo de `PS1`/`PS2` (20,25 V)** contra los 26 V de `U1`/`U2`, y el **OVP de `PS3`/`PS4` (16,2 V)** contra lo que el crowbar de rack deje pasar |
| `check_telemetria.py` | hereda, crece | direcciones, divisores (el nuevo de AIN3), shunts; `U13`/`U14` de D-F2 |
| `kicad/check_bom.py`, `check_netlist.py`, `check_pcb.py`, `check_fab.py`, `check_huellas.py` | **una por placa** | R y C; `check_huellas.py` estrena **seis huellas IRM de la p. 3** (§12.3); `check_netlist.py` de R asevera que **ningún retorno de IRM comparte pista** hasta ★ y que **`GNDD` no toca ★** |
| `check_netlist.py` de la bahía | **requisito** (§10) | **ningún casquillo de jack está en `GNDA`** |
| `check_red_chasis.py` | hereda, crece | IEC con su recorte (#130), un fusible, y `NT1`/`L_F` con rating ≥ la fila «AC CURRENT» sumada |
| `check_bringup.py` | **se reescribe** | §9.1 |
| `valle_budget.py` | **muere** | no hay valle |
| `margen_budget.py` | **nuevo** | tolerancia + tempco + rizado + `DCR` del LC contra el dropout de `U1`/`U2` a la corriente real |
| `fusible_budget.py` | **nuevo** | permanente con la fila «AC CURRENT»; I²t frío con `NT1` y **rearranque caliente**; contra el I²t de la hoja del fusible |
| `fuga_budget.py` | **nuevo** | seis fugas + Y2 contra la cifra de la norma |
| `calor_budget.py` | **nuevo** | **la cadena entera de §6**: sala 45 → `guarda_aire()` del case con los 120 W de fila y digital → recinto → módulo; curva de derating leída; devuelve **la columna «sostenido» de §1** |
| `rizado_budget.py` | **nuevo** | LC amortiguado × PSRR(`U1`) × PSRR(LT) a 65 kHz **y a 1–20 MHz**, contra la cota de ruido; y **declara que el modo común no lo cubre** |
| `secuencia_budget.py` | **nuevo** | umbrales del detector de ventana contra tolerancia + tempco de los IRM y el dropout de `U1`/`U2`; y que ningún estado deja un riel solo |
| `consumo_total_budget.py` (módulo 3) | **enmienda** | `RESERVA_INVITADOS` desaparece; el 650 con 30 % es del instrumento |
| `invitados_budget.py` | **nuevo** | placa vs. declarado vs. **sostenido** (de `calor_budget.py`) vs. censo de §4.3 |
| `power_budget.py` (módulo 2) | **enmienda** | `TECHO_W_PESIMISTA` = **sostenido de `PS6`**, de `calor_budget.py` |
| `ground_budget.py` (bus board) | **enmienda** | el desfase rack ↔ instrumento **I × R_retorno** con N patches como parámetro; y la aserción de que ese término **no entra** en la cadena de tono porque la bahía lo recibe en diferencial |
| `clearance_budget.py::guarda_aire()` (case) | **enmienda** | los 120 W del cajón que hoy no tiene |

Todos entran por `hardware/tools/gates.py` sin lista, y **cada uno se ve fallar
con su mutación antes de mergear**.

### 9.1 El bring-up, reescrito

Se escribe antes de que exista la placa, hereda la forma de la v3 (cada paso
predice un número, `medidas.csv` lo guarda, `check_bringup.py` juzga) y **no
pierde ninguno de sus pasos**: los 6 (telemetría contra multímetro), 7
(térmica con el recinto cerrado a carga de diseño) y 8 de la v3 siguen; la v1
de este papel los había dejado caer.

- **Paso 0** (desenchufado): aislamiento de los tres tabs contra la pared **se
  queda** (`U2` con el tab a −15 V, la pared a PE). Continuidad de tierra,
  igual. **Nuevo**: continuidad de cada borne de ★ de cada módulo con ★
  (miliohmios), y **aislamiento** —no «abierto»: > 1 MΩ— entre el borne de ★
  de un módulo y el de otro **con ★ desconectado**, medido entre los dos
  bornes que tocan ★ (para `PS2`/`PS4`, su positivo). Y **> 1 MΩ entre `GNDA` y
  `GNDD`**, como la v3.
- **Paso 1** (R sola, C y bus board desconectados): **cada IRM, uno por uno**,
  tensión en vacío y a su nominal con carga ficticia, **rizado a 20 MHz con el
  método de la nota 2 de la hoja** (par trenzado de 12", 0,1 µF ‖ 47 µF), y
  **la corriente de red rms** con pinza a esa carga, contra la fila de la hoja.
  **Inrush** con pinza de corriente en un arranque frío y en un rearranque a
  los 100 ms: contra `fusible_budget.py`.
- **Paso 2**: ±15 V con carga → rizado **después del LC**, a 20 MHz, y el
  mínimo de +15 V con carga contra los 14,1 V que `U1` necesita.
- **Paso 2b, el secuenciador**: quitar la red a `PS1` sola, con `PS2` viva:
  **los dos rieles de la cascada caen juntos**, y viceversa. Lo mismo en el
  rack. Es el paso que valida D-F4; sin él, D-F4 es una promesa.
- **Pasos 3–5**: la cascada, iguales a la v3 (setpoints, `J2` medido y no
  leído, ±12 V con carga).
- **El paso 4 de la v3 —el valle— muere**; su sustituto es el paso 2.
- **Paso 6**: telemetría contra multímetro, **más los ±15 V con carga**.
- **Paso 7**: térmica con el recinto en su configuración final (cerrado o
  ventilado, D-F3) **a la carga sostenida declarada**, TMP1075 y termopar sobre
  `PS3` y `PS6`: es la medida que valida `calor_budget.py`, y **la que decide
  si la columna «sostenido» de §1 es cierta**.
- **Nuevo, el desfase rack ↔ instrumento**: 2 A de carga ficticia en +12 V de
  rack y **milivoltios entre la masa del bus board de invitados y `GNDREF`
  de C**; contra `ground_budget.py`. Y con un CV de 1 V entrando por la bahía
  desde un jack cargado con esos 2 A, **el 1 V/oct del instrumento en cents**:
  es la medida de que el diferencial de la bahía funciona.
- **Nuevo, el crowbar de rack**: forzar el disparo con `PS3` cargada: **`PS3`
  entra en *hiccup*, `PS4` se apaga por el secuenciador**, nada humea.
- **El LNA (#58) es la puerta del riel ultra, y no basta**: además de su
  banda, **el riel de ±12 V se mira a 20 MHz de ancho de banda** con carga y
  los seis módulos encendidos, contra la cota de RF de `rizado_budget.py`.

---

## 10. Enmiendas a otros papeles

Para ejecutarlas en el plan de esta tanda, **no para que un documento prometa
lo que otro no hace** (#214, #206).

| Documento | Tipo | Qué |
|---|---|---|
| `hardware/01-power-supply/v3/README.md`, `docs/modules/01-power-supply.md` | Update | estado: la v3 no se pide; la v4 es la que se construye, y por qué; la regla «nunca con una v4» y qué la sustituye |
| `design-notes.md` v1 §13 | Patch | ★ es un nodo en R; `GNDD` no lo toca; el chasis es la masa del rack |
| `design-notes.md` v1 §18 | **Rewrite** | de 100 Hz a 65 kHz: seis módulos, LC amortiguado, ferritas, Y2 de modo común, enlace trenzado, **el LNA y la mirada a 20 MHz como puertas** |
| spec del chasis §3.1, §3.2, §3.3, §4 | Update / **Rewrite** de §3.2 | térmica → `calor_budget.py` con la cadena de §6; «conduce calor, nunca corriente» → «conduce la corriente del rack, nunca la del instrumento»; geometría sin toroide y con D-F3 |
| `case/clearance_budget.py::guarda_aire()` y el papel del case | Expand / Sync | los 120 W del cajón; D-F3; `chasis_toroide_*` desaparece; dos placas; distancia R ↔ C como parámetro y puerta; el IEC (#130) sigue pendiente |
| **Papel de la bahía** (#166 §5, #183) | **Requisito** | isla de masa del rack bajo los jacks; **recepción diferencial** de cada CV que cruza al instrumento; `check_netlist.py` con «ningún casquillo en `GNDA`» |
| `alimentacion-n657-design.md` §3.2 | Patch | el calor del LDO a máximo (4,57 W); D-R1 sigue abierto con los dos números |
| `psu-v2-goat-design.md` §7, §11.5 | Patch | la IRM-15-5 «fuera de la placa» → `PS6` en R |
| `consumo_total_budget.py` | Patch | sin `RESERVA_INVITADOS` |
| `power_budget.py` | Patch | techo = sostenido de `PS6`, de `calor_budget.py` |
| `ground_budget.py` | Expand | I × R_retorno con N; la aserción de que no entra en la cadena de tono |
| Spec del cerebro (módulo 2) | **Requisito** | el VBUS del host USB se regula en el módulo 2; la fuente entrega 4,875 V menos el cable |
| #169 | Update | rieles de §4.3, PTC por slot como requisito, secuenciador y crowbar aguas arriba |
| #151 | Update | dueño del techo: `calor_budget.py`; sigue abierto hasta que corra |
| #118 | Update | el crowbar vuelve **solo** en los rieles de rack, y por qué ahí sí cierra el lazo |
| #256 | Update | ya no bloquea el dimensionado del +5 V; bloquea el calor del 1,8 V |
| #58 | Update | puerta del riel ultra, y no basta sola (RF a 20 MHz) |
| #141, #280, #106, #56, #57 | Close (al adoptar la v4) | el sujeto desapareció con el toroide y el rectificador |

---

## 11. Lo que este papel NO decide

- **D-R1, el 1,8 V** (LDO o buck, y dónde vive). Aquí solo su calor en los dos
  extremos.
- **El bus board de invitados** (#169): peines, PTC (valor), sitio. Aquí sus
  rieles y sus requisitos.
- **La bahía**: aquí sus dos requisitos; el mecanismo del diferencial es suyo.
- **El valor del fusible**: ya no es hipótesis. `fusible_budget.py` corrió
  el 2026-09-04 y da **6,3 A T**; lo que sigue abierto es la **pieza**, que
  la decide el poder de corte y necesita una hoja de fusible cerámico que
  no está en el árbol.
- **Ninguna pieza que no esté en §3 con su hoja** (R-M3): LC, ferritas, Y2,
  detector de ventana, interruptores, SCR, conectores, `NT1` y `L_F` nuevos, se
  nombran en el plan con hoja en el árbol.
- **El tope de brillo de la cadena de LEDs**: se queda por diseño.

---

## 12. Verificaciones antes de sellar

1. **Las curvas de derating de las cuatro hojas, con los ojos** (p. 3): codo,
   pendiente y el 45 °C de las salidas de 5 V. Entrada de `calor_budget.py`.
2. **Las curvas de PSRR** de LM2941 (Fig. 9), LM2991 (Fig. 8), LT3045 y LT3094
   a 65 kHz y a 1–20 MHz, de las cuatro hojas ya en el árbol, con los ojos.
   Entrada de `rizado_budget.py`.
3. **Las seis huellas IRM** dibujadas de la p. 3 de cada hoja y pasadas por
   `check_huellas.py`: una huella equivocada pasa el ERC, el DRC y la netlist.
4. **«EMI testing of component power supplies»** de Mean Well
   (meanwell.com/Upload/PDF/EMI_statement_en.pdf): el mecanismo de modo común
   de D-F5, dicho por el fabricante.
5. **La cifra de fuga de IEC 62368-1** para Clase I enchufable, de la norma.
6. **La hoja de Ametherm SL22** (o la talla que salga): régimen ≥ 4 A, energía
   por arranque y capacidad máxima a 230 V contra ~205 µF.
7. **Si un IRM encapsulado puede conducir calor por su cara a la chapa**
   (pregunta a Mean Well, o medida en el paso 7): cambia cuánto vale A en D-F3.
8. **El I²t del fusible elegido**, de su hoja, para `fusible_budget.py`.
9. **Que ningún módulo del instrumento expone un jack** (#167, «el frente se
   unifica»): es la condición del invariante de §4.1. Si alguno lo hace, ese
   jack cumple la misma isla y el mismo diferencial.
10. **Stock real** de las seis referencias el día de mandar.

---

## 13. Riesgos

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | **El listón sostenido no existe en el recinto cerrado** (la junta lo estima en 17–52 % de placa) | D-F3 decidido; `calor_budget.py` con la cadena entera; paso 7 medido |
| 2 | La RF de los flancos (1–20 MHz) entra en los op-amps mientras el LNA da verde en su banda | ferritas + LC amortiguado; la mirada a 20 MHz del paso final de §9.1 |
| 3 | El modo común de seis conmutadores vuelve por ★ y por el espárrago | D-F5 (Y2 al chasis en cada módulo), §12.4 leído, medido con los seis encendidos |
| 4 | El retorno de un invitado desafina el instrumento | la isla y el diferencial de la bahía (requisitos de §10); `ground_budget.py` extendido; la medida en cents del bring-up |
| 5 | Un riel crudo solo, en cada encendido, apagado y microcorte | D-F4 (secuenciador), paso 2b |
| 6 | Un IRM de 12 V en OVP pone 16,2 V en una fila ajena | D-F6 (crowbar de rack), su prueba en el bring-up |
| 7 | El fusible se fatiga con los rearranques en caliente | **Cerrado en el cálculo el 04-09**: `fusible_budget.py` da 6,3 A T y el rearranque gasta el 9,2 % de su I²t. Abierto el **poder de corte**: el 5×20 de vidrio corta 63 A contra ~490 disponibles |
| 8 | El calor del 1,8 V a máximo (4,57 W) cae dentro del recinto y nadie lo contó | §4.5 declarado; D-R1 decide con los dos números |
| 9 | El módulo 2 recibe 4,4 V por el cable y el host USB no arranca | conector y cable de §8; el VBUS regulado en el módulo 2 (requisito de §10) |
| 10 | Una huella IRM equivocada llega a fábrica | §12.3, `check_huellas.py` por placa |
| 11 | Tres proyectos KiCad donde había uno; las puertas se multiplican | heredan por placa (§9); lo que se paga es tiempo |
| 12 | El listón compró un máximo que no existe (fila de 104 HP a 3,8 A) y se paga en calor y chapa | es el precio del listón; lo que puede bajar es el **sostenido** declarado, y eso es D-F3, no un descubrimiento |

---

## 14. Lo que Samuel decidió (2026-09-03)

| | Decisión | Consecuencia inmediata |
|---|---|---|
| **D-F1** | el listón, como **corriente de placa** | §1; se **re-firma** en sostenida cuando corra `calor_budget.py` |
| **D-F3** | **A: ventilar** recinto y cajón, convección natural, **sin ventilador** | el papel del case rediseña techo y trasera; `guarda_aire()` con los 120 W; la franja de 230 V sigue cerrada |
| **D-F2** | telemetría de rack **poblada** (`U13`, `U14`) | +4 hilos en R ↔ C; 0x44 y 0x45 dejan de ser opcionales en `check_telemetria.py` |
| **D-F4** | **secuenciador** por ON/OFF, cascada y rack | detector de ventana ×2 en R; `secuencia_budget.py`; paso 2b del bring-up |
| **D-F5** | **Y2 de modo común** por módulo | seis Y2 al chasis en R; §12.4 por leer; entra en `fuga_budget.py` |
| **D-F6** | **crowbar** en los rieles de rack, y solo ahí | SCR por riel de rack; `check_absmax.py` contra los 16,2 V; su prueba en el bring-up |
| **D-F7** | `PS5` = **IRM-45-5** (era IRM-20-5); +5 V de rack **4,0 A declarados** sobre 8 de placa | `calor_budget.py` lo hizo nacer: con la IRM-20-5 el listón del +5 V no existía con ningún venteo (§3). Una referencia menos en R; 87 × 52 mm donde había 52 × 27 |
| **D-F8** (04-09) | `U1` = **LT1963A** (era LM2941) | `margen_budget.py` pasa de −388 a **+330 mV**. Trae la ventana de ESR nueva (0–3 Ω, acepta cerámico) y **se llevó por delante el hilo único del ON/OFF**, que D-F9 devuelve. Deja abierto su máximo absoluto de entrada: **#334** |
| **D-F9** (06-09) | `U2` = **LT3015** `LT3015IT#PBF` (era LM2991) | `margen_budget.py` pasa de −170 a **+536 mV** y sale de HUECO. Cierra el inversor del ON/OFF (**#323**) y abre la ventana del umbral de D-F4 (**#324**, +330 mV). Exige `COUT` = 47 µF **y** `CFF` = 10 nF, y el grado `I`. No mueve `chasis_to220_*` |

**Estas dos filas faltaban.** D-F8 se firmó el 04-09 y vivió sólo en su bloque
de enmiendas: la cabecera decía «D-F1 a D-F8 decididas (§14)» y §14 se paraba
en la D-F7. Se añaden las dos juntas al escribir D-F9.

**La columna «sostenido» de §1 está rellena** (03-09, `calor_budget.py`, con
D-F3 = A y D-F7): 2,0 / 2,0 / 4,0 A de rack y 4,2 A digital con el venteo
mínimo de 22 200 mm². Es una **predicción de modelo**, pesimista a sabiendas
(§6); su testigo es el paso 7 del bring-up, y hasta esa medida el papel dice
«sostenido según modelo». Lo que ese número le exige a otros: el venteo
mínimo al case (#289) y el techo nuevo del digital a `power_budget.py`
(Tarea 5 del plan).

**Lo que sigue sin ser de este papel** (§11): D-R1 (el 1,8 V), el valor del
fusible hasta `fusible_budget.py`, los peines y el PTC de #169, y el mecanismo
del diferencial de la bahía.
