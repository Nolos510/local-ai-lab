# Dashboard IA Restructure

Date: 2026-06-26

The model dashboard now uses four primary workflow surfaces:

- Home (`/`): workflow overview, next action, key metrics, top results, and machine context.
- Discover (`/radar`): model radar, specialty candidates, project radar, and candidate security gates.
- My Models (`/inventory`): local runtime inventory, run actions, removal guards, and keep/watch decisions.
- Benchmark (`/runs`): benchmark runs, local artifact imports, comparison tables, and performance charts.

Demoted detail routes remain reachable for continuity: `/lab`, `/capability`, `/specialty`, `/projects`, `/storage`, `/compare`, and `/reports`. They are not primary navigation items.

Reports are exposed as the Export report action (`/reports`) instead of a primary navigation tab.

Safety posture: this IA change adds no runtime dependencies, external assets, network calls, model download/install/run logic, cloud APIs, or secrets. Radar candidates remain metadata records until local benchmark evidence is imported and reviewed.
