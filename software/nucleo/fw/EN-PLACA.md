# Prueba en placa: STM32N6570-DK

El port de fase A apunta al **STM32N657X0H3Q** de la Discovery
**STM32N6570-DK**. El firmware SAM17 conserva su interfaz **USB MIDI**.
La primera prueba de hardware será el ejemplo independiente de **USB serial
CDC-ACM desde RAM**; después se probará SAM17 desde RAM y, más adelante,
el arranque persistente mediante **FSBL firmado y XSPI**.

Esta guía no registra pruebas físicas realizadas. Compilar, enlazar y pasar
los tests del host no demuestra arranque, enumeración USB ni arranque desde
XSPI. Marca cada casilla solo cuando exista evidencia de esa prueba.

## 1. Puerta de compilación de fase A

Desde la raíz del repositorio, en un entorno Bash con las herramientas que
usa el script (`cargo`, `grep`, `tail`, `stat`):

```bash
bash software/nucleo/fase_a.sh
```

- [ ] Termina con código 0 y `== FASE A VERDE ==`.
- [ ] Los tests de `core` pasan y el contador alcanza al menos 232.
- [ ] Existe el ELF `software/nucleo/fw/target/thumbv8m.main-none-eabihf/release/sam17-nucleo-fw`.
- [ ] No quedan dependencias ni elementos de arranque de la plataforma anterior
  en los archivos de firmware que inspecciona el script.

La autoridad para estos criterios es [fase_a.sh](../fase_a.sh). El target es
`thumbv8m.main-none-eabihf` y la selección del HAL es `stm32n657x0`; ambas
cosas deben coincidir con [Cargo.toml](Cargo.toml) y
[.cargo/config.toml](.cargo/config.toml). Los crates Embassy quedan fijados a
la revisión que declara el manifiesto; el verde se refiere a esa revisión.

### Resultado registrado

Corrida el 2026-09-09 en el worktree del port: **`== FASE A VERDE ==`**, con
**321 tests de `core`** verdes (1 ignorado) y el ELF de
**3 569 064 bytes**. `od` sobre la cabecera da `e_machine = 0x28` (EM_ARM):
imagen ARM32 hard-float, vectores en `0x341A0000`, reset en `0x341A034D` y
pila inicial en `0x34200000`.

Eso es evidencia del **enlace y de su mapa**, no de la ejecucion. Ninguna
casilla de las secciones 3 en adelante esta marcada: no ha habido placa.

Dos defectos de la propia puerta salieron en esa corrida y estan arreglados
en `fase_a.sh` — quedan escritos porque el siguiente que la lea los va a
volver a escribir:

- **Cargo lee `.cargo/config.toml` desde el directorio de trabajo, no desde
  el del manifiesto.** Con `--manifest-path fw/Cargo.toml` desde
  `software/nucleo` compilaba para el host y fallaba por falta de
  `panic_handler`. La puerta ahora **entra** en `fw/`.
- El censo de restos del RP2350 miraba tambien los comentarios, y obligaba a
  borrar los que cuentan de donde venimos. Ahora solo mira codigo vivo.

## 2. Qué se carga en RAM

[memory.x](memory.x) copia las direcciones y los tamaños de
`examples/stm32n6/memory.x` de embassy (rev dc6b716):

| Región del linker | Inicio | Tamaño | Final exclusivo |
| --- | --- | --- | --- |
| `FLASH` | `0x341A0000` | 256 KiB | `0x341E0000` |
| `RAM` | `0x341E0000` | 128 KiB | `0x34200000` |

**Las dos regiones están en SRAM.** `FLASH` es el nombre que usa el linker
para colocar código y datos de carga; no representa memoria persistente ni
configura XSPI. Se usan los alias seguros `0x34xxxxxx` de la referencia.
El ejemplo afirma que la ROM de arranque habilita AXISRAM2; falta comprobar
que el procedimiento de carga elegido conserve ese estado y permita
ejecutar esta imagen en el contexto de seguridad esperado.

Hay una discrepancia en el comentario de la referencia: dice que deja
768 KB libres al principio de AXISRAM2, pero las direcciones dan:

```text
0x341A0000 - 0x34100000 = 0xA0000 = 655360 bytes = 640 KiB
1024 KiB - 256 KiB - 128 KiB = 640 KiB
```

Se conservan las direcciones exactas. No se presupone espacio para el
framebuffer de 800 × 480 × 2 bytes (750 KiB) que menciona ese comentario:
750 KiB no caben en los 640 KiB inferiores. El reparto de memoria de una
aplicación con pantalla queda fuera de esta prueba.

- [ ] Inspecciona las secciones del ELF y confirma que código, datos, BSS y
  pila respetan las regiones declaradas.
- [ ] Registra la herramienta y su versión, el modo de arranque de la placa,
  las direcciones cargadas y cómo establece el punto de entrada, la pila y
  la tabla de vectores.
- [ ] Confirma en la placa que el acceso y la ejecución desde esos alias
  funcionan. Un nombre de chip aceptado por el runner no basta.

El runner de [.cargo/config.toml](.cargo/config.toml) es una configuración
pendiente de validar en hardware. No hay aquí un comando de carga RAM
verificado ni una receta de programación XSPI.

## 3. Preparación eléctrica y USB

La referencia inicial es
`examples/stm32n6/src/bin/usb_serial.rs` de embassy (rev dc6b716, PR #6939).
Los siguientes valores se trasladan de ese ejemplo sin reajustar el reloj:

- Alimentación: `SupplyConfig::External`. El comentario del ejemplo remite
  a **UM3300, tabla 6**, y advierte que la selección del SMPS interno puede
  dejar la inicialización esperando `VOSRDY` en esta Discovery.
- USB: `USB1_OTG_HS`, con interrupción homónima y
  `Driver::new_hs_dedicated_pins`. El PHY integrado usa las señales
  dedicadas `OTG1_HSDP` y `OTG1_HSDM`; este constructor no recibe GPIO D+/D−.
- Referencia del PHY: HSI → PLL4 → IC15 → `otgphy1sel`.

```text
HSI       = 64 MHz
DIVM      = 4; DIVN = 60; fractional = 0
PLL4      = (64 / 4) × 60 / 2 / 1 = 480 MHz
IC15      = PLL4 / 20             = 24 MHz
otgphy1sel = Ic15
```

El ejemplo cita **RM0486 Rev 4, §14.6.2, §14.6.5 y USBPHYC_CR.FSEL** para
esa configuración. Estas son referencias heredadas del archivo; no son
una medición del reloj de esta placa ni una validación de otras revisiones.

`vbus_detection = false` también se conserva del ejemplo. Queda pendiente
resolver **VBUS-TOPOLOGIA**: cómo se alimentará la placa, qué ocurre al
retirar el cable del dispositivo y qué detección de VBUS ofrece el circuito
del puerto elegido. El propio ejemplo indica que un dispositivo que sigue
alimentado sin USB requiere detección de VBUS para cumplir la especificación.
El valor copiado no cierra esa comprobación.

- [ ] Identifica en UM3300 y en el esquemático de la revisión de la placa
  el conector conectado a USB1, sus puentes y su ruta de alimentación.
- [ ] Distingue ese puerto del USB del depurador ST-LINK: ver el depurador
  en el host no demuestra que USB1 haya enumerado.
- [ ] Anota la alimentación usada y el comportamiento al conectar y retirar
  USB; resuelve `VBUS-TOPOLOGIA` antes de dar esa configuración por válida.

[core/src/pinout.rs](../core/src/pinout.rs) contiene **índices provisionales
de señales**, no una asignación a puertos y pines del STM32. Ese archivo
está protegido en fase A. Recorrerlo o imprimirlo no configura GPIO reales
ni habilita J2, I²C, DIN, pedal o CLOCK IN/OUT. El esquemático definitivo del
hub y su asignación física siguen pendientes.

## 4. Primero: USB serial CDC-ACM desde RAM

Esta prueba usa el ejemplo de referencia como una imagen independiente.
No forma parte del binario MIDI de SAM17 ni cambia su protocolo. El ejemplo
no es por sí solo un proyecto Cargo ejecutable: su integración en un proyecto
de prueba y el procedimiento de carga deben quedar registrados.

- [ ] Compila el ejemplo para el mismo chip, con su mapa RAM y una revisión
  de Embassy que incluya el soporte N6 utilizado por el port.
- [ ] Cárgalo en RAM con el procedimiento validado en el paso 2.
- [ ] Observa `Hello World!` por RTT. Si no aparece, revisa carga, contexto
  de ejecución y alimentación antes de atribuir el fallo al USB.
- [ ] Comprueba que el host enumera **USB-serial example**, fabricante
  **Embassy**, VID `0xc0de`, PID `0xcafe`, serie `12345678`.
- [ ] Abre el puerto CDC, envía bytes y verifica que el eco devuelve los
  mismos bytes. El ejemplo configura endpoints bulk de **512 bytes** y
  buffers de lectura de ese tamaño.
- [ ] Repite el eco tras cerrar y abrir el puerto, y tras desconectar y
  reconectar USB; registra qué alimentación se mantiene en cada caso.
- [ ] Guarda el log RTT y los descriptores observados por el host,
  incluida la velocidad negociada y el tamaño de los endpoints.

El éxito aquí valida esa combinación de placa, alimentación, carga RAM,
reloj, PHY y transporte CDC. El contrato MIDI de SAM17 se comprueba aparte.

## 5. Después: SAM17 por USB MIDI desde RAM

- [ ] Carga el ELF de SAM17 usando el procedimiento RAM ya validado.
- [ ] Observa el log de arranque y la versión que publica
  `VERSION_PROTOCOLO` en [servidor.rs](../core/src/servidor.rs): **2**.
- [ ] Comprueba que la tabla de partes provisional declara una parte,
  cuatro voces, canal MIDI 0 y rango de notas 0–127. El descubrimiento por
  EEPROM de #175 todavía debe sustituirla; esto no demuestra que exista
  una placa de voces conectada.
- [ ] Confirma la enumeración como **SAM17 nucleo**, fabricante **SAM17**,
  VID `0x1209`, PID `0x0017`, serie `0001`.
- [ ] Inspecciona los endpoints MIDI bulk de **512 bytes** y la velocidad
  negociada. Cada evento USB-MIDI sigue ocupando 4 bytes; el buffer de
  lectura debe admitir el paquete bulk completo. Prueba también varios
  eventos agrupados en una transferencia.

Los identificadores USB anteriores son los que declara [usb.rs](src/usb.rs).
La asignación legítima del VID/PID para distribuir el producto queda
pendiente; estos valores no acreditan un registro.

### HELLO y compatibilidad

- [ ] Envía `HELLO { version: 2 }` y recibe
  `HOLA { version: 2, huella }`.
- [ ] Envía una versión distinta y recibe primero `HOLA` con la versión
  actual y después `ERROR { etiqueta: 0x01, codigo: VersionIncompatible }`.

La etiqueta de `HELLO` es `0x01`; su versión se codifica como `u16`
little-endian. El sobre es `F0 7D <datos empaquetados a 7 bits> F7`.
Usa [protocolo.rs](../core/src/protocolo.rs),
[sysex.rs](../core/src/sysex.rs) y [usbmidi.rs](../core/src/usbmidi.rs) como
contrato del codec y del empaquetado. `HOLA` incluye una huella de `u32`;
un cliente que solo conoce la respuesta antigua de versión 1 debe adaptarse.

### DESCRIBE completo

- [ ] Envía `DESCRIBE` y recibe `VolcadoInicio { n, huella }` antes de los
  descriptores y `VolcadoFin { enviados }` después del último.
- [ ] Verifica `n = enviados = 42`: las 27 medidas de
  [medidas.rs](../core/src/medidas.rs) más los 15 parámetros de
  [tiempo_params.rs](../core/src/tiempo_params.rs). Son 42 sobres de
  descriptores más los dos mensajes de control del volcado.
- [ ] Comprueba nombres, unidades, rangos e identificadores únicos; coteja
  la huella con la del saludo para el mismo modelo.
- [ ] Interrumpe y repite el volcado. Sin cierre, o con `enviados != n`, el
  cliente debe reconocer que no tiene un modelo completo.

Hay parámetros de tiempo escribibles: los 42 no son todos medidas. Los
valores de las medidas de audio pueden seguir en sus valores iniciales
mientras no exista adquisición real por J2.

### GET, error de SET y suscripción

- [ ] Haz `GET` de un identificador recibido en `DESCRIBE`: responde
  `CHANGED(id, valor)` incluso sin suscripción.
- [ ] Haz `SET` sobre una banda de Bark y recibe
  `ERROR { etiqueta: 0x04, codigo: SoloLectura }`.
- [ ] Activa `SUBSCRIBE { activo: true }` y cambia el tempo
  `ID_TEMPO = 0x000000C1` a `121000` (121 BPM). Si ese ya era el valor,
  usa `122000`. Espera `CHANGED` para el valor nuevo.
- [ ] Desactiva `SUBSCRIBE` y cambia otra vez el tempo dentro de su rango
  declarado, `20000..300000`. Ese `SET` válido no lleva confirmación;
  verifica su efecto con `GET`.

`SUBSCRIBE` tampoco lleva confirmación propia. Al suscribirse pueden llegar
cambios del reloj: distingue sus identificadores del parámetro que estás
probando. La prueba de escritura valida el modelo y el transporte; no
demuestra una salida de reloj física.

### Reconexión y tiempo musical

- [ ] Después de desconectar y reconectar, repite `HELLO`, `DESCRIBE` y
  `GET`; configura explícitamente el estado de suscripción deseado.
- [ ] Con el transporte interno en marcha, verifica por `GET` que la
  posición avanza aun durante un intervalo sin cliente USB.
- [ ] Mide latencia y jitter con tráfico MIDI y durante un volcado. El
  periodo de 1 ms de `PERIODO_TICK` es una configuración, no una medida de
  latencia ni una garantía de planificación.

CLOCK IN/OUT, RESET, MIDI DIN, el puente inalámbrico, USB host y los enlaces
de J2 necesitan sus propios controladores, circuito y pruebas. Esta fase
no conecta esas señales; sus presupuestos del host no son medidas del N657.

## 6. Más adelante: FSBL firmado y XSPI

Una ejecución correcta desde RAM no demuestra que la ROM pueda arrancar
la imagen después de cortar la alimentación. El flujo de **FSBL firmado**
y la programación de **XSPI** se valida después del CDC y del MIDI desde RAM.
Ni [build.rs](build.rs) ni el mapa RAM producen por sí solos ese resultado.

Antes de escribir un procedimiento reproducible hay que cerrar estas
incógnitas con fuentes del fabricante y con la revisión real de la placa:

| Incógnita | Dato o evidencia que falta |
| --- | --- |
| `RAM-CARGA` | Herramienta y versión con soporte comprobado del N657, modo de arranque, carga en los alias seguros, inicialización de pila y vectores, y ejecución observada. |
| `VBUS-TOPOLOGIA` | Alimentación y detección de VBUS del puerto USB1, contrastadas con UM3300 y el esquemático de la placa utilizada. |
| `FSBL-FIRMA` | Formato de la imagen aceptada por la ROM, herramienta y versión para firmarla, opciones usadas y condiciones del ciclo de vida de seguridad del chip. |
| `XSPI-CARGA` | Memoria montada, cargador compatible, distribución de imágenes y direcciones, y configuración que establece el FSBL. |
| `FSBL-SALTO` | Destino y contexto de ejecución de SAM17, responsabilidades de inicialización y transferencia de control desde el FSBL. |
| `PINOUT-N657` | Asignación de las señales provisionales a puertos y pines reales del hub, contrastada con su esquemático. |
| `USB-IDENTIDAD` | VID/PID asignados y política de número de serie para distribuir el producto. |
| `TIEMPO-MEDIDO` | Latencia y jitter del transporte MIDI, el reloj y el volcado de descriptores medidos en el N657. |

No se fijan offsets XSPI, comandos de firma, posiciones de interruptores ni
opciones de seguridad sin verificarlos. Las únicas referencias de hardware
concretas heredadas por esta guía son las que cita el ejemplo: UM3300,
tabla 6, y RM0486 Rev 4, §14.6.2, §14.6.5 y USBPHYC_CR.FSEL. No constituyen
una receta de firma o arranque desde XSPI.

- [ ] Documenta y ejecuta el procedimiento de FSBL firmado y carga XSPI.
- [ ] Corta y restablece la alimentación sin una sesión del depurador que
  cargue el programa; observa arranque y enumeración MIDI.
- [ ] Repite `HELLO`, `DESCRIBE`, `GET` y los dos casos de `SET` desde ese
  arranque persistente.
- [ ] Guarda versiones de herramientas, imagen y hash, opciones de firma,
  distribución de memoria y logs suficientes para repetir la prueba.

Para cerrar fase A falta ejecutar la puerta completa y obtener su verde.
Los tests y el ELF inspeccionado quedan como verificaciones parciales;
las pruebas de placa y de arranque persistente siguen pendientes.
