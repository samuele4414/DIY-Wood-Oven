"""Offline SVG illustrations; none are cutting or manufacturing drawings."""
from html import escape


def n(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


class SVG:
    def __init__(self, title, subtitle):
        self.lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="850" viewBox="0 0 1300 850">',
                      '<style>text{font-family:Arial,sans-serif;fill:#233c4b;font-size:19px}.small{font-size:16px}.head{font-size:28px;font-weight:bold}.dim{font-size:17px;fill:#316986}</style>',
                      '<rect width="1300" height="850" fill="white"/>']
        self.text(45, 44, title, "head")
        self.text(45, 76, subtitle, "small")
        self.text(45, 824, "C03 · mm nominali · NON ESECUTIVO · nessuna approvazione termica, strutturale o per produzione", "small")

    def text(self, x, y, value, cls="", anchor="start"):
        self.lines.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def rect(self, x, y, w, h, fill="none", stroke="#6b8390", dash=""):
        self.lines.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-dasharray="{dash}"/>')

    def line(self, x1, y1, x2, y2, colour="#587b8b", dash=""):
        self.lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" stroke-width="2" stroke-dasharray="{dash}"/>')

    def circle(self, x, y, r, fill="none", stroke="#698a99", dash=""):
        self.lines.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-dasharray="{dash}"/>')

    def dim(self, x1, y, x2, value):
        self.line(x1, y, x2, y)
        for x in (x1, x2):
            self.line(x, y - 6, x, y + 6)
        self.text((x1 + x2) / 2, y - 11, value, "dim", "middle")

    def end(self):
        return "\n".join(self.lines + ["</svg>"]) + "\n"


def plan(cfg, v4, r):
    s = SVG("Due moduli indipendenti — pianta di integrazione", "Centri, piano e dischi V4 invariati; motori collocati verso i lati esterni. Non è l'assieme completo del forno.")
    scale, ox, oy = 1.35, 110, 155
    X, Y = lambda x: ox + x * scale, lambda y: oy + y * scale
    s.rect(X(0), Y(0), 790 * scale, 410 * scale, "#f6f0e6")
    for i, mod in enumerate(r["packaging"]["modules"], 1):
        cx, cy = mod["centre_xy_mm"]
        mx, my = mod["motor_centre_xy_mm"]
        x0, x1, y0, y1 = mod["bounds_xy_mm"]
        s.circle(X(cx), Y(cy), 160 * scale, "none", "#bd9f6b")
        s.rect(X(x0), Y(y0), (x1 - x0) * scale, (y1 - y0) * scale, "none", "#397491", "7 4")
        s.circle(X(cx), Y(cy), 27 * scale, "#bacbd3")
        s.circle(X(mx), Y(my), 16 * scale, "#79a5b9")
        s.line(X(mx), Y(my), X(cx), Y(cy), "#357b99", "5 4")
        s.text(X(cx), Y(cy + 74), f"Modulo {i}: 240 × 180", "small", "middle")
        s.text(X(cx), Y(cy + 118), f"Disco Ø320 / centro ({cx};{cy})", "small", "middle")
        s.dim(X(min(mx, cx)), Y(cy - 44), X(max(mx, cx)), "C = " + n(r["drive"]["centre_distance_mm"], 2))
    s.dim(X(0), Y(-22), X(790), "Piano V4 790")
    s.dim(X(330), Y(340), X(460), "Tra moduli 130")
    s.text(45, 760, "Cinghia 10 T5/280 · pulegge 16/32 · interasse geometrico senza tensione, deformazione o tolleranze.", "small")
    return s.end()


def module(cfg, r):
    s = SVG("Modulo a freddo — proiezione frontale degli inviluppi", "Motore da STEP del fornitore nel modello 3D; qui proiezioni semplificate. Viti, tenute e accoppiamento caldo non disegnati.")
    scale = 2.8
    X = lambda x: 100 + (x - 90) * scale
    Z = lambda z: 145 + (-85 - z) * scale
    x, y = r["packaging"]["modules"][0]["centre_xy_mm"]
    mx, _ = r["packaging"]["modules"][0]["motor_centre_xy_mm"]
    s.rect(X(90), Z(-85), 240 * scale, 160 * scale, "#f3f7f9", "#66818f", "6 4")
    def rect(x0, x1, z0, z1, colour, dash=""):
        s.rect(X(x0), Z(z1), (x1 - x0) * scale, (z1 - z0) * scale, colour, "#617a87", dash)
    top = r["packaging"]["tray_top_z_mm"]
    rect(90, 330, top - cfg["tray_thickness_mm"], top, "#6f8997")
    rect(mx - 22, mx + 22, -205, -128, "#6eabc0")
    rect(mx - 4, mx + 4, -128, -108, "#d3b96c")
    rect(x - 6, x + 6, *cfg["shaft_z_range_mm"], "#d3b96c")
    for cx, ro, hub in ((mx, 16, 9), (x, 27, 19)):
        rect(cx - ro, cx + ro, -119, -104, "#bacbd2")
        rect(cx - hub, cx + hub, -125, -119, "#bacbd2")
    s.line(X(mx), Z(-111.5), X(x), Z(-111.5), "#283e49", "4 4")
    rect(x - 23, x + 23, -176, -131, "none")
    for z in cfg["bearing_centres_z_mm"]:
        for a, b in ((x - 16, x - 6), (x + 6, x + 16)):
            rect(a, b, z - 5, z + 5, "#ba899b")
    rect(x - 32, x + 32, -181, -176, "#6f8997")
    rect(mx - 30, mx + 30, -128, -124, "#6f8997")
    rect(90, 330, *cfg["shield_z_range_mm"], "#b6c1c7")
    for cx, side, z1 in ((mx, 26, -128), (x, 27, -181)):
        for sign in (-1, 1):
            rect(cx + side * sign - 3, cx + side * sign + 3, top, z1, "none", "3 3")
    s.dim(X(90), 635, X(330), "Vassoio 240")
    for yy, text in enumerate([
        "Interfaccia caldo/freddo z−85: aperta",
        "Schermo sul cassetto, non sul telaio",
        "Pulegge / schermo: 3 mm nominali",
        "Cartuccia separata dal motore",
        "Cuscinetti: Ø12 × Ø32 × 10",
        "Centri 25 / punti pressione 43 (ip.)",
        "Altezza inviluppo 136 / vano 160",
        "Residuo inferiore 24 mm grezzi",
        "14 mm oltre riserva di servizio10",
        "Driver fuori vano: ambiente ≤40 °C"
    ]):
        s.text(830, 160 + yy * 38, text, "small")
    s.text(45, 720, "Percorso carichi da progettare: disco → supporti qualificati → albero/cartucce → telaio → appoggio; non sulla scocca o sull'isolante.", "small")
    s.text(45, 756, "L'interfaccia superiore, il precarico e i dettagli di montaggio restano aperti: nessun albero costruttivo è definito da questa vista.", "small")
    return s.end()


def service(cfg, r):
    s = SVG("Manutenzione frontale — schema condizionato a freddo", "Abbassamento ed estrazione sono una proposta di percorso nel vuoto; telaio, guide e sweep nel forno reale ancora da verificare.")
    scale, ox = 1.45, 80
    Y = lambda y: ox + (y + 480) * scale
    Z = lambda z: 180 + (-85 - z) * scale
    bay0, bay1 = r["packaging"]["bay_bottom_top_z_mm"]
    front = cfg["front_skin_y_reference_mm"]
    s.rect(Y(front), Z(bay1), (315 - front) * scale, (bay1 - bay0) * scale, "#f4f7f9", "#93aab5", "5 4")
    p0, p1 = r["service"]["port_bottom_top_z_mm"]
    s.line(Y(front), Z(p0), Y(front), Z(p1), "#b28042")
    bottom, top = r["packaging"]["cassette_bottom_top_z_mm"]
    drop = cfg["service_lowering_mm"]
    s.rect(Y(115), Z(top), 180 * scale, (top - bottom) * scale, "none", "#5e8597")
    s.rect(Y(115), Z(top - drop), 180 * scale, (top - bottom) * scale, "none", "#b27b34", "7 4")
    move = r["service"]["horizontal_translation_to_fully_clear_front_mm"]
    s.rect(Y(115 - move), Z(top - drop), 180 * scale, (top - bottom) * scale, "#d7e7eb", "#397589")
    s.text(Y(205 - move), 153, "Modulo sfilato (abbassato)", "small", "middle")
    s.text(Y(205), 153, "In quota / abbassato (tratteggio)", "small", "middle")
    s.text(Y(front) + 14, Z(bay0) + 24, "Fronte: luce 280 × 144", "small")
    s.line(Y(front - 300), 465, Y(front), 465, "#769aa9")
    s.dim(Y(front - 300), 490, Y(front), "Spazio anteriore riservato 300")
    s.dim(Y(115 - move), 545, Y(115), "Traslazione " + n(move, 1))
    s.text(45, 605, "1. Forno freddo, alimentazione isolata; sostenere il disco prima di disconnettere l'interfaccia superiore.", "small")
    s.text(45, 640, "2. Liberare ritegni e connettori; abbassare la cassetta di12 mm con un sostegno/guida protetto ancora da progettare.", "small")
    s.text(45, 675, "3. Sfilare dal fronte insieme allo schermo. Luce proposta280 × 144; margini residui verticali1 + 1 dopo riserva3 per bordo.", "small")
    s.text(45, 710, "4. Non possibile in quota: l'albero supera il passaggio. Nessuna estrazione dal basso sul piano fisso.", "small")
    s.text(45, 760, "Tolleranze, utensili, peso cassetta, raccordi, guide e cablaggi possono invalidare il percorso: porta di servizio NON congelata.", "small")
    return s.end()


def all_drawings(cfg, v4, result):
    return {"pianta_C03.svg": plan(cfg, v4, result), "modulo_C03.svg": module(cfg, result), "servizio_C03.svg": service(cfg, result)}
