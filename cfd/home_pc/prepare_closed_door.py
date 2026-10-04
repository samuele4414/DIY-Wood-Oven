"""Prepare a sealed-front-door V4 preheat comparison; never invokes FDS."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
CFD = HERE.parent
BASE = HERE / "campaign"
OUTPUT = HERE / "campaign_door_closed"
ARCHIVE = HERE.parent.parent / "forno_v4_porta_chiusa_pc_casa.zip"
CHID = "v4_preheat_door"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(base: Path = BASE, output: Path = OUTPUT) -> Path:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    source = base / "preheat" / "preheat.fds"
    if digest(source) != manifest["preheat_input_sha256"]:
        raise ValueError("Baseline FDS input differs from its manifest")
    case = json.loads((base / "preheat" / "case.json").read_text(encoding="utf-8"))
    if (case["mouth_width"], case["mouth_height"], case["front_extension"]) != (0.72, 0.16, 0.08):
        raise ValueError("Closed-door obstruction needs recalculation for this mouth geometry")
    text = source.read_text(encoding="ascii")
    text, changed = re.subn(r"&HEAD CHID='v4_preheat', TITLE='[^']*' /",
                            f"&HEAD CHID='{CHID}', TITLE='V4 empty oven, fully closed front door' /", text, count=1)
    if changed != 1 or "&TAIL /" not in text:
        raise ValueError("Unexpected baseline FDS structure")
    # The entrance vestibule is one 25 mm cell deep here. The door seals the
    # whole discretised mouth: x=.025-.775, z=0-.15, y=-.075..-.05 m.
    # No front air slot. The flue OPEN boundary from the baseline is retained.
    door = (
        "&SURF ID='FRONT_DOOR', MATL_ID(1,1)='STEEL', MATL_ID(2,1)='INSULATION', "
        "MATL_ID(3,1)='STEEL', THICKNESS=0.0015,0.025,0.001, TMP_INNER=25, "
        "TMP_GAS_BACK=25, HEAT_TRANSFER_COEFFICIENT_BACK=8., EMISSIVITY=0.9 /\n"
        "&OBST ID='CLOSED_FRONT_DOOR', XB=0.025,0.775,-0.075,-0.05,0,0.15, "
        "SURF_ID='FRONT_DOOR' /\n"
        "&DEVC ID='flue_inward_z_negative', XB=0.33,0.46,-0.02,0.11,1.255,1.255, "
        "QUANTITY='MASS FLOW -', SPATIAL_STATISTIC='AREA INTEGRAL' /\n"
    )
    text = text.replace("&TAIL /", door + "&TAIL /")
    pre = output / "preheat"
    pre.mkdir(parents=True)
    (pre / "preheat.fds").write_text(text, encoding="ascii")
    case.update(id=CHID, label="V4 porta anteriore chiusa", front_door="fully_closed",
                front_door_air_gap_m=0, chimney_open=True,
                thermal_model="Empty oven cold-start, closed front door, open chimney")
    (pre / "case.json").write_text(json.dumps(case, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    metadata = json.loads((base / "preheat" / "v4_preheat_metadata.json").read_text(encoding="utf-8"))
    metadata.update(case_id=CHID, fds_input="preheat.fds", front_door="fully_closed")
    (pre / f"{CHID}_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.copy2(base / "preheat" / "probes.json", pre / "probes.json")
    profiles = json.loads((base / "preheat" / "profiles.json").read_text(encoding="utf-8"))
    for profile in profiles:
        profile["file"] = profile["file"].replace("v4_preheat_", CHID + "_")
    (pre / "profiles.json").write_text(json.dumps(profiles, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.copy2(base / "campaign_config.json", output / "campaign_config.json")
    new_manifest = {
        "schema": 1,
        "config_sha256": digest(output / "campaign_config.json"),
        "preheat_input_sha256": digest(pre / "preheat.fds"),
        "reference_open_input_sha256": digest(source),
        "stages": {
            "preheat": {"directory": "preheat", "input": "preheat.fds", "chid": CHID,
                        "duration_s": manifest["stages"]["preheat"]["duration_s"]},
            "bake": {"directory": "bake", "input": "bake.fds", "chid": "v4_bake",
                     "duration_s": manifest["stages"]["bake"]["duration_s"]},
        },
        "note": "Only preheat is prepared. Do not run bake for this comparison.",
    }
    (output / "manifest.json").write_text(json.dumps(new_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def package(campaign: Path, archive: Path = ARCHIVE) -> Path:
    if archive.exists():
        raise FileExistsError(f"Refusing to overwrite {archive}")
    files = {
        "cfd/home_pc/run_home.py": HERE / "run_home.py",
        "cfd/home_pc/export_results.py": HERE / "export_results.py",
        "cfd/home_pc/requirements.txt": HERE / "requirements.txt",
        "cfd/postprocess.py": CFD / "postprocess.py",
        "cfd/v4_fire/export_volume.py": CFD / "v4_fire" / "export_volume.py",
        "cfd/v4_fire/render_video.py": CFD / "v4_fire" / "render_video.py",
        "LEGGIMI_PORTA_CHIUSA.md": HERE / "README_DOOR_CLOSED.md",
    }
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, source in files.items():
            bundle.write(source, name)
        for source in campaign.rglob("*"):
            if source.is_file():
                bundle.write(source, "cfd/home_pc/campaign_door_closed/" + source.relative_to(campaign).as_posix())
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    campaign = prepare(output=args.output.resolve())
    archive = package(campaign, args.archive.resolve())
    print(f"Prepared: {campaign}\nPortable ZIP: {archive}\nFDS was not executed.")


if __name__ == "__main__":
    main()
