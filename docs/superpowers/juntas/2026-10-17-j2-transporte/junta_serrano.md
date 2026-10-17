INFORME DE SERRANO. Junta J2 del 2026-10-17 (transporte). Solo lectura: no edité ningún archivo.

## A) Diagnóstico

- Documento: propuesta de enmienda de arquitectura (papel-v1, sin firmar) más su brief. Sustituye el transporte firmado de D5.1 (una tarea por ranura en un `InterruptExecutor`) por máquinas de estado movidas por un tic de TIM7 y por los EOT, con planificador y recuperación D4 en P3.
- Implementabilidad hoy: baja. Las dos decisiones que hacen el diseño implementable y comprobable (cómo se vigila el plazo; qué cuenta como «el J2» del límite) siguen abiertas dentro del texto que pasaría a la spec. Las condiciones de §5 no las puede evaluar la infraestructura de puertas actual.
- BLOCKERS: 2 (hallazgos 1 y 2). HIGH: 10. MEDIUM: 3. Total 15 (el tope).
- Comprobado contra EN-PLACA y el código, y correcto: la tabla de §3 del brief; 333+1 479+549+345 = 2 706; 5 810−2 706 = 3 104; 8 000−5 810−244 = 1 946; 6 278−2 428 = 3 850 (con 2 428 = 1 457+971); 15 % de 800 MHz entre 48 000 giros/s = 2 500; 48 % y 24 %; 50 ms/490 µs = 102×; 50 ms/620 µs = 80×.
- No sigue: «8 000 − 2 706 = 5 300» es exacto (5 294), pero su contenido no es el que el brief dice (hallazgo 12). La suma de §3 da 1 650–2 150 con P2, no 1 700–2 200 (hallazgo 10). El 3 850 de la opción D está en otra base que el límite (hallazgo 12). El 620 µs no sigue de su propia premisa (hallazgo 2).
- No verificable: la cota de 1 500 como «giros que de verdad se completan». Los logs crudos del 17-10 no están en el árbol: ningún `carga_j2,cache=` fuera de EN-PLACA y de las herramientas. Con lo publicado no se puede demostrar (hallazgo 11).

## B) Hallazgos

**1. [BLOCKER] [AMB, SCOPE, GAP] «El J2» del límite no está definido, y el instrumento lo define distinto que el texto firmado**

Evidencia:
- Spec, enmienda 16-10: «con sus ISR, el despacho del ejecutor y los DMA».
- Papel §0: «ISR, DMA y lo que haga falta para despachar». En «No decide»: «ni si el planificador entra en él (HUECO, §6)».
- EN-PLACA, `carga_j2`: el número comparado es «lo que el hilo no usa en un ciclo».
- Papel §2.1 pone el planificador en «bajo (P3, interrupción de software)».
- Brief §6: «Si es el J2, el límite se rompe antes de empezar.» Brief §3.3: «No está medido y no está escrito.»

Problema:
- Hay tres definiciones que no coinciden. (a) La firmada enumera mecanismos. El planificador no figura y «el despacho del ejecutor» deja de existir con la propuesta. (b) La del medidor es operativa: cuenta todo lo que preempte al hilo, así que un planificador en P3 entra por construcción. Hoy `bajada_fn` y `juez` ya están dentro de los 8 000 (`j2_ejecutor.rs:346,368`) y de los 1 500 (`j2_isr.rs:323,340`). (c) La del papel es abierta («lo que haga falta»).
- El papel declara que no decide si el planificador entra y a la vez lo coloca en un nivel que el medidor suma.
- No dice si cuentan: el CRC del sobre en ambos sentidos, `Ranura::paso`, `publicar_cuentas`, los traspasos entre niveles, D4 en régimen ni el costo de rellenar cachés del hilo real (el hilo del medidor es un `yield_now`).
- «15 % = 2 500 por giro» solo coincide con seis ranuras activas a 8 kHz. Con menos ranuras (R-MJ6) las dos formas del límite divergen.
- «Se rompe antes de empezar» no tiene cifra detrás.

Impacto: la condición «≤ 2 500 ciclos por giro» de §5.1 no es evaluable, porque la misma fila pasa o falla según la definición. La firma del 16-10 se aplicaría a un conjunto distinto del que Samuel firmó.

Qué hay que decidir: ¿Qué actividades suman contra los 2 500, enumeradas una a una? ¿Vale la enumeración del texto o la ocupación del hilo? ¿El límite es por giro o por fracción de núcleo cuando hay menos de seis ranuras?

**2. [BLOCKER] [CONTRA, STATE, GAP] El plazo de D3 no se puede vigilar «tal cual» con un tic de 125 µs, y el papel deja la elección abierta dentro del texto que pasaría a la spec**

Evidencia:
- Spec D3: «El plazo es por mensaje, no global». También: «el T_GAP entre mensajes y la cadencia del giro. Esos son del planificador».
- Spec D2 regla 1: «se descarta y se cuenta». Papel §2.4 (P2): «se acepta como bueno».
- Papel §1: «cambia cómo se vigila (§2.4, decisión abierta)». Cabecera del papel: «Si Samuel firma, §1-§3 pasan a la spec».
- Enmienda 18-09: «El techo de recuperación de §3 se mantiene: 220 + 20 + 125 = 365 µs < 490.» Papel §2.4: «620 µs», y «un SET de dieciséis (226 µs) en el segundo (250 µs)».
- Spec §8: `t_recuperacion = plazo_max + T_REINICIO + 2/F_LAZO` (gate L183). Riesgo 2: «FACTOR_PLAZO se fija con ≥ 3× el peor exceso medido».
- Papel §2.4: «con DWT_CYCCNT como reloj (sin acceso al bus)» y «a verificar en el RM del N657».

Problema:
- (a) La spec fija plazos por mensaje: 70 µs un `NADA`, unas decenas de µs un `HOLA` de 25 B, 162 µs `BAHIA`, 226 µs el `SET` de 16. Con P2, todo plazo menor que ~117–125 µs se detecta en el tic siguiente. La fórmula solo discrimina a los mensajes de plazo > 125 µs, y `FACTOR_PLAZO`/`T_SUELO_PLAZO` dejan de ser observables por `plazos_vencidos`. P1 exige un temporizador cuya disponibilidad el papel marca «a verificar» (Not specified).
- (b) P2 invierte D2 regla 1. `plazos_vencidos` y `eot_tardios` son columnas de R-MJ8: los ceros del soak del 16-17 y los de una fila nueva dejan de ser comparables, y la evidencia de la puerta de fabricación pierde sensibilidad.
- (c) Un EOT y un tic pendientes a la vez al mismo nivel (P1) se atienden por número de IRQ. Si el tic va primero, una trama buena se declara vencida y se descarta. Es la carrera que D2 regla 3 evitaba. Que el tic lea `SR.EOT` antes de declarar el vencimiento: Not specified.
- (d) El techo suma máximos que no coinciden. Con la premisa del propio §2.4 (el `SET` se detecta a los 250 µs) el orden de magnitud es 500–520 µs, no 620. La spec y la enmienda 18-09 dicen 490/365 y «se mantiene». La fórmula de la puerta no tiene término de cuantización: con P2 seguiría imprimiendo 102×. La función de golpe perdido de D6/§3 («3 × P(EVENTO)», «3 giros») no se propaga: 490/125 = 3,92, el guion ya imprime `round()` = 4, y a 620 µs serían ~5.
- (e) `DWT_CYCCNT` hoy solo lo enciende `perfil::iniciar()` bajo la feature `perfil`. Unidades (µs del plazo contra ciclos) y disponibilidad en producción: Not specified. «Cero ciclos extra» tampoco es cero: lectura, resta y comparación por ranura en cada tic.

Impacto: no se puede implementar ni probar el plazo. Se firmaría una enmienda con su mecanismo central sin elegir, y con tres cifras de la spec (490, 365, 3 giros) falsas.

Qué hay que decidir: ¿El plazo es frontera del giro (D2 regla 1) o frontera de detección? ¿Qué pasa con un EOT entre plazo y tic, y con un EOT y un tic pendientes a la vez? ¿Qué reloj mide `t_arm`? ¿Qué suma da el techo, y qué fórmula asevera la puerta?

**3. [HIGH] [CONTRA, STATE] D2 pasa de dos esperas (DMA y EOT) a un solo evento, y el cierre en el EOT no mira el DMA**

Evidencia:
- Papel §1: «cambia: son dos estados con un plazo (§2.2)». §2.2 solo tiene `Armada` →`Eot`→ `Cerrando`, y `Cerrando` espera al planificador, no al DMA.
- Spec §1.1: «tiene que cubrir también la espera del DMA (D2)». Título de D2: «la v1 ponía el plazo solo sobre EOT».
- Papel §2.3: «borra las banderas por IFCR, SPE = 0 y solo entonces los dos DMAEN a cero».
- Spec D4.5 (RM): «all the FIFOs content is flushed».
- `j2_isr.rs:165-168`: la cota sí lee `SR` de los dos canales y calcula `bien = tcf && tcf`. El papel no lo recoge.

Problema:
- La espera del DMA de D2 desaparece. Ningún estado o evento del papel observa el fin o el error del DMA.
- El cierre pasa del tic siguiente (cota) al propio EOT. Que el DMA de recepción haya vaciado la FIFO antes de `SPE = 0` no queda dicho.
- Un canal parado o con error con EOT presente no tiene camino hacia D4, porque D4 solo nace de un plazo (EOT ausente).
- Nada garantiza que el canal está parado antes de reescribir `BR1`/dirección/`CR.EN` en el armado siguiente.
- El papel devuelve a D2 el defecto que la junta del 11-09 (H-1) tumbó.

Impacto: subidas truncadas con riesgo de CRC o corrupción silenciosa, y un canal trabado que solo se descubre por efecto lateral.

Qué hay que decidir: ¿Qué observación da por terminado, y cuál por fallido, el DMA de cada canal antes de `SPE = 0` y antes de tocar el canal otra vez? ¿Se conserva la regla «el plazo abraza DMA y EOT» o se retira?

**4. [HIGH] [STATE, GAP] El ejecutor único daba exclusión mutua implícita; P1/P3 la destruye y el papel no lo dice**

Evidencia:
- Papel §2.1: «mientras dura (20 µs ESTIMADO) los demás giros se arman y se cierran». Papel §2.5: «la escalada marca todas las ranuras con canales_sucios y el tic las reprograma antes de armar».
- `j2_spi.rs:764`: «resetear_por_rcc corre en seccion critica». `j2_spi.rs:793-794`: son dos llamadas seguidas (`disable`, `enable_and_reset`) sin sección crítica externa.
- Spec D4 paso 4: «Entre el reset y esa escritura el SPI no maneja NSS ni SCK».
- `j2_spi.rs:839-841`: `T_CANAL` se acota con `Instant::now()`, tiempo de pared.

Problema:
- Hoy el armado de cada ranura y la recuperación de cualquiera corren en un ejecutor cooperativo: no se intercalan. La spec nunca lo exige porque era un efecto lateral.
- Con tic y EOT en P1 sobre recuperación en P3:
  - (i) entre `disable` y `enable_and_reset` del GPDMA1 un tic puede escribir canales de ranuras sanas con el controlador sin reloj. La marca `canales_sucios` no es atómica con el reset.
  - (ii) la ventana del paso 3 al 4 de D4, hoy código lineal («un instante»), dura lo que dure el trabajo de P1 que la preempte (~8 µs por tic según el papel). Durante ese tiempo el CS del módulo queda flotando.
  - (iii) `T_CANAL` = 10 µs de pared puede consumirse en un tic: escalada falsa que resetea las seis ranuras.
  - (iv) la sección crítica de RCC y del `defmt::error!` enmascara P1, contra lo que dice §2.1.

Impacto: H-1 («un plazo vencido no retrasa a las otras cinco») puede degenerar en «un plazo vencido rompe a las otras cinco».

Qué hay que decidir: ¿Qué excluye al tic y a los EOT durante D4.2 y durante los pasos 3–4 de D4, y por cuánto tiempo máximo? ¿`T_CANAL` es tiempo de pared o de CPU en un contexto que P1 interrumpe?

**5. [HIGH] [STATE, GAP] Dueño de `Ranura` y frontera entre `Transporte`, política y planificador**

Evidencia:
- Papel §2.2: «Vive en core (Transporte), pura y probada en el host, como la política». Papel §1: D7/`core::Ranura` «igual».
- Papel §2.3: «pasa a la política GiroOk y SubidaOk o SubidaMala con la hora del cierre». §2.7: «la misma semántica» de los contadores.
- Spec D8: «Una máquina por ranura, sin hardware, sin async». `j2_ejecutor.rs:323`: `politica` es local a la tarea. `maestro_j2.rs:350`: `paso(&mut self, …)` con anillo de 16 `u64`.
- Spec D3: la cadencia «es del planificador».

Problema:
- Hoy `Ranura` tiene un solo escritor por construcción. En el papel los eventos nacen en P1 (tic, EOT) y en P3 (planificador, D4). Qué filas de §2.2 se traducen a `Ranura::paso`, desde qué nivel y con qué reloj (µs o ciclos): Not specified. Si se traducen, `paso(&mut self)` se llama desde dos niveles sobre estado no atómico.
- Dos máquinas deciden «pedir D4»: `Ranura::paso(PlazoVencido)` devuelve `Reiniciar` y la fila `Armada/Tic` también.
- La identidad (`Vacia`/`Activa`, R-MJ6) vive en la política, pero el tic debe saltar la ranura. `Transporte` no tiene estado `Vacia`. Qué pasa si se retira la identidad con una transferencia `Armada`: Not specified.
- Que el tic decida saltar o no armar es cadencia, que D3 asigna al planificador.

Impacto: carreras sobre contadores y marcas `inestable`/`muda`, y doble petición de reinicio.

Qué hay que decidir: ¿Quién es el único que llama `Ranura::paso`, desde qué nivel y con qué reloj? ¿Qué máquina es la autoridad sobre «reiniciar» y sobre «no armar»?

**6. [HIGH] [GAP, STATE] El buzón: la bajada se compone un periodo antes y su ausencia no está definida**

Evidencia:
- Papel §2.1: el planificador «compone la bajada de cada ranura para el tic siguiente». Papel §2.3: «toma del buzón la bajada que dejó el planificador y su TSIZE».
- Spec D5.1(2): el planificador «Decide qué baja por cada ranura en cada giro». `j2_ejecutor.rs:346`: `bajada_fn` se llama dentro de la tarea, al armar.
- Spec D4: «La secuencia de la trama abortada se consumió.» Spec §10: «perdidas − rechazadas − plazos_vencidos es lo que de verdad se perdió por el cable».

Problema:
- Productor (P3) y consumidor (P1) sin protocolo escrito: doble búfer o atomicidad, Not specified. Qué envía el tic con el buzón vacío o viejo: Not specified. `TSIZE` es `NonZeroU16` (R-MJ1), así que «sin bajada» no se puede representar en él.
- Latencia nueva de un periodo entre decisión y cable, también para el `EVENTO` (sin red según D7 de la cabecera). Ningún límite de latencia aparece en el papel.
- Una bajada compuesta con su `secuencia` y no enviada (`Cerrando`+`Tic` «no se arma», o sobrescrita) abre huecos de secuencia que el módulo cuenta en `perdidas` y ningún contador del cerebro explica. La identidad de cruce de D4/§10 deja de cerrar.
- El sello al armar (D5.4) pasa a depender de que el planificador haya entregado.

Impacto: golpes perdidos sin causa registrada y un bring-up cuyo cruce de contadores no se puede interpretar.

Qué hay que decidir: ¿Qué hace el tic sin bajada nueva? ¿Qué se hace con una bajada compuesta y no enviada (su secuencia, su `EVENTO`)? ¿Qué latencia máxima decisión→cable está firmada?

**7. [HIGH] [CONTRA, STATE] «R-MJ2 igual» es falso: tres de los cinco estados no tienen plazo ni acción**

Evidencia:
- Papel §1: R-MJ2 «igual: cada estado de espera tiene su plazo».
- Papel §2.2: `Cerrando`+`Tic` → «contar tics_perdidos; no se arma». `Vencida` y `Reiniciando` solo cambian con eventos de P3.
- Spec R-MJ2: «Ninguna espera del J2 en el cerebro es un bucle síncrono sin cota.» Spec D7.1: «El planificador gira a 8 kHz por toda ranura activa, siempre.»

Problema:
- Una ranura en `Cerrando` (planificador que no consume), `Vencida` (P3 que no arranca) o `Reiniciando` queda fuera del lazo sin límite de tiempo. Solo crece un contador.
- `Cerrando` es una espera nueva: hoy la tarea llama `juez` de forma síncrona.
- La única red sería el sello del IWDG, requisito mandado al hub y pendiente (#291).
- La premisa de R-MJ2 («las dos esperas son futuros bajo plazo») también queda sin sujeto.

Impacto: pérdida silenciosa de una ranura; el módulo suelta a los ~50 ms.

Qué hay que decidir: ¿Qué cota y qué acción tienen `Cerrando`, `Vencida` y `Reiniciando`? ¿Qué dice R-MJ2 después de la enmienda?

**8. [MEDIUM] [CONTRA, GAP] Las enmiendas 18-09 y 16-10 «desaparecen», pero se afirman propiedades que el diseño no garantiza**

Evidencia:
- Papel §2.2: «el hueco de un periodo sale solo». Papel §2.7: «el tic encontró la ranura sin acabar y todavía en plazo».
- Spec 18-09: «dejaría fronteras de trama con gap ≈ 0». Spec 16-10: «Un atraso es un fallo del presupuesto de CPU, no del módulo.»
- EN-PLACA L781: el rearme del esclavo es «sin cota en ningún papel».

Problema:
- (a) El rearme ocurre en el primer tic tras `ReinicioHecho`. La distancia va de ~0 a 125 µs, no «un periodo». Que el mínimo (lo que quede de D4 tras soltar el NSS) baste al esclavo no está demostrado: `T_GAP` es HUECO y el tiempo de rearme del módulo no tiene cota. Con P1 el hueco no queda anclado al tic, con P2 sí.
- (b) `atrasos` medía presupuesto de CPU. `tics_perdidos` cuenta al menos dos causas distintas: transferencia aún en vuelo dentro de plazo, y planificador que no consumió. El papel lo llama renombre. Si mueve `inestable`/`muda` (16-10, punto 2): Not specified.

Impacto: `atrasos` era el observable de sobrecarga del soak y del riesgo 9; el contador nuevo no distingue I/O de CPU.

Qué hay que decidir: ¿Qué hueco mínimo debe quedar tras D4 y con qué fuente? ¿`tics_perdidos` sustituye a `atrasos` o los dos significados se separan?

**9. [HIGH] [CONTRA, GAP] D4 paso 6 no coincide con el código que el papel toma de modelo, y R-MJ3 queda rota**

Evidencia:
- Papel §2.3 y §2.5 paso 6: «Reprogramar los dos canales (TR1, TR2, TR3, CR)».
- `j2_isr.rs:15-17`: la cota programa «TR1, TR2, TR3, LLR, CR». Además `llr` (L76), el reset y la limpieza de `FCR` (L66-75), y la dirección del lado periférico (L108-114): «la direccion de TXDR o RXDR se escribe aqui y no se vuelve a tocar».
- `j2_spi.rs:811-812`: «el CxCR.RESET que aplica es el que de verdad deja el canal reconfigurable» (lo aplicaba el `Drop` de embassy). Spec R-MJ3: «cada paso cita su página».

Problema:
- La lista del papel omite `LLR` (mal copiada de su propia fuente) y la dirección del periférico. El papel nombra como implícito solo el `configure` de embassy, no el `RESET` del canal que hacía el `Drop`.
- Tras D4.2 (GPDMA1 por RCC) esos registros vuelven a reset: reprogramar solo `TR1..CR` deja la dirección del periférico en 0.
- En D4 normal el papel suspende los canales (`CR.SUSP`) y nunca dice `RESET`.
- R-MJ3 pasa de seis a siete pasos y el nuevo no cita página del RM. `canales_sucios` es una bandera nueva sin dueño ni atomicidad.

Impacto: la primera escalada real puede dejar una DMA apuntando a una dirección errónea, justo el camino que el 14-10 se midió con el transporte viejo.

Qué hay que decidir: ¿Qué registros de cada canal se programan una vez, cuáles por giro y cuáles rehace cada recuperación, con página del RM? ¿Quién resetea el canal que hoy resetea el `Drop`?

**10. [HIGH] [ASSUMP, AMB] La suma de §3 (1 700–2 200) descansa en supuestos no declarados**

Evidencia:
- Papel §3: «La propuesta cabe en el papel». Filas: plazo «0 a 50», estados «~50», búferes «100 a 600».
- Papel §2.6 (i): «cada lectura del búfer de subida cuesta ~80 ciclos por palabra».
- EN-PLACA L809: «La D-cache del M55 está apagada.» `j2_spi.rs:327-330` asevera lo mismo al construir la ranura.
- Brief §3.3: «entre compilaciones distintas del código varía hasta un 10 %». `carga_j2.py:247` compila siempre con `perfil`.

Problema:
- (1) La base 1 500 presupone D-cache encendida en el hub. Hoy está apagada y ninguna decisión firmada la enciende («las cachés del hub» no está definido). Sin ella, la misma cota mide 7 837. Con D-cache aparecen mapa MPU y mantenimiento para todos los DMA del hub, fuera del alcance de la suma.
- (2) Búferes: con 25–103 B (7–26 palabras) y ~80 ciclos por palabra, (i) da 560–2 080, fuera del rango 100–600, salvo que `ldm` abarate la lectura, lo cual no está medido. En (ii) no se dice cuándo se invalida la subida (¿antes de armar, antes de leer, ambas?) y el `clean` de la bajada no figura en R-MJ7.
- (3) Ninguna fila cubre el traspaso a P3 (entrada y salida de excepción, `pend`, buzón), ni la lectura de DWT por ranura en cada tic. La cota tenía un nivel y el papel tiene tres.
- (4) Aritmética: 1 500+0+50+100 = 1 650, no 1 700 (los extremos citados usan el 50 de P1, y se recomienda P2). Papel §2.1: 5 intervalos de ~1 100 ciclos son 6,9 µs, no 8. Y 1 100 es la ISR completa de la cota (cierra + arma + juez), no solo armar.
- (5) Una sola ranura medida. Resolución del medidor: 1‰ de ~100 000 ciclos, o sea ~100 ciclos por ranura. Ruido entre compilaciones: hasta 150–220 ciclos. Es del orden del margen de la suma (300–800).
- (6) Binario instrumentado, y un hilo medidor mínimo cuyo rellenado de caché no es el del hilo real.
- (7) El renglón del planificador es HUECO: la suma no tiene techo.

Impacto: «cabe en el papel» es una frase sin cota superior, con margen del tamaño del ruido.

Qué hay que decidir: ¿Con qué estado de cachés y de mapa de memoria se firma el 2 500? ¿Qué supuesto sostiene cada fila de §3? ¿Con qué resolución se compara contra el límite?

**11. [HIGH] [GAP, OPS] La cota de 1 500: lo que no demuestra**

Evidencia:
- Brief: «esa cifra es una cota inferior».
- `carga_j2.rs:194` imprime `c.plazos_vencidos`, que es el contador de la política. `j2_isr.rs` nunca emite `PlazoVencido`; cuenta aparte en `g.plazos` (L333). `publica()` pasa `atrasos = 0` fijo (L304). `fallos()` (L350) no tiene ningún llamador.
- `carga_j2.py:105-106`: «plazos vencidos; la medida no vale». `carga_j2.py:63`: ciclos = (1000 − libre) × ciclo_us × f / ranuras.
- `j2_isr.rs:319-337`: `Some(b) if b.eot() && g.cierra() => … _ => { g.plazos += 1; return }`.

Problema:
- (a) La guarda que invalida una pasada con plazos es ciega para `--isr`: una corrida con tics saltados imprimiría `plazos_vencidos=0`.
- (b) La cifra por giro depende de `ciclo_us` (giros completados), que ni EN-PLACA ni el brief publican para esa fila. 1 500 es 15‰ a 125 µs, pero también 5‰ a 375 µs (dos de cada tres tics sin completar). Indicio a favor: la ISR del SPI mide 185 por giro completado.
- (c) Callejón latente: si `cierra()` da `false`, `tomar()` ya consumió el resultado, `en_vuelo` sigue en `true` y cada tic posterior solo suma `plazos`. No se rearma nunca. No lo cubre lo medido.
- (d) «Cota inferior» es una afirmación de dirección sin prueba. Incluye costos que seis ranuras amortizan (lectura de TIM12 = 48 ciclos, entrada de excepción) y excluye otros que el papel añade. La ISR del SPI medida es `j2_spi::Isr` (185), no el manejador de EOT del papel. En la cota el cierre vive en el tic a P2 con el SPI a P1; en el papel, en el EOT con el tic a P1.
- (e) `juez_del_banco` compara contra un patrón fijo y con el MISO al aire sale en la primera diferencia (inferencia mía).

Impacto: el ancla de toda la propuesta no es auditable. No afirmo que sea errónea; afirmo que lo publicado no la demuestra.

Qué hay que decidir: ¿Qué evidencia publicada (cadencia, giros, plazos y errores de DMA del propio transporte) demuestra que la cota completa un giro por tic? ¿En qué sentido es «inferior»?

**12. [HIGH] [AMB, GAP] La opción D se descarta con una aritmética que no se reproduce**

Evidencia:
- Brief §5.D: «quedan 3 850; … 3 900 a 4 400 (ESTIMADO, de sumar las partes del perfil)».
- EN-PLACA L665: el perfil «Da cómo se reparten los ciclos, no cuántos son». L709: «Los 1 700 que faltan hasta los 8 000 no caen en ninguna función». L697: «cada una espera en su propio Timer».
- Brief §3.1: «Lo que no es código de la tarea son 5 300 ciclos: más del doble del límite.»

Problema:
- (a) Base: 3 850 = 6 278 − 2 428 está en la base del perfil. El límite está en la base «J2 entero» (8 000). En esta base, la misma resta da 5 572.
- (b) No monótono: el segundo paso quita más (driver de DMA de embassy 1 281, tareas más magras) y da más (3 900–4 400 > 3 850). Solo puede ser otra base. En la base del perfil, quitar también el driver deja 6 278−2 428−1 281 = 2 569, 69 ciclos sobre el límite antes de contar el driver sustituto.
- (c) El instrumento dice que da repartos, no cuentas, y se usan sus cifras como ciclos.
- (d) La cota mide 1 121 para armar+cerrar+juzgar+política, contra 2 706 de «código de la tarea». Son ~1 600 que salen del protocolo de registros (canales preprogramados, escrituras enteras) y no del ejecutor. D incluye «driver propio de DMA sin Transfer», y la derivación no muestra que acredite ese ahorro. Tampoco se midió una configuración tipo D (un solo `Timer` para las seis). Con cifras del propio brief y supuestos míos (un `Timer` y una entrada de ejecutor repartidos entre seis ranuras, el protocolo de la cota dentro de una tarea): 1 121+185+2 428/6+~194 ≈ 1 900. No afirmo que D llegue; afirmo que el texto no excluye ese caso. A y D heredan los mismos añadidos (plazo, búferes, planificador).
- (e) Los 5 300 mezclan 244 de la ISR del SPI, que cualquier transporte paga (la cota paga 185), y ~1 950 que EN-PLACA atribuye de dos maneras distintas y declara «no medido». La maquinaria atribuible es 3 104 = 1,24×. La conclusión «D5.1 firmada no cabe» sobrevive; «más del doble» y el piso de D dependen de lo no medido.

Impacto: se retira evidencia de 44,7 millones de transferencias y 24 h apoyándose en una imposibilidad no demostrada.

Qué hay que decidir: ¿Sobre qué base se compara un piso con 2 500? ¿Cuál es la derivación completa de 3 850 y de 3 900–4 400? ¿Qué parte de los 8 000 es propia del ejecutor y cuál de cualquier transporte?

**13. [HIGH] [GAP, OPS] Las condiciones de §5 no las puede evaluar la infraestructura de puertas; R-MJ8 no distingue transporte**

Evidencia:
- Papel §5.1: «Una fila de carga_j2.csv a ≥ 800 MHz» con «el transporte completo». Papel §5.3: «La fila del 16-17 de octubre es del transporte de D5.1 y no se transfiere.»
- `carga_j2.py:141-142`: «es una cota de coste y no se anota». El CSV (`fecha,firmware,placa,f_cpu_hz,cache,ciclos_por_giro,hilo_libre_permil,ranuras,periodo_us`) no tiene columna de transporte.
- `recuperacion_j2_budget.py:237-252`: `mejor = min(en_diseno)`, filtrando solo por `f_cpu`. L295: `return 2` fijo.
- EN-PLACA: «la cabecera de resistencia_j2.csv es de R-MJ8 y no se toca». EN-PLACA L455: «esclavo del banco en SPI4 como tarea del mismo ejecutor».

Problema:
- (1) La herramienta se niega a anotar una fila del transporte nuevo, y el CSV no la distingue.
- (2) La puerta pasa si cualquier fila a ≥ 800 MHz cumple. Ignora `ranuras`, `cache`, transporte y antigüedad: una fila vieja buena tapa una regresión, y una de una ranura con planificador de juguete cumple la letra de §5.1.
- (3) «lo sigue marcando HUECO» es una promesa: el guion devuelve 2 siempre (#369 pendiente).
- (4) `resistencia_j2.csv`, puerta de fabricación, no puede marcar la fila de 24 h como no transferible: sin columna, y con la cabecera intocable.
- (5) §4 exige banco con esclavo a 8 kHz, pero el esclavo vive en el `EJECUTOR_J2` que el papel borra. Dónde vive y cómo corre a 8 kHz: Not specified. Los binarios `resistencia_j2`, `barrido_retardo`, `plazos_j2` y `control_positivo`, y las herramientas `perfil_pc` y `muestreo`, dependen del ejecutor y no figuran en el papel. Tampoco el test del riesgo 8 (búfer contra analizador lógico), obligatorio si se enciende la D-cache.
- (6) §5 es «condición para que el código entre» y la fila exige «todo lo de §2 compilado». Si «entrar» es rama o main: Not specified.

Impacto: se puede fabricar o dar por cerrado el riesgo 9 sobre una fila que no corresponde al transporte.

Qué hay que decidir: ¿Qué distingue, en cada CSV, una fila del transporte nuevo, y qué comprueba la puerta además de `f_cpu` y `ciclos_por_giro`? ¿Qué es «entrar»? ¿Dónde vive el esclavo del banco?

**14. [MEDIUM] [CONTRA, AMB] Censo A: frases de la spec firmada que el papel-v1 vuelve falsas o ambiguas**

Evidencia: números de línea de la spec. F = falsa. A = ambigua (su sujeto desaparece o cambia).

1. L118–125, D2: «Las dos esperas son futuros» y el bloque `with_timeout(plazo, async { join(...); eot.await })`. F. El papel lo admite en §1.
2. L127: «la tarea recibe TimeoutError y ejecuta D4». F. No hay tarea ni `TimeoutError`, y qué evento dispara D4 es Not specified.
3. L135: la ISR «despierta (AtomicWaker)». F.
4. L139 y L143 (regla 1 y su enmienda 18-09): «La tarea acepta un resultado solo si la generación coincide». A: «la tarea» pasa a ser tic, ISR del EOT o planificador.
5. L141, regla 3: «registra el waker antes de mirar la bandera». Sin sujeto; la carrera reaparece (hallazgo 2c).
6. L212–235, D4.2 y enmienda 18-09: `Transfer`, `Drop`, `ManuallyDrop`, «ven sus futuros de DMA resolverse». F. La misma enmienda firma una razón contra reiniciar en un contexto aparte: «una espera sin cota bloquea al ejecutor donde gire, y todos tienen algo debajo que no puede parar». P3 y A' son ese camino y el papel no responde a esa razón.
7. L287–293, D5 y D5.1(1)–(3): «una tarea por ranura», «las tareas solo los atienden», «las seis tareas son el transporte», `InterruptExecutor` propio. F. El papel lo declara para (1) y (3), no para (2).
8. L293, H-9: «Una tarea de pantalla que retenga la CPU 15 ms no retrasa un giro». A: cubre el hilo; las ISR de USB y pantalla contra P1 quedan en §6.
9. L296 y L300–307 (18-09 y 16-10): `Ticker::reset()`, `Ticker`, `Calendario`, `iniciar_ejecutor`/`lanzar_ranuras` («el esclavo nace antes»). Desaparecen (ver hallazgo 8).
10. L336, D7.3: «no cambia lo que la tarea hace». A.
11. L351, D8.2: «j2_spi.rs se retira y el J2 vuelve a embassy_stm32::spi». La salida deseable de la spec deja de existir y el papel no lo dice.
12. L385 y L388, R-MJ2 y R-MJ5: «son futuros bajo plazo (D2)» y «Cada ranura activa tiene su tarea…». R-MJ5 se reescribe (consta). R-MJ2 se declara «igual» (hallazgo 7).
13. L410–413, §5: «El ejecutor del J2, con seis tareas». F.
14. L487, riesgo 6: «pausarlo por registro desde otra tarea». La prueba de cierre no tiene dónde ejecutarse.
15. L581, §10 «hub N657 | nueva: los ejecutores»: su contenido pasa a ser una tabla de niveles de IRQ.
16. Papel §2.2: «plazo cumplido» dispara D4, mientras que la spec D3 (L203) usa «declarada y no cumplida» para decir que no se satisface. La fila que reinicia un SPI se puede leer al revés.

Impacto: una enmienda que deja 16 frases firmadas falsas o sin sujeto, sin lista de derogaciones.

Qué hay que decidir: ¿Qué frases se enmiendan, cuáles se declaran derogadas, y qué significa «plazo cumplido»?

**15. [MEDIUM] [CONTRA] Censo B: lo que el papel dice «igual» y cambia, y piezas firmadas ausentes de su tabla de §1**

Evidencia: papel §1 y §2; spec.

- **D2 «el orden de arranque… igual».** El papel quita el primer paso `SPE = 0` («SPE ya está en 0»). Pasa a depender de un invariante de estado, aunque la spec dice que `TSIZE` «solo con SPE = 0» (L146). Además cita «D2, orden de cierre» y «D2, cierre del manual», pero D2 no contiene un orden de cierre. La cita de §67.4.14 está en D4 paso 2 (L212).
- **D3 «igual la fórmula».** Ver hallazgo 2.
- **D4 «igual el contenido».** Siete pasos (R-MJ3 dice seis), en contexto preemptible y con paso nuevo.
- **R-MJ2 «igual».** Falso (hallazgo 7).
- **R-MJ4.** Las constantes nuevas (tic, cuantización, `T_CANAL`) no tienen casa, y la fórmula de la puerta no se menciona.
- **R-MJ7 «igual».** El papel añade `clean` de la bajada, y `Ranura::nueva` asevera D-cache apagada (cambio de driver no listado).
- **R-MJ8.** Ausente de la tabla (hallazgo 13).
- **R-C8 «igual».** El tic decide cuándo se arma o se salta (hallazgo 5).
- **D5.4 «igual».** El sello depende de que el planificador entregue (hallazgo 6).
- **D7/`Ranura` «igual».** Cambia el modelo de propiedad (hallazgo 5).
- **Riesgo 6 «se cierra por construcción».** La spec (L487) lo cierra con una prueba en placa. La espera sin cota del `Drop` se reemplaza por una acotada, pero el canal que no responde persiste.
- **Ausentes de la tabla de §1:**
  - D8: el contrato `Ok/PlazoVencido/EotTardio` del driver y su retirada vía upstream.
  - §5 «Muere/Nace».
  - Las filas pendientes de §10 (hub: «los ejecutores», supervisor).
  - Riesgos 1, 5 y 9.
  - `j2_esclavo.rs` y los binarios del banco.
- **Contradicción interna.** El papel decide en §2.2 qué hace el tic con una ranura sin módulo y con una recién recuperada, y lo lista como abierto en §6.
- **Regla firmada que la cota ya incumple.** La enmienda 16-10 punto 3 dice que el periodo del banco es «nunca más corto». `j2_isr::lanzar` acepta `periodo_us >= 2` (`j2_isr.rs:289`).

Impacto: la spec quedaría con dos arquitecturas vivas, que es el patrón que ya costó una junta (enmiendas mandadas sin aplicar).

Qué hay que decidir: ¿Cuál es la lista cerrada de piezas de la spec que esta enmienda toca, con su estado (reescrita, derogada, igual)?

## C) Preguntas que el documento evita

1. ¿Qué actividades suman contra los 2 500 y con qué definición se miden (enumerada u ocupación del hilo)? (1)
2. ¿El plazo de D3 es frontera del giro o frontera de detección? ¿Qué pasa con un EOT entre plazo y tic, y con un EOT y un tic pendientes a la vez? (2)
3. ¿Qué observa el transporte para saber que el DMA terminó o falló antes de apagar el SPI y antes de reescribir un canal? (3)
4. ¿Qué excluye al tic y a los EOT durante D4.2 y los pasos 3–4 de D4, y cuánto enmascara el peor caso? (4)
5. ¿Quién llama `Ranura::paso` y qué máquina manda «reiniciar»? (5)
6. ¿Qué envía el tic sin bajada nueva y qué ocurre con una bajada compuesta que nadie envió? (6)
7. ¿Qué cota y qué acción tienen `Cerrando`, `Vencida` y `Reiniciando`? (7)
8. ¿La D-cache del hub está encendida, con qué mapa MPU, y con qué estado de cachés se firma el 2 500? (10)
9. ¿Qué parte de los 8 000 es propia del ejecutor? ¿Existe una medida de configuración D? (12)
10. ¿Qué fila de cada CSV cuenta como la del transporte nuevo y cómo la distingue la puerta? (13)

## D) Riesgos por categoría

**Técnico**
- Subida truncada o canal trabado no detectado: 3, 9.
- Carreras entre niveles y datos compartidos en recuperación: 4, 5, 6.
- Plazo con significado distinto y contadores no comparables: 2, 8.
- Ranura fuera del lazo sin cota: 7.

**Producto**
- Golpes (`EVENTO`) perdidos o con un periodo más de latencia, y función de golpe perdido mal propagada: 2, 6.
- Escalada falsa o mal reprogramada que afecta a ranuras sanas (y, si el escritor de CV comparte GPDMA1, a una salida de audio; §6 del papel): 4, 9.
- Decisión de abandonar D5.1 sobre una imposibilidad no demostrada y un límite sin definición: 1, 12.

**Ejecución y operaciones**
- Puertas que no pueden evaluar §5 ni R-MJ8: 13.
- Cota no auditable y margen del tamaño del ruido: 10, 11.
- Costo de repetir evidencia (soak, barrido, `plazos_j2`) y reescribir binarios y banco: 13, 15.
- Enmiendas silenciosas y derogaciones sin lista: 14, 15.

## E) Aclaraciones inmediatas (solo BLOCKERS)

1. **Hallazgo 1.** Enumerar qué suma contra los 2 500 y con qué definición se mide, antes de pedir una sola fila a ≥ 800 MHz.
2. **Hallazgo 2.** Definir si el plazo es frontera del giro o de detección, y cerrar P1/P2 antes de que §1–§3 pasen a la spec.

Archivos relevantes (rutas absolutas):
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\docs\superpowers\juntas\2026-10-17-j2-transporte\papel-v1.md`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\docs\superpowers\juntas\2026-10-17-j2-transporte\junta-2026-10-17-brief.md`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\docs\superpowers\specs\2026-09-03-maestro-j2-recuperacion-design.md`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\software\nucleo\fw\EN-PLACA.md`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\software\nucleo\fw\src\j2_isr.rs`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\software\nucleo\fw\src\j2_spi.rs`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\software\nucleo\fw\src\j2_ejecutor.rs`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\software\nucleo\fw\src\bin\carga_j2.rs`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\software\nucleo\fw\carga_j2.py`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\software\nucleo\core\src\maestro_j2.rs`
- `D:\Desktop\projects\sam17\.claude\worktrees\banco2\hardware\02-midi-cv\recuperacion_j2_budget.py`
