"""CSV import/export support for dashboard tables."""

import csv
from pathlib import Path

from . import db
from .scoring import METRIC_FIELDS, normalize_score_record

TABLE_FIELDS = {
    "models": (
        "id",
        "model_name",
        "model_family",
        "provider",
        "params_b",
        "license",
        "source_url",
        "notes",
    ),
    "model_runs": (
        "id",
        "model_id",
        "date_tested",
        "backend",
        "format",
        "quantization",
        "context_window",
        "hardware",
        "temperature",
        "top_p",
        "tokens_per_sec",
        "ttft_seconds",
        "total_latency_seconds",
        "ram_usage_gb",
        "stability_notes",
        "run_notes",
    ),
    "eval_scores": (
        "id",
        "run_id",
        *METRIC_FIELDS,
        "total_score",
        "final_label",
        "score_status",
    ),
    "decisions": (
        "id",
        "model_id",
        "decision",
        "keep_installed",
        "best_use_case",
        "weakness",
        "retest_condition",
        "created_at",
    ),
}

IMPORT_ORDER = ("models", "model_runs", "eval_scores", "decisions")

INTEGER_FIELDS = {"id", "model_id", "run_id", "context_window"}
REAL_FIELDS = {
    "params_b",
    "temperature",
    "top_p",
    "tokens_per_sec",
    "ttft_seconds",
    "total_latency_seconds",
    "ram_usage_gb",
    "total_score",
    *METRIC_FIELDS,
}
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _blank_to_none(value):
    if value is None:
        return None
    value = value.strip()
    return None if value == "" else value


def _coerce_row(table_name, row):
    clean = {field: _blank_to_none(row.get(field)) for field in TABLE_FIELDS[table_name]}
    if table_name == "eval_scores":
        clean = normalize_score_record(clean)
    if table_name == "decisions":
        clean["keep_installed"] = _coerce_bool(clean.get("keep_installed"))

    for field in INTEGER_FIELDS:
        if field in clean and clean[field] is not None:
            clean[field] = int(clean[field])
    for field in REAL_FIELDS:
        if field in clean and clean[field] is not None:
            clean[field] = float(clean[field])
    return clean


def _coerce_bool(value):
    if value in (None, ""):
        return 0
    if isinstance(value, int):
        return 1 if value else 0
    normalized = str(value).strip().lower()
    if normalized in ("1", "true", "yes", "y", "keep"):
        return 1
    if normalized in ("0", "false", "no", "n", "delete"):
        return 0
    raise ValueError(f"Cannot parse boolean value: {value!r}")


def _safe_csv_cell(value):
    if value is None:
        return value
    text = str(value)
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return value


def _insert_row(conn, table_name, row):
    fields = TABLE_FIELDS[table_name]
    placeholders = ", ".join("?" for _ in fields)
    field_list = ", ".join(fields)
    update_fields = [field for field in fields if field != "id"]
    update_list = ", ".join(f"{field} = excluded.{field}" for field in update_fields)
    sql = (
        f"INSERT INTO {table_name} ({field_list}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {update_list}"
    )
    conn.execute(sql, [row.get(field) for field in fields])


def import_table(conn, table_name, csv_path):
    csv_path = Path(csv_path)
    if table_name not in TABLE_FIELDS:
        raise ValueError(f"Unknown table: {table_name}")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        optional = set()
        if table_name == "eval_scores":
            optional.add("score_status")
        if table_name == "model_runs":
            optional.update({"ttft_seconds", "total_latency_seconds"})
        missing = (set(TABLE_FIELDS[table_name]) - optional) - fieldnames
        if missing:
            raise ValueError(
                "{} is missing columns: {}".format(csv_path, ", ".join(sorted(missing)))
            )
        count = 0
        for row in reader:
            _insert_row(conn, table_name, _coerce_row(table_name, row))
            count += 1
    return count


def import_all(db_path, csv_paths):
    db.init_db(db_path, reset=False)
    counts = {}
    with db.connect(db_path) as conn:
        for table_name in IMPORT_ORDER:
            csv_path = csv_paths.get(table_name)
            if csv_path:
                counts[table_name] = import_table(conn, table_name, csv_path)
        conn.commit()
    return counts


def import_fixture_set(db_path, fixture_dir):
    fixture_dir = Path(fixture_dir)
    return import_all(
        db_path,
        {
            "models": fixture_dir / "models.csv",
            "model_runs": fixture_dir / "model_runs.csv",
            "eval_scores": fixture_dir / "eval_scores.csv",
            "decisions": fixture_dir / "decisions.csv",
        },
    )


def export_table(conn, table_name, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{table_name}.csv"
    fields = TABLE_FIELDS[table_name]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        rows = conn.execute(
            "SELECT {} FROM {} ORDER BY id".format(", ".join(fields), table_name)
        ).fetchall()
        for row in rows:
            writer.writerow({field: _safe_csv_cell(row[field]) for field in fields})
    return output_path


def export_all(db_path, output_dir):
    output_paths = {}
    with db.connect(db_path) as conn:
        for table_name in IMPORT_ORDER:
            output_paths[table_name] = export_table(conn, table_name, output_dir)
    return output_paths
