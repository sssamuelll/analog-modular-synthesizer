# HUECOS de D-V2: respuestas y requisitos para selección

Trabajo contra [el papel de fuente v5](2026-09-05-fuente-v5-ladrillo-design.md),
§3 y §9.2, con sus preguntas literales y sus dueños. D-V2 está firmada en
dirección; **este documento no cierra ningún HUECO por sí solo, no firma
decisiones ni autoriza cobre**. Propone moverlos a requisitos verificables o a
decisiones explícitas. No hay ladrillo ni DC-DC elegidos ni sus hojas locales.

En las citas, «papel v5» es el anterior y «papel v4» es
[fuente v4](2026-09-03-fuente-v4-liston-design.md). `ladrillo_budget.py` está en
`hardware/01-power-supply/v5/`; los demás guiones citados, en
`hardware/01-power-supply/v4/`; las hojas, en `docs/reference/datasheets/`.
Se ejecutó `python hardware/01-power-supply/v5/ladrillo_budget.py`: devuelve
**código 2 por HUECOS**, como declara `ladrillo_budget.py:3` y ejecuta
`ladrillo_budget.py:362`. Ningún guion se modifica.

Los valores calculados conservan sus condiciones: **ESTIMADO no equivale a
garantizado**, una corriente de carga no equivale a corriente de fallo y un
máximo absoluto no es un punto de trabajo ni admite sobrepasarlo durante un
tiempo elegido por nosotros.

## H-V2-ENTRADA

**ESTADO: (B) REQUISITO COMPRABLE**

Dueño: fabricante (papel v5 §9.2).

> «¿Qué mínimos y máximos de salida garantiza el ladrillo bajo línea, carga y temperatura, qué ventana admiten los DC-DC para arrancar y para seguir regulando, y qué caídas máximas de cordón, contactos y protecciones permite compatibilizar ambas?» (papel v5 §3).

**Respuesta y requisito.** No se conocen esos extremos ni las ventanas de los
convertidores. El nominal exigible es **24 V** (`ladrillo_budget.py:93`; papel
v5 §9, D-V2). El ladrillo debe garantizar sus extremos a la carga de
H-V2-RESERVA y en todo el intervalo de línea y temperatura que se admita; no
basta el ajuste en vacío. El ambiente de sala de diseño es **45 °C**
(`calor_budget.py:138`); la temperatura de cada DC-DC dentro del chasis debe
salir de su montaje y pérdidas, no confundirse con la de sala.

Para convertirlo en selección comprobable, se denominan `Bmin/Bmax` los
extremos del ladrillo, `Δmax/Δmin` las caídas totales de cordón, contactos y
protecciones, y `Dmin/Dmax` los límites garantizados del DC-DC. Para cada
condición de servicio se exige:

- **Arranque:** `Bmin_arranque − Δmax_arranque ≥ Dmin_arranque` y
  `Bmax_arranque − Δmin_arranque ≤ Dmax_arranque`.
- **Regulación:** `Bmin_régimen − Δmax_régimen ≥ Dmin_regulación` y
  `Bmax_régimen − Δmin_régimen ≤ Dmax_regulación`.
- Por tanto, la caída máxima comprable es
  `Δmax ≤ Bmin − Dmin`, tomando el caso más restrictivo entre arranque y
  régimen. Son las inclusiones de ventanas exigidas en papel v5 §3,
  H-V2-ENTRADA; todavía no tienen extremos numéricos con pieza.

Para una caída resistiva, `Δ = I·R_total + Δ_protecciones(I,T)`. No debe usarse
la corriente nominal para el arranque ni para toda la ventana de entrada.
El único escenario de cable calculado tiene **16 AWG, 2 m y 0,0132 Ω/m**
(`ladrillo_budget.py:339`), **0,0528 Ω de ida y vuelta**, derivados por
`ladrillo_budget.py:175`, y **141 mV a 2,68 A**, resultado de
`ladrillo_budget.py:169`, `ladrillo_budget.py:173` y `ladrillo_budget.py:344`.
Es un escenario sin contactos ni protección; no fija el cable ni una caída
máxima contractual.

El lado de salida del DC-DC sí tiene una restricción numérica derivable:
debe sostener en el pin del prerregulador, mientras se permita regular,
**al menos 14,039752… V en U1 y 13,833770… V de magnitud negativa en U2**
(`margen_budget.py:189`, `margen_budget.py:213`, `margen_budget.py:228`,
`margen_budget.py:397`; derivación en H-V2-SUBTENSION). El nominal crudo
firmado es **15,5 V de magnitud** (`ladrillo_budget.py:107`; papel v5 §5).
La hoja del DC-DC debe garantizar esa entrega después de descontar las
pérdidas y excursiones de H-V2-TRANSITORIOS. **Esto no determina la tensión
mínima del ladrillo:** falta la relación de conversión garantizada de una
topología y una pieza que D-V4 aún no define (papel v5 §9).

**Criterio de aceptación.** En las hojas de candidatos, reunir `output
voltage tolerance`, `line/load regulation`, deriva y reducción de capacidad
con temperatura, aclarando cuáles ya están incluidas en la tolerancia total.
En los DC-DC, comprobar por separado `input voltage range`, arranque,
umbrales UVLO y regulación con carga. Rellenar las inclusiones anteriores
con extremos garantizados, y comprobarlos en el chasis y a la entrada de cada
DC-DC con el cordón completo. Los transitorios se contrastan además con
H-V2-TRANSITORIOS; no se esconden dentro de una ventana de continua.

**Sigue faltando.** Referencias y hojas; extremos de línea y temperatura
admitidos; pérdidas de protección; resistencia completa y comportamiento
térmico del cordón. Dependencias: H-V5-CALIBRE y H-V5-CONECTOR deben caber en
`Δmax`; H-V5-INCOMPATIBLE debe aportar la envolvente de fuentes ajenas que
haya que sobrevivir. Aquí no se elige ninguna de ellas.

## H-V2-SUBTENSION

**ESTADO: (B) REQUISITO COMPRABLE**

Dueño: diseño (papel v5 §9.2). La lógica heredada se puede contestar; los
umbrales y tiempos completos del transporte y del detector todavía no.

> «¿Qué tensión mínima permite arrancar, cuál obliga a inhibir la conversión, con qué histéresis, tolerancia y tiempos, en qué nodo se detectan y cómo se coordinan esas señales con la habilitación de la cascada de D-F4?» (papel v5 §3).

**Respuesta y requisito.** El mínimo para arrancar el DC-DC y su UVLO se
compran en el nodo **entrada del DC-DC después de las protecciones**; no se
deducen del nominal del cordón. La autorización de la cascada se detecta
separadamente en **ambos crudos después del LC, referidos a su masa local**
(papel v4, enmienda inicial sobre D-F4; `secuencia_budget.py:152`). Debe
representar lo que realmente alcanza los pines, incluida la ferrita y
cualquier protección añadida.

El suelo de regulación que el árbol calcula para esos pines es:

| Pin y polaridad | Derivación del suelo; no es un umbral ya elegido |
|---|---|
| `IN(U1)`, positivo | **13,1 + 13,1·(1,246−1,210)/1,210 + 0,55 = 14,039752… V** (`margen_budget.py:189`, `margen_budget.py:213`, `margen_budget.py:228`, `margen_budget.py:397`; `lt1963a-rev-g-2021-02.pdf` p. 5). |
| `IN(U2)`, negativo, expresado en magnitud | **12,9 + 12,9·(1,244−1,220)/1,220 + 0,68 = 13,833770… V** (mismas líneas de `margen_budget.py`; `lt3015-rev-b.pdf` p. 5, fila TO-220/DD-PAK). |

Son las cotas de dropout que el modelo toma a **1,5 A**
(`margen_budget.py:229`), no valores típicos interpolados. La tolerancia del
ajuste final que no cubra la referencia también debe entrar en el cierre.
No se redondean los suelos hacia abajo para especificar una pieza.

El detector comprable debe satisfacer, para cada crudo y con todas sus
tolerancias incluidas:

- `V_off,min ≥ V_necesaria + caída_durante_respuesta`, donde la caída se
  integra durante detección, mando y apagado. Para una pendiente acotada,
  `caída_durante_respuesta ≤ pendiente_máxima·tiempo_total`.
- `V_on,max ≤ V_sano,min` para que una unidad legal pueda arrancar, y
  `V_on > V_off` con histéresis garantizada superior al rizado y error
  variable del punto de sensado. Es el criterio de
  `secuencia_budget.py:159`, `secuencia_budget.py:169` y
  `secuencia_budget.py:182`, añadiendo la caída durante la respuesta que la
  ventana estática no demuestra.
- La autorización común exige **ambos crudos válidos**; si falta cualquiera,
  se inhiben ambos prerreguladores (`secuencia_budget.py:236`). El mando debe
  garantizar apagado en **−0,5 V ≤ SHDN ≤+0,25 V**
  (`lt3015-rev-b.pdf` p. 6; `secuencia_budget.py:108`) y encendido con
  **alto ≥2,0 V** (`secuencia_budget.py:109`). La cota inferior importa:
  LT3015 también admite habilitación negativa; «bajo» sin límite inferior
  no garantiza apagarlo (`lt3015-rev-b.pdf` p. 6). Deben cumplirse además
  sus límites de SHDN respecto de IN (misma hoja p. 2). El techo absoluto
  del SHDN de U1 es **±20 V**, que exige margen y no es el nivel alto a
  adoptar (`lt1963a-rev-g-2021-02.pdf` p. 2). El hilo roto debe caer a
  inhibición, como exige `secuencia_budget.py:329`.

El presupuesto propone **1,0 ms de detección y 0,1 ms de apagado**, ambos
**ESTIMADOS, sin circuito** (`secuencia_budget.py:125`,
`secuencia_budget.py:128`, `secuencia_budget.py:131`,
`secuencia_budget.py:142`). Sirven como objetivos iniciales a verificar; no
son tiempos garantizados de los LT ni una autorización de sobretensión.
La aceptación existente de D-F4 exige **ventana con un riel solo ≤10 ms**
(`check_bringup.py:237`). Eso tampoco permite violar antes el suelo de
regulación o los máximos absolutos.

**Criterio de aceptación.** Hoja y cálculo del detector con umbrales mínimo y
máximo, histéresis, error del divisor/referencia y propagación bajo temperatura;
hoja del DC-DC con UVLO de subida/bajada y arranque. Medir rampas lentas,
caídas rápidas y pérdida individual de cada crudo, registrando ambos pines,
mando y salidas. Verificar las desigualdades anteriores, el límite de
asimetría de **10 ms** (`check_bringup.py:237`) y el hilo abierto. El arranque
del DC-DC debe poder establecer los crudos mientras la cascada está inhibida;
si necesita una carga mínima, esta debe estar documentada y presupuestada.

**Sigue faltando.** UVLO de transporte, circuito y piezas del detector,
histéresis y tiempos garantizados, pendiente de caída, carga mínima, error de
ajuste y temperatura real. La ventana calculada de **14,851 V disponibles**
(`ladrillo_budget.py:319`) conserva supuestos de los IRM y no sustituye esas
garantías. La política que permita volver a arrancar es H-V2-RECUPERACION;
no queda elegida al establecer la lógica de D-F4.

## H-V2-TRANSITORIOS

**ESTADO: (B) REQUISITO COMPRABLE**

Dueño: diseño (papel v5 §9.2).

> «¿Qué tolerancia del crudo en régimen y qué amplitud, polaridad, duración y repetición de transitorios garantiza o admite cada interfaz, bajo qué carga y temperatura, y qué elemento limita lo que finalmente alcanza los pre-reguladores?» (papel v5 §3).

**Respuesta y requisito.** No existe una envolvente garantizada del ladrillo,
entrada del chasis o DC-DC. Sí existe el presupuesto de error que debe
respetar su salida. Desde el crudo nominal de **15,5 V**
(`ladrillo_budget.py:107`), el total de error hacia abajo, caídas de filtro y
protección, rizado y excursión de carga no puede gastar más de:

- **Aproximadamente 1,460248 V en el positivo**, diferencia entre el nominal y el suelo de
  U1 (`ladrillo_budget.py:107`; `margen_budget.py:397`, con constantes
  `margen_budget.py:189`, `margen_budget.py:213`, `margen_budget.py:228`).
- **Aproximadamente 1,666230 V en magnitud del negativo**, diferencia equivalente para U2
  (`ladrillo_budget.py:107`; `margen_budget.py:189`, `margen_budget.py:213`,
  `margen_budget.py:228`, `margen_budget.py:397`).

Además se reserva el margen para la detección de H-V2-SUBTENSION. Estas
cantidades son el presupuesto **total disponible**, no una tolerancia
adicional concedida a cada efecto. La hoja debe acreditar regulación global
línea/carga/temperatura y respuesta dinámica para el reparto simultáneo y
asimétrico de las cargas; se suma solo lo que no esté ya incluido. Para la
desigualdad de aceptación se usa la diferencia algebraica sin redondear,
`V_crudo_nominal − V_necesaria`, no el redondeo mostrado.

El supuesto **±2,5 %** da **15,1125–15,8875 V** antes de otras pérdidas o
derivas (`ladrillo_budget.py:107`, `ladrillo_budget.py:108`,
`ladrillo_budget.py:115`). **No es tolerancia garantizada del DC-DC ni una
envolvente completa de transitorios.** Tampoco se trasladan su frecuencia ni
el coeficiente térmico de los IRM a los candidatos nuevos
(`margen_budget.py:167`, `margen_budget.py:334`).

Los límites de supervivencia locales que el nuevo conjunto debe respetar
simultáneamente incluyen:

| Interfaz expuesta | Límite absoluto documentado y referencia de medida |
|---|---|
| U1 / LT1963A | `IN`, `OUT` y diferencial `IN−OUT`: **±20 V** (`lt1963a-rev-g-2021-02.pdf` p. 2 y p. 6, nota 2). |
| U2 / LT3015 | `IN` y `OUT`: **±33 V**; `OUT−IN`: **−0,3 a +33 V** (`lt3015-rev-b.pdf` p. 2). La nota 10, p. 6, limita también OUT, ADJ y SHDN respecto de IN durante el fallo. |
| LT3045, después de U1 | `IN` y `IN−OUT`: **±22 V**; OUT, OUTS y SET: **−0,3 a +16 V** (`lt3045-rev-d.pdf` p. 2). |
| LT3094, después de U2 | `IN` respecto de GND: **−22 a +0,3 V**; `OUT−IN`: **−0,3 a +22 V** (`lt3094-rev-b.pdf` p. 3). La rama negativa no admite invertir la polaridad por analogía con la positiva. |

No son una garantía de funcionamiento hasta esos extremos ni un permiso de
pulso por encima de ellos. Hay que reservar el error de disparo, la subida
durante la respuesta y el pico debido al montaje. Para U1 lo proporciona la
**protección independiente propuesta en H-V2-CORTO-DCDC**, con interrupción
serie y limitación local. Su elección debe incluir la rama negativa y los
caminos de retorno de energía: al desaparecer un crudo negativo con carga
residual en la salida, cumplir solo el máximo de `IN` no prueba el
diferencial de U2 (`lt3015-rev-b.pdf` p. 2 y p. 6).

Para salida del ladrillo, chasis y entrada del DC-DC se exige una ficha por
evento con amplitud, polaridad, duración, repetición, carga, temperatura y
responsable físico de la limitación. Sus cifras siguen sin derivarse del
árbol. Los eventos son arranque, cambios de carga, pérdida de cada crudo,
corte, recuperación y las maniobras del cordón que se admitan (papel v5 §3).
No se asigna una inmunidad del transporte usando el máximo absoluto de U1.

**Criterio de aceptación.** Hoja de salida y respuesta transitoria del DC-DC,
con condiciones y límites garantizados; verificación de cada evento en todos
los nodos, con las cargas de `ladrillo_budget.py:126` y la temperatura de
diseño. Mientras se declare regulación, se respetan los suelos anteriores;
si se sale de ella, actúa la inhibición, preservando siempre los límites
absolutos y diferenciales. El filtro se vuelve a verificar con el espectro
del candidato: su criterio local es **pico ≤3 dB**
(`rizado_budget.py:162`, `rizado_budget.py:217`), pero pasar ese ensayo no
demuestra limitar un corto de continua.

**Sigue faltando.** Envolventes de transporte y DC-DC, perfiles de carga,
temperaturas, límites térmicos/pulsados de la protección y componentes
pasivos, y esquema que permita evaluar los diferenciales. **H-V5-CALIENTE
debe coincidir con esta envolvente y H-V2-RESERVA**; su eventual autorización
no puede añadir pulsos o repetición que aquí queden sin verificar (papel v5
§9.2).

## H-V2-RESERVA

**ESTADO: (B) REQUISITO COMPRABLE**

Dueño: fabricante (papel v5 §9.2).

> «¿Qué carga capacitiva y perfil de corriente de arranque admite el ladrillo, qué corriente y energía exige la cadena completa con sus cargas, qué tensión mínima conserva durante ese arranque y qué reserva garantizada evita que su limitación y el arranque de los DC-DC se impidan mutuamente?» (papel v5 §3).

**Respuesta y requisito.** No se conocen ni la capacidad admisible del
ladrillo ni el perfil completo de la cadena. La base de dimensionamiento en
régimen es **64,22 W y 2,68 A al nominal de 24 V**, resultado ejecutado de
`ladrillo_budget.py:151`, `ladrillo_budget.py:169` y
`ladrillo_budget.py:93`. **No contiene reserva de arranque** y depende de
rendimientos ESTIMADOS (`ladrillo_budget.py:110`). Es la base del presupuesto
actual, no una potencia máxima certificada de la cadena final.

Para seleccionar candidatos que conserven ese presupuesto, la capacidad
continua garantizada debe cubrir esa base **más las pérdidas y consumos que
falten**, y debe recalcularse con los rendimientos garantizados de las piezas.
El cálculo actual suma las entradas ideales de los DC-DC
(`ladrillo_budget.py:143`, `ladrillo_budget.py:147`,
`ladrillo_budget.py:157`); no suma explícitamente pérdidas del cordón,
contactos o protecciones. Tampoco contabiliza separadamente los consumos
propios de los prerreguladores: asigna a cada crudo **0,650 A**
(`ladrillo_budget.py:136`, `ladrillo_budget.py:138`). Por eso no se transforma
la cifra impresa en una compra cerrada ni se añade un porcentaje arbitrario.

Las cargas con las que debe acreditarse el arranque son:

| Salida | Carga declarada usada por el presupuesto |
|---|---|
| +12 rack y pantalla | **1,050 A a 12 V** (`ladrillo_budget.py:128`; `calor_budget.py:182`). |
| −12 rack | **0,500 A a −12 V** (`ladrillo_budget.py:130`; `calor_budget.py:182`). |
| +5 rack | **0,500 A a 5 V** (`ladrillo_budget.py:132`; `calor_budget.py:182`). |
| +5 digital | **2,895 A a 5 V** (`ladrillo_budget.py:134`; `calor_budget.py:204`). |
| Cada crudo de cascada | **0,650 A**, con nominal de magnitud **15,5 V** (`ladrillo_budget.py:78`, `ladrillo_budget.py:107`, `ladrillo_budget.py:136`, `ladrillo_budget.py:138`); falta cerrar consumos propios. |

Esas corrientes describen régimen. Durante la subida se necesita
`I_salida(t) = I_cargas(t) + C_efectiva(V,T)·dV/dt`, incluyendo carga de
condensadores de los módulos y consumo propio. La hoja debe garantizar el
arranque del DC-DC con esa carga y el ladrillo debe admitir el perfil que
resulte referido a su entrada. No basta sumar corrientes de rieles de
distinta tensión ni trasladar al cordón su capacidad en paralelo.

Ya se puede cuantificar una parte de la energía: si se conserva el filtro
presupuestado, cada crudo tiene **47 µF + 220 µF = 267 µF**
(`rizado_budget.py:145`, `rizado_budget.py:159`,
`rizado_budget.py:522`). Para los filtros de ambos crudos, inicialmente
descargados, `E = Σ C·V²/2` da **64,14675 mJ al nominal de 15,5 V**
(derivado de esas capacidades, `ladrillo_budget.py:107` y las ramas
`ladrillo_budget.py:136`, `ladrillo_budget.py:138`); en el extremo de cálculo
de **15,8875 V**, da **67,39418 mJ** (`ladrillo_budget.py:126`, mismas
capacidades). Es energía almacenada en ese subconjunto, **no energía total
de arranque ni capacidad vista directamente por el ladrillo**. El
condensador de amortiguación carga a través de su resistencia; no se suma al
otro para predecir una corriente instantánea.

Quedan fuera de ese subtotal la entrada de los DC-DC, los demás filtros, la
ferrita y su amortiguación (`rizado_budget.py:171`, `rizado_budget.py:182`),
salidas de prerreguladores (`margen_budget.py:278`,
`rizado_budget.py:205`), reguladores finales, módulos, pantalla y pérdidas.
El consumo de carga durante el arranque añade `∫P_cargas(t)dt`, que no puede
evaluarse sin duración y perfil. No hay un inventario capacitivo completo
de la cadena nueva.

El contrato de compra debe garantizar simultáneamente:

- Carga capacitiva admitida por el ladrillo superior a la carga **efectiva
  de entrada** de la cadena propuesta, bajo la maniobra admitida; perfil
  permitido de corriente y su duración, no solo `rated current`.
- `V_ladrillo,min(t) − Δcordón/contactos/protección(t)` dentro de la ventana
  necesaria para la fase de arranque o regulación del DC-DC, según
  H-V2-ENTRADA y H-V2-SUBTENSION.
- Perfil de limitación y recuperación que permita completar el arranque
  con cargas conectadas. Un candidato que reinicie indefinidamente antes
  de alcanzar sus condiciones de habilitación no cumple, aunque su
  potencia de placa supere el presupuesto estacionario (papel v5 §3,
  H-V2-RESERVA).

**Criterio de aceptación.** Hoja con `maximum capacitive load`, arranque con
carga, limitación mínima/máxima, reducción con temperatura, duración de
sobrecarga y modo de recuperación. Una curva típica o una potencia nominal
sin ese contrato no acredita reserva. Completar inventario y perfil,
contrastar energía/corriente con límites garantizados y ensayar arranque con
las cargas conectadas, tanto descargado como con los residuos admitidos,
midiendo tensión y corriente en las interfaces. El arranque debe llegar a
regulación y no entrar en un ciclo de limitación y reinicio.

**Sigue faltando.** Capacidades efectivas, rampas, cargas dinámicas y
consumos propios; DC-DC y ladrillo; energía, corriente y duración garantizadas
de arranque. **H-V5-CALIENTE debe usar exactamente la capacidad, corriente y
envolvente temporal que se validen aquí y en H-V2-TRANSITORIOS** (papel v5
§9.2). No se da por admitida esa maniobra.

## H-V2-RECUPERACION

**ESTADO: (C) DECISION**

Dueño: Samuel + fabricante (papel v5 §9.2).

> «¿La cadena debe recuperarse automáticamente, reintentar o esperar una intervención, bajo qué condición de tensión y tiempo se autoriza, y en qué estado deben quedar sus rieles y habilitaciones durante la caída, la espera y el rearranque?» (papel v5 §3).

**Respuesta: falta una política que solo Samuel puede elegir.** Debe
especificar a qué causas aplica; una subtensión transitoria y un corto
permanente del DC-DC pueden requerir tratamientos distintos. Las opciones
son las del propio enunciado:

| Opción | Qué compra | Qué cuesta, rastreado | Con qué se choca |
|---|---|---|---|
| Recuperación automática al recuperar condiciones válidas | Regreso al servicio sin intervención tras una caída recuperable. | Cada vuelta exige otro arranque completo y vuelve a consumir la envolvente de energía y repetición que reclaman H-V2-RESERVA y H-V2-TRANSITORIOS (papel v5 §3). No hay coste numérico cerrado. | Una fuente que entra en limitación antes de completar el arranque puede mantener ciclos indefinidos. Volver a tener tensión no demuestra que hayan desaparecido el fallo o los residuos. |
| Reintentos controlados con espera y condición de abandono | Oportunidades de recuperación ante una causa transitoria y un final definido si persiste. | Temporización, criterio de intento y abandono, energía acumulada y comprobación de repetición (papel v5 §3, H-V2-RECUPERACION, H-V2-RESERVA y H-V2-TRANSITORIOS). El árbol no fija intervalo ni cupo. | El ladrillo puede reintentar por su cuenta; su modo nativo no puede reiniciar indebidamente la política local. No se hereda el hiccup de los IRM retirados (papel v4 §3; papel v5 §7). |
| Espera enclavada hasta intervención | Impide nuevas energizaciones por una mera vuelta de la tensión después del evento protegido. | Interrupción de servicio y definición del acto de liberación; conservación o reconstrucción del bloqueo al perder alimentación (papel v5 §3, H-V2-RECUPERACION). | Falta decidir si retirar alimentación libera el bloqueo. Rebote o energía residual no pueden convertir una maniobra no autorizada en liberación; dependencia de H-V5-RECONEXION (papel v5 §3 y §9.2). |

**No se elige ni se recomienda una:** el árbol sostiene la coordinación de
la cascada, pero no prioriza disponibilidad frente a intervención ni fija
qué causas son recuperables. Ninguna opción permite usar el DC-DC averiado
como único elemento que deba desconectarse en H-V2-CORTO-DCDC.

En todas las opciones, cuando la caída invalide una condición de habilitación
deben **inhibirse ambos prerreguladores dentro del tiempo acreditado en
H-V2-SUBTENSION**; durante la espera ambos permanecen inhibidos. Solo se
autoriza la cascada cuando ambos crudos son válidos
(`secuencia_budget.py:236`). El mando común tiene los niveles de
H-V2-SUBTENSION. **Inhibición no significa que los rieles estén descargados**:
se deben declarar su evolución y los caminos de descarga/realimentación
con las cargas mínima y máxima. En particular, la energía residual no puede
violar el límite **OUT−IN ≥−0,3 V** de U2 (`lt3015-rev-b.pdf` p. 2 y p. 6).
Para rack y digital debe declararse también el estado durante cada fase;
su control y protección dependen del reparto aún pendiente de D-V4
(papel v5 §9), sin suponer que SHDN de la cascada los desconecta.

**Criterio de aceptación.** Samuel elige política, causas, condiciones de
abandono o liberación y comportamiento de cada grupo de rieles. Los umbrales
y tiempos elegidos deben caber en H-V2-SUBTENSION, y las hojas deben acreditar
la recuperación y el arranque exigidos. Ensayar caída, espera y rearranque,
con pérdida individual de crudos, fallo persistente y energía residual;
verificar habilitaciones, evolución de rieles y diferenciales. Se mantiene
la aceptación de asimetría **≤10 ms** (`check_bringup.py:237`), sin convertirla
en tiempo permitido de sobretensión.

**Sigue faltando.** La elección, su aplicación por causa, condiciones de
tensión/tiempo, intervalos/cupo o acto de liberación si proceden, piezas y
prueba integrada. **H-V5-RECONEXION debe seguir esa política sin que el
rebote o la carga residual eludan sus condiciones** (papel v5 §9.2). Aquí
solo se transmite esa restricción.

## H-V2-CORTO-DCDC

**ESTADO: (B) REQUISITO COMPRABLE**

Dueño: diseño; corresponde a **#334** (papel v5 §3 y §9.2).

> «¿Qué recorrido eléctrico deja un corto entre entrada y salida del DC-DC, qué tensión, duración y energía alcanzan `IN` de `U1`, y qué elemento independiente limita o interrumpe ese recorrido dentro de los límites documentados, incluidos sus tiempos y tolerancias?» (papel v5 §3).

**Respuesta sobre el recorrido.** En la realización que deja retorno
conductor, el lazo peligroso es:

```text
salida del ladrillo → cordón/contactos/protecciones de entrada
                   → puente de fallo entrada–salida del DC-DC
                   → filtro LC → ferrita → IN(U1)
                   → carga/condensadores/protección local → masa local
                   → retorno conductor hacia el ladrillo
```

Se debe verificar ese retorno en el esquema del candidato. Si existe una
barrera real y una salida flotante, un puente entre terminales puede cambiar
el modo común sin imponer por sí solo toda la tensión diferencial sobre
U1. Eso requiere evidencia de la barrera y de todas las conexiones; el
nombre `ETA_AISLADO` no la proporciona (`ladrillo_budget.py:103`,
`ladrillo_budget.py:49`). D-V4 todavía debe definir la realización (papel v5
§9). **El caso conductor debe protegerse o demostrarse excluido.**

En ese caso, sin protección independiente, ni el LC ni apagar la conmutación
del convertidor ya puenteado interrumpen la continua. Al reducirse la carga,
la caída resistiva también se reduce y `IN(U1)` puede tender a la tensión
transportada. El nominal **24 V** ya supera en **4 V** el máximo **20 V**
positivo de U1 (`ladrillo_budget.py:93`; `check_absmax.py:209`;
`lt1963a-rev-g-2021-02.pdf` p. 2; diferencia derivada). El máximo real del
fallo puede ser mayor: faltan H-V2-ENTRADA y la envolvente admitida en
H-V5-INCOMPATIBLE. Si el ladrillo sigue suministrando, la duración y energía
del fallo **no tienen una cota finita demostrada**.

**Propuesta de diseño para comprar, pendiente de pieza y validación.**
Interrupción serie independiente a la salida del DC-DC **antes del LC**,
con detector propio de sobretensión, y **limitación local entre IN(U1) y su
masa**, después de la ferrita. Al abrir antes del inductor hace falta
**un recorrido independiente de recirculación**, propuesto desde la masa
local hacia el nodo entre interruptor e inductor. En la rama positiva,
debe conducir la corriente inductiva en este lazo al abrir:

```text
masa local → elemento de recirculación → entrada del inductor
           → inductor → condensadores / ferrita y limitador local
           → masa local
```

Se deben acreditar su polaridad, corriente, energía, recuperación y la
tensión que impone al interruptor abierto. El limitador de IN no completa
ese lazo por sí solo. La absorción o recirculación de la rama negativa
requiere su propio recorrido con las polaridades correctas.
El detector vigila el nodo protegido; su
alimentación y su elemento de corte deben sobrevivir a la tensión de fallo
y alcanzar un estado de corte aunque el DC-DC o su control no respondan.
El corte debe bloquear el recorrido real, incluidos diodos internos y
posibles retornos; la limitación local absorbe el frente de tensión y la
energía que quede aguas abajo. Se coordina la inhibición de ambos
prerreguladores con D-F4. Es una función propuesta, **no una referencia
elegida ni una protección ya demostrada**.

La especificación de esa pareja interruptor/limitador exige:

- `V_sano,max < V_disparo,min` y
  `V_disparo,max + subida_hasta_corte + pico_local < 20 V`, con todas las
  tolerancias y error de medida incluidos (límite de
  `lt1963a-rev-g-2021-02.pdf` p. 2). También debe respetarse el diferencial
  **IN−OUT dentro de ±20 V** (misma hoja p. 2 y p. 6). La tensión máxima de
  limitación **a la corriente real del pulso y a temperatura**, no solo la
  tensión nominal de un supresor, debe cumplirlo.
- Tensión soportada por interruptor, detector y elementos situados antes
  del corte superior a la envolvente máxima de transporte/fallo; corriente
  continua suficiente para la cascada y sus consumos propios, sin gastar
  la holgura de H-V2-TRANSITORIOS. Sus caídas y pérdidas vuelven al presupuesto.
- Tiempo máximo de detección, propagación y apertura, área de operación
  segura pulsada, energía admisible del limitador y repetición garantizados
  para **el mismo perfil de fallo**. El tiempo admisible sale de cuánto
  tarda ese perfil en alcanzar el límite del nodo, no de un número tomado
  del rack.

**Energía ya rastreable, con alcance limitado.** El modelo conserva
**22 µH y 47 µF** (`rizado_budget.py:144`, `rizado_budget.py:145`), con rama
de amortiguación de **0,68 Ω y 220 µF** (`rizado_budget.py:158`,
`rizado_budget.py:159`). La ferrita añade **0,05 Ω** de continua, un
condensador local de **100 nF** y otra rama de **2,2 Ω y 2,2 µF**
(`rizado_budget.py:170`, `rizado_budget.py:171`,
`rizado_budget.py:181`, `rizado_budget.py:182`). Los parasíticos son
ESTIMADOS (`rizado_budget.py:219`): aún faltan piezas, capacidad efectiva,
tolerancias, saturación y montaje.

Para el condensador principal, `E=C·V²/2` da **9,400 mJ a 20 V** y
**13,536 mJ a 24 V**, una diferencia de **4,136 mJ**
(`rizado_budget.py:145`; `lt1963a-rev-g-2021-02.pdf` p. 2;
`ladrillo_budget.py:93`; derivación energética). Son energías en ese
condensador, que está antes de la ferrita: **no son energía disipada dentro
de U1 ni energía que U1 tenga permitido absorber**. Tampoco prueban que la
tensión final quede limitada. El subtotal de filtros de H-V2-RESERVA muestra
otra energía almacenada que debe seguirse al abrir el interruptor.

Desde el nominal crudo de **15,5 V**, ese condensador parte de **5,646 mJ**;
hasta **20 V** quedan **3,754 mJ** y una carga `ΔQ=C·ΔV` de **211,5 µC**
(`ladrillo_budget.py:107`; `rizado_budget.py:145`;
`lt1963a-rev-g-2021-02.pdf` p. 2; cálculos con esos valores nominales).
Con corriente neta constante en ese condensador, el intervalo sería
**`t = 211,5 µC / I_neta`** (mismas fuentes). Falta la corriente máxima
que permitiría convertirlo en una cota temporal, y ese intervalo no es el
tiempo de reacción disponible en IN ni parte del umbral real de disparo.
La rama de amortiguación tiene **`Rd·Cd = 149,6 µs`**
(`rizado_budget.py:158`, `rizado_budget.py:159`; producto calculado sin la
ESR estimada de `rizado_budget.py:160`): otra razón para no sumarle su
capacidad instantáneamente al condensador principal.

Para el inductor, **`E_L = 11·I_L[A]² µJ`**, derivado de
`rizado_budget.py:144`. Evaluado a los **0,650 A declarados**, serían
**4,648 µJ** (`ladrillo_budget.py:78`; misma inductancia). La corriente al
cortar puede ser mayor y la inductancia puede cambiar por saturación:
esta evaluación en régimen no dimensiona el absorbedor de fallo.

El tiempo y la energía hasta el corte se cierran con el balance local:

`C_local,ef·dV_IN/dt = I_entrante − I_U1 − I_limitador`

`E_limitador = ∫ V_IN·I_limitador dt`

`E_interruptor = ∫ V_interruptor·I_interruptor dt`

`E_L = L·I_L²/2`

El tiempo total garantizado debe incluir detección, propagación del mando,
apertura y extinción de la corriente por todos los recorridos que alimenten
el pin. Se verifica hasta que termine esa alimentación y después durante
la absorción de la energía residual; no solo hasta que cambie una señal.

Para corriente neta constante y capacidad efectiva constante, el tiempo
de subida entre disparo y límite es `Δt = C_local,ef·ΔV/I_neta`.
Con corriente neta positiva acotada por `I_neta,max` y capacidad no inferior
a `C_local,min`, `C_local,min·ΔV/I_neta,max` es una **cota inferior** del
tiempo hasta el límite; la protección debe actuar antes, incluyendo la
respuesta del limitador y los picos locales que el balance capacitivo no
cubra. Aquí **no se conocen ni I_neta de fallo ni
C_local,ef mínima**, por lo que no puede publicarse un tiempo garantizado
de apertura. Los **47 µF** (`rizado_budget.py:145`) no están directamente
en el pin: entre ellos y el pin está la ferrita; los **220 µF**
(`rizado_budget.py:159`) están detrás de la resistencia de amortiguación.
Sumarlos como un único condensador instantáneo en IN daría un tiempo de
protección ficticio.

La integral debe seguir también la descarga de condensadores aguas abajo,
energía inductiva tras abrir, posible realimentación de salidas y alimentación
del fallo desde condensadores de entrada. No se usa la corriente del cordón
en régimen como corriente máxima de cortocircuito. Tampoco se heredan los
**10 µs ESTIMADOS del crowbar de rack** (`check_absmax.py:100`) ni los
**1,0 ms y 0,1 ms ESTIMADOS de D-F4** (`secuencia_budget.py:128`,
`secuencia_budget.py:131`). Apagar SHDN de U1 no elimina tensión de su pin
IN, y su hoja no publica un tiempo permitido por encima de su máximo
(`lt1963a-rev-g-2021-02.pdf` p. 2 y p. 6).

**Criterio de aceptación.** Esquema con terminales del puente de fallo,
retornos y barreras explícitos; hojas locales del interruptor, detector,
limitador y pasivos, con límites garantizados y cálculo de las integrales
anteriores. Ensayar el puente físico que represente el fallo, con el control
del DC-DC incapaz de ayudar, al extremo alto de la fuente admitida y con
energía residual/cargas extremas. Registrar IN, OUT, masa local, SHDN,
corrientes y tiempo real de apertura. El pico más tolerancia y error de
medida debe quedar **por debajo de 20 V** y deben cumplirse simultáneamente
los diferenciales (`lt1963a-rev-g-2021-02.pdf` p. 2 y p. 6), sin exceder
energía, temperatura o área de operación segura de la protección. La
repetición debe obedecer H-V2-RECUPERACION.

**Sigue faltando.** Topología y retornos de D-V4; envolvente máxima y
corriente/energía de fallo de la fuente; piezas de protección y pasivos;
umbral, tolerancia y tiempo garantizados; cálculo dinámico y ensayo. La
propuesta debe verificar también U2 y los límites de H-V2-TRANSITORIOS,
sin trasladar una limitación positiva a la rama negativa. **#334 sigue
abierto** (papel v5 §9).

## H-V2-AISLAMIENTO

**ESTADO: (B) REQUISITO COMPRABLE**

Dueño: fabricante (papel v5 §9.2). El requisito documental es comprable;
sus límites eléctricos de aceptación todavía están incompletos.

> «¿Qué clase de protección, aislamiento, corriente de fuga, relación entre salida DC y PE, y protecciones con su modo de recuperación acredita la referencia propuesta, en qué hoja o certificado y bajo qué condiciones?» (papel v5 §3).

**Respuesta y requisito.** No hay referencia propuesta que acredite esos
datos. Lo firmado exige una **pieza AC-DC de catálogo, certificada y fuera
de la caja** (papel v5 §3 y §9, D-V1). Para aceptar un candidato, su hoja y
certificado deben identificar la referencia exacta y aportar:

- Clase de protección, norma y alcance de la certificación, condiciones de
  montaje y servicio a las que se aplica.
- Aislamiento entre entrada y salida, y respecto de PE cuando exista:
  tensión, tipo y duración de ensayo, y condiciones ambientales aplicables.
- Corriente de fuga máxima, con tensión/frecuencia de red, carga, método y
  condiciones; relación eléctrica explícita entre cada terminal DC y PE.
- Declaración de protecciones presentes y ausentes frente a corto,
  sobrecarga, sobretensión y temperatura; para las presentes, sus límites,
  tiempos y recuperación. Su cobertura se contrasta con
  H-V2-ENTRADA, H-V2-RESERVA, H-V2-RECUPERACION y H-V2-CORTO-DCDC
  (papel v5 §3, contrato de D-V2).

**No se puede fijar aquí una clase, tensión de aislamiento o fuga admisible
con un número del sustituto.** La **clase II, 4,2 kVac y fuga <0,25 mA a
277 Vac** describen los IRM retirados (papel v4 §3, características
compartidas). Los **3,5 mA** son solo un **VALOR DE TRABAJO** con la norma
ausente (`fuga_budget.py:95`), no un límite normativo acreditado para comprar
el ladrillo nuevo. No se heredan esas cifras ni se elige por inferencia una
salida flotante o referida a PE.

La restricción numérica del conjunto que sí permanece es **>1 MΩ entre
GNDA y GNDD dentro de la fuente** (papel v5 §3, enmienda D-V5; papel v4
§9.1). Limita la realización de D-V4 y sus conexiones; no es una prueba de
aislamiento de seguridad del ladrillo ni demuestra su clase. Su PE, si lo
tiene, tampoco demuestra un camino hasta el chasis a través del cordón
(papel v5 §3).

**Criterio de aceptación.** Correspondencia entre referencia, hoja y
certificado local, condiciones de uso y montaje. Confrontar cada dato con
los límites del sistema una vez adoptados; una certificación sin esa
comparación no basta. Entregar a H-V5-PE la relación salida–PE y la fuga
documentada, para que su solución de modo común preserve la separación
GNDD exigida. Esta respuesta no decide la unión retorno–chasis ni el relevo
de D-F5.

**Sigue faltando.** Candidato, hoja/certificado y límites aceptados de
clase, aislamiento y fuga para el sistema. No puede aceptarse una pieza
solo por contestar la pregunta descriptiva del fabricante. La relación
con chasis depende de H-V5-PE, y la recuperación de la decisión de Samuel.

## Estado final propuesto

| HUECO | Estado | Qué falta |
|---|---|---|
| H-V2-ENTRADA | **(B) REQUISITO COMPRABLE** | Extremos garantizados de ladrillo/DC-DC, condiciones de servicio y caída completa del cordón/protección. |
| H-V2-SUBTENSION | **(B) REQUISITO COMPRABLE** | UVLO de transporte y detector con umbrales, histéresis y tiempos garantizados; prueba de D-F4. |
| H-V2-TRANSITORIOS | **(B) REQUISITO COMPRABLE** | Envolventes por nodo, carga y temperatura; protección y coincidencia con H-V5-CALIENTE. |
| H-V2-RESERVA | **(B) REQUISITO COMPRABLE** | Inventario completo, perfiles de arranque y garantía de que fuente y DC-DC completan el arranque cargados. |
| H-V2-RECUPERACION | **(C) DECISION** | Política de Samuel por causa, condiciones temporales/eléctricas, estados de rieles y compatibilidad con las piezas. |
| H-V2-CORTO-DCDC | **(B) REQUISITO COMPRABLE** | Recorrido real, protección independiente con pieza, corriente/energía/tiempo máximos y ensayo; #334 pendiente. |
| H-V2-AISLAMIENTO | **(B) REQUISITO COMPRABLE** | Límites de aceptación del sistema, candidato y evidencia documental compatible con H-V5-PE. |
