# Contribuir al proyecto SAM17

¡Gracias por tu interés en colaborar! Este proyecto reproduce y mejora el
sintetizador analógico modular descrito en `docs/thesis.pdf`. Toda contribución
es bienvenida: correcciones de la documentación, simulaciones SPICE, mejoras de
hardware, código del firmware MIDI/CV o ideas nuevas para módulos adicionales.

## Antes de empezar

1. Lee el [README](README.md) y la [arquitectura](docs/architecture.md).
2. Revisa los *issues* abiertos para ver si tu idea ya está en discusión.
3. Si vas a hacer un cambio grande, abre primero un *issue* para conversarlo.

## Flujo de trabajo

1. *Fork* del repositorio y crea una rama descriptiva: `feat/vco-pwm-input`,
   `fix/vca-offset`, `docs/midi-cv-pinout`, etc.
2. Haz tus cambios en commits pequeños y con mensajes claros (en español o
   inglés, ambos sirven). Sigue el formato [Conventional Commits](https://www.conventionalcommits.org/)
   cuando puedas: `feat(vcf): añade input de modulación a 1 V/oct`.
3. Si tocas firmware Python, ejecuta los linters/tests locales:

   ```bash
   cd software/midi-cv
   pip install -e ".[dev]"
   ruff check .
   pytest
   ```

4. Abre el Pull Request indicando: módulo afectado, qué cambia y cómo se
   probó (mediciones, simulaciones, capturas, etc.).

## Convenciones por área

### Hardware (KiCad)

- Un proyecto KiCad por módulo, dentro de `hardware/NN-<módulo>/kicad/`.
- Esquemáticos en `schematics/` exportados también a PDF.
- BOM en CSV (`bom.csv`) con columnas: `ref,value,footprint,quantity,supplier,notes`.
- Nombres de redes en mayúsculas: `+12V`, `-12V`, `+5V`, `GND`, `CV_NOTE`,
  `GATE`, `VCO_OUT`, etc.

### Simulaciones SPICE

- Una carpeta por módulo dentro de `simulations/<módulo>/`.
- Incluye el `.asc` (LTspice) o `.cir` (ngspice) y un README breve con qué
  se pretende validar y los resultados esperados.

### Firmware (`software/midi-cv`)

- Python ≥ 3.10, type hints obligatorios en código nuevo.
- Formateo con `ruff format`, lint con `ruff check`.
- Tests con `pytest`. Mockea `RPi.GPIO` y `spidev` para que los tests corran
  fuera del Pi (ver `tests/conftest.py`).

### Documentación

- Markdown estándar (CommonMark + GFM), encabezados en español.
- Imágenes en `docs/images/` referenciadas con rutas relativas.
- Si añades un módulo nuevo o cambias uno existente, actualiza también el
  resumen en `docs/architecture.md` y el README raíz.

## Código de conducta

Sé respetuoso, técnico y constructivo. Las críticas se dirigen a las ideas y
diseños, no a las personas.
