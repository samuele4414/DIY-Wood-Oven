"""Read actual FDS 6.11.1 results for the oven viewer, without fdsreader.

Format contract: Source/dump.f90, tag FDS-6.11.1, lines 1075-1160,
2224-2248 and 6264-6267; Source/read.f90 lines 13647-13662 and
15927-15963; FDS User Guide section 27.9. An uncompressed structured
slice has three 30-byte string records, six int32 bounds, then repeated
float32 time and float32 field records. Four-byte Fortran record markers
surround every payload. Bounds are inclusive; I varies fastest.

SMV SLCF/SLCC entries provide mesh, filename and labels; TRNX/Y/Z contain
actual mesh-node coordinates. VECTOR produces separate U/V/W slices.
Gas MASS FLOW is an integral in the positive global coordinate direction;
IOR does not reverse its sign. Negative Y at this oven's mouth is outward.
CSV row one contains units, row two quoted device IDs, then numerical rows.

Only main() with the explicit --output option writes files. Completion
requires normal solver success AND actual recorded time reaching T_END.
Missing measurements are omitted, never replaced by estimated values.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
from pathlib import Path
from typing import Any

import numpy as np

try:
    from .fds_writer import inside_plan, roof_height
except ImportError:
    from fds_writer import inside_plan, roof_height


NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][-+]?\d+)?"


def _number(value: str) -> float:
    return float(value.replace("D", "E").replace("d", "e"))


def _record(stream, endian: str) -> bytes | None:
    marker = stream.read(4)
    if not marker:
        return None
    if len(marker) != 4:
        raise EOFError("incomplete Fortran record marker")
    size = struct.unpack(endian + "i", marker)[0]
    if size < 0 or size > 1_000_000_000:
        raise ValueError(f"unsupported Fortran record length: {size}")
    payload = stream.read(size)
    trailer = stream.read(4)
    if len(payload) != size or len(trailer) != 4:
        raise EOFError("incomplete Fortran record payload")
    if trailer != marker:
        raise ValueError("Fortran record length markers disagree")
    return payload


def read_slice(path: str | Path) -> dict[str, Any]:
    """Read a standard .sf, retaining complete frames from an active run."""
    path = Path(path)
    with path.open("rb") as stream:
        first = stream.read(4)
        endian = "<" if first == struct.pack("<i", 30) else ">"
        if first != struct.pack(endian + "i", 30):
            raise ValueError(f"{path.name}: not an uncompressed structured slice")
        stream.seek(0)
        labels = []
        for _ in range(3):
            payload = _record(stream, endian)
            if payload is None or len(payload) != 30:
                raise ValueError("slice label must be exactly 30 bytes")
            labels.append(payload.decode("ascii", errors="replace").strip(" \x00"))
        payload = _record(stream, endian)
        if payload is None or len(payload) != 24:
            raise ValueError("slice must have six int32 bounds")
        bounds = tuple(struct.unpack(endian + "6i", payload))
        shape = tuple(bounds[2 * n + 1] - bounds[2 * n] + 1 for n in range(3))
        if min(shape) < 1:
            raise ValueError("reversed slice bounds")
        count = int(np.prod(shape))
        times, fields = [], []
        truncated = False
        while True:
            try:
                timestamp = _record(stream, endian)
                if timestamp is None:
                    break
                if len(timestamp) != 4:
                    raise ValueError("slice time must be float32")
                payload = _record(stream, endian)
                if payload is None:
                    raise EOFError("missing slice frame")
                if len(payload) != 4 * count:
                    raise ValueError("slice data length disagrees with bounds")
                time = struct.unpack(endian + "f", timestamp)[0]
                if not np.isfinite(time):
                    raise ValueError("non-finite slice time")
                field = np.frombuffer(payload, dtype=endian + "f4").reshape(shape, order="F")
                times.append(time)
                fields.append(field)
            except EOFError:
                truncated = True
                break
    return {
        "quantity": labels[0], "short_name": labels[1], "units": labels[2],
        "bounds": bounds, "times": np.asarray(times, dtype=float),
        "values": np.stack(fields) if fields else np.empty((0,) + shape),
        "truncated": truncated,
    }


def read_smv(path: str | Path) -> dict[str, Any]:
    """Read structured slice references and their nonuniform grid coordinates."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    meshes: dict[int, dict[str, Any]] = {}
    slices = []
    mesh_id = 0
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r"^GRID(?:\s|$)", line):
            mesh_id += 1
            meshes[mesh_id] = {"ijk": tuple(map(int, lines[i + 1].split()[:3]))}
            i += 2
            continue
        if line in ("TRNX", "TRNY", "TRNZ") and mesh_id:
            axis = "XYZ".index(line[-1])
            transformations = int(lines[i + 1].strip())
            start = i + 2 + transformations
            count = meshes[mesh_id]["ijk"][axis] + 1
            coordinates = np.empty(count, dtype=float)
            for row in lines[start:start + count]:
                index, value = row.split()[:2]
                coordinates[int(index)] = _number(value)
            meshes[mesh_id][line[-1].lower()] = coordinates
            i = start + count
            continue
        match = re.match(r"^(SLCF|SLCC)\s+(\d+)(?:\s|$)", line)
        if match:
            if i + 4 >= len(lines):
                break
            slices.append({
                "mesh": int(match[2]), "cell_centered": match[1] == "SLCC",
                "filename": lines[i + 1].strip(),
                "quantity": lines[i + 2].strip(),
                "short_name": lines[i + 3].strip(),
                "units": lines[i + 4].strip(),
            })
            i += 5
            continue
        i += 1
    return {"meshes": meshes, "slices": slices}


def read_csv(path: str | Path) -> dict[str, Any]:
    """Parse FDS's two CSV header rows, including quoted labels and D exponents."""
    with Path(path).open(encoding="utf-8-sig", errors="replace", newline="") as stream:
        reader = csv.reader(stream)
        units = next(reader, [])
        labels = next(reader, [])
        units = [x.strip() for x in units]
        labels = [x.strip() for x in labels]
        if not labels:
            return {"units": {}, "columns": {}}
        if len(set(labels)) != len(labels):
            raise ValueError("duplicate CSV column IDs")
        rows = []
        for row in reader:
            if not row or len(row) != len(labels):
                continue
            try:
                rows.append([_number(x.strip()) for x in row])
            except ValueError:
                continue
    values = np.asarray(rows, dtype=float).reshape((-1, len(labels)))
    return {
        "units": dict(zip(labels, units)),
        "columns": {name: values[:, i] for i, name in enumerate(labels)},
        "source": Path(path).name,
    }


def _ordered(times: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    finite = np.isfinite(times)
    times, values = np.asarray(times)[finite], np.asarray(values)[finite]
    order = np.argsort(times, kind="stable")
    times, values = times[order], values[order]
    # A restart/event can repeat time: keep the final recorded sample.
    keep = np.r_[times[1:] != times[:-1], True] if len(times) else np.array([], dtype=bool)
    return times[keep], values[keep]


def time_mean(
    times: np.ndarray, values: np.ndarray, start: float, end: float,
) -> tuple[np.ndarray, list[float], int]:
    """Trapezoidal time mean; clip to recorded support and never extrapolate."""
    times, values = _ordered(times, values)
    if not len(times):
        raise ValueError("no recorded samples")
    lo, hi = max(float(times[0]), start), min(float(times[-1]), end)
    if hi < lo:
        raise ValueError("no samples in requested time window")
    query = np.unique(np.r_[lo, times[(times > lo) & (times < hi)], hi])
    sampled = []
    for t in query:
        right = min(int(np.searchsorted(times, t)), len(times) - 1)
        if times[right] == t or right == 0:
            sampled.append(values[right])
        else:
            left = right - 1
            fraction = (t - times[left]) / (times[right] - times[left])
            sampled.append(values[left] * (1 - fraction) + values[right] * fraction)
    stacked = np.asarray(sampled, dtype=float)
    if hi == lo:
        return stacked[0], [lo, hi], 1
    weights = np.diff(query).reshape((-1,) + (1,) * (stacked.ndim - 1))
    mean = np.sum((stacked[:-1] + stacked[1:]) * .5 * weights, axis=0) / (hi - lo)
    return mean, [lo, hi], len(query)


def _input_text(case: dict, run_dir: Path, metadata: dict) -> str:
    candidates = [run_dir / f"{case['id']}.fds"]
    if metadata.get("fds_input"):
        candidates.append(Path(metadata["fds_input"]))
    for path in candidates:
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    return ""


def _blocks(text: str, kind: str) -> list[str]:
    # Current writer emits one namelist per line and no slash inside strings.
    return re.findall(r"&" + kind + r"\b(.*?)/", text, flags=re.I | re.S)


def _bounds(block: str) -> tuple[float, ...] | None:
    match = re.search(r"\bXB\s*=\s*(" + NUMBER + r"(?:\s*,\s*" + NUMBER + r"){5})", block, re.I)
    return tuple(_number(x) for x in match[1].split(",")) if match else None


def _status(case: dict, run_dir: Path, metadata: dict, text: str) -> tuple[dict, list[str]]:
    warnings = []
    run_status = {}
    try:
        run_status = json.loads((run_dir / "run_status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    target = None
    for block in _blocks(text, "TIME"):
        match = re.search(r"\bT_END\s*=\s*(" + NUMBER + r")", block, re.I)
        if match:
            target = _number(match[1])
    if target is None:
        value = metadata.get("duration_s", run_status.get("duration_requested_s"))
        if value is not None:
            target = float(value)
    logs = []
    for path in [run_dir / f"{case['id']}.out", run_dir / "solver.log"]:
        if path.is_file():
            logs.append(path.read_text(encoding="utf-8", errors="replace"))
    log = "\n".join(logs)
    times = [_number(x) for x in re.findall(
        r"(?:Total Time|Simulation Time)\s*:\s*(" + NUMBER + r")\s*s", log, re.I,
    )]
    actual = max(times) if times else None
    terminal_messages = re.findall(r"^\s*STOP:.*$", log, re.I | re.M)
    normal_success = bool(terminal_messages and re.fullmatch(
        r"\s*STOP:\s*FDS completed successfully(?:\s*(?:\(.*\))?)?\s*",
        terminal_messages[-1], re.I,
    ))
    failed = bool(re.search(
        r"^\s*(?:ERROR(?:\(\d+\)|:)|STOP:\s*FDS.*(?:numerical instability|error))", log, re.I | re.M,
    )) or run_status.get("returncode") not in (None, 0)
    reached = actual is not None and target is not None and actual >= target - 0.005
    if normal_success and reached and not failed:
        status = "completed"
    elif failed or run_status.get("status") in ("failed", "timeout"):
        status = run_status.get("status") if run_status.get("status") == "timeout" else "failed"
    elif run_status.get("status") == "running":
        status = "running"
    elif log or run_status:
        status = "incomplete"
    else:
        status = "generated" if text else "not_started"
    if normal_success and not reached:
        warnings.append("Solver success exists but recorded final time does not establish T_END.")
    return {
        "status": status, "time_s": actual, "duration_requested_s": target,
        "normal_solver_success": normal_success, "reached_requested_end": reached,
    }, warnings


def _gas_mask(case: dict, x: np.ndarray, y: np.ndarray, z: float,
              metadata: dict, text: str, include_vestibule: bool) -> np.ndarray:
    mask = np.zeros((len(y), len(x)), dtype=bool)
    floor = float(metadata.get("resolved", {}).get("floor_top_m", 0.0))
    front = float(case.get("front_extension", 0))
    mouth_cx = float(case.get("mouth_center_x", case["width"] / 2))
    for j, yy in enumerate(y):
        for i, xx in enumerate(x):
            main = inside_plan(case, float(xx), float(yy)) and floor < z < roof_height(case, float(xx), float(yy))
            vestibule = (
                include_vestibule and -front <= yy < 0
                and abs(xx - mouth_cx) < float(case["mouth_width"]) / 2
                and floor < z < float(case["mouth_height"])
            )
            mask[j, i] = main or vestibule
    # Exact generated voxel solids/pizzas override the ideal display outline.
    for block in _blocks(text, "OBST"):
        xb = _bounds(block)
        if xb and xb[4] - 1e-8 <= z <= xb[5] + 1e-8:
            rows = (y >= xb[2] - 1e-8) & (y <= xb[3] + 1e-8)
            cols = (x >= xb[0] - 1e-8) & (x <= xb[1] + 1e-8)
            mask[np.ix_(rows, cols)] = False
    return mask


def _json_matrix(values: np.ndarray, mask: np.ndarray) -> list[list[float | None]]:
    return [[float(value) if valid and np.isfinite(value) else None
             for value, valid in zip(row, good)] for row, good in zip(values, mask)]


def _plane(case: dict, run_dir: Path, metadata: dict, text: str,
           start: float, end: float, include_vestibule: bool) -> tuple[dict | None, list[str]]:
    warnings = []
    smv_path = run_dir / f"{case['id']}.smv"
    if not smv_path.is_file():
        return None, ["No Smokeview manifest; no measured slice displayed."]
    manifest = read_smv(smv_path)
    candidates = []
    for ref in manifest["slices"]:
        if ref["quantity"].upper() != "TEMPERATURE":
            continue
        path = Path(ref["filename"])
        if not path.is_absolute():
            path = run_dir / path
        if not path.is_file():
            continue
        data = read_slice(path)
        bounds = data["bounds"]
        if bounds[4] == bounds[5] and bounds[0] < bounds[1] and bounds[2] < bounds[3] and len(data["times"]):
            mesh = manifest["meshes"].get(ref["mesh"], {})
            if all(axis in mesh for axis in ("x", "y", "z")):
                candidates.append((ref, data, mesh))
    if not candidates:
        return None, ["No completed horizontal temperature slice frames available."]
    # Current writer requests one horizontal plane. Prefer z closest to 0.10 m.
    def plane_z(candidate):
        ref, data, mesh = candidate
        k = data["bounds"][4]
        return .5 * (mesh["z"][k - 1] + mesh["z"][k]) if ref["cell_centered"] else mesh["z"][k]
    ref, data, mesh = min(candidates, key=lambda item: abs(plane_z(item) - .10))
    z = float(plane_z((ref, data, mesh)))
    bounds = data["bounds"]
    selections, coordinates = [], []
    for axis, label in enumerate(("x", "y", "z")):
        lo, hi = bounds[axis * 2:axis * 2 + 2]
        index = np.arange(lo, hi + 1)
        first = 1 if ref["cell_centered"] and lo < hi else 0
        selections.append(slice(first, None))
        index = index[first:]
        if ref["cell_centered"]:
            if np.any(index < 1):
                raise ValueError("cell-centered slice has invalid physical cell index")
            coordinates.append((mesh[label][index - 1] + mesh[label][index]) * .5)
        else:
            coordinates.append(mesh[label][index])
    x, y = coordinates[:2]
    xkeep = (x >= 0) & (x <= float(case["width"]))
    ykeep = (y >= (-float(case.get("front_extension", 0)) if include_vestibule else 0)) & (y <= float(case["depth"]))
    x, y = x[xkeep], y[ykeep]
    mask = _gas_mask(case, x, y, z, metadata, text, include_vestibule)
    mean, interval, samples = time_mean(data["times"], data["values"], start, end)

    def horizontal(values):
        return values[tuple(selections)][:, :, 0].T[np.ix_(ykeep, xkeep)]

    result = {
        "x": x.tolist(), "y": y.tolist(), "z": z,
        "temperature_C": _json_matrix(horizontal(mean), mask),
        "mean_window_s": interval, "sample_count": samples,
        "source_file": ref["filename"], "cell_centered": ref["cell_centered"],
        "includes_vestibule": include_vestibule,
    }
    if samples < 2:
        warnings.append("Temperature slice has one sample; this is a snapshot, not a time mean.")
    if data["truncated"]:
        warnings.append("Incomplete trailing temperature slice frame ignored.")
    for quantity, key in (("U-VELOCITY", "u_m_s"), ("V-VELOCITY", "v_m_s"), ("W-VELOCITY", "w_m_s")):
        for velocity_ref in manifest["slices"]:
            if (velocity_ref["quantity"].upper() != quantity or velocity_ref["mesh"] != ref["mesh"]
                    or velocity_ref["cell_centered"] != ref["cell_centered"]):
                continue
            path = Path(velocity_ref["filename"])
            if not path.is_absolute():
                path = run_dir / path
            if not path.is_file():
                continue
            velocity = read_slice(path)
            if velocity["bounds"] != bounds or not len(velocity["times"]):
                continue
            average, velocity_window, _ = time_mean(velocity["times"], velocity["values"], *interval)
            if not np.allclose(velocity_window, interval, atol=1e-5, rtol=0):
                warnings.append(f"{quantity} omitted: recorded time window differs from temperature.")
                break
            result[key] = _json_matrix(horizontal(average), mask)
            break
    return result, warnings


def summarize_run(case: dict, run_dir: str | Path, metadata: dict, window_s: float = 10,
                  *, include_vestibule: bool = True) -> dict[str, Any]:
    """Return JSON-ready measurements; API invocation never writes files."""
    if not np.isfinite(window_s) or window_s <= 0:
        raise ValueError("window_s must be positive and finite")
    run_dir = Path(run_dir)
    text = _input_text(case, run_dir, metadata)
    status, warnings = _status(case, run_dir, metadata, text)
    result = {
        "case_id": case["id"], **status, "metrics": {}, "metrics_window_s": {},
        "traces": {}, "window_comparison": {},
        "method": "Actual FDS output; clipped time window, linear endpoint interpolation and trapezoidal means.",
        "analysis_warnings": warnings,
    }
    if status["status"] != "completed":
        warnings.append("Run has not met the completion criteria; available measurements describe a partial run.")
    tables = {}
    for suffix in ("devc", "hrr"):
        path = run_dir / f"{case['id']}_{suffix}.csv"
        if path.is_file():
            try:
                tables[suffix] = read_csv(path)
            except (OSError, ValueError) as exc:
                warnings.append(f"{path.name}: {exc}")
    measured_times = []
    for table in tables.values():
        times = table["columns"].get("Time", np.empty(0))
        measured_times.extend(times[np.isfinite(times)].tolist())
    end = status["time_s"]
    if end is None and measured_times:
        end = max(measured_times)
        result["time_s"] = end
    if end is None:
        result["mean_window_s"] = None
        warnings.append("No actual simulation timestamps available.")
        return result
    start = max(0.0, end - window_s)
    result["mean_window_s"] = [start, end]
    device = tables.get("devc", {"columns": {}, "units": {}})
    # Negative-only mouth flow retains its negative sign in the FDS file.
    mappings = {
        "mouth_out_kg_s": (("mouth_outward_y_negative",), -1.0, "kg/s"),
        "mouth_in_kg_s": (("mouth_inward_y_positive",), 1.0, "kg/s"),
        "mouth_net_y_kg_s": (("mouth_net_y", "mouth_flow"), 1.0, "kg/s"),
        "flue_out_kg_s": (("flue_outward_z_positive",), 1.0, "kg/s"),
        "flue_net_z_kg_s": (("flue_net_z", "flue_flow"), 1.0, "kg/s"),
        "mouth_soot_out_kg_s": (("mouth_soot_outward_negative",), -1.0, "kg/s"),
        "flue_soot_out_kg_s": (("flue_soot_outward_positive",), 1.0, "kg/s"),
    }

    def trace(table, column, key, factor, unit):
        times, values = _ordered(table["columns"]["Time"], table["columns"][column])
        valid = np.isfinite(values)
        times, values = times[valid], values[valid] * factor
        result["traces"][key] = {
            "time_s": times.tolist(), "values": values.tolist(), "unit": unit,
            "source": table.get("source"), "column": column,
        }
        # Compare two full consecutive measured five-second windows. A
        # difference is evidence, not a stationarity/convergence pass or fail.
        if len(times) >= 2 and times[-1] - times[0] >= 10:
            stop = float(times[-1])
            previous, previous_window, _ = time_mean(times, values, stop - 10, stop - 5)
            recent, recent_window, _ = time_mean(times, values, stop - 5, stop)
            previous, recent = float(previous), float(recent)
            delta = recent - previous
            result["window_comparison"][key] = {
                "previous_window_s": previous_window, "recent_window_s": recent_window,
                "previous_mean": previous, "recent_mean": recent, "delta": delta,
                "relative_delta": delta / abs(previous) if abs(previous) > 1e-12 else None,
                "unit": unit,
            }

    def metric(table, column, key, factor=1.0, unit=None):
        columns = table["columns"]
        if column not in columns or "Time" not in columns or not len(columns["Time"]):
            return False
        if unit and table["units"].get(column, "").replace(" ", "") != unit:
            warnings.append(f"{column} omitted: unexpected units {table['units'].get(column)!r}.")
            return False
        try:
            average, interval, samples = time_mean(columns["Time"], columns[column], start, end)
        except ValueError as exc:
            warnings.append(f"{column}: {exc}")
            return False
        value = float(average) * factor
        if not np.isfinite(value):
            warnings.append(f"{column} mean omitted: non-finite measured values.")
            return False
        result["metrics"][key] = value
        result["metrics_window_s"][key] = interval
        trace(table, column, key, factor, unit or table["units"].get(column, ""))
        if samples < 2:
            warnings.append(f"{column} has one sample; reported value is not a time mean.")
        return True

    for key, (columns, factor, unit) in mappings.items():
        for column in columns:
            if metric(device, column, key, factor, unit):
                break
    mouth_soot = result["metrics"].get("mouth_soot_out_kg_s")
    flue_soot = result["metrics"].get("flue_soot_out_kg_s")
    if mouth_soot is not None and flue_soot is not None:
        mouth_window = result["metrics_window_s"]["mouth_soot_out_kg_s"]
        flue_window = result["metrics_window_s"]["flue_soot_out_kg_s"]
        shared = np.allclose(mouth_window, flue_window, rtol=0, atol=1e-7)
        duration = mouth_window[1] - mouth_window[0]
        total = mouth_soot + flue_soot
        if shared and duration > 0 and min(mouth_soot, flue_soot) >= 0 and total > 0:
            key = "soot_flue_fraction_of_measured_exits"
            result["metrics"][key] = flue_soot / total
            result["metrics_window_s"][key] = mouth_window
            result["soot_exit_proxy"] = {
                "definition": "Mean outward flue soot mass flow divided by mean outward flue plus mouth soot mass flows.",
                "mean_window_s": mouth_window,
                "interpretation": (
                    "Share of modelled soot leaving through these two measured planes during the same interval. "
                    "Not a fraction of generated soot: storage, deposition, re-entry and other exits are not accounted for. "
                    "Not a prediction of real wood-smoke emissions or capture efficiency."
                ),
            }
        elif not shared:
            warnings.append("Soot exit share omitted: mouth and flue averages cover different measured intervals.")
    hrr = tables.get("hrr", {"columns": {}, "units": {}})
    if not metric(hrr, "HRR", "hrr_kw_mean", unit="kW"):
        metric(device, "HRR", "hrr_kw_mean", unit="kW")
    prescribed = metadata.get("resolved", {}).get("hrr_kw_gross_prescribed")
    measured = result["metrics"].get("hrr_kw_mean")
    if prescribed is not None and measured is not None and float(prescribed) > 0:
        relative = (measured - float(prescribed)) / float(prescribed)
        result["hrr_comparison"] = {
            "prescribed_kw": float(prescribed), "measured_mean_kw": measured,
            "relative_difference": relative, "deviation_above_10_percent": abs(relative) > .10,
            "mean_window_s": result["metrics_window_s"]["hrr_kw_mean"],
            "prescribed_source": "metadata.resolved.hrr_kw_gross_prescribed",
        }
        if abs(relative) > .10:
            warnings.append(
                "Measured HRR differs by more than 10% from the prescribed source. "
                "Ramp/transient behaviour, oxygen limitation or incomplete combustion may contribute; "
                "HRR alone does not establish the cause."
            )
    pizza_temperatures = []
    probe_positions = {}
    for block in _blocks(text, "DEVC"):
        identity = re.search(r"\bID\s*=\s*['\"](pizza_\d+_gas_temp)['\"]", block, re.I)
        xyz = re.search(r"\bXYZ\s*=\s*(" + NUMBER + r"(?:\s*,\s*" + NUMBER + r"){2})", block, re.I)
        if identity and xyz:
            probe_positions[identity[1]] = [_number(x) for x in xyz[1].split(",")]
    for index, _ in enumerate(case.get("pizza_centers", []), 1):
        column = f"pizza_{index}_gas_temp"
        key = f"pizza_{index}_gas_temperature_C"
        measured_probe = metric(device, column, key, unit="C")
        pizza_temperatures.append(result["metrics"].pop(key) if measured_probe else None)
    if any(value is not None for value in pizza_temperatures):
        result["metrics"]["pizza_gas_temperature_C"] = pizza_temperatures
        result["pizza_gas_probes"] = [
            {"id": f"pizza_{i}_gas_temp", "xyz_m": probe_positions.get(f"pizza_{i}_gas_temp")}
            for i in range(1, len(pizza_temperatures) + 1)
        ]
        if len(pizza_temperatures) > 1 and all(value is not None for value in pizza_temperatures):
            result["metrics"]["pizza_gas_temperature_spread_C"] = max(pizza_temperatures) - min(pizza_temperatures)
        result["gas_uniformity_proxy"] = (
            "Maximum minus minimum of the measured mean gas temperatures at the recorded probe locations. "
            "This compares local gas exposure, not pizza temperatures, heat flux, cooking time or doneness."
        )
    try:
        plane, notes = _plane(case, run_dir, metadata, text, start, end, include_vestibule)
        warnings.extend(notes)
        if plane is not None:
            result["slice"] = plane
    except (OSError, ValueError, IndexError, KeyError, EOFError) as exc:
        warnings.append(f"Measured slice unavailable: {exc}")
    warnings.append("Gas temperatures above pizzas do not predict pizza temperature or cooking time.")
    warnings.append("Short prescribed-fire CFD run; no mesh-convergence or experimental validation is implied.")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--window", type=float, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    case = json.loads((args.run_dir / "case.json").read_text(encoding="utf-8"))
    metadata = json.loads((args.run_dir / f"{case['id']}_metadata.json").read_text(encoding="utf-8"))
    result = summarize_run(case, args.run_dir, metadata, args.window)
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)


if __name__ == "__main__":
    main()
