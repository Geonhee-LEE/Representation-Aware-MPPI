# Dynamic-obstacle 시나리오 분류 + 제어기법 비교

> "어떤 시나리오에서 어떤 controller 가 잘 동작하나" — 명시 매트릭스.
> [`docs/dynamic_obstacles_uncertainty_track.md`](dynamic_obstacles_uncertainty_track.md) §2 의 D1-D4 stage 를 시나리오 차원으로 풀어쓴 동반 문서.

---

## 1. 시나리오 분류 (로봇 ego 기준 10종)

| ID | 이름 | 상대 운동 | 폐쇄성 | 반응성 | freezing 위험 |
|---|---|---|---|---|---|
| S01 | **Stationary cluster** | 정지 | 낮음 | n/a | 낮음 |
| S02 | **Head-on (정면 접근)** | $-v_{ego}$ 방향 접근 | 중간 | 보통 | 높음 |
| S03 | **Crossing (직각 횡단)** | $\perp v_{ego}$ | 중간 | 보통 | 중간 |
| S04 | **Robot overtaking** (느린 obstacle 추월) | $+v_{ego}$ 같은 방향, 느림 | 낮음 | n/a | 낮음 |
| S05 | **Overtaken by obstacle** (추월당함) | $+v_{ego}$ 같은 방향, 빠름 | 낮음 | 보통 | 낮음 |
| S06 | **Cut-in (끼어듦)** | $\perp$ → $+v_{ego}$ 전환 | 중간 | 빠름 | 중간 |
| S07 | **Tailgating (뒤따라옴)** | $+v_{ego}$ 일정 거리 유지 | 낮음 | n/a | 낮음 |
| S08 | **Convoy / Group** | 동시 + 패턴 (선형 / 군집) | 높음 | 보통 | 중간 |
| S09 | **Freezing trigger (좌우 동시)** | 좌우 양쪽 동시 접근 | 높음 | 보통 | **매우 높음** |
| S10 | **Surprise / Emergency** | 가려진 곳 갑작스러운 등장 | 가변 | 빠름 | 높음 |

차원 정의:
- **상대 운동**: ego frame 기준 obstacle 속도 벡터
- **폐쇄성**: 회피 가능 공간의 좁음 (cafe 좁은 통로 = 높음)
- **반응성**: obstacle 이 ego 행동에 반응하는 정도 (scripted = n/a, SFM = 보통, reactive RL = 높음)
- **freezing 위험**: robot 이 정체될 가능성 (DRA-MPPI 논문 명시)

---

## 2. 제어기법 비교 매트릭스 (10 시나리오 × 8 controller)

각 셀: 적합성 ★★★ (강함) / ★★ (적합) / ★ (약함) / ❌ (실패 가능) / **?** (검증 필요)
모두 가설 — Phase D3 ablation (#34) 으로 채울 ground truth.

| Controller \ Scen | S01 | S02 | S03 | S04 | S05 | S06 | S07 | S08 | S09 | S10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **Nav2 ObstaclesCritic** (baseline) | ★★ | ★ | ★★ | ★★★ | ★★ | ★ | ★★ | ★ | ❌ | ❌ |
| **Nav2 + STVL** (3D voxel) | ★★ | ★★ | ★★ | ★★★ | ★★ | ★ | ★★ | ★★ | ❌ | ★ |
| **C3BF** (collision cone) | ★★★ | ★★ | ★★ | ★★★ | ★★ | ? | ★★ | ★ | ❌ | ? |
| **DPCBF** (#33) | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ | ★★ | ★★ | **★★★** | ★★ | ? |
| **DRA-MPPI** (Monte Carlo prob) | ★★ | ★★ | ★★★ | ★★★ | ★★ | ★★ | ★★ | ★★★ | **★★★** | ★★ |
| **DualGuard MPPI** (HJ filter) | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ | ★★ | ★★ | ★★ | ★★ | ★★★ |
| **CFM-MPPI** (multimodal prior) | ★★ | ★★ | ★★★ | ★★ | ★★ | ★★★ | ★★ | ★★★ | ★★ | ★★ |
| **DR-MPC** (RL residual) | ★★ | ★★ | ★★ | ★★ | ★★ | ★★ | ★★ | ★★ | ★★ | ★★ |

### 매트릭스 해설 (가설 근거)
- **DPCBF S08 ★★★**: 논문이 100 obstacle 까지 검증 — group / convoy 시나리오 최강
- **DRA-MPPI S09 ★★★**: 논문이 명시적으로 "freezing robot problem 해결"
- **DualGuard S10 ★★★**: HJ reachability 가 OOD / 돌발 surprise 에 strict safety 보장
- **CFM-MPPI S06 ★★★**: multimodal prior 가 cut-in 의 양쪽 회피 옵션 동시 sampling
- **ObstaclesCritic S09 ❌**: hard-margin only → 좌우 동시 접근 시 frozen
- **C3BF S09 ❌**: collision cone infeasibility (DPCBF 가 해결하려는 정확한 문제)

---

## 3. 시나리오별 success criterion (PRD § 5 보강)

각 시나리오 의 정량 metric (PRD § 1 의 "완벽" 임계 + 시나리오별 추가):

| Scen | 시나리오 특화 metric | 임계 (가설) |
|---|---|---|
| S01 | path tracking (cte_rms) | ≤ 0.2 m |
| S02 | min-distance-to-obstacle | ≥ 0.5 m |
| S03 | yield decision time (yield/proceed) | ≤ 1.0 s |
| S04 | overtake clearance | ≥ 0.5 m, 추월 완료 ≤ 15 s |
| S05 | lateral displacement during overtake | ≤ 0.3 m |
| S06 | cut-in detection latency | ≤ 0.5 s |
| S07 | inter-vehicle distance variance | ≤ 0.2 m² |
| S08 | 통과 시간 vs solo baseline | ≤ 1.5× |
| S09 | **goal_reached = 1 (no freeze)** | required |
| S10 | reaction-to-stop time | ≤ 0.3 s (CBF 가 활성화되는 시점까지) |

S09 의 `goal_reached` 은 binary — frozen 으로 timeout 면 0.

---

## 4. 우리 sim 에서 어떻게 생성하나

### 옵션 A: Gazebo actor waypoint 패치 (scripted)
- `worlds/cafe3_jazzy.sdf.xacro` 의 `<actor><script><trajectory>` waypoint 수정
- 장점: 우리 기존 Gazebo + Nav2 + run_metrics 스택 그대로
- 단점: scripted → 반응 X. S10 (surprise) 제외 모두 가능

### 옵션 B: safe_control offline (Python)
- `refs/safe_control/dynamic_env/main.py` 의 obstacle 정의 수정
- 장점: 초 단위 iteration. controller (CBF/DPCBF/DRA-MPPI) 변경도 빠름
- 단점: ROS 외부 — `eval.run_metrics` 와 별도 path

### 옵션 C: HuNav / SFM (반응형)
- P4 본격 도입. 보행자가 robot 에 반응
- 장점: S05/S06/S09 같은 reactive 시나리오 가능
- 단점: 추가 setup (RVO2/HuNav)

### 권장: **A + B 동시**
- A 로 우리 Gazebo Nav2 stack 평가 (real metric)
- B 로 controller 후보 빠른 ablation (DPCBF/DRA-MPPI/DualGuard 비교)
- 두 결과 cross-validation → C 는 P4 본격에서

---

## 5. 평가 우선순위 (D3 stage 의 작업 분할)

| 우선 | 시나리오 | 이유 |
|---|---|---|
| 1 | S03 Crossing | 가장 흔함, baseline ★★ — 비교에 의미 |
| 2 | S02 Head-on | freezing 위험 + DPCBF 우월성 검증 |
| 3 | S09 Freezing trigger | **결정적 시나리오** — DRA-MPPI 의 가치 입증 |
| 4 | S08 Convoy | DPCBF 100-obstacle 주장 검증 |
| 5 | S06 Cut-in | CFM-MPPI multimodal 가치 검증 |
| 6 | S10 Surprise | DualGuard HJ reachability 검증 |
| 7 | S01/S04/S05/S07 | baseline pass 의 sanity check |

각 시나리오 yaml 정의 + safe_control 매핑 + Gazebo actor 매핑 → 별도 issue.

---

## 6. 새 시나리오 yaml 정의 (이번 commit 에 4개 추가)

| 파일 | 시나리오 | 매핑 |
|---|---|---|
| `eval/scenarios/cafe_head_on_v0.yaml` | S02 | 기존 actor 1명 trajectory 패치 |
| `eval/scenarios/cafe_crossing_v0.yaml` | S03 | 이미 `cafe_obstacle_crossing_v0` 존재 — refactor |
| `eval/scenarios/cafe_freezing_v0.yaml` | S09 | 좌우 동시 접근 actor 2명 신규 |
| `eval/scenarios/cafe_cut_in_v0.yaml` | S06 | actor 1명 직각 → 진행방향 전환 |
| `eval/scenarios/cafe_convoy_v0.yaml` | S08 | actor 5명 선형 patrol |

각 yaml 에 `acceptance:` 블록 추가 — § 3 의 시나리오 특화 metric 임계.

---

## 7. open question

- **메트릭 가중치**: S03 의 yield-decision-time vs S09 의 goal_reached binary — 어느 쪽 더 중요? PRD § 5 에 추가 가중치 정의 필요.
- **반응성 측정**: scripted vs SFM vs RL obstacle 의 "반응성 등급" 정량화 가능한가?
- **시나리오 합성**: 단일 시나리오 평가 + 합성 시나리오 (예: S02→S08 전환) — 합성 metric 어떻게?
- **OOD**: 학습한 distribution 밖 — 학습된 controller 가 fail 하는 점부터 새 시나리오로 promote

---

_이 문서는 사람이 갱신. 새 controller / 시나리오 추가 시 §1, §2, §6 표에 한 행._
_2026-05-27 KST_
