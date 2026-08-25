# The eighth pin was a registry with two modules

- **Cycle**: 2026-08-15 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<strand-clear>` clear the three-cycle strand (05:00, 06:00, 07:00)
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` rc=1 named **three** cycles and 9 unpushed commits,
  one of them ungraded. Per D-112 that outranks the decision tree, so this cycle
  took no new TODO. `cycle_wallclock review` opened with the 07:00 run at 47m26
  against a 35m budget and said cut scope — so the scope was exactly the two red
  tests blocking the push gate, and nothing else.
- Diagnosed the 8th pin the 07:00 cycle stopped on, rather than re-running its
  repair list.

## What worked / what failed

- **The 07:00 diagnosis was wrong, and cheaply falsifiable.** That journal
  concluded `window_axis_migration.sites()` "returns 0 on the subprocess path"
  and recorded the real cause as unfound. `sites()` returns **49** under both a
  plain import and `python -c` in a subprocess — two commands, ten seconds. The
  `__main__` path was never implicated.
- **`sites()` was never called at all.** `control()` short-circuits on
  `binding(registry) != CALL_TIME` and returns `UNREACHABLE` with a hardcoded
  `0, 0`. That is where the "base 0 → 0" reading came from: not a reader
  returning zero, but a reader that never ran. A reading of `0 -> 0` from a
  short-circuit and one from a dead reader are indistinguishable in the report,
  which is what sustained the wrong diagnosis for a whole cycle.
- **The real defect is that a from-imported registry has two modules.**
  `Tamper.registry` was doing two jobs: naming the registry's identity (what
  `binding()` resolves reads against) and naming the namespace to `setattr` on.
  For the other ten tampers those coincide. `from .window_axis_reach import
  RESOLVERS` splits them, and either collapse breaks the control in a different
  direction — name the reader and you get `UNREACHABLE`; name the declarer and
  the patch lands on a tuple the reader no longer reads, giving `INERT`. Both
  directions are now pinned in one test.
- **Fixed via `Tamper.bound_in`**, defaulting to empty (the two coincide).
  11/11 tampers now `BITES`, on both the in-process and `python -m` paths;
  `inert()` and `uncontrolled()` are both empty.
- **The 6 pins the 07:00 cycle repaired all still hold** — guard pool 110,
  unwatched set of 6 including `RESOLVERS`. Re-measured directly rather than
  trusted, in seconds.

## North-star delta

- **Zero.** Fourth consecutive cycle whose entire output is the reflexive
  census. Nothing here touches obstacle avoidance or path tracking.
- What *did* move: the strand is cleared at 4 cycles / 10 commits rather than
  compounding to 5. That is bookkeeping, not progress, and Q-158 is the right
  place for the question of whether this tax is still worth paying.

## Key learnings

- **A short-circuit that fabricates a reading is worse than one that refuses.**
  `control()` returns `0, 0` for `UNREACHABLE` because there is no reading to
  report — but the report renders it identically to a measured zero, and a
  cycle read it as one. The honest render is `—` (which the `unreachable`
  section already uses); the `0 -> 0` row is a lie the table tells.
- **Re-derive an inherited diagnosis before paying for it.** 07:00 inherited
  06:00's repair list and said afterwards that re-pricing it would have cost two
  minutes. This cycle inherited 07:00's *diagnosis* and falsifying it cost about
  the same. Both times the inherited claim was the expensive item.
- **`from X import R` defeating a patch of `X` now has a control, not just a
  note.** 07:00 flagged the hazard as worth a guard of its own; the failure is
  silent (`INERT` against a live registry), which is the shape `exemption_control`
  exists to catch — so it is pinned as a test rather than left as prose.

## Recommended next 1–3 priorities

1. **Render `UNREACHABLE` as `—` in `control()`/`report()`** rather than `0 -> 0`,
   so a short-circuit is never readable as a measurement. Small, and it closes
   the exact confusion that cost this cycle and the last.
2. **Answer Q-158** — four cycles of reflexive-census repair with zero north-star
   movement is the evidence it asked for.
3. **Return to the P3 cost-critic thrust** (the branch's actual subject) once the
   strand is clear.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/exemption_control.py, eval/mppi_sandbox/tests/test_exemption_control.py, docs/decisions.md, journal/2026-08/15-08-*.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
