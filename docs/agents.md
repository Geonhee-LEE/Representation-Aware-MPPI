# Agents — 4개 자율 cron 에이전트 + 보조

각 에이전트는 **단일 책임 + 단일 prompt 파일 + 단일 cron 슬롯** 을 가진다. shell 스크립트는 wrapper일 뿐, 로직은 `scripts/prompts/*.md` 에 있다.

---

## 한눈에

```
                          ┌───────────────────────┐
                          │  공유 blackboard       │
                          │  CLAUDE.md            │
                          │  STATE.md             │
                          │  JOURNAL.md           │
                          │  research/feed.md     │
                          │  Notion TODO DB       │
                          │  results/*.tsv        │
                          │  RESULTS.md           │
                          └─────┬─────────────┬───┘
                                ↑             ↓
   ┌──────────┐  ┌──────────┐  │  ┌────────┐ │  ┌──────────┐
   │Researcher│  │ Planner  │──┘  │Builder │─┘  │ Curator  │
   │  4h cron │  │ +Executor│     │ in-line │   │ 23:00 day│
   └──────────┘  └──────────┘     └────────┘    └──────────┘
        +
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │  Brief   │  │  Wrap    │  │  Weekly  │  │  Inbox   │
   │ 09:00 day│  │ 22:00 day│  │ Sun 22:30│  │ 2분 poll  │
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
                                              + Urgent (tmux on demand)
```

---

## A. 핵심 4-agent (북극성에 직접 기여)

### A1. Researcher (`scripts/prompts/researcher.md`)
- **목적**: 외부 최신 동향 (MPPI / social nav / flow matching / Nav2) 발견 → `research/feed.md` 누적 → 선별 TODO 화
- **Cron**: `0 */4 * * *` (4시간마다)
- **입력**: `research/feed.md` 최근 5건 (dedup), `STATE.md` (현 bottleneck 알아야 search query 정렬)
- **출력**: feed.md prepend, `research/YYYY-MM/<seq>.md` 아카이브, Notion `[research]` TODO ≤2개
- **도구**: `WebSearch`, `WebFetch`, `Bash`, `mcp__claude_ai_Notion__*`
- **Telegram**: 신규 발견 시 digest 1건, 없으면 silent
- **종료 신호**: `RESEARCHER_DONE found=N todos=K` / `RESEARCHER_SKIP reason=...`

### A2. Planner + Builder (`scripts/prompts/auto_research.md`, executor wrapper)
- **목적**: 1 cycle = 1 TODO 자율 처리 (코드/문서/PR)
- **Cron**: `0 * * * *` (매시간)
- **입력**: `CLAUDE.md` (north star), `STATE.md`, `JOURNAL.md` top 5, `RESULTS.md`, Notion TODO, `research/feed.md` top 5, 최근 merged PR
- **출력**: `autoresearch/<phase>-<slug>` 브랜치 + commit + push + PR + `results/<slug>.tsv` + journal entry + STATE 갱신
- **도구**: `Bash`, `Read`, `Edit`, `Write`, `Grep`, `Glob`, Notion MCP
- **안전 게이트** (스킵 조건):
  - PR 큐 ≥6 → `EXECUTOR_SKIP reason=pr-queue-full`
  - 24h 내 신규 브랜치 ≥10 → `daily-cap-reached`
  - `Status=Doing` 24h 정체 ≥1 → `stuck-todo`
  - actionable backlog 0건 → `no-actionable-todo`
- **5-phase budget**: REVIEW 5min + PLAN 5min + EXECUTE 15min + REPORT 5min + PLAN_NEXT 5min = 35min
- **Telegram**: cycle 완료 시 1건 (skip은 silent)

### A3. Curator (`scripts/prompts/curator.md`)
- **목적**: PR 큐 drain (auto-merge / rebase / attention 라벨)
- **Cron**: `0 23 * * *` (매일 23:00, wrap 후)
- **입력**: open PR 전체, 각 PR 의 label/age/changed files/mergeable status
- **출력**: PR auto-merge / force-rebase / `needs-user-attention` 라벨 / Telegram 보고
- **도구**: `Bash` (gh CLI), `mcp__claude_ai_Notion__notion-fetch`
- **Auto-merge 규약** (3 lines):
  > title `[auto]` + label `safe-auto-merge` + 변경 path 모두 `{docs/**, prompts/*.md, RESULTS/JOURNAL/STATE, journal/, results/*.tsv, research/}` + 48h idle + mergeable + CI green
- **Hard NO**: `src/**` / `eval/**` / `learning/**` / `.github/workflows/**` 자동 머지 금지, 모든 PR auto-close 금지, force-push to main 금지
- **Telegram**: `🧹 Curator: merged=N rebased=M attention=K stale-branches=L`

### A4. Brief + Wrap (`brief.md`, `wrap.md`)
- **Brief**: 09:00 매일 — 어제 지시 / 인박스 / 오늘 후보 TODO 5건 / current bottleneck → Telegram
- **Wrap**: 22:00 매일 — 오늘 commits 요약 / Today TODO 검토 / Recent Activity 갱신 / 회고 → Telegram
- 5-phase loop 의 "human-facing surface" 역할

---

## B. 보조 에이전트

### B1. Weekly Rollup (`weekly.md`)
- **Cron**: `30 22 * * 0` (일 22:30)
- 그 주 7개 daily log → "Weekly Summary YYYY-Www" sub-page 생성

### B2. Telegram Poll (`telegram_inbox.md`)
- **Cron**: `*/2 * * * *` (매 2분)
- 새 메시지 → Notion `💬 Telegram inbox` 적재
- 메시지에 긴급 키워드 (`긴급`/`즉시`/`urgent`/`asap`/`now`) → tmux + `urgent_agent.sh` spawn (Tier 3)

### B3. Urgent Agent (`urgent.md`)
- **Trigger**: telegram_poll 의 키워드 감지
- tmux session 안에서 `claude -p` 자율 실행, hard limits (refuse force-push/rm-rf/system mutation)
- 결과 → `🚨 Urgent log` Notion 섹션 + Telegram

### B4. Mirror TODOs (`mirror_todos.md`)
- **Cron**: `5 22 * * *` (wrap 5분 후)
- Notion TODO DB → repo root `TODO.md` 동기화

---

## C. 권한 매트릭스

| 에이전트 | Bash | Read | Edit | Write | Notion MCP | WebSearch | git push | gh merge |
|---|---|---|---|---|---|---|---|---|
| Researcher | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | feature only | ✗ |
| Planner+Builder | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | feature only | ✗ |
| Curator | ✓ (gh) | ✓ | ✗ | ✗ | fetch only | ✗ | feature force-with-lease | ✓ safe-only |
| Brief | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Wrap | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Weekly | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Inbox | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| Urgent | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | feature only | ✗ |

---

## D. 새 에이전트 추가 절차

1. `scripts/prompts/<name>.md` 작성 (다른 prompt 참고, 5-phase 또는 단일 task 구조)
2. `scripts/<name>.sh` 작성 (`daily_brief.sh` 패턴 — flock + log + allowlist)
3. `chmod +x scripts/<name>.sh`
4. `crontab -e` 한 줄 추가
5. `docs/agents.md` (이 파일) 의 표 + 권한 매트릭스에 행 추가
6. `_cron_log_snippet.md` 의 `<script>` enum 에 추가
7. smoke test 1회 `bash scripts/<name>.sh`

---

_이 문서는 사람이 갱신. Curator가 stale 감지 시 `docs-refresh` 라벨 PR 띄움._
