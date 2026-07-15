# Dependency Review Gate

Before adding a package, ask whether Python's standard library already covers
the need and whether the package is runtime code or only a development tool.
Review whether it downloads models, calls cloud APIs, requires credentials, or
brings heavy transitive packages. Reject those risks unless the user explicitly
approves a scope change.

If a dependency is accepted, document the exact missing capability, expected
import location, transitive risk, and removal plan. Do not add vendored
packages, ad hoc requirements files, or global install instructions. Python
dependencies remain centralized in `pyproject.toml` and `uv.lock`.
