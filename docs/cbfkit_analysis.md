# cbfkit 분석 — CBF safety-filter 계열의 canonical 참조

[bardhh/cbfkit](https://github.com/bardhh/cbfkit) (Toyota Research NA, arXiv 2404.07158,
**BSD-3-Clause**, JAX). user 지정 reference (2026-07-11) — issue #65 **S1** 의 설계 기준.

safe_control (D-005) 과 함께 CBF 계열 2번째 외부 ref. `scripts/fetch_refs.sh` 로 클론
(5번째 repo), vendoring X — **패턴 + 수식 차용**.

---

## 무엇인가

| 축 | 내용 |
|---|---|
| 핵심 | CBF/CLF-QP safety filter + **JAX MPPI planner** + 순수함수 sim 파이프라인 |
| 시스템 | unicycle / single·double integrator / quadrotor 6DOF / fixed-wing |
| CBF 변형 | vanilla zeroing / **stochastic (SDE)** / robust (bounded disturbance) / **risk-aware CVaR** / adaptive CVaR / **Neural CBF** / exponential (relative-degree rectify) |
| 인프라 | ROS2 node 생성, Gymnasium safe-RL wrapper, 자체 fast QP (2×5 에서 880× vs JAXopt), Monte-Carlo safety verification (vmap 200 rollouts) |
| 예제 | **pedestrian head-on** (= 우리 S02), MPPI reach-avoid, multi-robot |

### 아키텍처 (차용 1순위)

```
Planner (MPPI: u_traj 반환)
   │ (u_traj 있으면 nominal skip)
   ▼
Nominal controller (t, x, key, ref) → u_nom
   │
   ▼
Safety controller (t, x, u_nom, key, data) → u   ← CBF-QP projection
   │
   ▼
Plant (RK4)
```

모든 컴포넌트가 **고정 시그니처의 순수 함수** — 우리 sandbox 의 controller plug-in
계약 (`command(state, t) → u`) 과 같은 철학. 이 구조 덕에 "MPPI 는 성능,
CBF 는 안전" 의 역할 분리가 코드 경계로 강제됨.

---

## 우리 프로젝트와의 매핑

| cbfkit | 우리 | 관계 |
|---|---|---|
| CBF-QP safety filter | `controllers/cbf_mppi.py` (S1, 이번 구현) | **아키텍처 차용** — MPPI nominal + QP projection |
| risk-aware CVaR-CBF | D-014 `AleatoricRiskCritic` (chance-constraint/CVaR) | 같은 δ/CVaR 수식 — 우리 critic 검증 기준 |
| stochastic CBF (σ(x)dw) | D-013 epistemic k·σ margin | margin inflation 의 원리적 상한 후보 (feed TODO) |
| Neural CBF (h(x) 학습) | P3 학습 representation | "학습된 안전 표현" 의 CBF-side 대응물 |
| MPPI (JAX, reach-avoid) | `stock_mppi` (NumPy) | 병렬 구현 — cross-check 용 |
| Monte-Carlo verification (vmap) | S5 seed-sweep runner | 같은 발상 — 통계적 안전 검증 |

### safe_control 과의 역할 분담

| | safe_control | cbfkit |
|---|---|---|
| 라이선스 | 미명시 (⚠) | **BSD-3 명시** |
| 백엔드 | NumPy/CasADi + Gurobi | JAX (vmap/jit) |
| 강점 | DPCBF (ICRA 2026), gatekeeper, MPC-CBF | CBF 변형 폭 (stochastic/CVaR/neural), 순수함수 계약, MPPI 내장 |
| 우리 용도 | 완성 알고리즘 비교 백엔드 (wrapper 3종) | **설계 패턴 + 수식 원전** (sandbox 구현의 기준) |

---

## sandbox 구현 — `cbf_mppi` (S1)

cbfkit 의 filter 파이프라인을 NumPy 로 이식 (JAX 의존 없이):

- **barrier**: moving-obstacle distance CBF, offset-point 기법으로 unicycle 의
  relative-degree 문제 해소 — `p_l = p + l·[cosθ, sinθ]`,
  `h = ‖p_l − p_o‖² − d_safe²`, `ḣ = 2Δ·(J(θ)u − v_o) ≥ −α·h`
  (J(θ) 가 (v,ω) 에 대해 full-rank → QP 가 control-affine)
- **obstacle velocity feedforward**: scripted schedule 의 finite-difference —
  cbfkit 의 time-varying barrier 대응
- **QP**: `min ‖u − u_mppi‖² s.t. a_i·u ≥ b_i, u ∈ box` — 2D 이므로
  active-set 전수조사 (unconstrained / 단일 constraint / pair 교점) 로
  의존성 없이 정확해. cbfkit 의 fast QP 는 참조만 (JAX 전용)
- **nominal pluggable**: `nominal="stock_mppi" | "risk_mppi"` — cbfkit 의
  planner/nominal 분리 그대로. representation (BEV) 과 안전 (CBF) 의
  **합성이 곧 우리 논지**: representation 이 성능을 올리고 CBF 가 하한을 보증

한계 (v0, 문서화): 우리 plant 는 accel-limited (kinematic CBF 가정과 mismatch)
→ margin 으로 흡수. infeasible QP 는 최소 위반 fallback.

---

## 관련

- [`mppi_sandbox.md`](mppi_sandbox.md) — controller 등록 위치 + 실측
- [`safe_control_harness.md`](safe_control_harness.md) — CBF 계열 1번째 ref
- [`scenarios_and_controllers.md`](scenarios_and_controllers.md) — 8-controller 매트릭스
- [`decisions.md`](decisions.md) D-014 (CVaR routing) / D-013 (k·σ margin)

_2026-07-11 KST_
