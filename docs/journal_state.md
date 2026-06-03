# STATE / JOURNAL / journal/ — cycle 회고 자산

자동 R&D 루프의 **시간축 누적 기억**. 5-phase loop (REVIEW → PLAN → EXECUTE → REPORT → PLAN_NEXT) 의 REPORT phase 가 매 cycle 끝에 갱신.

설계 결정: [`decisions.md`](decisions.md) **D-002** (5-phase 루프 도입), **D-008** (decisions/deliberations 도입).

---

## 3 layer 자산

```
┌──────────────────────────────────────────────────────┐
│  STATE.md (root, 1 page, 매 cycle rewrite)            │
│  → "지금 어디 있나, 다음 무엇" 의 단일 스냅샷           │
│  → REVIEW phase 가 다음 cycle 시작 시 첫 줄로 읽음     │
└─────────────┬────────────────────────────────────────┘
              │
┌─────────────▼────────────────────────────────────────┐
│  JOURNAL.md (root, 최근 20 cycle digest, prepend)    │
│  → 각 cycle 1 paragraph "pick / outcome / next"      │
│  → REVIEW phase 가 top 5 entry 만 읽음 (bloat 방지)   │
└─────────────┬────────────────────────────────────────┘
              │
┌─────────────▼────────────────────────────────────────┐
│  journal/YYYY-MM/DD-HH-<slug>.md (cycle full report) │
│  → ≤80 lines, 상세 reflection                         │
│  → REVIEW phase 가 routinely 안 읽음 (필요시만)        │
└──────────────────────────────────────────────────────┘
```

추가: **decisions.md / deliberations.md** 는 cycle level 위의 **결정 timeline** (D-NNN / Q-NNN). REVIEW phase 가 항상 읽지 않고 신규 결정 발생 시에만 갱신.

---

## STATE.md — "지금 어디 있나"

매 cycle REPORT phase 가 **전체 overwrite** (append 아님). 한 페이지에:
- North star distance
- Current bottleneck
- Open experiments (table)
- Recent learnings (last 3 cycles)
- Next 3 priorities (actionable)
- Cycles to date

크기 일정 → 시간 축 길어져도 REVIEW prompt 폭주 방지.

---

## JOURNAL.md — 최근 20 cycle digest

prepend, 캡 20 entry. 그 너머는 잘려나가지만 `journal/` 의 per-cycle 파일이 canonical.

각 entry:
```markdown
## YYYY-MM-DD HH:MM — <slug>
- **Pick**: <TODO title>
- **Outcome**: <1 sentence>
- **Next**: <one of the recommended priorities>
- **Full**: [`journal/YYYY-MM/DD-HH-<slug>.md`](journal/YYYY-MM/DD-HH-<slug>.md)
```

읽는 쪽: 다음 cycle REVIEW (top 5 entry 만, bloat 방지). LRU cap 핵심: cycle 수 무관 prompt 입력 크기 일정.

---

## journal/YYYY-MM/DD-HH-<slug>.md — 상세 report

≤80 lines, append-only. 필수 섹션:
- **What I tried** (2-4 bullets)
- **What worked / what failed**
- **North-star delta** (zero-impact run 도 honest)
- **Key learnings**
- **Recommended next 1-3 priorities**
- **Artifacts**

읽는 쪽: routinely X. retroactive 또는 cross-link 시.

---

## Phase 4 REPORT 의 4 step 분기

```
Phase 4 REPORT
  ├── 4a) journal/YYYY-MM/DD-HH-<slug>.md  ── 매 cycle 항상
  │
  ├── 4a-bis) (선택)
  │     ├── docs/decisions.md  ── architecture/scope/priority 결정 시
  │     └── docs/deliberations.md  ── open trade-off 발견 시
  │
  ├── 4b) JOURNAL.md  ── prepend (cap 20)
  ├── 4c) STATE.md  ── 전체 rewrite
  └── 4d) Telegram cycle summary  ── 1 message per cycle
```

trivial 변경 → journal 만, decisions/deliberations skip. 신호 대 잡음 비율 보호.

---

## 회고 활용

- **단기** (다음 cycle REVIEW): STATE → PLAN input, JOURNAL top 5 → 최근 흐름
- **중기** (Wrap 22:00 / Weekly 일 22:30): 그 날/주 모든 journal 종합 → 회고
- **장기** (사람 회고): decisions.md timeline → "왜 이 방향" 한눈에 (28일간 D-001~D-008)

---

## 한계

- decisions.md D-NNN 발급은 cron 자동 — trivial/결정 구분 prompt 의존, 실수로 부풀림 가능. Curator (issue #41) weekly cleanup.
- STATE.md single page → 시퀀스 보려면 git log + JOURNAL 조합
- journal/ monthly subdir 1 년 후 12 dir, archival rotation 미정 (agents.md 미래 작업)

---

## 관련

- [`agents.md`](agents.md) A2 Planner+Builder, B1 Weekly
- [`skills.md`](skills.md) C 공통 contract
- [`automation.md`](automation.md) — Phase 4 cron/Notion/Telegram 연결
- [`decisions.md`](decisions.md), [`deliberations.md`](deliberations.md) — cycle-above timeline

_2026-06-03 KST_
