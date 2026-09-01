"""Contrato del prototipo de boca desmontable del valle."""

import unittest
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from unittest.mock import patch

from case.clearance_budget import leer_params
from case.valle_boca import evaluar_boca, validar_boca


class ValleBocaContract(unittest.TestCase):
    def test_mouth_occludes_populated_rail_bands_without_touching_panels(self):
        p = leer_params()
        m = evaluar_boca(p)

        self.assertEqual(p["rehundido_panel"], 1.50)
        self.assertEqual(p["alto_panel_inf"], 128.5)
        self.assertEqual(p["alto_panel_sup"], 128.5)
        self.assertEqual(p["alto_panel_1u"], 55.0)
        self.assertAlmostEqual(m["banda_riel_expuesta"], 2.0, places=6)
        self.assertAlmostEqual(m["holgura_canto_panel"], 0.10, places=6)
        self.assertGreaterEqual(m["margen_tira_sobre_riel"], 0.25)
        self.assertEqual(m["solape_panel"], 0.0)
        self.assertAlmostEqual(m["apertura_kondor"], 55.0, places=6)
        self.assertAlmostEqual(m["espesor_zapato"], 3.0, places=6)
        self.assertAlmostEqual(m["holgura_zapato_riel"], 0.10, places=6)
        self.assertAlmostEqual(m["tira_nominal"], 0.20, places=6)
        self.assertAlmostEqual(m["tira_comprimida"], 0.10, places=6)

    def test_all_four_valley_boundaries_have_positive_real_coverage(self):
        m = evaluar_boca(leer_params())

        self.assertEqual(
            set(m["coberturas_rieles"]),
            {"3u_inferior", "kondor_inferior", "kondor_superior", "3u_superior"},
        )
        for cobertura in m["coberturas_rieles"].values():
            self.assertGreaterEqual(cobertura, m["banda_riel_expuesta"])

    def test_mouth_uses_existing_tabs_and_separable_supports(self):
        m = evaluar_boca(leer_params())

        self.assertEqual(m["fijaciones_m3_existentes"], 2)
        self.assertEqual(m["fijaciones_visibles_nuevas"], 0)
        self.assertEqual(
            m["construccion"],
            "boca_visual_con_soportes_ocultos_separables",
        )
        self.assertEqual(m["estado_liberacion"], "prototipo_geometrico")
        self.assertTrue(m["requiere_cupon_fisico"])
        self.assertEqual(
            m["secuencia_servicio"],
            ("retirar_soportes", "retirar_modulos",
             "retirar_boca_visual", "acceder_rieles"),
        )
        cad = Path(__file__).parent / "cad" / "sam17_case.scad"
        source = cad.read_text(encoding="utf-8")
        prototype = source[source.index("module tapa_valle_boca_prototipo()") :]
        prototype = prototype[: prototype.index("module tira_anti_ruido_valle()")]
        self.assertIn("pv_x()", source)
        self.assertIn("pv_a()", source)
        self.assertIn("cylinder(d = d_M3_paso", source)
        self.assertIn("module puente_lateral_boca_prototipo", source)
        self.assertIn("module boca_visual_valle_prototipo()", source)
        self.assertIn("module soportes_boca_valle_prototipo()", source)
        self.assertIn("module alojamiento_extraccion_soportes_prototipo(", source)
        self.assertIn("module barrido_extraccion_soportes_prototipo(", source)
        self.assertIn("alojamiento_extraccion_soportes_prototipo();", source)
        self.assertIn("x_lower3u_max", source)
        self.assertIn("x_upper3u_min", source)
        self.assertIn("y_cross_min = P[3].y - rehundido_panel + hol_riel/2", source)
        self.assertIn("y_cross_max = P[3].y", source)
        self.assertIn("r_boss = 1.5*d_M3_paso", source)
        self.assertNotIn("y_inferior = y_superior - t_valle", source)
        self.assertIn("for (z = [z0, z0 + au - t_valle])", source)
        self.assertNotIn("for (z = [z0 - t_valle, z0 + au])", source)
        self.assertIn("module cabezas_m3_boca_prototipo(", source)
        self.assertIn("module herramientas_m3_boca_prototipo(d_herramienta = 5.7)", source)
        self.assertIn("recorrido = au/2", source)
        self.assertIn("module barrido_extraccion_boca_prototipo(", source)
        self.assertIn("module barrido_extraccion_paneles_prototipo(", source)
        self.assertIn("minkowski()", source)
        self.assertIn("u = [-sqrt(0.5), sqrt(0.5), 0]", source)
        self.assertIn("(rail_er_fondo - rail_er_eje)*cos(angulo_inferior)", source)
        self.assertIn("rail_er_eje*cos(angulo_superior)", source)

    def test_mutation_canaries_reject_lost_occlusion_and_panel_contact(self):
        p = leer_params()
        self.assertEqual(validar_boca(p), [])
        with patch("case.valle_boca.COBERTURA_ZAPATO", 1.5):
            self.assertIn("oclusion", validar_boca(p))
        with patch("case.valle_boca.HOLGURA_ZAPATO_RIEL", -0.10):
            self.assertIn("contacto_riel", validar_boca(p))
        with patch("case.valle_boca.SOLAPE_PANEL", 0.25):
            self.assertIn("solape_panel", validar_boca(p))
        with patch("case.valle_boca.HOLGURA_CANTO_PANEL", 0.0):
            self.assertIn("holgura_panel", validar_boca(p))
        with patch("case.valle_boca.COBERTURA_ZAPATO", 2.10):
            self.assertIn("margen_tira", validar_boca(p))

    def test_openscad_exposes_an_isolated_prototype_not_production_dxf(self):
        cad = Path(__file__).parent / "cad" / "sam17_case.scad"
        source = cad.read_text(encoding="utf-8")

        self.assertIn("module tapa_valle_boca_prototipo()", source)
        self.assertIn("module assembly_valle_boca_prototipo()", source)
        self.assertIn("module rails_reales_prototipo()", source)
        self.assertIn("module tiras_boca_valle_prototipo()", source)
        self.assertIn("n_inf*t_valle", source)
        self.assertIn("n_sup*t_valle", source)

        self.assertIn(
            'else if (PART == "assembly_valle_boca_prototipo")', source
        )
        production = source[source.index("module tapa_valle_2d()") :]
        production = production[: production.index("module onda(")]
        self.assertNotIn("boca_valle", production)

    def test_named_blend_builder_has_an_explicit_prototype_mode(self):
        script = Path(__file__).parent / "renders" / "piezas.py"
        source = script.read_text(encoding="utf-8")

        self.assertIn("SAM17_VALLE_BOCA_PROTOTIPO", source)
        self.assertIn("valle_boca_source_hashes", source)
        self.assertIn("sam17-piezas-valle-boca.blend", source)
        self.assertIn('"tapa_valle_boca_prototipo"', source)
        self.assertIn('"zrail_clear"', source)
        self.assertIn('"rieles_3u_reales_prototipo"', source)
        self.assertIn('"rieles_1u_reales_prototipo"', source)
        self.assertIn('"tiras_boca_valle_prototipo"', source)
        self.assertIn('"cabezas_m3_boca_prototipo"', source)
        self.assertIn('"herramientas_m3_boca_prototipo"', source)
        self.assertIn('"barrido_extraccion_boca_prototipo"', source)
        self.assertIn('"barrido_extraccion_paneles_prototipo"', source)
        self.assertIn('"boca_visual_valle_prototipo"', source)
        self.assertIn('"soportes_boca_valle_prototipo"', source)
        self.assertIn('"barrido_extraccion_soportes_prototipo"', source)
        self.assertIn("nombre not in ALWAYS_REBUILD", source)

        piezas = Path(__file__).parent / "cad" / "piezas.scad"
        piezas_source = piezas.read_text(encoding="utf-8")
        self.assertIn("module rieles_1u_reales_prototipo()", piezas_source)
        self.assertIn(
            "translate([rail_er_fondo/2 - rail_er_eje, 0, 0])",
            piezas_source,
        )


    def test_blend_collision_gate_is_reviewable(self):
        verifier = Path(__file__).parent / "renders" / "verify_valle_boca.py"
        self.assertTrue(verifier.exists())
        source = verifier.read_text(encoding="utf-8")
        self.assertIn("BOCA_COLLISION_GATE PASS", source)
        self.assertNotIn("MAX_NUMERICAL_VOLUME_MM3", source)
        self.assertIn("MAX_INTERSECTION_VOLUME_MM3 = 0.000001", source)
        self.assertIn("MIN_PANEL_CLEARANCE_MM = 0.09", source)
        self.assertIn("surface_clearance(MOUTH, PANELS)", source)
        self.assertIn("STRIP_COVERAGE_MM = 2.25", source)
        self.assertIn("MAX_CONTACT_RESIDUAL_VOLUME_MM3", source)
        self.assertIn("component_xy_diameters", source)
        self.assertIn("component_xy_thicknesses", source)
        self.assertIn("component_support_distances", source)
        self.assertIn("polygon.center", source)
        self.assertIn("apoyos 1U/3U", source)
        self.assertIn("MOUTH_RAIL_CLEARANCE_MM", source)
        self.assertIn("tiras_boca_valle_prototipo", source)
        self.assertIn("(MOUTH, FRAMES)", source)
        self.assertIn("(MOUTH, RINGS)", source)
        self.assertIn("(MOUTH, STRIPS)", source)
        self.assertIn("(TOOLS, MOUTH)", source)
        self.assertIn("(TOOLS, PANELS)", source)
        self.assertIn("(TOOLS, RAILS_1U)", source)
        self.assertIn("(TOOLS, RAILS_3U)", source)
        self.assertIn("(TOOLS, FRAMES)", source)
        self.assertIn("(TOOLS, RINGS)", source)
        self.assertIn("(EXTRACTION, RINGS)", source)
        self.assertNotIn("(EXTRACTION, PANELS)", source)
        self.assertIn("(EXTRACTION, RAILS_1U)", source)
        self.assertIn("(EXTRACTION, RAILS_3U)", source)
        self.assertIn("(EXTRACTION, FRAMES)", source)
        self.assertNotIn("(PANELS_EXTRACTION, MOUTH)", source)
        self.assertIn("connected_components(bpy.data.objects[MOUTH]) != 4", source)
        self.assertIn("connected_components(bpy.data.objects[VISIBLE]) != 2", source)
        self.assertIn("connected_components(bpy.data.objects[SUPPORTS]) != 2", source)
        self.assertIn("(SUPPORTS_EXTRACTION, VISIBLE)", source)
        self.assertIn("(PANELS_EXTRACTION, VISIBLE)", source)
        self.assertIn("(TOOLS, MOUTH)", source)
        self.assertIn("sys.exit(1)", source)
        self.assertIn("atexit.register", source)
        self.assertIn("blend obsoleto", source)

    def test_prototype_exports_as_four_serviceable_components(self):
        openscad = shutil.which("openscad")
        windows = Path(r"C:\Program Files\OpenSCAD\openscad.exe")
        if not openscad and windows.exists():
            openscad = str(windows)
        if not openscad:
            self.skipTest("OpenSCAD no disponible")
        cad = Path(__file__).parent / "cad" / "piezas.scad"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "boca.stl"
            subprocess.run(
                [
                    openscad,
                    "-o",
                    str(out),
                    "-D",
                    'PIEZA="tapa_valle_boca_prototipo"',
                    str(cad),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            data = out.read_text(encoding="ascii")
        parent: dict[tuple[float, float, float], tuple[float, float, float]] = {}

        def find(v):
            parent.setdefault(v, v)
            if parent[v] != v:
                parent[v] = find(parent[v])
            return parent[v]

        def union(a, b):
            parent[find(a)] = find(b)

        vertices = [
            tuple(round(float(x), 4) for x in match)
            for match in re.findall(
                r"vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)",
                data,
            )
        ]
        for i in range(0, len(vertices), 3):
            triangle = vertices[i : i + 3]
            self.assertEqual(len(triangle), 3)
            union(triangle[0], triangle[1])
            union(triangle[1], triangle[2])
        self.assertEqual(len({find(v) for v in parent}), 4)


if __name__ == "__main__":
    unittest.main()
