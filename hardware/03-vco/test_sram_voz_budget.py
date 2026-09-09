"""El contrato del censo de SRAM DE LA VOZ, escrito antes que el guion.

    python hardware/03-vco/test_sram_voz_budget.py

La otra mitad de la enmienda de hub sec.534 ("Partir en dos censos: Voz sin
cara, hub con cara"). Este censo es el descendiente directo del viejo
`hardware/02-midi-cv/sram_budget.py`: se queda con lo que de verdad era
suyo --el sampler, las tablas clase Serum, la vara del EP-133-- y suelta la
cara, que se fue al hub con D2 (firmada el 2026-08-30).

Lo que este contrato fija:

  * QUE LA VOZ NO CARGA CON EL FRAMEBUFFER. El censo viejo restaba hasta
    2 304 000 B de doble buffer RGB888 al mismo pote del que come el
    sampler. La pantalla es del hub desde D2; a la Voz no le toca.

  * QUE LA CAMARA Y LA NPU NO SON DE LA VOZ NI CON D3-prima NI SIN ELLA. En
    el papel viejo eran del motor integrado. Hoy, o son del hub (D3-prima
    sin firmar) o son del mago (D3-prima firmada). De la Voz no son en
    ningun escenario, y por eso aqui no aparecen como interruptor: aparecen
    como ausencia.

  * QUE EL BINARIO DE LA VOZ SIGUE SIENDO HUECO, Y POR QUE. El del hub se
    midio el 2026-09-09 (82 280 B) porque `software/nucleo/fw` existe y
    enlaza. Firmware de la Voz no hay: no hay nada que medir. Pero la medida
    del hub NO es inutil aqui -- calibra la parte compartida (pila USB,
    protocolo, modelo, descubrimiento), y deja como unico desconocido de
    verdad los motores de audio. El censo tiene que decir eso en vez de
    heredar el rango viejo como si nada hubiera pasado.

  * LA MISMA GUARDA DE FORMA QUE EL HUB: ningun techo publicado puede
    calcularse por su cuenta. El fallo del 2026-09-09 (dos cuentas de lo
    fijo, techos inflados en 600 000 B) nacio en este archivo.
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "..", "tools"))
import sram_voz_budget as vb                                # noqa: E402
from canario import borde_rojo                              # noqa: E402


# --- la Voz no lleva cara ---------------------------------------------------

def test_la_voz_no_reserva_framebuffer() -> None:
    """D2 (firmada 2026-08-30) mudo la cara al hub.

    Si este censo vuelve a restar un framebuffer, es que alguien copio el
    archivo viejo sin leer que decidio D2."""
    assert not hasattr(vb, "framebuffer_b"), (
        "el censo de la Voz calcula framebuffer: la cara es del hub (D2)")
    fuente = " ".join(str(getattr(vb, n, "")) for n in dir(vb)
                      if not n.startswith("_"))
    assert "800" not in fuente or "PANTALLA" not in dir(vb)


def test_la_camara_y_la_npu_no_son_de_la_voz_en_ningun_escenario() -> None:
    """Ni con D3-prima ni sin ella: o son del hub o son del mago.

    En el papel viejo vivian aqui porque el motor era uno solo."""
    for prohibido in ("NPU_ACTIVACIONES_B", "FRAMES_CAMARA_B"):
        assert not hasattr(vb, prohibido), (
            f"{prohibido} sigue en el censo de la Voz: esos bytes son del "
            f"hub (D3-prima sin firmar) o del mago (D3-prima firmada), "
            f"nunca de la Voz")


# --- lo que si es suyo ------------------------------------------------------

def test_la_voz_conserva_la_demanda_del_motor_de_audio() -> None:
    """Tabla clase Serum residente + buffer de sample de trabajo.

    Son los 1 256 000 B que el censo viejo le cobraba al chip equivocado.
    Aqui si son la demanda de casa."""
    assert vb.demanda_voz_b() == vb.TABLA_SERUM_B + vb.MINIMO_SAMPLE_B


def test_el_binario_de_la_voz_sigue_siendo_un_rango_declarado() -> None:
    """No hay firmware de la Voz que medir, y eso se dice, no se rellena."""
    assert isinstance(vb.BINARIO_VOZ_B, tuple) and len(vb.BINARIO_VOZ_B) == 2
    assert vb.BINARIO_VOZ_B[1] > vb.BINARIO_VOZ_B[0], (
        "un ESTIMADO sin ancho es un numero disfrazado")


def test_la_medida_del_hub_calibra_la_parte_compartida() -> None:
    """82 280 B del hub acotan la pila USB, el protocolo y el modelo.

    Es lo unico que la medida del 2026-09-09 le compra a este censo, y
    tenerlo escrito impide que alguien diga que no le compro nada --o que le
    compro mas de lo que le compro--."""
    assert vb.CALIBRACION_HUB_B == 82_280, (
        "la calibracion que trae la medida del hub cambio de valor sin que "
        "nadie volviera a medir")


# --- la misma guarda de forma que el hub ------------------------------------

def test_todo_techo_publicado_sale_de_la_misma_cuenta_que_el_veredicto() -> None:
    """El fallo del 2026-09-09 nacio en este archivo; no puede renacer.

    `sram_budget.py:85` cobraba cuatro costos fijos y `:149` calculaba los
    techos con dos. Identidad, no cifra: meter el techo como binario deja el
    libre exactamente en la demanda."""
    techo = vb.techo_binario_b()
    assert techo > 0
    assert vb.libre_b(peor=True, binario=techo) == vb.demanda_voz_b(), (
        "el techo del binario de la Voz no sale de fijo_b(): hay dos cuentas "
        "de lo fijo, que es el fallo del 2026-09-09")


def test_el_censo_sale_hueco_mientras_no_haya_firmware_que_medir() -> None:
    """Exit 2. La Voz no tiene binario porque no tiene firmware."""
    assert vb.main() == 2


def test_la_guarda_de_la_voz_muerde_por_el_binario() -> None:
    """Por biseccion, no con un valor escrito a mano."""
    p = vb.parametros()
    rojo = borde_rojo(vb.guarda_voz, p, "binario", 0, vb.SRAM_B,
                      "no cabe en la SRAM de la Voz")
    assert 0 < rojo < vb.SRAM_B


def _tests():
    return [(n, f) for n, f in sorted(globals().items())
            if n.startswith("test_") and callable(f)]


def main() -> int:
    fallos = 0
    for nombre, f in _tests():
        try:
            f()
            print(f"  ok    {nombre}")
        except AssertionError as e:
            fallos += 1
            print(f"  FALLA {nombre}\n        {e}")
    print(f"\n{len(_tests()) - fallos}/{len(_tests())} verdes")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
