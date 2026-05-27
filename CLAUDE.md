# Representation-Aware MPPI

> MPPI planner의 입력 표현(representation)을 costmap 너머로 발전시켜
> 새로운 형태의 navigation 모듈을 만드는 자기계발 프로젝트.

- Repo: https://github.com/Geonhee-LEE/Representation-Aware-MPPI
- 기간: 약 6개월, 외부 deadline 없음 — **흥미 유지가 최우선**.

---

## 🎯 North Star

> **모바일 로봇의 주행 MPPI 가 모든 환경에서 물체회피 + 경로추종을 완벽하게 수행한다.**

- "모든 환경": cafe(좁은 실내) → small_city(open outdoor) → 미관측 분포(real-world rosbag)
- "물체회피 완벽": static + dynamic + 다중 + 가까운 + 가려진 + 의외 — 모든 클래스
- "경로추종 완벽": cross-track error / heading error / smoothness / time-to-goal 동시 만족
- "완벽" 정의는 P5 평가 단계에서 quantitative metric set 으로 못박음 (success rate ≥ X, near-miss ≤ Y, etc.)

이 north star 가 모든 phase 의 우선순위 판단 기준. 로드맵 작업 ↔ north star 거리가 멀면 deprioritize.

---

## Core Hypothesis

> "Plan/control 품질의 상한은 입력 표현(representation)의 품질이 결정한다."

End-to-end RL 대신 **classical planner(MPPI) + 학습된 representation** 조합으로
접근. 보유 자산(MPPI 계보 깊이 + learning dynamics 경험) 위에 새로운
perception representation을 얹는 구조.

---

## Developer Profile

대화 톤/설명 깊이를 맞추기 위한 컨텍스트.

- 7년차 mobile robotics 엔지니어
- Production swerve drive AMR 운영 경험 (회사)
- MPPI 계보를 깊이 follow-up: vanilla → SVG-MPPI, Spline-MPPI, SOPPI,
  π-MPPI, CBF-MPPI 등
- Learning dynamics model 작업 경험 (residual dynamics, system ID)
- ROS2/Nav2 production 디버깅 경험
- Python/CasADi MPC 시뮬, Claude Code + GitHub Actions 자동화 익숙
- 기본 RL 다뤄봄 (PyTorch)

→ MPPI 수식, ROS2 내부, system ID 같은 주제는 기초 설명 생략 가능.
→ 새 영역(예: BEV semantic seg, uncertainty estimation)은 적극 설명/제안.

---

## Technical Stack

| 영역 | 선택 |
|---|---|
| Robot | differential drive (TurtleBot3 또는 자체) — swerve 강제 아님 |
| Simulator | Gazebo Sim Harmonic + 동적 장애물 (trajectory plugin / actor / PedSim) |
| Middleware | ROS2 Jazzy + Cyclone DDS |
| Control | ros2_control, Nav2 plugin |
| ML | PyTorch |
| Workflow | Claude Code + GitHub Actions |

---

## Phased Roadmap

| Phase | 주차 | 내용 |
|---|---|---|
| 0 | 1 | 환경 + baseline MPPI + Claude 통합 셋업 |
| 1 | 2–3 | Multi-Channel BEV 첫 구현 (pretrained semantic seg 활용) |
| 2 | 4–6 | Learning dynamics model을 MPPI rollout에 통합 |
| 3 | 7–10 | BEV → Risk/Uncertainty Field 확장 (static / dynamic / traversability / epistemic / aleatoric channels) |
| 4 | 11–14 | 동적 장애물 시나리오, dynamic risk channel |
| 5 | 15–18 | 평가 + ablation + 시각화 |
| 6 | 19–24 | 외부 산출물 (블로그 / 오픈소스). 논문은 선택. |

---

## 📚 Docs 항해 가이드

`docs/` = 단일 진입점. 새 의사결정/구현 전에 먼저 읽기.

**🏛 헌법 4종** (사람이 manual update, agent stale 감지 시 `docs-refresh` 라벨 PR):
| 파일 | 역할 |
|---|---|
| [`docs/prd.md`](docs/prd.md) | **북극성 + 기능 요구 + 성공 지표 + 의사결정 헌법 7항.** 모든 우선순위 판단의 기준점. |
| [`docs/agents.md`](docs/agents.md) | 4 cron agent + 보조 agent 명세 + 권한 매트릭스. |
| [`docs/skills.md`](docs/skills.md) | prompt ↔ tool ↔ artifact 매핑. |
| [`docs/todo.md`](docs/todo.md) | 4 surface (Notion / TODO.md / issue / PR) canonical authority. |

**🧭 R&D 진척 누적** (Builder REPORT phase 가 매 cycle append):
| 파일 | 역할 |
|---|---|
| [`docs/decisions.md`](docs/decisions.md) | ADR-lite. architecture / scope / priority pivot timeline (D-NNN). |
| [`docs/deliberations.md`](docs/deliberations.md) | 미해결 trade-off + open question (Q-NNN). 답 나면 decisions.md 로 승격. |
| [`docs/scenarios_and_controllers.md`](docs/scenarios_and_controllers.md) | 10 시나리오 × 8 controller 매트릭스. |
| [`docs/dynamic_obstacles_uncertainty_track.md`](docs/dynamic_obstacles_uncertainty_track.md) | 두 axis 통합 track (D1-D4 / U1-U4 stage). |

**⚙️ 자동화 / 인프라 / Sim**: [`docs/automation.md`](docs/automation.md), `sensor_suite.md`, `jackal_cafe.md`, `small_city.md`, ...
전체 인덱스: [`docs/README.md`](docs/README.md).

agent / cron / Notion 관련 모든 의사결정은 `docs/prd.md` § 7 (Decision Constitution) 따른다. 매 cycle 의 큰 결정은 자동으로 `decisions.md` 에 누적 → 회고 가능.

---

## 🔄 Auto-research cadence

Executor (`scripts/daily_executor.sh` + `scripts/prompts/auto_research.md`) runs **hourly** under cron with four safety gates: PR queue capped at 3 outstanding `autoresearch/*` branches, daily branch creation cap at 6, stuck-TODO halt (>24h in `Doing`), and empty-backlog skip. Skips emit `EXECUTOR_SKIP reason=...` silently — user merges set the actual pace. PR Claude review + lightweight ROS2 CI fire on every PR (`.github/workflows/`). Each cycle reflects via `STATE.md` / `JOURNAL.md` so next cycle's plan is informed by the previous one's report.

---

## Working Preferences

- **목표 우선순위**: 흥미 유지 > 학습 깊이 > 외부 산출물. 논문화는 옵션.
- **접근 방식**: end-to-end 학습보다 classical + 학습 representation 결합 선호.
- **결정 기준**: production-grade 완성도보다 실험·반복 속도 우선
  (자기계발 프로젝트 성격).
- **Phase 단위로 incremental하게 진행** — 한 번에 큰 구조 만들지 말 것.
