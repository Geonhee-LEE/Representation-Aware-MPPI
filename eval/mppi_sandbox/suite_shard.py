"""Run the *whole* suite on all cores, instead of running less of it.

The problem this exists for, stated as a number
-----------------------------------------------

The suite costs **1261 s** (D-205's measured price, read off the last receipt by
:func:`cycle_wallclock.suite_price`) against a **35 min** cycle budget.  One run
therefore eats 60% of a cycle, which is why ``receipt_cost.Budget`` reports
``runs_affordable == 1`` and why a cycle that has to re-run after a doc write
(D-043's re-take) is already over budget when it starts.

That is not a hypothetical tax.  Between 2026-08-11 21:00 and 2026-08-12 06:00
**seven consecutive cycles finished work and could not publish it** — the D-112
strand — and 05:00's own post-mortem named the cause without ambiguity: *"no
cycle since 21:00 has finished a full suite, so every diagnosis has been written
from a partial run and inherited as fact."*  Three of the five reds that cycle
inherited were other cycles' misdiagnoses, written in exactly that state.

Why sharding rather than a subset
---------------------------------

The standing proposal (STATE's next-actionable #2, and Q-126 before it) was a
``--fast`` **subset** receipt: run fewer tests, push on the strength of that.
:mod:`receipt_cost` was built to price precisely that and its whole difficulty
is soundness — a subset receipt is a *weaker claim* about the tree, so it needs
an argument that the deselected tests could not have moved, and that argument
has to be re-made every cycle against every diff.

Sharding needs no such argument.  It runs **the same tests on the same tree**
and merely spends 16 cores instead of 1, so the receipt it produces is the
receipt ``push_preflight.check`` already knows how to grade.  The suite's cost
is dominated by guard/census tests that shell out to ``git`` and re-scan the
repo — work that is embarrassingly parallel and currently serialised for no
reason beyond nobody having split it.  D-141 already established the pattern on
this machine: ``calibrate_matrix`` puts 16 cells on 16 cores.

The soundness obligations sharding *does* carry are the ones below, and unlike a
subset's they are properties of the split, checkable once:

* **Partition** — :func:`plan` must emit shards whose union is exactly the
  expanded target set and whose pairwise intersections are empty.  A dropped
  file is a silently smaller suite, which is the subset failure mode arriving
  through the back door.  :func:`plan` raises rather than returning a bad split.
* **Fail closed on an unreadable shard** — :func:`merge_counts` returns ``{}``
  if *any* shard's summary failed to parse, because a merged total computed from
  a subset of the shards is a confident wrong number.  ``{}`` grades
  :data:`push_preflight.VACUOUS`.
* **Any red shard reddens the run** — :func:`merge_returncode` keeps the first
  non-zero, including pytest's ``5`` (collected nothing).

What sharding does *not* preserve, and why it is still safe
-----------------------------------------------------------

Tests that share mutable process-external state can collide when run
concurrently — this suite has ~11 files that build scratch git worktrees or read
repo state.  That risk is not argued away here, it is **measured**: the split is
only adopted because the sharded run reproduces the serial run's
``2516 passed / 157 skipped / 1 xfailed`` exactly.  A collision would show up as
a failure, i.e. in the direction that refuses the push, not one that grants it.
"""

from __future__ import annotations

import os
from pathlib import Path

#: Cap on concurrent pytest processes.  Two cores are left for the executor's
#: own work (git, the editor, this process) — the same reservation the Agent
#: fan-out cap uses, and the reason a 16-core box is not run at 16.
JOBS_RESERVE = 2

#: Never more than this, whatever the machine reports.  Beyond ~16 the shards
#: are short enough that interpreter start-up (~0.6 s each, ×114 files) starts
#: to dominate what is being saved.
JOBS_CEILING = 16


def default_jobs(cpu: int | None = None) -> int:
    """Concurrency to use when the caller did not pick one.

    ``cpu=None`` reads the machine.  Always ``>= 1``, so a single-core box
    degrades to the serial path rather than to zero shards.
    """
    n = cpu if cpu is not None else (os.cpu_count() or 1)
    return max(1, min(JOBS_CEILING, n - JOBS_RESERVE))


def split_args(args) -> tuple[list[str], list[str]]:
    """Separate pytest *path* arguments from flags, preserving order in each.

    Sharding rewrites the paths and must pass the flags through untouched — a
    dropped ``-q`` is cosmetic but a dropped ``--slow`` would change *which
    tests run*, i.e. would turn the split into a subset.  Anything starting with
    ``-`` is a flag; anything else is a target.

    The known-lossy case is a flag that takes its value as a **separate**
    argument (``-k expr``, ``-m expr``, ``-p name``): the value does not start
    with ``-`` and lands here among the paths.  That case is caught in
    :func:`expand_targets` by asking the **filesystem** whether each supposed
    target exists, rather than by carrying a table of which flags take values.

    A typed table is the wrong instrument twice over.  It goes stale as pytest
    grows options — D-047's grep, which hand-copied three of a registry's five
    paths and silently stopped matching the other two — and it is itself a
    module-level allow-list, the shape ``exemption_control`` exists to refuse
    unless something watches it.  The filesystem re-answers the question on
    every run and needs no watcher.
    """
    paths: list[str] = []
    flags: list[str] = []
    for a in args:
        a = str(a)
        if a == "--":
            continue
        (flags if a.startswith("-") else paths).append(a)
    return paths, flags


def expand_targets(paths, root: Path) -> list[str]:
    """Expand pytest path arguments to the individual test files behind them.

    Directories expand to their ``test_*.py`` recursively; explicit files pass
    through.  Returns repo-relative POSIX paths, **sorted** — determinism
    matters because the split is a load-bearing part of what a receipt claims,
    and a run that shards differently every time cannot be reproduced.

    Returns ``[]`` — meaning *do not shard, run this serially* — if any supposed
    target does not exist on disk.  That is the one refusal, and it covers three
    different failures with a single question the tree answers itself:

    * a separate-argument flag value (``-k`` **expr**) that :func:`split_args`
      could not tell from a path,
    * a typo'd target, which must reach pytest intact rather than be silently
      dropped from a shard,
    * a directory holding no ``test_*.py``, where a shard would collect nothing
      and pytest would exit 5.

    Serial is always safe: it is the path that was licensing pushes before this
    module existed.
    """
    out: list[str] = []
    for p in paths:
        full = (root / p) if not Path(p).is_absolute() else Path(p)
        if full.is_dir():
            found = sorted(
                q.relative_to(root).as_posix() for q in full.rglob("test_*.py")
            )
            if not found:
                return []
            out.extend(found)
        elif full.is_file():
            out.append(full.relative_to(root).as_posix())
        else:
            return []
    # dedupe while keeping the sort; a directory arg that also names one of its
    # own files explicitly must not run that file twice (the counts would
    # double-count and the merged total would exceed the real suite).
    return sorted(dict.fromkeys(out))


def file_weight(rel: str, root: Path) -> int:
    """Cost proxy for load balancing: the test file's size in bytes.

    Not runtime.  Runtime would be better and is available in principle from
    ``--durations`` output, but a durations table is a hand-carried measurement
    that goes stale as tests are added — exactly D-047's shape — while size is
    re-read from the tree on every run.  Size is a *proxy* and it is allowed to
    be a bad one: a mis-balanced split is slower, never wrong, so this is the
    one input here that carries no soundness weight.
    """
    try:
        return max(1, (root / rel).stat().st_size)
    except OSError:
        return 1


def plan(files, jobs: int, weights=None) -> list[tuple[str, ...]]:
    """Split *files* into at most *jobs* shards, longest-processing-time first.

    LPT: sort by descending weight, hand each file to the currently lightest
    shard.  Greedy and good enough — the bound is 4/3 of optimal, and the
    quantity being optimised is wall clock, not correctness.

    Raises :class:`ValueError` unless the result is a genuine **partition** of
    the input: same set, no duplicates.  This is the check that keeps sharding
    from degenerating into the subset it exists to avoid, so it is an
    unconditional assertion rather than a test-only one — a partition bug would
    otherwise surface as a green receipt over a suite that quietly shrank.

    Empty shards are dropped, so ``len(result) <= jobs`` and a 3-file request at
    ``jobs=16`` returns 3 shards rather than 3 shards and 13 empty commands
    (pytest exits 5 on an empty target list, which would redden the run).
    """
    files = list(dict.fromkeys(str(f) for f in files))
    if jobs < 1:
        raise ValueError(f"jobs must be >= 1, got {jobs}")
    if not files:
        return []
    w = weights if weights is not None else {f: 1 for f in files}
    buckets: list[list[str]] = [[] for _ in range(jobs)]
    load = [0] * jobs
    for f in sorted(files, key=lambda f: (-w.get(f, 1), f)):
        i = min(range(jobs), key=lambda i: (load[i], i))
        buckets[i].append(f)
        load[i] += w.get(f, 1)
    result = [tuple(sorted(b)) for b in buckets if b]

    flat = [f for b in result for f in b]
    if len(flat) != len(set(flat)) or set(flat) != set(files):
        raise ValueError(
            "shard plan is not a partition of its input: "
            f"{len(files)} in, {len(flat)} out, {len(set(flat) ^ set(files))} differ"
        )
    return result


def merge_counts(per_shard) -> dict[str, int]:
    """Sum the shards' outcome counts, or return ``{}`` if any is unreadable.

    The ``{}`` case is the whole point.  A total summed over the shards that
    *did* parse is a number with no defect visible in it — it looks like a
    smaller but healthy suite — and
    :func:`push_preflight.check` would grade it on ``executed``, which would
    still be large.  Returning ``{}`` routes it to :data:`VACUOUS` instead,
    which refuses.
    """
    per_shard = list(per_shard)
    if not per_shard or any(not c for c in per_shard):
        return {}
    total: dict[str, int] = {}
    for c in per_shard:
        for word, n in c.items():
            total[word] = total.get(word, 0) + int(n)
    return total


def merge_returncode(codes) -> int:
    """First non-zero shard return code, else 0.

    Includes pytest's ``5`` (no tests collected): a shard that collected nothing
    means the split handed it files pytest could not read, and that is a red
    run, not an empty one.
    """
    for c in codes:
        if int(c) != 0:
            return int(c)
    return 0
