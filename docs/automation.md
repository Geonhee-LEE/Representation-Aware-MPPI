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
├── daily_wrap.sh           # cron 22:00 entry point
├── weekly_rollup.sh        # cron 일 22:30 entry point
├── telegram_poll.sh        # cron 매 2분 entry point (flock 단일 인스턴스)
├── urgent_agent.sh         # telegram_poll.sh가 긴급 키워드 감지 시 tmux로 spawn
└── prompts/
    ├── brief.md                # 09:00에 claude -p가 읽는 지시문
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
| `~/.local/share/representation-aware-mppi/logs/wrap-YYYY-MM-DD.log` | wrap 로그 |
| `~/.local/share/representation-aware-mppi/logs/weekly-YYYY-Www.log` | 주간 롤업 로그 |
| `~/.local/share/representation-aware-mppi/logs/telegram-poll-YYYY-MM-DD.log` | 폴링 로그 (메시지 있을 때만 채워짐) |
| `~/.local/share/representation-aware-mppi/logs/urgent-<session>.log` | urgent agent 실행 로그 (세션 단위) |
| `~/.local/state/representation-aware-mppi/telegram_last_update_id` | 마지막 처리한 Telegram update_id (폴링 dedup용) |
| `~/.local/state/representation-aware-mppi/telegram_poll.lock` | 폴링 single-instance flock 파일 |

## 동작 변경 / 디버깅

**프롬프트 튜닝**: `scripts/prompts/<name>.md` 만 수정 → 다음 cron 실행에 반영. 셸 스크립트 손댈 일 거의 없음.

**수동 실행 (테스트)**:
```bash
# 한 번 즉시 실행 (cron 기다리지 않고)
./scripts/daily_brief.sh
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

## 의도적 비-기능

- 코드 자동 commit/push 없음. 모든 작업 실행은 사용자의 일반 Claude Code 세션에서 진행.
- 실패 시 자동 retry 없음. cron 이 다음 슬롯에 다시 시도하면 그만 (idempotent 설계).
- 캘린더 통합, 이메일 알림 없음 — 추가하려면 별도 prompt + cron 한 줄.
