import unittest

from switchdepth.analysis import MISSING


class AnalysisTests(unittest.TestCase):
    def test_missing_marker_explicitly_forbids_inference(self):
        self.assertIn("do not infer", MISSING.lower())


if __name__ == "__main__":
    unittest.main()
