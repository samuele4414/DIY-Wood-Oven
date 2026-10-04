"""Optional Gmsh/OCC import audit and mixed supplier/envelope STEP export.

Dependencies are installed in an isolated temporary directory, never globally.
The normal dossier generator needs only Python's standard library and the
recorded audit. This is not a manufacturing CAD validation.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from checks import HERE, evaluate, load
from geometry import parts


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solid_bounds(gmsh, volumes):
    # Imported STEP auxiliary points can remain outside transformed solids.
    # They are not assembly components and must not expand its bounds.
    boxes = [gmsh.model.getBoundingBox(dim, tag) for dim, tag in volumes]
    return [min(b[i] for b in boxes) for i in range(3)] + [max(b[i] for b in boxes) for i in range(3, 6)]


def main(gmsh_dir):
    if gmsh_dir:
        sys.path.insert(0, str(Path(gmsh_dir).resolve()))
    import gmsh
    cfg, components, v4, c02 = load()
    result = evaluate(cfg, components, v4, c02)
    target = HERE / "cad"
    target.mkdir(exist_ok=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("General.NumThreads", 2)
    sources = []
    try:
        for filename in ("PG5_fornitore.STEP", "WGA_fornitore.STEP"):
            gmsh.model.add(filename)
            path = HERE / "fonti" / filename
            before = sha(path)
            volumes = gmsh.model.occ.importShapes(str(path))
            gmsh.model.occ.synchronize()
            if not volumes or any(dim != 3 or gmsh.model.occ.getMass(dim, tag) <= 0 for dim, tag in volumes):
                raise ValueError(f"Missing/nonpositive volume in {filename}")
            sources.append({"file": filename, "sha256": before, "solid_count": len(volumes),
                            "bbox_mm_xyz_min_max": solid_bounds(gmsh, volumes),
                            "sum_geometric_volume_mm3_not_weight": sum(gmsh.model.occ.getMass(dim, tag) for dim, tag in volumes),
                            "import_succeeded": True, "tolerances_or_product_revision_validated": False})
            if sha(path) != before:
                raise ValueError("Source STEP changed")
            if filename.startswith("PG5"):
                gmsh.option.setNumber("Mesh.MeshSizeMin", 0.8)
                gmsh.option.setNumber("Mesh.MeshSizeMax", 4)
                gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
                gmsh.model.mesh.generate(2)
                tags, coords, _ = gmsh.model.mesh.getNodes()
                nodes = {int(tag): [round(float(c), 5) for c in coords[3 * i:3 * i + 3]] for i, tag in enumerate(tags)}
                types, _, connectivity = gmsh.model.mesh.getElements(2)
                triangles = []
                for element_type, conn in zip(types, connectivity):
                    if element_type != 2:
                        raise ValueError("Expected first-order triangles")
                    for i in range(0, len(conn), 3):
                        triangles.append([nodes[int(tag)] for tag in conn[i:i + 3]])
                (target / "PG5_mesh_preview.json").write_text(json.dumps({"source_sha256": before, "units": "mm", "raw_supplier_coordinates": True,
                                                                         "preview_only": True, "triangles": triangles}, separators=(",", ":")) + "\n", encoding="utf-8")
        gmsh.model.add("C03_modulo_freddo_NON_ESECUTIVO")
        imported = gmsh.model.occ.importShapes(str(HERE / "fonti/PG5_fornitore.STEP"))
        mx, my = result["packaging"]["modules"][0]["motor_centre_xy_mm"]
        # TDS reconciliation: output face in supplier STEP at z=-27.3,
        # shaft points toward -Z. Turn 180 degrees around X, then translate.
        offset = cfg["motor_output_face_z_mm"] - 27.3
        gmsh.model.occ.rotate(imported, 0, 0, 0, 1, 0, 0, math.pi)
        gmsh.model.occ.translate(imported, mx, my, offset)
        labels = {tag: "P01_STEP_fornitore" for dim, tag in imported}
        for part in parts(cfg, result):
            if part["shape"] == "box":
                a, b, c, d, e, f = part["bounds"]
                tag = gmsh.model.occ.addBox(a, c, e, b - a, d - c, f - e)
                radius = part.get("hole_radius_mm")
                if radius:
                    hx, hy = part["hole_xy"]
                    hole = gmsh.model.occ.addCylinder(hx, hy, e - 1, 0, 0, f - e + 2, radius)
                    cut, _ = gmsh.model.occ.cut([(3, tag)], [(3, hole)])
                    if len(cut) != 1:
                        raise ValueError("Unexpected box cut")
                    tag = cut[0][1]
            else:
                x, y = part["xy"]
                z0, z1 = part["z"]
                tag = gmsh.model.occ.addCylinder(x, y, z0, 0, 0, z1 - z0, part["outer_radius_mm"])
                inner = part["inner_radius_mm"]
                if inner:
                    hole = gmsh.model.occ.addCylinder(x, y, z0 - 1, 0, 0, z1 - z0 + 2, inner)
                    cut, _ = gmsh.model.occ.cut([(3, tag)], [(3, hole)])
                    if len(cut) != 1:
                        raise ValueError("Unexpected ring cut")
                    tag = cut[0][1]
            labels[tag] = part["name"]
        gmsh.model.occ.synchronize()
        for tag, label in labels.items():
            gmsh.model.setEntityName(3, tag, label)
        bbox = {tag: gmsh.model.getBoundingBox(3, tag) for tag in labels}
        intersections, checked = [], 0
        keys = list(labels)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                aa, bb = bbox[a], bbox[b]
                if any(min(aa[j + 3], bb[j + 3]) < max(aa[j], bb[j]) for j in range(3)):
                    continue
                checked += 1
                copies = gmsh.model.occ.copy([(3, a), (3, b)])
                common, _ = gmsh.model.occ.intersect(copies[:1], copies[1:])
                volume = sum(gmsh.model.occ.getMass(dim, tag) for dim, tag in common if dim == 3)
                if volume > 1e-3:
                    intersections.append({"parts": [labels[a], labels[b]], "overlap_mm3": volume})
                if common:
                    gmsh.model.occ.remove(common, recursive=True)
        gmsh.model.occ.synchronize()
        final_volumes = gmsh.model.getEntities(3)
        if {tag for dim, tag in final_volumes} != set(labels):
            raise ValueError("Unexpected audit topology change")
        step_path = target / "modulo_freddo_C03_NON_ESECUTIVO.step"
        gmsh.write(str(step_path))
        assembly_box = solid_bounds(gmsh, final_volumes)
        gmsh.model.add("roundtrip")
        roundtrip = gmsh.model.occ.importShapes(str(step_path))
        gmsh.model.occ.synchronize()
        roundtrip_box = solid_bounds(gmsh, roundtrip)
        if len(roundtrip) != len(labels) or max(abs(a - b) for a, b in zip(assembly_box, roundtrip_box)) > 0.02:
            raise ValueError(f"STEP roundtrip count {len(roundtrip)} vs {len(labels)}; bbox {roundtrip_box} vs {assembly_box}")
        record = {"study_id": "C03", "engine": f"Gmsh {gmsh.__version__}, OpenCASCADE backend", "units": "mm", "production_approved": False,
                  "supplier_sources": sources, "layout_sha256": sha(HERE / "layout.json"), "componenti_sha256": sha(HERE / "componenti.json"),
                  "geometry_py_sha256": sha(HERE / "geometry.py"), "checks_py_sha256": sha(HERE / "checks.py"),
                  "motor_transformation": {"rotation_X_deg": 180, "translation_xyz_mm": [mx, my, offset], "supplier_output_face_z_mm": -27.3},
                  "envelope_part_labels": labels, "solid_count": len(labels), "bbox_mm_xyz_min_max": assembly_box,
                  "positive_volume_overlap_pairs": intersections, "boolean_pairs_checked_after_AABB_filter": checked,
                  "positive_overlap_reporting_threshold_mm3": 0.001,
                  "audit_cad_py_sha256": sha(Path(__file__).resolve()),
                  "roundtrip_solid_count": len(roundtrip), "roundtrip_bbox_mm_xyz_min_max": roundtrip_box,
                  "artefacts_sha256": {step_path.name: sha(step_path), "PG5_mesh_preview.json": sha(target / "PG5_mesh_preview.json")},
                  "excluded_from_collision_check": ["belt solid/teeth and elastic deflection", "coupling and hot carrier", "screws/clamps and detailed bearing seats", "seals and cable routing", "actual frame and rails", "service sweep against actual oven"],
                  "scope": "Positive-volume nominal overlap and STEP read-back only. One real supplier motor; every other solid is an ENVELOPE. Contact/zero clearance may be intentional. Not a fit, motion, stiffness, load, material, thermal or complete-assembly validation."}
        (target / "audit_CAD.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Supplier imports: {[row['solid_count'] for row in sources]}; mixed STEP: {len(labels)} solids")
        print(f"Positive-volume overlaps: {len(intersections)}; STEP read-back checked")
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gmsh-dir", help="Optional isolated directory containing gmsh.py and DLL")
    args = parser.parse_args()
    main(args.gmsh_dir)
