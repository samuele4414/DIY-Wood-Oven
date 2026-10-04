"""C02: transparent screening calculations, NOT an oven certification.

Standard library only. The pressure equations reproduce the previous local
MATLAB network, adding a separate inlet-loss sensitivity. All temperatures,
fuel burn rate and loss coefficients remain assigned, not predicted.
"""
from dataclasses import dataclass, replace
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def load():
    cfg = json.loads((HERE / "assunzioni.json").read_text(encoding="utf-8"))
    v4 = json.loads((HERE / cfg["source_v4"]).read_text(encoding="utf-8"))
    c01 = json.loads((HERE / cfg["source_c01"]).read_text(encoding="utf-8"))
    if v4["units"] != "mm" or c01["units"] != "mm":
        raise ValueError("Source units must be millimetres")
    if cfg["production_approved"]:
        raise ValueError("Screening generator cannot approve production")
    return cfg, v4, c01


def growth_mm(length_mm, mean_alpha, temperature_C, reference_C):
    if not all(math.isfinite(v) for v in (length_mm, mean_alpha, temperature_C, reference_C)):
        raise ValueError("Non-finite thermal expansion input")
    if length_mm <= 0 or mean_alpha < 0:
        raise ValueError("Invalid thermal expansion input")
    return length_mm * mean_alpha * (temperature_C - reference_C)


def shaft_heat_W(outer_mm, inner_mm, length_mm, conductivity_W_mK, delta_K):
    if not all(math.isfinite(v) for v in (outer_mm, inner_mm, length_mm, conductivity_W_mK, delta_K)):
        raise ValueError("Non-finite shaft input")
    if not (0 <= inner_mm < outer_mm and length_mm > 0 and conductivity_W_mK > 0):
        raise ValueError("Invalid shaft geometry/properties")
    area_m2 = math.pi / 4 * ((outer_mm / 1000) ** 2 - (inner_mm / 1000) ** 2)
    return conductivity_W_mK * area_m2 * delta_K / (length_mm / 1000)


def mechanical(cfg, v4, c01):
    m, h = cfg["mechanical"], c01["packaging_hypotheses"]
    spec = v4["program_constraints"]["rotating_discs"]
    floor = v4["program_constraints"]["cooking_floor"]
    radius_m = spec["diameter"] / 2000
    stone_mass = math.pi * radius_m ** 2 * h["cooking_stone_mm"] / 1000 * m["stone_density_assumed_kg_m3"]
    moving_mass = stone_mass + m["extra_rotating_mass_assumed_kg"] + m["pizza_mass_assumed_kg"]
    load_N = moving_mass * 9.81 + m["downward_tool_load_assumed_N"]
    p = m["parallel_stack_reservations_mm"]
    parallel = p["shield_and_standoff"] + p["pulley_coupling_plane"] + max(p["bearing_cartridge"], p["offset_gearmotor"]) + p["bottom_service_margin"]
    coaxial = sum(m["coaxial_stack_reservations_mm"])
    torque = [{"assumed_mu": mu,
               "running_screening_Nm": mu * load_N * m["equivalent_friction_radius_mm"] / 1000 + m["seal_torque_assumed_Nm"],
               "starting_screening_Nm": (mu * load_N * m["equivalent_friction_radius_mm"] / 1000 + m["seal_torque_assumed_Nm"]) * m["starting_torque_multiplier_assumed"]}
              for mu in m["friction_coefficients_assumed"]]
    steel_growth = growth_mm(m["hot_spreader_candidate_diameter_mm"], m["steel_mean_alpha_20_600_per_K"], m["hot_spreader_temperature_C"], m["reference_temperature_C"])
    stone_growth = growth_mm(spec["diameter"], m["stone_alpha_assumed_per_K"], m["stone_temperature_C"], m["reference_temperature_C"])
    widths, depth = m["module_width_depth_mm"], floor["depth"]
    modules = []
    for x, y in spec["centres"]:
        bounds = [x - widths[0] / 2, x + widths[0] / 2, y - widths[1] / 2, y + widths[1] / 2]
        modules.append({"xy_bounds_mm": bounds, "inside_nominal_floor_projection": bounds[0] >= 0 and bounds[1] <= floor["width"] and bounds[2] >= 0 and bounds[3] <= depth})
    return {
        "stone_mass_each_kg": stone_mass, "assumed_rotating_mass_with_pizza_kg": moving_mass,
        "assumed_axial_load_with_tool_N": load_N,
        "tool_at_stone_edge_overturning_moment_Nm": m["downward_tool_load_assumed_N"] * radius_m,
        "parallel_required_height_mm": parallel, "coaxial_required_height_mm": coaxial,
        "bay_comparison": [{"net_height_mm": b, "parallel_remaining_mm": b - parallel,
                            "coaxial_remaining_mm": b - coaxial} for b in m["bay_comparison_mm"]],
        "increment_body_height_from_c01_mm": m["proposed_clear_bay_mm"] - h["mechanism_clear_height_mm"] + m["carrier_height_reservation_mm"] - h["carrier_reserve_mm"],
        "steel_spreader_diameter_growth_mm": steel_growth, "stone_diameter_growth_assumed_mm": stone_growth,
        "thermal_strain_difference_equivalent_over_320mm": growth_mm(spec["diameter"], m["steel_mean_alpha_20_600_per_K"], m["hot_spreader_temperature_C"], m["reference_temperature_C"]) - stone_growth,
        "torque_sensitivity": torque, "modules": modules,
        "module_separation_mm": spec["centres"][1][0] - spec["centres"][0][0] - widths[0],
        "rotation": [{"rpm": rpm, "turns_in_60s": rpm, "turns_in_90s": rpm * 1.5} for rpm in m["rpm_candidates"]],
        "radial_gap_geometry_only": [{"gap_mm": gap,
                                      "between_nominal_holes_mm": spec["centres"][1][0] - spec["centres"][0][0] - spec["diameter"] - 2 * gap,
                                      "front_nominal_stone_bridge_mm": spec["centres"][0][1] - spec["diameter"] / 2 - gap}
                                     for gap in m["radial_gap_candidates_mm"]],
        "shaft_heat_screening": [{"outer_mm": d, "inner_mm": di,
                                  "conducted_W_each": shaft_heat_W(d, di, m["shaft_comparison"]["length_mm"], m["shaft_comparison"]["conductivity_assumed_W_mK"], m["shaft_comparison"]["delta_temperature_K"])}
                                 for d, di in m["shaft_comparison"]["outer_inner_diameters_mm"]],
        "bearing_and_motor_selected": False, "hot_strength_or_temperature_validated": False
    }


def flue_geometry(cfg, v4, c01):
    a, h = cfg["air_and_flue"], c01["packaging_hypotheses"]
    entry = math.prod(a["collector_entry_clear_width_height_mm"])
    neck = math.prod(a["collector_neck_clear_width_height_mm"])
    wall = a["collector_sheet_candidate_mm"]
    reserve = h["collector_reservation"]
    original_top_diameter = 2 * 76  # Explicitly from the C01 mesh, NOT a V4 quote.
    original_top_across_flats = original_top_diameter * math.cos(math.pi / 8)
    collar_cases = []
    throat_cases = []
    for d in a["flue_diameter_comparison_mm"]:
        area = math.pi * d * d / 4
        throat_cases.append({"diameter_mm": d, "area_cm2": area / 100,
                             "entry_area_ratio": entry / area, "neck_area_ratio": neck / area,
                             "same_30mm_height_at_width_D_ratio": d * a["collector_entry_clear_width_height_mm"][1] / area,
                             "height_at_width_D_for_equal_area_mm": area / d,
                             "proposed_neck_area_ge_pipe": neck >= area})
        for insulation in a["local_flue_insulation_comparison_mm"]:
            # Illustrative pipe-wall budget, not dimensions of the named chimney.
            pipe_outer = d + 2 * h["flue_wall_mm"] + 2 * insulation + 2 * h["outer_skin_mm"]
            collar_min = pipe_outer + 2 * a["collar_radial_mounting_reserve_mm"] + 2 * a["collar_cover_sheet_mm"]
            collar_cases.append({"bore_mm": d, "insulation_mm": insulation,
                                 "illustrative_pipe_outer_mm": pipe_outer,
                                 "min_collar_across_flats_with_mounting_mm": collar_min,
                                 "fits_C01_top_nominally": pipe_outer <= original_top_across_flats - 2 * h["outer_skin_mm"],
                                 "fits_C02_reservation_with_mounting": collar_min <= a["collar_across_flats_reservation_mm"]})
    plate = a["catalogue_DN130_25_reference"]["support_plate_A_B_mm"]
    plate_outer_budget = [v + 2 * (a["collar_radial_mounting_reserve_mm"] + a["collar_cover_sheet_mm"]) for v in plate]
    # A bounding rectangle must fit the octagon's diagonal faces, not only its
    # X/Y span. Regular octagon, normals along X/Y and at 45 degrees.
    base_min = max(*plate_outer_budget, sum(plate_outer_budget) / math.sqrt(2))
    plate_check = {"catalogue_A_B_mm": plate, "rectangle_with_mounting_and_cover_mm": plate_outer_budget,
                   "min_regular_octagon_outer_across_flats_mm": base_min,
                   "fits_old_proposed_340_octagon": base_min <= 340,
                   "proposed_base_outer_across_flats_mm": a["collar_base_across_flats_reservation_mm"],
                   "fits_proposed_base_budget": base_min <= a["collar_base_across_flats_reservation_mm"],
                   "actual_plate_CAD_validated": False}
    return {"collector_entry_area_cm2": entry / 100, "collector_neck_area_cm2": neck / 100,
            "entry_outer_width_height_mm": [v + 2 * wall for v in a["collector_entry_clear_width_height_mm"]],
            "entry_outer_fits_C01_box_width_height": a["collector_entry_clear_width_height_mm"][0] + 2 * wall <= reserve["x_range_mm"][1] - reserve["x_range_mm"][0] and a["collector_entry_clear_width_height_mm"][1] + 2 * wall <= reserve["z_range_mm"][1] - reserve["z_range_mm"][0],
            "neck_height_exceeds_C01_box": a["collector_neck_clear_width_height_mm"][1] + 2 * wall > reserve["z_range_mm"][1] - reserve["z_range_mm"][0],
            "C01_collar_top_across_flats_mm": original_top_across_flats,
            "C02_collar_reserved_across_flats_mm": a["collar_across_flats_reservation_mm"],
            "collar_plate_budget": plate_check,
            "throat_comparison": throat_cases, "collar_comparison": collar_cases,
            "captation_validated": False, "flue_product_selected": False}


@dataclass(frozen=True)
class DraftCase:
    ambient_C: float = 25
    chamber_C: float = 500
    flue_C: float = 250
    pressure_Pa: float = 101325
    gas_constant_J_kgK: float = 287
    gravity_m_s2: float = 9.81
    roof_z_m: float = .28
    inlet_z_m: float = .03
    door_width_m: float = .72
    door_height_m: float = .16
    door_open: bool = False
    inlet_area_cm2: float = 60
    cd_inlet: float = .65
    cd_door: float = .65
    extra_inlet_K: float = 0
    flue_diameter_mm: float = 130
    flue_height_m: float = 1
    minor_flue_K: float = 4
    darcy_f: float = .03
    wind_adverse_Pa: float = 0
    fuel_kg_h: float = 4.5
    moisture_wet_fraction: float = .2
    dry_fractions: tuple = (.508, .064, .418, .01)
    oxygen_mass_fraction: float = .231


def draft_parameters(cfg, v4):
    r = cfg["air_and_flue"]["pressure_network_reference"]
    values = {key: value for key, value in r.items() if key in DraftCase.__dataclass_fields__}
    values["dry_fractions"] = tuple(r["dry_C_H_O_ash_fractions"])
    values["roof_z_m"] = v4["roof_and_flue_candidates"]["roof_peak_z"] / 1000
    opening = v4["current_layout_candidate"]["door_clear_opening"]
    values["door_width_m"], values["door_height_m"] = opening["width"] / 1000, opening["height"] / 1000
    return DraftCase(**values)


def validate_draft(a):
    for value in a.__dict__.values():
        if isinstance(value, (int, float)) and not math.isfinite(value):
            raise ValueError("Non-finite draft input")
    if not (a.door_open in (True, False) and a.ambient_C > -273.15 and a.chamber_C >= a.ambient_C and a.flue_C > -273.15
            and a.pressure_Pa > 0 and a.gas_constant_J_kgK > 0 and a.gravity_m_s2 > 0
            and a.roof_z_m >= a.door_height_m > 0 and a.door_width_m > 0
            and 0 <= a.inlet_z_m <= a.roof_z_m and a.inlet_area_cm2 > 0
            and 0 < a.cd_inlet <= 1 and 0 < a.cd_door <= 1 and a.extra_inlet_K >= 0
            and a.flue_diameter_mm > 0 and a.flue_height_m >= 0 and a.minor_flue_K > 0
            and a.darcy_f >= 0 and a.fuel_kg_h >= 0 and 0 <= a.moisture_wet_fraction < 1
            and 0 < a.oxygen_mass_fraction <= 1 and len(a.dry_fractions) == 4
            and all(math.isfinite(v) and v >= 0 for v in a.dry_fractions)
            and abs(sum(a.dry_fractions) - 1) < 1e-8):
        raise ValueError("Invalid draft input")


def properties(a):
    validate_draft(a)
    density = lambda t: a.pressure_Pa / (a.gas_constant_J_kgK * (t + 273.15))
    ra, rc, rf = density(a.ambient_C), density(a.chamber_C), density(a.flue_C)
    beta = a.gravity_m_s2 * (ra - rc)
    stack = a.gravity_m_s2 * a.flue_height_m * (ra - rf)
    fuel = a.fuel_kg_h / 3600
    C, H, O, ash = a.dry_fractions
    stoich = ((8 / 3) * C + 8 * H - O) / a.oxygen_mass_fraction
    if stoich <= 0:
        raise ValueError("Non-positive stoichiometric air")
    fuel_gas = fuel * (1 - (1 - a.moisture_wet_fraction) * ash)
    required = stoich * (1 - a.moisture_wet_fraction) * fuel
    return ra, rc, rf, beta, stack, fuel_gas, required, stoich


def door_integrals(p0, beta, height):
    def segment(length, q0, q1):
        den = math.sqrt(q0) + math.sqrt(q1)
        return 0 if den == 0 else (2 / 3) * length * (q0 + math.sqrt(q0 * q1) + q1) / den
    if beta < 1e-10:
        return height * math.sqrt(max(-p0, 0)), height * math.sqrt(max(p0, 0))
    crossing = min(height, max(0, -p0 / beta))
    incoming = segment(crossing, max(-p0, 0), max(-(p0 + beta * crossing), 0))
    outgoing = segment(height - crossing, max(p0 + beta * crossing, 0), max(p0 + beta * height, 0))
    return incoming, outgoing


def solve_draft(a):
    ra, rc, rf, beta, stack, fuel_gas, required, stoich = properties(a)
    diameter = a.flue_diameter_mm / 1000
    area = math.pi * diameter ** 2 / 4
    loss = a.minor_flue_K + a.darcy_f * a.flue_height_m / diameter
    effective_cd = 1 / math.sqrt(1 / a.cd_inlet ** 2 + a.extra_inlet_K)
    def balance(p):
        inlet = p + beta * a.inlet_z_m
        rear_in = effective_cd * a.inlet_area_cm2 / 10000 * math.sqrt(2 * ra * max(-inlet, 0))
        rear_out = effective_cd * a.inlet_area_cm2 / 10000 * math.sqrt(2 * rc * max(inlet, 0))
        door_in, door_out = 0, 0
        if a.door_open:
            int_in, int_out = door_integrals(p, beta, a.door_height_m)
            door_in = a.cd_door * a.door_width_m * math.sqrt(2 * ra) * int_in
            door_out = a.cd_door * a.door_width_m * math.sqrt(2 * rc) * int_out
        drive = p + beta * a.roof_z_m + stack - a.wind_adverse_Pa
        flow = math.copysign(area * math.sqrt(2 * (rf if drive >= 0 else ra) * abs(drive) / loss), drive)
        residual = rear_in + door_in + fuel_gas - rear_out - door_out - flow
        return residual, rear_in, rear_out, door_in, door_out, flow, drive
    bound = max(1, abs(stack) + beta * a.roof_z_m + abs(a.wind_adverse_Pa))
    for _ in range(80):
        if balance(-bound)[0] >= 0 >= balance(bound)[0]:
            break
        bound *= 2
    else:
        raise ValueError("Cannot bracket chamber pressure")
    lo, hi = -bound, bound
    for _ in range(160):
        p = (lo + hi) / 2
        residual = balance(p)[0]
        if abs(hi - lo) < 1e-12 or residual == 0:
            break
        if residual > 0:
            lo = p
        else:
            hi = p
    residual, rear_in, rear_out, door_in, door_out, flow, drive = balance(p)
    return {"pressure_floor_Pa": p, "pressure_door_top_Pa": p + beta * a.door_height_m,
            "lambda_rear": rear_in / required if required else None,
            "lambda_total_inlets": (rear_in + door_in + max(-flow, 0)) / required if required else None,
            "rear_in_kg_h": rear_in * 3600, "rear_out_kg_h": rear_out * 3600,
            "door_in_kg_h": door_in * 3600, "door_out_gas_kg_h": door_out * 3600,
            "flue_gas_kg_h": flow * 3600, "reverse_flue": flow < 0,
            "neutral_height_mm": -p / beta * 1000 if beta > 1e-10 else None,
            "mass_residual_kg_s": residual, "effective_inlet_Cd": effective_cd,
            "air_stoich_kg_per_kg_dry": stoich, "captation_validated": False}


def pressure_budget(a, comparison_lambda=2):
    if a.door_open:
        raise ValueError("Closed-door pressure budget is not applicable to an open mouth")
    if not math.isfinite(comparison_lambda) or comparison_lambda <= 0:
        raise ValueError("Invalid comparison lambda")
    ra, rc, rf, beta, stack, fuel_gas, required, stoich = properties(a)
    air = required * comparison_lambda
    gas = air + fuel_gas
    inlet_area = a.inlet_area_cm2 / 10000
    diameter = a.flue_diameter_mm / 1000
    flue_area = math.pi * diameter ** 2 / 4
    inlet_loss = air ** 2 / (2 * ra * inlet_area ** 2) * (1 / a.cd_inlet ** 2 + a.extra_inlet_K)
    flue_loss = gas ** 2 / (2 * rf * flue_area ** 2) * (a.minor_flue_K + a.darcy_f * a.flue_height_m / diameter)
    head = beta * (a.roof_z_m - a.inlet_z_m) + stack
    return {"comparison_lambda": comparison_lambda, "required_air_kg_h": air * 3600,
            "required_air_at_ambient_m3_h": air / ra * 3600,
            "net_inlet_velocity_m_s": air / (ra * inlet_area),
            "static_head_Pa": head, "inlet_loss_Pa": inlet_loss, "flue_loss_Pa": flue_loss,
            "wind_adverse_Pa": a.wind_adverse_Pa,
            "margin_Pa": head - a.wind_adverse_Pa - inlet_loss - flue_loss,
            "is_combustion_or_safety_approval": False}


def scenarios(cfg, v4):
    base = draft_parameters(cfg, v4)
    a = cfg["air_and_flue"]
    result = []
    def add(name, case):
        row = {"id": name, "inlet_cm2": case.inlet_area_cm2, "diameter_mm": case.flue_diameter_mm,
               "height_m_from_hot_roof": case.flue_height_m, "mean_flue_C": case.flue_C,
               "minor_flue_K": case.minor_flue_K, "extra_inlet_K": case.extra_inlet_K,
               "wind_Pa": case.wind_adverse_Pa, "door_open": case.door_open,
               **solve_draft(case), "closed_door_budget": None if case.door_open else pressure_budget(case, a["pressure_network_reference"]["comparison_lambda"])}
        result.append(row)
    add("RIFERIMENTO_MATLAB_60_H1", base)
    for area in a["comparison_free_areas_cm2"]:
        for height in a["flue_height_comparison_m"]:
            for extra in a["extra_inlet_loss_K_candidates"]:
                add(f"A{area}_H{height:g}_Ka{extra}", replace(base, inlet_area_cm2=area, flue_height_m=height, extra_inlet_K=extra))
    preferred = replace(base, inlet_area_cm2=a["preferred_inlet_free_area_cm2"], flue_height_m=1.5, extra_inlet_K=2)
    add("C02_PUNTO_DI_CONFRONTO", preferred)
    add("C02_PORTA_APERTA", replace(preferred, door_open=True))
    add("C02_FREDDO100_K8_VENTO3", replace(preferred, flue_C=100, minor_flue_K=8, wind_adverse_Pa=3))
    add("C02_T150_K8_VENTO3", replace(preferred, flue_C=150, minor_flue_K=8, wind_adverse_Pa=3))
    add("C02_D150_CON_STESSE_IPOTESI", replace(preferred, flue_diameter_mm=150))
    add("C02_WIND10_INVERSIONE_POSSIBILE", replace(preferred, wind_adverse_Pa=10))
    return result


def evaluate(cfg, v4, c01):
    a = cfg["air_and_flue"]
    air_rows = []
    for area in a["comparison_free_areas_cm2"]:
        air_rows.append({"net_area_cm2": area, "gross_area_cm2_at_assumed_free_fraction": area / a["grille_free_fraction_assumed"],
                         "primary_secondary_net_cm2_assumed": [area * f for f in a["primary_secondary_area_split_assumed"]]})
    return {"study_id": cfg["study_id"], "scope": "mechanical_geometrical_and_1D_pressure_SCREENING",
            "production_approved": False, "full_CFD_executed": False, "physical_tests_executed": False,
            "mechanical": mechanical(cfg, v4, c01), "body_budget": body_budget(cfg, v4, c01),
            "flue_geometry": flue_geometry(cfg, v4, c01),
            "inlet_areas": air_rows, "pressure_scenarios": scenarios(cfg, v4),
            "network_height_note": "H calcolo dal colmo CALDO z280 al terminale, come rete MATLAB: non H1000 dal collare C01. Il raccordo e il suo salto di quota restano da dettagliare; nessun guadagno gratuito di tiraggio aggiunto."}


def c01_geometry():
    """Load the existing C01 envelope helper read-only, under a unique name."""
    name = "forno_c01_geometry_reference"
    if name not in sys.modules:
        path = HERE.parent / "concept_sfaccettato" / "geometry.py"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def body_budget(cfg, v4, c01):
    geo = c01_geometry()
    original = geo.build_case(c01, v4)
    modified = deepcopy(c01)
    modified["packaging_hypotheses"]["carrier_reserve_mm"] = cfg["mechanical"]["carrier_height_reservation_mm"]
    modified["packaging_hypotheses"]["mechanism_clear_height_mm"] = cfg["mechanical"]["proposed_clear_bay_mm"]
    proposed = geo.build_case(modified, v4)
    fields = ("width_mm", "depth_mm", "body_height_with_feet_mm", "ridge_z_from_cooking_floor_mm")
    outer_base = cfg["air_and_flue"]["collar_base_across_flats_reservation_mm"]
    flue_x, flue_y = v4["roof_and_flue_candidates"]["flue"]["centre_xy"]
    base_front = flue_y - outer_base / 2
    return {"C01": {k: original["summary"][k] for k in fields},
            "C02_body_only": {k: proposed["summary"][k] for k in fields},
            "C02_thermal_bottom_z_mm": proposed["thermal_bottom_z_mm"],
            "C02_bay_bottom_z_mm": proposed["bottom_z_mm"],
            "C02_feet_bottom_z_mm": proposed["feet_bottom_z_mm"],
            "C01_front_outer_y_mm": original["bounds"][1][0],
            "collar_base_front_y_mm": base_front,
            "collar_base_plan_overhang_from_C01_front_mm": max(0, original["bounds"][1][0] - base_front),
            "scope": "Same C01 body envelope; only carrier/bay stack changed. Collar, flue, support frame, collector and their penetrations NOT integrated.",
            "integrated_CAD_validated": False}
