# Decision Log — ADR-lite

> 매 cycle 끝에 **Decision** (했음) + **Deferred** (안 했지만 했어야) 가 한 줄씩 append 됨.
> 사람이 manual 로 큰 결정 (architecture / scope / priority pivot) 도 여기 누적.
> 형식은 ADR (Architecture Decision Record) 의 경량 버전 — 1 cycle = 1 entry.

**컨벤션**:
- 최신이 위 (prepend)
- 한 entry ≤ 12 줄
- Status: `accepted` / `superseded by D-XXX` / `reverted`
- 참조: 관련 PR, journal, STATE
- Open question 은 별도 [`deliberations.md`](deliberations.md)

---

## D-008 — 2026-05-28 — Decision log + Deliberation log 도입

- **Context**: 자율 R&D 가 9 cycle 진행됐는데 "왜 이 선택" 의 timeline 이 git log + journal 에 분산. 결정 회고가 어려움.
- **Decision**: `docs/decisions.md` + `docs/deliberations.md` 신설. auto_research.md Phase 4 REPORT 에 "Decision append" 단계 추가.
- **Alternatives**: (a) journal 안에 섹션 추가 — 산만, (b) GitHub Discussions — 외부 의존, (c) Notion sub-page — 검색성 떨어짐.
- **Status**: accepted
- **Refs**: 이 commit, docs/agents.md A2 Builder 의 REPORT phase 갱신 (follow-up).

## D-007 — 2026-05-27 — 시나리오 10종 + Controller 8종 격자 가설 도입

- **Context**: 동적 장애물 정책 비교 필요. 사용자 명시 요청.
- **Decision**: ego-frame 10 시나리오 (S01-S10) × controller 8종 (ObstaclesCritic ~ DR-MPC) 매트릭스 가설 → Phase D3 ablation 으로 ground truth.
- **Alternatives**: 단일 시나리오 + controller per phase — 비교 불가능.
- **Status**: accepted
- **Refs**: `docs/scenarios_and_controllers.md`, issue #38/#39/#40, commit 70e8b39

## D-006 — 2026-05-26 — Dynamic obstacle + Uncertainty 단일 track 으로 묶음

- **Context**: feed 에 14+ 관련 paper, 사용자도 두 axis 명시 관심. 분리하면 시야 분산.
- **Decision**: 두 axis 가 risk-aware MPPI cost 단일 출구를 공유함을 명시. `docs/dynamic_obstacles_uncertainty_track.md` 통합 track 으로.
- **Alternatives**: 2개 별 doc — 중복 + cross-ref 부담.
- **Status**: accepted
- **Refs**: `docs/dynamic_obstacles_uncertainty_track.md`, commit 4f1a8d8

## D-005 — 2026-05-25 — safe_control 외부 ref 통합 (use-in-place, vendoring X)

- **Context**: 사용자가 4 reference (cfm_mppi + DR-MPC + SCOPE + safe_control) 통합 요청. License 미명시 다수.
- **Decision**: `scripts/fetch_refs.sh` 로 외부 clone, `eval/<harness>/` 에 wrapper 만. vendoring 안 함.
- **Alternatives**: (a) fork — license 불확실, (b) re-implement from paper — 시간 ↑, (c) submodule — git complexity.
- **Status**: accepted (safe_control 의 DPCBF/evade/tracking 3건 즉시 실측 검증)
- **Refs**: `scripts/fetch_refs.sh`, `eval/safe_control_harness/`, commit cb16e3a + 47a8a9e

## D-004 — 2026-05-25 — docs 4종 "헌법" 신설 (prd/agents/skills/todo)

- **Context**: docs 분산. 자율 agent 가 어디 인용해야 할지 불명.
- **Decision**: PRD (북극성+요구) / agents (역할) / skills (도구) / todo (4 surface) 4종 = 프로젝트 헌법.
- **Alternatives**: CLAUDE.md 안에 다 넣기 — 너무 길어짐.
- **Status**: accepted
- **Refs**: `docs/{prd,agents,skills,todo}.md`, commit 3d418dc

## D-003 — 2026-05-24 — Multi-agent + auto-merge 정책 도입 (PR 정체 14일 후)

- **Context**: 5/10~24 PR 큐 cap=3 도달 → cron 216회 silent skip → 진척 0. 사용자 부재 시 시스템 self-block.
- **Decision**: Researcher (4h) + Curator (daily, safe-surface auto-merge) 추가. PR cap 3→6, daily cap 6→10.
- **Alternatives**: (a) 사용자 머지 알림만 강화 — 부재 시 무력, (b) 모든 PR auto-merge — 위험.
- **Status**: accepted (다음 날 6 PR/24h 처리 입증)
- **Refs**: commit 827bb57, `scripts/{researcher,curator}.sh`, `scripts/prompts/{researcher,curator}.md`

## D-002 — 2026-05-05 — 5-phase R&D 루프 (REVIEW → PLAN → EXECUTE → REPORT → PLAN_NEXT)

- **Context**: 단순 pick-and-execute 로 5일간 infra PR 만 쌓이고 north-star 진척 0.
- **Decision**: karpathy/autoresearch 패턴 차용, 35 min budget 5 phase.
- **Alternatives**: (a) 단순 cron with budget — reflection 없음, (b) 사람 매일 review — 자율성 X.
- **Status**: accepted (cycle 1 직후 path-tracking metric v0 produce)
- **Refs**: commit ef349b1, `scripts/prompts/auto_research.md` 449 lines

## D-001 — 2026-05-01 — Notion DB + Telegram bot + cron 4종 자동화 시스템 셋업

- **Context**: 자기계발 프로젝트, 6개월 일관 페이스 필요. 사용자 부재 시간 활용.
- **Decision**: Notion TODO DB + Telegram bot + cron (brief/wrap/weekly/poll) 셋업.
- **Alternatives**: GitHub Projects (Notion 보다 빈약), email (실시간 X).
- **Status**: accepted, 28일째 가동 중
- **Refs**: 초기 commit 들, `docs/automation.md`

---

## Append 정책 (cron-agent)

매 cycle 의 REPORT phase 에서 (auto_research.md Phase 4 의 추가 step):
- 이번 cycle 에 새로운 architecture-level / scope-level / priority-pivot 결정 있으면 → 이 파일 prepend
- 단순 코드 변경/문서 수정 → journal 만, 이 파일 X
- Open question 만 발견 시 → 이 파일 X, [`deliberations.md`](deliberations.md) prepend

D-NNN 번호는 strictly 증가, 절대 재사용 X. supersede 시 새 D 번호 + 이전 entry Status 갱신.

_Last manual update: 2026-05-28 KST_
