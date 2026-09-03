"""La mutacion de una guarda, buscada por biseccion en vez de escrita a mano.

Vivia en case/clearance_budget.py, privada, desde el 2026-08-30. Sale aqui
porque la fuente v4 estrena nueve presupuestos y cada uno necesita ver morder
sus asertos: nueve copias de esta funcion son nueve sitios donde el numero
frontera se queda viejo, que es EXACTAMENTE el fallo del que nacio.

    python hardware/tools/test_canario.py      (su contrato)
"""
from __future__ import annotations

import contextlib
import io


def borde_rojo(guarda, p: dict[str, float], clave: str, lo: float, hi: float,
               texto: str, pasos: int = 24) -> float:
    """El valor de `clave` con el que `guarda` salta POR `texto`, buscado.

    NACE DE UNA CLASE ENTERA DE FALLOS (2026-08-30). Los canarios de
    clearance_budget llevaban su mutacion escrita a mano, y en un solo dia
    CUATRO dejaron de morder porque la geometria se movio debajo: t_piel, el
    radio del doblez de la pestana, la compresion del taco y el labio del
    techo. Cada vez se corregia el numero y a la siguiente tanda pasaba otra
    vez.

    El problema no era el numero: era atarlo. Un canario dice "este aserto
    muerde, y por SU texto"; para eso no hace falta saber DONDE muerde, solo
    que hay un sitio. Asi que se busca por biseccion entre lo y hi, y si no lo
    encuentra el canario falla -- que es exactamente lo que tiene que pasar si
    un aserto se quedo sin dientes.

    Devuelve el valor rojo; levanta AssertionError si en todo el rango no hay
    ninguno que salte por ese texto."""
    def salta(v: float) -> bool:
        roto = dict(p)
        roto[clave] = v
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                guarda(roto)
        except AssertionError as e:
            return texto in str(e)
        except Exception:                       # noqa: BLE001
            return False
        return False

    if salta(hi):
        a, b = lo, hi
    elif salta(lo):
        a, b = hi, lo
    else:
        raise AssertionError(
            f"canario: en {clave} entre {lo:g} y {hi:g} no hay ningun valor que "
            f"haga saltar a {guarda.__name__}() por '{texto}'. O el aserto se "
            f"quedo sin dientes, o su texto cambio y nadie actualizo el canario")
    for _ in range(pasos):                      # b salta, a no
        m = (a + b) / 2
        if salta(m):
            b = m
        else:
            a = m
    # b es el lado ROJO, y a un pelo del borde. Se devuelve un 5 % MAS ADENTRO
    # del rojo, no el borde: si no, el redondeo a tres decimales lo puede
    # devolver al verde y el canario denunciaria un aserto sano. El +/-0.001
    # evita que el redondeo a 3 decimales caiga justo sobre la raya.
    # Un canario tiene que caer dentro, no encima del borde.
    v = round(b + (b - a) * 0.05 + (0.001 if b > a else -0.001), 3)
    assert salta(v), (
        f"canario: el borde de {clave} para '{texto}' salio en {v:g} y ahi no "
        f"salta. La biseccion encontro el sitio pero el valor devuelto se cayo "
        f"al lado verde")
    return v
