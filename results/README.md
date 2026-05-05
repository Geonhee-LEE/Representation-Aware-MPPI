# results/

Append-only TSV logs for autoresearch experimental thrusts.
Convention adapted from `karpathy/autoresearch` (single TSV per branch, append-only).

## Files

One TSV per `autoresearch/<phase>-<slug>` branch:

```
results/<phase>-<slug>.tsv
```

Example: `results/p1-bev-semseg-baseline.tsv` corresponds to branch
`autoresearch/p1-bev-semseg-baseline`.

## Format

Tab-separated, header row required on first append:

```
timestamp	commit	metric	status	description
2026-05-08T10:14:22+09:00	a3f1c2e	qual:build-pass	in_progress	Wired BEV node skeleton; no projection math yet
2026-05-08T10:27:09+09:00	b4e0d11	qual:topics-flow	keep	/bev/raw publishes at ~10 Hz, mono channel
2026-05-08T10:41:55+09:00	c92f7ab	qual:doc-only	keep	Channel taxonomy v0 spec'd in docs/bev_channels.md
```

### Columns

| col | meaning |
|---|---|
| `timestamp` | ISO-8601 with offset (KST `+09:00`). |
| `commit` | Git short SHA (the commit this row is about). |
| `metric` | Pre-P5: qualitative string `qual:<short>` (e.g. `qual:build-pass`, `qual:sim-launches-clean`, `qual:topics-flow`, `qual:doc-only`, `qual:script-syntax-ok`). P5+: float, plus the metric name as a suffix (e.g. `success_rate=0.78`). |
| `status` | One of: `keep` / `discard` / `crash` / `in_progress`. |
| `description` | One-line human note. ≤ 160 chars. |

### Status semantics

- `keep` — change is worth carrying forward; baseline for the next iteration.
- `discard` — tried it, reverted (or planning to). The commit may stay in history but the line of work doesn't.
- `crash` — build/test broke or harness errored. Investigate before re-running.
- `in_progress` — partial work, executor budget hit; resume next run.

## Rules

1. **Append-only.** Never edit past rows. If a `keep` row turns out to be wrong, append a follow-up `discard` row that references it in the description.
2. **One TSV per branch.** Don't merge across branches. When a branch lands on `main`, the TSV stays as the historical record for that thrust.
3. **Header on first append.** Subsequent appends just add data rows.
4. **Commits referenced must exist** in the corresponding branch (no hand-edited orphan rows).

## Why qualitative metrics pre-P5

P5 (weeks 15–18) introduces the first quantitative eval harness — until then, "did the build pass" / "did the sim launch cleanly" / "do the topics flow at expected rate" are the only repeatable checks. The TSV format accepts both qualitative and quantitative metrics so the same tooling carries through.

## Reading

```bash
column -ts $'\t' results/p1-bev-semseg-baseline.tsv | less -S
```
