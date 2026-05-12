# Decisions

## 2026-05-12: Start as One Repo

AI Lab OS starts as one monorepo because the radar, eval harness, dashboard, skills, tasks, and evidence docs share data and context. Separate repos can come later for portfolio-ready tools or security boundaries.

## 2026-05-12: Dependency-Free Dashboard MVP

The Local Model Performance Dashboard uses the Python standard library instead of Streamlit or Flask for the MVP. This keeps setup simple on macOS, avoids dependency installation, and makes validation possible immediately.

## 2026-05-12: SQLite as Dashboard Source of Truth

The dashboard persists data in SQLite under `data/dashboard`. CSV remains the interchange format for fixtures, imports, exports, and future benchmark scripts.

## 2026-05-12: Fixture-First Workflow

The dashboard ships with demo CSV fixtures so the app, tests, and reports work before any real model testing data exists.

## 2026-05-12: No Model Automation in MVP

The MVP tracks model results only. It does not download, install, run, benchmark, or call any AI model.
