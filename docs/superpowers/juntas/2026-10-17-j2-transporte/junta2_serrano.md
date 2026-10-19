# Serrano · segunda pasada · papel-v3 (transporte «por tic» del J2) · 2026-10-17

*Informe de la segunda pasada sobre el `papel-v3.md` anterior a la absorción (commit `72d6e6f`). Texto del informe tal como lo entregó la lente.*

Referencias: v3 por sección. Spec por línea (`docs/superpowers/specs/2026-09-03-maestro-j2-recuperacion-design.md`). Código y `software/nucleo/fw/EN-PLACA.md` por archivo:línea. No modifiqué ningún archivo.

## A) Diagnóstico

- **Qué es.** Un papel de decisión: pide seis firmas (§1) sobre un diseño ya construido en banco y sobre dos mecanismos sin construir (§2.5 presupuesto de escaladas, §2.8 presupuesto de retraso). El título dice «enmienda a D5.1», pero §6 reescribe D2 y D4 y enmienda D8.
- **Implementabilidad.** §2.2 y §2.4 a §2.7 coinciden con `transporte_j2.rs` y `j2_tic.rs`. Lo nuevo no existe en código ni en modelo. La ficha A no está en condiciones de firmarse tal como se plantea.
- **Hallazgos.** 1 BLOCKER, 7 ALTA, 7 MEDIA (15, el máximo).
- **Método.** Cada cifra citada se contrastó con EN-PLACA.md y el código, línea a línea; la aritmética es a mano y los conteos son por grep. No ejecuté código.
- **Límite.** No pude abrir el manual (no hay renderizador de PDF). Las citas del RM que v3 usa quedan sin verificar: `GPDMA_CxCR.EN` bajado por hardware y p. 3449. El comentario de `j2_tic.rs:335-337` cita el RM con «[...]» dentro, justo lo que la spec prohibió en S-3.

## B) Hallazgos

**1. [BLOCKER] [CONTRA, ASSUMP] La ficha A (y §5.4) invierte el orden que firmó el acta y descansa en una premisa que no declara**
- **Evidencia.**
  - Acta ficha 2 (l.12): «el transporte se decide cuando haya una tabla de CPU del resto del hub y medidas de los dos transportes».
  - Acta l.24: «Si el transporte cambia o no. Eso lo decide el censo del hub junto con las medidas del prototipo.»
  - v3 ficha A: «El censo decide el presupuesto; no decide el transporte». v3 §5.4: «No bloquea el transporte; bloquea saber si 12,6 a 13,9 % cabe.»
  - v3 §1 («Firmado») resume la ficha 2 sin esa cláusula.
- **Problema.**
  - La ficha pide contestar lo que el acta reservó al censo, y no avisa de que se aparta.
  - El argumento es de dominancia: el tic cuesta menos que el ejecutor para todo presupuesto B < 48 %. Solo vale si B ≥ 48 % es inverosímil, y «no cabe en ningún reparto plausible» no define «plausible».
  - No hay dato: el censo tiene 11 filas y 0 cifras (`carga_hub_budget.py:101-118`). El primer brief decía del 15 %: «es el límite el que es de partida» (`junta-2026-10-17-brief.md:82`).
  - Dos soportes de la premisa fallan.
    - «no baja con más ranuras» es propiedad de la estructura medida: «cada una espera en su propio Timer» (EN-PLACA:715-716). EN-PLACA:731-734 dice: «con un solo `Timer` y una entrada de ejecutor repartidos entre las seis bajaría, y no se ha medido ninguna configuración así».
    - Los 8 000 / 8 167 son exploración sin región MPU (EN-PLACA:697-704: «Es exploración, no una fila de `carga_j2.csv`: la pasada con D-cache va sin la región MPU»). La tabla de §3 se titula «con I-cache, D-cache y la región MPU» y los compara con el tic, que sí la lleva.
- **Impacto.** Se firma sobre una descripción inexacta del acta. Si el censo concede ≥ 48 %, o si baja la configuración de un solo Timer, la respuesta cambia. Si concede menos de ~12 a 14 %, ninguno cabe y la ficha no resuelve nada.
- **Falta decidir.** ¿v3 pide enmendar la secuencia de la ficha 2 y lo dice? ¿Para qué rango de presupuesto del J2 es válido el «Sí», y quién lo fija sin censo?

**2. [ALTA] [GAP, SCOPE] Ficha A: el costo del «Sí» no figura, y opciones vivas de la primera pasada desaparecen sin cerrarse**
- **Evidencia.**
  - La ficha solo lista «Lo que cuestan las otras». Alternativas citadas: «Esperar al censo» y «#436, opciones 2 y 3».
  - Primer brief §5: opción D («un solo `Timer` para las seis») y E («No explorada»).
  - v2 §8 S12: «sigue sin medirse una configuración con un solo `Timer`».
  - Spec D5.1(3), l.293: «Una tarea de pantalla que retenga la CPU 15 ms no retrasa un giro del J2 ni un microsegundo».
- **Problema.** Costos reales del «Sí» que el propio papel documenta y la ficha omite:
  - El aislamiento frente al hilo (H-9) se cambia por promesas del hub que hoy no existen (R-H1, R-H2, R-H4). La primera pasada ya lo señaló (hallazgo 14.8).
  - Seis SPI y doce canales del GPDMA1 a mano para siempre: v2 §6 dice que la salida upstream de D8.2 «pierde su sujeto».
  - Se descarta la evidencia del ejecutor (ficha F).
  - Los costos de B a F son consecuencias de A.
  - El «costo» de «Esperar» («no puede tener un J2 que quepa hasta que el censo exista») es la premisa del hallazgo 1 repetida, no un costo.
  - D y E ni se mencionan ni se cierran.
- **Impacto.** Una decisión con un lado sin precio.
- **Falta decidir.** ¿Cuál es el costo del «Sí»? ¿D y E se cierran con dato, o se declaran abiertas?

**3. [ALTA] [GAP, OPS, STATE] «Muerta ⇒ el IWDG reinicia el chip» descansa en un supervisor que no existe, y ninguna condición de §5 lo exige**
- **Evidencia.**
  - §2.5: «deja de sellar, el IWDG del hub reinicia el chip». §6 D5.4: «igual».
  - Spec §10 (l.588, 616, 619): supervisor de vitalidad «pendiente». La fila de l.619 quiere cambiar el sello a «armé y alguno de los últimos N terminó».
  - No hay código de IWDG ni de supervisor en `fw/src` (solo comentarios, `j2_ejecutor.rs:86-87,162-165`). La prueba D de EN-PLACA:850 solo mide que «el sello del IWDG se queda quieto».
  - R-H1 a R-H7 y §5.2 no incluyen supervisor.
- **Problema.**
  - El único destino de una ranura `Muerta` nunca se ejerció, y la regla del sello choca con una fila pendiente de la spec.
  - Spec D5.4 (l.294): «no al completarla: una ranura reiniciando también está viva». En v3, `Vencida` y `Reiniciando` no arman ni sellan hasta 25 ms por diseño. La relación entre la ventana del supervisor, esos 25 ms y T_IWDG (> 50 ms) no está escrita.
  - La ficha C («Nada») más «sello al armar» acopla «planificador atrasado» con «reset del chip» (la primera pasada, hallazgo 6, ya advertía «El sello al armar (D5.4) pasa a depender de que el planificador haya entregado»).
  - El silencio que añade el arranque del cerebro es HUECO desde la spec (l.294) y v3 no lo cuantifica.
  - El punto 5 de la enmienda 16-10 («El IWDG lo alimenta el hilo»), que hace operativo todo esto, vive en una enmienda que §2.9 da por «desaparecida» sin acotar.
- **Impacto.** El transporte puede entrar al instrumento con su red de seguridad sin definir, y la ficha B no dice que su «Sí» termina en reinicio del instrumento.
- **Falta decidir.** ¿Cuál es la regla del supervisor (ventana, ranuras que cuentan, T_IWDG)? ¿Es condición de entrada?

**4. [ALTA] [CONTRA, GAP, ASSUMP] Ficha B y §2.5: el presupuesto de escaladas no se sostiene como está planteado**
- **Evidencia.**
  - Ficha B, costo de «Tope de 1»: «se llevaría la ranura por una sola escalada legítima». §2.5: «Una avería que toca varias ranuras a la vez produce **una** escalada».
  - §2.5: «varias seguidas indican un canal que no se arregla con un reset»; «La política no cambia».
  - §2.1: el estado «nadie más lo escribe, salvo `ReinicioHecho` y la marca de escalada».
  - §8: «H4 … presupuesto de 3 por segundo». `junta_halberg_codigo.md:20` (H4) pedía además «una decisión de la junta sobre cómo cuenta la política (D7) una transferencia que mató la escalada de otra».
- **Problema.**
  - (a) El costo atribuido a «Tope de 1» exige lo que §2.5 niega. `tic_recupera` fase C lo respalda en un caso: 10 escaladas forzadas dan exactamente 10, con dos vecinas en vuelo (EN-PLACA:850).
  - (b) El criterio «3 < 10» lo cumple cualquier tope entre 1 y 9; el 3 no está derivado. No figura como ESTIMADO en §7 ni está atado a `umbral_inestable` (R-MJ4).
  - (c) El contador es global y mata a «la ranura que la pide». Eso castiga a quien llega, no a quien agota el presupuesto, y «un canal que no se arregla» solo se infiere si las cuatro peticiones son de la misma ranura.
  - (d) La mitad de H4 (cómo cuenta D7 el `PlazoVencido` ajeno) se decide por omisión: contamina la ventana de las vecinas hasta 3 de 10, y la frase D5.1(1) «un cuelgue en una no ensucia la ventana de las demás» (l.291) sigue sin enmendar. §8 da H4 por resuelto.
  - (e) No se escribe cómo se llega a `Muerta`: la recuperación (nivel 4) tendría que escribir el estado que §2.1 reserva al tic, y no se dice si es inmediato o por las cotas de 100 tics.
  - (f) Una sola ficha mezcla dos decisiones: cotas y presupuesto.
- **Impacto.** Se firma un número y un castigo sin derivación ni dueño.
- **Falta decidir.** ¿De dónde sale 3? ¿Quién escribe `Muerta`, y a quién se le atribuye? ¿Cómo cuenta D7 el plazo ajeno? ¿Cotas y presupuesto se firman juntos o por separado?

**5. [ALTA] [CONTRA, SCOPE] El límite firmado «cero artefactos audibles atribuibles al bus» no aparece en v3, y v3 añade exposiciones**
- **Evidencia.**
  - Spec l.518 (acta 11-09): «cero artefactos audibles atribuibles al bus».
  - v2 R-H3: «cada recuperación escalada del J2 es un artefacto audible». v3 R-H3 ya no lo dice.
  - La búsqueda de «audible» y «artefacto» en v3 da 0 resultados.
  - §2.5: «una avería de una ranura le cuesta una transferencia a las otras cinco». §2.8: «cuesta un giro por ranura y una recuperación, no el instrumento».
- **Problema.**
  - `EVENTO` no tiene red (D6): un golpe perdido es audible. La función de D6 (l.381) es de una ranura. Con la escalada, hasta 5 vecinas en vuelo pierden su transferencia, y con un tic tardío hasta 6.
  - Si el escritor de CV comparte el GPDMA1 (R-H3, HUECO #367), cada escalada es audible. El presupuesto permite hasta 3 por segundo.
  - `Muerta` es silencio total.
  - Ninguno de estos casos se evalúa contra el límite.
- **Impacto.** Se adopta un mecanismo sin comprobar que cumple el límite que descartó cambiar de chip.
- **Falta decidir.** ¿Qué cuenta como «atribuible al bus» para escalada, tic tardío y `Muerta`? ¿Con qué función se calcula?

**6. [ALTA] [CONTRA, GAP] §2.8: «Un atraso no mueve `inestable` ni `muda`» es falso cuando el atraso rompe el presupuesto, y la derivación de 60 µs no coincide con el código**
- **Evidencia.**
  - §2.8: «Un atraso no mueve `inestable` ni `muda`» y «todas las ranuras armadas en ese tic vencen a la vez».
  - `maestro_j2.rs:375-379` (`PlazoVencido` → `plazos_vencidos += 1; anota_plazo; Reiniciar`) y `:418-426`. `transporte_j2.rs:240-243`.
  - §2.8: «84 µs para un `NADA`, 98 para un `EVENTO` y 64 para un `TONO`». `maestro_j2.rs:150-153`. `transporte_j2.rs:327-328` (`tics_de_plazo(126, 125) == 2`).
  - EN-PLACA:848: «el retardo máximo del tic al entrar fue de 0 µs».
- **Problema.**
  - (a) Un tic con retraso por encima del presupuesto produce un `PlazoVencido` real en cada ranura de plazo 1. La política no distingue causa: cuenta, marca y manda `Reiniciar`, que resetea por RCC un SPI sano a mitad de trama. Diez tics tardíos en 1 s dejan `inestable` en las seis ranuras. La frase solo vale por debajo del presupuesto; es la regla del 16-10 punto 2 sin su condición.
  - (b) 84, 98 y 64 µs son aritmética (125 − 8,8 − t_trama a 6,25 MHz) sin etiqueta. El TONO de 41 B a 6,25 MHz no es de plazo 1 en el código: `plazo_us` redondea `t_nominal` a 53 µs, da 2×53+20 = 126 µs y por tanto 2 tics. v2 §2.4 decía «125 → 1» y v3 lo hereda. Los 64 µs que dejan 4 µs de margen sobre 60 son de un mensaje que el código trata con 2 tics.
  - (c) El presupuesto nunca se ejerció: el retraso máximo fue 0 µs en 600 s. El caso XSPI e I-cache fría está «sin medir». Los 8,8 µs son con cachés calientes; con D-cache fría el tic va a 1 528 ciclos por ranura (EN-PLACA:839), es decir 11,5 µs para seis.
- **Impacto.** La consecuencia de romper el presupuesto es peor que lo que v3 dice, y el número que lo ajusta no sale del código.
- **Falta decidir.** ¿Cómo clasifica D7 un `PlazoVencido` causado por CPU? ¿Qué tabla de plazos en tics rige a cada reloj del SPI, y quién la genera?

**7. [ALTA] [GAP, ASSUMP] Ficha D cuenta una latencia (la subida) y no la cadena que importa**
- **Evidencia.**
  - Ficha D: «de 65 a 90 µs más que con la ISR del EOT» y «Es el 6,5 al 9 % del objetivo de 1 ms mano→DAC».
  - `j2_ejecutor.rs:346` (`bajada_fn` se llama al armar) contra `j2_tic.rs:918, 928, 852, 964-1017`.
  - Primera pasada, hallazgo 6: «Latencia nueva de un periodo entre decisión y cable, también para el `EVENTO`». v2 §2.6 decía «no cambia para la bajada» y v3 lo omite.
  - `latencia_mano_budget.py:199-205` sale con 2 (HUECO).
- **Problema.**
  - La cadena mano→DAC es subida (mandos), compone, bajada (Voz). Con el tic, la subida se cierra en el tic n+1, el planificador compone después y la bajada solo puede armarse en el tic n+2. Con el ejecutor, la Voz componía al armar.
  - El efecto de extremo a extremo está cuantizado a la rejilla y llega a un periodo (125 µs, 12,5 % de 1 ms), no a 65 o 90 µs.
  - El porcentaje es del objetivo, no del margen que queda: el guion no calcula línea base (faltan T_CONVERSION_US y TAU_RC).
  - La pregunta que v3 deja a la junta sobre D7 (§2.6) tiene respuesta aritmética. `muda` son 40×125 µs = 5 ms, así que sube un periodo más tarde (+2,5 %). `inestable` cuenta plazos y no depende de la subida.
- **Impacto.** Se acepta una latencia sobre el producto más caro del instrumento con la mitad de la cuenta.
- **Falta decidir.** ¿Qué latencia máxima subida→compone→bajada se acepta, medida de extremo a extremo?

**8. [ALTA] [GAP, OPS] La puerta no puede fallar sobre el caso malo, y §5.1 declara «hecha» una fila que el repositorio no tiene**
- **Evidencia.**
  - `recuperacion_j2_budget.py:251-256` (`mejor = min(en_diseno)`; `assert mejor <= limite`) y `carga_hub_budget.py:96` (`mejor = min(a_diseno)`).
  - Spec l.312 (enmienda 16-10): «falla si una fila a 800 MHz lo pasa». v3 §5.2(a): «hoy la puerta toma el mínimo de cualquier fila a ≥ 800 MHz».
  - v3 §5.1: «la fila de `carga_j2` con la definición de la ficha 1, hecha». v3 §1: «la fila de `carga_j2.csv` espera a que el CSV tenga la columna `transporte`».
  - EN-PLACA:805: «`carga_j2.csv` no tiene filas suyas». El CSV tiene 3 filas, todas a 64 MHz.
- **Problema.**
  - La puerta pasa con la mejor fila y no mira `cache`, `ranuras` ni `periodo` (primera pasada, hallazgo 13.2). §5.2(a) corrige solo la columna `transporte`.
  - Con una fila caliente de 1 967 y otra fría de 2 778, la puerta pasa. El texto firmado dice lo contrario del código («falla si *una* fila lo pasa» frente a «falla si la *mejor* lo pasa»).
  - El riesgo 9 cierra con «una fila a 800 MHz ≤ 2 500» sin decir qué régimen de caché es «el del hub».
  - El `return 2` fijo (#369) sigue pendiente.
  - §1 y §5.1 se contradicen. La medida existe como prosa de EN-PLACA y `carga_j2.py` se niega a anotarla. El acta (lo que sigue, 1 y 3) pide la fila con las dos definiciones.
- **Impacto.** Las condiciones 5.2(a) a (c) no pueden verificar lo que v3 dice que verifican.
- **Falta decidir.** ¿Qué estadística usa la puerta, con qué filtros? ¿Qué es una «fila hecha»?

**9. [MEDIA] [AMB, GAP] «12,6 a 13,9 %»: de dónde sale y qué le falta**
- **Evidencia.**
  - §3: «Un CRC por tabla a unos 5 ciclos por byte suma de 125 a 350 ciclos según el mensaje».
  - Acta ficha 1: armar y cerrar, tic o ISR, DMA, CRC del sobre y contadores de salud; no cuenta componer.
- **Problema.**
  - Sale de la ficha 1: 1 967 (enlace solo, 3 ranuras, cachés calientes) + CRC estimado = 2 092 a 2 317 ciclos, que con 48 000 giros/s dan 12,55 % y 13,90 %. La aritmética cuadra.
  - Falta lo siguiente.
    - Los 5 ciclos por byte no tienen fuente ni medida en el repo. La pendiente medida del enlace entre 25 y 71 B es 5,1 ciclos por byte, y eso no es un CRC.
    - Cubre el bucle del CRC, no la validación del sobre. El juez de juguete (~12 ciclos) sigue dentro de los 1 967.
    - La tabla de 512 B con D-cache fría no está contada.
    - Con caché fría más CRC: 2 903 a 3 128 ciclos (17,4 a 18,8 %) con la base del medidor, o 2 717 a 2 942 (16,3 a 17,7 %) con la del DWT. v3 dice «y con el CRC, más» sin cifrar. El «margen de 183 a 408 ciclos (7 a 16 %)» vale solo con D-cache caliente.
    - Seis ranuras: extrapolación. El ruido entre compilaciones no se acota.
  - Doble contabilidad tic/planificador: no la encontré. 1 175 + 823 = 1 998 contra 1 967 del medidor (la instrumentación pesa ~100 ciclos, EN-PLACA:830) y el perfil resta el tic anidado (`j2_tic.rs:1020-1026`).
- **Impacto.** El rango que lee Samuel es el favorable. Con caché fría, todas las variantes pasan del 15 %.
- **Falta decidir.** ¿Cuál es la cifra del J2 en el censo: caliente o fría? ¿Quién mide el CRC y el juez reales?

**10. [MEDIA] [AMB] Cifras sin estatus, o con el estatus equivocado**

| Cifra (v3) | Qué es | Lo que v3 dice | Observación |
|---|---|---|---|
| «≤ 8,8 µs» (§2.1, §2.8) | 6 × 1 175 ciclos / 800 MHz. 1 175 es el promedio DWT por ranura y giro con 3 ranuras, cachés calientes | §2.1 «no medido»; §2.8 lo usa sin decirlo | Frío: 11,5 µs. «El tic mide 4,4 µs» es 3 × 1 175 / 800, un promedio, no una duración de pared ni un máximo |
| «84 / 98 / 64 µs» (§2.8) | 125 − 8,8 − t_trama a 6,25 MHz | nada | TONO: ver hallazgo 6 |
| «65 a 90 µs», «6,5 a 9 %» (ficha D) | 125 − c, con c = 35 a 60 µs; ÷ 1 000 µs | nada | Depende de 6,25 MHz y de la posición en el tic. El % es del objetivo, no del margen |
| «3 por segundo» (ficha B) | Deducido de `umbral_inestable` = 10 (ESTIMADO) | «sale de D7.3» | Fuera de la lista de ESTIMADO de §7 |
| «60 µs» (R-H2, §2.8) | 64 − 4 | nada | Ídem |
| «125 a 350 ciclos» (§3) | 5 ciclos/byte × 25 a 70 B | «a unos 5 ciclos por byte» | Sin fuente |
| «249 µs … primera trama buena» (§0.4, §2.4) | Marca `cstart_siguiente`, tras `hw.arma` de la siguiente trama (`tic_recupera.rs:223`, `j2_tic.rs:878-886`) | «medido» | Es el inicio de la trama, no su cierre, y una sola muestra. Se compara con el «techo de 395 µs» de v2, definido de otro modo. 249 + 32 µs de trama = 281 µs, que coincide con los 284 µs simulados por Halberg (v2 §2.4). El «200×» sale de un punto de referencia distinto |
| «123 / 131», «6 µs», «1,2 / 1,5 µs» | Marcas `DWT` de un incidente | «medido» | EN-PLACA:892: «se supone que el CS sube en cuanto el SPI suelta el pin». §4.2 no lo lista como no ejercido |
| «2 778 → 16,7 %» (Resumen, §3) | Medidor del hilo con el artefacto que reconoce EN-PLACA:841 | «medido» | El DWT da 2 592 (15,5 %). §0.6 usa «+600 a +700» (base DWT) y la tabla +811 (base medidor) |
| «8 000 / 48 %» (§3) | 8 000 × 48 000 / 800 M. Con 3 ranuras, 8 167 = 49 % | «con las mismas cachés» | Exploración sin MPU (hallazgo 1). Las filas del tic usan 3 ranuras y la del ejecutor 1 |
| «(146 ciclos)» (§3) | Compositor de mentira | nada | Sin fuente en el repo. EN-PLACA:807 dice «unos 170»; el acta, 155; la diferencia de la tabla, 133 |
| «T_CANAL = 25 µs» (§2.5) | Constante elegida | v2: ESTIMADO | v3 pierde la etiqueta en §2.5 y en «Los números ESTIMADO que quedan» (§7) |
| «unas decenas» (§2.6, `ldm` de 25 B) | | | EN-PLACA:766 mide 96 ciclos por 32 B |
| «nueve mutaciones, todas con una prueba en rojo» (§4.1, `marcos_j2`) | | | Sin rastro en `marcos_j2.rs` ni en EN-PLACA. La del buzón sí tiene fuente (`junta_halberg_codigo.md:9`) |

Además, el Resumen («ha aguantado 4,7 millones de marcos numerados bajo … retenciones de la CPU») omite tres cosas:
- Los golpes eran de P3, no de P2 (EN-PLACA:877).
- Fue con `pines-medio`: el binario no compila sin él (`tic_estres.rs:34-37`).
- Fue con 1 ranura con esclavo.

Su lista de «lo que no se ha probado» omite un módulo real, el CS con analizador (EN-PLACA:892) y los 12 de 16 contenidos que fallan a `VeryHigh`. Los «esclavos de relleno» de §4.2 son maestros sin módulo (EN-PLACA:650-651).
- **Falta decidir.** ¿Qué etiqueta lleva cada cifra (medida, estimada o aritmética) y con qué condiciones?

**11. [MEDIA] [ASSUMP, GAP] Las cotas de 100 + 100 tics: evidencia circular, requisito mal acotado y tic = 125 µs sin compensar**
- **Evidencia.**
  - §2.5: «sobrevive a una retención de P2 de 12 ms … y muere con 14». `tic_cota.rs:36-39`.
  - R-H1: «ninguna ISR de P2 retiene al planificador más de 12 ms».
  - `j2_tic.rs:786-793`. `transporte_j2.rs:26-30`.
  - `T_WATCHDOG_TRAMA_US` (`maestro_j2.rs:27-32`) no se enlaza con las cotas.
- **Problema.**
  - (a) «Medido» verifica que 100 tics son 12,5 ms, es decir la constante, no que 12,5 ms sea el valor adecuado.
  - (b) R-H1 acota cada ISR, pero la muerte viene de la inanición acumulada. P2 encadenado más el WCET del propio planificador, que sostiene a la recuperación (P4), pesan en dos esperas sucesivas. El compositor real no existe.
  - (c) «100 tics = 12,5 ms» supone ningún tic fundido: el tic suma 1 por entrada aunque cuente `fundidos`, y edad, espera y reloj de la política se estiran. `tics_fusionados` no tiene umbral ni condición de aceptación.
  - (d) Se justifican contra los ~50 ms, que son ESTIMADO con techo HUECO de voz-total. Ningún guion ni aserto los ata (ni las otras constantes nuevas: 3/8 000, 60 µs, T_CANAL), contra R-MJ4. El margen ≥ 10× del guion baja a ~2× (25 ms contra 50 ms) en el peor caso, sin decirlo.
- **Falta decidir.** ¿Qué acota el tiempo acumulado de inanición? ¿Quién enlaza las cotas con la ventana del módulo?

**12. [MEDIA] [GAP, OPS] §5: condiciones imposibles, inverificables o ausentes**
- **Evidencia.**
  - §5.2(d): «un `tic_estres` con tres o más ranuras con esclavo (hoy el banco tiene un solo esclavo)».
  - `j2_spi.rs:147-154` (`SPI_DE_RANURA`). EN-PLACA:809 y :877. §5.1: «las medidas 2 y 3 de v2 §4 limpias, hechas».
- **Problema.**
  - El chip tiene seis SPI. Seis maestros (5.2(b)) no dejan ninguno como esclavo; tres pares (5.2(d)) usan los seis, y SPI4 (el esclavo actual) es la ranura 1 del hub. No son la misma configuración y v3 no lo dice.
  - El esclavo comparte el GPDMA1, así que cualquier escalada lo mata, y es una tarea de P2, así que los golpes de P2 le pegan. (d) no puede cubrir escalada ni P2.
  - Ambas piden SPI3 y SPI6; v3 no establece que la Nucleo exponga pines para esa función alterna.
  - «limpio» no lleva N, duración ni criterio (la spec usa 3/T).
  - La medida 2 de v2 §4 pedía «una escalada forzada con cinco vecinas en vuelo» y «qué hueco ve el módulo»; se hizo con dos vecinas y sin esclavo (`tic_recupera.rs:18-21`).
  - Faltan condiciones que el diseño necesita:
    - R-H1 a R-H4 aceptados por el hub.
    - El supervisor (hallazgo 3).
    - Cualquier evidencia de una escalada real. §7 la declara imposible en banco, aunque la spec la cierra «pausando un canal por registro» (l.495), que no produce un canal que ignore SUSP.
  - §5.3 no dice qué contenido ni qué pines usa el soak de 24 h.
  - La ficha F dice «columna `transporte` en los CSV», pero 5.2(a) solo habla de `carga_j2.csv`. El costo de «Menos» (44,7 millones de transferencias y 24 h) no es lo que 5.2 exige (el soak está en 5.3), y esa evidencia del ejecutor no es a 8 kHz.
- **Falta decidir.** ¿Qué configuraciones de banco, y con qué criterio numérico, satisfacen (b) y (d)? ¿Qué entra en «Menos»?

**13. [MEDIA] [GAP, ASSUMP] R-H7 y ficha E: requisito circular y criterio de aceptación frágil**
- **Evidencia.**
  - Ficha E: «pase `tic_contenidos` (16 de 16) y un `tic_estres` limpio antes de fabricarlo». §5.3: «y el arnés del J2 con R-H7».
  - Spec l.606: «no es alcanzable con el kernel de hoy». `tic_estres.rs:34-37`.
  - §4.2: la causa física «no se midió con osciloscopio».
- **Problema.**
  - «El arnés real» es el objeto que se fabrica: el requisito pide validar antes de fabricarlo lo que existe después.
  - «Su reloj de diseño» (34,5 MHz) no es un valor que produzcan los divisores. Con pclk2 = 100 MHz salen 50, 25, 12,5 y 6,25 MHz, y todo el banco corre a 6,25 MHz.
  - Dieciséis contenidos elegidos a mano no cubren contenido arbitrario: a `VeryHigh` fallan 12 por un mecanismo no medido.
  - `tic_estres` solo corre con `pines-medio`, nunca en la condición que R-H7 exige.
  - Qué objeto es «el arnés» (cinta de 74 cm, PCB, prototipo) y cuándo existe: Not specified.
- **Falta decidir.** ¿Qué objeto se valida y cuándo existe? ¿A qué reloj?

**14. [MEDIA] [STATE, AMB] La tabla de §2.2 no está completa respecto del código ni de las reglas que cita**
- **Evidencia.**
  - §2.2: «Todo estado de espera tiene una cota en tics» y «`Muerta` es absorbente». R-MJ2 reescrita: «ninguna espera es un bucle síncrono sin cota ni un estado sin salida».
  - `transporte_j2.rs:223, 252-265`. `maestro_j2.rs:366-368`. `j2_tic.rs:1000-1007, 704, 735, 1049`.
  - Spec l.640: «hacía absorbente el estado enfermo».
- **Problema.**
  1. `Muerta` es un estado sin salida: contradice la frase con que v3 cumple R-MJ2, la de D7.1 («gira … siempre») y lo que la primera junta mató. §6 dice D7 «igual».
  2. `Libre` sin bajada fresca espera sin cota, y la ficha C lo vuelve regla.
  3. Identidad y recuperación:
     - La política en `Vacia` responde `Nada` a `PlazoVencido`.
     - El planificador pide el reinicio solo si la política dice `Reiniciar`.
     - Si la identidad se retira con la ranura `Vencida`, nadie pide el reinicio y la ranura va a `Muerta`. Sin salida, si el módulo vuelve queda una ranura activa que no sella.
     - En placa la identidad se fija una vez, y la propiedad de §4.1 («vuelve a Libre o a Muerta») no cubre cambios de identidad.
  4. Orden no escrito: `Vencida` con `reinicio_hecho` y `espera ≥ 100` en el mismo tic (el código da prioridad a `reinicio_hecho`; la tabla lista ambas). La fila de `T_GAP_REARME` de v2 ya no figura.
  5. `Libre` sin identidad no está en la tabla.
  6. El paso 1 de §2.5 dice «sondear `SUSPF`»; el código acepta también `IDLEF`. Sin esa aceptación, un canal ya terminado (EN = 0) escalaría por nada y gastaría presupuesto.
- **Falta decidir.** ¿Cuál es la tabla completa de transiciones, con precedencias y la salida de `Muerta`? ¿Qué pasa con la identidad en cada estado?

**15. [MEDIA] [CONTRA, SCOPE] Frases de la spec que v3 vuelve falsas o ambiguas y que §6 no lista**

| Frase de la spec | Dónde | Por qué |
|---|---|---|
| «El planificador gira a 8 kHz por toda ranura activa, siempre» / «Lo que NO decide este papel: qué hace el instrumento con una ranura `inestable` o `muda`» | D7, l.341 y 350; §6 fila 1 | `Muerta` por presupuesto es política de salud decidida en el transporte; §6 dice D7 «igual» (hallazgos 3, 4, 14) |
| «un cuelgue en una no ensucia la ventana de las demás» | D5.1(1), l.291 | Hasta 3 de 10 por diseño (hallazgo 4); ya era falsa desde el 18-09 |
| «una ranura reiniciando también está viva» | D5.4, l.294 | Hasta 25 ms sin sellar (hallazgo 3) |
| «El IWDG del hub deja de ser la cobertura del riesgo 6» | D4.2, enmienda 18-09, l.230 | Vuelve a serlo como consecuencia diseñada |
| «No mueve `inestable` ni `muda`» | Enmienda 16-10, punto 2 | Hallazgo 6 |
| Enmienda del 16-10 (puntos 3 a 5 y el 15 % firmado) | §2.9: «desaparecen … las enmiendas … del 16-10» | §6 acota a `Calendario`, §2.9 no; el límite firmado y el IWDG desde el hilo viven en esa misma enmienda |
| `P(golpe perdido) = 3 × P(EVENTO)` | D6 y §3, l.381 | Cuatro valores en circulación: 3 (spec), 4 (`round(490/125)`, `recuperacion_j2_budget.py:223`), 5 (v2 §2.4) y 2 medido para NADA (480 412 − 465 414 = 14 998 giros por 7 500 recuperaciones, EN-PLACA:872-874). v2 §6 marca D6 «igual» |
| `T_REINICIO` = 20 µs, ESTIMADO: «16 % por ranura» | D7.2 y §3, l.374 | Medido 6 µs; el guion sigue en 20 (`recuperacion_j2_budget.py:52`) |
| «fórmula igual» y riesgo 2: «≥ 3× el peor exceso medido» (l.491) | §6 D3 | El plazo efectivo en µs es 125 − posición − δ, no la fórmula; el criterio lo sustituye el presupuesto de 60 µs |
| Cierre del riesgo 6: «pausarlo por registro desde otra tarea» | Spec l.495 | Pausar no produce un canal que ignore SUSP; v3 §7 dice «no hay forma» sin decir que el criterio es inejecutable |
| «Viven en un solo `struct Umbrales`» | R-MJ4, l.395 | Cotas, 3/8 000, 60 µs y T_CANAL sin casa ni aserto (ya señalado en el hallazgo 15 de la primera pasada) |
| Alcance | Título y §6 | D2 y D4 (firmadas «sin matiz», l.669) y D8 (la salida upstream) se reescriben; ninguna ficha las pide por separado |

## Lectura de las seis fichas

| Ficha | ¿Se contesta sin leer el resto? | Costo del «Sí» | Qué decisión falta o está mal planteada |
|---|---|---|---|
| A | No: depende de §5, de un censo inexistente y de #436 | No figura (hallazgo 2) | El orden del acta (1); D y E (2) |
| B | No: «Muerta» se define en §2.2 y el IWDG en §2.5 | No figura: reinicio del chip, silencio sin cuantificar (3) | Dos decisiones en una; el 3 sin derivación (4) |
| C | Casi | No figura: sin tramas ≥ 50 ms el módulo suelta las notas; `Libre` sin cota (14); acople con el sello (3) | La ficha trata «relleno» y «segundo escritor» como lo mismo; no separa quién produce el relleno de quién escribe la `secuencia` |
| D | No | No figura: la cadena extremo a extremo (7) | La ficha opone «+65 a 90 µs» a «16 kHz»; este último altera las cifras de A |
| E | No | No figura: bloquea fabricar contra un arnés que aún no existe (13) | Arnés de prototipo frente a arnés de producción |
| F | No | No figura | «Menos» sin definir; «los CSV» no es 5.2(a) (12) |

A es la raíz y B a F son consecuencias. Las alternativas de C y D cambian la máquina o la CPU de A y no se propagan a sus cifras.

## Comprobado y correcto

- La aritmética de §3 y de la ficha 1 cuadra:
  - 11,8 / 12,6 / 13,2 / 16,7 %.
  - 2 092 a 2 317 ciclos = 12,6 a 13,9 %.
  - 183 / 408 ciclos = 7,3 / 16,3 %.
  - 6,2 días, 4,4 y 8,8 µs, 65 a 90 µs, 128 × 5/6 ≈ 107.
  - Lo único que no es redondeo estricto es «94 %» (da 94,6) y que el ejecutor use 1 ranura y el tic 3.
- Las cifras de banco que v3 cita coinciden con EN-PLACA:
  - 400/300 µs y 12/14 ms; 123/131/249 µs; 6 µs; 1,2/1,5 µs; 650 ns.
  - 4 799 999 giros; 1 894 419 y 4 727 452 marcos.
  - 11 570 + 2 963 = 14 533 y 29 209 + 7 342 = 36 551, también por fase.
  - 4 de 16 y 16 de 16; 65 / 2 102 / 6 904 tramas sin bajada fresca.
  - 1 967 / 2 100 / 2 778 / 15 773 / 17 900.
- El orden de filas de §2.2 coincide con `Transporte::paso`: error DMA > giro completo > plazo, y `reinicio_hecho` > `reinicio_en_curso` > cota.
- 59 pruebas de integración (grep). Las unitarias son 347 por grep contra 346 declaradas (±1, sin consecuencia).
- Sin doble contabilidad tic/planificador (hallazgo 9).
- La cita de la ficha 1 en v3 §1 es fiel al acta.

## C) Preguntas que el documento evita

1. ¿Qué evidencia hay de que un canal del GPDMA1 deje de contestar a SUSP? Sin ella, el presupuesto de escaladas protege de un fallo nunca observado y su único efecto observable sería el reinicio del chip.
2. ¿Qué regla del supervisor hace que `Muerta` provoque el reinicio, y cuánto silencio añade el arranque del cerebro?
3. ¿Cómo cuenta D7 un `PlazoVencido` que no es de la ranura (escalada, tic tardío)?
4. ¿Qué es «audible» para el límite de cero artefactos? ¿Entran el reinicio del chip y un `EVENTO` perdido por una escalada ajena?
5. ¿Qué latencia máxima subida→compone→bajada acepta el producto?
6. ¿Para qué rango de presupuesto vale el «Sí» de la ficha A, y quién lo declara sin censo?
7. ¿Qué objeto es «el arnés real» y cuándo existe?
8. ¿Qué acota el tiempo acumulado de inanición del planificador (P2 más el WCET del compositor real)?
9. ¿Qué estadística de la puerta decide «cabe en 15 %» con cachés calientes y frías?

## D) Riesgos por categoría

- **Técnico:** 3, 4, 6, 11, 14 (y 9, 10).
- **Producto:** 1, 2, 5, 7, 13.
- **Ejecución y operaciones:** 3, 8, 10, 12, 15.

## E) Aclaraciones inmediatas (solo BLOCKER)

1. **Ficha A (hallazgo 1).** ¿v3 pide enmendar la secuencia que fijó la ficha 2 del acta, y lo dice? ¿Para qué rango de presupuesto del J2 es válido el «Sí»?

Fuera del BLOCKER, las ALTA 3 a 8 cambian lo que se le pregunta a Samuel (fichas B y D) o lo que dicen verificar las puertas. Conviene cerrarlas antes de la firma.
