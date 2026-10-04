"""Numerical/geometry tests only: no thermal or physical validation claims."""
import copy
import math
import unittest

from geometry import (build_case, clip_polygon, dot, hot_plan, hot_support,
                      load_inputs, roof_at, section_polygon, unit, width_at)
from render_scene import png_bytes, rasterize_projected


class PackingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config, cls.v4, _, _ = load_inputs()
        cls.case = build_case(cls.config, cls.v4)

    def test_preserves_v4_disc_positions(self):
        spec = self.v4["program_constraints"]["rotating_discs"]
        self.assertEqual(spec["centres"], [[210, 205], [580, 205]])
        self.assertEqual(spec["diameter"], 320)

    def test_roof_reference(self):
        self.assertEqual(roof_at(self.v4, 395, 205), 280)
        self.assertEqual(roof_at(self.v4, 0, 205), 190)
        self.assertEqual(width_at(self.v4, 660), 510)

    def test_support_bounds_dense_samples(self):
        normals = [unit(v) for v in ((1, 0, 1), (-1, -.3, 1), (.2, .5, 1),
                                     (0, -1, 1), (.7, .2, 0), (0, 0, -1))]
        for n in normals:
            support = hot_support(self.v4, n)
            for yi in range(75):
                y = -80 + 740 * yi / 74
                a = width_at(self.v4, y) / 2
                for xi in range(81):
                    x = 395 + a * (-1 + 2 * xi / 80)
                    for z in (0, roof_at(self.v4, x, y)):
                        self.assertLessEqual(dot(n, (x, y, z)), support + 1e-7)

    def test_every_cover_plane_has_normal_reserve(self):
        for p in self.case["planes"]:
            self.assertAlmostEqual(dot(p.normal, p.normal), 1)
            if p.kind != "bottom":
                self.assertAlmostEqual(p.offset - hot_support(self.v4, p.normal), 87.5)

    def test_polyhedron_vertices_inside_all_planes(self):
        for vertex in self.case["vertices"]:
            for plane in self.case["planes"]:
                self.assertGreaterEqual(plane.gap(vertex), -1e-6)

    def test_dimensions_include_mounting_reserve(self):
        summary = self.case["summary"]
        self.assertAlmostEqual(summary["width_mm"], 965)
        self.assertAlmostEqual(summary["depth_mm"], 915)
        self.assertGreater(summary["body_height_with_feet_mm"], 600)

    def test_insulation_variants_are_monotonic(self):
        cases = [build_case(self.config, self.v4, i) for i in (50, 75, 100)]
        for key in ("width_mm", "depth_mm", "body_height_with_feet_mm"):
            values = [case["summary"][key] for case in cases]
            self.assertTrue(values[0] < values[1] < values[2])

    def test_thin_mechanism_case_is_flagged_not_silently_shrunk(self):
        self.assertFalse(build_case(self.config, self.v4, mechanism_height=80)["summary"]["drive_reservations_fit"])
        self.assertTrue(self.case["summary"]["drive_reservations_fit"])
        self.assertTrue(build_case(self.config, self.v4, mechanism_height=160)["summary"]["drive_reservations_fit"])

    def test_no_front_face_closes_the_mouth(self):
        y = self.case["bounds"][1][0]
        for face in self.case["mesh"]:
            if face["name"] != "side_0":
                continue
            pts = face["points"]
            self.assertTrue(all(abs(p[1] - y) < 1e-5 for p in pts))
            minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
            minz, maxz = min(p[2] for p in pts), max(p[2] for p in pts)
            self.assertFalse(minx < 395 < maxx and minz < 80 < maxz)

    def test_sections_have_real_extents(self):
        transverse = section_polygon(self.case, 1, 205)
        longitudinal = section_polygon(self.case, 0, 210)
        self.assertGreaterEqual(len(transverse), 5)
        self.assertGreaterEqual(len(longitudinal), 5)
        self.assertAlmostEqual(max(x for x, _ in transverse) - min(x for x, _ in transverse), 965)
        self.assertAlmostEqual(max(y for y, _ in longitudinal) - min(y for y, _ in longitudinal), 915)

    def test_full_flue_height_not_render_stub(self):
        h = self.config["packaging_hypotheses"]
        points = [p for f in self.case["mesh"] if f["group"] == "flue" for p in f["points"]]
        self.assertAlmostEqual(max(p[2] for p in points) - min(p[2] for p in points), 1000)
        self.assertAlmostEqual(self.case["summary"]["height_with_flue_1500_mm"] - self.case["summary"]["height_with_flue_1000_mm"], 500)
        self.assertEqual(h["flue_height_above_collar_mm"], 1000)

    def test_clipping_is_geometric(self):
        points = [(0, 0, 0), (10, 0, 0), (10, 0, 10), (0, 0, 10)]
        result = clip_polygon(points, 2, 4, True)
        self.assertEqual(len(result), 4)
        self.assertTrue(all(p[2] >= 4 for p in result))

    def test_stone_mass_is_not_total_oven_mass(self):
        s = self.case["summary"]
        self.assertAlmostEqual(s["one_disc_mass_kg"], 4.18208814, places=6)
        self.assertAlmostEqual(s["stone_mass_only_kg"], 29.41292107, places=6)
        self.assertNotIn("total_oven_mass_kg", s)

    def test_stone_thickness_changes_disc_mass(self):
        config = copy.deepcopy(self.config)
        config["packaging_hypotheses"]["cooking_stone_mm"] = 10
        thinner = build_case(config, self.v4)
        self.assertAlmostEqual(thinner["summary"]["one_disc_mass_kg"] * 2, self.case["summary"]["one_disc_mass_kg"])

    def test_collector_reservation_inside_chamber(self):
        reserve = self.config["packaging_hypotheses"]["collector_reservation"]
        for x in reserve["x_range_mm"]:
            for y in reserve["y_range_mm"]:
                self.assertLess(reserve["z_range_mm"][1], roof_at(self.v4, x, y))
        self.assertGreater(reserve["z_range_mm"][0], self.v4["current_layout_candidate"]["door_clear_opening"]["height"])

    def test_no_production_approval(self):
        self.assertFalse(self.case["summary"]["is_production_approved"])
        self.assertEqual(self.config["status"], "studio_ingombri_non_esecutivo")

    def test_renderer_occlusion_is_order_independent(self):
        back = {"points": [(1, 1, 10), (9, 1, 10), (1, 9, 10)], "rgb": (255, 0, 0)}
        front = {"points": [(1, 1, 0), (9, 1, 0), (1, 9, 0)], "rgb": (0, 0, 255)}
        first = rasterize_projected([back, front], 12, 12, draw_edges=False)
        second = rasterize_projected([front, back], 12, 12, draw_edges=False)
        self.assertEqual(first, second)
        index = (2 * 12 + 2) * 4
        self.assertEqual(first[index:index + 4], bytes((0, 0, 255, 255)))

    def test_renderer_png_is_real_png(self):
        image = png_bytes(bytearray(4 * 3 * 2), 3, 2)
        self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertIn(b"IHDR", image)
        self.assertTrue(image.endswith(b"IEND\xaeB`\x82"))


if __name__ == "__main__":
    unittest.main()
