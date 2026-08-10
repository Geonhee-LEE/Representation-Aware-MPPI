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
