"""Offline fixtures only: none of these tests invokes FDS."""
import csv
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import pipeline


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'campaign'
        self.block=patch('subprocess.Popen',side_effect=AssertionError('No process may run'))
        self.block.start()
        pipeline.prepare(self.root,pipeline.HERE/'campaign_config.json')
    def tearDown(self):self.block.stop();self.tmp.cleanup()

    def fixture_results(self,ready=True):
        pre=self.root/'preheat';config=pipeline.config_load(self.root/'campaign_config.json')
        probes=json.loads((pre/'probes.json').read_text());names=['Time']+[p['id'] for p in probes]+['gas_L','gas_R','gas_REAR','gas_FLUE']
        with (pre/'v4_preheat_devc.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['s']+['C']*(len(names)-1));w.writerow(names)
            for t in [0,3480,3600]:
                hot=500 if ready else 100
                w.writerow([t]+[25 if t==0 else hot]*(len(names)-1))
        (pre/'v4_preheat.out').write_text('Total Time: 3600.00000 s\nSTOP: FDS completed successfully (CHID: v4_preheat)\n')
        manifest=json.loads((self.root/'manifest.json').read_text())
        pipeline.dump(pre/'run_status.json',{'status':'completed','input_sha256':manifest['preheat_input_sha256'],'config_sha256':manifest['config_sha256']})
        for p in json.loads((pre/'profiles.json').read_text()):
            thick=p['thickness_m']
            with (pre/p['file']).open('w',newline='') as f:
                w=csv.writer(f);w.writerow(['ID','IOR','x','y','z']);w.writerow([p['id'],p['ior']]+p['xyz']);w.writerow(['Time(s)','Npoints','depths','temps'])
                w.writerow([3600,3,0,thick/2,thick,500,220,35])

    def test_empty_preheat_and_nonrunnable_bake_template(self):
        text=(self.root/'preheat/preheat.fds').read_text()
        self.assertNotIn("&OBST ID='PIZZA_",text)
        self.assertNotIn("TMP_FRONT=500",text)
        self.assertNotIn('RAMP_T_I',text)
        self.assertFalse((self.root/'bake/bake.fds').exists())
        self.assertIn("ID='floor_p1_C'",text)

    def test_real_profile_transfer_cold_food_hot_substrate(self):
        self.fixture_results();pipeline.prepare_bake(self.root)
        trans=json.loads((self.root/'bake/transfer.json').read_text())
        p=trans['profiles']['PIZZA_1']
        self.assertEqual(p[0],[0,25]);self.assertEqual(p[2],[.006,500])
        self.assertAlmostEqual(p[-1][0],.086);self.assertEqual(p[-1][1],35)
        text=(self.root/'bake/bake.fds').read_text()
        self.assertIn("RAMP_T_I='INIT_PIZZA_1'",text)
        self.assertIn("SURF_IDS='PIZZA_1','INERT','INERT'",text)
        self.assertNotIn('TMP_INNER=',text)
        self.assertIn("T=0., F=1.",text)
        self.assertIn('TEMPERATURE=500',text)
        self.assertIn("QUANTITY='RADIATIVE HEAT FLUX'",text)
        self.assertIn("QUANTITY='CONVECTIVE HEAT FLUX'",text)
        # A second preparation validates provenance and reuses the same input.
        pipeline.prepare_bake(self.root)
        self.assertEqual(text,(self.root/'bake/bake.fds').read_text())

    def test_unready_oven_cannot_produce_bake(self):
        self.fixture_results(ready=False)
        with self.assertRaisesRegex(ValueError,'not ready'):pipeline.prepare_bake(self.root)
        self.assertFalse((self.root/'bake/bake.fds').exists())

    def test_short_run_cannot_transfer(self):
        self.fixture_results();path=self.root/'preheat/v4_preheat_devc.csv'
        path.write_text(path.read_text().replace('3600,','3500,'))
        with self.assertRaisesRegex(ValueError,'Incomplete'):pipeline.prepare_bake(self.root)

    def test_profile_identity_cannot_be_swapped(self):
        self.fixture_results();path=self.root/'preheat/v4_preheat_prof_1.csv'
        path.write_text(path.read_text().replace('floor_p1_C','wrong_probe'))
        with self.assertRaisesRegex(ValueError,'identity'):pipeline.prepare_bake(self.root)

    def test_modified_input_cannot_be_transferred(self):
        self.fixture_results();path=self.root/'preheat/preheat.fds';path.write_text(path.read_text()+'! changed')
        with self.assertRaisesRegex(ValueError,'input changed'):pipeline.prepare_bake(self.root)

    def test_apparent_latent_energy_integral(self):
        c=pipeline.config_load(pipeline.HERE/'campaign_config.json')
        lines='\n'.join(pipeline.material_lines(c))
        pairs=[tuple(map(float,p)) for p in re.findall(r"ID='FOOD_CP', T=([\d.]+), F=([\d.]+)",lines)]
        base=c['food']['base_cp_kJ_kgK']
        energy=sum((b-a)*((ca-base)+(cb-base))/2 for (a,ca),(b,cb) in zip(pairs,pairs[1:]))
        self.assertAlmostEqual(energy,c['food']['water_mass_fraction']*c['food']['latent_heat_kJ_kg'],places=4)


if __name__=='__main__':unittest.main()
