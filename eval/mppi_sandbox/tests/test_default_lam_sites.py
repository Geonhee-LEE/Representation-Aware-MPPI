# SPDX-License-Identifier: BSD-3-Clause
"""Q-060 asked for a count its own method could not produce.  Pin both facts.

Fast tests only -- every assertion reads the repo's syntax tree.  Nothing
simulates, so nothing here is dispatch-fragile (the property that lets
``claim_scope`` / ``operating_point`` / this module police claims that are).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from eval.mppi_sandbox import default_lam_sites as dls
from eval.mppi_sandbox import operating_point as op
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.cbf_mppi import CBFMPPI
from eval.mppi_sandbox.controllers.risk_mppi import RiskMPPI
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams, StockMPPI

REPO_ROOT = Path(__file__).resolve().parents[3]


# --------------------------------------------------------------------------
# 1. Why Q-060's stated method returns a number that means nothing.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("ctor", [make_controller, StockMPPI, RiskMPPI, CBFMPPI])
def test_no_controller_constructor_takes_a_lam_parameter(ctor):
    """Q-060 planned to grep call sites "passing no temperature".

    None of them *can* pass one: ``lam`` is a field of ``params``, never a
    kwarg of a constructor.  So the planned count is 100 % by construction and
    carries no information -- the defect this whole module exists to record.
    """
    assert dls.LAM_FIELD not in inspect.signature(ctor).parameters


def test_lam_is_reachable_only_through_the_params_object():
    assert dls.LAM_FIELD in {f for f in MPPIParams.__dataclass_fields__}
    assert dls.PARAMS_KWARG in inspect.signature(StockMPPI).parameters


def test_every_make_controller_site_lacks_a_lam_kwarg():
    """The vacuous count, asserted so nobody re-derives it and believes it.

    If this ever fails, ``make_controller`` grew a ``lam`` parameter and this
    module's framing needs revisiting -- which is why it is a test, not prose.
    """
    tree = ast.parse((REPO_ROOT / "eval/mppi_sandbox/ab.py").read_text())
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and getattr(n.func, "id", None) == "make_controller"]
    assert calls
    for call in calls:
        assert dls.LAM_FIELD not in {k.arg for k in call.keywords}


# --------------------------------------------------------------------------
# 2. The resolver's own near-misses, both of which failed fail-open.
# --------------------------------------------------------------------------

def test_both_import_spellings_are_resolved():
    """``from ab import seed_sweep`` and ``from pkg import ab`` + ``ab.seed_sweep``.

    Both are live in this repo.  The first draft resolved only the bare-name
    spelling and read **66** sites instead of 103, understating ``DEFAULTS`` by
    24 -- silently, and in the same fail-open direction as D-037's regex bug
    and D-038's ``2.320x``.  Asserting one example is not enough: assert that
    each spelling contributes at least one site to the real scan.
    """
    found = dls.sites()
    bare = [s for s in found
            if s.path.endswith("tests/test_ab_harness.py")]          # from ..ab import run_arm
    dotted = [s for s in found
              if s.path.endswith("tests/test_shadow_cost_seed_robustness.py")]
    assert bare, "bare-name import spelling resolved no sites"
    assert dotted, "module-attribute import spelling (ab.seed_sweep) resolved no sites"


def test_dotted_spelling_is_actually_how_that_file_imports():
    """Guards the guard: if the file switches to a bare import, the test above
    stops covering the dotted spelling without saying so."""
    src = (REPO_ROOT
           / "eval/mppi_sandbox/tests/test_shadow_cost_seed_robustness.py").read_text()
    assert "from eval.mppi_sandbox import ab" in src
    assert "ab.seed_sweep(" in src


def test_carriers_are_qualified_not_bare_names():
    """Keying carriers on the bare name made every ``main`` / ``__init__`` /
    ``measure`` in the tree a carrier once any one of them forwarded: 136 sites,
    33 of them in files that construct no controller at all."""
    for module, name in dls.carriers():
        assert module.startswith("eval."), (module, name)
    assert not any(s.path.startswith("eval/run_metrics.py")
                   or s.path.startswith("eval/tests/") for s in dls.sites())


def test_simulates_follows_helpers_transitively():
    """``_sweeps`` reaches ``ab.seed_sweep``; its callers therefore weight.

    Matching the seed names directly scored eight sites in this file inert and
    would have reported 44 weighting sites instead of 52 -- a false ``False``,
    which deletes evidence, unlike a false ``True`` which only over-counts.
    """
    shadow = [s for s in dls.sites()
              if s.path.endswith("tests/test_shadow_cost_seed_robustness.py")
              and s.kind == dls.DEFAULTS]
    assert shadow
    assert all(s.simulates for s in shadow)


# --------------------------------------------------------------------------
# 3. The census itself.
# --------------------------------------------------------------------------

def test_partition_is_exhaustive_and_disjoint():
    found = dls.sites()
    assert {s.kind for s in found} <= set(dls.KINDS)
    c = dls.census()
    assert c.decides + c.defaults + c.forwards == len(found) == c.total


def test_census_counts_are_pinned():
    """Pinned so a refactor that moves the population announces itself.

    It keeps announcing. `decides` 30 → **31** (D-058) when
    `TestTheShadowBatchIsSitedOnTheScene._armed` armed a controller at an
    explicit `lam` — the **eighth** consecutive cycle whose new module landed
    in a census its own package takes. Worth saying plainly: this pin has never
    once fired for a refactor, only for the auditor walking into its own
    population, and it has caught every one.

    `defaults` 54 → **55** (D-060), **ninth** consecutive cycle:
    `guard_witness._w_batch_per_unit_spread` calls a simulating function without
    naming a `lam`. It never simulates — the knob `KeyError` is raised before a
    controller is constructed, which `test_guard_witness` proves by execution —
    but the site detector is static and cannot see that. See
    `test_lam_dependence.test_exactly_one_site_is_not_a_test`.

    `defaults` 55 → **58** and `forwards` 19 → **20** (D-118), **tenth**
    consecutive cycle: `baseline_matrix`'s three entry points (`run_cell`,
    `run_matrix`, `default_scenarios`) each carry a defaulted `seeds`, and
    `run_cell` forwards `**arm_kwargs` to `ab.seed_sweep`. The entrant is not
    incidental — it is the P5 matrix, and it names no `lam`, which is exactly
    why 12 of its 24 cells graded `ESS_OUT_OF_BAND` at the shipped default.

    `decides` 31 → **33** (D-119), **eleventh** consecutive cycle — and the
    first entrant that is the *repair* of the previous one rather than a new
    module walking into the census. D-118's note above ends "it names no
    `lam`"; this cycle makes `run_matrix` resolve one per cell from
    `lam_windows.yaml`, so `baseline_matrix.py:316` becomes a deciding site
    (+1 non-test), and the live test that proves the calibration is not inert
    arms a cell at an explicit rung (+1 test). `defaults` and `forwards` are
    unchanged: `run_cell` still forwards `**arm_kwargs` and still defaults
    `seeds`, because neither is what moved.

    `decides` 33 → **34** (D-123), **twelfth** consecutive cycle, and the
    cheapest entrant yet to justify: `temperature_confound.measure` arms every
    cell of its 2×2 grid at an explicit rung, because naming both rungs *is*
    the measurement — the module exists to price the gap between two named
    temperatures. One non-test site, `temperature_confound.py:331`. `defaults`
    and `forwards` hold: the new tests pass points, not sweeps, so nothing new
    defers a `lam` to a caller and nothing new defaults one.

    `decides` 34 → **39** (D-124), **thirteenth** consecutive cycle, and the
    first entrant that is **entirely tests**. `test_gap_gate.py` arms all five
    of its controller-level constructions at an explicit `LAM = 0.8` rather
    than inheriting `MPPIParams.lam = 0.1`, because two of those tests assert
    on the *softmax winner* and the shipped default has median ESS ~1 of 256 —
    a greedy argmin, where a cost-shape change flips the argmin arbitrarily and
    "the gate is audible" would prove nothing (D-118). The first draft of that
    file defaulted the rung and the census caught it as **+5 `defaults`, +1
    inert**; naming the rung moved all five to `decides` and put `defaults`
    back to 58 and `inert_defaults` back to 2, so the bill on both is **nil**.
    That is the census working as intended on a new module rather than being
    re-pinned around one. `forwards` holds — the tests pass points, not sweeps.

    `decides` 39 → **45**, `forwards` 20 → **23** (D-125), **fourteenth**
    consecutive cycle. `barrier_ceiling` contributes three forwards (`_score`
    hands one `MPPIParams` to `seed_sweep` and `weight_units.measure`, and
    `sweep` hands it to `_score`) and its tests contribute the decides, each
    naming `LAM = 0.8`. `defaults` and `inert_defaults` hold at 58 / 2, and
    that is the second time the census has *earned* the nil rather than been
    re-pinned to it: the first draft passed `params` positionally into
    `_score`, which the syntactic classifier reads as "no lam named here" and
    scored **+2 `defaults`** — the same two also surfacing in
    `lam_dependence.judge`'s non-test list, which is pinned to exactly the two
    known detector artifacts. Making the parameter keyword-only moved both to
    `forwards` and restored that list, so the census caught a real legibility
    defect in a new module rather than billing for it.

    `decides` 45 → **46** (D-126), **fifteenth** consecutive cycle, and the
    smallest entrant yet: `relief_interval.survey` is the whole bill, one site,
    with `defaults`, `inert_defaults` and `forwards` all holding. The site is
    `survey` handing `barrier_ceiling.sweep` the rung it read from
    `lam_for_cell`. Classifying that as `decides` rather than `forwards` is
    right on both readings: syntactically it names a `lam`, and semantically
    `survey` is not handed a temperature by its caller — it *chooses the
    policy* that each scene runs at its own calibrated rung, which is a
    decision the module makes and documents rather than one it relays. Its
    tests contribute **zero**, because they assemble `SweepResult` dataclasses
    directly instead of constructing controllers, so there is no rung for them
    to name or inherit.

    `decides` 46 → **47** (D-127), **sixteenth** consecutive cycle, and the
    same shape as D-126's: one site, `defaults` / `inert_defaults` / `forwards`
    all holding. The site is `test_operating_weight`'s injection test, which
    names `LAM = 0.8` alongside the weight it is actually asserting about —
    that test's whole claim is *which* params reach the controller, so a run
    that left the temperature implicit would be asserting about the shipped
    0.1 while reading as a statement about the weight. `operating_weight`
    itself contributes **zero**: it maps a `ReliefInterval` to a float and
    never constructs a controller, so there is no rung for it to name. The two
    `run_matrix(calibrated=False)` calls in the same file are likewise unbilled
    — `run_matrix` is not a controller construction, and the temperature they
    leave alone is the pre-D-126 baseline they exist to reproduce.

    `decides` 47 → **55** (D-167), **seventeenth** consecutive cycle, the
    largest single-file entrant on this axis, and the first one this pin caught
    **before** the cycle's own claim was written rather than after. All eight
    sites are `test_geometric_null.py`, the new min-lidar null arm's tests.
    They were not written to name a rung: the first draft called
    `ab.run_arm(scen, "geometric_mppi", seed=3, w_geom=0.0)` and friends, which
    billed `defaults` 58 → **66** and `inert_defaults` 2 → **6** — the four
    inert being the `make_controller` sites that assert on construction and
    never simulate. Naming the walked rung's own `LAM = 0.8` and `W_OBS = 75.0`
    at each site moved all eight to `decides` and put both other counts back,
    so the net bill is **decides-only**, exactly the D-124 shape.

    Two details are worth the lines. First, the repair is the *right* one on
    the semantics and not merely on the count: the file's whole subject is a
    comparison at one recorded operating point, so a byte-identity test run at
    the shipped `lam = 0.1` would have been asserting about a temperature the
    walk never used. Second, the obvious spelling of the repair fails —
    factoring the params into a `_params()` helper and passing `params=_params()`
    reads `FORWARDS` (23 → 31), because `_classify` requires a **literal**
    `MPPIParams(...)` at the call site. So the census charges for the
    indirection rather than for the ignorance, which is D-072's syntax result
    once more: what is counted here is a spelling, and the only spelling that
    discharges the bill is the one that repeats the constructor eight times.

    `decides` 55 → **76** (D-172), **eighteenth** consecutive cycle, and now the
    largest single-file entrant — all 21 sites are `test_structural_null.py`,
    the structural null arm's tests. The paragraph above predicted this file's
    first draft exactly: it *did* factor the constructor into a `params()`
    helper, and the census billed `forwards` 23 → **43** while `decides` moved
    only 1 (the one literal `MPPIParams(lam=1.6, …)`). Inlining the constructor
    at all 20 helper sites moved them to `decides` and put `forwards` back to
    23, `defaults` never having moved — a **decides-only** bill again.

    That the warning was already written down and the draft incurred the bill
    anyway is the useful part: this pin is not redundant with its own docstring.
    It is the thing that makes the docstring get read.

    `decides` 76 → **78** (D-217), **nineteenth** consecutive cycle, and the
    first entrant in nineteen that is not an instrument — it is a *controller
    arm*: `test_predicted_geometry_arm.py`'s two `make_controller` sites for the
    PGIF predicted-geometry critic. It is also the cleanest demonstration yet
    that this census is not bookkeeping. The first draft defaulted the rung and
    was billed **+2 `defaults`** (58 → 60); the reason that mattered is not the
    count but what the count was pointing at. Both tests assert on *trajectory
    difference* — one that `w_ped = 0` reproduces the baseline byte-for-byte,
    one that `w_ped = 50` does not — and at the shipped `lam = 0.1` the softmax
    has median ESS ~1 of 256, i.e. a greedy argmin where any cost-shape change
    flips the winner arbitrarily. The non-inertness assertion would have been
    **satisfied by noise**, and the headline clearance number taken alongside it
    would have been measured at a temperature where the planner is not averaging
    at all. Naming `LAM = 0.8` moved both sites to `decides`, put `defaults` back
    to **58**, and made the claim mean what it says. `forwards` holds at 23 — the
    tests pass a literal `MPPIParams(lam=LAM)` at each site rather than routing
    it through a helper, which is the spelling D-172's paragraph above extracts
    the bill for.
    """
    c = dls.census()
    assert (c.decides, c.defaults, c.forwards) == (78, 58, 23)
    assert c.total == 159
    assert c.inert_defaults == 2
    # 52 through D-059. Reads 53 as of D-060 and **the sim bill is still 52**:
    # `simulates` is static call-graph reachability, so the new site inherits
    # `batch_per_unit_spread`'s controller step even though its `KeyError` fires
    # first and no controller is ever built. The detector cannot see that, and
    # `inert_defaults` is derived from the same detector, so it does not
    # subtract it. Pinned at the detector's reading, with the true bill named —
    # the alternative is a hand-maintained exemption, which is the shape this
    # package has now been wrong about nine cycles running (Q-073).
    assert c.weighting_at_shipped == 56


def test_the_default_is_no_longer_the_majority_choice():
    """The headline **flipped** on 2026-08-10 (D-172), and it is a real result.

    For eighteen cycles this asserted `defaults > decides`: more construction
    sites took the shipped `lam = 0.1` than named a rung, which is what made
    "the default is a choice, not a fallback" a statement about the repo rather
    than about one file. As of `test_structural_null.py`'s 21 sites it reads
    **76 decides vs 58 defaults** and the inequality no longer holds.

    Renamed rather than inverted-in-place, because the two are different
    claims and a silent `<` would have made eighteen cycles of history read as
    though nothing happened.

    What the flip does and does not mean. It does **not** mean the migration
    got cheaper: `migration_cost == defaults == 58`, unmoved — the same 58
    sites would still need an edit if `lam` became required, and
    `test_migration_cost_is_the_defaults_not_every_site` still pins that. What
    changed is only the *denominator's* composition, and it changed because
    recent cycles' tests are about **one recorded operating point** and say so
    at every call site. That is the census working as intended: it was built to
    make naming the rung cheaper to comply with than to ignore, and the
    majority crossing over is what compliance looks like at scale.

    The honest caveat: the crossover was bought by one file contributing 21
    sites, so `decides > defaults` is not yet a stable property of the repo —
    it is one cycle's margin. `abs(decides - defaults)` is pinned below so a
    later cycle that removes `test_structural_null.py` sees this test fail
    rather than silently re-crossing back.

    Margin 18 → **20** (D-217): the PGIF arm's two sites, and they widen it from
    the `decides` side only. That is the second cycle running in which the margin
    grew without `defaults` moving, which is the direction that would eventually
    make the crossover a property of the repo rather than of one file — but two
    cycles is not that yet, and `test_structural_null.py`'s 21 sites still carry
    it on their own.
    """
    c = dls.census()
    assert c.decides > c.defaults
    assert c.decides - c.defaults == 20


def test_migration_cost_is_the_defaults_not_every_site():
    """Q-060 (c) priced itself as "호출부 전부" -- it is 54 of 103.

    ``FORWARDS`` sites already delegate the choice to their caller, so making
    ``lam`` required does not touch them; ``DECIDES`` sites already comply.
    """
    c = dls.census()
    assert c.migration_cost == c.defaults
    assert c.migration_cost < c.total
    assert c.migration_cost + c.forwards + c.decides == c.total


def test_forwarding_sites_decide_nothing_so_need_no_edit():
    for site in dls.sites():
        if site.kind == dls.FORWARDS:
            assert not site.at_shipped_lam


def test_inert_defaults_are_only_raises_tests():
    """Reported, not netted out -- 52 is the load-bearing number and it should
    not be reachable only by subtracting an unexamined residual."""
    inert = [s for s in dls.sites()
             if s.kind == dls.DEFAULTS and not s.simulates]
    assert len(inert) == 2
    assert all("raises" in s.function for s in inert), [s.function for s in inert]


# --------------------------------------------------------------------------
# 4. What the count means -- the link to D-040.
# --------------------------------------------------------------------------

def test_every_defaulting_site_runs_at_the_shipped_lam():
    for site in dls.sites():
        if site.kind == dls.DEFAULTS:
            assert site.at_shipped_lam


def test_the_shipped_lam_those_sites_take_is_admissible_nowhere():
    """The join with D-040: the rung 52 live sites take qualifies in 0 of 24 cells.

    Read from ``operating_point`` rather than restated, so a recalibration that
    moves the windows moves this claim instead of leaving it stale.
    """
    admitting = sum(1 for rungs in op.windows().values()
                    if op.SHIPPED_LAM in rungs)
    assert admitting == 0
    assert dls.census().weighting_at_shipped > 0


def test_shipped_lam_is_read_from_the_dataclass():
    assert op.SHIPPED_LAM == MPPIParams().lam


# --------------------------------------------------------------------------
# 5. Scan surface -- declared, and declared with evidence (D-038's corollary).
# --------------------------------------------------------------------------

def test_scan_root_is_the_complete_controller_construction_surface():
    """``eval/`` is not a convention here, it is all there is.

    An undeclared exclusion is indistinguishable from an oversight, so the
    claim "nothing outside ``eval/`` builds a controller" is checked rather
    than asserted in a docstring.
    """
    seeds = {name for _, name in dls.CARRIER_SEEDS}
    stray = []
    for path in REPO_ROOT.rglob("*.py"):
        rel = path.relative_to(REPO_ROOT)
        if rel.parts[0] in (dls.SCAN_ROOT, ".git") or "site-packages" in rel.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(seed in text for seed in seeds):
            stray.append(str(rel))
    assert not stray, f"controller construction outside {dls.SCAN_ROOT}/: {stray}"


def test_report_names_both_the_cost_and_the_population():
    text = dls.report()
    assert "migration cost" in text
    assert "no calibrated cell admits" in text
