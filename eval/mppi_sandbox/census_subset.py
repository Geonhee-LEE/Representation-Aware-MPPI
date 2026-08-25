"""Price the census subset against the full suite — Q-159's missing measurement.

The question, and why the obvious answer was refused
---------------------------------------------------

D-280 measured that census pin *repairs* are cheap (``1 : 8.7`` against the
authoring they follow) and that the binding constraint is the **suite**: 11.0
min against a 35 min budget, so a pin-moving cycle pays 22 of 35 minutes in
pytest.  The remedy that seems to follow is a targeted runner — re-run only the
test files that hold census pins, confirm the repair, and spend the full suite
once at the receipt step.

D-280 declined to ship it, for a reason worth restating because it is the whole
point of this module.  The one measurement it could afford timed the census
files **serially** (timed out at 400 s) against a full suite of 659 s at **14
shards**.  Those two numbers are not comparable, so the premise "the subset is
cheap" was neither supported nor refuted.  Shipping the runner on that basis
would have been the exact "inherited claim" failure D-280 was diagnosing.

This module supplies the comparable number: the same files, through the same
:func:`push_preflight.record_sharded` path, at the same job count.

What this module is *not*
-------------------------

It is **not** a receipt producer, and that is enforced structurally rather than
by a warning in prose.  :func:`price` returns a :class:`Price`, not a
:class:`push_preflight.Receipt`, so there is no object here that
``push_preflight.check`` will accept and no way to license a push with a subset
run by mistake.

:mod:`suite_shard`'s preamble argues the soundness case at length and it is not
re-argued here: a subset receipt is a *weaker claim about the tree*, so it needs
an argument that the deselected tests could not have moved, re-made every cycle
against every diff.  Sharding needs no such argument because it runs the same
tests.  A subset is legitimate for **timing** — the question "what would this
cost" is answerable without claiming the tree is green — and illegitimate for
**licensing**.  The type split is where that line lives.

The population is derived, not typed
------------------------------------

:func:`modules` reads :data:`exemption_control.REGISTRIES` and
:func:`files` asks the filesystem which of those modules has a test file.
Neither is a hand-copied list.  D-047 is the standing reason: a typed copy of a
registry is a registry with two statements of itself, and the copy is the one
that goes stale silently.  D-280's own "11 census test files" is an instance —
``REGISTRIES`` holds 11 *registries* but only 9 distinct *modules*, so the file
count was never 11 and nothing was watching the difference.
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from . import suite_shard as ss
from . import tree_provenance as tp
from .exemption_control import REGISTRIES

#: Where a module's test file lives, relative to the repo root.
TEST_DIR = "eval/mppi_sandbox/tests"

#: Verdict words for :func:`verdict`.  Deliberately three, not two: the
#: interesting outcome of Q-159 is the middle one, where the subset is cheaper
#: but not cheaply enough to change how a cycle is planned.
SUBSET_CHEAP = "SUBSET_CHEAP"
SUBSET_MARGINAL = "SUBSET_MARGINAL"
SUBSET_NOT_CHEAP = "SUBSET_NOT_CHEAP"

#: Q-159's own thresholds, quoted from its `다음 action` line: "`< ~3분` 이면
#: (a), full suite 에 근접하면 (b) 또는 (c)".  Kept as the fractions the
#: question actually stated so the verdict is the question's, not this
#: module's.
CHEAP_SECONDS = 180
NEAR_FULL_FRACTION = 0.5


def modules() -> tuple[str, ...]:
    """Distinct modules named by :data:`exemption_control.REGISTRIES`, sorted.

    Distinct **modules**, not registries: ``claim_scope`` and ``suite_memo``
    each contribute two registries, so the 11 entries collapse to 9 owners.
    That collapse is the reason this is a function and not a constant.
    """
    return tuple(sorted({module for module, _ in REGISTRIES}))


def files(root: Path | None = None) -> tuple[str, ...]:
    """Test files holding census pins — repo-relative POSIX, sorted.

    A module with no ``test_<name>.py`` is simply absent from the result.  It is
    *not* an error: the census covers registries, and whether a given registry's
    module happens to own a same-named test file is a fact about the test
    layout.  Raising here would couple the pricing instrument to a naming
    convention it does not control.
    """
    base = Path(str(root or tp.REPO_ROOT))
    found = []
    for name in modules():
        rel = f"{TEST_DIR}/test_{name}.py"
        if (base / rel).is_file():
            found.append(rel)
    return tuple(sorted(found))


@dataclass(frozen=True)
class Price:
    """What a subset run cost.  **Not** a :class:`push_preflight.Receipt`.

    The absence of a ``worktree`` / ``head`` fingerprint is deliberate and is
    the structural half of this module's docstring: a receipt must pin the tree
    it measured so a later reader can tell whether it still applies, and this
    object must never be mistaken for one.  It answers "what would this cost",
    which is a question about the *clock*, not about the tree.
    """

    #: Wall clock of the fan-out, the same quantity
    #: :func:`push_preflight.record_sharded` puts in ``duration_seconds``.
    seconds: float
    #: Files actually run.
    files: tuple[str, ...]
    #: Shard structure, one tuple per concurrent pytest process.
    shards: tuple[tuple[str, ...], ...]
    #: pytest's return code, merged across shards.  Non-zero means the subset
    #: was red — which does not invalidate the *timing*, so this is recorded
    #: rather than raised on.
    returncode: int


def price(root: Path | None = None,
          jobs: int | None = None,
          timeout: int = 1800) -> Price:
    """Run :func:`files` sharded and time it.

    Uses :mod:`suite_shard`'s own ``plan`` at :func:`suite_shard.default_jobs`,
    so the split is built by the same code and the same job count as the full
    suite's.  A subset timed under a *different* concurrency than its control is
    the mistake this module exists to correct; re-implementing the split here
    would reintroduce it one refactor later.
    """
    import concurrent.futures as cf

    base = Path(str(root or tp.REPO_ROOT))
    targets = files(base)
    jobs = ss.default_jobs() if jobs is None else jobs
    weights = {f: ss.file_weight(f, base) for f in targets}
    shards = ss.plan(targets, jobs, weights)

    def run_one(shard):
        return subprocess.run(
            [sys.executable, "-m", "pytest", *shard, "-q"],
            cwd=str(base), capture_output=True, text=True, timeout=timeout,
        )

    began = time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=max(1, len(shards))) as pool:
        procs = list(pool.map(run_one, shards))
    duration = time.monotonic() - began

    rc = next((p.returncode for p in procs if p.returncode != 0), 0)
    return Price(seconds=duration, files=targets,
                 shards=tuple(tuple(s) for s in shards), returncode=rc)


def verdict(subset_seconds: float, full_seconds: float) -> str:
    """Grade a subset price against the full suite's, per Q-159's thresholds.

    ``SUBSET_NOT_CHEAP`` wins ties with ``SUBSET_CHEAP``: a subset that is both
    under :data:`CHEAP_SECONDS` *and* over half the full suite means the full
    suite is itself cheap, and the correct reading is that there is nothing to
    buy — not that the subset is a bargain.
    """
    if full_seconds > 0 and subset_seconds >= NEAR_FULL_FRACTION * full_seconds:
        return SUBSET_NOT_CHEAP
    if subset_seconds < CHEAP_SECONDS:
        return SUBSET_CHEAP
    return SUBSET_MARGINAL


def report(root: Path | None = None) -> str:
    """One-line human reading, for the CLI."""
    from .cycle_wallclock import suite_price

    p = price(root=root)
    full, source = suite_price()
    v = verdict(p.seconds, full)
    return (f"census_subset — {len(p.files)} files in {len(p.shards)} shards: "
            f"{p.seconds:.1f}s (rc={p.returncode}) against a full suite of "
            f"{full}s [{source}] → {v}")


if __name__ == "__main__":  # pragma: no cover - CLI
    print(report())
