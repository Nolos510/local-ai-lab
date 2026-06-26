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
        self.assertIn("<defs>", html)
        self.assertIn("<linearGradient", html)
        self.assertIn('id="chart-bar-gradient"', html)
        self.assertIn('stop-color="#8b7bff"', html)
        self.assertIn('stop-color="#2ad4ee"', html)
        self.assertEqual(3, html.count('fill="url(#chart-bar-gradient)"'))

    def test_largest_value_maps_to_full_bar_width(self):
        html = charts.horizontal_bars([("Small", 5), ("Large", 10)])
        widths = [float(match) for match in re.findall(r'<rect[^>]+ width="([^"]+)"', html)]

        self.assertEqual([300.0, 600.0], widths)

    def test_explicit_max_value_scales_against_full_range(self):
        html = charts.horizontal_bars([("Score", 72.5)], max_value=100)
        widths = [float(match) for match in re.findall(r'<rect[^>]+ width="([^"]+)"', html)]

        self.assertEqual([435.0], widths)

    def test_values_above_explicit_max_are_clamped_to_plot_width(self):
        html = charts.horizontal_bars([("Too high", 725)], max_value=100)
        widths = [float(match) for match in re.findall(r'<rect[^>]+ width="([^"]+)"', html)]

        self.assertEqual([600.0], widths)

    def test_zero_or_empty_data_returns_placeholder(self):
        empty = charts.horizontal_bars([])
        zero = charts.horizontal_bars([("Zero", 0)])
        custom = charts.horizontal_bars([], empty_message="No perf values yet")

        self.assertIn("No data yet", empty)
        self.assertIn("No data yet", zero)
        self.assertIn("No perf values yet", custom)
        self.assertNotIn("NaN", empty + zero)
        self.assertNotIn("inf", empty + zero)
        self.assertNotIn("<rect", empty + zero)

    def test_labels_are_escaped(self):
        html = charts.horizontal_bars([("Qwen <Coder> & Friends", 1)])

        self.assertIn("Qwen &lt;Coder&gt; &amp; Friends", html)
        self.assertNotIn("Qwen <Coder>", html)

    def test_long_labels_expand_chart_width_without_truncation(self):
        label = "Dolphin-Mistral-24B-Venice-Edition (LM Studio CLI)"
        html = charts.horizontal_bars([(label, 28.1)])

        self.assertIn(f">{label}</text>", html)
        self.assertNotIn("...", html)
        self.assertIn('style="min-width:', html)

    def test_custom_label_width_moves_plot_start(self):
        html = charts.horizontal_bars([("Long local model label", 1)], label_width=420)

        self.assertIn('viewBox="0 0 1162 54"', html)
        self.assertIn('style="min-width:1162px"', html)
        self.assertIn('x1="436"', html)


if __name__ == "__main__":
    unittest.main()
