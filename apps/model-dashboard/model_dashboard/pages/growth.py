"""Growth / Skills Lab dashboard cockpit."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

import re

from .. import growth as growth_data
from ..components import *
from ..components import _metric_label
from ..layout import _layout
from ..pagination import _paginate, _pagination_controls
from ..sorting import _sort_rows, _sortable_headers

DEFAULT_GROWTH_CATALOG_DIR = REPO_ROOT / "data" / "growth_registry"
DEFAULT_GROWTH_STATE_PATH = REPO_ROOT / ".local-ai-lab" / "growth-state-v1.json"
GROWTH_VIEWS = (
    ("skills", "Skills"),
    ("extensions", "Extensions"),
    ("learning", "Learning"),
    ("inbox", "Inbox"),
)
VIEW_KINDS = {
    "skills": "skill",
    "extensions": "extension",
    "learning": "learning",
}
EVIDENCE_FILTERS = {
    "detected": "Detected in saved inventory",
    "not_detected": "Not detected in saved inventory",
    "evidenced": "Evidence artifact exists now",
    "not_evidenced": "No evidence artifact exists now",
    "detected_not_evidenced": "Detected, not evidenced",
}
GROWTH_PAGE_SIZE = 5
SAFE_FILTER_RE = re.compile(r"^[A-Za-z0-9 _.,:;/'()@+&?-]{1,80}$")
PRIORITY_ORDER = {"Now": 0, "Next": 1, "Later": 2, "Watch": 3, "Blocked": 4}

GROWTH_SORT_COLUMNS = {
    "item": (lambda row: row.get("name") or row.get("id"), "text"),
    "priority": (lambda row: PRIORITY_ORDER.get(row.get("status"), 99), "number"),
    "role": (lambda row: " ".join(row.get("career_lenses", ())), "text"),
    "effort": (lambda row: row.get("effort_tier"), "text"),
    "evidence": (
        lambda row: f'{int(bool(row.get("_detected")))} {int(bool(row.get("_evidenced")))}',
        "text",
    ),
    "review": (lambda row: row.get("review_state"), "text"),
    "next_action": (lambda row: row.get("next_action"), "text"),
    "progress": (lambda row: row.get("_progress_status"), "text"),
}
GROWTH_SORT_HEADERS = {
    "Item": "item",
    "Priority": "priority",
    "Role": "role",
    "Effort": "effort",
    "Detected vs evidenced": "evidence",
    "Safe? / review_state": "review",
    "Proof + next action": "next_action",
    "Progress": "progress",
}


def _query_value(query, key):
    value = (query or {}).get(key, "")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value).strip()


def _safe_risk_filter(value):
    if not SAFE_FILTER_RE.fullmatch(value or "") or growth_data.contains_private_literal(value):
        return ""
    return value


def _growth_filter_values(query):
    role = _query_value(query, "role")
    effort = _query_value(query, "effort")
    status = _query_value(query, "status")
    evidence = _query_value(query, "evidence")
    return {
        "role": role if role in growth_data.CAREER_LENSES else "",
        "effort": effort if effort in growth_data.EFFORT_TIERS else "",
        "status": (
            status
            if status in growth_data.CATALOG_STATUSES | growth_data.PROGRESS_STATUSES
            else ""
        ),
        "risk": _safe_risk_filter(_query_value(query, "risk")),
        "evidence": evidence if evidence in EVIDENCE_FILTERS else "",
    }


def _safe_query(query, view, filters):
    safe = {"view": [view]}
    for key, value in filters.items():
        if value:
            safe[key] = [value]
    sort = _query_value(query, "sort")
    if sort in GROWTH_SORT_COLUMNS:
        safe["sort"] = [sort]
        safe["dir"] = ["desc" if _query_value(query, "dir") == "desc" else "asc"]
    for key in ("page", "page_size"):
        value = _query_value(query, key)
        if value.isdigit() and 0 < int(value) <= 100:
            safe[key] = [value]
    return safe


def _matches_growth_filters(item, filters):
    if filters["role"] and filters["role"] not in item["career_lenses"]:
        return False
    if filters["effort"] and filters["effort"] != item["effort_tier"]:
        return False
    if filters["status"] and filters["status"] not in {
        item["status"],
        item.get("_progress_status"),
    }:
        return False
    if filters["risk"]:
        risk_haystack = " ".join(item["risk_facts"][field] for field in growth_data.RISK_FIELDS)
        if filters["risk"].casefold() not in risk_haystack.casefold():
            return False
    evidence = filters["evidence"]
    if evidence == "detected" and not item["_detected"]:
        return False
    if evidence == "not_detected" and item["_detected"]:
        return False
    if evidence == "evidenced" and not item["_evidenced"]:
        return False
    if evidence == "not_evidenced" and item["_evidenced"]:
        return False
    return evidence != "detected_not_evidenced" or (
        item["_detected"] and not item["_evidenced"]
    )


def _display(value):
    return _text("—" if value in (None, "") else value)


def _yes_no(value):
    return "yes" if value else "no"


def _option(value, label, selected):
    selected_attr = " selected" if value == selected else ""
    return f'<option value="{_text(value)}"{selected_attr}>{_text(label)}</option>'


def _growth_view_switcher(active_view, counts):
    links = []
    for view, label in GROWTH_VIEWS:
        active = view == active_view
        current = ' aria-current="true"' if active else ""
        active_class = " active" if active else ""
        links.append(
            '<a class="filter-chip{active_class}" href="/growth?view={view}"{current} '
            'aria-label="{label} view, {count} items{current_label}">'
            "<span>{label}</span><strong>{count}</strong></a>".format(
                active_class=active_class,
                view=_text(view),
                current=current,
                label=_text(label),
                count=_text(counts[view]),
                current_label=", current view" if active else "",
            )
        )
    return (
        '<nav class="filter-chip-row growth-view-switcher" aria-label="Growth views">'
        + "".join(links)
        + "</nav>"
    )


def _growth_filters(filters, view):
    status_options = (
        ("Now", "Now"),
        ("Next", "Next"),
        ("Later", "Later"),
        ("Watch", "Watch"),
        ("Blocked", "Blocked"),
        ("queued", "queued progress"),
        ("in_progress", "in_progress progress"),
        ("completed", "completed progress"),
        ("skipped", "skipped progress"),
    )
    clear_link = (
        f'<a class="clear-link" href="/growth?view={_text(view)}">Clear</a>'
        if any(filters.values())
        else ""
    )
    return """
    <form class="filters filters-growth" method="get" action="/growth">
      <input type="hidden" name="view" value="{view}">
      <div class="field">
        <label for="growth-role">Role</label>
        <select id="growth-role" name="role">
          {all_roles}
          {role_options}
        </select>
      </div>
      <div class="field">
        <label for="growth-effort">Effort</label>
        <select id="growth-effort" name="effort">
          {all_efforts}
          {effort_options}
        </select>
      </div>
      <div class="field">
        <label for="growth-status">Status</label>
        <select id="growth-status" name="status">
          {all_statuses}
          {status_options}
        </select>
      </div>
      <div class="field">
        <label for="growth-risk">Risk fact contains</label>
        <input id="growth-risk" name="risk" type="search" maxlength="80" value="{risk}" placeholder="network, token scope, writes…">
      </div>
      <div class="field">
        <label for="growth-evidence">Evidence</label>
        <select id="growth-evidence" name="evidence">
          {all_evidence}
          {evidence_options}
        </select>
      </div>
      <div class="filter-actions">
        <button type="submit">Apply</button>
        {clear_link}
      </div>
    </form>
    """.format(
        view=_text(view),
        all_roles=_option("", "All roles", filters["role"]),
        role_options="".join(
            _option(value, value, filters["role"])
            for value in ("AIA", "AUT", "MLD")
        ),
        all_efforts=_option("", "All effort tiers", filters["effort"]),
        effort_options="".join(
            _option(value, f"{value} hrs/wk", filters["effort"])
            for value in ("1-3", "4-6", "7-10")
        ),
        all_statuses=_option("", "All catalog/progress statuses", filters["status"]),
        status_options="".join(
            _option(value, label, filters["status"])
            for value, label in status_options
        ),
        risk=_text(filters["risk"]),
        all_evidence=_option("", "All detection/evidence states", filters["evidence"]),
        evidence_options="".join(
            _option(value, label, filters["evidence"])
            for value, label in EVIDENCE_FILTERS.items()
        ),
        clear_link=clear_link,
    )


def _source_link(item):
    url = item.get("source_url")
    if not url:
        return '<span class="empty">—</span>'
    return f'<a href="{_text(url)}" rel="noopener noreferrer">Catalog source</a>'


def _item_cell(item):
    official = "yes" if item["official"] is True else "no" if item["official"] is False else "—"
    return """
    <div class="growth-item-cell">
      <strong>{name}</strong>
      <code>{item_id}</code>
      <span>{type} · availability: {availability} · official: {official}</span>
      <p>{practical_value}</p>
      <p><strong>Marketability:</strong> {marketability}</p>
      {source}
    </div>
    """.format(
        name=_display(item["name"]),
        item_id=_display(item["id"]),
        type=_display(item["type"]),
        availability=_display(item["availability"]),
        official=_text(official),
        practical_value=_display(item["practical_value"]),
        marketability=_display(item["marketability"]),
        source=_source_link(item),
    )


def _inventory_facts(item):
    records = []
    for entry in item["_inventory"]:
        records.append(
            """
            <li>
              <strong>{ecosystem} · {source}</strong>
              <span>available {available}; configured {configured}; installed {installed}; enabled {enabled}; referenced {referenced}; scan-evidenced {evidenced}</span>
            </li>
            """.format(
                ecosystem=_display(entry["ecosystem"]),
                source=_display(entry["source"]),
                available=_text(_yes_no(entry["available"])),
                configured=_text(_yes_no(entry["configured"])),
                installed=_text(_yes_no(entry["installed"])),
                enabled=_text(_yes_no(entry["enabled"])),
                referenced=_text(_yes_no(entry["referenced"])),
                evidenced=_text(_yes_no(entry["evidenced"])),
            )
        )
    details = (
        """
        <details class="growth-inventory-details">
          <summary aria-label="Show matched sanitized inventory facts">Matched sanitized inventory ({count})</summary>
          <ul>{records}</ul>
        </details>
        """.format(count=_text(len(records)), records="".join(records))
        if records
        else '<span class="empty">No matched saved inventory record.</span>'
    )
    return """
    <div class="growth-evidence-cell">
      <strong>Detected in saved inventory: {detected}</strong>
      <strong>Evidence artifact exists now: {evidenced}</strong>
      <span>Saved scan said evidenced: {scan_evidenced}</span>
      <p>Available, configured, installed, or enabled never implies evidence or mastery.</p>
      {details}
    </div>
    """.format(
        detected=_text(_yes_no(item["_detected"])),
        evidenced=_text(_yes_no(item["_evidenced"])),
        scan_evidenced=_text(_yes_no(item["_scan_evidenced"])),
        details=details,
    )


def _review_cell(item):
    return """
    <div class="growth-review-cell">
      <code>{review_state}</code>
      <span>Rendered exactly from the reviewed catalog.</span>
      <span>No install approval or blanket safety verdict is inferred.</span>
    </div>
    """.format(review_state=_display(item["review_state"]))


def _risk_facts_cell(item):
    facts = []
    for field in growth_data.RISK_FIELDS:
        facts.append(
            "<div><dt><code>{field}</code></dt><dd>{value}</dd></div>".format(
                field=_text(field),
                value=_display(item["risk_facts"][field]),
            )
        )
    return """
    <details class="growth-risk-details">
      <summary aria-label="Show all risk facts for {name}">12 verbatim risk facts</summary>
      <dl class="growth-risk-facts">{facts}</dl>
    </details>
    """.format(name=_text(item["name"]), facts="".join(facts))


def _proof_action_cell(item):
    return """
    <div class="growth-proof-cell">
      <span><strong>proof_artifact</strong></span>
      <code>{proof_artifact}</code>
      <span>Artifact exists now: {proof_exists}</span>
      <span><strong>next_action</strong></span>
      <p>{next_action}</p>
    </div>
    """.format(
        proof_artifact=_display(item["proof_artifact"]),
        proof_exists=_text(_yes_no(item["_proof_exists"])),
        next_action=_display(item["next_action"]),
    )


def _progress_cell(item, action_token, view):
    control_id = re.sub(r"[^A-Za-z0-9_-]", "-", item["id"])
    if item["_progress_evidence_recorded"]:
        evidence_note = (
            "A personal evidence path is recorded and the artifact exists now."
            if item["_progress_evidence_exists"]
            else "A personal evidence path is recorded, but the artifact is missing now."
        )
        evidence_note += " Leave the field blank to preserve the recorded path."
    else:
        evidence_note = "No personal evidence path is recorded."
    options = [_option("", "Choose status", item.get("_progress_status") or "")]
    options.extend(
        _option(status, status, item.get("_progress_status") or "")
        for status in ("queued", "in_progress", "completed", "skipped")
    )
    return """
    <div class="growth-progress-cell">
      <span>Current: {current}</span>
      <span>{evidence_note}</span>
      <form class="inline-form growth-progress-form" method="post" action="/actions/growth-progress">
        <input type="hidden" name="token" value="{token}">
        <input type="hidden" name="item_id" value="{item_id}">
        <input type="hidden" name="view" value="{view}">
        <label for="growth-progress-{control_id}">Personal progress</label>
        <select id="growth-progress-{control_id}" name="status" required>{options}</select>
        <label for="growth-evidence-{control_id}">Evidence path (optional)</label>
        <input id="growth-evidence-{control_id}" name="evidence" type="text" maxlength="240" autocomplete="off" spellcheck="false" placeholder="reports/growth/proof.md">
        <button type="submit">Update progress</button>
      </form>
    </div>
    """.format(
        current=_display(item.get("_progress_status")),
        evidence_note=_text(evidence_note),
        token=_text(action_token),
        item_id=_text(item["id"]),
        view=_text(view),
        control_id=_text(control_id),
        options="".join(options),
    )


def _growth_rows(items, action_token, view):
    return [
        [
            _item_cell(item),
            _display(item["status"]),
            _display(" / ".join(item["career_lenses"])),
            _display(f'{item["effort_tier"]} hrs/wk'),
            _inventory_facts(item),
            _review_cell(item),
            _proof_action_cell(item),
            _risk_facts_cell(item),
            _progress_cell(item, action_token, view),
        ]
        for item in items
    ]


def _inventory_summary(state, unmatched_count):
    counts = growth_data.inventory_counts(state)
    return """
    <section class="panel growth-inventory-summary" aria-labelledby="growth-inventory-title">
      <h2 id="growth-inventory-title">Saved sanitized inventory</h2>
      <p>These are explicit booleans from the last <code>ai-lab growth scan</code>, not a render-time scan. They may be stale. This page runs no inventory command.</p>
      <dl class="growth-inventory-counts">
        <div><dt>records</dt><dd>{total}</dd></div>
        <div><dt>available</dt><dd>{available}</dd></div>
        <div><dt>configured</dt><dd>{configured}</dd></div>
        <div><dt>installed</dt><dd>{installed}</dd></div>
        <div><dt>enabled</dt><dd>{enabled}</dd></div>
        <div><dt>referenced</dt><dd>{referenced}</dd></div>
        <div><dt>scan-evidenced</dt><dd>{evidenced}</dd></div>
      </dl>
      <p class="empty">{unmatched} unmatched inventory record(s) are counted but their identifiers are not rendered. Use the explicit local CLI to inspect sanitized inventory.</p>
    </section>
    """.format(unmatched=_text(unmatched_count), **{key: _text(value) for key, value in counts.items()})


def _growth(
    query=None,
    *,
    catalog_dir=DEFAULT_GROWTH_CATALOG_DIR,
    state_path=DEFAULT_GROWTH_STATE_PATH,
    repo_root=REPO_ROOT,
    action_token="",
    notice="",
):
    query = query or {}
    requested_view = _query_value(query, "view")
    view = requested_view if requested_view in dict(GROWTH_VIEWS) else "skills"
    catalog_items = growth_data.load_catalogs(catalog_dir)
    state = growth_data.load_state(state_path, repo_root=repo_root)
    all_items, unmatched_count = growth_data.item_views(
        catalog_items,
        state,
        repo_root=repo_root,
    )
    counts = {
        "skills": sum(1 for item in all_items if item["catalog_kind"] == "skill"),
        "extensions": sum(1 for item in all_items if item["catalog_kind"] == "extension"),
        "learning": sum(1 for item in all_items if item["catalog_kind"] == "learning"),
        "inbox": sum(1 for item in all_items if item["_progress_status"]),
    }
    if view == "inbox":
        view_items = [item for item in all_items if item["_progress_status"]]
    else:
        view_items = [item for item in all_items if item["catalog_kind"] == VIEW_KINDS[view]]
    filters = _growth_filter_values(query)
    safe_query = _safe_query(query, view, filters)
    filtered_items = [
        item for item in view_items if _matches_growth_filters(item, filters)
    ]
    sorted_items = _sort_rows(filtered_items, safe_query, GROWTH_SORT_COLUMNS)
    page = _paginate(
        sorted_items,
        safe_query,
        default_page_size=GROWTH_PAGE_SIZE,
    )
    detected_count = sum(1 for item in view_items if item["_detected"])
    evidenced_count = sum(1 for item in view_items if item["_evidenced"])
    notice_html = (
        f'<section class="panel growth-notice" role="status"><p>{_text(notice)}</p></section>'
        if notice
        else ""
    )
    empty_message = (
        "No personal progress items match these filters. Queue an item from Skills, Extensions, or Learning."
        if view == "inbox"
        else "No reviewed catalog items match these filters."
    )
    body = """
    {notice}
    <section class="panel page-intro growth-intro">
      <h2>Growth / Skills Lab</h2>
      <p>Compare cataloged skills, extensions, and learning paths against saved local inventory and repo evidence.</p>
      <p class="empty"><strong>Detected is not evidenced.</strong> Available, configured, installed, enabled, referenced, and evidenced remain separate facts. Catalog priority and metadata review are not install approval.</p>
      <p class="empty">Inbox is the personal progress queue from ignored <code>.local-ai-lab/</code> state. No discovery, install, removal, network, model, or subprocess action runs from this G2 page.</p>
    </section>
    {switcher}
    <section class="grid grid-compact growth-stats">
      {catalog_stat}
      {detected_stat}
      {evidenced_stat}
      {inbox_stat}
    </section>
    {inventory_summary}
    <section class="growth-catalog-section">
      <div class="section-heading-row">
        <div>
          <h2>{heading}</h2>
          <p class="section-note">Risk search is literal across the twelve named risk facts. It does not create or upgrade a risk rating.</p>
        </div>
        <div class="growth-safety-heading">{safe_prompt}</div>
      </div>
      {filters}
      {table}
    </section>
    """.format(
        notice=notice_html,
        switcher=_growth_view_switcher(view, counts),
        catalog_stat=_stat_card("Items in view", len(view_items), "ti-sparkles"),
        detected_stat=_stat_card("Detected", detected_count, "ti-radar"),
        evidenced_stat=_stat_card("Evidenced now", evidenced_count, "ti-checkup-list"),
        inbox_stat=_stat_card("Progress inbox", counts["inbox"], "ti-list-details"),
        inventory_summary=_inventory_summary(state, unmatched_count),
        heading=_text(dict(GROWTH_VIEWS)[view]),
        safe_prompt=_metric_label("Safe?", tip_key="growth_safety", auto=False),
        filters=_growth_filters(filters, view),
        table=(
            _table(
                [
                    "Item",
                    "Priority",
                    "Role",
                    "Effort",
                    "Detected vs evidenced",
                    "Safe? / review_state",
                    "Proof + next action",
                    "Risk facts",
                    "Progress",
                ],
                _growth_rows(page.items, action_token, view),
                empty_message=empty_message,
                table_class="growth-table",
                scroll_controls=True,
                scroll_id="growth-catalog-table-scroll",
                scroll_label="Growth catalog table",
                header_tip_keys={"Safe? / review_state": "growth_safety"},
                sortable_headers=_sortable_headers(
                    "/growth",
                    safe_query,
                    GROWTH_SORT_HEADERS,
                ),
            )
            + _pagination_controls(
                "/growth",
                safe_query,
                page,
                label="Growth catalog pagination",
            )
        ),
    )
    return _layout("Growth / Skills Lab", "/growth", body)


__all__ = (
    "DEFAULT_GROWTH_CATALOG_DIR",
    "DEFAULT_GROWTH_STATE_PATH",
    "GROWTH_PAGE_SIZE",
    "_growth",
    "_growth_filter_values",
    "_growth_view_switcher",
    "_matches_growth_filters",
)
