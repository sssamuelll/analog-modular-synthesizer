# El arranque del N657: tres caminos, y cuál es el de cada día

Escrito **sin placa** el 2026-09-11 (#231, tarea de escritorio del riesgo 6
del motor y del riesgo 2 del hub: «FSBL + Rust vivos»). Lo que aquí compila,
compiló en esta máquina; lo que aquí arranca, **no está probado**: nadie ha
tenido la Discovery en la mano.

## Lo que hace la ROM, con su página

El N657 **no tiene flash interna**. Siempre arranca en la ROM del chip, y la
ROM decide por dos pines y una palabra de OTP. RM0486 Rev 4 §9.1, p. 286:

> *«The ROM code is the first code executed after any system reset. The boot
> mode is determined by BOOT0 and BOOT1 pins, and one OTP word.»*

La Tabla 32 (p. 286), entera:

| BOOT0 | BOOT1 | Boot source #1 |
|---|---|---|
| - | 1 | Development boot |
| 0 | 0 | Flash boot |
| 1 | 0 | Serial boot |

AN5967 Rev 5 §10, p. 24, añade la prioridad: *«The BOOT1 pin check has
priority on the BOOT0 pin check. If the BOOT1 pin is not set, BOOT0 is
checked.»* En la DK, BOOT0 y BOOT1 son los dos interruptores de BOOT.

Y lo que la ROM verifica, §3.2, p. 183:

> *«On an application reset, the Cortex-M55 always boots from the start of an
> on-chip ROM. This ROM code is used to authenticate and decrypt images loaded
> into the internal memory from an external flash memory, or through UART,
> USB, I2C, SPI, FDCAN, or JTAG.»*

> *«Devices are delivered to customers in a BSEC-closed state, so the boot ROM
> execution is enforced. On a BSEC-closed device, if the secure_boot fuse bit
> (see Section 5: OTP mapping (OTP)) is still unblown, then the boot ROM
> behavior depends on the DEV_BOOT pin: If the DEV_BOOT pin is set, the boot
> ROM disables the access to secrets, and opens the debug to allow customer
> development. If the DEV_BOOT pin is not set, the boot ROM executes the boot
> image regardless of whether it is correctly signed. However, on a
> BSEC-closed device, once the secure_boot fuse bit is blown, authenticated
> secure boot is enforced. STMicroelectronics supplies signing tools to allow
> customers to create signed and encrypted boot images. The boot image is
> sometimes referred as an FSBL (first-stage bootloader), or as an uRoT
> (updatable root-of-trust firmware).»*

Lo que eso significa para nosotros, fuera de las comillas: **la «firma» que
exige la DK es una cabecera**, no una clave. Mientras `secure_boot` no esté
fundido (y en la DK no lo está), la ROM exige que la imagen lleve la cabecera
de ST y la ejecuta *aunque no esté bien firmada*. La cabecera la pone
`STM32_SigningTool_CLI` con `-nk` (*no key*). La firma con clave propia
(§3.3, provisionado por SFI) es una decisión de producto, fundir OTP es
irreversible, y **en la Discovery no se hace**.

## Los tres caminos

### A. Development boot: el de cada día, y el único que ya tenemos

BOOT1 arriba. RM0486 §9.1.3, p. 287:

> *«If BOOT1 is selected, the BootROM code finishes in an endless loop after
> having reopened debug in a secure way. This boot mode is available only when
> the device is in development.»*

La ROM abre el depurador y se queda en un bucle; `probe-rs` carga el ELF en
AXISRAM2 y lo arranca. **Sin cabecera, sin firma, sin STM32CubeProgrammer.**
Es exactamente lo que hace `cargo run --release` con el `memory.x` de hoy
(FLASH `0x341A0000`, RAM `0x341E0000`, copiado de `examples/stm32n6/memory.x`
de embassy, cuyo README dice: *«primarily intended for dev mode — loaded
directly to RAM via probe-rs with no flash boot required»*).

Testigo en la placa: en development boot **el LED rojo de PG10 se queda fijo**
(AN5967 §11.2, p. 25: *«In development boot mode, the PG10 pin is set to low
open-drain, meaning the debug LED lights up brightly»*). Si parpadea rápido,
la ROM está en serial boot esperando un cable: BOOT1 está abajo.

Con `probe-rs 0.32.0` (instalado hoy) el chip existe con su mapa:
`probe-rs chip info STM32N657` da las AXISRAM en `0x34000000` (3,8 MiB) y la
NOR externa como NVM en `0x70000000` (128 MiB). Ese NVM es lo que permite
grabar la flash externa desde probe-rs en el camino C.

### B. Serial boot: el «USB serial de la ROM», y no es gratis

BOOT0 arriba, BOOT1 abajo. RM0486 §9.1.2, p. 286: *«USB boot: USB 2.0 OTG
HS»* y *«UART boot: USART1, USART2, and UART4»*. La ROM recibe la imagen por
ese cable, la deja en RAM y la ejecuta. Es el camino que el #231 llamaba «el
cómodo para los primeros días» y **no lo es para nosotros**: la imagen pasa por
la ROM, así que lleva la misma cabecera de ST que el FSBL (§3.2 arriba: la ROM
autentica lo que entra *«through UART, USB»*), y el host que la empuja es
STM32CubeProgrammer. Lo único que ahorra frente a C es grabar la NOR. Frente a
A no ahorra nada y cuesta dos herramientas. Queda anotado como suplente si un
día el ST-LINK de la DK falla.

### C. Flash boot: el arranque de verdad, y ya está escrito en Rust

BOOT0 y BOOT1 abajo. La ROM lee el FSBL de la NOR (§9.1.1: *«If no boot
source is programmed in OTP, default source is serial NOR»*), lo copia a
`0x34180400` y salta. El FSBL levanta la XSPI2 en modo memoria y salta a la
aplicación, que corre **desde la NOR mapeada** en `0x70100400`.

**No hay que escribirlo.** La rev de embassy que fija nuestro `Cargo.lock`
(`dc6b716`, rama `n6-usb` del fork) trae `examples/stm32n6-flashboot/`: dos
crates, `fsbl` (sobre `embassy-boot-stm32`) y `app`, para la DK y la Nucleo,
con su `justfile` y sus notas (`BOOT_NOTES.md`). Lo que hace el FSBL, leído
en `fsbl/src/main.rs`:

1. Abre el depurador escribiendo en BSEC (`AP_UNLOCK` en `0xE90`, `DBGCR` en
   `0xE8C`, y sube el HDPL de 0 a 1 por `0xE98` si hace falta). El propio
   código avisa: en un chip BSEC-open esas escrituras no hacen nada.
2. `VTOR = 0x34180400`.
3. Limpia la XSPI1 que usó la ROM (`XSPIM MODE=1`) y pone `XSPIM MODE=0`:
   XSPI1 a P1, XSPI2 a P2.
4. Reloj: `SupplyConfig::External` (la DK lleva SMPS externo),
   `xspi2sel = Per` (HSI 64 MHz), `vddio3_1v8 = true`.
5. Enciende las seis AXISRAM, las dos AHBSRAM y la BKPSRAM.
6. XSPI2 contra la MX66UW1G45G de 128 MiB (`MemoryType::Macronix`,
   prescaler 8), modo memoria, y `embassy-boot` decide ACTIVE/DFU y salta.

Los dos mapas, tal como vienen:

```
NOR externa (0x70000000, 128 MiB):
  BOOTLOADER  0x70000000  1 MiB    <- fsbl-trusted.bin
  ACTIVE      0x70100000  2044 K   <- app-trusted.bin (codigo en +0x400)
  DFU         0x70300000  2048 K
  STATE       0x70500000  12 K

FSBL en SRAM:            RAM 0x34100000 513 K, FLASH 0x34180400 507 K
App (XIP desde la NOR):  FLASH 0x70100400 2043 K, RAM 0x34100000 512 K
```

**Compila aquí, hoy** (copia en el scratchpad con los `path` apuntando al
checkout de `~/.cargo`, target `thumbv8m.main-none-eabihf`, `--features dk`):

| Crate | `cargo build --release` | `text` | `.bin` |
|---|---|---|---|
| `stm32n6-fsbl` | verde, 1 min 39 s | 17 432 B | 17 488 B |
| `stm32n6-app` | verde, 1 min 05 s | 19 288 B | 19 292 B |

Es lo que embassy sabe hacer con nuestro toolchain; que arranque es de la
placa.

#### La cadena de mandos, sin `just`

El `justfile` son cuatro mandos de verdad. Con `$ST` = `bin/` de
STM32CubeProgrammer:

```bash
# 1. ELF -> binario crudo (cargo-binutils + llvm-tools, instalados hoy)
rust-objcopy -O binary target/thumbv8m.main-none-eabihf/release/stm32n6-fsbl fsbl.bin
rust-objcopy -O binary target/thumbv8m.main-none-eabihf/release/stm32n6-app  app.bin

# 2. La cabecera de ST (sin clave: -nk). Igual para los dos binarios.
$ST/STM32_SigningTool_CLI -bin fsbl.bin -nk -of 0x80000000 -t fsbl -o fsbl-trusted.bin -hv 2.3 -align -dump fsbl-trusted.bin -s
$ST/STM32_SigningTool_CLI -bin app.bin  -nk -of 0x80000000 -t fsbl -o app-trusted.bin  -hv 2.3 -align -dump app-trusted.bin  -s

# 3. A la NOR, por el ST-LINK de la DK
probe-rs download --chip STM32N657 --binary-format bin --base-address 0x70000000 fsbl-trusted.bin
probe-rs download --chip STM32N657 --binary-format bin --base-address 0x70100000 app-trusted.bin

# 4. BOOT0 y BOOT1 abajo, reset.
```

`-align` no es opcional: sin él la herramienta lee el punto de entrada en el
offset `0x70` del binario (una entrada de la tabla de vectores) en vez del
vector de reset en `0x04`; con él rellena a `0x400` y lo saca bien (comentario
del `justfile`, verificado por quien lo escribió, no por nosotros). `-hv 2.3`
es la versión de cabecera del N6. Si probe-rs no consigue grabar la NOR, el
`justfile` trae el suplente con `STM32_Programmer_CLI -c port=SWD
mode=HOTPLUG -el ExternalLoader/MX66UW1G45G_STM32N6570-DK.stldr -d ...`.

## Lo que le falta a NUESTRO firmware para el camino C

Hoy `fw/` está enlazado para A y solo para A. Para C:

1. **Un segundo mapa.** `memory.x` con FLASH en `0x70100400` y RAM en
   `0x34100000` (el de `flashboot/app/memory.x`, arriba). Es un archivo
   distinto, no un `if`: A y C no se mezclan.
2. **Dos líneas de reloj** en `usb::configuracion()`, porque la app tiene que
   llegar al mismo estado que dejó el FSBL: `xspi2sel = XspiClkSrc::Per` y
   `vddio3_1v8 = true`, además del `SupplyConfig::External` que ya está. Las
   dos existen en `rcc/n6.rs` de la rev fijada.
3. **La PLL4 del PHY de USB** sigue nuestra: el FSBL no la toca.
4. **Decidir dónde corre el código.** El FSBL de embassy deja la app en XIP
   desde la NOR por XSPI2 (con `cacheaxi`/`icache` por medio). Nuestro
   `memory.x` de hoy razona un framebuffer de 768 KB contiguo en AXISRAM2;
   una app XIP libera esa RAM entera, pero el sampler (`psram_budget.py`)
   quiere la XSPI1 para la PSRAM y la biblioteca en la XSPI2, la misma que
   sirve el código. Eso es del papel del hub (riesgo 2), no de este archivo;
   se anota como HUECO, no se decide aquí.

## Herramientas, y qué hay en esta máquina (2026-09-11)

| Herramienta | Para | Estado |
|---|---|---|
| `rustup target thumbv8m.main-none-eabihf` | compilar | instalado |
| `llvm-tools` + `cargo-binutils 0.4.0` (`rust-objcopy`, `rust-size`) | ELF a `.bin` | **instalado hoy** |
| `probe-rs-tools 0.32.0` | A: cargar a RAM; C: grabar la NOR (`NVM 0x70000000` en su mapa) | **instalado hoy**. El README de embassy decía «v0.32+ not yet released»; salió a crates.io y es la que está |
| STM32CubeProgrammer (`STM32_SigningTool_CLI`, `STM32_Programmer_CLI`, `ExternalLoader/*.stldr`) | la cabecera de B y C; suplente para grabar | **falta**. Solo está STM32CubeMX. Se baja de st.com con cuenta; `curl` no entra (memoria del repo): lo baja Samuel |
| `just` | recetas | no hace falta: los mandos están arriba |
| `lrzsz` (`sx`), `uhubctl` | DFU por UART, ciclo de alimentación | opcionales, del `justfile` |

**Lo único que bloquea el camino C sin placa es STM32CubeProgrammer.** Con él
instalado, el paso 2 se puede correr hoy sobre los `.bin` del scratchpad y
dejar los `-trusted.bin` listos.

## Fuentes

- RM0486 Rev 4, `docs/reference/datasheets/stm32n6-rm0486-rev4.pdf`: §3.2
  p. 183, §9.1 pp. 286-287.
- AN5967 Rev 5, `docs/reference/datasheets/stm32n6-an5967-rev5.pdf`: §10
  p. 24 (Tabla 10), §11.2 p. 25.
- embassy `dc6b716` (`~/.cargo/git/checkouts/embassy-*/dc6b716/`):
  `examples/stm32n6/README.md`, `examples/stm32n6-flashboot/{README.md,
  BOOT_NOTES.md, justfile, fsbl/src/main.rs, fsbl/memory.x, app/memory.x,
  app/src/main.rs}`.
- UM3300 (la DK) **no está en el repo**: los interruptores de BOOT se citan
  por la Tabla 32 del RM y por el README de embassy («Set both BOOT switches
  to LOW»).
