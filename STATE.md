# Research State — auto-generated each cycle

_Last updated: 2026-05-06 01:10 KST · cycle p1-eval-scenarios-yaml-v0_

## North star distance

정량 metric **layer + 노드 + scenario spec** 까지 도달 — `eval.path_tracking_metrics.summary()` (PR #4) + `eval/run_metrics.py` ROS2 노드 (별도 PR) + `eval/scenarios/*.yaml` v0 4건 (이번 PR). 메트릭이 "어디서, 어떤 path 위에서 측정되는지" 가 코드와 spec 양쪽에서 박힘. 다만 **첫 실측 숫자는 0건** — 3개 PR 의 직렬 머지 + sim 1회 실행이 필요.

## Current bottleneck

**3 PR 의 직렬 병합 + 첫 baseline sim 실행** (user-blocked). 머지 순서 권장: PR #4 → `autoresearch/p1-eval-run-metrics-node` → `autoresearch/p1-eval-scenarios-yaml-v0`. 셋이 main 에 들어오면 다음 cycle 의 launch-flag 작업이 stack-branch 없이 가능해짐.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p1-path-tracking-metrics-v0` | 2026-05-05 23:38 | qual:tests-17pass | 1 (PR #4 pending) |
| `autoresearch/p1-eval-run-metrics-node` | 2026-05-06 00:06 | qual:tests-8pass | 0 (PR pending) |
| `autoresearch/p1-eval-scenarios-yaml-v0` | 2026-05-06 01:10 | qual:yaml-parse-ok | 0 (PR pending) |

## Recent learnings (last 3 cycles)

- **(이번 cycle)** Decision tree 의 "top-priority Today" pick 이 PR-dependency 로 막히면 stack-branching (금지) 대신 **다음 후보 fallback** 이 정답. `auto_research.md` 에 이 규칙을 명시할 가치 있음.
- **(cycle 2, run_metrics)** Cross-PR dependency 는 lazy import + `@skipUnless` 로 격리 가능 — sim 직전 단계까지 실제 진척 가능.
- **(cycle 1, PR #4)** v0 metric 정의가 박히면 후속 작업 (scenarios, launch flag, calibration) 이 같은 언어로 말함. 이번 cycle 의 scenarios 가 그 효과를 즉시 입증.

## Next 3 priorities (actionable)

1. **(user) 3 PR 직렬 머지** — PR #4 → run_metrics PR → scenarios PR. 머지가 cycle 페이스를 결정.
2. **(claude 자율, post-merge)** `include_run_metrics:=true` + `scenario:=…` 옵션을 `jackal_cafe.launch.py` 에 추가. scenario YAML 파싱 → 시작 pose / waypoints 를 run_metrics 노드 파라미터로 전달.
3. **(user verification, then claude)** `cafe_straight_v0` 1회 실행 → JSON 캡처 → 이번 PR 의 `acceptance:` 임계 가설을 실측으로 calibration. `docs/path_tracking_metrics.md` 의 "v0 가설" 표도 같이 갱신.

## Cycles to date

- 이번 주: **3** (5-phase 루프 cycle 1 + 2 + 3)
- 프로젝트 통합: **3**
