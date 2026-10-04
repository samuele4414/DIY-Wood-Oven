"""Build C01 drawings, offline 3D viewer, nominal CAD and engineering brief.

Python 3.11+, standard library only. Does NOT modify V4, MATLAB or CFD inputs.
"""
from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import io
import json
from pathlib import Path
import unicodedata
import unittest

from geometry import (HERE, build_case, hot_plan, load_inputs,
                      roof_at, section_polygon)
from render_scene import render

INK, GREY, BLUE = "#193345", "#607580", "#23779a"
ORANGE, PURPLE, GREEN = "#ad6630", "#9556a1", "#719264"


def fmt(value, digits=1):
    return f"{value:.{digits}f}".rstrip("0").rstrip(".") if digits else f"{value:.0f}"


class SVG:
    def __init__(self, title, subtitle, height=1050):
        self.height = height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="{height}" viewBox="0 0 1400 {height}" role="img"><title>{escape(title)}</title>',
                      '<rect width="100%" height="100%" fill="#ffffff"/>']
        self.text(60, 55, title, 27, INK, bold=True)
        self.text(60, 88, subtitle, 16, GREY)
        self.line(60, 110, 1340, 110, "#cbd6dc")

    def text(self, x, y, text, size=17, colour=INK, bold=False, anchor="start", rotate=None):
        transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
        self.parts.append(f'<text x="{x:.3f}" y="{y:.3f}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{colour}" text-anchor="{anchor}"{transform}>{escape(str(text))}</text>')

    def line(self, x1, y1, x2, y2, colour=INK, width=1.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{colour}" stroke-width="{width}"{d}/>')

    def poly(self, points, fill="none", stroke=INK, width=1.5, dash=None, opacity=1):
        p = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<polygon points="{p}" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{width}"{d}/>')

    def rect(self, x, y, width, height, fill="none", stroke=INK, dash=None):
        self.poly([(x, y), (x + width, y), (x + width, y + height), (x, y + height)], fill, stroke, dash=dash)

    def circle(self, x, y, radius, fill="none", stroke=INK, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius:.3f}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>')

    def footer(self):
        y = self.height - 60
        self.line(60, y, 1340, y, "#cbd6dc")
        self.text(60, y + 27, "C01 · STUDIO NON ESECUTIVO · Nessun profilo di taglio, dimensionamento strutturale o validazione termica.", 15, GREY)
        self.text(1340, y + 27, "Quote in mm", 15, GREY, anchor="end")

    def finish(self):
        self.footer()
        return "\n".join(self.parts) + "\n</svg>"


class View:
    def __init__(self, svg, x, y, scale):
        self.svg, self.x, self.y, self.scale = svg, x, y, scale

    def p(self, x, y):
        return self.x + x * self.scale, self.y - y * self.scale

    def poly(self, points, **kwargs):
        self.svg.poly([self.p(*p) for p in points], **kwargs)

    def line(self, a, b, **kwargs):
        self.svg.line(*self.p(*a), *self.p(*b), **kwargs)

    def rect(self, x, y, width, height, **kwargs):
        self.poly([(x, y), (x + width, y), (x + width, y + height), (x, y + height)], **kwargs)

    def text(self, x, y, text, **kwargs):
        self.svg.text(*self.p(x, y), text, **kwargs)

    def dim_h(self, x0, x1, y, label):
        self.line((x0, y), (x1, y), colour=GREY, width=1)
        for x in (x0, x1):
            self.line((x, y - 7), (x, y + 7), colour=GREY, width=1)
        px, py = self.p((x0 + x1) / 2, y)
        self.svg.text(px, py - 9, label, 17, GREY, anchor="middle")

    def dim_v(self, x, y0, y1, label):
        self.line((x, y0), (x, y1), colour=GREY, width=1)
        for y in (y0, y1):
            self.line((x - 7, y), (x + 7, y), colour=GREY, width=1)
        px, py = self.p(x, (y0 + y1) / 2)
        self.svg.text(px - 12, py, label, 17, GREY, anchor="middle", rotate=-90)


def notes(svg, x, y, heading, lines):
    svg.text(x, y, heading, 19, BLUE, bold=True)
    for i, line in enumerate(lines):
        svg.text(x, y + 30 + 25 * i, line, 16, GREY)
    return y + 60 + 25 * len(lines)


def plan_svg(case, config, v4):
    s = SVG("C01 / PIANTA DI INGOMBRO", "Scocca inox sfaccettata; camera V4 conservata. Collettore e camino sono proiezioni ALTE.")
    v = View(s, 220, 735, .70)
    h, layout = config["packaging_hypotheses"], v4["current_layout_candidate"]
    polygon = section_polygon(case, 2, 0)
    v.poly(polygon, fill="#eef2f4", stroke="#465a66", width=2.2)
    v.poly(hot_plan(v4), fill="#fffdf7", stroke=BLUE, width=2)
    v.rect(0, 0, 790, 410, fill="#eee5d0", stroke=BLUE)
    v.poly([(0, 410), (790, 410), (650, 660), (140, 660)], fill="#f4ddc3", stroke=ORANGE)
    reserve = h["collector_reservation"]
    v.rect(reserve["x_range_mm"][0], reserve["y_range_mm"][0],
           reserve["x_range_mm"][1] - reserve["x_range_mm"][0], reserve["y_range_mm"][1] - reserve["y_range_mm"][0], stroke=PURPLE, dash="8 5")
    for n, (x, y) in enumerate(v4["program_constraints"]["rotating_discs"]["centres"], 1):
        s.circle(*v.p(x, y), 160 * v.scale, "#dfd0ad", ORANGE)
        s.circle(*v.p(x, y), 150 * v.scale, "none", GREY, "4 5")
        v.rect(x - 70, y - 70, 140, 140, stroke=BLUE, dash="5 5")
        v.line((x - 12, y), (x + 12, y), colour=BLUE)
        v.line((x, y - 12), (x, y + 12), colour=BLUE)
        v.text(x, y + 29, f"DISCO {n}", size=18, anchor="middle", bold=True)
        v.text(x, y - 40, "Ø320 / pizza Ø300", size=15, anchor="middle")
    flue = v4["roof_and_flue_candidates"]["flue"]
    s.circle(*v.p(*flue["centre_xy"]), flue["collar_diameter"] / 2 * v.scale, "none", PURPLE, "8 5")
    s.circle(*v.p(*flue["centre_xy"]), flue["internal_diameter"] / 2 * v.scale, "none", PURPLE)
    v.text(395, 40, "C", size=19, colour=PURPLE, anchor="middle", bold=True)
    v.line((35, -80), (755, -80), colour=INK, width=4)
    v.line((35, case["bounds"][1][0]), (755, case["bounds"][1][0]), colour=INK, width=5)
    v.line((245, 660), (545, 660), colour=ORANGE, width=3, dash="7 4")
    v.line((245, case["bounds"][1][1]), (545, case["bounds"][1][1]), colour=ORANGE, width=4)
    v.text(395, 530, "FOCOLARE POSTERIORE", size=18, colour=ORANGE, anchor="middle", bold=True)
    v.text(395, 492, "790 → 510 / profondità 250", size=16, colour=ORANGE, anchor="middle")
    v.text(395, 378, "PIANO 790 × 410", size=16, colour=BLUE, anchor="middle")
    v.text(395, -112, "BOCCA 720 × 160", size=17, anchor="middle")
    v.dim_h(case["bounds"][0][0], case["bounds"][0][1], -245, fmt(case["summary"]["width_mm"]))
    v.dim_v(-170, *case["bounds"][1], fmt(case["summary"]["depth_mm"]))
    y = notes(s, 940, 185, "BASELINE DI STUDIO", [
        "Isolamento corpo: 75 mm", "Acciaio caldo / esterno: 1,5 / 1 mm", "Riserva montaggio: 10 mm",
        "Piano / dischi: 20 mm", "Fondo focolare: 30 mm", "Vano meccanico netto: 120 mm"])
    y = notes(s, 940, y + 15, "PERCORSO E ACCESSI", [
        "Caricamento legna dal retro.", "Porta interna di riferimento: y = −80.", "Pelle esterna fronte: y = −167,5.", "Centri dischi dalla pelle: 372,5 mm.",
        "Il tunnel aggiunto richiede prova pala.", "Camino alto: asse (395; 45)."])
    notes(s, 940, y + 15, "DA NON CONFONDERE", [
        "Cerchi = dischi, non fori di taglio.", "Viola = spazio ALTO per raccolta fumi.", "Blu tratteggiato = azionamenti sotto.", "Non sono condotti o motori selezionati.", "Porta e botola: dettagli da sviluppare."])
    s.text(60, 945, "Riferimento: v4/quote_v4.json · origine sul bordo anteriore sinistro del piano, z=0 sulla pietra.", 16, GREY)
    return s.finish()


def transverse_svg(case, config, v4):
    s = SVG("C01 / SEZIONE TRASVERSALE", "Taglio y=205, attraverso entrambi i dischi. Colori = componenti / riserve, NON temperature.")
    v = View(s, 215, 520, .74)
    h = config["packaging_hypotheses"]
    profile = section_polygon(case, 1, 205)
    v.poly(profile, fill="#eef2f4", stroke="#465a66", width=2.2)
    # The base is an envelope, not a continuous load-bearing plate specification.
    v.rect(case["bounds"][0][0], case["bottom_z_mm"], case["summary"]["width_mm"],
           case["thermal_bottom_z_mm"] - case["bottom_z_mm"], fill="#e2e9ed", stroke=INK)
    curve = [(790 * i / 80, roof_at(v4, 790 * i / 80, 205)) for i in range(81)]
    v.poly([(0, 0), (790, 0)] + curve[::-1], fill="#fffaf0", stroke=BLUE, width=2)
    v.rect(0, -20, 790, 20, fill="#dfd0ad", stroke=ORANGE)
    v.rect(0, -70, 790, 50, fill="#e0eadb", stroke=GREEN)
    v.line((0, -71.5), (790, -71.5), colour=INK, width=2)
    for x in (210, 580):
        v.rect(x - 160, -20, 320, 20, fill="#eadbb8", stroke=ORANGE)
        v.rect(x - 70, -191.5, 140, 100, fill="#d9eaf0", stroke=BLUE, dash="6 4")
        v.line((x, -91.5), (x, -70), colour=BLUE, width=4)
        v.text(x, -140, "RISERVA", size=13, colour=BLUE, anchor="middle")
        v.text(x, -163, "AZIONAMENTO", size=12, colour=BLUE, anchor="middle")
    v.line((0, 0), (790, 0), colour=ORANGE, width=2)
    v.text(395, 100, "CAMERA CALDA", size=19, colour=BLUE, anchor="middle", bold=True)
    v.text(395, 65, "volta interna parabolica V4", size=16, colour=BLUE, anchor="middle")
    for x in (60, 730):
        v.rect(x - 25, case["feet_bottom_z_mm"], 50, h["feet_height_mm"], fill="#26343d", stroke=INK)
    v.dim_h(*case["bounds"][0], -300, "965 esterno")
    # Maximum body ridge is present in this section; do not dimension a projection.
    v.dim_v(-155, case["feet_bottom_z_mm"], case["summary"]["ridge_z_from_cooking_floor_mm"], "617,0 corpo + piedini")
    v.dim_v(395, case["thermal_bottom_z_mm"] - 120, case["thermal_bottom_z_mm"], "120 netto")
    p = next(p for p in case["planes"] if p.name == "roof_0_1")
    nx, _, nz = p.normal
    x = 395 + nx * 395 ** 2 / (2 * nz * 90)
    point = (x, roof_at(v4, x, 205))
    end = (point[0] + nx * case["normal_offset_mm"], point[1] + nz * case["normal_offset_mm"])
    v.line(point, end, colour=PURPLE, width=2.5)
    v.text(end[0] + 15, end[1] + 20, "87,5 normale", size=15, colour=PURPLE)
    y = notes(s, 960, 175, "COME SI COSTRUISCE L'INVILUPPO", [
        "1,5 acciaio + 75 isolante", "+ 10 riserva + 1 rivestimento.", "Distanza misurata NORMALE", "a ciascuna falda, non verticale.", "Le pieghe non invadono il volume", "riservato al pacchetto nominale."])
    y = notes(s, 960, y + 15, "SOTTO IL PIANO", [
        "20 mm pietra di cottura", "50 mm pannello: tipo da qualificare", "Carrier / appoggi: da progettare", "30 mm pietra nel focolare posteriore", "120 mm vano netto per meccanica", "25 mm piedini: solo riserva"])
    notes(s, 960, y + 15, "LIMITI IMPORTANTI", [
        "La lana non sostiene le pietre.", "Colonne dei dischi: schema riservato.", "Nessuna verifica di ponti termici.", "Nessun componente selezionato.", "80 mm netti NON bastano alle", "riserve di azionamento attuali."])
    s.text(60, 940, "L'ingombro stimato è più alto del render: 617 mm nello scenario 75/120. Ridurlo richiede riprogettare il pacchetto.", 16, GREY)
    return s.finish()


def longitudinal_svg(case, config, v4):
    s = SVG("C01 / SEZIONE LONGITUDINALE", "Taglio x=210 nel disco sinistro. Camino e collettore centrali sono PROIETTATI, non tagliati.", 1150)
    v = View(s, 210, 670, .70)
    h = config["packaging_hypotheses"]
    profile = section_polygon(case, 0, 210)
    v.poly(profile, fill="#eef2f4", stroke="#465a66", width=2)
    curve = [(y, roof_at(v4, 210, y)) for y in [-80 + 740 * i / 80 for i in range(81)]]
    v.poly([(-80, 0), (660, 0)] + curve[::-1], fill="#fffaf0", stroke=BLUE, width=2)
    v.rect(0, -20, 410, 20, fill="#dfd0ad", stroke=ORANGE)
    v.rect(410, -30, 250, 30, fill="#d1b28d", stroke=ORANGE)
    v.rect(0, -70, 410, 50, fill="#e0eadb", stroke=GREEN)
    v.rect(410, -80, 250, 50, fill="#e0eadb", stroke=GREEN)
    v.rect(45, -20, 320, 20, fill="#eadbb8", stroke=ORANGE)
    v.rect(135, -191.5, 140, 100, fill="#d9eaf0", stroke=BLUE, dash="6 4")
    v.line((205, -91.5), (205, -70), colour=BLUE, width=4)
    v.line((-80, 0), (-80, 160), colour=INK, width=4, dash="7 4")
    v.text(-105, 80, "porta", size=15, anchor="end")
    v.text(205, 105, "DISCO 1", size=18, colour=ORANGE, anchor="middle", bold=True)
    v.text(535, 100, "LEGNA", size=18, colour=ORANGE, anchor="middle", bold=True)
    reserve = h["collector_reservation"]
    v.rect(*[reserve["y_range_mm"][0], reserve["z_range_mm"][0],
             reserve["y_range_mm"][1] - reserve["y_range_mm"][0], reserve["z_range_mm"][1] - reserve["z_range_mm"][0]], stroke=PURPLE, dash="7 5")
    v.text(120, 225, "riserva collettore (proiezione)", size=15, colour=PURPLE)
    # A visibly broken projection; the separate overview below contains the FULL flue.
    for y in (-20, 110):
        v.line((y, 250), (y, 640), colour=PURPLE, dash="8 5")
        v.line((y - 12, 550), (y + 12, 568), colour=PURPLE, width=2)
        v.line((y - 12, 571), (y + 12, 589), colour=PURPLE, width=2)
    v.text(135, 620, "CAMINO: proiezione interrotta", size=16, colour=PURPLE)
    v.text(135, 585, "H candidata 1000 / 1500 dal collare", size=16, colour=PURPLE)
    v.text(135, 550, "Raccordo interno NON dimensionato", size=15, colour=PURPLE)
    v.dim_h(*case["bounds"][1], -300, "915 esterno")
    v.dim_h(-80, 0, -355, "80")
    v.dim_h(0, 410, -355, "410 piano")
    v.dim_h(410, 660, -355, "250 fuoco")
    v.line((case["bounds"][1][0], case["feet_bottom_z_mm"]), (case["bounds"][1][1], case["feet_bottom_z_mm"]), colour=GREY, dash="4 4")
    y = notes(s, 930, 170, "INGOMBRI COMPLETI", [
        "Corpo + piedini: 617 mm", "Con canna H1000: 1717 mm", "Con canna H1500: 2217 mm", "Quote dal piano d'appoggio.", "Altezza canna ancora da verificare."])
    y = notes(s, 930, y + 10, "VISTA COMPLETA, SCALA RIDOTTA", [])
    small = View(s, 1005, 965, .24)
    centre_profile = section_polygon(case, 0, 395)
    small.poly(centre_profile, fill="#eef2f4", stroke=INK)
    small.poly([(-50, case["summary"]["ridge_z_from_cooking_floor_mm"]),
                (140, case["summary"]["ridge_z_from_cooking_floor_mm"]),
                (110, case["collar_top_z_mm"]), (-20, case["collar_top_z_mm"])], fill="#d8dfe4", stroke=PURPLE)
    small.rect(-20, case["collar_top_z_mm"], 130, 1000, fill="#d8dfe4", stroke=PURPLE)
    for y in (-40, 600):
        small.rect(y - 25, case["feet_bottom_z_mm"], 50, h["feet_height_mm"], fill="#26343d", stroke=INK)
    small.dim_v(860, case["feet_bottom_z_mm"], case["collar_top_z_mm"] + 1000, "1717 con H1000")
    s.text(60, 1005, "Bocca e botola NON devono interrompere lo scarico fumi. Servono presa d'aria, collettore, terminale e verifiche di captazione.", 16, GREY)
    return s.finish()


def preview_svg(case):
    s = SVG("C01 / ASSIEME DI INGOMBRO", "Modello geometrico, non render fotorealistico. Camino H1000 rappresentato COMPLETO.")
    image = base64.b64encode(render(case)).decode()
    s.parts.append(f'<image x="130" y="140" width="1030" height="795" href="data:image/png;base64,{image}"/>')
    s.text(1100, 200, "965 × 915", 24, BLUE, bold=True, anchor="middle")
    s.text(1100, 236, "corpo: 617 mm", 19, GREY, anchor="middle")
    s.text(1100, 270, "totale: 1717 mm", 19, PURPLE, anchor="middle")
    s.text(60, 950, "La posizione anteriore del camino deriva dalla V4: non è la posizione posteriore suggerita dal render estetico.", 16, GREY)
    return s.finish()


def write_obj(case, output):
    rows = ["# C01 - millimetres - NON EXECUTIVE SURFACE / RESERVATION MODEL", "# Not watertight manufacturing solids; not cutting/bending profiles.", "mtllib assieme_C01.mtl"]
    materials, index = {}, 1
    for face in case["mesh"]:
        group = face["group"]
        materials.setdefault(group, face["colour"])
        rows.extend((f"g {group}", f"usemtl {group}"))
        for p in face["points"]:
            rows.append("v " + " ".join(f"{v:.6f}" for v in p))
        for i in range(1, len(face["points"]) - 1):
            rows.append(f"f {index} {index + i} {index + i + 1}")
        index += len(face["points"])
    (output / "assieme_C01.obj").write_text("\n".join(rows) + "\n", encoding="ascii")
    mtl = ["# Presentation materials only; no certified material properties."]
    for name, colour in materials.items():
        rgb = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        mtl.extend((f"newmtl {name}", "Kd " + " ".join(f"{v:.6f}" for v in rgb),
                    "d 0.3" if name in ("collector", "mechanisms") else "d 1.0", "illum 1", ""))
    (output / "assieme_C01.mtl").write_text("\n".join(mtl), encoding="ascii")


def write_dxf(case, v4, output):
    rows = []
    def pair(code, value):
        rows.extend((str(code), str(value)))
    def line(a, b, layer, colour):
        for code, value in ((0, "LINE"), (8, layer), (62, colour), (10, a[0]), (20, a[1]), (30, 0),
                            (11, b[0]), (21, b[1]), (31, 0)):
            pair(code, value)
    def polygon(points, layer, colour):
        for a, b in zip(points, points[1:] + points[:1]):
            line(a, b, layer, colour)
    def text(x, y, content):
        content = unicodedata.normalize("NFKD", content).encode("ascii", "ignore").decode()
        for code, value in ((0, "TEXT"), (8, "NOTE_NON_ESECUTIVO"), (62, 7), (10, x), (20, y), (30, 0), (40, 18), (1, content)):
            pair(code, value)
    for code, value in ((0, "SECTION"), (2, "HEADER"), (9, "$ACADVER"), (1, "AC1015"),
                        (9, "$INSUNITS"), (70, 4), (0, "ENDSEC"), (0, "SECTION"), (2, "ENTITIES")):
        pair(code, value)
    polygon(section_polygon(case, 2, 0), "INVILUPPO_NOMINALE", 8)
    polygon(hot_plan(v4), "CAMERA_INTERNA_V4", 5)
    for x, y in v4["program_constraints"]["rotating_discs"]["centres"]:
        for code, value in ((0, "CIRCLE"), (8, "DISCHI_NON_FORI_TAGLIO"), (62, 30), (10, x), (20, y), (30, 0), (40, 160)):
            pair(code, value)
    text(0, -290, "C01 PIANTA - mm - NON PROFILI DI TAGLIO")
    for offset, axis, value, title in ((1300, 1, 205, "SEZIONE y=205"), (2800, 0, 210, "SEZIONE x=210")):
        polygon([(x + offset, z) for x, z in section_polygon(case, axis, value)], "SEZIONE_INVILUPPO", 8)
        curve = [(x, roof_at(v4, x, value)) for x in range(0, 791, 10)] if axis == 1 else [(y, roof_at(v4, value, y)) for y in range(-80, 661, 10)]
        for a, b in zip(curve, curve[1:]):
            line((a[0] + offset, a[1]), (b[0] + offset, b[1]), "VOLTA_INTERNA_RIFERIMENTO", 5)
        text(offset, -290, f"C01 {title} - RISERVE DI INGOMBRO")
    text(0, -340, "NON ESECUTIVO - nessuna approvazione di struttura, isolamento, tiraggio o cottura")
    pair(0, "ENDSEC"); pair(0, "EOF")
    (output / "ingombri_C01.dxf").write_text("\n".join(rows) + "\n", encoding="ascii")


def engineering_report(case, cases, config, v4, test_count):
    s, h = case["summary"], config["packaging_hypotheses"]
    rows = "\n".join(f"| {c['insulation_mm']} | {c['mechanism_clear_height_mm']} | {fmt(c['summary']['width_mm'])} | {fmt(c['summary']['depth_mm'])} | {fmt(c['summary']['body_height_with_feet_mm'])} | {'sì, solo riserva' if c['summary']['drive_reservations_fit'] else 'NO'} |" for c in cases)
    return f"""# C01 — studio d'ingombro del forno inox sfaccettato

**Stato: non esecutivo.** Nessuna CFD, misura fisica o verifica strutturale nuova.
Unità geometriche: mm. Origine e assi sono quelli di `v4/quote_v4.json`.

## Requisiti confermati

Forno domestico da esterno, appoggio fisso, due pizze Ø300, cottura nominale
60–90 s a forno pronto. Preriscaldamento desiderato 45–60 min; primo obiettivo
di verifica entro 60 min. Questi sono obiettivi, non prestazioni dimostrate.
Riferimento estetico: `design-concepts/14-inox-sfaccettato.png`.

## Baseline geometrica proposta

- Camera V4: piano 790 × 410, dischi Ø320 ai centri (210;205) e (580;205).
- Focolare posteriore trapezoidale, profondità 250; avancorpo interno 80.
- Bocca candidata 720 × 160; botola posteriore 300 × 140.
- Volta interna parabolica: imposta 190, colmo 280. Il suo profilo è esteso
  all'avancorpo SOLO come ipotesi di ingombro; il raccordo reale resta aperto.
- Pietra piano/dischi 20; fondo focolare 30. Sono due ipotesi distinte.
- Acciaio caldo 1,5; lana di roccia 75; montaggio/dilatazioni riservati 10;
  rivestimento esterno 1. Prodotti e leghe non selezionati.
- Isolante inferiore 50, carrier riservato 1,5, vano meccanico netto 120,
  fondo 1,5 e piedini riservati 25. Nessuna verifica di portanza del pannello.
- Scocca a falde trasversali 12° e testate 30°, spalle sfaccettate.

**Ingombro proposto: {fmt(s['width_mm'])} × {fmt(s['depth_mm'])} ×
{fmt(s['body_height_with_feet_mm'])} mm**, altezza del corpo inclusi piedini,
senza camino. Il render molto basso non dimostra disponibilità di questo spazio.

Con canna candidata H1000 dal collare: altezza sul piano d'appoggio
{fmt(s['height_with_flue_1000_mm'])}; con H1500: {fmt(s['height_with_flue_1500_mm'])}.
Non sono altezze di canna approvate. Asse mantenuto (395;45), ANTERIORE:
il prompt del render colloca il camino dietro, ma qui non modifichiamo il
percorso fumi V4 per inseguire un'immagine. Una diversa posizione richiede
un confronto separato di captazione e distribuzione termica.

## Verifica geometrica delle falde

Ogni piano esterno delimita un semispazio di contenimento `n·p ≤ d`, con `|n|=1`.
Si calcola analiticamente il massimo `n·p` sulla camera con volta parabolica,
poi si aggiungono {fmt(case['normal_offset_mm'])} mm NORMALI al piano.
Questo evita di confondere lo spessore normale con un semplice incremento
verticale del tetto. I piani inclinati rispettano il pacchetto nominale;
rimangono {fmt(s['nominal_roof_insulation_space_mm'])} mm dopo sottrazione
delle due pelli, dei quali 75 per isolamento e 10 di riserva.

**Non è una verifica dell'isolamento reale:** bocca, botola, collare,
giunti, supporti, ponti termici e dilatazioni devono ancora essere progettati.
I pannelli sono superfici/riserve, non solidi di lamiera pronti da piegare.

## Ingombri alternativi

| Isolante | Vano netto | Larghezza | Profondità | Corpo+piedini | Riserve azionamenti |
|---:|---:|---:|---:|---:|---|
{rows}

Le scatole azionamenti 140 × 140 × 100 non sono motori selezionati.
Servono 10 mm sopra e sotto: lo scenario con vano 80 fallisce questa riserva.
Il vano 120 non prova manutenzione, raffreddamento o montabilità di componenti reali.

## Criticità emerse

1. Altezza e profondità superiori all'impressione del render.
2. Dalla pelle esterna ai centri dei dischi: {fmt(s['front_skin_to_disc_centres_mm'])};
   dal piano porta interno erano 285. Serve prova della pala nel tunnel aggiunto.
3. Pala ipotizzata 340: solo {fmt(s['paddle_side_margin_mm'])} mm per lato nelle
   posizioni allineate. Esclusi telaio, tolleranze e manovra inclinata.
4. Gioco radiale dischi 1: semplice ipotesi V4, NON tolleranza di taglio.
5. Collettore viola: riserva x70…720, y−60…120, z180…215. NON un condotto
   dimensionato; può modificare irraggiamento e captazione. Raccordo da definire.
6. Sotto i dischi: riserva per un carrier isolato. Meccanica e appoggi
   devono essere definiti prima di attribuire conduzione e ponti termici.
7. Presa d'aria non dimensionata. 60/90 cm² restano scenari della rete,
   non tagli geometrici approvati. Non usare una porta chiusa senza aria progettata.
8. Massa della SOLA pietra: circa {fmt(s['stone_mass_only_kg'])} kg,
   con densità ipotizzata {h['provisional_stone_density_kg_m3']} kg/m³.
   Ogni disco: {fmt(s['one_disc_mass_kg'])} kg. Telaio, pelli, isolanti, motori,
   camino e accessori sono esclusi: non è la massa del forno.

## Stato delle simulazioni preesistenti

La campagna CFD da un'ora usa pietra 30 e isolante generico 50; non questa C01.
Il suo `readiness.json` riporta `ready=false`: piano minimo circa 289 °C,
escursione circa 76 °C, volta minima circa 405 °C. La cottura successiva è
stata avviata in deroga alle soglie. La scocca esterna non è validata al tatto.
Il confronto di spessori 10/20/30 e isolanti 50/75/100 NON è stato simulato qui.

## Controlli effettuati

{test_count} test automatici geometrici/numerici superati durante la generazione:
posizioni V4, supporto della parabola contro campionamento denso, distanze
normali, contenimento, sezioni, bocca aperta, ingombri alternativi,
camino completo, volumi riservati e massa indicativa delle pietre.
Sono controlli del generatore, NON prove del forno reale.

## Consegne

- `index.html`: visualizzatore 3D offline, varianti e viste tecniche.
- `pianta.svg`, `sezione_trasversale.svg`, `sezione_longitudinale.svg`.
- `assieme.svg`: modello geometrico con camino completo.
- `scheda_stampa.html`: scheda stampabile; PDF con lo script opzionale.
- `ingombri_C01.dxf`: riferimento nominale 2D in mm, NON profili di taglio.
- `assieme_C01.obj` + `.mtl`: superfici/riserve 3D in mm, non solidi manifatturabili.
- `confronto_ingombri.csv`, `verifica_geometrica.json`, `provenienza.json`.
- `PIANO_VERIFICHE.md`: sequenza e criteri da definire prima del prototipo.

Prossimo gate: circuito aria/collettore, prodotti reali e architettura dei dischi.
Solo dopo aggiornare i modelli e qualificare un prototipo strumentato.
"""


TEST_PLAN = """# C01 — piano di verifiche prima della produzione

**Nessuna di queste prove fisiche è stata eseguita dal generatore.**
Il superamento dei test Python non costituisce approvazione del forno.

| Gate | Attività | Uscita richiesta / criterio |
|---|---|---|
| G1 — definizione | Geometria quotata, distinta materiali candidata, uso outdoor, sessione massima e carica legna | Una configurazione unica; limiti d'uso espliciti e analisi dei rischi preliminare |
| G2 — aria e fumi | Presa dedicata, braci, collettore, raccordo, terminale; porta e botola | Percorso continuo anche a porta chiusa; quote e perdite da verificare, nessuna approvazione basata sul solo render |
| G3 — materiali | Lega della camera e della zona fiamma, lana industriale, pannello inferiore e pietra reale | Schede a temperatura, limite di servizio, legante, ritiro, emissività, portanza e documentazione alimentare pertinenti |
| G4 — campione sandwich | Pacchetto reale con giunti/fissaggi; riscaldamento e cicli controllati | Temperature, integrità e assestamento entro criteri concordati con fornitori/laboratorio; nessuna fibra verso camera e alimenti |
| G5 — meccanica a freddo | Pala reale, carrier, tolleranze, trasmissione, manutenzione | Nessuna interferenza; pietre non serrate rigidamente; pulizia e sostituzione dimostrate |
| G6 — calcolo | Modello termico con dati reali e rotazione; CFD per flusso, maglia e statistiche | Bilanci controllati; sensitività documentata; niente temperatura esterna imposta usata come prova al tatto |
| G7 — prototipo termico | Almeno tre partenze da freddo; registrare legna/umidità e temperature | Prima doppia infornata soddisfacente entro 60 min come obiettivo; puntare a 45 senza sacrificare sicurezza |
| G8 — cottura/recupero | Una pizza, due simultanee, 5–10 doppie consecutive con ricetta controllata | 60–90 s nominali con risultato sopra/sotto soddisfacente; registrare attesa e recupero, non solo una temperatura media |
| G9 — captazione | Accensione, regime, ricarica posteriore, apertura frontale, vento da più direzioni | Pressione, O2/CO nei fumi e CO presso operatore; esposizione/emissioni entro limiti definiti per prodotto e installazione |
| G10 — temperature | Scocca, maniglie, comandi, supporto, motori/cavi; includere il dopo-fuoco | Limiti al contatto e ai materiali stabiliti prima della prova; nessuna temperatura universale assunta sicura |
| G11 — guasti/durata | Blocco disco, mancanza alimentazione, dilatazioni, sovraccarichi ammessi, cicli | Gestione sicura; 50–100 cicli come screening iniziale, non certificazione della vita utile |
| G12 — industrializzazione | Prove ambientali pertinenti, classificazione normativa, preserie | Dossier rischi e conformità, tracciabilità, tolleranze ripetibili, montaggio e collaudo definiti |

Strumentazione: termocoppie su pietra sopra/sotto, volta, retro, faccia calda
isolante, scocca, camino e meccanismi; manometro differenziale; analizzatore
O2/CO e monitor CO operatore; bilancia, umidità legna, velocità/corrente motori.
La termocamera richiede riferimenti di emissività, soprattutto sull'inox.

Le soglie preliminari 430 °C piano / 450 °C volta / escursione 50 °C sono
riferimenti di confronto del vecchio modello, da correlare alla cottura vera.
Non sostituiscono criteri di sicurezza o valutazione del prodotto alimentare.
Guasti, sovraccarichi e shock termici vanno provati in condizioni protette,
con personale competente; non raffreddare il forno caldo con acqua.
"""


def print_sheet(svgs, report, reference, cases):
    summary = "".join(f"<tr><td>{c['id']}</td><td>{fmt(c['summary']['width_mm'])} × {fmt(c['summary']['depth_mm'])}</td><td>{fmt(c['summary']['body_height_with_feet_mm'])}</td><td>{'solo riserva compatibile' if c['summary']['drive_reservations_fit'] else 'riserva meccanica insufficiente'}</td></tr>" for c in cases)
    pages = [f'<section><h1>FORNO C01 · Inox sfaccettato</h1><p>Studio d’ingombro non esecutivo · uso domestico outdoor · appoggio fisso</p><div class="cover"><div><h2>Riferimento estetico</h2><img src="{reference}"/><p>Render illustrativo: non contiene quote né prove fisiche.</p></div><div>{svgs["assieme.svg"]}</div></div><p><b>Baseline: 965 × 915 × 617 mm corpo con piedini.</b> Con camino candidato H1000: 1717 mm sul piano d’appoggio.</p><p>20 mm piano, 30 mm focolare, 75 mm isolamento corpo, 10 mm riserva montaggio, 120 mm vano meccanico. Materiali e componenti da qualificare.</p><p><b>Obiettivi, non risultati:</b> due pizze Ø300, cottura nominale 60–90 s, preriscaldamento desiderato 45–60 min.</p></section>']
    pages.extend(f'<section class="drawing">{svgs[name]}</section>' for name in ("pianta.svg", "sezione_trasversale.svg", "sezione_longitudinale.svg"))
    pages.append(f'<section><h1>Confronto ingombri e prossimi gate</h1><p>Ogni alternativa mantiene la camera V4. I volumi motore non sono componenti selezionati.</p><table><tr><th>Caso I=isolante / M=vano</th><th>Pianta mm</th><th>Corpo+piedini mm</th><th>Azionamenti riservati</th></tr>{summary}</table><h2>Prima del prototipo</h2><ol><li>Definire presa d’aria e collettore; verificare camino e captazione.</li><li>Selezionare leghe, lana industriale, pannello portante e pietra reali.</li><li>Progettare carrier, appoggi, tolleranze e trasmissione dei dischi.</li><li>Provare pala, sportelli, smontaggio e manutenzione a freddo.</li><li>Aggiornare simulazioni, poi prototipo strumentato e prove di durata.</li></ol><p><b>Limiti:</b> nessuna nuova CFD, nessuna verifica al tatto, nessuna approvazione strutturale. DXF/OBJ sono riferimenti nominali, non file da mandare in produzione.</p><p>Rapporto completo e piano verifiche sono nei file Markdown della stessa cartella. Provenienza e controlli automatici sono nei JSON.</p></section>')
    return '<!doctype html><html lang="it"><meta charset="utf-8"><title>C01 — scheda stampabile</title><style>@page{size:A3 landscape;margin:10mm}*{box-sizing:border-box}body{margin:0;color:#193345;font:17px Arial,sans-serif}section{height:275mm;padding:7mm;break-after:page;overflow:hidden}section:last-child{break-after:auto}h1{font-size:30px}h2{font-size:21px}.cover{display:grid;grid-template-columns:1fr 1fr;gap:12mm;height:172mm}.cover img{width:100%;max-height:135mm;object-fit:contain}.cover svg{width:100%;height:100%}.drawing{display:flex;justify-content:center;align-items:center}.drawing svg{max-width:100%;height:100%;width:auto}table{border-collapse:collapse;width:100%;margin:8mm 0}td,th{padding:3mm;border-bottom:1px solid #cbd6dc;text-align:left}th{background:#eef2f4}li{margin:3mm 0}@media screen{body{background:#e5ebef}section{background:white;width:400mm;margin:15px auto;box-shadow:0 2px 15px #abb9c2}}</style><body>' + "\n".join(pages) + "</body></html>"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=HERE / "concept.json")
    parser.add_argument("--output", type=Path, default=HERE / "output")
    args = parser.parse_args()
    config, v4, config_path, source = load_inputs(args.config)
    import test_geometry
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_geometry))
    if not result.wasSuccessful():
        raise SystemExit(log.getvalue())
    baseline = build_case(config, v4)
    h = config["packaging_hypotheses"]
    cases = [build_case(config, v4, i, m) for i in h["body_insulation_comparison_mm"] for m in h["mechanism_comparison_mm"]]
    if not baseline["summary"]["drive_reservations_fit"]:
        raise SystemExit("Baseline mechanism reservation does not fit")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    svgs = {"pianta.svg": plan_svg(baseline, config, v4),
            "sezione_trasversale.svg": transverse_svg(baseline, config, v4),
            "sezione_longitudinale.svg": longitudinal_svg(baseline, config, v4),
            "assieme.svg": preview_svg(baseline)}
    for name, content in svgs.items():
        (output / name).write_text(content, encoding="utf-8")
    reference_path = (config_path.parent / config["aesthetic_reference"]).resolve()
    reference = "data:image/png;base64," + base64.b64encode(reference_path.read_bytes()).decode()
    serial = [{"id": c["id"], "insulation_mm": c["insulation_mm"],
               "mechanism_clear_height_mm": c["mechanism_clear_height_mm"],
               "summary": c["summary"], "collar_top_z_mm": c["collar_top_z_mm"],
               "mesh": c["mesh"]} for c in cases]
    template = (HERE / "viewer.template.html").read_text(encoding="utf-8")
    html = template.replace("@@DATA@@", json.dumps(serial, separators=(",", ":")))
    html = html.replace("@@REFERENCE@@", reference)
    for name, content in svgs.items():
        html = html.replace("@@" + name + "@@", content)
    (output / "index.html").write_text(html, encoding="utf-8")
    (output / "anteprima.html").write_text('<!doctype html><meta charset="utf-8"><title>C01 assieme</title><style>body{margin:0}svg{width:100vw;height:100vh}</style>' + svgs["assieme.svg"], encoding="utf-8")
    report = engineering_report(baseline, cases, config, v4, result.testsRun)
    (output / "RAPPORTO_C01.md").write_text(report, encoding="utf-8")
    (output / "PIANO_VERIFICHE.md").write_text(TEST_PLAN, encoding="utf-8")
    (output / "scheda_stampa.html").write_text(print_sheet(svgs, report, reference, cases), encoding="utf-8")
    write_obj(baseline, output)
    write_dxf(baseline, v4, output)
    with (output / "confronto_ingombri.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["caso", "isolante_mm", "vano_mm", "larghezza_mm", "profondita_mm", "corpo_con_piedini_mm", "altezza_H1000_mm", "altezza_H1500_mm", "riserve_azionamenti_compatibili"]
        writer = csv.writer(f, delimiter=";")
        writer.writerow(fields)
        for c in cases:
            s = c["summary"]
            writer.writerow([c["id"], c["insulation_mm"], c["mechanism_clear_height_mm"], *[round(s[k], 3) for k in ("width_mm", "depth_mm", "body_height_with_feet_mm", "height_with_flue_1000_mm", "height_with_flue_1500_mm")], s["drive_reservations_fit"]])
    validation = {"scope": "geometry_generator_only_NOT_physical_validation", "tests_run": result.testsRun,
                  "tests_passed": result.wasSuccessful(), "baseline": baseline["id"],
                  "summary": baseline["summary"], "normal_offset_checks": baseline["normal_offset_checks"],
                  "all_variants": [{"id": c["id"], "summary": c["summary"]} for c in cases],
                  "production_approved": False}
    (output / "verifica_geometrica.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "test_generatore.log").write_text(log.getvalue(), encoding="utf-8")
    sources = [config_path, source, reference_path, HERE / "geometry.py", HERE / "build_study.py", HERE / "render_scene.py", HERE / "viewer.template.html", HERE / "test_geometry.py", HERE / "test_viewer.cjs", HERE / "export_preview.ps1"]
    readiness = (config_path.parent / config["thermal_readiness_reference"]).resolve()
    if readiness.exists():
        sources.append(readiness)
    provenance = {"study_id": config["study_id"], "generated_utc": datetime.now(timezone.utc).isoformat(),
                  "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  "thermal_solver_started": False, "v4_source_modified": False,
                  "output_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file() and p.name not in ("provenienza.json", "Scheda_C01.pdf", "assieme.png", "pianta.png", "sezione_trasversale.png", "sezione_longitudinale.png", "viewer.png")}}
    (output / "provenienza.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"C01 generated: {output}")
    print(f"{result.testsRun} geometry tests passed. No CFD or physical tests executed.")
    print("Baseline:", json.dumps(baseline["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
