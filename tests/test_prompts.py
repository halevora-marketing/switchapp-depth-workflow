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
            "Core task:",
            "Material bindings:",
            "Identity and appearance lock:",
            "Mandatory wardrobe and props:",
            "Subjects and relationships:",
            "Shot timeline:",
            "Environment, camera, and lighting:",
            "Dialogue, audio, and text:",
            "Maintain consistency:",
        ]
        positions = [text.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))

    def test_unresolved_observation_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["wardrobe_and_props"] = "NOT SUPPLIED"
        codes = {issue.code for issue in validate_prompt(data)}
        self.assertIn("content.unsupplied", codes)

    def test_only_wan_style_is_accepted(self):
        data = copy.deepcopy(self.data)
        data["prompt_style"] = "generic"
        codes = {issue.code for issue in validate_prompt(data)}
        self.assertIn("style.invalid", codes)


if __name__ == "__main__":
    unittest.main()
