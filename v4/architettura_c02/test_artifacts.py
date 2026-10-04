"""Delivery checks: deterministic data, resolved templates and valid SVG/XML."""
import csv
from html.parser import HTMLParser
import io
import json
import re
import unittest
import xml.etree.ElementTree as ET

from build_study import (HERE, fill, json_text, markdown_html, preliminary_parts_csv,
                         pressure_csv, report_values, sheet_html)
from checks import evaluate, load
from drawings import all_drawings, octagon


class DeliveryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.v4,cls.c01=load()
        cls.results=evaluate(cls.cfg,cls.v4,cls.c01)
        cls.materials=json.loads((HERE/"materiali_candidati.json").read_text(encoding="utf-8"))
        cls.drawings=all_drawings(cls.cfg,cls.v4,cls.results)

    def test_four_svg_schemes_are_well_formed_and_labelled(self):
        self.assertEqual(len(self.drawings),4)
        for name,text in self.drawings.items():
            root=ET.fromstring(text)
            self.assertTrue(root.tag.endswith("svg"),name)
            self.assertEqual(root.attrib["viewBox"],"0 0 1400 950")
            self.assertIn("NON ESECUTIVO",text)
            self.assertNotRegex(text,r"\b(?:nan|inf)\b")

    def test_marker_ids_unique_when_embedded_on_one_HTML_page(self):
        identifiers=[]
        for text in self.drawings.values():
            root=ET.fromstring(text)
            identifiers.extend(e.attrib["id"] for e in root.iter() if "id" in e.attrib)
        self.assertEqual(len(set(identifiers)),len(identifiers))

    def test_references_to_SVG_markers_exist(self):
        for text in self.drawings.values():
            root=ET.fromstring(text)
            ids={e.attrib["id"] for e in root.iter() if "id" in e.attrib}
            for marker in re.findall(r"url\(#([^)]+)\)",text):
                self.assertIn(marker,ids)

    def test_report_has_no_unfilled_placeholders_including_digits(self):
        report=fill((HERE/"report.template.md").read_text(encoding="utf-8"),report_values(self.results,self.materials,0))
        self.assertNotIn("@@",report)
        self.assertIn("670",json_text(self.results))
        self.assertIn("671",report)
        self.assertIn("415,8",report)
        with self.assertRaises(ValueError):
            fill("@@UNKNOWN_120@@",{})

    def test_print_and_preview_have_six_sections_and_no_remote_assets(self):
        text=sheet_html(self.results,self.materials,0,self.drawings)
        self.assertNotIn("@@",text)
        self.assertEqual(text.count('<section class="page'),6)
        self.assertNotRegex(text,r'(?:src=|@import|url\()["\']?https?://')
        self.assertNotIn("<script",text)
        HTMLParser().feed(text)

    def test_csv_includes_every_scenario_and_closed_door_budget(self):
        rows=list(csv.DictReader(io.StringIO(pressure_csv(self.results)),delimiter=";"))
        self.assertEqual(len(rows),len(self.results["pressure_scenarios"]))
        self.assertEqual(len(set(r["id"] for r in rows)),len(rows))
        preferred=next(r for r in rows if r["id"]=="C02_PUNTO_DI_CONFRONTO")
        self.assertGreater(float(preferred["budget_margin_Pa"]),0)
        opened=next(r for r in rows if r["id"]=="C02_PORTA_APERTA")
        self.assertEqual(opened["budget_margin_Pa"],"")
        self.assertGreater(float(opened["door_out_gas_kg_h"]),0)

    def test_archived_manufacturer_sources_exist(self):
        source_ids={s["id"] for s in self.materials["sources"]}
        for source in self.materials["sources"]:
            path=HERE/source["archive"]
            self.assertTrue(path.is_file(),str(path))
            if path.suffix==".pdf":
                self.assertTrue(path.read_bytes().startswith(b"%PDF"))
        for item in self.materials["items"]:
            if item["source_id"]:
                self.assertIn(item["source_id"],source_ids)

    def test_preliminary_parts_list_is_not_an_order_list(self):
        rows = list(csv.DictReader(io.StringIO(preliminary_parts_csv(self.materials)), delimiter=";"))
        self.assertEqual(len(rows), len(self.materials["items"]))
        self.assertEqual({row["id"] for row in rows}, {item["id"] for item in self.materials["items"]})
        for row in rows:
            self.assertTrue(row["quantita_di_studio"])
            self.assertFalse(row["codice_commerciale_selezionato"])
            self.assertEqual(row["produzione_approvata"], "False")
            self.assertEqual(row["stato"], "da_qualificare_non_ordinabile")

    def test_drawn_octagon_has_declared_across_flats_and_orientation(self):
        vertices = octagon(0, 0, 440)
        self.assertAlmostEqual(max(x for x, y in vertices), 220)
        self.assertAlmostEqual(min(x for x, y in vertices), -220)
        self.assertAlmostEqual(max(y for x, y in vertices), 220)
        self.assertAlmostEqual(min(y for x, y in vertices), -220)
        # A 260 x 328 bounding rectangle fails the 340 octagon's diagonal
        # face but lies inside the reserved 440 octagon.
        import math
        corner_projection = (130 + 164) / math.sqrt(2)
        self.assertGreater(corner_projection, 340 / 2)
        self.assertLess(corner_projection, 440 / 2)

    def test_only_documented_mean_steel_coefficient_is_used(self):
        table=self.materials["documented_material_curves"]["310S_mean_expansion_20_to_T_per_K"]
        value=next(v for t,v in table if t==600)
        self.assertEqual(self.cfg["mechanical"]["steel_mean_alpha_20_600_per_K"],value)

    def test_pure_calculation_and_drawings_are_deterministic(self):
        again=evaluate(self.cfg,self.v4,self.c01)
        self.assertEqual(json_text(self.results),json_text(again))
        self.assertEqual(self.drawings,all_drawings(self.cfg,self.v4,again))

    def test_dossier_renderer_escapes_raw_HTML(self):
        text=markdown_html("# Test\n\n<script>bad()</script>\n", "Title")
        self.assertNotIn("<script>",text)
        self.assertIn("&lt;script&gt;",text)


if __name__=="__main__":
    unittest.main()
