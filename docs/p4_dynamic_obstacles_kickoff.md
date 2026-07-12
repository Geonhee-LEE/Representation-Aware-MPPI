# P4 Dynamic Obstacles Kick-off Spec

> Phase 4 (2026-07-10 ~ 2026-08-06, ~4 weeks). Goal: MPPI 가 moving-obstacle 환경에서
> 안정적으로 물체회피를 하고 그 성능을 dynamic risk channel 이 설명한다.

---

## 1. North-Star Alignment

North-star "물체회피 완벽": **static + dynamic + 다중 + 가까운 + 가려진 + 의외** — 모든 클래스.

P3 까지는 static risk field (obstacle distance, epistemic/aleatoric uncertainty)를 MPPI critic
에 공급하는 구조를 설계했다. P4 는 moving obstacle 을 실시간으로 예측하고 그
예측 분포를 **dynamic risk channel** 로 MPPI 에 주입하는 것이 핵심이다.

---

## 2. D-Stage 점진 계획 (from `dynamic_obstacles_uncertainty_track.md`)

| Stage | 내용 | 선행 | P4 위치 |
|---|---|---|---|
| D1 | Gazebo + scripted 5 actors + Nav2 ObstaclesCritic | 완료 (baseline) | start |
| D2 | DPCBF critic (infeasibility 해결, 100 obs 검증) | issue #33 (in-progress) | P4 Week 1-2 |
| D3 | DRA-MPPI / DualGuard / SocialNav-Map 3-way ablation | D2 baseline 필요 | P4 Week 2-3 |
| D4 | 반응형 보행자 (HuNav/SFM — 우리 controller 에 반응) | D2/D3 | P4 Week 3-4 |

D2 는 P4 시작과 함께 가장 먼저 풀어야 할 코드 TODO. **P2 build-path (#44→#45→#23)
merge 가 선행 조건**이다. 코드가 없는 동안은 doc lane (D-stage spec 보강, 시나리오
YAML 초안, research TODO 생성) 으로 병렬 진행.

---

## 3. Dynamic Risk Channel 아키텍처

```
Sensor (LiDAR/camera)
  │
  ▼
Obstacle Tracker  ──►  Per-agent pose+velocity history
  │
  ▼
Prediction Model  ──►  p(x_t | history)   ← I²Former 또는 Gaussian linear
  │                    (trajectory distribution)
  ▼
Dynamic Risk Field  ─►  BEV grid (W, H) with per-cell collision probability
  │
  ▼
MPPI Critic (DynamicRiskCritic)  ──►  cost += α · risk(x_rollout[t])
```

### 3.1 Prediction Model 후보

| 모델 | 메커니즘 | Feed 근거 | 복잡도 | 비고 |
|---|---|---|---|---|
| **Gaussian linear (baseline)** | 등속 선형 예측 + Gaussian 오차 분포 | — | 낮음 | P4 Week 1 프로토타입 |
| **DRA-MPPI MC aggregate** | Monte Carlo 보행자 prediction → collision probability | 피드 2506.21205 | 중간 | D3 비교 후보 |
| **I²Former (iCrowdNav)** | pose-driven cross-attention → intent prediction | 피드 2606.26047 | 높음 | P4 Week 3+ (D4) |
| **DUCCT-MPPI dual** | UT localization uncertainty + MC prediction uncertainty | 피드 2605.28330 | 높음 | P5 평가 후보 |

**초기 목표**: Gaussian linear baseline 으로 dynamic risk field 파이프라인을 완성하고
MPPI critic 에 연결한다. 이후 DRA-MPPI MC → I²Former 순으로 예측 모델 교체.

### 3.2 DUCCT-MPPI 이중 불확실성 통합 노트

DUCCT-MPPI 는 (1) Unscented Transform 으로 로봇 pose uncertainty 를 propagate 하고
(2) MC aggregation 으로 보행자 예측 uncertainty 를 propagate 하여 두 arm 을 단일
MPPI chance-constraint cost 에 통합 (+28% success vs MC-MPPI baseline).

P4 에서 localization arm 을 바로 구현하기보다 **DRA-MPPI MC arm 을 먼저 검증**하고,
P5 σ-calibration harness 확장 시 UT localization arm 을 추가하는 순서를 권장.
이유: UT arm 은 AMCL particle filter 의 multi-modal 분포를 Gaussian 으로 근사하는
단순화가 필요하므로 별도 검증 cycle 이 필요.

---

## 4. Gazebo 동적 장애물 설정 옵션

### 4.1 현재 상태 (Stage D1)

`src/representation_aware_mppi_bringup/worlds/` 의 cafe/small_city 에
scripted Gazebo actor 5명 사용 중. 행로가 하드코딩 → 반응 없음.

### 4.2 Stage D2/D3 목표: PedSim 또는 HuNav

| 옵션 | 특징 | 난이도 | 추천 |
|---|---|---|---|
| **Gazebo scripted actor (현행)** | 고정 경로, 단순 | 완료 | Stage D1 baseline |
| **HuNav (ROS2 plugin)** | Social Force Model, 반응형, ROS2 Jazzy 포트 존재 | 중간 | Stage D3/D4 ★ |
| **PedSim_ros2** | SFM 기반, Gazebo Sim Harmonic 아직 불완전 | 높음 | 차선 |
| **NavIsaacLab 방법론 차용** | trajectory-diffusion + adversarial motion (Isaac Lab) | 매우 높음 | P5 평가용 아이디어 차용 |

**추천**: HuNav ROS2 플러그인을 Stage D3/D4 에서 사용. Stage D2 DPCBF critic
테스트는 scripted actor 5명으로도 충분.

### 4.3 NavIsaacLab 방법론 활용 전략

NavIsaacLab (피드 2606.26265) 은 Isaac Lab 기반이라 직접 포팅은 큰 sim-stack 결정.
다음 두 가지를 **방법론만** 차용한다:
1. **crowd-generation taxonomy** (density 단계: 5 → 10 → 20 actors) — Gazebo 시나리오
   YAML 에 반영해 per-density success-rate 곡선 생성
2. **cross-scale benchmark 분류** (narrow corridor / open plaza / mixed) — P5
   evaluation 시나리오 taxonomy 에 추가

---

## 5. iCrowdNav I²Former 통합 계획 (Stage D4 후보)

### 핵심 아이디어

iCrowdNav (피드 2606.26047) 의 **I²Former** — pose-driven cross-attention module:
- 입력: 각 보행자의 recent pose history
- 출력: predicted trajectory distribution (where the pedestrian intends to go)
- 이 distribution 을 dynamic risk field 에 반영 → intention-aware dynamic cost

### P4 에서의 통합 위치

```
boostDynamicRisk(agent) {
  intention_dist = I2Former(agent.pose_history)   // P4 D4
  // vs.
  intention_dist = linear_gaussian(agent.vel)      // P4 D2 baseline
  
  cost += integrate(p_collision | intention_dist, rollout_traj)
}
```

### 구현 전제

- I²Former 는 RL 정책과 분리 가능한 **모듈** — the RL policy itself is NOT borrowed
- 학습 데이터: NavIsaacLab crowd-sim 방법론 또는 ETH–UCY 공개 pedestrian trajectory
  dataset 으로 offline 학습
- P2 build-path merge 가 선행 필수; 그 후 `learning/` 아래 I²Former 모듈 scaffold

---

## 6. P4 초기 TODO Seeds

아래 TODO 들은 next executor cycles 에서 Notion 에 생성할 후보들.
(Notion MCP grant 대기 중 — MCP 허가 시 즉시 생성)

| # | Title | Owner | Priority | Phase | 비고 |
|---|---|---|---|---|---|
| P4-T01 | DPCBF Stage B: nav2_mppi critic prototype (Python) | claude | P0 | P4 | P2 merge 선행 필요 |
| P4-T02 | Gazebo dynamic scenario YAML v1 (5/10/20 actor density) | claude | P1 | P4 | scripted actors, no P2 dep |
| P4-T03 | Dynamic risk channel baseline: Gaussian linear prediction → BEV grid critic | claude | P1 | P4 | P2 merge 선행 필요 |
| P4-T04 | DRA-MPPI MC collision probability critic — P4 D3 ablation candidate | claude | P1 | P4 | P2 merge 선행 필요 |
| P4-T05 | HuNav ROS2 plugin integration study + install test in Jazzy | claude | P2 | P4 | no P2 dep |
| P4-T06 | [research] I²Former intention predictor module scaffold for dynamic risk channel | claude | P2 | P4 | P2 merge + D3 선행 |

---

## 7. P2 Build-Path 의존성 정리

아래 코드 TODOs 는 **모두 P2 build-path (#44→#45→#23) merge 후에만 실행 가능**:
- P4-T01, P4-T03, P4-T04, P4-T06

P2 merge 전 실행 가능한 P4 TODO:
- P4-T02 (Gazebo scenario YAML — world 파일/config 만 수정)
- P4-T05 (HuNav study — doc/install test, src/ 변경 없음)

따라서 **P2 merge 전 P4 executor 가 먼저 집중할 영역 = D-stage doc + 시나리오 YAML**.

---

## 8. 평가 기준 (P4 done 조건)

P4 완료 기준은 P5 정량 harness 수행 전에 다음이 만족되어야 한다:

1. **D2 완료**: DPCBF critic 이 café 시나리오에서 5명 scripted actor 를 안정적으로
   회피 (시각 확인 + no collision in 5 runs)
2. **D3 ablation 비교**: DRA-MPPI vs DPCBF 두 방식의 비교 결과 journal entry 1건
3. **Dynamic risk channel 파이프라인**: Gaussian linear prediction → BEV grid → MPPI
   critic hook 이 빌드 성공하고 sim 에서 topics flow 확인
4. **Stage D4 candidate**: HuNav reactive pedestrian 이 Gazebo 에서 동작 확인
   (또는 technical limitation 명시)

---

## 9. Research 참고 문헌 (이 킥오프와 관련 feed entry 링크)

| Paper | Feed date | 관련 | 활용 |
|---|---|---|---|
| iCrowdNav (I²Former) | 2026-07-06 | D4 의도 예측 | I²Former pedestrian intent predictor for dynamic risk channel |
| DUCCT-MPPI | 2026-07-07 | D3/D4 uncertainty | UT localization + MC prediction dual arm; proper scoring rules |
| NavIsaacLab | 2026-07-04 | P4/P5 crowd sim | crowd-gen taxonomy + cross-scale benchmark taxonomy |
| DRA-MPPI (2506.21205) | (prior) | D3 ablation | MC collision probability as dynamic MPPI cost |
| FCP-MPC (2607.00776) | 2026-07-04 | P3/P4 | conformalized distance field as tightened sampler constraint |
| Rethinking-Gaussian (2603.10407) | (prior) | D3 | recalibrated covariance baseline for pedestrian prediction |

---

_Generated: 2026-07-09 00:02 KST · autoresearch/p4-dynamic-obstacles-kickoff_
_Next manual update: when D2 (DPCBF Stage B) starts or P2 merges_
