import copy
import json
import unittest
from pathlib import Path

from switchdepth.prompts import render_prompt, validate_prompt


EXAMPLE = Path(__file__).parents[1] / "examples" / "sample_prompt.json"


class PromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_is_valid(self):
        self.assertEqual(validate_prompt(self.data), [])

    def test_stage_gap_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["stages"][1]["start"] = 3.0
        codes = {issue.code for issue in validate_prompt(data)}
        self.assertIn("stage.coverage", codes)

    def test_depth_identity_leak_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["reference_assets"][3]["allowed"] += ", face identity"
        codes = {issue.code for issue in validate_prompt(data)}
        self.assertIn("asset.depth-role-leak", codes)

    def test_renderer_has_stable_section_order(self):
        text = render_prompt(self.data)
        headings = [
            "【Generation Goal】",
            "【Reference Asset Roles】",
            "【Identity and Appearance Lock】",
            "【Mandatory Wardrobe and Props】",
            "【Subjects and Relationships】",
            "【Stage 1 0s–2.5s】",
            "【Camera and Lighting】",
            "【Sound Design】",
        ]
        positions = [text.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()

