# Dynamic Obstacles + Uncertainty — 통합 R&D Track

> 사용자 명시 관심: **동적 장애물 + 불확실성**. north star "perfect avoidance + tracking in **all** envs" 의 두 핵심 axis.
> 이 문서는 research feed 의 관련 14+ entry 를 단일 트랙으로 묶어 우선순위 + 의존성 + 통합 단계를 명시.

---

## 1. 두 axis 의 관계

```
                        ┌─────────────────────────┐
                        │   North Star            │
                        │ "all envs, perfect"     │
                        └────────┬────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                ▼                                  ▼
       ┌──────────────────┐              ┌──────────────────┐
       │ Dynamic obstacle │              │  Uncertainty     │
       │   avoidance      │              │ quantification   │
       │ (보행자/차량/돌발)│              │ (epi/ale 분리)   │
       └────────┬─────────┘              └─────────┬────────┘
                │                                  │
                └──────────────┬───────────────────┘
                               ▼
                   ┌────────────────────────┐
                   │ Risk-aware MPPI cost   │
                   │ (P3-P4 critic plug)    │
                   └────────────────────────┘
```

두 axis 는 **risk-aware MPPI cost** 라는 단일 출구를 공유 — 동적 obstacle 의 *위치/속도 분포* 가 곧 *불확실성* 의 표현 형태. 따라서 별개 thread 가 아니라 1개 통합 cost 구조의 2 입력원으로 본다.

---

## 2. 동적 장애물 thread — 4단 점진

### Stage D1. 충돌 회피 baseline (현재)
- 현존: Gazebo + 5 scripted actors + Nav2 ObstaclesCritic + 2D scan
- 한계: scripted 만 (반응 X), Nav2 hard-margin (probabilistic X)
- 거리: north star 까지 매우 멈

### Stage D2. **DPCBF 통합** (issue #33, 진행 중)
- 동적 obstacle 회피 의 infeasibility failure 해결
- 100 obstacle 까지 검증된 method
- Stage A: offline char (Python) → Stage B: nav2_mppi critic prototype → Stage C: C++ port

### Stage D3. **DRA-MPPI / DualGuard / SocialNav-Map 비교** (issue 신규 예정)
- DRA-MPPI: Monte Carlo collision probability → soft cost (hard reject 아님)
- DualGuard: HJ reachability + MPPI 양쪽 safety filter
- SocialNav-Map: 동적 occupancy map (prediction → planner 입력)
- 셋 다 동적 obstacle 처리 다른 각도 — 우리 시나리오에서 ablation 비교

### Stage D4. **반응형 보행자 (HuNav/SFM)** (P4 본격)
- 현 scripted actor → social-force model 보행자 (반응)
- 우리 controller 의 영향에 따라 obstacle 행동도 바뀜
- 진짜 north star 시나리오

---

## 3. 불확실성 thread — 5채널 + 정량화

### 채널 (P3 spec, taxonomy)
| 채널 | 종류 | 출처 | 측정 가능 시점 |
|---|---|---|---|
| static | aleatoric | 정적 occupancy noise | P1 BEV semseg pixel 가변성 |
| dynamic | aleatoric | obstacle motion noise | tracker covariance |
| traversability | aleatoric | terrain variance | semantic seg confidence |
| epistemic | epistemic | model OOD | MC dropout + ensemble disagreement |
| aleatoric | aleatoric (residual) | task-irrelevant noise | predictive variance head |

### 정량화 reference (feed 정리)
- **SCOPE** (Xie & Dames 2024) — stochastic occupancy prediction, 89× faster, 분포 출력
- **TRAIL** (Jia/Li/How 2026) — INR terrain traversability 연속 표현
- **Deep Prob Traversability** (Nature Sci. Rep. 2026) — 학습 + test-time adaptation
- **Sensitivity Tubes Robust MPPI** (2026) — parameter 불확실성 vs MPPI 견고화
- **Disentangling Uncertainty** (IROS 2025) — epi/ale/predictive 명확 분리
- **Socially Aware Risk Adaptation** (2506.14305) — online dual-level filter

### 통합 단계
- Stage U1. 5채널 spec (issue 이미 #29 의 한 부분, refactor)
- Stage U2. 단일 채널 (`static`) prototype + RViz overlay
- Stage U3. 모든 5채널 + MPPI critic 가중치 매트릭스
- Stage U4. OOD test-time adaptation (sim → real-ish noise)

---

## 4. 의존성 + 권장 순서

```
P0 sim ground truth ──┐
                       ├──► Stage D2 (DPCBF #33) ──► Stage U2 (static channel proto)
                       │                                       │
P1 BEV semseg ─────────┤                                       ▼
                       │                              Stage D3 (DRA-MPPI/Dual ablation)
                       └──► Stage U1 (5채널 spec) ──► Stage U3 (5채널 + 가중치 매트릭스)
                                                              │
                                                              ▼
                                                Stage D4 (HuNav 반응형) + Stage U4 (OOD TTA)
                                                              │
                                                              ▼
                                                P5 정량 ablation (#16 4-way + DPCBF + DRA-MPPI)
```

병렬 가능:
- **D2 (DPCBF)** 와 **U2 (static channel proto)** 동시 진행 가능 (의존성 없음)
- **D3 ablation 비교** 는 D2 완료 후 (baseline 필요)

---

## 5. 단기 목표 (다음 2 주, P0/P1 wrap-up 와 병행)

| # | 작업 | issue | priority |
|---|---|---|---|
| 1 | DPCBF Stage A (offline char) | #33 | P0 |
| 2 | 동적 obstacle handling 3-way 비교 spec (DPCBF vs DRA-MPPI vs DualGuard) | 신규 | P1 |
| 3 | 불확실성 5채널 v0 spec doc | 신규 | P1 |
| 4 | DyObAv-MPCnWTA warehouse 코드 clone + 우리 시나리오 비교 평가 | 신규 | P2 |
| 5 | Socially Aware Risk Adaptation (2506.14305) 의 dual-level filter 수식 발췌 → P3 critic 가중치 schedule 후보 | 신규 | P1 |

---

## 6. 성공 지표 (PRD § 5 보강)

기존 PRD 의 obstacle metric (collision 0%, near-miss < 1/run) 외 추가:

- **per-pedestrian-density**: actor 5 → 10 → 20 단계별 success rate degradation 곡선
- **uncertainty calibration**: epistemic uncertainty 가 OOD 환경에서 ↑, in-distribution 에서 stable (ECE/MCE)
- **failure-mode 분류** (issue 별도 backlog 에 이미 있음): timeout / collision / stuck / diverged / off-path 비율

---

## 7. open question (아직 답 없음)

- 5채널 가중치를 **사용자 튜닝 vs 학습 vs 환경별 lookup** 어느 것?
- DPCBF 의 parabola 파라미터 (vertex, curvature) 를 environment context (BEV) 에서 학습할 수 있나?
- HuNav 보행자 + DPCBF safety filter — 정상 종료 (deadlock 없음)?
- TRAIL INR 의 미분 가능성 + MPPI critic gradient 결합 — 메모리/속도 trade-off?

이 질문들은 cycle 진행 중 답 채워가고, 별도 doc 으로 분기.

---

## 8. 갱신

이 문서는 사람이 manual update. 새 reference paper 추가 시 §2/§3 적절한 slot 에 한 줄 추가. 단 stage 정의 자체가 바뀌면 별도 commit + Telegram 알림.

_Last manual update: 2026-05-26 KST_
