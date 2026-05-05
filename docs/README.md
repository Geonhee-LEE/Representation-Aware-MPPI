# Docs

프로젝트 외적 컨텍스트(아키텍처, 운영, 셋업) 정리.
코드 구조나 빌드 방법은 리포 루트 `README.md` 와 `CLAUDE.md` 참조.

## 목록

- [`automation.md`](automation.md) — Notion + Telegram + cron 일일/주간 자동화 시스템 전체.
  매일 09:00 브리핑, **10:00 auto-research executor** (TODO DB → autoresearch 브랜치 + `results/*.tsv`,
  `karpathy/autoresearch` `program.md` 패턴), 22:00 마감 (TODO 결산 포함), 일요일 22:30 주간 롤업,
  **2분 간격** Telegram inbox 폴링.
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
- [`small_city.md`](small_city.md) — Stage 2 of the RDSim port: same Jackal in
  a much larger outdoor environment (~170×100 m road grid + apartments,
  cars, oak/pine trees, gas station, fountain, etc.). 185 `<include>` blocks
  preserved verbatim from upstream `small_city.world`; 1.3 GB models live
  outside the repo (fetch with `scripts/fetch_rdsim_models.sh`). 5 scripted
  actors cover crosswalk / sidewalk / plaza / pedestrian-street / diagonal
  patterns. Launch: `jackal_outdoor_sim.launch.py world:=city|cafe`.
