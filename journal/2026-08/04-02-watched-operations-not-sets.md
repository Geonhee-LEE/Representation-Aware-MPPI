# The verbs, not the sets — and the scan that judged 23 guards without the 24th

- **Cycle**: 2026-08-04 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE #1` Enumerate the *acts* each guard watches, not the sets (Q-064 (b))
- **Phase**: P3
- **Status**: keep

## What I tried

- Added Q-064 (b) to `guard_reflexivity.py`: `Act`, `acts_of()`,
  `watched_operations()`, `scope_coverage()`, `misnamed_scopes()`,
  `unobserved_scopes()`. Each act is a git subcommand or filesystem read, and
  its **scope** — the state a change must reach before that act can see it,
  one of `WORKTREE` / `INDEX` / `COMMIT` / `NAMESET` — is derived from the
  invocation's own literal arguments. Attribution walks the call graph across
  modules, because no guard calls `subprocess` itself: they call `_git(...)`,
  and the scope-deciding literal (`--cached`, a `..` range) is at the call
  site, not in the wrapper.
- Started by executing the hypothesis rather than arguing it: staged `STATE.md`
  and ran D-047's push guard.
- Corrected two defects the first draft had, then fixed the gap the instrument
  found.

## What worked / what failed

- 🔴 **The headline is a correction of D-048, and it lands on D-047's own
  guard.** D-048's scan read `-`, `in` and `not in`. `staged_declarations`
  narrows an observation *down to* the registry — `changed & set(DECLARED_LOCAL_ONLY)`
  — so it was **absent from the 23 guards D-048 judged**. A population selected
  down to a registry is filtered by it as surely as one with the registry
  removed; the two spellings differ only in which side survives. Admitting `&`
  gives **28**, and one of the three new guards is the one D-047 shipped to
  close D-011's hole. **Fifth of the last six cycles** whose first-draft scan
  was wrong about its own population.
- 🔴 **D-048's predicate was short in the same place, and this halves the
  correction.** `revocable` asks whether a population is a *difference*; it does
  not ask whether the forbidden act **empties** it. Committing a snapshot file
  empties `undeclared_drift` (the guard goes quiet — D-047's failure) and
  **fills** `staged_declarations` (a guard working). So the shape now occurs
  **twice** and the failure still occurs **once**: D-048's conclusion survives,
  its population and its predicate did not. Reported at that size rather than as
  a refutation.
- 🔴 **`INDEX` was the one scope no guard in the package observed** — derived on
  both sides, the vocabulary fixed and the reached set computed. The unwatched
  verb D-048 named by reading three guards by hand falls out of the acts in the
  code.
- 🔴 **And the guard named for it did not read it.** With `STATE.md` genuinely
  `git add`-ed, `local_only_audit staged` printed `OK: no declared local-only
  path staged (5 declared, **none committed**)` and exited 0. The message was
  honest; the name was not. **The name is the fourth statement of a registry** —
  after the constant, the prose and the check — and it is the one nothing
  compares against the code. `misnamed_scopes()` derives that comparison.
- ✅ **Fixed, not just reported.** `staged_declarations` now reads
  `diff --cached` as well as `origin/main...HEAD`. Same command, same staged
  file, now: `ERROR: snapshot file staged on branch — unstage before push:
  STATE.md`, exit 1. `unobserved_scopes()` → `()`, `misnamed_scopes()` → `()`,
  both kept as equalities because an empty result is a clearance only while
  something re-derives it.
- 🔴 **One self-inflicted defect, D-048's shape one layer down**: counting
  `subprocess.run(("git", *args))` inside the `_git` wrapper as an act gave
  every git-touching guard a phantom `UNKNOWN`. A call that names no subcommand
  decides nothing — the same "filter site with no population" that produced
  D-048's six false guards. Pinned by test.
- ⚠️ `scope_coverage` still reports `DECLARED_LOCAL_ONLY` as 2 watchers / 3
  windows: `exemption_watchers` counts guards whose *population* is the list, and
  `staged_declarations` exempts it rather than enumerating it. The `INDEX` read
  is visible to `unobserved_scopes` (all guards' acts) and not to
  `scope_coverage` (watchers only). Stated, not silently reconciled.

## North-star delta

- **No avoidance or tracking number moved — seventeenth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4.
- What moved: D-011's push guard now actually enforces the act it is named for,
  and the suite has no unobserved scope. That is a real defect closed in the
  rule that keeps the merge queue conflict-free — the queue being the standing
  bottleneck.

## Key learnings

- **A guard's name is a registry statement, and it is the only one nothing
  checks.** The constant, the prose and the check were all audited across
  D-045→D-048; the *name* was audited by nobody, and it was wrong.
- **Scanning for a semantic by its spelling misses the other spelling.** `&`
  and `-` are the same filter; D-048 looked for one. This is the same class as
  D-048's own finding that a mirror written as a comprehension on one side and a
  generator on the other reads as four unrelated expressions.
- **A shape predicate is not a failure predicate.** `revocable` matches twice
  and the failure occurs once, because the direction of the offending act is not
  in the structure. Any future "the class is bounded at N" needs the direction
  test or the bound is about matches, not failures.
- **Executing the hypothesis first was worth more than the module.** Staging one
  file took thirty seconds and turned the whole cycle from a structural argument
  into a demonstrated defect with a fix.

## Recommended next 1–3 priorities

1. **Give `revocable` a direction test** — the shape/failure gap is now named and
   untested. Cheapest form: perform the offending act in a scratch worktree and
   compare the guard's reading before and after, as
   `test_the_index_read_is_real_not_inferred` already does by hand for one guard.
2. **Audit the remaining guard *names* against their acts for the other three
   scopes** — `misnamed_scopes` is green, but `NAME_SCOPE_CLAIMS` has 7 tokens and
   fails by under-detecting. Derive the token set from the guard names actually
   present rather than typing it.
3. **Score the `TYPED` exemptions for bite** (prior STATE #2) — still unscored,
   and an `INERT` exemption is D-046's coincidence shape.

## Artifacts
- PR: #67 (open, 44th consecutive cycle writing into it)
- Files touched: `eval/mppi_sandbox/guard_reflexivity.py`,
  `eval/mppi_sandbox/local_only_audit.py`,
  `eval/mppi_sandbox/tests/test_guard_reflexivity.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
