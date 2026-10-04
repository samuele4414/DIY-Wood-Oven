"""Write preliminary FDS cases for comparative wood-oven flow screening.

This module intentionally models a prescribed, preheated operating condition.
It is not a combustion or pizza-baking model.  Geometry is voxelised on the
FDS mesh so the same input path works for polygonal and circular chambers.
"""

from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path
from typing import Any, Iterable


def inside_plan(case: dict[str, Any], x: float, y: float) -> bool:
    """Return whether a horizontal point lies in the specified cooking plan."""
    plan = case["plan"]
    if plan["kind"] == "circle":
        cx, cy = plan["center"]
        return (x - cx) ** 2 + (y - cy) ** 2 <= plan["radius"] ** 2 and y >= plan.get("clip_front", 0)
    points = plan["points"]
    inside = False
    j = len(points) - 1
    for i, (xi, yi) in enumerate(points):
        xj, yj = points[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def roof_height(case: dict[str, Any], x: float, y: float) -> float:
    """Interior vault height at a point inside the cooking plan."""
    roof = case["roof"]
    eave, peak = float(roof["eave"]), float(roof["peak"])
    plan = case["plan"]
    if roof["kind"] == "paraboloid" or plan["kind"] == "circle":
        if plan["kind"] == "circle":
            cx, cy = plan["center"]
            r = plan["radius"]
        else:
            cx, cy, r = case["width"] / 2, case["depth"] / 2, max(case["width"], case["depth"]) / 2
        q = min(1.0, ((x - cx) ** 2 + (y - cy) ** 2) / max(r * r, 1e-12))
        return eave + (peak - eave) * (1.0 - q)
    # Barrel: parabola across the local horizontal chord of the polygon.
    # Sampling left/right keeps it applicable to a trapezoid without a CAD kernel.
    step = max(case["width"] / 400, 0.001)
    left = x
    while inside_plan(case, left - step, y):
        left -= step
    right = x
    while inside_plan(case, right + step, y):
        right += step
    mid, half = (left + right) / 2, max((right - left) / 2, step)
    q = min(1.0, ((x - mid) / half) ** 2)
    return eave + (peak - eave) * (1.0 - q)


def _snap_down(value: float, dx: float) -> float:
    return math.floor(value / dx + 1e-9) * dx


def _snap_up(value: float, dx: float) -> float:
    return math.ceil(value / dx - 1e-9) * dx


def _fmt(value: float) -> str:
    return f"{value:.5f}".rstrip("0").rstrip(".")


def _point_in_disc(x: float, y: float, center: Iterable[float], diameter: float) -> bool:
    cx, cy = center
    return (x - cx) ** 2 + (y - cy) ** 2 <= (diameter / 2) ** 2


def write_case(
    case: dict[str, Any],
    out_dir: str | Path,
    cell_size: float = 0.025,
    duration: float = 30.0,
    flue_position: str = "front",
    hrr_kw: float = 18.75,
) -> dict[str, Any]:
    """Create one self-contained ``.fds`` input and its geometry metadata.

    ``flue_position`` is retained in metadata because the resolved geometry is
    determined by ``case['chimney']['center']``.  The caller can therefore
    compare any pickup layout without hidden coordinate changes.
    """
    if cell_size <= 0 or duration <= 0 or hrr_kw <= 0:
        raise ValueError("cell_size, duration and hrr_kw must be positive")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dx = float(cell_size)
    width, depth = float(case["width"]), float(case["depth"])
    front = float(case.get("front_extension", 0.08))
    mouth_w, mouth_h = float(case["mouth_width"]), float(case["mouth_height"])
    mouth_cx = float(case.get("mouth_center_x", width / 2))
    chimney = case["chimney"]
    ccx, ccy = map(float, chimney["center"])
    cr = float(chimney["diameter"]) / 2
    wall_cells = 1
    floor_cells = 1
    side_buffer, rear_buffer, top_buffer = 0.20, 0.18, 0.15
    x0, x1 = _snap_down(-side_buffer, dx), _snap_up(width + side_buffer, dx)
    y0, y1 = _snap_down(-front - side_buffer, dx), _snap_up(depth + rear_buffer, dx)
    chimney_base = mouth_h if flue_position == "front" else roof_height(case, ccx, ccy)
    outlet_height = float(chimney.get("outlet_height_m", chimney_base + float(chimney["height"])))
    ch = outlet_height - chimney_base
    if ch <= dx:
        raise ValueError("chimney outlet_height_m must be above the resolved pickup base")
    chimney_wall_temp = float(case.get("chimney_wall_temperature_C", 200.0))
    z0 = -dx  # physical cooking surface is z=0, not one voxel above it
    z1 = _snap_up(max(case["roof"]["peak"], chimney_base + ch) + top_buffer, dx)
    nx, ny, nz = round((x1 - x0) / dx), round((y1 - y0) / dx), round((z1 - z0) / dx)
    z_split = _snap_up(float(case["roof"]["peak"]) + 2 * dx, dx)
    ux0, ux1 = _snap_down(ccx - cr - 3 * dx, dx), _snap_up(ccx + cr + 3 * dx, dx)
    uy0, uy1 = _snap_down(ccy - cr - 3 * dx, dx), _snap_up(ccy + cr + 3 * dx, dx)
    unx, uny, unz = round((ux1 - ux0) / dx), round((uy1 - uy0) / dx), round((z1 - z_split) / dx)

    def xyz(i: int, j: int, k: int) -> tuple[float, float, float]:
        return x0 + (i + 0.5) * dx, y0 + (j + 0.5) * dx, z0 + (k + 0.5) * dx

    plan_xy = {(i, j): inside_plan(case, xyz(i, j, 0)[0], xyz(i, j, 0)[1]) for i in range(nx) for j in range(ny)}
    roof_xy = {(i, j): roof_height(case, xyz(i, j, 0)[0], xyz(i, j, 0)[1]) for (i, j), present in plan_xy.items() if present}

    def chamber_void(i: int, j: int, k: int) -> bool:
        x, y, z = xyz(i, j, k)
        # Main cooking chamber.
        if plan_xy.get((i, j), False) and z >= 0 and z < roof_xy[(i, j)]:
            return True
        # The front vestibule is deliberately only as wide/high as the mouth.
        if -front <= y < 0 and abs(x - mouth_cx) <= mouth_w / 2 and 0 <= z < mouth_h:
            return True
        # A round flue bore joins the cavity to the exterior. It is not an
        # imposed velocity inlet/outlet; all flow arises from buoyancy.
        if z >= chimney_base and z < chimney_base + ch + dx and (x - ccx) ** 2 + (y - ccy) ** 2 <= cr ** 2:
            return True
        return False

    void: set[tuple[int, int, int]] = set()
    # Restrict work to the oven/vestibule/chimney envelope rather than the air buffer.
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if chamber_void(i, j, k):
                    void.add((i, j, k))

    offsets = ((-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1))
    solid: set[tuple[int, int, int]] = set()
    for cell in void:
        for di, dj, dk in offsets:
            neighbour = cell[0] + di, cell[1] + dj, cell[2] + dk
            if not (0 <= neighbour[0] < nx and 0 <= neighbour[1] < ny and 0 <= neighbour[2] < nz) or neighbour in void:
                continue
            nxp, nyp, nzp = xyz(*neighbour)
            # Keep the mouth and flue top genuinely open to the exterior air
            # buffer. A shell cell here would silently cap the intended opening.
            mouth_exit = dj == -1 and nyp < -front and abs(nxp - mouth_cx) <= mouth_w / 2 and nzp < mouth_h
            flue_exit = dk == 1 and nzp >= chimney_base + ch and (nxp - ccx) ** 2 + (nyp - ccy) ** 2 <= cr ** 2
            if not (mouth_exit or flue_exit):
                solid.add(neighbour)
    # Add a second shell only to the chimney; a one-cell wall is adequate for
    # the preliminary prescribed-temperature screen and keeps the small laptop case tractable.
    for i, j, k in list(solid):
        x, y, z = xyz(i, j, k)
        if z >= chimney_base and (x - ccx) ** 2 + (y - ccy) ** 2 <= (cr + dx) ** 2:
            for di, dj, dk in offsets:
                q = i + di, j + dj, k + dk
                if 0 <= q[0] < nx and 0 <= q[1] < ny and 0 <= q[2] < nz and q not in void:
                    solid.add(q)

    def surface_ids(cell: tuple[int, int, int]) -> tuple[str, str, str, str, str, str]:
        i, j, k = cell
        names: list[str] = []
        for face, (di, dj, dk) in enumerate(offsets):
            q = i + di, j + dj, k + dk
            if q in void:
                # FDS face order is XMIN, XMAX, YMIN, YMAX, ZMIN, ZMAX.
                if face == 5:
                    names.append("FLOOR_HOT")
                elif xyz(i, j, k)[2] >= float(case["roof"]["peak"]) + dx:
                    names.append("CHIMNEY_INNER")
                else:
                    names.append("WALL_HOT")
            else:
                names.append("COLD_OUTER")
        return tuple(names)  # type: ignore[return-value]

    # Merge vertical voxel columns only where all six face treatments agree.
    by_column: dict[tuple[int, int], list[int]] = {}
    for i, j, k in solid:
        by_column.setdefault((i, j), []).append(k)
    obstacles: list[tuple[int, int, int, int, tuple[str, str, str, str, str, str]]] = []
    for (i, j), ks in by_column.items():
        ks.sort()
        start = previous = ks[0]
        signature = surface_ids((i, j, start))
        for k in ks[1:]:
            current = surface_ids((i, j, k))
            if k != previous + 1 or current != signature:
                obstacles.append((i, j, start, previous, signature))
                start, signature = k, current
            previous = k
        obstacles.append((i, j, start, previous, signature))

    # Burner is snapped to floor cells, which makes its prescribed HRR exact on the FDS grid.
    bx0, bx1, by0, by1 = map(float, case["burner_bounds"])
    bx0, bx1 = _snap_down(bx0, dx), _snap_up(bx1, dx)
    by0, by1 = _snap_down(by0, dx), _snap_up(by1, dx)
    burner_area = max((bx1 - bx0) * (by1 - by0), dx * dx)
    # FDS HRRPUA is expressed in kW/m²; hrr_kw is deliberately gross kW.
    hrrpua = hrr_kw / burner_area
    slices_z = min(max(0.10, 2 * dx), z1 - dx)
    xplane = _snap_down(width / 2, dx)
    yplane = _snap_down(depth / 2, dx)

    lines = [
        f"&HEAD CHID='{case['id']}', TITLE='Preheated prescribed-HRR oven screening: {case.get('label', case['id'])}' /",
        f"&MESH ID='MESH01', IJK={nx},{ny},{round((z_split-z0)/dx)}, XB={_fmt(x0)},{_fmt(x1)},{_fmt(y0)},{_fmt(y1)},{_fmt(z0)},{_fmt(z_split)} /",
        f"&MESH ID='MESH02', IJK={unx},{uny},{unz}, XB={_fmt(ux0)},{_fmt(ux1)},{_fmt(uy0)},{_fmt(uy1)},{_fmt(z_split)},{_fmt(z1)} /",
        "&TIME T_END=" + _fmt(duration) + " /",
        "&MISC TMPA=25. /",
        "&RADI RADIATION=.TRUE. /",
        "&REAC ID='WOOD_PROXY', FUEL='PROPANE', SOOT_YIELD=0.015, RADIATIVE_FRACTION=0.35 /",
        "&SURF ID='COLD_OUTER', TMP_FRONT=25. /",
        "&SURF ID='WALL_HOT', TMP_FRONT=500. /",
        "&SURF ID='FLOOR_HOT', TMP_FRONT=450. /",
        f"&SURF ID='CHIMNEY_INNER', TMP_FRONT={_fmt(chimney_wall_temp)} /",
        "&SURF ID='PIZZA_PREHEATED', TMP_FRONT=100. /",
        f"&SURF ID='BURNER', HRRPUA={_fmt(hrrpua)}, RAMP_Q='FIRE_RAMP' /",
        "&RAMP ID='FIRE_RAMP', T=0., F=0. /",
        "&RAMP ID='FIRE_RAMP', T=5., F=1. /",
        # Explicit external faces leave the shared MESH01/MESH02 interface
        # untouched; FDS couples the conformal, adjacent meshes automatically.
        f"&VENT XB={_fmt(x0)},{_fmt(x0)},{_fmt(y0)},{_fmt(y1)},{_fmt(z0)},{_fmt(z_split)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(x1)},{_fmt(x1)},{_fmt(y0)},{_fmt(y1)},{_fmt(z0)},{_fmt(z_split)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(x0)},{_fmt(x1)},{_fmt(y0)},{_fmt(y0)},{_fmt(z0)},{_fmt(z_split)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(x0)},{_fmt(x1)},{_fmt(y1)},{_fmt(y1)},{_fmt(z0)},{_fmt(z_split)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(x0)},{_fmt(x1)},{_fmt(y0)},{_fmt(y1)},{_fmt(z0)},{_fmt(z0)}, SURF_ID='COLD_OUTER' /",
        # MESH01 top is exterior except for the MESH02 footprint. Leaving these
        # four rectangles unspecified would create an artificial cold ceiling.
        f"&VENT XB={_fmt(x0)},{_fmt(ux0)},{_fmt(y0)},{_fmt(y1)},{_fmt(z_split)},{_fmt(z_split)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(ux1)},{_fmt(x1)},{_fmt(y0)},{_fmt(y1)},{_fmt(z_split)},{_fmt(z_split)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(ux0)},{_fmt(ux1)},{_fmt(y0)},{_fmt(uy0)},{_fmt(z_split)},{_fmt(z_split)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(ux0)},{_fmt(ux1)},{_fmt(uy1)},{_fmt(y1)},{_fmt(z_split)},{_fmt(z_split)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(ux0)},{_fmt(ux0)},{_fmt(uy0)},{_fmt(uy1)},{_fmt(z_split)},{_fmt(z1)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(ux1)},{_fmt(ux1)},{_fmt(uy0)},{_fmt(uy1)},{_fmt(z_split)},{_fmt(z1)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(ux0)},{_fmt(ux1)},{_fmt(uy0)},{_fmt(uy0)},{_fmt(z_split)},{_fmt(z1)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(ux0)},{_fmt(ux1)},{_fmt(uy1)},{_fmt(uy1)},{_fmt(z_split)},{_fmt(z1)}, SURF_ID='OPEN' /",
        f"&VENT XB={_fmt(ux0)},{_fmt(ux1)},{_fmt(uy0)},{_fmt(uy1)},{_fmt(z1)},{_fmt(z1)}, SURF_ID='OPEN' /",
    ]
    for i, j, k0, k1, faces in obstacles:
        xa, xb = x0 + i * dx, x0 + (i + 1) * dx
        ya, yb = y0 + j * dx, y0 + (j + 1) * dx
        za, zb = z0 + k0 * dx, z0 + (k1 + 1) * dx
        ids = ",".join(f"'{name}'" for name in faces)
        lines.append(f"&OBST XB={_fmt(xa)},{_fmt(xb)},{_fmt(ya)},{_fmt(yb)},{_fmt(za)},{_fmt(zb)}, SURF_ID6={ids} /")
    # Pizzas are fixed 25 mm voxel obstructions. The rotating discs remain flush
    # with the floor, so their rotation is handled by later exposure post-processing.
    pizza_rows = 0
    for pidx, center in enumerate(case.get("pizza_centers", []), 1):
        row_start: int | None = None
        for j in range(ny):
            xs = [i for i in range(nx) if _point_in_disc(*xyz(i, j, 0)[:2], center, float(case["pizza_diameter"]))]
            if not xs:
                continue
            for group_start in range(len(xs)):
                if group_start and xs[group_start] == xs[group_start - 1] + 1:
                    continue
                end = group_start
                while end + 1 < len(xs) and xs[end + 1] == xs[end] + 1:
                    end += 1
                xa, xb = x0 + xs[group_start] * dx, x0 + (xs[end] + 1) * dx
                ya, yb = y0 + j * dx, y0 + (j + 1) * dx
                lines.append(f"&OBST ID='PIZZA_{pidx}', XB={_fmt(xa)},{_fmt(xb)},{_fmt(ya)},{_fmt(yb)},0,{_fmt(dx)}, SURF_ID='PIZZA_PREHEATED' /")
                pizza_rows += 1
    lines.append(f"&VENT ID='FIRE', XB={_fmt(bx0)},{_fmt(bx1)},{_fmt(by0)},{_fmt(by1)},0,0, SURF_ID='BURNER' /")
    lines += [
        f"&DEVC ID='mouth_net_y', XB={_fmt(mouth_cx-mouth_w/2)},{_fmt(mouth_cx+mouth_w/2)},{_fmt(-front)},{_fmt(-front)},0,{_fmt(mouth_h)}, QUANTITY='MASS FLOW Y', SPATIAL_STATISTIC='AREA INTEGRAL' /",
        f"&DEVC ID='mouth_outward_y_negative', XB={_fmt(mouth_cx-mouth_w/2)},{_fmt(mouth_cx+mouth_w/2)},{_fmt(-front)},{_fmt(-front)},0,{_fmt(mouth_h)}, QUANTITY='MASS FLOW -', SPATIAL_STATISTIC='AREA INTEGRAL' /",
        f"&DEVC ID='mouth_inward_y_positive', XB={_fmt(mouth_cx-mouth_w/2)},{_fmt(mouth_cx+mouth_w/2)},{_fmt(-front)},{_fmt(-front)},0,{_fmt(mouth_h)}, QUANTITY='MASS FLOW +', SPATIAL_STATISTIC='AREA INTEGRAL' /",
        f"&DEVC ID='mouth_soot_outward_negative', XB={_fmt(mouth_cx-mouth_w/2)},{_fmt(mouth_cx+mouth_w/2)},{_fmt(-front)},{_fmt(-front)},0,{_fmt(mouth_h)}, QUANTITY='MASS FLOW -', SPEC_ID='SOOT', SPATIAL_STATISTIC='AREA INTEGRAL' /",
        f"&DEVC ID='flue_net_z', XB={_fmt(ccx-cr)},{_fmt(ccx+cr)},{_fmt(ccy-cr)},{_fmt(ccy+cr)},{_fmt(chimney_base+ch-dx)},{_fmt(chimney_base+ch-dx)}, QUANTITY='MASS FLOW Z', SPATIAL_STATISTIC='AREA INTEGRAL' /",
        f"&DEVC ID='flue_outward_z_positive', XB={_fmt(ccx-cr)},{_fmt(ccx+cr)},{_fmt(ccy-cr)},{_fmt(ccy+cr)},{_fmt(chimney_base+ch-dx)},{_fmt(chimney_base+ch-dx)}, QUANTITY='MASS FLOW +', SPATIAL_STATISTIC='AREA INTEGRAL' /",
        f"&DEVC ID='flue_soot_outward_positive', XB={_fmt(ccx-cr)},{_fmt(ccx+cr)},{_fmt(ccy-cr)},{_fmt(ccy+cr)},{_fmt(chimney_base+ch-dx)},{_fmt(chimney_base+ch-dx)}, QUANTITY='MASS FLOW +', SPEC_ID='SOOT', SPATIAL_STATISTIC='AREA INTEGRAL' /",
        f"&SLCF PBZ={_fmt(slices_z)}, QUANTITY='TEMPERATURE' /",
        f"&SLCF PBZ={_fmt(slices_z)}, QUANTITY='VELOCITY', VECTOR=.TRUE. /",
        f"&SLCF PBX={_fmt(xplane)}, QUANTITY='TEMPERATURE' /",
        f"&SLCF PBX={_fmt(xplane)}, QUANTITY='VELOCITY', VECTOR=.TRUE. /",
        f"&SLCF PBY={_fmt(yplane)}, QUANTITY='TEMPERATURE' /",
        "&DUMP DT_DEVC=1., DT_SLCF=2., DT_HRR=1. /",
    ]
    # Gas temperature immediately above each fixed pizza is a robust, point
    # diagnostic. Surface heat-flux gauges are deferred until their mesh-face
    # placement is independently validated for every voxelised layout.
    for pidx, (px, py) in enumerate(case.get("pizza_centers", []), 1):
        lines.append(f"&DEVC ID='pizza_{pidx}_gas_temp', XYZ={_fmt(px)},{_fmt(py)},0.1, QUANTITY='TEMPERATURE' /")
    lines.append("&TAIL /")
    fds_path = out / f"{case['id']}.fds"
    fds_path.write_text("\n".join(lines) + "\n", encoding="ascii")

    # Check that the staircase bore has at least one connected route from the
    # lower pickup to the top; a false result is a generator error, not a CFD result.
    bore = {c for c in void if xyz(*c)[2] >= chimney_base and (xyz(*c)[0] - ccx) ** 2 + (xyz(*c)[1] - ccy) ** 2 <= cr ** 2}
    starts = [c for c in bore if xyz(*c)[2] < chimney_base + dx]
    seen = set(starts)
    queue = deque(starts)
    while queue:
        c = queue.popleft()
        for di, dj, dk in offsets:
            q = c[0] + di, c[1] + dj, c[2] + dk
            if q in bore and q not in seen:
                seen.add(q)
                queue.append(q)
    reaches_top = any(xyz(*c)[2] >= chimney_base + ch - dx for c in seen)
    mouth_cells = [c for c in void if abs(xyz(*c)[1] + front) <= dx and abs(xyz(*c)[0] - mouth_cx) <= mouth_w/2 and xyz(*c)[2] < mouth_h]
    metadata = {
        "case_id": case["id"], "fds_input": str(fds_path), "cell_size_m": dx,
        "mesh": {"ijk": [nx, ny, nz], "xb": [x0, x1, y0, y1, z0, z1]},
        "meshes": [
            {"id": "MESH01", "ijk": [nx, ny, round((z_split-z0)/dx)], "xb": [x0, x1, y0, y1, z0, z_split]},
            {"id": "MESH02", "ijk": [unx, uny, unz], "xb": [ux0, ux1, uy0, uy1, z_split, z1]},
        ],
        "resolved": {"obstacle_columns": len(obstacles), "pizza_voxel_rows": pizza_rows,
                     "burner_bounds_m": [bx0, bx1, by0, by1], "burner_area_m2": burner_area,
                     "hrr_kw_gross_prescribed": hrr_kw, "hrrpua_kw_m2": hrrpua,
                     "mouth_open_area_m2": len(mouth_cells) * dx * dx,
                     "flue_bore_area_m2": len(starts) * dx * dx, "flue_connected_to_top": reaches_top,
                     "chimney_base_m": chimney_base, "chimney_outlet_height_m": outlet_height,
                     "chimney_effective_vertical_length_m": ch, "mesh_interface_height_m": z_split},
        "assumptions": [
            "Preheated fixed wall temperatures: inner roof/walls 500 C, floor 450 C, pizza 100 C; outer shell 25 C.",
            f"Chimney inner wall is prescribed {chimney_wall_temp:g} C above the vault, not 500 C along the full flue.",
            "Prescribed gross HRR wood proxy with propane stoichiometry and soot yield 0.015; not wood emissions or combustion validation.",
            "Radiation enabled; radiation fraction 0.35 is an assumed sensitivity input.",
            "Discs/pizzas are stationary CFD geometry; rotation is exposure post-processing/visualisation only.",
            "Voxel stair-step walls and round flue; results require mesh and physical validation before design use.",
            "Mass-flow signs: mouth +Y is inward, so outward flow is the negative component; flue +Z is outward.",
            "Two conformal adjacent meshes: full lower oven/exterior and a narrow upper chimney/exterior; their shared interface is not OPEN.",
            f"Layout label flue_position={flue_position}; physical pickup is case chimney.center.",
        ],
    }
    (out / f"{case['id']}_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
