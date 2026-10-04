"""Export actual FDS Smoke3D RLE fields for the V4 browser renderer.

Contract: FDS 6.11.1 Source/smvv.f90 SMOKE3D_TO_FILE and RLE.
HRRPUV is quantised 0..254 against HRRPUV_MINMAX; soot against each
frame's maximum in .s3d.sz. No synthetic flame geometry or motion.
"""
import argparse
import json
import struct
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from postprocess import _record, read_smv, read_slice


def decode_rle(data, count):
    out=bytearray(); i=0
    while i<len(data):
        value=data[i]; i+=1
        if value==255:
            if i+2>len(data): raise ValueError('Truncated RLE')
            value,n=data[i:i+2]; i+=2
            out.extend(bytes([value])*n)
        else: out.append(value)
        if len(out)>count: raise ValueError('RLE exceeds declared size')
    if len(out)!=count: raise ValueError('RLE size mismatch')
    return np.frombuffer(out,dtype=np.uint8)


def sampled_frames(path, step=.5):
    sizes=[]
    for line in Path(str(path)+'.sz').read_text().splitlines()[1:]:
        cols=line.split()
        if len(cols)>=4: sizes.append(float(cols[3]))
    with path.open('rb') as f:
        header=struct.unpack('<8i',_record(f,'<'))
        shape=tuple(header[i+1]-header[i]+1 for i in (2,4,6))
        wanted=0.; index=0
        while True:
            try:
                record=_record(f,'<')
                if record is None: break
                t=struct.unpack('<f',record)[0]
                count,compressed=struct.unpack('<2i',_record(f,'<'))
                payload=_record(f,'<')
                if payload is None: break
                if len(payload)!=compressed: raise ValueError('Compressed size mismatch')
                if t+1e-5>=wanted:
                    data=decode_rle(payload,count).reshape(shape,order='F')
                    yield t,data,sizes[index]
                    wanted=t+step
                index+=1
            except EOFError: break


def export(run_dir,out_dir,step=.5):
    case=json.loads((run_dir/'case.json').read_text(encoding='utf-8'))
    cid=case['id']; smvpath=run_dir/f'{cid}.smv'
    manifest=read_smv(smvpath); lines=smvpath.read_text().splitlines()
    hrrmax=1200.
    refs=[]
    for i,line in enumerate(lines):
        if line.strip()=='HRRPUV_MINMAX': hrrmax=float(lines[i+1].split()[1])
        if line.startswith('SMOKF3D'):
            refs.append((int(line.split()[1]),lines[i+1].strip(),lines[i+2].strip()))
    output={'case':case,'source_run':str(run_dir),'hrr_max_kw_m3':hrrmax,
            'description':'FDS 3D fields; volume emission visualises HRRPUV, not optical flame chemistry.',
            'model':case.get('thermal_model','Prescribed-fire baseline; wall and pizza temperatures imposed.'), 'meshes':[], 'slices':[]}
    out_dir.mkdir(parents=True,exist_ok=True)
    for mid,grid in manifest['meshes'].items():
        item={'id':mid,'shape':[len(grid[a]) for a in 'xyz'],
              'coordinates':{a:grid[a].round(6).tolist() for a in 'xyz'}}
        for quantity,name in [('HRRPUV','fire'),('SOOT DENSITY','smoke')]:
            match=next((r for r in refs if r[0]==mid and r[2]==quantity),None)
            if match is None: continue
            frames=list(sampled_frames(run_dir/match[1],step))
            if not frames: continue
            filename=f'mesh{mid}_{name}.bin'
            # x fastest in file and in GPU/index formula.
            (out_dir/filename).write_bytes(b''.join(v.ravel(order='F').tobytes() for _,v,_ in frames))
            item[name]={'file':filename,'times':[round(t,5) for t,_,_ in frames],
                        'maxima':[v for _,_,v in frames]}
        output['meshes'].append(item)
    for ref in manifest['slices']:
        if ref['quantity'] not in ('TEMPERATURE','U-VELOCITY','V-VELOCITY','W-VELOCITY'): continue
        data=read_slice(run_dir/ref['filename']); grid=manifest['meshes'][ref['mesh']]
        if not len(data['times']): continue
        b=data['bounds']; fixed=[a for a in range(3) if b[2*a]==b[2*a+1]]
        if len(fixed)!=1: continue
        output['slices'].append({'mesh':ref['mesh'],'quantity':ref['quantity'],
            'axis':fixed[0], 'coordinates':{a:grid[a][b[2*i]:b[2*i+1]+1].round(6).tolist() for i,a in enumerate('xyz')},
            'times':data['times'].round(4).tolist(),
            'values':[v.ravel(order='F').round(2).tolist() for v in data['values']]})
    (out_dir/'volume.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'meshes':len(output['meshes']),'slices':len(output['slices']),
                      'frames':[len(m.get('fire',{}).get('times',[])) for m in output['meshes']]}))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('run_dir',type=Path); p.add_argument('out_dir',type=Path)
    p.add_argument('--step',type=float,default=.5); a=p.parse_args(); export(a.run_dir,a.out_dir,a.step)
