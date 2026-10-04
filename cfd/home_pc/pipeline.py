"""Generate/transfer V4 warm-up and bake inputs. This module NEVER runs FDS."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fds_writer import write_case, inside_plan, roof_height
from run_study import load_cases, variant

HERE=Path(__file__).resolve().parent
ZONES=('FLOOR_L','FLOOR_R','HEARTH','VAULT','FLUE')
LAYERS={
    'FLOOR_L': [('CORDIERITE',.03),('BOARD',.05)],
    'FLOOR_R': [('CORDIERITE',.03),('BOARD',.05)],
    'HEARTH': [('CORDIERITE',.03),('BOARD',.05)],
    'VAULT': [('STEEL',.0015),('INSULATION',.05),('STEEL',.001)],
    'FLUE': [('STEEL',.001)]}
NUM=r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[Ee][-+]?\d+)?'
IOR=(-1,1,-2,2,-3,3)

def dump(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def generator_hashes():
    return {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['pipeline.py','../fds_writer.py','../cases.json']}

def config_load(path):
    c=json.loads(path.read_text(encoding='utf-8'))
    for name in ('cell_size_m','preheat_seconds','bake_seconds','fire_kw','fire_ramp_seconds'):
        if not math.isfinite(c[name]) or c[name]<=0:raise ValueError(f'Invalid {name}')
    f=c['food'];lo,hi=f['phase_band_C']
    if not (0<=f['water_mass_fraction']<1 and lo<hi and 0<f['contact_transition_m']<f['thickness_m']/4):raise ValueError('Invalid food parameters')
    if c['preheat_seconds']<c['readiness']['window_seconds']:raise ValueError('Preheat is shorter than readiness window')
    return c

def zone_for(name,xyz):
    if name=='FLOOR_HOT':return 'HEARTH' if xyz[1]>.41 else ('FLOOR_L' if xyz[0]<.395 else 'FLOOR_R')
    return {'WALL_HOT':'VAULT','CHIMNEY_INNER':'FLUE'}.get(name,name)

def geometry(text,case,bake=False):
    """Tag thermal faces and return coordinates of actually exposed surfaces."""
    faces=[];output=[]
    for line in text.splitlines():
        if not line.startswith('&OBST') or 'SURF_ID6=' not in line:
            output.append(line);continue
        xb=[float(v) for v in re.search(r'XB=([^/]+?),\s*SURF_ID6',line)[1].split(',')]
        names=re.findall(r"'([^']+)'",line.split('SURF_ID6=')[1])
        centers=[(xb[2*i]+xb[2*i+1])/2 for i in range(3)]
        mapped=[]
        for n,name in enumerate(names):
            xyz=centers.copy();xyz[n//2]=xb[n]
            zone=zone_for(name,xyz)
            under_pizza=bake and name=='FLOOR_HOT' and n==5 and any((xyz[0]-px)**2+(xyz[1]-py)**2<=(case['pizza_diameter']/2)**2 for px,py in case['pizza_centers'])
            if under_pizza:zone='INERT'  # substrate storage is in the pizza+floor column
            mapped.append(zone)
            if zone in ZONES:faces.append({'zone':zone,'xyz':xyz,'ior':IOR[n],'xb':xb})
        output.append(line.split('SURF_ID6=')[0]+'SURF_ID6='+','.join(repr(n) for n in mapped)+' /')
    return '\n'.join(output)+'\n',faces

def surface_at(faces,zone,x,y,ior):
    candidates=[f for f in faces if f['zone']==zone and f['ior']==ior and f['xb'][0]-1e-8<=x<=f['xb'][1]+1e-8 and f['xb'][2]-1e-8<=y<=f['xb'][3]+1e-8]
    if not candidates:raise ValueError(f'No exposed {zone} face at {x},{y}')
    f=min(candidates,key=lambda f:abs(f['xyz'][2]-(.25 if ior<0 else 0)))
    return {'zone':zone,'xyz':[x,y,f['xyz'][2]],'ior':ior}

def probe_plan(faces,case):
    probes=[]
    for n,(x,y) in enumerate(case['pizza_centers'],1):
        zone='FLOOR_L' if x<.395 else 'FLOOR_R'
        for suffix,ox,oy in [('C',0,0),('L',-.09,0),('R',.09,0),('F',0,-.09),('B',0,.09)]:
            f=surface_at(faces,zone,x+ox,y+oy,3)
            probes.append(dict(f,id=f'floor_p{n}_{suffix}',profile=suffix=='C',contact=n if suffix=='C' else None))
        for suffix,yy in [('F',.12),('B',.32)]:
            f=surface_at(faces,'VAULT',x,yy,-3)
            probes.append(dict(f,id=f'vault_p{n}_{suffix}',profile=True,contact=None))
    probes.append(dict(surface_at(faces,'HEARTH',.20,.47,3),id='hearth',profile=True,contact=None))
    flue=min([f for f in faces if f['zone']=='FLUE'],key=lambda f:abs(f['xyz'][2]-.8))
    probes.append(dict(flue,id='flue_liner',profile=True,contact=None))
    return probes

def coord(p):return ','.join(f'{v:.7g}' for v in p)

def material_lines(c):
    f=c['food'];lo,hi=f['phase_band_C'];epsilon=.01
    # A trapezoid with area w*latent exactly; ramp values are kJ/(kg K).
    boost=f['water_mass_fraction']*f['latent_heat_kJ_kg']/(hi-lo-epsilon)
    lines=["&MATL ID='STEEL', DENSITY=7900., CONDUCTIVITY=16., SPECIFIC_HEAT=0.5 /",
           "&MATL ID='INSULATION', DENSITY=128., CONDUCTIVITY=0.12, SPECIFIC_HEAT=1. /",
           "&MATL ID='CORDIERITE', DENSITY=2600., CONDUCTIVITY=2.5, SPECIFIC_HEAT=0.9 /",
           "&MATL ID='BOARD', DENSITY=250., CONDUCTIVITY=0.09, SPECIFIC_HEAT=1. /",
           f"&MATL ID='FOOD', DENSITY={f['density_kg_m3']}, CONDUCTIVITY={f['conductivity_W_mK']}, SPECIFIC_HEAT_RAMP='FOOD_CP' /"]
    for t,cp in [(0,f['base_cp_kJ_kgK']),(lo,f['base_cp_kJ_kgK']),(lo+epsilon,f['base_cp_kJ_kgK']+boost),(hi-epsilon,f['base_cp_kJ_kgK']+boost),(hi,f['base_cp_kJ_kgK']),(1200,f['base_cp_kJ_kgK'])]:
        lines.append(f"&RAMP ID='FOOD_CP', T={t:.7g}, F={cp:.9g} /")
    return lines

def surf_line(name,layers,c,hot):
    spec=', '.join(f'MATL_ID({i},1)={mat!r}' for i,(mat,_) in enumerate(layers,1))
    thick=','.join(f'{x:.7g}' for _,x in layers)
    initial=f"RAMP_T_I='INIT_{name}'" if hot else f"TMP_INNER={c['ambient_C']}"
    return f"&SURF ID='{name}', {spec}, THICKNESS={thick}, {initial}, TMP_GAS_BACK={c['ambient_C']}, HEAT_TRANSFER_COEFFICIENT_BACK=8., EMISSIVITY=0.9 /"

def build_stage(destination,c,bake=False,transfer=None,template=False):
    destination.mkdir(parents=True,exist_ok=True)
    case=variant(load_cases()[0],'front');centers=case['pizza_centers']
    case['id']='v4_bake' if bake else 'v4_preheat';case['label']=case['id']
    if not bake:case['pizza_centers']=[]
    # Remove obsolete fixed-temperature metadata inherited from screening.
    for k in ['inner_roof_temperature_C','floor_temperature_C','pizza_surface_temperature_C','chimney_wall_temperature_C']:
        case.pop(k,None)
    case.update(thermal_model='Transferred hot solid profiles; cold pizza' if bake else 'Empty oven cold-start thermal preheat',rotating=False,rotation_rpm=0,fire_hrr_kw=c['fire_kw'],ambient_temperature_C=c['ambient_C'],pizza_initial_C=c['pizza_initial_C'])
    sec=c['bake_seconds'] if bake else c['preheat_seconds'];dx=c['cell_size_m']
    meta=write_case(case,destination,cell_size=dx,duration=sec,hrr_kw=c['fire_kw'])
    raw=destination/(case['id']+'.fds');text=raw.read_text();case['pizza_centers']=centers
    text,faces=geometry(text,case,bake)
    # Geometry writer has no food in preheat, but candidate locations remain metadata.
    case['pizza_present']=bake
    text=re.sub(r"&HEAD[^/]+/",f"&HEAD CHID='{case['id']}', TITLE='V4 {'bake hot-start' if bake else 'empty oven preheat'}' /",text,count=1)
    text=re.sub(r'&MISC[^/]+/',f"&MISC TMPA={c['ambient_C']} /",text,count=1)
    text=text.replace("&SURF ID='COLD_OUTER', TMP_FRONT=25. /",f"&SURF ID='COLD_OUTER', TMP_FRONT={c['ambient_C']} /")
    text=re.sub(r"&REAC[^/]+/",f"&REAC ID='WOODGAS_PROXY', FUEL='WOOD', C=3.4, H=6.2, O=2.5, HEAT_OF_COMBUSTION=15000., SOOT_YIELD=0.015, RADIATIVE_FRACTION={c['radiative_fraction']} /",text,count=1)
    for name in ['WALL_HOT','FLOOR_HOT','CHIMNEY_INNER','PIZZA_PREHEATED']:
        text=re.sub(r"&SURF ID='"+name+r"'[^/]+/\s*",'',text)
    text=re.sub(r'&DUMP[^/]+/',f"&DUMP DT_DEVC={.5 if bake else 10}, DT_SLCF={1 if bake else 30}, DT_HRR={1 if bake else 10}, DT_BNDF={1 if bake else 30}, DT_PROF={1 if bake else 30}, DT_SMOKE3D={.25 if bake else 10}, DT_RESTART=60. /",text)
    if bake:
        # Fire remains established, without a second ignition ramp.
        text=text.replace("T=0., F=0.","T=0., F=1.")
        for n in [1,2]:
            text=re.sub(r"(&OBST ID='PIZZA_"+str(n)+r"'[^\n]+)SURF_ID='PIZZA_PREHEATED'",r"\1SURF_IDS='PIZZA_"+str(n)+"','INERT','INERT'",text)
    else:text=text.replace("T=5., F=1.",f"T={c['fire_ramp_seconds']}, F=1.")
    additions=material_lines(c)+[surf_line(z,LAYERS[z],c,bake) for z in ZONES]
    for q in ['WALL TEMPERATURE','RADIATIVE HEAT FLUX','CONVECTIVE HEAT FLUX','NET HEAT FLUX']:
        additions.append(f"&BNDF QUANTITY='{q}' /")
    gas=[('L',.21,.205,.12),('R',.58,.205,.12),('REAR',.395,.55,.12),('FLUE',.395,.045,.8)]
    for name,x,y,z in gas:additions.append(f"&DEVC ID='gas_{name}', XYZ={x},{y},{z}, QUANTITY='TEMPERATURE' /")
    profile_manifest=[]
    if not bake:
        plan=probe_plan(faces,case)
        for p in plan:
            loc=f"XYZ={coord(p['xyz'])}, IOR={p['ior']}"
            additions.append(f"&DEVC ID='{p['id']}', {loc}, QUANTITY='WALL TEMPERATURE' /")
            if p['profile']:
                index=len(profile_manifest)+1
                additions.append(f"&PROF ID='{p['id']}', {loc}, QUANTITY='INSIDE WALL TEMPERATURE', CELL_CENTERED=.FALSE., FORMAT_INDEX=1 /")
                profile_manifest.append(dict(p,index=index,file=f"v4_preheat_prof_{index}.csv",thickness_m=sum(x for _,x in LAYERS[p['zone']])))
        dump(destination/'profiles.json',profile_manifest)
        dump(destination/'probes.json',plan)
    else:
        food=c['food'];th=food['thickness_m']
        for n,(x,y) in enumerate(centers,1):
            zone='FLOOR_L' if x<.395 else 'FLOOR_R'
            additions.append(surf_line(f'PIZZA_{n}',[('FOOD',th)]+LAYERS[zone],c,True))
            for suffix,ox,oy in [('C',0,0),('L',-.09,0),('R',.09,0),('F',0,-.09),('B',0,.09)]:
                loc=f'XYZ={x+ox:.6g},{y+oy:.6g},{dx:.6g}, IOR=3'
                for q,short in [('WALL TEMPERATURE','surface'),('RADIATIVE HEAT FLUX','rad'),('CONVECTIVE HEAT FLUX','conv'),('NET HEAT FLUX','net')]:
                    additions.append(f"&DEVC ID='pizza_{n}_{suffix}_{short}', {loc}, QUANTITY='{q}' /")
                for depth,label in [(th/2,'core'),(th-.0002,'bottom')]:
                    additions.append(f"&DEVC ID='pizza_{n}_{suffix}_{label}', {loc}, QUANTITY='INSIDE WALL TEMPERATURE', DEPTH={depth} /")
                additions.append(f"&DEVC ID='pizza_{n}_{suffix}_gas', XYZ={x+ox:.6g},{y+oy:.6g},0.1, QUANTITY='TEMPERATURE' /")
            # Backward-compatible centre aliases for renderer/probe summaries.
            additions.append(f"&DEVC ID='pizza_{n}_surface', XYZ={x},{y},{dx}, IOR=3, QUANTITY='WALL TEMPERATURE' /")
        additions.append("&DEVC ID='floor_surface', XYZ=0.395,0.20,0., IOR=3, QUANTITY='WALL TEMPERATURE' /")
        if transfer:
            for name,profile in transfer['profiles'].items():
                for depth,temp in profile:additions.append(f"&RAMP ID='INIT_{name}', T={depth:.9g}, F={temp:.9g} /")
            # Hot gas temperatures from four measured regions; momentum/species
            # are not transferred, so this is deliberately not called a restart.
            xb=meta['meshes'][0]['xb'];nx,ny,_=meta['meshes'][0]['ijk']
            for i in range(nx):
                x=xb[0]+(i+.5)*dx
                for j in range(ny):
                    y=xb[2]+(j+.5)*dx
                    if not inside_plan(case,x,y):continue
                    zmax=math.floor(roof_height(case,x,y)/dx+.5)*dx
                    key='REAR' if y>.41 else ('L' if x<.395 else 'R')
                    additions.append(f"&INIT XB={coord([x-dx/2,x+dx/2,y-dx/2,y+dx/2,0,zmax])}, TEMPERATURE={transfer['gas_C'][key]:.8g} /")
            additions.append(f"&INIT XB=0.335,0.455,-0.01,0.10,0.30,1.28, TEMPERATURE={transfer['gas_C']['FLUE']:.8g} /")
        elif template:additions.append('! NON ESEGUIBILE: INIT_* RAMP profiles come from the completed preheat.')
    text=text.replace('&TAIL /','\n'.join(additions)+'\n&TAIL /')
    name='bake.template.fds' if template else ('bake.fds' if bake else 'preheat.fds')
    target=destination/name;target.write_text(text,encoding='ascii');raw.unlink()
    meta['fds_input']=name
    meta['assumptions']=c['notes']+['1D temperature profiles are transferred by representative surface region, not an exact CFD restart.','Pizza floor storage exists only in pizza+substrate columns; inactive floor faces underneath are INERT.']
    dump(destination/(case['id']+'_metadata.json'),meta);dump(destination/'case.json',case)
    return target

def read_devc(path):
    with path.open() as f:rows=list(csv.reader(f))
    names=[v.strip().strip('"') for v in rows[1]]
    records=[dict(zip(names,map(float,r))) for r in rows[2:] if r]
    if any(not all(math.isfinite(v) for v in row.values()) for row in records):raise ValueError('Non-finite DEVC values')
    if not records or any(records[i]['Time']>=records[i+1]['Time'] for i in range(len(records)-1)):raise ValueError('Invalid DEVC time series')
    return records

def read_profile(path,end,thickness,expected=None,dx=.025):
    if expected is not None:
        with path.open() as f:headers=list(csv.reader(f))[:3]
        if len(headers)<3 or len(headers[1])<5:raise ValueError('Profile header missing')
        actual=headers[1]
        if actual[0].strip().strip('"')!=expected['id'] or int(actual[1])!=expected['ior']:raise ValueError('Profile identity mismatch')
        if any(abs(float(v)-w)>dx*.51+1e-5 for v,w in zip(actual[2:5],expected['xyz'])):raise ValueError('Profile face coordinates mismatch')
    valid=[]
    for line in path.read_text().splitlines():
        try:r=[float(x) for x in line.split(',')]
        except ValueError:continue
        if len(r)<4:continue
        n=int(r[1])
        if r[1]!=n or n<2 or len(r)!=2+2*n:continue
        if not all(math.isfinite(v) for v in r):raise ValueError('Non-finite profile values')
        valid.append((r[0],list(zip(r[2:2+n],r[2+n:]))))
    if not valid or abs(valid[-1][0]-end)>1e-3:raise ValueError(f'Incomplete profile: {path}')
    pairs=valid[-1][1]
    if abs(pairs[0][0])>1e-6 or abs(pairs[-1][0]-thickness)>1e-5 or any(a[0]>=b[0] for a,b in zip(pairs,pairs[1:])):raise ValueError(f'Profile depth mismatch: {path}')
    if any(not math.isfinite(t) or not -100<t<2000 for _,t in pairs):raise ValueError('Invalid profile temperatures')
    return pairs

def interp(pairs,x):
    if x<=pairs[0][0]:return pairs[0][1]
    for (xa,ya),(xb,yb) in zip(pairs,pairs[1:]):
        if x<=xb:return ya+(yb-ya)*(x-xa)/(xb-xa)
    return pairs[-1][1]

def readiness(records,c):
    r=c['readiness'];last=records[-1];first=min(records,key=lambda p:abs(p['Time']-(last['Time']-r['window_seconds'])))
    floor=[k for k in last if k.startswith('floor_p')];vault=[k for k in last if k.startswith('vault_p')]
    if len(floor)!=10 or len(vault)!=4:raise ValueError('Readiness probes missing')
    dt=last['Time']-first['Time']
    if dt<r['window_seconds']*.9:raise ValueError('Insufficient readiness history')
    values={'floor_min_C':min(last[k] for k in floor),'vault_min_C':min(last[k] for k in vault),'floor_spread_C':max(last[k] for k in floor)-min(last[k] for k in floor),'max_rate_C_per_min':max(abs(last[k]-first[k])*60/dt for k in floor+vault)}
    checks={'floor_hot':values['floor_min_C']>=r['floor_min_C'],'vault_hot':values['vault_min_C']>=r['vault_min_C'],'floor_uniform':values['floor_spread_C']<=r['max_floor_spread_C'],'near_steady':values['max_rate_C_per_min']<=r['max_rate_C_per_min']}
    return {'ready':all(checks.values()),'checks':checks,'measured':values,'thresholds':r}

def prepare(output,config):
    if (output/'manifest.json').exists():raise FileExistsError('Campaign already exists; use a new output folder')
    c=config_load(config);output.mkdir(parents=True,exist_ok=True);dump(output/'campaign_config.json',c)
    build_stage(output/'preheat',c);build_stage(output/'bake',c,bake=True,template=True)
    manifest={'schema':1,'config_sha256':hashlib.sha256((output/'campaign_config.json').read_bytes()).hexdigest(),'stages':{'preheat':{'directory':'preheat','input':'preheat.fds','chid':'v4_preheat','duration_s':c['preheat_seconds']},'bake':{'directory':'bake','input':'bake.fds','chid':'v4_bake','duration_s':c['bake_seconds']}}}
    manifest['preheat_input_sha256']=hashlib.sha256((output/'preheat/preheat.fds').read_bytes()).hexdigest()
    manifest['generator_sha256']=generator_hashes()
    dump(output/'manifest.json',manifest)
    print(f'Prepared inputs only: {output}. No solver has been launched.')

def prepare_bake(campaign):
    c=config_load(campaign/'campaign_config.json');manifest=json.loads((campaign/'manifest.json').read_text())
    if hashlib.sha256((campaign/'campaign_config.json').read_bytes()).hexdigest()!=manifest['config_sha256']:raise ValueError('Config changed after preparation; generate a new campaign')
    if generator_hashes()!=manifest['generator_sha256']:raise ValueError('Generator changed after preparation; use the original package or generate a new campaign')
    if hashlib.sha256((campaign/'preheat/preheat.fds').read_bytes()).hexdigest()!=manifest['preheat_input_sha256']:raise ValueError('Preheat input changed after preparation')
    status=json.loads((campaign/'preheat/run_status.json').read_text())
    if status.get('status')!='completed' or status.get('input_sha256')!=manifest['preheat_input_sha256'] or status.get('config_sha256')!=manifest['config_sha256']:raise ValueError('Completed preheat provenance does not match campaign')
    pre=campaign/'preheat';out=(pre/'v4_preheat.out').read_text(errors='replace')
    stop=re.findall(r'STOP:\s*([^\r\n]+)',out)
    if not stop or stop[-1].strip()!='FDS completed successfully (CHID: v4_preheat)':raise ValueError('Preheat not successfully completed')
    rows=read_devc(pre/'v4_preheat_devc.csv');end=c['preheat_seconds']
    if abs(rows[-1]['Time']-end)>1e-3:raise ValueError('Incomplete preheat time')
    report=readiness(rows,c);dump(campaign/'readiness.json',report)
    if not report['ready']:raise ValueError('Oven not ready according to measured criteria. See readiness.json; do not force the cooking run.')
    if (campaign/'bake/bake.fds').exists():
        prior=json.loads((campaign/'bake/transfer.json').read_text())
        if prior['config_sha256']!=manifest['config_sha256'] or prior['bake_input_sha256']!=hashlib.sha256((campaign/'bake/bake.fds').read_bytes()).hexdigest():raise ValueError('Existing bake input/config no longer matches provenance')
        for name,digest in prior['source_sha256'].items():
            if hashlib.sha256((pre/name).read_bytes()).hexdigest()!=digest:raise ValueError('Warmup outputs changed after bake preparation')
        print('Existing bake input and source hashes verified. No solver has been launched.')
        return
    plans=json.loads((pre/'profiles.json').read_text());groups={z:[] for z in ZONES};contacts={};sources={name:hashlib.sha256((pre/name).read_bytes()).hexdigest() for name in ['v4_preheat_devc.csv','v4_preheat.out','profiles.json']}
    for p in plans:
        path=pre/p['file'];pairs=read_profile(path,end,p['thickness_m'],p,c['cell_size_m']);groups[p['zone']].append(pairs)
        sources[p['file']]=hashlib.sha256(path.read_bytes()).hexdigest()
        if p['contact']:contacts[p['contact']]=pairs
    profiles={}
    for zone,entries in groups.items():
        if not entries:raise ValueError(f'Missing {zone} profiles')
        depths=sorted(set(d for pair in entries for d,_ in pair))
        profiles[zone]=[(d,sum(interp(pair,d) for pair in entries)/len(entries)) for d in depths]
    f=c['food'];th=f['thickness_m'];eps=f['contact_transition_m']
    for n in [1,2]:
        floor=contacts[n]
        profiles[f'PIZZA_{n}']=[(0,c['pizza_initial_C']),(th-eps,c['pizza_initial_C'])]+[(th+d,t) for d,t in floor]
    transfer={'profiles':profiles,'gas_C':{k:rows[-1]['gas_'+k] for k in ['L','R','REAR','FLUE']},'preheat_seconds':end,'source_sha256':sources,'method':'Representative 1D solid profiles and regional gas temperatures. No velocities/species/radiation restart.'}
    build_stage(campaign/'bake',c,bake=True,transfer=transfer)
    transfer['config_sha256']=manifest['config_sha256']
    transfer['bake_input_sha256']=hashlib.sha256((campaign/'bake/bake.fds').read_bytes()).hexdigest()
    dump(campaign/'bake/transfer.json',transfer)
    print('Bake input prepared from completed hot-state data. No solver has been launched.')

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare');a.add_argument('--output',type=Path,required=True);a.add_argument('--config',type=Path,default=HERE/'campaign_config.json')
    a=sub.add_parser('prepare-bake');a.add_argument('--campaign',type=Path,required=True)
    args=p.parse_args()
    if args.cmd=='prepare':prepare(args.output,args.config)
    else:prepare_bake(args.campaign)

if __name__=='__main__':main()
