# Product Requirements — Representation-Aware MPPI

> 이 문서는 프로젝트의 **북극성 + 기능 요구 + 성공 지표** 의 단일 진입점이다.
> 모든 cron-agent / 사람 결정은 여기 정의된 우선순위에 정렬되어야 한다.

---

## 1. 북극성 (North Star)

> **모바일 로봇의 주행 MPPI 가 모든 환경에서 물체회피 + 경로추종을 완벽하게 수행한다.**

### "완벽" 의 운영적 정의 (P5 calibration 후 확정)

| 차원 | 1차 임계 (가설) | 측정 방법 |
|---|---|---|
| Path tracking | `cte_rms ≤ 0.2 m` (실내) / `≤ 0.5 m` (실외) | `eval.path_tracking_metrics.summary()` |
| Goal reaching | `goal_reached = 1`, `completion_final ≥ 0.99` | 동일 |
| Smoothness | `jerk_lat ≤ 5 m/s³` (실내) | 동일 |
| Time | `|time_deviation| / T_target < 0.2` | 동일 |
| Obstacle avoidance | collision rate 0%, near-miss < 1/run | gz contact sensor + `eval.run_metrics` |
| Environment generality | 위 모두를 `tests/scenarios/*` **전체** 에서 만족 | 시나리오별 ablation |

### 비-목표 (Non-Goals)
- end-to-end RL 단일 학습 — 우리는 classical MPPI + 학습 representation
- production 안전 인증 — 자기계발 프로젝트 성격
- 모든 가능한 dynamics 지원 — diff drive 우선, swerve/Ackermann 차후
- 실세계 하드웨어 deploy — sim-first, P6 에서 HIL 평가만

---

## 2. Phased Roadmap

| Phase | 주차 | 결과물 | exit criterion |
|---|---|---|---|
| **P0** | 1 | bringup + 자동화 + docs | cron 자율 7일 + sim 1회 시각 검증 |
| **P1** | 2-3 | Multi-Channel BEV (semseg) | `/bev/raw` 5 Hz + cafe 시나리오 alignment 검증 |
| **P2** | 4-6 | learning dynamics → MPPI rollout | residual model + rollout fidelity qual ↑ |
| **P3** | 7-10 | Risk/Uncertainty Field (5 channel) | per-channel critic 가중치 ablation 표 |
| **P4** | 11-14 | 동적 장애물 + dynamic risk channel | crossing/head-on 시나리오 collision ↓ |
| **P5** | 15-18 | 평가 + ablation + 시각화 | `success rate`, `cte_rms` 정량 비교 (4-way) |
| **P6** | 19-24 | 블로그/오픈소스 | README polish + screencast + 논문 draft (선택) |

각 Phase 의 exit criterion 이 STATE.md `Current bottleneck` 결정.

---

## 3. 기능 요구 (Functional Requirements)

### R-F-001 단일 launch 로 sim + nav2 + 센서 + (선택) metric 동시 가동
```
ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py [include_run_metrics:=true]
```
- 100% main 머지된 코드만으로 동작
- 첫 launch 시간 ≤ 3분 (Fuel cache hot 후 ≤ 1분)

### R-F-002 4 surface 자동 동기화
| Surface | 갱신 주기 | 메커니즘 |
|---|---|---|
| Notion TODO DB | 실시간 (executor + researcher) | `mcp__claude_ai_Notion__*` |
| `TODO.md` (repo root) | 매일 22:05 | `scripts/mirror_todos.sh` |
| GitHub issues | 사용자 또는 `claude_dev` workflow | `gh` CLI |
| GitHub PRs | 매 executor cycle + Curator | `gh pr create / merge` |

### R-F-003 자율 R&D 루프 (5-phase 매시간)
REVIEW → PLAN → EXECUTE → REPORT → PLAN_NEXT, `auto_research.md` 가 단일 contract.

### R-F-004 외부 reference offline 통합
`scripts/fetch_refs.sh` + `eval/<harness>/` 패턴으로 vendoring 없이 use-in-place.

### R-F-005 메시지 양방향 (Telegram)
- bot → user: brief / wrap / weekly / urgent / cycle 보고 (push)
- user → bot: 메시지 → Notion `💬 Telegram inbox` (pull, 2분 cron)
- 키워드 `긴급/즉시/urgent` → tmux + claude -p 자율 실행 (Tier 3)

### R-F-006 결과 보존 (append-only)
- `results/<branch>.tsv` per experiment
- `journal/YYYY-MM/<file>.md` per cycle
- `RESULTS.md` 집계 (auto-regen)
- `STATE.md` 최신 스냅샷 (rewrite)

---

## 4. 비기능 요구 (Non-Functional Requirements)

### R-NF-001 자율성
- 사용자 부재 7일 시에도 시스템 정체 없음 (Curator 가 PR 큐 drain)
- 모든 안전 게이트 silent skip 가능 (no Telegram spam)

### R-NF-002 비용 제한
- 일일 Anthropic token ≤ env `RAMPPI_DAILY_TOKEN_BUDGET` (기본 200k)
- 95% 도달 시 LLM 비호출 agent (Researcher/Executor 의 일부) 자동 throttle
- (issue #32 미구현, P0)

### R-NF-003 안전
- main 직접 push 금지 (executor)
- `git push --force-{push,with-lease}` to `main` 금지 (Curator)
- `src/` / `eval/` / `learning/` / `.github/workflows/` 자동 머지 금지
- `crontab -r`, `rm -rf` 외부, system mutation 자동 거절

### R-NF-004 관측성
- 매 cycle Notion `🤖 Cron activity` 한 줄
- 로그 `~/.local/share/representation-aware-mppi/logs/<agent>-DATE.log`
- 상태 `~/.local/state/representation-aware-mppi/`

### R-NF-005 reproducibility
- `colcon build --packages-select representation_aware_mppi_bringup` 한 줄 빌드
- 모든 sim launch 동일 seed 결과 동일
- `eval/scenarios/*.yaml` 정의된 start/goal/world 만 비교 대상

---

## 5. 성공 지표 (Success Metrics)

### 단기 (P0-P1 마무리, ~2026-06)
- [ ] sim 1회 시각 검증 + `eval.summary()` 첫 baseline JSON
- [ ] BEV `/bev/raw` 토픽 5 Hz 발행
- [ ] PR throughput ≥ 3/week 사용자 평균 작업시간 ≤ 30분/week

### 중기 (P3 마무리, ~2026-08)
- [ ] 5 risk channel 모두 RViz 시각화
- [ ] 1 시나리오 (cafe_straight) baseline vs +BEV vs +risk ablation 표

### 장기 (P5 마무리, ~2026-09)
- [ ] 4-way ablation (no-3D / scan_3d / VoxelLayer / STVL) × 2 worlds 24 runs
- [ ] cross-env transfer score (cafe → city 무튜닝) 측정

### Project (P6)
- [ ] GitHub README + screencast 1분
- [ ] (선택) 논문 draft outline

---

## 6. 위험 + 완화 (Risks)

| 위험 | 영향 | 완화 |
|---|---|---|
| 사용자 부재 → PR 큐 정체 | 자율 R&D 멈춤 (5/10~24 14일 사례) | Curator auto-merge `[safe-auto-merge]` 도입 (5/24 해결) |
| Anthropic 토큰 burst | 월 budget 조기 소진 | issue #32 token_guard.sh (P0 backlog) |
| 외부 ref 라이선스 미명시 | 차용 위험 | `scripts/fetch_refs.sh` 외부 클론 (vendoring 안 함) |
| Sim ↔ 실세계 gap | P6 deploy 실패 | P6 sim-to-real audit 항목 미리 적재 |
| MPPI mode collapse (multimodal prior) | path 후보 평균이 infeasible 영역 | cfm_mppi 의 mode-selective MPPI 도입 (#17-21) |

---

## 7. 의사결정 헌법 (Decision Constitution)

- **북극성 alignment 우선** — 어떤 작업도 "이게 north-star 거리를 어떻게 줄이나" 답 못하면 priority down.
- **Simplicity criterion** — `+50 LOC` 이상 추가 시 측정 가능한 이득 1개 명시. 순수 삭제 환영 (karpathy/autoresearch).
- **Append-only 기록** — `results/*.tsv`, `journal/`, `feed.md` 과거 행은 절대 수정 X.
- **외부 의존성 최소화** — apt 외 system install 자동 거절, venv 격리 권장.
- **양방향 sync** — 4 surface (Notion / TODO.md / issues / PRs) 어느 한쪽만 갱신 금지.

---

## 8. 변경 관리

이 문서는 사람이 갱신한다. cron-agent 가 임의로 수정하지 않음. 단:
- `STATE.md`, `JOURNAL.md`, `RESULTS.md` — agent rewrite (single page snapshot, append-only digest, regenerated aggregate 각각)
- `agents.md`, `skills.md` — Curator 가 stale 감지 시 PR 띄움 (label `docs-refresh`), 사람 머지

이 PRD 의 갱신은 git log 로 추적. 큰 변경은 별도 commit + Telegram 알림.

---

_Last manual update: 2026-05-25 KST_
_North-star statement는 `CLAUDE.md` 의 동일 섹션과 1:1 일치해야 한다._
