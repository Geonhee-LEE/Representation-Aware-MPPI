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
