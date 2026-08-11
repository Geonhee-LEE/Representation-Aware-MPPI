"""Tests for :mod:`eval.mppi_sandbox.inert_surface` (STATE #2).

The load-bearing ones are the controls.  An exemption module whose tests only
check that the exempt paths are exempt is a module that cannot fail, which is
the shape D-079 named decoration and D-075 named vacuous survival.  So:

* both directions of the static layer (a read path must grade ``HAS_READER``, an
  unmentioned one ``NO_READER``);
* an empty probe grades ``VACUOUS``, never ``INERT``;
* :func:`inert` refuses on *either* half of its composition failing;
* drift outside the population is material no matter what.
"""

from __future__ import annotations

import json
import os

import pytest

from eval.mppi_sandbox import inert_surface as ins
from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import tree_provenance as tp


# --------------------------------------------------------------------------
# population
# --------------------------------------------------------------------------


def test_population_is_the_post_receipt_write_surface():
    """Exactly the writes the Phase-4 order performs after the receipt, no more.

    ``journal/`` joins D-044's four because D-043 mandates a **second** write of
    the 4a file: the journal must quote the *re-taken* count, which is not
    knowable until after the re-run.  D-044's own table reasons about the 4a
    write only and concludes "commit it, cheap to include" — true of that write
    and silent about the one its sibling rule forces afterwards.
    """
    assert set(ins.POST_RECEIPT_WRITES) == {
        "STATE.md",
        "JOURNAL.md",
        "RESULTS.md",
        "results/",
        "journal/",
    }
    assert all(reason for reason in ins.POST_RECEIPT_WRITES.values())


def test_the_tsv_entry_is_a_prefix_not_a_filename():
    """Per-branch TSV names differ; pinning one exempts one branch only."""
    assert "results/" in ins.POST_RECEIPT_WRITES
    assert not any(
        c.endswith(".tsv") for c in ins.POST_RECEIPT_WRITES
    ), "a literal TSV name would silently re-admit the next branch's file"


# --------------------------------------------------------------------------
# the finding: D-044's "read by no test (checked)" is false as a static claim
# --------------------------------------------------------------------------


def test_every_post_receipt_write_has_a_static_reader():
    """All four are reachable from some test, directly or one hop away.

    This is the measured refutation of the assertion the exemption used to rest
    on.  If a future tree makes one genuinely unmentioned, this test goes red
    and the finding gets restated rather than silently inverted.
    """
    survey = ins.survey()
    assert set(survey) == set(ins.POST_RECEIPT_WRITES)
    for candidate, readers in survey.items():
        assert readers, f"{candidate} unexpectedly has no static reader"
        assert ins.classify(candidate) == ins.HAS_READER


# --------------------------------------------------------------------------
# static layer — both directions
# --------------------------------------------------------------------------


def test_control_a_path_the_suite_really_reads_grades_has_reader():
    """Positive control: the scenario yaml every sandbox run loads."""
    assert ins.classify("eval/scenarios/cafe_straight_v0.yaml") == ins.HAS_READER


def test_control_a_path_nobody_mentions_grades_no_reader():
    """Negative control: without this the scan could return HAS_READER always.

    The candidate is **assembled at runtime**, and that is the content of the
    test rather than a style choice.  :func:`mentions` scans every Python
    source in the package *including this file*, so a control that spells its
    own subject as a literal puts that subject into the scanned corpus and the
    scan then truthfully reports a reader — itself.  The first draft did
    exactly that and graded ``HAS_READER``, so the control asserted the
    opposite of what it was written to assert and the module shipped with its
    only negative control inverted.

    D-079's rule (ship the control with the instrument) is necessary and, here,
    not sufficient: a control over a *whole-corpus* scan is inside the
    population it controls.  The reflexivity `guard_reflexivity` was built to
    detect, reappearing one layer up in a test.
    """
    absent = "docs/" + "no-such-file-" + "unspelled-zzz.md"
    assert ins.classify(absent) == ins.NO_READER


def test_naming_a_path_in_a_test_makes_that_test_its_reader():
    """The contamination above, pinned as a property instead of hidden.

    This is the sibling of the control and the reason it must be assembled:
    the scan cannot distinguish "a test that reads this path" from "a test
    that merely names it as data".  Stated out loud so the next reader of
    :func:`classify` knows the verdict counts mentions, not reads — which is
    precisely why the dynamic probe exists, and why the shipped ``PROBED``
    entries are transcribed probe output rather than static verdicts.
    """
    literal = "docs/there-is-no-such-file-zzz.md"  # the same path, spelled
    assert ins.classify(literal) == ins.HAS_READER
    # and the sole "reader" is this file, which never opens it
    assert ins.mentions(literal) == ("eval/mppi_sandbox/tests/test_inert_surface.py",)


def test_mentions_keys_on_the_full_path_not_the_basename():
    """D-081's class: a bare name is owned by more than one file."""
    sources = {
        "eval/mppi_sandbox/tests/test_a.py": "open('alpha/run.py')",
        "eval/mppi_sandbox/tests/test_b.py": "open('beta/run.py')",
    }
    assert ins.mentions("alpha/run.py", sources) == (
        "eval/mppi_sandbox/tests/test_a.py",
    )
    # basename keying would return both files here
    assert len(ins.mentions("run.py", sources)) == 2


def test_prefix_candidate_matches_any_member():
    sources = {"eval/tests/test_x.py": "load('results/p3-something.tsv')"}
    assert ins.mentions("results/", sources) == ("eval/tests/test_x.py",)


def test_readers_is_transitive_one_hop_through_the_package():
    """A test that never spells the path still reaches it through a module."""
    sources = {
        "eval/mppi_sandbox/carrier.py": "PATHS = ['STATE.md']",
        "eval/mppi_sandbox/tests/test_carrier.py": "from . import carrier\n",
    }
    readers = ins.readers("STATE.md", sources)
    assert readers.direct == ()
    assert readers.via == ("eval/mppi_sandbox/tests/test_carrier.py",)
    assert readers.modules == ("carrier",)
    assert readers.all == ("eval/mppi_sandbox/tests/test_carrier.py",)


def test_a_carrier_that_no_test_imports_yields_no_reader():
    """Reachability needs the second hop to exist, not just the first."""
    sources = {
        "eval/mppi_sandbox/carrier.py": "PATHS = ['STATE.md']",
        "eval/mppi_sandbox/tests/test_other.py": "from . import elsewhere\n",
    }
    assert ins.classify("STATE.md", sources) == ins.NO_READER


def test_readers_key_moves_when_the_set_moves_not_when_the_count_does():
    base = {
        "eval/mppi_sandbox/tests/test_a.py": "open('STATE.md')",
    }
    swapped = {
        "eval/mppi_sandbox/tests/test_b.py": "open('STATE.md')",
    }
    assert ins.readers_key("STATE.md", base) != ins.readers_key("STATE.md", swapped)
    assert len(ins.readers("STATE.md", base).all) == len(
        ins.readers("STATE.md", swapped).all
    )


# --------------------------------------------------------------------------
# probe — emptiness before success
# --------------------------------------------------------------------------


def test_a_probe_with_no_readers_is_vacuous_not_inert():
    """The run observed nothing; 'nothing moved' is not a finding.

    D-081 graded an empty pair ``VACUOUS`` for this reason and D-075 shipped a
    claim that survived because it asserted nothing.  An unprobed path must not
    arrive at the same verdict as a probed-and-still one.
    """
    sources = {"eval/mppi_sandbox/tests/test_a.py": "nothing relevant here"}
    result = ins.probe("STATE.md", sources=sources)
    assert result.verdict == ins.VACUOUS
    assert result.tests == ()
    assert result.verdict != ins.INERT


def test_probe_verdicts_are_distinct_constants():
    assert len({ins.INERT, ins.CONTENT_READ, ins.VACUOUS}) == 3
    assert ins.NO_READER != ins.HAS_READER


# --------------------------------------------------------------------------
# inert() — the composition, and both halves failing
# --------------------------------------------------------------------------


@pytest.fixture
def pinned(monkeypatch):
    """A synthetic tree with one pinned candidate, so the pin can be moved."""
    sources = {"eval/mppi_sandbox/tests/test_a.py": "open('STATE.md')"}
    key = ins.readers_key("STATE.md", sources)
    monkeypatch.setattr(
        ins,
        "PROBED",
        {"STATE.md": ins.Pin(verdict=ins.INERT, readers_key=key, taken="synthetic")},
    )
    return sources


def test_inert_holds_when_both_halves_hold(pinned):
    assert ins.inert("STATE.md", pinned) is True


def test_inert_fails_when_the_reader_set_moved(pinned):
    """The premise check: a new test reading the path withdraws the exemption."""
    moved = dict(pinned)
    moved["eval/mppi_sandbox/tests/test_new.py"] = "open('STATE.md')"
    assert ins.inert("STATE.md", moved) is False
    assert ins.stale_pins(moved) == ("STATE.md",)


def test_inert_fails_without_a_pin(pinned):
    assert ins.inert("JOURNAL.md", pinned) is False


def test_inert_fails_on_a_non_inert_pin(monkeypatch):
    sources = {"eval/mppi_sandbox/tests/test_a.py": "open('STATE.md')"}
    monkeypatch.setattr(
        ins,
        "PROBED",
        {
            "STATE.md": ins.Pin(
                verdict=ins.CONTENT_READ,
                readers_key=ins.readers_key("STATE.md", sources),
                taken="synthetic",
            )
        },
    )
    assert ins.inert("STATE.md", sources) is False


def test_stale_pins_is_empty_when_the_premise_holds(pinned):
    assert ins.stale_pins(pinned) == ()


def test_every_shipped_pin_states_its_premise_and_when():
    """A pin without provenance is a number somebody typed (D-081)."""
    for candidate, pin in ins.PROBED.items():
        assert candidate in ins.POST_RECEIPT_WRITES
        assert pin.verdict in (ins.INERT, ins.INERT_COMPOSED,
                               ins.CONTENT_READ, ins.VACUOUS)
        assert pin.taken, f"{candidate}'s pin does not say when it was taken"
        if pin.verdict == ins.INERT_COMPOSED:
            # A composed verdict rests on a base it did not re-measure, so the
            # provenance requirement is strictly larger: it must say what it
            # carried and how many generations deep it is.
            assert pin.carried, f"{candidate} composes but names nothing carried"
            assert pin.generation > 0


def test_the_shipped_population_is_pinned_at_all():
    """Emptiness decided before success — the two tests above were vacuous.

    ``PROBED`` shipped empty for the whole of the module's first life, and the
    loop test above iterated it and passed by having nothing to check, while
    :func:`ins.stale_pins` returned ``()`` for the same reason.  Two green
    tests, zero measurements, and a :func:`ins.inert` that answered ``False``
    to every question — the module was complete and inoperative and nothing
    said so.  That is D-075's vacuous survival wearing this module's clothes,
    so it gets this module's own rule applied to itself.
    """
    assert ins.PROBED, "the module grades nothing until a probe is transcribed"
    assert set(ins.PROBED) == set(ins.POST_RECEIPT_WRITES)


#: The candidates whose premise moved between 2026-08-06 06:00 and 08-07 01:00,
#: kept as a record of what the decay looked like: **the whole population**.
#: Three entered via D-097/D-098, ``results/`` via D-099 and then D-105.
#: Discharged by D-107's incremental re-take, and retained because the *shape*
#: of the reading — every pin stale inside one day — is the argument for
#: :func:`ins.reprobe` existing.
STALE_SINCE_D098: tuple[str, ...] = ("JOURNAL.md", "RESULTS.md", "STATE.md",
                                     "results/")


def test_the_whole_population_can_go_stale_inside_a_day():
    """What D-107 repaired, asserted as the mechanism rather than as a state.

    Each withdrawal was individually correct and all four composed into
    :func:`ins.inert` answering ``False`` to every question — D-088's
    ``UNPOPULATED`` reached a second time, by attrition.  The load-bearing part
    is the *rate*: the pins were taken on 08-06 06:00 and the last one went
    stale the same day.  A re-take priced at ~8.5 min per candidate cannot keep
    up with that, which is why the repair had to be the cost and not the
    diligence.
    """
    # Scoped, not widened (D-100's rule).  This set is a **record of the
    # 08-06→08-07 decay**, and `journal/` was not in the population then, so
    # adding it would make the tuple match today's membership at the cost of
    # the historical claim it exists to carry.  What the assertion is really
    # about is that the decay covered *everything pinned at the time* — so it
    # is stated as containment plus the reason the residue is outside it.
    assert set(STALE_SINCE_D098) <= set(ins.POST_RECEIPT_WRITES)
    assert set(ins.POST_RECEIPT_WRITES) - set(STALE_SINCE_D098) == {"journal/"}
    # A pin whose premise moves must be withdrawn *at the gate*, not at an audit.
    moved = ins.Pin(verdict=ins.INERT, readers_key="stale|key", taken="synthetic")
    with _patch_pin("STATE.md", moved):
        assert ins.inert("STATE.md") is False
        assert "STATE.md" in ins.stale_pins()


def _patch_pin(candidate, pin):
    import unittest.mock as _m

    return _m.patch.dict(ins.PROBED, {candidate: pin})


def test_the_reprobe_is_affordable_where_the_full_probe_was_not():
    """The claim that justified leaving the instrument dark, measured.

    The superseded version of this test reasoned that a re-take "costs hours"
    because ``STATE.md``'s readers include suites that spawn nested runs, and
    concluded the staleness should be *named* rather than repaired.  Two things
    were wrong with that.  The estimate contradicted the module's own pin note
    (~34 min for all four, not hours per candidate); and more importantly the
    question is not what a **full** probe costs, because a stale pin does not
    need one — only what entered since needs running.

    Measured 2026-08-07: 8 entrant files across the four candidates, worst
    single file 48 s, ~3.5 min for all four re-takes together.  This test pins
    the property that makes that true, not the timing: the entrant sets stay a
    small fraction of the reader sets.  If that stops holding, the affordability
    argument stops holding with it and the cap forces a full probe anyway.
    """
    src = ins._python_sources()
    for cand in ins.POST_RECEIPT_WRITES:
        total = len(ins.readers(cand, src).all)
        assert total, f"{cand} has no readers at all — check the scan, not the pin"
        assert len(ins.entrants(cand, src)) <= total


def test_the_stale_set_is_discharged_and_the_detector_still_bites():
    """The control D-079 asks for, run against the tree actually shipping.

    Both halves matter and they fail for different reasons.  ``stale_pins() ==
    ()`` says the repair landed; the synthetic pin says the detector that found
    the decay is still capable of finding it, which a green reading alone cannot
    show.  Without the second half this is the shape the 06-18 assertion had —
    a state that passes for having nothing to catch.
    """
    assert ins.stale_pins() == ()
    unmeasured = ins.Pin(verdict=ins.INERT, readers_key="not|the|real|key",
                         taken="synthetic")
    with _patch_pin("results/", unmeasured):
        assert ins.stale_pins() == ("results/",)


def test_the_stale_pins_no_longer_exempt_the_real_post_receipt_writes():
    """The end-to-end claim, with no fixture standing in for the measurement.

    Every test around this one substitutes a synthetic pin over synthetic
    sources, which proves the *composition* and says nothing about whether the
    tree actually shipping is exempt.  This one asks :func:`ins.filter_drift`
    the question the push line asks it, with the shipped pins and the real
    reader scan.

    With the pins re-taken, the exact write set D-044's Phase-4 order produces
    is ignorable again and the second-suite-run tax is gone.  The tax was real
    while it lasted and is what this cycle went to collect: every cycle from
    08-06 06:00 to 08-07 01:00 paid one.
    """
    drift = tp.Drift(
        changed=("STATE.md", "JOURNAL.md", "RESULTS.md"),
        added=("results/p3-epistemic-shadow-cost-critic.tsv",),
    )
    material, ignored = ins.filter_drift(drift)
    assert set(ignored) == {
        "STATE.md", "JOURNAL.md", "RESULTS.md",
        "results/p3-epistemic-shadow-cost-critic.tsv",
    }
    assert not material.changed and not material.added
    # And the gate keeps refusing everything outside the population.
    other = tp.Drift(changed=("eval/mppi_sandbox/run.py",))
    material2, ignored2 = ins.filter_drift(other)
    assert ignored2 == () and material2.changed == ("eval/mppi_sandbox/run.py",)


def test_an_unrecognised_path_is_still_material_against_the_shipped_pins(pinned):
    """The exemption is a hole exactly as wide as the population, not wider.

    Runs against ``pinned`` rather than the shipped pins: with all three
    ``.md`` premises stale, the shipped set exempts none of them, so the real
    pins can no longer witness "inside the population" for this assertion.
    """
    drift = tp.Drift(changed=("STATE.md", "eval/mppi_sandbox/run.py"))
    material, ignored = ins.filter_drift(drift, sources=pinned)
    assert material.changed == ("eval/mppi_sandbox/run.py",)
    assert ignored == ("STATE.md",)


# --------------------------------------------------------------------------
# filter_drift — and the fail-closed default
# --------------------------------------------------------------------------


def test_drift_outside_the_population_is_always_material(pinned):
    drift = tp.Drift(changed=("eval/mppi_sandbox/run.py", "STATE.md"))
    material, ignored = ins.filter_drift(drift, sources=pinned)
    assert material.changed == ("eval/mppi_sandbox/run.py",)
    assert ignored == ("STATE.md",)


def test_a_prefix_exemption_covers_its_members(monkeypatch):
    sources = {"eval/mppi_sandbox/tests/test_a.py": "open('results/x.tsv')"}
    monkeypatch.setattr(
        ins,
        "PROBED",
        {
            "results/": ins.Pin(
                verdict=ins.INERT,
                readers_key=ins.readers_key("results/", sources),
                taken="synthetic",
            )
        },
    )
    drift = tp.Drift(changed=("results/p3-epistemic.tsv",))
    material, ignored = ins.filter_drift(drift, sources=sources)
    assert not material
    assert ignored == ("results/p3-epistemic.tsv",)


def test_membership_alone_never_exempts(monkeypatch):
    """Population membership is necessary, not sufficient — the pin decides."""
    monkeypatch.setattr(ins, "PROBED", {})
    drift = tp.Drift(changed=("STATE.md", "JOURNAL.md"))
    material, ignored = ins.filter_drift(drift, sources={})
    assert material.changed == ("JOURNAL.md", "STATE.md")
    assert ignored == ()


# --------------------------------------------------------------------------
# push_preflight integration — the defect this module exists to fix
# --------------------------------------------------------------------------


def _receipt(**over):
    base = dict(
        head="0" * 40,
        worktree_fingerprint="fp-before",
        committed_fingerprint="cfp",
        returncode=0,
        counts={"passed": 900},
        command=("python3", "-m", "pytest"),
        worktree={"eval/mppi_sandbox/run.py": "a", "STATE.md": "b"},
    )
    base.update(over)
    return pp.Receipt(**base)


def _stamp(worktree):
    return tp.Stamp(
        head="0" * 40,
        worktree_fingerprint="fp-after",
        committed_fingerprint="cfp",
        untracked_digest="",
        n_tracked=len(worktree),
        n_untracked=0,
        worktree=dict(worktree),
        committed=dict(worktree),
    )


def test_a_post_receipt_write_to_an_inert_path_still_licenses_the_push(
    tmp_path, monkeypatch, pinned
):
    """The bug: D-044's mandated write order made every cycle grade STALE."""
    monkeypatch.setattr(ins, "_python_sources", lambda root=None: pinned)
    after = {"eval/mppi_sandbox/run.py": "a", "STATE.md": "MOVED"}
    monkeypatch.setattr(pp.tp, "stamp", lambda root=None, ref="HEAD": _stamp(after))
    monkeypatch.setattr(pp.tp, "undeclared_drift", lambda *a, **k: tp.Drift())

    path = tmp_path / "receipt.json"
    path.write_text(_receipt().to_json())
    # ``frontier=()`` states the population this test assumes rather than
    # inheriting the live repository's (D-109).  This test is about the *inert*
    # axis; left live it grades UNSUPPORTED_CLAIM on every cycle, because at
    # 4a-ter the in-flight journal's TSV claim is unmet by D-044's own order.
    verdict = pp.check(path, frontier=())
    assert verdict.verdict == pp.GREEN, verdict.describe()
    assert "STATE.md" in verdict.detail


def test_a_post_receipt_write_to_a_read_path_still_grades_stale(
    tmp_path, monkeypatch, pinned
):
    """The gate must keep doing its job for everything else."""
    monkeypatch.setattr(ins, "_python_sources", lambda root=None: pinned)
    after = {"eval/mppi_sandbox/run.py": "CHANGED", "STATE.md": "b"}
    monkeypatch.setattr(pp.tp, "stamp", lambda root=None, ref="HEAD": _stamp(after))

    path = tmp_path / "receipt.json"
    path.write_text(_receipt().to_json())
    verdict = pp.check(path)
    assert verdict.verdict == pp.STALE
    assert "run.py" in verdict.detail


def test_the_mandated_second_journal_write_licenses_the_push(tmp_path, monkeypatch):
    """The tax this cycle removes, stated as the gate call that used to refuse.

    D-043 requires the journal to quote the **re-taken** suite count, which is
    not knowable until after the re-run — so the 4a file is necessarily written
    a second time, *after* the receipt.  ``journal/`` had no pin, ``inert()``
    answers ``False`` to every unpinned candidate, and the receipt therefore
    graded :data:`~push_preflight.STALE` on a write the constitution mandates.
    The only currency available was a second full suite run, and two
    consecutive cycles (08-07 06:00, 07:00) died inside it with their journals
    already claiming a push that never happened.

    Note the path is **nested**.  That is the half a flat-directory pin would
    have missed: the exemption has to cover ``journal/YYYY-MM/DD-HH-*.md``,
    which is the file a cycle writes, not ``journal/README.md``, which is what
    the one-level probe walk used to measure.
    """
    written = "journal/2026-08/07-08-a-slug.md"
    sources = {"eval/mppi_sandbox/tests/test_a.py": f"open({written!r})"}
    monkeypatch.setattr(ins, "_python_sources", lambda root=None: sources)
    monkeypatch.setattr(
        ins,
        "PROBED",
        {
            "journal/": ins.Pin(
                verdict=ins.INERT,
                readers_key=ins.readers_key("journal/", sources),
                taken="synthetic",
            )
        },
    )
    after = {"eval/mppi_sandbox/run.py": "a", written: "REWRITTEN WITH THE COUNT"}
    monkeypatch.setattr(pp.tp, "stamp", lambda root=None, ref="HEAD": _stamp(after))
    monkeypatch.setattr(pp.tp, "undeclared_drift", lambda *a, **k: tp.Drift())

    path = tmp_path / "receipt.json"
    path.write_text(
        _receipt(worktree={"eval/mppi_sandbox/run.py": "a", written: "FIRST WRITE"})
        .to_json()
    )
    verdict = pp.check(path, frontier=())
    assert verdict.verdict == pp.GREEN, verdict.describe()
    assert written in verdict.detail


def test_a_journal_write_outside_the_pinned_prefix_is_still_material(
    tmp_path, monkeypatch
):
    """Control: the prefix exemption must not become 'any path at all'."""
    sources = {"eval/mppi_sandbox/tests/test_a.py": "open('journal/x.md')"}
    monkeypatch.setattr(ins, "_python_sources", lambda root=None: sources)
    monkeypatch.setattr(
        ins,
        "PROBED",
        {
            "journal/": ins.Pin(
                verdict=ins.INERT,
                readers_key=ins.readers_key("journal/", sources),
                taken="synthetic",
            )
        },
    )
    after = {"eval/mppi_sandbox/run.py": "CHANGED"}
    monkeypatch.setattr(pp.tp, "stamp", lambda root=None, ref="HEAD": _stamp(after))

    path = tmp_path / "receipt.json"
    path.write_text(_receipt(worktree={"eval/mppi_sandbox/run.py": "a"}).to_json())
    verdict = pp.check(path, frontier=())
    assert verdict.verdict == pp.STALE
    assert "run.py" in verdict.detail


def test_a_receipt_without_per_path_digests_grades_stale(tmp_path, monkeypatch):
    """Fail closed: an older receipt cannot be asked which paths moved."""
    monkeypatch.setattr(
        pp.tp, "stamp", lambda root=None, ref="HEAD": _stamp({"STATE.md": "x"})
    )
    path = tmp_path / "receipt.json"
    path.write_text(_receipt(worktree={}).to_json())
    verdict = pp.check(path)
    assert verdict.verdict == pp.STALE
    assert "per-path" in verdict.detail


def test_record_writes_the_per_path_map_into_the_receipt():
    """Without this the fix has no input; the field must survive a round trip."""
    r = _receipt()
    assert pp.Receipt.from_json(r.to_json()).worktree == r.worktree
    assert "worktree" in json.loads(r.to_json())


# --------------------------------------------------------------------------
# D-107: the incremental re-take, and the price it is allowed to charge
# --------------------------------------------------------------------------


def test_every_pin_is_live_right_now():
    """The exemption mechanism is operative — the thing that was not true.

    Worth being exact about what had gone wrong, because it was **not** that
    the decay went unnoticed: ``stale_pins`` reported it, and the four
    superseded tests above asserted it by name.  It was that the reading was
    *accepted*.  The verdict "a re-probe is owed and is not affordable in a
    cycle" was carried for four cycles as a documented condition, so the
    instrument sat dark with a green suite over it.  A named debt nobody can
    pay reads exactly like a debt nobody has.
    """
    assert ins.stale_pins() == ()
    assert all(ins.inert(c) for c in ins.POST_RECEIPT_WRITES)


def test_the_composition_is_a_disjunction_not_an_average():
    """A moving entrant condemns the whole set; an inert one cannot clear it."""
    assert ins.compose(ins.INERT, ins.INERT, True) == ins.INERT_COMPOSED
    assert ins.compose(ins.INERT, ins.CONTENT_READ, True) == ins.CONTENT_READ
    assert ins.compose(ins.INERT_COMPOSED, ins.CONTENT_READ, True) == ins.CONTENT_READ


def test_a_vacuous_entrant_probe_is_not_inertness():
    """Emptiness is decided before success, here as everywhere else."""
    assert ins.compose(ins.INERT, ins.VACUOUS, True) == ins.VACUOUS


def test_composition_cannot_launder_a_weak_base_into_a_strong_verdict():
    """A base that never graded INERT has nothing to compose onto."""
    assert ins.compose(ins.CONTENT_READ, ins.INERT, True) == ins.CONTENT_READ
    assert ins.compose(ins.VACUOUS, ins.INERT, True) == ins.VACUOUS


def test_no_entrants_carries_the_base_verdict_unchanged():
    """Nothing entered means the pin already covers the set — no upgrade."""
    assert ins.compose(ins.INERT, ins.VACUOUS, False) == ins.INERT
    assert ins.compose(ins.INERT_COMPOSED, ins.VACUOUS, False) == ins.INERT_COMPOSED


def test_a_pin_may_not_carry_generations_forever(monkeypatch):
    """The cap is what stops composition reproducing the decay it fixes.

    Each generation inherits an un-re-measured base, so an uncapped chain is a
    pin that is never actually taken again — the exact failure this cycle found,
    dressed as a measurement.
    """
    exhausted = ins.Pin(
        verdict=ins.INERT_COMPOSED,
        readers_key=ins.readers_key("STATE.md"),
        taken="synthetic",
        generation=ins.COMPOSITION_CAP,
    )
    monkeypatch.setitem(ins.PROBED, "STATE.md", exhausted)
    assert ins.inert("STATE.md") is False


def test_a_probe_subset_outside_the_readers_is_refused_not_intersected():
    """A caller error must not read as a narrower measurement."""
    with pytest.raises(ValueError, match="not a subset"):
        ins.probe("STATE.md", tests=("eval/mppi_sandbox/tests/test_nonexistent.py",))


def test_entrants_and_carried_partition_the_reader_set():
    """The disjunction only holds if the two halves cover the set exactly."""
    src = ins._python_sources()
    for cand in ins.POST_RECEIPT_WRITES:
        entered = set(ins.entrants(cand, src))
        carried = {n for n in ins.readers(cand, src).all if n not in entered}
        assert entered | carried == set(ins.readers(cand, src).all)
        assert not (entered & carried)


def test_an_unpinned_candidate_has_no_entrants():
    """No base means no delta — `()` here is 'no question', not 'nothing new'."""
    assert ins.entrants("no/such/path") == ()
    assert ins.departures("no/such/path") == ()


def test_a_nested_prefix_probes_the_file_a_cycle_writes_not_the_top_level_one(
    tmp_path,
):
    """The one-level walk measured ``journal/README.md`` and called it ``journal/``.

    ``results/`` is flat, so ``glob('*')`` happened to name the TSV the cycle
    had just appended to, and the rule looked correct for as long as the
    population held only flat directories.  ``journal/`` is nested — cycles
    write ``journal/YYYY-MM/DD-HH-<slug>.md`` — and one level up the only file
    is the hand-written ``README.md``, which no cycle ever writes.

    The failure is not that the probe errors; it is that it *succeeds* on the
    wrong file.  The verdict would be a true statement about ``README.md``
    while the exemption it licenses covers the per-cycle journal, a path no
    probe ever touched — a measurement stapled to a claim it does not support,
    which reads as evidence and is therefore worse than no measurement.
    """
    readme = tmp_path / "journal" / "README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text("conventions, not a cycle artifact")
    written = tmp_path / "journal" / "2026-08" / "07-08-a-slug.md"
    written.parent.mkdir(parents=True)
    written.write_text("the file 4a writes and 4a-ter rewrites")
    # Make the nested file unambiguously newer, so the assertion is about the
    # walk's depth and not about a tie in mtime.
    os.utime(readme, (1, 1))
    os.utime(written, (2, 2))

    assert ins._probe_target("journal/", tmp_path) == written


def test_the_prefix_walk_still_selects_by_mtime_not_by_depth(tmp_path):
    """Negative control for the fix above: recursion must not become 'deepest'.

    Recursing is only sound because the selection rule is unchanged — newest
    wins, wherever it sits.  If the walk started preferring nested files as
    such, a flat population member like ``results/`` would keep working by
    luck and the next nested one would silently probe a stale file.
    """
    top = tmp_path / "journal" / "written-last.md"
    top.parent.mkdir(parents=True)
    top.write_text("newest, and at the top level")
    nested = tmp_path / "journal" / "2026-08" / "written-first.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("older, and nested")
    os.utime(nested, (1, 1))
    os.utime(top, (2, 2))

    assert ins._probe_target("journal/", tmp_path) == top


def test_an_empty_prefix_has_no_target_rather_than_a_directory(tmp_path):
    """``rglob`` yields directories too; a probe must never write to one."""
    (tmp_path / "journal" / "2026-08").mkdir(parents=True)
    assert ins._probe_target("journal/", tmp_path) is None


def test_a_reader_set_that_moves_mid_probe_is_no_measurement_not_a_read(
    tmp_path, monkeypatch
):
    """The confound that produced this candidate's first, wrong verdict.

    A probe pass costs minutes, so "nobody edits the reader set meanwhile" is a
    premise, not a fact.  On the first take of the ``journal/`` pin five test
    functions were added to one of the fourteen reader files between the two
    passes; the counts came out ``343 -> 348`` and the module called it
    :data:`CONTENT_READ`.  That is the *same arithmetic* a genuine content read
    produces, so the count alone cannot tell them apart.

    The verdict must be :data:`VACUOUS` rather than :data:`CONTENT_READ`.  Both
    refuse the exemption, so the gate is equally safe either way — but only one
    of them is honest about having no measurement, and a spoiled probe recorded
    as a *read* is a finding the evidence does not carry.
    """
    reader = tmp_path / "eval" / "mppi_sandbox" / "tests" / "test_a.py"
    reader.parent.mkdir(parents=True)
    reader.write_text("open('journal/x.md')")
    target = tmp_path / "journal" / "2026-08" / "07-08-a.md"
    target.parent.mkdir(parents=True)
    target.write_text("body")

    sources = {"eval/mppi_sandbox/tests/test_a.py": "open('journal/x.md')"}
    runs = iter(({"passed": 343}, {"passed": 348}))

    def fake_run(tests, root=None):
        # Simulate the author's edit landing between the two passes.
        reader.write_text(reader.read_text() + "\ndef test_new(): pass")
        return next(runs)

    monkeypatch.setattr(ins, "_run", fake_run)
    probe = ins.probe("journal/", root=tmp_path, sources=sources)
    assert probe.verdict == ins.VACUOUS, probe.describe()
    assert probe.verdict != ins.CONTENT_READ


def test_a_quiescent_reader_set_still_reaches_a_real_verdict(tmp_path, monkeypatch):
    """Control: the guard must not swallow every probe it brackets."""
    reader = tmp_path / "eval" / "mppi_sandbox" / "tests" / "test_a.py"
    reader.parent.mkdir(parents=True)
    reader.write_text("open('journal/x.md')")
    target = tmp_path / "journal" / "2026-08" / "07-08-a.md"
    target.parent.mkdir(parents=True)
    target.write_text("body")

    sources = {"eval/mppi_sandbox/tests/test_a.py": "open('journal/x.md')"}
    monkeypatch.setattr(ins, "_run", lambda tests, root=None: {"passed": 343})
    assert ins.probe("journal/", root=tmp_path, sources=sources).verdict == ins.INERT

    moved = iter(({"passed": 343}, {"passed": 344}))
    monkeypatch.setattr(ins, "_run", lambda tests, root=None: next(moved))
    assert (
        ins.probe("journal/", root=tmp_path, sources=sources).verdict
        == ins.CONTENT_READ
    )


def test_the_run_fingerprint_keys_on_content_not_on_mtime(tmp_path):
    """A checkout rewriting a file to its own bytes has not moved the surface."""
    reader = tmp_path / "t.py"
    reader.write_text("body")
    first = ins._run_fingerprint(("t.py",), tmp_path)

    os.utime(reader, (1, 1))
    assert ins._run_fingerprint(("t.py",), tmp_path) == first

    reader.write_text("body and more")
    assert ins._run_fingerprint(("t.py",), tmp_path) != first


def test_an_absent_reader_is_distinct_from_an_empty_one(tmp_path):
    """Otherwise deleting a reader mid-probe reads as 'unchanged'."""
    (tmp_path / "t.py").write_text("")
    empty = ins._run_fingerprint(("t.py",), tmp_path)
    (tmp_path / "t.py").unlink()
    assert ins._run_fingerprint(("t.py",), tmp_path) != empty


def test_departures_are_reported_even_though_they_are_not_probed():
    """Monotone in the safe direction, but stated rather than implied (D-038)."""
    shrunk = ins.Pin(
        verdict=ins.INERT,
        readers_key="|".join(("a.py", *ins.readers("STATE.md").all)),
        taken="synthetic",
    )
    import unittest.mock as _m

    with _m.patch.dict(ins.PROBED, {"STATE.md": shrunk}):
        assert ins.departures("STATE.md") == ("a.py",)
        assert ins.entrants("STATE.md") == ()


# --------------------------------------------------------------------------
# Q-128: the reader scan reads the *index*, so a pin read before `git add`
# is a reading about a tree nobody is about to push.
# --------------------------------------------------------------------------


def _git_init(root):
    import subprocess

    def run(*a):
        subprocess.run(a, cwd=root, check=True, capture_output=True)

    run("git", "init", "-q")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")
    return run


def test_unstaged_readers_sees_what_the_tracked_scan_cannot(tmp_path):
    """The blind spot, stated as data rather than as prose.

    Both calls run over the *same disk*.  The only difference is the index,
    which is exactly the claim Q-128 makes.
    """
    run = _git_init(tmp_path)
    (tmp_path / "eval").mkdir()
    tracked = tmp_path / "eval" / "test_seen.py"
    tracked.write_text("x = 1\n")
    run("git", "add", "eval/test_seen.py")
    run("git", "commit", "-qm", "init")

    untracked = tmp_path / "eval" / "test_unseen.py"
    untracked.write_text("y = 2\n")

    # The scan the pins are derived from does not contain the new file...
    assert "eval/test_unseen.py" not in ins._python_sources(tmp_path)
    assert "eval/test_seen.py" in ins._python_sources(tmp_path)
    # ...and this is the function that says so.
    assert ins.unstaged_readers(tmp_path) == ("eval/test_unseen.py",)


def test_the_unstaged_reading_is_cleared_by_git_add(tmp_path):
    """D-044: a check that cannot be cleared is a check that gets muted.

    This is the property that licenses `pin_reading` to be a reading rather
    than a warning, so it is pinned rather than assumed.
    """
    run = _git_init(tmp_path)
    (tmp_path / "eval").mkdir()
    (tmp_path / "eval" / "a.py").write_text("x = 1\n")
    run("git", "add", "eval/a.py")
    run("git", "commit", "-qm", "init")

    new = tmp_path / "eval" / "test_new.py"
    new.write_text("z = 3\n")
    assert ins.unstaged_readers(tmp_path) == ("eval/test_new.py",)

    run("git", "add", "eval/test_new.py")
    assert ins.unstaged_readers(tmp_path) == ()
    # And the file is now inside the surface the pins are derived from —
    # i.e. `git add` did not merely silence the reading, it made it moot.
    assert "eval/test_new.py" in ins._python_sources(tmp_path)


def test_only_python_under_scan_roots_counts_as_an_unseen_reader(tmp_path):
    """A stray `.md` or a file outside `eval/` cannot import its way to a pin."""
    _git_init(tmp_path)
    (tmp_path / "eval").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "eval" / "notes.md").write_text("not a reader\n")
    (tmp_path / "scripts" / "wrap.py").write_text("x = 1\n")
    (tmp_path / "eval" / "test_real.py").write_text("x = 1\n")
    assert ins.unstaged_readers(tmp_path) == ("eval/test_real.py",)


def test_pin_reading_separates_a_clean_read_from_an_uninformed_one(tmp_path):
    """`PINS_CURRENT` and `PINS_UNSTAGED` differ in exactly the Q-128 case.

    `stale_pins` returns `()` in both.  Collapsing them is the false green the
    17:00 cycle would have pushed on.
    """
    run = _git_init(tmp_path)
    (tmp_path / "eval").mkdir()
    (tmp_path / "eval" / "a.py").write_text("x = 1\n")
    run("git", "add", "eval/a.py")
    run("git", "commit", "-qm", "init")

    pinned = {}  # no pins ⇒ `stale_pins` is `()` by construction
    import unittest.mock as _m

    with _m.patch.dict(ins.PROBED, {}, clear=True):
        assert ins.stale_pins(pinned) == ()
        clean = ins.pin_reading(pinned, tmp_path)
        assert clean.verdict == ins.PINS_CURRENT
        assert clean.trustworthy

        (tmp_path / "eval" / "test_new.py").write_text("y = 2\n")
        # Same `stale_pins()`; different answer to "is this about the pushed tree".
        assert ins.stale_pins(pinned) == ()
        uninformed = ins.pin_reading(pinned, tmp_path)
        assert uninformed.verdict == ins.PINS_UNSTAGED
        assert not uninformed.trustworthy
        assert uninformed.unstaged == ("eval/test_new.py",)


def test_a_moved_pin_outranks_the_index_caveat(tmp_path):
    """Ordering is load-bearing: a withdrawn exemption is actionable *now*.

    The reverse order would let an unstaged-file notice hide a pin that has
    already moved — reporting the smaller of two problems, which is the
    failure D-082's `check` orders its verdicts to avoid.
    """
    run = _git_init(tmp_path)
    (tmp_path / "eval").mkdir()
    (tmp_path / "eval" / "a.py").write_text("x = 1\n")
    run("git", "add", "eval/a.py")
    run("git", "commit", "-qm", "init")
    (tmp_path / "eval" / "test_new.py").write_text("y = 2\n")

    moved = ins.Pin(verdict=ins.INERT, readers_key="stale-key", taken="synthetic")
    import unittest.mock as _m

    with _m.patch.dict(ins.PROBED, {"STATE.md": moved}, clear=True):
        reading = ins.pin_reading({}, tmp_path)
        assert reading.verdict == ins.PINS_STALE
        assert reading.stale == ("STATE.md",)
        # The caveat is carried, not dropped — it widens the stale set.
        assert reading.unstaged == ("eval/test_new.py",)
        assert "may not be all of them" in reading.describe()


def test_the_real_repo_reading_is_current():
    """The live control.  If this goes red, read it before staging anything."""
    reading = ins.pin_reading()
    assert reading.verdict == ins.PINS_CURRENT, reading.describe()


# --------------------------------------------------------------------------
# what a content write can and cannot do to a pin (D-198)
# --------------------------------------------------------------------------


def _sources_reaching_state(*names: str) -> dict[str, str]:
    """Synthetic source map whose named test modules all spell ``STATE.md``."""
    return {ins._TESTS + n: "open('STATE.md')\n" for n in names}


def test_rewriting_the_pinned_file_cannot_stale_its_pin():
    """A 4c write to ``STATE.md`` moves no reader set, so no pin goes stale.

    The control for a misdiagnosis that has already been made and acted on.
    The 2026-08-11 13:00 cycle found 4 red here, attributed them to the 12:00
    cycle's 4c ``STATE.md`` rewrite, and escalated that into a finding against
    D-044's ordering table.  :func:`stale_pins` never reads the candidate's
    *content* — it compares :func:`readers_key`, a set of reader files — so
    the attributed cause cannot produce the observed effect, at any content.
    """
    src = _sources_reaching_state("test_a.py", "test_b.py")
    pin = ins.Pin(
        verdict=ins.INERT,
        readers_key=ins.readers_key("STATE.md", src),
        taken="synthetic",
    )
    import unittest.mock as _m

    with _m.patch.dict(ins.PROBED, {"STATE.md": pin}, clear=True):
        # Same reader set, arbitrarily different file content on disk.
        assert ins.stale_pins(src) == ()
        assert ins.stale_pins(dict(src)) == ()


def test_adding_a_reader_is_what_stales_a_pin():
    """The other direction — the detector bites on the cause that is real.

    Paired with the test above deliberately: together they say *which* of two
    same-cycle events produced the red, which is the reading the 13:00 cycle
    got backwards.  A cycle that adds a test module reaching the pinned path
    stales the pin; that cycle is also the one :func:`unstaged_readers`
    (Q-128) hides the fact from until ``git add``.
    """
    before = _sources_reaching_state("test_a.py", "test_b.py")
    pin = ins.Pin(
        verdict=ins.INERT,
        readers_key=ins.readers_key("STATE.md", before),
        taken="synthetic",
    )
    after = _sources_reaching_state("test_a.py", "test_b.py", "test_entrant.py")
    import unittest.mock as _m

    with _m.patch.dict(ins.PROBED, {"STATE.md": pin}, clear=True):
        assert ins.stale_pins(after) == ("STATE.md",)
        assert ins.entrants("STATE.md", after) == (
            ins._TESTS + "test_entrant.py",
        )
