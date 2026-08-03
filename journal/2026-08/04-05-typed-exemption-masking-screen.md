# Screen every TYPED exemption for masking — and the probe that found the one mask was a coincidence

- **Cycle**: 2026-08-04 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — screen every `TYPED` exemption for masking (+ answer Q-067)
- **Phase**: P4 (calendar) / P3 thread
- **Status**: keep

## What I tried

- Derived all `(guard, TYPED exemption)` pairs from `Guard.typed_exemptions` —
  the same label every other `TYPED` screen consumes — and asked of each one the
  question D-050 asked of exactly one: **can this exemption be taken away, and
  does the guard read differently without it?**
- Classified the *suppression route* from the guard's own AST, ran the guard at
  `HEAD` and again with its registry emptied, with a liveness act in front so
  `INERT` means "removes nothing" rather than "my patch silently failed".
- Intersected the bite screen with revocability (D-048) to separate an exemption
  that is masking from one that is merely working.
- Answered **Q-067** with option (b) and wrote the obligation that comes with it
  into the two functions it constrains.

## What worked / what failed

- 🔴 **Of 12 typed pairs, exactly one takes its exemption as a parameter.**
  `undeclared_drift` accepts `declared=` so `tree_provenance.verify` can pass a
  stamp's own allow-list — *not* so anyone could audit it. **The only mask ever
  found in this package was found through a keyword argument that exists for an
  unrelated reason.** D-046's "a coincidence was holding a filter's place", one
  layer up: the coincidence was holding the **probe's** place. The other 11 were
  hard-wired, so D-050's method was inapplicable to them by construction.
- ✅ **Routed around it rather than reporting it.** A hard-wired constant is
  still a module global and Python resolves globals at call time, so the probe
  patches the attribute on the module the guard's body actually reads (checked by
  `getattr`, not by reading the import). 12/12 runnable, `unsuppressible()` = `()`.
- 🔴 **Bite alone is a weak screen — 6 of 12 grow under suppression, and 5 of
  those are exemptions doing their job.** Suppress `ADAPTERS` and all 7
  predicates are unadapted; that is what an exemption is *for*. D-048 supplies
  the missing half structurally: a mask needs the offence to **collapse** the
  population, and an `ENUMERATION` population still holds the offender
  afterwards. So masking ⟹ bites **and** revocable — and the intersection is
  **exactly 1**, D-050's own pair. Q-063 bounded this class at one by structure;
  this bounds it at one **by measurement over every typed pair**.
- 🔴 **D-048's "exactly one" had already drifted to 2 and nothing noticed.**
  `unmirrored_revocable` reads `staged_declarations` + `undeclared_drift` at
  `HEAD` — confirmed on a clean detached worktree, so it predates this cycle;
  D-049's `&` arm admitted the first one and the bound was never re-derived. The
  screen re-bounds it, and the separating fact is measured, not structural:
  `staged_declarations` narrows *down to* the registry rather than subtracting
  it, so suppression **empties** its population instead of growing it ⇒ `INERT`.
- 🔴 **Two self-inflicted defects, and both missed the exact guard the module
  generalises from.** (i) `_substitutes_for` required the assignment target to be
  a parameter, so `allow = DECLARED_LOCAL_ONLY if declared is None else declared`
  read as no route at all — the first run reported **0 parameter routes**, i.e.
  that D-050's own probe had been impossible. Moved the test onto the `IfExp`.
  **Ninth first-draft scan in ten cycles wrong about its own population, again
  under-counting.** (ii) `Drift` is a dataclass; collapsed to one `repr` it is a
  1-element reading on both sides of the suppression, so growth is undetectable
  and D-050's *proven* mask came out `DIVERGES`. Fields are flattened now. Both
  pinned by regression tests.
- 🔴 **The module entered the registry it audits** (D-046's shape, 4th
  occurrence): pool 38 → **40**, via `masking_candidates` and `unscreened`.
- ✅ **Q-067 → (b)**, with its cost stated rather than hidden: `_provenance`
  declines to follow a same-module call *on purpose*, because "is this a
  hand-typed registry" is a property of the call site and does not survive a
  frame, whereas `_is_set_valued`'s "is this a collection" does. Following would
  re-label genuinely derived populations `TYPED` — the wrong direction for a
  screen that exists to find underived registries.

## North-star delta

- **No avoidance or tracking number moved — twentieth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged. The 가려진-obstacle class still has exactly one working cost term
  (D-027).
- What moved: the claim "only one guard can be masked" stopped resting on a
  structural argument over 23 guards and now rests on a suppression measurement
  over all 12 typed exemption pairs — and the stale version of that claim was
  caught reading 2.
- The exposure Q-067 leaves open got **priced larger**, not smaller: an exemption
  that slips to `DERIVED` now also leaves the masking screen's population.

## Key learnings

- **An instrument's applicability is a fact about the code it reads, not about
  the instrument.** D-050's probe looked general and was applicable to 1 of 12
  sites; nobody had asked. Worth asking of the other dynamic probes.
- **A screen that fires on healthy behaviour is not a screen.** Bite fires on
  every exemption that removes anything, which is all of the working ones — the
  discriminator had to come from D-048's structure, not from a bigger threshold.
- **A bound is only true at the population it was derived over.** D-048's "one"
  was correct at 23 guards and wrong at 38, and re-deriving it was free while
  re-reading it would have confirmed the stale number.
- **Write the probe against the case you already know the answer to.** Both
  first-draft defects were invisible until the screen was pointed at D-050's own
  mask and failed to re-find it.

## Recommended next 1–3 priorities

1. **Hand the 1 masking candidate to `guard_direction`'s dynamic probe** and
   close the loop — the static half is done and says exactly where to look.
2. **Ask D-050's applicability question of the other probes** — `guard_direction`
   stands up a git repo per (guard × path); how many guards can it actually
   reach, and is that number also 1-by-coincidence?
3. **Re-derive every "exactly N" bound in `docs/decisions.md`** — D-048's drifted
   silently and it will not be the only one.

## Artifacts

- PR: #67 (open, 46+ cycles) — pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`)
- Files touched: `eval/mppi_sandbox/exemption_masking.py` (new),
  `eval/mppi_sandbox/tests/test_exemption_masking.py` (new, 21 tests),
  `eval/mppi_sandbox/guard_reflexivity.py` (Q-067 (b) stated in `_provenance`),
  `eval/mppi_sandbox/predicate_depth.py` (exposure's prescribed repair),
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py` (pool tally 38 → 40),
  `docs/decisions.md` (D-052), `docs/deliberations.md` (Q-067 resolved)
- TSV row appended: yes
