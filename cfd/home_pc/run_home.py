"""Portable, opt-in FDS runner. Without --execute this only inspects files."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
NUMBER = r"[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?"


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def input_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_status(directory, status):
    temporary = directory / "run_status.json.tmp"
    temporary.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    temporary.replace(directory / "run_status.json")


def output_progress(directory, chid, duration):
    """Require both a normal final STOP and the requested simulated duration."""
    output = directory / f"{chid}.out"
    text = output.read_text(errors="replace") if output.exists() else ""
    times = re.findall(r"Total Time:\s*(" + NUMBER + r")\s*s", text)
    current = float(times[-1].replace("D", "E").replace("d", "e")) if times else None
    stops = re.findall(r"^\s*STOP:\s*(.*)$", text, re.MULTILINE)
    normal = bool(stops and re.fullmatch(
        r"FDS completed successfully\s*\(CHID:\s*" + re.escape(chid) + r"\)\s*", stops[-1]))
    complete = normal and current is not None and current >= duration - 1e-5
    return {"simulated_time_s": current, "normal_stop": normal, "reached_end": complete}


def solver_path(explicit=None):
    value = explicit or os.environ.get("FDS_EXE")
    if value:
        candidate = Path(value).expanduser()
        if candidate.is_file():
            return candidate.resolve()
        found = shutil.which(value)
        if found:
            return Path(found).resolve()
        raise FileNotFoundError(f"FDS executable not found: {value}")
    for name in ("fds_openmp", "fds"):
        found = shutil.which(name)
        if found:
            return Path(found).resolve()
    raise FileNotFoundError("Specify --fds, set FDS_EXE, or add FDS to PATH. No solver is installed automatically.")


def load_campaign(path):
    campaign = Path(path).resolve()
    manifest = json.loads((campaign / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != 1:
        raise ValueError("Unsupported campaign manifest schema")
    for name in ("preheat", "bake"):
        stage = manifest["stages"][name]
        directory = (campaign / stage["directory"]).resolve()
        input_path = (directory / stage["input"]).resolve()
        if not directory.is_relative_to(campaign) or not input_path.is_relative_to(directory):
            raise ValueError("Campaign stage paths must stay inside the campaign")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", stage["chid"]):
            raise ValueError("Invalid CHID")
        duration = float(stage["duration_s"])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("Stage duration must be finite and positive")
    return campaign, manifest


def existing_outputs(directory, chid):
    """Never remove a stop file, restart, log, or previous result to rerun."""
    if not directory.exists():
        return []
    generated_inputs = {".fds", ".json"}
    return sorted(p.name for p in directory.iterdir() if p.is_file() and (
        p.name in {"run_status.json", "run_status.json.tmp", "solver.log"}
        or (p.name.startswith(chid) and p.suffix.lower() not in generated_inputs)))


def run_stage(campaign, manifest, name, solver, threads):
    if manifest.get('config_sha256') and (campaign/'campaign_config.json').exists():
        if input_hash(campaign/'campaign_config.json') != manifest['config_sha256']:
            raise ValueError('Campaign configuration changed after preparation')
    if name == 'preheat' and manifest.get('preheat_input_sha256'):
        source = campaign / manifest['stages']['preheat']['directory'] / manifest['stages']['preheat']['input']
        if input_hash(source) != manifest['preheat_input_sha256']:
            raise ValueError('Preheat input changed after preparation')
    stage = manifest["stages"][name]
    directory = (campaign / stage["directory"]).resolve()
    previous = existing_outputs(directory, stage["chid"])
    if previous:
        raise RuntimeError(f"Refusing to overwrite {name} outputs: {', '.join(previous[:8])}. Prepare a new campaign directory.")
    if name == "bake":
        # This command validates preheat completion and temperature targets and
        # transfers the profiles. Its failure prevents any solver invocation.
        subprocess.run([sys.executable, str(HERE / "pipeline.py"), "prepare-bake",
                        "--campaign", str(campaign)], check=True)
    input_path = directory / stage["input"]
    if not input_path.is_file():
        raise FileNotFoundError(f"Missing stage input: {input_path}")
    command = [str(solver), input_path.name]
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(threads)
    env["OMP_DYNAMIC"] = "FALSE"
    env["PATH"] = os.pathsep.join([str(solver.parent), str(solver.parent / "mpi"), env.get("PATH", "")])
    status = {"stage": name, "chid": stage["chid"], "status": "running",
              "started_utc": utc_now(), "duration_requested_s": stage["duration_s"],
              "input_sha256": input_hash(input_path), "config_sha256": manifest.get("config_sha256"),
              "solver": str(solver), "command": command, "threads": threads,
              "python_version": sys.version.split()[0], "simulated_time_s": 0.0}
    save_status(directory, status)
    start = time.monotonic()
    process = None
    print(f"START {name}: {command!r}; cwd={directory}; OpenMP threads={threads}", flush=True)
    try:
        with (directory / "solver.log").open("x", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=directory, env=env, stdout=log, stderr=subprocess.STDOUT)
            while process.poll() is None:
                status.update(output_progress(directory, stage["chid"], stage["duration_s"]))
                status["elapsed_wall_s"] = round(time.monotonic() - start, 2)
                save_status(directory, status)
                time.sleep(2)
            status["returncode"] = process.returncode
        status.update(output_progress(directory, stage["chid"], stage["duration_s"]))
        status["status"] = "completed" if process.returncode == 0 and status["reached_end"] else "failed"
    except BaseException as exc:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        status["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        status["error"] = str(exc)
        raise
    finally:
        status["finished_utc"] = utc_now()
        status["elapsed_wall_s"] = round(time.monotonic() - start, 2)
        save_status(directory, status)
    print(f"{status['status'].upper()} {name}: {status['simulated_time_s']} / {stage['duration_s']} s", flush=True)
    if status["status"] != "completed":
        raise RuntimeError(f"FDS did not complete {name}; inspect {directory / 'solver.log'}")
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, default=HERE / "campaign")
    parser.add_argument("--stage", choices=["preheat", "bake", "all"], default="all")
    parser.add_argument("--fds", help="FDS executable path (otherwise FDS_EXE or PATH)")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--execute", action="store_true", help="Explicitly permit solver execution")
    args = parser.parse_args(argv)
    if args.threads < 1:
        parser.error("--threads must be a positive integer")
    try:
        campaign, manifest = load_campaign(args.campaign)
        stages = ["preheat", "bake"] if args.stage == "all" else [args.stage]
        if not args.execute:
            print("DRY RUN: no commands invoked and no files changed. Add --execute on the simulation PC to run.")
            for name in stages:
                stage = manifest["stages"][name]
                directory = campaign / stage["directory"]
                status_path = directory / "run_status.json"
                status = json.loads(status_path.read_text()) if status_path.exists() else {"status": "not_started"}
                print(json.dumps({"stage": name, "input": str(directory / stage["input"]),
                                  "duration_s": stage["duration_s"], "status": status,
                                  "progress": output_progress(directory, stage["chid"], stage["duration_s"])}))
            return 0
        solver = solver_path(args.fds)
        for name in stages:
            run_stage(campaign, manifest, name, solver, args.threads)
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted. Existing outputs were preserved.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
