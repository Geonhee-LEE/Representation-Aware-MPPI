# Docs

프로젝트 외적 컨텍스트(아키텍처, 운영, 셋업) 정리.
코드 구조나 빌드 방법은 리포 루트 `README.md` 와 `CLAUDE.md` 참조.

## 목록

- [`automation.md`](automation.md) — Notion + Telegram + cron 일일/주간 자동화 시스템 전체.
  매일 09:00 브리핑, 22:00 마감, 일요일 22:30 주간 롤업, 10분 간격 Telegram inbox 폴링.
- [`sensor_suite.md`](sensor_suite.md) — TB3 waffle에 추가한 outdoor 센서 (Velodyne 16ch 3D LiDAR + 1280×720 RGB camera).
  Topic 이름, frame_id, 발행 주파수, Nav2 baseline 보존 방식.
