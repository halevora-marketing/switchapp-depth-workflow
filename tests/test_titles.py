import unittest

from switchdepth.titles import safe_title, slug


class TitleTests(unittest.TestCase):
    def test_removes_invalid_filename_characters(self):
        self.assertEqual(safe_title('Pool: "walk" / take?'), "Pool walk take")

    def test_handles_windows_reserved_name(self):
        self.assertEqual(safe_title("CON"), "CON Clip")

    def test_slug_is_stable(self):
        self.assertEqual(slug("Sunny Plaza Walk"), "sunny-plaza-walk")


if __name__ == "__main__":
    unittest.main()

