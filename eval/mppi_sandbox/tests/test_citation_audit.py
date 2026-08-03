# SPDX-License-Identifier: BSD-3-Clause
"""Q-056: the discovery half of citation policing.

``claim_scope``'s tests hold registered citations to the banked readings.
These hold the *registry itself* to the repo: a magnitude stated somewhere no
registry names goes red, which is the signal citation drift never emitted.

Every check here reads files and compares strings.  Nothing simulates, so
nothing depends on the SIMD dispatch these claims are conditional on (D-033) --
the same licence ``claim_scope`` and ``repair_admissibility`` operate under.
"""

from __future__ import annotations

import textwrap

import pytest

from eval.mppi_sandbox import citation_audit as ca
from eval.mppi_sandbox import claim_scope


# --------------------------------------------------------------------------
# The guard: no undeclared citation anywhere in the scan surface.
# --------------------------------------------------------------------------

def test_no_unregistered_citation_sites():
    """A magnitude stated where no registry accounts for it fails the suite.

    This is the whole point.  When the scan first ran it found three such
    sites, all module docstrings -- a surface ``claim_scope`` never read.
    """
    unreg = ca.unregistered()
    assert unreg == [], (
        "unregistered citation site(s); tag each in MEASURED_CLAIMS "
        "(defines/restates/diagnoses) or correct the prose:\n"
        + "\n".join(f"  {c}: {p} {a} x{n}" for c, p, a, n in unreg))


def test_no_stale_registered_sites():
    """A registered site that no longer states the number is a stale registry."""
    stale = ca.missing_sites()
    assert stale == [], (
        "registered site(s) no longer stating the magnitude:\n"
        + "\n".join(f"  {c}: {p} {a}" for c, p, a in stale))


def test_every_claim_has_a_defining_site():
    """A number with no measuring section is unsourced -- reject on sight."""
    assert ca.undefined() == []


@pytest.mark.parametrize("mc", ca.MEASURED_CLAIMS, ids=lambda m: m.claim)
def test_defining_site_is_unique(mc):
    """Two sections both claiming to have measured a number is a contradiction."""
    definers = [s for s in mc.sites if s.role == "defines"]
    assert len(definers) <= 1, f"{mc.claim}: {len(definers)} defining sites"


@pytest.mark.parametrize("mc", ca.MEASURED_CLAIMS, ids=lambda m: m.claim)
def test_instrument_module_exists(mc):
    """The named instrument must be importable and expose the function.

    Keeps the registry from pointing at a module a refactor renamed.
    """
    mod_name, _, func = mc.instrument.partition("::")
    mod = __import__(f"eval.mppi_sandbox.{mod_name}", fromlist=[mod_name])
    assert hasattr(mod, func), f"{mc.instrument} missing"


# --------------------------------------------------------------------------
# The specific defect this cycle found: D-036's repair stopped at docs/.
# --------------------------------------------------------------------------

def test_horizon_audit_docstring_disambiguates_the_drifted_ratio():
    """`horizon_audit`'s docstring states 2.0x; it must name the instrument too.

    D-036 stamped six ``docs/`` sections so no reader meets the ``2.0x``
    (``w(34)/w(15)``) without meeting the instrument's ``w(34)/w(30)``.  This
    docstring states the same pairing in code and was missed.  Same rule as
    ``claim_scope.undisambiguated``, applied to the module surface.
    """
    doc = ca._module_docstring(
        (ca.REPO_ROOT / "eval/mppi_sandbox/horizon_audit.py").read_text(encoding="utf-8"))
    swing = next(c for c in claim_scope.SCOPED_CLAIMS
                 if c.claim == "horizon_weight_swing")
    assert f"{swing.reading_calibrated:.4f}" in doc, (
        "horizon_audit docstring cites 2.0x without the instrument's reading")
    assert claim_scope.ORACLE in doc, "missing oracle stamp"


# --------------------------------------------------------------------------
# Scanner behaviour -- fixtures, so these do not move when the repo's prose does.
# --------------------------------------------------------------------------

def _write(tmp_path, rel, body):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def test_scan_attributes_occurrences_to_their_section(tmp_path):
    _write(tmp_path, "docs/decisions.md", """\
        ## D-001 — first
        measured 6.19× here and 6.19× again
        ## D-002 — second
        cites 6.19× once
        ## D-003 — third
        unrelated 1.46×
        """)
    got = ca.occurrences(6.19, root=tmp_path)
    assert got == [("docs/decisions.md", "## D-001", 2),
                   ("docs/decisions.md", "## D-002", 1)]


def test_scan_reads_module_docstrings_past_the_spdx_header(tmp_path):
    """Regression: every scanned module opens with a licence comment.

    A regex anchored at offset 0 returned nothing for all three real modules
    and the pass reported their registered sites as *stale* -- failing open,
    which for a discovery tool is the worst possible direction.
    """
    _write(tmp_path, "eval/mppi_sandbox/weight_units.py", '''\
        # SPDX-License-Identifier: BSD-3-Clause
        """Headline: 6.19× the baseline spread."""
        X = 1
        ''')
    assert ca.occurrences(6.19, root=tmp_path) == [
        ("eval/mppi_sandbox/weight_units.py", "eval/mppi_sandbox/weight_units.py", 1)]


def test_scan_ignores_numbers_outside_the_docstring(tmp_path):
    """Only prose is a citation; a literal in code is the instrument's own."""
    _write(tmp_path, "eval/mppi_sandbox/weight_units.py", '''\
        # SPDX-License-Identifier: BSD-3-Clause
        """No magnitude here."""
        THRESHOLD = 6.19  # 6.19× in a comment is not a citation either
        ''')
    assert ca.occurrences(6.19, root=tmp_path) == []


def test_magnitudes_do_not_collide(tmp_path):
    """`6.19` must not match inside `16.19`, nor `2.0` inside `12.0`."""
    _write(tmp_path, "docs/decisions.md", """\
        ## D-001 — x
        16.19× and 12.0× and 2.0×
        """)
    assert ca.occurrences(6.19, root=tmp_path) == []
    assert ca.occurrences(2.0, root=tmp_path) == [("docs/decisions.md", "## D-001", 1)]


def test_unregistered_flags_an_unknown_section(tmp_path):
    """The candidate-generating behaviour Q-056 asked for."""
    _write(tmp_path, "docs/decisions.md", """\
        ## D-027 — defines
        measured 6.19×
        ## D-099 — a section nobody registered
        reuses 6.19× silently
        """)
    unreg = ca.unregistered(root=tmp_path)
    assert ("w_voo_over_baseline_spread", "docs/decisions.md", "## D-099", 1) in unreg


def test_claim_scope_citation_list_is_lifted_not_retyped():
    """The 2.0x sites must track ``claim_scope``, not a second hand-typed copy."""
    swing = next(c for c in claim_scope.SCOPED_CLAIMS
                 if c.claim == "horizon_weight_swing")
    cited = next(m for m in ca.MEASURED_CLAIMS
                 if m.claim == "horizon_weight_swing_cited")
    lifted = {(s.path, s.anchor) for s in cited.sites}
    assert {(c.doc, c.anchor) for c in swing.citations} <= lifted


def test_swing_amplitude_origin_is_distinguished_from_its_restatements():
    """D-030 measured the 2.0x; four sections carried it to a foreign claim.

    ``claim_scope`` calls all five ``other-quantity`` citations, which is what
    D-036 concluded about their *pairing*.  It leaves no room to say that one
    of them is where the number came from -- and that asymmetry is the drift's
    actual shape.
    """
    cited = next(m for m in ca.MEASURED_CLAIMS
                 if m.claim == "horizon_weight_swing_cited")
    assert cited.defining is not None
    assert cited.defining.anchor == ca._SWING_AMPLITUDE_ORIGIN
    restated = {s.anchor for s in cited.sites if s.role == "restates"}
    assert {"## D-032", "## D-033", "## Q-054", "## Q-055"} <= restated


def test_hand_registration_was_incomplete():
    """Documents Q-056's premise: the scan found sites the hand list lacked.

    ``claim_scope`` registered five sections citing 2.0×.  The scan finds
    those plus D-036 (the diagnosis) and two module docstrings.
    """
    swing = next(c for c in claim_scope.SCOPED_CLAIMS
                 if c.claim == "horizon_weight_swing")
    found = ca.occurrences(2.0)
    assert len(found) > len(swing.citations)


# --------------------------------------------------------------------------
# D-038 / Q-057: the widened (bare-magnitude) pass and its ranking.
# --------------------------------------------------------------------------

def test_bare_pattern_is_a_strict_superset_of_the_marked_one():
    """Widening the spelling must not *lose* a site.

    This is the regression for the bug the widening shipped with: ASCII ``x``
    is a ``\\w``, so a bare pattern ending ``(?![\\w.])`` rejects ``2.320x``
    while the narrow ``N.NN×`` pattern matches it.  ``exposure``'s docstring
    spells the sign in ASCII, so the naive widening silently dropped a real
    citation -- failing open, the same direction as D-037's regex-vs-``ast``
    bug.  Asserted over the real scan surface, not over an example string.
    """
    base = ca.REPO_ROOT
    for path, anchor, body in ca._iter_bodies(base):
        marked = [m.group(1) for m in ca._MAGNITUDE.finditer(body)]
        bare = [m.group(1) for m in ca._BARE.finditer(body)]
        for value in marked:
            assert value in bare, (
                f"{path} {anchor}: {value!r} is found by the marked pattern "
                f"and lost by the widened one")


def test_widened_pass_finds_every_registered_site():
    """Every hand-registered site is reachable from the widened pass too."""
    for mc in ca.MEASURED_CLAIMS:
        found = {(o.path, o.anchor) for o in ca.all_occurrences(mc.magnitude)}
        for site in mc.sites:
            assert (site.path, site.anchor) in found, \
                f"{mc.claim}: widened pass misses registered {site.anchor}"


def test_widening_the_spelling_found_no_missed_citation():
    """D-038's negative result, held so a later cycle does not re-litigate it.

    Q-057 scoped the widening around an expected flood of false positives.
    What the repo actually contains is 5 unregistered bare hits across six
    claims, and *every one* is a different quantity sharing the value.  So the
    ``N.NN×`` spelling was missing nothing here.  If a future cycle writes a
    genuine bare citation this test goes red and the verdict gets revisited --
    which is the point of pinning a negative rather than remembering it.
    """
    assert ca.candidates() == [], (
        "a bare hit now scores as a citation candidate; if it is one, register "
        "it and update D-038's negative result:\n"
        + "\n".join(f"  {s:+.1f} {c} @ {o.anchor}: {o.quote.strip()}"
                    for s, c, o, _ in ca.candidates()))


def test_rejections_split_into_by_evidence_and_by_default():
    """Distinguishes "rejected because a signal fired" from "rejected by silence".

    The second kind is the ranking getting the right answer for no reason, and
    it is not hypothetical: D-038's own prose says "raw occurrence 로 세면 2.0
    이 10 → 40" -- a bare *mention* of the claim inside the section auditing
    it, carrying no local token either way.  It scores 0.0 and falls below
    threshold by default.

    So the honest statement of the ranking's power is the split, not the
    label.  Pinned rather than asserted away: if a future change makes the
    silent bucket the majority, the ranking has stopped discriminating and
    this goes red.
    """
    ranked = ca.rank_unregistered()
    assert ranked, "expected the widened pass to surface the known bare hits"
    silent = [r for r in ranked if not r[3]]
    assert len(silent) <= 2, (
        "rejections are increasingly by silence rather than by evidence:\n"
        + "\n".join(f"  {c} @ {o.anchor}: {o.quote.strip()}"
                    for _, c, o, _ in silent))
    assert len(ranked) - len(silent) >= 4 * len(silent), (
        f"only {len(ranked) - len(silent)} of {len(ranked)} rejections are "
        f"evidence-backed")


def test_no_signal_fires_on_a_registered_citation():
    """A negative signal that fires on a true citation is worse than none.

    The first draft counted ``:`` as an assignment, so ``결과: **6.19×**`` --
    the way this repo introduces a result -- cancelled ``multiplication_sign``
    and dropped four genuine citations to 0.0, colliding with the unregistered
    band.  The ordering property below would have caught it; this names the
    cause so the fix is not silently reverted.
    """
    for mc in ca.MEASURED_CLAIMS:
        known = {(s.path, s.anchor) for s in mc.sites}
        canonical = ca.canonical_spelling(mc)
        for occ in ca.all_occurrences(mc.magnitude):
            if (occ.path, occ.anchor) not in known or not occ.marked:
                continue
            fired = {s.name for s in ca.signals_for(occ, mc, canonical)}
            negative = fired & {"unit_suffix", "assignment", "denominator"}
            assert not negative, (
                f"{mc.claim} @ {occ.anchor}: {sorted(negative)} fired on a "
                f"registered citation -- {occ.quote.strip()}")


def test_the_ranking_separates_registered_sites_from_bare_hits():
    """Ordering, not calibration, is what the score has to get right.

    The weakest registered site must outrank the strongest unregistered one;
    a score that merely *labels* correctly while interleaving the two would
    give a human no useful reading order.
    """
    registered_scores = []
    for mc in ca.MEASURED_CLAIMS:
        known = {(s.path, s.anchor) for s in mc.sites}
        canonical = ca.canonical_spelling(mc)
        for occ in ca.all_occurrences(mc.magnitude):
            if (occ.path, occ.anchor) in known and occ.marked:
                registered_scores.append(
                    sum(s.weight for s in ca.signals_for(occ, mc, canonical)))
    unreg_scores = [s for s, _, _, _ in ca.rank_unregistered()]
    assert registered_scores and unreg_scores
    assert min(registered_scores) > max(unreg_scores), (
        f"overlap: registered min {min(registered_scores)} vs "
        f"unregistered max {max(unreg_scores)}")


def test_rank_is_sorted_best_first():
    scores = [s for s, _, _, _ in ca.rank_unregistered()]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.parametrize("anchor,signal", [
    ("## D-031", "unit_suffix"),        # `call` 시간 >= 2.0 s
    ("## D-026", "assignment"),         # w_speed = 2.0
    ("## D-024", "denominator"),        # median ESS 1.46 / K=256
    ("## D-029", "precision_mismatch"), # 2.00, where the claim is spelled 2.0
])
def test_each_known_false_positive_fires_its_diagnostic_signal(anchor, signal):
    """Names *why* each of the 5 is rejected, so a weight change shows up here."""
    fired = {s.name for _, _, occ, sigs in ca.rank_unregistered()
             if occ.anchor == anchor for s in sigs}
    assert signal in fired, f"{anchor}: expected {signal}, got {sorted(fired)}"


def test_canonical_spelling_comes_from_the_defining_site():
    """Derived from prose, not registered by hand -- one less field to drift."""
    swing = next(m for m in ca.MEASURED_CLAIMS
                 if m.claim == "horizon_weight_swing_cited")
    assert ca.canonical_spelling(swing) == "2.0"
    band = next(m for m in ca.MEASURED_CLAIMS
                if m.claim == "exposure_band_width_cruise")
    assert ca.canonical_spelling(band) == "2.320"


def test_bare_only_site_is_ranked_but_not_a_registry_failure(tmp_path):
    """The gate keeps reading the marked spelling only.

    Promoting the bare pass to a gate would fail the suite on the sentence
    "``w_speed = 2.0``".  A bare-only hit must therefore be reported by the
    ranking and ignored by :func:`~eval.mppi_sandbox.citation_audit.unregistered`.
    """
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "decisions.md").write_text(textwrap.dedent("""\
        ## D-099 — 2026-01-01 — a section using the value as a duration

        The step budget is 6.19 s per rollout, unrelated to any weight.
        """))
    (tmp_path / "docs" / "deliberations.md").write_text("# none\n")
    assert ca.unregistered(root=tmp_path) == []
    ranked = ca.rank_unregistered(root=tmp_path)
    hit = [r for r in ranked if r[2].anchor == "## D-099"]
    assert hit, "the widened pass should still surface it as a ranked hit"
    assert hit[0][0] < ca.CANDIDATE_THRESHOLD
    assert "unit_suffix" in {s.name for s in hit[0][3]}


def test_excluded_surfaces_are_declared_and_load_bearing():
    """An exclusion must be written down *and* actually exclude something.

    A declared exclusion that no file matches is decoration; this checks the
    named surfaces really do state the magnitudes, so the reasons in
    ``EXCLUDED_SURFACES`` are decisions about live prose.
    """
    assert ca.EXCLUDED_SURFACES
    for surface, reason in ca.EXCLUDED_SURFACES:
        assert len(reason) > 40, f"{surface}: reason too thin to be a decision"
        assert not any(s.path.startswith(surface.rstrip("/"))
                       for mc in ca.MEASURED_CLAIMS for s in mc.sites), \
            f"{surface} is declared excluded but a site is registered inside it"
    journal = ca.REPO_ROOT / "journal"
    if journal.exists():
        stating = [p for p in journal.rglob("*.md")
                   if ca._MAGNITUDE.search(p.read_text(encoding="utf-8"))]
        assert stating, "journal/ excluded but states no magnitude — check the reason"


# --------------------------------------------------------------------------
# D-045: the scan surface is discovered, and completeness over the tracked
# tree is an invariant rather than a habit.
# --------------------------------------------------------------------------

def test_scanned_modules_is_the_package_not_a_hand_list():
    """Every module in the package is scanned, with no tuple to maintain.

    The regression this pins is Q-056's: a module added by a future cycle must
    be inside the surface without that cycle editing this file.  Asserting
    against the real directory (not a fixture) is the point — a fixture would
    re-introduce a hand-written list one level down.
    """
    discovered = set(ca.scanned_modules())
    on_disk = {f"{ca.SCANNED_PACKAGE}/{p.name}"
               for p in (ca.REPO_ROOT / ca.SCANNED_PACKAGE).glob("*.py")}
    assert discovered == on_disk
    assert len(discovered) > 15, "package shrank unexpectedly — check the glob"
    # tree_provenance is the concrete case: D-044 could not register it and
    # resolved by not spelling a magnitude.  It is in the surface regardless.
    assert f"{ca.SCANNED_PACKAGE}/tree_provenance.py" in discovered
    # tests/ live one level down and stay out; they are declared excluded.
    assert not any("/tests/" in m for m in discovered)


def test_scanned_modules_picks_up_a_new_module(tmp_path):
    """A file that did not exist when this list was written is still scanned."""
    pkg = tmp_path / ca.SCANNED_PACKAGE
    pkg.mkdir(parents=True)
    (pkg / "brand_new.py").write_text('"""Docstring citing 6.19× out of thin air."""\n')
    discovered = ca.scanned_modules(tmp_path)
    assert f"{ca.SCANNED_PACKAGE}/brand_new.py" in discovered
    hits = ca.occurrences(6.19, tmp_path)
    assert (f"{ca.SCANNED_PACKAGE}/brand_new.py",
            f"{ca.SCANNED_PACKAGE}/brand_new.py", 1) in hits


def test_no_tracked_file_states_a_magnitude_unaccounted_for():
    """Scanned, or excluded with a reason — a third state is the defect.

    This is the check the hand-written file lists could not perform, and on
    its first run it was non-empty at four surfaces.  Three became declared
    exclusions; the fourth (``eval/requirements-ci.txt``) was a real citation
    of D-030's swing and became a scanned site.
    """
    unaccounted = ca.unaccounted_surfaces()
    assert unaccounted == [], (
        "tracked file(s) state a registered magnitude but are neither scanned "
        f"nor declared excluded: {unaccounted}. Add to SCANNED_* (and register "
        "the site) or to EXCLUDED_SURFACES with a reason."
    )


def test_requirements_pin_citation_is_registered_and_scanned():
    """The CI pin's rationale cites a dispatch-fragile claim; pin that it stays.

    Not incidental: if D-030 is ever rescoped the way D-039 rescoped D-028,
    this comment is where the superseded reading would survive — inside the
    file that decides which numpy CI installs, i.e. the file that decides
    whether the number is even reproducible.
    """
    req = "eval/requirements-ci.txt"
    assert req in ca.SCANNED_TEXT
    swing = next(mc for mc in ca.MEASURED_CLAIMS
                 if mc.claim == "horizon_weight_swing_cited")
    site = next((s for s in swing.sites if s.path == req), None)
    assert site is not None and site.role == "restates"
    assert (req, req) in {(p, a) for p, a, _ in ca.occurrences(swing.magnitude)}


def test_surface_enumeration_fails_loudly_rather_than_empty(tmp_path):
    """D-042: a check that only clears work must not clear it by failing.

    ``unaccounted_surfaces`` passes when it returns ``[]``, so an environment
    where the tracked-file list is unobtainable must raise, not return empty —
    otherwise a broken git makes every surface look accounted for.
    """
    with pytest.raises(ca.SurfaceEnumerationError):
        ca.tracked_files(tmp_path / "not-a-repo")


def test_accounted_prefix_match_is_not_a_substring_match():
    """``results/`` must not accidentally account for ``results_summary.md``.

    Directory exclusions are matched as path prefixes ending in ``/``; a bare
    ``startswith`` on the stripped name would silently swallow siblings, which
    is a fail-open in the direction that hides surfaces.
    """
    assert ca._accounted("results/p3-x.tsv") == "excluded"
    assert ca._accounted("results_summary.md") is None
    assert ca._accounted("docs/decisions.md") == "scanned"
    assert ca._accounted(f"{ca.SCANNED_PACKAGE}/exposure.py") == "scanned"
    # a module one level deeper is not in the glob and must not read as scanned
    assert ca._accounted(f"{ca.SCANNED_PACKAGE}/tests/test_sandbox.py") == "excluded"
    assert ca._accounted("docs/prd.md") is None


def test_denominator_signal_reads_the_prose_spelling_too():
    """"1.46 of K = 256" is D-024's "1.46 / K=256" in words, and scores alike.

    Pinned because the asymmetry was invisible until the scan surface widened:
    one spelling of the same fact carried a reason for its rejection and the
    other carried none, and only the *silent-rejection* meta-test could tell
    them apart — no verdict changed either way.
    """
    swing = next(mc for mc in ca.MEASURED_CLAIMS
                 if mc.claim == "w_voo_over_own_arm_spread")
    prose = ca.Occurrence(path="x.py", anchor="x.py", spelling="1.46",
                          marked=False, before="median ESS on this scene is **",
                          after=" of K = 256**, so the update")
    slash = ca.Occurrence(path="x.py", anchor="x.py", spelling="1.46",
                          marked=False, before="median ESS ",
                          after=" / K=256")
    for occ in (prose, slash):
        assert "denominator" in {s.name for s in ca.signals_for(occ, swing)}
    # and it must not fire on an ordinary sentence that happens to say "of"
    plain = ca.Occurrence(path="x.py", anchor="x.py", spelling="1.46",
                          marked=False, before="the ratio is ",
                          after=" of the baseline spread")
    assert "denominator" not in {s.name for s in ca.signals_for(plain, swing)}
