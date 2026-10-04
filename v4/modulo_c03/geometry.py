"""Nominal cold-module envelopes; generic CAD/mesh description in millimetres."""
import math


def parts(cfg, result, module=0):
    """Boxes/rings are deliberately not detailed components or machining solids."""
    x, y = result["packaging"]["modules"][module]["centre_xy_mm"]
    mx, my = result["packaging"]["modules"][module]["motor_centre_xy_mm"]
    top = result["packaging"]["tray_top_z_mm"]
    bottom = result["packaging"]["cassette_bottom_top_z_mm"][0]
    output = []

    def box(name, bounds, group="custom", hole=None):
        output.append({"name": name, "shape": "box", "bounds": bounds, "hole_radius_mm": hole, "hole_xy": [x, y], "group": group})

    def ring(name, cx, cy, outer, inner, z0, z1, group):
        output.append({"name": name, "shape": "ring", "xy": [cx, cy], "outer_radius_mm": outer, "inner_radius_mm": inner, "z": [z0, z1], "group": group})

    box("vassoio_RISERVA", [x - 120, x + 120, y - 90, y + 90, bottom, top])
    ring("albero12_solo_tratto_freddo_RISERVA", x, y, 6, 0, *cfg["shaft_z_range_mm"], "shaft")
    ring("cartuccia46_sedi_NON_quotate", x, y, 23, 16, cfg["cartridge_top_z_mm"] - 45, cfg["cartridge_top_z_mm"], "housing")
    for i, z in enumerate(cfg["bearing_centres_z_mm"]):
        ring(f"7201_{i + 1}_INVILUPPO_NON_CAD_SKF", x, y, 16, 6, z - 5, z + 5, "bearing")
    box("piastra_cartuccia_RISERVA", [x - 32, x + 32, y - 32, y + 32, *cfg["cartridge_plate_z_range_mm"]], hole=7)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = x + sx * 27, y + sy * 27
            box(f"supporto_cart_{sx}_{sy}_RISERVA", [px - 3, px + 3, py - 3, py + 3, top, cfg["cartridge_plate_z_range_mm"][0]])
    face = cfg["motor_output_face_z_mm"]
    box("piastra_FACCIA_motore_RISERVA", [mx - 30, mx + 30, my - 30, my + 30, face, face + cfg["motor_face_plate_mm"]], hole=11.5)
    output[-1]["hole_xy"] = [mx, my]
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = mx + sx * 26, my + sy * 26
            box(f"montante_motore_{sx}_{sy}_RISERVA", [px - 3, px + 3, py - 3, py + 3, top, face])
    z0 = cfg["pulley_bottom_z_mm"]
    hub_top = z0 + cfg["pulley_hub_extension_mm"]
    for label, cx, cy, flange, hub, inner in (("16", mx, my, 16, 9, 4), ("32", x, y, 27, 19, 6)):
        ring(f"T5_{label}_mozzo_INVILUPPO", cx, cy, hub, inner, z0, hub_top, "pulley")
        ring(f"T5_{label}_flange_INVILUPPO_senza_denti", cx, cy, flange, inner, hub_top, z0 + 21, "pulley")
    box("schermo_solidale_cassetta_RISERVA", [x - 120, x + 120, y - 90, y + 90, *cfg["shield_z_range_mm"]], "shield", 9)
    return output


COLOURS = {"custom": "#647d8b", "shaft": "#dbb04d", "housing": "#4c7788", "bearing": "#af728b", "pulley": "#b9c7cc", "shield": "#9ca9b1", "supplier_motor": "#357c9c", "belt": "#35444b"}


def mesh(part_list, segments=32):
    faces = []
    def add(points, part):
        faces.append({"points": [list(p) for p in points], "group": part["group"], "name": part["name"], "colour": COLOURS[part["group"]]})
    for p in part_list:
        if p["shape"] == "box":
            a, b, c, d, e, f = p["bounds"]
            vertices = [(a, c, e), (b, c, e), (b, d, e), (a, d, e), (a, c, f), (b, c, f), (b, d, f), (a, d, f)]
            for indices in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                add([vertices[i] for i in indices], p)
            r = p.get("hole_radius_mm")
            if r:
                cx, cy = p["hole_xy"]
                # Radial subdivision to rectangle perimeter leaves a true hole.
                corner_angles = [math.atan2(y - cy, x - cx) % math.tau for x in (a, b) for y in (c, d)]
                all_angles = sorted(set([math.tau * i / segments for i in range(segments)] + corner_angles))
                for angle0, angle1 in zip(all_angles, all_angles[1:] + [all_angles[0] + math.tau]):
                    angles = [angle0, angle1]
                    outside, inside = [], []
                    for angle in angles:
                        ux, uy = math.cos(angle), math.sin(angle)
                        distance = min((b - cx if ux >= 0 else a - cx) / ux if abs(ux) > 1e-9 else math.inf,
                                       (d - cy if uy >= 0 else c - cy) / uy if abs(uy) > 1e-9 else math.inf)
                        outside.append((cx + distance * ux, cy + distance * uy))
                        inside.append((cx + r * ux, cy + r * uy))
                    for z in (e, f):
                        add([(*outside[0], z), (*outside[1], z), (*inside[1], z), (*inside[0], z)], p)
                    add([(*inside[0], e), (*inside[1], e), (*inside[1], f), (*inside[0], f)], p)
            else:
                for indices in ((3, 2, 1, 0), (4, 5, 6, 7)):
                    add([vertices[i] for i in indices], p)
        else:
            cx, cy = p["xy"]
            ro, ri = p["outer_radius_mm"], p["inner_radius_mm"]
            z0, z1 = p["z"]
            for i in range(segments):
                a, b = math.tau * i / segments, math.tau * (i + 1) / segments
                out = [(cx + ro * math.cos(t), cy + ro * math.sin(t)) for t in (a, b)]
                inside = [(cx + ri * math.cos(t), cy + ri * math.sin(t)) for t in (a, b)]
                add([(*out[0], z0), (*out[1], z0), (*out[1], z1), (*out[0], z1)], p)
                for z in (z0, z1):
                    add([(*out[0], z), (*out[1], z), (*inside[1], z), (*inside[0], z)], p)
                if ri:
                    add([(*inside[0], z1), (*inside[1], z1), (*inside[1], z0), (*inside[0], z0)], p)
    return faces


def belt_mesh(result, module=0):
    """Pitch path visual only, not a tooth or elastic belt model."""
    drv = result["drive"]
    cx, cy = result["packaging"]["modules"][module]["centre_xy_mm"]
    mx, my = result["packaging"]["modules"][module]["motor_centre_xy_mm"]
    rs, rl, centre = drv["small_pitch_radius_mm"], drv["large_pitch_radius_mm"], drv["centre_distance_mm"]
    sign = 1 if cx > mx else -1
    angle = math.asin((rl - rs) / centre)
    # Local +X goes from the motor to the load; arcs joined by tangent lines.
    pts = []
    for i in range(33):
        a = math.pi / 2 + angle + (math.pi - 2 * angle) * i / 32
        pts.append([mx + sign * rs * math.cos(a), my + rs * math.sin(a)])
    for i in range(49):
        a = 3 * math.pi / 2 - angle + (math.pi + 2 * angle) * i / 48
        pts.append([cx + sign * rl * math.cos(a), cy + rl * math.sin(a)])
    z = -111.5
    return [{"name": "cinghia_PERCORSO_PRIMITIVO", "group": "belt", "colour": COLOURS["belt"], "points": [[*a, z - 5], [*b, z - 5], [*b, z + 5], [*a, z + 5]]} for a, b in zip(pts, pts[1:] + pts[:1])]
