# mppi_sandbox — Python-native primary verification surface

`eval/mppi_sandbox/` 는 NumPy 만으로 도는 diff-drive 폐루프 sim. **auto-research
사이클과 CI 가 실제로 검증할 수 있는 유일한 주행 실행 표면** (D-016).
Gazebo + Nav2 는 sensor-driven BEV / sim2sim gap 확인용 occasional bench 로 강등.

설계 결정: [`decisions.md`](decisions.md) **D-016** (2026-07-11, user 결정).
패턴 참조: [tkkim-robot/safe_control](https://github.com/tkkim-robot/safe_control)
(numpy sim loop + pluggable safety controller — 코드 vendoring 아님, D-005 유지).

---

## 왜 필요한가

cron executor 는 Gazebo 를 못 돌린다 (GPU / 분 단위 startup / non-deterministic /
assertable outcome 없음). 그 결과 5주간 (D-012~D-015 era) spec 만 누적, 실행 코드 0.
sandbox 는 그 gap 을 닫는다:

| | Gazebo + Nav2 | mppi_sandbox |
|---|---|---|
| 한 run | ~분, GPU | **~2-5 초, CPU** |
| deterministic | ✗ | ✅ (seeded rng) |
| CI 가능 | ✗ (disabled) | ✅ `sandbox-ci.yml` ~1 min |
| controller | nav2_mppi (C++) | plug-in registry (Python) |
| scenario | 동일 `eval/scenarios/*.yaml` | 동일 yaml (launch: 키 무시) |
| 출력 | `runs/<id>.json` | **동일 schema** + sandbox 확장 필드 |

---

## 사용법

```bash
# 한 시나리오
python3 -m eval.mppi_sandbox.run eval/scenarios/cafe_head_on_v0.yaml \
    --controller stock_mppi --seed 0 --run-id head-on-001 --out-dir runs

# 테스트 (CI 와 동일)
python3 -m pytest eval/mppi_sandbox/tests/ -q

# 8-시나리오 매트릭스
for f in eval/scenarios/*_v0.yaml; do python3 -m eval.mppi_sandbox.run "$f" --out-dir runs; done
```

exit code: pass=0 / fail=1 → 쉘에서 바로 gate 가능.

---

## 구조

```
eval/mppi_sandbox/
├── dynamics.py         diff-drive kinematics (accel-limited), 단일/batch 겸용
│                       — sim plant 와 MPPI rollout 모델이 같은 함수 (v0: model=truth,
│                         P2 residual 작업이 이 등식을 의도적으로 깬다)
├── obstacles.py        circle obstacle: static + time-waypoint scripted
│                       (scenario yaml 의 dynamic_obstacles: 블록 그대로)
├── scenario.py         yaml loader — launch:/world: 키 무시, 물리 키만 소비
├── representations/
│   ├── __init__.py     RiskChannel IntEnum (D-012 canonical order)
│   └── gt_bev.py       GT BEV producer: (5,H,W) stack + bool mask,
│                       dynamic=예측 sweep smear, epistemic=occlusion shadow+range
├── critics/
│   └── risk_inflation.py  RiskInflationCritic (D-013): clip(k·σ, 0, Δ_max)
│                          tighten-only margin, k=0 → no-op
├── controllers/
│   ├── __init__.py     REGISTRY = {"stock_mppi", "risk_mppi", "cbf_mppi"}
│   ├── stock_mppi.py   pure-NumPy vanilla MPPI (Williams 2017), seeded
│   │                   + representation hook 2개 (_extra_margin/_extra_cost, 기본 no-op)
│   ├── risk_mppi.py    representation-aware: DYNAMIC 채널 → w_risk cost,
│   │                   EPISTEMIC 채널 → RiskInflationCritic margin
│   └── cbf_mppi.py     cbfkit 아키텍처: MPPI nominal (stock|risk pluggable)
│                       + CBF-QP safety filter (offset-point unicycle barrier,
│                       moving-obstacle velocity feedforward, 2D active-set QP)
├── run.py              폐루프 sim → runs/<id>.json (+acceptance 판정 + pass)
│                       --ctrl-arg w_risk=40 등 controller kwargs 전달
└── tests/              pytest 계약 — 새 controller 가 통과해야 할 gate
```

### Controller plug-in 계약

```python
class MyController:
    def __init__(self, scenario, seed=0, **kw): ...
    def command(self, state, t) -> np.ndarray:   # (5,) → (2,) [v_cmd, w_cmd]
```
등록 = `controllers/__init__.py` REGISTRY 한 줄 + tests/ 통과. 그게 전부.

### JSON 출력

`eval/run_metrics.py` (Gazebo 노드) 와 동일한 core schema
(`run_id/started_at/world/robot/target_speed/metrics{...}`) + sandbox 확장:
`backend/controller/seed/min_obstacle_clearance/collision/acceptance/pass`.
→ 두 백엔드 숫자가 같은 비교 테이블에 들어간다.

---

## v0 첫 실측 — stock_mppi × 8 시나리오 (2026-07-11, seed 0)

| scenario | pass | goal | cte_rms | clearance | 비고 |
|---|---|---|---|---|---|
| cafe-straight | ✅ | 1 | 0.009 | — | |
| cafe-obstacle-crossing | ✅ | 1 | 0.024 | — (yaml 에 obstacle 없음) | |
| cafe-freezing | ✅ | 1 | 0.022 | 0.56 | |
| cafe-convoy | ✅ | 1 | 0.030 | 0.42 | |
| city-curved | ✅ | 1 | 0.131 | — | |
| **cafe-head-on** | ❌ | 1 | 0.200 | **0.01** | graze — vanilla MPPI 는 hard-collision 만 피함 |
| **cafe-cut-in** | ❌ | **0** | 0.094 | 0.14 | **freezing**: ped 이 경로 위 (0,-3.8) 정지 → local minimum |
| **city-figure8** | ❌ | 1 | 0.028 | — | self-crossing 경로에서 v0 metric projection 오판 (metric 한계) |

**해석**: fail 3건이 곧 프로젝트의 존재 이유 — head-on graze 와 cut-in freezing 은
representation-aware 확장 (dynamic risk channel, D-013/D-014 critic) 이 개선해야 할
정량 baseline. figure8 은 controller 아닌 metric v0 한계 (run_metrics.md 한계 절 참조).

---

## 4-way controller 매트릭스 (2026-07-11, seed 0, clearance [m])

`risk_mppi` = stock + GT BEV 소비 (DYNAMIC w_risk=40, EPISTEMIC k=0 default).
`cbf_mppi` = cbfkit 아키텍처 — MPPI nominal + CBF-QP filter (margin 0.25, [`cbfkit_analysis.md`](cbfkit_analysis.md)).

| scenario | stock | risk | cbf(stock) | **cbf(risk)** | 비고 |
|---|---|---|---|---|---|
| convoy | 0.42 | 0.91 | 0.57 | **0.91** | |
| cut-in | 0.14 | 0.45 | 0.21 | **0.45** | clearance 해결, **goal=0 전원** (freezing — liveness 는 CBF 소관 아님) |
| freezing | 0.56 | 0.92 | 0.81 | **1.03** | |
| head-on | 0.01 | 0.18 | 0.20 | **0.24** | 조합이 최고 — representation(성능)+CBF(floor) 합성 실증 |
| obstacle 없는 4종 | = | = | = | = | filter 완전 투명 (pytest 로 byte-identical 보증) |

**Pareto (head-on)**: w_risk 0→clear 0.005/cte 0.20 · 40→0.185/0.28 · 60→0.242/0.302 ·
cbf margin 0.45+w60→0.394/0.388 · margin 0.55→0.463/0.470.
acceptance (clear≥0.40 **and** cte≤0.30) 는 lateral dodge 만으론 기하적으로 tight —
timing 이 정교한 yield 행동 필요 (S1 잔여: DPCBF / yield critic).

**k·σ (D-013) 실증**: head-on 에선 무효과 (가림이 로봇 corridor 밖 — 정직한 물리).
경로 위 static obstacle 의 shadow 기하에서 k=0→0.014, k=0.4→0.052 — ignorance 가
margin 을 사는 메커니즘 확인. 본격 검증엔 S10(가려진/surprise) 시나리오 yaml 필요.

**CBF 교훈 (accel-limited plant)**: kinematic CBF 가정 그대로면 h<0 침투 (clear 0.05).
QP box 를 1-step 도달가능 집합으로 조여 command≈realized 강제 → clear≈margin 회복.

---

## Verification 계약 (executor + CI)

1. 새 controller / representation / dynamics 코드 → sandbox plug-in + pytest 동반 필수
2. push 전 로컬: `pytest eval/mppi_sandbox/tests/ ...` (초 단위)
3. PR 마다 `.github/workflows/sandbox-ci.yml` 이 같은 suite + straight smoke run
4. metric 문자열: `sandbox:pass=N/M`, `sandbox:cte_rms=...` — `qual:*` 보다 우선

---

## 알려진 한계 (v0)

- **fidelity**: LiDAR occlusion / sensor noise / 접촉물리 없음 — 알고리즘 *순위* 비교가
  목적. physical realism 은 Gazebo bench 몫
- obstacle schedule 은 마지막 waypoint 에서 **hold** (Gazebo actor 는 loop 일 수 있음) —
  cut-in 결과 비교 시 유의
- 5채널 BEV 는 아직 stub 없음 — GT/synthetic BEV producer 가 다음 slice (issue 참조)
- model = truth (rollout 모델 == plant) — P2 residual 통합 시 의도적으로 분리

---

## 관련

- [`safe_control_harness.md`](safe_control_harness.md) — 외부 controller 비교 백엔드 (보조)
- [`run_metrics.md`](run_metrics.md) — Gazebo 쪽 동일 schema 노드
- [`scenarios_and_controllers.md`](scenarios_and_controllers.md) — 10×8 매트릭스의 컨트롤러 후보
- [`decisions.md`](decisions.md) D-016 — 이 표면의 결정 기록

_2026-07-11 KST_
