"""Export completed home-PC results and optional video; never starts FDS."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import subprocess
import sys

from run_home import input_hash, load_campaign, output_progress

HERE = Path(__file__).resolve().parent
VISUALISER = HERE.parent / "v4_fire"
POINTS = ("C", "L", "R", "F", "B")


def read_probes(path, duration):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        lines = [row for row in csv.reader(stream) if row and any(v.strip() for v in row)]
    if len(lines) < 4:
        raise ValueError("DEVC output needs two headers and at least two samples")
    units, names = [[value.strip().strip('"') for value in row] for row in lines[:2]]
    if len(units) != len(names) or len(set(names)) != len(names) or "Time" not in names:
        raise ValueError("Invalid DEVC header")
    records = []
    for row in lines[2:]:
        if len(row) != len(names):
            raise ValueError("Incomplete DEVC row")
        values = [float(v.replace("D", "E").replace("d", "e")) for v in row]
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Non-finite DEVC sample")
        records.append(dict(zip(names, values)))
    times = [r["Time"] for r in records]
    if any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError("DEVC sample times must increase strictly")
    if abs(times[0]) > 1e-3 or abs(times[-1] - duration) > 1e-3:
        raise ValueError("DEVC data must cover the complete requested stage")
    return dict(zip(names, units)), records


def integrated(records, key):
    return sum((b["Time"] - a["Time"]) * (a[key] + b[key]) / 2
               for a, b in zip(records, records[1:]))


def report_for(stage_name, duration, units, records):
    first, final = records[0], records[-1]
    report = {"schema": 1, "stage": stage_name,
              "sample_count": len(records), "time_interval_s": [first["Time"], final["Time"]],
              "final_probes": {name: {"value": value, "unit": units[name]}
                               for name, value in final.items() if name != "Time"},
              "interpretation": "Point probes only. Values do not establish whether a pizza is cooked."}
    if stage_name != "bake":
        return report
    pizzas = []
    span = final["Time"] - first["Time"]
    for number in (1, 2):
        points = {}
        for point in POINTS:
            prefix = f"pizza_{number}_{point}_"
            expected = [prefix + quantity for quantity in ("rad", "conv", "net", "surface", "core", "bottom")]
            if any(name not in final for name in expected):
                raise ValueError(f"Missing pizza {number} point {point} heat/temperature probes")
            for quantity in ("rad", "conv", "net"):
                if units[prefix + quantity].replace(" ", "").replace("²", "2") != "kW/m2":
                    raise ValueError(f"Expected kW/m2 for {prefix + quantity}")
            for quantity in ("surface", "core", "bottom"):
                if units[prefix + quantity] not in ("C", "°C", "degC"):
                    raise ValueError(f"Expected Celsius for {prefix + quantity}")
            points[point] = {
                "time_mean_heat_flux_kW_m2": {q: integrated(records, prefix + q) / span for q in ("rad", "conv", "net")},
                "net_heat_flux_time_integral_kJ_m2": integrated(records, prefix + "net"),
                "final_temperature_C": {q: final[prefix + q] for q in ("surface", "core", "bottom")}}
        pizzas.append({"pizza": number, "points": points,
                       "final_temperature_range_across_five_probes_C": {
                           q: {"min": min(p["final_temperature_C"][q] for p in points.values()),
                               "max": max(p["final_temperature_C"][q] for p in points.values())}
                           for q in ("surface", "core", "bottom")}})
    report.update(pizzas=pizzas, integration="Trapezoidal integration using actual DEVC sample times.",
                  spatial_sampling="C=center, L=left, R=right, F=front, B=back; offsets 9 cm. These are five point probes, not whole-pizza area averages.",
                  heat_flux_sign="Signed FDS wall heat fluxes are retained without absolute-value conversion.")
    return report


def export_volumes(run, destination, step):
    sys.path.insert(0, str(VISUALISER))
    from export_volume import export
    export(run.resolve(), destination, step=step)


def export_stage(campaign, stage_name="bake", video=False):
    campaign, manifest = load_campaign(campaign)
    stage = manifest["stages"][stage_name]
    run = campaign / stage["directory"]
    status = json.loads((run / "run_status.json").read_text(encoding="utf-8"))
    progress = output_progress(run, stage["chid"], stage["duration_s"])
    if status.get("status") != "completed" or not progress["reached_end"]:
        raise ValueError("Only completed stages with normal STOP and full simulated duration can be exported")
    if status.get("input_sha256") and status["input_sha256"] != input_hash(run / stage["input"]):
        raise ValueError("Stage input changed after the completed run")
    units, records = read_probes(run / f"{stage['chid']}_devc.csv", stage["duration_s"])
    report = report_for(stage_name, stage["duration_s"], units, records)
    report.update(source_run=str(run.resolve()), input_sha256=status.get("input_sha256"),
                  config_sha256=manifest.get("config_sha256"))
    visualisation = run / "visualisation"
    export_volumes(run, visualisation, step=30 if stage_name == "preheat" else .5)
    report_path = run / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"3D data: {visualisation.resolve()}")
    print(f"Probe report: {report_path.resolve()}")
    if video:
        destination = run / "video"
        subprocess.run([sys.executable, str(VISUALISER / "render_video.py"), "--data", str(visualisation.resolve()),
                        "--output", str(destination.resolve())], check=True)
        print(f"Video: {destination.resolve()}")
    return report_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--stage", choices=["preheat", "bake"], default="bake")
    parser.add_argument("--video", action="store_true")
    args = parser.parse_args(argv)
    try:
        export_stage(args.campaign, args.stage, args.video)
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
