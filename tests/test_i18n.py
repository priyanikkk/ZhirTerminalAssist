import unittest
from zhirterminalassist.i18n import get_language, set_language, t

class TestI18n(unittest.TestCase):
    def test_language_switching(self):
        # Russian
        set_language("ru")
        self.assertEqual(get_language(), "ru")
        self.assertIn("ZhirTerminalAssist", t("app_title"))
        self.assertEqual(t("done"), "Готово")
        self.assertEqual(t("error"), "Ошибка")

        # English
        set_language("en")
        self.assertEqual(get_language(), "en")
        self.assertEqual(t("done"), "Done")
        self.assertEqual(t("error"), "Error")

        # Format kwargs
        res = t("file_created", path="my_file.py")
        self.assertEqual(res, "Created file: my_file.py")

        # Reset back to ru
        set_language("ru")

if __name__ == "__main__":
    unittest.main()
