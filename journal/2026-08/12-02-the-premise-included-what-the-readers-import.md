# The premise included what the readers import

- **Cycle**: 2026-08-12 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: _no Notion page_ — picked from STATE.md `Next claude-actionable` #1
  ("decide the probe cost model before paying it again"). Notion MCP was not
  authorised this run, so Phase 5a-5c did not run and no page id was resolved.
  The `b3ee1d96` in this cycle's commit trailers is the **data-source** id
  mistaken for a page id — recorded here rather than amended, since the commits
  are already the durable record.
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Took the stranding reading first (D-112): **3 stranded cycles** (22:00, 23:00, 01:00), all with honest Artifacts claims, so nothing to backfill — clearing it was a push, and the push needed a green suite the stale `STATE.md` pin cannot give.
- Answered STATE #1 with a measurement instead of a lean: implemented `carried_drift()` + `Pin.base_commit` to check the premise `COMPOSITION_CAP` stands in for — D-205(c).
- Deliberately **skipped the suite**: it is red on 6 `test_inert_surface` assertions for a known reason, so `push_preflight` would refuse and the 20 minutes buys nothing. Two consecutive cycles died discovering that at minute 34.

## What worked / what failed

- 🟢 The base tree was **prose inside `carried`** ("21 files pinned INERT on b90fc1f") — the one fact needed to check the premise was the one fact nothing could read (D-047). Now a field.
- 🟢 **Finding 1 — generation and drift are uncorrelated.** Over reader test files: gen-1 pins carry 6/16, 8/15, 10/21 drifted; gen-2 carries 11/23; gen-0 carries 0/13. The integer deciding 3.6 s vs 18 min does not order the pins by how far their premise moved — a gen-1 pin outdrifted the gen-2 one. Both cheap discharges D-204 celebrated were resting on drifted premises.
- 🔴 **Finding 2 reverses finding 1, and I found it by checking my own instrument before shipping it.** My first implementation diffed reader test files only, and graded `JOURNAL.md` — full-probed 40 minutes earlier — `PREMISE_INTACT` while `inert_surface.py`, a module mediating every one of its readers, had changed in between. That reading would have licensed a composition on a premise that had in fact moved: precisely the failure `COMPOSITION_CAP` guards. Including `Readers.modules` (already computed by the static layer — no second list, D-047), **all five pins are drifted**.
- 🔴 So **D-205(c) does not buy a cheaper probe.** `inert_surface.py` mediates all five pins and is the file the pin-machinery cycles keep editing, so every such cycle voids every pin. The hoped-for "charge the cliff on the real delta" collapses to "charge the full cliff, five times".
- 🔴 **Did not publish.** Strand is now **4 cycles deep**. This was a chosen cost, not an overrun: no reachable action this cycle makes the suite green.

## North-star delta

- **Zero movement.** Fifth consecutive cycle on the machinery guarding P3's deliverable rather than the deliverable. PR #67's `ShadowCostCritic` has been written and tested since 08-11 and is not the blocker.
- What did move is the diagnosis: the strand is now explained **structurally** rather than as four separate budget overruns.

## Key learnings

- **The pin scheme as gated is a deadlock generator.** Any edit to a mediating module voids all five pins; discharging all five costs 5 full probes across multiple cycles; any further edit re-voids them. `test_inert_surface` grades a stale pin **hard red**, so this non-terminating loop blocks every push. That is the whole of the 4-cycle strand.
- **An unverified premise is not a violated invariant.** Grading them alike is the clearable-vs-permanent conflation this repo has already fixed three times (D-199 rc=2, D-202 rc=2, D-044). `stale_pins()` should be advisory; a real `CONTENT_READ` probe verdict should stay hard red. That change is what unblocks PR #67 — see Q-129.
- **I did not make that change here.** It is the change that would unblock this cycle's own push, and the cycle that benefits should not be the one that weakens the guard. Recorded as a Q for a cycle with no stake in it.
- Checking an instrument against a case it *should* fail is worth more than another green test: the file-only diff passed all ten of my new tests and was still wrong.

## Cycle hygiene

- Notion MCP unauthorised → Phase 5a/5b/5c skipped; no TODO status reached
  `Doing`/`Today`, and the two follow-ups this cycle would have filed (Q-129
  adoption, `COMPOSITION_CAP` re-price) live only in STATE.md's list below.
- Cron activity logged to `.cron_activity_local.log` (the Daily Log is in the
  same unauthorised workspace).

## Recommended next 1–3 priorities

1. **Adopt Q-129**: make `stale_pins()` advisory in `test_inert_surface`, keep `CONTENT_READ` hard red. Cheap, principled, three precedents — and it is the only path to PR #67 that does not cost 5 full probes.
2. **Then the strand**: suite + push, one cycle, nothing else.
3. Re-price `COMPOSITION_CAP`'s purpose given D-206 — a counter bounding a premise it does not track is decoration (D-079); either drive composition off `carried_drift` or drop it.

## Artifacts
- PR: #67 open (autoresearch/p3-epistemic-shadow-cost-critic) — **unpushed, 4 cycles stranded**
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_inert_surface.py
- TSV row appended: yes
