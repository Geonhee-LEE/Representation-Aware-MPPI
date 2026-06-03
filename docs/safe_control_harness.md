# safe_control offline harness

`eval/safe_control_harness/` 는 [tkkim-robot/safe_control](https://github.com/tkkim-robot/safe_control) (264⭐, MPC-CBF / CBF-QP / gatekeeper / C3BF / **DPCBF**) 를 **use-in-place** 로 통합한 Python sim harness. Gazebo + Nav2 의 분 단위 iteration 대신 **초 단위 controller 비교** 가능.

설계 결정: [`decisions.md`](decisions.md) **D-005** (vendoring 안 함, refs/ 외부 클론) + **D-007** (10 시나리오 × 8 controller 매트릭스의 controller candidate 출처).

---

## 두 트랙 sim 의 역할

| | Gazebo + Nav2 (jackal_cafe) | safe_control (이 harness) |
|---|---|---|
| 한 iteration | ~분 | **~초** |
| 로봇 | Jackal differential drive | DynamicUnicycle2D / KinematicBicycle2D / Quad / VTOL |
| 환경 | cafe3 / small_city + 5 actor | dynamic_env + multi-agent |
| 안전 controller | nav2_costmap_2d + MPPI critic | CBF-QP / MPC-CBF / gatekeeper / **DPCBF (ICRA 2026)** / C3BF |
| 평가 metric | `eval.run_metrics` → JSON | (예정) wrapper → 동일 JSON schema |
| 용도 | 실제 metric, 시각 검증 | controller 가설 빠른 ablation |

→ **cross-validation**: safe_control 에서 promising 한 controller 만 Gazebo 로 promote.

---

## 셋업 (한 번만)

```bash
bash scripts/fetch_refs.sh                # 4 repo 클론 → ~/.local/share/.../refs/
cd ~/.local/share/representation-aware-mppi/refs/safe_control
uv venv .venv
uv pip install -e .
```

검증된 setup: torch 2.12 + numpy 1.26 + matplotlib + ~40 deps. **Gurobi 자동 활성화** (restricted license, 2027-11-29 만료, 연구용 OK).

---

## Wrapper 3종

| Wrapper | Backend | Outcome (검증 2026-05-25 ~ 28) |
|---|---|---|
| `run_tracking.sh --model du --algo mpc_cbf` | DynamicUnicycle + MPC-CBF | `Tracking finished. Success!` |
| `run_evade.sh` | gatekeeper backup, dynamic obstacle | `GOAL REACHED step 320, Collision: NO, nominal 91%/backup 9%, ✓ PASSED` |
| `run_dpcbf.sh` | kinematic bicycle + DPCBF (ICRA 2026, 100 obstacle 까지) | `Tracking finished` |

모든 wrapper `MPLBACKEND=Agg` headless. CLI 인자 그대로 전달.

---

## 사용 가능한 모델

| Short | Class | 우리 매핑 |
|---|---|---|
| `un` | Unicycle2D | kinematic, Jackal-equivalent |
| `du` | DynamicUnicycle2D | dynamic (accel 입력) — **default** |
| `kb` | KinematicBicycle2D | DPCBF default, 자동차형 |
| `quad` | Quad2D | UAV — 비우리 |

### Safety 알고리즘
- `cbf_qp` / `mpc_cbf` / **dpcbf** / C3BF / Optimal-Decay CBF / gatekeeper

---

## 통합 계획 (3-stage)

**Stage A** — offline characterization (issue #33 진행 중)
- 다양한 controller × scenario sweep → `docs/dpcbf_characterization.md`
- 80-cell 매트릭스 (issue #40)

**Stage B** — trajectory → run_metrics.summary() pipe
- safe_control logged state → `eval.path_tracking_metrics.summary()` → `runs/safe_control_<run_id>.json`
- Gazebo 의 JSON 과 같은 schema → 직접 비교

**Stage C** — controller 후보를 Gazebo Nav2 로 promote
- safe_control 의 CBF/DPCBF → nav2_mppi_controller critic plugin C++ port
- 별도 follow-up issue

---

## 외부 ref 디렉토리

```
~/.local/share/representation-aware-mppi/refs/
├── safe_control/      (264⭐, license 미명시, isolated .venv)
├── DR-MPC/            (RVO2+pysteam 무거움, 보류)
├── TCFM/              (BSD, Georgia Tech)
└── cfm_mppi/          (license 미명시)
```

git tree 외부 보관 — license 미명시 다수 + `fetch_refs.sh` 로 idempotent.

---

## 자주 막히는 곳

- **`ModuleNotFoundError: position_control`** — `run_dpcbf.sh` 가 `PYTHONPATH` 보정 자동
- **Gurobi 경고** — restricted license 자동 활성화, 무시 가능
- **`MPLBACKEND=Agg`** — headless 강제. GUI 필요 시 wrapper 의 export 제거

---

## 관련

- [`scenarios_and_controllers.md`](scenarios_and_controllers.md) — 시나리오 × controller 매트릭스
- [`run_metrics.md`](run_metrics.md) — Gazebo 트랙의 metric 노드
- [`dynamic_obstacles_uncertainty_track.md`](dynamic_obstacles_uncertainty_track.md) — 두 axis 통합 track

_2026-06-03 KST_
