# Environment Taxonomy v0

> 본 문서는 north-star ("모든 환경에서 물체회피 + 경로추종을 완벽하게 수행")
> 의 **"모든 환경"** 을 정의하기 위한 v0 분류표다. P5 평가 단계에서 환경별
> 성공률을 묶어 보고하기 위한 좌표축 역할을 한다.
>
> 의도적으로 단순하게 시작한다. P3–P5 진행하면서 실제 실패 모드가 구체화되면
> 축을 추가하거나 클래스를 쪼갠다. 본 v0 의 핵심 약속:
>
> 1. 모든 시뮬 world / rosbag 은 한 클래스에 속한다 (다중 라벨 허용).
> 2. 모든 평가 결과는 클래스별 분리해서 본다 (집계 평균 금지).
> 3. 클래스 정의가 흔들리면 해당 결과는 v0 라벨링 시점으로 회귀한다.

---

## 1. 분류 축

직교 4축. 한 world 는 각 축에서 한 값을 가진다.

| 축 | 값 | 정의 |
|---|---|---|
| **Space** | `narrow` / `open` / `mixed` | 자유 공간 너비. `narrow` = 평균 통로 폭 ≤ 2 m, `open` = ≥ 5 m, `mixed` = 둘 다 포함. |
| **Crowd** | `static` / `light` / `dense` | 동시에 활동 중인 보행자/이동체 수. `static` = 0, `light` = 1–4, `dense` = ≥ 5. |
| **Visibility** | `clear` / `occluded` / `degraded` | 센서 가시성. `clear` = 직선거리 무장애, `occluded` = 코너/장애물 뒤 가림 흔함, `degraded` = 노이즈/저조도/동적 폐색. |
| **Terrain** | `flat` / `rough` / `slope` | 지면 곡률·경사. `flat` = 거의 평평, `rough` = 잔디/비포장, `slope` = ≥ 5° 경사 또는 다층 (계단 제외). |

> Terrain 은 wheeled 로봇 가정에서 traversability 채널 (P3) 의 평가축이 된다.
> 계단/엘리베이터 등 비연속 토폴로지는 v0 범위에서 제외.

---

## 2. 클래스 (분류 축 조합으로 자주 등장하는 묶음)

각 클래스는 north-star 평가 시 **하나의 보고 행**이 된다.

### A. `indoor-narrow` (좁은 실내, 정적/약간 dynamic)
- Space=`narrow`, Crowd∈{`static`,`light`}, Visibility∈{`clear`,`occluded`}, Terrain=`flat`.
- 예시 world: `jackal_cafe.launch.py` (cafe3).
- 핵심 챌린지: 코너 occlusion, 좁은 통로의 경로추종 + 가까운 정적 장애물 회피, 보행자 마주침 시 yield.
- 대표 실패 모드: 코너 oversteer, dead-end 미감지, 좁은 통로 oscillation.

### B. `outdoor-open` (개방 실외, 정적)
- Space=`open`, Crowd=`static`, Visibility=`clear`, Terrain∈{`flat`,`rough`}.
- 예시 world: `jackal_outdoor_sim.launch.py world:=city` (보행자 0 모드), small_city 도로/광장 구간.
- 핵심 챌린지: 장거리 경로추종 (cross-track 누적), traversability (잔디/연석/포장의 차이), 멀리 있는 정적 장애물 우회.
- 대표 실패 모드: 곡선 도로 cross-track drift, 비포장 경계 오인.

### C. `outdoor-crowd` (실외 dense, 동적 보행자 군집)
- Space=`open`, Crowd=`dense`, Visibility∈{`clear`,`occluded`}, Terrain=`flat`.
- 예시 world: small_city + crosswalk/plaza/diagonal 5인 actor 패턴.
- 핵심 챌린지: 다중 동적 객체 예측, 군집 통과 시 social compliance, 횡단보도 yield.
- 대표 실패 모드: deadlock (양보 무한반복), freezing robot problem, 군집 사이 잘못된 틈으로 진입.

### D. `mixed-cluttered` (좁은 실내 + dense, 좁은 통로 보행자 마주침)
- Space=`narrow`, Crowd∈{`light`,`dense`}, Visibility=`occluded`, Terrain=`flat`.
- 예시 world: `tb3_sandbox_pedestrians`, cafe3 + actors.
- 핵심 챌린지: 좁은 공간에서 동적 회피 (옆/뒤 후퇴 옵션 부족), occluded 보행자 갑자기 등장.
- 대표 실패 모드: 정면 충돌 직전 정지, 통로 중앙 점거, swept volume 과소예측.

### E. `outdoor-degraded` (센서 열화, real-world rosbag)
- Space=any, Crowd=any, Visibility=`degraded`, Terrain=any.
- 예시 source: 실 환경 rosbag (LiDAR 노이즈, 카메라 저조도/HDR, IMU drift).
- 핵심 챌린지: 표현(representation) 의 epistemic uncertainty 처리, sensor dropout robustness.
- 대표 실패 모드: occupancy hallucination, semseg 라벨 swap, traversability 과신.

> 클래스 v0 은 5 개. P3 진입 후 epistemic/aleatoric 채널 도입 시 E 를 둘로 쪼갤 가능성이 크다.

---

## 3. 현 repo world ↔ 클래스 매핑

| World / launch | Space | Crowd | Visibility | Terrain | 클래스 |
|---|---|---|---|---|---|
| `cafe3_jazzy.sdf.xacro` (jackal_cafe.launch.py) | narrow | light (5 actors) | occluded | flat | A / D |
| `small_city.sdf.xacro` (jackal_outdoor_sim, world=city) | mixed | dense (5 actors) | clear | mixed (rough+slope) | B / C |
| `tb3_sandbox_pedestrians.sdf.xacro` | narrow | dense | clear | flat | D |
| (미관측) real-world rosbag | TBD | TBD | degraded | TBD | E |

> 실제 cafe3 보행자가 5명이라도 좁은 통로 공유라면 D 로 분류하는 게 더 정확하다. 라벨링은 평가 harness 구현 시 확정.

---

## 4. P5 평가 harness 와의 계약

P5 에서 quantitative metric harness 가 들어오면, 매 episode 결과는 다음 라벨을 기록한다:

```
{episode_id, class∈{A,B,C,D,E}, axes:{space, crowd, visibility, terrain}, success, near_miss, cross_track_rms, time_to_goal}
```

집계 보고는 **클래스별로 분리**한다 (`success_rate@A=…, success_rate@B=…`). 평균 단일 숫자로 묶지 않는다 — north-star 기준 "모든 환경" 의 정의 자체가 클래스별 lower bound 이기 때문이다.

---

## 5. v0 한계 (의도적)

- 좌표축 4 개로 부족하면 추가 (예: 광량, 무게중심 변화). v0 은 sim+rosbag 분류에 충분.
- 야간/우천/눈 같은 weather 축은 Visibility=`degraded` 로 묶어 v0 단순화.
- swerve 전용 좁은 회전 같은 로봇 형상 의존 챌린지는 별도 robot taxonomy 에서 다룬다 (현 v0 은 환경만).
- "완벽" 의 임계값 (success_rate ≥ X) 은 본 문서가 아닌 P5 evaluation 문서가 정한다.

---

## 6. 다음 단계

- P3 진입 시 본 문서의 클래스를 risk/uncertainty 채널 평가의 axis 로 사용.
- P4 동적 시나리오 정의 (`Define dynamic-obstacle eval scenarios` TODO) 가 클래스 C/D 의 sub-시나리오를 채운다.
- P5 evaluation harness 가 본 분류를 코드 레벨 (`evaluation/class_label.py` 등) 로 박는다.
