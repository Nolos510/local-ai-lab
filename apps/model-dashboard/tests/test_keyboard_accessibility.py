import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from model_dashboard import components  # noqa: E402
from model_dashboard.layout import _layout  # noqa: E402
from model_dashboard.pages import actions  # noqa: E402
from model_dashboard.pages import artifact as artifact_page  # noqa: E402
from model_dashboard.pages import inventory as inventory_page  # noqa: E402
from model_dashboard.pages import radar as radar_page  # noqa: E402
from model_dashboard.pages import retrieval as retrieval_page  # noqa: E402
from model_dashboard.pages import review as review_page  # noqa: E402
from model_dashboard.pages import runs as runs_page  # noqa: E402
from model_dashboard.pagination import _paginate, _pagination_controls  # noqa: E402
from model_dashboard.sorting import _sortable_headers  # noqa: E402

FOCUS_VISIBLE_SELECTOR = (
    ':where(a[href], button:not([disabled]), input:not([type="hidden"]):not([disabled]), '
    'select:not([disabled]), textarea:not([disabled]), summary, [contenteditable="true"], '
    '[tabindex]:not([tabindex="-1"])):focus-visible'
)


class KeyboardAccessibilityTests(unittest.TestCase):
    def test_shell_skip_target_active_nav_and_focus_contract(self):
        html = _layout("Fixture", "/retrieval", "<p>Body</p>")

        self.assertIn(
            '<a class="skip-link" href="#main-content">Skip to dashboard content</a>',
            html,
        )
        self.assertIn('<main id="main-content" tabindex="-1">', html)
        self.assertIn(
            'class="nav active" href="/runs" aria-current="page"',
            html,
        )
        self.assertEqual(1, html.count('aria-current="page"'))
        self.assertIn('<nav aria-label="Primary navigation">', html)
        self.assertIn('<nav class="nav-actions" aria-label="Report navigation">', html)
        self.assertIn("--focus-ring: #f8fafc", html)
        self.assertIn("--focus-halo: #2ad4ee", html)
        self.assertIn(FOCUS_VISIBLE_SELECTOR, html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link ", html)

    def test_sortable_headers_are_named_focusable_anchors_with_current_direction(self):
        current = _sortable_headers(
            "/runs",
            {"sort": ["model"], "dir": ["asc"]},
            {"Model": "model", "Score": "score"},
        )
        table = components._table(
            ["Model", "Score"],
            [["Fixture", "80"]],
            sortable_headers=current,
        )

        self.assertIn('<th aria-sort="ascending">', table)
        self.assertIn(
            'class="sort-link" href="/runs?sort=model&amp;dir=desc" '
            'aria-label="Model: currently sorted ascending. Activate to sort descending."',
            table,
        )
        self.assertIn(
            'class="sort-link" href="/runs?sort=score&amp;dir=asc" '
            'aria-label="Score: not currently sorted. Activate to sort ascending."',
            table,
        )

    def test_pagination_and_filter_controls_are_named_anchors(self):
        page = _paginate(list(range(5)), {"page": ["2"], "page_size": ["2"]})
        pagination = _pagination_controls(
            "/runs",
            {"page": ["2"], "page_size": ["2"]},
            page,
            label="Model runs pagination",
        )
        chips = radar_page._discover_chip_row(3, 2, 1, "", "")
        decision_card = components._stat_card(
            "Keep installed",
            3,
            "ti-device-desktop-check",
            href="/inventory?keep=yes#inventory-decisions",
            active=True,
            link_class="decision-stat-link",
        )

        self.assertIn(
            'class="pagination-link" rel="prev" '
            'href="/runs?page=1&amp;page_size=2" '
            'aria-label="Model runs pagination: previous page, page 1 of 3"',
            pagination,
        )
        self.assertIn(
            'class="pagination-link" rel="next" '
            'href="/runs?page=3&amp;page_size=2" '
            'aria-label="Model runs pagination: next page, page 3 of 3"',
            pagination,
        )
        self.assertIn(
            '<nav class="filter-chip-row" aria-label="Discover quick filters">',
            chips,
        )
        self.assertIn(
            'class="filter-chip active" href="/radar" aria-current="true" '
            'aria-label="To evaluate filter, 3 candidates, current filter"',
            chips,
        )
        self.assertIn(
            'class="filter-chip" href="/projects" '
            'aria-label="Open project deep view"',
            chips,
        )
        self.assertIn(
            'href="/inventory?keep=yes#inventory-decisions" aria-current="true" '
            'aria-label="Keep installed: 3, current filter"',
            decision_card,
        )

    def test_native_disclosures_have_contextual_escaped_names(self):
        history = runs_page._run_history_control(
            {
                "other_runs": [object(), object()],
                "authoritative_run": {"model_id": 7},
            },
            'Model "A" <unsafe>',
        )
        response = artifact_page._response_details(
            {"raw_response": "<private>"},
            disclosure_label='Show full response for prompt "p<1>"',
        )
        retrieval = retrieval_page._evidence_cell(
            retrieval_page._configuration(
                "corpus-<unsafe>",
                "hybrid",
                "cross-encoder",
            ),
            {"status": "not_scored"},
        )

        self.assertIn(
            '<summary aria-label="Show 2 earlier runs for Model &quot;A&quot; &lt;unsafe&gt;">',
            history,
        )
        self.assertIn(
            '<summary aria-label="Show full response for prompt &quot;p&lt;1&gt;&quot;">',
            response,
        )
        self.assertIn("&lt;private&gt;", response)
        self.assertNotIn("<private>", response)
        self.assertIn(
            '<summary aria-label="Show exact local collection and scoring command for '
            'corpus-&lt;unsafe&gt;, hybrid retrieval with cross-encoder reranker">',
            retrieval,
        )

    def test_review_and_two_step_action_pages_preserve_native_focus(self):
        confirmation_controls = review_page._confirmation_controls(
            {"final_label": "WATCHLIST"},
            "machine_reviewed",
        )
        agreement_control = review_page._confirm_agreements_control(
            [{"run_id": 'run-<unsafe>', "review": {"status": "machine_reviewed"}}],
            True,
            'token-<unsafe>',
        )
        review_result = actions._human_score_action_page(
            {"status": "confirmed", "benchmark_run_id": "fixture-run"}
        )
        batch_result = actions._human_confirmation_batch_page(
            {"confirmed": 1, "failed": 0, "results": []}
        )
        delete_target = SimpleNamespace(
            path=Path("/tmp/fixture-model"),
            root=Path("/tmp"),
            runtime="Fixture",
            model_id="fixture/model",
            size_bytes=1,
            action="Move to Trash",
        )
        delete_confirm = inventory_page._delete_confirm_page(
            delete_target,
            "fixture-key",
            "fixture-token",
        )
        run_all_confirm = inventory_page._run_all_confirm_page(
            {"runnable": [], "skipped": []},
            "fixture-token",
        )

        for html in (review_result, batch_result, delete_confirm, run_all_confirm):
            with self.subTest(title=html.split("<title>", 1)[1].split("</title>", 1)[0]):
                self.assertIn(
                    'class="action-focus-target" tabindex="-1" autofocus',
                    html,
                )
        self.assertIn(
            'class="nav active" href="/reviews" aria-current="page"',
            review_result,
        )
        self.assertIn(
            '<input type="checkbox" name="human_reviewed" value="yes" required>',
            confirmation_controls,
        )
        self.assertIn(
            '<button type="submit" name="confirmation_mode" value="primary">'
            "Confirm Primary Score</button>",
            confirmation_controls,
        )
        self.assertIn(
            '<button type="submit" name="confirmation_mode" value="edited">'
            "Edit &amp; Confirm</button>",
            confirmation_controls,
        )
        self.assertIn(
            'method="post" action="/actions/confirm-reviewed-agreements"',
            agreement_control,
        )
        self.assertIn('value="run-&lt;unsafe&gt;"', agreement_control)
        self.assertIn('value="token-&lt;unsafe&gt;"', agreement_control)
        self.assertIn('class="danger" type="submit">Confirm Remove</button>', delete_confirm)
        self.assertIn('class="clear-link" href="/inventory">Cancel</a>', delete_confirm)


if __name__ == "__main__":
    unittest.main()
