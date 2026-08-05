"""D-080's defect class measured across the package — and the control that
makes the measurement mean something.

The interesting assertions here are the ones about ``VACUOUS``.  A probe that
finds two identical readings has learned nothing if both are empty, and this
package has spent D-075 → D-079 discovering that distinction one instrument at
a time.  So the shipped-tree probe of ``unresolved_reads`` is pinned as
**unprobed**, not as clean, and the synthetic fixture is what actually convicts
it.
"""

from eval.mppi_sandbox import exemption_control as ec
from eval.mppi_sandbox import key_conflation as kc


def test_the_blind_spot_is_live_not_theoretical():
    """Bare-name keys can only conflate if names actually collide.  They do.

    Not pinned to an exact count: this module's own constants entered the
    population the moment it was written (the twenty-third consecutive cycle of
    that), so a literal would be stale by its own commit.  What is pinned is the
    shape — a non-trivial collision set that is a strict minority of the whole,
    and ``EXCLUDED_TESTS`` inside it.
    """
    shared = kc.shared_names()
    assert len(shared) >= 10
    assert len(shared) < kc.constant_population()
    assert "EXCLUDED_TESTS" in shared
    assert shared["EXCLUDED_TESTS"] == ("guard_vacuity", "predicate_vacuity")


def test_collision_pairs_are_drawn_from_shared_names():
    pairs = kc.collision_pairs()
    shared = kc.shared_names()
    assert len(pairs) == sum(len(m) for m in shared.values())
    for module, name in pairs:
        assert module in shared[name]


def test_d080s_repair_holds_under_an_independent_probe():
    """``references`` separates the two ``EXCLUDED_TESTS`` — 17 reads vs 1.

    D-080 asserted this from inside the module it repaired.  This asserts it
    from outside, by the definition of the defect rather than by the shape of
    the fix: call the scan with both registries and require different answers.
    """
    left, right = kc.CANONICAL_PAIR
    p = kc.probe(ec.references, left, right, name="references")
    assert p.verdict == kc.VERDICT_DISTINGUISHES
    assert (p.left_reading, p.right_reading) == ("17", "1")


def test_binding_distinguishes_and_is_never_graded_vacuous():
    """A scan returning a verdict string has no empty reading to be vacuous about."""
    left, right = kc.CANONICAL_PAIR
    p = kc.probe(ec.binding, left, right, name="binding")
    assert p.verdict == kc.VERDICT_DISTINGUISHES
    assert (p.left_reading, p.right_reading) == (ec.CALL_TIME, ec.DEF_TIME)


def test_the_remaining_bare_keyed_scan_is_unprobed_on_the_shipped_tree():
    """``unresolved_reads`` grades ``VACUOUS`` — carried as unrun, not as clean.

    It keys on the bare name by construction, because an unresolved read has no
    owner to key on.  But the package holds **zero** unresolved reads, so both
    readings are empty and no probe over the shipped population can show it.
    Reporting that as ``IDENTICAL`` would invent evidence; reporting it as
    absent would hide a known limit.  It is reported as neither.
    """
    assert kc.unprobed() == ("exemption_control.unresolved_reads",)
    assert "exemption_control.unresolved_reads" not in kc.conflating()
    assert ec.unresolved_reads(kc.CANONICAL_PAIR[0]) == ()
    assert ec.unresolved_reads(kc.CANONICAL_PAIR[1]) == ()


def test_no_scan_is_measured_conflating_on_the_shipped_tree():
    """The positive result — weaker than it looks, and the test says so.

    Green here means "no scan was *caught*", and one of the three was never
    actually asked (see the test above).  The pairing is the claim.
    """
    assert kc.conflating() == ()
    assert len(kc.probes()) == len(kc.SCANS) == 3


def test_synthetic_control_convicts_the_bare_keyed_scan():
    """Where the shipped tree is silent, the fixture is not: 2 and 1 read as 3 and 3."""
    bare, _keyed, _noop = kc.synthetic_control()
    assert bare.verdict == kc.VERDICT_IDENTICAL
    assert (bare.left_reading, bare.right_reading) == ("3", "3")


def test_synthetic_control_has_a_wrong_direction_control():
    """A keyed scan over the *same* fixture must separate ``a`` from ``b``.

    Without this the conviction above is unfalsifiable: a fixture in which
    nothing can tell the two modules apart would produce ``IDENTICAL`` for a
    correct scan too.  D-079's rule, applied to D-079's own successor.
    """
    _bare, keyed, _noop = kc.synthetic_control()
    assert keyed.verdict == kc.VERDICT_DISTINGUISHES
    assert (keyed.left_reading, keyed.right_reading) == ("2", "1")


def test_synthetic_control_has_a_no_op_control():
    """``VACUOUS`` must be a verdict the control can actually produce."""
    _bare, _keyed, noop = kc.synthetic_control()
    assert noop.verdict == kc.VERDICT_VACUOUS
    assert (noop.left_reading, noop.right_reading) == ("0", "0")


def test_emptiness_is_checked_before_equality():
    """The ordering inside ``probe`` is the whole file, so it is pinned directly."""
    empty = kc.probe(lambda r, p=None: (), ("a", "R"), ("b", "R"), name="e")
    same = kc.probe(lambda r, p=None: ("x",), ("a", "R"), ("b", "R"), name="s")
    differ = kc.probe(lambda r, p=None: ("x",) * len(r[0]),
                      ("a", "R"), ("bb", "R"), name="d")
    assert empty.verdict == kc.VERDICT_VACUOUS
    assert same.verdict == kc.VERDICT_IDENTICAL
    assert differ.verdict == kc.VERDICT_DISTINGUISHES


def test_equal_length_but_different_readings_are_not_identical():
    """Comparison is on values, not sizes — else a real difference reads as conflation."""
    p = kc.probe(lambda r, p=None: (r[0],), ("a", "R"), ("b", "R"), name="v")
    assert p.verdict == kc.VERDICT_DISTINGUISHES


def test_an_unsized_reading_is_refused_rather_than_coerced():
    """Silently numbering an unknown return type is how the first draft printed a hash."""
    import pytest
    with pytest.raises(TypeError):
        kc.probe(lambda r, p=None: 3.5, ("a", "R"), ("b", "R"), name="x")
