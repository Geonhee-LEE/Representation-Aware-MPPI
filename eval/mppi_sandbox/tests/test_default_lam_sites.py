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

    `defaults` held at **58** and `decides` 78 -> **81**, `forwards` 23 -> **27**
    (D-218), **twelfth** consecutive cycle: `three_arm`'s head-to-head threads
    `params` explicitly through `read_arm`/`walk`/`risk_interaction` and names
    `lam=` at `head_to_head` and in its closed-loop test. Worth recording *why*
    `defaults` did not move: the first version closed over `params` inside a
    local `walk()`, which the static detector cannot see through, so it scored
    two `DEFAULTS` — the census billed the temperature as unnamed one line below
    where it was named. Passing it as a keyword flipped both to `FORWARDS` and
    cleared `test_lam_dependence`'s non-test list back to its two artifacts. The
    pin caught a call site that really was silent about its rung.

    `defaults` held at **58** and `decides` 81 -> **82** (D-222), **thirteenth**
    consecutive cycle: `test_city_crossing_scene`'s contested-baseline screen
    arms `risk_mppi` at an explicit `MPPIParams(lam=0.8)`. One site, and it is
    worth naming which column it landed in — the *good* one. D-217's entrant
    cost +2 `defaults` because it measured at the shipped rung, where median ESS
    is ~1 of 256 and the reading would have been about the temperature; this
    one names the rung at the call site, so the bill is +1 `decides` and nil on
    `defaults`/`forwards`/`inert_defaults`. The census is doing exactly what it
    was built for: the compliant spelling was the cheaper one to write because
    the previous entrant's bill is in this docstring.

    `defaults` held at **58** and `decides` 82 -> **83** (D-223), **fourteenth**
    consecutive cycle, and it is the same file and the same shape one cycle on:
    `test_city_crossing_scene`'s *second* screen — the one that bounds the
    baseline from below, added when the first turned out to bound it only from
    above — arms `risk_mppi` at an explicit `MPPIParams(lam=0.8)` too. The
    docstring above says the compliant spelling was the cheaper one to write
    because the previous entrant's bill was recorded here; this entrant is the
    same author copying the site directly beneath it, which is the mechanism
    working at its cheapest and least interesting.

    `defaults` 58 -> **59** and `forwards` 27 -> **28** (D-225), **fifteenth**
    consecutive cycle, and the first entrant to land on *both* sides at once:
    `paired_step.walk_cells`. The non-test half is census-aware on purpose —
    `paired_step.py:237` threads `params` into `seed_sweep` explicitly, with a
    docstring saying it is spelled that way "for `default_lam_sites`' benefit"
    because the detector is static and reads a closure-fed temperature as
    DEFAULTS — so it grades FORWARDS, which is the compliant answer. The test
    half then walked into the census anyway: `test_paired_step.py:274`
    (`test_the_recorded_cafe_walk_is_re_derivable`) calls `walk_cells(seeds=(0,))`
    and names no rung, so the re-derivation runs at the shipped 0.1. Worth
    recording precisely because the same commit did the hard side right and the
    easy side wrong: being census-aware in the module does not make the module's
    own test census-aware, and `decides` is unmoved (83) for exactly that reason.
    `decides` 83 -> **85** and `forwards` 28 -> **30** (D-240), **fourteenth**
    consecutive cycle, and the second entrant in a row to land in the *good*
    column for the reason this docstring exists. `test_social_mppi_arm.py`'s
    three controller constructions each name `LAM = 0.8` explicitly, so all
    three scored `decides`; the `forwards` pair is `social_mppi.SocialMPPI`
    handing `**kwargs` up to `RiskMPPI` and the arm test's equivalence sweep.
    `defaults` holds at 60 and `inert_defaults` at 2 -- the nil was **earned,
    not re-pinned**: the first draft left the two construction-only sites
    (`test_registry_exposes_the_arm`, `test_defaults_are_the_measured_cell`)
    without a rung and the census billed them +2 `defaults` / +2
    `inert_defaults`, which is precisely D-124's pattern. Naming the rung moved
    both to `decides` and restored both pins.

    (85, 61, 31) -> **(88, 61, 31)**, total 177 -> 180 (D-243).
    `test_progress_price.py`'s three controller constructions -- two byte-identity
    arms and one freeze measurement -- entered as **+3 `defaults`** on the first
    draft, and this census is what caught it: all three assert on *trajectory*
    magnitudes (a freeze duration in seconds, a byte-identity between two
    simulated runs), so each was asserting about a temperature it never chose.
    Naming `LAM = 0.1` at the sites moved all three to `decides` and `defaults`
    held at 61 -- the third consecutive earned nil, and the second time in three
    cycles that the entrant arrived in the bad column and left in the good one.
    Worth noting which half of the file did *not* move: the eleven pure-arithmetic
    tests build no controller and so are not sites at all, which is the census
    working at the right granularity.

    (88, 61, 31) -> **(91, 61, 32)**, total 180 -> 184 (D-244).
    `freeze_weight` and its test entered as +3 `decides` / +1 `forwards` and
    `defaults` held at 61 -- the **fourth** consecutive earned nil. The entrant
    that had to be argued about was the CLI: `main()` called `sweep()` without a
    rung while *printing* `lam=` in its own header, so it read as `DEFAULTS`
    while looking legible on screen. That is the census catching the exact gap
    it exists for -- a temperature the reader can see but the call never chose.
    The fix was `--lam`, which the next cycle needs anyway to re-take this sweep
    at `PAIRED_LAM`. Note the one site deliberately left in `defaults`:
    `test_d243_lam_is_the_shipped_default_not_a_second_spelling` builds a bare
    `MPPIParams()` because its assertion **is about the default** -- naming a
    rung there would make the test assert its own argument.

    (91, 61, 32) -> **(92, 61, 32)**, total 184 -> 185 (D-245). One entrant,
    `test_the_d243_plateau_does_not_survive_the_paired_temperature`, and it
    names `PAIRED_LAM` at construction -- so the **fifth** consecutive earned
    nil on `defaults`. (D-244's line above recorded its own triple as
    (92, 61, 32) against total 184; those disagree by one and the pin it was
    describing read (91, 61, 32). Corrected here rather than left to look like
    this cycle's entrant had already been counted.)

    (92, 61, 32) -> **(94, 61, 33)**, total 185 -> 188 (D-248).
    `arrival_spread` entered +3 `decides` / +1 `forwards`, so `defaults` holds at
    61 for the **sixth** consecutive cycle. Two `decides` are `sweep(..., lam=)`
    calls -- one in `walk`, one in the CLI -- and the CLI one is the whole point
    of this line: D-244's entrant shipped a defaulted `main()` and had to be
    convicted before it moved, and this module's `--lams` was spelled in the
    first draft. Second cycle running that the habit arrived with the code
    rather than after the census. The third is `stall_split`'s own
    `MPPIParams(lam=lam)`, added later in the same cycle than the first pin
    reading -- which is why this line was written twice: a module that grows a
    second measurement path grows a second rung, and the pin does not care that
    both were mine. The `forwards` is `sweep` handing its one
    `MPPIParams(lam=lam)` to `ab.seed_sweep`, built at the call site rather than
    closed over for the reason the comment there states. The test file adds no
    site at all: it is arithmetic over fixture `ArmArrivals` and constructs no
    controller, the same granularity note D-243's paragraph makes.

    `decides` 95 -> **96** (D-250), and the entrant is a single test rung:
    `test_the_ablation_does_not_freeze_before_arrival_on_this_scene` calls
    `fw.sweep(..., lam=fw.PAIRED_LAM)` and spells the temperature, so it bills
    as `decides` rather than inheriting `MPPIParams.lam = 0.1` — which for that
    test would be measuring a scene at a temperature its claim is not about.
    `defaults` / `forwards` / `inert_defaults` all hold at 61 / 33 / 2: the
    cycle's module edits add no new controller construction, only a second
    reading over rows `freeze_weight.sweep` was already simulating.

    `defaults` 61 -> **65** and `forwards` 33 -> **34** (D-264), the first
    cycle in this series to move either. `decides` is unmoved at 97, which is
    the reading: `arm_audibility` names no temperature anywhere. Attributed
    exactly — the module is +1 `forwards` (`grade` passes `**measure_kwargs`
    through to `weight_units.measure`) and +1 `defaults`; its test file is +3
    `defaults`, one per sim-backed test, each constructing at the shipped
    `MPPIParams.lam`. That is on purpose and is the same reading
    `freeze_price.profile_arm` gets in `test_lam_dependence`: audibility is a
    statement about the operating point the A/B will actually run at, so
    spelling a `lam` here would measure it at a temperature the experiment is
    not run at.
    """
    c = dls.census()
    # D-265 adds `sweep_ratio` (+1 `forwards` — it hands `seed` straight to
    # `weight_units.measure`) and one more sim-backed test constructing at the
    # shipped `MPPIParams.lam` (+1 `defaults`). Same reading as the row above
    # and for the same reason: the ladder is a statement about the operating
    # point the A/B runs at, so naming a `lam` would measure it elsewhere.
    # D-266 adds one more sim-backed test (`test_bisect_point_reproduces`)
    # constructing at the shipped `MPPIParams.lam` (+1 `defaults`, 66 -> 67).
    # No new `forwards`: the three new readers (`bar_crossing`,
    # `common_audible_weights`, `scale_is_per_scene`) read recorded tables and
    # never reach a controller, so there is no `seed` to hand on.
    # D-268 adds `ess_at_peak.sweep_ess` (+1 `forwards`, 35 -> 36 — it hands
    # `seed` straight to `ab.run_arm`). Same reading as `sweep_ratio` above:
    # the ladder is a statement about the operating point the A/B runs at, so
    # naming a `lam` here would measure it somewhere other than the shipped
    # default. That this cycle *found* the shipped default to be degenerate on
    # this scene is a finding about the scene, not a licence to pin a `lam`
    # into the reader — the calibration is the follow-up TODO, not this row.
    # D-270 adds `calibrated_ladder.sweep`'s two `params` hand-offs (+2
    # `forwards`, 36 -> 38 — one into `ab.run_arm`, one into
    # `weight_units.measure`): one call site per callee, because the ESS reading
    # and the ratio reading have to be taken at the *same* temperature or they
    # describe different runs. These are the opposite of a pinned `lam` — the
    # sweep names no temperature at all, it forwards whichever one the caller
    # resolved from the calibration table. That the shipped default turned out
    # to sit below this scene's window is a fact about the window, not a licence
    # to spell a `lam` into a reader; `calibrated_window()` reads it.
    # D-274 adds `essps.harvest_costs` (+1 `decides`, 97 -> 98). It is the
    # first entrant in this series to bill `decides` for a reason the census
    # should *want*: the harvest exists to capture the cost stream at a named
    # operating point (`OPERATING_LAM = 0.8`), and the whole finding is that
    # the shipped default `0.1` is the wrong temperature for this scene. A
    # `defaults` here would have measured the very thing the module argues
    # against. `defaults` / `forwards` hold at 67 / 40 — the test file adds no
    # site at all: every one of its 19 tests is arithmetic over synthetic cost
    # vectors or over recorded constants, and none constructs a controller.
    # 98 -> 99 / 67 -> 68 (D-325). Two sites, one of each kind, and the pair is
    # why the margin below is unmoved. `essps.compare_arms` bills `decides`:
    # like `harvest_costs` above it names `OPERATING_LAM` because the arms are
    # only comparable at one temperature. `test_essps_mppi`'s registry-contract
    # test bills `defaults`: it constructs to prove `make_controller` resolves
    # the new name and never simulates, so naming a rung there would be
    # asserting about a temperature the test never uses.
    # 99 -> 101 (D-327). Two sites, **both** `decides`, both in
    # `clearance_census`: `retake` and `takes_epistemic_kwargs` each spell
    # `MPPIParams(lam=OPERATING_LAM)` because a clearance census across arms is
    # only readable at one temperature — comparing arms run at different `lam`
    # would be the confound the census exists to avoid. `defaults` unmoved at
    # 68: the new test file constructs controllers only through
    # `takes_epistemic_kwargs`, which names the temperature, so no test site
    # takes the shipped default.
    # 101 -> 102 (D-330; renamed `retake_scene` in D-332, still one site
    # because the scene became a parameter rather than a second copy of the
    # loop). One entrant, `scene_transfer.retake_scene`, which
    # spells `MPPIParams(lam=OPERATING_LAM)` for the same reason D-327's two
    # entrants did: it re-derives an eight-arm column, and a census whose arms
    # each picked their own temperature would be measuring the temperature
    # rather than the arms. `defaults` and `forwards` unmoved -- the module's
    # only other construction site is inside `takes_epistemic_kwargs`, which
    # `clearance_census` already owns and which names the temperature itself.
    # 103 -> 104 (D-376). One entrant, `decides`, and the same reason as every
    # census-harvesting entrant since D-327: `tail_stability.retake` spells
    # `MPPIParams(lam=OPERATING_LAM)` because the module compares `cte_max`
    # across eight arms on two scenes, and arms run at different temperatures
    # would be measuring the temperature rather than the tail. `defaults` and
    # `forwards` unmoved at 68 / 40 — the module's tests read the recorded
    # `CENSUS` and never construct a controller, so nothing new takes the
    # shipped default and nothing new defers a `lam` to a caller.
    # 105 -> 106 (D-390): `tail_mean.retake_max`, one `decides` site, with
    # `defaults` and `forwards` unmoved at 68 / 40 for the same reason as the
    # entrant above — its tests read the recorded `CTE_MAX_AT_OPERATING_POINT`
    # and never construct a controller.
    # `defaults` 68 -> **72** (D-411), `decides` and `forwards` unmoved. See the
    # `c.total` note below for why all four of `test_collision_knee.py`'s sites
    # land on the `defaults` side deliberately: D-410 measures what the shipped
    # configuration does when only the collision knee moves, so a named rung
    # would have changed the thing being measured. This is the first entrant
    # since D-225 to move `defaults` at all, and the pair-moves-together
    # property the `c.total` pin usually reads is therefore *absent* here by
    # design -- total and `defaults` move by the same four, `decides` by none.
    # `defaults` 72 -> **85** and `forwards` 40 -> **41** (D-428), the largest
    # single-cycle move this pin has ever recorded, and it was recorded *after*
    # the fact rather than in the entrant's own commit: D-427 added
    # `test_barrier_shape.py` (13 new `defaults` sites) without running
    # `census_preempt`, so the branch committed red and stranded for two cycles.
    # The entrants are legitimate -- every one constructs
    # `MPPIParams(obs_barrier_band=...)` to interrogate the *cost function*, and
    # `lam` is applied to that function's output -- but "legitimate" and
    # "announced" are different properties and only the pin supplies the second.
    # `forwards` 41 -> **42** (D-430), `decides` and `defaults` both unmoved --
    # the narrowest move this pin has recorded in the knee/shape sequence, and
    # a deliberate contrast with D-428's 13. `test_knee_shape_ensemble.py` runs
    # a 4-arm x 16-seed matrix through a *single* `run_scenario(..., params=
    # MPPIParams(**kw))` call inside one module fixture, so 64 integrations
    # enter the census as one forwarding site. The arm dictionary is data, not
    # call sites -- which is the shape to prefer when a cycle needs a wide
    # matrix without a wide census footprint.
    # `forwards` 42 -> **43** (D-434), `decides` and `defaults` both unmoved --
    # the same narrow shape D-430 recorded, and from the same sequence.
    # `test_heading_effort_weight.py` (added by D-433, the cycle *before* the one
    # bumping this pin) sweeps `w_omega` through one `run_scenario(..., params=
    # MPPIParams(**kw))` call, so its 64 integrations enter as a single
    # forwarding site. Worth stating plainly: D-433 did not take this reading, so
    # it left the pin red, its own push gate refused, and the commit stranded
    # unmeasured overnight -- `census_preempt` names `default_lam_sites` in
    # neither its covered nor its UNCOVERED list, which is how it read CLEAN.
    # `defaults` 85 -> **91** (D-440), `decides` and `forwards` both unmoved.
    # Six entrants, all in the one new file `test_heading_price_absence.py`,
    # and all six are bare `MPPIParams(...)` constructions rather than the
    # single forwarding site D-433's sweep contributed: that module builds its
    # params per arm at each call site instead of threading one `**kw` through
    # a helper, so it bills six `defaults` where a sweep-shaped module bills
    # one `forwards`. The distinction is the census's, not a style preference
    # -- D-440 needed two arms on two scenes plus three sim-free cost probes,
    # which is five separate constructions by construction.
    # `defaults` 91 -> **92** (D-442), `decides` and `forwards` both unmoved.
    # One entrant, `avoidance_price.measure_arm`'s `MPPIParams(w_heading=w)`,
    # and it is the narrow counterpart to D-440's six: that module needed five
    # separate constructions because it built params per arm per scene at each
    # call site; this one threads both arms through a single helper whose only
    # varying argument is the weight, so 32 integrations bill one `defaults`.
    # Same lesson as D-430's `forwards` note from the other side of the census
    # -- what the census counts is *construction sites*, not runs, and a helper
    # is how a wide matrix stays narrow here.
    # `defaults` 92 -> **93** (D-444), `decides` and `forwards` both unmoved.
    # One entrant, `avoidance_timing.measure_arm`'s `MPPIParams(w_heading=
    # w_heading)`, and it is the *same* narrow shape as D-442's directly above
    # -- same two arms, same 16 seeds, threaded through one helper whose only
    # varying argument is the weight, so 32 integrations bill one `defaults`
    # again. Worth naming because the pair is now evidence rather than a
    # coincidence: two consecutive reading-modules on this scene each billed
    # exactly one, where D-440's per-arm-per-scene construction billed six.
    # The helper shape is what keeps a wide matrix narrow in this census, and
    # it reproduced.
    # `defaults` 93 -> **94** (D-445), `decides` and `forwards` both unmoved.
    # One entrant, `avoidance_aim.measure_arm`'s `MPPIParams(w_heading=
    # w_heading)` -- the **third** consecutive reading-module on this scene to
    # bill exactly one, after D-442 and D-444 directly above. Three is where the
    # pair stops being evidence and becomes the shape of the thing: a module
    # that reads an existing question off two arms of 16 seeds costs this census
    # one site, because the arms are threaded through a single helper whose only
    # varying argument is the weight. D-440's six remains the counter-example
    # and its cause is unchanged (construction per arm per scene at each call
    # site). Deliberately left as `defaults` rather than named to `decides`: the
    # whole point of this module is that it re-reads *D-444's* runs, so naming a
    # rung here would couple the reading to a literal that could drift away from
    # the default the runs it must reproduce were taken at.
    # `defaults` 94 -> **95** (D-446), `decides` and `forwards` both unmoved.
    # One entrant, `avoidance_budget.measure_arm`'s `MPPIParams(w_heading=
    # w_heading)` -- the **fourth** consecutive reading-module on this scene to
    # bill exactly one, after D-442, D-444 and D-445 directly above. The row
    # above called three "the shape of the thing"; the fourth is the first one
    # that was *predicted* rather than observed, because `census_preempt`
    # named it at the stage for ~2 s instead of the suite naming it 25 min
    # later -- which is the whole difference this cycle set out to buy. The
    # cause is unchanged and so is the reading: two arms of 16 seeds threaded
    # through a single helper whose only varying argument is the weight cost
    # one site, where D-440's per-arm-per-scene construction cost six.
    # Deliberately left as `defaults` rather than named to `decides`, for the
    # same reason as D-445's line: this module re-reads *D-445's own* runs, so
    # naming a rung here would couple the reading to a literal that could
    # drift away from the default the runs it must reproduce were taken at.
    # `defaults` 95 -> **96** (D-447), `decides` and `forwards` both unmoved.
    # One entrant, `crossing_geometry.measure_arm`'s `MPPIParams(w_heading=
    # w_heading)` -- the **fifth** consecutive reading-module on this scene to
    # bill exactly one, after D-442, D-444, D-445 and D-446 directly above. The
    # fifth adds nothing to the mechanism, which is by now fully stated, but it
    # is the second one `census_preempt` named at the stage rather than the
    # suite naming it 25 min later, so the pre-empt's ~2 s is now paying on a
    # repeat rather than on a first sighting. Same reading, same cause: two arms
    # of 16 seeds threaded through a single helper whose only varying argument
    # is the weight. Deliberately left as `defaults` rather than named to
    # `decides`, for the same reason as D-445's and D-446's lines -- this module
    # re-reads *D-446's own* runs, so naming a rung here would couple the
    # reading to a literal that could drift away from the default those runs
    # were taken at.
    # 106 -> 107 (D-484): `lam_inertness.probe`, one `decides` site, with
    # `defaults` and `forwards` unmoved at 96 / 43. It is the census's own
    # subject matter arriving in the census: the site spells
    # `MPPIParams(lam=lam)` because the whole function is a sweep of that
    # argument, so it could not have landed in any other column. Worth one line
    # because it inverts the usual entry -- every prior `decides` entrant named
    # its rung to *avoid* measuring the temperature, and this one names it in
    # order to measure exactly that, then reports that one of the eight arms
    # cannot read what was named.
    assert (c.decides, c.defaults, c.forwards) == (107, 96, 43)
    # 200 -> 202 (D-270), 202 -> 204 (D-272): D-271's `sweep_seeds` forwards
    # `params` to `run_arm` and to `weight_units.measure`, the same two-site
    # shape D-270 added, and the cycle that added them left both this pin and
    # the `forwards` pin above red — the push gate is what caught it.
    # `total` is `decides + defaults + forwards`, so it moves whenever `total` is `decides + defaults + forwards`, so it moves whenever
    # any component does; it is pinned separately because a compensating pair of
    # moves (one site migrating between kinds) would leave the triple above
    # looking wrong while the total held, and vice versa.
    # 205 -> 207 (D-325): the `decides` and `defaults` entrants noted above.
    # 207 -> 209 (D-327): the two `decides` entrants noted above, and nothing
    # else — the triple and the total move by the same two, which is the
    # compensating-pair check this pin exists for reading clean.
    # 209 -> 210 (D-330): the single `decides` entrant above, and nothing else —
    # triple and total move by the same one, so the compensating-pair check
    # this pin exists for reads clean.
    # 210 -> 211 (D-334): the single `decides` entrant above, and nothing else
    # -- triple and total move by the same one, so the compensating-pair check
    # this pin exists for reads clean, fifth consecutive cycle.
    # 211 -> 212 (D-376): the single `decides` entrant above, and nothing else
    # -- triple and total move by the same one, so the compensating-pair check
    # this pin exists for reads clean, sixth consecutive cycle.
    # 212 -> 213 (D-383): the single `decides` entrant above (`tail_mean.retake`),
    # and nothing else -- triple and total move by the same one, seventh
    # consecutive cycle. The pair moving together is the whole point of keeping
    # both pins: a `decides` bump with `total` unmoved would mean a site changed
    # *class* rather than a site arriving, and those are repaired differently.
    # 213 -> 214 (D-390): `tail_mean.retake_max`, the sibling of D-383's entrant
    # and the same shape -- it names `lam=OPERATING_LAM` because naming the rung
    # *is* the content of the claim that the `cte_max` and TVaR columns now share
    # an operating point. Eighth consecutive cycle of the pair moving together.
    # 214 -> 218 (D-411): `test_collision_knee.py`'s four sites, and the first
    # entrant since D-225 to move `defaults` rather than `decides` -- four on
    # the `defaults` side, zero on `decides`, so the pair does *not* move
    # together here and that is correct rather than a class change. D-410's
    # whole claim is what the shipped configuration does when only the
    # collision knee moves, so every site is deliberately at the shipped rung:
    # naming an off-default `lam` would have made the three sim-backed tests
    # measure a temperature the journal's 2-scene x 3-margin x 3-seed walk
    # never ran at. Re-pinned rather than repaired-by-naming, which is the
    # D-225/D-234/D-264 honest-drift direction and not D-124/D-167's.
    # 218 -> 232 (D-428). Total and `defaults` move by 13, `forwards` by 1,
    # `decides` by none -- the D-264 shape at four times the amplitude.
    # 232 -> 233 (D-430). Total and `forwards` move by the same one, `decides`
    # and `defaults` by none -- the compensating-pair check reads clean again
    # after D-428/D-411 broke the pattern twice in a row on the `defaults` side.
    # 233 -> 234 (D-434): the single `forwards` entrant above
    # (`test_heading_effort_weight.py`), and nothing else -- triple and total
    # move by the same one, so the compensating-pair check this pin exists for
    # reads clean, eighth consecutive cycle.
    # 234 -> 240 (D-440): the six `defaults` entrants noted above, and nothing
    # else -- triple and total move by the same six, so the compensating-pair
    # check this pin exists for reads clean.
    # 240 -> 241 (D-442): the single `defaults` entrant above, and nothing else
    # -- triple and total move by the same one, so the compensating-pair check
    # this pin exists for reads clean, first clean read since D-440's six.
    # 241 -> 242 (D-444): the single `defaults` entrant above, and nothing else
    # -- triple and total move by the same one, so the compensating-pair check
    # this pin exists for reads clean, second consecutive clean read.
    # 242 -> 243 (D-445): the single `defaults` entrant above, and nothing
    # else -- triple and total move by the same one, so the compensating-pair
    # check this pin exists for reads clean.
    # 243 -> 244 (D-446): the single `defaults` entrant above, and nothing
    # else -- triple and total move by the same one, so the compensating-pair
    # check this pin exists for reads clean, fourth consecutive clean read.
    # 245 -> 246 (D-484): the single `decides` entrant above
    # (`lam_inertness.probe`), and nothing else -- triple and total move by the
    # same one, so the compensating-pair check this pin exists for reads clean,
    # fifth consecutive clean read. Recorded also because the entrant is the
    # first to move this pin from the *decides* side: the four before it were
    # all `defaults`.
    assert c.total == 246
    # 2 -> 3 (D-325) — the registry-contract test; see
    # `test_inert_defaults_are_only_construction_contract_tests` for why that
    # shape is inert and why the rule there is now an allowlist.
    # 3 -> 4 (D-411): `_cost_at`, and it is the *purest* instance of the shape
    # that allowlist exists for. It calls `ctrl._cost(...)` directly, and `lam`
    # is the softmax temperature applied to the vector `_cost` returns -- so
    # the rung is not merely unused-by-accident here, it is unreachable from
    # the code under test. Spelling one would be asserting its own argument.
    # 4 -> **17** (D-428). All 13 entrants are inert, which is why
    # `weighting_at_shipped` below is **unmoved at 68** while `defaults` rose by
    # 13: the load-bearing number -- sites that actually weight at an
    # inadmissible temperature -- did not change at all. This is the first
    # cycle in which the gap between `defaults` and the sim bill did the whole
    # work, and it is the reason re-pinning is the honest repair here rather
    # than a compliance regression to be argued away.
    # 17 -> **21** (D-440). Four entrants, all in `test_heading_price_absence.py`,
    # and all four are the `_cost_at` shape this test's allowlist already
    # describes: they construct `StockMPPI` only to interrogate `_cost`
    # directly on a hand-built rollout array, so no temperature is reachable.
    # The file's other two `defaults` sites *do* simulate (the two n=16
    # ensembles) and correctly stay out of this count -- the same
    # defaults-vs-sim-bill gap the paragraph above describes, arriving again.
    assert c.inert_defaults == 21
    # 52 through D-059. Reads 53 as of D-060 and **the sim bill is still 52**:
    # `simulates` is static call-graph reachability, so the new site inherits
    # `batch_per_unit_spread`'s controller step even though its `KeyError` fires
    # first and no controller is ever built. The detector cannot see that, and
    # `inert_defaults` is derived from the same detector, so it does not
    # subtract it. Pinned at the detector's reading, with the true bill named —
    # the alternative is a hand-maintained exemption, which is the shape this
    # package has now been wrong about nine cycles running (Q-073).
    #
    # 56 -> **57** (D-225): the derived count follows its base, `defaults` 58 ->
    # 59 less the unmoved 2 inert. The entrant is a test, so it really does
    # weight at the shipped rung — this is the honest direction of the drift,
    # not the detector's blind spot the paragraph above is about.
    #
    # 57 -> **58** (D-234), and the *same* entrant shape as D-225 one cycle
    # later: `test_the_recorded_family_walks_are_re_derivable` calls
    # `walk_cells` for the two new cafe scenes and names no rung, so the
    # re-derivation runs at the shipped 0.1 exactly as its predecessor did.
    # Being census-aware in the module still does not make the module's test
    # census-aware -- the twelfth consecutive cycle whose new code lands in a
    # census its own package takes, and `decides` is again unmoved (83).
    #
    # 59 -> **63** (D-264): the derived count follows its base again, `defaults`
    # 61 -> 65 less the unmoved 2 inert. Four of the entrants weight at the
    # shipped rung, and three of those are `arm_audibility`'s sim-backed tests
    # -- the same honest-drift direction as D-225 and D-234, now the thirteenth
    # consecutive cycle landing new code in a census its own package takes.
    # 63 -> 64 (D-265): the new sim-backed ladder test constructs at the
    # shipped `MPPIParams.lam` like the three `arm_audibility` tests
    # before it, for the same reason (see `test_census_counts_are_pinned`).
    # 64 -> 65 (D-266): `test_bisect_point_reproduces` re-measures one point of
    # the new bisect table, so it constructs at the shipped rung for the same
    # reason as every entrant since D-225. This assert sits *after* the census
    # tuple above and was masked by it when D-266 repaired that one against a
    # `-k`-filtered run -- a filtered run stops at the first failing assert in a
    # test and reports the later pins as clean. Repair the whole test body, not
    # the line the filter happened to reach.
    # 65 -> 68 (D-411): the derived count follows its base once more, `defaults`
    # 68 -> 72 less the **moved** inert 3 -> 4. Three of D-410's four entrants
    # really do weight at the shipped rung -- they are sim-backed and the
    # measurement is about the shipped configuration -- and the fourth is
    # `_cost_at`, which never reaches a softmax at all. So the honest split is
    # +3 here and +1 inert, not +4 either way.
    # 68 -> **70** (D-440): the two n=16 ensemble sites in
    # `test_heading_price_absence.py`. They simulate, so unlike that
    # file's other four entrants they bill here rather than in
    # `inert_defaults` -- the split these two pins exist to keep visible.
    # 70 -> **71** (D-442): `avoidance_price.measure_arm`, the same single
    # entrant the triple and the total record. It lands on this side because
    # the two arms it compares differ in `w_heading` alone -- a named rung
    # would have added the one difference the correlation excludes.
    # 71 -> **72** (D-444): `avoidance_timing.measure_arm`, the same single
    # entrant the triple and the total record, landing on this side for the
    # same reason D-442's did -- the arms it compares differ in `w_heading`
    # alone, and `simulates=True`, so it weights at the shipped rung rather
    # than falling to `inert_defaults`.
    # 72 -> **73** (D-445): `avoidance_aim.measure_arm`, the same single entrant
    # the triple and the total record, and the *third* consecutive reading-module
    # to land on this side for one reason -- its two arms differ in `w_heading`
    # alone, so a named rung would introduce the one difference the reading is
    # built to exclude. Three in a row is why this pin and the triple keep moving
    # together: on this scene the shape of a reading-module is fixed, and the
    # census is measuring the shape rather than the module.
    # 73 -> **74** (D-446): `avoidance_budget.measure_arm`, the same single
    # entrant the triple and the total record, and the *fourth* consecutive
    # reading-module to land on this side for the identical reason -- its two
    # arms differ in `w_heading` alone, so a named rung would introduce the one
    # difference the reading is built to exclude. This pin is one of the two
    # `census_preempt` does **not** re-derive (the other is `decides -
    # defaults` below), so it went red here after a *clean* pre-empt pass --
    # which is the sixth data point for Q-183 and the one that makes the case
    # concrete: the pre-empt's `UNCOVERED` line is not a footnote, it is a list
    # of the pins that still cost a suite.
    # 74 -> **75** (D-447), `crossing_geometry.measure_arm`, the sixth
    # consecutive reading-module to land on this side for the identical reason.
    # Q-183's **eighth** data point, and the sharpest: this cycle's
    # `census_preempt` pass came back CLEAN on all six re-derived censuses
    # *after* the triple was repaired, and this pin and `decides - defaults`
    # below still went red in the same run. The pre-empt named its own blind
    # spot in the `UNCOVERED` line and the blind spot is where the cost landed
    # -- twice in a row now (D-446 was the sixth data point, this the eighth).
    assert c.weighting_at_shipped == 75


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

    Margin 23 → **24** (D-222): one site, from the `decides` side again, and the
    third consecutive cycle the margin grew with `defaults` unmoved. Three is
    still not a property of the repo — `test_structural_null.py`'s 21 sites
    remain larger than the whole margin, so removing that one file still
    re-crosses the inequality. What three one-sided cycles running *does* say is
    that entrants are no longer arriving silent about their rung, which is the
    only mechanism by which this stops depending on one file.

    Margin 24 → **25** (D-223): one site, `decides` side, **fourth** consecutive
    one-sided cycle. Still not a property of the repo by the same arithmetic —
    21 < 25 now, so `test_structural_null.py` alone no longer re-crosses the
    inequality on its own, but it is one site short of that and the claim is
    not worth making on a one-site cushion.

    Margin 25 → **24** (D-225), and the first cycle in five to move it *down*:
    `walk_cells`' entrant pair is `defaults` +1 / `forwards` +1 with `decides`
    unmoved, so the inequality narrows for the first time since D-219. The
    one-site cushion the paragraph above declined to build a claim on has now
    been spent in the other direction, which is the argument for having declined.
    Margin 23 -> **25** (D-240), back up by two: `test_social_mppi_arm.py`'s
    three constructions all name their rung, so the entrant is `decides`-only
    and the inequality widens. The contrast with D-225 one paragraph up is the
    whole point of tracking the margin rather than the raw counts -- the same
    size of entrant moves it either way depending on whether the rung is spelled.

    Margin 24 -> **27** (D-243), the largest single-cycle widening yet, and by
    exactly the mechanism the paragraph above names: `test_progress_price.py`'s
    entrant is `decides`-only (+3/+0/+0) because the rung is spelled at all three
    sites. The contrast with D-225's -1 is now three data points deep and says the
    same thing each time -- the margin tracks a *habit*, not a volume of code.

    Margin 27 -> **30** (D-244), and it beats D-243's record by the same
    mechanism read one step earlier: `freeze_weight`'s entrant was +3/+0 only
    *after* the census convicted its CLI, which had shipped the rung defaulted.
    Four data points now, and the reading is unchanged -- the margin widens when
    the rung is spelled and narrows when it is inherited, regardless of size.

    Margin 30 -> **31** (D-245), the smallest widening recorded and the cheapest
    to explain: one new measured pin, entering `decides` because the temperature
    it is *about* is the temperature it names (`MPPIParams(lam=fw.PAIRED_LAM)`).
    Fifth data point, same reading. Worth setting against D-244's entry -- that
    cycle needed the census to convict a defaulted CLI first; this one was
    spelled in the first draft, which is what the habit looks like once taken.

    Margin 31 -> **34** (D-248). Sixth data point, same reading: `arrival_spread`
    is +3/+0 and every site is a rung the entrant spelled -- two `sweep(..., lam=)`
    calls including the CLI that D-244 had to be convicted over, plus
    `stall_split`'s. The margin moved by exactly the number of rungs spelled.

    Margin 34 -> **35** (D-250). Seventh data point, same reading: `freeze_weight`
    is +1/+0 and the site is a rung the entrant spelled. The margin moved by
    exactly the number of rungs spelled.

    Margin 36 -> **32** (D-264), and this is the first entrant to move it
    *down*. Same reading, opposite sign: `arm_audibility` spelled no rungs at
    all (+0 `decides`) and added four `defaults`, so the margin fell by exactly
    the number of unspelled constructions. The claim the test name makes is
    unchanged — 97 > 65 — but the direction is worth watching, because it is
    the first evidence that the margin is not monotone and that a module can be
    added without naming its temperature.
    """
    c = dls.census()
    assert c.decides > c.defaults
    # 32 -> 31 (D-265). Second entrant in a row to move the margin *down*,
    # and by the same mechanism D-264 named: a module that spells no rung
    # (+0 `decides`) but constructs at the shipped default (+1 `defaults`).
    # The claim the test name makes is unchanged -- 97 > 66.
    # 31 -> 30 (D-266). Third entrant in a row to move the margin *down*, and
    # by the same mechanism twice named: a module that spells no rung
    # (+0 `decides`) but adds a sim-backed test at the shipped default
    # (+1 `defaults`). Three consecutive falls is no longer a curiosity -- the
    # margin's drift is downward whenever new work is *measurement* rather than
    # *tuning*, which is what this branch has been doing since D-263.
    # 30 -> 31 (D-274). The first entrant in four cycles to move the margin
    # back *up*, and it breaks the pattern the D-266 note describes rather than
    # continuing it: this cycle's work is measurement too, but the measurement
    # is *about the temperature*, so its one site spells `OPERATING_LAM` and
    # bills `decides` (+1) with `defaults` unmoved. That is the distinction the
    # three notes above were groping toward — the margin falls when new work
    # measures something at whatever temperature happens to be shipped, and
    # rises when the temperature is the object of study.
    # 31 -> 33 (D-327). Both new sites bill `decides` with `defaults` unmoved,
    # so the margin rises by the full two — the largest single-cycle rise in
    # this pin's history. It fits the D-274 note exactly: the margin rises when
    # the temperature is *the object of study*, and a census that compares
    # eight arms cannot let any of them pick its own.
    # 33 -> 34 (D-330). One `decides` entrant, `defaults` unmoved, so the
    # margin rises by one -- the D-274 reading again, third consecutive
    # cycle: this branch's new work is all census work, and a census names
    # its temperature by construction.
    # 34 -> 35 (D-334). One `decides` entrant, `defaults` unmoved, so the
    # margin rises by one -- the D-274 reading a fourth consecutive time, and
    # the entrant is again a census (`scene_separability.retake_observables`
    # names `lam = OPERATING_LAM` because a separability table read at a
    # temperature the module did not choose would be measuring the default).
    # 35 -> 36 (D-376). One `decides` entrant, `defaults` unmoved, so the margin
    # rises by one -- the D-274 reading a fifth consecutive time, and the
    # entrant is again a census (`tail_stability.retake` names
    # `lam = OPERATING_LAM` because a tail read across eight arms at whatever
    # temperature each happened to ship would be measuring the default).
    # 36 -> 37 (D-383). A **sixth** consecutive time, same shape and same
    # reason: `tail_mean.retake` names `lam = OPERATING_LAM` because a TVaR
    # column harvested at whatever temperature each arm happened to ship would
    # be measuring the default rather than the operating point it is graded at.
    # Six in a row is no longer a coincidence -- every new census this branch
    # writes lands in `decides`, which is what compliance looks like once the
    # spelling is the habit rather than the exception.
    # 37 -> 38 (D-390). A **seventh**, and the tightest instance of the reason:
    # `tail_mean.retake_max` names `lam = OPERATING_LAM` because the *whole*
    # finding is that the `cte_max` column was previously harvested at a
    # different rung. A re-derivation that inherited the default would reproduce
    # the very defect Q-175 was opened to repair.
    # 38 -> **34** (D-411), and the first time in nine cycles this margin has
    # moved *down*. Every entrant since D-383 widened it from the `decides`
    # side; D-410's four widen the `defaults` side instead, because the module
    # measures the shipped configuration and naming a rung would change what it
    # measures. Worth recording plainly: the narrowing is the honest reading,
    # not a regression in compliance. The crossover still holds (106 > 72) with
    # room, but this is the first evidence that "entrants no longer arrive
    # silent about their rung" is a claim about the *kind* of module recent
    # cycles wrote, not a property the census enforces.
    # 34 -> **21** (D-428), and it dwarfs every prior move in this pin's
    # history (largest before: 3). Same reading as D-264/D-411, same sign, new
    # magnitude: `test_barrier_shape.py` spells no rung at all (+0 `decides`)
    # and constructs 13 times at the shipped default. The claim the test name
    # makes still holds -- 106 > 85 -- but the margin has now given back nine
    # cycles of accumulated widening in one commit, which is the clearest
    # evidence yet that the D-383 note ("every new census this branch writes
    # lands in `decides`") described a habit of *census* modules specifically,
    # not a property the census can enforce on a cost-function test file.
    # 21 -> **15** (D-440): six `defaults` entrants, no `decides` entrant, so
    # the margin narrows by the full six. The test's claim (106 > 91) still
    # holds, but this is the second consecutive commit in which a *cost-
    # function* test file -- not a census module -- did all the moving, which
    # is the D-383 note above being confirmed rather than eroded.
    # 15 -> **14** (D-442): `defaults` took the single entrant and `decides`
    # took none, so the gap narrows by one. Direction worth stating: this
    # margin has been closing since D-411, and it is the *shipped default*
    # side that keeps growing.
    # 14 -> **13** (D-444): `defaults` took the single entrant and `decides`
    # took none, so the gap narrows by one again -- the *third* consecutive
    # cycle in which it does, and the second in a row from a reading-module
    # rather than a census module. The direction D-442 flagged is holding, so
    # it is worth saying what would reverse it: a cycle that names a rung.
    # 13 -> **12** (D-445): the same shape a *fourth* consecutive time, and the
    # third in a row from a reading-module. D-444 asked what would reverse the
    # direction and answered "a cycle that names a rung"; D-445 is a cycle that
    # considered naming one and declined on the merits -- it re-reads D-444's
    # runs, so a literal rung here could drift away from the default those runs
    # were taken at. Worth recording because it means the margin is not closing
    # through inattention: each of the four narrowings had a reason, and it was
    # the same reason.
    # 12 -> **11** (D-446), the fifth consecutive narrowing, and the fifth to
    # have a reason rather than to happen by inattention: `avoidance_budget`
    # declined a named rung on exactly D-445's grounds, since it re-reads
    # D-445's own runs and a literal here could drift away from the default
    # those runs were taken at. The margin is now 11 and every step of its
    # decline is attributable, which is what this pin exists to establish --
    # a shrinking margin is only alarming if nobody can say why it shrank.
    # 11 -> **10** (D-447), the sixth consecutive narrowing and the sixth with
    # a reason rather than by inattention: `crossing_geometry` declined a named
    # rung on exactly D-445's and D-446's grounds, since it re-reads D-446's own
    # runs and a literal here could drift away from the default those runs were
    # taken at. Every step of the decline from 12 remains attributable.
    # 10 -> **11** (D-484), and it is the first *widening* since the pin was
    # written: `lam_inertness.probe` adds a `decides` and no `defaults`, so the
    # six-cycle decline breaks here rather than continuing. The reason is the
    # entrant's subject: a module that sweeps `lam` deliberately cannot take
    # the shipped default anywhere, so it contributes to the good column only.
    assert c.decides - c.defaults == 11


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


def test_inert_defaults_are_only_construction_contract_tests():
    """Reported, not netted out -- 52 is the load-bearing number and it should
    not be reachable only by subtracting an unexamined residual.

    2 -> 3 (D-325). The rule was ``"raises" in s.function``, which admitted a
    third legitimate shape only by accident of naming: a test that constructs
    through `make_controller` to prove the **registry resolves a name** and
    then asserts on the object, never simulating. That is the same kind of
    inertness the two `raises` tests have -- the temperature is never used, so
    spelling one would make the test assert its own argument -- but the
    substring rule could not say so.

    Replaced with an explicit allowlist rather than a widened substring, which
    *tightens* the check: under the old rule any new inert site could join by
    being named ``..._raises_...``; under this one a new entrant has to be
    added here in the same commit, which is the property the census wants.

    3 -> 4 (D-411), and the property above is exactly what failed to happen:
    `_cost_at` arrived in D-410's commit and this allowlist did not, so the
    branch pushed nothing and sat red for a cycle. The entrant is legitimate --
    it constructs a controller only to call `_cost` on it, and `lam` is applied
    to that function's *output*, so no temperature is reachable from what the
    test exercises. That makes it a stronger member than the three above it:
    those never use the rung, this one cannot.

    4 -> **17** (D-428), and the D-411 note above repeated at scale: the
    entrants arrived in D-427's commit and this allowlist did not, so the
    branch committed red and stranded for two cycles before anyone read it.
    All 13 are the `_cost_at` shape rather than the `raises` shape -- each
    constructs a `StockMPPI` only to interrogate its **cost function**
    (`_cost`, `_soft_obstacle_cost`), and `lam` is applied to that function's
    *output* in the softmax, so no temperature is reachable from what the tests
    exercise. Listed one line per site including the duplicates, because a
    function that constructs twice is two sites and netting them out here would
    reintroduce exactly the subtraction this test exists to avoid.
    """
    inert = [s for s in dls.sites()
             if s.kind == dls.DEFAULTS and not s.simulates]
    assert sorted(s.function for s in inert) == [
        "_cost_at",                                # D-411, cost-vector helper
        # D-427/D-428 — barrier-shape cost-function tests, `lam` downstream.
        "test_band_changes_cost_through_both_obstacle_branches",
        "test_band_changes_cost_through_both_obstacle_branches",
        "test_band_has_compact_support",
        "test_band_has_compact_support",
        "test_band_is_positive_and_decreasing_inside",
        "test_both_forms_agree_at_contact",
        "test_both_forms_agree_at_contact",
        # D-440 — heading-price cost-function tests, the same `_cost_at` shape:
        # each builds a rollout array by hand and reads `_cost` off it, so no
        # temperature is reachable. Interleaved rather than grouped because the
        # list is `sorted()` and grouping by decision would not survive it.
        "test_default_is_unpriced",
        "test_far_field_soft_cost_is_exactly_zero_under_the_band",
        "test_far_field_soft_cost_is_exactly_zero_under_the_band",
        "test_inert_means_the_legacy_exponential_exactly",
        "test_legacy_barrier_has_no_such_far_field",
        "test_legacy_barrier_has_no_such_far_field",
        "test_penetration_still_costs_more_than_contact",
        "test_priced_when_weight_positive",         # D-440, twice: on and off
        "test_priced_when_weight_positive",
        "test_registered_and_constructible",       # D-325, registry contract
        "test_unknown_controller_raises_with_available_list",
        "test_unknown_nominal_raises",
        "test_wrapping_is_symmetric_and_bounded",   # D-440
    ], [s.function for s in inert]


# --------------------------------------------------------------------------
# 4. What the count means -- the link to D-040.
# --------------------------------------------------------------------------

def test_every_defaulting_site_runs_at_the_shipped_lam():
    for site in dls.sites():
        if site.kind == dls.DEFAULTS:
            assert site.at_shipped_lam


def test_the_shipped_lam_those_sites_take_is_admissible_on_one_column_only():
    """The join with D-040. Was `…_is_admissible_nowhere`, and D-477 is what
    moved it — this test was written to move (see the second paragraph of its
    old docstring, kept below), so the rename is the mechanism working.

    The rung 52 live sites take used to qualify in **0 of 24** cells. D-470's
    8-controller walk widens the denominator to 72 (80 rows with the variant
    weights joined in), and the answer is now **8**, not 0.

    **The 8 are not scattered — they are one controller column.** Every scene's
    `essps_mppi` arm admits `lam = 0.1`, and no other arm does at any scene. So
    the claim D-040 rests on is unchanged in substance for the 7 columns it was
    measured over, and the exception is a single arm that was never offered to
    the calibrator until now (D-469). That is a sharper statement than "0 of
    24" was: the default rung is not universally wrong, it is right for exactly
    one controller and wrong for the other seven.

    Read from ``operating_point`` rather than restated, so a recalibration that
    moves the windows moves this claim instead of leaving it stale.
    """
    admitting = {key for key, rungs in op.windows().items()
                 if op.SHIPPED_LAM in rungs}
    assert len(admitting) == 8, sorted(admitting)
    assert {controller for _scene, controller in admitting} == {"essps_mppi"}, (
        f"the shipped rung now admits outside the essps column: "
        f"{sorted(admitting)} — D-040's premise is what changed, not this test")
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
