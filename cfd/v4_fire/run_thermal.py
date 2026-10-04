"""Run the thermal prototype with persisted status and export its real outputs."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from build_thermal import build
from export_volume import export

ROOT=Path(__file__).resolve().parent
RUN=ROOT.parent/'runs'/'v4_thermal_dx25_t60'
STATUS=ROOT/'web'/'data'/'thermal-status.json'
SOLVER=Path.home()/'.cache/forno-cfd/fds-6.11.1/unpacked/firemodels/FDS6/bin/fds_openmp.exe'


def write_status(state):
    temporary=STATUS.with_suffix('.tmp')
    temporary.write_text(json.dumps(state,indent=2),encoding='utf-8')
    temporary.replace(STATUS)


def main():
    if (RUN/'v4_thermal_woodgas.out').exists():
        raise RuntimeError('Run already exists; inspect it before rerunning to preserve outputs.')
    path=build(RUN,60,.025)
    state={'status':'running','run':str(RUN),'duration_s':60,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    write_status(state)
    env=os.environ.copy();env['OMP_NUM_THREADS']='2';env['OMP_DYNAMIC']='FALSE'
    env['PATH']=str(SOLVER.parent)+os.pathsep+str(SOLVER.parent/'mpi')+os.pathsep+env.get('PATH','')
    try:
        with (RUN/'solver.log').open('w') as log:
            result=subprocess.run([str(SOLVER),path.name],cwd=RUN,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=21600)
        out=(RUN/'v4_thermal_woodgas.out').read_text(errors='replace')
        if result.returncode or 'completed successfully' not in out.lower():
            raise RuntimeError('FDS did not complete normally; inspect solver.log')
        with (RUN/'v4_thermal_woodgas_devc.csv').open() as file:
            rows=list(csv.reader(file));labels=[v.strip().strip('"') for v in rows[1]];last=[float(v) for v in rows[-1]]
        state['last_measurements']=dict(zip(labels,last));state['status']='completed'
        export(RUN,ROOT/'web'/'thermal-data')
        state['volume_path']='thermal-data/volume.json'
    except Exception as error:
        state['status']='failed';state['error']=str(error)
        raise
    finally:
        write_status(state)
        (RUN/'run_status.json').write_text(json.dumps(state,indent=2),encoding='utf-8')


if __name__=='__main__':main()
