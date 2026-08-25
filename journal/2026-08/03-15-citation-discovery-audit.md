# The registry was incomplete in a way hand-checking could not reveal — it was reading the wrong surface

- **Cycle**: 2026-08-03 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 (Notion unreachable, 40th cycle — no page id)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 — audit the rest of `docs/`'s numbers against their instruments —
  which collides with **Q-056** (filed 14:00, unresolved): `claim_scope`'s
  citation list is hand-typed, so an unregistered citation is exactly as silent
  as the drift D-036 found.
- Built `citation_audit.py`: scans prose for the magnitudes of instrumented
  claims, attributes each occurrence to its section/module, flags any site no
  registry accounts for. Per Q-056's lean **(b)**, it emits *candidates*;
  tagging (`defines` / `restates` / `diagnoses`) stays a human call.
- Registered the four STATE-named suspects + D-025's `2.320×` + the `2.0×`
  whose citations `claim_scope` owns (lifted by import, not re-typed).
- 22 tests. Zero simulation — string search and arithmetic over repo files.

## What worked / what failed

- 🔴 **The hand registry was not merely incomplete — it was scanning the wrong
  surface.** `claim_scope` registers 5 sections citing `2.0×`; the scan finds
  **8**. The three it could never have found are `D-036` (the diagnosis, a role
  the registry had no vocabulary for) and **two module docstrings**, which
  `claim_scope` does not read at all.
- 🔴 **D-036's repair stopped at `docs/`.** `horizon_audit.py`'s docstring
  carried the drifted `2.0×` paired against a horizon change with neither the
  instrument's `1.3008` nor the oracle stamp — the exact defect D-036 fixed in
  six `docs/` sections. Repaired in the same cycle the scan found it.
- ✅ **STATE #1's suspicion was 3/4 right.** `6.19×` (D-027 → D-028, Q-049, 2
  docstrings), `2.11×` (D-029 → D-030, docstring), `6.8×` (D-030 → D-036,
  docstring) all propagate outside their measuring section. **`2.320×` does
  not** — it lives only in D-025. Honest negative, now held by test.
- 🔴 **D-030 both *defines* the `2.0×` and *cites* it against a foreign
  instrument.** `claim_scope` had no way to say that; the registry separates the
  roles, which is the drift's actual shape.
- ⚠️ **First cut of the docstring extractor failed open.** A regex anchored at
  offset 0 missed every module (all open with an SPDX comment) and reported the
  registered sites as *stale* — a discovery pass silently finding nothing. Now
  parsed with `ast`, with a regression test naming the SPDX header.
- ✅ **Guard verified live**: writing the D-037 entry turned the suite red with
  5 unregistered sites until each was tagged.
- Fast half: **314 passed** / 127 deselected / 1 xfailed, 114.9 s (was 290).

## North-star delta

- **No avoidance or tracking number moved — sixth consecutive instrument cycle.**
- What it bought: a *new* undeclared citation now goes red. Previously citation
  drift emitted no signal at all, which is what let one survive four cycles.
- The 가려진-obstacle class still has exactly one working cost term (D-027).
  Scenes able to contribute an avoidance number: **5**, reportable: **4** —
  unchanged.

## Key learnings

- **A hand-maintained registry's failure mode is not "forgot an entry" — it is
  "never looked at that surface".** Enumerating harder inside `docs/` would
  never have found the docstring citations; the fix was widening the scan, not
  deepening the list.
- **Code prose is a citation surface.** The repo kept its instruments and its
  claims in the same files and assumed the docstring was safe because it sat
  next to the code — it was the one place the drift survived D-036.
- **A guard must be inside its own scope.** `citation_audit` scans itself; the
  alternative is a module policing restatement that exempts the place it
  restates.
- **Register the negative too.** `2.320×` being clean is a result; leaving it
  unregistered means the next cycle re-establishes it by hand.

## Recommended next 1–3 priorities

1. **Extend the scan to bare magnitudes** (table cells, other precisions) — the
   stated limit of this pass. Candidate ranking will need to survive false
   positives, which is the reason it was scoped out here.
2. **Extend the excursion sweep to the other 122 closed-loop tests** (STATE #2,
   `dispatch_divergence.py` exists) — belongs on the re-baseline branch #15.
3. **Re-measure the self-vs-baseline denominator gap at the shipped `lam = 0.1`**
   (D-028's read suggests the verdict flips) — unpicked for eight cycles.

## Artifacts

- PR: #67 (existing, in-queue — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/citation_audit.py` (new),
  `eval/mppi_sandbox/tests/test_citation_audit.py` (new),
  `eval/mppi_sandbox/horizon_audit.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
