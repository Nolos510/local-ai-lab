"""SQLite persistence for the Local Model Performance Dashboard."""

import sqlite3
from pathlib import Path

from .scoring import FINAL_LABELS, SCORE_STATUSES

TABLES = ("models", "model_runs", "eval_scores", "decisions")


def connect(db_path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn):
    label_list = ", ".join(f"'{label}'" for label in FINAL_LABELS)
    status_list = ", ".join(f"'{status}'" for status in SCORE_STATUSES)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY,
            model_name TEXT NOT NULL,
            model_family TEXT,
            provider TEXT,
            params_b REAL,
            license TEXT,
            source_url TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS model_runs (
            id INTEGER PRIMARY KEY,
            model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
            date_tested TEXT NOT NULL,
            backend TEXT NOT NULL,
            format TEXT,
            quantization TEXT,
            context_window INTEGER,
            hardware TEXT,
            temperature REAL,
            top_p REAL,
            tokens_per_sec REAL,
            ttft_seconds REAL,
            total_latency_seconds REAL,
            ram_usage_gb REAL,
            stability_notes TEXT,
            run_notes TEXT
        );

        CREATE TABLE IF NOT EXISTS eval_scores (
            id INTEGER PRIMARY KEY,
            run_id INTEGER NOT NULL UNIQUE REFERENCES model_runs(id) ON DELETE CASCADE,
            instruction_following REAL NOT NULL,
            truthfulness_uncertainty REAL NOT NULL,
            reasoning REAL NOT NULL,
            coding_debugging REAL NOT NULL,
            agent_planning REAL NOT NULL,
            local_ai_lab_usefulness REAL NOT NULL,
            research_synthesis REAL NOT NULL,
            business_seo_strategy REAL NOT NULL,
            long_context REAL NOT NULL,
            creativity REAL NOT NULL,
            speed_practicality REAL NOT NULL,
            total_score REAL NOT NULL,
            final_label TEXT NOT NULL CHECK(final_label IN (__LABELS__)),
            score_status TEXT NOT NULL DEFAULT 'confirmed' CHECK(score_status IN (__STATUSES__))
        );

        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY,
            model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
            decision TEXT NOT NULL,
            keep_installed INTEGER NOT NULL DEFAULT 0 CHECK(keep_installed IN (0, 1)),
            best_use_case TEXT,
            weakness TEXT,
            retest_condition TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_model_runs_model_id ON model_runs(model_id);
        CREATE INDEX IF NOT EXISTS idx_eval_scores_run_id ON eval_scores(run_id);
        CREATE INDEX IF NOT EXISTS idx_decisions_model_id ON decisions(model_id);
        """.replace("__LABELS__", label_list).replace("__STATUSES__", status_list)
    )
    _ensure_eval_score_status(conn)
    _ensure_model_run_perf_fields(conn)
    conn.commit()


def _ensure_eval_score_status(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(eval_scores)").fetchall()}
    if "score_status" not in columns:
        conn.execute(
            """
            ALTER TABLE eval_scores
            ADD COLUMN score_status TEXT NOT NULL DEFAULT 'confirmed'
            CHECK(score_status IN ('confirmed', 'draft'))
            """
        )


def _ensure_model_run_perf_fields(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(model_runs)").fetchall()}
    for column_name in ("ttft_seconds", "total_latency_seconds"):
        if column_name not in columns:
            conn.execute(f"ALTER TABLE model_runs ADD COLUMN {column_name} REAL")


def init_db(db_path, reset=False):
    path = Path(db_path)
    if reset and path.exists():
        path.unlink()
    with connect(path) as conn:
        create_schema(conn)
    return path


def table_count(conn, table_name):
    if table_name not in TABLES:
        raise ValueError(f"Unknown table: {table_name}")
    return conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()["count"]


def database_has_data(db_path):
    path = Path(db_path)
    if not path.exists():
        return False
    with connect(path) as conn:
        create_schema(conn)
        return table_count(conn, "models") > 0


def list_model_summaries(conn):
    return conn.execute(
        """
        SELECT
            m.id,
            m.model_name,
            m.model_family,
            m.provider,
            m.source_url,
            m.params_b,
            r.backend,
            r.quantization,
            r.tokens_per_sec,
            r.ram_usage_gb,
            s.total_score,
            s.final_label,
            s.score_status,
            d.decision,
            d.keep_installed,
            d.best_use_case
        FROM models m
        LEFT JOIN model_runs r ON r.id = (
            SELECT mr.id
            FROM model_runs mr
            WHERE mr.model_id = m.id
            ORDER BY mr.date_tested DESC, mr.id DESC
            LIMIT 1
        )
        LEFT JOIN eval_scores s ON s.run_id = r.id
        LEFT JOIN decisions d ON d.id = (
            SELECT dd.id
            FROM decisions dd
            WHERE dd.model_id = m.id
            ORDER BY dd.created_at DESC, dd.id DESC
            LIMIT 1
        )
        ORDER BY COALESCE(s.total_score, 0) DESC, m.model_name ASC
        """
    ).fetchall()


def get_model_detail(conn, model_id):
    model = conn.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
    if model is None:
        return None
    runs = conn.execute(
        """
        SELECT r.*, s.total_score, s.final_label, s.score_status
        FROM model_runs r
        LEFT JOIN eval_scores s ON s.run_id = r.id
        WHERE r.model_id = ?
        ORDER BY r.date_tested DESC, r.id DESC
        """,
        (model_id,),
    ).fetchall()
    decisions = conn.execute(
        """
        SELECT *
        FROM decisions
        WHERE model_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (model_id,),
    ).fetchall()
    return {"model": model, "runs": runs, "decisions": decisions}


def list_runs(conn):
    return conn.execute(
        """
        SELECT
            r.*,
            m.model_name,
            m.model_family,
            m.provider,
            m.source_url,
            m.params_b,
            s.total_score,
            s.final_label,
            s.score_status
        FROM model_runs r
        JOIN models m ON m.id = r.model_id
        LEFT JOIN eval_scores s ON s.run_id = r.id
        ORDER BY r.date_tested DESC, r.id DESC
        """
    ).fetchall()


def list_score_details(conn):
    return conn.execute(
        """
        SELECT
            m.id AS model_id,
            m.model_name,
            m.provider,
            m.source_url,
            r.backend,
            r.quantization,
            r.tokens_per_sec,
            r.ttft_seconds,
            r.total_latency_seconds,
            s.*
        FROM eval_scores s
        JOIN model_runs r ON r.id = s.run_id
        JOIN models m ON m.id = r.model_id
        ORDER BY s.total_score DESC, m.model_name ASC
        """
    ).fetchall()


def list_decisions(conn):
    return conn.execute(
        """
        SELECT d.*, m.model_name, m.model_family, m.provider, m.source_url
        FROM decisions d
        JOIN models m ON m.id = d.model_id
        ORDER BY d.keep_installed DESC, d.created_at DESC, m.model_name ASC
        """
    ).fetchall()
