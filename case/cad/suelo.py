"""El suelo del case sin tabla: las cifras del aire del papel
docs/superpowers/specs/2026-10-12-case-suelo-design.md (sec.5).

Las calcula clearance_budget._tiro(), que desde el papel del suelo resuelve la
chimenea con la base como camino en serie. Este guion solo las imprime.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import clearance_budget as cb  # noqa: E402

if __name__ == "__main__":
    p = cb.leer_params()
    f_sala = cb.T_SALA_DISENO_K / cb.T_AMB
    t = cb._tiro(p)
    print(f"base: {len(cb._campo_base(p))} agujeros, {t['a_base']:.0f} mm2; "
          f"{p['potencia_disipada']} W, techo {p['salto_termico_max']:g} K")
    print("caso | salto pesim | 1 costado (pesim) | sala 45 (pesim)")
    filas = [("hoy, con la tabla", p, {"base": False})]
    for alto in (10.0, 20.0):
        for canal in (cb.CANAL_BASE, cb.CANAL_BASE_PESIMISTA):
            filas.append((f"patas de {alto:g}, canal de {canal:g}",
                          {**p, "alto_pie": alto}, {"canal": canal}))
    for nombre, q, kw in filas:
        n = cb._tiro(q, **kw)["dt"]
        pe = cb._tiro(q, cb.CD_TIRO_PESIMISTA, **kw)["dt"]
        c1 = cb._tiro(q, cb.CD_TIRO_PESIMISTA, costados=1, **kw)["dt"]
        print(f"{nombre:28s} | {n:5.2f} {pe:5.2f} | {c1:17.2f} | {pe * f_sala:15.2f}")
