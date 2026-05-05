# Research State — auto-generated each cycle

_Last updated: 2026-05-05 23:50 KST · cycle p1-path-tracking-metrics-v0_

## North star distance

P0 셋업 마무리. **정량 metric layer 등장 (cycle 1)** — `eval.path_tracking_metrics.summary()` 가 trajectory 당 9 scalar 반환 (cte/heading/completion/time/smoothness/goal). 단, **임계치는 가설** — 실 sim 데이터로 calibration 안 됨. 인터랙티브 sim 1차 시각 검증 미완 → 진짜 north-star 거리는 여전히 미측정. 6 phase 중 P0 마무리 + P1 prep 단계.

## Current bottleneck

여전히: **north-star ground truth 한 번 잡기** — Jackal cafe 또는 city 인터랙티브 sim 1회 시각 검증 + RViz 캡처 + (이제는) `eval.summary()` 적용으로 첫 baseline 숫자 확보. `User-blocked` (NeedsUserTest=true).

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p1-path-tracking-metrics-v0` | 2026-05-05 23:38 | qual:tests-17pass | 0 (PR #4 pending) |

## Recent learnings (last 3 cycles)

- **(cycle 1)** "User-blocked bottleneck → prep work 픽" 패턴은 EXECUTOR_SKIP 보다 효과적 — user 의 다음 액션 직후 진척 가능.
- **(cycle 1)** v0 metric 임계치는 가설이지만 **정의** 가 박히면 모든 후속 작업이 같은 언어로 말함. 통합 비용 ↓.
- **(bootstrap)** 5-phase loop 도입 전 5일간 pure infra 만 누적. 이번 cycle 부터 north-star 수직 진척 시작.

## Next 3 priorities (actionable)

1. **A1 — Sim 시각 검증** (user-blocked, NeedsUserTest=true): `ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py` 1회 실행 + RViz 토픽 흐름 확인 + 스크린샷 1장 + (PR #4 머지 후) `eval.summary()` 적용으로 첫 baseline.
2. **`eval/run_metrics.py` ROS2 노드 wrap**: `/odom + /plan` 구독 → run 당 dict 출력 → `runs/<run-id>.json`. v0 module 을 라이브 데이터에 연결. claude 자율 가능.
3. **시나리오 yaml v0** (`eval/scenarios/{straight,curved,figure8,obstacle_crossing}.yaml`): start/goal/world 명세. metric "어디서 측정" 부분 채움. claude 자율 가능.

## Cycles to date

- This cycle: **1** (5-phase loop 가동 후 첫 cycle)
- Project total: 1
