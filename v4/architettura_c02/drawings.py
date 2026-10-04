"""SVG engineering SCHEMES, not manufacturing drawings or integrated CAD."""
from html import escape
import math

INK = "#223542"
BLUE = "#267999"
GREEN = "#38775c"
RED = "#b54a36"
PURPLE = "#85609c"
STONE = "#e8d8b6"
STEEL = "#b5c1c8"


def num(value, decimals=1):
    return f"{value:.{decimals}f}".replace(".", ",")


class Sheet:
    def __init__(self, title, subtitle, number):
        self.arrow_id = f"arrow-t{number:02d}"
        self.parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="950"
viewBox="0 0 1400 950" role="img" aria-label="{escape(title, quote=True)}">
<title>{escape(title)}</title><desc>{escape(subtitle)}. Studio non esecutivo.</desc>
<defs><marker id="{self.arrow_id}" viewBox="0 0 10 10" refX="9" refY="5"
markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker></defs>
<style>text{{font-family:Arial,sans-serif;fill:{INK}}}
.small{{font-size:18px}} .note{{font-size:20px}} .label{{font-size:22px}}
.subtitle{{font-size:20px;fill:#526673}} .title{{font-size:32px;font-weight:700}}
.dim{{font-size:19px}}</style>
<rect width="1400" height="950" fill="#fff"/>
<path d="M40 95 H1360 M40 880 H1360" fill="none" stroke="#c8d3d9"/>
<text x="40" y="48" class="title">{escape(title)}</text>
<text x="40" y="78" class="subtitle">{escape(subtitle)}</text>
<text x="40" y="911" class="small">C02 · quote/riserve in mm salvo indicazione · NON ESECUTIVO · 03/10/2026</text>
<text x="1345" y="911" text-anchor="end" class="small">T{number:02d}</text>''']

    def text(self, x, y, lines, cls="note", anchor="start", colour=None):
        if isinstance(lines, str):
            lines = [lines]
        style = f' style="fill:{colour}"' if colour else ""
        spans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else 29}">{escape(str(line))}</tspan>' for i, line in enumerate(lines))
        self.parts.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{style}>{spans}</text>')

    def rect(self, x, y, w, h, fill="none", stroke=INK, dash=False, opacity=1):
        self.parts.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}" stroke="{stroke}" stroke-width="2" opacity="{opacity}"{self.dashed(dash)}/>')

    @staticmethod
    def dashed(dash):
        return ' stroke-dasharray="9 6"' if dash else ""

    def line(self, x1, y1, x2, y2, colour=INK, dash=False, arrow=False, both=False, width=2):
        markers = f' marker-end="url(#{self.arrow_id})"' if arrow else ""
        if both:
            markers += f' marker-start="url(#{self.arrow_id})"'
        self.parts.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{colour}" stroke-width="{width}"{self.dashed(dash)}{markers}/>')

    def polygon(self, points, fill="none", stroke=INK, dash=False, opacity=1):
        points = " ".join(f"{x:g},{y:g}" for x, y in points)
        self.parts.append(f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="2" opacity="{opacity}"{self.dashed(dash)}/>')

    def circle(self, x, y, r, fill="none", stroke=INK, dash=False):
        self.parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="{r:g}" fill="{fill}" stroke="{stroke}" stroke-width="2"{self.dashed(dash)}/>')

    def path(self, d, colour=INK, arrow=False, dash=False, width=3):
        marker = f' marker-end="url(#{self.arrow_id})"' if arrow else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{width}"{self.dashed(dash)}{marker}/>')

    def dimension(self, x1, y1, x2, y2, label):
        self.line(x1, y1, x2, y2, colour="#526673", arrow=True, both=True, width=1.2)
        self.text((x1 + x2) / 2, (y1 + y2) / 2 - 9, label, cls="dim", anchor="middle")

    def finish(self):
        return "\n".join(self.parts) + "\n</svg>\n"


def octagon(cx, cy, across_flats, vertex_angle=math.pi / 8):
    r = across_flats / (2 * math.cos(math.pi / 8))
    return [(cx + r * math.cos(vertex_angle + i * math.pi / 4),
             cy + r * math.sin(vertex_angle + i * math.pi / 4)) for i in range(8)]


def plan(cfg, v4, results):
    s = Sheet("PIANTA / Due moduli indipendenti", "Geometria V4 in proiezione; componenti inferiori sono riserve, non prodotti selezionati", 1)
    scale = .76
    xy = lambda x, y: (80 + x * scale, 640 - y * scale)
    width = v4["program_constraints"]["cooking_floor"]["width"]
    depth = v4["program_constraints"]["cooking_floor"]["depth"]
    lay = v4["current_layout_candidate"]
    rear = lay["firebox_y_range"][1]
    inset = (width - lay["firebox_width_rear"]) / 2
    s.polygon([xy(0, depth), xy(width, depth), xy(width-inset, rear), xy(inset, rear)], fill="#f1e2d4")
    s.rect(*xy(0, depth), width*scale, depth*scale, fill="#f5eee0")
    s.text(*xy(width / 2, 545), ["FOCOLARE POSTERIORE", "botola V4 300 × 140"], anchor="middle")
    hx = (width - lay["rear_loading_hatch_clear_opening"]["width"]) / 2
    s.line(*xy(hx, rear), *xy(width-hx, rear), colour=RED, width=7)
    for i, ((cx, cy), mod) in enumerate(zip(v4["program_constraints"]["rotating_discs"]["centres"], results["mechanical"]["modules"]), 1):
        x, y = xy(cx, cy)
        s.circle(x, y, 160*scale, fill=STONE)
        x0, x1, y0, y1 = mod["xy_bounds_mm"]
        s.rect(*xy(x0, y1), (x1-x0)*scale, (y1-y0)*scale, fill="#d6eaf4", stroke=BLUE, dash=True, opacity=.85)
        dx = 65 if i == 1 else -115
        s.rect(*xy(cx+dx, cy+35), 50*scale, 70*scale, fill="#c1d6df", stroke=BLUE)
        s.circle(x, y, 17, fill=STEEL, stroke=BLUE)
        motor_cx, motor_cy = xy(cx+dx+25, cy)
        s.line(x+10*(1 if i == 1 else -1), y-9, motor_cx, motor_cy-12, colour=BLUE)
        s.line(x+10*(1 if i == 1 else -1), y+9, motor_cx, motor_cy+12, colour=BLUE)
        s.line(x-26, y, x+26, y, dash=True, width=1)
        s.line(x, y-26, x, y+26, dash=True, width=1)
        s.text(x, y-42, f"DISCO {i} / Ø320", cls="label", anchor="middle")
        s.text(x, y+84, f"({cx}; {cy})", cls="small", anchor="middle")
    fy = lay["front_door_plane_y"]
    mouth = lay["door_clear_opening"]["width"]
    s.line(*xy((width-mouth)/2, fy), *xy((width+mouth)/2, fy), colour=INK, width=5)
    s.text(*xy(width/2, fy-35), "BOCCA V4 720 × 160", cls="small", anchor="middle")
    s.dimension(*xy(0, -54), *xy(width, -54), "790")
    s.dimension(730, xy(0, depth)[1], 730, xy(0, 0)[1], "410")
    s.dimension(*xy(210, 45), *xy(580, 45), "370 tra assi")
    s.line(210, 790, 210, 840, colour=BLUE, arrow=True)
    s.line(525, 790, 525, 840, colour=BLUE, arrow=True)
    s.text(365, 785, "ESTRAZIONE FRONTALE A FREDDO", cls="small", anchor="middle")
    s.text(365, 867, "Riserva servizio 300 · tratto non in scala", cls="small", anchor="middle")
    s.text(825, 155, "Mantenuti dalla V4", cls="label")
    s.text(825, 193, ["Dischi e centri originali.", "Focolare posteriore / camino anteriore.", "Nessuno spostamento per far stare il motore."])
    s.text(825, 320, "Riserve inferiori C02", cls="label", colour=BLUE)
    s.text(825, 358, ["2 × moduli 240 × 180 in pianta.", "Separazione nominale moduli: 130.", "Motore laterale: h70 riservati.", "Cartuccia distinta: h45 riservati.", "Cinghia/giunti: solo nel vano qualificato."])
    s.text(825, 548, "Vano e manutenzione", cls="label")
    s.text(825, 586, ["Proposta: 160 netti, non 120 congelati.", "Riserva parallela: 117; residuo: 43.", "Carter, cavi e fissaggi non disegnati.", "Estrazione senza sollevare il forno:", "sequenza da dimostrare sul banco."])
    s.rect(810, 760, 525, 88, fill="#fff1e5", stroke="#c59460")
    s.text(830, 796, ["Questi rettangoli NON selezionano motori", "e NON provano temperatura o accessibilità."], cls="small")
    return s.finish()


def rotating_module(cfg, v4, results):
    m = results["mechanical"]
    s = Sheet("DISCO / Catena di carico e separazione termica", "Schema funzionale di un modulo; scala non uniforme, quote del carrier ancora da dettagliare", 2)
    s.rect(135, 205, 560, 40, fill=STONE)
    s.text(415, 190, "Pietra Ø320 × 20 / flottante", cls="label", anchor="middle")
    s.rect(145, 251, 540, 10, fill=STEEL)
    s.rect(150, 273, 530, 90, fill="#d9e6d2", stroke=GREEN)
    # Wide spreader, discrete structural supports; insulation is NOT the load path.
    for x in (235, 585):
        s.rect(x, 261, 30, 110, fill="#f2e6d9", stroke=RED)
    s.rect(140, 369, 550, 25, fill=STEEL)
    s.text(415, 321, ["Isolante incapsulato / nominale 50", "NON assunto portante"], cls="small", anchor="middle")
    s.rect(100, 424, 680, 262, fill="#f5f9fb", stroke=BLUE, dash=True)
    s.rect(405, 394, 20, 230, fill=STEEL)
    s.line(110, 436, 387, 436, colour=INK, width=5)
    s.line(441, 436, 770, 436, colour=INK, width=5)
    s.path("M387 436 V451 H400 M441 436 V451 H430", colour=INK, width=2)
    s.rect(390, 475, 50, 30, fill="#b6d7e6", stroke=BLUE)
    s.rect(602, 520, 110, 120, fill="#b6d7e6", stroke=BLUE)
    s.rect(633, 475, 45, 30, fill="#b6d7e6", stroke=BLUE)
    s.rect(645, 505, 20, 15, fill=STEEL, stroke=BLUE)
    s.line(416, 478, 651, 478, colour=BLUE, width=3)
    s.line(416, 502, 651, 502, colour=BLUE, width=3)
    s.rect(378, 529, 75, 78, fill="#d7e4eb", stroke=BLUE)
    for y in (542, 584):
        s.line(380, y, 449, y, colour=BLUE, width=8)
    s.line(120, 618, 570, 618, colour=INK, width=7)
    s.line(570, 650, 735, 650, colour=INK, width=7)
    s.line(350, 607, 480, 607, colour=INK, width=5)
    s.line(350, 607, 350, 618, colour=INK, width=5)
    s.line(480, 607, 480, 618, colour=INK, width=5)
    s.line(602, 640, 602, 650, colour=INK, width=5)
    s.line(712, 640, 712, 650, colour=INK, width=5)
    s.text(412, 579, "h45*", cls="small", anchor="middle")
    s.text(657, 565, ["Motore", "h70*", "24 V*"], cls="small", anchor="middle")
    s.text(120, 726, ["* Riserve / candidati, non componenti commerciali.", "Vano netto 160; stack laterale 117; residuo 43.", "Cartuccia prende peso e momento; motore dà coppia."], cls="note")
    s.dimension(60, 424, 60, 686, "160*")
    s.line(686, 257, 825, 240, colour=INK)
    s.line(610, 279, 825, 304, colour=RED)
    s.line(690, 380, 825, 390, colour=INK)
    s.line(741, 436, 825, 475, colour=INK)
    s.text(845, 235, ["Ripartitore caldo Ø310 candidato.", "Appoggio ampio, niente pietra serrata."], cls="small")
    s.text(845, 309, ["Supporti ceramici strutturali qualificati.", "Non tre carichi puntuali sulla pietra."], cls="small", colour=RED)
    s.text(845, 387, ["Carrier: riserva altezza 15, NON lamiera 15.", "Fissaggi e stabilità a caldo da verificare."], cls="small")
    s.text(845, 477, ["Schermo fisso e labirinto ispezionabile.", "Raccoglibriciole separato dalla meccanica."], cls="small")
    s.text(845, 584, [f"Carico assiale di scenario: {num(m['assumed_axial_load_with_tool_N'])} N.",
                         f"Spinta al bordo: momento {num(m['tool_at_stone_edge_overturning_moment_Nm'])} Nm.",
                         "Misurare coppia sporco/caldo prima del motore.",
                         "Misurare anche il picco dopo spegnimento."], cls="small")
    s.rect(830, 748, 510, 100, fill="#fff1e5", stroke="#c59460")
    s.text(850, 780, ["L'isolamento non dimostra un vano freddo.", "Aria vano 50 °C: obiettivo, NON misura.", "La portanza e le temperature restano aperte."], cls="small")
    return s.finish()


def air_flue(cfg, v4, results):
    s = Sheet("ARIA–FUMI / Percorsi separati", "Sezione funzionale non quotata: forma di raccordi, distributori e attraversamenti ancora da integrare", 3)
    # Deliberately functional, not a geometrical longitudinal cut through a disc.
    s.rect(100, 425, 740, 235, fill="#fff8ed", stroke=INK)
    s.line(100, 425, 100, 540, width=6)
    s.text(72, 584, ["Bocca", "720 × 160"], cls="small", anchor="middle")
    s.rect(133, 658, 500, 22, fill=STONE)
    s.rect(665, 638, 175, 42, fill="#d8bc98")
    s.polygon([(100,425), (200,360), (480,330), (840,400)], fill="#e4eacf", stroke=GREEN)
    s.line(135, 397, 840, 427, colour=INK, width=4)
    s.text(643, 547, ["Focolare", "posteriore"], anchor="middle")
    s.rect(833, 492, 18, 110, fill="#d7dfe4")
    s.line(850, 546, 870, 567, colour=INK)
    s.text(875, 574, ["Botola ricarica 300 × 140", "Interferenza con l'aria", "da verificare"], cls="small")
    s.rect(160, 357, 330, 65, fill="#e8def0", stroke=PURPLE)
    s.polygon([(252,357), (312,280), (408,280), (434,357)], fill="#e8def0", stroke=PURPLE)
    s.rect(310, 122, 100, 158, fill=STEEL, stroke=INK)
    s.rect(337, 122, 46, 158, fill="#e8def0", stroke=PURPLE)
    s.path("M740 478 C700 451 580 449 473 394 L365 382 L365 153", colour=PURPLE, arrow=True, width=5)
    s.text(485, 235, ["Camino anteriore, asse V4 mantenuto.", "Collare/supporto da ingrandire.", "Continuità a porta chiusa da verificare."], cls="small")
    s.text(180, 480, ["Ingresso libero 640 × 30", "Collo rialzato 170 × 90", "Raccordo graduale a Ø130"], cls="small", colour=PURPLE)
    s.rect(135, 689, 665, 25, fill="#d8e6d3", stroke=GREEN)
    s.rect(135, 725, 665, 125, fill="#f2f7fa", stroke=BLUE)
    s.text(439, 772, ["VANO MECCANICO", "Ventilazione distinta da combustione e cenere"], cls="small", anchor="middle", colour=BLUE)
    s.rect(880, 693, 175, 50, fill="#e0eee3", stroke=GREEN)
    s.path("M1035 718 H847 V616 H797", colour=GREEN, arrow=True, width=5)
    s.path("M850 686 V594 H745", colour=GREEN, arrow=True, width=3)
    s.text(1080, 709, ["Presa 90 cm² NETTI*", "Griglia + condotto chiuso", "* punto di confronto"], cls="small", colour=GREEN)
    s.text(885, 806, ["Le uscite laterali e la ripartizione", "primaria/secondaria non sono quotate.", "Nessun passaggio aperto ai motori."], cls="small")
    s.text(980, 171, "Cosa manca per la nuova CFD", cls="label")
    s.text(980, 209, ["Forma tridimensionale reale.", "Perdite di presa e braci.", "Pulizia e tenuta a caldo.", "Aperture frontale/posteriore.", "Verifica vento e temperatura."], cls="small")
    s.rect(960, 398, 375, 155, fill="#fff1e5", stroke="#c59460")
    s.text(980, 432, ["L'area del passaggio non prova", "captazione né assenza di CO.", "La rete 1D non valida questo schema.", "Nessuna nuova CFD eseguita."], cls="small")
    return s.finish()


def collar_pressure(cfg, v4, results):
    f = results["flue_geometry"]
    p = f["collar_plate_budget"]
    s = Sheet("CAMINO / Collare, piastra e tiraggio", "Confronti di inviluppo e rete 1D a temperature assegnate: nessuna approvazione di captazione", 4)
    scale = .67
    cx, cy = 245, 342
    s.polygon(octagon(cx,cy,p["proposed_base_outer_across_flats_mm"]*scale), fill="#e6edf1", stroke=INK)
    s.polygon(octagon(cx,cy,340*scale), stroke=RED, dash=True)
    w,h = p["rectangle_with_mounting_and_cover_mm"]
    s.rect(cx-w*scale/2, cy-h*scale/2, w*scale,h*scale, stroke=RED, dash=True)
    w,h = p["catalogue_A_B_mm"]
    s.rect(cx-w*scale/2, cy-h*scale/2, w*scale,h*scale, fill="#d0e0ea",stroke=BLUE)
    s.circle(cx,cy,90*scale, fill="#f8fbfd",stroke=BLUE)
    s.text(cx,cy-10,["Tubo Ø180", "DN130/25"],cls="small",anchor="middle")
    s.text(65,145,"BASE / inviluppo prudenziale", cls="label")
    s.text(65,543,["Piastra catalogo A238 / B306.", "Budget 260 × 328 con margine + cover.", f"Ottagono minimo: {num(p['min_regular_octagon_outer_across_flats_mm'])} tra facce.", "340 tratteggiato: NON contiene i vertici.", "440 riservati; CAD della piastra da chiedere."], cls="small")
    s.dimension(cx-147.4,525,cx+147.4,525,"440 esterni*")
    tcx,tcy=585,325
    s.polygon(octagon(tcx,tcy,260*.8),fill="#e6edf1",stroke=INK)
    s.circle(tcx,tcy,234*.8/2,fill="#f3f8f5",stroke=GREEN)
    s.circle(tcx,tcy,180*.8/2,fill="#d2e1e9",stroke=BLUE)
    s.polygon(octagon(tcx,tcy,f["C01_collar_top_across_flats_mm"]*.8,vertex_angle=0),stroke=RED,dash=True)
    s.text(470,145,"SOMMITÀ / cover 260*", cls="label")
    s.text(465,492,["C01: circa 140,4 tra facce.", "Catalogo 130/25: esterno 180.", "Budget 130/50: esterno 234*.", "Con margine 10 e cover 1:", "richiesti 256* → riserva 260.", "*50: non è il CAD di un prodotto."],cls="small")
    s.line(805,125,805,833,colour="#cad5db",width=1)
    rows={r["id"]:r for r in results["pressure_scenarios"]}
    selections=[("Base 60 / H1", "RIFERIMENTO_MATLAB_60_H1"),
                ("C02 90 / H1,5", "C02_PUNTO_DI_CONFRONTO"),
                ("T150 °C / K8 / vento 3 Pa", "C02_T150_K8_VENTO3")]
    s.text(845,145,"MARGINE PORTA CHIUSA / Pa",cls="label")
    s.text(845,180,"Confronto a lambda 2; non criterio di sicurezza",cls="small")
    xzero=1150
    for i,(label,key) in enumerate(selections):
        y=250+i*113
        value=rows[key]["closed_door_budget"]["margin_Pa"]
        xend=xzero+value*30
        s.text(845,y-24,label,cls="small")
        s.rect(min(xzero,xend),y,abs(xend-xzero),25,fill=GREEN if value>0 else RED,stroke=GREEN if value>0 else RED)
        s.text(xend+9 if value>0 else xend-9,y+20,num(value,2),cls="small",anchor="start" if value>0 else "end")
    s.line(xzero,221,xzero,522,colour=INK,width=1.3)
    s.text(xzero,550,"0",cls="small",anchor="middle")
    s.rect(830,587,505,224,fill="#fff1e5",stroke="#c59460")
    s.text(852,623,[f"Porta aperta: {num(rows['C02_PORTA_APERTA']['door_out_gas_kg_h'])} kg/h di gas uscenti", "nel modello 1D, NON massa di fumo/CO.", "H della rete: dal colmo caldo al terminale.", "Tubo H1000: utile 955; H500: utile 455.", "Peso e vento al telaio, non alla volta.", "Raccordo, DoP e temperature da qualificare."],cls="small")
    s.text(65,760,[f"Asse V4 mantenuto; base 440: sporgenza frontale {num(results['body_budget']['collar_base_plan_overhang_from_C01_front_mm'])} mm rispetto C01.", "Ottagono: normali facce X/Y e 45°; raccordo/scocca da integrare.", "L'ingombro completo non è ancora congelato."],cls="small")
    return s.finish()


def all_drawings(cfg, v4, results):
    return {"pianta_moduli.svg": plan(cfg,v4,results),
            "modulo_disco.svg": rotating_module(cfg,v4,results),
            "schema_aria_fumi.svg": air_flue(cfg,v4,results),
            "collare_tiraggio.svg": collar_pressure(cfg,v4,results)}
