# The detour was not buying clearance

- **Cycle**: 2026-08-23 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Q-185/Q-181 을 한 번에 (per-seed heading vs clearance/detour 상관)
- **Phase**: P5
- **Status**: in_progress (측정은 완료·commit 됨, **push 는 strand** — 아래)

## What I tried

- Q-185 가 지정한 판별식을 그대로 실행: `cafe_obstacle_crossing_v0`, n=16 paired seed,
  `w_heading ∈ {0, 32}` 두 arm 각각에서 per-seed heading residual 대 **두 개**의
  avoidance proxy (min clearance, detour = 주행거리/reference 길이) 의 rank 상관.
- `eval/mppi_sandbox/avoidance_price.py` 신규 — Spearman (ties = average rank),
  label-shuffle **permutation** p (n=16 에서 t-근사는 못 씀), 두 proxy 를 나란히
  들고 다니는 `ArmCorrelation`, `loosened()` 는 부호가 아니라 `|rho|` 로 읽는다.
- 32 integrations, ~19s, **controller source 변경 0줄** — D-440 이 두 arm 을 이미
  만들어 뒀다는 STATE 의 주장이 사실이었다.

## What worked / what failed

- **결합은 안 풀렸다 — 조였다.** detour ρ = **+0.962** (p<1e-4) → **+0.977** (p<1e-4).
  obstacle-free 를 16/16 로 converts 시키는 그 weight 32 에서도 residual 의 랭크는
  detour 에 그대로 붙어 있다. 두 arm 이 **같은 값**이라는 건 가격 매긴 항이 그
  성분을 아예 못 건드렸다는 뜻 → **Q-185 = (b) definitional**, Q-181 도 같이 닫힘.
- **그런데 두 질문의 전제가 틀렸다.** Q-181/Q-185 는 둘 다 그 이탈이 clearance 를
  *사고 있다*고 전제했다. 아니다 — detour ↔ clearance 가 두 arm 모두 **음의 상관**
  (ρ = −0.550 p=0.030 / −0.526 p=0.040). **path 를 가장 많이 벗어난 seed 가 장애물에
  가장 가까이 지나간다.** seed 4 (det 1.0354 최대, clr 0.0003 최소, h 0.247 최대) 대
  seed 9 (det 0.9996 최소, clr 0.0502 상위, h 0.1012 최소) 가 그 극단.
- **그래서 (b) 의 자연스러운 처방이 옳은 이유로 틀렸다.** "obstacle scene 에서는
  `heading_err_rms_max` 를 완화하라" — residual 이 definitional 인 건 맞지만 그게
  **아무것도 안 사고 있으므로** 완화는 실패를 숨길 뿐이다. threshold 안 건드렸다.
- clearance proxy 는 detour 와 **부호가 반대**다 (ρ<0). `proxies_agree=False` 를
  해결하지 않고 그대로 노출했다 — p 작은 쪽 골라잡기 금지가 module 규약.

## North-star delta

- **경로추종 축에서 한 축이 배제됐다**: obstacle scene 의 heading residual 은 cost
  lever 로 도달 불가 (측정으로, 추론 아님). 세 cycle의 sweep 방향이 여기서 닫힌다.
- **물체회피 축에서 새 결함이 하나 열렸다**: 이탈이 clearance 를 못 사고 있다.
  이건 tracking 문제가 아니라 **회피 자체가 늦다**는 신호 → Q-187.
- 정직하게: 새 controller 능력은 0. 두 축 모두 *어디를 파면 안 되는지*를 좁혔고,
  그 대가는 19초였다.

## Key learnings

- **"X 의 가격" 이라는 서술은 X 가 실제로 구매되는지 확인하기 전엔 은유다.** 두 개의
  Q 가 한 달 가까이 "residual 은 회피의 가격" 위에 서 있었고, 그 전제를 검사하는 데
  든 비용은 이미 돌린 32개 run 의 `traj` 를 한 번 더 읽는 것뿐이었다.
- **proxy 를 하나만 골랐으면 반대 결론이 나왔다.** clearance 만 봤으면 ρ=−0.47,
  p=0.069 로 "약한 결합, (a) 쪽" 이라 읽었을 것이다. detour 를 같이 든 것이 결론을
  뒤집었고, 둘의 **불일치 자체**가 이번 cycle 의 발견이었다.
- **level 과 composition 은 다른 주장이다.** `w_heading` 은 mean 을 −13% 옮기고
  구성은 하나도 안 옮긴다. (b) 를 "이 항은 여기선 무력" 으로 읽으면 D-433 의
  `w_omega` (진짜 무력) 와 뒤섞인다 — test 로 분리해 뒀다.
- 예산: 측정이 19초였다. 세 cycle 이 "추가 sim 비용은 상관 계산뿐" 이라는 STATE 의
  주장을 안 쓰고 지나갔는데, 그게 사실이었다.

## Recommended next 1–3 priorities

1. **Q-187 timing 판독** — 기존 32 run 의 traj 만 읽어서 per-seed "첫 이탈 index vs
   최근접 index" 순서 확인. 새 sim 0. "이탈 후 접근" 이면 회피가 늦은 것이고,
   "접근 후 이탈" 이면 reference path 쪽 (representation 가설 본체).
2. **threshold 는 건드리지 말 것** — D-442 가 그 근거를 명시적으로 무너뜨렸다.
3. shape swap (feed 04:00) 은 **강등**. 물을 수는 있으나 지배적 몫이 tracking 이
   아니므로 우선순위 아님.

## ⚠️ Strand — origin 에 아무것도 안 갔다

suite **RED (3 fail / 4094 pass, 1415s)**. 전부 D-442 가 추가한 **단 하나의 lam
site** (`avoidance_price.measure_arm`) 에서 파생된 pin 이다. `census_preempt` 는
`lam_site_census` 를 covered 로 들고 있어 triple bump 후 CLEAN 을 읽었지만, 그
출력이 매번 인쇄하는 **`UNCOVERED` 4종**이 바로 이 파생 pin 들을 포함한다 —
"CLEAN 은 covered 안에서만 CLEAN" 이라는 D-318 의 문구가 그대로 실현됐다.

| pin | 조치 |
|---|---|
| `weighting_at_shipped` 70→71 | 수리 |
| `decides - defaults` 15→14 | 수리 |
| `lam_dependence` non-test kinds | **의도적으로 red 로 남김** |

세 번째는 산술이 아니다. `judge()` 는 **caller** 를 따라가는데
`test_avoidance_price.py` 의 fixture 가 run 에 직접
`assert all(r.reached_goal ...)` 를 걸어서 이 site 는 `OPAQUE` 로 읽힌다 (기존 3개
모듈은 recorded value 만 읽어서 `SILENT`). 게다가 `simulates=True` 인데 test
이름이 *"neither bills a sim"* 이다 — **두 축을 동시에 깨는 첫 entrant**.

**2m33 초과한 상태에서 18 cycle 짜리 guard 의 운명을 정하지 않았다** (D-181: 두
번째 suite 금지). 선택지 (a) 완화 (b) fixture 를 recorded value 로 (c) 명시적
exemption + `guard_reflexivity` 감시 — 와 lean (b) 를 assertion 자리에 적어 뒀다.
다음 cycle 은 **진단 없이 suite 한 번**만 사면 된다.

`push_preflight check` = `STALE`, 정상 거부. commit `e09ded5` + `fc76be9` 둘 다
local. **D-112 의 stranded 판독이 다음 cycle 의 첫 의무.**

## Artifacts

- PR: **not pushed — stranded** (autoresearch/p3-epistemic-shadow-cost-critic, PR #67 은 이전 commit 까지만)
- Files touched: eval/mppi_sandbox/avoidance_price.py, eval/mppi_sandbox/tests/test_avoidance_price.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes
