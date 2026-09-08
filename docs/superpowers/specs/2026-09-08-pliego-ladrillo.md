# El pliego del ladrillo: qué hay que comprar y qué falta para aceptarlo

**Fecha: 2026-09-08. Estado: requisitos de selección; ninguna referencia elegida ni compra definitiva acreditada.**

## 1. Cabecera de compra: amperios, vatios y alcance

**La base actual es 2,68 A y 64,22 W de salida a 24 V nominales. Es el presupuesto estacionario de las cargas declaradas de diseño, sujeto a las hipótesis del guion; todavía no es la capacidad continua definitiva que debe garantizar una referencia comprada.** Fuente: `hardware/01-power-supply/v5/ladrillo_budget.py:42`, `:93`, `:126`, `:151`, `:169`; resolución D-V2, bloque H-V2-RESERVA.

**No se puede especificar completamente el ladrillo hoy con D-V4 sin firmar. En particular, no se puede fijar numéricamente su ventana admisible de tensión sin la ventana garantizada de los DC-DC y las caídas de la entrada completa.** También quedan abiertos la entrega continua final, el arranque y las envolventes dinámicas. Sí se pueden exigir el nominal firmado, la condición conocida de ambiente, la pieza externa de catálogo certificada y un expediente documental concreto. Recibir ese expediente permite comparar candidatos; no sustituye las decisiones de integración pendientes.

La matriz de §3 cuenta **16 requisitos propios de compra: 2 en (1) NÚMERO YA, 7 en (2) REHÉN DE D-V4 y 7 en (3) ACREDITACIÓN DOCUMENTAL**. Los de (2) no son mayoría del total, aunque sí de los requisitos que necesitan una magnitud de aplicación. Tampoco los siete documentales equivalen a siete aceptaciones cerradas. **Consultar al fabricante puede avanzar hoy; aprobar una referencia para el conjunto final sigue bloqueado.** El conteo no incluye requisitos del cordón, del DC-DC o de la cascada como si fueran prestaciones del ladrillo.

### 1.1 Fuentes y autoridad

Se usan estas abreviaturas en todo el pliego:

- **V5**: [fuente v5](2026-09-05-fuente-v5-ladrillo-design.md), leída completa. Sus firmas de §9 y políticas de §9.3 son el estado vigente: D-V1, D-V2, D-V3 y D-V5 firmadas; D-V4 pendiente.
- **R2**: [resolución D-V2](2026-09-08-huecos-dv2-resolucion.md), leída completa. Sus bloques se citan por el identificador de su encabezado.
- **R5**: [resolución D-V5](2026-09-08-huecos-dv5-resolucion.md), leída completa, con la misma convención.
- **`ladrillo_budget.py`**: [presupuesto v5](../../../hardware/01-power-supply/v5/ladrillo_budget.py). Las referencias abreviadas a este guion apuntan siempre a `hardware/01-power-supply/v5/`.

Las alternativas de política que aparecen en R2 y R5 se leen con las elecciones posteriores de V5 §9.3. Este pliego las aplica; no vuelve a someterlas a elección. Ninguno de los HUECOS originales queda cerrado por reunirlos aquí (V5 §9.2–§9.3).

### 1.2 De dónde salen los amperios y vatios

El cálculo es `P_modelo = Σ(V_riel · I_riel / η_riel)` y `I_modelo = P_modelo / V_ladrillo` (`ladrillo_budget.py:143`, `:147`, `:157`, `:170`). Se separan los rieles porque no se pueden sumar sus amperios directamente para dimensionar el transporte.

| Rama del presupuesto | Tensión y corriente utilizadas | Hipótesis y cita |
|---|---|---|
| Rack positivo y pantalla | 12 V; 1,050 A | Fila declarada de 0,500 A más pantalla de 0,550 A sin pieza; `ladrillo_budget.py:75`, `:87`, `:128`; `hardware/01-power-supply/v4/calor_budget.py:182`. |
| Rack negativo | Magnitud 12 V; 0,500 A | D-B2; `ladrillo_budget.py:75`, `:130`; `hardware/01-power-supply/v4/calor_budget.py:182`. |
| Rack auxiliar | 5 V; 0,500 A | D-B2; `ladrillo_budget.py:75`, `:132`; `hardware/01-power-supply/v4/calor_budget.py:182`. |
| Digital | 5 V; 2,895 A | Cargas máximas del presupuesto digital, con el host; `ladrillo_budget.py:82`, `:134`; `hardware/01-power-supply/v4/calor_budget.py:204`. |
| Cada crudo de cascada | Magnitud 15,8875 V; 0,650 A | Nominal firmado de 15,5 V elevado por la tolerancia supuesta de ±2,5 %, extremo alto usado para potencia; `ladrillo_budget.py:78`, `:107`, `:108`, `:126`, `:136`, `:138`. |

Los rendimientos usados son **0,90 para las ramas buck, 0,85 para el inversor y 0,85 para el crudo**, todos **ESTIMADOS** y sin pieza (`ladrillo_budget.py:101`, `:102`, `:103`, `:110`). Los nombres de esas constantes no eligen las topologías ni prueban aislamiento (`ladrillo_budget.py:49`; R2 H-V2-CORTO-DCDC).

Con esas entradas, la salida de las conversiones suma **56,22875 W** y sus pérdidas **aproximadamente 7,989714 W**; el modelo pide **aproximadamente 64,218464 W y 2,675769 A** a su nominal. Los valores de cabecera son la impresión redondeada del mismo cálculo (`ladrillo_budget.py:143`, `:147`, `:151`, `:169`, `:289`, `:296`, `:297`). Para comparar una garantía se usa la fórmula sin redondear, y después el presupuesto completo que la sustituya.

La declaración de la cascada sigue siendo **0,650 A por riel**, aunque el censo sea menor; aquí no se recorta (V5 §8, HUECO 5; `ladrillo_budget.py:78`). El digital usa el máximo del presupuesto a **TJ = 125 °C**, mientras sigue abierto su punto real de trabajo; esa temperatura no es el ambiente del ladrillo (V5 §8, HUECO 3; `hardware/01-power-supply/v4/calor_budget.py:190`, `:204`). La pantalla permanece sin referencia (V5 §8, HUECO 2). Por tanto, **2,68 A es la traducción al transporte de la carga declarada bajo un escenario de conversión todavía supuesto**; no es el censo optimista ni corriente máxima de arranque o fallo (V5 §3; R2 H-V2-RESERVA).

### 1.3 Qué falta para convertir la cabecera en una capacidad garantizada

Se abre **H-PL-ENTREGA: capacidad continua final del ladrillo en amperios y vatios**. Es una obligación de compra que se explicita aquí; sus causas ya constan en R2 H-V2-RESERVA y V5 §8. Falta:

- Recalcular con las piezas y rendimientos garantizados de D-V4, a sus tensiones, cargas y temperaturas reales. El cálculo puede cambiar al sustituir los supuestos; no se consagra el resultado del modelo como mínimo invariable de cualquier realización.
- Incorporar las pérdidas del cordón completo, contactos, protecciones e interconexiones; el guion suma las entradas de los DC-DC sin añadirlas expresamente (`ladrillo_budget.py:157`; R2 H-V2-RESERVA).
- Cerrar consumos propios y auxiliares que no estén ya incluidos, especialmente los de prerreguladores y control; asignar la corriente de carga del crudo no demuestra haber contado esos consumos (R2 H-V2-RESERVA).
- Confirmar la pantalla y las cargas declaradas pendientes de acreditación, conservando las declaraciones firmadas mientras no se cambien (V5 §1 y §8).
- Evaluar la corriente a la tensión mínima real, con eficiencia y caída dependientes de carga y temperatura; dividir por el nominal no proporciona el máximo en toda la ventana (R2 H-V2-ENTRADA y H-V2-RESERVA).

El criterio final será `P_continua_garantizada(q) ≥ P_demanda_completa(q)` e `I_continua_garantizada(q) ≥ I_demanda_completa(q)` en cada condición de servicio `q`, con la reducción de capacidad del candidato incluida. La demanda completa suma las entradas de las conversiones, consumos no incluidos y pérdidas de transporte/protección, sin duplicar términos ya absorbidos en una eficiencia. Es la formalización de R2 H-V2-RESERVA. El arranque se compara aparte con su perfil temporal; **no se añade un porcentaje de reserva sin fuente**.

El rendimiento AC-DC supuesto de **0,88** solo convierte esta salida en demanda de red: **72,98 W**, con **8,76 W** disipados fuera en el modelo (`ladrillo_budget.py:96`, `:164`, `:298`, `:299`). Esas magnitudes no son la potencia de salida que se compra. La mención de clase de eficiencia junto a esa estimación tampoco establece una exigencia certificada de eficiencia ni una clase de protección eléctrica (`ladrillo_budget.py:95`, `:114`; R2 H-V2-AISLAMIENTO).

## 2. La frontera de tensión que D-V4 debe cerrar

Los puntos de medida son: **salida DC del ladrillo → cordón y contactos → entrada del chasis → protecciones → entrada de cada DC-DC → crudos y filtro → pines de los prerreguladores referidos a sus masas locales** (V5 §3; R2 H-V2-ENTRADA y H-V2-SUBTENSION). Si la ficha de un ladrillo con cable fijo garantiza la tensión al extremo del cable, se debe documentar ese punto y contar esa caída una sola vez.

Se conserva la notación de R2 H-V2-ENTRADA: `Bmin/Bmax` son los extremos garantizados del ladrillo; `Δmin/Δmax`, las caídas completas; `Dmin/Dmax`, los extremos admitidos por el DC-DC. **Δmax es una caída; Dmax es el techo de entrada del convertidor.** Para cada rama y condición se comprueba:

| Estado | Inclusiones exigidas, según R2 H-V2-ENTRADA |
|---|---|
| Arranque | `Bmin_arranque − Δmax_arranque ≥ Dmin_arranque`; `Bmax_arranque − Δmin_arranque ≤ Dmax_arranque`. |
| Regulación | `Bmin_régimen − Δmax_régimen ≥ Dmin_regulación`; `Bmax_régimen − Δmin_régimen ≤ Dmax_regulación`. |

De ahí sale **`Δmax ≤ Bmin − Dmin`**, usando el estado más restrictivo. D-V4 debe entregar **la referencia y configuración de cada convertidor, con sus ventanas garantizadas de arranque y regulación, UVLO e histéresis a las cargas y temperaturas del montaje**. Elegir solo una familia de topología, sin esos extremos, no basta. También faltan el cordón y los contactos de D-V5 y la caída de las protecciones, incluido el bloqueo de inversión firmado (V5 §9.3; R5 H-V5-CALIBRE).

**El fabricante puede declarar Bmin y Bmax hoy; nosotros todavía no podemos declarar cuáles aceptar.** Tampoco hay que fijarlos antes de pedir hojas: se pueden cotejar parejas candidatas de ladrillo y conversión con estas inclusiones. La aprobación final requiere que ambas queden acreditadas en el mismo contrato.

El nominal del crudo de **15,5 V** y los suelos locales de **14,039752… V en U1 y 13,833770… V de magnitud en U2** pertenecen a la salida de la conversión y a la cascada; no se convierten en extremos del ladrillo (V5 §5; R2 H-V2-ENTRADA y H-V2-SUBTENSION). El máximo absoluto **±20 V de U1** tampoco es el techo del ladrillo de **24 V nominales**: obliga a resolver el recorrido de fallo y la protección independiente de #334 (V5 §3; R2 H-V2-CORTO-DCDC).

## 3. Matriz de compra y aceptación

Cada identificador **L01–L16** cuenta una vez. Una fila (2) describe la envolvente que necesita la aplicación; una fila (3), evidencia del candidato. Por ejemplo, los tiempos que necesita la cadena en L09 no son la declaración del modo nativo recibida en L15. Los criterios de cadena se desarrollan en §4; los dueños ajenos al ladrillo, en §5.

### 3.1 (1) NÚMERO YA: 2 requisitos

| ID y requisito | Número con fuente | Documento y criterio de aceptación |
|---|---|---|
| **L01. Tensión nominal** | **24 V DC** (V5 §9, D-V2; `ladrillo_budget.py:93`). | Fila de tensión nominal de salida de la hoja de la referencia exacta: debe corresponder al nominal firmado. No acredita tolerancia ni transitorios; requieren L04 y L05. |
| **L02. Condición conocida de ambiente** | Servicio en sala de diseño a **45 °C** (`hardware/01-power-supply/v4/calor_budget.py:138`; R2 H-V2-ENTRADA). | Intervalo de temperatura de funcionamiento, curva garantizada de reducción de corriente/potencia y condiciones de montaje/refrigeración. Debe cubrir ese ambiente con la entrega que cierre L03. No es temperatura de carcasa ni de semiconductor; faltan el resto del intervalo ambiental y el montaje externo. No se fija aquí una forma de refrigeración. |

### 3.2 (2) REHÉN DE D-V4: 7 requisitos

| ID y requisito del ladrillo | Decisión exacta de D-V4 que permite poner el número; dependencias adicionales | Evidencia y aceptación |
|---|---|---|
| **L03. Corriente y potencia continuas garantizadas** | Referencias, reparto y configuración de conversiones; eficiencias garantizadas, consumos propios y temperaturas. Además: cargas pendientes, cordón y pérdidas de protecciones. **H-PL-ENTREGA**, §1.3; R2 H-V2-RESERVA. | Hoja: corriente/potencia de salida continua y reducción con línea y temperatura. Comparar con la demanda completa de §1.3 en toda la ventana; la cabecera es base condicionada. |
| **L04. Ventana garantizada de salida, en arranque y régimen** | Referencia de cada DC-DC con ventanas de entrada y UVLO garantizados. Además: caídas máximas/mínimas del cordón, contactos y protecciones, condiciones de red y ambiente. R2 H-V2-ENTRADA. | Hoja: tolerancia total, regulación de línea/carga, deriva térmica y salida durante arranque. Aclarar qué términos ya incluye cada cota. Cumplir ambas inclusiones de §2 en cada rama y medir los nodos reales. |
| **L05. Rizado y transitorios emitidos por la salida** | Conversiones y protecciones elegidas con límites de funcionamiento/supervivencia, respuesta de carga y recorridos de fallo. Además: cordón y contactos. R2 H-V2-ENTRADA, H-V2-TRANSITORIOS y H-V2-CORTO-DCDC. | Hoja o informe garantizado: rizado/ruido con carga, temperatura, ancho de banda y método de medida; excursiones al arrancar, cambiar carga, cortar y recuperar, con amplitud, polaridad, duración y repetición. Solicitar información espectral disponible distinguiendo garantía de dato típico. Comparar las perturbaciones que alcanzan cada nodo con su envolvente garantizada; la tolerancia de continua no sustituye esta prueba ni se hereda el límite de ruido final de la cascada. |
| **L06. Reserva de arranque y carga capacitiva efectiva admisible** | Referencias y configuración de DC-DC, capacidades de entrada, rampas, secuencia y consumos con cargas conectadas. Además: resto del inventario capacitivo y pérdidas de entrada. R2 H-V2-RESERVA. | Hoja: carga capacitiva máxima, arranque cargado, corriente disponible y duración, limitación y tensión mínima conservada. Comparar con el inventario/perfil efectivo visto por el ladrillo y completar el arranque sin un ciclo que lo impida. No sumar capacidades situadas tras distintos convertidores como si estuvieran directamente en su salida. |
| **L07. Supervivencia de la salida ante conexión energizada accidental** | Entrada de DC-DC, capacidades y limitación elegidas; límites y estado de los rieles. Además: cable, pareja de conectores y rebote. Política ya firmada; falta su envolvente. V5 §9.3; R5 H-V5-CALIENTE. | Informe del fabricante para conexión de carga con la salida energizada, con corriente, tensión, duración y repetición garantizadas. La misma carga y perfiles de L05/L06 deben quedar cubiertos por el ladrillo y el conjunto, sin daño; no se exige continuidad de funcionamiento durante el accidente. Ensayo de §4.2. |
| **L08. Salida frente a energía residual y realimentación** | Topología, barreras, caminos de descarga y posibilidad de corriente desde las conversiones hacia el transporte. Además: desconexión/reconexión y elementos de bloqueo reales. R5 H-V5-RECONEXION y H-V5-CORTO; R2 H-V2-TRANSITORIOS. | Hoja o declaración: capacidad de soportar tensión/corriente aplicada desde la carga con salida encendida o apagada, energía y duración; comportamiento con salida precargada. Comparar con el perfil residual real. Si el diseño demuestra que no llega energía al ladrillo, documentar el elemento y sus límites; no presumir bloqueo ni exigir capacidad de absorber energía sin necesidad demostrada. |
| **L09. Compatibilidad temporal con reintentos y abandono** | Realización del control/habilitación y protección de los grupos de rieles, estado cuando cae su alimentación y forma de coordinarse con la fuente. Además: aplicación por causa, estado de cada grupo de rieles, cupo, espera, abandono, rearme y discriminación del rebote todavía por declarar; cobertura física del cordón. V5 §9.3; R2 H-V2-RECUPERACION. | Tiempos y condiciones garantizadas de recuperación/arranque y, si existe, mando de rearme. Comparar con el control elegido según §4.1: cada intento autorizado puede completarse y el fallo persistente deja de ser energizado al agotarse el cupo. La palabra «hiccup» no acredita esto. |

### 3.3 (3) ACREDITACIÓN DOCUMENTAL: 7 requisitos

**No existe aún una hoja de candidato a la que asignar página o número de línea.** La columna siguiente identifica el campo concreto que debe contestar cada requisito. Al recibirla se registra **nombre de archivo local, revisión, página, tabla/fila o cláusula**; si no aparece, se solicita declaración técnica del fabricante para esa referencia, con condiciones y límites garantizados. Un dato típico o una respuesta comercial sin ese alcance deja pendiente la acreditación.

| ID y requisito | Línea o campo exigido y documento que lo contesta | Contra qué se compara |
|---|---|---|
| **L10. Pieza externa de catálogo certificada** | Hoja: modelo completo y modalidad de montaje/uso externo. Certificado: fabricante, referencia o variante cubierta, norma/edición, alcance y condiciones. | D-V1 firmado: AC-DC de catálogo, certificado, fuera de la caja (V5 §3 y §9). Verificar correspondencia de modelo, configuración y uso. El alcance aceptable del sistema debe estar declarado; «certificada» por sí solo no lo decide (R2 H-V2-AISLAMIENTO). |
| **L11. Clase de protección** | Hoja y certificado/informe de seguridad: clase declarada, necesidad de tierra de protección y condiciones de instalación. | Clase y esquema de protección que adopte el sistema, todavía pendientes. No se exige una clase concreta por herencia de la v4 (R2 H-V2-AISLAMIENTO). Recibir la clase es acreditación; aprobarla necesita ese criterio nuestro. |
| **L12. Aislamiento** | Certificado/informe y hoja: aislamiento entrada–salida y respecto de PE, tipo, tensión y duración de ensayo, pares de terminales y condiciones ambientales. | Límites de seguridad e instalación adoptados para el sistema, todavía sin fijar. La separación entre masas internas no reemplaza el ensayo de seguridad del ladrillo (R2 H-V2-AISLAMIENTO). |
| **L13. Corriente de fuga** | Fila de fuga máxima garantizada e informe de ensayo: tensión/frecuencia de red, carga, método, conexión y condiciones. | Límite aplicable al sistema y presupuesto de fuga completo, ambos pendientes de adopción/acreditación; usar las mismas condiciones de medida. No aprobar solo porque la ficha declare una fuga (R2 H-V2-AISLAMIENTO; R5 H-V5-PE). |
| **L14. Relación entre salida DC, PE y primario** | Esquema, hoja o declaración técnica: relación de cada terminal de salida con PE y primario; enlaces conductores y acoplamientos relevantes para el modo común, con condiciones. | Topología de retornos, barreras y chasis que entregue diseño con D-V4/D-V5. Debe permitir acreditar el relevo de modo común y preservar GNDD. Ni la presencia de PE en el ladrillo ni una salida descrita como flotante resuelven por sí solas el conjunto (R2 H-V2-AISLAMIENTO; R5 H-V5-PE). |
| **L15. Protecciones nativas y su recuperación** | Hoja y, si falta detalle, informe: presencia **o ausencia** de protección de corto, sobrecarga, sobretensión y temperatura; umbrales mínimo/máximo, tiempo de respuesta, curva de corriente/tensión, duración, repetición y forma de recuperación. Identificar qué exige quitar red, quitar carga o un mando. | Ventanas de L04/L05, arranque L06, recuperación L09 y soportabilidad del cordón/protección independiente de §5. Declarar una protección no acredita su ubicación ni toda la cadena; su ausencia exige cobertura asignada y demostrada, no una suposición (R2 H-V2-AISLAMIENTO; R5 H-V5-CORTO). |
| **L16. Referencia exclusiva e interfaz de salida identificada** | Hoja, plano y configuración de suministro: referencia exacta, cable fijo o separable, terminación, polaridad vista desde un lado indicado, referencias incluidas y punto donde se garantizan tensión/corriente. | Contrato exclusivo y transporte de alimentación/retorno de V5 §9 y §9.3. Comparar con la referencia de cordón y pareja de conectores que elija diseño; ninguna está elegida. Si se ofrece cable, su aceptación se tramita con los requisitos de cordón de §5. No permite sustituciones eléctricas por parecido físico (R5 H-V5-CONECTOR e H-V5-INCOMPATIBLE). |

**Cifras que no son límites de compra:** clase II, **4,2 kVac** y **fuga <0,25 mA** pertenecen a módulos IRM retirados; **3,5 mA** en `hardware/01-power-supply/v4/fuga_budget.py:95` es un valor de trabajo sin norma (R2 H-V2-AISLAMIENTO). Ninguna de esas cifras se traslada al candidato. La exigencia **>1 MΩ entre GNDA y GNDD dentro de la fuente** sigue siendo del conjunto, con GNDD fuera de la estrella, y no fija la clase, aislamiento o fuga del ladrillo (V5 §3; R5 H-V5-PE).

## 4. Qué exigen al ladrillo las políticas ya firmadas

### 4.1 Reintentos con abandono, también cuando actúa su protección

La cadena debe reintentar un cupo declarado, esperar entre intentos y abandonar si persiste el fallo (V5 §9.3). **Se exige al ladrillo un modo de recuperación compatible con esa secuencia, documentado por causa.** La política no exige por sí sola un contador dentro del ladrillo ni permite suponer un mando remoto inexistente.

| Comportamiento acreditado del candidato | Resultado de la comparación |
|---|---|
| Recupera por sí mismo o hace ciclos de limitación y rearranque. | Solo es compatible si esos ciclos permiten completar los intentos legítimos, no borran el cupo y no vuelven a energizar el fallo después del abandono. El control debe conservar o reconstruir el estado necesario cuando desaparezca su alimentación. Queda pendiente su realización (R2 H-V2-RECUPERACION; V5 §9.3). |
| Se enclava y solo sale retirando la red. | Si un evento que la política exige reintentar deja ese enclavamiento, la referencia no cumple por sí sola. Una acción manual en la pared no es un reintento de la cadena. Solo una realización de rearme acreditada podría resolverlo; no existe una elegida ni se presupone aquí (derivación de V5 §9.3 y R2 H-V2-RECUPERACION). |
| Admite rearme por descarga, retirada de carga o mando. | La condición y tiempos deben estar garantizados, y el diseño debe demostrar que puede producirlos incluso tras perder alimentación. Su existencia en una ficha no asigna el mecanismo ni garantiza un arranque cargado (R2 H-V2-RESERVA y H-V2-RECUPERACION). |

**Abandonar debe impedir seguir alimentando el fallo cubierto.** Inhibir la cascada no demuestra ni detener un corto de DC-DC puenteado ni interrumpir un corto del cordón situado antes del control interior. Si el ladrillo sigue enviando pulsos a ese tramo, falta acreditar cómo termina esa energización. El modo nativo o un elemento que cubra el recorrido deberán hacerlo; su asignación queda pendiente, sin elegir mecanismo (derivación conjunta de V5 §9.3, R2 H-V2-CORTO-DCDC y R5 H-V5-CORTO).

La prueba de aceptación registra salida del ladrillo, entrada de conversiones, habilitaciones y rieles durante fallo transitorio, fallo persistente, espera y abandono. Se comprueba el cupo y la espera declarados, que una caída de alimentación no libere indebidamente el abandono, y que el mecanismo alcance el recorrido de cada fallo. La recuperación de las protecciones propias se ensaya con las causas incluidas en su contrato; no basta simular únicamente una señal local.

El rebote del conector **no puede gastar reintentos**. Corregir la polaridad debe permitir arrancar cuando vuelvan las condiciones válidas; sigue pendiente definir cómo se rearma el cupo en ese cruce. Las habilitaciones y evolución de todos los rieles pertenecen al control del conjunto (V5 §9.3; R2 H-V2-RECUPERACION; R5 H-V5-RECONEXION). No se asignan aquí cupo, intervalo, condición de abandono ni de liberación.

### 4.2 Enchufe en caliente: supervivencia obligatoria

La maniobra normal es conectar con el ladrillo desenergizado. **La conexión accidental con su salida energizada está cubierta y debe sobrevivir tanto el ladrillo por su salida como el conjunto expuesto.** No se exige funcionamiento continuo durante el accidente (V5 §9.3).

L07 obliga a acreditar la conexión de la carga efectiva, incluyendo su corriente inicial, perturbación de salida y repetición. L08 cubre la energía que pueda regresar por una reconexión con carga residual. Se permite que una protección actúe si el resultado cumple la supervivencia y la recuperación firmadas; no se presume que actuar equivalga a sobrevivir.

La prueba usa el mismo cordón, conectores, capacidad efectiva, cargas, temperatura y estados iniciales que L05/L06/L08: caja descargada, estados residuales incluidos en el contrato y rebote declarado. Se registran tensión y corriente en salida del ladrillo, entrada del chasis y conversiones; se contrastan amplitud, polaridad, duración y repetición con las garantías de las piezas. Después se comprueba que se conservan sus prestaciones y que la cadena sigue la recuperación exigida. **Faltan las envolventes numéricas; no se sustituyen por una instrucción de uso ni por la corriente nominal del conector** (R5 H-V5-CALIENTE; R2 H-V2-TRANSITORIOS y H-V2-RESERVA).

### 4.3 Contrato exclusivo e inversión de polaridad

Se acreditarán **una referencia de ladrillo y una de cordón**, aún sin nombres; las fuentes ajenas quedan fuera de la garantía eléctrica (V5 §9.3, H-V5-INCOMPATIBLE). L16 permite identificar esa combinación. Que otra fuente encaje no la convierte en referencia autorizada.

La inversión es la excepción cubierta expresamente: **un elemento nuestro debe bloquearla y permitir recuperar al corregirla**. No se pide al ladrillo que proteja los circuitos interiores frente a un adaptador invertido. Diseño debe elegir el elemento, ubicación, envolvente y recuperación; su caída entra en L04 y su pérdida en L03 (V5 §9.3). La capacidad de la salida del ladrillo ante corriente que regresa desde la caja es otro fenómeno, tratado en L08; no demuestra el bloqueo de polaridad del instrumento.

## 5. Reparto completo: lo que no se compra al ladrillo

Esta tabla recorre los HUECOS de V5 §9.2 para que ninguno desaparezca al separar proveedores. Sus filas son trazabilidad, no requisitos adicionales en el conteo de §3.

| HUECO de origen | Parte comprable al ladrillo | Parte y dueño que permanecen fuera |
|---|---|---|
| H-V2-ENTRADA | L01/L04, extremos garantizados. | D-V4: ventanas de cada DC-DC. Diseño de entrada/cordón: caídas completas (R2, bloque homónimo). |
| H-V2-SUBTENSION | L04/L09/L15: comportamiento de salida que condiciona arranque y caída. | DC-DC: UVLO. Diseño: detector, histéresis, tiempos y coordinación de ambos crudos con D-F4; no se trasladan sus umbrales a la salida del ladrillo (R2, bloque homónimo). |
| H-V2-TRANSITORIOS | L05/L07/L08. | Diseño: límites por nodo, filtros y protecciones; fabricante de DC-DC: crudo garantizado. El ruido final de la cascada no es un límite de rizado del ladrillo (V5 §7; R2, bloque homónimo). |
| H-V2-RESERVA | L03/L06. | Diseño y fabricantes de cargas/conversiones: inventario y perfiles referidos a la entrada; no basta la capacidad parcial de filtros (R2, bloque homónimo). |
| H-V2-RECUPERACION | L09/L15 y §4.1. | Diseño: control, cupo/espera/abandono/rearme y estados de rack, digital y cascada. Parámetros aún pendientes, con política ya elegida (V5 §9.3). |
| H-V2-CORTO-DCDC | L05/L15: tensión y corriente/energía que puede aportar el ladrillo. | Diseño de D-V4 y protección independiente: recorrido real de fallo, barreras/retornos, corte, limitación y energía residual. Una OVP del ladrillo no cierra #334; la propuesta de R2 sigue sin pieza y validación (R2, bloque homónimo). |
| H-V2-AISLAMIENTO | L10–L15. | Diseño: criterio de seguridad del conjunto y comparación con sus límites; fabricante entrega evidencia, no decide esos límites (R2, bloque homónimo). |
| H-V5-CONECTOR | L16 para la terminación ofrecida. | Diseño y proveedor del cordón/conectores: pareja, polaridad, límites DC, resistencia de contactos y terminaciones, montaje y acreditación (R5, bloque homónimo). |
| H-V5-RETENCION | Documentación del anclaje o cable suministrado, si lo incluye L16. | Diseño mecánico: solicitación, fuerza, dirección, duración, repetición y criterio; proveedor y ensayo del conjunto: retención y alivio de tracción. No es una cifra de salida del AC-DC (R5, bloque homónimo). |
| H-V5-CALIBRE | L03/L04/L15 aportan las solicitaciones de la fuente. | Diseño/proveedor del cordón: longitud, calibre, resistencia total y temperatura. **16 AWG, 2 m y 141 mV** son un escenario sin contactos/protecciones, no una elección (`ladrillo_budget.py:173`, `:339`, `:341`; R5, bloque homónimo). |
| H-V5-INVERSION | L03/L04 reciben pérdida y caída del bloqueo. | Elemento físico nuestro y control de recuperación, §4.3. No se delega al ladrillo (V5 §9.3). |
| H-V5-CALIENTE | L07 y su cruce con L05/L06/L08. | Diseño de entrada, cordón y conectores: supervivencia de sus partes; norma de uso desenergizado. La protección del ladrillo no acredita el conector (V5 §9.3; R5, bloque homónimo). |
| H-V5-RECONEXION | L08/L09/L15. | Diseño: descargas, detección de reconexión válida, rebote y persistencia del cupo; hereda la política, sin otra elección independiente (V5 §9.3). |
| H-V5-CORTO | L15 y compatibilidad de abandono de L09. | Diseño: asignar cada recorrido de fallo a una protección que lo cubra; cordón/contactos: soportar corriente y duración, energía e integral térmica cuando sus hojas permitan usarla. Incluir descarga desde la caja; una protección posterior al cable no protege por sí sola el tramo anterior (R5, bloque homónimo). |
| H-V5-INCOMPATIBLE | L16, referencia exclusiva. | Diseño/documentación del producto: combinación autorizada y exclusiones, conservando inversión cubierta. No se crea una exigencia de adaptador universal (V5 §9.3). |
| H-V5-PE | L11–L14, evidencia de salida y seguridad. | D-V4/D-V5, diseño y medida: relaciones retorno/estrella/J5/chasis/PE, barreras de GNDD y relevo de modo común. El cordón de **dos hilos** no aporta PE separado (V5 §3 y §9; R5, bloque homónimo). |

## 6. Pendientes que impiden emitir una aceptación final

**D-V4 debe concretar** referencias y configuración de conversiones, garantías de entrada/salida y eficiencia, barreras y retornos, protección por riel, comportamiento de control y arranque. Eso proporciona las magnitudes que faltan en L03–L09 y la topología con la que comparar L14; una firma sin esos datos no evalúa las desigualdades (V5 §9; R2 H-V2-ENTRADA, H-V2-RESERVA y H-V2-CORTO-DCDC).

**Hay pendientes que no resuelve elegir el DC-DC.** No se los atribuye artificialmente a D-V4:

| Pendiente | Quién debe concretarlo y efecto en la compra |
|---|---|
| Intervalo de red, frecuencia y condiciones completas de servicio; ambiente y montaje externo. | Diseño: definir aplicación; fabricante: garantizarla. Solo hay un punto de sala conocido en L02. Sin el resto no se compara la cobertura total de L02–L06 ni las condiciones de los certificados (R2 H-V2-ENTRADA y H-V2-AISLAMIENTO). |
| Clase, aislamiento y fuga aceptables del sistema, con norma y alcance. | Diseño: adoptar límites respaldados; fabricante: aportar L10–L14. Son criterios de aceptación pendientes, no números que se puedan copiar del candidato (R2 H-V2-AISLAMIENTO). |
| Referencias de cordón/conectores, longitud, montaje, temperatura, retención y solicitación mecánica. | Diseño eléctrico/mecánico y proveedores: completar el contrato de R5 H-V5-CONECTOR, H-V5-RETENCION y H-V5-CALIBRE. La preferencia de retención que haga falta decidir se mantiene pendiente. |
| Aplicación de la recuperación por causa, estados de cada grupo de rieles, cupo, intervalos, condición de abandono/liberación, reconocimiento del intento y rearme tras corregir inversión. | Diseño y decisión de los parámetros de aplicación, con evidencia de fabricante. V5 §9.3 elige el comportamiento; R2 H-V2-RECUPERACION exige declarar causas y estados. Esos valores y condiciones siguen pendientes; no corresponde elegirlos en este pliego. |
| Capacidad continua final y cargas pendientes. | **H-PL-ENTREGA**, §1.3: diseño de potencia, fabricantes de conversiones y cargas. No se sustituye por un margen porcentual. |
| Coordinación entre recuperación nativa y fin de energización de cada fallo. | **H-PL-ABANDONO-FUENTE**: obligación de integración explicitada al traducir la política a la compra, §4.1. Diseño debe asignar el responsable físico y demostrar su alcance, incluso cuando el fallo quede en el cordón. El fabricante aporta las garantías de L09/L15. Deriva de V5 §9.3 y R5 H-V5-CORTO; no es una política nueva. |
| Punto de garantía de la salida en el suministro exacto. | **H-PL-PUNTO-SALIDA**: dato de oferta aún inexistente, L16. Fabricante identifica si los límites incluyen el cable suministrado; diseño hace corresponder ese punto con las caídas de §2. Deriva de la distinción de nodos de V5 §3 y del bucle de R5 H-V5-CALIBRE. |

Los identificadores H-PL hacen explícitos pendientes de este pliego; no sustituyen ni cierran los HUECOS originales. Los demás faltantes de la tabla ya estaban declarados en los papeles de origen.

### 6.1 Regla de lectura de una oferta

Para cada L01–L16 se registra: referencia/configuración, archivo local y revisión, página/fila, garantía con condiciones, criterio de este pliego, comparación y ensayo de integración que corresponda. El resultado es:

- **Cumple:** hay garantía suficiente y comparación satisfecha; si exige prueba del conjunto, existe esa evidencia.
- **No cumple:** una garantía, limitación o exclusión conocida contradice el criterio aplicable. Registrar la condición concreta.
- **Pendiente:** falta garantía, falta un límite nuestro o falta la prueba. Una celda pendiente no se convierte en «cumple» por tener certificación o potencia de placa elevada.

Una oferta puede descartarse por una incompatibilidad demostrada y puede conservarse para comparación documental. **Hoy ninguna puede declararse apta para comprar como solución final solo presentando su hoja: faltan criterios nuestros y pruebas de integración.** Esto aplica las condiciones de fabricación de V5 §9.2 y los criterios de R2/R5; no elige candidato ni autoriza fabricar.

## 7. Preguntas al fabricante para copiar en un correo

Trazabilidad del contexto siguiente, fuera del texto para enviar: nominal en `ladrillo_budget.py:93` y V5 §9; ambiente en `hardware/01-power-supply/v4/calor_budget.py:138` y R2 H-V2-ENTRADA; consumo provisional en `ladrillo_budget.py:151`, `:169`, `:296`, `:297` y R2 H-V2-RESERVA. El texto para copiar empieza en el párrafo siguiente.

Buscamos una fuente externa AC-DC de catálogo certificada, de **24 V DC nominales**, que pueda entregar la carga requerida en un ambiente de sala de **45 °C**. Nuestro presupuesto estacionario provisional es **64,22 W y 2,68 A al nominal**; todavía debemos completar las pérdidas, los consumos propios y las garantías de la conversión interior. No son valores de pico ni una reserva de arranque ya validada.

Para la referencia que nos propongan, agradeceríamos respuestas con valores garantizados, sus condiciones de aplicación y la página, tabla o cláusula de la hoja, certificado o informe que las respalde. Si un dato es solo típico, indiquen expresamente esa limitación. Necesitamos acreditar la fuente junto con su cable de salida y nuestra carga antes de aprobar la referencia.

1. ¿Cuál es la referencia completa y la configuración exacta de suministro? ¿Es una fuente AC-DC de catálogo para uso externo? ¿Qué cable y terminación de salida incluye, y son fijos o separables?
2. ¿Pueden adjuntar la hoja de datos y los certificados e informes aplicables a esa variante, indicando norma, edición, alcance y condiciones de instalación y servicio?
3. ¿Qué clase de protección tiene? ¿Necesita tierra de protección y qué condiciones de conexión son obligatorias?
4. ¿Qué aislamiento garantiza entre entrada, salida y tierra de protección? Indiquen tipo de aislamiento, pares de terminales, tensión y duración de los ensayos y condiciones ambientales.
5. ¿Cuál es la corriente de fuga máxima garantizada? Indiquen tensión y frecuencia de red, carga, método de medida y conexiones usadas en el ensayo.
6. ¿Qué relación eléctrica tiene cada terminal de salida con la tierra de protección y el primario? ¿Pueden documentar los enlaces conductores y los acoplamientos relevantes para las corrientes de modo común?
7. ¿Qué intervalos de tensión y frecuencia de red, temperatura ambiente y condiciones de montaje garantizan? ¿Cómo se reduce la corriente o potencia disponible dentro de esos intervalos?
8. ¿Qué corriente y potencia de salida continua garantizan en esas condiciones? ¿Exigen una carga mínima para arrancar o mantener regulación?
9. ¿Qué tensiones mínima y máxima de salida garantizan durante el arranque y en régimen, bajo línea, carga y temperatura? ¿Qué efectos están ya incluidos en la tolerancia total y en qué punto físico se mide: antes del cable o en su extremo?
10. ¿Qué rizado y ruido de salida garantizan, con qué carga, temperatura, ancho de banda y método de medida? ¿Qué información espectral pueden aportar, indicando si es garantizada o típica? Para las excursiones al conectar la red, cambiar la carga, perder alimentación, desconectar la carga y recuperar el servicio, indiquen amplitud, polaridad, duración y repetición garantizadas.
11. ¿Qué carga capacitiva efectiva admite la salida al arrancar con la carga conectada? ¿Qué perfil de corriente y duración permite, y qué tensión mínima conserva durante ese arranque?
12. ¿Qué protecciones incorpora y cuáles no incorpora frente a cortocircuito, sobrecarga, sobretensión y temperatura? Para cada una, indiquen umbrales mínimo y máximo, tolerancias, tiempo de actuación, evolución de corriente y tensión y condiciones de repetición.
13. Cuando actúa cada protección, ¿cómo recupera la salida: por sí sola, por ciclos de rearranque, al retirar carga, mediante un mando o únicamente al quitar la red? Indiquen los tiempos garantizados y las condiciones exactas de rearme, incluyendo el arranque con carga tras recuperarse.
14. Nuestro equipo debe realizar un número limitado de reintentos con espera y dejar de alimentar el fallo si persiste. ¿Qué funciones y limitaciones de esta fuente permiten coordinar ese comportamiento? ¿Alguna protección exige una intervención manual o continúa enviando energía a un fallo permanente sin una condición de parada?
15. Ante un cortocircuito en el cable de salida, tanto próximo a la fuente como al extremo de la carga, ¿qué corriente, duración y energía puede entregar la fuente, incluyendo la descarga inicial y los pulsos posteriores? ¿Qué condiciones garantizan la supervivencia del cable suministrado y cómo recupera el servicio al retirar el corto?
16. La maniobra normal será conectar el cable con la fuente apagada, pero debemos cubrir una conexión accidental con la salida energizada. ¿Bajo qué carga capacitiva, corriente, transitorio y repetición garantizan que la fuente sobrevive? Indiquen las exclusiones y si actúa alguna protección.
17. ¿Qué tensión, corriente y energía aplicadas desde la carga soporta la salida cuando la fuente está encendida o apagada? ¿Admite una carga con tensión residual al reconectar? Indiquen límites, duración, repetición y posibles caminos de corriente hacia la fuente.
18. ¿Qué condiciones garantizan para desconexión, reconexión y rebote del contacto con energía residual en la carga? ¿Pueden estos eventos reiniciar la recuperación nativa o liberar un enclavamiento de la fuente?
19. ¿Pueden aportar el plano de polaridad de la terminación, visto desde un lado identificado, y las referencias de sus contactos y pareja compatible? Si suministran cable, indiquen longitud, calibre, resistencia máxima completa, condiciones térmicas, retención y alivio de tracción con sus ensayos.
20. ¿Qué informes o ensayos de los puntos anteriores pueden entregar para la referencia y configuración exactas, y qué comprobaciones requieren nuestra carga y cable definitivos para emitir una garantía?
