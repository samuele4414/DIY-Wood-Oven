"""Pure-standard-library packaging geometry. All coordinates are millimetres.

The faceted cover is an intersection of supporting half-spaces of the V4
chamber. Offsets are NORMAL to each plane, not vertical roof gaps. This is a
geometrical envelope, not a structural, insulation or airflow validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOL = 1e-6


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def unit(v):
    length = math.sqrt(dot(v, v))
    if length < TOL:
        raise ValueError("Zero normal")
    return tuple(x / length for x in v)


@dataclass(frozen=True)
class Plane:
    name: str
    normal: tuple
    offset: float
    kind: str

    def gap(self, point):
        return self.offset - dot(self.normal, point)


def load_inputs(config_path=None):
    path = Path(config_path or HERE / "concept.json").resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    source = (path.parent / config["source_geometry"]).resolve()
    v4 = json.loads(source.read_text(encoding="utf-8"))
    if config.get("units") != "mm" or v4.get("units") != "mm":
        raise ValueError("Both inputs must use millimetres")
    h = config["packaging_hypotheses"]
    for key in ("hot_liner_mm", "outer_skin_mm", "body_insulation_mm",
                "cooking_stone_mm", "hearth_stone_mm", "underfloor_board_mm",
                "mechanism_clear_height_mm", "bottom_skin_mm"):
        if not math.isfinite(h[key]) or h[key] <= 0:
            raise ValueError(f"Invalid positive dimension: {key}")
    if not 0 < h["roof_transverse_slope_degrees"] < 60:
        raise ValueError("Invalid transverse roof slope")
    if not 0 < h["roof_end_slope_degrees"] < 80:
        raise ValueError("Invalid end roof slope")
    if h["mounting_and_expansion_reserve_mm"] < 0:
        raise ValueError("Negative mounting reserve")
    if v4["roof_and_flue_candidates"]["roof_profile"] != "parabolico candidato":
        raise ValueError("This generator requires the V4 parabolic roof")
    if v4["program_constraints"]["rotating_discs"]["quantity"] != 2:
        raise ValueError("This study preserves the two-disc V4 arrangement")
    return config, v4, path, source


def hot_plan(v4):
    floor = v4["program_constraints"]["cooking_floor"]
    layout = v4["current_layout_candidate"]
    width, depth = floor["width"], floor["depth"]
    rear_y = layout["firebox_y_range"][1]
    inset = (width - layout["firebox_width_rear"]) / 2
    return [(0, layout["front_door_plane_y"]), (width, layout["front_door_plane_y"]),
            (width, depth), (width - inset, rear_y), (inset, rear_y), (0, depth)]


def width_at(v4, y):
    width = v4["program_constraints"]["cooking_floor"]["width"]
    layout = v4["current_layout_candidate"]
    start, end = layout["firebox_y_range"]
    if y <= start:
        return width
    if y > end + TOL:
        raise ValueError("Position behind the firebox")
    return width + (layout["firebox_width_rear"] - width) * (y - start) / (end - start)


def roof_at(v4, x, y):
    centre = v4["program_constraints"]["cooking_floor"]["width"] / 2
    a = width_at(v4, y) / 2
    roof = v4["roof_and_flue_candidates"]
    rise = roof["roof_peak_z"] - roof["roof_eave_z"]
    return roof["roof_peak_z"] - rise * ((x - centre) / a) ** 2


def hot_support(v4, normal):
    """Exact support of the assumed chamber for any unit normal.

    At a given y the roof is quadratic in x. After maximizing in x its
    support is convex on each interval with linearly changing width, so its
    maximum in y is at interval endpoints. This also covers the vestibule
    extension, explicitly an assumption of this packaging study.
    """
    nx, ny, nz = normal
    if nz <= 0:
        return max(nx * x + ny * y for x, y in hot_plan(v4))
    floor = v4["program_constraints"]["cooking_floor"]
    layout = v4["current_layout_candidate"]
    centre = floor["width"] / 2
    roof = v4["roof_and_flue_candidates"]
    rise = roof["roof_peak_z"] - roof["roof_eave_z"]
    if rise <= 0:
        raise ValueError("Non-positive roof rise")
    values = []
    for y in (layout["front_door_plane_y"], 0, floor["depth"], layout["firebox_y_range"][1]):
        a = width_at(v4, y) / 2
        u = max(-1, min(1, nx * a / (2 * nz * rise)))
        x, z = centre + a * u, roof["roof_peak_z"] - rise * u * u
        values.append(nx * x + ny * y + nz * z)
    return max(values)


def intersect_three(a, b, c):
    bc, ca, ab = cross(b.normal, c.normal), cross(c.normal, a.normal), cross(a.normal, b.normal)
    det = dot(a.normal, bc)
    if abs(det) < 1e-10:
        return None
    return tuple((a.offset * bc[i] + b.offset * ca[i] + c.offset * ab[i]) / det for i in range(3))


def polyhedron(planes):
    vertices = []
    for triple in combinations(planes, 3):
        p = intersect_three(*triple)
        if p is None or any(plane.gap(p) < -TOL for plane in planes):
            continue
        if not any(dot(subtract(p, q), subtract(p, q)) < TOL ** 2 for q in vertices):
            vertices.append(p)
    faces = []
    for plane in planes:
        points = [p for p in vertices if abs(plane.gap(p)) < TOL * 4]
        if len(points) < 3:
            continue
        centre = tuple(sum(p[i] for p in points) / len(points) for i in range(3))
        ref = (0, 0, 1) if abs(plane.normal[2]) < .9 else (1, 0, 0)
        u = unit(cross(ref, plane.normal))
        v = cross(plane.normal, u)
        points.sort(key=lambda p: math.atan2(dot(subtract(p, centre), v), dot(subtract(p, centre), u)))
        faces.append((plane, points))
    if len(vertices) < 4 or len(faces) < 4:
        raise ValueError("Empty or unbounded external envelope")
    return vertices, faces


def clip_polygon(points, axis, value, keep_above):
    if not points:
        return []
    output = []
    for a, b in zip(points, points[1:] + points[:1]):
        da, db = a[axis] - value, b[axis] - value
        ina = da >= -TOL if keep_above else da <= TOL
        inb = db >= -TOL if keep_above else db <= TOL
        if ina:
            output.append(a)
        if ina != inb:
            t = da / (da - db)
            output.append(tuple(a[i] + t * (b[i] - a[i]) for i in range(3)))
    clean = []
    for point in output:
        if not clean or dot(subtract(point, clean[-1]), subtract(point, clean[-1])) > TOL ** 2:
            clean.append(point)
    if len(clean) > 1 and dot(subtract(clean[0], clean[-1]), subtract(clean[0], clean[-1])) < TOL ** 2:
        clean.pop()
    return clean if len(clean) >= 3 else []


def add_face(mesh, points, group, colour, name=""):
    if len(points) >= 3:
        mesh.append({"points": [list(p) for p in points], "group": group,
                     "colour": colour, "name": name or group})


def box(mesh, bounds, group, colour, name):
    x0, x1, y0, y1, z0, z1 = bounds
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    for indices in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
                    (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        add_face(mesh, [p[i] for i in indices], group, colour, name)


def cylinder(mesh, x, y, radius, z0, z1, group, colour, name, segments=32, capped=True):
    rings = [[(x + radius * math.cos(i * math.tau / segments),
               y + radius * math.sin(i * math.tau / segments), z) for i in range(segments)] for z in (z0, z1)]
    for i in range(segments):
        j = (i + 1) % segments
        add_face(mesh, [rings[0][i], rings[0][j], rings[1][j], rings[1][i]], group, colour, name)
    if capped:
        add_face(mesh, rings[0][::-1], group, colour, name)
        add_face(mesh, rings[1], group, colour, name)
    return rings


def external_roof_z(planes, x, y):
    return min((p.offset - p.normal[0] * x - p.normal[1] * y) / p.normal[2]
               for p in planes if p.kind == "roof")


def build_case(config, v4, insulation=None, mechanism_height=None):
    h = config["packaging_hypotheses"]
    insulation = h["body_insulation_mm"] if insulation is None else insulation
    mechanism_height = h["mechanism_clear_height_mm"] if mechanism_height is None else mechanism_height
    if insulation <= 0 or mechanism_height <= 0:
        raise ValueError("Negative or zero comparison dimension")
    stack = h["hot_liner_mm"] + insulation + h["outer_skin_mm"]
    offset = stack + h["mounting_and_expansion_reserve_mm"]
    thermal_bottom = -max(h["cooking_stone_mm"], h["hearth_stone_mm"]) - h["underfloor_board_mm"] - h["carrier_reserve_mm"]
    bottom = thermal_bottom - mechanism_height - h["bottom_skin_mm"]
    feet_bottom = bottom - h["feet_height_mm"]
    plan = hot_plan(v4)
    planes = []
    for i, (a, b) in enumerate(zip(plan, plan[1:] + plan[:1])):
        n = unit((b[1] - a[1], a[0] - b[0], 0))
        planes.append(Plane(f"side_{i}", n, hot_support(v4, n) + offset, "side"))
    for sign in (-1, 1):
        n = unit((sign, -1, 0))
        planes.append(Plane(f"front_bevel_{sign}", n, hot_support(v4, n) + offset, "side"))
    for axis, degrees in ((0, h["roof_transverse_slope_degrees"]), (1, h["roof_end_slope_degrees"])):
        angle = math.radians(degrees)
        for sign in (-1, 1):
            n = [0, 0, math.cos(angle)]
            n[axis] = sign * math.sin(angle)
            n = tuple(n)
            planes.append(Plane(f"roof_{axis}_{sign}", n, hot_support(v4, n) + offset, "roof"))
    planes.append(Plane("bottom", (0, 0, -1), -bottom, "bottom"))
    vertices, envelope_faces = polyhedron(planes)
    bounds = [(min(p[i] for p in vertices), max(p[i] for p in vertices)) for i in range(3)]
    front_y, rear_y = bounds[1]
    width = v4["program_constraints"]["cooking_floor"]["width"]
    layout = v4["current_layout_candidate"]
    opening = layout["door_clear_opening"]
    mouth_left, mouth_right = (width - opening["width"]) / 2, (width + opening["width"]) / 2
    mesh = []
    for plane, points in envelope_faces:
        if plane.name == "side_0":
            # Four non-overlapping regions leave the FRONT mouth genuinely open.
            parts = [clip_polygon(points, 2, 0, False), clip_polygon(points, 2, opening["height"], True)]
            mid = clip_polygon(clip_polygon(points, 2, 0, True), 2, opening["height"], False)
            parts.extend((clip_polygon(mid, 0, mouth_left, False), clip_polygon(mid, 0, mouth_right, True)))
        else:
            parts = [points]
        for part in parts:
            add_face(mesh, clip_polygon(part, 2, thermal_bottom, True), "shell", "#aeb7bd", plane.name)
            add_face(mesh, clip_polygon(part, 2, thermal_bottom, False), "base", "#252d34", plane.name)
    for x0, x1, z0, z1 in ((mouth_left - 20, mouth_right + 20, -22, 0),
                           (mouth_left - 20, mouth_right + 20, opening["height"], opening["height"] + 28),
                           (mouth_left - 20, mouth_left, 0, opening["height"]),
                           (mouth_right, mouth_right + 20, 0, opening["height"])):
        add_face(mesh, [(x0, front_y - .2, z0), (x1, front_y - .2, z0),
                        (x1, front_y - .2, z1), (x0, front_y - .2, z1)], "fascia", "#17232c", "front_fascia")
    # The opening lining is a reserved access tunnel, not a validated door frame.
    for x in (mouth_left, mouth_right):
        add_face(mesh, [(x, front_y, 0), (x, layout["front_door_plane_y"], 0),
                        (x, layout["front_door_plane_y"], opening["height"]), (x, front_y, opening["height"])],
                 "fascia", "#34414a", "mouth_tunnel")
    add_face(mesh, [(mouth_left, front_y, 0), (mouth_right, front_y, 0),
                    (mouth_right, 0, 0), (mouth_left, 0, 0)], "threshold", "#8b8171", "threshold_reserved")
    disc_spec = v4["program_constraints"]["rotating_discs"]
    radius = disc_spec["diameter"] / 2
    clearance = v4["mechanical_design_notes"]["disc_radial_clearance_hypothesis"]
    floor_depth = v4["program_constraints"]["cooking_floor"]["depth"]
    previous = 0
    for index, (cx, cy) in enumerate(disc_spec["centres"], 1):
        r = radius + clearance
        add_face(mesh, [(previous, 0, 0), (cx - r, 0, 0), (cx - r, floor_depth, 0), (previous, floor_depth, 0)], "floor", "#c9ba99")
        for i in range(32):
            a, b = math.pi * i / 32, math.pi * (i + 1) / 32
            xa, xb = cx - r * math.cos(a), cx - r * math.cos(b)
            ya, yb = r * math.sin(a), r * math.sin(b)
            add_face(mesh, [(xa, 0, 0), (xb, 0, 0), (xb, cy - yb, 0), (xa, cy - ya, 0)], "floor", "#c9ba99")
            add_face(mesh, [(xa, cy + ya, 0), (xb, cy + yb, 0), (xb, floor_depth, 0), (xa, floor_depth, 0)], "floor", "#c9ba99")
        previous = cx + r
        cylinder(mesh, cx, cy, radius, -h["cooking_stone_mm"], 0, "discs", "#e3d4ae", f"disc_{index}", 64)
        # Independent lower columns are RESERVED insulation/carrier arrangements.
        cylinder(mesh, cx, cy, radius, -h["cooking_stone_mm"] - h["underfloor_board_mm"], -h["cooking_stone_mm"], "underfloor", "#a8b99b", f"insulated_carrier_reservation_{index}")
        drive_top = thermal_bottom - h["drive_service_margin_each_side_mm"]
        drive_bottom = drive_top - h["drive_reservation_height_mm"]
        dw, dd = h["drive_reservation_width_mm"] / 2, h["drive_reservation_depth_mm"] / 2
        box(mesh, (cx - dw, cx + dw, cy - dd, cy + dd, drive_bottom, drive_top), "mechanisms", "#4b88a2", f"drive_reservation_{index}")
        cylinder(mesh, cx, cy, 7, drive_top, -h["cooking_stone_mm"] - h["underfloor_board_mm"], "mechanisms", "#536c77", f"shaft_reservation_{index}", 12)
    add_face(mesh, [(previous, 0, 0), (width, 0, 0), (width, floor_depth, 0), (previous, floor_depth, 0)], "floor", "#c9ba99")
    hearth = [(0, floor_depth, 0), (width, floor_depth, 0),
              (plan[3][0], plan[3][1], 0), (plan[4][0], plan[4][1], 0)]
    add_face(mesh, hearth, "hearth", "#b29470", "rear_hearth")
    for a, b in zip(plan[1:], plan[2:] + plan[:1]):
        add_face(mesh, [(a[0], a[1], 0), (b[0], b[1], 0),
                        (b[0], b[1], roof_at(v4, *b)), (a[0], a[1], roof_at(v4, *a))], "hot_walls", "#826d5b")
    ys = [layout["front_door_plane_y"], 0, floor_depth, layout["firebox_y_range"][1]]
    centre = width / 2
    for ya, yb in zip(ys, ys[1:]):
        for i in range(40):
            ua, ub = -1 + 2 * i / 40, -1 + 2 * (i + 1) / 40
            pts = []
            for y, u in ((ya, ua), (ya, ub), (yb, ub), (yb, ua)):
                x = centre + width_at(v4, y) / 2 * u
                pts.append((x, y, roof_at(v4, x, y)))
            add_face(mesh, pts, "hot_roof", "#977f65", "inner_roof_reference")
    collector = h["collector_reservation"]
    box(mesh, (*collector["x_range_mm"], *collector["y_range_mm"], *collector["z_range_mm"]), "collector", "#ae7bad", "collector_space_NOT_duct")
    hatch = layout["rear_loading_hatch_clear_opening"]
    hx0, hx1 = (width - hatch["width"]) / 2, (width + hatch["width"]) / 2
    hz0 = h["rear_hatch_lower_z_mm"]
    add_face(mesh, [(hx0, rear_y + .2, hz0), (hx1, rear_y + .2, hz0),
                    (hx1, rear_y + .2, hz0 + hatch["height"]), (hx0, rear_y + .2, hz0 + hatch["height"])], "shell", "#3a434c", "rear_hatch_RESERVATION")
    for i, (x, y) in enumerate(((60, -40), (width - 60, -40), (170, 600), (width - 170, 600)), 1):
        box(mesh, (x - 25, x + 25, y - 25, y + 25, feet_bottom, bottom), "feet", "#222a30", f"foot_reservation_{i}")
    flue = v4["roof_and_flue_candidates"]["flue"]
    fx, fy = flue["centre_xy"]
    ridge = bounds[2][1]
    collar_top = ridge + h["collar_height_above_ridge_mm"]
    lower, upper = [], []
    for i in range(8):
        a = math.tau * i / 8
        x, y = fx + flue["collar_diameter"] / 2 * math.cos(a), fy + flue["collar_diameter"] / 2 * math.sin(a)
        lower.append((x, y, external_roof_z(planes, x, y)))
        upper.append((fx + 76 * math.cos(a), fy + 76 * math.sin(a), collar_top))
    for i in range(8):
        j = (i + 1) % 8
        add_face(mesh, [lower[i], lower[j], upper[j], upper[i]], "collar", "#949fa7", "collar_reservation")
    r = flue["internal_diameter"] / 2
    outer_r = r + h["flue_wall_mm"]
    rings = cylinder(mesh, fx, fy, outer_r, collar_top, collar_top + h["flue_height_above_collar_mm"], "flue", "#a4afb7", "external_flue", 32, capped=False)
    # An open bore, not a cap across the outlet.
    inner = cylinder(mesh, fx, fy, r, collar_top, collar_top + h["flue_height_above_collar_mm"], "flue", "#44515b", "flue_bore", 32, capped=False)
    for i in range(32):
        j = (i + 1) % 32
        add_face(mesh, [rings[1][i], rings[1][j], inner[1][j], inner[1][i]], "flue", "#b8c1c7", "outlet_rim")
    drive_required = h["drive_reservation_height_mm"] + 2 * h["drive_service_margin_each_side_mm"]
    roof_clearance = min(p.offset - hot_support(v4, p.normal) - h["hot_liner_mm"] - h["outer_skin_mm"] for p in planes if p.kind == "roof")
    disc_area = math.pi * (radius / 1000) ** 2
    gap_area = 2 * math.pi * (((radius + clearance) / 1000) ** 2 - (radius / 1000) ** 2)
    floor_area = width * floor_depth / 1e6
    hearth_area = (layout["firebox_width_front"] + layout["firebox_width_rear"]) / 2 * layout["firebox_depth"] / 1e6
    density = h["provisional_stone_density_kg_m3"]
    stone_mass = (floor_area - gap_area) * h["cooking_stone_mm"] / 1000 * density + hearth_area * h["hearth_stone_mm"] / 1000 * density
    roof_checks = []
    for p in planes:
        if p.kind != "bottom":
            roof_checks.append({"plane": p.name, "normal": list(p.normal),
                                "normal_hot_to_outer_mm": p.offset - hot_support(v4, p.normal)})
    return {
        "id": f"I{insulation:g}_M{mechanism_height:g}", "insulation_mm": insulation,
        "mechanism_clear_height_mm": mechanism_height, "stack_mm": stack,
        "normal_offset_mm": offset, "planes": planes, "vertices": vertices,
        "envelope_faces": envelope_faces, "mesh": mesh, "bounds": bounds,
        "thermal_bottom_z_mm": thermal_bottom, "bottom_z_mm": bottom,
        "feet_bottom_z_mm": feet_bottom, "collar_top_z_mm": collar_top,
        "summary": {
            "width_mm": bounds[0][1] - bounds[0][0], "depth_mm": rear_y - front_y,
            "body_height_with_feet_mm": ridge - feet_bottom,
            "ridge_z_from_cooking_floor_mm": ridge,
            "height_with_flue_1000_mm": collar_top + 1000 - feet_bottom,
            "height_with_flue_1500_mm": collar_top + 1500 - feet_bottom,
            "nominal_roof_insulation_space_mm": roof_clearance,
            "drive_required_clear_height_mm": drive_required,
            "drive_reservations_fit": mechanism_height >= drive_required,
            "front_skin_to_disc_centres_mm": disc_spec["centres"][0][1] - front_y,
            "paddle_side_margin_mm": (opening["width"] - (disc_spec["centres"][1][0] - disc_spec["centres"][0][0]) - 340) / 2,
            "stone_mass_only_kg": stone_mass,
            "one_disc_mass_kg": disc_area * h["cooking_stone_mm"] / 1000 * density,
            "is_production_approved": False
        }, "normal_offset_checks": roof_checks
    }


def section_polygon(case, axis, value):
    points = []
    for _, face in case["envelope_faces"]:
        for a, b in zip(face, face[1:] + face[:1]):
            da, db = a[axis] - value, b[axis] - value
            if abs(da) < TOL:
                points.append(a)
            if da * db < 0:
                t = da / (da - db)
                points.append(tuple(a[i] + t * (b[i] - a[i]) for i in range(3)))
    unique = []
    for p in points:
        if not any(dot(subtract(p, q), subtract(p, q)) < TOL ** 2 for q in unique):
            unique.append(p)
    axes = [i for i in range(3) if i != axis]
    centre = [sum(p[i] for p in unique) / len(unique) for i in axes]
    unique.sort(key=lambda p: math.atan2(p[axes[1]] - centre[1], p[axes[0]] - centre[0]))
    return [(p[axes[0]], p[axes[1]]) for p in unique]
