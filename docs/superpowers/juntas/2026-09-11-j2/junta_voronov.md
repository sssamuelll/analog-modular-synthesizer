## Voronov — lente ontológica, junta del 2026-09-11

La junta del 03-09 me dejó doce hallazgos; el décimo lo etiquetó el acta como «restricción invisible». Aquí está el siguiente. No es sobre el chip.

---

**1. «Defecto, luego no confiable» predica sobre el objeto equivocado.** «Confianza» no es un predicado sobre una pieza; es un predicado sobre el lazo que la rodea. La terna que lo hace evaluable es (clase de fallo, latencia de detección, cota de consecuencia). El papel firmado ya dice dónde estaba el problema, y no era el silicio:

> «el J2 tiene red de seguridad del lado del módulo y ninguna del lado del cerebro»
> — `docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md` §0

El defecto no cambió entre el 02-09 y el 03-09. Lo que cambió fue que un extremo del lazo pasó de no tener red a tenerla. Sin la terna, «confiable» no es un requisito: es un estado de ánimo. **Ley de orquestación:** todo sistema que reclame grado de instrumento sobre un componente programable tiene que enunciar su confianza como terna, o no ha enunciado nada.

---

**2. El criterio «defecto reportado, se descarta» tiene extensión vacía.** El candidato maduro obvio, el H7, trae cuatro limitaciones de SPI publicadas por ST, tres presentes en todas las revisiones de silicio:

> «A = la limitación está presente en esa revisión; no la corrigió ninguna revisión del H750/H753»
> — `es0396-h7-spi-2.14.2.md`, Tabla 3

Los reportes son función del uso, y el uso es función de la selección. Un criterio que descarta por reportes selecciona **opacidad**, no fiabilidad: premia al chip cuyos defectos nadie ha escrito todavía. Aplicado con honestidad, el criterio descarta el N6, el H7 y cualquier pieza con hoja de erratas — o sea, toda pieza con hoja de erratas. La dicotomía «maduro confiable / joven no confiable» no describe cantidad de defectos; describe **dónde están redactados**. El del N6 vive en un issue de GitHub; el del H7, en papel con membrete de ST. La legibilidad se compra con dinero de instrumentación, no cambiando de pieza.

---

**3. El camino maduro converge en la decisión que ya firmaste.** El usuario del H743, en C, con el HAL de ST, frente a la errata 2.14.2: las soluciones 1 y 2 de ST no bastaron.

> «lo curó `HAL_SPI_Abort()` antes de cada transferencia»
> — brief `junta-2026-09-11-brief.md` §3.3

Eso es D4: reinicio completo del periférico antes de arrancar. El fabricante maduro, con el chip maduro, el driver del fabricante y la errata publicada, **llegó al mismo mecanismo que tu spec firmada**. La recuperación no es el precio de elegir silicio joven. Es el precio de esta familia de bloque SPI. Cambiar de chip dentro de la familia te cobra los 70 archivos y te devuelve D4 intacta.

---

**4. Silicio o driver no cambia si se puede construir; cambia si la recuperación caduca.** El papel nunca afirmó lo que la pregunta de hoy le atribuye: dice «en el silicio **o** en su driver», sin diagnosticar. Y la razón real del driver propio no es el defecto:

> «el driver de embassy tal cual no sirve para el J2, no por el defecto del N6, sino porque sus dos esperas no son cancelables»
> — spec §1.2

El H7 es `spi_v4`; el N657, `spi_v5`; embassy los trata juntos. Bajo la rama «driver», mudarse al H7 **transporta el fallo** por la misma ruta de código. La disyunción solo gobierna una cosa: si `j2_spi.rs` tiene fecha de retiro (D8.2, el PR upstream) o si la recuperación es parte permanente del producto, como el 2.14.2 lo es del H7. Eso decide la forma del mantenimiento a diez años. No decide nada hoy.

---

**5. La restricción invisible no es ninguna de las tres candidatas.** Las dos posiciones — «lo resolvemos como fabricantes» y «nunca podríamos confiar en él» — son afirmaciones sobre **un número que nadie tiene**: la tasa en nuestro montaje, con NSS por hardware, `TSIZE > 0`, 8 kHz.

> «La única forma de medir: la Discovery STM32N6570-DK, $223,67 (#231), aplazada el 28-08 por decisión de Samuel: no hay plata»
> — brief §2

Aquí está lo que ninguna de las dos ve: el criterio que propones hoy es **el único criterio del proyecto que se puede evaluar sin placa**. Leer un hilo es gratis; medir cuesta $223,67. La opción C gasta 70 archivos, 43 commits, tres papeles firmados y el pase a embassy-stm32 para no gastar $223,67. El criterio no lo eligió el requisito del instrumento; lo eligió el presupuesto. Esa es la restricción que las dos posiciones orbitan: **el proyecto se comprometió a decidir la plataforma sin poseer el aparato que la mide**, y cada opción sobre la mesa es un reparto distinto de ese mismo hueco.

---

**6. Lo que firmaste el 10-09 fue una estructura, no una cifra.** El papel lo dice de frente, y es su mayor virtud:

> «Lo que este papel no midió y dice que no midió: todo lo marcado ESTIMADO en §3, la tasa real del defecto en nuestro montaje»
> — spec §12

El 102× de margen es el cociente de `T_REINICIO` ESTIMADO, `T_WATCHDOG_TRAMA` ESTIMADO y un plazo con `FACTOR_PLAZO` ESTIMADO. Es un cociente de tres estimaciones, no evidencia de confianza. Tu firma acreditó un mecanismo de recuperación; nosotros la leímos como si hubiera acreditado una conclusión sobre el silicio. No te contradices hoy: estás notando que firmaste una arquitectura y te la devolvimos como veredicto.

---

**7. Las cuatro opciones son una decisión y dos placeholders.** A y B son la misma decisión con distinto orden — el brief lo admite («Cambia el orden, no el diseño»); la única diferencia real es que B compra primero **información sobre cuál rama de la disyunción del §0 es cierta**, y esa información es el insumo de C y de D. C y D no son alternativas al diagnóstico: son **funciones del diagnóstico**. C necesita como premisa «el defecto es del silicio del N6»; D necesita «el defecto está localizado en el bloque SPI». Las dos premisas son exactamente la proposición que la spec §6 declaró que no puede evaluar y le asignó a upstream y a la Discovery. Y D rompe composición por dos lados: los dos extremos del J2 son N657, así que mudar el maestro no saca al esclavo del mismo silicio; y el periférico de destino está menos documentado que el que huyes:

> «USART síncrono del N657 como maestro, contra la hoja: las dos ranuras de repuesto de D3 dependen de ello»
> — `docs\superpowers\specs\2026-08-30-hub-n657-y-radios-design.md` §10, punto 3

D cambia un desconocido con 28 comentarios, volcado de registros, dos reportantes y errata publicada de su familia, por un desconocido con cero reportes y con el modo maestro aún sin verificar en la hoja. Y pierde la red: la spec §0 excluyó esas ranuras porque son «otro periférico con otra máquina de estados», así que D1-D8 no se mudan con el enlace. Reducir incertidumbre mudándose a lo menos documentado es una inversión ontológica, no una mitigación.

---

**8. Punto de presión: la puerta declara duración, no veredicto.** La opción A escribe «soak ≥ 24 h a 8 kHz con NSS hw + `TSIZE > 0` antes de fabricar cualquier PCB». Veinticuatro horas es una duración. No es un criterio de aceptación. Con el período reportado de 30-120 min, un soak de 24 h que reproduzca el defecto dará entre 12 y 48 cuelgues recuperados, y ningún papel dice si 12 es aprobado. La spec fue honesta al respecto: el coste de CPU va «impreso, sin aserto», la política de ranura `inestable` se delega a otro papel, y el único daño que de verdad cruza al músico quedó así:

> «función, sin cifra: los dos parámetros son de la Discovery y del músico»
> — spec §3, fila «Corrupción sin red (D6)»

Esa fila es lo que estás rechazando hoy. No el chip: el residuo sin cuantificar. Un `EVENTO` perdido es un golpe perdido, y su probabilidad se dejó como función sin número. **Bajo la condición «el CSV recibe su primera fila», el sistema producirá necesariamente un número sin umbral contra el que compararlo, y esta misma conversación volverá a ocurrir con la misma estructura.** No es un bug: lo que falta no es el dato, es el umbral. La junta del 03-09 te dio un testigo donde no había ninguno (V-10). La del 11-09 encuentra que el testigo declara y nadie sentencia.

---

**El invariante, para firmar o rechazar:**

**El SAM17 no selecciona piezas sin defectos; selecciona defectos con cota medida en nuestro montaje — y mientras esa cota no exista, no hay plataforma que decidir, solo un experimento sin pagar.**
