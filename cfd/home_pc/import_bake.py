"""Import a completed V4 bake archive after validating its preheat provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
SUFFIXES = {'.fds', '.json', '.log', '.txt', '.out', '.smv', '.restart', '.sf',
            '.s3d', '.sz', '.csv', '.bf', '.bnd', '.plt', '.q'}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def import_bake(archive: Path, campaign: Path = HERE / 'campaign') -> dict:
    archive = archive.resolve()
    campaign = campaign.resolve()
    dest = campaign / 'bake'
    manifest = json.loads((campaign / 'manifest.json').read_text(encoding='utf-8'))
    if not dest.is_dir() or not (campaign / 'preheat' / 'v4_preheat.out').is_file():
        raise FileNotFoundError('Local V4 preheat campaign is incomplete')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Archive CRC failed')
        names = set(z.namelist())
        required = {'bake/bake.fds', 'bake/case.json', 'bake/run_status.json',
                    'bake/transfer.json', 'bake/v4_bake.out', 'bake/v4_bake_devc.csv'}
        if not required <= names:
            raise ValueError(f'Missing bake files: {sorted(required - names)}')
        status = json.loads(z.read('bake/run_status.json'))
        transfer = json.loads(z.read('bake/transfer.json'))
        if status.get('status') != 'completed' or status.get('chid') != 'v4_bake' or \
                status.get('duration_requested_s') != 120 or status.get('simulated_time_s') != 120 or \
                status.get('returncode') != 0 or not status.get('normal_stop'):
            raise ValueError('Bake status does not attest successful 120 s completion')
        if status.get('input_sha256') != sha(z.read('bake/bake.fds')) or \
                status.get('config_sha256') != manifest['config_sha256'] or \
                transfer.get('config_sha256') != manifest['config_sha256']:
            raise ValueError('Bake input/config provenance mismatch')
        case = json.loads(z.read('bake/case.json'))
        if case.get('id') != 'v4_bake' or z.read('bake/case.json') != (dest / 'case.json').read_bytes():
            raise ValueError('Bake geometry differs from the local V4 case')
        for filename, expected in transfer['source_sha256'].items():
            if '/' in filename or '\\' in filename or filename in {'.', '..'}:
                raise ValueError('Unsafe preheat source name')
            source = campaign / 'preheat' / filename
            if not source.is_file() or sha(source.read_bytes()) != expected:
                raise ValueError(f'Bake transfer does not match local preheat: {filename}')
        output = z.read('bake/v4_bake.out').decode(errors='replace')
        if not re.search(r'Total Time:\s*120\.0+\s*s', output) or \
                not output.rstrip().endswith('STOP: FDS completed successfully (CHID: v4_bake)'):
            raise ValueError('Bake solver output does not show normal 120 s completion')
        entries = []
        for item in z.infolist():
            if item.is_dir():
                continue
            path = PurePosixPath(item.filename)
            if len(path.parts) != 2 or path.parts[0] != 'bake' or \
                    path.name in {'', '.', '..'} or '\\' in path.name or ':' in path.name or \
                    Path(path.name).suffix.lower() not in SUFFIXES:
                raise ValueError(f'Unexpected archive member: {item.filename}')
            target = (dest / path.name).resolve()
            if not target.is_relative_to(dest):
                raise ValueError(f'Unsafe archive member: {item.filename}')
            entries.append((item, target))
        if sum(item.file_size for item, _ in entries) > 300 * 1024 * 1024:
            raise ValueError('Archive content unexpectedly large')
        for item, target in entries:
            if target.exists() and sha(target.read_bytes()) != sha(z.read(item)):
                # The initial local metadata names the non-runnable bake template.
                # The completed run legitimately changes only fds_input.
                if target.name != 'v4_bake_metadata.json':
                    raise ValueError(f'Existing file differs: {target}')
                old = json.loads(target.read_text(encoding='utf-8'))
                new = json.loads(z.read(item))
                if old.pop('fds_input', None) != 'bake.template.fds' or \
                        new.pop('fds_input', None) != 'bake.fds' or old != new:
                    raise ValueError('Metadata differs beyond template-to-run input')
        copied, reused = [], []
        for item, target in entries:
            data = z.read(item)
            if target.exists() and sha(target.read_bytes()) == sha(data):
                reused.append(target.name)
                continue
            with tempfile.NamedTemporaryFile(dir=dest, delete=False, prefix='.import-', suffix='.tmp') as f:
                temporary = Path(f.name)
                f.write(data)
            os.replace(temporary, target)
            copied.append(target.name)
        record = {'archive': str(archive), 'archive_sha256': sha(archive.read_bytes()),
                  'status': 'completed', 'simulation_end_s': 120, 'copied': copied,
                  'reused_identical': reused, 'readiness_override': 'bake/readiness_override.json' in names}
        (dest / 'import_record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    result = import_bake(args.archive)
    print(f"Imported {len(result['copied'])} files; reused {len(result['reused_identical'])} identical files.")
