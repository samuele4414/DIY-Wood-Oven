"""Make a portable input/code delivery; never starts FDS."""
import argparse
from pathlib import Path
import shutil
import zipfile
from pipeline import prepare

HERE=Path(__file__).resolve().parent
CFD=HERE.parent

def package(output):
    if output.exists():raise FileExistsError('Delivery folder already exists; choose a new name')
    output.mkdir(parents=True)
    files=['cases.json','fds_writer.py','run_study.py','postprocess.py',
           'v4_fire/export_volume.py','v4_fire/render_video.py',
           'home_pc/pipeline.py','home_pc/campaign_config.json','home_pc/run_home.py',
           'home_pc/RUN_HOME.ps1','home_pc/requirements.txt','home_pc/README.md',
           'home_pc/export_results.py','home_pc/test_pipeline.py','home_pc/test_runner.py',
           'home_pc/test_export_results.py']
    for relative in files:
        target=output/'cfd'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(CFD/relative,target)
    shutil.copy2(HERE/'README.md',output/'LEGGIMI.md')
    prepare(output/'cfd/home_pc/campaign',output/'cfd/home_pc/campaign_config.json')
    archive=output.with_suffix('.zip')
    if archive.exists():raise FileExistsError('Delivery archive already exists')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in output.rglob('*'):
            if path.is_file():z.write(path,Path(output.name)/path.relative_to(output))
    print(f'Portable folder: {output}\nArchive: {archive}\nNo CFD solver executed.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    package(p.parse_args().output.resolve())
