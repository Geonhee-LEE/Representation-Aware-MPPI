# SPDX-License-Identifier: BSD-3-Clause
"""`bottleneck_scope`: does STATE's bottleneck name an already-retired scene?

Fixtures, not the live `STATE.md`. STATE.md is `DECLARED_LOCAL_ONLY` (D-011), so
it is **absent in CI** — a test that read it would pass locally on the tree that
motivated it and then grade nothing at all where it actually runs. That absence
is itself pinned below, because a screen that raised on a missing file would
turn every CI run red for a file CI is supposed not to have.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import bottleneck_scope as bs
from eval.mppi_sandbox.scene_eligibility import GOAL_BALL_BLOCKED, census


@pytest.fixture(scope="module")
def matrix():
    return census()


def _state(tmp_path, body: str, heading: str = bs.BOTTLENECK_HEADING):
    p = tmp_path / "STATE.md"
    p.write_text(
        "# Research State\n\n## North star distance\n\nprose\n\n"
        f"{heading}\n\n{body}\n\n## Open experiments\n\n_없음_\n",
        encoding="utf-8",
    )
    return p


class TestSectionRead:
    def test_reads_only_the_bottleneck_section(self, tmp_path):
        p = _state(tmp_path, "the knee is mispriced")
        text = bs.bottleneck_text(p)
        assert text == "the knee is mispriced"
        assert "North star" not in text and "Open experiments" not in text

    def test_missing_file_is_empty_not_an_exception(self, tmp_path):
        """CI has no STATE.md. That must read as `NO_BOTTLENECK`, not a crash."""
        assert bs.bottleneck_text(tmp_path / "absent.md") == ""

    def test_missing_heading_is_empty(self, tmp_path):
        p = _state(tmp_path, "prose", heading="## Something Else")
        assert bs.bottleneck_text(p) == ""


class TestNaming:
    def test_both_spellings_are_found(self, matrix):
        """The yaml's own `name:` hyphenates; the file stem does not."""
        assert bs.named_scenes("blocked on cafe_cut_in_v0 today", matrix) == \
            ("cafe_cut_in_v0",)
        assert bs.named_scenes("blocked on cafe-cut-in-v0 today", matrix) == \
            ("cafe_cut_in_v0",)

    def test_word_bounded(self, matrix):
        """A stem inside a longer token is not a naming."""
        assert bs.named_scenes("see xcafe_cut_in_v0y", matrix) == ()

    def test_unnamed_scene_is_not_reported(self, matrix):
        assert "cafe_head_on_v0" not in bs.named_scenes(
            "only cafe_cut_in_v0 here", matrix)

    def test_names_are_derived_from_the_census_not_typed(self, matrix):
        """The defect this module catches is a hand-typed scene list, so the
        module must not contain one (D-047, D-072).

        Scans *executable* source only. Docstrings and comments are stripped
        via `ast`, not by splitting on quotes: this module's prose cites
        `cafe_cut_in_v0` by name on purpose — that citation is the motivating
        example, not a registry copy — and a guard that read its own
        explanation would be grading prose (D-390, D-396).
        """
        import ast

        tree = ast.parse(open(bs.__file__, encoding="utf-8").read())
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef,
                                 ast.FunctionDef, ast.AsyncFunctionDef)):
                first = (node.body or [None])[0]
                if (isinstance(first, ast.Expr)
                        and isinstance(first.value, ast.Constant)
                        and isinstance(first.value.value, str)):
                    docstrings.add(id(first.value))

        literals = [
            n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in docstrings
        ]
        identifiers = [n.id for n in ast.walk(tree) if isinstance(n, ast.Name)]
        identifiers += [n.attr for n in ast.walk(tree)
                        if isinstance(n, ast.Attribute)]
        executable = "\n".join(literals + identifiers)

        for scene in matrix.scenes:
            assert scene.scenario not in executable, (
                f"{scene.scenario} is spelled in bottleneck_scope's "
                "executable source; scene names must come from the census")


class TestVerdict:
    def test_the_motivating_sentence_is_retired(self, tmp_path, matrix):
        """STATE.md 2026-08-21 22:00, verbatim in substance.

        This is the case the module exists for: every clause true, conclusion
        unreachable.
        """
        p = _state(tmp_path, "`cafe_cut_in_v0` fails `goal_reached` at "
                             "**every** collision margin.")
        result = bs.scope(p, matrix)
        assert result.verdict == bs.RETIRED
        assert [s.scenario for s in result.retired] == ["cafe_cut_in_v0"]
        assert GOAL_BALL_BLOCKED in result.retired[0].exclusions

    def test_eligible_scene_is_live(self, tmp_path, matrix):
        p = _state(tmp_path, "`cafe_head_on_v0` clearance needs a second seed.")
        result = bs.scope(p, matrix)
        assert result.verdict == bs.LIVE
        assert not result.retired

    def test_no_scene_named_is_live(self, tmp_path, matrix):
        p = _state(tmp_path, "the push gate costs 22 minutes.")
        assert bs.scope(p, matrix).verdict == bs.LIVE

    def test_absent_state_is_its_own_verdict(self, tmp_path, matrix):
        """`NO_BOTTLENECK` is distinct from `LIVE`: an empty population must
        not read as a clean one (D-107)."""
        result = bs.scope(tmp_path / "absent.md", matrix)
        assert result.verdict == bs.NO_BOTTLENECK
        assert result.verdict != bs.LIVE

    def test_mixed_naming_reports_both_sides(self, tmp_path, matrix):
        p = _state(tmp_path, "compare cafe_cut_in_v0 against cafe_head_on_v0.")
        result = bs.scope(p, matrix)
        assert result.verdict == bs.RETIRED
        assert [s.scenario for s in result.retired] == ["cafe_cut_in_v0"]
        assert [s.scenario for s in result.live] == ["cafe_head_on_v0"]


class TestAcknowledgement:
    """The false positive the module's first live reading produced.

    STATE.md 2026-08-28 10:00 named `cafe_cut_in_v0` *as already excluded*,
    inside a live P5 baseline question. The screen returned `RETIRED` on a
    correctly-aimed bottleneck, and the only remedy it left was deleting a true
    clause — the D-044 shape (a check whose honest fix degrades the artifact).
    """

    def test_quoting_the_reason_code_is_not_a_finding(self, tmp_path, matrix):
        p = _state(tmp_path, "picking P5's baseline: `cafe_cut_in_v0` is out "
                             f"under `{GOAL_BALL_BLOCKED}`, leaving 7 arms.")
        result = bs.scope(p, matrix)
        assert result.verdict == bs.ACKNOWLEDGED
        assert not result.retired
        assert [s.scenario for s in result.acknowledged] == ["cafe_cut_in_v0"]

    def test_acknowledged_exits_zero(self, tmp_path, matrix):
        """The gate's whole purpose: this must not cost a cycle a re-aim."""
        p = _state(tmp_path, f"`cafe_cut_in_v0` — {GOAL_BALL_BLOCKED}.")
        assert bs.main(["--state", str(p)]) == 0

    def test_prose_that_only_means_it_does_not_clear(self, tmp_path, matrix):
        """Legibility, not sincerity, is the bar — and deliberately so.

        "Excluded on geometry" is true and is what the 10:00 bottleneck said.
        It still reads as `RETIRED`, because a screen that accepted paraphrase
        would need a typed vocabulary of synonyms, which is the D-047 defect
        this module exists to catch.
        """
        p = _state(tmp_path, "`cafe_cut_in_v0` is excluded on geometry.")
        assert bs.scope(p, matrix).verdict == bs.RETIRED

    def test_the_motivating_sentence_still_retires(self, tmp_path, matrix):
        """The 2026-08-21 sentence re-derived the exclusion from closed-loop
        runs and named no code. Acknowledgement must not blunt that."""
        p = _state(tmp_path, "`cafe_cut_in_v0` fails `goal_reached` at "
                             "**every** collision margin.")
        assert bs.scope(p, matrix).verdict == bs.RETIRED

    def test_a_code_without_the_scene_is_not_an_acknowledgement(
            self, tmp_path, matrix):
        """Acknowledgement is per-scene: the code only clears the scene it is
        an exclusion *of*, so a bare code cannot launder an unnamed one."""
        result = bs.scope(_state(tmp_path, f"see {GOAL_BALL_BLOCKED}."), matrix)
        assert result.verdict == bs.LIVE
        assert not result.acknowledged

    def test_one_acknowledged_does_not_cover_another_retired(
            self, tmp_path, matrix):
        """Two excluded scenes, one code. The uncited one still retires."""
        others = [s for s in matrix.scenes
                  if not s.eligible and s.scenario != "cafe_cut_in_v0"]
        if not others:
            pytest.skip("census has a single excluded scene")
        other = others[0]
        p = _state(tmp_path, f"`cafe_cut_in_v0` is out under "
                             f"`{GOAL_BALL_BLOCKED}`; also {other.scenario}.")
        result = bs.scope(p, matrix)
        assert result.verdict == bs.RETIRED
        assert [s.scenario for s in result.retired] == [other.scenario]

    def test_reason_vocabulary_is_derived_not_typed(self, matrix):
        """`acknowledges` must read `scene.exclusions`, not a spelled list —
        the same rule `test_names_are_derived_from_the_census_not_typed`
        applies to scene names, one level in (D-047)."""
        import ast
        import inspect

        src = ast.parse(inspect.getsource(bs.acknowledges))
        docstrings = {id(n.value) for n in ast.walk(src)
                      if isinstance(n, ast.Expr)
                      and isinstance(n.value, ast.Constant)
                      and isinstance(n.value.value, str)}
        literals = [n.value for n in ast.walk(src)
                    if isinstance(n, ast.Constant)
                    and isinstance(n.value, str) and id(n) not in docstrings]
        for scene in matrix.scenes:
            for reason in scene.exclusions:
                assert reason not in "\n".join(literals), (
                    f"{reason} is spelled in acknowledges(); exclusion codes "
                    "must come from the census")


class TestGroundTruth:
    def test_cut_in_is_blocked_by_the_geometry_feasibility_documented(self, matrix):
        """The screen's premise, re-derived rather than trusted.

        `feasibility`'s docstring states -0.2 m; if the yaml or the radii ever
        move, this fails here rather than silently making the module's
        motivating example non-reproducible.
        """
        scene = {s.scenario: s for s in matrix.scenes}["cafe_cut_in_v0"]
        assert GOAL_BALL_BLOCKED in scene.exclusions
        assert scene.best_goal_clearance == pytest.approx(-0.2, abs=1e-9)

    def test_retired_direction_is_the_only_finding(self, tmp_path, matrix):
        """A `LIVE` verdict claims nothing — the CLI must not go red on it."""
        p = _state(tmp_path, "`cafe_head_on_v0` needs a second seed.")
        assert bs.main(["--state", str(p)]) == 0

    def test_cli_returns_one_on_a_retired_bottleneck(self, tmp_path):
        p = _state(tmp_path, "`cafe_cut_in_v0` fails `goal_reached`.")
        assert bs.main(["--state", str(p)]) == 1


class TestLoopWiring:
    """D-481: the screen shipped with 15 tests and no caller.

    Every test above builds its own STATE in `tmp_path`, so the suite was
    green for five days while the live `STATE.md` carried a `RETIRED`
    bottleneck and no loop step read it. These pin the call itself — the one
    part of the arrangement that CI can see, since `STATE.md` is local-only
    (D-011) and no runner has a live one to screen.
    """

    def test_the_loop_prompt_invokes_this_screen(self):
        assert bs.wired_into_loop(), (
            f"{bs.LOOP_PROMPT} does not contain {bs.INVOCATION!r} — the screen "
            "has no caller, which is the defect D-481 was opened for."
        )

    def test_invocation_string_is_derived_from_the_module_name(self):
        """A typed spelling would keep matching a module that had been
        renamed out from under it — D-047's shape, in one string."""
        assert bs.INVOCATION == f"python3 -m {bs.__name__}"
        assert bs.__name__.endswith("bottleneck_scope")

    def test_prompt_path_exists(self):
        """`wired_into_loop` reports `False` on a missing prompt rather than
        raising, so the pin above could pass vacuously if the path were
        wrong. This is the discriminator."""
        assert bs.LOOP_PROMPT.is_file()

    def test_absent_prompt_is_not_wired_and_does_not_raise(self, tmp_path):
        assert bs.wired_into_loop(tmp_path / "nope.md") is False

    def test_a_prompt_that_only_mentions_the_name_is_not_wired(self, tmp_path):
        """Prose naming the module is not a call. `docs/decisions.md` has
        named it since D-412 and the screen still never ran."""
        p = tmp_path / "prompt.md"
        p.write_text("see `bottleneck_scope` for the retired-scene screen.",
                     encoding="utf-8")
        assert bs.wired_into_loop(p) is False
