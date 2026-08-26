#!/usr/bin/env python3
"""La procedencia del censo de pines, convertida en puerta.

    python check_pinout_n657.py

POR QUE EXISTE ESTE GUION

  El censo del N657 (micro_budget.py, issue #213) carga una destilacion de
  la Tabla 16 del DS14791 Rev 2 y decide una COMPRA con ella. Su junta dejo
  el hallazgo escrito: "los datos del censo no son reproducibles desde el
  repo: el script de extraccion que se cita no existe" -- la tabla era un
  dato con una nota jurando que no lo era. Este guion es esa extraccion,
  versionada: relee el PDF del arbol, re-deriva la tabla y los totales de
  GPIO, y compara contra las constantes del censo, senal por senal y pin
  por pin. Si alguien edita N6_PINES a mano, o cambia la revision del DS,
  esta puerta grita.

  La misma junta cazo la unica omision de la v1 (PG11 lleva ETH1_MDC y
  faltaba): esta puerta la habria cazado sola, y ahora caza las proximas.

FUENTE

  docs/reference/datasheets/stm32n657-ds14791-rev2.pdf
  Tabla 16 (pp86-109): una fila por pin; columnas = balls en VFBGA142/169/
  178/198/223/264, nombre, tipo, estructura, notas, funciones alternas y
  adicionales. El PDF vuelca ~60 filas rotadas (caracter por caracter, con
  los guiones de columnas ausentes pegados: "----" = 4 ausencias); se
  reconstruyen aqui de forma determinista. Una sola reparacion manual
  (PP11), declarada abajo con su motivo.
"""
from __future__ import annotations

import os
import re
import sys

sys.stdout.reconfigure(errors="replace")

RAIZ = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(RAIZ, "..", "..", "docs", "reference", "datasheets",
                   "stm32n657-ds14791-rev2.pdf")

try:
    from pypdf import PdfReader
except ImportError:
    print("HUECO: necesita pypdf (pip install pypdf) para releer el DS")
    raise SystemExit(2)

sys.path.insert(0, RAIZ)
import micro_budget as mb  # noqa: E402  (las constantes bajo prueba)

PKGS = ["142", "169", "178", "198", "223", "264"]

# --- extraccion determinista de la Tabla 16 (pp86-109) ---------------------

HEADER_JUNK = (
    "Pinout, pin description and alternate functions",
    "STM32N647xx STM32N657xx",
    "DS14791 Rev 2",
    "Table 16. Pin description",
    "Pin number",
    "Pin name (function",
    "after reset)",
    "Pin type",
    "I/O structure",
    "Notes",
    "Alternate functions",
    "dditional functions",  # "A dditional functions" partido por el PDF
    "VFBGA142", "VFBGA169", "VFBGA178", "VFBGA198", "VFBGA223", "VFBGA264",
)

# Un ball del grid es UNA letra (A-W sin I,O,Q,S) + digitos; los nombres de
# pin (PA0, PN12) llevan dos letras y no son balls.
BALL = r"(?:[A-HJ-NPR-W]\d{1,2}|-)"
NAME = r"[A-Z][A-Z0-9_+/().-]*"
ROW_START = re.compile(
    rf"(?m)^({BALL})\s+({BALL})\s+({BALL})\s+({BALL})\s+({BALL})\s+({BALL})\s+({NAME})\b"
)
BALLLIKE = re.compile(r"^[A-HJ-NPR-W]\d{1,2}$")
ES_EXPLOTADA = re.compile(
    r"^(?:-{2,6}|(?:[A-HJ-NPR-W]\d{1,2}\s+){1,5}-{0,6})\s*(?:[A-Z0-9] ){4,}")


def _reparar_linea(ln: str) -> str:
    """Filas rotadas: pega las rachas de caracteres sueltos y separa los
    guiones de columnas ausentes."""
    toks, out, run = ln.split(), [], []

    def vaciar():
        if len(run) >= 4:  # racha explotada real, no una sigla suelta
            pegado = "".join(run)
            # nombres de pin (dos letras) ANTES que balls (una letra)
            out.extend(re.findall(r"P[A-Q]\d{1,2}|[A-Z]\d{1,2}|[A-Z]+|\d+",
                                  pegado))
        else:
            out.extend(run)
        run.clear()

    for t in toks:
        if len(t) == 1 and t.isalnum():
            run.append(t)
            continue
        vaciar()
        if re.fullmatch(r"-{2,6}", t):
            out.extend("-" * len(t))
        else:
            out.append(t)
    vaciar()
    return " ".join(out)


def extraer_filas() -> list[dict]:
    r = PdfReader(PDF)
    lines = []
    for n in range(86, 110):  # paginas impresas 86..109
        t = r.pages[n - 1].extract_text() or ""
        for ln in t.splitlines():
            s = ln.strip()
            if not s or any(j in s for j in HEADER_JUNK):
                continue
            if re.fullmatch(r"\d{2,3}/244", s):
                continue
            lines.append(s)
    lines = [_reparar_linea(ln) if ES_EXPLOTADA.match(ln) else ln
             for ln in lines]
    text = "\n".join(lines)

    rows = []
    starts = list(ROW_START.finditer(text))
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        rest = text[m.end():end].replace("\n", " ").strip()
        caps = [m.group(k) for k in range(1, 7)]
        name = m.group(7)
        # El "-" final de la columna "Additional functions" de la fila
        # anterior cae al inicio de linea y desplaza la captura en uno.
        if BALLLIKE.match(name) and caps[0] == "-":
            toks = rest.split(None, 1)
            caps = caps[1:] + [name]
            name = toks[0]
            rest = toks[1] if len(toks) > 1 else ""
        balls = {p: (caps[k] if caps[k] != "-" else None)
                 for k, p in enumerate(PKGS)}
        rows.append({"balls": balls, "name": name, "rest": rest})

    # Reparacion manual unica: el rest de PP11 sale rotado e ilegible para
    # la busqueda ("XSPIM _ P 1 _ IO 11 , F M C _ D 2 7"). Verificada a ojo
    # contra el volcado crudo; las otras filas mangled son de alimentacion.
    for row in rows:
        if row["name"] == "PP11" and "XSPIM _" in row["rest"]:
            row["rest"] = "I/O - XSPIM_P1_IO11, FMC_D27, EVENTOUT -"
    return rows


def _tolerante(senal: str) -> re.Pattern:
    """El PDF parte nombres con espacios/saltos: busqueda tolerante.

    La cola exige ademas que tras el nombre no venga un digito NI SIQUIERA
    separado por espacios: la junta de la pantalla demostro que sin eso,
    sobre una fila explotada sin reparar ("IO 1 1"), XSPIM_P1_IO1 matchea
    dentro de XSPIM_P1_IO11 -- hoy lo tapaba solo la reparacion manual de
    PP11, y una revision futura del PDF no tendria esa defensa."""
    return re.compile(r"(?<![A-Z0-9_])" + r"\s*".join(map(re.escape, senal))
                      + r"(?![0-9A-Z])(?!\s+[0-9])")


ADC_RX = re.compile(r"ADC\s*\d\s*_\s*INP\s*\d+")


RESERVADOS = {"PA13", "PA14", "PH0", "PH1", "PC14", "PC15"} | \
    {f"PN{i}" for i in range(13)}


def main() -> int:
    filas = extraer_filas()
    fallos: list[str] = []

    # 1. Las senales que el censo demanda, re-derivadas del PDF. CAPTURAS
    #    trae ya las dos mudadas a TIM1, y PANTALLA las 28 del LTDC (acta
    #    camino A).
    demandadas = set(mb.CAPTURAS) | set(mb.RGMII) | set(mb.PSRAM) \
        | set(mb.PANTALLA)
    demandadas |= {f"SAI{i}_{s}" for i in (1, 2)
                   for s in ("MCLK_A", "SCK_A", "FS_A", "SD_A", "SD_B")}
    demandadas |= {f"SPI{i}_{s}" for i in (1, 2, 3, 4, 5, 6)
                   for s in ("SCK", "MOSI", "MISO", "NSS")}
    demandadas |= {f"I2C{i}_{s}" for i in (1, 2, 3, 4)
                   for s in ("SCL", "SDA")}

    gpio_rx = re.compile(r"^P[A-Q]\d{1,2}$")
    frescas: dict[str, set] = {s: set() for s in demandadas}
    frescas["ADC_IN"] = set()
    for row in filas:
        nombre = row["name"].split("(")[0].split("-")[0]
        if not gpio_rx.match(nombre):
            continue
        # Las reservas fijas (SWD/HSE/LSE/XSPI2) no son candidatos del
        # censo POR DISENO, asi que tampoco se cotejan como tales: el DS
        # saca LCD_B4/LCD_B6 tambien por PN10/PN11, pero el puerto PN
        # entero es del arranque y la biblioteca.
        if nombre in RESERVADOS:
            continue
        pres = "".join("x" if row["balls"][p] else "." for p in PKGS)
        for s in demandadas:
            if _tolerante(s).search(row["rest"]):
                frescas[s].add((nombre, pres))
        if ADC_RX.search(row["rest"]):
            frescas["ADC_IN"].add((nombre, pres))

    for s in sorted(frescas):
        del_censo = {(pin, pres) for pin, (pres, ss) in mb.N6_PINES.items()
                     if s in ss}
        if frescas[s] != del_censo:
            fallos.append(
                f"{s}: PDF dice {sorted(frescas[s])}, "
                f"el censo dice {sorted(del_censo)}")

    # 2. Los totales de GPIO por encapsulado (el pool del que se restan
    #    reservas y reparto -- la junta noto que 4 de los 6 no los
    #    vigilaba nadie).
    for k, p in enumerate(PKGS):
        total = sum(1 for row in filas
                    if gpio_rx.match(row["name"].split("(")[0].split("-")[0])
                    and row["balls"][p])
        censado = mb.N6_GPIO_TOTAL[f"VFBGA{p}"]
        if total != censado:
            fallos.append(f"GPIO VFBGA{p}: PDF da {total}, censo {censado}")

    # 3. La reserva XSPI2 (arranque + biblioteca): PN0..PN12 en los seis.
    pn = {row["name"]: row["balls"] for row in filas
          if re.fullmatch(r"PN\d{1,2}", row["name"])}
    if sorted(pn) != sorted(f"PN{i}" for i in range(13)):
        fallos.append(f"puerto PN: se esperaban PN0..PN12, hay {sorted(pn)}")
    for nombre, balls in pn.items():
        if not all(balls[p] for p in PKGS):
            fallos.append(f"{nombre} no esta en los seis encapsulados")

    if fallos:
        print(f"FALLO: {len(fallos)} discrepancias entre el DS y el censo:")
        for f in fallos:
            print(f"  - {f}")
        return 1

    n_sen = len(frescas)
    print(f"OK: censo reproducido desde el DS. {len(filas)} filas de la "
          f"Tabla 16, {n_sen} senales cotejadas pin por pin, 6 totales de "
          f"GPIO y el puerto PN completo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
