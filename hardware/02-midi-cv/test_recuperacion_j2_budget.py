"""La puerta de `resistencia_j2.csv` (#369): el codigo de salida se calcula, no se fija.

    python -m pytest hardware/02-midi-cv/test_recuperacion_j2_budget.py
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recuperacion_j2_budget as r  # noqa: E402

CAB = ("ranura,instancia,tsize,nss,reloj_MHz,horas,giros,plazos_vencidos,eot_tardios,"
       "subidas_malas,fecha,placa")


def fila(horas, giros, vencidos=0, eot=0, malas=0):
    return {"horas": str(horas), "giros": str(giros), "plazos_vencidos": str(vencidos),
            "eot_tardios": str(eot), "subidas_malas": str(malas)}


# El instrumento: seis ranuras a 8 kHz, 172,8 millones de transferencias por hora.
INSTRUMENTO = dict(ranuras=6, f_lazo_hz=8000)
A_8K = 8000 * 3600   # giros por hora de una ranura al lazo del hub


def test_la_cota_de_poisson_es_la_de_la_tabla():
    assert r.cota_poisson(0) == pytest.approx(math.log(20), abs=1e-9)
    # Una cola, al 95 %: chi2(0,95; 2k+2) / 2.
    for k, cota in ((1, 4.744), (2, 6.296), (10, 16.962)):
        assert r.cota_poisson(k) == pytest.approx(cota, abs=1e-3)


def test_sin_horizonte_o_sin_filas_es_hueco():
    assert r.juicio_resistencia([fila(24, 24 * A_8K)], None, **INSTRUMENTO)[0] == 2
    assert r.juicio_resistencia([], 1.0, **INSTRUMENTO)[0] == 2


def test_setecientos_mil_cuelgues_en_24_h_es_rojo():
    # La fila del 17-10 mutada: es de 1 kHz, y un fallo visto a cualquier cadencia cuenta.
    assert r.juicio_resistencia([fila(24, 86_399_999, vencidos=700_000)], 1.0,
                                **INSTRUMENTO)[0] == 1


def test_una_fila_limpia_al_lazo_cubre_un_tercio_de_su_largo_entre_seis():
    # 24 h limpias en una ranura a 8 kHz: 24 / (6 x 2,996) = 1,34 h de instrumento.
    limpia = [fila(24, 24 * A_8K)]
    assert r.juicio_resistencia(limpia, 1.3, **INSTRUMENTO)[0] == 0
    assert r.juicio_resistencia(limpia, 1.4, **INSTRUMENTO)[0] == 2


def test_las_ranuras_del_soak_se_suman():
    seis = [fila(24, 24 * A_8K) for _ in range(6)]
    assert r.juicio_resistencia(seis, 8.0, **INSTRUMENTO)[0] == 0
    assert r.juicio_resistencia(seis, 8.1, **INSTRUMENTO)[0] == 2


def test_el_horizonte_firmado_pide_48_h_en_tres_ranuras():
    # Samuel, 2026-10-20: H = 8 h, y una Nucleo soakea tres ranuras con esclavo.
    assert r.juicio_resistencia([fila(48, 48 * A_8K)] * 3, r.HORIZONTE_H, **INSTRUMENTO)[0] == 0
    assert r.juicio_resistencia([fila(47, 47 * A_8K)] * 3, r.HORIZONTE_H, **INSTRUMENTO)[0] == 2


def test_una_fila_limpia_por_debajo_del_lazo_no_aprueba():
    # La del 17-10, a 1 kHz, aunque durara un ano: D5.1, enmienda del 16-10.
    assert r.juicio_resistencia([fila(24 * 365, 365 * 86_400_000)], 0.01,
                                **INSTRUMENTO)[0] == 2


def test_un_evento_pide_mas_soak_y_no_es_rojo():
    # 30 h a 8 kHz con un plazo vencido: cota 4,744 / 864e6 por giro, x 172,8e6 = 0,95 por hora.
    assert r.juicio_resistencia([fila(30, 30 * A_8K, vencidos=1)], 1.0, **INSTRUMENTO)[0] == 0
    assert r.juicio_resistencia([fila(24, 24 * A_8K, eot=1)], 1.0, **INSTRUMENTO)[0] == 2
    assert r.juicio_resistencia([fila(24, 24 * A_8K, malas=1)], 1.0, **INSTRUMENTO)[0] == 2


def _demo_con(monkeypatch, tmp_path, linea, horizonte, t_iwdg):
    csv = tmp_path / "resistencia_j2.csv"
    csv.write_text(CAB + "\n" + linea + "\n", encoding="utf-8")
    monkeypatch.setattr(r, "_CSV", str(csv))
    monkeypatch.setattr(r, "HORIZONTE_H", horizonte)
    monkeypatch.setattr(r, "T_IWDG_S", t_iwdg)
    monkeypatch.setattr(r, "ESTIMADOS", ())
    # Las filas de carga_j2 de los dos regimenes del hub, dentro del reparto y de la ficha H.
    hub = dict(transporte="tic", cache="icache+dcache-mpu", f_cpu_hz="800000000", ranuras="6",
               periodo_us="125", firmware="a", fecha="", placa="")
    carga = tmp_path / "carga_j2.csv"
    carga.write_text("\n".join(
        [",".join(list(hub) + ["regimen_cache", "ciclos_por_giro", "cuerpos_por_giro"])]
        + [",".join(list(hub.values()) + fin)
           for fin in (["caliente", "2000", "1900"], ["fria", "2100", "1920"])]) + "\n",
        encoding="utf-8")
    monkeypatch.setattr(r, "_CSV_CARGA", str(carga))
    return r.demo()


def test_demo_sale_con_1_con_la_fila_mutada(monkeypatch, tmp_path):
    with pytest.raises(AssertionError):
        _demo_con(monkeypatch, tmp_path, "0,SPI5,25,hw,8,24,86399999,700000,0,0,,x", 1.0, 0.1)


def test_demo_sale_con_0_o_2_segun_t_iwdg(monkeypatch, tmp_path):
    limpia = f"0,SPI5,25,hw,8,24,{24 * A_8K},0,0,0,,x"
    assert _demo_con(monkeypatch, tmp_path, limpia, 1.0, 0.1) == 0
    assert _demo_con(monkeypatch, tmp_path, limpia, 1.0, None) == 2
    assert _demo_con(monkeypatch, tmp_path, limpia, None, 0.1) == 2
