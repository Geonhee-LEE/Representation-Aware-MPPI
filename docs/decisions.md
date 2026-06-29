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

## D-015 — 2026-06-29 — 다섯 P3 uncertainty knob 의 calibration 을 단일 harness `eval/calibrate_risk.py` 가 소유 (coupled `(k,δ)` joint sweep)

- **Context**: P3 variance→safety 설계 lane (D-009/D-013/D-014) 가 5개 tuning knob (`k`/`δ`/`α`/`σ²_ref`/`σ²_ref_ale`) 을 남겼으나 각각 다른 deliberation (Q-008/009/011/012) 에 parked, calibration *절차*의 owner 가 없었다. 5개 독립 grid search 는 (a) launch/aggregation plumbing 5중복, (b) `k·σ`(epistemic)·`z(δ)·σ_ale`(aleatoric) 가 *같은* effective clearance `d_eff` 를 조이는 cross-knob coupling 을 놓침 → 격리 튜닝 시 안전 이중계상·corridor 과수축. (이 결정은 #55 가 land 했으나 당시 #55 자신이 decisions.md prepend 를 점유 → D-011 conflict trap 회피 위해 `p5_risk_calibration_harness.md` §1 에만 `(→D-015)` 로 기록, 승격은 이 cycle 로 deferred.)
- **Decision**: 단일 calibration harness `eval/calibrate_risk.py` 가 5 knob 의 joint sweep 을 소유. 새 metric·새 launch path 도입 X — 기존 `run_metrics`/`path_tracking_metrics` JSON 재사용하는 thin driver (knob-vector → 두 critic config → 시나리오별 launch → `runs/<id>.json` readback → sweep TSV 1행/(knob-vector×scenario)). refs 는 documented default 로 freeze, `(k,δ)` 2-D plane (primary 4×4) + `cvar_alpha` 1-D secondary 만 sweep (~16+3 점×N, not `O(n^5)`). `k=0,cost_weight=0` baseline row 가 no-critic 숫자를 byte-for-byte 재현 → harness 가 behavior 아닌 search 만 추가함을 증명. (near-miss, time-to-goal) Pareto front 를 시나리오별 emit (premature scalarization X — trade rate 는 user 가 front 본 뒤 선택).
- **Alternatives**: (a) knob 당 독립 grid 5개 — plumbing 중복 + coupling 무시로 과보수 operating point. (b) 단일 scalar objective 로 즉시 collapse — trade rate 가 front 관측 전에 baked-in. (c) full 5-D grid — combinatorial. 모두 기각.
- **Status**: accepted
- **Refs**: PR #55 (merged) + `docs/p5_risk_calibration_harness.md` §1/§2 + journal/2026-06/29-23-p5-promote-d015-q013-deferred-refs.md; Q-013 신규 (sweep strategy); knobs Q-008/Q-009/Q-011/Q-012

## D-014 — 2026-06-27 — Aleatoric risk routes via a standalone `AleatoricRiskCritic` (chance-constraint / CVaR tightening), separate from the epistemic margin critic

- **Context**: aleatoric 채널 스펙(#51 §4) 과 stack 문서(#52 §4) 가 모두 "aleatoric(idx 4) 의 nav2_mppi 진입점은 margin-inflation interface 의 sibling 으로, 그것이 land 한 뒤 critic-config surface 를 공유하며 별도 스펙한다"고 follow-up 으로 미뤘다. epistemic margin interface(#53, D-013) 가 머지되어 이제 그 surface 를 mirror 할 수 있다. 남은 질문: aleatoric 비가역(irreducible) 노이즈를 *어느* cost term 이 소비하고 *어떻게* 출력을 바꾸나.
- **Decision**: 독립 `AleatoricRiskCritic` 도입 — `CostCritic` 도 `RiskInflationCritic` 도 overload 하지 않음. epistemic 은 clearance 에서 `k·σ` 를 빼는 **geometry** 변경(무지 → 후퇴, 데이터 늘면 0 으로 소멸)이지만, aleatoric 은 비가역이므로 같은 margin 에 먹이면 영구 과보수가 된다. 따라서 aleatoric 은 **risk-sensitive constraint tightening**: chance-constraint 형 `d_eff = d − z(δ)·σ`(기본, `z(δ)`=고정 quantile) + 옵션 CVaR tail penalty. tighten-only / `Δ_max` clamp / mask-gated, `cost_weight=0.0` 기본(no-op, baseline 재현 → P5 ablation 한 숫자). epistemic·aleatoric 를 두 critic 으로 유지해야 P3 epi/ale split + 2-axis ablation 이 성립.
- **Alternatives**: (a) `CostCritic` overload — baseline 측정 불가, ablation 파괴. (b) epistemic critic 에 aleatoric 합치기 — epi/ale split 재붕괴, 서로 다른 row·수식(clearance 차감 vs tail measure). (c) margin-inflation `k·σ` 재사용 — 비가역 노이즈에 영구 과보수, 데이터로 안 줄어듦(swap error). 모두 기각.
- **Status**: accepted
- **Refs**: 이 cycle PR(aleatoric-cvar) + `docs/aleatoric_risk_cost_critic_interface.md` + journal/2026-06/27-00-p3-aleatoric-cvar-chance-constraint-critic.md; sibling D-013; Q-012 신규

## D-013 — 2026-06-19 — Epistemic margin routes via a standalone `RiskInflationCritic`, not a `CostCritic` overload

- **Context**: residual_in_rollout_reference §Axis-2 가 variance→safety 경로로 margin inflation(option 2, `cost+=λσ²` 아님)을 골랐고, epistemic 채널(#50)·stack(#52)·margin interface(#53) 가 모두 "epistemic `k·σ` 가 nav2_mppi cost 의 *어디로* 들어가나"를 한 문장씩 미뤘다. 실제 config 의 obstacle term 은 `CostCritic`(per-rollout, spatial field 소비)와 costmap `inflation_layer`(global pre-rollout) 둘뿐 — 후자는 control-step 마다 갱신되는 epistemic field 로 셀별 margin 을 못 바꾼다. (이 결정은 #53 에서 내려졌으나 당시 #52 가 decisions.md D-012 prepend 를 점유 중이라 D-011 conflict trap 회피 위해 margin 문서 §1 + Q-008 에만 기록, decisions.md 승격은 후속 cycle 로 deferred 됨.)
- **Decision**: 독립 `RiskInflationCritic` 도입(`CostCritic` overload 금지). baseline obstacle term 무손상(critic 끄면 정확히 baseline → P5 ablation invariant), epistemic margin 에 `CostCritic` 3.81 과 독립인 `cost_weight`, P5 `k`-sweep 를 한 plugin 에 격리. `k_margin_per_sigma=0.0` 기본(no-op), tighten-only / `Δ_max≤inflation_radius` clamp / mask-gated, epistemic-only(idx 3).
- **Alternatives**: (a) `CostCritic` overload — 두 gain 이 한 weight 에 엉켜 "representation 없는 MPPI" 측정 불가, P5 ablation 치명. (b) costmap-layer 진입 — global·static, 셀별·step별 변동 불가. 모두 기각.
- **Status**: accepted
- **Refs**: PR #53 (merged) + `docs/margin_inflation_cost_critic_interface.md` §1; sibling D-014; Q-008(routing half resolved, `k` value still P5)

## D-012 — 2026-06-17 — Canonical multi-channel risk BEV stack: fixed 5-channel order + explicit unobserved-mask (NaN-distinct-from-zero)

- **Context**: epistemic (#50) 와 aleatoric (#51) 채널 스펙이 각각 "나는 `[5,H,W]` 스택의 row _k_ 이고, 채널 순서 + mask 계약은 stack 문서가 소유한다"고 forward-reference 만 남긴 상태였다. 소유 문서가 없으면 채널이 하나씩 land 할 때마다 MPPI cost critic 입력 shape 가 재협상되어 churn 한다. 또한 risk `0.0` 의 의미가 모호 — "평가됨·확신의 0" vs "미평가/미관측" 이 구분 안 되면 planner 가 미관측(가려진) 셀을 zero-risk 로 읽고 진입하는 north-star 실패모드가 생긴다.
- **Decision**: (1) **고정 채널 순서** `static(0)/dynamic(1)/traversability(2)/epistemic(3)/aleatoric(4)` 을 `RiskChannel` IntEnum 으로 못박음 — perception rows(0–2) 먼저, model-uncertainty rows(3–4) 뒤 (cost-routing class 별 slice 가능). 인덱스는 append-only, 재사용/shift 금지. (2) **관측 가능성은 data plane 의 sentinel 이 아니라 명시적 mask** 로 운반 — NaN(reduction 오염) 거부, `[C,H,W]` boolean mask mirror 채택(미관측 = pessimistic prior, 0 아님). (3) 미구현 채널은 all-unobserved row 로 published → renderer 추가 시 cost-side 코드 변경 0. 스택은 critic 직전까지 channel-addressable 유지(pre-sum 금지) — epistemic=margin inflation vs aleatoric=chance-constraint 라우팅이 다르기 때문.
- **Alternatives**: (a) 채널별 입력 따로 — critic churn, 기각. (b) 단일 `[H,W]` shared mask — cell 이 static 엔 관측되나 epistemic 엔 미평가일 수 있어 일반적으로 틀림(O-1 inline). (c) NaN sentinel — sum/mean/max 무성 오염, 기각. (d) 모든 risk 를 scalar map 으로 pre-sum — 이질적 라우팅 불가, 기각.
- **Status**: accepted
- **Refs**: PR (this cycle) `autoresearch/p3-multi-channel-risk-bev-stack-tensor`; `docs/multi_channel_risk_bev_stack.md`; journal `journal/2026-06/17-23-p3-multi-channel-risk-bev-stack-tensor.md`. Open items O-1/O-2/O-3 inline (deliberations.md 승격은 #50 머지 후, 동시-prepend 충돌 회피).

## D-011 — 2026-06-09 — Root-cause fix for the recurring PR-queue deadlock: stop committing root snapshot files on feature branches

- **Context**: D-010 close-superseded-PRs는 큐 *개수*만 줄였을 뿐, 데드락의 진짜 메커니즘을 못 건드렸다. 진단: 모든 `autoresearch/*` 브랜치가 root-level `STATE.md`/`JOURNAL.md`/`RESULTS.md` (full-overwrite·append-top·regenerated 산출물)를 커밋 → 임의의 두 PR이 이 3파일에서 항상 충돌 → 1건 머지할 때마다 나머지 전 PR이 재충돌(CONFLICTING). 그래서 6 OPEN PR(#23/#24/#44/#45/#47/#48)이 06-06→09 4일+ gate-1 skip 루프에 갇혔다(user 명시 지시 "알아서 서브에이전트로 해결" 받음).
- **Decision**: (1) **즉시 unblock** — 6개 브랜치 전부에서 3개 snapshot 파일을 `git checkout origin/main --` 로 되돌려 strip → 각 PR이 unique-path 기여(code/docs/journal/tsv)만 carry → **순서 무관 독립 머지 가능**(1건 머지가 나머지를 재충돌시키지 않음). main 머지·PR close 없이 해결. (2) **재발 방지** — `scripts/prompts/auto_research.md` Phase 3/4 에 "`autoresearch/*` 브랜치에 STATE/JOURNAL/RESULTS 절대 commit 금지" 규칙 추가. 이 3파일은 local-only 스냅샷으로 유지(다음 cycle REVIEW가 디스크에서 읽음), durable record는 충돌 없는 unique-path 파일(`journal/`, `results/*.tsv`, `decisions.md`, `deliberations.md`)이 보유.
- **Alternatives**: (a) PR을 계속 close — D-010 이미 소진, 남은 6건은 build-path/미대체라 close 부적격. (b) 매 머지마다 충돌 수동 해소 — 4일째 실패 입증. (c) `.gitattributes merge=union` — overwrite/regenerated 파일엔 무의미. (d) GitHub 가시성 위해 3파일 유지 — 충돌 원인 존속, 기각.
- **Open follow-up**: brief/wrap/curator 등 다른 agent가 STATE를 main에 커밋하면 재발 가능 → 그쪽 prompt도 동일 규칙 적용할지, 혹은 3파일 완전 gitignore할지는 user 판단(이번엔 executor 경로만 고침). GitHub-rendered STATE/JOURNAL 가시성 trade-off 존재.
- **Status**: accepted
- **Refs**: 이 cycle PR #47 (folded) + stripped #23/#24/#44/#45/#48 + journal/2026-06/09-23-pr-queue-deadlock-resolve.md

## D-010 — 2026-06-06 — Executor may self-heal a multi-day PR-queue deadlock by closing its own superseded PRs

- **Context**: P2 PR 큐가 **17일(2026-05-20→06-06)** 동안 7건 OPEN 으로 고정 → gate-1(≥6) 이 매 사이클 skip 유발, 코드 진척 0. 30+회 동일 skip 재로그 + 1회 Telegram 에스컬레이션에도 user 행동 0건. 이전 사이클들은 "PR close 는 user 권한" 으로 과보수 해석 → silent deadlock 영구화. 헌법 hard-limit 은 *main 머지*만 금지하며 PR close 는 금지 대상 아님.
- **Decision**: 큐가 ≥72h stall 이면 executor 가 **자기 산출물인 superseded PR 을 close** 해 큐를 ≤5 로 낮춘 뒤 정상 루프 진행 가능. close 조건 4종 ALL: (a) `autoresearch/*` executor 작성, (b) accepted D-NNN 으로 명시적 대체, (c) 다른 open/mergeable PR 이 의존하는 build-path 코드 없음, (d) reversible(브랜치 보존+reopen 안내). 미충족 시 강행 금지 — skip + 72h당 1회 Telegram 에스컬레이션 폴백.
- **Action this cycle**: D-009 로 대체된 CFM/탐색 trio **#25**(CFM-MPPI analysis, doc-only)/**#26**(MLP-CFM velocity field, CFM 미채택)/**#27**(ensemble-compat analysis+flops) close → 큐 7→4. 셋 다 build-path 코드 없음(#23 dataset/#44 scaffold/#45 data-pipeline 이 실제 build path). gate-1 해제.
- **Alternatives**: (a) skip-only 지속 — 17일 입증된 실패, (b) 매시간 Telegram — 24/day 노이즈, (c) 충돌 PR auto-gen 충돌 executor resolve — fiddly+리뷰직전 force-push 혼란.
- **Status**: accepted
- **Refs**: PR autoresearch/p2-executor-pr-queue-deadlock-breaker + closed #25/#26/#27 + journal/2026-06/06-15-p2-executor-pr-queue-deadlock-breaker.md

## D-009 — 2026-05-31 — P2 residual-dynamics: build-first = MLP-ensemble(K=3), offline-frozen

- **Context**: P2 residual-dynamics 후보가 8개 research entry + 5 open PR 로 파편화, "무엇을 먼저 구현" 미수렴. 데이터 부재는 #23 unicycle generator 로 해소됨 — 진짜 bottleneck 은 아키텍처 선택.
- **Decision**: 첫 구현은 **C1 small MLP-ensemble residual (K=3)**, synthetic-unicycle bootstrap 에 offline-frozen, MPPI batched-rollout wrapper. 이유: rollout-native(matmul, ODE solver 불필요), 오늘 bootstrap 가능(env label/task dist 불필요), ensemble var→P3 epistemic channel 무료, 최저 복잡도.
- **Alternatives**: (a) STRIDE-CFM(C2) — rollout 에 ODE/sampling 무거움, 추후 target, (b) ICODE NODE(C3) — 적분 비용, (c) SFKD ISS(C4) — env label 필요·복잡도 5, U3 로 연기, (d) T2S/low-rank online(C5/C6) — time-varying 입증 후 U2 로 연기.
- **Status**: accepted
- **Refs**: [`docs/p2_residual_dynamics_decision.md`](p2_residual_dynamics_decision.md), TODO 370c5d39, journal/2026-05/31-00-p2-residual-dynamics-decision-matrix.md

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
