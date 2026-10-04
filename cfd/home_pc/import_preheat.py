"""Copy a completed home-PC preheat from cfd.zip without changing input files."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
PREFIX='cfd/home_pc/campaign/preheat/'
SUFFIXES={'.fds','.json','.log','.txt','.out','.smv','.restart','.sf','.s3d','.sz','.csv','.bf','.bnd','.plt','.q'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def copy(zip_path,project=HERE.parent.parent):
    dest=project/'cfd/home_pc/campaign/preheat'
    if not (dest/'preheat.fds').is_file():raise FileNotFoundError('Project campaign input missing')
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:raise ValueError('Archive CRC failed')
        manifest=json.loads(z.read('cfd/home_pc/campaign/manifest.json'))
        status=json.loads(z.read(PREFIX+'run_status.json'))
        out=z.read(PREFIX+'v4_preheat.out').decode(errors='replace')
        if sha(dest/'preheat.fds')!=manifest['preheat_input_sha256']:raise ValueError('Project input differs from archived campaign')
        if status.get('status')!='completed' or status.get('input_sha256')!=manifest['preheat_input_sha256'] or status.get('config_sha256')!=manifest['config_sha256']:raise ValueError('Archived status does not match its input')
        if 'STOP: FDS completed successfully (CHID: v4_preheat)' not in out or not re.search(r'Total Time:\s*3600\.0+\s*s',out):raise ValueError('Preheat output has no normal 3600 s completion')
        entries=[]
        for item in z.infolist():
            if item.is_dir() or not item.filename.startswith(PREFIX):continue
            relative=PurePosixPath(item.filename[len(PREFIX):])
            if len(relative.parts)!=1 or relative.name in ('','.','..') or '\\' in relative.name or ':' in relative.name:raise ValueError(f'Unsafe archive member: {item.filename}')
            if Path(relative.name).suffix.lower() not in SUFFIXES:raise ValueError(f'Unexpected file type: {relative.name}')
            target=(dest/relative.name).resolve()
            if not target.is_relative_to(dest.resolve()):raise ValueError('Unsafe target path')
            entries.append((item,target))
        if sum(i.file_size for i,_ in entries)>300*1024*1024:raise ValueError('Unexpectedly large archive content')
        for item,target in entries:
            if target.exists() and sha(target)!=hashlib.sha256(z.read(item)).hexdigest():raise ValueError(f'Existing file differs: {target.name}')
        copied=[];skipped=[]
        for item,target in entries:
            if target.exists():skipped.append(target.name);continue
            with tempfile.NamedTemporaryFile(dir=dest,delete=False,prefix='.import-',suffix='.tmp') as tmp:
                name=Path(tmp.name)
                with z.open(item) as src:shutil.copyfileobj(src,tmp)
            os.replace(name,target)
            copied.append(target.name)
        record={'source_archive':str(zip_path),'source_archive_sha256':sha(zip_path),'status':'completed','simulation_end_s':3600,'copied':copied,'identical_inputs_skipped':skipped}
        (dest/'import_record.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(f'Imported {len(copied)} files; reused {len(skipped)} identical inputs. Destination: {dest}')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('zip_path',type=Path);a=p.parse_args();copy(a.zip_path)
