# Docs

프로젝트 외적 컨텍스트(아키텍처, 운영, 셋업) 정리.
코드 구조나 빌드 방법은 리포 루트 `README.md` 와 `CLAUDE.md` 참조.

## 목록

- [`automation.md`](automation.md) — Notion + Telegram + cron 일일/주간 자동화 시스템 전체.
  매일 09:00 브리핑, 22:00 마감, 일요일 22:30 주간 롤업, **2분 간격** Telegram inbox 폴링.
  Telegram 메시지에 **`긴급`/`즉시`/`urgent`** 키워드가 있으면 tmux 안에서 claude 가 자동 실행 (Tier 3 제한 버전).
  모든 cron 호출은 today entry 의 `🤖 Cron activity` 섹션에 한 줄 감사 로그.
- [`sensor_suite.md`](sensor_suite.md) — TB3 waffle에 추가한 outdoor 센서 (Velodyne 16ch 3D LiDAR + 1280×720 RGB camera).
  Topic 이름, frame_id, 발행 주파수, Nav2 baseline 보존 방식.
- [`pedestrians.md`](pedestrians.md) — 5인 capsule 보행자 + TrajectoryFollower 로 만든 dynamic obstacle world variant.
  `<actor>` 대신 `<model>` 을 쓴 이유 (LiDAR 가시성), 5명 패턴/속도/색 표, baseline 과의 전환 명령.
