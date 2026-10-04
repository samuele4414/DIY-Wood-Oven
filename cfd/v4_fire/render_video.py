"""Render a deterministic scientific animation from the exported FDS fields.

Pillow draws the geometry; NumPy projects the Smoke3D node fields. Gaussian
reconstruction avoids a point-grid display. Emission/opacity are illustrative,
not an optical flame model. No artificial flame motion or rotating pizzas.
"""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE=Path(__file__).resolve().parent
DATA=HERE/'web'/'data'
OUT=HERE/'exports'
W,H=1280,720
BG=(14,23,31); TEXT=(231,237,237); MUTED=(148,169,181); AMBER=(255,202,124)
FONT=Path('C:/Windows/Fonts')
def font(n,bold=False):return ImageFont.truetype(str(FONT/('segoeuib.ttf' if bold else 'segoeui.ttf')),n)
RIGHT=np.array([.88,.475,0]); RIGHT/=np.linalg.norm(RIGHT)
EYE=np.array([.475,-.88,.7]); EYE/=np.linalg.norm(EYE)
UP=np.cross(EYE,RIGHT); UP/=np.linalg.norm(UP)
TARGET=np.array([.395,.29,.20])

def project(points):
    v=np.asarray(points)-TARGET
    return np.stack((430+550*(v@RIGHT),330-550*(v@UP)),axis=-1)

def poly(draw,points,fill=None,outline=None,width=1):
    p=[tuple(v) for v in project(points)]
    if fill:draw.polygon(p,fill=fill)
    if outline:draw.line(p+[p[0]],fill=outline,width=width)

def curve(draw,points,fill,width=1):draw.line([tuple(v) for v in project(points)],fill=fill,width=width)

def circle(x,y,r,z):
    t=np.linspace(0,2*np.pi,100)
    return np.column_stack((x+r*np.cos(t),y+r*np.sin(t),np.full_like(t,z)))

def roof(y):
    edge=0 if y<=.41 else .14*(y-.41)/.25
    x=np.linspace(edge,.79-edge,70)
    z=.19+.09*(1-((x-.395)/(.395-edge))**2)
    return np.column_stack((x,np.full_like(x,y),z))

def base_scene(case, speed=2.5, duration=60):
    thermal='thermal_model' in case
    preheat=case.get('pizza_present') is False
    hot_start=case['id']=='v4_bake'
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    d.text((44,27),'V4  /  MODELLO TERMICO' if thermal else 'V4  /  SIMULAZIONE CFD',font=font(17,True),fill=AMBER)
    title='Preriscaldamento del forno vuoto' if preheat else ('Pizza inserita nel forno caldo' if hot_start else ('Fiamma, fumi e primo riscaldamento' if thermal else 'Fiamma e fumi nella camera di cottura'))
    d.text((44,55),title,font=font(30,True),fill=TEXT)
    d.text((44,99),f'Run FDS • {duration:g} s simulati • conduzione transitoria nei materiali' if thermal else 'Dati FDS • vista 3D in sezione • geometria di riferimento',font=font(17),fill=MUTED)
    d.rounded_rectangle((910,147,1238,624),radius=16,fill=(23,35,45),outline=(43,62,73))
    # Floor, trapezoid, and the narrower flat-roofed front vestibule.
    outline=[(0,0,0),(.79,0,0),(.79,.41,0),(.65,.66,0),(.14,.66,0),(0,.41,0)]
    poly(d,outline,fill=(139,130,110),outline=(184,175,151),width=2)
    poly(d,[(.035,-.08,0),(.755,-.08,0),(.755,0,0),(.035,0,0)],fill=(167,153,125),outline=(193,181,157))
    poly(d,[(.035,-.08,0),(.755,-.08,0),(.755,-.08,-.027),(.035,-.08,-.027)],fill=(103,102,94))
    for x,y in ([] if preheat else case['pizza_centers']):
        poly(d,circle(x,y,.16,.006),fill=(211,199,171),outline=(236,224,195),width=2)
        poly(d,circle(x,y,.15,.016),fill=(193,137,73),outline=(244,204,140),width=3)
        poly(d,circle(x,y,.133,.021),fill=(177,91,44))
        # Static illustrative toppings, unrelated to the thermal field.
        for a,r in [(0,.06),(1.4,.07),(2.7,.065),(4.1,.073),(5.2,.06)]:
            poly(d,circle(x+r*np.cos(a),y+r*np.sin(a),.025,.022),fill=(234,206,152))
    poly(d,[(.25,.475,.002),(.525,.475,.002),(.525,.625,.002),(.25,.625,.002)],fill=(59,49,40),outline=(138,99,64))
    # A transparent wire outline is intentional: it exposes the CFD interior.
    for y in [0,.205,.41,.66]:curve(d,roof(y),(69,98,112),1)
    for side in [0,1]:
        curve(d,[tuple(roof(y)[-1 if side else 0]) for y in np.linspace(0,.66,40)],(88,117,130),2)
    for x,y in [(0,0),(.79,0),(.14,.66),(.65,.66)]:curve(d,[(x,y,0),(x,y,.19)],(69,98,112))
    poly(d,[(.035,-.08,.16),(.755,-.08,.16),(.755,0,.16),(.035,0,.16)],outline=(79,108,123))
    for x in [.035,.755]:curve(d,[(x,-.08,0),(x,-.08,.16)],(96,126,139),2)
    for theta in np.linspace(0,2*np.pi,8,endpoint=False):
        x=.395+.065*np.cos(theta);y=.045+.065*np.sin(theta)
        curve(d,[(x,y,.16),(x,y,.70)],(51,75,90))
    curve(d,circle(.395,.045,.065,.70),(105,132,145),2)
    d.text((44,601),'Camino sezionato a 70 cm per rendere leggibile la camera.',font=font(15),fill=MUTED)
    d.text((934,170),'COME LEGGERE IL CAMPO',font=font(15,True),fill=AMBER)
    d.text((934,206),'Arancio / giallo',font=font(19,True),fill=TEXT)
    d.text((934,235),'Rilascio di calore nella fiamma',font=font(15),fill=MUTED)
    d.text((934,272),'Grigio',font=font(19,True),fill=TEXT)
    d.text((934,301),'Fuliggine trasportata dai gas',font=font(15),fill=MUTED)
    d.text((934,341),'Colore e opacità illustrativi.',font=font(15),fill=MUTED)
    d.text((934,363),'Nessun movimento aggiunto.',font=font(15),fill=MUTED)
    d.line((934,405,1215,405),fill=(53,72,83))
    d.text((934,430),'18,75 kW',font=font(28,True),fill=TEXT)
    d.text((934,466),'Sorgente equivalente • rampa 5 s',font=font(15),fill=MUTED)
    d.text((934,506),'Celle CFD: 25 mm',font=font(17),fill=TEXT)
    d.text((934,537),'Pizze Ø30 cm • piatti Ø32 cm',font=font(15),fill=MUTED)
    d.text((934,579),f'Riproduzione circa {speed:.1f}×'.replace('.',','),font=font(16),fill=AMBER)
    d.line((44,645,1238,645),fill=(53,72,83))
    if thermal:
        # Replace the baseline legend with actual probe readings, drawn per frame.
        d.rectangle((929,163,1220,562),fill=(23,35,45))
        d.text((934,170),'CAMPI DELLA COMBUSTIONE',font=font(15,True),fill=AMBER)
        d.text((934,205),'Arancio / giallo: rilascio termico',font=font(15),fill=MUTED)
        d.text((934,234),'Grigio: fuliggine nei gas',font=font(15),fill=MUTED)
        d.text((934,267),'Colore e opacità illustrativi.',font=font(15),fill=MUTED)
        d.line((934,307,1215,307),fill=(53,72,83))
        d.text((934,329),'SONDE SUPERFICIE  /  °C',font=font(15,True),fill=AMBER)
        labels=['Piano 1','Piano 2','Volta'] if preheat else ['Pizza 1','Pizza 2','Piano']
        for label,y in zip(labels,[366,411,456]):
            d.text((934,y),label,font=font(19),fill=TEXT)
        d.text((934,497),'Valori puntuali, non medie.',font=font(14),fill=MUTED)
        start='Forno caldo, pizze fredde' if hot_start else f"Partenza a freddo: {case.get('ambient_temperature_C',25):g} °C"
        d.text((934,523),start,font=font(16),fill=TEXT)
        d.text((934,550),f"Sorgente prescritta: {case.get('fire_hrr_kw',18.75):g} kW",font=font(14),fill=MUTED)
        note='Forno vuoto, profili termici salvati.' if preheat else ('Pizze ferme, calore latente apparente.' if hot_start else 'Pizze ferme, senza evaporazione.')
        d.text((44,661),'PROTOTIPO • Gas equivalente al legno, senza pirolisi dei ciocchi. '+note,font=font(15),fill=MUTED)
        d.text((44,686),'I colori della geometria sono illustrativi. Le sonde riportano le temperature calcolate; non è una prova di cottura.',font=font(14),fill=MUTED)
    else:
        d.text((44,661),'CASO PRELIMINARE • Propano equivalente, temperature dei solidi imposte, pizze ferme nella CFD.',font=font(16),fill=MUTED)
        d.text((44,686),'Il nuovo modello termico è una simulazione separata.',font=font(14),fill=MUTED)
    return im


def load_fields(data):
    fields=[]
    for m in data['meshes']:
        nx,ny,nz=m['shape'];n=nx*ny*nz
        zz,yy,xx=np.meshgrid(m['coordinates']['z'],m['coordinates']['y'],m['coordinates']['x'],indexing='ij')
        xyz=np.column_stack((xx.ravel(),yy.ravel(),zz.ravel()))
        uv=project(xyz).round().astype(int)
        mask=(xyz[:,2]>=0)&(xyz[:,2]<=.70)&(uv[:,0]>=35)&(uv[:,0]<885)&(uv[:,1]>=150)&(uv[:,1]<590)
        # The common node plane belongs to the lower mesh only.
        if m['id']!=1:mask &= xyz[:,2]>.350001
        for kind in ['fire','smoke']:
            raw=np.fromfile(DATA/m[kind]['file'],dtype=np.uint8)
            if len(raw)!=n*len(m[kind]['times']):raise ValueError('Invalid field length')
            fields.append(dict(kind=kind,uv=uv[mask],values=raw.reshape(-1,n)[:,mask],times=np.array(m[kind]['times']),maxima=m[kind]['maxima']))
    return fields


def smooth(a):
    # Three separable box filters approximate a Gaussian without quantising
    # small soot concentrations to 8-bit before reconstruction.
    radius=5;window=2*radius+1
    for _ in range(3):
        for axis in [0,1]:
            pad=[(0,0),(0,0)];pad[axis]=(radius,radius)
            padded=np.pad(a,pad)
            pad[axis]=(1,0)
            integral=np.pad(np.cumsum(padded,axis=axis,dtype=np.float64),pad)
            lo=[slice(None),slice(None)];hi=lo.copy()
            lo[axis]=slice(None,-window);hi[axis]=slice(window,None)
            a=(integral[tuple(hi)]-integral[tuple(lo)])/window
    return np.maximum(a,0)


def load_probes(data):
    if 'thermal_model' not in data['case']:return None
    path=Path(data['source_run'])/(data['case']['id']+'_devc.csv')
    with path.open() as file:
        rows=list(csv.reader(file))
    labels=[s.strip().strip('"') for s in rows[1]]
    values=np.array([[float(v) for v in row] for row in rows[2:] if row])
    names=['Time','pizza_1_surface','pizza_2_surface','floor_surface']
    actual=['Time','floor_p1_C','floor_p2_C','vault_p1_F'] if data['case'].get('pizza_present') is False else names
    result={name:values[:,labels.index(source)] for name,source in zip(names,actual)}
    if np.any(np.diff(result['Time'])<=0):raise ValueError('Probe timestamps are not increasing')
    return result


def render_frame(base,fields,t,end_time=29.61274,probes=None,preheat=False):
    power=np.zeros((H,W),np.float32);soot=np.zeros_like(power)
    for field in fields:
        f=int(np.argmin(abs(field['times']-t)));v=field['values'][f].astype(float)/254
        if field['kind']=='smoke':v*=field['maxima'][f]*8700*.025*4
        target=power if field['kind']=='fire' else soot
        np.add.at(target,(field['uv'][:,1],field['uv'][:,0]),v)
    # This is a qualitative projected-volume visualisation, not radiometry.
    p=smooth(power);s=smooth(soot)
    rgb=np.asarray(base,dtype=float)
    sa=(1-np.exp(-s*40))*.58
    rgb=rgb*(1-sa[...,None])+np.array([139,157,167])*sa[...,None]
    fa=1-np.exp(-p*85)
    temperature_colour=np.clip(p*32,0,1)  # brightness palette, NOT gas temperature
    fire=np.stack((np.full_like(p,255),70+180*temperature_colour,10+95*temperature_colour),axis=-1)
    rgb=rgb*(1-fa[...,None])+fire*fa[...,None]
    im=Image.fromarray(np.uint8(np.clip(rgb,0,255)));d=ImageDraw.Draw(im)
    d.rounded_rectangle((44,152,303,201),radius=10,fill=(27,42,53),outline=(65,91,106))
    d.text((61,161),f'Tempo simulato  {t:04.1f} s',font=font(21,True),fill=TEXT)
    d.line((44,625,884,625),fill=(45,64,76),width=3)
    d.line((44,625,44+840*t/end_time,625),fill=AMBER,width=3)
    if probes is not None:
        for key,y in [('pizza_1_surface',361),('pizza_2_surface',406),('floor_surface',451)]:
            value=np.interp(t,probes['Time'],probes[key])
            d.text((1115,y),f'{value:.1f}'.replace('.',','),font=font(27,True),fill=(129,223,220))
        points=[('1',(.21,.205,0)),('2',(.58,.205,0)),('V',(.21,.12,.25))] if preheat else [('1',(.21,.205,.025)),('2',(.58,.205,.025)),('P',(.395,.20,0))]
        for label,(x,y,z) in points:
            px,py=project([[x,y,z]])[0]
            d.ellipse((px-11,py-11,px+11,py+11),fill=(20,44,51),outline=(129,223,220),width=2)
            d.text((px-5,py-10),label,font=font(14,True),fill=TEXT)
    return im


def main():
    global DATA,OUT
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--thermal',action='store_true');parser.add_argument('--data',type=Path);parser.add_argument('--output',type=Path);a=parser.parse_args()
    if a.thermal:
        DATA=HERE/'web'/'thermal-data';OUT=HERE/'exports'/'termico'
    if a.data:DATA=a.data
    if a.output:OUT=a.output
    OUT.mkdir(parents=True,exist_ok=True);data=json.loads((DATA/'volume.json').read_text(encoding='utf-8'))
    thermal='thermal_model' in data['case'];preheat=data['case'].get('pizza_present') is False
    times=data['meshes'][0]['fire']['times'];end_time=times[-1]
    base=base_scene(data['case'],end_time/(len(times)/5),end_time);fields=load_fields(data);probes=load_probes(data)
    hero=render_frame(base,fields,end_time if thermal else 23.,end_time,probes,preheat);hero.save(OUT/'v4_cfd_anteprima.png')
    if a.preview:return
    frames=[]
    sys.path.insert(0,str(Path.home()/'.cache/forno-video/python'))
    import imageio_ffmpeg
    writer=imageio_ffmpeg.write_frames(str(OUT/'v4_cfd_fiamma_fumi.mp4'),(W,H),fps=5,codec='libx264',pix_fmt_out='yuv420p',quality=8,output_params=['-threads','1','-movflags','+faststart','-r','25'])
    writer.send(None)
    for i,t in enumerate(times):
        im=render_frame(base,fields,t,end_time,probes,preheat);writer.send(np.asarray(im))
        frames.append(im.resize((960,540),Image.Resampling.LANCZOS))
        if i%10==0:print(f'Frame {i+1}/{len(times)}',flush=True)
    writer.close()
    # A common palette prevents colour flicker between frames.
    palette=hero.resize((960,540)).quantize(colors=160)
    frames=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    frames[0].save(OUT/'v4_cfd_fiamma_fumi.gif',save_all=True,append_images=frames[1:],duration=200,loop=0,optimize=False)
    caveats=['prescribed generic wood-gas release',data['case'].get('thermal_model'),'1D transient solid conduction','no resolved water loss or CFD pizza rotation','not an optical flame model'] if thermal else ['prescribed propane fire','fixed solid temperatures','no CFD pizza rotation','not an optical flame model']
    provenance={'source_run':data['source_run'],'source_manifest':str(DATA/'volume.json'),'frames':len(times),'simulation_times_s':times,'playback_fps':5,'method':'orthographic Gaussian reconstruction of actual FDS HRRPUV and soot node fields; qualitative palette and opacity','clipped_chimney_z_m':.70,'caveats':caveats}
    if probes is not None:
        renamed={'pizza_1_surface':'floor_p1_C','pizza_2_surface':'floor_p2_C','floor_surface':'vault_p1_F'} if preheat else {}
        provenance['final_probe_values_C']={renamed.get(k,k):float(v[-1]) for k,v in probes.items() if k!='Time'}
    (OUT/'provenienza.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(str(OUT/'v4_cfd_fiamma_fumi.mp4'),flush=True)


if __name__=='__main__':main()
