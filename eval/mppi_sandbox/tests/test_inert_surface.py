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

import pytest

from eval.mppi_sandbox import inert_surface as ins
from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import tree_provenance as tp


# --------------------------------------------------------------------------
# population
# --------------------------------------------------------------------------


def test_population_is_the_post_receipt_write_surface():
    """Exactly D-044's after-the-re-run rows, no more."""
    assert set(ins.POST_RECEIPT_WRITES) == {
        "STATE.md",
        "JOURNAL.md",
        "RESULTS.md",
        "results/",
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
        assert pin.verdict in (ins.INERT, ins.CONTENT_READ, ins.VACUOUS)
        assert pin.taken, f"{candidate}'s pin does not say when it was taken"


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


#: The candidates whose premise moved and whose verdict has **not** been
#: re-measured since.  Named rather than tolerated: a re-probe is owed (Q-093),
#: and until it is taken none of these is exempt.
#:
#: Three entered on 2026-08-06 via D-097/D-098.  ``results/`` — the one the
#: 10:00 cycle called "the candidate whose premise did not move" — joined them
#: hours later via D-099: ``test_drift_repair.py`` imports
#: ``repair_admissibility``, which spells ``results/``, making it a transitive
#: reader.  The set is now the **whole population**, so the name's ``_D098``
#: suffix records only when the first three entered, not a cause the four share.
STALE_SINCE_D098: tuple[str, ...] = ("JOURNAL.md", "RESULTS.md", "STATE.md",
                                     "results/")


def test_every_pin_is_now_stale_so_the_instrument_grades_nothing():
    """The state D-088 named ``UNPOPULATED``, reached by attrition.

    Each of the last three cycles wrote a module that mentions a pinned path,
    and each withdrawal was individually correct.  Composed, they leave
    :func:`ins.inert` answering ``False`` to every question it can be asked —
    a complete instrument with no live population, which is exactly the
    condition :func:`ins.PROBED`'s own vacuity test exists to make loud.

    Asserted separately from the set literal because the two facts fail for
    different reasons: the literal moves when *which* pin is stale changes, this
    one moves when the exemption mechanism goes dark or comes back.
    """
    assert set(ins.stale_pins()) == set(ins.POST_RECEIPT_WRITES)
    assert not any(ins.inert(c) for c in ins.POST_RECEIPT_WRITES)


def test_the_stale_set_is_exactly_the_four_owed_a_reprobe():
    """The control D-079 asks for, run against the tree actually shipping.

    This asserted ``stale_pins() == ()`` until 2026-08-06, when it went red for
    the reason it exists: the reader set genuinely moved.  ``test_suite_coverage``
    (D-097) imports :mod:`tree_provenance`, which spells all three paths, so it
    became a transitive reader of each; ``test_simd_attribution`` (D-098) spells
    ``STATE.md`` directly.  Neither *reads* those files — both merely mention or
    import something that mentions them — but :func:`ins.readers` is a string
    scan by design (its own docstring states the bound), and the pin's premise is
    the reader set, not the reading.

    Re-taking the probe is the correct repair and is **not affordable in a
    cycle**: ``STATE.md``'s reader set includes ``test_predicate_inputs`` and
    ``test_predicate_vacuity``, each of which spawns a full nested suite, so one
    probe costs hours.  So the staleness is *named* here instead of asserted
    away.  It bit as designed: it went red again when ``results/`` became the
    fourth, which is the whole population.  It still bites — a pin coming back
    live without a measurement fails it, and so would a fifth candidate if the
    population ever grew.
    """
    assert ins.stale_pins() == STALE_SINCE_D098


def test_the_stale_pins_no_longer_exempt_the_real_post_receipt_writes():
    """The end-to-end claim, with no fixture standing in for the measurement.

    Every test around this one substitutes a synthetic pin over synthetic
    sources, which proves the *composition* and says nothing about whether the
    tree actually shipping is exempt.  This one asks :func:`ins.filter_drift`
    the question the push line asks it, with the shipped pins and the real
    reader scan.

    The answer is now **material**, and that is the mechanism working, not
    failing: :func:`ins.inert` withdraws an exemption the moment its premise
    moves, which is precisely what ``inert_surface`` was built to do.  The
    consequence is real and is the cost of the honest answer — the
    second-suite-run tax is back until the probe is re-taken (Q-093).
    """
    drift = tp.Drift(
        changed=("STATE.md", "JOURNAL.md", "RESULTS.md"),
        added=("results/p3-epistemic-shadow-cost-critic.tsv",),
    )
    material, ignored = ins.filter_drift(drift)
    # Nothing is ignored any more.  `results/` was the last live pin and D-099
    # withdrew it, so every post-receipt write is material and the push line
    # pays a full second suite run unconditionally until the probe is re-taken.
    assert ignored == ()
    assert set(material.changed) | set(material.added) == {
        "STATE.md", "JOURNAL.md", "RESULTS.md",
        "results/p3-epistemic-shadow-cost-critic.tsv",
    }


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
    verdict = pp.check(path)
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
