# Deliberation Log — 풀리지 않은 고민

> 의사결정 이전 단계. **답이 아직 없는 질문** + **trade-off 의 양쪽 모두 무게 있는 사안**.
> 답을 내면 `decisions.md` 로 승격 (D-NNN entry 추가, 여기서 strikethrough).
> 사람도 cron-agent 도 추가 가능.

**컨벤션**:
- 최신이 위 (prepend), 한 entry ≤ 15 줄
- Status: `open` / `partially-answered` / `resolved → D-NNN`
- Tag: `[scope]` `[arch]` `[priority]` `[license]` `[meta]` `[uncertainty]`

---

## Q-009 — 2026-06-13 — `[uncertainty]` epistemic channel 정규화 기준 `σ²_ref`: 어떻게 set 하나

- **Question**: ensemble `σ²` 를 BEV 채널 `[0,1]` 로 매핑할 때 fixed reference `σ²_ref` 가 필요한데 (per-frame min-max 는 cross-frame 비교성 파괴 → P5 calibration metric 무력화), 그 값을 어디서 얻나. Q-008 의 `k` margin gain 과 형제 knob.
- **Trade-off**:
  - **held-out OOD percentile (예: 95th)**: 의미 있는 기준, 그러나 OOD set 이 real rosbag/terrain-shift 데이터 생기기 전엔 없음
  - **hand-pick 임시값**: 즉시 진행 가능, 그러나 의미 없는 스케일 → 채널이 임의적
- **Lean**: 문서화된 placeholder 로 두되 hard-code 금지 (config), P5 measured OOD spread 로 calibrate. Q-008 (`k`) 와 함께 sweep.
- **다음 action**: P5 uncertainty-calibration harness (epi↑ on OOD) 확보 시 `σ²_ref` + `k` 동시 set → resolve 시 D-MMM. ref: [`epistemic_channel_bev_rendering.md`](epistemic_channel_bev_rendering.md) §2.3/§5.

## Q-008 — 2026-06-12 — `[uncertainty]` epistemic-margin gain `k`: 어떻게 set 하나 (variance→safety routing)

- **Question**: ensemble `σ` 를 안전 margin 으로 라우팅할 때 (additive `λσ²` 아닌 margin-inflation) margin = `k·σ` 의 gain `k` (m / unit σ) 를 어떻게 정하나. Stochastic-MPPI 는 chance-constraint level `ε` 에서 유도하나 우리는 `ε` target 도 정량 harness 도 P5 전엔 없음.
- **Trade-off**:
  - **measured near-miss 로 sweep (P5)**: 의미 있는 값, 그러나 eval harness 전엔 측정 불가
  - **hand-pick 임시값**: 즉시 진행, 그러나 임의 스케일 → margin 이 의미 없는 보수성
- **Lean**: config 로 노출 (`k_margin_per_sigma`), **default `0.0` ⇒ exact-baseline no-op** 로 plumbing 먼저 landing, P5 near-miss metric 으로 sweep. `σ²_ref`(Q-009) 와 형제 knob — 함께 calibrate.
- **다음 action**: (1) routing **resolved** this cycle — `k·σ` 가 standalone `RiskInflationCritic` (overload `CostCritic` 아님) 으로 진입, mask-gated/tighten-only/bounded by `inflation_radius`. → D-013 으로 승격 예정 (decisions.md 가 #52 prepend 와 충돌 안 할 때). (2) `k` **값** 은 P5 harness 확보 시 set → resolve 시 D-MMM. ref: [`margin_inflation_cost_critic_interface.md`](margin_inflation_cost_critic_interface.md), [`residual_in_rollout_reference.md`](residual_in_rollout_reference.md) §Axis-2.
- **Status**: partially-answered (routing → D-013 pending; `k` value open for P5)

## Q-007 — 2026-05-31 — `[arch]` residual 의 nominal model: analytic unicycle vs 학습 LNN

- **Question**: C1 ensemble residual 의 nominal 항을 analytic unicycle (현재 bootstrap) 로 둘지, STRIDE-style 학습 LNN 으로 둘지.
- **Trade-off**:
  - **analytic unicycle**: 즉시 구현, residual 이 순수 mismatch 만 학습 → 해석 쉬움. 위험: real diff-drive 에서 nominal 자체가 부정확하면 residual 부담 ↑
  - **학습 LNN**: nominal 이 데이터로 보정 → residual 가벼움. 위험: 학습 nominal+학습 residual 이중 학습, unicycle bootstrap 만으론 식별 어려움
- **Lean**: analytic-nominal 우선 (D-009). real diff-drive/Gazebo 데이터 생기면 재평가.
- **다음 action**: U1 distribution-shift probe 결과 + 실데이터 확보 후 결정. resolve 시 D-MMM.

## Q-006 — 2026-05-28 — `[arch]` Decision log 의 cron-agent append 권한 범위

- **Question**: cron Builder/Curator 가 `decisions.md` 에 직접 append 할 수 있는가? doc 인데 doc 자체에 대한 결정이 있을 수 있어서 self-reference.
- **Trade-off**:
  - **자율 append**: 매 cycle 의 큰 결정 즉시 기록, 정체 없음. 위험: agent 가 trivial 한 변경도 D-NNN 으로 부풀림 → 가독성 ↓
  - **사람 only**: 신호 대 잡음 ↑, 그러나 사용자 부재 시 timeline 결손
- **Lean**: agent append 허용하되 prompt 에 "architecture/scope/priority pivot 만" 명시. trivial → journal 만.
- **다음 action**: Phase 4 REPORT step 갱신 (issue 신규 #41) 시 prompt 검증.

## Q-005 — 2026-05-28 — `[priority]` reference paper 8건 모두 분석할 시간 있나

- **Question**: feed 에 14+ paper, issue #17-21 + #28-31 + #33-37 + #38-40 = 24개 open. Builder cycle 당 1 issue. 24일 backlog → DPCBF/DRA-MPPI/DualGuard 실측 ablation (#34) 진입 시간 ↓.
- **Trade-off**:
  - **순차 처리**: 정착 보장, 늦음
  - **병렬 우선순위**: DPCBF Stage A (#33) + 5채널 spec (#35) + scenario yaml (#38) 세 thread 동시 → 다른 issues 는 Backlog
- **Lean**: 병렬 3 thread, 나머지 Backlog 유지. Researcher 가 새 paper 추가 시 자동 Priority=P3 (낮춤).
- **다음 action**: 다음 Builder cycle 의 PLAN 단계가 이 lean 반영하는지 모니터.

## Q-004 — 2026-05-27 — `[uncertainty]` 5채널 가중치 — fixed / env-conditioned / learned?

- **Question**: P3 의 5 risk channel (static/dynamic/traversability/epistemic/aleatoric) 각 `w_c` 를 어떻게 결정?
  - (a) hand-tuned constant
  - (b) environment-class lookup (`docs/environment_taxonomy.md` A~E 별)
  - (c) 학습 (context → weights regression)
- **Trade-off**: (a) 단순/투명, (b) 적당히 일반화, (c) 일반화 ↑ but black-box + 학습 데이터 필요
- **Lean**: P3 v0 = (a), P5 calibration 단계에서 (b), P6 outputs 단계에서 (c) 비교.
- **참조**: `docs/dynamic_obstacles_uncertainty_track.md` § 7 open question 첫 항목
- **다음 action**: issue #35 (5채널 spec) 작성 시 § "weighting strategy" 섹션에 위 3 옵션 명시.

## Q-003 — 2026-05-26 — `[arch]` HuNav (반응형 보행자) 도입 시점

- **Question**: 현재 scripted actor 가 한계 (S05 overtaken, S06 cut-in 의 "반응" 검증 X). HuNav/PedSim 도입 = P4 본격? 아니면 P3 와 병행?
- **Trade-off**:
  - **P4 본격**: 5채널 spec (P3) 안정화 후 도입 → 안전
  - **P3 와 병행**: 반응형 actor 가 5채널 검증 신뢰도 ↑ but install 무거움 (RVO2 cmake + Gazebo plugin 포팅 등)
- **Lean**: P3 와 병행하되 작은 prototype (1-2 명) 부터. issue 별도 작성 예정.
- **다음 action**: HuNav ROS2 Jazzy fork 가용성 조사 (research feed item 만들기).

## Q-002 — 2026-05-26 — `[meta]` Decision/Open-question 자동 추출 신뢰도

- **Question**: cron Builder 가 journal 에 적은 "Recommended next priorities" 가 진짜 우선순위인가? 그냥 task 끝의 형식적 한 줄 아닌가?
- **Trade-off**: 신뢰하면 자동 Today 승격 가능 (자율성 ↑), 의심하면 사람 review 필요 (정확성 ↑)
- **Lean**: 신뢰하되 매주 wrap 의 회고에서 "지난 주 next priorities 중 실현 비율" 측정 (calibration metric).
- **다음 action**: wrap.md 에 "지난 주 priority 명중률" 한 줄 추가 (issue 별도).

## Q-001 — 2026-05-25 — `[license]` reference 4종 모두 license 미명시 — 어디까지 vendoring?

- **Question**: safe_control (264⭐), cfm_mppi, DR-MPC, TCFM 모두 LICENSE 파일 X. 차용 어디까지?
- **Trade-off**: vendoring → 빠른 통합 + license 위험 / use-in-place → license 안전 + setup 비용
- **Lean**: D-005 로 결정 — use-in-place + wrapper. **resolved → D-005**.
- ~~Status: open~~
- **Status**: resolved → D-005

---

## Append 정책 (cron-agent)

매 cycle 의 REPORT phase 에서:
- 이번 cycle 중 결론 안 났지만 의미 있는 trade-off 만났으면 → 이 파일 prepend (Q-NNN)
- 트리비얼한 모호함 (단순 어떤 변수명 쓸까) → journal 의 "open question" 섹션만
- 이미 결정 났으면 → `decisions.md` 의 D-NNN 으로 직접 가고 여기 X

Q 번호도 strictly 증가, 절대 재사용 X. 답 나면:
1. Q-NNN 의 Status `resolved → D-MMM` 으로 변경
2. `decisions.md` 에 D-MMM entry 추가하면서 Refs 에 Q-NNN 인용

_Last manual update: 2026-05-28 KST_
