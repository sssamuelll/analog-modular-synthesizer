# Contribuir al proyecto SAM17

¡Gracias por tu interés en colaborar! Este proyecto reproduce y mejora el
sintetizador analógico modular descrito en `docs/thesis.pdf`. Toda contribución
es bienvenida: correcciones de la documentación, simulaciones SPICE, mejoras de
hardware, código del firmware MIDI/CV o ideas nuevas para módulos adicionales.

## Antes de empezar

1. **Lee la [constitución](.specify/memory/constitution.md).** Son siete
   principios innegociables y las puertas de calidad del proyecto. No son buenas
   intenciones: cada uno está ahí porque su ausencia ya costó trabajo perdido, y
   el caso viene citado. Todo PR se revisa contra ella.
2. Lee el [README](README.md) y las dos arquitecturas vigentes:
   [analógica](docs/architecture-poly.md) (poly de 4 voces) y
   [de cómputo](docs/architecture-compute.md) (micro en Rust, computadora
   externa y opcional, VST compañero y agente de IA). [`architecture.md`](docs/architecture.md) es la referencia
   monofónica de la tesis.
3. Revisa los *issues* abiertos para ver si tu idea ya está en discusión.
4. Si vas a hacer un cambio grande, abre primero un *issue* para conversarlo.

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

4. Si tocas hardware, corre las puertas de calidad antes de abrir el PR:

   ```bash
   python hardware/tools/gates.py
   ```

   Corre todos los `check_*.py`, todos los `*_budget.py`, las simulaciones y la
   firma de conectividad. Si cambia la
   conectividad de un módulo a propósito, regenera su golden con
   `python hardware/tools/netdiff.py --write` y **commitéalo junto al cambio de
   diseño**, para que la revisión vea las dos cosas a la vez. Detalle en
   [`hardware/tools/README.md`](hardware/tools/README.md).

5. Abre el Pull Request indicando: módulo afectado, qué cambia y cómo se
   probó (mediciones, simulaciones, capturas, etc.).

## Las puertas corren solas, y son las únicas que hay

**GitHub Actions está deshabilitado en este repositorio** — es privado, y el
workflow figura como `disabled_manually`. El `ci.yml` sigue ahí porque es la
receta, pero **no ha corrido desde el PR #3**. Así que las puertas locales no
son un adelanto de CI: **son la única puerta que tiene el proyecto.**

Para que no dependan de acordarse, hay un hook. Se instala una vez:

```bash
git config core.hooksPath .githooks
```

A partir de ahí, cada `git push` corre lo mismo que correría el workflow, en el
mismo orden:

| | Qué corre |
|---|---|
| `hardware` | `python hardware/tools/gates.py` |
| `firmware` | `ruff check .` y `pytest` en `software/midi-cv` |
| `nucleo` | `cargo test`, `cargo clippy -D warnings` y `cargo fmt --check` en `software/nucleo` |

Tarda unos dos minutos y medio; casi todo es `check_pcb.py` de la fuente v3.

Y cubre **más** que el workflow: los dos guiones que necesitan el Python de
KiCad salían HUECO en CI —instalar KiCad en el runner costaba más de lo que
cubría— y aquí corren de verdad, porque la máquina lo tiene.

Si algo sale en rojo, el push se bloquea y el hook imprime el log. Saltárselo se
puede —`git push --no-verify`— pero **entonces dilo en el PR**.

> Lo que un hook no puede cazar es lo que su propia lista no incluye. Dos veces
> en un mismo día pasó lo mismo: `software/nucleo` llevaba 190 tests que ningún
> job ejecutaba, y dos presupuestos nuevos salieron con nombres que el glob de
> `gates.py` no recogía. **Si añades un guion ejecutable, que se llame
> `check_*.py` o `*_budget.py`** — es lo que el descubridor busca, y un guion
> que el gate no ve no es un gate.

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
