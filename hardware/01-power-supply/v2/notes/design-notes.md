# Design Notes — PSU v2

## §1 Puertas de datasheet

### §1.1 LM2941CT

- [ ] Dropout máximo garantizado sobre temperatura a 1 A (y la curva a ~650 mA si existe). Anotar el número que aplica a 650 mA por el lado conservador.
- [ ] VREF y fórmula de VOUT (esperado: VOUT = 1.275 V × (1 + R1/R2)).
- [ ] Tab del TO-220-5: ¿a qué pin va? (esperado GND; si muerde, mica — se escribe igual).
- [ ] Ventana de ESR y C_OUT mínimo para estabilidad (fija el tipo de C17).
- [ ] Corriente del pin ADJ (error sobre el divisor de ~1.2 mA: despreciable o no).
- [ ] Pin ON/OFF: cómo se ata para siempre-encendido.

### §1.2 LM2991T

- [ ] Dropout máx. garantizado a 650 mA sobre temperatura.
- [ ] VREF y fórmula.
- [ ] Tab (el LM2990 de la v1 mordía — se asume que muerde hasta leer).
- [ ] Carga mínima (esperado 500 µA — la da el divisor).
- [ ] Ventana ESR/C_OUT (fija C18).
- [ ] ON/OFF.

### §1.3 LT3045

- [ ] Fórmula y constante de R_ILIM; calcular el valor para 400 mA/chip y escribirlo (es el valor de R11/R12).
- [ ] ¿ILIM se comparte entre chips en paralelo o va uno por chip? (sección «Paralleling Devices» del DS).
- [ ] Red SET en paralelo: confirmar «una sola R_SET + un solo C_SET, pines SET unidos» y el ballast recomendado.
- [ ] Fuga máxima tolerable del C_SET: anotar el cálculo (cada nA de fuga × 120 kΩ = 120 µV de error) y qué dieléctrico recomienda el DS.
- [ ] Dropout máx. a 350 mA; V_IN abs max (esperado 20 V — justifica el TVS D8); conexión del EP (esperado GND); PG si se deja sin usar; EN/UV atado a siempre-ON.
- [ ] Pinera de los dos packages (DFN-10 3×3 y MSOP-12E) — tabla pin→función en §1.3.
- [ ] Orientación del Schottky de protección inversa out→in en el circuito de aplicación (fija D10).

### §1.4 LT3094

- [ ] Fórmula y constante de R_ILIM; calcular el valor para 400 mA/chip y escribirlo (es el valor de R13/R14).
- [ ] ¿ILIM se comparte entre chips en paralelo o va uno por chip? (sección «Paralleling Devices» del DS).
- [ ] Red SET en paralelo: confirmar «una sola R_SET + un solo C_SET, pines SET unidos» y el ballast recomendado.
- [ ] Fuga máxima tolerable del C_SET: anotar el cálculo (cada nA de fuga × 120 kΩ = 120 µV de error) y qué dieléctrico recomienda el DS.
- [ ] Dropout máx. a 350 mA; V_IN abs max (esperado 20 V — justifica el TVS D9); conexión del EP (esperado GND); PG si se deja sin usar; EN/UV atado a siempre-ON.
- [ ] Pinera de los dos packages (DFN-10 3×3 y MSOP-12E) — tabla pin→función en §1.4.
- [ ] Orientación del Schottky de protección inversa out→in en el circuito de aplicación (fija D11).

## §2 Stock

| parte | código LCSC | stock | básica/extendida | precio | fecha |
|-------|------------|-------|------------------|--------|-------|

## §3 Decisiones y aritmética

(vacío; Task 5 mete el worksheet de F1)

## §4 Medidas de la mula

(vacío; Task 10 mete el protocolo)

## §5 Bring-up

(vacío; Task 10)
