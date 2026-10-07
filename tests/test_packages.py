import json
import tempfile
import unittest
from pathlib import Path

from switchdepth.packages import create_item, validate_package


class PackageTests(unittest.TestCase):
    def test_create_item_uses_descriptive_safe_title(self):
        with tempfile.TemporaryDirectory() as raw:
            item = create_item(Path(raw), title="Pool: Walk?")
            self.assertEqual(item.name, "Pool Walk")
            self.assertTrue((item / "manifest.json").is_file())

    def test_complete_fake_package_passes_without_media_probe(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = {
                "version": 1,
                "item_key": "demo",
                "title": "Demo",
                "analysis": {"status": "complete", "file": "Full analysis.md"},
                "prompts": {
                    "seedance": "Seedance prompt.txt",
                    "kling": "Kling prompt.txt",
                    "gemini": "Gemini prompt.txt",
                    "finished": "Finished prompt.txt"
                },
                "media": {
                    "original": "Original video.mp4",
                    "audio": "Original audio.m4a",
                    "depth_maps": ["Depth map.mp4"]
                },
                "status": "complete"
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            for name in (
                "Full analysis.md", "Seedance prompt.txt", "Kling prompt.txt",
                "Gemini prompt.txt", "Finished prompt.txt", "Original video.mp4",
                "Original audio.m4a", "Depth map.mp4",
            ):
                (root / name).write_text("placeholder", encoding="utf-8")
            self.assertEqual(validate_package(manifest_path, probe_media=False), [])


if __name__ == "__main__":
    unittest.main()

