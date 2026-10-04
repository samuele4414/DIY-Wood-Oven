"""C03 cold-module screening. Standard library; no physical safety approval."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load():
    read = lambda path: json.loads(path.read_text(encoding="utf-8"))
    cfg = read(HERE / "layout.json")
    components = read(HERE / "componenti.json")
    v4 = read(HERE.parent / "quote_v4.json")
    c02 = read(HERE.parent / "architettura_c02/output/calcoli_C02.json")
    if cfg["units"] != "mm" or v4["units"] != "mm":
        raise ValueError("Only millimetres supported")
    for data in (cfg, components, c02):
        if data["production_approved"]:
            raise ValueError("A preliminary study cannot approve production")
    for key in ("cold_bench_executed", "thermal_safety_validated", "bearing_life_validated", "hot_parts_modelled"):
        if cfg[key]:
            raise ValueError(f"Not supported by this screening: {key}")
    return cfg, components, v4, c02


def finite_positive(*values):
    if not all(math.isfinite(v) and v > 0 for v in values):
        raise ValueError("Expected positive finite values")


def open_belt_length(centre_mm, small_radius_mm, large_radius_mm):
    """Exact planar, inextensible pitch-circle geometry, no tooth deflection."""
    finite_positive(centre_mm, small_radius_mm, large_radius_mm)
    delta = large_radius_mm - small_radius_mm
    if delta < 0 or centre_mm <= delta:
        raise ValueError("Invalid pitch-circle geometry")
    angle = math.asin(delta / centre_mm)
    return 2 * math.sqrt(centre_mm ** 2 - delta ** 2) + math.pi * (small_radius_mm + large_radius_mm) + 2 * delta * angle


def belt_centre(length_mm, small_radius_mm, large_radius_mm):
    finite_positive(length_mm, small_radius_mm, large_radius_mm)
    if large_radius_mm < small_radius_mm:
        raise ValueError("Radii must be ordered")
    lo = max(large_radius_mm - small_radius_mm, 1e-10) + 1e-8
    if length_mm <= open_belt_length(lo, small_radius_mm, large_radius_mm):
        raise ValueError("Belt too short")
    hi = max(length_mm, lo * 2)
    for _ in range(100):
        mid = (lo + hi) / 2
        if open_belt_length(mid, small_radius_mm, large_radius_mm) > length_mm:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def belt_load(torque_Nm, driven_radius_mm, pretension_N, tangent_angle_rad):
    finite_positive(torque_Nm, driven_radius_mm, pretension_N)
    if not math.isfinite(tangent_angle_rad) or not 0 <= tangent_angle_rad < math.pi / 2:
        raise ValueError("Invalid tangent angle")
    delta = torque_Nm / (driven_radius_mm / 1000)
    slack = pretension_N - delta / 2
    return {"delta_branch_N": delta, "tight_N": pretension_N + delta / 2,
            "slack_N": slack, "positive_slack_assumption": slack > 0,
            "radial_resultant_N": math.hypot(2 * pretension_N * math.cos(tangent_angle_rad), delta * math.sin(tangent_angle_rad)) if slack > 0 else None}


def evaluate(cfg, components, v4, c02):
    items = {row["id"]: row["facts"] for row in components["items"]}
    motor, bearing = items["P01"], items["P03"]
    small, large, belt = items["P04A"], items["P04B"], items["P05"]
    rs, rl = (row["teeth"] * row["pitch_mm"] / (2 * math.pi) for row in (small, large))
    centre = belt_centre(belt["pitch_length_mm"], rs, rl)
    angle = math.asin((rl - rs) / centre)
    external_ratio = large["teeth"] / small["teeth"]
    planet_ratio = motor["gear_ratio_numerator"] / motor["gear_ratio_denominator"]
    m = c02["mechanical"]
    torque = max(row["starting_screening_Nm"] for row in m["torque_sensitivity"])
    force_rows = []
    for pretension in cfg["pretension_branch_candidates_N"]:
        row = {"pretension_each_branch_N": pretension, **belt_load(torque, rl, pretension, angle)}
        row["below_motor_radial_catalogue_limit_only"] = row["radial_resultant_N"] < motor["shaft_radial_limit_N"] if row["radial_resultant_N"] is not None else False
        force_rows.append(row)
    selected = belt_load(torque, rl, cfg["pretension_comparison_N"], angle)
    # a is measured from the side face, NOT from the bearing centre.
    zupper, zlower = cfg["bearing_centres_z_mm"]
    centre_span = zupper - zlower
    outward_offset = bearing["pressure_point_a_mm"] - bearing["width_mm"] / 2
    pressure_upper, pressure_lower = zupper + outward_offset, zlower - outward_offset
    span = pressure_upper - pressure_lower
    overhang = cfg["belt_force_plane_z_mm"] - pressure_upper
    finite_positive(centre_span, span, overhang)
    radial = selected["radial_resultant_N"]
    if radial is None:
        raise ValueError("The comparison pretension cannot maintain positive slack")
    moment = m["tool_at_stone_edge_overturning_moment_Nm"]
    d, di = cfg["shaft_outer_inner_mm"]
    if not (math.isfinite(di) and 0 <= di < d):
        raise ValueError("Invalid shaft diameters")
    finite_positive(d, cfg["steel_E_assumed_GPa"], cfg["net_bay_mm"])
    bending_moment = moment + radial * overhang / 1000
    inertia_mm4 = math.pi / 64 * (d ** 4 - di ** 4)
    bending_MPa = bending_moment * 1000 * d / (2 * inertia_mm4)
    torsion_MPa = torque * 1000 * d / (4 * inertia_mm4)
    exposed_stub_mm = cfg["shaft_z_range_mm"][1] - pressure_upper
    stub_angle = moment * 1000 * exposed_stub_mm / (cfg["steel_E_assumed_GPa"] * 1000 * inertia_mm4)
    area_m2 = math.pi / 4 * (d ** 2 - di ** 2) / 1e6
    shaft_heat = cfg["shaft_heat_k_assumed_W_mK"] * area_m2 * cfg["shaft_heat_delta_assumed_K"] / (cfg["shaft_heat_length_assumed_mm"] / 1000)
    tray_top = cfg["motor_output_face_z_mm"] - cfg["motor_body_length_reservation_mm"] - cfg["motor_rear_to_tray_reserve_mm"]
    bottom = tray_top - cfg["tray_thickness_mm"]
    top = cfg["shaft_z_range_mm"][1]
    bay_bottom = cfg["bay_top_z_mm"] - cfg["net_bay_mm"]
    port_top = cfg["service_port_top_z_mm"]
    port_bottom = port_top - cfg["service_port_width_height_mm"][1]
    margin = cfg["service_passage_margin_mm"]
    drop = cfg["service_lowering_mm"]
    width, depth = cfg["module_width_depth_mm"]
    modules = []
    for index, (x, y) in enumerate(v4["program_constraints"]["rotating_discs"]["centres"]):
        bounds = [x - width / 2, x + width / 2, y - depth / 2, y + depth / 2]
        modules.append({"centre_xy_mm": [x, y], "motor_centre_xy_mm": [x + (-1 if index == 0 else 1) * centre, y], "bounds_xy_mm": bounds})
    old_front = c02["body_budget"]["C01_front_outer_y_mm"]
    if abs(old_front - cfg["front_skin_y_reference_mm"]) > 1e-6:
        raise ValueError("Front skin reference no longer matches C01/C02")
    translation = modules[0]["bounds_xy_mm"][3] - old_front + margin
    projection = depth + margin
    pulley_top = cfg["pulley_bottom_z_mm"] + cfg["pulley_axial_mm"]
    return {
        "study_id": "C03", "production_approved": False, "physical_tests_executed": False,
        "hot_integration_validated": False, "CFD_executed": False,
        "drive": {"planet_ratio": planet_ratio, "external_ratio": external_ratio,
                  "total_motor_to_disc_ratio": planet_ratio * external_ratio,
                  "small_pitch_radius_mm": rs, "large_pitch_radius_mm": rl,
                  "centre_distance_mm": centre, "belt_length_residual_mm": open_belt_length(centre, rs, rl) - belt["pitch_length_mm"],
                  "small_wrap_deg": 180 - 2 * math.degrees(angle),
                  "small_teeth_in_contact_geometric": small["teeth"] * (math.pi - 2 * angle) / (2 * math.pi),
                  "inside_tension_slot_range": cfg["tensioner_centre_range_mm"][0] <= centre <= cfg["tensioner_centre_range_mm"][1],
                  "required_geared_motor_torque_screening_Nm": torque / (external_ratio * cfg["belt_efficiency_assumed"]),
                  "catalogue_torque_conflict_Nm": [motor["curve_max_permissible_torque_Nm"], motor["max_permissible_torque_TDS_Nm"]],
                  "running_torque_available_validated": False,
                  "speed_rows": [{"disc_rpm": rpm, "geared_output_rpm": rpm * external_ratio,
                                  "bare_motor_rpm": rpm * external_ratio * planet_ratio,
                                  "microsteps_per_fullstep": u,
                                  "pulse_frequency_Hz": rpm * external_ratio * planet_ratio * 200 * u / 60,
                                  "disc_turns_in_90s": rpm * 1.5}
                                 for rpm in cfg["rpm_disc_candidates"] for u in cfg["microsteps_candidates"]]},
        "mechanics": {"axial_scenario_N": m["assumed_axial_load_with_tool_N"], "stone_mass_kg": m["stone_mass_each_kg"],
                      "moving_mass_with_pizza_assumed_kg": m["assumed_rotating_mass_with_pizza_kg"], "tool_moment_Nm": moment,
                      "direct_axial_motor_limit_N": motor["shaft_axial_limit_N"], "direct_axial_support_incompatible": m["assumed_axial_load_with_tool_N"] > motor["shaft_axial_limit_N"],
                      "startup_torque_assumed_Nm": torque, "belt_pretension_sensitivity": force_rows,
                      "belt_force_comparison": selected,
                      "bearing_geometric_centre_span_mm": centre_span, "bearing_pressure_point_span_DB_hypothesis_mm": span,
                      "upper_lower_pressure_points_z_mm": [pressure_upper, pressure_lower], "belt_overhang_to_upper_pressure_point_mm": overhang,
                      "tool_only_radial_couple_per_bearing_N": moment * 1000 / span,
                      "upper_radial_reaction_envelope_N": radial * (1 + overhang / span) + moment * 1000 / span,
                      "lower_radial_reaction_envelope_N": radial * overhang / span + moment * 1000 / span,
                      "bearing_equivalent_load_or_life_validated": False,
                      "shaft_max_moment_superposition_assumed_Nm": bending_moment, "shaft_bending_nominal_MPa": bending_MPa,
                      "shaft_torsion_nominal_MPa": torsion_MPa, "shaft_von_mises_nominal_MPa": math.sqrt(bending_MPa ** 2 + 3 * torsion_MPa ** 2),
                      "stub_only_rigid_clamp_length_mm": exposed_stub_mm, "stub_only_tool_moment_rim_displacement_mm": v4["program_constraints"]["rotating_discs"]["diameter"] / 2 * stub_angle,
                      "whole_disc_deflection_validated": False, "shaft_conduction_1D_each_W": shaft_heat,
                      "motor_copper_two_phase_Irms_reference_W": 2 * motor["phase_current_A"] ** 2 * motor["phase_resistance_ohm"]},
        "packaging": {"modules": modules, "module_gap_mm": modules[1]["bounds_xy_mm"][0] - modules[0]["bounds_xy_mm"][1],
                      "tray_top_z_mm": tray_top, "cassette_bottom_top_z_mm": [bottom, top], "cassette_height_mm": top - bottom,
                      "bay_bottom_top_z_mm": [bay_bottom, cfg["bay_top_z_mm"]], "bottom_raw_clearance_mm": bottom - bay_bottom,
                      "bottom_after_service_reserve_mm": bottom - bay_bottom - cfg["bottom_service_reserve_mm"],
                      "motor_mount_outer_side_margin_at_max_slot_mm": width / 2 - max(cfg["tensioner_centre_range_mm"]) - cfg["motor_face_plate_width_mm"] / 2,
                      "pulley_to_shield_gap_mm": cfg["shield_z_range_mm"][0] - pulley_top,
                      "pulley_to_cartridge_gap_mm": cfg["pulley_bottom_z_mm"] - cfg["cartridge_top_z_mm"],
                      "motor_shaft_pulley_bore_overlap_min_mm": min(cfg["pulley_bottom_z_mm"] + cfg["pulley_axial_mm"], cfg["motor_output_face_z_mm"] + motor["shaft_length_mm"] - motor["shaft_length_tolerance_mm"]) - cfg["pulley_bottom_z_mm"],
                      "all_fit_and_tolerances_validated": False},
        "service": {"port_bottom_top_z_mm": [port_bottom, port_top], "proposed_drop_mm": drop,
                    "unlowered_top_passage_margin_mm": port_top - margin - top,
                    "lowered_top_passage_margin_mm": port_top - margin - (top - drop),
                    "lowered_bottom_passage_margin_mm": bottom - drop - (port_bottom + margin),
                    "lowered_bay_bottom_after_reserve_mm": bottom - drop - bay_bottom - cfg["bottom_service_reserve_mm"],
                    "port_horizontal_extra_after_margins_mm": cfg["service_port_width_height_mm"][0] - width - 2 * margin,
                    "horizontal_translation_to_fully_clear_front_mm": translation,
                    "front_projection_of_cassette_when_clear_mm": projection,
                    "workspace_remaining_geometric_only_mm": cfg["front_workspace_mm"] - projection,
                    "requires_cold_supported_disc_disconnection": True, "shield_must_move_with_cassette": True,
                    "rails_frame_coupling_cables_and_sweep_validated": False,
                    "condition": "Fit ONLY in empty rectangular path with shield attached to drawer; no real-frame/sweep or ergonomic approval"},
        "temperature_limits": {"motor_ambient_max_C": motor["ambient_C"][1], "driver_ambient_max_C": items["P06"]["operating_C"][1],
                               "belt_max_C": belt["temperature_C"][1], "bay_reference_C02_C": 50,
                               "driver_inside_reference_bay_compatible": False, "thermal_prediction_performed": False}
    }
