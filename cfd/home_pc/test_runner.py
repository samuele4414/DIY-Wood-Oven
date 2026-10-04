"""Runner contract tests: FDS is always mocked and never executed."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_home


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.campaign = Path(self.temporary.name)
        self.manifest = {"schema": 1, "config_sha256": "example", "stages": {}}
        for name, duration in (("preheat", 3600), ("bake", 120)):
            directory = self.campaign / name
            directory.mkdir()
            (directory / f"{name}.fds").write_text(f"&HEAD CHID='v4_{name}' /\n")
            self.manifest["stages"][name] = {"directory": name, "input": f"{name}.fds",
                                              "chid": f"v4_{name}", "duration_s": duration}
        (self.campaign / "manifest.json").write_text(json.dumps(self.manifest))
        self.solver = self.campaign / "fds_openmp.exe"
        self.solver.write_text("Not an executable; tests mock process creation.")

    def output(self, name="preheat", time=3600, stop="FDS completed successfully (CHID: v4_preheat)"):
        path = self.campaign / name / f"v4_{name}.out"
        path.write_text(f"Step Size: 0.01 s, Total Time: {time:.5f} s\nSTOP: {stop}\n")

    def test_dry_run_never_invokes_commands_or_changes_files(self):
        before = {str(p): p.read_bytes() for p in self.campaign.rglob("*") if p.is_file()}
        with patch.object(run_home.subprocess, "Popen") as popen, patch.object(run_home.subprocess, "run") as run:
            with contextlib.redirect_stdout(io.StringIO()):
                result = run_home.main(["--campaign", str(self.campaign), "--fds", "missing.exe"])
        self.assertEqual(result, 0)
        popen.assert_not_called()
        run.assert_not_called()
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.campaign.rglob("*") if p.is_file()})

    def test_completion_requires_time_normal_stop_and_correct_chid(self):
        self.output(time=90)
        self.assertFalse(run_home.output_progress(self.campaign / "preheat", "v4_preheat", 3600)["reached_end"])
        self.output(stop="FDS stopped by user (CHID: v4_preheat)")
        self.assertFalse(run_home.output_progress(self.campaign / "preheat", "v4_preheat", 3600)["reached_end"])
        self.output(stop="FDS completed successfully (CHID: another_case)")
        self.assertFalse(run_home.output_progress(self.campaign / "preheat", "v4_preheat", 3600)["reached_end"])
        self.output()
        self.assertTrue(run_home.output_progress(self.campaign / "preheat", "v4_preheat", 3600)["reached_end"])
        with (self.campaign / "preheat" / "v4_preheat.out").open("a") as stream:
            stream.write("STOP: Numerical instability\n")
        self.assertFalse(run_home.output_progress(self.campaign / "preheat", "v4_preheat", 3600)["reached_end"])

    def test_success_preserves_command_environment_and_hash(self):
        process = Mock(returncode=0)
        process.poll.return_value = 0

        def launch(*args, **kwargs):
            self.output()
            return process

        with patch.object(run_home.subprocess, "Popen", side_effect=launch) as popen:
            with contextlib.redirect_stdout(io.StringIO()):
                result = run_home.run_stage(self.campaign, self.manifest, "preheat", self.solver, 6)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["input_sha256"], run_home.input_hash(self.campaign / "preheat" / "preheat.fds"))
        self.assertEqual(popen.call_args.args[0], [str(self.solver), "preheat.fds"])
        self.assertEqual(popen.call_args.kwargs["env"]["OMP_NUM_THREADS"], "6")
        self.assertEqual(popen.call_args.kwargs["env"]["OMP_DYNAMIC"], "FALSE")
        self.assertEqual(popen.call_args.kwargs["cwd"], self.campaign / "preheat")
        self.assertEqual(json.loads((self.campaign / "preheat" / "run_status.json").read_text())["status"], "completed")

    def test_zero_exit_without_complete_output_fails(self):
        process = Mock(returncode=0)
        process.poll.return_value = 0
        with patch.object(run_home.subprocess, "Popen", return_value=process):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "did not complete"):
                run_home.run_stage(self.campaign, self.manifest, "preheat", self.solver, 2)
        self.assertEqual(json.loads((self.campaign / "preheat" / "run_status.json").read_text())["status"], "failed")

    def test_refuses_previous_outputs_even_without_status(self):
        self.output()
        with patch.object(run_home.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "Refusing to overwrite"):
                run_home.run_stage(self.campaign, self.manifest, "preheat", self.solver, 2)
        popen.assert_not_called()

    def test_failed_preheat_transfer_blocks_bake(self):
        with patch.object(run_home.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "prepare-bake")) as run:
            with patch.object(run_home.subprocess, "Popen") as popen:
                with self.assertRaises(subprocess.CalledProcessError):
                    run_home.run_stage(self.campaign, self.manifest, "bake", self.solver, 2)
        popen.assert_not_called()
        self.assertIn("prepare-bake", run.call_args.args[0])
        self.assertTrue(run.call_args.kwargs["check"])

    def test_path_escape_is_rejected(self):
        self.manifest["stages"]["preheat"]["directory"] = "../outside"
        (self.campaign / "manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "inside the campaign"):
            run_home.load_campaign(self.campaign)

    def test_thread_count_must_be_positive(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            run_home.main(["--campaign", str(self.campaign), "--threads", "0"])

    def test_solver_uses_explicit_path_without_invocation(self):
        with patch.object(run_home.subprocess, "run") as run, patch.object(run_home.subprocess, "Popen") as popen:
            self.assertEqual(run_home.solver_path(str(self.solver)), self.solver.resolve())
        run.assert_not_called()
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
