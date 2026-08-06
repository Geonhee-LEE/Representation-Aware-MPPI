"""What the ``slow`` job does with a **confirmed** drift failure (STATE #4).

D-098 answered *whether* the six readable CI failures are dispatch artefacts:
all six pass under native AVX-512 and fail with it masked, three reproducing
CI's number to the digit.  That closed the attribution question and opened the
one nobody had costed — six tests calibrated on an AVX-512 box fail on every
runner **forever**, so the job is red by construction until something changes.
STATE named three candidate routes:

* **(a)** ``xfail`` conditioned on the dispatch,
* **(b)** tolerances spanning both dispatches,
* **(c)** mask AVX-512 in the dev box's own conftest so the two machines agree.

This module prices each route against the six rows *as measured*, and its whole
reason for existing is that the pricing does not come out the way the list's
ordering implies.

**Route (b) is a special case, not a route.**  Widening is an operation on a
two-sided acceptance interval, and only **two** of the six assertions have one.
Of those two, one is admissible (``x1.14``) and one is not (``x2.95``, above
:data:`~eval.mppi_sandbox.repair_admissibility.MAX_HONEST_WIDEN`).  The other
four have no widening operator at all: three are one-sided and one is a set
equality.  So (b) can repair **1 of 6**.

**And the three one-sided ones are not merely inadmissible — they are
unpriceable.**  :mod:`~eval.mppi_sandbox.repair_admissibility` prices a
threshold as the fraction of the asserted effect surviving a drop to the other
machine's value, measured over ``RATIO_NULL = 1.0``, and says so in its own
docstring: *"All four thresholds in the divergent set are ratios where 1.0
means no effect."*  True of D-034's population; **false of this one** — this
population's thresholds are ``> 1.25 * 0.0343``, ``< 0.124 / 3`` and ``> 1.2``,
whose nulls are 0, 0 and 1.  Borrowing 1.0 anyway yields a negative "effect
retained" that reads like a number.  That is D-097's finding one module over —
a verdict scoped to one population quoted about another — so this module
returns :data:`NO_NULL_SUPPLIED` rather than a figure.  A price nobody can
state is the honest output, and it is what makes (b) not a route.

**Route (c) is a re-baseline wearing a repair's clothes.**  Masking AVX-512 on
the dev box does make the machines agree, and it makes them agree on a dispatch
**none of the constants were measured under**: all six assertions become
unmeasured at once.  The cost is not a tolerance, it is the D-017…D-098 bill,
and it is already a queued item.  Priced by count, not by arithmetic.

**Route (a) is admissible, and only for rows with a reading.**  A marker keyed
on ``CALIBRATED_SIMD not in simd_found()`` is a *dispatch* condition; the
license to apply it to a given test is D-098's *per-test* measurement.  So the
marked set is derived from :func:`simd_attribution.verdicts` — never
hand-typed, which is D-047's defect class — and the two ``exclusion_scope``
rows that have no reading are **refused**, not swept in with the rest.

Which is why this does not turn the job green, and STATE #4 said it would:

    14 red  →  6 marked (a)  +  4 already fixed by D-096's timeout  =  2 left,

and the 2 left are exactly Q-092's unexplained pair.  Red-with-a-known-residue
is a different state from green, and reporting the second would be the banner's
error again.

Usage::

    python3 -m eval.mppi_sandbox.drift_repair

**This module asserts nothing about dispatch-dependent values** — the rule
:mod:`dispatch_divergence` and :mod:`repair_admissibility` adopted, for the
reason that a test pinning one would fail on CI for the very reason the file
documents.  Its tests cover the parsing, the routing and the refusals.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import repair_admissibility as ra
from . import simd_attribution as sa

#: Route verdicts.  ``NO_NULL_SUPPLIED`` and ``NO_READING`` are refusals, and
#: they are values rather than exceptions because a refusal that stops the run
#: cannot be tabulated next to the prices that *were* stateable.
WIDENABLE = "WIDENABLE"
WIDENING_DESTROYS = "WIDENING_DESTROYS"
NO_WIDENING_OPERATOR = "NO_WIDENING_OPERATOR"
NO_NULL_SUPPLIED = "NO_NULL_SUPPLIED"
NO_READING = "NO_READING"
MARKABLE = "MARKABLE"

#: Assertion shapes, as parsed from CI's own text.
BAND = "band"
THRESHOLD = "threshold"
CATEGORICAL = "categorical"

#: A tolerance printed to this many significant figures or fewer *may* be a
#: rendering rather than the measurement: CI printed ``± 0.0625`` where this box
#: printed ``± 6.2e-02`` for the same comparison (D-098), and a widen factor
#: computed off the short form moves in the third digit.
#:
#: One line of text cannot distinguish a rounded rendering from an exactly
#: declared constant — ``± 0.05`` trips this at 1 s.f. and is exact.  The flag
#: is therefore deliberately one-directional: it only ever *caps* the digits
#: reported, so a false positive under-claims precision and a false negative is
#: impossible.  Reading the declared tolerance from source instead of from CI's
#: line is the fix that would discriminate; it is not this cycle's.
IMPRECISE_SIGFIGS = 3

_NUM = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
_BAND = re.compile(rf"({_NUM})\s*==\s*({_NUM})\s*(?:±|\+/-)\s*({_NUM})")
_MULT_LO = re.compile(rf"({_NUM})\s*>\s*\(\s*({_NUM})\s*\*\s*({_NUM})\s*\)")
_DIV_HI = re.compile(rf"({_NUM})\s*<\s*\(\s*({_NUM})\s*/\s*({_NUM})\s*\)")
_PLAIN_LO = re.compile(rf"^assert\s+({_NUM})\s*>\s*({_NUM})\s*$")
_SET_EQ = re.compile(r"(set\(\)|\{.*\})\s*==\s*(set\(\)|\{.*\})")


@dataclass(frozen=True)
class Assertion:
    """One CI failure's assertion, reduced to the shape a repair acts on."""

    test_id: str
    shape: str
    #: the value the failing machine produced (``None`` when categorical)
    value: float | None = None
    #: two-sided acceptance interval (band only)
    lo: float | None = None
    hi: float | None = None
    #: one-sided bound (threshold only), with the side it constrains
    bound: float | None = None
    side: str = ""  # "lower" | "upper"
    #: significant figures the printed tolerance carried (band only)
    tolerance_sigfigs: int | None = None

    @property
    def imprecise(self) -> bool:
        return (
            self.tolerance_sigfigs is not None
            and self.tolerance_sigfigs <= IMPRECISE_SIGFIGS
        )


def _sigfigs(text: str) -> int:
    """Significant figures in a printed number, as printed.

    ``6.2e-02`` carries 2 and ``0.0625`` carries 3, which is the whole point:
    the two render the same measurement and only one of them supports a third
    digit in a derived factor.
    """
    mantissa = text.lower().split("e")[0]
    digits = mantissa.lstrip("-+").replace(".", "").lstrip("0")
    return len(digits.rstrip("0")) or 1


def classify(test_id: str, signature: str) -> Assertion | None:
    """Parse one CI ``short test summary info`` signature.

    Returns ``None`` for a signature this parser does not understand, rather
    than guessing a shape.  A misparsed shape would route a claim to a repair
    that cannot be applied to it, which is worse than declining.
    """
    if not signature:
        return None
    m = _BAND.search(signature)
    if m:
        value, target, tol = (float(m.group(i)) for i in (1, 2, 3))
        return Assertion(
            test_id,
            BAND,
            value=value,
            lo=target - tol,
            hi=target + tol,
            tolerance_sigfigs=_sigfigs(m.group(3)),
        )
    m = _MULT_LO.search(signature)
    if m:
        value, a, b = (float(m.group(i)) for i in (1, 2, 3))
        return Assertion(test_id, THRESHOLD, value=value, bound=a * b, side="lower")
    m = _DIV_HI.search(signature)
    if m:
        value, a, b = (float(m.group(i)) for i in (1, 2, 3))
        return Assertion(test_id, THRESHOLD, value=value, bound=a / b, side="upper")
    m = _PLAIN_LO.match(signature.strip())
    if m:
        value, lo = float(m.group(1)), float(m.group(2))
        return Assertion(test_id, THRESHOLD, value=value, bound=lo, side="lower")
    if _SET_EQ.search(signature):
        return Assertion(test_id, CATEGORICAL)
    return None


@dataclass(frozen=True)
class Route:
    """What each of the three routes costs for one assertion."""

    test_id: str
    shape: str
    #: route (b)
    widen_verdict: str
    widen_factor: float | None = None
    #: route (a)
    mark_verdict: str = NO_READING
    note: str = ""

    @property
    def widen_factor_text(self) -> str:
        """The factor, at the precision its input supports."""
        if self.widen_factor is None:
            return "n/a"
        return f"x{self.widen_factor:.2f}"


def price_widening(a: Assertion) -> tuple[str, float | None, str]:
    """Route (b) for one assertion — delegating the arithmetic, not copying it.

    The band case is handed to :func:`repair_admissibility.price` so the
    ``widen_factor = 1 + excursion`` identity keeps having exactly one
    statement in the tree (D-047).  The threshold case is *not* handed to it,
    because that function's null is a population parameter this population does
    not satisfy — see the module docstring.
    """
    if a.shape == CATEGORICAL:
        rep = ra.price({}, {"categorical": True}, a.test_id)
        return NO_WIDENING_OPERATOR, None, rep.note
    if a.shape == THRESHOLD:
        return (
            NO_NULL_SUPPLIED,
            None,
            f"one-sided {a.side} bound {a.bound:.5g}: no acceptance interval to "
            f"widen, and no per-claim null with which to price the drop "
            f"(RATIO_NULL={ra.RATIO_NULL:g} is D-034's population, not this one)",
        )
    half = (a.hi - a.lo) / 2.0
    centre = (a.lo + a.hi) / 2.0
    excursion = max(0.0, (abs(a.value - centre) - half) / half)
    rep = ra.price(
        {"value": centre},
        {"value": a.value, "lo": a.lo, "hi": a.hi, "excursion": excursion},
        a.test_id,
    )
    verdict = WIDENABLE if rep.verdict == "widenable" else WIDENING_DESTROYS
    note = rep.note
    if a.imprecise:
        note += (
            f"; tolerance printed to {a.tolerance_sigfigs} s.f., so the factor "
            f"is stated to 2 decimals and no further (D-098)"
        )
    return verdict, rep.widen_factor, note


def routes(
    census: tuple[sa.CiFailure, ...] = sa.CI_FAILURES,
    readings: tuple[sa.LocalReading, ...] = sa.MEASURED_2026_08_06,
) -> tuple[Route, ...]:
    """Price all three routes for every row that has a dispatch reading.

    Rows without one are absent, not defaulted: :func:`markable` and
    :func:`grade` both read the gap, and a row silently present with
    ``NO_READING`` would be indistinguishable from a row read as clean — the
    absence-read-as-clean shape this branch has now hit eleven times.
    """
    verdicts = sa.verdicts(readings, census)
    drift = {sa.DRIFT_CONSISTENT, sa.DRIFT_SHAPED}
    by_id = {f.test_id: f for f in census}
    out = []
    for test_id, verdict in sorted(verdicts.items()):
        if verdict not in drift:
            continue
        parsed = classify(test_id, by_id[test_id].signature)
        if parsed is None:
            out.append(
                Route(
                    test_id,
                    "unparsed",
                    NO_NULL_SUPPLIED,
                    mark_verdict=MARKABLE,
                    note="signature not parsed; route (b) unavailable, (a) still "
                    "licensed by the per-test reading",
                )
            )
            continue
        wv, wf, note = price_widening(parsed)
        out.append(
            Route(
                test_id,
                parsed.shape,
                wv,
                widen_factor=wf,
                mark_verdict=MARKABLE,
                note=note,
            )
        )
    return tuple(out)


def markable(
    census: tuple[sa.CiFailure, ...] = sa.CI_FAILURES,
    readings: tuple[sa.LocalReading, ...] = sa.MEASURED_2026_08_06,
) -> frozenset[str]:
    """Node ids route (a) may mark — exactly the rows measured as drift.

    This is the set the conftest applies, and deriving it here is the whole
    safety argument: a hand-typed marker list would drift from the measurement
    that licenses it, and a marker keyed on the *dispatch* alone would xfail a
    row whose failure on the runner has nothing to do with dispatch.
    """
    return frozenset(r.test_id for r in routes(census, readings))


def refused(
    census: tuple[sa.CiFailure, ...] = sa.CI_FAILURES,
    readings: tuple[sa.LocalReading, ...] = sa.MEASURED_2026_08_06,
) -> tuple[str, ...]:
    """Attributable rows route (a) must **not** mark: no reading exists.

    Q-092's pair.  Marking these would be the banner's error with a mechanism:
    an unexplained failure retired as a machine artefact on the strength of
    other rows' evidence.
    """
    return sa.unmeasured(sa.verdicts(readings, census), census)


def rebaseline_cost(
    census: tuple[sa.CiFailure, ...] = sa.CI_FAILURES,
    readings: tuple[sa.LocalReading, ...] = sa.MEASURED_2026_08_06,
) -> int:
    """Route (c)'s price: assertions that become unmeasured if the dev box masks.

    Every row whose constant was calibrated under native dispatch, which is
    every row route (a) would mark.  Stated as a count because there is no
    tolerance to quote — the claims do not loosen, they stop having been
    measured.
    """
    return len(markable(census, readings))


#: Grades for the population as a whole.
FULLY_ROUTED = "FULLY_ROUTED"
RESIDUE = "RESIDUE"
VACUOUS = "VACUOUS"


def grade(
    census: tuple[sa.CiFailure, ...] = sa.CI_FAILURES,
    readings: tuple[sa.LocalReading, ...] = sa.MEASURED_2026_08_06,
) -> str:
    """Does route (a) leave the job green, or red with a known residue?

    ``VACUOUS`` first, for :mod:`suite_memo`'s reason: an empty route table has
    routed nothing and must not report that everything is handled.
    """
    if not routes(census, readings):
        return VACUOUS
    return RESIDUE if refused(census, readings) else FULLY_ROUTED


def report(
    census: tuple[sa.CiFailure, ...] = sa.CI_FAILURES,
    readings: tuple[sa.LocalReading, ...] = sa.MEASURED_2026_08_06,
) -> str:
    table = routes(census, readings)
    lines = [
        f"{'test':<46} {'shape':<12} {'(b) widen':<20} {'factor':>7} {'(a)':<9}",
        "-" * 98,
    ]
    for r in table:
        short = r.test_id.split("::")[0].split("/")[-1].removesuffix(".py")
        lines.append(
            f"{short:<46} {r.shape:<12} {r.widen_verdict:<20} "
            f"{r.widen_factor_text:>7} {r.mark_verdict:<9}"
        )
    shapes = [r.shape for r in table]
    verdicts = [r.widen_verdict for r in table]
    lines += [
        "",
        f"route (b): defined for {shapes.count(BAND)}/{len(table)} (bands only), "
        f"admissible for {verdicts.count(WIDENABLE)}, "
        f"unpriceable for {verdicts.count(NO_NULL_SUPPLIED)}",
        f"route (c): {rebaseline_cost(census, readings)} assertions become "
        f"unmeasured — a re-baseline, not a repair",
        f"route (a): {len(markable(census, readings))} markable, "
        f"{len(refused(census, readings))} refused for want of a reading",
        f"grade: {grade(census, readings)}",
    ]
    for test_id in refused(census, readings):
        lines.append(f"  refused: {test_id.split('::')[-1]}")
    for r in table:
        lines.append(f"  {r.test_id.split('::')[-1]}: {r.note}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
