# Cycle Journal — Representation-Aware-MPPI

이 파일은 hourly auto-research executor 의 5-phase 루프 (REVIEW → PLAN → EXECUTE → REPORT → PLAN_NEXT) 가 매 cycle 끝에 prepend 하는 **digest 묶음**. 한 entry = 한 cycle, 최신이 위. Full report 는 `journal/YYYY-MM/DD-HH-<slug>.md` 에 — 여기는 다음 cycle 의 REVIEW 가 5건만 빠르게 훑는 용도.

캡: 20 entry. 그 너머는 잘려나가지만 `journal/` 안의 per-cycle 파일이 canonical 기록으로 남음. 자세한 규약은 [`journal/README.md`](journal/README.md).

---

## 0000-bootstrap — 2026-05-05 23:30 KST
- **Pick**: 5-phase loop 인프라 배포 (STATE.md / JOURNAL.md / journal/ + auto_research.md 재작성)
- **Outcome**: REVIEW→PLAN→EXECUTE→REPORT→PLAN_NEXT 루프가 다음 cron tick 부터 가동. 이전엔 단순 pick-and-execute 였음. north-star 거리 변화 0 — pure infra.
- **Next**: A1 (Jackal cafe/city 인터랙티브 sim 1회 시각 검증) — STATE.md 의 current bottleneck.
- **Full**: 이 entry 는 bootstrap — per-cycle journal 파일 없음. 다음 entry 부터 [`journal/`](journal/) 링크.
