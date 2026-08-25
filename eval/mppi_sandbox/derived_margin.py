"""Can a margin taken **from the data** host the comparison the declared ones cannot?

Every declared margin in the eligible population is censored. `cafe_head_on_v0`
declares 0.40 m and its `stock_mppi` arm clears nothing at `w ∈ {75, 100}`
(a `CEILING`); `cafe_convoy_v0` and `cafe_obstacle_crossing_v0` both declare
0.30 m and *everything* either arm achieves clears it (a `FLOOR`). Three scenes,
three dead ends, `0/3` two-sided at the declared threshold — D-159's census
closed there (D-164). STATE read that as an indictment of the **declared**
thresholds and asked the obvious successor: the per-seed clearances are
recorded constants, so a threshold can be *derived* from them instead of read
off a scenario yaml. Does one exist, and does it decide anything?

Both halves are answered here, and they answer differently at different rungs,
which is why this is a census and not a number:

- **3 of the 6 walked rungs have no derived margin at all.** `head_on`'s
  `w ∈ {75, 100}` (arms overlapping by 7.6 mm and 9.9 mm) and all of `convoy`
  (arms **disjoint**, overlap −0.0198 m) return
  :data:`~scene_transplant.NO_TWO_SIDED_TO_SPREAD`. Not "no good threshold" —
  no threshold, over the reals, by :func:`margin_sweep.breakpoints`'
  exhaustiveness argument. Re-grading is not a repair that is available here.
- **2 rungs have a derived margin and it is inert**: `head_on` at `w = 150`
  (9 two-sided margins, all `REPRODUCED`) and at `w = 250` (23, all
  `REPRODUCED`). These are the only margin-independent verdicts in the whole
  population, and both point in the mechanism's direction.
- **1 rung has a derived margin that decides the answer**: `crossing` at
  `w = 250` spreads 46 two-sided margins over four verdicts with no majority
  (D-164). A derived threshold exists and picking one *is* picking the result.

The cross-scene readings are the point, and there are two. Neither is visible
from any single rung, which is why the per-scene sweeps that already existed
did not amount to this:

**1. Scene coverage is 1 of 3, and it is the scene that was already published.**
Only `cafe_head_on_v0` contributes a rung with a margin-independent verdict.
`convoy` and `crossing` — the two scenes walked specifically to widen the
evidence base past the published band — contribute **zero** between them, at
any threshold their own runs can express. The derived-margin route does not
enlarge the population; it re-finds the same scene.

**2. No single derived margin scores two rungs — and now not even two scenes.**
The three non-empty windows are `[0.4194, 0.4437]`, `[0.5467, 0.5938]` and
`[0.9712, 1.0906]`: pairwise disjoint (:attr:`DerivedMarginCensus.shared_window`
is `None`). `BandSweep` already capped arm coverage at 1/4 *within* the band
(D-158); the same ceiling holds across scenes, and for a reason that is not bad
luck. A margin is a length in metres and clearance scale is a **scene**
property — `head_on`'s arms live near 0.4–0.6 m and `crossing`'s near 1.0 m — so
`Headroom`'s refusal to grade two arms against two margins bites the matrix as
a whole. There is no matrix-wide threshold, declared or derived.

And a direction that holds without exception, recorded as
:attr:`RungDerivation.declared_placement`: **every declared margin that has a
derived window at all sits strictly below it** (`BELOW_WINDOW`, 3/3). Not one
scene declares a threshold that is merely mis-centred inside its own two-sided
span — they are all outside it, all on the permissive side. The instrument is
biased in one direction across the matrix, which is a stronger statement than
"the margins are wrong" and a much stronger one than three unrelated
mis-choices.

What this does **not** license, stated because the two inert rungs are the only
positive result in the file and are easy to over-read. Both of their windows
lie *above* the 0.40 m the scene declares (:data:`BELOW_WINDOW`), so the
`REPRODUCED` reading holds only at thresholds stricter than the scene's own
declared safety requirement — thresholds chosen to make the arms separable, not
to mean anything about safety. It is an ordering of two clearance
distributions, and the headline `unsafe_rate` is `0.0000` at every declared
margin with nothing here moving it.

The reason is **not** the one D-158 gives, and that prose is wrong on its own
numbers. It says of `w = 250`'s window that "at that threshold most runs of
*both* arms count as unsafe"; measured, the arms are sharply asymmetric — at
the window's lower end `stock_mppi` is 11/32 unsafe and `risk_mppi` **3/32**,
and at `w = 150` it is 19/32 against **2/32**. Neither rung has a majority-
unsafe risk arm anywhere in its window. Two-sidedness only requires both arms
*interior* (rate strictly between 0 and 1), which is a far weaker condition
than both being mostly unsafe, and the caveat stands on the threshold being
undeclared rather than on the runs being bad. Pinned by
`test_inert_windows_are_asymmetric_not_majority_unsafe` so the corrected
numbers cannot drift back.

Zero simulation cost: the 192 per-seed clearances are constants, and every
reading below is a composition of `MarginSweep`, `regrade` and
`scene_transplant.margin_decides` over them.
"""

from dataclasses import dataclass

from .margin_sweep import MarginSweep
from .scene_transplant import (
    MARGIN_DECIDES_VERDICT,
    MARGIN_INERT,
    NO_TWO_SIDED_TO_SPREAD,
    margin_decides,
    margin_verdict_counts,
)

#: The rung has no two-sided window, so the declared margin cannot be placed
#: relative to one. Distinct from the three real placements below: "outside a
#: window that does not exist" is not a reading (D-107).
NO_WINDOW = "NO_WINDOW"

#: The declared margin is strictly below every two-sided threshold — the arms
#: clear it so comfortably that grading against it censors them at a floor.
BELOW_WINDOW = "BELOW_WINDOW"

#: The declared margin lies inside the rung's two-sided window. Nothing in the
#: eligible population reads this; kept because its absence is the finding.
INSIDE_WINDOW = "INSIDE_WINDOW"

#: The declared margin is strictly above every two-sided threshold — nothing
#: clears it, so both arms pin at a ceiling.
ABOVE_WINDOW = "ABOVE_WINDOW"


@dataclass(frozen=True)
class RungDerivation:
    """One walked rung asked whether a threshold derived from its own runs
    exists, and whether that threshold decides the verdict."""

    scenario: str
    sweep: MarginSweep

    @property
    def weight(self) -> float:
        return self.sweep.weight

    @property
    def declared_margin(self) -> float:
        """The margin the *scenario yaml* declares, which is what the rung was
        published against. Read off the walk rather than passed in, so a rung
        cannot be graded against a margin it was never walked at."""
        return self.sweep.reproduction.reference.headroom.margin

    @property
    def decides(self) -> str:
        """One of `NO_TWO_SIDED_TO_SPREAD` / `MARGIN_INERT` /
        `MARGIN_DECIDES_VERDICT`."""
        return margin_decides(self.sweep)

    @property
    def window(self) -> tuple[float, float] | None:
        return self.sweep.window

    @property
    def stable_verdict(self) -> str | None:
        """The rung's verdict if it has one that survives the threshold choice.

        `None` in both failure directions — no window, or a window that
        disagrees with itself — because the two are already separated by
        :attr:`decides` and collapsing them here would re-merge them.
        """
        if self.decides != MARGIN_INERT:
            return None
        (verdict,) = margin_verdict_counts(self.sweep)
        return verdict

    @property
    def declared_placement(self) -> str:
        """Where the declared margin sits relative to the derived window."""
        w = self.window
        if w is None:
            return NO_WINDOW
        lo, hi = w
        m = self.declared_margin
        if m < lo:
            return BELOW_WINDOW
        if m > hi:
            return ABOVE_WINDOW
        return INSIDE_WINDOW

    def __str__(self) -> str:
        w = self.window
        span = f"[{w[0]:.4f}, {w[1]:.4f}]" if w else "—"
        return (f"{self.scenario} w={self.weight:g} margin={self.declared_margin:.2f} "
                f":: {self.decides} n={len(self.sweep.two_sided)} {span} "
                f"{self.declared_placement}")


#: No rung anywhere in the population has a margin-independent verdict.
NO_STABLE_RUNG = "NO_STABLE_RUNG"

#: Stable rungs exist but all sit on one scene — the derived-margin route did
#: not widen the population past the scene that was already published.
SINGLE_SCENE_STABLE = "SINGLE_SCENE_STABLE"

#: Two or more scenes each contribute a margin-independent verdict. Not reached
#: by the measured population; the constant exists so `SINGLE_SCENE_STABLE` is
#: a reading rather than the only thing the function can say (D-107).
MULTI_SCENE_STABLE = "MULTI_SCENE_STABLE"


@dataclass(frozen=True)
class DerivedMarginCensus:
    """Every walked rung in the eligible population, graded against thresholds
    derived from its own recorded clearances."""

    rungs: tuple[RungDerivation, ...]

    @property
    def scenes(self) -> tuple[str, ...]:
        """Distinct scenarios represented, in first-seen order."""
        out: list[str] = []
        for r in self.rungs:
            if r.scenario not in out:
                out.append(r.scenario)
        return tuple(out)

    @property
    def stable(self) -> tuple[RungDerivation, ...]:
        return tuple(r for r in self.rungs if r.decides == MARGIN_INERT)

    @property
    def deciding(self) -> tuple[RungDerivation, ...]:
        return tuple(r for r in self.rungs
                     if r.decides == MARGIN_DECIDES_VERDICT)

    @property
    def windowless(self) -> tuple[RungDerivation, ...]:
        return tuple(r for r in self.rungs
                     if r.decides == NO_TWO_SIDED_TO_SPREAD)

    @property
    def stable_scenes(self) -> tuple[str, ...]:
        """Scenes contributing at least one margin-independent verdict."""
        out: list[str] = []
        for r in self.stable:
            if r.scenario not in out:
                out.append(r.scenario)
        return tuple(out)

    @property
    def scene_coverage(self) -> tuple[int, int]:
        """`(scenes with a stable rung, scenes walked)`. The headline: 1 of 3."""
        return len(self.stable_scenes), len(self.scenes)

    @property
    def rung_coverage(self) -> tuple[int, int]:
        """`(stable rungs, rungs walked)` — 2 of 6."""
        return len(self.stable), len(self.rungs)

    @property
    def shared_window(self) -> tuple[float, float] | None:
        """The threshold interval two-sided on **every** rung that has a window.

        `None` here is the cross-scene form of `BandSweep`'s
        `SINGLE_RUNG_CEILING`: `Headroom` grades one margin at a time, so a
        result quoted over the population needs one threshold the population
        shares, and there is none.

        A **windowless rung forces `None`** rather than being skipped. Skipping
        is the tempting implementation and it is wrong in the direction that
        flatters the census: a rung with no two-sided margin is not neutral
        evidence about a shared threshold, it is the strongest evidence
        against one, so dropping it from the intersection would let a
        population of one windowed rung and five windowless ones report a
        shared window — the more scenes admitting no threshold at all, the
        more confidently the census would name one. Written the skipping way
        first; `test_windowless_rungs_do_not_widen_the_shared_window` caught
        it, and the shipped census reads `None` either way only because its
        three windows happen to be pairwise disjoint.
        """
        if not self.rungs or any(r.window is None for r in self.rungs):
            return None
        windows = [r.window for r in self.rungs]
        lo = max(w[0] for w in windows)
        hi = min(w[1] for w in windows)
        return (lo, hi) if lo <= hi else None

    @property
    def declared_placements(self) -> dict[str, int]:
        """How the declared margins sit against their derived windows."""
        out: dict[str, int] = {}
        for r in self.rungs:
            p = r.declared_placement
            out[p] = out.get(p, 0) + 1
        return out

    @property
    def verdict(self) -> str:
        n_scenes = len(self.stable_scenes)
        if n_scenes == 0:
            return NO_STABLE_RUNG
        return SINGLE_SCENE_STABLE if n_scenes == 1 else MULTI_SCENE_STABLE

    def __str__(self) -> str:
        sc, st = self.scene_coverage
        rc, rt = self.rung_coverage
        return (f"{self.verdict} scenes={sc}/{st} rungs={rc}/{rt} "
                f"shared_window={self.shared_window}")


def walked_rungs() -> tuple[RungDerivation, ...]:
    """Every rung in the eligible population with recorded per-seed clearances.

    Six: the published band's four on `cafe_head_on_v0` (D-152/153) plus the
    one walk each on `cafe_convoy_v0` (D-160) and `cafe_obstacle_crossing_v0`
    (D-164). That is the whole measured population — D-159 screened the matrix
    to **3** eligible scenes and all three are here.
    """
    from . import scene_transplant as st
    from . import separation_reproduction as sr

    return (
        RungDerivation("cafe_head_on_v0.yaml",
                       MarginSweep(reproduction=sr.w75_reproduction())),
        RungDerivation("cafe_head_on_v0.yaml",
                       MarginSweep(reproduction=sr.w100_reproduction())),
        RungDerivation("cafe_head_on_v0.yaml",
                       MarginSweep(reproduction=sr.w150_reproduction())),
        RungDerivation("cafe_head_on_v0.yaml",
                       MarginSweep(reproduction=sr.w250_reproduction())),
        RungDerivation(st.CONVOY_SCENARIO, st.convoy_w75_sweep()),
        RungDerivation(st.CROSSING_SCENARIO, st.crossing_w250_sweep()),
    )


def census() -> DerivedMarginCensus:
    """The measured answer: `SINGLE_SCENE_STABLE`, scenes 1/3, rungs 2/6, no
    shared threshold."""
    return DerivedMarginCensus(rungs=walked_rungs())


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    c = census()
    print(c)
    for r in c.rungs:
        print(f"  {r}")
        counts = margin_verdict_counts(r.sweep)
        if counts:
            spread = " ".join(f"{k}={v}" for k, v in sorted(counts.items()))
            print(f"    {spread}")
    print(f"  declared placements: {c.declared_placements}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
