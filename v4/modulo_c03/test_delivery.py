import csv
import io
import json
import math
import unittest
import xml.etree.ElementTree as ET

from build_study import audited_cad, candidate_csv, fill, planned_register, sha, values
from checks import HERE, evaluate, load
from drawings import all_drawings
from geometry import mesh, parts


class DossierConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.components, cls.v4, cls.c02 = load()
        cls.result = evaluate(cls.cfg, cls.components, cls.v4, cls.c02)

    def test_false_approval_flags(self):
        for data in (self.cfg, self.components, self.result):
            self.assertFalse(data["production_approved"])
        self.assertFalse(self.result["physical_tests_executed"])
        self.assertFalse(self.result["hot_integration_validated"])

    def test_source_acquisition_complete_and_hashes(self):
        record = json.loads((HERE / "fonti/acquisizione.json").read_text(encoding="utf-8"))
        self.assertEqual(record["errors"], [])
        self.assertEqual(len(record["files"]), 18)
        for row in record["files"]:
            path = HERE / "fonti" / row["file"]
            self.assertEqual(path.stat().st_size, row["bytes"])
            self.assertEqual(sha(path), row["sha256"])

    def test_cad_current_and_limited(self):
        audit = audited_cad()
        self.assertEqual(audit["solid_count"], 21)
        self.assertEqual(audit["roundtrip_solid_count"], 21)
        self.assertEqual(audit["positive_volume_overlap_pairs"], [])
        self.assertGreaterEqual(len(audit["excluded_from_collision_check"]), 6)
        self.assertFalse(audit["production_approved"])

    def test_cad_bbox_matches_budget(self):
        box = audited_cad()["bbox_mm_xyz_min_max"]
        expected = [90, 115, -221, 330, 295, -85]
        for a, b in zip(box, expected):
            self.assertAlmostEqual(a, b, places=5)

    def test_vendor_STEPS_are_not_envelope_STEP(self):
        self.assertNotEqual(sha(HERE / "fonti/PG5_fornitore.STEP"), sha(HERE / "cad/modulo_freddo_C03_NON_ESECUTIVO.step"))

    def test_torque_discrepancy_not_erased(self):
        self.assertEqual(self.result["drive"]["catalogue_torque_conflict_Nm"], [2, 3])

    def test_pulley_original_bores_not_proposed_finished_bores(self):
        facts = {r["id"]: r["facts"] for r in self.components["items"]}
        self.assertIsNone(facts["P04A"]["pilot_bore_mm"])
        self.assertEqual(facts["P04B"]["pilot_bore_mm"], 8)
        self.assertEqual(self.result["packaging"]["motor_shaft_pulley_bore_overlap_min_mm"], 16)

    def test_bearing_not_assumed_greased(self):
        row = next(r for r in self.components["items"] if r["id"] == "P03")
        self.assertEqual(row["facts"]["lubricant_supplied"], "none")
        self.assertFalse(row["facts"]["matched_pair_supplied"])

    def test_part_envelopes_finite(self):
        for face in mesh(parts(self.cfg, self.result)):
            self.assertGreaterEqual(len(face["points"]), 3)
            self.assertTrue(all(math.isfinite(c) for p in face["points"] for c in p))

    def test_drawings_parse_and_warning(self):
        drawings = all_drawings(self.cfg, self.v4, self.result)
        self.assertEqual(len(drawings), 3)
        for source in drawings.values():
            ET.fromstring(source)
            self.assertIn("NON ESECUTIVO", source)

    def test_document_tokens_resolve(self):
        vals = values(self.result, self.components, 0)
        vals.update({"VIEWER": "", "PLAN": "", "MODULE": "", "SERVICE": ""})
        for filename in ("report.template.md", "sheet.template.html"):
            result = fill((HERE / filename).read_text(encoding="utf-8"), vals)
            self.assertNotIn("@@", result)

    def test_unknown_token_fails(self):
        with self.assertRaises(ValueError):
            fill("@@UNKNOWN@@", {})

    def test_print_not_overridden_by_mobile_layout(self):
        text = (HERE / "sheet.template.html").read_text(encoding="utf-8")
        self.assertIn("@media screen and (max-width:760px)", text)
        self.assertEqual(text.count('<section class="page'), 5)

    def test_registry_has_no_fake_measurements(self):
        rows = planned_register()
        self.assertEqual(len(rows), 10)
        for row in rows:
            self.assertEqual(row["stato"], "NON_ESEGUITA")
            for key, value in row.items():
                if key not in ("id", "prova_pianificata", "stato"):
                    self.assertEqual(value, "")

    def test_candidate_csv_includes_missing_groups(self):
        rows = list(csv.DictReader(io.StringIO(candidate_csv(self.components)), delimiter=";"))
        self.assertEqual(len(rows), 14)
        self.assertEqual(sum(r["stato"] == "MANCANTE_NON_ORDINABILE" for r in rows), 6)
        self.assertTrue(all(r["produzione_approvata"] == "False" for r in rows))

    def test_driver_not_connected_directly_to_motor(self):
        text = (HERE / "report.template.md").read_text(encoding="utf-8")
        self.assertIn("non vanno alimentate direttamente", text)
        self.assertIn("non è qui approvata", text)


if __name__ == "__main__":
    unittest.main()
