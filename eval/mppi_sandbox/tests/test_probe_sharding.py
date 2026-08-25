"""A reader set too large for one pass is still measurable, in pieces.

D-238 established that the largest pin in
:data:`inert_surface.POST_RECEIPT_WRITES` is not re-takable by
:func:`inert_surface.probe` **at any cycle length**: :data:`_RUN_TIMEOUT` is a
ceiling on a *single pass*, a probe needs two, and the un-mutated one alone
overran.  Its alternative (d) is the only one that does not give something up —
cut the readers into disjoint shards, probe each, and compose.  Sound because
:func:`inert_surface.compose` already rests on the same disjunction over a
different split.

The verdict these tests are most concerned with is the one that separates
sharding from composition: a sharded reading is :data:`INERT`, **not**
:data:`INERT_COMPOSED`, because nothing is inherited from an older tree.

Like its sibling file, this one names the *population* and never respells its
members — a docstring that spells a pinned path makes this module a reader of
it and withdraws the pin between two readings (D-237).
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import inert_surface as ins


@pytest.fixture
def target(tmp_path):
    """A one-file tree standing in for a probe candidate."""
    path = tmp_path / "artifact.md"
    path.write_text("original\n")
    return path


def _readers(*names):
    return lambda *_a, **_k: ins.Readers(tuple(names), ())


# --------------------------------------------------------------------------
# the split is a partition
# --------------------------------------------------------------------------


def test_shards_cover_every_reader_exactly_once():
    """The premise the disjunction rests on — not a formatting detail."""
    names = tuple(f"t{i}.py" for i in range(13))
    shards = ins._shards(names, 5)
    flat = [n for shard in shards for n in shard]
    assert flat == list(names)
    assert len(set(flat)) == len(names)


def test_a_short_final_shard_is_kept_not_padded_or_dropped():
    names = tuple(f"t{i}.py" for i in range(7))
    assert ins._shards(names, 3) == (
        ("t0.py", "t1.py", "t2.py"),
        ("t3.py", "t4.py", "t5.py"),
        ("t6.py",),
    )


def test_a_set_smaller_than_one_shard_is_a_single_pass():
    assert ins._shards(("a.py", "b.py"), 6) == (("a.py", "b.py"),)


def test_an_empty_set_yields_no_shards():
    assert ins._shards((), 6) == ()


def test_a_nonsensical_shard_size_is_refused_not_silently_clamped():
    """Size 0 would loop forever; a caller error is not a narrower reading."""
    with pytest.raises(ValueError):
        ins._shards(("a.py",), 0)


def test_the_default_shard_size_is_below_the_set_that_overran():
    """SHARD_SIZE has one job: make a pass fit the per-pass ceiling."""
    assert 1 <= ins.SHARD_SIZE < 27


# --------------------------------------------------------------------------
# compose_shards: the disjunction, and the order of its rules
# --------------------------------------------------------------------------


def test_all_inert_shards_compose_to_inert_not_inert_composed():
    """The crux: sharding inherits nothing, so it owes no weakened verdict."""
    assert ins.compose_shards([ins.INERT] * 4) == ins.INERT


def test_the_sharded_verdict_is_strong_enough_to_license_an_exemption():
    """INERT_COMPOSED would price a composition debt sharding does not carry."""
    assert ins.compose_shards([ins.INERT, ins.INERT]) != ins.INERT_COMPOSED
    assert ins.inert.__doc__ is not None  # the consumer of this verdict


def test_one_content_read_shard_carries_the_whole_set():
    assert ins.compose_shards([ins.INERT, ins.CONTENT_READ, ins.INERT]) == ins.CONTENT_READ


def test_a_content_read_outranks_an_unaffordable_sibling():
    """A measurement that *was* bought is not discarded because another was not."""
    assert ins.compose_shards([ins.CONTENT_READ, ins.UNAFFORDABLE]) == ins.CONTENT_READ


def test_an_unaffordable_shard_blocks_an_otherwise_inert_set():
    assert ins.compose_shards([ins.INERT, ins.UNAFFORDABLE, ins.INERT]) == ins.UNAFFORDABLE


def test_unaffordable_outranks_vacuous_so_the_next_move_survives():
    """compose()'s reason: only one of the two prices a re-take."""
    assert ins.compose_shards([ins.VACUOUS, ins.UNAFFORDABLE]) == ins.UNAFFORDABLE


def test_a_vacuous_shard_is_not_laundered_into_inert():
    assert ins.compose_shards([ins.INERT, ins.VACUOUS]) == ins.VACUOUS


def test_no_shards_at_all_is_vacuous_not_inert():
    """Emptiness before success — the direction that reads clean."""
    assert ins.compose_shards([]) == ins.VACUOUS


def test_no_composition_of_shards_ever_invents_a_new_verdict():
    known = {ins.INERT, ins.CONTENT_READ, ins.UNAFFORDABLE, ins.VACUOUS}
    for a in known:
        for b in known:
            assert ins.compose_shards([a, b]) in known


# --------------------------------------------------------------------------
# shard_probe: full coverage, assembled from affordable passes
# --------------------------------------------------------------------------


def test_every_reader_is_run_across_the_shards(monkeypatch, target):
    """Coverage is the whole claim: a missed reader is an unmeasured hole."""
    seen: list[tuple[str, ...]] = []

    def _spy(_c, root=None, sources=None, tests=None, timeout=None):
        seen.append(tests)
        return ins.Probe(_c, ins.INERT, tests=tests)

    names = tuple(f"t{i}.py" for i in range(7))
    monkeypatch.setattr(ins, "readers", _readers(*names))
    monkeypatch.setattr(ins, "readers_key", lambda *a, **k: "|".join(names))
    monkeypatch.setattr(ins, "probe", _spy)
    reading = ins.shard_probe("artifact.md", sources={}, size=3)
    assert tuple(n for shard in seen for n in shard) == names
    assert reading.verdict == ins.INERT


def test_the_full_set_is_probed_in_more_than_one_pass(monkeypatch, target):
    """The point of the exercise — one pass is what priced out."""
    names = tuple(f"t{i}.py" for i in range(7))
    monkeypatch.setattr(ins, "readers", _readers(*names))
    monkeypatch.setattr(ins, "readers_key", lambda *a, **k: "|".join(names))
    monkeypatch.setattr(
        ins, "probe", lambda c, **kw: ins.Probe(c, ins.INERT, tests=kw["tests"])
    )
    assert len(ins.shard_probe("artifact.md", sources={}, size=3).passes) == 3


def test_a_candidate_with_no_readers_is_vacuous_not_inert(monkeypatch):
    monkeypatch.setattr(ins, "readers", lambda *a, **k: ins.Readers((), ()))
    reading = ins.shard_probe("artifact.md", sources={})
    assert reading.verdict == ins.VACUOUS
    assert reading.passes == ()


def test_a_reader_set_that_moves_mid_probe_spoils_the_composition(monkeypatch):
    """Shards of a moved set are readings of two different questions."""
    names = ("t0.py", "t1.py")
    monkeypatch.setattr(ins, "readers", _readers(*names))
    monkeypatch.setattr(ins, "readers_key", lambda *a, **k: "t0.py|t1.py|t2.py")
    monkeypatch.setattr(
        ins, "probe", lambda c, **kw: ins.Probe(c, ins.INERT, tests=kw["tests"])
    )
    reading = ins.shard_probe("artifact.md", sources={}, size=1)
    assert reading.verdict == ins.VACUOUS
    assert reading.readers_key == ""


def test_the_premise_check_rescans_rather_than_trusting_the_snapshot(monkeypatch):
    """Asking `sources` whether `sources` moved would answer itself."""
    monkeypatch.setattr(ins, "readers", _readers("t0.py"))
    monkeypatch.setattr(
        ins, "probe", lambda c, **kw: ins.Probe(c, ins.INERT, tests=kw["tests"])
    )
    seen = {}

    def _key(_c, sources=None):
        seen["sources"] = sources
        return "t0.py"

    monkeypatch.setattr(ins, "readers_key", _key)
    ins.shard_probe("artifact.md", sources={"eval/x.py": "text"})
    assert seen["sources"] is None


def test_one_read_shard_survives_into_the_sharded_verdict(monkeypatch):
    names = ("t0.py", "t1.py")
    monkeypatch.setattr(ins, "readers", _readers(*names))
    monkeypatch.setattr(ins, "readers_key", lambda *a, **k: "|".join(names))
    monkeypatch.setattr(
        ins,
        "probe",
        lambda c, **kw: ins.Probe(
            c, ins.CONTENT_READ if kw["tests"] == ("t1.py",) else ins.INERT, tests=kw["tests"]
        ),
    )
    assert ins.shard_probe("artifact.md", sources={}, size=1).verdict == ins.CONTENT_READ


def test_each_shard_is_reported_so_the_disjunction_is_auditable(monkeypatch):
    """Which shard carried the verdict is the only thing that makes it checkable."""
    names = ("t0.py", "t1.py")
    monkeypatch.setattr(ins, "readers", _readers(*names))
    monkeypatch.setattr(ins, "readers_key", lambda *a, **k: "|".join(names))
    monkeypatch.setattr(
        ins,
        "probe",
        lambda c, **kw: ins.Probe(
            c, ins.CONTENT_READ if kw["tests"] == ("t1.py",) else ins.INERT, tests=kw["tests"]
        ),
    )
    text = ins.shard_probe("artifact.md", sources={}, size=1).describe()
    assert ins.CONTENT_READ in text and ins.INERT in text
    assert "2 shards" in text


def test_the_per_pass_timeout_reaches_every_shard(monkeypatch):
    """The ceiling is what sharding exists to fit under; a dropped kwarg voids it."""
    seen = []
    monkeypatch.setattr(ins, "readers", _readers("t0.py", "t1.py"))
    monkeypatch.setattr(ins, "readers_key", lambda *a, **k: "t0.py|t1.py")

    def _spy(c, **kw):
        seen.append(kw["timeout"])
        return ins.Probe(c, ins.INERT, tests=kw["tests"])

    monkeypatch.setattr(ins, "probe", _spy)
    ins.shard_probe("artifact.md", sources={}, size=1, timeout=42.0)
    assert seen == [42.0, 42.0]


# --------------------------------------------------------------------------
# the CLI: `shard` exists to clear an `UNAFFORDABLE`, so the codes must agree
# --------------------------------------------------------------------------


def test_the_cli_grades_a_sharded_inert_as_clean(monkeypatch, capsys):
    monkeypatch.setattr(ins, "_python_sources", lambda *a, **k: {})
    monkeypatch.setattr(
        ins, "shard_probe", lambda c, **kw: ins.ShardedProbe(c, ins.INERT)
    )
    assert ins._main(["shard", "artifact.md"]) == 0
    assert ins.INERT in capsys.readouterr().out


def test_the_cli_still_reports_two_when_a_shard_prices_out(monkeypatch, capsys):
    """Same code the full probe uses — `shard` clears it, so it must mean the same."""
    monkeypatch.setattr(ins, "_python_sources", lambda *a, **k: {})
    monkeypatch.setattr(
        ins, "shard_probe", lambda c, **kw: ins.ShardedProbe(c, ins.UNAFFORDABLE)
    )
    assert ins._main(["shard", "artifact.md"]) == 2


def test_the_cli_reports_one_on_a_sharded_content_read(monkeypatch):
    monkeypatch.setattr(ins, "_python_sources", lambda *a, **k: {})
    monkeypatch.setattr(
        ins, "shard_probe", lambda c, **kw: ins.ShardedProbe(c, ins.CONTENT_READ)
    )
    assert ins._main(["shard", "artifact.md"]) == 1


def test_the_two_subcommands_agree_on_every_verdict_code(monkeypatch):
    """One rule, not two — a disagreement makes the clearing unreadable."""
    monkeypatch.setattr(ins, "_python_sources", lambda *a, **k: {})
    for verdict in (ins.INERT, ins.CONTENT_READ, ins.UNAFFORDABLE, ins.VACUOUS):
        monkeypatch.setattr(ins, "probe", lambda c, **kw: ins.Probe(c, verdict))
        monkeypatch.setattr(
            ins, "shard_probe", lambda c, **kw: ins.ShardedProbe(c, verdict)
        )
        assert ins._main(["probe", "artifact.md"]) == ins._main(["shard", "artifact.md"])


def test_the_cli_passes_the_requested_shard_size_through(monkeypatch):
    monkeypatch.setattr(ins, "_python_sources", lambda *a, **k: {})
    seen = {}

    def _spy(c, **kw):
        seen.update(kw)
        return ins.ShardedProbe(c, ins.INERT)

    monkeypatch.setattr(ins, "shard_probe", _spy)
    ins._main(["shard", "artifact.md", "--size", "4"])
    assert seen["size"] == 4
