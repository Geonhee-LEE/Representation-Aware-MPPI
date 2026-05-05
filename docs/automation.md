# Daily / Weekly Automation

매일 자동으로 Notion에 작업 내역이 정리되고 Telegram으로 알림이 오도록 구축한 시스템. 사용자는 이동 중 폰에서 메시지를 보내 다음 날 방향을 지시할 수 있음.

## 한 화면 요약

```
┌─────────────────────────── 매일 ───────────────────────────┐
                                                              
   09:00  brief.sh   ──► Notion 오늘 entry 생성                
                       + 어제 지시/inbox 종합                  
                       + Telegram 푸시                         
                                                              
   22:00  wrap.sh    ──► Notion 오늘 entry 마감                
                       (Done/Blockers/Build/Commits 채움)      
                       + Root page "Recent Activity" 갱신      
                       + Telegram 푸시                         
                                                              
   매 2분   telegram_poll.sh ──► 사용자가 봇에 보낸 메시지를     
                                Notion 오늘 entry "💬 Telegram 
                                inbox" 섹션에 누적              
                                                              
└────────────────────── 일요일 22:30 ──────────────────────────┘
                                                              
   weekly_rollup.sh ──► Root page 하위에                       
                       "Weekly Summary YYYY-Www" sub-page 생성 
                       + Telegram 다이제스트                    
                                                              
└──────────────────────────────────────────────────────────────┘
```

## 파일 구성

```
scripts/
├── daily_brief.sh          # cron 09:00 entry point
├── daily_executor.sh       # cron 10:00 entry point (auto-research loop, flock 단일 인스턴스)
├── daily_wrap.sh           # cron 22:00 entry point
├── weekly_rollup.sh        # cron 일 22:30 entry point
├── telegram_poll.sh        # cron 매 2분 entry point (flock 단일 인스턴스)
├── urgent_agent.sh         # telegram_poll.sh가 긴급 키워드 감지 시 tmux로 spawn
├── seed_todos.tsv          # TODO DB 초기 backlog (P0~P6, ~54건)
└── prompts/
    ├── brief.md                # 09:00에 claude -p가 읽는 지시문
    ├── auto_research.md        # 10:00 executor 지시문 (autoresearch program.md 패턴)
    ├── wrap.md                 # 22:00 지시문
    ├── weekly.md               # 일요일 22:30 지시문
    ├── telegram_inbox.md       # telegram_poll.sh가 새 메시지 있을 때만 호출
    ├── urgent.md               # urgent_agent.sh 실행 지시문 (Tier 3 제한)
    └── _cron_log_snippet.md    # 모든 프롬프트가 참조하는 "🤖 Cron activity" 로깅 규약
```

각 셸 스크립트는 짧음 — 실제 로직은 모두 `prompts/*.md` 에 있어서 동작을 바꾸려면 프롬프트만 수정하면 됨 (재빌드/재배포 불필요). 첫 줄 한 번 수정 후 다음 cron 실행에 즉시 반영.

## 동작 원리

각 entry-point 셸은 본질적으로 동일한 패턴:

```bash
claude -p "$(cat scripts/prompts/<name>.md)" \
  --output-format text \
  --permission-mode acceptEdits \
  --allowedTools Bash Read mcp__claude_ai_Notion__*
```

`claude -p` 가 비대화형으로 실행되며, 프롬프트에 명시된 단계대로 Notion MCP + Bash(curl/git) 도구를 호출. 권한 프롬프트가 뜨지 않도록 `--allowedTools` 로 사전 허용.

`telegram_poll.sh` 만 예외 — `claude -p` 호출 비용을 줄이려고 **새 메시지가 있을 때만** LLM 단계로 진입. 평소엔 순수 `curl + jq` 만 돌면서 Telegram getUpdates 가 빈 결과를 돌려주면 즉시 종료.

## Cron 등록

```cron
0    9 * * *   /home/geonhee/Representation-Aware-MPPI/scripts/daily_brief.sh
0    * * * *   /home/geonhee/Representation-Aware-MPPI/scripts/daily_executor.sh   # 매시간 executor (hourly) — safety gates 참조
0   22 * * *   /home/geonhee/Representation-Aware-MPPI/scripts/daily_wrap.sh
30  22 * * 0   /home/geonhee/Representation-Aware-MPPI/scripts/weekly_rollup.sh
*/2  * * * *   /home/geonhee/Representation-Aware-MPPI/scripts/telegram_poll.sh
```

**executor cadence 변경 (10:00 → 매시간)**: `auto_research.md` 의 "Hourly cadence safety gates" 섹션에 4개 게이트 정의 — PR 큐 ≥3, stuck TODO ≥1 (24h 갱신 없음), 24h 내 신규 브랜치 ≥6, actionable backlog 0건. 어떤 게이트라도 fire 하면 `EXECUTOR_SKIP reason=...` 으로 무음 종료 (Telegram 알림 없음, `🤖 Cron activity` 한 줄만).

시스템 timezone 이 `Asia/Seoul` 이면 위 시각이 KST 기준. 다른 TZ 시스템이면 cron 라인 앞에 `TZ=Asia/Seoul` 추가.

## 외부 의존성

| 자원 | 위치 | 비고 |
|---|---|---|
| Telegram bot 토큰 | `~/.config/representation-aware-mppi/telegram.env` (chmod 600) | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| Notion 워크스페이스 | Claude Code MCP 통합 (`mcp__claude_ai_Notion__*`) | 토큰 별도 관리 불필요 |
| Notion root page | `353c5d39-343d-80f5-990e-c5a35c03d301` | 프롬프트에 하드코딩 |
| Daily Log data source | `collection://6c727442-39fb-4f88-915f-c779db3d7109` | 프롬프트에 하드코딩 |
| `claude` CLI | `/home/geonhee/.local/bin/claude` | 셸 스크립트가 PATH 보강 |
| `tmux`, `curl`, `jq`, `flock` | 시스템 패키지 | urgent flow + 폴링이 사용 |

## Notion 구조

```
Representation-Aware-MPPI (root page)
├── 핵심 가설
├── Phased Roadmap (체크리스트)
├── Stack (표)
├── 📈 Recent Activity (최근 7일)   ← wrap.sh 가 매일 갱신
├── ## Daily Log
├── (database) Daily Log             ← 매일 entry 추가
│   └── 🚀 YYYY-MM-DD                ← brief.sh 가 생성
│       ├── 📋 어제 받은 지시
│       ├── 🔧 오늘 시작 시점 상태
│       ├── ✅ 오늘 한 일             ← wrap.sh 채움
│       ├── 🚧 Blockers
│       ├── 📋 Today's Instructions   ← 사용자 입력
│       ├── 🤖 Cron activity         ← 모든 cron 실행이 한 줄씩 append
│       ├── 🚨 Urgent log            ← urgent_agent.sh 결과 (해당 시)
│       └── 💬 Telegram inbox        ← telegram_poll.sh 채움
└── 📅 Weekly Summary YYYY-Www      ← weekly_rollup.sh 가 매주 생성
    ├── 🎯 Phase progress
    ├── ✅ Shipped
    ├── 🚧 Carried-over blockers
    ├── 🔢 Numbers
    ├── 💡 사용자 지시 (이번 주)
    ├── 📌 다음 주 제안
    └── 📓 일일 entries (링크)
```

## Telegram 양방향 흐름

**Bot → User** (push):
- 09:00 morning brief
- 22:00 evening wrap
- 일 22:30 weekly digest
- 폴링 시 새 메시지 받으면 무음 confirmation `📥 Notion inbox에 N건 추가`

**User → Bot** (pull, 2분 간격):
- 사용자가 폰에서 메시지 보냄 (예: "내일은 P1 BEV 시작")
- 다음 폴링 (≤2분) 에서 getUpdates 가 가져옴
- claude 가 오늘 Daily Log entry 의 `💬 Telegram inbox` 섹션에 timestamp + 텍스트로 추가
- 다음 09:00 morning brief 가 inbox 를 읽고 그날 방향에 surface

**기본 동작 (Tier 1)** 은 inbox 적재만 — 사용자가 Notion 에서 보고 직접 실행 결정. 단, 메시지에 **`긴급`/`즉시`/`urgent`/`asap`/`now`** 키워드가 있으면 아래 **Tier 3 제한 버전** 으로 자동 escalate (tmux 안에서 claude 가 직접 실행).

## 🚨 Urgent 키워드 → tmux 자동 실행 (Tier 3 제한 버전)

폴링이 새 메시지에서 **`긴급`/`즉시`/`urgent`/`asap`/`now`** (대소문자 무시) 를 발견하면, 그 메시지를 분리된 tmux 세션의 `urgent_agent.sh` 에 넘김. 그 안에서 `claude -p` 가 `prompts/urgent.md` 지시문에 따라 자율 실행.

흐름:
```
사용자 폰 메시지 ── "긴급 빌드 상태 알려줘"
       │
       ▼
telegram_poll.sh (2분 cron)
       │  ├── inbox 적재 (평소 흐름)
       │  └── urgent 키워드 감지 ──► tmux 세션 spawn
       │                              │
       │                              ▼
       │                          urgent_agent.sh
       │                              ├── 🚨 시작 알림 → Telegram
       │                              ├── claude -p (Bash/Edit/Write/...)
       │                              │     ├── 1줄 plan → Telegram (무음)
       │                              │     ├── 작업 실행
       │                              │     ├── 결과 → Telegram (소리 ON)
       │                              │     └── Notion entry 의 "🚨 Urgent log" 섹션 append
       │                              └── 60초 linger (사용자 attach 가능)
```

**Hard limits** (urgent.md 에 명시 — claude 가 자체 거절):
- `git push --force` to main 거절
- 리포 밖 `rm -rf` 거절
- `crontab -r` 등 시스템 변경 거절
- 일반 `git push` 는 메시지에 push/배포/release 등이 있을 때만

**라이브 attach** (실시간 진행 보기):
```bash
tmux ls                                    # 진행 중인 urgent 세션 목록
tmux attach -t ram-urgent-YYYYMMDD-...     # attach (Ctrl-b d 로 detach)
```

**로그**: `~/.local/share/representation-aware-mppi/logs/urgent-<session>.log`

**Tier 1 (inbox) 와 충돌 안 함**: urgent 결과는 `🚨 Urgent log` 섹션, 일반 메시지는 `💬 Telegram inbox` 섹션 — 다른 영역이라 동시 실행해도 race 없음.

## 🤖 Cron activity (감사 로그)

브리핑/마감/주간/inbox/urgent — **모든 cron-triggered 스크립트** 가 today 의 Daily Log entry 안 `## 🤖 Cron activity` 섹션에 한 줄을 append. 사용자가 Notion 한 페이지만 봐도 "오늘 cron 이 뭘 했나" 가 즉시 보임 (로컬 로그 파일을 굳이 안 열어도 됨).

형식:
```
- **HH:MM** `<script>` · <한 줄 결과>
```

예시 (실제 entry):
```
- **09:00** `brief` · 오늘 entry 생성, 지시 1건 surface (P0)
- **14:32** `inbox` · 메시지 2건 추가
- **14:32** `urgent` · [ram-urgent-...] ros2 토픽 응답 완료
- **22:00** `wrap` · Status=Done, 커밋 3개, build pass, Recent Activity 갱신
- **22:30** `weekly` · W18 sub-page 생성 (entries=7)
```

규약은 `scripts/prompts/_cron_log_snippet.md` 에 단일 소스로 정리 — 새 cron 스크립트 추가 시 그 한 단계만 따르면 됨.

**조용한 폴링은 로깅 안 함**: `telegram_poll.sh` 가 메시지 0건 발견하면 Notion 에 아무것도 적지 않음 (섹션이 노이즈로 차오르지 않도록). 따라서 이 섹션 길이 = 의미있는 cron 이벤트 수.

**섹션 자동 healing**: 기존 entry 에 섹션이 없으면 첫 cron 호출이 섹션을 새로 만들고 한 줄을 적음. 사용자가 직접 섹션을 만들 필요 없음.

## 로그와 상태

| 경로 | 내용 |
|---|---|
| `~/.local/share/representation-aware-mppi/logs/brief-YYYY-MM-DD.log` | 일일 brief 실행 로그 |
| `~/.local/share/representation-aware-mppi/logs/executor-YYYY-MM-DD.log` | auto-research executor 로그 |
| `~/.local/share/representation-aware-mppi/logs/wrap-YYYY-MM-DD.log` | wrap 로그 |
| `~/.local/share/representation-aware-mppi/logs/weekly-YYYY-Www.log` | 주간 롤업 로그 |
| `~/.local/share/representation-aware-mppi/logs/telegram-poll-YYYY-MM-DD.log` | 폴링 로그 (메시지 있을 때만 채워짐) |
| `~/.local/share/representation-aware-mppi/logs/urgent-<session>.log` | urgent agent 실행 로그 (세션 단위) |
| `~/.local/state/representation-aware-mppi/telegram_last_update_id` | 마지막 처리한 Telegram update_id (폴링 dedup용) |
| `~/.local/state/representation-aware-mppi/telegram_poll.lock` | 폴링 single-instance flock 파일 |
| `~/.local/state/representation-aware-mppi/executor.lock` | executor single-instance flock 파일 (overrun 보호) |

## 동작 변경 / 디버깅

**프롬프트 튜닝**: `scripts/prompts/<name>.md` 만 수정 → 다음 cron 실행에 반영. 셸 스크립트 손댈 일 거의 없음.

**수동 실행 (테스트)**:
```bash
# 한 번 즉시 실행 (cron 기다리지 않고)
./scripts/daily_brief.sh
./scripts/daily_executor.sh    # auto-research loop (TODO DB 가 설정돼 있어야 함)
./scripts/daily_wrap.sh
./scripts/weekly_rollup.sh
./scripts/telegram_poll.sh
# urgent 는 보통 폴링이 spawn 하지만 직접도 가능:
./scripts/urgent_agent.sh "긴급 git 상태 알려줘" "test-$(date +%s)"
```
로그 파일에 결과 기록됨.

**진행 중 urgent 세션 보기**:
```bash
tmux ls                                  # 활성 세션 목록
tmux attach -t ram-urgent-YYYYMMDD-...   # 라이브 보기 (Ctrl-b d 로 detach)
```

**실패 시**: 어떤 entry-point 든 실패하면 `❌ ... 실패` 메시지가 Telegram 으로 자동 발송. 로그를 보고 진단 (보통 Notion API rate limit 또는 프롬프트의 페이지 ID 오타).

**Telegram 토큰 회전**: BotFather → `/revoke` → 새 토큰을 `~/.config/representation-aware-mppi/telegram.env` 에 직접 수정. 코드 변경 불필요.

**Notion 구조 변경**: Daily Log DB 의 schema 를 바꾸면 `prompts/brief.md`, `wrap.md`, `weekly.md`, `telegram_inbox.md`, `urgent.md` 의 schema 참조도 같이 갱신.

**새 cron 스크립트 추가**: 마지막에 `_cron_log_snippet.md` 의 규약을 따라 `🤖 Cron activity` 섹션에 한 줄 append 하도록 프롬프트 작성. 그러면 자동으로 감사 로그에 표시됨.

**폴링 cadence 조정**: crontab `*/2` 부분을 원하는 분 단위로 변경. 1분 미만은 cron 한계로 불가 (systemd timer 또는 데몬 필요). flock 이 race 를 막아주기 때문에 더 짧게 줄여도 안전.

## ⚙️ GitHub Actions integration

Stage 1 에서 추가된 두 워크플로우:

| 파일 | Trigger | 역할 |
|---|---|---|
| `.github/workflows/ci.yml` | push/PR to `main`, `workflow_dispatch` | `osrf/ros:jazzy-desktop` 컨테이너에서 `colcon build`, xacro/SDF 검증, ShellCheck, (옵션) ruff. |
| `.github/workflows/claude-code-review.yml` | `pull_request` (opened/sync/reopened) | `.github/scripts/claude_review.py` 호출 → PR 에 단일 리뷰 코멘트 (`<!-- claude-review v1 -->` 헤더). |

## 🐙 GitHub-side Claude automation

Local hourly executor proactively picks work from Notion TODO DB.
GitHub-side workflows make the **opposite** surface available: open a GitHub
issue or drop a `@claude` comment and the same agent acts. Two surfaces, one
agent.

| 파일 | Trigger | 산출물 |
|---|---|---|
| `.github/workflows/claude-code-review.yml` | PR opened/synchronized | 단일 리뷰 코멘트 (`<!-- claude-review v1 -->`). |
| `.github/workflows/claude_dev.yml` | Issue opened/labeled with `claude-task` | `autoresearch/issue-<N>-<slug>` 브랜치 + PR + 이슈에 confirmation 코멘트. |
| `.github/workflows/claude-mention.yml` | Issue/PR comment 가 `@claude` 로 시작 | 이슈/PR 에 답글 코멘트 (`<!-- claude-mention v1 -->`) + 원본 코멘트에 `eyes` 리액션. |

### Gates

- **`claude_dev`**: `claude-task` 라벨 없으면 미실행. 라벨은 issue template
  (`Claude Task`) 가 자동으로 부여.
- **`claude-mention`**: 코멘트 본문이 `@claude` 로 시작해야 하고, 코멘트 작성자가
  Bot 이면 무시 (재귀 방지).
- **둘 다**: `ANTHROPIC_API_KEY` 가 repo Secrets 에 없으면 첫 step 의 guard 가
  clean-skip (workflow 자체는 success).

### 사용

- **이슈로 작업 지시**: GitHub → New issue → `Claude Task` 템플릿 → Goal /
  Constraints / Files / Acceptance criteria 채우고 submit.
  → 워크플로우가 `autoresearch/issue-<N>-<slug>` 브랜치에 diff 적용 → push →
  `gh pr create` → 이슈에 `Claude has processed this task. PR: #<n>` 코멘트.
- **PR 토론에서 추가 작업/질문**: PR 또는 이슈 코멘트에 `@claude please rebase`,
  `@claude 이 spec 의 trade-off 정리해줘` 등으로 작성. 답글 코멘트로 응답.
  Mention handler 는 코드 변경을 직접 commit 하지 않음 — 더 큰 작업이 필요하면
  새 `Claude Task` 이슈를 열도록 안내.

### 필요 secret

- **`ANTHROPIC_API_KEY`** (repo settings → Secrets and variables → Actions):
  Anthropic API 키. 미설정이면 모든 Claude 워크플로우 (review / dev / mention)
  가 clean-skip — repo CI 는 영향 없음.

### Diff 적용 전략 (claude_dev)

`claude_agent.py` 는 Claude 응답에서 ` ```diff ... ``` ` fence 만 추출 후
`git apply --whitespace=nowarn` 시도 → 실패 시 `--3way` → 그래도 실패 시
`--reject`. 단순 텍스트 add/modify (스크립트, docs, workflow YAML) 는 잘 적용됨.
바이너리 변경, 큰 리팩토링, 중첩 디렉토리 rename 은 fail 가능 — 그 경우
이슈에 자동 진단 코멘트 (`claude_response.md` 본문) 가 달림.

### Hard limits

`claude_agent.py` 는 issue/comment 본문에서 다음 패턴 발견 시 API 호출 없이
거절: force push to main/master, `delete branch`, `rm -rf`,
`git reset --hard`, `crontab -r`, `drop table/database`.

### 모델

`claude-opus-4-7` 우선, 실패 시 `claude-sonnet-4-6` fallback (review 와 동일 정책).

### 필요 secret

- **`ANTHROPIC_API_KEY`** (repo settings → Secrets and variables → Actions): Claude review workflow 가 호출하는 Anthropic API 키. 미설정이면 워크플로우는 **clean-skip** (guard 스텝이 0 으로 종료) — CI 자체는 영향 없음.

### per-PR 리뷰 비활성화

PR 제목에 `[skip-review]` 포함 시 Claude review job 자체가 skip (workflow `if:` 조건). 예: `[skip-review] WIP - rebase later`.

### 모델 선택

`claude_review.py` 는 우선 `claude-opus-4-7` 시도 → 실패 시 `claude-sonnet-4-6` fallback. Diff 는 200 KB 로 캡, PR description 을 user intent 로, `CLAUDE.md` 를 프로젝트 컨텍스트로 함께 전달. North Star alignment 와 simplicity (>50 net LOC w/o justification) 를 명시적으로 점검하도록 prompt 작성.

### 결과 뷰 — `RESULTS.md`

`scripts/aggregate_results.sh` 가 `results/*.tsv` 를 합쳐 repo root `RESULTS.md` 를 재생성. executor 가 push 직전에 호출하므로 모든 autoresearch 브랜치는 자체 RESULTS.md 스냅샷을 포함. 수동 실행도 가능:

```bash
./scripts/aggregate_results.sh && head -20 RESULTS.md
```

## 🤖 Auto-research loop (hourly)

`daily_executor.sh` 가 cron 으로 매시간 실행. 디자인 영감: [`karpathy/autoresearch`](https://github.com/karpathy/autoresearch) — 단일 `program.md` 가 에이전트의 프로젝트 헌법 역할, 사람은 스크립트가 아니라 그 프롬프트만 튜닝하면 됨.

흐름:
```
09:00  brief        ──► 오늘 후보 TODO 5건 surface (Notion + Telegram)
                       │
                       ▼
10:00  daily_executor.sh
                       ├── Notion TODO DB fetch (Status=Today/Backlog, Owner=claude)
                       ├── 1~2건 picked (≤30분 budget)
                       ├── git checkout -B autoresearch/<phase>-<slug>
                       ├── 코드 편집 + (touched src/) colcon build smoke
                       ├── results/<phase>-<slug>.tsv append (timestamp/sha/qual:metric/status/desc)
                       ├── 필요시 Telegram 으로 🧪 test request 발송 → TODO=Blocked NeedsUserTest
                       ├── git push --force-with-lease origin <branch>  (main push 절대 금지)
                       └── Telegram 으로 머지 요청 (사용자가 수동 머지)
                       ▼
22:00  wrap         ──► 7b. TODO review: 오늘 commit 의 TODO short-id 매칭으로
                       Done/Doing/carry/new 결산 + Telegram 1줄 (📋 TODO: N done, M carry, K new)
```

핵심 디자인 결정 (autoresearch 와의 의도적 차이):
- **다파일 프로젝트** — autoresearch 는 `nanochat` 단일 파일 가정, 여기는 planner+sensors+world+nav2 다파일. 따라서 편집 범위는 TODO 가 명시.
- **정량 metric 부재 (P5 까지)** — `qual:build-pass` / `qual:topics-flow` 같은 string metric. P5 에 eval harness 가 들어오면 `auto_research.md` 의 `<!-- NEVER_STOP_PLACEHOLDER -->` 를 풀어서 perpetual loop 로 업그레이드.
- **하루 1회 cron 실행** — autoresearch 의 NEVER STOP 무한 루프가 아니라 일일 budget 30분.

**Hard limits** (executor 자체 거절):
- `git push` to `main` 금지 (브랜치 푸시만, 머지는 사용자)
- `crontab`/`systemctl`/`apt`/시스템 venv 외 `pip install --user` 금지
- 리포 밖 `rm -rf`, dotfile 삭제 금지
- 2분 초과 sim 실행 금지 (test request 로 사용자에게 핸드오프)

**Soft limits**:
- 한 thrust = 한 브랜치 (`autoresearch/<phase>-<slug>`)
- TSV append-only, 한 브랜치당 한 파일
- Simplicity criterion: +50 LOC 이상이면 commit description 에 측정 가능한 이득 1개 명시. 순수 삭제는 환영.
- Daily wall-clock ≤ 30분.

### branch + TODO + TSV — 한 사이클 구체 예시

세 자산 (git branch, Notion TODO row, `results/*.tsv`) 의 매칭 규약:

| 자산 | 명명 패턴 | 예시 |
|---|---|---|
| Git branch | `autoresearch/<phase>-<slug>` | `autoresearch/p1-bev-semseg-baseline` |
| TSV file | `results/<phase>-<slug>.tsv` | `results/p1-bev-semseg-baseline.tsv` |
| Notion TODO `Branch` 필드 | branch 와 동일 문자열 | `autoresearch/p1-bev-semseg-baseline` |
| TODO short-id | Notion page id 첫 8자 | `357c5d39` |

`<phase>` 는 TODO 의 Phase select 값 (소문자), `<slug>` 는 Title 을 lowercase-kebab 으로 변환 후 ≤ 40 자 truncate. 한 thrust = 한 branch = 한 TSV — 이 셋은 1:1:1.

**TSV 포맷** (`results/<phase>-<slug>.tsv`, tab-separated, 첫 append 시 헤더 추가):

```
timestamp	commit	metric	status	description
2026-05-08T10:14:22+09:00	a1b2c3d	qual:script-syntax-ok	in_progress	Wired BEV node skeleton; no projection math yet
2026-05-08T10:23:11+09:00	d4e5f6g	qual:build-pass	keep	Added URDF→intrinsics extractor; colcon clean
```

`status` ∈ `{keep, discard, crash, in_progress}` — 과거 row 는 절대 수정 X, append 만. 정량 metric 이 없는 P5 이전엔 `qual:*` 문자열을 쓰고, P5 의 eval harness 가 들어오면 float 로 교체.

**TODO state 전이** (executor 가 한 thrust 를 끝낼 때 결정):

| 결과 | Status | NeedsUserTest | Branch | 비고 |
|---|---|---|---|---|
| 머지 가능 (사용자가 PR/머지만 하면 됨) | `Done` | 그대로 | 채움 | wrap 이 commit-id 매칭으로 자동 인식 |
| 다음 날까지 이어짐 (budget 초과 등) | `Doing` | 그대로 | 채움 | TSV 마지막 row `status=in_progress` |
| sim/visual 검증 필요 | `Blocked` | `__YES__` | 채움 | Telegram 으로 🧪 test request 동시 발송 |
| executor 가 실패/crash | `Today` | 그대로 | 빈값 또는 그대로 | 다음 날 retry — `Doing` 으로 두지 않음 |

각 picked TODO 의 page body 에는 한 줄 progress note 를 timestamp + commit short-sha 와 함께 append (Notion 의 `Updated` 는 last_edited_time 으로 자동 갱신).

**머지는 사용자 손**: executor 는 `git push --force-with-lease` 로 `autoresearch/*` 브랜치만 push 하고, Telegram 으로 `🔀 [auto] 머지 요청: <branch>` 를 보냄. `main` 머지는 사용자가 GitHub PR 또는 다음 wrap 이 처리하는 `merge <branch>` 답글로 트리거.

**TODO DB**: 사용자가 Notion 에 별도 데이터베이스로 만들고 ID 를 한 번 sed-replace:
```bash
# 사용자가 DB 생성 후 (한 번):
sed -i 's/<TODO_DATA_SOURCE_ID>/<실제-uuid>/g' \
  scripts/prompts/auto_research.md \
  scripts/prompts/brief.md \
  scripts/prompts/wrap.md
```
seed 데이터는 `scripts/seed_todos.tsv` (P0~P6 전 phase 약 54건 backlog).

**TODO DB 스키마**: `Title` / `Priority`(P0~P3) / `Phase`(P0~P6) / `Status`(Backlog/Today/Doing/Blocked/Done) / `NeedsUserTest`(checkbox) / `Owner`(claude/user) / `Branch`(rich_text).

**Cron 등록** (한 줄 추가):
```cron
0 10 * * *   /home/geonhee/Representation-Aware-MPPI/scripts/daily_executor.sh
```

**로그**: `~/.local/share/representation-aware-mppi/logs/executor-YYYY-MM-DD.log`.
**Lock**: `~/.local/state/representation-aware-mppi/executor.lock` (flock — 이전 실행이 30분 budget 초과해도 다음 tick 충돌 없음).

**실패 모드**: executor 가 죽으면 `❌ [auto] 실패` Telegram 발송 + TODO 는 다시 `Today` 로 (Doing 으로 두지 않음 — 다음 날 retry).

## 의도적 비-기능

- 코드 자동 commit/push 없음 — **단, autoresearch 브랜치는 예외** (위 섹션 참조). `main` 푸시는 여전히 사용자 손으로.
- 실패 시 자동 retry 없음. cron 이 다음 슬롯에 다시 시도하면 그만 (idempotent 설계).
- 캘린더 통합, 이메일 알림 없음 — 추가하려면 별도 prompt + cron 한 줄.
