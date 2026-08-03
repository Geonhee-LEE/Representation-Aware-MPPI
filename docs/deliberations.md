# Deliberation Log — 풀리지 않은 고민

> 의사결정 이전 단계. **답이 아직 없는 질문** + **trade-off 의 양쪽 모두 무게 있는 사안**.
> 답을 내면 `decisions.md` 로 승격 (D-NNN entry 추가, 여기서 strikethrough).
> 사람도 cron-agent 도 추가 가능.

**컨벤션**:
- 최신이 위 (prepend), 한 entry ≤ 15 줄
- Status: `open` / `partially-answered` / `resolved → D-NNN`
- Tag: `[scope]` `[arch]` `[priority]` `[license]` `[meta]` `[uncertainty]`

---

## Q-055 — 2026-08-03 — `[uncertainty]` AVX-512 상수와 AVX2 상수 중 **어느 쪽이 정본**인가

- **Question**: D-033 이 D-029/D-030 상수가 **AVX-512 dispatch 에 조건부**임을 확정했다. dev box 는 AVX-512 를 갖고 GH runner 는 갖지 않으며, 두 machine 은 서로 다른 숫자를 낸다 (D-030 headline swing **2.0× vs 1.029×** — 결론의 부호가 갈린다). 그러면 프로젝트가 들고 갈 상수는 어느 쪽인가?
- **Trade-off**: **(a) AVX-512 유지** — 지금까지 측정한 모든 것과 연속적이고 재측정 비용 0. 그러나 CI slow half 는 영구 red 이고, north star 가 요구하는 "모든 환경"에 CPU 는 명백히 포함된다. **(b) AVX2 로 재보정** — portable 하고 CI 와 일치하며 더 흔한 baseline. 그러나 D-029/D-030 전체 재측정이 필요하고 D-030 의 headline 이 **뒤집힌다**. **(c) 둘 다 보고** — 정직하지만 모든 표가 2 배가 되고, 어느 쪽으로도 결정을 못 내린다.
- **Lean**: **(b) 쪽으로 기운다**, 단 재보정 전에 Q-054(d) 의 fragility sweep 이 선행되어야 한다. 이유: 부호가 CPU 에서 뒤집히는 상수는 어느 machine 에서 쟀든 **주장이 약한 것**이지 AVX-512 가 틀린 게 아니다. AVX2 를 고르는 실질적 근거는 "더 맞아서"가 아니라 **검증 가능해서** — CI 가 재현할 수 없는 상수는 다음에도 똑같이 조용히 썩는다. 다만 (b) 는 D-030 을 철회하는 것과 같으므로 sweep 없이 하면 안 된다.
- **다음 action**: re-baseline branch (STATE #16) 에서, Q-054 의 fragility sweep 직후. **stack 금지** — queue drain 이 선행. 그 전까지 D-029/D-030 은 `AVX512_SKX 에서 측정됨` 이라는 scope line 을 달고 다닌다.

## Q-054 — 2026-08-03 — `[uncertainty]` numpy minor version 에서 **부호가 뒤집히는 결과**를 증거로 계속 들고 갈 수 있는가 → **전제 정정 (D-033): 뒤집는 것은 version 이 아니라 CPU SIMD dispatch 였다.** 질문 자체(FP-fragile 한 결론이 증거가 되는가)는 그대로 open 이고, (d) fragility sweep 이 여전히 다음 action — 다만 sweep 의 축은 numpy version 이 아니라 **dispatch** 다.

- **Question**: D-032 가 측정했다 — scale-matched `w_voo` 의 horizon swing 이 numpy **1.26.4 에서 2.0×**, **2.5.1 에서 1.029×**. 같은 box, 같은 seed, 같은 코드. D-030 은 그 2.0× 위에 "rollout horizon 은 sweep 가능한 축이 아니다" 를 세웠고, test 의 실패 메시지 스스로가 1.2× 미만이면 반대 결론이라고 적어 놓았다. pin 은 이 숫자를 **재현 가능**하게 만들었지 **참**으로 만들지 않았다. 그렇다면 D-029/D-030 은 planner 에 대한 사실인가, 아니면 `planner × FP 환경` 에 대한 사실인가?
- **Trade-off**: (a) **pin 을 계약으로 받아들이고 진행** — 값싸고 지금 상태. 하지만 "이 결과는 numpy 1.26.4 에서 참" 은 north star("모든 환경에서") 가 요구하는 주장보다 훨씬 약하고, 그 약함이 어디에도 안 적혀 있으면 다음 독자는 강한 주장으로 읽는다. (b) **결론을 내는 test 는 threshold 가 아니라 seed 분포로 판정** — `n` seed 에서 swing 의 CI 가 1.2 를 넘는지. FP drift 를 noise 로 흡수하지만 지금 4-seed 를 훨씬 키워야 하고 slow half 비용이 곧 증거인 상황에서 직격이다. (c) **두 numpy 에서 모두 재도출하고 겹치는 결론만 carry** — 가장 정직하고 가장 비싸다 (D-029/D-030 전체 재측정 × 2). (d) **chaotic amplification 자체를 측정** — 같은 arm 을 FP 섭동만 주고 여러 번 돌려 결론의 fragility 를 수치화. 그러면 어떤 주장이 취약한지 *알고* 고를 수 있다.
- **Lean**: **(d) 먼저, 그다음 (c) 를 선택적으로.** 지금 모르는 것은 "어느 결론이 취약한가" 이지 "어떻게 고치나" 가 아니다 — 5 개가 뒤집혔고 353 개는 안 뒤집혔으므로 fragility 는 **suite 전반의 성질이 아니라 특정 주장의 성질**이고, 그 경계를 긋는 것이 가장 정보량이 큰 다음 한 걸음이다. (b) 는 (d) 의 답이 "대부분 취약" 일 때만 정당화된다.
- **선결 문제 / 규모**: `w_voo` 계열 결론 대부분이 D-029 의 scale-matched weight 위에 서 있고 그게 다시 D-028 의 quotient 위에 선다 — 이 stack 이 통째로 같은 FP 민감성을 공유하는지는 미확인. 또한 D-032 가 기록한 **numpy 2 내부의 machine 간 ~3% 잔차**는 pin 이 문제를 줄였을 뿐 없애지 않았다는 뜻이므로, (d) 의 섭동 규모는 임의로 고를 게 아니라 그 3% 에서 잡는 게 자연스럽다.
- **다음 action**: queue drain 후 re-baseline branch (STATE #16) 에서. 그 branch 는 이미 "모든 baseline 수정 + 전면 재측정" 이므로 (d) 의 자연스러운 집이고, 그전에 stack 하면 안 된다.
- **Status**: `open`

## Q-053 — 2026-08-03 — `[meta]` executor 의 REVIEW 는 **자기 PR 의 CI 상태**를 읽어야 하는가

- **Question**: 이 branch 의 CI 는 **14 run 연속 red** 였고 (2026-08-02T10:09Z 이후), 마지막 6 run 은 job timeout 으로 killed 됐다. 그 24 시간 동안 매 cycle 은 `sandbox:pass=357/357` 을 **local** 기준으로 보고했고 STATE 는 "#67 ... 21 (PR #67)" 로만 적었다 — #68/#69 에는 "CI green" 이 붙어 있는데 #67 에는 아무 표기가 없었고, 아무도 그 부재를 눈치채지 못했다. D-016 은 "red PR = deliverable 이 안 끝난 것" 이라 선언했지만 그것을 **읽는 단계**를 어디에도 넣지 않았다.
- **Trade-off**: (a) **REVIEW Phase 1 에 `gh pr checks <own-PR>` 한 줄 추가.** 비용 ~2 초, 26 cycle 짜리 사각을 닫는다. 단 gate-1 이 먼저 fire 하면 REVIEW 까지 못 가는 cycle 도 있어 위치가 애매하다. (b) **EXECUTE 끝, push 직후에 확인** — 방금 민 commit 의 CI 는 아직 안 돌았으므로 항상 *직전* commit 을 보는 셈이라 한 cycle 늦다. 그래도 지금(무한)보다 낫다. (c) **local pass 를 metric 으로 쓰는 것을 금지하고 CI 결과만 TSV 에 기록** — 가장 엄격하지만 cycle 이 CI 를 기다려야 해 15 분 EXECUTE 예산과 충돌.
- **Lean**: **(a) + (b) 병행, (c) 는 기각.** 진짜 결함은 "확인을 안 했다" 가 아니라 **`sandbox:pass=N/N` 이라는 metric 문자열이 어느 surface 에서 잰 값인지 표기가 없다** 는 것이다. 그래서 최소 수리는 TSV/commit 의 metric 을 `sandbox:pass=...` → `sandbox-local:pass=...` 로 정규화하고, CI 값은 별도 이름으로 두는 것. 그러면 "local 만 있고 CI 가 없다" 가 표에서 **보인다**.
- **선결 문제**: gate 1 이 51 cycle 연속 fire 하는 상황에서 executor 가 같은 PR 에 계속 쓰는 것 자체가 이 사각을 만든다 — 새 PR 이라면 생성 직후 CI 를 봤을 것이다. 즉 이건 queue stall 의 **2차 피해**이고, drain 이 되면 압력이 줄어든다. 그래도 표기 수리는 drain 과 무관하게 유효하다.
- **Status**: `open`

## Q-051 — 2026-08-03 — `[meta]` suite 가 636 s 다. `slow` marker 인가, cap 단축인가, 예산 증액인가 → **~~open~~ resolved → D-031**

- **Question**: 원안 그대로. 답은 marker 였고, lean 이 맞았다.
- **답이 바꾼 것**: 질문의 **전제**가 틀렸다. 이건 "나중 cycle 을 싸게 만드는" 최적화가 아니라 **head-of-line PR 의 CI 가 이미 red 였던 것의 수리**였다 (→ Q-053). 그리고 marker 의 **단위**가 비자명했다: test 단위 marking 은 class-scoped fixture 비용을 살아남은 형제에게 옮길 뿐이라 628 s → 338 s 에서 멈췄고, `call` 시간만 재는 측정은 97.65 s 짜리 `setup` 을 구조적으로 못 봤다. fixture scope 로 자르니 **115 s**.
- **Status**: `resolved → D-031`

## Q-052 — 2026-08-03 — `[meta]` closed-loop 행동의 귀인은 leave-one-out 을 버리고 **power set** 으로 가야 하는가

- **Question**: D-030 이 `H=45` freeze 의 원인이 `w_collision` 과 `w_obs_soft` 의 **논리합**임을 보였다 — 각각을 끄면 cruise 가 0.97× / 0.90× (개선 없음), 둘 다 끄면 5.6×. LOO 는 두 항에 각각 책임 ≈ 0 을 매긴다. D-028 의 `weight_units.measure` 는 구조상 LOO 다. 그렇다면 이 repo 의 귀인 도구 기본값을 `2**g` power set 으로 바꿔야 하는가?
- **Trade-off**: (a) **LOO 유지, power set 은 opt-in** (`horizon_audit.ablate` 가 지금 그 위치). 싸고 (`g` runs), *cost 기여도* 질문에는 정확하다 — LOO 는 틀린 게 아니라 **다른 질문**에 답한다. 대신 중복 원인은 아무도 찾지 않으면 안 보인다. (b) **행동 주장에는 power set 을 필수화**. `g=3` 이면 8 arm × seed — 이미 504 s 인 suite 에 감당 안 되고, 후보 term 선정 자체가 cost 함수 읽기라 D-026 이 경고한 바로 그 단계에 의존한다. (c) **중간 — LOO 로 훑고, "아무 singleton 도 안 움직이는데 행동은 설명이 필요한" 경우에만 power set 으로 승격.** 이번 cycle 이 실제로 밟은 경로.
- **Lean**: **(c)**, 단 발동 조건을 명시적으로 적을 것. 이번엔 "LOO 가 전부 ≈0 인데 행동은 명백히 달라졌다" 가 신호였고, 그건 자동으로 검사 가능하다 — `redundant_sets` 가 그 검사의 절반이다. 나머지 절반 (LOO 표가 전부 0 일 때 경고) 은 `weight_units` 쪽에 있어야 하는데 아직 없다.
- **선결 문제**: 중복성은 term 쌍의 성질이 아니라 **(scene, horizon, lam) 의 성질**일 수 있다. `H=30` 에서는 freeze 자체가 없으므로 이 쌍의 중복성도 없다. 한 scene · 한 rung 의 관찰을 도구 기본값 변경 근거로 쓰기 전에 최소 한 개의 다른 scene 에서 재현이 필요하다.
- **Status**: `open`

## Q-049 — 2026-08-03 — `[uncertainty]` 새 cost 항의 weight 는 **무엇의 단위**로 sweep 되어야 하는가

- **Question**: D-027 이 `w_voo=200` — 직전 항의 weight 를 그대로 물려받은 값 — 이 이 scene baseline total-cost spread 의 **6.19×** 임을 측정했고, 그 결과는 "정보 선호가 강한 planner" 가 아니라 median ESS **1.00** 인 argmin-over-draws, 즉 **위장된 temperature 변경**이었다. 그렇다면 repo 의 모든 critic weight (`w_risk=40`, `w_epist`, `k_margin_per_sigma`, `w_terminal=30`) 는 무엇에 대해 상대적으로 진술되어야 하는가?
- **Trade-off**: (a) **절대 단위 유지 + weight 마다 ESS band 를 검사** — 지금 방식. 싸고 arm 재현이 쉽지만, band 를 벗어난 cell 이 나올 때까지 그 sweep 이 controller 비교가 아니었다는 걸 모른다. (b) **weight 를 baseline spread 의 비율로 선언** (`w_voo = 0.1 · median ptp`) — 항끼리, scene 끼리 비교 가능해지고 D-017 의 lam 문제와 직교하지만, 계수가 **scene 의존적이고 measured** 가 되어 simulation-free screen 계열의 자산 (D-023/D-025) 과 성질이 달라진다. (c) cost 를 **step 마다 정규화** — softmax 를 계산 순간에 scale-free 로 만들지만 `lam` 의 의미와 이미 calibrate 된 `lam_windows.yaml` 전체를 무효화한다.
- **Lean**: **(b), 단 보고 단위로만.** 계수를 코드에 넣지 말고 **결과를 진술할 때** baseline spread 배수를 함께 적는다 — D-027 의 6.19× 가 그 한 줄로 collision 을 설명했다. (c) 는 `lam` 축 전체를 다시 열므로 지금 값이 없다.
- **선결 문제**: baseline spread 의 중앙값은 scene·seed·step 에 따라 크게 흔들린다 (이 scene 에서 median 79.09 vs mean 3806.8, **48×** 차이). 비율을 쓰려면 **어느 통계**인지부터 못박아야 하고, D-024→D-025 가 정확히 그 종류의 실수 (읽히지 않는 값으로 나눈 비율) 를 두 cycle 잡아먹으며 고쳤다.
- **Status**: `resolved → D-028` (2026-08-03 06:00).
- **답**: **(b), 보고 단위로만 — lean 대로.** 단 표는 Q 가 예상한 두 결말 중 어느 쪽도 아니었다. (1) 네 knob 은 **한 class 가 아니다**: `w_terminal` 만 live 한 순수 additive 계수 (0.328), `w_epist` 는 spread 가 항등적으로 0 인 항을 곱하므로 ratio **정확히 0**, `k_margin_per_sigma` 는 애초에 계수가 아니라 `exp()` 안쪽 shift 라 **cost 단위 자체가 없다** (미터). (2) 그리고 일반화되는 건 분자가 아니라 **분모**였다 — 같은 weight 를 자기 arm 에서 재면 1.46×, 더해지는 baseline 에서 재면 6.19×. 나쁜 weight 일수록 자기가 만든 landscape 로 채점되어 **유리하게** 나온다. **선결 문제(어느 통계인가)는 `REPORTING_STATISTIC = "median"` 으로 선언 후 계측**했다.
- **남은 것**: 이 비율을 실제 sweep 의 **보고 형식**으로 채택할지는 미결 — 계측기 (`weight_units.py`) 는 있고 default 는 하나도 안 움직였다.

## Q-048 — 2026-08-03 — `[arch]` goal 재방문 reference 를 **screen 으로 막을 것인가, controller 를 고칠 것인가**

- **Question**: D-026 이 shipped objective 의 계약을 특정했다 — `v_ref` 와 `w_terminal` 이 둘 다 **Euclidean `d_goal`** 의 함수라, goal 근방을 중간에 재방문하는 reference 에서 loop 이 자기 goal 위에 주차한다. 수리 경로는 둘: (a) `feasibility.goal_approach` screen 으로 그런 scene 을 **matrix 에서 배제**한다 (이번 cycle 이 배포한 것), (b) 두 항을 **remaining arclength** 구동으로 바꾸고 `reached_goal` 이 근접뿐 아니라 completion 도 요구하게 한다.
- **Trade-off**: (a) 는 지금 당장 공짜고 기존 수치를 하나도 안 건드리지만, **north star 의 "모든 환경" 을 깎아서 산다** — loop / patrol / return-to-start 미션을 영구히 계약 밖에 둔다. (b) 는 진짜 capability 를 되찾지만 `d_goal` 은 shipped cost 의 **두 항 모두**에 들어있어 repo 의 모든 기존 수치를 무효화하고, arclength 추적은 self-intersecting path 에서 **projection 이 모호**해진다 (figure-8 의 crossing point 에서 "남은 거리" 가 두 값을 갖는다 — 이게 애초에 문제가 어려운 이유).
- **Lean**: **(b), 단 re-baseline branch (#11) 에서.** (a) 를 영구 답으로 두면 D-026 이 찾아낸 게 "고칠 결함" 이 아니라 "선언된 한계" 가 되는데, 그건 이 cycle 이 실제로 측정한 것보다 약한 결론이다. 다만 Q-032 (queue 중 shared baseline 정정 금지) 가 유효하므로 지금은 아니다. arclength 모호성은 **monotone progress state** (되돌아가지 않는 arclength 커서) 로 풀리는 게 표준이고, 그 자체가 P3 representation 축과 무관하지 않다.
- **선결 문제**: A4/B4 가 보여주듯 `w_terminal = 0` 은 답이 아니다 — **0/4 reached**, goal 에서 멈출 이유가 사라진다. 즉 terminal 항은 제거 대상이 아니라 **재-매개변수화** 대상이다.
- **다음 action**: #11 re-baseline branch 에서 (b) 를 구현하고, `city_figure8_v0` 를 **회귀 테스트**로 승격 (현재는 screen 이 배제하는 대상). screen 은 그 뒤에도 남는다 — 정적 전제조건은 수리와 무관하게 유효하다.

## Q-047 — 2026-08-03 — `[scope]` `city_figure8_v0` 의 0.016 m/s → **~~open~~ resolved → D-026: 두 선택지 모두 기각**

- 제기된 이분법 (Q-037 계열 scene defect vs self-intersecting reference 에서의 controller 실패) 은 **partition 이 아니라 가설**이었고, 양방향 intervention 이 양쪽을 각각 죽였다. self-intersection 없는 `city_curved_v0` 에 `goal := start` **하나만** 적용해도 동일 붕괴 (→ (b) 기각); figure-8 의 closure 를 열어도 30.6 m 중 13.1 m 만 주행 (→ (a) 기각). 실제 원인은 **controller 계약** — 자세히는 D-026, 수리 경로는 Q-048.
- reportable matrix 는 **4 로 유지** (축소 분기가 반증됨).

## Q-043 — 2026-08-02 — `[uncertainty]` epistemic 채널을 들리게 하려면 **scene 을 고를 것인가, planner 를 바꿀 것인가** → **partially-answered → D-027: 제3안 (cost 구성을 바꿈) 이 scene 선택도 horizon 증가도 없이 통함**

- **D-027 (2026-08-03)**: 이 이분법은 다시 한번 partition 이 아니었다. shadow 가 rollout cone 안에 들어오게 만드는 대신 **cost 를 rollout 이 이미 도달하는 위치에서 평가되도록** 구성을 바꾸면 (value-of-observation), shipped `H=30` 그대로 그리고 shipped scene 그대로 spread 0.00 → 1060 이 된다. 즉 (a) 도 (b) 도 필요 없었다. **단** "들린다" 와 "돕는다" 는 별개이고 후자는 n=8 에서 철회됐으므로, `(w_voo, horizon)` 2×2 는 여전히 할 일로 남는다 — 이제 **항이 0 이 아닌 상태에서** 돌릴 수 있다는 점만 다르다.

- **Question**: D-021 이 `w_epist` 의 효과를 **rollout reach** 로 게이팅된다고 특정했다. 그러면 P3 의 epistemic 축을 측정 가능하게 만드는 방법은 둘 중 하나다 — (a) rollout 이 이미 shadow 에 닿는 **scene 을 고른다** (blind-corner 계열, PR #68), 또는 (b) planner 를 **바꿔서** 닿게 만든다 (horizon↑, sampled speed↑, sensing range↓). 어느 쪽이 정직한 실험인가?
- **Trade-off**: (a) 는 controller 를 안 건드리므로 A/B 가 깨끗하지만, "epistemic 채널이 도움이 된다" 가 **shadow 가 rollout 안에 들어오도록 고른 scene 에서만** 성립하는 주장이 된다 — north star 의 "모든 환경" 과 정면 충돌. (b) 는 모든 scene 에 적용되지만 **horizon 을 늘리면 stock 도 같이 좋아진다** — epistemic 항의 기여와 지평 확장의 기여가 교란되어 D-017 이 금지한 종류의 uncontrolled 비교가 된다. 게다가 horizon 은 shipped `MPPIParams` 기본값이라 바꾸면 repo 의 **모든** 기존 수치가 무효.
- **Lean**: (b) 를 **factor 로 승격**하되 default 는 안 건드린다 — 즉 `horizon` 을 A/B 의 **명시된 축**으로 만들어 `(w_epist, horizon)` 2×2 를 돌린다. 그러면 "epistemic 이 돕는가" 와 "지평이 돕는가" 가 분리되고, D-021 의 reach 게이트가 교란이 아니라 **측정 대상**이 된다. (a) 는 그 2×2 를 어느 scene 에서 도느냐의 문제로 흡수된다.
- **선결 문제**: D-021 은 reach 게이트의 **scalar 형태를 반증**했다 (거리만으로는 예측 불가, 방향이 필요). 따라서 "이 scene 에서 epistemic 이 들릴 것인가" 를 **돌리기 전에** 판정하는 screen 은 아직 없다. `exposure.py` 가 정적 스크린의 선례이므로, rollout cone × σ-field 교집합을 재는 유사 스크린이 자연스러운 후보.
- **다음 action**: 위 2×2 를 blind-corner scene (#68) 에서 — 단 **#68/#69 merge 이후**. 그 전에 할 수 있는 것: 방향을 담은 reach screen 을 `exposure.py` 옆에 8 scene 전체로 돌려 **어느 scene 이 애초에 epistemic 을 들을 수 있는지** 표로 만드는 일 (시뮬레이션 없음, merge 불필요).

## Q-042 — 2026-08-02 — `[uncertainty]` window admissibility 기준을 **all-seeds 논리곱**에서 무엇으로 바꿔야 하나

- **Question**: D-019 가 밝혔듯 "모든 seed 가 band 안" 기준은 `n` 이 커질수록 단조로 엄격해져, `shared`/`per_arm` 판정이 seed 수의 함수가 된다 (parent scene: n=4 `shared`, n=8 `per_arm`). 그렇다면 기준은 무엇이어야 하나?
- **Trade-off**: (a) **현행 유지 + `n` 명시** — 싸고 기존 표 보존, 그러나 판정이 여전히 n 의존이라 matrix 확장 때마다 과거 판정이 흔들린다. (b) **quantile 완화** (≥⌈0.9n⌉ seeds) — n-민감도는 낮추지만 없애지 못하고, threshold 자체가 새 자유 파라미터. (c) **구간추정** — seed bootstrap 으로 window 에 신뢰구간을 붙이고 "교집합이 비었다"를 유의성으로 판단. 원리적으로 옳고 `n` 을 명시적 통계량으로 흡수하지만 calibration 비용이 몇 배.
- **Lean**: (c) 가 옳은 방향이되 **re-baseline 이후**. 당장은 (a) — D-019 가 채택한 것. 판단 근거: 지금 필요한 건 판정의 정밀도가 아니라 **판정이 무엇의 함수인지 아는 것**이고, 그건 이미 얻었다.
- **2026-08-02 22:00 답**: 세 기준을 **새 run 없이** 채점 완료 → **D-020**. per-seed ESS 는 보유하지 **않지만** `(n_in_band, n)` 이 충분통계량이라 무관했다. **(b) 폐기** (`ceil(0.9n) == n` for `n ≤ 9` → 이 repo 의 seed 수에서 (a) 와 점별 동일, 산술 반증). **(c) 확정** — `k=n` 에서 bound 가 `n/(n+z²)` 로 `n` 에 증가하므로 D-019 편향을 **역전**; 실측 flip 에서 0.510 → 0.529. bootstrap 이 아니라 **closed form** 으로 (n=8 격자 step 0.125 ≫ 분해할 효과 0.019). default 는 (a) 유지.
- **남은 질문 (여전히 open)**: (c) 의 **threshold** 를 무엇으로 정당화하나. 이번 cycle 은 의도적으로 고르지 않았고, 그 전엔 default 승격 불가.
- **다음 action**: re-baseline 브랜치(STATE #7)가 window 를 (a)/(c) **양쪽으로** 재생성하고 **불일치 집합**을 보고 — 그 집합이 D-019 `n` stamp 가 실제로 필요한 범위다.
- **Status**: partially-answered → (b) refuted / (c) adopted by **D-020**; threshold 미정

## Q-017 — 2026-07-13 — `[uncertainty]` 가려진 obstacle 을 피하려면 epistemic σ 를 어떻게 소비해야 하나 — margin inflation vs additive shadow cost

- **Question**: EPISTEMIC 채널(σ, occlusion shadow + beyond-range)을 MPPI cost 로 소비하는 두 경로 — (a) **additive** `w_epist·σ` (rollout point 마다 σ 비례 가산, field-absolute), (b) **margin inflation** `k·σ` (D-013, 알려진 obstacle clearance 를 σ 만큼 축소, obstacle-relative) — 중 어느 것이 '가려진 obstacle' class 를 실제로 피하게 하나?
- **이번 cycle 결과 (negative, 기하학적)**: `ShadowCostCritic` (a) 를 sandbox 에 구현·검증했으나 **단일 볼록 obstacle 시나리오에서는 (a) 도 (b) 와 똑같이 closed-loop inert**. 근거: 단일 obstacle 의 occlusion shadow = robot→obstacle ray-cone 정확히 그 뒤. rollout 이 그 shadow 에 들어가려면 obstacle 쪽으로 향해야 하고, 그 지점은 이미 stock soft/collision cost 가 지배 → shadow-avoidance ⊆ obstacle-avoidance. 측정: centered obstacle 에서 `w_epist` 0→200 min_clearance Δ=1.9e-12; pre-obstacle pose 에서 softmax-weighted E_w[σ]=~0 already at w_epist=0 (uniform mean 1.234). 즉 **가산항이 재분배할 weight 가 없다**.
- **Trade-off / 남은 갈림길**: (a) 가 정보를 더하는 건 shadow 가 *obstacle-cost 낮은 shortcut* 일 때뿐 — **blind corner / wall (다중·확장 occluder)** geometry, 또는 **beyond-range frontier** 차등(현재 r_sense=5m ≫ rollout reach 1.2m 라 common-mode 로 softmax 에서 상쇄). 대안: reachability risk-region (2503.04563) 또는 CVaR-over-occluded-prior 재정식화.
- **Lean**: (a) mechanism 은 유지(구현 완료, ablation-invariant, w_epist=0 no-op). 다음은 **blind-corner sandbox scenario** 를 만들어 (a) 가 non-inert 임을 closed-loop 로 입증 — 그 전까진 단일 obstacle 벤치로 epistemic gain 을 판단 금지.
- **다음 action**: `eval/scenarios/` 에 wall/L-corner occlusion scenario 추가(가려진 free-space shortcut) → `test_shadow_cost_moves_needle_in_blind_corner` GREEN 목표. resolve 시 D-MMM. refs: PR(이 cycle) + `journal/2026-07/13-*-p3-epistemic-shadow-cost-critic.md`, research feed `research/2026-07/159.md` (occlusion-aware CMPC 2503.04563).
- **Status**: partially-answered (mechanism 구현·검증 완료; 단일 obstacle inert 확인 → blind-corner 시나리오 대기)

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
