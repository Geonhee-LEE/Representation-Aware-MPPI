# Research State — auto-generated each cycle

_Last updated: 2026-05-05 23:30 KST · cycle 0000-bootstrap_

## North star distance

P0 셋업은 본질적으로 마무리됨 (bringup 패키지, 자동화, 환경 분류, TODO/journal 인프라). 정량 metric 은 없음 (P5 이전). 인터랙티브 sim 1차 시각 검증 (Jackal cafe 또는 city) 미완 — north star ground truth 가 아직 한 번도 잡히지 않은 상태. 자동화 메타-인프라는 완성, 도메인 검증은 0%.

## Current bottleneck

North-star ground truth 한 번 잡기 — Jackal cafe 또는 city 인터랙티브 sim 1회 시각 검증 + RViz 캡처로 baseline 거동 확인.

## Open experiments

_없음_ (모든 `results/*.tsv` 의 마지막 row 가 `keep` 상태).

## Recent learnings (last 3 cycles)

- Bootstrap 시점 — 실 cycle 데이터 없음. 최근 3개 PR (#1 docs autoresearch, #2 env taxonomy, #3 mirror_todos) 은 모두 P0 인프라/문서 작업이었고 north-star 거리에 직접 영향 없음.
- 5-phase 루프 도입 직전. 다음 cycle 부터 진짜 reflection 데이터가 쌓이기 시작.
- 정량 평가 부재가 reflection signal 의 상한선 — P5 까지는 qualitative metric 으로 진행.

## Next 3 priorities (actionable)

1. **A1 — Sim 시각 검증 (north star ground truth)**: `jackal_cafe.launch.py` 또는 `jackal_outdoor_sim.launch.py world:=cafe` 로 인터랙티브 1회 실행 + RViz topics flow 확인 + 스크린샷 1장. user test request 핸드오프 가능 (NeedsUserTest=true).
2. **A2 — CI lite 추가 검증**: 현 `.github/workflows/ci.yml` 이 PR 마다 통과 중인지 확인하고, build matrix 가 빠뜨린 launch-validate 단계 (xacro/SDF 파싱) 보강.
3. **A3 — Eval harness v0 스캐폴드**: P5 에 들어갈 metric 모듈 디렉토리 (`eval/`) 만 미리 placeholder 로 만들고 `success_rate` / `path_length` / `time_to_goal` 의 JSON schema 1차 작성. 실제 측정 로직은 P5 본격 시점에 채움.

## Cycles to date

이번 주: 0 · 프로젝트 통합: 0 (5-phase 루프 cycle 한정. P0 인프라 PR 3건은 이전 단발 executor 산출물이라 cycle 카운트에서 제외.)
