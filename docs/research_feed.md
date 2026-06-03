# research/feed.md — 외부 SOTA 자동 trawl

`research/` 디렉토리는 Researcher agent (`scripts/researcher.sh`, 4시간 cron) 가 web search 로 발견한 외부 paper / github / blog 누적 기록.

설계 결정: [`decisions.md`](decisions.md) **D-003** (multi-agent 도입). Researcher 역할/도구: [`agents.md`](agents.md) A1 + [`researcher.md`](researcher.md).

---

## 자산 구조

```
research/
├── README.md      (컨벤션)
├── feed.md        (newest first, cap 30 entries — Researcher 가 prepend)
└── YYYY-MM/       (월별 archive — 캡 넘은 entry 보관)
```

- **feed.md** = LRU cache, 신규 5 entry 가 다음 cycle Planner+Builder REVIEW 입력
- **YYYY-MM/** = append-only 영구, agent 가 routinely 안 읽음

---

## entry 형식

```markdown
## YYYY-MM-DD HH:MM — <short title>
- **Source**: <URL>
- **Type**: arxiv | github | blog | benchmark | dataset
- **Why relevant**: <1-2 sentences tying to north star or current phase>
- **Suggested TODO**: <none | one-line action>
```

- **Type**: 5 enum 만
- **Why relevant**: phase 또는 north star 와 연결 명시. 단순 "흥미로운 paper" → skip
- **Suggested TODO**: 선별적 — cycle 당 ≤2 항목만 실제 Notion TODO 로 promote

---

## Researcher 의 dedup gate

매 cycle 시작 시 feed.md 최근 5 entry 읽음:
- 마지막 entry **<23시간** 전 → "lite mode" (3 query)
- 그 너머 → "full mode" (3-8 query)

→ cron 마다 폭주 없음. 중복 entry 없음.

---

## Filter 정책

다음은 feed 에 추가 **안 함**:
- 12개월 이상 old (seminal 제외)
- 직전 5 entry 와 중복
- SEO blog content (substack/medium 수준)
- paywalled 인데 arxiv mirror 없음

→ noise 최소화.

---

## Notion promote 정책

cycle 당 최대 **2 entry** 만 TODO 생성:
- 우선순위: north star 의 current bottleneck 과 가장 가까운 entry
- 형식: TODO title 에 `[research]` prefix + Source URL 인용
- Status=Backlog, Owner=claude (분석 가능) 또는 user (라이선스/architecture 결정)

→ 매주 ~30-50 finding 중 ~14 TODO 만 backlog 적재.

---

## 28일 통계 (대략)

- feed entry 추가: ~60
- 동시 cap 30: 최신 30 visible
- archive YYYY-MM/: 월별 디렉토리 (5/29 부터)
- Notion TODO promote: ~14
- 통합 진행: TCFM analysis (#22 merged), MAML analysis (#41 merged), DPCBF 실측 (#33 Stage A 진행)

---

## 새 paper 직접 추가 (사용자 수동)

1. Researcher 의 다음 cycle (≤4h) 대기, OR
2. 직접 `research/feed.md` 의 top 에 entry prepend + commit

수동 추가 시에도 format 동일 — 다음 cycle dedup gate 가 처리.

---

## Telegram digest

Researcher cycle:
- ≥1 신규 entry → digest 1건 (수면 안 깸):
  ```
  🔬 Research feed +N
  - <title> [<type>]
  📓 research/feed.md
  ```
- 신규 0 → silent

→ 하루 6 cycle × ~2 entry = ~12 digest/day max.

---

## 큰 그림

```
WebSearch arxiv/github
  │
  ▼
Researcher (4h cron) — filter + dedup
  │
  ▼
research/feed.md (cap 30) ──► research/YYYY-MM/<seq>.md (archive)
  │
  ▼ top 5
Planner+Builder REVIEW
  │ relevant → Notion TODO (Backlog)
  ▼
Notion TODO DB
  │ Builder Today pick
  ▼
GitHub PR
  │ Curator (daily) auto-merge
  ▼
main
  │
  ▼
docs/<analysis>.md
```

→ external SOTA → 우리 main 까지 자율 파이프라인.

---

## 관련

- [`agents.md`](agents.md) A1 Researcher
- [`researcher.md`](researcher.md) — 1-page explainer
- [`dynamic_obstacles_uncertainty_track.md`](dynamic_obstacles_uncertainty_track.md) — dynamic/uncertainty entry 흐름

_2026-06-03 KST_
