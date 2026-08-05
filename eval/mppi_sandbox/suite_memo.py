"""One nested suite run per distinct command, per unchanged tree.

:mod:`nested_run_ledger` measured what the ``slow`` job attempts: **18**
full-suite nested runs across its 6 subject files, falling into **4** distinct
commands.  At the measured 1396 s each that is 419 min against a 120 min
ceiling, and 14 of the 18 runs are a command that was already issued.  This
module removes those 14.

It is a **memo, not a scheduler**.  It makes no equivalence argument: two runs
share a result only when they are the same command over the same inputs on the
same tree, so a hit returns what a re-run would have produced, byte for byte.
That is the whole safety argument, and it is why the key is wide rather than
convenient:

``argv`` + ``cwd``
    what pytest is asked to collect, and from where.

``plugin_digest``
    the recorder's **text**.  Not its name — :mod:`predicate_vacuity` installs
    two different recorders under the single name ``predicate_vacuity_plugin``
    by writing one or the other into a temporary directory on ``PYTHONPATH``.
    An argv-keyed memo would serve an attributed census to a plain one and the
    reading would be wrong in a way no test of either module would notice.

``payload_digest``
    the population the recorder is asked about, which travels in the
    ``PREDICATE_VACUITY_SITES`` environment variable and appears in no argv.

``tree_digest``
    the sources the nested run imports.  Within one session the tree normally
    does not move, but a test that measures, edits a scratch tree, and measures
    again is asking a different question the second time, and a memo that
    cannot see the edit would answer the first question twice.

Two refusals, both failing closed:

* **A failed run is never stored.**  ``produce`` returns ``None`` when the run
  timed out or wrote no dump file; caching that would convert one timeout into
  a permanent one and, worse, hand a caller willing to wait 1800 s a result
  produced under 900 s.  Note that this is ``None`` and *not* ``{}``: a run
  that completed and observed nothing is a **reading**, and is cached like any
  other.  The recorders used to return ``{}`` for both, which is the same
  absence-read-as-a-result shape this package has now named four times
  (``UNPOPULATED``, ``UNRUN``, ``UNCOLLECTED``, ``UNIDENTIFIED``); keying a
  cache on it would have made the conflation permanent instead of momentary.
* **No tree, no cache.**  If the digest scope finds no files there is nothing
  to detect a change with, so the memo declines and every call runs.  An empty
  reading is not a reading — :mod:`exemption_masking`'s ``UNPOPULATED`` and
  :mod:`ci_verdict`'s ``UNRUN``, at the cache layer.

The cache lives for the process.  Nothing is written to disk on purpose: a
fixed on-disk path is precisely the shape that has bitten this branch nine
times, where a stale artifact is indistinguishable from a fresh one to any
check that asks whether a file exists.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

#: Suffixes whose contents can change what a nested suite run observes.  The
#: scenario yamls are in because the sandbox reads them at collection time.
TREE_SUFFIXES: tuple[str, ...] = (".py", ".yaml", ".yml")

#: Directory names never digested — build/run droppings that no import reads.
TREE_SKIP: frozenset[str] = frozenset({"__pycache__", ".git", "runs", ".pytest_cache"})

#: Subdirectories of ``cwd`` that a nested suite run imports from.
TREE_SCOPE: tuple[str, ...] = ("eval",)


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tree_digest(root: Path, scope: Sequence[str] = TREE_SCOPE) -> str | None:
    """Digest of every importable source under ``scope``, or ``None``.

    ``None`` means *nothing was found* and is the refusal signal — see the
    module docstring.  Paths are relative to ``root`` and sorted, so the digest
    is a property of the contents rather than of the walk order.
    """
    root = Path(root)
    files: list[Path] = []
    for name in scope:
        base = root / name
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.suffix not in TREE_SUFFIXES or not path.is_file():
                continue
            if TREE_SKIP & set(path.relative_to(root).parts):
                continue
            files.append(path)
    if not files:
        return None
    h = hashlib.sha256()
    for path in sorted(files):
        h.update(str(path.relative_to(root)).encode("utf-8"))
        h.update(b"\0")
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


@dataclass(frozen=True)
class Command:
    """Everything that decides what a nested suite run produces."""

    argv: tuple[str, ...]
    cwd: str
    plugin_digest: str
    payload_digest: str

    def key(self, tree: str) -> tuple:
        return (self.argv, self.cwd, self.plugin_digest, self.payload_digest,
                tree)


@dataclass
class Stats:
    """What the memo did.  ``runs`` is what was actually spawned."""

    hits: int = 0
    runs: int = 0
    #: Runs that did not complete (``None``), so not stored.
    failures: int = 0
    #: Runs the memo declined to key at all (no tree to digest).
    unkeyed: int = 0

    @property
    def saved(self) -> int:
        return self.hits

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"runs={self.runs} hits={self.hits} "
                f"failures={self.failures} unkeyed={self.unkeyed}")


_CACHE: dict[tuple, dict] = {}
_STATS = Stats()


def stats() -> Stats:
    """A snapshot — mutating it does not touch the memo's own counters."""
    return Stats(**{f.name: getattr(_STATS, f.name)
                    for f in _STATS.__dataclass_fields__.values()})


def clear() -> None:
    """Drop the cache and the counters.  For tests, and for a caller that has
    deliberately changed something the key cannot see."""
    _CACHE.clear()
    for name in _STATS.__dataclass_fields__:
        setattr(_STATS, name, 0)


def run_once(command: Command, produce: Callable[[], dict | None],
             root: Path | None = None) -> dict | None:
    """``produce()`` unless this exact command already ran on this exact tree.

    ``produce`` returns ``None`` for *the run did not complete* and a dict —
    possibly empty — for *this is what it observed*.  Only the second is
    stored.  Returns a deep copy either way, so a caller that mutates its
    result cannot corrupt what a later caller is handed.
    """
    tree = tree_digest(Path(root) if root is not None else Path(command.cwd))
    if tree is None:
        _STATS.unkeyed += 1
        return produce()
    key = command.key(tree)
    if key in _CACHE:
        _STATS.hits += 1
        return copy.deepcopy(_CACHE[key])
    result = produce()
    _STATS.runs += 1
    if result is None:
        _STATS.failures += 1
        return None
    _CACHE[key] = copy.deepcopy(result)
    return result


def _main() -> None:  # pragma: no cover - CLI
    print(stats())


if __name__ == "__main__":  # pragma: no cover - CLI
    _main()
