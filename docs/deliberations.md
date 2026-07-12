# Deliberation Log — 풀리지 않은 고민

> 의사결정 이전 단계. **답이 아직 없는 질문** + **trade-off 의 양쪽 모두 무게 있는 사안**.
> 답을 내면 `decisions.md` 로 승격 (D-NNN entry 추가, 여기서 strikethrough).
> 사람도 cron-agent 도 추가 가능.

**컨벤션**:
- 최신이 위 (prepend), 한 entry ≤ 15 줄
- Status: `open` / `partially-answered` / `resolved → D-NNN`
- Tag: `[scope]` `[arch]` `[priority]` `[license]` `[meta]` `[uncertainty]`

---

## Q-016 — 2026-07-08 — `[arch]` HOLO-MPPI prior interface: 학습된 sampling prior 는 어떤 representation 을 conditioning 입력으로 써야 하나

- **Question**: HOLO-MPPI 패턴으로 offline-trained policy 가 nav2_mppi 의 sampling distribution parameters 를 출력할 때, 그 policy 의 observation input 을 (a) raw P1 BEV features 만 쓸지, (b) P2 latent / residual encoder output 을 쓸지, (c) 둘을 합칠지. 즉, sampling prior 가 *perception representation* 만 조건화되어야 하나 *dynamics latent* 까지 조건화되어야 하나.
- **Trade-off**:
  - **(a) P1 BEV only**: P2 독립 → prototype 지금 시작 가능, 학습 파이프라인 단순; 단, dynamics-regime 정보(venue-specific friction, speed profile) 가 prior 에 없어 cafñe → small_city 이동 시 covariance 적응 제한.
  - **(b) P2 latent only**: dynamics context 풍부하나 #44 merge 전까지 blocked; BEV 시각 맥락 없이 latent 만 쓰면 obstacle geometry 정보 손실.
  - **(c) both (fusion)**: 가장 완전하나 두 encoder 의 학습·inference pipeline 결합 → staging / dependency 복잡화; P5 ablation 전엔 (a) vs (c) contribution 분리 불가.
- **Lean**: **(a) P1 BEV-only prior 먼저** — P2 독립, HOLO-MPPI 핵심 thesis ("representation drives sampler") 을 가장 빠르게 검증; (c) 는 P2 land 후 P4/P5 ablation fork (HOLO-MPPI-fused vs HOLO-MPPI-BEV-only). 근거: 현재 P2 stall 21일 — P2 gated 작업은 scheduling 열위, BEV-only prior 가 thesis 입증 선행 조건.
- **다음 action**: P1 BEV feature extractor (semseg pretrained) prototype 후 `BEVConditionedPrior` 모듈 설계 → P2 land 시 (c) extension 분기. resolve 시 D-MMM. ref: [`research_feed_synthesis_2026_07_05.md`](research_feed_synthesis_2026_07_05.md) Entry 3 + 02:00 feed HOLO-MPPI [[2606.16480]].
- **Status**: open

## Q-015 — 2026-07-05 — `[uncertainty]` P5 harness σ-calibration-quality 축: 소비자 gain sweep 전에 σ 자체가 calibrated 인가를 검증·metric 화해야 하나

- **Question**: §2 의 모든 gain (`k·σ`, `z(δ)·σ_ale`, `σ²_ref`) 은 upstream σ 가 신뢰할 수 있다고 가정한다. §3 metric 은 downstream 결과(near-miss, time-to-goal, cte)만 본다 — σ 의 stated coverage 가 empirical coverage 와 맞는지 않는다. σ 가 mis-calibrated 이면 `(k,δ)` sweep 은 miscalibration 을 gain 에 흡수해 scenario 간 mis-generalize 하고, frozen config 가 "geometry 필요" vs "σ 불신" 구분 불가. **harness 에 σ-calibration stage + calibration-quality metric axis (ECE / interval-coverage / reliability-diagram) 가 §2 gain sweep 의 *upstream* 으로 필요한가, 아니면 gain sweep 의 흡수로 충분한가?**
- **Trade-off**:
  - **gain sweep 이 흡수**: 구현 최소; 그러나 `k` 가 geometry vs σ 불신 구분 불가 → cross-scenario mis-generalization 위험
  - **(a) parametric recalibration** (Rethinking-Gaussian `2603.10407`): 가장 저렴, Gaussian head 가정; §3 ECE axis 는 새 σ 소스 없이 즉시 추가 가능
  - **(b) global conformal coverage** (Scenario-aware UQ `2512.05682`): distribution-free 1 quantile; local variation 무시
  - **(c) perception-conditioned local conformal** (OCULAR `2605.13028`): per-cell BEV-feature 기반; 가장 강하나 non-linear residual+ensemble 에서 linear-Gaussian 가정 포기
- **Lean**: stage warranted (P4 pedestrian covariance 가 miscalibration 가장 쉽게 물림). 시작 = **(a) parametric recalibration + §3 ECE/coverage metric axis** (새 σ 소스 없이 즉시 추가); local conformal (c) 는 P5 ablation fork (vs OCULAR).
- **다음 action**: P4/P5 cycle 이 첫 `(k,δ)` Pareto front 대비 "recalibrated σ 가 front 를 움직이나?" 검증 → yes: D-MMM (stage 추가); no: D-MMM (gain 흡수 충분). 구별: Q-013 (sweep *전략*), D-015 (sweep *소유자*). ref: [`p5_risk_calibration_harness.md`](p5_risk_calibration_harness.md) §3½.

## Q-014 — 2026-07-02 — `[uncertainty]` epistemic 채널의 *response mode*: passive `k·σ` margin 만인가, active-perception / tube 도 필요한가

- **Question**: 설계(§5, stack §4, margin critic §2)는 epistemic vs aleatoric 를 *routing* 으로만 가르고, epistemic 의 *response* 는 암묵적으로 passive back-off (`k·σ` 로 clearance 확대)라 가정한다. 그러나 epistemic uncertainty 는 정의상 **sensing / replanning / data 로 감소 가능** — 그래서 올바른 대응은 물러서기가 아니라 *능동적으로 줄이기* 일 수 있다. epistemic 채널이 `k·σ` margin 에 **더해 (또는 대신)** 두 번째 response term (info-gather / active-perception cost) 을 가져야 하나, 그리고 tube 가 swept scalar `k` 보다 나은 σ→margin map 인가.
- **Trade-off**:
  - **margin-only (`k·σ`)**: 단순, `k=0`⇒baseline 깔끔한 ablation, 구현 최소. 그러나 epistemic 의 reducible 성질을 안 씀 — 미관측 영역을 계속 회피만 하고 관측하러 안 감.
  - **+ active-perception term (PA-MPPI 2509.14978)**: rollout 을 미관측 pose 관측 쪽으로 bias — unobserved-mask(§3)의 능동 짝. 그러나 새 cost term + weight knob, MPPI objective 복잡화.
  - **tube-margin (GP-contraction-tube 2507.02098)**: hand-set `k` 대신 contraction-bounded reachable tube 로 σ→margin 을 *원리적으로* 매핑. 그러나 contraction metric 추정 필요, 무거움.
- **Lean**: shipping default 는 margin-only (`k·σ`, D-013 critic) 유지 — 깔끔한 ablation baseline 이 먼저. active-perception / tube 는 **P3-design / P5-ablation fork** 로 둔다 (margin-only vs margin+active-perception vs tube-margin 3-way). Q-008(margin `k` 의 *value*)과 구별됨 — 이건 response *mode* 자체를 물음. 근거: 2026-06-29 feed 4건 수렴 (TRIAGE 2603.08128 routing-by-dominant-type, PA-MPPI 2509.14978 in-sampler perception cost, GP-contraction-tube 2507.02098, BC-MPPI 2510.00272 aleatoric 짝).
- **다음 action**: P2 ensemble land + P3 critic 구현 후 baseline `k·σ` 먼저 세우고, P5 harness 에서 3-way ablation 추가. resolve 시 D-MMM. ref: [`margin_inflation_cost_critic_interface.md`](margin_inflation_cost_critic_interface.md) §7 (O-2 원문), [`residual_in_rollout_reference.md`](residual_in_rollout_reference.md).

## Q-013 — 2026-06-29 — `[uncertainty]` coupled knob-vector 의 sweep 전략: 2-D `(k,δ)` plane vs full grid vs coordinate-descent

- **Question**: D-015 의 calibration harness 가 5 knob (`k`/`δ`/`α`/`σ²_ref`/`σ²_ref_ale`) 을 어떤 전략으로 sweep 하나. full 5-D grid (기각, combinatorial) vs **2-D `(k,δ)` plane + refs frozen** (harness 문서 default) vs coordinate-descent (저렴하나 `k`↔`σ²_ref` 결합 valley 에서 stall).
- **Trade-off**:
  - **full grid**: unbiased 이나 `O(n^5)` — 사실상 실행 불가
  - **2-D `(k,δ)` plane + refs frozen**: refs 가 gain 과 separable 가정 (1차 근사 true, §1) — 가장 적은 점수로 coupling 의 핵심(`k`·`δ` 가 같은 `d_eff` 조임)을 본다
  - **coordinate-descent**: 최저가이나 `k`↔`σ²_ref` redundancy 를 가장 못 다룸 — 결합 valley 에서 stall
- **Lean**: 2-D `(k,δ)` plane + refs 를 documented default 로 freeze; ±2× ref perturbation 에 Pareto front 가 움직이면 그때만 1-D ref sensitivity pass 추가.
- **다음 action**: P5 cycle 이 첫 measured `(k,δ)` Pareto front 에 대해 resolve → D-MMM 승격. ref: [`p5_risk_calibration_harness.md`](p5_risk_calibration_harness.md) §2/§5.

## Q-012 — 2026-06-27 — `[uncertainty]` aleatoric risk level `δ` / `α`: 어떻게 set 하나 (chance-constraint / CVaR tightening)

- **Question**: `AleatoricRiskCritic` 가 aleatoric `σ` 로 clearance 를 `z(δ)·σ` 만큼 조이거나 CVaR_α tail 을 벌점할 때, target collision prob `δ` (quantile) / tail fraction `α` 를 어디서 얻나. Q-008 의 `k` (epistemic margin gain) 의 aleatoric 형제 knob.
- **Trade-off**:
  - **measured near-miss rate 로 sweep**: 의미 있는 risk 수준, 그러나 P5 eval harness (near-miss/success/time-to-goal) 전엔 없음
  - **hand-pick (예: δ=0.05)**: 즉시 진행, 그러나 임의 — 노이즈 분포·환경에 안 맞을 수 있음
- **Lean**: documented placeholder (`chance_delta=0.05`, `cvar_alpha=0.10`), `cost_weight=0.0` no-op 기본 → P5 measured near-miss 로 calibrate. `k`(Q-008)·`σ²_ref`(Q-009)·`σ²_ref_ale`(Q-011) 와 함께 한 sweep 에 묶음. epistemic `k` 와 달리 데이터 늘어도 0 으로 안 감 (비가역).
- **다음 action**: P5 risk-calibration harness 확보 시 `δ`/`α` set → resolve 시 D-MMM. ref: [`aleatoric_risk_cost_critic_interface.md`](aleatoric_risk_cost_critic_interface.md) §3/§5.

## Q-011 — 2026-06-15 — `[uncertainty]` aleatoric homoscedastic degeneracy guard: spatial-CoV floor 값은

- **Question**: variance head 가 global 단일 노이즈(homoscedastic) 로 collapse 하면 aleatoric 채널이 spatial 정보 0 인 flat raster 가 되는데(유효해 *보이는* 무효 출력), 이를 acceptance 에서 거르는 spatial coefficient-of-variation floor 값을 얼마로.
- **Trade-off**:
  - **엄격한 floor**: collapse 확실히 거름, 그러나 진짜로 균일하게 노이지한 환경을 false-fail
  - **느슨한 floor**: false-fail 적음, 그러나 부분 collapse 통과
- **Lean**: floor 는 #44 가 학습된 뒤에야 set 가능 (`k`/`σ²_ref` 와 같은 un-set 상태). varied-terrain/varied-`(v,ω)` slice 의 측정 CoV 분포로 정함. 채널이 flat ⇒ upstream head-training 버그(렌더러 아님).
- **다음 action**: #44 (heteroscedastic head) land + 학습 후 측정 → floor set. ref: [`aleatoric_channel_bev_rendering.md`](aleatoric_channel_bev_rendering.md) §2/§4.

## Q-010 — 2026-06-15 — `[arch]` D-009 ensemble head: heteroscedastic (NLL) vs MSE point — aleatoric 채널 존재 여부를 가름

- **Question**: D-009 scaffold (PR #44) 의 ensemble head 가 per-dim 예측분산 `σ²_k` 를 내는 heteroscedastic(NLL 학습) 인가, 단순 MSE point regression 인가. 후자면 aleatoric 신호가 *아예 없어* aleatoric 채널·`AleatoricRiskCritic` 둘 다 build 불가. epistemic 은 means 만 필요해 영향 없음.
- **Trade-off**:
  - **NLL variance heads**: epi/ale split (핵심 P3 deliverable) unlock, 비용은 출력 dim +1 + Gaussian NLL loss
  - **MSE point heads**: 단순, epistemic-only, 그러나 P3 의 절반(aleatoric)을 포기
- **Lean**: NLL heads — epi/ale split 이 P3 의 reason-for-being 이고 추가 비용이 새 모델이 아니라 출력 1차원 + loss 교체뿐.
- **다음 action**: #44 머지 전 scaffold 가 head type 확정해야 함 (user/구현 cycle). resolve 시 D-MMM. ref: [`aleatoric_channel_bev_rendering.md`](aleatoric_channel_bev_rendering.md) §1/§7.

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
