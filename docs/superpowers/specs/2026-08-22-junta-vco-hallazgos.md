# Junta de revisión del VCO ×16 — hallazgos y decisiones

> Tres revisiones independientes sobre
> [`2026-08-22-modulo-3-vco-dieciseis-design.md`](2026-08-22-modulo-3-vco-dieciseis-design.md)
> y [`2026-08-22-contrato-modulo-voz-design.md`](2026-08-22-contrato-modulo-voz-design.md),
> el mismo día en que se escribieron y antes de que pasaran a plan.
> **Resultado: los dos specs se parten en dos —cobre y orquestación— y el
> segundo no es implementable contra el firmware que hoy existe.**

## 0. Por qué existe este documento

Los dos specs crecieron en una sola sesión, de «duplicar cuatro voces a ocho»
hasta dieciséis osciladores con FM, sync, anillo, enrutado por cerebro,
imperfección programable y telemetría completa. Cada añadido era defendible por
separado y **ninguno se cruzó contra los otros** hasta esta junta.

Lo que sigue no es opinión: **todo lo marcado como verificado se comprobó contra
fuente primaria** —el código que ya corre en `software/nucleo/`, el datasheet del
SSI2130, y los propios documentos del proyecto— citando archivo y línea.

## 1. Lo verificado contra fuente primaria

### 1.1 El firmware que ya corre contradice al contrato

| Lo que el spec asume | Lo que dice el código | Archivo |
|---|---|---|
| «La trama de 72 bits deja de estar clavada en el contrato» | `N_DACS = 3`, `BITS_TRAMA = N_DACS * 24`, y un test asevera `BITS_TRAMA == 72`. El cerebro **compone palabras de AD5686R él mismo** | `core/src/j2.rs:33-36,137` |
| «Lo que no se pudo medir se reporta como hueco» (Regla 6) | `TuneProgress { voz: u8, cents_x100: i16, hecho: bool }` — **no existe representación de hueco**. Cero significa «afinado perfecto» | `core/src/protocolo.rs:76` |
| Dieciséis osciladores direccionables, más sensores y salud | `MAX_INSTANCIAS = 16`. Consumido **exacto** por los osciladores | `core/src/param.rs:9` |
| Un preset carga del orden de 160 parámetros | `MAX_RESPUESTAS = 4`. Desbordamiento estructural de cuarenta veces | `core/src/servidor.rs:31` |
| «El cerebro se entera» cuando entra un cable | El mensaje `Jacks` tiene **carga útil cero**, y no existe ningún parámetro de ocupación de jack | `core/src/protocolo.rs`, `core/src/medidas.rs` |
| El conteo de voces sale del descubrimiento | `Placa.voces` es **constante de catálogo**, fijada en compilación e indexada por tipo de placa | `core/src/descubrimiento.rs` |
| El blob de calibración son 2688 B | El largo del blob es un `u8` en la cabecera: techo absoluto 255 B, y `FIN_ZONA_LIBRE = 0xFA` lo baja a 238 | `core/src/descubrimiento.rs` |

**Consecuencia:** el módulo de dieciséis no es un proyecto de hardware. Es un
proyecto de hardware **más una revisión del núcleo digital**, y ese segundo
trabajo no estaba contabilizado en ningún documento.

### 1.2 El módulo se identifica, pero no se describe

Núcleo §3.5, literal:

> «Monta el mapa de parámetros buscando el **tipo de placa** en una tabla que
> vive **en el firmware del cerebro**» · «La EEPROM del 24AA02 son 256 bytes:
> alcanzan para identidad y calibración, **no para un descriptor completo**»

El agente consume **esquema**, no identidad. El esquema de este módulo vive en
otra placa, lo escribe una persona a mano, y **no hay mecanismo que detecte que
divergió**. Cada juguete añadido hoy es una línea más de ese mantenimiento.

> **La ley, enunciada por la revisión ontológica:** un sistema que quiere ser
> gobernable por un agente tiene que alojar el esquema en el mismo objeto cuyo
> ciclo de vida el esquema describe.

### 1.3 Errores propios, corregidos en voz alta

Tres números del spec estaban mal y se verificaron contra fuente:

1. **El sentido del span está invertido.** §5.1 decía que corregir la resistencia
   de escala sube el span de 7,576 a 7,63 octavas. Es al revés: la v1 tiene
   **7,633** y corregir lo **baja a 7,576**. La corrección **gasta** margen
   trimless, no lo gana. Sigue valiendo la pena; el balance no era el escrito.
2. **El objetivo de 3 cents/octava en el jack era inalcanzable.** Una resistencia
   al 1 % vale **±12 cents por octava**, y hay dos en ese camino.
3. **El coste de la FM estaba subestimado.** §7.2 decía «medio amplificador
   operacional y pasivas por voz». La figura 18 del datasheet lleva además **un
   comparador LM311 y un MOSFET 2N7000** por oscilador, y ese LM311 gobierna
   `TIME REVERSE` **y** `LIN FREQ` a la vez.

Un cuarto, de concepto: **el anillo necesita una onda moduladora de audio**, y el
spec presupuestaba un canal de convertidor. Un convertidor da un voltaje de
control, no una onda.

## 2. Lo que va al spec del cobre

Hallazgos que se cierran con piezas, geometría o presupuestos.

1. **La matriz de modulación no tenía ni una pieza asignada**, siendo la razón
   entera por la que el módulo es de dieciséis. Decidido en §3.
2. **El encadenado de entradas rompe la escala**, y no por falta de corriente
   sino por **divisor de tensión**: dieciséis entradas en paralelo son 3,1 kΩ
   contra la resistencia de salida del módulo que ataque, y **cambia cada vez que
   se mete o se saca un cable**. Falta además declarar qué alimenta el pin de
   normalizado del primer jack de la cadena.
3. **El pin del jack no puede llevar señal encadenada y ser leído como bit de
   ocupación.** Decidido en §3.
4. **Falta un camino de silencio por oscilador.** Con dieciséis salidas siempre
   vivas y sin VCA en la placa, un esclavo que no arranca son ocho osciladores
   sonando. El patrón correcto ya existe en el repo: el cerebro lo aplicó a los
   gates con pull-down por hardware, «con una sola inversión un GPIO flotante
   abre las cuatro envolventes de golpe al encender». Este módulo no lo aplicó a
   sus salidas.
5. **La carga de la referencia estaba a la mitad.** Los 1,6 mA contaban solo el
   pin `VREF` de los chips. Del mismo nodo cuelgan la corriente de escala del
   expo (94,34 µA por oscilador) y la lineal (5,01 µA): **~3,2 mA**, sin contar
   las entradas de referencia de los conversores.
6. **La fila del fondo se contradice a sí misma**: 1,6 mm de placa más una pieza
   de ~9 mm no son 7,6 mm. Con el número correcto, el caso de conectores de
   10 mm **no cabe**.
7. **Los dos micros son dos cristales**, y el presupuesto de afinado tiene un
   solo `F_PIO`. Un desajuste de 50 ppm son **0,087 cents de sesgo sistemático
   entre columnas**, del mismo orden que la resolución de desafinado prometida, y
   la tabla de calibración lo absorbe como si fuera afinación real.
8. **El autoafinado deja de ser silencioso.** `architecture-poly.md` §5 lo
   justificaba porque el VCA está cerrado; con dieciséis salidas a jacks,
   cualquier cable patcheado hace audible un barrido de 2,7 s de notas
   cromáticas.
9. **De los 54 canales de conversor, solo 48 estaban desglosados.**

## 3. Decisiones tomadas en la junta (con Samuel, 2026-08-22)

1. **Los specs se parten en dos**: cobre y orquestación. El cobre puede avanzar;
   la orquestación se resuelve contra el núcleo digital, que es software y por
   tanto barato de cambiar. El orden importa: **el cobre no se itera y el
   software sí.**
2. **Matriz de enrutado libre: cada oscilador elige de cuál de los dieciséis
   come**, para sync y para modulación. **No es un crosspoint de 256 cruces**:
   es un selector por destino, que ya permite que varios coman de la misma
   fuente. Son **dos matrices distintas** —el sync es digital, la FM es
   analógica— del orden de 32 selectores repartidos entre las cuatro placas.
   Acotarlo se descartó a propósito: si el enrutado se acota, la matriz completa
   que justifica un solo módulo deja de existir y podrían haber sido dos de ocho.
3. **La memoria pasa a 32 KB** (misma familia I²C, mismo encapsulado). Resuelve
   el blob de calibración **y** deja que el módulo cargue su propio descriptor,
   que es lo que ataca la raíz de §1.2.
4. **Camino de silencio por oscilador**, con estado de reposo garantizado por
   hardware —pull, no firmware— como condición de arranque hasta que el esclavo
   confirme.
5. **`R_SCALE` y `R_CVIN` pasan a tolerancia del 0,1 %** en el camino de escala:
   1,2 cents por octava y por resistencia en vez de 12. El objetivo de 3
   cents/octava se mantiene y ahora es alcanzable.
6. **La onda moduladora del anillo sale de otro oscilador**, por el mismo
   selector analógico que la FM. Un concepto de fuente para las dos.
7. **Se busca el jack con contacto de conmutación independiente.** Si existe en
   el mismo formato mecánico, hay normalizado en cascada **y** sensado de
   ocupación. Si no existe, se vuelve a decidir con el dato en la mano.
8. **Las perillas quedan aplazadas** hasta tener la planta del panel dibujada,
   con el riesgo declarado: para entonces el reparto de entradas analógicas del
   micro puede estar congelado.

## 4. Lo que va al spec de orquestación

Nada de esto se cierra con cobre. Es contrato, protocolo y firmware.

1. **Handshake maestro-esclavo, con actuador.** Hoy no hay línea de reset ni de
   arranque-OK al esclavo: un esclavo colgado solo se recupera apagando la caja
   con la mano. Y el descubrimiento prueba que existe una memoria, no que exista
   un procesador — el cerebro puede publicar dieciséis voces antes de que ningún
   micro haya ejecutado una instrucción.
2. **Nueve de once modos de fallo son invisibles** para el resto del instrumento,
   en un aparato cuyo principio declarado es fallar en voz alta.
3. **El barrido no se degrada: se cuelga.** El presupuesto de afinado calcula el
   tiempo de medida desde la frecuencia *esperada* y **no tiene timeout**. Un
   oscilador con el sync alto está parado —el datasheet lo dice: «if held high it
   stops the oscillator»— y no da flancos nunca.
4. **El conteo de voces depende del preset y el descubrimiento ocurre al
   arranque.** Declarar dieciséis manda notas a moduladoras; declarar ocho deja
   la mitad del hardware inalcanzable en modo limpio. Las dos salidas son
   incorrectas y silenciosas.
5. **No hay primitiva de transacción** para que el barrido desmonte y restaure el
   enrutado. Sin ella hay actualización perdida: un `SET` del agente durante los
   2,7 s del barrido lo pisa la restauración, y el cliente no puede distinguir
   una restauración interna de una escritura suya.
6. **Dos interpoladores en serie.** El contrato autoriza al módulo a «interpolar,
   suavizar un salto, sostener un portamento» y el cerebro ya tiene rampas
   implementadas. Con los dos encendidos, el tiempo de glide no es parámetro de
   nada — y una rampa de duración cero, que está definida como salto deliberado,
   la destruye un suavizado que vive fuera del modelo.
7. **La deriva programada contamina la medida.** El corolario escrito en §7.7
   gobierna la **escritura**; la contaminación está en la **lectura**: el
   autoafinado mide frecuencia y la deriva *es* una divagación de frecuencia.
   Hay que congelarla durante el barrido, y ningún documento dice quién.
8. **Veintiséis pares de parámetros se excluyen o se degradan entre sí**, y el
   spec escribía uno. El descriptor no tiene campo para expresar ninguno.
9. **La cadena de LED tiene dos dueños.** El núcleo la declara un mazo del
   cerebro que encadena todos los paneles; el spec se la asigna a los micros del
   módulo. O el módulo regenera el flujo, o la cadena del instrumento muere aquí
   — y de eso depende el patcheo guiado.
10. **El contrato cierra por decreto una decisión que el núcleo dejó abierta.**
    §10 del núcleo reservaba al diseño del módulo 5 si los módulos 5/6/7 llevan
    micro propio o registro de desplazamiento; la Regla 2 lo cierra desde el spec
    de otro módulo.
11. **El contrato lleva el nombre de una propiedad que solo su autor posee.**
    `architecture-poly.md` §11 ya decía que al filtro **no hay nada que lo
    escuche**. El VCF, el ADSR y el VCA presentarían «se mide a sí mismo» como
    hueco permanente, para siempre.
12. **Cambios que el núcleo necesita**, en orden de dependencia: representación
    de hueco en `TuneProgress`; carga útil y parámetro destino para `Jacks`, con
    cadencia de sondeo declarada; ampliar `MAX_RESPUESTAS`; desacoplar la trama
    del J2 del AD5686R; espacio de direcciones para lo que no es una voz; y un
    campo de relación entre parámetros en el descriptor.

## 5. Lo que la junta NO discutió

- El hardware analógico del oscilador en sí. Las tres correcciones de exactitud
  (escala, compensación de agudos, histéresis del comparador) se dan por buenas:
  salen de datasheet primario contra un BOM existente y con la dirección del
  error declarada.
- El reparto en cuatro placas de cuatro osciladores, con el rendimiento evaluado
  por placa y no por módulo. Se dio por razonamiento correcto.
- El enrutado de audio del instrumento (matriz en el módulo 4, topología en
  estrella), que sigue aplazado a su propio ciclo.
