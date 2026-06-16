import re
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import charts  # noqa: E402


class ChartTests(unittest.TestCase):
    def test_horizontal_bars_returns_svg_with_viewbox(self):
        html = charts.horizontal_bars([("A", 1), ("B", 2)])

        self.assertIn("<svg", html)
        self.assertIn("viewBox", html)

    def test_horizontal_bars_renders_one_rect_per_item(self):
        html = charts.horizontal_bars([("A", 1), ("B", 2), ("C", 3)])

        self.assertEqual(3, html.count("<rect"))

    def test_largest_value_maps_to_full_bar_width(self):
        html = charts.horizontal_bars([("Small", 5), ("Large", 10)])
        widths = [float(match) for match in re.findall(r'<rect[^>]+ width="([^"]+)"', html)]

        self.assertEqual([300.0, 600.0], widths)

    def test_zero_or_empty_data_returns_placeholder(self):
        empty = charts.horizontal_bars([])
        zero = charts.horizontal_bars([("Zero", 0)])

        self.assertIn("No data yet", empty)
        self.assertIn("No data yet", zero)
        self.assertNotIn("NaN", empty + zero)
        self.assertNotIn("inf", empty + zero)
        self.assertNotIn("<rect", empty + zero)

    def test_labels_are_escaped(self):
        html = charts.horizontal_bars([("Qwen <Coder> & Friends", 1)])

        self.assertIn("Qwen &lt;Coder&gt; &amp; Friends", html)
        self.assertNotIn("Qwen <Coder>", html)


if __name__ == "__main__":
    unittest.main()
