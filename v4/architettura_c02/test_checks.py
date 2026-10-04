"""Unit tests establish numerical consistency, not real-oven performance."""
from dataclasses import replace
import math
import unittest

from checks import (DraftCase, body_budget, door_integrals, draft_parameters, evaluate,
                    flue_geometry, growth_mm, load, mechanical, pressure_budget,
                    scenarios, shaft_heat_W, solve_draft)


class ScreeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.v4, cls.c01 = load()
        cls.base = draft_parameters(cls.cfg, cls.v4)

    def test_expansion_uses_mean_coefficient_and_temperature_difference(self):
        self.assertAlmostEqual(growth_mm(790, 18.8e-6, 600, 20), 8.61416)
        self.assertEqual(growth_mm(320, 3e-6, 20, 20), 0)

    def test_shaft_heat_scales_with_cross_section(self):
        solid = shaft_heat_W(12, 0, 80, 20, 300)
        hollow = shaft_heat_W(12, 8, 80, 20, 300)
        self.assertAlmostEqual(hollow / solid, (12 ** 2 - 8 ** 2) / 12 ** 2)
        with self.assertRaises(ValueError):
            shaft_heat_W(12, 14, 80, 20, 300)

    def test_mechanisms_preserve_two_original_centres(self):
        m = mechanical(self.cfg, self.v4, self.c01)
        self.assertTrue(all(v["inside_nominal_floor_projection"] for v in m["modules"]))
        self.assertEqual(m["module_separation_mm"], 130)
        self.assertEqual(self.v4["program_constraints"]["rotating_discs"]["centres"], [[210, 205], [580, 205]])

    def test_parallel_stack_not_serial_sum(self):
        m = mechanical(self.cfg, self.v4, self.c01)
        self.assertEqual(m["parallel_required_height_mm"], 117)
        self.assertEqual(m["coaxial_required_height_mm"], 157)
        self.assertEqual(m["bay_comparison"][0]["parallel_remaining_mm"], 3)
        self.assertEqual(m["bay_comparison"][1]["parallel_remaining_mm"], 43)

    def test_height_reserves_are_separate_from_C01(self):
        self.assertEqual(mechanical(self.cfg, self.v4, self.c01)["increment_body_height_from_c01_mm"], 53.5)
        self.assertEqual(self.c01["packaging_hypotheses"]["mechanism_clear_height_mm"], 120)

    def test_body_budget_is_actual_C01_geometry_without_mutating_source(self):
        before = repr(self.c01)
        b = body_budget(self.cfg, self.v4, self.c01)
        self.assertAlmostEqual(b["C02_body_only"]["body_height_with_feet_mm"] - b["C01"]["body_height_with_feet_mm"], 53.5)
        self.assertAlmostEqual(b["collar_base_plan_overhang_from_C01_front_mm"], 7.5)
        self.assertEqual(b["C02_body_only"]["width_mm"], 965)
        self.assertEqual(before, repr(self.c01))

    def test_corner_of_rectangular_plate_does_not_fit_small_octagon(self):
        p = flue_geometry(self.cfg, self.v4, self.c01)["collar_plate_budget"]
        self.assertFalse(p["fits_old_proposed_340_octagon"])
        self.assertTrue(p["fits_proposed_base_budget"])
        self.assertAlmostEqual(p["min_regular_octagon_outer_across_flats_mm"], 588 / math.sqrt(2))

    def test_tool_load_also_produces_overturning_moment(self):
        self.assertAlmostEqual(mechanical(self.cfg, self.v4, self.c01)["tool_at_stone_edge_overturning_moment_Nm"], 6.4)

    def test_nonfinite_shaft_and_budget_fail(self):
        with self.assertRaises(ValueError):
            shaft_heat_W(12, 0, 80, 20, math.nan)
        with self.assertRaises(ValueError):
            pressure_budget(self.base, math.nan)

    def test_flue_area_no_rectangular_area_confusion(self):
        f = flue_geometry(self.cfg, self.v4, self.c01)
        self.assertAlmostEqual(f["throat_comparison"][0]["area_cm2"], math.pi * 130 ** 2 / 400)
        self.assertTrue(f["throat_comparison"][0]["proposed_neck_area_ge_pipe"])
        self.assertFalse(f["throat_comparison"][1]["proposed_neck_area_ge_pipe"])
        self.assertTrue(f["neck_height_exceeds_C01_box"])
        self.assertTrue(f["entry_outer_fits_C01_box_width_height"])

    def test_insulated_chimney_does_not_fit_original_collar(self):
        f = flue_geometry(self.cfg, self.v4, self.c01)
        self.assertTrue(all(not c["fits_C01_top_nominally"] for c in f["collar_comparison"]))
        # The 260 mm reservation fits illustrative D130/I50, NOT D150/I50.
        self.assertTrue(f["collar_comparison"][1]["fits_C02_reservation_with_mounting"])
        self.assertFalse(f["collar_comparison"][3]["fits_C02_reservation_with_mounting"])

    def test_old_MATLAB_network_numbers_reproduced(self):
        r = solve_draft(self.base)
        self.assertAlmostEqual(r["lambda_rear"], 1.87, delta=.015)
        self.assertAlmostEqual(pressure_budget(self.base)["margin_Pa"], -.97, delta=.05)
        opened = solve_draft(replace(self.base, door_open=True))
        self.assertAlmostEqual(opened["door_out_gas_kg_h"], 60.8, delta=.3)
        self.assertAlmostEqual(opened["neutral_height_mm"], 83, delta=1)

    def test_mass_balance_in_every_scenario(self):
        for case in scenarios(self.cfg, self.v4):
            self.assertLess(abs(case["mass_residual_kg_s"]), 1e-10, case["id"])

    def test_extra_inlet_losses_reduce_air_supply(self):
        low = solve_draft(replace(self.base, extra_inlet_K=0))["lambda_rear"]
        high = solve_draft(replace(self.base, extra_inlet_K=4))["lambda_rear"]
        self.assertGreater(low, high)

    def test_large_area_increases_supply_with_others_fixed(self):
        self.assertGreater(solve_draft(replace(self.base, inlet_area_cm2=120))["lambda_rear"], solve_draft(self.base)["lambda_rear"])

    def test_budget_only_for_closed_door(self):
        with self.assertRaises(ValueError):
            pressure_budget(replace(self.base, door_open=True))

    def test_pressure_margin_changes_by_applied_wind(self):
        normal = pressure_budget(self.base)["margin_Pa"]
        adverse = pressure_budget(replace(self.base, wind_adverse_Pa=3))["margin_Pa"]
        self.assertAlmostEqual(normal - adverse, 3)

    def test_no_division_by_zero_with_cold_chamber(self):
        r = solve_draft(replace(self.base, chamber_C=25, flue_C=25, door_open=True, fuel_kg_h=0))
        self.assertIsNone(r["neutral_height_mm"])
        self.assertIsNone(r["lambda_rear"])
        self.assertAlmostEqual(r["mass_residual_kg_s"], 0)

    def test_door_exact_integral(self):
        incoming, outgoing = door_integrals(-1, 0, .16)
        self.assertEqual(incoming, .16)
        self.assertEqual(outgoing, 0)
        i, o = door_integrals(-1, 10, .2)
        self.assertAlmostEqual(i, o)

    def test_invalid_and_nonfinite_parameters_fail(self):
        for values in ({"inlet_area_cm2": -1}, {"extra_inlet_K": -1}, {"moisture_wet_fraction": 1}, {"flue_C": -300}, {"wind_adverse_Pa": math.nan}):
            with self.assertRaises(ValueError):
                solve_draft(replace(self.base, **values))

    def test_no_approval_and_no_implicit_full_simulation(self):
        result = evaluate(self.cfg, self.v4, self.c01)
        self.assertFalse(result["production_approved"])
        self.assertFalse(result["full_CFD_executed"])
        self.assertFalse(result["physical_tests_executed"])


if __name__ == "__main__":
    unittest.main()
