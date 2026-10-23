"""El suelo del case sin tabla: las cifras del aire del papel
docs/superpowers/specs/2026-10-12-case-suelo-design.md (sec.5).

Las calcula clearance_budget._tiro(), que desde el papel del suelo resuelve la
chimenea con la base como camino en serie. Este guion solo las imprime.

La primera fila es la base tapada (sobre un pano o una alfombrilla): la misma
cuenta que el aviso «sobre un pano» de clearance_budget.guarda_aire(),
_tiro(base=False), que en la tabla del papel se llamaba «hoy, con la tabla».
Queda fuera de las condiciones de uso (PLIEGO sec.7: mesa dura, con las patas
libres debajo).

El techo es salto_termico_max de params.scad: salto del aire del case sobre la
sala, tomado de la DELTA_T de hardware/02-midi-cv/tuning_budget.py. Lo juzga
guarda_aire() con el C_D nominal; aqui solo se marca con x lo que lo pasa.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import clearance_budget as cb  # noqa: E402

if __name__ == "__main__":
    p = cb.leer_params()
    f_sala = cb.T_SALA_DISENO_K / cb.T_AMB
    t = cb._tiro(p)
    techo = p["salto_termico_max"]
    print(f"base: {len(cb._campo_base(p))} agujeros, {t['a_base']:.0f} mm2; "
          f"{p['potencia_disipada']} W; techo {techo:g} K de salto sobre la sala "
          f"(params.scad, DELTA_T de tuning_budget.py), x = lo pasa")
    print("caso | salto pesim | 1 costado (pesim) | sala 45 (pesim)")

    def k(v: float, ancho: int) -> str:
        return f"{v:{ancho}.2f}{'x' if v > techo else ' '}"

    filas = [("sobre un pano (base tapada)", p, {"base": False})]
    for alto in (10.0, 20.0):
        for canal in (cb.CANAL_BASE, cb.CANAL_BASE_PESIMISTA):
            filas.append((f"patas de {alto:g}, canal de {canal:g}",
                          {**p, "alto_pie": alto}, {"canal": canal}))
    for nombre, q, kw in filas:
        n = cb._tiro(q, **kw)["dt"]
        pe = cb._tiro(q, cb.CD_TIRO_PESIMISTA, **kw)["dt"]
        c1 = cb._tiro(q, cb.CD_TIRO_PESIMISTA, costados=1, **kw)["dt"]
        print(f"{nombre:28s} | {k(n, 5)}{k(pe, 5)}| {k(c1, 16)} | {k(pe * f_sala, 14)}")
