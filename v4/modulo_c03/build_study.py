"""Build C03 offline dossier from audited inputs, without modifying C01/C02."""
import argparse
import csv
from html import escape
import hashlib
import io
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from checks import HERE, evaluate, load
from drawings import all_drawings, n
from geometry import belt_mesh, mesh, parts

OUTPUT = HERE / "output"
PROJECT = HERE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jtext(data):
    return json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def fill(template, values):
    def replace(match):
        if match[1] not in values:
            raise ValueError(f"Unresolved token: {match[1]}")
        return str(values[match[1]])
    return re.sub(r"@@([A-Z0-9_]+)@@", replace, template)


def csv_text(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def audited_cad():
    audit = json.loads((HERE / "cad/audit_CAD.json").read_text(encoding="utf-8"))
    for key, path in (("layout_sha256", "layout.json"), ("componenti_sha256", "componenti.json"),
                      ("geometry_py_sha256", "geometry.py"), ("checks_py_sha256", "checks.py"), ("audit_cad_py_sha256", "audit_cad.py")):
        if audit[key] != sha(HERE / path):
            raise ValueError(f"Stale CAD audit: {path}. Repeat audit_cad.py first")
    for row in audit["supplier_sources"]:
        if row["sha256"] != sha(HERE / "fonti" / row["file"]) or not row["import_succeeded"]:
            raise ValueError("Supplier STEP differs from audited input")
    for filename, digest in audit["artefacts_sha256"].items():
        if sha(HERE / "cad" / filename) != digest:
            raise ValueError(f"Modified CAD artefact: {filename}")
    if audit["production_approved"] or audit["positive_volume_overlap_pairs"]:
        raise ValueError("CAD gate: positive-volume overlap or unsupported production approval")
    return audit


def watched():
    files = [HERE.parent / "quote_v4.json", HERE.parent / "concept_sfaccettato/concept.json",
             HERE.parent / "concept_sfaccettato/geometry.py", HERE.parent / "architettura_c02/assunzioni.json",
             HERE.parent / "architettura_c02/checks.py", HERE.parent / "architettura_c02/output/calcoli_C02.json",
             HERE.parent / "architettura_c02/output/provenienza.json"]
    return {str(p.relative_to(PROJECT)).replace("\\", "/"): sha(p) for p in files}


def inline(text):
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text)


def markdown_html(text, title):
    lines, chunks, i = text.splitlines(), [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
        elif line.startswith("#"):
            depth = len(line) - len(line.lstrip("#"))
            chunks.append(f"<h{depth}>{inline(line[depth:].strip())}</h{depth}>")
            i += 1
        elif line.startswith("|"):
            chunks.append("<div class='table-wrap'><table>")
            row_index = 0
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = lines[i].strip().strip("|").split("|")
                if not all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
                    tag = "th" if row_index == 0 else "td"
                    chunks.append("<tr>" + "".join(f"<{tag}>{inline(c.strip())}</{tag}>" for c in cells) + "</tr>")
                    row_index += 1
                i += 1
            chunks.append("</table></div>")
        elif re.match(r"(- |\d+\. )", line):
            ordered = bool(re.match(r"\d+\. ", line))
            tag = "ol" if ordered else "ul"
            chunks.append(f"<{tag}>")
            while i < len(lines) and re.match(r"(- |\d+\. )", lines[i].strip()):
                item = re.sub(r"^(- |\d+\. )", "", lines[i].strip())
                i += 1
                chunks.append("<li>" + inline(item) + "</li>")
            chunks.append(f"</{tag}>")
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(#|\||- |\d+\. )", lines[i].strip()):
                para.append(lines[i].strip())
                i += 1
            chunks.append("<p>" + inline(" ".join(para)) + "</p>")
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title>
<style>body{{margin:0;background:#edf2f5;color:#233b4b;font:16px/1.55 Arial,sans-serif}}article{{max-width:1100px;margin:25px auto;padding:28px 35px;background:white}}a{{color:#276e8c}}h1,h2,h3{{line-height:1.2}}h2{{margin-top:35px;border-top:1px solid #ccd8de;padding-top:18px}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{border:1px solid #cbd7dd;padding:7px;text-align:left;vertical-align:top}}th{{background:#edf4f6}}.table-wrap{{overflow:auto}}code{{font-size:13px;background:#eff4f6}}@media(max-width:760px){{article{{padding:18px;margin:0}}}}@media print{{body{{background:white}}article{{margin:0;padding:0}}}}</style></head><body><article><nav><a href="index.html">← C03: modulo e scheda</a></nav>{''.join(chunks)}</article></body></html>\n'''


def values(result, components, tests):
    d, m, p, s = (result[key] for key in ("drive", "mechanics", "packaging", "service"))
    table = ["| ID / quantità per modulo | Codice candidato / funzione | Documenti e gate |", "|---|---|---|"]
    for row in components["items"]:
        table.append(f"| {row['id']} /{row['quantity_one_module']} | {row['code']}. {row['role']} | {row['source']}. {row['gate']} |")
    speed = ["| Disco rpm | Riduttore rpm | Motore rpm | Microstep | Impulsi Hz |", "|---|---|---|---|---|"]
    for row in d["speed_rows"]:
        speed.append(f"| {n(row['disc_rpm'])} | {n(row['geared_output_rpm'])} | {n(row['bare_motor_rpm'],2)} | {row['microsteps_per_fullstep']} | {n(row['pulse_frequency_Hz'],2)} |")
    forces = ["| F0 per ramo N (assunto) | Ramo teso N | Ramo lento N | Radiale N | Confronto100N senza derating |", "|---|---|---|---|---|"]
    for row in m["belt_pretension_sensitivity"]:
        force = n(row["radial_resultant_N"], 2) if row["radial_resultant_N"] is not None else "modello invalido"
        forces.append(f"| {row['pretension_each_branch_N']} | {n(row['tight_N'],2)} | {n(row['slack_N'],2)} | {force} | {'sotto SOLO limite catalogo' if row['below_motor_radial_catalogue_limit_only'] else 'NO / ipotesi invalida'} |")
    sources = json.loads((HERE / "fonti/acquisizione.json").read_text(encoding="utf-8"))
    source_list = "\n".join(f"- [{row['file']}]({row['url']}) — {row['owner']}; archivio locale `../fonti/{row['file']}`, SHA-256 in acquisizione.json." for row in sources["files"])
    return {"HEIGHT": n(p["cassette_height_mm"], 0), "BOTTOM": n(p["bottom_raw_clearance_mm"], 0),
            "AFTER_RESERVE": n(p["bottom_after_service_reserve_mm"], 0), "PORT_TOP": n(s["lowered_top_passage_margin_mm"], 0),
            "PORT_BOTTOM": n(s["lowered_bottom_passage_margin_mm"], 0), "COMPONENT_TABLE": "\n".join(table),
            "RATIO": n(d["total_motor_to_disc_ratio"], 5), "SPEED_TABLE": "\n".join(speed), "BELT_TABLE": "\n".join(forces),
            "RS": n(d["small_pitch_radius_mm"], 4), "RL": n(d["large_pitch_radius_mm"], 4), "CENTRE": n(d["centre_distance_mm"], 2),
            "WRAP": n(d["small_wrap_deg"], 2), "TEETH": n(d["small_teeth_in_contact_geometric"], 2),
            "TORQUE": n(m["startup_torque_assumed_Nm"], 3), "MOTOR_TORQUE": n(d["required_geared_motor_torque_screening_Nm"], 3),
            "DELTA_FORCE": n(m["belt_force_comparison"]["delta_branch_N"], 2), "RADIAL": n(m["belt_force_comparison"]["radial_resultant_N"], 2),
            "STONE_MASS": n(m["stone_mass_kg"], 3), "MOVING_MASS": n(m["moving_mass_with_pizza_assumed_kg"], 3), "AXIAL": n(m["axial_scenario_N"], 1),
            "COUPLE": n(m["tool_only_radial_couple_per_bearing_N"], 1), "UPPER_REACTION": n(m["upper_radial_reaction_envelope_N"], 1),
            "LOWER_REACTION": n(m["lower_radial_reaction_envelope_N"], 1), "BENDING_MOMENT": n(m["shaft_max_moment_superposition_assumed_Nm"], 3),
            "BENDING_STRESS": n(m["shaft_bending_nominal_MPa"], 2), "VM_STRESS": n(m["shaft_von_mises_nominal_MPa"], 2),
            "STUB_DISP": n(m["stub_only_tool_moment_rim_displacement_mm"], 3), "SHAFT_HEAT": n(m["shaft_conduction_1D_each_W"], 2),
            "COPPER": n(m["motor_copper_two_phase_Irms_reference_W"], 2), "ENGAGEMENT": n(p["motor_shaft_pulley_bore_overlap_min_mm"], 0),
            "TEST_COUNT": tests, "SOURCE_LIST": source_list,
            "BOOLEAN_COUNT": audited_cad()["boolean_pairs_checked_after_AABB_filter"]}


def viewer(cfg, result):
    triangles = json.loads((HERE / "cad/PG5_mesh_preview.json").read_text(encoding="utf-8"))["triangles"]
    mx, my = result["packaging"]["modules"][0]["motor_centre_xy_mm"]
    transformed = [[[round(mx + p[0], 5), round(my - p[1], 5), round(cfg["motor_output_face_z_mm"] - 27.3 - p[2], 5)] for p in tri] for tri in triangles]
    data = {"faces": mesh(parts(cfg, result)) + belt_mesh(result), "motorTriangles": transformed}
    script = (HERE / "viewer.js").read_text(encoding="utf-8")
    encoded = json.dumps(data, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    return f'''<section class="scene-wrap"><div class="eyebrow">VISUALIZZATORE OFFLINE / SOLO MODULO SINISTRO</div><h2>Motore STEP e inviluppi della cassetta</h2><div class="scene-grid"><canvas id="scene" aria-label="Modulo freddo: trascina per ruotare, rotella per zoom"></canvas><aside class="controls"><strong id="scene-state"></strong><label><input id="show-shield" type="checkbox"> Mostra schermo solidale al cassetto</label><label><input id="show-motor" type="checkbox" checked> Mostra motore da STEP fornitore</label><button id="front">Fronte</button><button id="side">Lato</button><button id="top">Pianta</button><button id="reset">Assieme</button><p class="legend">Blu: motore da STEP originale.<br>Rosa: inviluppi cuscinetti.<br>Giallo: tratto freddo albero.<br>Grigio: parti custom/pulegge semplificate.</p><p><strong>Nessun modulo completo qualificato.</strong> Mancano sedi, viti, tenute, giunto/parti calde, telaio, guide e cablaggi. La vista non rappresenta temperature.</p></aside></div><p class="small">Trascina / zoom. Schermo occultato solo graficamente per vedere la trasmissione; il piano V4 e i due moduli sono nella tavola seguente.</p></section><script>const sceneData={encoded};\n{script}</script>'''


def planned_register():
    names = ["Montaggio", "Geometria", "Pretensione", "Velocita", "Coppia", "Carico_momento", "Temperatura_freddo", "Manutenzione", "Guasti", "Cicli"]
    return [{"id": f"BF{i:02d}", "prova_pianificata": name, "stato": "NON_ESEGUITA", "configurazione_seriali_revisioni": "",
             "data_ora": "", "operatore": "", "criteri_approvati_prima_prova": "", "strumenti_calibrazione": "",
             "incertezza": "", "carichi_reali": "", "velocita_misurata_rpm": "", "coppia_spunto_Nm": "", "coppia_marcia_Nm": "",
             "tensione_cinghia_N": "", "temperatura_aria_motore_cartucce_driver_C": "", "corrente_misurata_A_tipo": "",
             "eccentricita_oscillazione_mm": "", "durata_ripetizioni": "", "file_grezzi": "", "anomalie": "", "esito_revisore": ""}
            for i, name in enumerate(names, 1)]


def candidate_csv(components):
    rows = [{"id": row["id"], "candidato_codice_NON_approvato": row["code"], "quantita_studio_un_modulo": row["quantity_one_module"],
             "funzione": row["role"], "documento": row["source"], "stato": "CANDIDATO_NON_APPROVATO", "gate": row["gate"], "produzione_approvata": False}
            for row in components["items"]]
    for i, name in enumerate(("Pietra_carrier_appoggi_caldi", "Albero_giunto_ritenzioni", "Cartuccia_sedi_distanziali_grasso_tenute", "Telaio_vassoio_guide_schermo_carter", "Quadro_alimentatore_controller_protezioni_cavi", "Sensori_feedback_arresto"), 1):
        rows.append({"id": f"CUSTOM{i:02d}", "candidato_codice_NON_approvato": "", "quantita_studio_un_modulo": "kit_da_definire", "funzione": name,
                     "documento": "nessun prodotto qualificato", "stato": "MANCANTE_NON_ORDINABILE", "gate": "Progettare e riesaminare prima del banco", "produzione_approvata": False})
    return csv_text(rows)


def build():
    before = watched()
    cfg, components, v4, c02 = load()
    audit = audited_cad()
    result = evaluate(cfg, components, v4, c02)
    drawings = all_drawings(cfg, v4, result)
    for content in drawings.values():
        ET.fromstring(content)
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py"))
    if not tests.wasSuccessful():
        raise RuntimeError(log.getvalue())
    vals = values(result, components, tests.testsRun)
    vals.update({"PLAN": drawings["pianta_C03.svg"], "MODULE": drawings["modulo_C03.svg"], "SERVICE": drawings["servizio_C03.svg"], "VIEWER": ""})
    template = (HERE / "sheet.template.html").read_text(encoding="utf-8")
    paper = fill(template, vals)
    vals["VIEWER"] = viewer(cfg, result)
    index = fill(template, vals)
    report = fill((HERE / "report.template.md").read_text(encoding="utf-8"), vals)
    result["software_validation"] = {"tests_run": tests.testsRun, "successful": True, "scope": "Software/input consistency ONLY; no real-oven validation"}
    products = {**drawings, "index.html": index, "scheda_stampa.html": paper, "RAPPORTO_C03.md": report,
                "rapporto.html": markdown_html(report, "Rapporto completo C03"), "calcoli_C03.json": jtext(result),
                "componenti_C03.json": jtext(components), "audit_CAD.json": jtext(audit),
                "distinta_candidati.csv": candidate_csv(components), "registro_banco_freddo.csv": csv_text(planned_register()),
                "velocita.csv": csv_text(result["drive"]["speed_rows"]), "pretensione_confronti.csv": csv_text(result["mechanics"]["belt_pretension_sensitivity"]),
                "test_generatore.log": log.getvalue()}
    for name, html_name in (("RICHIESTE_TECNICHE_C03.md", "richieste_tecniche.html"), ("PIANO_FREDDO_C03.md", "piano_freddo.html")):
        text = (HERE / name).read_text(encoding="utf-8")
        products[name] = text
        products[html_name] = markdown_html(text, name)
    if before != watched():
        raise RuntimeError("A preserved input changed during build")
    OUTPUT.mkdir(exist_ok=True)
    for name, content in products.items():
        (OUTPUT / name).write_text(content, encoding="utf-8-sig" if name.endswith(".csv") else "utf-8", newline="")
    own = [p for p in HERE.iterdir() if p.is_file()]
    own += [p for folder in (HERE / "fonti", HERE / "cad") for p in folder.iterdir() if p.is_file()]
    manifest = {"study_id": "C03", "production_approved": False, "date": "2026-10-03", "pre_existing_read_inputs_unchanged_during_build": True,
                "pre_existing_sources_sha256": before, "own_inputs_sha256": {str(p.relative_to(HERE)).replace("\\", "/"): sha(p) for p in sorted(own)},
                "generated_sha256": {name: sha(OUTPUT / name) for name in sorted(products)}, "tests_run": tests.testsRun,
                "physical_tests_executed": False, "CFD_executed": False, "supplier_requests_sent": False,
                "scope": "Component shortlist + mixed supplier/envelope cold CAD; not complete CAD or safety/manufacturing approval",
                "PDF_PNG_note": "Separate export; re-run export_preview.ps1 after every build. See esportazione.json."}
    (OUTPUT / "provenienza.json").write_text(jtext(manifest), encoding="utf-8")
    print(f"C03 generated: {OUTPUT}; {tests.testsRun} software tests passed.")
    print("Preserved read inputs unchanged. PDF/PNG require export_preview.ps1.")


EXPORTS = ["Scheda_C03.pdf", "pianta_C03.png", "modulo_C03.png", "servizio_C03.png", "anteprima.png"]
EXPORT_INPUTS = ["index.html", "scheda_stampa.html", "pianta_C03.svg", "modulo_C03.svg", "servizio_C03.svg"]


def record_export():
    for name in EXPORTS:
        data = (OUTPUT / name).read_bytes()
        signature = b"%PDF" if name.endswith(".pdf") else b"\x89PNG\r\n\x1a\n"
        if len(data) < 1000 or not data.startswith(signature):
            raise ValueError(f"Invalid/missing export: {name}")
    # Chromium exports ordinary uncompressed Page dictionaries. Fail closed
    # if pagination changes or a different exporter requires a proper parser.
    pdf_data = (OUTPUT / "Scheda_C03.pdf").read_bytes()
    page_count = len(re.findall(rb"/Type\s*/Page\b", pdf_data))
    if page_count != 5:
        raise ValueError(f"Expected five Chromium PDF pages, found {page_count}. Inspect print CSS/exporter before delivery")
    (OUTPUT / "esportazione.json").write_text(jtext({"study_id": "C03", "inputs_sha256": {n: sha(OUTPUT / n) for n in EXPORT_INPUTS},
                                                   "exports_sha256": {n: sha(OUTPUT / n) for n in EXPORTS}, "method": "isolated headless browser",
                                                   "PDF_page_dictionary_count": page_count,
                                                   "scope": "Visual previews ONLY; non-executive study"}), encoding="utf-8")
    print("C03 browser export provenance recorded.")


def verify():
    manifest = json.loads((OUTPUT / "provenienza.json").read_text(encoding="utf-8"))
    count = 0
    for key, base in (("pre_existing_sources_sha256", PROJECT), ("own_inputs_sha256", HERE), ("generated_sha256", OUTPUT)):
        for name, digest in manifest[key].items():
            if sha(base / name) != digest:
                raise ValueError(f"Hash mismatch: {name}")
            count += 1
    export = json.loads((OUTPUT / "esportazione.json").read_text(encoding="utf-8"))
    for key in ("inputs_sha256", "exports_sha256"):
        for name, digest in export[key].items():
            if sha(OUTPUT / name) != digest:
                raise ValueError(f"Stale browser export: {name}")
            count += 1
    links = 0
    for path in OUTPUT.glob("*.html"):
        for href in re.findall(r'href="([^"]+)"', path.read_text(encoding="utf-8")):
            if re.match(r"[a-z]+:", href) or href.startswith("#"):
                continue
            if not (path.parent / href.split("#")[0]).exists():
                raise ValueError(f"Broken local link: {path.name} → {href}")
            links += 1
    print(f"C03 delivery verified: {count} hashes, {links} local links; browser export inputs current.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    flags = parser.add_mutually_exclusive_group()
    flags.add_argument("--record-export", action="store_true")
    flags.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    record_export() if args.record_export else verify() if args.verify else build()
