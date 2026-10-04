"""Reproducible local FDS screening; all lengths are metres, HRR is kW.

Generate: python run_study.py --generate-only
Run:      python run_study.py --case c1_v4_two_rotating --flue front
The external FDS runtime is kept out of Git. No installer is executed here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time

from fds_writer import write_case

ROOT = Path(__file__).resolve().parent
DEFAULT_FDS = Path.home() / '.cache/forno-cfd/fds-6.11.1/unpacked/firemodels/FDS6/bin/fds_openmp.exe'


def merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load_cases():
    study = json.loads((ROOT / 'cases.json').read_text(encoding='utf-8'))
    return [merge(study['common'], c) for c in study['cases']]


def variant(case, flue):
    c = copy.deepcopy(case)
    c['layout_id'] = case['id']
    c['id'] = f"{case['id']}__{flue}"
    c['flue_position'] = flue
    if flue == 'central':
        c['chimney']['center'] = c['plan'].get('center', [c['width']/2, c['depth']/2])
    elif flue != 'front':
        raise ValueError(flue)
    # FDS input is ASCII; the full Italian label remains in cases.json/viewer.
    c['label'] = c['id']
    return c


def execute(case, args):
    tag = f"{args.tag}_dx{round(args.dx*1000):02d}_t{args.seconds:g}"
    run_dir = ROOT / 'runs' / tag / case['id']
    run_dir.mkdir(parents=True, exist_ok=True)
    completion = run_dir / 'run_status.json'
    fingerprint = hashlib.sha256((json.dumps(case, sort_keys=True) + str(args.dx) + str(args.seconds)).encode()
                                 + (ROOT/'fds_writer.py').read_bytes()).hexdigest()
    if completion.exists() and not args.force:
        old = json.loads(completion.read_text())
        if old.get('status') == 'completed' and old.get('generation_fingerprint') == fingerprint:
            print(f"SKIP completed {case['id']}", flush=True)
            return old
    metadata = write_case(case, run_dir, cell_size=args.dx,
                          duration=args.seconds, flue_position=case['flue_position'],
                          hrr_kw=case['fire_hrr_kw'])
    (run_dir / 'case.json').write_text(json.dumps(case, indent=2), encoding='utf-8')
    input_path = run_dir / f"{case['id']}.fds"
    stop_file = run_dir / f"{case['id']}.stop"
    if stop_file.exists():
        stop_file.unlink()
    inputs = ROOT / 'inputs' / tag
    inputs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, inputs / input_path.name)
    shutil.copy2(run_dir / f"{case['id']}_metadata.json", inputs)
    if args.generate_only:
        print(f"GENERATED {case['id']} {metadata['mesh']['ijk']}", flush=True)
        return {'status': 'generated'}
    solver = Path(args.fds).resolve()
    if not solver.is_file():
        raise FileNotFoundError(f'FDS executable not found: {solver}')
    env = os.environ.copy()
    env['PATH'] = str(solver.parent / 'mpi') + os.pathsep + str(solver.parent) + os.pathsep + env.get('PATH', '')
    env['OMP_NUM_THREADS'] = str(args.threads)
    env['OMP_DYNAMIC'] = 'FALSE'
    status = {'case_id': case['id'], 'status': 'running', 'duration_requested_s': args.seconds,
              'cell_size_m': args.dx, 'threads': args.threads,
              'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
              'generation_fingerprint': fingerprint,
              'solver': str(solver), 'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    completion.write_text(json.dumps(status, indent=2), encoding='utf-8')
    cell_count = sum(math.prod(m['ijk']) for m in metadata.get('meshes',[metadata['mesh']]))
    print(f"START {case['id']} cells={cell_count} dx={args.dx:g}m t={args.seconds:g}s", flush=True)
    start = time.monotonic()
    with (run_dir / 'solver.log').open('w', encoding='utf-8') as log:
        try:
            result = subprocess.run([str(solver), input_path.name], cwd=run_dir, env=env,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
            status['returncode'] = result.returncode
        except subprocess.TimeoutExpired:
            status['returncode'] = None
            status['status'] = 'timeout'
    outpath = run_dir / f"{case['id']}.out"
    output = outpath.read_text(errors='replace') if outpath.exists() else ''
    log_text = (run_dir / 'solver.log').read_text(errors='replace')
    success = 'completed successfully' in (output + log_text).lower()
    if status['status'] != 'timeout':
        status['status'] = 'completed' if status['returncode'] == 0 and success else 'failed'
    status['elapsed_wall_s'] = round(time.monotonic() - start, 2)
    completion.write_text(json.dumps(status, indent=2), encoding='utf-8')
    print(f"{status['status'].upper()} {case['id']} wall={status['elapsed_wall_s']}s", flush=True)
    if status['status'] != 'completed':
        print(log_text[-5000:], flush=True)
        raise RuntimeError(f"FDS {status['status']}: {run_dir}")
    return status


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', action='append', help='Layout ID (repeatable); default all six')
    p.add_argument('--flue', choices=['front', 'central', 'both'], default='both')
    p.add_argument('--dx', type=float, default=.04)
    p.add_argument('--seconds', type=float, default=30)
    p.add_argument('--threads', type=int, default=2)
    p.add_argument('--timeout', type=float, default=14400)
    p.add_argument('--tag', default='coarse', help='Safe alphanumeric run-family name')
    p.add_argument('--fds', default=str(DEFAULT_FDS))
    p.add_argument('--generate-only', action='store_true')
    p.add_argument('--force', action='store_true')
    args = p.parse_args()
    if not args.tag.replace('_', '').replace('-', '').isalnum():
        p.error('tag may contain only letters, digits, underscores and hyphens')
    if args.seconds <= 0 or args.dx <= 0 or args.threads < 1:
        p.error('seconds, dx and threads must be positive')
    cases = load_cases()
    if args.case:
        unknown = set(args.case) - {c['id'] for c in cases}
        if unknown:
            p.error('Unknown cases: ' + ', '.join(sorted(unknown)))
        cases = [c for c in cases if c['id'] in args.case]
    flues = ['front', 'central'] if args.flue == 'both' else [args.flue]
    for case in cases:
        for flue in flues:
            execute(variant(case, flue), args)


if __name__ == '__main__':
    main()
