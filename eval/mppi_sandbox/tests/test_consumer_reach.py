"""`consumer_reach` — the D-188 shape, made into a reading.

Two populations are asserted here and they answer different questions.  The
synthetic trees (`tmp_path`) pin the *grading rules*, because the input to this
instrument genuinely is source text and writing that text by hand is not the
D-188 sin — it is the subject.  The real-package tests pin the *finding*, which
is the half a synthetic tree can never establish (D-139: make the generator
reproduce its own table).
"""

from __future__ import annotations

import textwrap

from eval.mppi_sandbox import consumer_reach as cr


def _tree(tmp_path, files: dict[str, str]):
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
    return tmp_path


def _source_of(defn) -> str:
    """The `def` block a `Definition` points at, read off disk.

    Derived rather than typed: the alternative is a hand-kept list of which
    residue members are deliberately uncovered, which is the unwatched
    allow-list shape D-189 replaced with a rule.
    """
    path = cr.SANDBOX_DIR / f"{defn.module}.py"
    lines = path.read_text(encoding="utf-8").splitlines()
    body = []
    for line in lines[defn.lineno - 1:]:
        if body and line and not line[0].isspace():
            break
        body.append(line)
    return "\n".join(body)


def _by_name(rows):
    return {r.definition.name: r for r in rows}


# --------------------------------------------------------------------------
# the headline: a mention is not a call, and only a parser can tell
# --------------------------------------------------------------------------

def test_prose_mentions_do_not_make_a_constructor_live(tmp_path):
    """The exact shape that made `grep -rn from_sweep` read clean.

    Three prose hits — a module docstring, a method docstring, a comment — and
    zero calls.  A line-oriented search reports four matches and concludes the
    constructor is used; the parser sees none of them.
    """
    root = _tree(tmp_path, {
        "defs.py": '''
            class WalkCount:
                @classmethod
                def from_sweep(cls, stats):
                    return cls()
        ''',
        "caller.py": '''
            """`WalkCount.from_sweep` — the constructor that consumes it."""

            def _rung(stats):
                """The `k` a rate estimator wants, so that `from_sweep` works."""
                # this is the line that makes `from_sweep` reachable
                return stats
        ''',
        "tests/test_defs.py": '''
            from defs import WalkCount

            def test_it():
                assert WalkCount.from_sweep(None)
        ''',
    })

    row = _by_name(cr.reaches(root))["from_sweep"]
    assert row.verdict == "TEST_ONLY"
    assert row.prod_calls == 0
    assert row.prod_mentions == 0
    assert row.test_calls == 1
    assert row.is_finding

    # and the search that missed it would have found four lines
    hits = sum(f.read_text().count("from_sweep") for f in cr.source_files(root))
    assert hits >= 4


def test_a_real_production_call_makes_it_live(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @classmethod
                def build(cls, x):
                    return cls()
        ''',
        "caller.py": '''
            from defs import C

            def go(x):
                return C.build(x)
        ''',
    })
    assert _by_name(cr.reaches(root))["build"].verdict == "LIVE"


def test_calling_module_is_its_own_caller(tmp_path):
    """A constructor used by its defining module is live — not a foreign-caller test."""
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @classmethod
                def build(cls):
                    return cls()

                @classmethod
                def wrapper(cls):
                    return cls.build()
        ''',
    })
    rows = _by_name(cr.reaches(root))
    assert rows["build"].verdict == "LIVE"
    assert rows["wrapper"].verdict == "UNREACHED"


def test_nothing_anywhere_is_unreached_not_test_only(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @staticmethod
                def orphan():
                    return 1
        ''',
    })
    assert _by_name(cr.reaches(root))["orphan"].verdict == "UNREACHED"


# --------------------------------------------------------------------------
# the escape hatch bends toward silence, on purpose
# --------------------------------------------------------------------------

def test_string_dispatch_key_downgrades_to_referenced_not_called(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @classmethod
                def from_json(cls, s):
                    return cls()
        ''',
        "registry.py": '''
            HOOKS = {"from_json": None}
        ''',
        "tests/test_defs.py": '''
            from defs import C

            def test_it():
                assert C.from_json("{}")
        ''',
    })
    row = _by_name(cr.reaches(root))["from_json"]
    assert row.verdict == "REFERENCED_NOT_CALLED"
    assert not row.is_finding, "a dispatch-reachable name must not be a finding"


def test_attribute_mention_without_call_downgrades(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @classmethod
                def make(cls):
                    return cls()
        ''',
        "user.py": '''
            from defs import C

            FACTORY = C.make
        ''',
    })
    assert _by_name(cr.reaches(root))["make"].verdict == "REFERENCED_NOT_CALLED"


def test_prose_string_that_is_not_an_identifier_is_not_a_mention(tmp_path):
    """`"call from_sweep here"` is prose; only a bare identifier is a dispatch key."""
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @classmethod
                def make(cls):
                    return cls()
        ''',
        "user.py": '''
            NOTE = "you should call make eventually"
        ''',
        "tests/test_defs.py": '''
            from defs import C

            def test_it():
                assert C.make()
        ''',
    })
    assert _by_name(cr.reaches(root))["make"].verdict == "TEST_ONLY"


def test_homonym_under_reports_and_that_is_the_safe_direction(tmp_path):
    """Two classes, one name: the live one rescues the dead one.

    Pinned because it is the documented cost of name-based matching. It can
    only hide a finding, never invent one.
    """
    root = _tree(tmp_path, {
        "a.py": '''
            class A:
                @classmethod
                def load(cls):
                    return cls()
        ''',
        "b.py": '''
            class B:
                @classmethod
                def load(cls):
                    return cls()
        ''',
        "caller.py": '''
            from a import A

            def go():
                return A.load()
        ''',
    })
    rows = cr.reaches(root)
    assert {r.verdict for r in rows} == {"LIVE"}
    assert len(rows) == 2


# --------------------------------------------------------------------------
# population boundaries
# --------------------------------------------------------------------------

def test_plain_methods_are_not_in_the_population(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                def method(self):
                    return 1

                @property
                def prop(self):
                    return 2

                @classmethod
                def ctor(cls):
                    return cls()
        ''',
    })
    assert [d.name for d in cr.definitions(root)] == ["ctor"]


def test_definitions_exclude_tests_but_calls_from_tests_still_count(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @classmethod
                def ctor(cls):
                    return cls()
        ''',
        "tests/test_helper.py": '''
            class Helper:
                @classmethod
                def helper_ctor(cls):
                    return cls()

            def test_it():
                from defs import C
                assert C.ctor()
        ''',
    })
    names = [d.name for d in cr.definitions(root)]
    assert names == ["ctor"], "a test-local helper is not the defect"
    assert _by_name(cr.reaches(root))["ctor"].test_calls == 1


def test_protocol_hooks_are_excluded(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @staticmethod
                def __new__(cls):
                    return object.__new__(cls)
        ''',
    })
    assert cr.definitions(root) == []


def test_dotted_decorator_form_is_recognised(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            import builtins

            class C:
                @builtins.classmethod
                def ctor(cls):
                    return cls()
        ''',
    })
    assert [d.name for d in cr.definitions(root)] == ["ctor"]


def test_unparsable_file_is_skipped_not_fatal(tmp_path):
    root = _tree(tmp_path, {
        "broken.py": "def (((:\n",
        "defs.py": '''
            class C:
                @classmethod
                def ctor(cls):
                    return cls()
        ''',
    })
    assert [d.name for d in cr.definitions(root)] == ["ctor"]


def test_the_def_line_is_not_a_call_or_a_mention(tmp_path):
    root = _tree(tmp_path, {
        "defs.py": '''
            class C:
                @classmethod
                def ctor(cls):
                    return cls()
        ''',
    })
    row = _by_name(cr.reaches(root))["ctor"]
    assert (row.prod_calls, row.prod_mentions, row.test_calls) == (0, 0, 0)


def test_reaches_is_sorted_and_deterministic(tmp_path):
    root = _tree(tmp_path, {
        "z.py": "class Z:\n    @classmethod\n    def z(cls): return cls()\n",
        "a.py": "class A:\n    @classmethod\n    def a(cls): return cls()\n",
    })
    names = [r.definition.qualname for r in cr.reaches(root)]
    assert names == sorted(names)
    assert names == [r.definition.qualname for r in cr.reaches(root)]


# --------------------------------------------------------------------------
# the real package — the half a synthetic tree cannot establish
# --------------------------------------------------------------------------

def test_from_sweep_is_the_residue_on_the_real_package():
    """D-188 said `from_sweep` gains "the repo's first production caller". It did not.

    D-188 made `Rung` carry `n_in_band`/`n_reached`, which satisfies the
    constructor's duck type — but satisfying an argument's shape is not calling
    the function, and no production path calls it. This is the instrument
    reproducing the defect that motivated it, one frame further out than the
    cycle that thought it had closed it.
    """
    rows = _by_name(cr.reaches())
    assert "from_sweep" in rows, "population lost its motivating instance"
    row = rows["from_sweep"]
    assert row.definition.module == "seed_count_licence"
    assert row.definition.cls == "WalkCount"
    assert row.verdict == "TEST_ONLY"
    assert row.prod_calls == 0
    assert row.test_calls > 0


def test_real_package_findings_are_exactly_the_known_residue():
    """A pinned residue, so a *new* dead constructor turns this red.

    Clearable in both directions: wire a production caller (the verdict flips
    to LIVE) or delete the constructor (it leaves the population). D-044.
    """
    assert sorted(r.definition.qualname for r in cr.findings()) == [
        "seed_count_licence.WalkCount.from_sweep",
    ]


def test_real_package_population_is_small_and_all_others_are_live():
    rows = cr.reaches()
    assert len(rows) >= 4
    live = [r for r in rows if r.verdict == "LIVE"]
    assert len(live) == len(rows) - len(cr.findings())


def test_report_names_the_finding_and_check_refuses():
    text = cr.report()
    assert "TEST_ONLY" in text
    assert "from_sweep" in text
    assert cr.main(["report"]) == 0
    assert cr.main(["check"]) == 1


# ---------------------------------------------------------------------------
# Population B — module-level public functions (D-191)
# ---------------------------------------------------------------------------


def _write_module(tmp_path, name, body):
    (tmp_path / name).write_text(body, encoding="utf-8")


def test_module_population_is_top_level_public_only(tmp_path):
    """Closures and `_private` names are not part of a module's call surface."""
    _write_module(tmp_path, "m.py", textwrap.dedent("""
        def public():
            def closure():
                return 1
            return closure()

        def _private():
            return 2

        class K:
            def method(self):
                return 3
    """))
    names = {d.name for d in cr.module_functions(tmp_path)}
    assert names == {"public"}


def test_module_scope_qualname_omits_the_empty_class(tmp_path):
    _write_module(tmp_path, "m.py", "def solo():\n    return 1\n")
    only = cr.module_functions(tmp_path)[0]
    assert only.scope == "module"
    assert only.qualname == "m.solo"


def test_test_only_is_a_finding_for_a_constructor_and_not_for_a_function(tmp_path):
    """The asymmetry that makes B reportable at all.

    An assertion helper the suite calls is *being used for its purpose*; a
    constructor only its own tests reach is the `from_sweep` defect. Same
    verdict string, opposite readings — so `is_finding` keys on scope.
    """
    _write_module(tmp_path, "m.py", textwrap.dedent("""
        class K:
            @classmethod
            def from_thing(cls):
                return cls()

        def assert_thing():
            return True
    """))
    (tmp_path / "tests").mkdir()
    _write_module(tmp_path / "tests", "test_m.py", textwrap.dedent("""
        from m import K, assert_thing

        def test_it():
            K.from_thing()
            assert_thing()
    """))
    ctor = cr.reaches(tmp_path)
    funcs = cr.module_reaches(tmp_path)
    assert [(r.verdict, r.is_finding) for r in ctor] == [("TEST_ONLY", True)]
    assert [(r.verdict, r.is_finding) for r in funcs] == [("TEST_ONLY", False)]


def test_unreached_is_a_finding_in_both_populations(tmp_path):
    _write_module(tmp_path, "m.py", textwrap.dedent("""
        class K:
            @classmethod
            def from_thing(cls):
                return cls()

        def orphan():
            return True
    """))
    assert [r.is_finding for r in cr.reaches(tmp_path)] == [True]
    assert [r.is_finding for r in cr.module_reaches(tmp_path)] == [True]


def test_pytest_hook_grades_framework_dispatched_not_unreached(tmp_path):
    """A hook pytest resolves by name has no in-repo call site by construction.

    It is *graded into its own verdict* rather than filtered out — a filter
    would be a fifth unwatched allow list, which is the defect
    `guard_reflexivity` counts.
    """
    _write_module(tmp_path, "m.py", textwrap.dedent("""
        def pytest_configure(config):
            return None

        def orphan():
            return None
    """))
    graded = {r.definition.name: r.verdict for r in cr.module_reaches(tmp_path)}
    assert graded == {"pytest_configure": "FRAMEWORK_DISPATCHED",
                      "orphan": "UNREACHED"}
    assert cr.module_findings(tmp_path) == [
        r for r in cr.module_reaches(tmp_path) if r.definition.name == "orphan"]


def test_a_called_pytest_hook_is_live_not_framework_dispatched(tmp_path):
    """The prefix rule only fires where there is nothing else to say.

    Otherwise `FRAMEWORK_DISPATCHED` would mask a hook that *is* called, and
    the verdict would stop meaning "no in-repo call site".
    """
    _write_module(tmp_path, "m.py", textwrap.dedent("""
        def pytest_configure(config):
            return None

        def driver():
            return pytest_configure(None)
    """))
    graded = {r.definition.name: r.verdict for r in cr.module_reaches(tmp_path)}
    assert graded["pytest_configure"] == "LIVE"


def test_module_residue_on_the_real_package_is_pinned():
    """The ratchet. B is reported, not gated — this is what stops it growing.

    `check` grades A only: uncalled functions cannot be cleared in one cycle
    and a red that stands for weeks is a red nobody reads (D-044). So the
    residue is pinned by name here instead. Deleting one of these, or giving
    it a caller, means editing this list — which is the point. Growing it
    silently is what the pin forbids.

    Down one from 11: `candidate_scope.stale_grades` now has a caller, and it
    is the only member so far whose fix was *running* it rather than editing
    it — it is `GRADED`'s watcher, so a test that calls it is the use it was
    written for. Down one again to 9: `reading_record.take_and_record` now
    grades `DEFERRED_BY_COST` (D-193) and left the finding count without
    leaving the report. The nine below are deliberately **not** given callers;
    see `test_a_manufactured_caller_is_not_a_fix`.

    This list is also the **watcher** for `DEFERRED_MARKER`. That marker is
    self-serve — any signature can type it — so what stops it becoming a
    silent exemption is that taking it moves a name *out of this list*, which
    cannot happen without editing this test in the same commit.
    """
    assert sorted(r.definition.qualname for r in cr.module_findings()) == [
        # D-248. `stall_splits` is the arm x seed grid entry point; its single
        # element `stall_split` is what the tests exercise, and a caller here
        # would be nine simulations inside the fast suite. Listed rather than
        # given a manufactured caller, per the docstring above.
        "arrival_spread.stall_splits",
        "assert_reach.asserts_in",
        "calibrate_lam.scene_is_calibratable",
        # D-271. `sweep_seeds` is the seed-ensemble entry point — eight
        # closed-loop runs plus eight cost-field reads, so a caller here would
        # put a minutes-scale sim inside the fast suite. Same trade as
        # `sweep_ess` below: the recorded table (`MEASURED_SEEDS`) is what the
        # tests exercise. Listed by D-272, which found the pin left red by the
        # cycle that added the function.
        "calibrated_ladder.sweep_seeds",
        # D-268. `sweep_ess` is the ESS ladder entry point — five closed-loop
        # runs, so a caller here would put a minutes-scale sim inside the fast
        # suite. The recorded table it produces (`MEASURED_ESS`) is what the
        # tests exercise instead, the same trade `arm_audibility.sweep_ratio`
        # already makes for the ratio ladder.
        "ess_at_peak.sweep_ess",
        # D-325. `compare_arms` re-takes `PER_ITERATION_ARMS` — two closed-loop
        # runs (`essps_mppi` and its `risk_mppi` control), so a caller here
        # would put ~26 s of sim in the fast suite. Same trade as
        # `harvest_costs` directly below, and the constants it produced are
        # what `test_essps_mppi.py` exercises instead.
        "essps.compare_arms",
        # D-274. `harvest_costs` captures one episode's rollout cost vectors —
        # a closed-loop run, so a caller here would put a ~13 s sim in the fast
        # suite. Same trade as `sweep_ess` directly above and for the same
        # reason: the recorded constants it produced (`SOLVED_LAM`,
        # `MEDIAN_MATCHED`, `COMPLIANCE_OPTIMAL`) are what the tests exercise.
        # Listed in the cycle that added it rather than left for the next one
        # to find red — which is the mistake D-272 had to clean up for D-271.
        "essps.harvest_costs",
        "guard_vacuity.never_fired",
        "horizon_audit.format_scan",
        "inert_surface.reprobe",
        "magnitude_survival.standings",
        "predicate_vacuity.one_sided",
        "predicate_vacuity.unpatchable",
    ]


def test_the_residue_is_not_one_population():
    """The triage, as a reading. `UNREACHED` was one verdict over three kinds.

    D-191 split A from B because one verdict string meant a defect in one
    population and the normal state in the other. The same split was owed one
    level down: "delete or wire" presumes every residue member is debt, and at
    least one is not. `reading_record.take_and_record` costs 2k concurrent
    five-minute suite runs, so the fast suite cannot reach it *by
    construction* — the `FRAMEWORK_DISPATCHED` shape (an absence of callers
    with a structural reason) rather than the dead-code shape. D-193 gives it
    its own verdict, so the finding count no longer carries a known non-defect.
    """
    graded = {r.definition.qualname: r.verdict for r in cr.module_reaches()}
    assert graded["reading_record.take_and_record"] == "DEFERRED_BY_COST"
    assert cr.DEFERRED_MARKER in _source_of(
        next(d for d in cr.module_functions()
             if d.qualname == "reading_record.take_and_record"))
    # One member, and the report still shows it — graded, not filtered.
    deferred = [r.definition.qualname for r in cr.module_reaches()
                if r.verdict == "DEFERRED_BY_COST"]
    assert deferred == ["reading_record.take_and_record"]
    assert "take_and_record" in cr.report()


def test_the_bare_coverage_pragma_confers_nothing(tmp_path):
    """The key STATE proposed, and why it is not the one that shipped (D-193).

    ``# pragma: no cover`` occurs 48× in population B and reads `- CLI` (13×),
    `- reporting` (5×), `- defended` (3×)… It is a *coverage* directive and is
    silent about callers; 43 of those 48 are `LIVE`. Keying the verdict on it
    would have been narrow only by coincidence — two dozen of the 43 are
    reporters kept alive solely by their own ``__main__`` block, so deleting
    that block in a routine refactor would grade a newly-dead function
    `DEFERRED_BY_COST` instead of `UNREACHED`: an exemption that hides a
    finding, granted by a marker never making that claim.

    This is the fixture of that refactor. It must stay `UNREACHED`.
    """
    (tmp_path / "m.py").write_text(textwrap.dedent("""
        def report():  # pragma: no cover - CLI
            return "nobody calls me any more"

        def sugar():  # pragma: no cover - reporting sugar
            return 1
    """))
    graded = {r.definition.name: r.verdict for r in cr.module_reaches(tmp_path)}
    assert graded == {"report": "UNREACHED", "sugar": "UNREACHED"}


def test_the_marker_labels_a_residue_member_it_cannot_manufacture_one(tmp_path):
    """The marker explains an absence of callers; it never overrides a presence.

    Ordered after the reachability verdicts in `_grade`, so a marked function
    that something calls is `LIVE`. A marker able to outrank a measurement
    would be an exemption rather than a label — the shape this package keeps
    removing (D-189, D-192).
    """
    (tmp_path / "m.py").write_text(textwrap.dedent("""
        def expensive():  # pragma: no cover -- deferred-by-cost: 2k runs
            return 1

        def also_expensive():  # pragma: no cover -- deferred-by-cost: hardware
            return 2

        def driver():
            return also_expensive()
    """))
    graded = {r.definition.name: r.verdict for r in cr.module_reaches(tmp_path)}
    assert graded["expensive"] == "DEFERRED_BY_COST"
    assert graded["also_expensive"] == "LIVE"
    assert cr.module_findings(tmp_path) == [] or {
        r.definition.name for r in cr.module_findings(tmp_path)} == {"driver"}


def test_the_marker_is_read_off_the_signature_not_the_body(tmp_path):
    """A comment buried in a body cannot exempt the function it sits in.

    The claim ("nothing calls this, and here is why") belongs at the definition
    site where a reader of the residue will see it, so the scan is bounded to
    the lines between `def` and the first body statement.
    """
    (tmp_path / "m.py").write_text(textwrap.dedent("""
        def sneaky():
            # pragma: no cover -- deferred-by-cost: not where this counts
            return 1
    """))
    graded = {r.definition.name: r.verdict for r in cr.module_reaches(tmp_path)}
    assert graded["sneaky"] == "UNREACHED"


def test_a_manufactured_caller_is_not_a_fix():
    """Why the other nine keep their verdict instead of being cleared.

    `guard_vacuity.never_fired` and `predicate_vacuity.one_sided` are one-line
    accessors their own module docstrings name as the reading's vocabulary —
    true of both only since D-194, which measured the claim and found it held
    for `never_fired` and not for `one_sided`, whose module had cited its
    siblings and not it.  The citation is checked in
    `test_the_vocabulary_defence_is_a_citation_not_an_assertion`, so this pin
    now rests on a verified premise rather than a restated one.
    Nothing calls them because the consumers reach `cens.candidates` directly.
    A call added *to clear this instrument* would be D-189's shape-fitting —
    satisfying a measurement rather than the thing it measures — so the
    honest state is to leave them red and say so. This test fails if a future
    cycle quietly gives one a caller without arguing for it.
    """
    residue = {r.definition.qualname for r in cr.module_findings()}
    assert {"guard_vacuity.never_fired", "predicate_vacuity.one_sided"} <= residue


def _module_docstring(module_stem: str) -> str:
    import ast
    import pathlib
    src = pathlib.Path(__file__).parent.parent / f"{module_stem}.py"
    return ast.get_docstring(ast.parse(src.read_text(encoding="utf-8"))) or ""


#: Residue members whose defence is "this is the module's stated vocabulary".
#: Membership is not the claim — the citation is, and it is checked below.
VOCABULARY_DEFENCE = ("guard_vacuity.never_fired", "predicate_vacuity.one_sided")

#: Residue members whose own module docstring never names them, so the
#: vocabulary defence is unavailable to them and some other argument is owed.
#: `guard_direction.build_stranding_repo` was a fourth member until D-195 found
#: it was never in the residue at all — see the registry tests below.
NO_VOCABULARY_DEFENCE = ("assert_reach.asserts_in",
                         "horizon_audit.format_scan",
                         "inert_surface.reprobe")


def test_a_same_module_registry_entry_is_a_mention():
    """The reference form the escape hatch was missing, on the case that found it.

    STATE sent this cycle to triage four residue members on the premise that
    each owed an argument for staying uncalled.  For one of the four the
    premise was not that the argument was weak — it was that the reading was
    **wrong**.  `guard_direction.PROBES` holds `build=build_stranding_repo` and
    three sites dispatch it as `(probe.build or build_scratch_repo)(repo)`, so
    the builder runs every time that probe runs, and the census reported it
    `UNREACHED` with `mentions=0` — the verdict that means dead code.

    The hatch handled `mod.func` (cross-module attribute) and `"name"` (string
    key) and not the bare same-module name, which is the form a registry
    declared beside its members necessarily takes.  Note which way the blind
    spot cut: it never invented a caller, it only ever *hid* one, so every
    verdict it distorted was distorted toward the finding.
    """
    _, _, mentions = cr.call_census()
    assert mentions.get("build_stranding_repo", 0) >= 1

    by_name = {r.definition.qualname: r for r in cr.module_reaches()}
    entry = by_name["guard_direction.build_stranding_repo"]
    assert entry.verdict == "REFERENCED_NOT_CALLED"
    assert entry.prod_calls == 0, (
        "REFERENCED_NOT_CALLED is the honest ceiling here: the census does not "
        "follow `probe.build` back to this function, so it reports that "
        "somebody holds the name, not that somebody calls it")


def test_the_registry_form_is_not_an_amnesty():
    """The negative control the widened hatch has to pass to be a fix.

    A mention rule loose enough to clear the whole residue would be an amnesty
    dressed as a measurement — D-189's shape-fitting, one level up: instead of
    manufacturing a caller for each red, manufacture one rule that makes every
    red green.  So the blast radius is pinned, not asserted: adding the bare
    name moved **exactly one** member out, and the eight that remain are
    untouched at zero references of any kind.

    If a future widening of `call_census` empties this list, this test is where
    it has to be argued for.
    """
    by_name = {r.definition.qualname: r for r in cr.module_reaches()}
    for qualname in sorted(r.definition.qualname for r in cr.module_findings()):
        row = by_name[qualname]
        assert row.prod_mentions == 0, (
            f"{qualname} is in the residue with {row.prod_mentions} mention(s) "
            "— a residue member is by definition referenced by nothing")

    assert "guard_direction.build_stranding_repo" not in {
        r.definition.qualname for r in cr.module_findings()}


def test_the_vocabulary_defence_is_a_citation_not_an_assertion():
    """What "keep it, the docstring names it" has to survive to stay true.

    STATE carried these two as one case for three cycles — "one-line accessors
    their own module docstrings name as the reading's vocabulary".  Measured,
    that was half true.  `guard_vacuity` does cite `:func:`never_fired`` while
    explaining why it returns candidates rather than findings; `predicate_
    vacuity` cited its *siblings* `unpatchable` and `calibration_census` and
    never `one_sided`, so the accessor that IS the reading went unintroduced
    for as long as it existed.  The defence was sound for one of them and
    merely asserted for the other, and nothing could tell the two apart.

    So the citation is checked rather than believed.  Both directions are now
    load-bearing: delete either function and its module docstring is left
    citing something that is not there; delete either citation and the
    vocabulary defence for a still-uncalled function silently evaporates.
    This is what lets these two keep a residue verdict without a caller and
    without D-189's shape-fitting — the alternative was a manufactured call,
    which satisfies the instrument instead of the thing it measures.
    """
    import re
    for qualname in VOCABULARY_DEFENCE:
        module, function = qualname.split(".")
        doc = _module_docstring(module)
        assert re.search(rf":func:`~?\.?{function}`", doc), (
            f"{qualname} is kept on the vocabulary defence, but "
            f"{module}'s module docstring does not cite it")


def test_the_uncited_residue_cannot_claim_the_vocabulary_defence():
    """The other half of the split, pinned so it cannot be borrowed.

    Four of the nine are named by nothing — not `:func:`, not even in prose.
    Whatever keeps them is not "the docstring says so", and recording that
    here stops the defence spreading to the rest of the residue by proximity,
    which is exactly how the two above came to be read as one case.  A cycle
    that wants to keep one of these owes an argument or a citation; writing
    the citation moves the name up to `VOCABULARY_DEFENCE` and this test
    fails until it does, which is the intended cost.
    """
    import re
    for qualname in NO_VOCABULARY_DEFENCE:
        module, function = qualname.split(".")
        doc = _module_docstring(module)
        assert not re.search(rf"\b{function}\b", doc), (
            f"{qualname} is now named by {module}'s docstring — decide "
            f"whether it has become vocabulary and move it, do not leave "
            f"it in the uncited list")


def test_the_instrument_layer_is_helpers_doing_their_job_not_dead_weight():
    """The answer to the bottleneck, as a reading rather than a claim.

    D-189 excluded this population because ~96 entries would bury a 1-item
    residue. The exclusion was right and the silence was not: the 96 are
    `assert_*` / `*_census` helpers a suite calls, and the write-only residue
    underneath them is an order of magnitude smaller.
    """
    tally = cr._tally(cr.module_reaches())
    assert tally["TEST_ONLY"] > 50
    assert len(cr.module_findings()) < tally["TEST_ONLY"] // 4
    assert tally["FRAMEWORK_DISPATCHED"] == 2
    # Both non-defect verdicts stay small and stay visible: they are the two
    # ways a function can lack callers for a stated structural reason.
    assert tally["DEFERRED_BY_COST"] == 1


def test_the_two_populations_are_reported_separately_never_summed():
    text = cr.report()
    assert "alternative constructors" in text
    assert "module-level public functions" in text
    assert "from_sweep" in text
    # A's 1-item residue stays readable because B's 96 helpers are elided.
    assert "assert_ess_in_band" not in text
    assert "assert_ess_in_band" in cr.module_report()
    assert cr.main(["report", "--module"]) == 0
