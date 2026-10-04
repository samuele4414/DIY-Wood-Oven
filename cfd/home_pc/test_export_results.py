"""Completed-result export tests; neither FDS nor the renderer is executed."""
import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import export_results


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.campaign = Path(self.temporary.name)
        manifest = {"schema": 1, "stages": {}}
        for stage in ("preheat", "bake"):
            run = self.campaign / stage
            run.mkdir()
            manifest["stages"][stage] = {"directory": stage, "input": stage + ".fds", "chid": "v4_" + stage, "duration_s": 120}
            (run / "run_status.json").write_text(json.dumps({"status": "completed"}))
            (run / ("v4_" + stage + ".out")).write_text(f"Total Time: 120.00000 s\nSTOP: FDS completed successfully (CHID: v4_{stage})\n")
        (self.campaign / "manifest.json").write_text(json.dumps(manifest))
        self.names = ["Time"]
        self.units = ["s"]
        for number in (1, 2):
            for point in export_results.POINTS:
                for quantity in ("rad", "conv", "net", "surface", "core", "bottom"):
                    self.names.append(f"pizza_{number}_{point}_{quantity}")
                    self.units.append("kW/m2" if quantity in ("rad", "conv", "net") else "C")
        self.rows = [[t] + [t if unit == "kW/m2" else 25 + i for i, unit in enumerate(self.units[1:])]
                     for t in (0, 30, 120)]
        for stage in ("preheat", "bake"):
            self.write_csv(stage)

    def write_csv(self, stage):
        with (self.campaign / stage / f"v4_{stage}_devc.csv").open("w", newline="") as stream:
            csv.writer(stream).writerows([self.units, self.names] + self.rows)

    def test_bake_uses_actual_timestamps_and_exports_without_process(self):
        with patch.object(export_results, "export_volumes") as export, patch.object(export_results.subprocess, "run") as run:
            with contextlib.redirect_stdout(io.StringIO()):
                path = export_results.export_stage(self.campaign)
        report = json.loads(path.read_text())
        point = report["pizzas"][0]["points"]["C"]
        self.assertEqual(point["time_mean_heat_flux_kW_m2"]["rad"], 60)
        self.assertEqual(point["net_heat_flux_time_integral_kJ_m2"], 7200)
        self.assertEqual(len(report["pizzas"][1]["points"]), 5)
        self.assertEqual(export.call_args.kwargs["step"], .5)
        run.assert_not_called()

    def test_video_only_invokes_python_renderer(self):
        with patch.object(export_results, "export_volumes"), patch.object(export_results.subprocess, "run") as run:
            with contextlib.redirect_stdout(io.StringIO()):
                export_results.export_stage(self.campaign, video=True)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[1]).name, "render_video.py")
        self.assertIn("--data", command)
        self.assertIn("--output", command)
        self.assertTrue(run.call_args.kwargs["check"])

    def test_incomplete_stage_blocks_export_and_video(self):
        (self.campaign / "bake" / "run_status.json").write_text('{"status":"running"}')
        with patch.object(export_results, "export_volumes") as export, patch.object(export_results.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "Only completed"):
                export_results.export_stage(self.campaign, video=True)
        export.assert_not_called()
        run.assert_not_called()

    def test_preheat_has_final_probes_only(self):
        with patch.object(export_results, "export_volumes") as export:
            with contextlib.redirect_stdout(io.StringIO()):
                path = export_results.export_stage(self.campaign, "preheat")
        report = json.loads(path.read_text())
        self.assertIn("final_probes", report)
        self.assertNotIn("pizzas", report)
        self.assertEqual(export.call_args.kwargs["step"], 30)

    def test_missing_probe_rejected_before_volume_export(self):
        self.names[-1] = "unknown"
        self.write_csv("bake")
        with patch.object(export_results, "export_volumes") as export:
            with self.assertRaisesRegex(ValueError, "Missing pizza"):
                export_results.export_stage(self.campaign)
        export.assert_not_called()

    def test_bad_time_coverage_rejected(self):
        self.rows[-1][0] = 90
        self.write_csv("bake")
        with self.assertRaisesRegex(ValueError, "complete requested stage"):
            export_results.read_probes(self.campaign / "bake" / "v4_bake_devc.csv", 120)


if __name__ == "__main__":
    unittest.main()
