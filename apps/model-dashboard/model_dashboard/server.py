"""A dependency-free local web dashboard for model eval results."""

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import db
from .reports import generate_markdown_report
from .scoring import METRIC_FIELDS

NAV_ITEMS = (
    ("/", "Overview"),
    ("/runs", "Model Runs"),
    ("/compare", "Compare Models"),
    ("/storage", "Storage / Install Status"),
    ("/reports", "Reports"),
)


def _text(value, fallback=""):
    return escape(fallback if value is None else str(value))


def _number(value, digits=1, fallback=""):
    if value is None:
        return fallback
    return "{:.{}f}".format(float(value), digits)


def _pill(value):
    label = _text(value, "UNLABELED")
    return '<span class="pill">{}</span>'.format(label)


def _table(headers, rows, empty_message="No rows yet."):
    if not rows:
        return '<p class="empty">{}</p>'.format(escape(empty_message))
    header_html = "".join("<th>{}</th>".format(escape(header)) for header in headers)
    row_html = []
    for row in rows:
        row_html.append("<tr>{}</tr>".format("".join("<td>{}</td>".format(cell) for cell in row)))
    return "<table><thead><tr>{}</tr></thead><tbody>{}</tbody></table>".format(
        header_html, "".join(row_html)
    )


def _query_value(query, key):
    value = query.get(key, "")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value).strip()


def _option(value, label, selected):
    selected_attr = " selected" if value == selected else ""
    return '<option value="{}"{}>{}</option>'.format(
        _text(value), selected_attr, _text(label)
    )


def _field_options(rows, field):
    values = {str(row[field]) for row in rows if row[field] not in (None, "")}
    return sorted(values, key=lambda value: value.lower())


def _filter_values(query):
    return {
        "q": _query_value(query, "q"),
        "label": _query_value(query, "label"),
        "decision": _query_value(query, "decision"),
        "keep": _query_value(query, "keep"),
    }


def _matches_search(row, search):
    if not search:
        return True
    haystack = " ".join(
        str(row[field] or "")
        for field in (
            "model_name",
            "model_family",
            "provider",
            "backend",
            "quantization",
            "final_label",
            "decision",
            "best_use_case",
        )
    )
    return search.lower() in haystack.lower()


def _filter_summaries(rows, filters):
    filtered = []
    for row in rows:
        if filters["label"] and row["final_label"] != filters["label"]:
            continue
        if filters["decision"] and row["decision"] != filters["decision"]:
            continue
        if filters["keep"] == "yes" and row["keep_installed"] != 1:
            continue
        if filters["keep"] == "no" and row["keep_installed"] != 0:
            continue
        if not _matches_search(row, filters["q"]):
            continue
        filtered.append(row)
    return filtered


def _overview_filters(rows, filters):
    label_options = "".join(
        _option(label, label, filters["label"]) for label in _field_options(rows, "final_label")
    )
    decision_options = "".join(
        _option(decision, decision, filters["decision"])
        for decision in _field_options(rows, "decision")
    )
    clear_link = '<a class="clear-link" href="/">Clear</a>' if any(filters.values()) else ""
    return """
    <form class="filters" method="get" action="/">
      <div class="field field-wide">
        <label for="filter-q">Search</label>
        <input id="filter-q" name="q" type="search" value="{q}">
      </div>
      <div class="field">
        <label for="filter-label">Label</label>
        <select id="filter-label" name="label">
          {all_labels}
          {label_options}
        </select>
      </div>
      <div class="field">
        <label for="filter-decision">Decision</label>
        <select id="filter-decision" name="decision">
          {all_decisions}
          {decision_options}
        </select>
      </div>
      <div class="field">
        <label for="filter-keep">Install</label>
        <select id="filter-keep" name="keep">
          {any_keep}
          {keep_yes}
          {keep_no}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        q=_text(filters["q"]),
        all_labels=_option("", "All labels", filters["label"]),
        label_options=label_options,
        all_decisions=_option("", "All decisions", filters["decision"]),
        decision_options=decision_options,
        any_keep=_option("", "Any", filters["keep"]),
        keep_yes=_option("yes", "Keep", filters["keep"]),
        keep_no=_option("no", "Not kept", filters["keep"]),
        clear_link=clear_link,
    )


def _layout(title, current_path, body):
    nav = []
    for path, label in NAV_ITEMS:
        active = " active" if current_path == path else ""
        nav.append('<a class="nav{}" href="{}">{}</a>'.format(active, path, escape(label)))
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - Local Model Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f5ef;
      --panel: #ffffff;
      --ink: #202124;
      --muted: #62676f;
      --line: #ded9cf;
      --accent: #196f6b;
      --accent-2: #9b4d1f;
      --good: #1f7a42;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 15px;
      line-height: 1.45;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: #fffdf8;
    }}
    .topbar {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 18px 20px 12px;
    }}
    h1 {{
      margin: 0 0 14px;
      font-size: 28px;
      line-height: 1.15;
      letter-spacing: 0;
    }}
    nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .nav {{
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 7px 10px;
      text-decoration: none;
      background: #fbfaf6;
    }}
    .nav.active {{
      border-color: var(--accent);
      color: #ffffff;
      background: var(--accent);
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .stat, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 4px;
    }}
    .stat .value {{
      font-size: 26px;
      font-weight: 700;
    }}
    .filters {{
      display: grid;
      grid-template-columns: minmax(220px, 2fr) repeat(3, minmax(140px, 1fr)) auto;
      gap: 10px;
      align-items: end;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      margin: 0 0 14px;
    }}
    .field label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      margin: 0 0 4px;
    }}
    input, select {{
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fffdf8;
      color: var(--ink);
      font: inherit;
      padding: 7px 9px;
    }}
    button {{
      min-height: 36px;
      border: 1px solid var(--accent);
      border-radius: 6px;
      background: var(--accent);
      color: #ffffff;
      font: inherit;
      font-weight: 700;
      padding: 7px 12px;
      cursor: pointer;
    }}
    .filter-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .clear-link {{
      color: var(--muted);
      font-size: 13px;
      text-decoration: none;
    }}
    h2 {{
      font-size: 20px;
      margin: 0 0 12px;
      letter-spacing: 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 9px;
      text-align: left;
      vertical-align: top;
      white-space: normal;
      overflow-wrap: anywhere;
    }}
    th {{
      background: #ede7dc;
      color: #393b3f;
      font-size: 13px;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    a {{ color: var(--accent); }}
    .pill {{
      display: inline-block;
      border-radius: 999px;
      padding: 3px 8px;
      background: #e4f0ed;
      color: #185a55;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .empty {{ color: var(--muted); }}
    .report {{
      background: #1e2227;
      color: #f6f0e6;
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      white-space: pre-wrap;
    }}
    .split {{
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.6fr);
      gap: 16px;
    }}
    @media (max-width: 780px) {{
      .filters {{ grid-template-columns: 1fr; }}
      .filter-actions {{ justify-content: flex-start; }}
      .split {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 24px; }}
      th, td {{ padding: 8px 7px; }}
    }}
  </style>
</head>
<body>
  <header><div class="topbar"><h1>Local Model Performance Dashboard</h1><nav>{nav}</nav></div></header>
  <main>{body}</main>
</body>
</html>""".format(
        title=escape(title), nav="".join(nav), body=body
    )


def _overview(conn, query=None):
    counts = {table: db.table_count(conn, table) for table in db.TABLES}
    summaries = db.list_model_summaries(conn)
    filters = _filter_values(query or {})
    filtered_summaries = _filter_summaries(summaries, filters)
    avg_score = conn.execute("SELECT AVG(total_score) AS avg_score FROM eval_scores").fetchone()[
        "avg_score"
    ]
    keep_count = conn.execute(
        "SELECT COUNT(*) AS count FROM decisions WHERE keep_installed = 1"
    ).fetchone()["count"]
    rows = []
    for row in filtered_summaries:
        rows.append(
            [
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["id"], name=_text(row["model_name"])
                ),
                _text(row["provider"]),
                _number(row["params_b"]),
                _text(row["backend"]),
                _number(row["tokens_per_sec"]),
                _number(row["ram_usage_gb"]),
                _number(row["total_score"], 2),
                _pill(row["final_label"]),
                _text(row["decision"]),
            ]
        )
    body = """
    <section class="grid">
      <div class="stat"><div class="label">Models</div><div class="value">{models}</div></div>
      <div class="stat"><div class="label">Runs</div><div class="value">{runs}</div></div>
      <div class="stat"><div class="label">Average score</div><div class="value">{avg}</div></div>
      <div class="stat"><div class="label">Kept installed</div><div class="value">{kept}</div></div>
    </section>
    <section>
      {filters}
      <h2>Ranked Local Models{filtered_count}</h2>
      {table}
    </section>
    """.format(
        models=counts["models"],
        runs=counts["model_runs"],
        avg=_number(avg_score, 1, "0.0"),
        kept=keep_count,
        filters=_overview_filters(summaries, filters),
        filtered_count=(
            " ({} of {})".format(len(filtered_summaries), len(summaries))
            if any(filters.values())
            else ""
        ),
        table=_table(
            [
                "Model",
                "Provider",
                "Params B",
                "Backend",
                "Tok/s",
                "RAM GB",
                "Score",
                "Label",
                "Decision",
            ],
            rows,
            empty_message="No models match these filters.",
        ),
    )
    return _layout("Overview", "/", body)


def _runs(conn):
    rows = []
    for row in db.list_runs(conn):
        rows.append(
            [
                _text(row["date_tested"]),
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["model_id"], name=_text(row["model_name"])
                ),
                _text(row["backend"]),
                _text(row["format"]),
                _text(row["quantization"]),
                _text(row["context_window"]),
                _number(row["tokens_per_sec"]),
                _number(row["ram_usage_gb"]),
                _number(row["total_score"], 2),
                _pill(row["final_label"]),
                _text(row["stability_notes"]),
            ]
        )
    body = "<h2>Model Runs</h2>{}".format(
        _table(
            [
                "Date",
                "Model",
                "Backend",
                "Format",
                "Quant",
                "Context",
                "Tok/s",
                "RAM GB",
                "Score",
                "Label",
                "Stability",
            ],
            rows,
        )
    )
    return _layout("Model Runs", "/runs", body)


def _compare(conn):
    headers = ["Model", "Score", "Label"] + [field.replace("_", " ").title() for field in METRIC_FIELDS]
    rows = []
    for row in db.list_score_details(conn):
        cells = [
            '<a href="/models/{id}">{name}</a>'.format(
                id=row["model_id"], name=_text(row["model_name"])
            ),
            _number(row["total_score"], 2),
            _pill(row["final_label"]),
        ]
        cells.extend(_number(row[field], 0) for field in METRIC_FIELDS)
        rows.append(cells)
    body = "<h2>Compare Models</h2>{}".format(_table(headers, rows))
    return _layout("Compare Models", "/compare", body)


def _model_detail(conn, model_id):
    detail = db.get_model_detail(conn, model_id)
    if detail is None:
        return _layout("Model Detail", "", "<h2>Model not found</h2>")
    model = detail["model"]
    run_rows = []
    for row in detail["runs"]:
        run_rows.append(
            [
                _text(row["date_tested"]),
                _text(row["backend"]),
                _text(row["format"]),
                _text(row["quantization"]),
                _text(row["context_window"]),
                _number(row["tokens_per_sec"]),
                _number(row["ram_usage_gb"]),
                _number(row["total_score"], 2),
                _pill(row["final_label"]),
                _text(row["run_notes"]),
            ]
        )
    decision_rows = []
    for row in detail["decisions"]:
        decision_rows.append(
            [
                _text(row["created_at"]),
                _text(row["decision"]),
                "yes" if row["keep_installed"] else "no",
                _text(row["best_use_case"]),
                _text(row["weakness"]),
                _text(row["retest_condition"]),
            ]
        )
    body = """
    <div class="split">
      <section class="panel">
        <h2>{name}</h2>
        <p><strong>Family:</strong> {family}</p>
        <p><strong>Provider:</strong> {provider}</p>
        <p><strong>Parameters:</strong> {params}B</p>
        <p><strong>License:</strong> {license}</p>
        <p><strong>Source:</strong> <a href="{source}">{source}</a></p>
        <p>{notes}</p>
      </section>
      <section class="panel">
        <h2>Current Read</h2>
        <p>{summary}</p>
      </section>
    </div>
    <section style="margin-top:16px"><h2>Runs</h2>{runs}</section>
    <section style="margin-top:16px"><h2>Decisions</h2>{decisions}</section>
    """.format(
        name=_text(model["model_name"]),
        family=_text(model["model_family"]),
        provider=_text(model["provider"]),
        params=_number(model["params_b"], 1),
        license=_text(model["license"]),
        source=_text(model["source_url"], "#"),
        notes=_text(model["notes"]),
        summary=_text(detail["decisions"][0]["best_use_case"] if detail["decisions"] else ""),
        runs=_table(
            [
                "Date",
                "Backend",
                "Format",
                "Quant",
                "Context",
                "Tok/s",
                "RAM GB",
                "Score",
                "Label",
                "Notes",
            ],
            run_rows,
        ),
        decisions=_table(
            ["Created", "Decision", "Keep", "Best use case", "Weakness", "Retest"],
            decision_rows,
        ),
    )
    return _layout("Model Detail", "", body)


def _storage(conn):
    rows = []
    for row in db.list_decisions(conn):
        rows.append(
            [
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["model_id"], name=_text(row["model_name"])
                ),
                _text(row["decision"]),
                "yes" if row["keep_installed"] else "no",
                _text(row["best_use_case"]),
                _text(row["weakness"]),
                _text(row["retest_condition"]),
            ]
        )
    body = "<h2>Storage / Install Status</h2>{}".format(
        _table(
            ["Model", "Decision", "Keep installed", "Best use case", "Weakness", "Retest"],
            rows,
        )
    )
    return _layout("Storage / Install Status", "/storage", body)


def _reports(conn, database_path):
    report = generate_markdown_report(database_path)
    body = '<h2>Reports</h2><pre class="report">{}</pre>'.format(escape(report))
    return _layout("Reports", "/reports", body)


def make_handler(database_path):
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            try:
                with db.connect(database_path) as conn:
                    db.create_schema(conn)
                    html = self._route(parsed.path, parse_qs(parsed.query), conn)
                self.send_response(200)
            except Exception as exc:
                html = _layout("Error", "", "<h2>Error</h2><p>{}</p>".format(_text(exc)))
                self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def log_message(self, fmt, *args):
            return

        def _route(self, path, query, conn):
            if path == "/":
                return _overview(conn, query)
            if path == "/runs":
                return _runs(conn)
            if path == "/compare":
                return _compare(conn)
            if path == "/storage":
                return _storage(conn)
            if path == "/reports":
                return _reports(conn, database_path)
            if path.startswith("/models/"):
                model_id = int(path.rsplit("/", 1)[-1])
                return _model_detail(conn, model_id)
            return _layout("Not Found", "", "<h2>Page not found</h2>")

    return DashboardHandler


def serve(database_path, host="127.0.0.1", port=8765):
    server = ThreadingHTTPServer((host, port), make_handler(database_path))
    print("Serving Local Model Dashboard at http://{}:{}".format(host, port), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
