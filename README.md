# Representation-Aware-MPPI

> **모바일 로봇의 주행 MPPI 가 모든 환경에서 물체회피 + 경로추종을 완벽하게 수행한다.**
> 자기계발 프로젝트, 약 6개월. 자율 R&D 루프 가동 중.

자세한 컨텍스트: [`CLAUDE.md`](CLAUDE.md) · 헌법 + 의사결정: [`docs/prd.md`](docs/prd.md) · 진척 timeline: [`docs/decisions.md`](docs/decisions.md) · 인덱스: [`docs/README.md`](docs/README.md)

---

## 한 화면 요약

```
┌────────────────────── 자율 R&D 루프 ──────────────────────┐
│                                                            │
│   매시간 Builder ── 1 TODO → PR (5-phase REVIEW→PLAN→...)  │
│   매 4시간 Researcher ── arxiv/github 검색 → feed + TODO   │
│   매일 23:00 Curator ── safe-PR auto-merge / stale 정리    │
│   매일 09:00 Brief / 22:00 Wrap / 일 22:30 Weekly         │
│   매 2분 Telegram inbox 폴링 + 긴급키워드 tmux 자동 실행   │
│                                                            │
└────────────────────────────────────────────────────────────┘
                            ▲
                            │ 양방향 sync
                            ▼
   ┌────────────┬────────────┬────────────┬────────────┐
   │ Notion DB  │  TODO.md   │ GitHub     │ Telegram   │
   │  (canon)   │  (mirror)  │ issue/PR   │   bot      │
   └────────────┴────────────┴────────────┴────────────┘
```

지금까지 진척: ~28일 가동 · 50+ PR 머지 · 9 D-NNN 결정 entry · 20+ docs · ~10 reference paper 통합.

---

## 즉시 실행할 수 있는 것

### 1) ROS2 Jackal + Gazebo (실내 cafe)
```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select representation_aware_mppi_bringup
source install/setup.bash
ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py
```
RViz 의 `2D Goal Pose` 로 navigation goal 송신. SLAM (slam_toolbox) 기본. 자세히: [`docs/jackal_cafe.md`](docs/jackal_cafe.md).

### 2) Outdoor city (대규모 outdoor, Fuel 자동 다운로드)
```bash
./scripts/fetch_rdsim_models.sh                       # 한 번만 (~1.3 GB)
ros2 launch representation_aware_mppi_bringup jackal_outdoor_sim.launch.py world:=city
```
~170×100 m road grid + apartments / cars / trees / gas station / fountain 자동 fetch. 자세히: [`docs/small_city.md`](docs/small_city.md).

### 3) Sim + 정량 metric 동시 (run_metrics)
```bash
ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py \
  include_run_metrics:=true run_id:=cafe-001
```
`/odom + /plan` 구독 → 한 run 당 `runs/cafe-001.json` 자동 dump. 자세히: [`docs/run_metrics.md`](docs/run_metrics.md), [`docs/path_tracking_metrics.md`](docs/path_tracking_metrics.md).

### 4) safe_control offline (초 단위 controller 비교)
```bash
bash scripts/fetch_refs.sh                            # 4 repo 클론
bash eval/safe_control_harness/run_tracking.sh --model du --algo mpc_cbf
bash eval/safe_control_harness/run_evade.sh          # gatekeeper backup
bash eval/safe_control_harness/run_dpcbf.sh          # ICRA 2026 DPCBF
```
초 단위 controller 비교. 자세히: [`docs/safe_control_harness.md`](docs/safe_control_harness.md).

---

## 개발된 핵심 기능

### 🤖 시뮬 + 로봇
| 기능 | docs |
|---|---|
| TB3 baseline (Phase 0 reference) | [`sensor_suite.md`](docs/sensor_suite.md), [`pedestrians.md`](docs/pedestrians.md) |
| Jackal differential drive | [`jackal_cafe.md`](docs/jackal_cafe.md) |
| Outdoor scout (Husky-class) | [`outdoor_robot.md`](docs/outdoor_robot.md) |
| cafe3 + 5 scripted actors | [`jackal_cafe.md`](docs/jackal_cafe.md) |
| small_city (~170×100 m) | [`small_city.md`](docs/small_city.md) |
| 환경 분류 v0 (4축 × 5클래스) | [`environment_taxonomy.md`](docs/environment_taxonomy.md) |

### 🛡 동적 장애물 + 불확실성
| 기능 | docs |
|---|---|
| 10 시나리오 × 8 controller 비교 매트릭스 | [`scenarios_and_controllers.md`](docs/scenarios_and_controllers.md) |
| 동적 obstacle + uncertainty 통합 track | [`dynamic_obstacles_uncertainty_track.md`](docs/dynamic_obstacles_uncertainty_track.md) |
| safe_control offline harness | [`safe_control_harness.md`](docs/safe_control_harness.md) |
| 시나리오 yaml v1 (`cafe_*_v0.yaml`) | `eval/scenarios/*.yaml` |

### 📊 평가 + metric
| 기능 | docs |
|---|---|
| Path-tracking metric v0 (8 함수 + 17 test) | [`path_tracking_metrics.md`](docs/path_tracking_metrics.md) |
| run_metrics ROS2 노드 (sim → JSON) | [`run_metrics.md`](docs/run_metrics.md) |
| Per-branch TSV + RESULTS.md 자동 집계 | [`automation.md`](docs/automation.md) |

### 🔬 R&D 자동화
| 기능 | docs |
|---|---|
| 4 cron agent + 권한 매트릭스 | [`agents.md`](docs/agents.md) |
| skill = prompt 단위 (10 활성) | [`skills.md`](docs/skills.md) |
| Notion + Telegram + cron 통합 | [`automation.md`](docs/automation.md) |
| Researcher 4h cron | [`researcher.md`](docs/researcher.md), [`research_feed.md`](docs/research_feed.md) |
| 5-phase R&D 루프 | `scripts/prompts/auto_research.md` |
| STATE / JOURNAL / journal 회고 자산 | [`journal_state.md`](docs/journal_state.md) |

### 🧭 R&D 진척 누적
| 기능 | docs |
|---|---|
| ADR-lite (D-NNN) | [`decisions.md`](docs/decisions.md) |
| 미해결 trade-off (Q-NNN) | [`deliberations.md`](docs/deliberations.md) |
| PRD + 헌법 7항 | [`prd.md`](docs/prd.md) |
| 4 surface TODO 라이프사이클 | [`todo.md`](docs/todo.md), `TODO.md` |

### 🔬 Reference 통합 (외부 SOTA)
| Reference | 통합 형태 | docs |
|---|---|---|
| [safe_control](https://github.com/tkkim-robot/safe_control) (264⭐, CBF library) | use-in-place + wrapper | [`safe_control_harness.md`](docs/safe_control_harness.md) |
| [DPCBF](https://arxiv.org/abs/2510.01402) (ICRA 2026) | safe_control 내 실측 | issue #33 |
| [cfm_mppi](https://arxiv.org/abs/2508.01192) (ICRA 2026) | analysis (#17/18/29/31) | (예정) |
| [TCFM](https://github.com/CORE-Robotics-Lab/TCFM) | analysis 머지됨 | [`tcfm_evaluation.md`](docs/tcfm_evaluation.md) |
| [DR-MPC](https://github.com/James-R-Han/DR-MPC) | analysis 진행 | issue #29 |
| MAML residual adaptation | analysis 머지됨 | [`maml_residual_adaptation_analysis.md`](docs/maml_residual_adaptation_analysis.md) |

전체 reference: [`research/feed.md`](research/feed.md) (30 entry 캡, 월별 archive).

---

## 작업 지시 (사용자 → 시스템)

3가지 surface 중 어느 것이든:

1. **Notion TODO DB** 에 새 row (Status=Today, Owner=claude)
2. **GitHub issue** with `claude-task` label
3. **Telegram** 메시지 (bot @RepresentationAwareMPPIBot)
4. **Telegram 긴급 키워드** (`긴급/즉시/urgent/asap`) → tmux 즉시 자율 실행

Notion DB: https://www.notion.so/b0b1bd5492d94cf89844a7e9cf7d166d

---

## 시스템 운영 상태

- **Cron**: 매시간 Builder · 매 4시간 Researcher · 매일 Curator · ~28일 가동
- **PR 큐 cap**: 6 (Curator drain). 도달 시 silent skip — 사용자 머지 페이스가 throughput 결정
- **Telegram 토큰**: `~/.config/representation-aware-mppi/telegram.env` (chmod 600)
- **로그**: `~/.local/share/representation-aware-mppi/logs/`
- **상태**: `~/.local/state/representation-aware-mppi/`
- **외부 refs**: `~/.local/share/representation-aware-mppi/refs/` (4 repo, isolated venv)

---

## 라이선스 + 출처

자체 코드: BSD-3-Clause 패턴 (`SPDX-License-Identifier`). 외부 reference: **use-in-place** (refs/ 외부 클론, vendoring 안 함). 라이선스 정책 결정: [`decisions.md`](docs/decisions.md) D-005.

설계 패턴 차용:
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — single `program.md` skill 패턴
- [Geonhee-LEE/toy_claude_project](https://github.com/Geonhee-LEE/toy_claude_project) — GitHub Actions Claude 자동화
- [Geonhee-LEE/RDSim](https://github.com/Geonhee-LEE/RDSim) — Jackal description + actor + worlds
