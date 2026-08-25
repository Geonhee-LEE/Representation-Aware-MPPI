# SPDX-License-Identifier: BSD-3-Clause
"""`source_reach` — the census of `recorded_clearance`'s registry.

The graded claim is narrow on purpose: the scan must find, from source alone,
per-seed ensembles that no registered reader accounts for. Everything else here
protects that claim from the two ways it could quietly stop being true — the
vocabulary narrowing past the registry, and the scan silently reading nothing.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from eval.mppi_sandbox import recorded_clearance, source_reach


def test_scan_reads_the_package_and_is_not_empty():
    """A scan that returns nothing would grade IN_SYNC for the wrong reason."""
    assert len(source_reach.sites()) > 20


def test_ensemble_sites_are_a_subset_of_sites():
    broad = {s.qualname for s in source_reach.sites()}
    narrow = {s.qualname for s in source_reach.ensemble_sites()}
    assert narrow <= broad
    assert narrow, "the vocabulary filtered out every site"


def test_uncovered_is_the_complement_and_is_reported():
    """The blind spot must be a reading, not an assumption (D-318)."""
    broad = {s.qualname for s in source_reach.sites()}
    narrow = {s.qualname for s in source_reach.ensemble_sites()}
    skipped = {s.qualname for s in source_reach.uncovered()}
    assert narrow | skipped == broad
    assert not (narrow & skipped)
    assert skipped, "nothing was filtered — the UNCOVERED line would be a lie"
    assert "UNCOVERED" in source_reach.format_grade()


def test_both_registered_constants_are_found_by_the_scan():
    """The two literal-backed readers must be visible to a source-only scan."""
    found = {s.qualname for s in source_reach.ensemble_sites()}
    assert "clearance_census.SEED_ENSEMBLE" in found
    assert "scene_census.PAIRED_ENSEMBLE" in found


def test_vocabulary_covers_every_registered_constant_backed_source():
    """The narrowing may not stop covering the registry it audits.

    This is what keeps :data:`source_reach.VOCABULARY` honest despite being
    typed: register a reader whose constant falls outside it and this fails.
    """
    assert source_reach.vocabulary_gap() == ()


def test_function_backed_source_is_unscanned_not_convicted():
    """`published_census()` is assembled by a function — reported, not a failure."""
    r = source_reach.reach()
    assert "separation_reproduction.published_census()" in r.unscanned


def test_the_registry_is_still_short_but_not_on_scene_transfer():
    """The finding this module produced, and the half of it that is now paid.

    It was written when `scene_transfer` held per-seed ensembles on five
    scenes and no reader in `recorded_clearance.SOURCES` touched the module.
    Registering it (D-417's demanded follow-up) is what moved
    `cafe_obstacle_crossing_v0` out of "unmeasured", so the headline site is
    asserted here in its *new* class rather than deleted — a test that only
    ever recorded the bug would leave nothing watching the fix.

    The verdict stays `UNREGISTERED`, and that is the point: the census found
    15 modules the registry had never heard of and this cycle registered one.
    A green verdict here would mean the remaining sites had been audited, and
    they have not been.
    """
    r = source_reach.reach()
    assert r.verdict == source_reach.UNREGISTERED
    assert not r.in_sync
    unregistered = {s.qualname for s in r.unregistered}
    # Paid: the module is registered, so its constants are weak evidence now.
    assert "scene_transfer.OBSTACLE_CROSSING_ENSEMBLE" not in unregistered
    assert "scene_transfer.OBSTACLE_CROSSING_ENSEMBLE" in {
        s.qualname for s in r.unnamed}
    # Unpaid: modules the registry still cannot read at all.
    assert any(s.module not in {"separation_reproduction", "clearance_census",
                                "scene_census", "scene_transfer"}
               for s in r.unregistered)


def test_obstacle_crossing_ensemble_is_a_real_seed_ensemble():
    """The headline site is an ensemble by the registry's own MIN_SEEDS rule."""
    from eval.mppi_sandbox import scene_transfer

    rows = scene_transfer.OBSTACLE_CROSSING_ENSEMBLE
    assert scene_transfer.OBSTACLE_CROSSING_SCENE == "cafe_obstacle_crossing_v0"
    assert len(rows) >= 2
    assert all(len(v) >= recorded_clearance.MIN_SEEDS for v in rows.values())


def test_unnamed_is_separated_from_unregistered():
    """A registered module's other constants are weak evidence, not convictions."""
    r = source_reach.reach()
    unnamed = {s.qualname for s in r.unnamed}
    unregistered = {s.qualname for s in r.unregistered}
    assert not (unnamed & unregistered)
    # `published_census()` aggregates these four; the module is registered.
    assert "separation_reproduction.W75_CLEARANCES" in unnamed
    assert all(s.module in {"separation_reproduction", "clearance_census",
                            "scene_census", "scene_transfer"}
               for s in r.unnamed)


def test_row_width_recurses_through_nesting():
    assert source_reach._row_width((0.1, 0.2, 0.3)) == 3
    assert source_reach._row_width({"a": (0.1, 0.2)}) == 2
    # the PAIRED_ENSEMBLE shape: a pair of rows, not a row of width 2
    assert source_reach._row_width({("s", "a"): ((0.1,) * 8, (0.2,) * 8)}) == 8
    assert source_reach._row_width({"a": "not a row"}) == 0
    assert source_reach._row_width((True, False)) == 0, "bools are not clearances"


def test_scan_is_literal_only(tmp_path: Path):
    """Non-literal right-hand sides are skipped rather than imported."""
    (tmp_path / "m.py").write_text(
        textwrap.dedent(
            """
            COMPUTED = dict(a=(0.1, 0.2, 0.3))
            LITERAL_ENSEMBLE = {"a": (0.1, 0.2, 0.3)}
            lower_ensemble = {"a": (0.1, 0.2, 0.3)}
            """
        ),
        encoding="utf-8",
    )
    found = {s.name for s in source_reach.sites(tmp_path)}
    assert found == {"LITERAL_ENSEMBLE"}


def test_a_clean_tree_grades_in_sync(tmp_path: Path):
    """The IN_SYNC branch is reachable — otherwise the verdict is decoration."""
    (tmp_path / "m.py").write_text("SOMETHING = (1.0, 2.0)\n", encoding="utf-8")
    r = source_reach.Reach(found=source_reach.ensemble_sites(tmp_path), declared=())
    assert r.found == ()
    assert r.verdict == source_reach.IN_SYNC
    assert r.in_sync


def test_min_seeds_comes_from_the_registry_not_a_local_copy():
    """D-047: one statement of the threshold, not two."""
    assert source_reach.MIN_SEEDS is recorded_clearance.MIN_SEEDS


def test_main_returns_nonzero_while_the_registry_is_short(capsys):
    assert source_reach.main() == 1
    out = capsys.readouterr().out
    assert "UNREGISTERED" in out
    assert "source reach" in out


@pytest.mark.parametrize("name,expected", [
    ("SEED_ENSEMBLE", True),
    ("W75_CLEARANCES", True),
    ("SHIPPED_ARM_CLEARANCE", True),
    ("DEFAULT_LADDER", False),
    ("ENSEMBLES", False),  # plural-only token is not in the vocabulary
])
def test_vocabulary_membership_is_token_wise_not_substring(name, expected):
    site = source_reach.Site(module="m", name=name, width=8, kind="dict")
    assert site.in_vocabulary is expected
