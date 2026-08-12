# The blame clock read the runner's zone, not the one it pinned

- **Cycle**: 2026-08-13 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — read the CI `divergence_digest` output from the 05:00 push
- **Phase**: P3
- **Status**: keep

## What I tried

- Read the CI run for `f883280` — the first run carrying `divergence_digest`,
  which the 04:00 cycle wrote and the 05:00 cycle un-stranded. Shard 6 was red
  and the digest came with it.
- Put CI's census beside the local one **field by field** rather than comparing
  the two headline grades, which is all four previous cycles had.
- The corpus fields were **identical** — `cycles=233`, `tsv_rows=230`,
  `undated_rows=0` on both sides. That refutes Q-140's (b)/(c) outright: same
  journals, same rows, different *assignment*. Only `orphan_rows` moved (0 → 1),
  and that is the signature of rows sliding backwards off the front of the
  journal set.
- Re-ran the local digest with **only the ambient `TZ` changed**, and it
  reproduced CI **exactly** — all eight census fields plus the three control
  lines, byte for byte.

## What worked / what failed

- 🔴 **`_blame_minutes` converted a raw epoch with `time.localtime`.**
  `git blame --line-porcelain` reports `committer-time` as an integer, so the
  `TZ=Asia/Seoul` pinned on the subprocess never reaches it — that variable
  steers git's own date *formatting*, and this field is not formatted. The
  conversion happened in Python against the ambient zone: KST here, **UTC on a
  GitHub runner**. Every row landed nine hours early in CI and was reassigned to
  whichever cycle then preceded it.
- **D-230 excluded timezone by measuring the wrong function.** It checked
  `_commit_minute`, which really is pinned (`--date=format-local` + `TZ`), and
  checked that `undated_rows` was 0 — true, and irrelevant, because the fallback
  it gates was never the path in question. The unpinned twin was never measured.
  An exclusion is only as good as the function it was taken on.
- **The correct spelling was already in the repo.** `tsv_timestamp._blame_times`
  parses the *same field* out of the *same command* and has always converted
  with an explicit `KST`. Two readers of one fact, one wrong, agreeing for as
  long as the machine sat in Seoul — D-047's shape, found for the third time.
- Fix imports `KST` from that module rather than respelling it, so the two
  cannot drift apart again. Census is now identical under `Asia/Seoul`, `UTC`
  and `America/New_York`, and reads the correct **206/17**.

## North-star delta

- **No planner movement; 22nd consecutive instrument cycle on this branch.** The
  substantive result on the board is still D-225's paired cafe reading.
- But the instrument that grades every cycle's honesty was **wrong in CI for its
  entire life**, and CI is the constitution's only authority over the pushed
  tree. 20 cycles were being graded UNSUPPORTED there for rows they had actually
  appended. That authority is now readable.
- Concretely: 5 cycles of divergence hunting (D-228 → D-231) close, and the next
  CI run should show shard 6's two `cycle_artifacts` failures gone.

## Key learnings

- **A pinned `TZ` on a subprocess is not a pinned clock.** It only reaches
  fields the subprocess *formats*. Any raw epoch crossing the boundary is
  converted on the near side, under whatever zone that process happens to have —
  and CI is the one environment where that differs, which is exactly the
  environment nobody can step into to check.
- **"Timezone is excluded" cost four cycles because it was recorded without
  naming the function it was taken on.** D-230's exclusion list should have read
  `_commit_minute: timezone excluded`, not `timezone excluded`. An exclusion
  inherits the scope of its measurement, and dropping that scope turns a true
  local finding into a false global one.
- **The reproduction was one environment variable.** Four cycles reconstructed
  trees, clones, merge refs and process shapes looking for a difference that a
  `TZ=UTC` prefix would have surfaced in three seconds. The cheap discriminator
  existed the whole time; what was missing was the census *field list* that
  showed the corpus was identical and therefore that only the clock could move.
- D-229's clone passed at the merge ref because it ran under **KST** — the clone
  was correct and the conclusion drawn from it ("environment excluded") was not.

## Recommended next 1–3 priorities

1. **Read the next CI run** — confirm shard 6's two `cycle_artifacts` failures
   clear. This is the falsifiable prediction D-231 makes; if they persist, the
   attribution is wrong and must be reopened.
2. **Sweep for other epoch-across-the-subprocess-boundary reads** — this cycle
   checked `eval/` and found exactly two, but the rule is now nameable and
   worth applying once deliberately rather than at the next red run.
3. **Return to capability work.** Twenty-two instrument cycles is the real cost
   here; D-225's cafe reading has had no successor since.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/cycle_artifacts.py, eval/mppi_sandbox/tests/test_cycle_artifacts.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
