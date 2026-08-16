# Design Notes — PSU v2

## §1 Puertas de datasheet

### §1.1 LM2941CT

Fuente: TI, `LM2941, LM2941C`, doc. SNVS770I (June 1999–Revised January 2015),
`https://www.ti.com/lit/ds/symlink/lm2941.pdf`. Descargado con `curl` (WebFetch no
hizo falta, bajó a la primera).

- [x] **Dropout máximo garantizado**: **1.0 V a IOUT = 1 A**, sobre todo el rango
  de temperatura (LM2941CT: 0–125 °C) — tabla §6.6 "Electrical Characteristics:
  LM2941CT, LM2941CS", p.6 (idéntico en §6.5 para T/S/LD, p.5). A 100 mA: MAX
  200 mV (misma tabla). **No existe un dato garantizado a 650 mA** — el DS solo
  da 100 mA y 1 A. Hay una curva típica por temperatura para 1 A/500 mA/100 mA
  (Fig. 2, p.7), pero es típica, no garantizada. Por el lado conservador (el
  dropout crece monótonamente con la corriente, confirmado en esa misma curva):
  **se usa el MAX de 1 A = 1.0 V como cota aplicable a 650 mA.**
- [x] **VREF y fórmula de VOUT**: VREF **MIN 1.211 / TYP 1.275 / MAX 1.339 V**
  (5 mA ≤ IOUT ≤ 1 A, sobre temperatura completa) — tabla §6.6, p.6. Fórmula real
  del DS (§8.2.2.2, p.13): **VOUT = VREF × (R1+R2)/R1 = VREF × (1 + R2/R1)**.
  **Ojo**: la fórmula esperada en el brief tenía R1 y R2 invertidos — es `1+R2/R1`,
  no `1+R1/R2`. R1 es la resistencia inferior (a masa), R2 la superior (a OUT).
- [x] **Tab del TO-220-5 (KC)**: **GND**. El pin-out del TO-263 (KTT), p.3,
  rotula literalmente "TAB IS GND" y la tabla de pines confirma pin 3 = GND en
  ese package. §10.4.1 (p.17): "The TAB... connected to the die substrate...
  and to device pin 3 [GND]... The TAB must not be connected to any potential
  other than ground." El layout example del TO-220 (Fig. 22, p.15) muestra el
  tab cosido al plano de GND. **No hace falta mica** en el LM2941 (a diferencia
  del LM2991, ver §1.2).
- [x] **Ventana de ESR y C_OUT mínimo**: §8.1 (p.12): COUT ≥ 22 µF, ESR entre
  **100 mΩ y 1 Ω**. §8.2.2.1 (p.13), más permisivo con tantalio: ESR 0.01–5 Ω si
  es tantalio; si es cerámico X5R/X7R 22 µF, se necesita **resistencia serie de
  0.1–1 Ω** para simular el ESR. Fig. 13 (p.9) da la ventana gráfica. **Fija
  C17: no puede ser un MLCC solo** (2–20 mΩ típico, por debajo del piso de
  100 mΩ) — o tantalio, o MLCC + serie R.
- [x] **Corriente del pin ADJ**: el DS **no da un número garantizado en tabla**
  — solo texto en §8.2.2.2 (p.13): "Using 1 kΩ for R1 will ensure that the bias
  current error from the adjust pin will be negligible... R1 higher than 10 kΩ
  may cause the output voltage to shift." Con R1 = 1 kΩ y VREF ≈ 1.275 V, la
  corriente del divisor es ≈ 1.275 mA (~1.2 mA, coincide con el brief); el error
  del ADJ se declara "negligible" de forma cualitativa, sin cifra garantizada
  que citar.
- [x] **Pin ON/OFF**: activo-bajo habilita. §7.4.1 (p.11): "the ON/OFF pin
  voltage must fall below the minimum ON/OFF(ON) voltage threshold (0.8 V) to
  enable... If the ON/OFF function is not needed this pin can be connected
  directly to Ground." Tabla §6.6 (p.6): threshold ON, MAX garantizado = 0.8 V;
  threshold OFF, MIN garantizado = 2 V. **Atar a GND = siempre-encendido**,
  garantizado sobre todo el rango (0 V < 0.8 V).

### §1.2 LM2991T

Fuente: TI, `LM2991`, doc. SNVS099I (May 1999–Revised October 2016),
`https://www.ti.com/lit/ds/symlink/lm2991.pdf`. Descargado con `curl`.

- [x] **Dropout máx. garantizado**: **1.0 V a IOUT = 1 A**, sobre todo el rango
  de temperatura (−40 a 125 °C) — tabla §6.5 "Electrical Characteristics", p.5
  (TYP 0.6 V, MAX 0.8 V a 25 °C; MAX 1 V sobre temperatura). A 0.1 A: MAX 0.3 V
  sobre temperatura. **Igual que el LM2941: no hay dato garantizado a 650 mA.**
  Fig. 1 (p.6) confirma la monotonía (curvas típicas a −55/25/125 °C). Por el
  lado conservador: **se usa el MAX de 1 A = 1.0 V para 650 mA.**
- [x] **VREF y fórmula**: VREF **MIN −1.234 / TYP −1.210 / MAX −1.186 V** a
  25 °C (5 mA ≤ IOUT ≤ 1 A); sobre temperatura completa (−40 a 125 °C): **MIN
  −1.27 / MAX −1.15 V** — tabla §6.5, p.5. Fórmula completa (§8.2.2.4, p.13):
  **VOUT = VREF × (1 + R2/R1) − (IADJ × R2)**, con VREF = −1.21 V. La portada
  (p.1) da la versión simplificada sin el término IADJ; §8.2.2.4 aclara que la
  corriente del ADJ es ≈ 60 nA y que con resistores < 100 kΩ el error es
  despreciable (ejemplo del propio DS: R2 = 100 kΩ, VOUT = −5 V → error de
  0.16 % ignorando IADJ).
- [x] **Tab: MUERDE — confirmado.** Pin-out p.3 (TO-220 KC/NDH y TO-263 KTT):
  el tab está rotulado **"Input"**, y la tabla de pines lo deja explícito: "TAB
  — I: Negative Input voltage. Internally connected directly to the device pin
  3 (IN)... Do NOT connect the thermal tab to ground." No es GND, es la entrada
  negativa sin regular. Coincide con lo que hacía el LM2990 en la v1. **Mica
  obligatoria** si el disipador va a masa de chasis; si no, el tab (y todo lo
  que toque) queda al potencial de VIN−.
- [x] **Carga mínima**: **500 µA**, exacto — §8.2.2.3 (p.13): "A minimum load
  current of 500 μA is required for proper operation. The external resistor
  divider can provide the minimum load, with the resistor from the adjust pin
  to ground set to 2.4 kΩ."
- [x] **Ventana ESR / C_OUT**: §8.2.2.1 (p.12), texto: COUT ≥ 10 µF aluminio
  electrolítico o ≥ 1 µF tantalio, ESR < 10 Ω. Fig. 16 (p.12) da la ventana
  exacta: **ESR entre ~25 mΩ y 10 Ω**. Cerámico ≥ 2.2 µF admitido solo con
  1 Ω de serie recomendado; dieléctrico X7R/X5R si el rango de temperatura
  varía más de ±25 °C del ambiente. **Fija C18: mismo patrón que C17** — ni un
  MLCC solo.
- [x] **ON/OFF**: activo-alto deshabilita. §7.3.1 (p.9): "impedance of the
  voltage source driving the ON/OFF pin must be low enough... 100 µA maximum
  at 2.4 V. If the ON/OFF function is not needed, connect the pin to GND. The
  ON/OFF pin should not be left floating." Tabla §6.5 (p.5): threshold ON, MAX
  garantizado sobre temperatura = 0.8 V; threshold OFF, MIN garantizado sobre
  temperatura = 2.4 V. **Atar a GND = siempre-encendido**, garantizado.

### §1.3 LT3045

**BLOQUEADO — no se pudo descargar el datasheet.** `analog.com` resetea o
cuelga la conexión (TLS) desde este entorno con **todos** los caminos
probados: `curl` (con y sin cabeceras de navegador completas, forzando
HTTP/1.1 y TLS 1.2, con cookie jar y referer), PowerShell
`Invoke-WebRequest`, Python `urllib.request` (dos veces, con streaming y
timeout de 90 s), `.NET HttpClient`, `Start-BitsTransfer` (este sí obtuvo
cabeceras HTTP de vuelta, pero rechazó el cuerpo por no traer
`Content-Length`) y la tool `WebFetch` (dos intentos, timeout de 60 s cada
uno). El patrón — TLS handshake OK, request enviado, reset a los ~19-20 s
sin cuerpo — es consistente con un bloqueo de bot-management (Akamai) del
lado de `analog.com`, no con un problema de sintaxis de la petición.
`ti.com` (LM2941, LM2991) bajó sin problema con el mismo `curl` simple.

No se inventó ningún número de este datasheet. Los valores esperados del
brief (constante de R_ILIM, abs max V_IN ≈ 20 V, EP = GND, etc.) **siguen sin
verificar contra fuente primaria** — quedan como pendiente explícito, no como
hecho.

- [ ] Fórmula y constante de R_ILIM; calcular el valor para 400 mA/chip y escribirlo (es el valor de R11/R12).
- [ ] ¿ILIM se comparte entre chips en paralelo o va uno por chip? (sección «Paralleling Devices» del DS).
- [ ] Red SET en paralelo: confirmar «una sola R_SET + un solo C_SET, pines SET unidos» y el ballast recomendado.
- [ ] Fuga máxima tolerable del C_SET: anotar el cálculo (cada nA de fuga × 120 kΩ = 120 µV de error) y qué dieléctrico recomienda el DS.
- [ ] Dropout máx. a 350 mA; V_IN abs max (esperado 20 V — justifica el TVS D8); conexión del EP (esperado GND); PG si se deja sin usar; EN/UV atado a siempre-ON.
- [ ] Pinera de los dos packages (DFN-10 3×3 y MSOP-12E) — tabla pin→función en §1.3.
- [ ] Orientación del Schottky de protección inversa out→in en el circuito de aplicación (fija D10).

### §1.4 LT3094

**BLOQUEADO por la misma razón que §1.3** — `analog.com` inalcanzable desde
este entorno con los mismos métodos agotados. No se probó siquiera a
localizar la URL exacta del PDF (la página de producto tampoco cargó), así
que ni la URL quedó confirmada.

- [ ] Fórmula y constante de R_ILIM; calcular el valor para 400 mA/chip y escribirlo (es el valor de R13/R14).
- [ ] ¿ILIM se comparte entre chips en paralelo o va uno por chip? (sección «Paralleling Devices» del DS).
- [ ] Red SET en paralelo: confirmar «una sola R_SET + un solo C_SET, pines SET unidos» y el ballast recomendado.
- [ ] Fuga máxima tolerable del C_SET: anotar el cálculo (cada nA de fuga × 120 kΩ = 120 µV de error) y qué dieléctrico recomienda el DS.
- [ ] Dropout máx. a 350 mA; V_IN abs max (esperado 20 V — justifica el TVS D9); conexión del EP (esperado GND); PG si se deja sin usar; EN/UV atado a siempre-ON.
- [ ] Pinera de los dos packages (DFN-10 3×3 y MSOP-12E) — tabla pin→función en §1.4.
- [ ] Orientación del Schottky de protección inversa out→in en el circuito de aplicación (fija D11).

### §1.5 Veredicto GO/NO-GO de márgenes

Recomputado con los dropouts **máximos garantizados** leídos en §1.1/§1.2
(no los típicos), y el valle simulado de 14.12 V de la v1 (Talema 120 VA,
9400 µF/riel, red a 207 V, plena carga — `hardware/01-power-supply/notes/design-notes.md`
§16.5).

```
Positivo: 14.12 V − dropout_max(LM2941 @ 650 mA, conservador = MAX@1A) ≥ 13.1 V
          14.12 V − 1.0 V = 13.12 V ≥ 13.1 V  →  margen = +0.02 V  →  GO

Negativo: 14.12 V − dropout_max(LM2991 @ 650 mA, conservador = MAX@1A) ≥ 12.9 V
          14.12 V − 1.0 V = 13.12 V ≥ 12.9 V  →  margen = +0.22 V  →  GO
```

**Riel negativo: GO cómodo (+0.22 V).**

**Riel positivo: GO, pero por el canto de la uña (+0.02 V).** Esto cierra el
riesgo §11.1 de la spec con un número, y el número que sale es peor de lo que
sonaba la nota de la spec ("el margen de valle +0.22 V el peor"): usando el
dropout **garantizado** en vez del típico, el margen del riel positivo cae a
**2 centésimas de voltio**. Cualquiera de estos se lo come entero:

- Tolerancia de R1/R2 del divisor del LM2941 (desplaza el setpoint de 13.1 V).
- Caída extra en conectores/pistas entre el bulk y el LM2941.
- Que la mula real mida un valle por debajo de los 14.12 V simulados (la
  propia spec, §11.4, ya avisa que esa cifra es "fina hasta que la mula mida").
- Que el dropout real a 650 mA/caliente esté más cerca del MAX de 1 A que del
  TYP de 0.5 V (el DS no da un punto intermedio garantizado — ver §1.1).

No hace falta bajar el setpoint todavía porque el margen no dio negativo, pero
con 0.02 V de colchón la recomendación para Task 4/5 es dejar el trimmer del
divisor del LM2941 con margen para bajar el setpoint (el brief documenta el
trimmer llegando hasta ~12.3 V) **si la medida en la mula real no confirma al
menos unas décimas de margen**. Verificar contra el V_IN mínimo del LT3045
queda pendiente de §1.3 (bloqueado, ver arriba) — no se pudo cerrar ese
extremo de la cadena.

## §2 Stock

| parte | código LCSC | stock | básica/extendida | precio | fecha |
|-------|------------|-------|------------------|--------|-------|

## §3 Decisiones y aritmética

(vacío; Task 5 mete el worksheet de F1)

## §4 Medidas de la mula

(vacío; Task 10 mete el protocolo)

## §5 Bring-up

(vacío; Task 10)
