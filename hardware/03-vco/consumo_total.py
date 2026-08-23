"""Corriente del instrumento por riel, y cuanto queda para los invitados.

    python consumo_total.py

BLOQUEANTE (modulo-voz-total S8 y S9.4). Nace de dos hallazgos de la junta:

  * S-8: la v1 comparaba "+90 mA" contra los 650 totales como si fueran
    holgura libre. El consumo se re-suma ENTERO, no en delta.
  * Acta E-4: la fila de abajo pasa a ser rack Eurorack de verdad, asi que
    el presupuesto deja de sumar "el instrumento" y pasa a sumar el
    instrumento MAS una reserva declarada para modulos invitados (#169).

--- La regla de este guion ---------------------------------------------------

Cada carga lleva su ORIGEN pegado, y hay solo tres:

  CITADO         hoja de datos leida, con pagina
  DECLARADO      decision de diseno escrita en el repo
  POR_CONFIRMAR  cota conservadora; falta la hoja

El guion reporta que fraccion del total sigue en POR_CONFIRMAR. Un presupuesto
que no dice cuanto de si mismo es fe no es un presupuesto.

--- Que rieles ---------------------------------------------------------------

Los 650 mA/riel del modulo 1 son los de +-12 V. El +5 V viene de la IRM-15-5
aparte (spec del cerebro S9), asi que los DAC, la referencia, los micros y los
LED NO cargan este presupuesto: cuelgan de otra fuente. Aqui se suma +-12.
"""
from __future__ import annotations

CITADO, DECLARADO, POR_CONFIRMAR = "CITADO", "DECLARADO", "POR_CONFIRMAR"

# --- el techo, y la puerta --------------------------------------------------
RIEL_MA = 650.0        # hardware/01-power-supply/README.md: "PCB ruteada a
                       # 650 mA/riel"
MARGEN = 0.30          # voz-total S8: "si no cierra con un 30 % de margen,
                       # se renegocia antes del cobre"
USABLE_MA = RIEL_MA / (1.0 + MARGEN)


class Carga:
    def __init__(self, nombre, n, mas12, menos12, origen, nota):
        self.nombre, self.n = nombre, n
        self.mas12, self.menos12 = mas12, menos12
        self.origen, self.nota = origen, nota

    @property
    def total_mas(self):
        return self.n * self.mas12

    @property
    def total_menos(self):
        return self.n * self.menos12


# --- modulo de Voz: 16 canales, estereo topologia A (acta E-6) --------------
VOZ = [
    Carga("SSI2130", 16, 3.75, 2.90, CITADO,
          "ssi2130-rev2.4 p.2: ISY+ 3,75 mA / ISY- -2,90 mA"),
    Carga("LM13700 (filtro)", 16, 2.6, 2.6, CITADO,
          "lm13700 p.5: 2,6 mA con IABC=500 uA, AMBOS canales, a +-15 V"),
    Carga("SSI2164 (VCA)", 12, 8.4, 8.4, CITADO,
          "ssi2164 p.5: '+-8,4 mA con 1,0 mA de mode current'. "
          "12 chips = 16 VCA de resonancia + 32 de voz (estereo A)"),
    Carga("TL074", 18, 5.6, 5.6, POR_CONFIRMAR,
          "TL074 clasico, 1,4 mA por amplificador. El BOM pide TL074H, que "
          "consume MENOS: esta es cota alta hasta que llegue esa hoja. "
          "16 de canal + 2 de la suma y salida que llegan con E-5"),
]

# --- lo demas que cuelga de +-12 -------------------------------------------
RESTO = [
    Carga("AD75019 (bahia)", 2, 10.0, 10.0, POR_CONFIRMAR,
          "crosspoint +-12 V. Cota; falta la hoja"),
    Carga("codec de 24 bits", 1, 15.0, 15.0, POR_CONFIRMAR,
          "los oidos que llegan con E-5. Pieza sin elegir todavia"),
    Carga("mux analogico de medida", 2, 1.0, 1.0, POR_CONFIRMAR,
          "ADG1206, camino de caracterizacion. Cota"),
]

# El cerebro, los micros, los DAC, la referencia y los LED cuelgan del +5 V
# de la IRM-15-5, no de este riel (spec del cerebro S9).


def suma(cargas):
    return (sum(c.total_mas for c in cargas),
            sum(c.total_menos for c in cargas))


def demo() -> None:
    todo = VOZ + RESTO
    print("Consumo del instrumento en +-12 V\n")
    print(f"  {'carga':24s} {'n':>3s} {'+12 mA':>8s} {'-12 mA':>8s}  origen")
    for c in todo:
        print(f"  {c.nombre:24s} {c.n:3d} {c.total_mas:8.1f} "
              f"{c.total_menos:8.1f}  {c.origen}")

    mas, menos = suma(todo)
    peor = max(mas, menos)
    print(f"\n  {'TOTAL':24s} {'':3s} {mas:8.1f} {menos:8.1f}")

    # --- cuanto de esto es fe --------------------------------------------
    duda = suma([c for c in todo if c.origen == POR_CONFIRMAR])
    frac = max(duda) / peor
    print(f"\n  de eso, POR CONFIRMAR: {max(duda):.1f} mA  ({frac:.0%} del "
          "peor riel)")
    for c in todo:
        if c.origen == POR_CONFIRMAR:
            print(f"    - {c.nombre}: {c.nota}")

    citado = suma([c for c in todo if c.origen == CITADO])
    print(f"\n  y solo con lo CITADO ya son {max(citado):.1f} mA: aunque todo "
          "lo dudoso")
    print("  saliera a cero, el instrumento no baja de ahi.")
    assert max(citado) < USABLE_MA, (
        "si la parte citada sola se pasara, no habria nada que discutir")

    # --- la puerta ---------------------------------------------------------
    print(f"\npuerta: {RIEL_MA:.0f} mA/riel con {MARGEN:.0%} de margen "
          f"= {USABLE_MA:.0f} mA utiles")
    print(f"  peor riel: {peor:.1f} mA  ->  "
          f"{'OK' if peor <= USABLE_MA else '<<< NO CABE'}")
    assert peor <= USABLE_MA, (
        f"el instrumento se pasa: {peor:.1f} contra {USABLE_MA:.0f} mA")

    # --- lo que E-4 pedia: la reserva de invitados (#169) -----------------
    reserva = USABLE_MA - peor
    print(f"\nreserva para modulos invitados (acta E-4, #169): "
          f"{reserva:.0f} mA/riel")
    print(f"  eso son {reserva/30:.0f} modulos de 30 mA, o "
          f"{reserva/60:.0f} de 60.")
    print("  Un delay analogico de BBD anda por ahi. NO es holgura del")
    print("  instrumento: es un compromiso con la fila de abajo, y gastarlo")
    print("  en el instrumento cierra el rack sin avisar.")
    assert reserva >= 120.0, (
        "por debajo de 120 mA/riel la fila de abajo deja de ser rack de "
        "verdad y E-4 se vuelve una promesa vacia")

    # --- el que mas mueve la aguja ----------------------------------------
    print("\nsensibilidad -- que hoja de datos cambiaria mas el numero:\n")
    for c in sorted(todo, key=lambda c: -max(c.total_mas, c.total_menos))[:3]:
        m = max(c.total_mas, c.total_menos)
        print(f"  {c.nombre:24s} {m:6.1f} mA  ({m/peor:5.1%})  {c.origen}")
    print("\n  El TL074 es la unica carga grande sin citar, y esta puesta")
    print("  ALTA a proposito: el TL074H del BOM consume menos, asi que la")
    print("  hoja solo puede mejorar este numero, nunca empeorarlo.")

    print("\nOK: presupuesto cerrado.")


if __name__ == "__main__":
    demo()
