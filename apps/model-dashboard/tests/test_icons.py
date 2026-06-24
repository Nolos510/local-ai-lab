import re
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import icons, server  # noqa: E402


class IconTests(unittest.TestCase):
    def test_layout_has_no_external_stylesheet_link(self):
        html = server._layout("Icons", "/", "<p>body</p>")

        self.assertNotIn("cdn.jsdelivr", html)
        self.assertNotRegex(html, r'<link[^>]+rel="stylesheet"[^>]+https?://')

    def test_nav_icons_render_inline_svg(self):
        for name in server.NAV_ICONS.values():
            with self.subTest(name=name):
                self.assertIn("<svg", icons.icon(name))

    def test_current_server_icon_names_resolve(self):
        package_dir = Path(server.__file__).parent
        source = "\n".join(path.read_text() for path in package_dir.rglob("*.py"))
        names = sorted(set(re.findall(r"ti-[a-z0-9-]+", source)))

        self.assertTrue(names)
        for name in names:
            with self.subTest(name=name):
                self.assertIn("<svg", icons.icon(name))

    def test_unknown_icon_uses_fallback(self):
        html = icons.icon("ti-does-not-exist")

        self.assertIn("<svg", html)
        self.assertIn("ti-circle", html)


if __name__ == "__main__":
    unittest.main()
