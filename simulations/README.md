# Simulaciones SPICE

Modelos LTspice / ngspice para validar el comportamiento de los módulos
analógicos antes de ir a la PCB.

| Módulo | Carpeta | Qué validar |
|--------|---------|-------------|
| VCO | [`vco/`](vco) | Forma de las ondas, linealidad 1 V/oct, PWM |
| VCF | [`vcf/`](vcf) | Respuesta en frecuencia (Bode), tracking 1 V/oct, auto-oscilación |
| ADSR | [`adsr/`](adsr) | Envolvente para distintos valores A/D/S/R, tiempos mínimos/máximos |
| VCA | [`vca/`](vca) | THD vs nivel de entrada, feed-through del CV, transferencia |
| Mixer | [`mixer/`](mixer) | Suma con distintos pesos, ruido y crosstalk |
| Power | [`power/`](power) | Rizado bajo carga, regulación de línea |

## Convención

Cada subcarpeta contiene:

- Archivos `.asc` (LTspice) y/o `.cir`/`.net` (ngspice).
- Un `README.md` breve que documente:
  - Qué se está midiendo.
  - Resultados esperados (rangos numéricos).
  - Capturas (`.png`) de las curvas significativas.
- Modelos de componentes (`.lib`, `.mod`) cuando no estén disponibles en
  las librerías estándar (p. ej. CEM3340, LM13700).
