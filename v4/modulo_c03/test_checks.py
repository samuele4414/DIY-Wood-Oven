from copy import deepcopy
import math
import unittest

from checks import belt_centre, belt_load, evaluate, load, open_belt_length


class NumericalScreening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = load()
        cls.result = evaluate(*cls.inputs)

    def test_exact_belt_centre(self):
        d = self.result["drive"]
        self.assertAlmostEqual(d["centre_distance_mm"], 78.97134949670658, places=9)
        self.assertLess(abs(d["belt_length_residual_mm"]), 1e-10)

    def test_equal_pulley_limit(self):
        self.assertAlmostEqual(open_belt_length(100, 10, 10), 200 + 20 * math.pi)
        self.assertAlmostEqual(belt_centre(200 + 20 * math.pi, 10, 10), 100)

    def test_monotonic_length(self):
        self.assertLess(open_belt_length(70, 10, 20), open_belt_length(90, 10, 20))

    def test_invalid_belt_geometry(self):
        for values in ((0, 10, 20), (10, 10, 20), (100, 20, 10), (math.inf, 10, 20), (100, -1, 20)):
            with self.assertRaises(ValueError):
                open_belt_length(*values)

    def test_impossible_belt(self):
        with self.assertRaises(ValueError):
            belt_centre(20, 10, 20)

    def test_ratio_not_rounded_five(self):
        self.assertAlmostEqual(self.result["drive"]["total_motor_to_disc_ratio"], 114 / 11)

    def test_pulse_units(self):
        rows = self.result["drive"]["speed_rows"]
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertAlmostEqual(row["pulse_frequency_Hz"], row["bare_motor_rpm"] * 200 * row["microsteps_per_fullstep"] / 60)
        self.assertAlmostEqual(rows[0]["pulse_frequency_Hz"], 103.63636363636)

    def test_wrap(self):
        d = self.result["drive"]
        self.assertTrue(160 < d["small_wrap_deg"] < 162)
        self.assertAlmostEqual(d["small_teeth_in_contact_geometric"], 16 * d["small_wrap_deg"] / 360)

    def test_moment_and_axial_scenario(self):
        m = self.result["mechanics"]
        self.assertAlmostEqual(m["tool_moment_Nm"], 6.4)
        self.assertAlmostEqual(m["axial_scenario_N"], 110.45628465790017)
        self.assertTrue(m["direct_axial_support_incompatible"])

    def test_startup_torque_inherited_not_measured(self):
        m, d = self.result["mechanics"], self.result["drive"]
        self.assertAlmostEqual(m["startup_torque_assumed_Nm"], 1.3455799214408262)
        self.assertAlmostEqual(d["required_geared_motor_torque_screening_Nm"], m["startup_torque_assumed_Nm"] / 1.8)
        self.assertFalse(d["running_torque_available_validated"])

    def test_pretension_underflow_not_real_negative_force(self):
        row = self.result["mechanics"]["belt_pretension_sensitivity"][0]
        self.assertLess(row["slack_N"], 0)
        self.assertIsNone(row["radial_resultant_N"])

    def test_pretension_high_overloads_catalogue(self):
        row = self.result["mechanics"]["belt_pretension_sensitivity"][-1]
        self.assertGreater(row["radial_resultant_N"], 100)
        self.assertFalse(row["below_motor_radial_catalogue_limit_only"])

    def test_belt_branches_sum(self):
        row = self.result["mechanics"]["belt_force_comparison"]
        self.assertAlmostEqual(row["tight_N"] + row["slack_N"], 80)
        self.assertAlmostEqual(row["tight_N"] - row["slack_N"], row["delta_branch_N"])

    def test_invalid_force_inputs(self):
        with self.assertRaises(ValueError):
            belt_load(1, 10, 20, math.pi)

    def test_pressure_points_not_geometric_centres(self):
        m = self.result["mechanics"]
        self.assertEqual(m["bearing_geometric_centre_span_mm"], 25)
        self.assertEqual(m["bearing_pressure_point_span_DB_hypothesis_mm"], 43)
        self.assertEqual(m["upper_lower_pressure_points_z_mm"], [-132, -175])

    def test_reaction_equilibrium_envelope(self):
        m = self.result["mechanics"]
        self.assertAlmostEqual(m["upper_radial_reaction_envelope_N"] - m["lower_radial_reaction_envelope_N"], m["belt_force_comparison"]["radial_resultant_N"])
        self.assertFalse(m["bearing_equivalent_load_or_life_validated"])

    def test_shaft_screening_has_no_strength_approval(self):
        m = self.result["mechanics"]
        self.assertAlmostEqual(m["shaft_von_mises_nominal_MPa"], math.hypot(m["shaft_bending_nominal_MPa"], math.sqrt(3) * m["shaft_torsion_nominal_MPa"]))
        self.assertFalse(m["whole_disc_deflection_validated"])

    def test_heat_is_1D_not_temperature_prediction(self):
        self.assertAlmostEqual(self.result["mechanics"]["shaft_conduction_1D_each_W"], 8.482300164692441)
        self.assertFalse(self.result["temperature_limits"]["thermal_prediction_performed"])
        self.assertFalse(self.result["temperature_limits"]["driver_inside_reference_bay_compatible"])

    def test_height_budget(self):
        p = self.result["packaging"]
        self.assertEqual(p["cassette_bottom_top_z_mm"], [-221, -85])
        self.assertEqual(p["cassette_height_mm"], 136)
        self.assertEqual(p["bottom_raw_clearance_mm"], 24)
        self.assertEqual(p["bottom_after_service_reserve_mm"], 14)

    def test_unlowered_service_fails(self):
        self.assertLess(self.result["service"]["unlowered_top_passage_margin_mm"], 0)

    def test_lowered_service_tight_not_qualified(self):
        s = self.result["service"]
        self.assertEqual(s["lowered_top_passage_margin_mm"], 1)
        self.assertEqual(s["lowered_bottom_passage_margin_mm"], 1)
        self.assertEqual(s["lowered_bay_bottom_after_reserve_mm"], 2)
        self.assertFalse(s["rails_frame_coupling_cables_and_sweep_validated"])

    def test_workspace_not_translation(self):
        s = self.result["service"]
        self.assertEqual(s["horizontal_translation_to_fully_clear_front_mm"], 465.5)
        self.assertEqual(s["front_projection_of_cassette_when_clear_mm"], 183)
        self.assertEqual(s["workspace_remaining_geometric_only_mm"], 117)

    def test_previous_geometry_centres_unchanged(self):
        mods = self.result["packaging"]["modules"]
        self.assertEqual([m["centre_xy_mm"] for m in mods], [[210, 205], [580, 205]])
        self.assertEqual(self.result["packaging"]["module_gap_mm"], 130)

    def test_stale_front_reference_rejected(self):
        args = deepcopy(self.inputs)
        args[0]["front_skin_y_reference_mm"] = -172.5
        with self.assertRaises(ValueError):
            evaluate(*args)


if __name__ == "__main__":
    unittest.main()
