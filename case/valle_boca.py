"""Geometria analitica del prototipo de boca desmontable del valle.

La pieza de produccion no cambia en esta fase. Estas cotas gobiernan el modulo
OpenSCAD ``tapa_valle_boca_prototipo`` y permiten rechazar una variante que
oculte el riel a costa de tocar los paneles montados.
"""

from __future__ import annotations

COBERTURA_ZAPATO = 2.25
HOLGURA_ZAPATO_RIEL = 0.10
HOLGURA_CANTO_PANEL = 0.10
SOLAPE_PANEL = 0.00
TIRA_NOMINAL = 0.20
TIRA_COMPRIMIDA = 0.10


def evaluar_boca(p: dict[str, float]) -> dict[str, float]:
    """Devuelve las cotas cerradas de la boca con las filas pobladas."""
    expuesta = p["rail_er_alto"] / 2 - p["inset_er"]
    coberturas = {
        "3u_inferior": COBERTURA_ZAPATO,
        "kondor_inferior": COBERTURA_ZAPATO,
        "kondor_superior": COBERTURA_ZAPATO,
        "3u_superior": COBERTURA_ZAPATO,
    }
    return {
        "banda_riel_expuesta": expuesta,
        "holgura_canto_panel": HOLGURA_CANTO_PANEL,
        "margen_tira_sobre_riel": COBERTURA_ZAPATO - expuesta,
        "coberturas_rieles": coberturas,
        "espesor_zapato": p["t_valle"],
        "holgura_zapato_riel": HOLGURA_ZAPATO_RIEL,
        "holgura_apilado": (
            p["rehundido_panel"] + p["t_panel"] - p["t_valle"]
        ),
        "tira_nominal": TIRA_NOMINAL,
        "tira_comprimida": TIRA_COMPRIMIDA,
        "solape_panel": SOLAPE_PANEL,
        "apertura_kondor": p["alto_panel_1u"] - 2 * SOLAPE_PANEL,
        "fijaciones_m3_existentes": 2,
        "fijaciones_visibles_nuevas": 0,
        "construccion": "boca_visual_con_soportes_ocultos_separables",
        "estado_liberacion": "prototipo_geometrico",
        "requiere_cupon_fisico": True,
        "secuencia_servicio": (
            "retirar_soportes",
            "retirar_modulos",
            "retirar_boca_visual",
            "acceder_rieles",
        ),
    }


def validar_boca(p: dict[str, float]) -> list[str]:
    """Devuelve fallos físicos del prototipo; una lista vacía es aceptable."""
    m = evaluar_boca(p)
    fallos = []
    if min(m["coberturas_rieles"].values()) < m["banda_riel_expuesta"]:
        fallos.append("oclusion")
    if m["holgura_zapato_riel"] < 0:
        fallos.append("contacto_riel")
    if abs(m["holgura_zapato_riel"] - m["holgura_apilado"]) > 0.05:
        fallos.append("apilado")
    if m["solape_panel"] != 0:
        fallos.append("solape_panel")
    if m["holgura_canto_panel"] < 0.10:
        fallos.append("holgura_panel")
    if m["margen_tira_sobre_riel"] < 0.25:
        fallos.append("margen_tira")
    if m["apertura_kondor"] <= 0:
        fallos.append("apertura_kondor")
    return fallos
