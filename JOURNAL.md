# Cycle Journal — Representation-Aware-MPPI

이 파일은 hourly auto-research executor 의 5-phase 루프 (REVIEW → PLAN → EXECUTE → REPORT → PLAN_NEXT) 가 매 cycle 끝에 prepend 하는 **digest 묶음**. 한 entry = 한 cycle, 최신이 위. Full report 는 `journal/YYYY-MM/DD-HH-<slug>.md` 에 — 여기는 다음 cycle 의 REVIEW 가 5건만 빠르게 훑는 용도.

캡: 20 entry. 그 너머는 잘려나가지만 `journal/` 안의 per-cycle 파일이 canonical 기록으로 남음. 자세한 규약은 [`journal/README.md`](journal/README.md).

---

## 2026-05-31 23:00 — p2-training-data-collection
- **Pick**: P2 training-data collection path (replay buffer + scripted rollouts)
- **Outcome**: Landed `data_pipeline/` (ReplayBuffer + synthetic diff-drive plant + scripted collector); 300-tuple smoke passes, residual gap learnable. Decoupled from unmerged `learning/`. NOTE: PR-queue gate (≥6) stood at 7 — cycle should have skipped; PR #45 adds to the backlog.
- **Next**: User drains the 8-PR P2 queue (gate-blocking); then numeric dynamics-model eval (MSE nominal vs nominal+residual)
- **Full**: [`journal/2026-05/31-23-p2-training-data-collection.md`](journal/2026-05/31-23-p2-training-data-collection.md)

## 2026-05-28 02:00 — p2-maml-residual-adaptation
- **Pick**: [research] Evaluate MAML-based residual adaptation as sim-to-real transfer strategy for P2 learned dynamics model
- **Outcome**: Design-level analysis mapping MAML meta-learning onto our residual MLP. Composes with energy reg (safety survives adaptation) + ensemble (shared init, diverge at adapt). Completes P2 learned dynamics design triad. < 1 ms adaptation cost.
- **Next**: (user) Install PyTorch + merge PR cluster (#22–27, #41); (claude) extend gen_unicycle_dataset.py with --meta task distribution.
- **Full**: [`journal/2026-05/28-02-p2-maml-residual-adaptation.md`](journal/2026-05/28-02-p2-maml-residual-adaptation.md)

---

## 2026-05-25 00:00 — p2-tcfm-evaluation
- **Pick**: [research] Clone + evaluate TCFM (arxiv 2403.10809, CORE-Robotics-Lab/TCFM)
- **Outcome**: Deep architecture analysis of TCFM's Conditional Flow Matching pipeline. TCFM and cfm_mppi are complementary (backbone vs integration). Recommended Option A (trajectory generator) for P2 prototype. First P2 artifact produced after 15-day executor drought.
- **Next**: (claude) Create synthetic unicycle trajectory dataset generator for TCFM training bootstrap.
- **Full**: [`journal/2026-05/25-00-p2-tcfm-evaluation.md`](journal/2026-05/25-00-p2-tcfm-evaluation.md)

---

## 2026-05-10 18:00 — p0-state-template-split-next-priorities
- **Pick**: [infra] STATE.md template: split next-priorities into claude-actionable vs user-blocked
- **Outcome**: Phase 4c STATE template now has two distinct sections (claude-actionable = PLAN's pool, user-blocked = Telegram queue). Decision tree preamble + REVIEW step 2 + PLAN_NEXT 5a updated together; 5a now derives Owner from the section with mismatch check. +17/-7 LOC, doc-only, four sections kept consistent. PR #12 opened. Removes the `a0a3420`-style fix-up commit class.
- **Next**: (claude) per-class result reporting in `scripts/aggregate_results.sh` (TODO `357c5d39…819a` Backlog).
- **Full**: [`journal/2026-05/10-18-p0-state-template-split-next-priorities.md`](journal/2026-05/10-18-p0-state-template-split-next-priorities.md)

---

## 2026-05-07 10:00 — p0-auto-research-md-gh-pr-create-step
- **Pick**: [infra] auto_research.md EXECUTE phase: make `gh pr create` an explicit step after push
- **Outcome**: New `### Open the PR` section in Phase 3 (gh pr create + skip-if-exists) + Phase 4d Telegram template uses `${PR_URL}`; +33 LOC doc-only; PR #9 opened via the new step itself (dogfood). Eliminates push-without-PR housekeeping debt for future cycles.
- **Next**: (user) Merge PR #7 + #8 + #9 → unblock first quantitative number; (claude post-sim) calibrate v0 thresholds.
- **Full**: [`journal/2026-05/07-10-p0-auto-research-md-gh-pr-create-step.md`](journal/2026-05/07-10-p0-auto-research-md-gh-pr-create-step.md)

---

## 2026-05-06 01:10 — p1-eval-scenarios-yaml-v0
- **Pick**: [north-star] eval/scenarios/*.yaml v0 (4 spec YAMLs + schema README)
- **Outcome**: 4 scenarios scaffolded (cafe-straight A, city-curved B, city-figure8 B, cafe-obstacle-crossing D); schema documented; all parse + required-key check pass. `qual:yaml-parse-ok` row, status=keep.
- **Next**: User-blocked PR-merge cluster (PR #4 → run_metrics PR → this PR), then wire `include_run_metrics:=true` flag into jackal_cafe.launch.py.
- **Full**: [`journal/2026-05/06-01-p1-eval-scenarios-yaml-v0.md`](journal/2026-05/06-01-p1-eval-scenarios-yaml-v0.md)

---

## 2026-05-06 00:00 — p1-eval-run-metrics-node (entry pending PR merge to main)
- **Pick**: [north-star] eval/run_metrics.py — ROS2 node wrap of v0 metrics
- **Outcome**: Live ROS2 node + 8/9 unit tests (1 skipped on PR #4 import). `/odom + /plan` → `runs/<id>.json`. Lives on `autoresearch/p1-eval-run-metrics-node`.
- **Next**: User merge PR #4 + this branch's run_metrics PR + the scenarios YAML PR (this cycle).
- **Full**: [`journal/2026-05/06-00-p1-eval-run-metrics-node.md`](journal/2026-05/06-00-p1-eval-run-metrics-node.md) (lands on main after run_metrics PR merge)

---

## 0000-bootstrap — 2026-05-05 23:30 KST
- **Pick**: 5-phase loop 인프라 배포 (STATE.md / JOURNAL.md / journal/ + auto_research.md 재작성)
- **Outcome**: REVIEW→PLAN→EXECUTE→REPORT→PLAN_NEXT 루프가 다음 cron tick 부터 가동. 이전엔 단순 pick-and-execute 였음. north-star 거리 변화 0 — pure infra.
- **Next**: A1 (Jackal cafe/city 인터랙티브 sim 1회 시각 검증) — STATE.md 의 current bottleneck.
- **Full**: 이 entry 는 bootstrap — per-cycle journal 파일 없음. 다음 entry 부터 [`journal/`](journal/) 링크.
