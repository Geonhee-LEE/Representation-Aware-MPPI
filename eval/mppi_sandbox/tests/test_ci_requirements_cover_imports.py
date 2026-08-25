"""Every third-party module `eval/` imports must be declared in requirements-ci.txt.

Why this exists (2026-08-25). `eval/mppi_sandbox/essps.py` imported
`scipy.optimize` at module scope while `eval/requirements-ci.txt` never listed
scipy. The dev box had scipy installed ambiently, so the local suite was green
(4196 passed) on the exact commit whose CI was red — CI died at *collection*
with `ModuleNotFoundError: No module named 'scipy'`, aborting whole shards
("4146 deselected, 3 errors"). A red PR cannot be merged, and an unmergeable PR
is one the review queue cannot drain, so the omission fed directly into the
gate-1 stall.

The failure is invisible to every check this package already runs, because they
all execute on a box where the import happens to succeed. It is only observable
by comparing the *declared* environment against the *imported* one — which is
what this test does, and why it is a derivation rather than a hand-kept list
(D-047: a registry should have exactly one statement of itself).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

EVAL_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = EVAL_ROOT / "requirements-ci.txt"

# Import name -> distribution name, for the cases where they differ.
_DISTRIBUTION_ALIASES = {"yaml": "pyyaml"}

# First-party top-level packages: these resolve from the repo, not from pip.
_FIRST_PARTY = {"eval", "learning", "scripts"}


def _declared_distributions() -> set[str]:
    """Parse requirements-ci.txt into a set of lowercased distribution names."""
    declared = set()
    for raw in REQUIREMENTS.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        # Split off any version specifier: name==1.2.3, name>=1,<2, name
        name = line
        for spec in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            name = name.split(spec, 1)[0]
        name = name.strip()
        if name:
            declared.add(name.lower())
    return declared


def _module_scope_imports(node: ast.AST):
    """Yield Import/ImportFrom nodes that execute when the module is imported.

    Deliberately does NOT descend into function bodies. The distinction is the
    whole point of this test: a module-scope import runs at *collection* time
    and takes the entire pytest shard down with it, while a deferred import
    inside a function only runs if that function is called. `eval/run_metrics.py`
    imports rclpy/nav_msgs/std_srvs inside a factory precisely so the module
    stays importable without ROS on the box, and `guard_vacuity.py` defers
    `coverage` the same way — those are correct and must not be flagged.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if isinstance(child, (ast.Import, ast.ImportFrom)):
            yield child
        # Class bodies, if/try/with blocks at module scope DO execute on import.
        yield from _module_scope_imports(child)


def _imported_top_level_modules() -> dict[str, list[str]]:
    """Map each module-scope-imported top-level module -> the eval/ files doing it."""
    imports: dict[str, list[str]] = {}
    for path in sorted(EVAL_ROOT.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError:  # pragma: no cover - a broken file is another test's problem
            continue
        rel = str(path.relative_to(EVAL_ROOT.parent))
        for node in _module_scope_imports(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                # level > 0 is a relative import — first-party by construction.
                if node.level:
                    continue
                names = [node.module] if node.module else []
            for dotted in names:
                top = dotted.split(".", 1)[0]
                imports.setdefault(top, []).append(rel)
    return imports


def _third_party(imports: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        module: files
        for module, files in imports.items()
        if module not in sys.stdlib_module_names
        and module not in _FIRST_PARTY
        and not module.startswith("_")
    }


def test_requirements_file_exists():
    assert REQUIREMENTS.is_file(), f"{REQUIREMENTS} is the environment CI installs"


def test_every_third_party_import_is_declared():
    declared = _declared_distributions()
    third_party = _third_party(_imported_top_level_modules())

    undeclared = {}
    for module, files in sorted(third_party.items()):
        distribution = _DISTRIBUTION_ALIASES.get(module, module).lower()
        if distribution not in declared:
            undeclared[module] = sorted(set(files))[:4]

    assert not undeclared, (
        "eval/ imports modules that eval/requirements-ci.txt does not declare, so "
        "CI will die at collection while this box (which has them installed "
        "ambiently) stays green:\n"
        + "\n".join(
            f"  {module!r} imported by {', '.join(files)}"
            for module, files in undeclared.items()
        )
        + f"\ndeclared: {sorted(declared)}"
    )


def test_scipy_specifically_is_declared():
    """Regression pin for the 2026-08-25 outage — scipy is the module that did it."""
    imports = _imported_top_level_modules()
    assert "scipy" in imports, (
        "scipy is no longer imported anywhere in eval/. If that removal was "
        "deliberate, drop this test and the scipy pin together."
    )
    assert "scipy" in _declared_distributions(), (
        "scipy is imported by eval/ but absent from requirements-ci.txt — this is "
        "the exact omission that made every Sandbox CI run red while the local "
        "receipt read green."
    )


@pytest.mark.parametrize("module", ["numpy", "yaml", "pytest"])
def test_known_dependencies_stay_declared(module):
    distribution = _DISTRIBUTION_ALIASES.get(module, module)
    assert distribution in _declared_distributions()
