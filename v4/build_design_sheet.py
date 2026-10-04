"""Produce the V4 design brief and a nominal 2D CAD reference, in millimetres."""
from pathlib import Path
from math import pi
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
for name, file in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts') / file)))
W,H = landscape(A4)
INK=HexColor('#17323D'); BLUE=HexColor('#246C89'); ORANGE=HexColor('#A66824')
PURPLE=HexColor('#72428F'); LIGHT=HexColor('#E7F0F4'); SAND=HexColor('#F2E7CF')
GREY=HexColor('#58666C'); PALE=HexColor('#F3F5F6'); LINE=HexColor('#CCD5D8')
PDF=OUT/'Forno_V4_Scheda_design.pdf'
c=canvas.Canvas(str(PDF), pagesize=(W,H))
c.setTitle('Forno V4 - Base per il design')
c.setAuthor('Progetto forno - bozza V4')
style=ParagraphStyle('body',fontName='Body',fontSize=9.5,leading=13,textColor=INK)

def text(x,y,t,size=9,color=INK,bold=False,align='left'):
    c.setFillColor(color);c.setFont('Bold' if bold else 'Body',size)
    {'left':c.drawString,'center':c.drawCentredString,'right':c.drawRightString}[align](x,y,t)

def para(x,top,width,t,size=9.5,color=INK,leading=None):
    st=ParagraphStyle('p',parent=style,fontSize=size,leading=leading or size*1.4,textColor=color)
    p=Paragraph(t,st);_,hh=p.wrap(width,1000);p.drawOn(c,x,top-hh);return top-hh

def header(title,subtitle,page):
    text(36,H-39,'FORNO / V4',11,BLUE,True)
    text(W-36,H-39,'BASE PER IL DESIGN · 21.09.2026',9,GREY,align='right')
    text(36,H-70,title,22,INK,True)
    text(36,H-90,subtitle,10,GREY)
    c.setStrokeColor(LINE);c.line(36,42,W-36,42)
    text(36,27,'Quote in mm · Dimensioni interne nominali · Bozza per sviluppo della forma',8,GREY)
    text(W-36,27,f'V4 / {page} di 2',8,GREY,align='right')

def line(x1,y1,x2,y2,color=INK,width=.7,dash=None):
    c.setStrokeColor(color);c.setLineWidth(width);c.setDash(dash or [])
    c.line(x1,y1,x2,y2);c.setDash([])

def poly(points,fill=None,stroke=INK,width=.7):
    p=c.beginPath();p.moveTo(*points[0])
    for v in points[1:]:p.lineTo(*v)
    p.close();c.setStrokeColor(stroke);c.setLineWidth(width)
    if fill:c.setFillColor(fill)
    c.drawPath(p,stroke=1,fill=int(fill is not None))

def dims(x1,x2,y,label):
    line(x1,y,x2,y,GREY,.5)
    for x in (x1,x2):line(x,y-3,x,y+3,GREY,.5)
    text((x1+x2)/2,y+4,label,8,GREY,align='center')

def dimv(x,y1,y2,label):
    line(x,y1,x,y2,GREY,.5)
    for y in (y1,y2):line(x-3,y,x+3,y,GREY,.5)
    c.saveState();c.translate(x-5,(y1+y2)/2);c.rotate(90)
    text(0,0,label,8,GREY,align='center');c.restoreState()

def section_title(x,y,title):
    text(x,y,title,9,BLUE,True)

header('La base da cui partire','Due pizze, due piastre rotanti e caricamento della legna dal retro.',1)
sx,sy,scale=93,147,.43
xy=lambda x,y:(sx+x*scale,sy+y*scale)
poly([xy(0,-80),xy(790,-80),xy(790,0),xy(0,0)],LIGHT)
poly([xy(0,0),xy(790,0),xy(790,410),xy(0,410)],SAND)
poly([xy(0,410),xy(790,410),xy(650,660),xy(140,660)],HexColor('#F1D3AE'))
for n,x in enumerate([210,580],1):
    cx,cy=xy(x,205)
    c.setFillColor(HexColor('#CDE1E8'));c.setStrokeColor(BLUE);c.setLineWidth(1.2)
    c.circle(cx,cy,160*scale,fill=1,stroke=1)
    text(cx,cy+8,f'PIASTRA {n}',9,BLUE,True,align='center')
    text(cx,cy-7,'Ø320',12,BLUE,True,align='center')
    line(cx-4,cy,cx+4,cy,BLUE,.5);line(cx,cy-4,cx,cy+4,BLUE,.5)
text(*xy(395,525),'ZONA LEGNA',10,ORANGE,True,align='center')
text(*xy(395,491),'forma da sviluppare',9,ORANGE,align='center')
dims(*[xy(x,0)[0] for x in (0,790)],xy(0,746)[1],'790')
dims(*[xy(x,0)[0] for x in (140,650)],xy(0,690)[1],'510 attuale')
dimv(xy(-48,0)[0],xy(0,-80)[1],xy(0,0)[1],'80')
dimv(xy(-48,0)[0],xy(0,0)[1],xy(0,410)[1],'410')
dimv(xy(-48,0)[0],xy(0,410)[1],xy(0,660)[1],'250')
dimv(xy(-100,0)[0],xy(0,-80)[1],xy(0,660)[1],'740 interno')
dims(xy(210,0)[0],xy(580,0)[0],xy(0,375)[1],'interasse 370')
line(*xy(35,-80),*xy(755,-80),PURPLE,3)
text(*xy(395,-135),'PORTA ESTERNA - luce candidata 720 × 160',8,PURPLE,align='center')
line(*xy(245,660),*xy(545,660),ORANGE,2.5)
c.setStrokeColor(PURPLE);c.setLineWidth(1);c.setDash([4,3]);c.circle(*xy(395,45),95*scale)
c.setDash([1,3]);c.circle(*xy(395,45),65*scale);c.setDash([])
text(*xy(395,35),'C',10,PURPLE,True,align='center')
text(90,72,'C = camino proiettato dal tetto. Sovrapposizione alle pizze ammessa.',8,GREY)

rx,rw=471,334
section_title(rx,493,'DA CONSERVARE NEL PRIMO CONCEPT')
y=para(rx,481,rw,'<b>Piano in cordierite 790 × 410.</b><br/>Due piastre rotanti Ø320; supporti e trasmissioni sotto il piano da sviluppare.')
y=para(rx,y-12,rw,'<b>Centri delle piastre:</b> (210; 205) e (580; 205). Origine sul bordo anteriore sinistro del piano; x verso destra, y verso il retro.',9)
y=para(rx,y-10,rw,'Il modello di cottura considera pizze Ø300. Una piastra Ø320 non garantisce, da sola, una pizza utile Ø320.',9,GREY)
section_title(rx,y-24,'RIFERIMENTI MODIFICABILI')
y=y-37
for label,value in [('Avancorpo / profondità totale','80 / 740'),('Focolare, profondità attuale','250'),('Focolare, larghezze attuali','790 davanti / 510 dietro'),('Porta, luce interna candidata','720 × 160'),('Botola posteriore candidata','300 × 140')]:
    text(rx,y,label,9);text(rx+rw,y,value,9,INK,True,align='right')
    line(rx,y-6,rx+rw,y-6,LINE,.45);y-=24
y=para(rx,y-2,rw,'Il trapezio è una proposta. Può diventare più arrotondato, rettangolare o articolato: dopo la modifica si ricontrollano legna, braci, fiamma e percorso dei fumi.',9)
box_y=72;box_h=76
c.setFillColor(PALE);c.roundRect(rx-10,box_y,rw+20,box_h,6,stroke=0,fill=1)
para(rx,box_y+box_h-11,rw,'<b>790 × 740 NON è la base esterna.</b><br/>Pareti, isolamento, telaio, motori, maniglie e sportelli si aggiungono. Materiali e spessori devono essere scelti prima di chiudere l’ingombro esterno.',9)
c.showPage()

header('Forma libera, funzioni da conservare','Le sezioni mostrano il riferimento attuale, non impongono il disegno della volta.',2)
fx,fy,fs=49,339,.405
f=lambda x,z:(fx+x*fs,fy+z*fs)
section_title(48,488,'VOLTA ATTUALE / PORTA IN PROIEZIONE')
p=c.beginPath()
for i in range(101):
    x=790*i/100;z=190+90*(1-(2*x/790-1)**2)
    if i==0:p.moveTo(*f(x,z))
    else:p.lineTo(*f(x,z))
c.setStrokeColor(BLUE);c.setLineWidth(1.7);c.drawPath(p)
line(*f(0,0),*f(0,190),BLUE,1.2);line(*f(790,0),*f(790,190),BLUE,1.2)
line(*f(0,0),*f(790,0),BLUE,1.4)
line(*f(35,0),*f(35,160),PURPLE,1);line(*f(35,160),*f(755,160),PURPLE,1)
line(*f(755,160),*f(755,0),PURPLE,1)
text(*f(395,72),'720 × 160',10,PURPLE,align='center')
dimv(*[f(823,0)[0],f(0,0)[1],f(0,280)[1]],'280 attuale')
text(48,320,'Imposta attuale 190; profilo parabolico da ridisegnare.',8,GREY)
text(48,307,'Materiale della volta: acciaio isolato o refrattario, da scegliere.',8,GREY)

lx,ly,ls=455,339,.43
q=lambda y,z:(lx+y*ls,ly+z*ls)
section_title(454,488,'SEZIONE CENTRALE DELLA VARIANTE COMPATTA')
line(*q(0,0),*q(740,0),BLUE,1.5)
line(*q(0,0),*q(0,160),PURPLE,3)
line(*q(0,160),*q(0,280),BLUE,1.2)
line(*q(0,280),*q(60,280),BLUE,1.2)
line(*q(190,280),*q(740,280),BLUE,1.2)
line(*q(740,280),*q(740,0),BLUE,1.2)
line(*q(60,280),*q(60,320),PURPLE,1.2)
line(*q(190,280),*q(190,320),PURPLE,1.2)
line(*q(30,284),*q(220,284),PURPLE,1,dash=[3,2])
line(*q(80,0),*q(80,280),LINE,.6,dash=[1,3])
line(*q(125,4),*q(445,4),BLUE,3)
text(*q(530,80),'legna',9,ORANGE)
dims(q(0,0)[0],q(80,0)[0],ly-13,'80')
dims(q(80,0)[0],q(490,0)[0],ly-13,'410')
dims(q(490,0)[0],q(740,0)[0],ly-13,'250')
text(454,307,'Porta → bordo dischi 125; porta → centri dischi 285.',8,GREY)
text(454,294,'Camino C: x=395, y=45 dal bordo del piano; quota candidata.',8,GREY)

section_title(36,270,'COSA PUÒ MODIFICARE IL DESIGN')
columns=[36,174,477,W-36]
rows=[
 ('Camera di combustione','Contorno, raccordi e disposizione del volume posteriore.','Ricontrollare ciocchi da 250, carica, cenere, distanza dal piano e alimentazione dell’aria.'),
 ('Volta','Profilo, curvatura, altezza e materiale. Le quote 280/190 sono riferimenti.','Ricalcolare volume, superfici e scambi termici; verificare fiamma, pala e collettore alto.'),
 ('Guscio e struttura','Forma esterna, rivestimento, piedini, maniglie e accesso ai meccanismi.','Lasciare spazio a isolamento, dilatazioni, supporti della cordierite, motori e manutenzione.'),
 ('Porta e raccolta fumi','Forma della porta e integrazione del collettore nella copertura.','A porta chiusa, camera e camino restano collegati. Presa d’aria e captazione vanno verificate.'),
]
yy=255
for i,row in enumerate(rows):
    h=40
    c.setFillColor(PALE if i%2==0 else white);c.rect(36,yy-h,W-72,h,fill=1,stroke=0)
    for j,t in enumerate(row):para(columns[j]+8,yy-7,columns[j+1]-columns[j]-16,t,8.4,leading=11)
    line(36,yy-h,W-36,yy-h,LINE,.45);yy-=h
para(44,86,W-88,'<b>Da non congelare:</b> camino Ø130 e H1000 (confronti Ø150 / H1500), raccordo Ø190, presa d’aria netta 60-90 cm², spessori e giochi. Sono ipotesi di studio. La verifica a porta aperta resta irrisolta: definire prima il collettore, poi ripetere i calcoli e le prove.',8.5,leading=11)
c.save()

reader=PdfReader(str(PDF))
assert len(reader.pages)==2
extracted='\n'.join(page.extract_text() for page in reader.pages)
for expected in ['790','410','320','740','280','190','sovrapposizione']:
    assert expected.lower() in extracted.lower(), expected

# Minimal DXF drawing: nominal placement, explicitly not manufacturing profiles.
parts=[]
def pair(code,value):parts.extend([str(code),str(value)])
pair(0,'SECTION');pair(2,'HEADER');pair(9,'$ACADVER');pair(1,'AC1009')
pair(9,'$INSUNITS');pair(70,4);pair(0,'ENDSEC');pair(0,'SECTION');pair(2,'ENTITIES')
def cad_line(x1,y1,x2,y2,layer,color):
    for code,val in [(0,'LINE'),(8,layer),(62,color),(10,x1),(20,y1),(30,0),(11,x2),(21,y2),(31,0)]:pair(code,val)
def cad_polygon(points,layer,color):
    for a,b in zip(points,points[1:]+points[:1]):cad_line(*a,*b,layer,color)
cad_polygon([(0,0),(790,0),(790,410),(0,410)],'PIANO_NOMINALE',5)
cad_polygon([(0,-80),(790,-80),(790,0),(0,0)],'AVANCORPO_CANDIDATO',8)
cad_polygon([(0,410),(790,410),(650,660),(140,660)],'FOCOLARE_MODIFICABILE',30)
for x,y,rad,layer,color in [(210,205,160,'PIASTRE_NOMINALI',5),(580,205,160,'PIASTRE_NOMINALI',5),
                           (395,45,95,'COLLARE_PROIEZIONE_TETTO',6),(395,45,65,'CAMINO_PROIEZIONE_TETTO',6)]:
    for code,val in [(0,'CIRCLE'),(8,layer),(62,color),(10,x),(20,y),(30,0),(40,rad)]:pair(code,val)
cad_line(35,-80,755,-80,'PORTA_CANDIDATA',6)
cad_line(245,660,545,660,'BOTOLA_CANDIDATA',30)
for y,t in [(-145,'V4 - MILLIMETRI - GEOMETRIA INTERNA NOMINALE'),(-175,'NON PROFILI DI TAGLIO / NON BASE ESTERNA'),(-205,'CAMINO E COLLARE SONO PROIETTATI DAL TETTO')]:
    for code,val in [(0,'TEXT'),(8,'NOTE'),(62,7),(10,0),(20,y),(30,0),(40,13),(1,t)]:pair(code,val)
pair(0,'ENDSEC');pair(0,'EOF')
(ROOT/'Base_V4_riferimento_mm.dxf').write_text('\n'.join(parts)+'\n',encoding='ascii')
print(PDF)
print('PDF: 2 pagine; quote principali presenti. DXF: mm, geometria nominale e layer separati.')
