"""The `d_enc` consumer census — Q-200's gating count, and the prose it corrects.

These tests exist because the count was wrong twice before it was right, both
times reading clean in its own output. They pin the derivation, not the number.
"""

from __future__ import annotations

import ast

from eval.mppi_sandbox import d_enc_consumers as dec
from eval.mppi_sandbox import obstacle_reach, threshold_vacuity


def test_pin_matches_the_walk():
    """The whole point: a new consumer is a failing test, not a wider cascade."""
    assert dec.drift() == []
    assert dec.consumers() == dec.CONSUMERS


def test_q200_fits_one_cycle():
    """Q-200's own splitting rule, graded rather than eyeballed."""
    assert dec.fits_one_cycle()
    assert len(dec.consumers()) <= dec.Q200_SPLIT_THRESHOLD


def test_exactly_one_non_test_consumer_and_it_reads_one_symbol():
    """The finding that makes the re-point cheap.

    If a second non-test module ever reads a `d_enc` value, the re-point stops
    being a one-file edit and this assertion is how that gets noticed.
    """
    code = dec.code_consumers()
    assert code == ("mppi_sandbox/excursion_tracking.py",)
    assert dec.CONSUMERS[code[0]] == ("CENSUS",)


def test_every_pinned_symbol_actually_exists_on_the_source_module():
    """A typo in `D_ENC_DERIVED` silently shrinks the consumer set."""
    for name in dec.D_ENC_DERIVED:
        assert hasattr(obstacle_reach, name), name


def test_threshold_vacuity_is_named_in_the_prose_but_reads_nothing():
    """The negative result, pinned from both ends.

    `obstacle_reach.SPEED_IS_LOAD_BEARING` says re-pointing `scene_reach` moves
    `threshold_vacuity`'s verdict. It does not: the module reads no
    `obstacle_reach` symbol. Asserting only the walk would let the prose be
    repaired without the pin noticing, so the prose is asserted too — when
    someone fixes the sentence, this test tells them to unpin the module.
    """
    assert "threshold_vacuity" in obstacle_reach.SPEED_IS_LOAD_BEARING
    assert dec.prose_overreach() == ("threshold_vacuity",)

    src = ast.parse(open(threshold_vacuity.__file__, encoding="utf-8").read())
    assert dec._read_symbols(src) == set()


def test_aliased_module_import_is_seen():
    """The bug the first cut had: `import obstacle_reach as ore` was invisible.

    `test_speed_load_bearing` is the module written *about* this census and it
    imports under an alias, so a walk that matches only the literal module name
    drops precisely the consumer that matters most — while reporting a smaller,
    more comfortable number.
    """
    tree = ast.parse(
        "from eval.mppi_sandbox import obstacle_reach as ore\n"
        "x = ore.CRUISE_CENSUS\n"
    )
    assert dec._read_symbols(tree) == {"CRUISE_CENSUS"}
    assert "mppi_sandbox/tests/test_speed_load_bearing.py" in dec.CONSUMERS


def test_comment_only_mention_is_not_a_consumer():
    """`test_key_discrimination` names `measure_at` in a comment and reads none."""
    tree = ast.parse("# obstacle_reach.measure_at entered, LIVE\nx = 1\n")
    assert dec._read_symbols(tree) == set()
    assert not any("key_discrimination" in p for p in dec.consumers())


def test_source_module_is_not_its_own_consumer():
    """Including it would make the count unfalsifiable.

    Compared on the basename, not as a substring: `test_obstacle_reach.py`
    *contains* `obstacle_reach.py` and is a genuine consumer, so the loose
    check fails on a correct tree.
    """
    stems = {p.rsplit("/", 1)[-1] for p in dec.consumers()}
    assert f"{dec.SOURCE_MODULE}.py" not in stems


def test_prose_only_modules_are_not_counted_as_consumers():
    """A comment mention costs nothing to re-point; folding it in inflates the cascade."""
    live = dec.consumers()
    for module in dec.PROSE_ONLY:
        assert not any(p.endswith(f"/{module}.py") for p in live), module
