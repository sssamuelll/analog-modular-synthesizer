# D-V5: resolución propuesta de los HUECOS del cordón

Documento de trabajo contra [el papel de la fuente v5](2026-09-05-fuente-v5-ladrillo-design.md), §3 y §9.2. D-V5 está firmada en dirección; sus HUECOS siguen siendo condición de fabricación (papel v5 §9). **Este documento no cierra ningún HUECO por sí solo: los mueve de estado para su integración. No firma decisiones ni autoriza cobre.**

En las citas, **papel v5** designa el documento anterior; **papel v4**, [fuente-v4-liston](2026-09-03-fuente-v4-liston-design.md); **`ladrillo_budget.py`**, [el guion de presupuesto](../../../hardware/01-power-supply/v5/ladrillo_budget.py). Se ejecutó ese guion y terminó con el código **2** previsto (`ladrillo_budget.py:362`). Se conservan sus resultados y sus límites. No hay pareja de conectores ni cable elegidos, ni sus hojas locales. Los requisitos de estado B que dependen de esas hojas o de otro HUECO quedan expresamente incompletos; no equivalen a una orden de compra lista para emitir.

## H-V5-CONECTOR

**ESTADO: (B) REQUISITO COMPRABLE**

**Dueño:** diseño (papel v5 §9.2).

**Pregunta exacta:** «¿Qué pareja de conectores se elige para ladrillo y chasis, qué contacto lleva alimentación y cuál retorno, cómo se identifica esa polaridad y qué hoja local acredita sus límites eléctricos y su resistencia de contacto?»

**Respuesta y especificación de compra.** No se puede nombrar la pareja ni asignar números de contacto sin piezas. La oferta debe identificar ambas mitades compatibles, sus terminaciones y el plano de contactos visto desde un lado declarado. Debe documentar el recorrido de alimentación y retorno y su identificación física, coincidente en ladrillo, cordón y chasis. La dirección firmada transporta alimentación y retorno, sin PE separado (papel v5 §3 y §9, D-V5); no obliga a una geometría comercial concreta.

| Requisito para cualquier candidato | Evidencia que debe aportar su hoja local |
|---|---|
| Servicio a **24 V DC nominales** (`ladrillo_budget.py:93`; papel v5 §9, D-V2). Es una condición necesaria, no la tensión máxima de selección. | Tensión admisible en DC y condiciones de uso que cubran también la salida máxima de `H-V2-ENTRADA` y las solicitaciones admitidas por `H-V2-TRANSITORIOS` y `H-V5-INCOMPATIBLE`. Un dato solo en AC no acredita ese servicio. |
| Cada recorrido de alimentación y de retorno debe conducir al menos los **2,68 A** del presupuesto estacionario nominal (`ladrillo_budget.py:169`, salida impresa en `:297`). | Corriente admisible con el cable, contactos cargados, montaje y temperatura de la aplicación. Si hay contactos en paralelo, debe acreditarse la capacidad y el reparto para la configuración autorizada por el fabricante. Ese presupuesto no acredita el máximo a entrada baja ni arranque o fallo (papel v5 §3, H-V2-RESERVA). |
| La resistencia máxima equivalente de los contactos y terminaciones de ida y retorno debe caber en el saldo que deja el cable dentro de `R_total_adm`, definido en H-V5-CALIBRE (derivación del papel v5 §3, H-V2-ENTRADA y H-V5-CALIBRE). | Resistencia máxima por contacto o por pareja acoplada, con definición del punto de medida y de qué incluye. Se suman las contribuciones en serie y se acredita la equivalente de cualquier grupo en paralelo, sin confundir una pareja con un contacto ni usar una resistencia típica como máximo. |
| La pareja debe cumplir la retención y las maniobras que finalmente se admitan (papel v5 §3, H-V5-RETENCION y H-V5-CALIENTE). | Datos mecánicos y, si se admite conexión energizada, capacidad documentada para esa maniobra con la carga real. La corriente nominal de conducción no prueba capacidad de conexión. |

**Criterio de aceptación.** Referencias y hojas locales de las mitades y terminaciones; plano de polaridad sin ambigüedad; comprobación de continuidad desde el ladrillo hasta la entrada del chasis; resistencia máxima del conjunto compatible con H-V5-CALIBRE; verificación de corriente y temperatura en el montaje previsto. Solo se acepta la pareja cuando las envolventes completas, no únicamente el nominal, quedan dentro de sus garantías.

**Sigue faltando:** referencias, asignación e identificación de contactos, hojas, resistencia máxima, condiciones térmicas y mecánicas, y límites de las interfaces dependientes. Ningún diámetro, corriente comercial ni polaridad de un conector genérico queda elegido aquí.

## H-V5-RETENCION

**ESTADO: (B) REQUISITO COMPRABLE**

**Dueño:** diseño (papel v5 §9.2).

**Pregunta exacta:** «¿Qué retención y alivio de tracción se exigen al conjunto, bajo qué esfuerzo se verifican y qué condición de aceptación debe cumplir?»

**Respuesta y especificación de compra, todavía sin cuantificar.** Se exige acreditar por separado la retención de la pareja acoplada y el alivio de tracción de las terminaciones, incluido el anclaje al chasis. La carga mecánica de ensayo debe llegar al sistema de sujeción previsto sin arrancar terminaciones, dañar aislamiento ni producir aperturas o cambios de resistencia que incumplan H-V5-CONECTOR y H-V5-CALIBRE. Es la traducción verificable de la sujeción del **conjunto** exigida por el papel v5 §3, H-V5-RETENCION; una ficha del conector sin su montaje no la acredita.

**No hay un esfuerzo numérico derivable para este cordón.** Faltan la fuerza, dirección de aplicación, duración, repetición y condición de uso que el ensayo representa. La resistencia eléctrica del cable no proporciona esos datos. Tampoco se deriva del papel v5 §3 si se exige enclavamiento, retención por fricción o liberación deliberada ante un tirón. No se asigna una fuerza arbitraria ni se convierte un ensayo del arnés interior de otra versión en requisito del cordón exterior.

La petición al proveedor debe exigir la fuerza de retención garantizada, las condiciones del ensayo, el cable y las terminaciones compatibles y el alivio de tracción aplicable al montaje. Esos datos permiten comparar candidatos **después** de que diseño declare la solicitación de servicio; no corresponde adoptar como necesidad del instrumento la fuerza que casualmente publique un proveedor.

**Criterio de aceptación.** Antes de ensayar, diseño deja registrados la solicitación y el resultado exigido. Con el conjunto definitivo se verifica que no haya liberación dentro de la carga de retención declarada, extracción de conductores, daño del aislamiento ni pérdida de continuidad; después se repiten polaridad y resistencia del conjunto contra su especificación. Si se decide una liberación intencional, su condición y el comportamiento eléctrico posterior tienen que concordar con H-V5-RECONEXION (papel v5 §3).

**Sigue faltando:** definición mecánica de servicio, esfuerzo y protocolo cuantificados, mecanismo y piezas. Este B contiene un requisito parcial; **no puede avanzar a aceptación solo comprando una pieza**. La definición del esfuerzo sigue siendo trabajo de diseño. Si para definirlo hace falta que Samuel elija entre impedir la desconexión y permitirla ante un tirón, esa preferencia se presenta antes de fijar el mecanismo; aquí no se toma.

## H-V5-CALIBRE

**ESTADO: (B) REQUISITO COMPRABLE**

**Dueño:** diseño (papel v5 §9.2).

**Pregunta exacta:** «¿Qué calibre, longitud máxima y resistencia total admisible se adoptan para el cordón completo, incluidos conectores y terminaciones, y qué corriente y temperatura debe soportar en uso, arranque y hasta el corte por fallo?»

**Respuesta y especificación de compra.** Se conserva, sin recalcularla, la caída de **141 mV con 16 AWG y 2 m**, para los **2,68 A** del presupuesto (`ladrillo_budget.py:173`, escenario `:339` y `:341`, corriente `:169`; papel v5 §3). El guion usa **0,0132 Ω/m por conductor** (`ladrillo_budget.py:339`). Su resistencia de bucle es **52,8 mΩ**, derivada de ida y vuelta y de la longitud de ese escenario (`ladrillo_budget.py:175`, `:339`, `:341`). **Esa resistencia corresponde solo a los conductores del escenario; no es un máximo garantizado del cable comprado ni del cordón completo.** El guion no especifica una temperatura o tolerancia para esa resistencia (papel v5 §3, enmienda D-V5; `ladrillo_budget.py:173` y `:339`).

El criterio vinculante propuesto para integración es el siguiente: **cualquier calibre y longitud que se documenten deben cumplir la resistencia total admisible de la ventana de entrada, incluyendo contactos y terminaciones, a las temperaturas y corrientes admitidas**. Se adopta una restricción, no un techo numérico inventado ni una longitud de uso no firmada.

Definiciones del reparto eléctrico exigido por el papel v5 §3, H-V2-ENTRADA:

- `R_total = R_ida + R_retorno + R_contactos,eq + R_terminaciones,eq`: bucle resistivo completo desde la salida del ladrillo hasta la entrada del chasis. Las contribuciones equivalentes incluyen todos los contactos y terminaciones de ambos recorridos según su conexión real. La resistencia de una terminación se cuenta una sola vez, aunque su hoja la incluya en la del contacto.
- Para cada condición admitida `q`, `V_L,min(q)` es la salida mínima garantizada del ladrillo; `V_D,min(q)`, la entrada mínima necesaria del DC-DC para ese estado; `ΔV_P,max(q)`, la caída máxima desde la entrada del chasis hasta el DC-DC, incluidas protecciones y sus interconexiones. Los extremos de tensión proceden de **H-V2-ENTRADA**, no se contestan aquí.
- `I_max(q)` es la corriente máxima por el cordón en esa condición. El estado de arranque y su perfil vienen de **H-V2-RESERVA**. `q` distingue arranque de regulación, carga, temperatura y tolerancias; no sustituye una condición por otra.

Para condiciones con corriente de alimentación positiva, se exige esta cota conservadora:

```text
R_total_adm = mínimo sobre q de:
    [V_L,min(q) − V_D,min(q) − ΔV_P,max(q)] / I_max(q)

R_total,máx garantizada en servicio ≤ R_total_adm
```

Es un despeje de la compatibilidad de ventanas de **papel v5 §3, H-V2-ENTRADA**, incorporando el bucle completo de H-V5-CALIBRE. Se toma el mínimo sobre estados compatibles con la alimentación y sobre sus condiciones declaradas; los estados deshabilitados no se tratan como estados que deban regular. Si no queda saldo positivo para las caídas, la pareja ladrillo/conversión/protecciones no admite ese cordón: elegir un AWG por nombre no resuelve la incompatibilidad.

También hay que cumplir el extremo superior de la ventana con la salida máxima y las caídas mínimas reales. **La resistencia del cable no se acepta como protección de sobretensión**: al reducirse la carga se reduce su caída. Los transitorios inductivos y el rebote se contrastan por separado con H-V2-TRANSITORIOS y H-V5-CALIENTE; la ecuación resistiva no los modela (papel v5 §3).

Para comparar un candidato con el escenario conservado, el saldo para contactos y terminaciones es `R_total_adm − R_conductores,máx`. Los **52,8 mΩ** solo sirven como referencia del cálculo del escenario (`ladrillo_budget.py:175`, `:339`, `:341`); se sustituyen por el máximo acreditado del cable a su longitud y temperatura. Adoptarlos como techo del **conjunto** dejaría sin presupuesto explícito a contactos y terminaciones, y el papel no respalda esa adopción (papel v5 §3, enmienda D-V5).

**Corriente y temperatura.** La compra debe cubrir, como mínimo, los **2,68 A** estacionarios al nominal del presupuesto (`ladrillo_budget.py:169`), y además la corriente de funcionamiento en toda la ventana, el perfil de arranque de H-V2-RESERVA y la solicitación hasta el corte o la limitación sostenible de H-V5-CORTO. No se infiere un fusible ni una corriente de disparo de ese nominal. Existe un antecedente de ambiente de cálculo de **45 °C** (`hardware/01-power-supply/v4/calor_budget.py:137` y `:138`); no es la temperatura máxima del conductor o del contacto. Faltan el montaje de la entrada, su ambiente local, el autocalentamiento y las garantías térmicas de las piezas. No se hereda como temperatura del cable la temperatura de un semiconductor o del recinto retirado.

**Criterio de aceptación.** Documentar calibre y longitud máxima de la referencia ofrecida, resistencia máxima de cada conductor, contactos y terminaciones, y condiciones térmicas. Medir el bucle completo, contrastarlo con `R_total_adm` y verificar las tensiones en la entrada de los DC-DC a las condiciones admitidas. Comprobar temperatura y continuidad con la carga de servicio, y soportabilidad frente al arranque y fallo declarados. La suma de hojas y la prueba del conjunto deben satisfacer la misma cota; una medida a ambiente sin tolerancias no reemplaza el máximo en servicio.

**Sigue faltando:** ventana de H-V2-ENTRADA, caídas de protecciones, corriente máxima y arranque, temperatura local, referencias y longitud de uso. Sin esos datos **no se puede dar un valor numérico de `R_total_adm` ni adoptar definitivamente un calibre o longitud**. La resistencia queda vinculada funcionalmente; el escenario conservado no se convierte en una elección encubierta.

## H-V5-INVERSION

**ESTADO: (C) DECISION**

**Dueño:** diseño (papel v5 §9.2); el comportamiento exigido contiene una política todavía no tomada (papel v5 §3, decisiones pendientes). Se presenta a Samuel sin reasignar la ingeniería.

**Pregunta exacta:** «¿Qué debe ocurrir al aplicar polaridad inversa, qué tensión y duración debe soportar el conjunto, qué elemento responde y cómo se recupera al corregirla?»

**Respuesta:** el árbol no elige el comportamiento ni un elemento que lo garantice. Estas alternativas son políticas propuestas para decidir, no capacidades ya acreditadas. Primero hay que decidir si se cubre la inversión. Si se cubre, su amplitud y duración deben acordarse con H-V5-INCOMPATIBLE antes de seleccionar protección (papel v5 §3).

| Opción para Samuel | Qué compra | Qué cuesta, con rastro | Con qué se choca |
|---|---|---|---|
| Excluir la aplicación inversa del alcance garantizado. | Acota la garantía a la polaridad que se documente. | Exige identificar la polaridad y declarar la exclusión; queda sin promesa de supervivencia frente a una conexión inversa (papel v5 §3, H-V5-CONECTOR e H-V5-INCOMPATIBLE). | No puede coexistir con una cobertura de adaptadores invertidos que exija supervivencia. El marcado o la orientación mecánica no proporcionan esa garantía eléctrica. |
| Bloquear la polaridad inversa y permitir recuperación al corregirla, cuando la cadena vuelva a autorizar el arranque. | Recuperación sin una intervención adicional específica por inversión. | Un elemento físico que cubra la inversión y una prueba de corrección con energía residual; su caída consume saldo de entrada (papel v5 §3, H-V5-INVERSION, H-V5-RECONEXION y H-V2-ENTRADA). No hay pieza para cuantificar coste o pérdida. | Solo es compatible si H-V2-RECUPERACION permite esa recuperación. Corregir la polaridad por sí solo no prueba condiciones de arranque válidas. |
| Bloquear la polaridad inversa y mantener inhibición hasta una intervención explícita después de corregirla. | Evita un rearranque no solicitado tras ese fallo. | Añade la intervención del usuario y la realización/verificación del estado de inhibición, también al desaparecer la alimentación (papel v5 §3, H-V5-INVERSION y H-V2-RECUPERACION). El árbol no cuantifica su coste físico. | Requiere que la política común de recuperación contemple ese rearme. No puede introducirse como política paralela que contradiga H-V5-RECONEXION. |

No se recomienda una opción: el árbol no acredita una preferencia de uso. Si se cubre la inversión, la forma completa de la respuesta será: incompatibilidad cubierta, amplitud y duración en el nodo de entrada, estado de rieles, referencia y ubicación del elemento que bloquea, límites de las piezas todavía expuestas y condición de recuperación. Si se excluye, la respuesta declara esa ausencia de garantía y su coherencia con H-V5-INCOMPATIBLE. Una polaridad marcada o un acoplamiento orientado ayudan a identificar la conexión, pero no demuestran supervivencia eléctrica frente a un adaptador cableado al revés (papel v5 §3, H-V5-CONECTOR e H-V5-INCOMPATIBLE).

**Criterio de aceptación.** Si se cubre la inversión: política elegida y envolvente documentada; ensayo de inversión y de corrección a sus extremos, verificando entradas, rieles y habilitaciones, sin rebasar límites acreditados de ninguna pieza expuesta. El resultado debe coincidir con H-V2-RECUPERACION y H-V5-RECONEXION. Si se excluye: comprobar identificación y declaración del alcance, sin dar por ensayada ni garantizada la supervivencia.

**Sigue faltando:** decisión de alcance y, si se cubre la inversión, duración, pieza, límites y ensayo. Ni el nominal de transporte ni el máximo absoluto de un regulador de la cascada fijan por sí solos la supervivencia de la entrada del chasis (papel v5 §3, distinción de nodos).

## H-V5-CALIENTE

**ESTADO: (C) DECISION**

**Dueño:** diseño (papel v5 §9.2). La admisión de la maniobra es una política pendiente; sus límites son trabajo de diseño y evidencia de fabricante.

**Pregunta exacta:** «¿Se admite conectar el cordón con el ladrillo energizado y, si se admite, cuáles son los límites garantizados de corriente de entrada y transitorio, qué carga capacitiva admite el ladrillo y cómo deben comportarse los rieles durante la conexión?»

**Respuesta en su forma compatible con D-V2.** No se admite ni se prohíbe la maniobra por inferencia de la firma. Hay que elegir entre estas opciones (papel v5 §3, H-V5-CALIENTE y §9.2):

| Opción para Samuel | Qué compra | Qué cuesta, con rastro | Con qué se choca |
|---|---|---|---|
| Admitir la conexión con el ladrillo energizado dentro de una envolvente declarada. | Permite conectar el instrumento sin desenergizar previamente el ladrillo. | Acreditar la pareja para conectar esa carga, la corriente de entrada, la carga capacitiva y los transitorios; realizar la limitación que resulte necesaria (papel v5 §3, H-V5-CALIENTE, H-V2-RESERVA y H-V2-TRANSITORIOS). Faltan piezas para cuantificar el coste. | No puede exceder la reserva admitida del ladrillo ni la envolvente de ninguna interfaz. La capacidad de conducir del conector no demuestra capacidad para esta maniobra. |
| Exigir acoplar el cordón con el ladrillo desenergizado y energizarlo después. | Restringe la maniobra normal y evita prometer conexión energizada como prestación. | Añade ese paso de uso; sigue exigiendo demostrar el arranque con las cargas conectadas (papel v5 §3, H-V2-RESERVA). | No resuelve la energía residual ni el rebote. Tampoco decide la supervivencia ante una conexión energizada accidental: debe quedar expresamente cubierta o excluida, sin vender la instrucción como protección física. |

No hay recomendación sostenida por el árbol. **No se fija aquí corriente de pico, capacitancia ni tiempo.** Si se admite la maniobra, la respuesta debe declarar el estado inicial del ladrillo y de la caja, carga capacitiva efectiva, perfil de corriente, extremos de tensión por nodo y comportamiento de rieles y habilitaciones. La corriente y la capacitancia deben caber en **H-V2-RESERVA**; amplitud, polaridad, duración y repetición de la perturbación deben caber en **H-V2-TRANSITORIOS**, con la misma carga, temperatura y puntos de medida (papel v5 §3 y §9.2).

La cascada debe mantener la coordinación de D-F4: habilitar sus ramas juntas cuando corresponda y deshabilitarlas juntas al faltar la condición válida; la prueba de cortar la señal de habilitación sigue vigente (papel v4 §4.2 y enmienda D-F9, «Lo que cierra»; papel v5 §7). Esto no equivale a prometer un tiempo de subida o un desfase máximo no documentado. Los estados concretos de los demás rieles y los tiempos se heredan del contrato común de D-V2 y de su realización en D-V4.

**Criterio de aceptación.** Elegida la política, ensayar la maniobra admitida con la pareja y la carga reales, incluyendo estados iniciales, condiciones extremas y rebote. Superponer las formas de onda medidas a las envolventes de H-V2-RESERVA y H-V2-TRANSITORIOS, y verificar el estado de las habilitaciones. Si se exige conexión desenergizada, acreditar igualmente el arranque posterior y declarar el alcance de la maniobra accidental.

**Sigue faltando:** política de uso, alcance accidental, piezas y envolventes de D-V2. Este bloque entrega la forma y las condiciones de compatibilidad; no contesta esos HUECOS ajenos.

## H-V5-RECONEXION

**ESTADO: (C) DECISION**

**Dueño:** diseño (papel v5 §9.2), **dependiente de la decisión de Samuel en H-V2-RECUPERACION**. No es otra elección independiente.

**Pregunta exacta:** «¿Qué debe ocurrir al desconectar y reconectar con energía residual en la caja o rebote de contactos, qué condiciones habilitan el rearranque y qué límites temporales y eléctricos lo verifican?»

**Respuesta condicionada.** Se aplicará la política que se elija en H-V2-RECUPERACION, también cuando la caída proceda del cordón. Las alternativas siguientes solo explican sus consecuencias en esta interfaz; **no eligen ni resuelven H-V2-RECUPERACION** (papel v5 §3 y §9.2).

| Si H-V2-RECUPERACION elige… | Qué compra en el cordón | Qué cuesta, con rastro | Con qué se choca |
|---|---|---|---|
| Recuperación automática cuando vuelvan las condiciones válidas. | Reconectar puede restablecer el servicio sin otro gesto. | Acreditar que la detección de entrada válida y la energía residual no generen habilitaciones espurias (papel v5 §3, H-V5-RECONEXION y H-V2-SUBTENSION). | El rebote no puede confundirse con un permiso estable. Se conserva D-F4 y la envolvente de arranque, no se la sustituye por «volvió el contacto». |
| Reintentos gobernados por una política declarada. | Ofrece oportunidades de rearranque ante una caída transitoria. | Definir y verificar las condiciones de cada intento, de espera y de abandono; acreditar su repetición y energía acumulada (papel v5 §3, H-V2-RECUPERACION, H-V2-TRANSITORIOS y H-V2-RESERVA). | Los reintentos de la cadena y los del ladrillo no pueden impedirse mutuamente; tampoco puede autorizarse un intento por cada rebote sin demostrar compatibilidad. |
| Espera de intervención explícita. | Reconectar solo ordena un rearranque si la política heredada identifica y acredita esa maniobra como intervención válida. | Requiere reconocer la intervención y mantener la inhibición hasta entonces durante caída, reconexión y espera (papel v5 §3, H-V2-RECUPERACION). | La pérdida y recuperación del contacto no deben borrar el requisito de intervención de una forma contraria a la política elegida. |

No se recomienda una política desde D-V5. Para cada alternativa elegida, la respuesta completa debe especificar: estado de los rieles y habilitaciones al abrirse el contacto; energía residual admitida y posibles caminos de realimentación hacia la entrada; condición para reconocer una reconexión válida; condición de habilitación; tiempos, histéresis y repetición tolerada. Todos esos parámetros deben venir del contrato común de recuperación y sus envolventes, con sus nodos de detección (papel v5 §3, H-V2-RECUPERACION, H-V2-SUBTENSION y H-V5-RECONEXION).

**Criterio de aceptación.** Aplicar desconexión, reconexión y rebote con los estados de carga residual que declare el contrato; registrar entrada, rieles y habilitaciones. La secuencia debe corresponder exactamente a la política de H-V2-RECUPERACION, conservar D-F4 (papel v4 §4.2 y enmienda D-F9) y permanecer dentro de H-V2-TRANSITORIOS y H-V2-RESERVA. Faltan sus límites: no se fija aquí un tiempo de descarga, intervalo de reintento o umbral de rearranque.

**Sigue faltando:** la política ajena y sus parámetros, carga almacenada, caminos físicos de descarga o realimentación, realización y ensayo. No se heredan tiempos ni modos de recuperación de los módulos de red retirados.

## H-V5-CORTO

**ESTADO: (B) REQUISITO COMPRABLE**

**Dueño:** diseño (papel v5 §9.2).

**Pregunta exacta:** «¿Qué debe ocurrir ante un corto entre los conductores o hacia el chasis, qué elemento limita o interrumpe, cuáles son sus límites de corriente y duración y cómo se recupera después del corto?»

**Respuesta y especificación de compra.** Ante el corto cubierto, el conjunto debe quedar dentro de las envolventes de cable, contactos, terminaciones y piezas expuestas hasta la interrupción, o soportar de manera sostenida el régimen limitado si no hay interrupción. **No hay un elemento nombrado ni una corriente o duración de corte acreditadas.** Sí queda fijada por la pregunta la obligación de cubrir todo el tramo expuesto, incluida la parte anterior a las protecciones de la caja (papel v5 §3, H-V5-CORTO).

| Fallo que debe cubrir la evidencia | Requisito de ubicación y de recorrido |
|---|---|
| Corto alimentación–retorno en el cordón, junto al ladrillo o junto al chasis. | La limitación debe actuar desde la fuente del fallo: protección acreditada del ladrillo o elemento interpuesto antes del tramo protegido. Un elemento solo después del cordón deja ese corto fuera de su recorrido de corte (papel v5 §3, H-V5-CORTO). |
| Corto de alimentación al chasis. | Dibujar el lazo de falta usando las relaciones reales de H-V5-PE y D-V4. Sin ese mapa no se conoce la corriente disponible ni se demuestra que una protección dispare (papel v5 §3, H-V5-CORTO y H-V5-PE). |
| Corto del retorno al chasis. | Comprobar si crea una unión nueva, altera el retorno de modo común o puentea una separación exigida. Aunque no provoque sobrecorriente, debe evaluarse contra H-V5-PE; no se declara inocuo por llamarse retorno (papel v5 §3). |

Además de la contribución del ladrillo, debe trazarse la descarga desde la caja hacia el corto si la realización permite ese recorrido. La energía residual puede alimentar el fallo aunque el ladrillo haya limitado o interrumpido su aportación. Su perfil se incorpora a la solicitación del tramo afectado y al elemento físico que lo protege; no se presupone un bloqueo de corriente inversa todavía sin pieza (derivación de papel v5 §3, H-V5-RECONEXION y H-V5-CORTO).

La cadena elegida debe mantener el servicio de **24 V nominales** y los **2,68 A** estacionarios presupuestados (`ladrillo_budget.py:93` y `:169`), además de la operación completa y el arranque que entregue D-V2. Esos números **no son una corriente de disparo, un máximo de corto ni una curva de protección** (papel v5 §3, H-V2-RESERVA).

La documentación de compra debe aportar la corriente de cortocircuito disponible, su evolución y modo de limitación; el tiempo máximo de actuación y su dispersión; y la recuperación acreditada del ladrillo. Si se añade un elemento de corte, su hoja debe cubrir tensión DC, corriente de interrupción disponible y solicitación de paso. La documentación de cable y contactos debe acreditar que soportan ese perfil. Se exige comparar la corriente instantánea, duración y, cuando las hojas lo permitan, la integral térmica `∫i(t)²dt` y la energía contra los límites de cada tramo; un dato integral aislado no sustituye las restantes condiciones de su hoja. Son las comprobaciones derivadas del límite de corriente y duración exigido en papel v5 §3, H-V5-CORTO y H-V5-CALIBRE.

El comportamiento tras retirar el corto debe concordar con H-V2-RECUPERACION y H-V5-RECONEXION; no se prescribe recuperación automática ni un modo de reintento. La evidencia de las protecciones propias del ladrillo se recibe de H-V2-AISLAMIENTO (papel v5 §3). El fusible de la franja de red anterior no es un protector heredado del cordón: esa franja sale de la caja (papel v5 §6 y §9, D-V1).

**Criterio de aceptación.** Un mapa del conjunto debe asignar cada posición de fallo a un elemento físico que cubra el recorrido, con hojas locales y comparación de envolventes. En ensayo controlado se verifica cada recorrido, la limitación o interrupción, el estado de los rieles y la recuperación declarada; se comprueba que el cable y las terminaciones conservan sus propiedades. Para el fallo hacia el chasis, el criterio requiere previamente la topología de H-V5-PE. Ninguna prueba de una protección ubicada después del cordón sustituye la prueba de su tramo anterior.

**Sigue faltando:** referencias, corriente disponible, límites y tiempo de actuación, soportabilidad del cable, topología del fallo hacia el chasis y política común de recuperación. El requisito de cobertura queda concreto; sus números de fallo no se pueden obtener del consumo nominal.

## H-V5-INCOMPATIBLE

**ESTADO: (C) DECISION**

**Dueño:** Samuel + diseño (papel v5 §9.2).

**Pregunta exacta:** «¿Qué adaptadores incompatibles debe cubrir el contrato y, para cada incompatibilidad de tensión, polaridad o capacidad de entrega, qué comportamiento y límites de supervivencia se exigen, y quién los garantiza?»

**Respuesta:** falta una política de cobertura. La firma del nominal no define qué adaptadores ajenos hay que sobrevivir. Las opciones siguientes dejan visible ese alcance; el árbol no proporciona precios ni permite cuantificar componentes adicionales (papel v5 §3, H-V5-INCOMPATIBLE).

| Opción para Samuel | Qué compra | Qué cuesta, con rastro | Con qué se choca |
|---|---|---|---|
| Contrato exclusivo de una referencia de ladrillo y cordón identificada; los adaptadores ajenos quedan fuera de la garantía eléctrica. | Acota el conjunto que hay que acreditar. | Restringe la sustitución a referencias aprobadas y exige identificarlas y marcar la polaridad (papel v5 §3, H-V5-CONECTOR e H-V5-INCOMPATIBLE). | Que otro adaptador encaje sigue siendo posible; esta exclusión no es protección física ni prueba de supervivencia. Debe explicitarse su relación con la inversión cubierta en H-V5-INVERSION. |
| Cubrir además un conjunto finito de incompatibilidades expresamente delimitadas. | Permite exigir rechazo o supervivencia para errores concretos de tensión, polaridad o capacidad de entrega. | Identificar cada envolvente ajena y garantizarla con piezas y ensayos; las protecciones añaden las caídas que H-V2-ENTRADA exige presupuestar (papel v5 §3). No hay referencias con las que cuantificar la pérdida. | El alcance no puede expresarse como «cualquiera que encaje». La envolvente que se elija puede exigir otra pareja o protecciones todavía ausentes; recuperación y arranque deben concordar con D-V2. |

No se recomienda una opción. Tampoco se ofrece compatibilidad universal: el árbol no contiene una envolvente que la haga comprobable.

Si se elige cubrir incompatibilidades, la respuesta debe completar esta matriz sin confundir supervivencia con funcionamiento:

| Incompatibilidad | Qué debe declararse antes de exigir una pieza |
|---|---|
| Tensión por debajo o por encima de la admitida, o transitorios ajenos. | Extremos y duración aplicados al chasis; si se exige inhibición, supervivencia o funcionamiento; pieza responsable y límites de los nodos todavía expuestos. Se cruza con H-V2-ENTRADA, H-V2-SUBTENSION y H-V2-TRANSITORIOS (papel v5 §3). |
| Polaridad invertida. | Amplitud y duración cubiertas, rechazo y recuperación elegidos en H-V5-INVERSION; elemento físico que los garantiza (papel v5 §3). |
| Capacidad de entrega insuficiente o con una limitación incompatible con el arranque. | Estado de los rieles durante caída y espera, condición de recuperación y arranque exigible; cruce con H-V2-RESERVA y H-V2-RECUPERACION (papel v5 §3). |
| Mayor capacidad de entrega o energía disponible de la que cubre la protección elegida. | Corriente y energía de fallo disponibles y cobertura real de H-V5-CORTO. La capacidad nominal de una fuente no obliga por sí sola a que la carga consuma más, pero puede cambiar el fallo que debe interrumpirse (derivación de papel v5 §3, H-V5-CORTO e H-V5-INCOMPATIBLE). |

**Criterio de aceptación.** Samuel fija el alcance; diseño asigna cada fila a una envolvente y un responsable físico con hoja local, y verifica el comportamiento exigido mediante ensayo. Bajo el contrato exclusivo se verifica la combinación aprobada y se dejan explícitas las exclusiones, sin anunciar supervivencia de adaptadores ajenos. Bajo cobertura ampliada, cada incompatibilidad incluida debe tener resultado y límites verificables.

**Sigue faltando:** alcance elegido, referencias admitidas o envolventes ajenas, conducta por incompatibilidad, responsables físicos y límites. Esta decisión no se puede sustituir por la elección comercial de un conector.

## H-V5-PE

**ESTADO: (B) REQUISITO COMPRABLE**

**Dueño:** diseño + medida (papel v5 §9.2). Es un requisito de compra **e integración del conjunto**, incompleto mientras falte su topología; no una característica que se satisfaga con la ficha de una pieza aislada.

**Pregunta exacta:** «¿Qué relación tendrán el retorno DC del cordón, ★, `J5`, el chasis y PE, quién proporcionará el camino de modo común que D-F5 cerraba por chasis → PE → primario, y qué evidencia y ensayo del conjunto lo acreditarán preservando la separación de GNDD?»

**Respuesta demostrable: nadie lo hereda todavía.** Lo declara el papel v5 §3 y lo confirma la retirada de las piezas de D-F5 sin un sustituto identificado (papel v5 §9, D-V1). La v4 prescribía este recorrido:

```text
Retornos analógicos y del rack → ★ → J5 → espárrago/chasis
                                               ↑
                                      PE de red separado

Camino de modo común previsto por D-F5:
módulo → Y2 local → chasis → PE → primario
```

Fuente del mapa histórico: **papel v4 §4.1 y §4.2, EMI**. `J5` y PE tenían anillos separados; GNDD quedaba fuera de ★ (papel v4 §4.1). Ese mapa identifica la intención y los conductores anteriores, no acredita rendimiento de la versión nueva. Las «Enmiendas de la tanda A» del papel v4 corrigen además el alcance de la explicación de D-F5 y de su cita de fabricante.

En la dirección nueva solo está fijado el transporte de alimentación y retorno hasta la entrada de la conversión. El trazado documental queda así:

```text
Salida DC del ladrillo ── alimentación y retorno ── entrada de conversión

Relaciones que faltan para cerrar un lazo de modo común:
primario del ladrillo ⇢ salida DC ⇢ dominios internos ⇢ ★ / J5 / chasis
          ↑                                                        ⇣
          └──────────── retorno al origen sin acreditar ────────────┘

⇢ / ⇣ señalan acoplamientos o enlaces por caracterizar, no conexiones elegidas.
```

Fuente y límite del mapa: **papel v5 §3, H-V2-AISLAMIENTO y H-V5-PE, y §9, D-V4**. No es un circuito construido ni una asignación de barreras. La corriente de modo común que se acople desde el ladrillo necesita regresar a su origen; la que generen los convertidores interiores también requiere identificar sus propios lazos. Los conductores DC transportan corriente, pero no determinan por sí solos por qué enlace se cierra cada lazo hacia el chasis o hacia el primario. **La trayectoria cerrada real todavía no puede trazarse con la evidencia disponible.**

| Relación | Qué consta y qué falta |
|---|---|
| Retorno DC ↔ ★ | No está definida por llamar retorno al conductor; depende del reparto y las barreras de D-V4 (papel v5 §3 y §9). |
| ★ ↔ `J5` ↔ espárrago/chasis | Es el recorrido prescrito en la v4. La v5 reabre esa realización y exige declarar su relevo; no localiza el nodo nuevo ni aporta el esquema de conexión (papel v4 §4.1; papel v5 cabecera y §3). |
| Chasis ↔ PE | El cordón firmado no transporta PE separado. El PE eventual del ladrillo no demuestra continuidad hasta el chasis (papel v5 §3). |
| Salida DC del ladrillo ↔ PE/primario | Depende de la referencia: la evidencia se solicita en H-V2-AISLAMIENTO. Su entrega no elige cómo se conecta el chasis (papel v5 §3). |
| GNDD ↔ ★ / GNDA | GNDD debe permanecer fuera de ★ y se exige **>1 MΩ entre GNDA y GNDD dentro de la fuente** (papel v4 §4.1 y §9.1; papel v5 §3). No se autoriza un puente común para resolver el retorno. |

Tampoco se elige dejar el chasis flotante, usar el retorno como PE, añadir otro conductor o cerrar el camino mediante cables de señal. Si hay retornos por acoplamientos capacitivos o por conexiones externas, hay que identificarlos y medirlos: no se contabilizan como un relevo garantizado por intuición. Un PE separado añadido al cordón exigiría reabrir la dirección de D-V5, no esconderlo bajo la palabra retorno (papel v5 §3 y §9).

**Especificación de compra e integración.** El candidato a ladrillo debe aportar la evidencia de H-V2-AISLAMIENTO. El esquema que entregue D-V4 debe declarar los dominios, enlaces y barreras de forma compatible con **>1 MΩ GNDA–GNDD** dentro de la fuente (papel v4 §4.1 y §9.1). Para cada rama del lazo de modo común debe nombrarse un conductor o elemento físico, sus condiciones y la evidencia local. No basta la palabra «certificado» ni la existencia de PE en el ladrillo (papel v5 §3 y §9, D-V1).

No hay en el contrato nuevo una cota garantizada de corriente de modo común, impedancia del retorno o fuga del conjunto que pueda convertirse ahora en un número de compra. No se trasladan las cifras de los módulos de red retirados. Faltan el responsable del relevo, su envolvente y el protocolo de medida; **comprar el ladrillo no cierra esos enlaces por sí solo**.

**Criterio de aceptación.** Primero, esquema completo que trace hasta su origen los lazos de modo común del ladrillo y de la conversión interior, con relaciones retorno/★/`J5`/chasis/PE explícitas y respaldo local de cada enlace. Después, fuente desenchufada: comprobar GNDD fuera de ★ y **>1 MΩ entre GNDA y GNDD dentro de la fuente** (papel v4 §4.1 y §9.1), con el punto de unión externo previsto para el cerebro fuera de esta medida interna. Verificar las continuidades o separaciones restantes contra el esquema aprobado; no imponer una continuidad a PE que aún no está diseñada.

Por último, ensayo del conjunto final con ladrillo, cordón, conversión, chasis y conexiones externas declaradas: identificar las ramas por las que circula el modo común, medir su comportamiento y compararlo con límites documentados antes del ensayo. Esos límites siguen faltando. Debe evitarse que la conexión de tierra del instrumental cree el camino que se pretende acreditar.

Se conserva como comprobación del riel la observación hasta **20 MHz** del papel v4 §9.1, junto con su puerta de ruido, adaptadas al montaje nuevo. **Eso no certifica por sí solo el lazo de modo común**: `hardware/01-power-supply/v4/rizado_budget.py:213` declara `CUBRE_MODO_COMUN = False` y `:482` lo asevera. La medida de resistencia entre masas tampoco demuestra comportamiento de modo común a frecuencia elevada.

**Sigue faltando:** topología de D-V4, referencia y evidencia de H-V2-AISLAMIENTO, responsable físico del relevo de D-F5, relaciones con chasis y PE, límites y protocolo de modo común, y medidas. La conclusión negativa está demostrada; la pregunta completa sigue abierta y no merece estado A.

## Estado de cada HUECO

| HUECO | Estado | Qué falta |
|---|---|---|
| H-V5-CONECTOR | **B — REQUISITO COMPRABLE** | Pareja, polaridad física, hojas, resistencias y garantías para las envolventes completas. |
| H-V5-RETENCION | **B — REQUISITO COMPRABLE** | Solicitación de servicio, esfuerzo/protocolo cuantificados, mecanismo, montaje y ensayo. |
| H-V5-CALIBRE | **B — REQUISITO COMPRABLE** | Extremos de H-V2-ENTRADA y perfiles de corriente, protecciones, temperatura, cable y longitud; evaluar `R_total_adm`. |
| H-V5-INVERSION | **C — DECISION** | Política de rechazo/recuperación, alcance de inversión cubierto, pieza, envolvente y prueba. |
| H-V5-CALIENTE | **C — DECISION** | Admisión de maniobra y alcance accidental; compatibilidad con H-V2-TRANSITORIOS y H-V2-RESERVA. |
| H-V5-RECONEXION | **C — DECISION** | Política de H-V2-RECUPERACION y sus parámetros; energía residual, realización y ensayo. |
| H-V5-CORTO | **B — REQUISITO COMPRABLE** | Protección del tramo completo, corriente/tiempo de fallo, soportabilidad, topología hacia chasis y recuperación. |
| H-V5-INCOMPATIBLE | **C — DECISION** | Cobertura elegida por Samuel, referencias o envolventes ajenas, conducta exigida y responsables. |
| H-V5-PE | **B — REQUISITO COMPRABLE** | Nadie lo hereda todavía: falta topología, responsable físico, evidencia del ladrillo y ensayo del relevo. |
