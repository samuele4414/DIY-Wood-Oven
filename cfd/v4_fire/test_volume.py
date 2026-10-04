import unittest
from export_volume import decode_rle


class SmokeRLETest(unittest.TestCase):
    def test_literals_and_run(self):
        self.assertEqual(decode_rle(bytes([0,2,255,7,3,254]),6).tolist(),[0,2,7,7,7,254])

    def test_rejects_incomplete_and_wrong_lengths(self):
        for encoded,count in [(bytes([255,7]),3),(bytes([255,7,5]),3),(bytes([2]),3)]:
            with self.subTest(encoded=encoded):
                with self.assertRaises(ValueError):decode_rle(encoded,count)


if __name__=='__main__':unittest.main()
