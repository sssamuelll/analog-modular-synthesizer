"""El contrato del censo de SRAM DEL HUB, escrito antes que el guion.

    python hardware/02-midi-cv/test_sram_hub_budget.py

De donde sale este archivo: `sram_budget.py` mezclaba tres chips. El papel
del hub lo mando partir el 2026-08-30 y la enmienda quedo sin ejecutar:

    2026-08-30-hub-n657-y-radios-design.md:534
    | hardware/02-midi-cv/sram_budget.py | Partir en dos censos: Voz sin
    | cara, hub con cara (y con colas de audio si sec.6.2) | pendiente

Lo que este contrato fija, y por que cada cosa:

  * QUE EL BINARIO DEL HUB ES MEDIDO. Dejo de ser ESTIMADO el 2026-09-09:
    `fw/` enlaza para el N657 desde el #349 y el mapa del linker es un
    artefacto de escritorio, no del bring-up. El censo viejo decia que ese
    numero "sale del mapa del linker en el paso 2 del bring-up" y por eso
    esperaba una placa que no hacia falta.

  * QUE NINGUN TECHO SE CALCULE DOS VECES. El fallo que destapo todo esto:
    `sram_budget.py:85` cobraba cuatro costos fijos y `:149` calculaba los
    techos con solo dos de ellos --se le caia FRAMES_CAMARA_B-- y publicaba
    techos inflados en 600 000 B. El mismo descuido estaba repetido en
    `:275`. Aqui no se arregla el numero: se arregla que HAYA DOS CUENTAS.
    El techo tiene que salir DE `fijo_b`, y este contrato lo comprueba como
    identidad algebraica, no como cifra.

  * QUE LO NO FIRMADO NO SE DE POR FIRMADO. Dos decisiones abiertas mueven
    1 800 000 B de este censo: D3-prima (la camara y la NPU a un tercer
    chip, sec.3.2 -- la linea de firma del papel la deja PENDIENTE) y donde
    vive la interfaz de audio (sec.6.2, "decision de Samuel con el papel
    propio delante"). El censo las declara como interruptores con su valor
    conservador por defecto; no las decide.

  * QUE NO SE INVENTE LA DEMANDA DEL HUB. El censo viejo le cobraba al hub
    TABLA_SERUM_B + MINIMO_SAMPLE_B = 1 256 000 B. Eso es lo que pide el
    MOTOR DE AUDIO, que vive en la Voz: el hub no corre el sampler
    (hub sec.3.1: "Tiene la misma memoria y ningun sampler"). Lo que el hub
    SI necesita residente no esta enumerado en ningun papel, y este contrato
    exige que se declare HUECO en vez de rellenarlo con el numero del vecino.

Este test puede quedar rojo por el aserto de la demanda aun con el guion
bien escrito: eso no se arregla poniendo un numero, se lleva a Samuel.
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "..", "tools"))
import sram_hub_budget as hb                                # noqa: E402
from canario import borde_rojo                              # noqa: E402


# --- el binario: medido, no estimado ----------------------------------------

def test_el_binario_del_hub_es_un_numero_medido_no_un_rango() -> None:
    """Un rango aqui seria una regresion: el numero existe desde el 2026-09-09.

    El censo viejo lo tenia como BINARIO_B = (700_000, 2_000_000), un
    ESTIMADO sin fuente cuya amplitud (1 300 000 B) era la mayor del censo y
    sostenia su conclusion entera ("el mayor desconocido del motor")."""
    assert isinstance(hb.BINARIO_HUB_B, int), (
        "el binario del hub esta medido: si vuelve a ser rango, alguien "
        "deshizo la medida del 2026-09-09 sin decirlo")


def test_el_binario_es_la_suma_de_las_secciones_que_el_guion_publica() -> None:
    """La cifra no se copia: se recalcula de las secciones que declara.

    El error de este repo no suele estar en el modelo, esta en el salto del
    guion al papel. Si el total y las partes viven en el mismo archivo sin
    atarse, se separan."""
    assert sum(hb.SECCIONES_MEDIDAS.values()) == hb.BINARIO_HUB_B


def test_las_secciones_medidas_son_las_ALLOC_y_no_el_tamano_del_ELF() -> None:
    """3 570 972 B es el ELF en disco con debug = 2; 82 280 es lo que ocupa.

    Confundirlos es un factor 43. El perfil de release de `fw/` lleva
    debug = 2 (fw/Cargo.toml), asi que el archivo no es la huella."""
    assert hb.BINARIO_HUB_B < 200_000, (
        "el binario del hub paso de 200 KB: o crecio de verdad --y entonces "
        "hay que volver a medir y recorrer el censo-- o alguien metio el "
        "tamano del ELF en disco en vez de la suma de las secciones ALLOC")
    assert ".text" in hb.SECCIONES_MEDIDAS and ".bss" in hb.SECCIONES_MEDIDAS


# --- el fallo que destapo todo: dos cuentas para lo mismo --------------------

def test_todo_techo_publicado_sale_de_la_misma_cuenta_que_el_veredicto() -> None:
    """LA guarda de este contrato. Identidad algebraica, no cifra.

    `sram_budget.py:149` calculaba los techos con COLAS + NPU y olvidaba
    FRAMES_CAMARA, mientras `:85` cobraba los cuatro. Resultado: cinco
    techos publicados, todos inflados en 600 000 B, y dos configuraciones
    que el guion daba por posibles y no cierran ni con el binario en cero.

    Comprobarlo con las cifras corregidas seria arreglar el sintoma: el
    numero se vuelve a mover el dia que entre un quinto costo fijo. Lo que
    se fija es la FORMA -- meter el techo como binario tiene que dejar el
    libre exactamente en la demanda. Si alguien vuelve a escribir la resta a
    mano en otro sitio, esta identidad se rompe."""
    for bpx in list(hb.FORMATOS.values()) + [0]:        # 0 = framebuffer fuera
        for doble in (False, True):
            for d3p in (False, True):
                for audio in (False, True):
                    techo = hb.techo_binario_b(bpx, doble, d3p=d3p, audio=audio)
                    if techo <= 0:
                        continue
                    libre = hb.libre_b(bpx, doble, peor=True, d3p=d3p,
                                       audio=audio, binario=techo)
                    assert libre == hb.demanda_hub_b(), (
                        f"el techo de ({bpx} B/px, doble={doble}, d3p={d3p}, "
                        f"audio={audio}) no sale de fijo_b(): con ese binario "
                        f"queda {libre:,} y la demanda es "
                        f"{hb.demanda_hub_b():,}. Hay dos cuentas de lo fijo "
                        f"otra vez, que es el fallo del 2026-09-09")


def test_los_costos_fijos_condicionales_mueven_de_verdad_a_fijo_b() -> None:
    """Mover cualquiera de los sumandos tiene que mover `fijo_b`.

    Es la mutacion del test de arriba por el otro lado: si un costo deja de
    contarse, `fijo_b` se queda quieto y esto lo ve."""
    base = hb.fijo_b(peor=True, d3p=False, audio=True)
    sin_npu = hb.fijo_b(peor=True, d3p=True, audio=True)
    sin_audio = hb.fijo_b(peor=True, d3p=False, audio=False)
    assert sin_npu < base, (
        "firmar D3-prima no baja lo fijo: la NPU y la camara no se estan "
        "cobrando")
    assert sin_audio < base, (
        "sacar el audio del hub no baja lo fijo: las colas no se estan "
        "cobrando")


# --- lo que no esta firmado no se da por firmado ----------------------------

def test_d3_prima_esta_firmada_y_el_hub_deja_de_pagar_la_camara() -> None:
    """FIRMADA por Samuel el 2026-09-09. La condicional de sec.3.1 se cumplio.

    Este test decia lo contrario hasta el 2026-09-09, y con razon: el papel
    llevaba desde el 2026-08-30 diciendo "Pendiente: D3-prima", y cobrarle al
    hub como si estuviera firmada le regalaba 1 400 000 B que nadie le habia
    quitado. Ya se los quitaron. Acta de Samuel: "un procesador solo para la
    IA", dentro de un diseno de cuatro N657, uno por trabajo, "para tener
    suficiente headroom y que el instrumento jamas se cuelgue".

    Lo que la firma cierra de paso: la contradiccion entre sec.10 fila 2 (que
    le cobraba NPU y cuadros de camara al hub) y sec.10 fila 11 (que se los
    daba al mago). Gana la fila 11."""
    assert hb.D3P_FIRMADA is True, (
        "D3-prima figura sin firmar: Samuel la firmo el 2026-09-09 y el "
        "papel del hub tiene que llevarlo en su linea de firma")
    assert hb.ACTA_CUATRO_CHIPS == "2026-09-09", (
        "la firma tiene que traer su fecha: una decision sin acta fechada "
        "es una premisa comoda esperando a que alguien la herede como hecho")
    con = hb.fijo_b(peor=True, d3p=False, audio=False)
    sin = hb.fijo_b(peor=True, d3p=True, audio=False)
    assert con - sin == hb.NPU_ACTIVACIONES_B[1] + hb.FRAMES_CAMARA_B[1]


def test_el_audio_tiene_chip_propio_y_el_hub_no_paga_sus_colas() -> None:
    """sec.6.2 daba a elegir entre hub y Voz. La respuesta no fue ninguna.

    Samuel firmo el 2026-09-09 una tercera via que el papel no ofrecia: un
    CUARTO N657 dedicado solo a la interfaz de audio. Asi que las colas de
    audio no son del hub -- pero ojo, esto NO es "sec.6.2 contestada segun lo
    previsto": es una enmienda que obliga a que el papel propio de la
    interfaz nazca describiendo un chip dedicado, y que ese chip estrene su
    propio censo de SRAM como lo tiene el mago (sec.10 fila 11)."""
    assert hb.AUDIO_EN_EL_HUB is False, (
        "el hub sigue cobrando las colas de audio: desde el 2026-09-09 la "
        "interfaz de audio tiene su propio N657")
    assert hb.CENSO_INTERFAZ_AUDIO_PENDIENTE is True, (
        "el cuarto chip no tiene censo de SRAM propio declarado como "
        "pendiente: sacarle un costo al hub sin darselo a nadie es como se "
        "pierden los bytes entre papeles")


# --- la demanda del hub: hueco declarado, no numero prestado ----------------

def test_el_hub_no_hereda_la_demanda_del_motor_de_audio() -> None:
    """1 256 000 B de tabla Serum y sample son de la Voz, no del hub.

    hub sec.3.1: "La SRAM del hub hereda el framebuffer, y SOLO el
    framebuffer... y ningun sampler". El censo viejo le exigia al hub sitio
    para una tabla clase Serum residente mas un buffer de sample de trabajo
    --la vara del motor de audio-- y con eso lo declaraba rojo."""
    assert hb.demanda_hub_b() != 1_256_000, (
        "el hub sigue pidiendo tabla Serum + buffer de sample: esa es la "
        "demanda de la Voz (hub sec.3.1)")


def test_la_demanda_propia_del_hub_esta_declarada_como_hueco() -> None:
    """Lo que el hub necesita residente NO esta enumerado en ningun papel.

    Y es el hallazgo que queda cuando el binario deja de ser el desconocido:
    ya no falta medir el firmware, falta ESCRIBIR que tiene que caber al
    lado --composicion de la UI, buffers del protocolo, DMA de las seis
    ranuras del J2--. Principio V: un hueco visible vale mas que un fallo
    invisible. Rellenarlo con un numero comodo seria justo el fallo."""
    assert hb.DEMANDA_HUB_ENUMERADA is False, (
        "la demanda del hub figura como enumerada: si es verdad, tiene que "
        "haber un papel que la enumere y este test tiene que citarlo")


def test_el_censo_sale_hueco_mientras_la_demanda_no_este_enumerada() -> None:
    """Exit 2, no 0. Verde aqui seria mentir por el lado nuevo.

    El binario ya no es el hueco; la demanda si. Un censo que se declara
    cerrado porque su costo mas gordo se midio, mientras su otro lado sigue
    sin escribirse, promete en vez de comprobar."""
    assert hb.main() == 2


# --- el canario: que el aserto que decide MUERDA ----------------------------

def test_la_guarda_del_hub_solo_muerde_por_encima_de_la_SRAM_FISICA() -> None:
    """Y eso NO es un aprobado: es la medida de cuanto le falta a esta puerta.

    Hasta el 2026-09-09 este test buscaba el borde dentro de [0, SRAM_B] y lo
    encontraba, porque el hub cargaba con 1 800 000 B de NPU, camara y colas
    de audio que no eran suyos. La firma de ese dia se los quito, y el binario
    esta medido en 82 280 B. Lo que queda es una guarda que compara un saldo
    de 4,1 MB contra una demanda de CERO: no puede saltar mientras el binario
    quepa fisicamente.

    No se arregla ensanchando el rango y callandose. Un aserto que solo puede
    fallar ante un imposible fisico no vigila un diseno, y este repo ya se
    quemo con guardas asi. Se deja escrito donde muerde HOY --por encima de
    los 4,2 MB del chip-- para que el dia que alguien enumere la demanda del
    hub, este test falle y obligue a rearmar el canario contra el numero de
    verdad.

    O sea: mientras DEMANDA_HUB_ENUMERADA sea False, esta linea es el
    recordatorio de que la puerta del hub no vigila nada."""
    assert hb.DEMANDA_HUB_ENUMERADA is False, (
        "la demanda del hub ya esta enumerada: este canario tiene que "
        "rearmarse contra ella y volver a buscar el borde DENTRO de la SRAM")
    p = hb.parametros()
    rojo = borde_rojo(hb.guarda_hub, p, "binario", 0, hb.SRAM_B * 2,
                      "no cabe en la SRAM del hub")
    assert rojo > hb.SRAM_B, (
        f"el borde salio en {rojo:,.0f} B, dentro de la SRAM: si la guarda "
        f"volvio a tener dientes es que alguien le puso un costo al hub -- "
        f"buena noticia, pero hay que decir cual y de donde salio")


def test_la_guarda_del_hub_muerde_por_el_framebuffer() -> None:
    """La otra punta: el framebuffer es el otro sumando que puede tumbarlo."""
    p = hb.parametros()
    rojo = borde_rojo(hb.guarda_hub, p, "framebuffer", 0, hb.SRAM_B,
                      "no cabe en la SRAM del hub")
    assert 0 < rojo < hb.SRAM_B


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
