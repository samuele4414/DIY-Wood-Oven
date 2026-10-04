"""Core regressions without starting FDS.

Run: python -m unittest discover -s cfd -p test_core.py -v
All generated inputs and binary fixtures live in temporary directories.
The geometry tests reconstruct the emitted meshes/obstructions, independently
of the writer's internal void sets or its connectivity metadata.
"""

from __future__ import annotations

import copy
import csv
import json
import math
import re
import struct
import tempfile
import unittest
from collections import deque
from pathlib import Path

import numpy as np

from check_geometry import nominal_check
from fds_writer import write_case
from postprocess import read_slice, read_smv, summarize_run, time_mean
from run_study import load_cases, variant


def blocks(text, kind):
    return re.findall(r"&" + kind + r"\b(.*?)/", text, re.I | re.S)


def vector(block, name, count):
    number = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[Ee][-+]?\d+)?"
    match = re.search(r"\b" + name + r"\s*=\s*(" + number + r"(?:\s*,\s*" + number + r"){" + str(count - 1) + r"})", block, re.I)
    if not match:
        raise AssertionError(f"Missing {name} in emitted input")
    return np.asarray([float(x) for x in match[1].split(",")])


def tagged(block, name, value):
    return bool(re.search(r"\b" + name + r"\s*=\s*['\"]" + re.escape(value) + r"['\"]", block, re.I))


def fixture_slice(path, endian="<", unfinished=False):
    """Build records from the published Fortran loop, not NumPy reshaping."""
    def record(payload):
        length = struct.pack(endian + "i", len(payload))
        return length + payload + length
    data = b"".join(record(label.encode().ljust(30)) for label in ("TEMPERATURE", "temp", "C"))
    data += record(struct.pack(endian + "6i", 2, 4, 5, 6, 7, 7))
    for time in (0, 3, 10):
        values = [100 * k + 10 * j + i + time
                  for k in range(7, 8) for j in range(5, 7) for i in range(2, 5)]
        data += record(struct.pack(endian + "f", time))
        data += record(struct.pack(endian + "6f", *values))
    if unfinished:
        data += struct.pack(endian + "i", 4) + b"\0\0"
    Path(path).write_bytes(data)


def emitted_lattice(text):
    """Reconstruct a conformal Cartesian lattice from MESH and OBST lines."""
    meshes = [(vector(b, "IJK", 3).astype(int), vector(b, "XB", 6)) for b in blocks(text, "MESH")]
    spacing = (meshes[0][1][1::2] - meshes[0][1][::2]) / meshes[0][0]
    for counts, bounds in meshes:
        np.testing.assert_allclose((bounds[1::2] - bounds[::2]) / counts, spacing, rtol=0, atol=1e-8)
    origin = np.min([bounds[::2] for _, bounds in meshes], axis=0)
    stop = np.max([bounds[1::2] for _, bounds in meshes], axis=0)
    shape = np.rint((stop - origin) / spacing).astype(int)
    domain = np.zeros(tuple(shape), dtype=bool)
    solid = np.zeros_like(domain)

    def index_box(bounds):
        raw = (bounds.reshape(3, 2) - origin[:, None]) / spacing[:, None]
        np.testing.assert_allclose(raw, np.rint(raw), rtol=0, atol=1e-7)
        index = np.rint(raw).astype(int)
        return tuple(slice(max(0, a), min(int(n), b)) for (a, b), n in zip(index, shape))

    for _, bounds in meshes:
        domain[index_box(bounds)] = True
    for block in blocks(text, "OBST"):
        solid[index_box(vector(block, "XB", 6))] = True
    axes = [origin[i] + (np.arange(shape[i]) + .5) * spacing[i] for i in range(3)]
    return domain & ~solid, axes, meshes, solid


def flood(free, seed):
    """Six-neighbour connectivity on parsed cells, with no geometry assumptions."""
    visited = np.zeros_like(free)
    seed = tuple(seed)
    if not free[seed]:
        raise AssertionError(f"Seed {seed} is not a gas cell")
    visited[seed] = True
    queue = deque([seed])
    while queue:
        point = queue.popleft()
        for axis in range(3):
            for step in (-1, 1):
                adjacent = list(point)
                adjacent[axis] += step
                if not 0 <= adjacent[axis] < free.shape[axis]:
                    continue
                adjacent = tuple(adjacent)
                if free[adjacent] and not visited[adjacent]:
                    visited[adjacent] = True
                    queue.append(adjacent)
    return visited


class BinaryAndTimeTests(unittest.TestCase):
    def test_fortran_record_order_both_endians_and_partial_tail(self):
        with tempfile.TemporaryDirectory() as folder:
            for endian in ("<", ">"):
                path = Path(folder) / "native.sf"
                fixture_slice(path, endian=endian, unfinished=True)
                result = read_slice(path)
                self.assertEqual(result["bounds"], (2, 4, 5, 6, 7, 7))
                self.assertEqual(result["values"].shape, (3, 3, 2, 1))
                self.assertEqual(result["values"][0, 0, 0, 0], 752)
                self.assertEqual(result["values"][1, 2, 1, 0], 767)
                self.assertEqual(result["values"][2, 1, 0, 0], 763)
                self.assertTrue(result["truncated"])

    def test_mismatched_fortran_record_marker_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "broken.sf"
            fixture_slice(path)
            content = bytearray(path.read_bytes())
            content[34:38] = struct.pack("<i", 29)  # First label's trailing marker.
            path.write_bytes(content)
            with self.assertRaisesRegex(ValueError, "markers disagree"):
                read_slice(path)

    def test_time_mean_integrates_irregular_samples_and_clips_support(self):
        times = np.array([0., 2., 10.])
        values = np.array([0., 4., 4.])
        average, interval, _ = time_mean(times, values, 0, 10)
        self.assertAlmostEqual(float(average), 3.6)
        average, interval, _ = time_mean(times, values, 1, 5)
        self.assertAlmostEqual(float(average), 3.75)
        average, interval, _ = time_mean(times, values, -5, 15)
        self.assertEqual(interval, [0, 10])
        self.assertAlmostEqual(float(average), 3.6)
        average, _, _ = time_mean(np.array([0., 2., 2., 10.]), np.array([0., 99., 4., 4.]), 0, 10)
        self.assertAlmostEqual(float(average), 3.6)

    def test_smv_preserves_nonuniform_coordinates_and_mesh_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            lines = []
            grids = [([-0.1, 0, .15], [0, .2], [0, .1, .3]),
                     ([0, .1], [0, .2], [.3, .5])]
            for number, coordinates in enumerate(grids, 1):
                lines += [f"GRID MESH0{number}", " ".join(str(len(axis) - 1) for axis in coordinates)]
                for name, axis in zip("XYZ", coordinates):
                    lines += ["TRN" + name, "1", "0 0 0"]
                    lines += [f"{i} {value}" for i, value in enumerate(axis)]
            lines += ["SLCF 1 # STRUCTURED & 0 2 0 1 1 1 ! 1 0 3",
                      "case_1_1.sf", "TEMPERATURE", "temp", "C"]
            path = Path(folder) / "case.smv"
            path.write_text("\n".join(lines))
            result = read_smv(path)
            np.testing.assert_allclose(result["meshes"][1]["x"], [-.1, 0, .15])
            np.testing.assert_allclose(result["meshes"][2]["z"], [.3, .5])
            self.assertEqual(result["slices"][0]["mesh"], 1)


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.case = {"id": "case", "pizza_centers": []}
        (self.folder / "case.fds").write_text("&TIME T_END=30 /")
        self.log("Total Time: 30.0 s\nSTOP: FDS completed successfully\n")

    def log(self, text):
        (self.folder / "case.out").write_text(text)

    def devices(self, soot=True, soot_values=(-1e-5, 3e-5)):
        labels = ["Time", "mouth_outward_y_negative", "mouth_inward_y_positive",
                  "flue_outward_z_positive"]
        values = [-.2, .1, .3]
        if soot:
            labels += ["mouth_soot_outward_negative", "flue_soot_outward_positive"]
            values += list(soot_values)
        with (self.folder / "case_devc.csv").open("w", newline="") as stream:
            writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
            writer.writerow(["s"] + ["kg/s"] * (len(labels) - 1))
            writer.writerow(labels)
            for time in (0, 10, 20, 30):
                writer.writerow([time] + values)

    def test_global_axis_signs_and_soot_share_are_explicit(self):
        self.devices()
        result = summarize_run(self.case, self.folder, {})
        self.assertEqual(result["status"], "completed")
        self.assertAlmostEqual(result["metrics"]["mouth_out_kg_s"], .2)
        self.assertAlmostEqual(result["metrics"]["mouth_in_kg_s"], .1)
        self.assertAlmostEqual(result["metrics"]["flue_out_kg_s"], .3)
        self.assertAlmostEqual(result["metrics"]["mouth_soot_out_kg_s"], 1e-5)
        self.assertAlmostEqual(result["metrics"]["soot_flue_fraction_of_measured_exits"], .75)
        self.assertEqual(result["soot_exit_proxy"]["mean_window_s"], [20, 30])
        self.assertIn("Not a fraction of generated soot", result["soot_exit_proxy"]["interpretation"])
        json.dumps(result, allow_nan=False)

    def test_no_soot_share_for_missing_or_zero_measurements(self):
        for kwargs in ({"soot": False}, {"soot_values": (0, 0)}):
            self.devices(**kwargs)
            result = summarize_run(self.case, self.folder, {})
            self.assertNotIn("soot_flue_fraction_of_measured_exits", result["metrics"])

    def test_completion_requires_last_normal_terminal_and_requested_end(self):
        scenarios = [
            ("Total Time: 29.9 s\nSTOP: FDS completed successfully\n", "incomplete"),
            ("Total Time: 30 s\nSTOP: FDS was stopped by KILL control function and completed successfully\n", "incomplete"),
            ("Total Time: 30 s\nSTOP: FDS completed successfully\nSTOP: FDS stopped by user\n", "incomplete"),
            ("Total Time: 30 s\n", "incomplete"),
            ("Total Time: 30 s\nSTOP: FDS completed successfully (CHID: case)\n", "completed"),
        ]
        for log, expected in scenarios:
            with self.subTest(log=log):
                self.log(log)
                self.assertEqual(summarize_run(self.case, self.folder, {})["status"], expected)

    def test_hrr_trace_and_adjacent_windows_are_measurements_not_pass_labels(self):
        (self.folder / "case_hrr.csv").write_text(
            '"s","kW"\n"Time","HRR"\n0,0\n10,10\n20,20\n25,30\n30,40\n')
        metadata = {"resolved": {"hrr_kw_gross_prescribed": 18.75}}
        result = summarize_run(self.case, self.folder, metadata)
        self.assertEqual(result["traces"]["hrr_kw_mean"]["values"], [0, 10, 20, 30, 40])
        comparison = result["window_comparison"]["hrr_kw_mean"]
        self.assertAlmostEqual(comparison["previous_mean"], 25)
        self.assertAlmostEqual(comparison["recent_mean"], 35)
        self.assertAlmostEqual(comparison["delta"], 10)
        self.assertNotIn("passed", comparison)
        self.assertTrue(result["hrr_comparison"]["deviation_above_10_percent"])


class PhysicalInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.case = variant(load_cases()[0], "front")
        cls.folder = Path(cls.temp.name)
        cls.metadata = write_case(cls.case, cls.folder, cell_size=.05, duration=30, hrr_kw=18.75)
        cls.text = (cls.folder / f"{cls.case['id']}.fds").read_text()

    def test_all_six_layouts_fit_declared_items_without_nominal_collisions(self):
        cases = load_cases()
        self.assertEqual(len(cases), 6)
        self.assertEqual([len(case["pizza_centers"]) for case in cases], [2, 3, 3, 3, 3, 2])
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(case["pizza_diameter"], .30)
                self.assertEqual(case["disc_diameter"], .32)
                result = nominal_check(case)
                for key in ("minimum_wall_gap_cm", "minimum_fire_zone_gap_cm", "minimum_inter_item_gap_cm"):
                    self.assertGreaterEqual(result[key], 0)
        overlapping = copy.deepcopy(cases[0])
        overlapping["pizza_centers"][1] = overlapping["pizza_centers"][0][:]
        with self.assertRaisesRegex(ValueError, "collision"):
            nominal_check(overlapping)

    def test_emitted_burner_has_18_75_kw_physical_power(self):
        burner = next(b for b in blocks(self.text, "SURF") if tagged(b, "ID", "BURNER"))
        fire = next(b for b in blocks(self.text, "VENT") if tagged(b, "ID", "FIRE"))
        bounds = vector(fire, "XB", 6)
        area = (bounds[1] - bounds[0]) * (bounds[3] - bounds[2])
        hrrpua = vector(burner, "HRRPUA", 1)[0]
        expected_kw = 4.5 / 3600 * 15e6 / 1000
        self.assertAlmostEqual(expected_kw, 18.75)
        self.assertAlmostEqual(hrrpua * area, expected_kw, places=5)
        self.assertEqual(bounds[4], 0)
        self.assertEqual(bounds[5], 0)

    def test_parsed_staircase_connects_chamber_mouth_and_flue(self):
        free, axes, meshes, solid = emitted_lattice(self.text)
        index = lambda xyz: tuple(int(np.argmin(abs(axis - value))) for axis, value in zip(axes, xyz))
        seed = index([.395, .25, .10])
        # Seal the exterior mouth route: the upper target must be reached
        # through the oven's actual flue, not by going around the outside.
        flue_free = free.copy()
        flue_free[:, axes[1] < 0, :] = False
        reached = flood(flue_free, seed)
        cx, cy = self.case["chimney"]["center"]
        outlet = self.case["chimney"]["outlet_height_m"]
        self.assertTrue(reached[index([cx, cy, outlet + .075])], "Flue outlet is capped/disconnected")
        self.assertTrue(reached[index([cx, cy, meshes[1][1][4] + .025])], "Mesh interface blocks the bore")
        # Close the higher escape path so this reachability requires an
        # opening below the mouth lintel rather than an external flue detour.
        mouth_free = free.copy()
        mouth_free[:, :, axes[2] >= self.case["mouth_height"]] = False
        reached = flood(mouth_free, seed)
        self.assertTrue(reached[index([.395, -.15, .075])], "Staircase mouth is capped")
        fire = next(b for b in blocks(self.text, "VENT") if tagged(b, "ID", "FIRE"))
        bounds = vector(fire, "XB", 6)
        center = [(bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2]
        self.assertTrue(solid[index([*center, -.025])], "Burner has no supporting floor")
        self.assertTrue(free[index([*center, .025])], "Burner faces a solid cell")

    def test_uncovered_lower_mesh_top_is_open_but_interface_is_coupled(self):
        mesh = [vector(b, "XB", 6) for b in blocks(self.text, "MESH")]
        lower, upper = mesh
        split = lower[5]
        self.assertAlmostEqual(split, upper[4])
        counts = vector(blocks(self.text, "MESH")[0], "IJK", 3).astype(int)
        x = lower[0] + (np.arange(counts[0]) + .5) * (lower[1] - lower[0]) / counts[0]
        y = lower[2] + (np.arange(counts[1]) + .5) * (lower[3] - lower[2]) / counts[1]
        xx, yy = np.meshgrid(x, y, indexing="ij")
        interface = (xx > upper[0]) & (xx < upper[1]) & (yy > upper[2]) & (yy < upper[3])
        open_top = np.zeros_like(interface)
        for vent in blocks(self.text, "VENT"):
            if not tagged(vent, "SURF_ID", "OPEN"):
                continue
            bounds = vector(vent, "XB", 6)
            if np.allclose(bounds[4:], [split, split]):
                open_top |= (xx > bounds[0]) & (xx < bounds[1]) & (yy > bounds[2]) & (yy < bounds[3])
        self.assertTrue(np.all(open_top[~interface]), "Uncoupled mesh-top cells become unintended solid ceiling")
        self.assertFalse(np.any(open_top[interface]), "OPEN must not replace mesh coupling")


if __name__ == "__main__":
    unittest.main()
