# Cycle Journal — Representation-Aware-MPPI

이 파일은 hourly auto-research executor 의 5-phase 루프 (REVIEW → PLAN → EXECUTE → REPORT → PLAN_NEXT) 가 매 cycle 끝에 prepend 하는 **digest 묶음**. 한 entry = 한 cycle, 최신이 위. Full report 는 `journal/YYYY-MM/DD-HH-<slug>.md` 에 — 여기는 다음 cycle 의 REVIEW 가 5건만 빠르게 훑는 용도.

캡: 20 entry. 그 너머는 잘려나가지만 `journal/` 안의 per-cycle 파일이 canonical 기록으로 남음. 자세한 규약은 [`journal/README.md`](journal/README.md).

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
