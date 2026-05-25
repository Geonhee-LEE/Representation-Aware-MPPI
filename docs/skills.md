# Skills — prompt ↔ tool ↔ artifact 매핑

> "Skill" = 한 prompt 파일이 정의하는 **재사용 가능한 단위 작업** + 호출하는 도구 셋 + 산출 artifact.
> karpathy/autoresearch 의 `program.md` 개념 차용.

각 에이전트의 prompt 가 곧 skill. 새 skill 추가 = 새 prompt 추가.

---

## A. 활성 skill 인벤토리

| Skill (prompt) | 호출 wrapper | 도구 allowlist | 산출 artifact | 트리거 |
|---|---|---|---|---|
| `brief.md` | `daily_brief.sh` | Bash / Read / Notion MCP | Notion entry + Telegram digest | cron 09:00 |
| `auto_research.md` | `daily_executor.sh` | Bash / Read / Edit / Write / Grep / Glob / Notion MCP | branch + commit + PR + TSV + journal + STATE | cron 매시간 |
| `wrap.md` | `daily_wrap.sh` | Bash / Read / Edit / Write / Notion MCP | Notion entry 갱신 + Recent Activity + Telegram | cron 22:00 |
| `weekly.md` | `weekly_rollup.sh` | Bash / Read / Notion MCP | Notion Weekly Summary sub-page + Telegram | cron 일 22:30 |
| `telegram_inbox.md` | `telegram_poll.sh` (claude path) | Bash / Notion MCP | Notion 💬 inbox 추가 | cron 매 2분 (메시지 있을 때만) |
| `urgent.md` | `urgent_agent.sh` (tmux) | Bash / Read / Edit / Write / Grep / Glob / Notion MCP | 결과 + 🚨 Urgent log + Telegram | telegram_poll 키워드 감지 |
| `researcher.md` | `researcher.sh` | Bash / Read / Edit / Write / WebSearch / WebFetch / Notion MCP | `research/feed.md` + `research/YYYY-MM/<seq>.md` + Notion TODO | cron 4시간 |
| `curator.md` | `curator.sh` | Bash (gh CLI) / Read / Notion fetch | PR auto-merge / rebase / label + Telegram | cron 23:00 |
| `mirror_todos.md` | `mirror_todos.sh` | Bash / Notion MCP | `TODO.md` 갱신 | cron 22:05 |
| `_cron_log_snippet.md` | (참조용) | — | `🤖 Cron activity` 한 줄 컨벤션 | 모든 cron skill 의 마지막 단계 |

---

## B. Skill 간 의존성

```
researcher.md  ──writes──►  research/feed.md  ──reads──►  auto_research.md
                                                              │
                                                              ├──writes──►  results/<slug>.tsv
                                                              ├──writes──►  journal/<file>.md
                                                              ├──writes──►  STATE.md ◄──reads── brief.md
                                                              └──pushes──►  autoresearch/<slug>  ◄──merges── curator.md
                                                                                                       │
                                                                                                       └──writes──►  main

telegram_inbox.md  ──writes──►  Notion 💬 inbox  ──reads──►  brief.md (다음 09:00)
                   └──spawns──►  urgent.md (긴급 키워드)

wrap.md  ──reads──►  results/*.tsv + journal/* + Notion TODO + git log
         └──writes──►  STATE / JOURNAL / Notion entry / Recent Activity

mirror_todos.md  ──reads──►  Notion TODO  ──writes──►  TODO.md
```

---

## C. 공통 contract (모든 cron skill 이 지켜야 함)

### C1. Cron activity 로깅
모든 skill 의 마지막 단계는 today entry 의 `🤖 Cron activity` 섹션에 한 줄 append:
```
- **HH:MM** `<script>` · <≤80자 한국어 한 줄>
```
`<script>` enum: `brief | executor | researcher | wrap | curator | weekly | inbox | urgent`

### C2. Lock + log
- Lock: `~/.local/state/representation-aware-mppi/<skill>.lock` (flock 단일 인스턴스)
- Log: `~/.local/share/representation-aware-mppi/logs/<skill>-YYYY-MM-DD.log`

### C3. Telegram 안전
- bot/chat_id: `~/.config/representation-aware-mppi/telegram.env` (chmod 600)
- silent skip 일 때 알림 발송 금지 (수면 방해)
- `disable_notification=true` 옵션을 bookkeeping 메시지에 사용

### C4. 에러 처리
- 실패 시 `❌ <skill> 실패: <reason>` Telegram 1건 + non-zero exit
- 부분 실패는 stdout 에 명시하고 cron 은 계속 진행

### C5. 시간 예산
- Skill 자체에 명시된 분량 (예: `auto_research.md` 35min)
- 초과 시 강제 종료 OR 다음 cycle 로 이월

---

## D. 외부 의존성 (모든 skill 공통)

| 자원 | 위치 | 용도 |
|---|---|---|
| `claude` CLI | `/home/geonhee/.local/bin/claude` | LLM 호출 |
| Notion MCP | Claude Code 설정 | `mcp__claude_ai_Notion__*` 도구 |
| `gh` CLI | system | GitHub API (issue/PR/repo) |
| `curl`, `jq`, `flock`, `tmux` | system pkg | 셸 유틸 |
| Telegram bot | `~/.config/representation-aware-mppi/telegram.env` | push/poll |
| Anthropic API key | (시스템에서 claude CLI 가 관리) | LLM 호출 인증 |

---

## E. Skill 추가 checklist

1. [ ] `scripts/prompts/<name>.md` 작성
   - Setup section (env, IDs)
   - 단계별 step 명세 (Step 1, 2, ...)
   - Stdout 마지막 줄 컨벤션 (`SKILL_DONE ...` / `SKILL_SKIP ...`)
   - Constraints (Korean for Telegram, no destructive ops, etc.)
2. [ ] `scripts/<name>.sh` 작성 (flock + log dir + claude -p + allowlist)
3. [ ] `chmod +x scripts/<name>.sh`
4. [ ] `scripts/prompts/_cron_log_snippet.md` `<script>` enum 에 추가
5. [ ] `docs/agents.md` 표 + 권한 매트릭스에 행
6. [ ] `docs/skills.md` (이 파일) A 표에 행
7. [ ] `crontab -e` 한 줄
8. [ ] smoke test `bash scripts/<name>.sh` 1회 + 로그/Notion/Telegram 검증

---

## F. Skill 라이프사이클 + 회전

skill 자체는 git 으로 버전 관리. 변경 시:
- 작은 튜닝: 직접 prompt 수정 → 다음 cron 실행에 즉시 반영 (재빌드 불필요)
- 큰 변경: brand new skill 추가 + 기존 skill `_deprecated` suffix → cron 빼고 일정 기간 후 삭제

`auto_research.md` 의 5-phase 구조는 안정화됨. 새 phase 추가는 신중하게 (REVIEW/REPORT 예산 초과 위험).

---

_이 문서는 사람이 갱신. Curator 가 stale 감지 시 `docs-refresh` 라벨 PR 띄움._
