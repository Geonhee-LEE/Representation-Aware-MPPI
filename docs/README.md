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
- [`epistemic_channel_bev_rendering.md`](epistemic_channel_bev_rendering.md) — P3 epistemic 채널 BEV 렌더링 spec. ensemble `σ²` → ego-frame grid (geometry / `σ²→[0,1]` 정규화 / 5채널 composition). companion: `residual_in_rollout_reference.md`.

## ⚙️ 자동화 / 인프라

- [`automation.md`](automation.md) — Notion + Telegram + cron 일일/주간 자동화 + GitHub Actions 통합 전체.
  매일 09:00 브리핑, **매시간 auto-research executor (hourly + safety gates, 5-phase 루프)** (TODO DB → autoresearch 브랜치 + `results/*.tsv` → `RESULTS.md` 집계 + `STATE.md`/`JOURNAL.md`/`journal/` reflection 자산,
  `karpathy/autoresearch` `program.md` 패턴 위에 REVIEW→PLAN→EXECUTE→REPORT→PLAN_NEXT), 22:00 마감 (TODO 결산 + 오늘 cycle 회고 포함), 일요일 22:30 주간 롤업,
  **2분 간격** Telegram inbox 폴링.
  PR 마다 Claude code review 자동 실행 (`.github/workflows/claude-code-review.yml`) + 경량 ROS2 CI (`ci.yml`).
  GitHub-side 추가 surface: `claude_dev.yml` (issue with `claude-task` label → PR), `claude-mention.yml` (`@claude` 코멘트 → 답글).
  Telegram 메시지에 **`긴급`/`즉시`/`urgent`** 키워드가 있으면 tmux 안에서 claude 가 자동 실행 (Tier 3 제한 버전).
  모든 cron 호출은 today entry 의 `🤖 Cron activity` 섹션에 한 줄 감사 로그.
- [`researcher.md`](researcher.md) — Researcher agent 1-page explainer (web search / feed 갱신 / TODO 생성 / Telegram digest).

## 🤖 Sim / 로봇 / 센서

- [`sensor_suite.md`](sensor_suite.md) — TB3 waffle outdoor 센서 (Velodyne 16ch + 1280×720 RGB camera). Topic / frame_id / 발행 주파수 / Nav2 baseline 보존.
- [`pedestrians.md`](pedestrians.md) — 5인 capsule 보행자 + TrajectoryFollower world variant. `<actor>` vs `<model>` 선택 이유 + LiDAR 가시성.
- [`outdoor_robot.md`](outdoor_robot.md) — Husky-class `scout_outdoor` (1.0×0.7 m). TB3 비율 불일치 + `<mu2>` 누락 마찰 버그 동시 해결.
- [`jackal_cafe.md`](jackal_cafe.md) — RDSim Stage 1 — Clearpath Jackal + cafe3 indoor + 5 colored actors. `jackal_cafe.launch.py` slam=True default.
- [`small_city.md`](small_city.md) — RDSim Stage 2 — Jackal + ~170×100 m city + 185 model includes (Fuel auto-download). `jackal_outdoor_sim.launch.py world:=city|cafe`.
- [`environment_taxonomy.md`](environment_taxonomy.md) — north-star "모든 환경" v0 분류 (4축 × 5클래스 A~E). repo world 매핑 + P5 harness label contract.

## 📊 평가 / metric

- [`mppi_sandbox.md`](mppi_sandbox.md) — **primary verification surface (D-016)**. NumPy diff-drive 폐루프 sim + controller plug-in registry + sandbox CI. auto-research 가 코드를 증명하는 표면.
- [`path_tracking_metrics.md`](path_tracking_metrics.md) — v0 metric set (CTE / heading / completion / time / smoothness / goal). 8 함수 + 17 unit test 의 spec doc.
- [`run_metrics.md`](run_metrics.md) — `include_run_metrics:=true run_id:=...` 한 명령으로 sim → JSON. launch 인자 + JSON schema + 시나리오 yaml 연계 + 사용 시나리오 3종.
- [`safe_control_harness.md`](safe_control_harness.md) — `eval/safe_control_harness/` Python sim 트랙. 두 트랙 sim 의 역할 분담 + 3 wrapper + 통합 3-stage.
- [`journal_state.md`](journal_state.md) — STATE / JOURNAL / journal/ 3 layer 자산. 매 cycle REPORT phase 가 갱신, prompt-bloat 방지.
- [`research_feed.md`](research_feed.md) — Researcher 의 외부 SOTA trawl 결과 누적. dedup gate + filter + Notion promote 정책.

## 🔬 분석 / reference 통합

- [`tcfm_evaluation.md`](tcfm_evaluation.md) — TCFM (Sean Ye / Georgia Tech, 100× faster CFM than diffusion) 평가.
- [`maml_residual_adaptation_analysis.md`](maml_residual_adaptation_analysis.md) — MAML-based residual dynamics 평가 (P2-relevant).
- [`p2_residual_dynamics_decision.md`](p2_residual_dynamics_decision.md) — P2 residual-dynamics 후보 8종 결정 매트릭스 + build-first 선택 (D-009).
- [`cbfkit_analysis.md`](cbfkit_analysis.md) — cbfkit (Toyota Research, BSD-3, JAX) 분석. safety-filter 아키텍처 차용 → sandbox `cbf_mppi` (S1). stochastic/CVaR-CBF ↔ D-013/D-014 매핑.
- [`residual_in_rollout_reference.md`](residual_in_rollout_reference.md) — Stochastic-MPPI 에서 추출: residual-in-batched-rollout 배선 + variance→margin (P3 epistemic channel) 구현 레퍼런스.
- (예정) `cfm_mppi_analysis.md` (#17), `cfm_mppi_integration_spec.md` (#18), `dr_mpc_analysis.md` (#29), `scope_analysis.md` (#28), `safe_control_evaluation.md` (#30), `reference_lineage.md` (#31), `dpcbf_characterization.md` (#33 Stage A), `risk_field.md` (#35).

---

## 🔄 docs 자동 진화 정책

- **헌법 4종** (`prd/agents/skills/todo`): 사람 manual update. agent 가 stale 감지 시 `docs-refresh` 라벨 PR.
- **decisions.md / deliberations.md**: 매 cycle 의 Builder REPORT phase 가 자동 append (architecture/scope/priority 결정 만). 사람도 직접 추가 가능.
- **track / scenarios doc**: 새 paper / 새 controller 추가 시 Researcher 가 자동 추가 (issue #37 통과 후).
- **분석 doc** (`*_analysis.md`, `*_evaluation.md`): Builder 가 issue 픽업해서 생성 + cycle 마다 풍부해짐.
- **sim / metric doc**: 사람 또는 Builder 가 src 변경과 함께 갱신.
