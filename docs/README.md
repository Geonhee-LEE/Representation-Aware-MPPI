# Docs

프로젝트 외적 컨텍스트 (아키텍처 / 운영 / 셋업 / R&D 진척) 정리.
코드 구조나 빌드 방법은 리포 루트 `README.md` 와 `CLAUDE.md` 참조.

---

## 🏛 핵심 4종 — 프로젝트 헌법 (먼저 읽기)

- [`prd.md`](prd.md) — Product Requirements: 북극성 운영적 정의 + 기능 요구 R-F-001..006 + 비기능 R-NF-001..005 + 성공 지표 + 의사결정 헌법 7항. **모든 결정 기준점.**
- [`agents.md`](agents.md) — 4 cron agent (Researcher / Planner-Builder / Curator / Brief-Wrap) + 4 보조 agent 명세 + 권한 매트릭스 + 새 agent 추가 7-step.
- [`skills.md`](skills.md) — skill = prompt 단위. 활성 10건 인벤토리 + 의존성 다이어그램 + 공통 contract + 새 skill 8-step.
- [`todo.md`](todo.md) — 4 surface (Notion DB / TODO.md / GitHub issue / PR) 빠른 사용 + canonical authority + TODO 라이프사이클 + stuck 처리.

## 🧭 R&D 진척 누적 (의사결정 + 고민 timeline)

- [`decisions.md`](decisions.md) — ADR-lite. architecture / scope / priority pivot 결정 timeline (D-NNN entry). Builder 가 REPORT phase 에서 자동 append.
- [`deliberations.md`](deliberations.md) — 미해결 trade-off + open question (Q-NNN entry). 답 나면 `decisions.md` 로 승격.
- [`scenarios_and_controllers.md`](scenarios_and_controllers.md) — 동적 장애물 시나리오 10종 (S01-S10, ego frame 기준) × controller 8종 비교 매트릭스. 평가 우선순위 + 시나리오 yaml 매핑.
- [`dynamic_obstacles_uncertainty_track.md`](dynamic_obstacles_uncertainty_track.md) — 두 axis 통합 R&D track. D1-D4 (동적 obstacle) + U1-U4 (불확실성 5채널) stage + 의존성 그래프.

## ⚙️ 자동화 / 인프라

- [`automation.md`](automation.md) — Notion + Telegram + cron 일일/주간 자동화 + GitHub Actions 통합 전체.
  매일 09:00 브리핑, **매시간 auto-research executor (hourly + safety gates, 5-phase 루프)** (TODO DB → autoresearch 브랜치 + `results/*.tsv` → `RESULTS.md` 집계 + `STATE.md`/`JOURNAL.md`/`journal/` reflection 자산,
  `karpathy/autoresearch` `program.md` 패턴 위에 REVIEW→PLAN→EXECUTE→REPORT→PLAN_NEXT), 22:00 마감 (TODO 결산 + 오늘 cycle 회고 포함), 일요일 22:30 주간 롤업,
  **2분 간격** Telegram inbox 폴링.
  PR 마다 Claude code review 자동 실행 (`.github/workflows/claude-code-review.yml`) + 경량 ROS2 CI (`ci.yml`).
  GitHub-side 추가 surface: `claude_dev.yml` (issue with `claude-task` label → PR), `claude-mention.yml` (`@claude` 코멘트 → 답글).
  Telegram 메시지에 **`긴급`/`즉시`/`urgent`** 키워드가 있으면 tmux 안에서 claude 가 자동 실행 (Tier 3 제한 버전).
  모든 cron 호출은 today entry 의 `🤖 Cron activity` 섹션에 한 줄 감사 로그.
- [`sensor_suite.md`](sensor_suite.md) — TB3 waffle에 추가한 outdoor 센서 (Velodyne 16ch 3D LiDAR + 1280×720 RGB camera).
  Topic 이름, frame_id, 발행 주파수, Nav2 baseline 보존 방식.
- [`pedestrians.md`](pedestrians.md) — 5인 capsule 보행자 + TrajectoryFollower 로 만든 dynamic obstacle world variant.
  `<actor>` 대신 `<model>` 을 쓴 이유 (LiDAR 가시성), 5명 패턴/속도/색 표, baseline 과의 전환 명령.
- [`outdoor_robot.md`](outdoor_robot.md) — Husky-class `scout_outdoor` (1.0×0.7 m base) 추가.
  TB3 너무 작아서 1.7 m walking actor 와 비율 안 맞는 문제 + upstream `<mu2>` 누락
  마찰 버그 동시 해결. TB3 launch 는 그대로 두고 `outdoor_sim.launch.py` 로 분리.
- [`jackal_cafe.md`](jackal_cafe.md) — Stage 1 of the RDSim port: real Clearpath
  Jackal (~62×42 cm, ~17 kg) with VLP16/UST10/RGB/IMU sensors + simplified cafe3
  indoor world (4-wall shell + 5 cafe_tables) + 5 scripted colored actors
  (walk-{red,blue,green,white}.dae). Reactive SFM pedestrians are deferred to Stage 3.
  Launch: `jackal_cafe.launch.py` (slam:=True default).
- [`environment_taxonomy.md`](environment_taxonomy.md) — north-star "모든 환경"의 v0 분류표.
  Space/Crowd/Visibility/Terrain 4축, 5개 클래스 (indoor-narrow / outdoor-open /
  outdoor-crowd / mixed-cluttered / outdoor-degraded). 현 repo world 매핑 + P5
  평가 harness 가 사용할 라벨 contract 포함.
- [`small_city.md`](small_city.md) — Stage 2 of the RDSim port: same Jackal in
  a much larger outdoor environment (~170×100 m road grid + apartments,
  cars, oak/pine trees, gas station, fountain, etc.). 185 `<include>` blocks
  preserved verbatim from upstream `small_city.world`; 1.3 GB models live
  outside the repo (fetch with `scripts/fetch_rdsim_models.sh`). 5 scripted
  actors cover crosswalk / sidewalk / plaza / pedestrian-street / diagonal
  patterns. Launch: `jackal_outdoor_sim.launch.py world:=city|cafe`.
- [`cfm_mppi_analysis.md`](cfm_mppi_analysis.md) — CFM-for-MPPI integration
  analysis. Flow Planner hierarchical CFM → Nav2 architecture mapping,
  adoption strategy per phase, comparison with cfm_mppi and TCFM approaches.
