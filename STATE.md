# Research State — auto-generated each cycle

_Last updated: 2026-05-06 00:00 KST · cycle p1-eval-run-metrics-v0_

## North star distance

정량 metric layer 가 라이브 데이터에 닿을 수 있는 코드까지 도달 — `eval.path_tracking_metrics.summary()` (PR #4) + `eval/run_metrics.py` ROS2 wrapper (이 PR). `/odom + /plan` 구독 → `runs/<id>.json` 경로 확보. **그러나 sim 자체는 여전히 미실행** — 첫 baseline 숫자 0건. 도메인 측정은 0%, 인프라는 첫 sim 한 방이면 자동 산출 가능한 상태.

## Current bottleneck

여전히: **north-star ground truth 한 번 잡기** — Jackal cafe 인터랙티브 sim 1회 실행이 PR #4 + 이 PR 머지 직후에 가능. user-blocked (NeedsUserTest=true). 이번 머지로 첫 baseline JSON 자동 생성됨.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p1-path-tracking-metrics-v0` | 2026-05-05 23:38 | qual:tests-17pass | 1 (PR #4 pending) |
| `autoresearch/p1-eval-run-metrics-node` | 2026-05-06 00:06 | qual:tests-8pass | 0 (PR pending) |

## Recent learnings (last 3 cycles)

- **(이번 cycle)** Cross-PR dependency 는 lazy import + `@skipUnless` 로 깨끗이 격리 가능 — sim 직전 단계까지 실제로 진척시킬 수 있음. "user-blocked = stop" 아님.
- **(cycle 1, PR #4)** v0 metric 임계치는 가설이지만 *정의* 가 박히면 모든 후속 작업이 같은 언어로 말함. 통합 비용 ↓.
- **(이번 cycle)** ROS2 노드 코드를 factory function 안에 캡슐화하면 unit test 와 sim deploy 양쪽 모두 깨끗함.

## Next 3 priorities (actionable)

1. **`eval/scenarios/*.yaml` v0** (claude 자율): straight / curved / figure8 / obstacle_crossing 4종 — start, goal, world 명세. metric "어디서 측정" 못박음.
2. **`jackal_cafe.launch.py` 에 run_metrics 노드 옵션** (claude 자율): `include_run_metrics:=true` 플래그로 sim 실행과 동시 metric 수집. PR #4 + 이 PR 머지 후 즉시 가능.
3. **A1 — Sim 시각 검증** (user-blocked, NeedsUserTest=true): PR 2건 머지 후 `ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py include_run_metrics:=true` → RViz 캡처 + `runs/jackal-cafe-001.json` 첫 baseline.

## Cycles to date

- 이번 주: **2** (5-phase 루프 cycle 1 + 2)
- 프로젝트 통합: 2
