"""Generate the C02 dossier, limited to this directory's own output artefacts."""
from __future__ import annotations

import argparse
import csv
import hashlib
from html import escape
import io
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from checks import HERE, evaluate, load
from drawings import all_drawings, num

OUTPUT = HERE / "output"
PROJECT = HERE.parent.parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def fill(template, values):
    """Fail instead of silently delivering an unresolved numerical placeholder."""
    def substitute(match):
        key = match.group(1)
        if key not in values:
            raise ValueError(f"Unresolved template token: {key}")
        return str(values[key])
    return re.sub(r"@@([A-Z0-9_]+)@@", substitute, template)


def report_values(results, materials, test_count):
    m,f,b = results["mechanical"],results["flue_geometry"],results["body_budget"]["C02_body_only"]
    rows = {r["id"]:r for r in results["pressure_scenarios"]}
    comparison = rows["C02_PUNTO_DI_CONFRONTO"]["closed_door_budget"]
    names = {"RIFERIMENTO_MATLAB_60_H1": "Base 60 / Ø130 / H1 / Ka0",
             "C02_PUNTO_DI_CONFRONTO": "C02 90 / Ø130 / H1,5 / Ka2",
             "C02_PORTA_APERTA": "C02 stessa presa / porta aperta",
             "C02_T150_K8_VENTO3": "C02 T150 / Kfumi8 / vento 3 Pa",
             "C02_FREDDO100_K8_VENTO3": "C02 T100 / Kfumi8 / vento 3 Pa",
             "C02_D150_CON_STESSE_IPOTESI": "Confronto Ø150 / stesse ipotesi",
             "C02_WIND10_INVERSIONE_POSSIBILE": "Vento 10 Pa / inversione prevista"}
    pressure_table=[]
    for key,label in names.items():
        r = rows[key]
        budget = r["closed_door_budget"]
        margin = num(budget["margin_Pa"],2) if budget else "—"
        pressure_table.append(f"| {label} | {num(r['lambda_rear'],2)} | {num(r['door_out_gas_kg_h'],1)} | {margin} |")
    material_table = ["| Zona /ID | Candidato e dati acquisiti | Verifiche ancora richieste |", "|---|---|---|"]
    for item in materials["items"]:
        source = item["source_id"] or "nessuna scheda esatta"
        material_table.append(f"| {item['zone']} /{item['id']} | {item['candidate']} [{source}]. {item['study_dimension']}. {item['verified_facts']} | {item['release_gate']} |")
    sources = ["### Fonti produttori consultate e archiviate"]
    for source in materials["sources"]:
        sources.append(f"- [{source['id']} — {source['owner']}: {source['title']}]({source['url']}). Archivio `{source['archive']}`; {source['locations']}; consultato {source['checked']}.")
    return {"STONE_MASS":num(m["stone_mass_each_kg"],2), "MOVING_MASS":num(m["assumed_rotating_mass_with_pizza_kg"],2),
            "AXIAL_LOAD":num(m["assumed_axial_load_with_tool_N"],1), "TOOL_MOMENT":num(m["tool_at_stone_edge_overturning_moment_Nm"],1),
            "TORQUE_MIN":num(min(t["starting_screening_Nm"] for t in m["torque_sensitivity"]),2),
            "TORQUE_MAX":num(max(t["starting_screening_Nm"] for t in m["torque_sensitivity"]),2),
            "STEEL_GROWTH":num(m["steel_spreader_diameter_growth_mm"],2), "STONE_GROWTH":num(m["stone_diameter_growth_assumed_mm"],2),
            "STRAIN_DIFF":num(m["thermal_strain_difference_equivalent_over_320mm"],2),
            "SHAFT_SOLID":num(m["shaft_heat_screening"][0]["conducted_W_each"],2),
            "SHAFT_HOLLOW":num(m["shaft_heat_screening"][1]["conducted_W_each"],2),
            "SHAFT_LARGE":num(m["shaft_heat_screening"][2]["conducted_W_each"],2),
            "MODULE_GAP":num(m["module_separation_mm"],0), "PARALLEL_HEIGHT":num(m["parallel_required_height_mm"],0),
            "PARALLEL_120":num(m["bay_comparison"][0]["parallel_remaining_mm"],0),
            "PARALLEL_160":num(m["bay_comparison"][1]["parallel_remaining_mm"],0),
            "COAXIAL_HEIGHT":num(m["coaxial_required_height_mm"],0),
            "COAXIAL_120":num(m["bay_comparison"][0]["coaxial_remaining_mm"],0),
            "COAXIAL_160":num(m["bay_comparison"][1]["coaxial_remaining_mm"],0),
            "BODY_INCREMENT":num(m["increment_body_height_from_c01_mm"],1),
            "BODY_WIDTH":num(b["width_mm"],0), "BODY_DEPTH":num(b["depth_mm"],0), "BODY_HEIGHT":num(b["body_height_with_feet_mm"],0),
            "BODY_SIZE":" × ".join(num(b[k],0) for k in ("width_mm","depth_mm","body_height_with_feet_mm")),
            "REQUIRED_AIR":num(comparison["required_air_kg_h"],1), "AIR_VOLUME":num(comparison["required_air_at_ambient_m3_h"],1),
            "PRESSURE_TABLE":"\n".join(pressure_table), "PREFERRED_MARGIN":num(comparison["margin_Pa"],2),
            "ADVERSE_MARGIN":num(rows["C02_T150_K8_VENTO3"]["closed_door_budget"]["margin_Pa"],2),
            "OPEN_OUTFLOW":num(rows["C02_PORTA_APERTA"]["door_out_gas_kg_h"],1),
            "ENTRY_AREA":num(f["collector_entry_area_cm2"],0), "NECK_AREA":num(f["collector_neck_area_cm2"],0),
            "PIPE_AREA":num(f["throat_comparison"][0]["area_cm2"],1),
            "FLAT_NECK_PERCENT":num(100*f["throat_comparison"][0]["same_30mm_height_at_width_D_ratio"],1),
            "OLD_COLLAR":num(f["C01_collar_top_across_flats_mm"],1),
            "PLATE_OCTAGON_MIN":num(f["collar_plate_budget"]["min_regular_octagon_outer_across_flats_mm"],1),
            "COLLAR_OVERHANG":num(results["body_budget"]["collar_base_plan_overhang_from_C01_front_mm"],1),
            "TEST_COUNT":test_count, "SCENARIO_COUNT":len(results["pressure_scenarios"]),
            "MASS_RESIDUAL":f"{max(abs(r['mass_residual_kg_s']) for r in rows.values()):.2e}",
            "MATERIAL_TABLE":"\n".join(material_table), "SOURCES":"\n".join(sources)}


def sheet_html(results, materials, test_count, drawings):
    values=report_values(results,materials,test_count)
    values.update({"PIANTA":drawings["pianta_moduli.svg"],"DISCO":drawings["modulo_disco.svg"],
                   "ARIA":drawings["schema_aria_fumi.svg"],"CAMINO":drawings["collare_tiraggio.svg"]})
    return fill((HERE / "scheda.template.html").read_text(encoding="utf-8"),values)


def inline_md(text):
    """Small renderer for this dossier's trusted Markdown, not arbitrary HTML."""
    text=escape(text)
    text=re.sub(r"`([^`]+)`",r"<code>\1</code>",text)
    text=re.sub(r"\*\*([^*]+)\*\*",r"<strong>\1</strong>",text)
    text=re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)",r'<a href="\2">\1</a>',text)
    return text


def markdown_html(markdown, title):
    # Only headings, paragraphs, tables, lists and inline formatting are used.
    lines=markdown.splitlines()
    chunks=[]
    i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:
            i+=1
            continue
        if line.startswith("#"):
            depth=len(line)-len(line.lstrip("#"))
            chunks.append(f"<h{depth}>{inline_md(line[depth:].strip())}</h{depth}>")
            i+=1
        elif line.startswith("|"):
            table=[]
            while i<len(lines) and lines[i].strip().startswith("|"):
                cells=lines[i].strip().strip("|").split("|")
                if not all(re.fullmatch(r"\s*:?-+:?\s*",c) for c in cells):
                    table.append(cells)
                i+=1
            chunks.append("<div class='table-wrap'><table>")
            for j,cells in enumerate(table):
                tag="th" if j==0 else "td"
                chunks.append("<tr>"+"".join(f"<{tag}>{inline_md(c.strip())}</{tag}>" for c in cells)+"</tr>")
            chunks.append("</table></div>")
        elif re.match(r"(?:- |\d+\. )",line):
            ordered=bool(re.match(r"\d+\. ",line))
            tag="ol" if ordered else "ul"
            chunks.append(f"<{tag}>")
            while i<len(lines) and re.match(r"(?:- |\d+\. )",lines[i].strip()):
                item=re.sub(r"^(?:- |\d+\. )","",lines[i].strip())
                i+=1
                while i<len(lines) and lines[i].startswith("  ") and lines[i].strip():
                    item+=" "+lines[i].strip()
                    i+=1
                chunks.append(f"<li>{inline_md(item)}</li>")
            chunks.append(f"</{tag}>")
        else:
            paragraph=[]
            while i<len(lines) and lines[i].strip() and not re.match(r"(?:#|\||- |\d+\. )",lines[i].strip()):
                paragraph.append(lines[i].strip())
                i+=1
            chunks.append("<p>"+inline_md(" ".join(paragraph))+"</p>")
    return f'''<!doctype html><html lang="it"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)}</title>
<style>body{{font:16px/1.55 Arial,sans-serif;color:#223542;background:#edf2f5;margin:0}}
article{{max-width:1100px;margin:25px auto;background:white;padding:28px 35px}}
a{{color:#206986}}h1,h2,h3{{line-height:1.2}}h2{{border-top:1px solid #ccd7dd;padding-top:22px;margin-top:32px}}
.table-wrap{{overflow-x:auto}}table{{border-collapse:collapse;font-size:13px;width:100%}}th,td{{border:1px solid #ccd7dd;padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:#edf3f6}}code{{font-size:13px;background:#eef3f5;padding:2px 3px}}li{{margin-bottom:6px}}
@media(max-width:760px){{article{{padding:18px;margin:0}}}}@media print{{body{{background:white}}article{{margin:0;padding:0}}}}
</style><article><nav><a href="index.html">← Scheda C02 e tavole</a></nav>{''.join(chunks)}</article></html>\n'''


def pressure_csv(results):
    rows=[]
    for scenario in results["pressure_scenarios"]:
        row={k:v for k,v in scenario.items() if k!="closed_door_budget"}
        budget=scenario["closed_door_budget"]
        row.update({f"budget_{k}":v for k,v in (budget or {}).items()})
        rows.append(row)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    text=io.StringIO(newline="")
    writer=csv.DictWriter(text,fieldnames=fields,delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return text.getvalue()


def preliminary_parts_csv(materials):
    """Functional groups only: no purchase codes or approved quantities."""
    rows = [{"id": item["id"], "zona": item["zone"],
             "quantita_di_studio": item["study_quantity"], "candidato": item["candidate"],
             "quote_riserve": item["study_dimension"], "fonte": item["source_id"] or "",
             "codice_commerciale_selezionato": "", "stato": "da_qualificare_non_ordinabile",
             "gate": item["release_gate"], "produzione_approvata": False}
            for item in materials["items"]]
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=list(rows[0]), delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return text.getvalue()


def watched_sources(cfg):
    paths=[HERE/cfg["source_v4"],HERE/cfg["source_c01"],HERE.parent/"concept_sfaccettato"/"geometry.py",
           PROJECT/"dimensionamento"/"oven_draft_network.m",PROJECT/"dimensionamento"/"oven_draft_defaults.m",
           PROJECT/"dimensionamento"/"results"/"VERIFICHE_COMPATTA.md",
           PROJECT/"cfd"/"home_pc"/"campaign_config.json",PROJECT/"cfd"/"home_pc"/"campaign"/"readiness.json"]
    return {str(p.resolve().relative_to(PROJECT)).replace("\\","/"):sha256(p) for p in paths}


def build():
    cfg,v4,c01=load()
    originals=watched_sources(cfg)
    materials=json.loads((HERE/"materiali_candidati.json").read_text(encoding="utf-8"))
    result=evaluate(cfg,v4,c01)
    drawings=all_drawings(cfg,v4,result)
    for text in drawings.values():
        ET.fromstring(text)
    test_log=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(HERE),pattern="test_*.py")
    tests=unittest.TextTestRunner(stream=test_log,verbosity=2).run(suite)
    if not tests.wasSuccessful():
        raise RuntimeError(test_log.getvalue())
    values=report_values(result,materials,tests.testsRun)
    report=fill((HERE/"report.template.md").read_text(encoding="utf-8"),values)
    html=sheet_html(result,materials,tests.testsRun,drawings)
    result["software_validation"]={"tests_run":tests.testsRun,"successful":True,
                                   "note":"Numerical/software consistency only, not real-oven validation"}
    products={**drawings,"calcoli_C02.json":json_text(result),"rete_pressione.csv":pressure_csv(result),
              "distinta_preliminare.csv":preliminary_parts_csv(materials),
              "materiali_C02.json":json_text({**materials,"archive_root_from_output":".."}),
              "RAPPORTO_C02.md":report,"rapporto.html":markdown_html(report,"Rapporto C02 — completo"),
              "index.html":html,"scheda_stampa.html":html,"test_generatore.log":test_log.getvalue()}
    for name in ("RICHIESTE_FORNITORI.md","PIANO_BANCO_C02.md"):
        content=(HERE/name).read_text(encoding="utf-8")
        products[name]=content
        products["richieste_fornitori.html" if name.startswith("RICHIESTE") else "piano_banco.html"]=markdown_html(content,name)
    after=watched_sources(cfg)
    if originals!=after:
        raise RuntimeError("A pre-existing input changed during the build; no delivery generated")
    OUTPUT.mkdir(exist_ok=True)
    for name,content in products.items():
        (OUTPUT/name).write_text(content,encoding="utf-8-sig" if name.endswith(".csv") else "utf-8",newline="")
    local_sources=[p for p in HERE.iterdir() if p.is_file()]
    local_sources+=sorted((HERE/"fonti").iterdir())
    manifest={"study_id":"C02","date":cfg["date"],"production_approved":False,
              "pre_existing_sources_sha256":originals,"pre_existing_read_inputs_unchanged_during_build":True,
              "own_inputs_sha256":{str(p.relative_to(HERE)).replace("\\","/"):sha256(p) for p in local_sources if p.is_file()},
              "generated_sha256":{name:sha256(OUTPUT/name) for name in sorted(products)},
              "tests_run":tests.testsRun,"pressure_scenario_rows":len(result["pressure_scenarios"]),
              "maximum_abs_mass_residual_kg_s":max(abs(r["mass_residual_kg_s"]) for r in result["pressure_scenarios"]),
              "full_CFD_executed":False,"physical_tests_executed":False,
              "PDF_PNG_note":"Separate browser exports: regenerate AFTER build and see esportazione.json. No PDF/PNG validation is implied here."}
    (OUTPUT/"provenienza.json").write_text(json_text(manifest),encoding="utf-8")
    print(f"C02 generated: {OUTPUT}")
    print(f"{tests.testsRun} tests passed; {len(result['pressure_scenarios'])} pressure-scenario rows; 4 SVG schemes.")
    print("Pre-existing read inputs unchanged. PDF/PNG: run export_preview.ps1 after this build.")


def record_exports():
    """Record browser artefacts and the exact HTML/SVG input hashes."""
    files=["Scheda_C02.pdf","pianta_moduli.png","modulo_disco.png","schema_aria_fumi.png","collare_tiraggio.png","anteprima.png"]
    for name in files:
        data=(OUTPUT/name).read_bytes()
        signature=b"%PDF" if name.endswith(".pdf") else b"\x89PNG\r\n\x1a\n"
        if not data.startswith(signature) or len(data)<1000:
            raise ValueError(f"Invalid/missing browser export: {name}")
    names=["index.html","scheda_stampa.html", *all_drawings(*_drawing_args()).keys()]
    record={"study_id":"C02","method":"isolated headless browser, see export_preview.ps1",
            "inputs_sha256":{n:sha256(OUTPUT/n) for n in names},
            "exports_sha256":{n:sha256(OUTPUT/n) for n in files},
            "scope":"Browser previews of preliminary SCHEMES, not CAD or manufacturing drawings"}
    (OUTPUT/"esportazione.json").write_text(json_text(record),encoding="utf-8")
    print("Browser export provenance recorded.")


def _drawing_args():
    cfg,v4,c01=load()
    return cfg,v4,evaluate(cfg,v4,c01)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-export",action="store_true")
    args=parser.parse_args()
    record_exports() if args.record_export else build()
