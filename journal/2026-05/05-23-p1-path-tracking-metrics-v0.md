# Path-tracking metrics v0 (north-star 정량화 layer 첫 cut)

- **Cycle**: 2026-05-05 23:30 KST
- **Branch**: `autoresearch/p1-path-tracking-metrics-v0`
- **TODO**: `357c5d39-343d-818d` [north-star] Define path-tracking metric set v0
- **Phase**: P1
- **Status**: keep
- **PR**: #4

## What I tried
- 5-phase loop 의 첫 진짜 cycle. STATE.md bottleneck "sim 시각 검증" 은 user-blocked → bottleneck 해소 직후 즉시 활용할 prep work 로 metric module 을 픽.
- `eval/path_tracking_metrics.py` 작성: 7 함수 (cte / heading / completion / time / smoothness / goal / summary). 순수 NumPy, ROS 의존성 0. summary() 가 한 run 당 dict 반환 → CSV append 친화.
- 17 unit test (synthetic trajectory 기반) — on-path / signed offset / heading wrap / overshoot clamp / behind-schedule / constant-velocity-zero-jerk / goal tolerance.
- `docs/path_tracking_metrics.md` 스펙 문서 — formula + "완벽" provisional threshold (indoor/outdoor split) + v0→v1→v2 통합 계획.

## What worked / what failed
- 17/17 tests pass in 23 ms — math 재검증 신뢰도 ↑.
- 임계치는 v0 가설 — P5 calibration 전엔 **숫자 자체보다 메트릭 정의가 안정화** 된 점이 더 중요. threshold 는 후속 cycle 에서 sim 데이터로 보정.
- 세 번 commit 갈렸음 (eval / RESULTS regen / docs / RESULTS regen). cycle pre-flight 에서 모든 deliverable 이 디스크에 떨어진 다음 한 번에 stage + commit 하는 패턴으로 다음 cycle 부터 정리 필요.
- `goal_reached()` 의 "임의의 timestep 만족 시 True" 는 의도적 — 지나가서 멀어진 경우도 success. 단 이 동작이 "잠시 지나갔다가 멈춰서 안 돌아온" failure 를 가릴 수 있음. P5 에서 "마지막 K timestep 이 만족" 으로 정제 검토.

## North-star delta
- **+1 정량 metric layer 등장** — 이전엔 `qual:*` 문자열만. 이제 `cte_rms` / `completion_final` 등 float 가 STATE.md "north star distance" 의 첫 진짜 숫자 자리.
- bottleneck (sim 시각 검증) 자체는 **이동 0** — user-blocked. 이 PR 머지된 후 user 가 sim 1회 돌리면 그 trajectory 에 즉시 `summary()` 적용 → 첫 baseline 숫자.
- 6 phase 중 P5 (평가) 작업 일부가 P1 단계에 미리 떨어진 셈 — 의존성 trail 줄임.

## Key learnings
- "User-blocked bottleneck → prep work 픽" 는 5-phase loop 의 **유효한 PLAN 패턴**. EXECUTOR_SKIP 으로 가만히 있는 것보다 PR 하나 더 떨궈서 user 의 다음 액션 직후 진척 가능하게 함.
- `auto_research.md` 의 decision tree step 2 ("아직 bottleneck 과 aligned 한가") 의 "aligned" 는 **직접 해결** 만 아니라 **bottleneck 직후 활용 가능** 도 포함해야 함. prompt 다음 개정에서 이 confusion 해소 필요.
- v0 metric 의 "완벽" 임계는 P5 calibration 까지 가설. 그러나 metric **정의** 가 박혀있으면 다음 시뮬레이션 데이터 수집부터 모든 작업이 같은 언어로 말함 → 통합 비용 ↓.

## Recommended next 1–3 priorities
1. **A1 sim 시각 검증 (북-스타 ground truth)** — user-blocked, 그러나 이 PR 머지 후 즉시 가치 ↑. user 핸드오프 우선 trigger.
2. **`eval/run_metrics.py` ROS2 노드 wrap** — `/odom + /plan` 구독 → run 당 dict 출력. v0 module 을 라이브 데이터에 연결. claude 자율 진행 가능.
3. **시나리오 yaml (`eval/scenarios/*.yaml`) 정의 시작** — start/goal/world 명세 v0. metric 의 "어디서 측정" 부분 채움.

## Artifacts
- PR: #4 (https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/4) — pending merge
- Files touched: 5 new (eval/__init__.py, eval/path_tracking_metrics.py, eval/tests/__init__.py, eval/tests/test_path_tracking_metrics.py, docs/path_tracking_metrics.md), 1 modified (RESULTS.md), 1 new TSV (results/p1-path-tracking-metrics-v0.tsv)
- TSV row appended: yes (in_progress / qual:tests-17pass)
