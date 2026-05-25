# TODO 진입점

이 파일은 사람을 위한 짧은 안내. 실제 TODO 데이터는 4 surface 에 있다:

| Surface | 어디 | 갱신 |
|---|---|---|
| Notion TODO DB (canonical) | https://www.notion.so/b0b1bd5492d94cf89844a7e9cf7d166d | Researcher / Builder 실시간 |
| `TODO.md` (offline mirror) | repo root | `scripts/mirror_todos.sh` 매일 22:05 |
| GitHub issues | https://github.com/Geonhee-LEE/Representation-Aware-MPPI/issues | 사용자 또는 `claude_dev` 워크플로 |
| GitHub PRs | https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pulls | Builder 자동 |

---

## 빠른 사용 (사람 입장)

### 무엇이 진행 중인지 보기
- 모바일/PC 어디서나 → [`TODO.md`](../TODO.md) (repo root)
- 풍부한 UI → Notion DB (위 링크)
- PR 형태로 → `gh pr list --state open`

### 새 작업 지시하기
3가지 surface 중 어느 곳이나 됨:
1. **Notion DB** → 새 row 추가, Status=`Today`, Owner=`claude`
2. **GitHub issue** → `Claude Task` 템플릿, `claude-task` 라벨 자동 부여
3. **Telegram bot** → 그냥 메시지 (`💬 inbox` 적재 → 다음 brief surface)
   또는 `긴급 <task>` (즉시 tmux executor spawn)

### 작업 완료 알림
- Notion `Status=Done` 으로 변경 OR
- PR 머지 (`Closes #N` body 면 issue 도 자동 close) OR
- Curator 가 48h idle [safe-auto-merge] doc PR auto-merge

---

## 어디서 어느 게 권위인가 (canonical authority)

| 정보 종류 | Canonical | 다른 곳 |
|---|---|---|
| 작업 상태 | Notion DB | TODO.md mirror, issue label, PR state |
| 코드 결과 | main 브랜치 | results/*.tsv, journal/, JOURNAL/STATE |
| 측정 metric | `runs/*.json` + `RESULTS.md` | (지금은 qual:*, P5+ 정량) |
| 외부 reference | `research/feed.md` | (issue body 인용) |
| 시스템 상태 | `STATE.md` | (매 cycle rewrite) |
| 변경 timeline | git log + JOURNAL.md | (PR 머지 메시지) |
| North star | `CLAUDE.md` + `docs/prd.md` | (논의 시 인용) |

---

## TODO 의 생애주기

```
[새 TODO]
  Notion 에 row 추가 (Status=Backlog/Today, Owner=claude|user)
        │
        ├── Builder 가 pick (cron 매시간)
        │     Status: Today → Doing
        │     branch + commit + push + PR 생성
        │     Status: Doing → Done (or Blocked)
        │
        └── 또는 사용자 직접 (PR open)
              PR body 에 "Closes #N" or "TODO: <short-id>"
              머지 시 GitHub 가 issue close

[NeedsUserTest=true 인 경우]
  Builder 가 PR 생성 후 Telegram `🧪 Test request` 발송
  사용자 답글 `ok` / `fail: ...` / `skip` 으로 다음 cycle 반영
```

---

## Stuck TODO 처리

`Status=Doing` 24h 이상 변화 없으면 Builder 의 안전 게이트가 `EXECUTOR_SKIP reason=stuck-todo` + Notion 에 `[stuck]` 제목 prefix 추가.

사용자 액션:
- Notion 에서 직접 Status 조정 (Backlog 로 되돌리거나 Done 으로 종결)
- 또는 GitHub 이슈로 끌어내 더 작은 단위로 쪼개기

---

_이 문서는 정적 안내. TODO 데이터는 위 4 surface 참조._
