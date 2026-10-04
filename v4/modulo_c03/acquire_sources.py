"""Archive public, read-only technical downloads. No supplier messages/orders."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
SOURCES = [
    ("P01", "STEPPERONLINE", "PG5_pagina.html", "https://www.omc-stepperonline.com/nema-17-stepper-motor-bipolar-l-48mm-w-gear-ratio-5-1-planetary-gearbox-17hs19-1684s-pg5"),
    ("P01", "STEPPERONLINE", "PG5_scheda.pdf", "https://www.omc-stepperonline.com/index.php?route=product/product/get_file&file=183/17HS19-1684S-PG5_Full_Datasheet.pdf"),
    ("P01", "STEPPERONLINE", "PG5_fornitore.STEP", "https://www.omc-stepperonline.com/index.php?route=product/product/get_file&file=183/17HS19-1684S-PG5.STEP"),
    ("P01", "STEPPERONLINE", "PG5_curva_coppia.pdf", "https://www.omc-stepperonline.com/index.php?route=product/product/get_file&file=183/17HS19-1684S-PG5_Torque_Curve.pdf"),
    ("P02", "STEPPERONLINE", "WGA_pagina.html", "https://www.omc-stepperonline.com/brushed-24v-dc-gear-motor-22kg-cm-8rpm-w-422-1-worm-gearbox-wga-4058247000-g422"),
    ("P02", "STEPPERONLINE", "WGA_scheda.pdf", "https://www.omc-stepperonline.com/index.php?route=product/product/get_file&file=3054/WGA-4058247000-G422.pdf"),
    ("P02", "STEPPERONLINE", "WGA_fornitore.STEP", "https://www.omc-stepperonline.com/index.php?route=product/product/get_file&file=3054/WGA-4058247000-G422.STEP"),
    ("P03", "SKF (copia pubblicata da RS)", "SKF_7201_BEGAP_RS.pdf", "https://docs.rs-online.com/31d5/A700000013821012.pdf"),
    ("P04", "MAEDLER", "pulegge_T5.pdf", "https://smarthost.maedler.de/datenblaetter/K43_150_EN.pdf"),
    ("P04", "MAEDLER", "puleggia_16_pagina.html", "https://www.maedler.de/Article/16221600"),
    ("P04", "MAEDLER", "puleggia_32_pagina.html", "https://www.maedler.de/Article/16223200"),
    ("P05", "MAEDLER", "cinghia_280_pagina.html", "https://www.maedler.de/Article/16261300"),
    ("P05", "MAEDLER", "cinghie_T5.pdf", "https://smarthost.maedler.de/datenblaetter/K43_207_EN.pdf"),
    ("P05", "MAEDLER", "calcolo_cinghie.pdf", "https://smarthost.maedler.de/datenblaetter/zahnriemenantriebe_EN.pdf"),
    ("P06", "STEPPERONLINE", "DM542T_V4_manual.pdf", "https://www.omc-stepperonline.com/index.php?route=product/product/get_file&file=382/DM542T_V4.0.pdf"),
    ("P06", "STEPPERONLINE", "DM542T_pagina.html", "https://www.omc-stepperonline.com/digital-stepper-driver-1-0-4-2a-20-50vdc-for-nema-17-23-24-stepper-motor-dm542t"),
    ("P07", "Promat / Etex", "PROMASIL_1000L_1100_SUPER_IT.pdf", "https://media.promat.com/pd36064/original/241012037/promasil-1000l--1100-super_tds_it.pdf"),
    ("P07", "Promat / Etex (edizione US)", "PROMASIL_1000L_SDS_US.pdf", "https://media.promat.com/doc_682572_us/original/342586981/promat-sds-promasil-1000l-en-us.pdf?brand=promatconstruction&market=us"),
]


def validate(name, data):
    if len(data) < 500:
        raise ValueError(f"Empty download: {name}")
    if name.endswith(".pdf") and not data.startswith(b"%PDF"):
        raise ValueError(f"Not a PDF: {name}")
    if name.endswith(".STEP") and b"ISO-10303-21" not in data[:200]:
        raise ValueError(f"Not a STEP: {name}")


def main():
    folder = HERE / "fonti"
    folder.mkdir(exist_ok=True)
    old_path = folder / "acquisizione.json"
    old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else {"files": []}
    known = {row["file"]: row for row in old["files"]}

    def acquire(source):
        source_id, owner, name, url = source
        path = folder / name
        if path.exists():
            row = known.get(name)
            if row is None or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(f"Existing unrecognized/modified file, not overwritten: {path}")
            return row
        linked_url = url
        # Public regional catalogue: the global download endpoint returns 403.
        # No authentication, form submissions, CAPTCHA or private access used.
        if "route=product/product/get_file" in url:
            url = url.replace("www.omc-stepperonline.com", "au-stepperonline.com")
        request = Request(url, headers={"User-Agent": "Mozilla/5.0",
                                       "Referer": "https://www.omc-stepperonline.com/"})
        with urlopen(request, timeout=90) as response:
            data = response.read()
            final_url = response.url
        validate(name, data)
        with path.open("xb") as stream:
            stream.write(data)
        return {"source_id": source_id, "owner": owner, "file": name,
                "url": url, "global_catalogue_link": linked_url,
                "resolved_url": final_url, "checked": "2026-10-03",
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs = [(source, pool.submit(acquire, source)) for source in SOURCES]
        for source, job in jobs:
            try:
                row = job.result()
                rows.append(row)
                print(f"OK {row['file']}: {row['bytes']} bytes")
            except Exception as error:
                errors.append({"file": source[2], "error": str(error)})
                print(f"FAILED {source[2]}: {error}")
    old_path.write_text(json.dumps({"scope": "Public downloads only; no supplier contact/order",
                                   "files": rows, "errors": errors}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
