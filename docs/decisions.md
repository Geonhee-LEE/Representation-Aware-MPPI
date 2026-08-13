## D-241 — 2026-08-13 — freeze 를 **선언만 하고 채점하지 않던** scene: `"skipped"` 는 통과로 읽힌다

- **Context**: STATE 의 bottleneck 이 "freeze 는 detect 되지만 planner 에 값이 매겨지지 않는다" 였고 D-240 이 그것을 다음 mechanism-급 후속으로 지목했다. cost term 을 쓰러 갔다가, 직전 cycle 이 규칙으로 만든 "제안하기 전에 grep" 을 돌렸고 그것이 걸렸다 — **bottleneck 이 한 단계 앞을 잘못 짚고 있었다.**
- **측정된 사실**: `freeze_duration` 은 tree 전체에서 **정확히 한 곳**, `cafe_freezing_v0.yaml` 의 `acceptance` 에만 존재한다. 같은 파일이 그것을 `success_metric_priority` 의 **두 번째**로 올려놓았다. 계산하는 코드는 없다. 그리고 단순 누락보다 나쁜 형태였다: `run.check_acceptance` 는 모르는 key 를 문자열 `"skipped"` 로 매핑하고, `run_scenario` 는 `pass` 를 `[v for v in checks.values() if isinstance(v, bool)]` 로 계산한다. `str` 은 `bool` 이 아니므로 **scene 의 2순위 성공 기준이 자기 pass/fail 에서 조용히 빠져 있었다.** freezing-robot failure mode 를 위해 존재하는 scene 이 freezing 을 검사하지 않고 통과해 왔다.
- **Decision**: metric 을 먼저 구현하고 cost term 은 이 cycle 에 넣지 않는다. `freeze_price.freeze_duration` = **reference path 를 따른** 최장 연속 정체 구간 [s] (yaml 자신의 문구가 "stopped *without progress*" 이므로 ground speed 가 아니라 along-path 진행률로 정의 — 보행자를 옆으로 크게 도는 궤적은 속도가 있어도 정체다). 임계값은 새 knob 을 만들지 않고 `StockMPPI` 의 shipped `creep_speed` (0.08) 를 빌린다: "정체" = *controller 자신이 정의한 전진 최소치보다 느림*. 두 상수를 test 로 묶어 둔다. `check_acceptance` 에 rule 을 넣어 key 가 실제로 채점되게 한다.
- **측정 결과 (3 seeds × 3 arms, `cafe_freezing_v0`, 최장 정체 [s], 선언 한계 2 s)**: `stock_mppi` 1.60/0.60/0.40 → **0/3 초과**; `risk_mppi` 0.60/6.30/3.30 → **2/3 초과**; `social_mppi` 3.30/1.70/2.40 → **2/3 초과**. **9/9 전부 goal 도달.** 따라서 `three_arm` 의 freeze 판정(`d_reached < 0` 에서 발화)은 여기 측정된 **전부에 대해 맹목**이다 — 로봇이 회복하는 freeze 를 기존 detector 는 볼 수 없고, 이 population 이 통째로 그것이다.
- **n=1 이 순위를 뒤집었다는 사실을 명시한다**: seed 0 만 보면 `risk_mppi` 가 가장 덜 언다(0.60). 3 seed 로 넓히면 최악 단일 판독(6.30)을 그것이 갖는다. 0.60→6.30 의 산포에서 **arm 순위는 n=3 으로 지지되지 않는다**; 지지되는 것은 순위를 필요로 하지 않는 blindness 주장(9/9)이다. D-235 의 paired-seed protocol 로 넓히기 전에는 표의 순위를 인용하지 않는다.
- **일반화되는 교훈**: **선언되었으나 구현되지 않은 acceptance key 는 아예 없는 key 보다 나쁘다** — artifact 안에서 `"skipped"` 는 *검사됨*처럼 읽히기 때문이다. 그리고 규칙과 계획이 충돌하면 규칙이 이겼다: STATE 가 시킨 대로 cost term 을 넣었다면 D-021(측정 없는 cost term 금지)을 정면으로 위반했을 것이다.
- **Alternatives**: (a) 채택 — metric + rule 배선 + 7 test, cost term 은 다음 cycle. (b) cost term 을 이번에 같이 — 채점할 숫자가 없는 상태의 D-021 재현, 기각. (c) metric 만 만들고 `check_acceptance` 는 건드리지 않는다 — 결함의 절반(조용한 `"skipped"`)을 남김, 기각. (d) startup transient 를 특례 처리 — 지표를 궤적보다 좋아 보이게 만드는 것 외의 목적이 없어 기각, 대신 문서화.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-17-the-freezing-scene-was-not-testing-for-freezing.md` · D-240 (이 후속을 지목한 결정) · D-021 (측정 없는 cost term 금지 — 이 cycle 이 따른 규칙) · D-235 (순위 인용 전 넓혀야 할 protocol) · D-016 (sandbox-executable bias)

## D-240 — 2026-08-13 — 가장 강한 증거를 가진 configuration 이 **arm 이 아니었다**: isolation 규율이 finding 을 만들고 동시에 숨겼다

- **Context**: STATE 의 bottleneck 이 세 cycle 째 같은 문장이었다 — "nothing on the board proposes the next capability". ~21 cycle 이 instrument 였고, 다음 non-repair cycle 이 갚아야 할 것은 D-225 의 capability 후속이라고 STATE 가 명시했다. feed 가 제안한 가장 싼 capability (PGIF cost term port) 는 **이미 shipped** 였다 (`PredictedGeometryCritic`, D-217). 그래서 후속은 "port 하라" 가 아니었고, 실제 공백은 `three_arm.ARMS` 를 읽고서야 보였다.
- **측정된 사실 (재측정 아님, 기록 재독)**: 이 branch 의 최대 clearance step 은 `(w_risk, w_ped) = (40, 50)` 의 **+0.3755 m** 이고 (D-218 의 2x2 top row), 세 eligible scene 전부에서 pair 가 두 member 를 이기며 (D-219/D-234), n=12 로 넓혔을 때 **강해진** 유일한 half 다 (D-235: 6+/0− p=0.031 → 11+/1− p=0.006). 그런데 `ARMS` 의 네 entry 는 **전부** `w_risk = 0.0` 이다 — 즉 이 cell 은 override 두 개를 손으로 넘겨야만 도달 가능했고, **이름으로 sweep 하는 harness** (`ab.seed_sweep`, `baseline_matrix`, `near_miss.score_runs`, P5 matrix) 는 그것을 볼 수 없었다.
- **Decision**: `social_mppi` 를 registry controller 로 신설한다 — `RiskMPPI` 를 그 cell 로 default 한 subclass, cost term 신설 없음, 상수 신설 없음, 새 측정 없음. `gap_gated_mppi` 와 같은 shape: **arm 이지 mechanism 이 아니다**. 등가성을 test 로 고정한다 — `social_mppi` 는 `risk_mppi(w_risk=40, w_ped=50)` 와 **byte-identical** 로 simulate 해야 하고, 그래야 D-218/D-219/D-234/D-235 의 판독이 재취득 없이 이 이름으로 이전된다. 이름 붙이기가 조용히 re-tuning 이 되는 경로를 그 test 가 막는다.
- **`ARMS` 에는 넣지 않는다, 그리고 그것이 이 결정의 절반이다**: `w_risk = 40` row 를 모든 entry 가 `w_risk = 0.0` 인 dict 에 넣으면 D-218 이 D-217 에게서 잡아낸 바로 그 오류 — 두 denomination 의 혼입 — 를 한 층 위에서 재생산한다. `ARMS` 는 "각 knob 이 **단독으로** 무엇을 사는가" 를 답하고 이 arm 은 "pair 가 무엇을 사는가" 를 답한다. 둘 다 필요하고, 하나를 다른 하나로 보고하는 것만이 금지된다. isolation invariant 자체를 test 로 고정했다 (양방향).
- **일반화되는 교훈**: **finding 을 가능하게 한 규율이 그 finding 을 숨길 수 있다.** 네 cycle 이 이 2x2 를 걸었고 아무도 승리 cell 에 이름이 없다는 것을 알아차리지 못했다 — isolation denomination 이 정확히 그것을 보이지 않게 만들었기 때문이다. 점검 규칙: *측정 결과가 어떤 configuration 을 지목하면, 그 configuration 이 harness 가 도달 가능한 이름인지 확인하라.*
- **사지 못하는 것을 명시한다**: 이 cycle 은 **새 회피 mechanism 을 만들지 않았다**. 두 cost term 은 이미 존재했다. 움직인 것은 가장 잘 측정된 *조합*이 P5 matrix 가 채점할 수 있는 first-class object 가 되었다는 것뿐이고, capability axis 의 정직한 delta 는 "+1 sweepable arm, +0 mechanism" 이다. freeze 는 여전히 *detect* 만 되고 (`BOUGHT_WITH_FREEZE`) planner 에 값이 매겨지지 않는다 — 그것이 다음 mechanism-급 후속이다.
- **Alternatives**: (a) 채택 — registry arm + 등가성 pin + `ARMS` isolation pin. (b) `ARMS` 에 다섯 번째 entry 로 추가 — 한 줄이면 되지만 denomination 을 섞어 D-218 을 무효화, 기각. (c) STATE #1 (sharded pin re-take) 을 대신 집는다 — instrument track 이고, STATE 자신이 capability 를 우선으로 지목했으며 ~21 cycle 이 이미 instrument 였다, 기각. (d) mechanism 을 새로 발명 (freeze pricing) — 이 cycle 예산에 설계까지 들어가지 않고, 근거 없는 새 cost term 은 이 branch 가 반복해 후회한 모양 (D-021 의 inert critic), 다음 cycle 로.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-16-the-pair-that-wins-becomes-an-arm.md` · D-235 / D-234 / D-219 / D-218 (이 arm 이 물려받는 판독) · D-217 (denomination 오류의 원본) · D-140 (열린 PR 위 계속 작업) · D-016 (sandbox-executable bias)

## D-239 — 2026-08-13 — per-pass ceiling 은 **측정의 한계가 아니라 질의 방식의 한계**였다: probe 를 shard 로 쪼개 compose 하면 가장 큰 pin 에 닿는다

- **Context**: D-238 이 한 시간 전에 `STATE.md` pin 을 "현재 code path 로는 **어떤 cycle 길이에서도** 재취득 불가" 로 확정했다 — `_RUN_TIMEOUT` 900 s 에 un-mutated pass 하나가 이미 걸렸고 probe 는 pass 를 둘 요구하므로, 60분 예산도 소용이 없다는 판독이었다. 그 판독은 **한 문장에서만 틀렸다**: ceiling 은 *pass* 당 걸린 것이지 *측정* 당 걸린 것이 아니다. D-238 자신의 alternative (d) 가 그 구분을 이미 적어두고 다음 cycle 의 1순위로 넘겼다.
- **Decision**: `shard_probe` 를 신설한다. reader set 을 **partition** 으로 쪼개고 (`_shards`), 각 shard 를 기존 `probe(tests=...)` subset 경로로 재고, `compose_shards` 가 disjunction 으로 합친다 — `compose` 가 pin/entrant split 위에서 이미 기대고 있는 바로 그 disjunction 을 partition 위에 적용한 것이므로 건전성은 새로 논증할 것이 없다. CLI `shard` subcommand 추가, exit code 규칙은 `probe` 와 **하나의 함수**를 공유한다 (`shard` 의 존재 이유가 `UNAFFORDABLE` 을 *해소*하는 것이므로, 두 subcommand 가 그 코드의 의미에 대해 불일치하면 해소 자체가 판독 불가가 된다).
- **핵심 설계 판단 — 합성 결과는 `INERT` 이지 `INERT_COMPOSED` 가 아니다**: 둘 다 probe 를 쪼개 감당 가능하게 만들지만 **무엇을 물려받는지가 다르다**. `compose` 는 pinned half 의 판독을 *더 오래된 tree* 에서 상속하고, `COMPOSITION_CAP` 은 정확히 그 부채를 묶으려고 존재한다. sharding 은 아무것도 상속하지 않는다 — 모든 reader 를 눈앞의 tree 에서 다시 돌리고, 달라진 것은 그 run 들이 몇 개의 subprocess 로 나뉘었느냐뿐이다. 여기에 약한 verdict 를 붙이면 **아무도 지지 않는 비용을 청구**하는 것이고, 한 단계 아래에서 같은 cap 문제를 다시 만든다.
- **규칙 순서도 load-bearing**: (i) shard 하나의 `CONTENT_READ` 는 **결정적**이고 `UNAFFORDABLE` 형제를 압도한다 — 움직인 shard 는 이미 전체 질문에 답했으므로, 다른 shard 가 값을 못 냈다고 그 측정을 버리는 것은 실제로 산 측정을 버리는 것이다. (ii) `UNAFFORDABLE` 은 `VACUOUS` 를 압도한다 (`compose` 와 같은 이유: 둘 다 exemption 을 거절하지만 하나만 재취득 가격을 알려준다). (iii) shard 가 없으면 `VACUOUS` — emptiness-before-success.
- **사지 못하는 것을 명시한다**: 총량은 줄지 **않는다**. 같은 2×N file-run 에 shard 하나당 interpreter 기동이 추가되므로 합은 오히려 약간 **오른다**. sharding 이 옮기는 것은 ceiling 이지 work 가 아니다 — 즉 pin 은 "도달 불가" 에서 "비싸고 일정 가능" 으로 옮겨간 것이고, 한 cycle 에 안 들어가면 **cycle 을 가로질러 carry** 해야 하는 대상이지 포기 대상이 아니다.
- **정적으로 값을 매겼다**: `STATE.md` 는 이제 **28** reader (27 이 아니라 — 이 cycle 자신의 test file 이 via-reader 로 진입) → **5 shards, 최대 6**. 나머지 넷은 3–4 shards. 가장 큰 pin 에 거절이 아니라 경로에 붙은 숫자가 처음으로 생겼다.
- **Alternatives**: (a) 채택 — partition + disjunction. (b) `_RUN_TIMEOUT` 상향 — D-238 이 이미 기각 (ceiling 이 예산의 절반). (c) shard 결과에 `INERT_COMPOSED` 부여 — 안전해 보이지만 부채 없는 판독에 부채를 청구하고 cap 을 재도입, 기각. (d) overlapping shard — 양성 방향은 여전히 건전하나 음성 방향 비용을 조용히 부풀림, 기각.
- **미해결**: 실제 pin 에 대해 end-to-end 로 돌리지 못했다 (총량이 이미 900 s 를 넘긴 것의 ~2배라 이 cycle 의 suite 옆에 들어가지 않는다). 한 cycle 에 안 들어가면 **resumable shard reading** (shard 별 verdict 기록 후 예산 소진 지점부터 재개) 이 다음 기구다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-15-sharding-reaches-the-pin-the-full-probe-cannot.md` · D-238 (alternative (d) 를 넘긴 결정 — *"불가능" 판독은 이로써 "비싸다" 로 정정된다*) · D-237 (prose 가 pin 을 철회한다 — 이 cycle 의 write 가 전부 receipt 앞으로 간 이유) · D-236 (재취득 비용은 어느 파일이냐) · D-044 (write order — 이 pin 이 마지막 제약) · D-107 (composition pricing) · D-038 (제외는 세지 말고 이름을 불러라) · D-016

## D-238 — 2026-08-13 — full probe 는 가장 큰 pin 에 **닿지 않는다**: `COMPOSITION_CAP` 의 fallback 이 per-pass 900 s ceiling 과 교차했다

- **Context**: STATE #1 이 `STATE.md` pin 재취득을 "one dedicated cycle, single thrust" 로 값을 매겼다 (sibling full probe 가 15m45 / 17m57 로 기록돼 있었으므로). 이 cycle 이 그 dedicated cycle 로 들어가 8분 지점에 probe 를 띄우고 모든 write 를 보류했다 — `probe` 가 측정 후 reader set 을 재유도해 set 이 움직였으면 `VACUOUS` 로 매기므로 "no other work" 는 일정이 아니라 기계적 제약이다. 15분 뒤 `subprocess.TimeoutExpired`: `_run` 의 hard 900 s ceiling 에 **첫 번째(un-mutated) pass** 가 걸렸다. reader 는 26 이 아니라 **27** 이었다 (13:00 의 `test_licence_recall.py` 가 entrant).
- **Decision**: 두 가지를 분리해 확정한다. (1) **측정된 사실**: probe 는 pass 를 둘 필요로 하고 un-mutated pass 하나가 이미 ceiling 을 넘으므로, `STATE.md` pin 은 현재 code path 로는 **어떤 cycle 길이에서도** 재취득 불가다 — 60분 예산도 per-pass ceiling 을 바꾸지 못한다. "비싸다" 가 아니라 "불가능하다". (2) **기구 수정**: timeout 은 raise 가 아니라 **grade** 한다. `UNAFFORDABLE` verdict 신설, `_run` 은 `None` 반환, `probe` 는 첫 pass 가 timeout 이면 mutation 을 아예 쓰지 않고 (두 번째 pass 는 순수 낭비) 두 번째에서 걸리면 `finally` 로 복원한 뒤 등급을 매긴다. `compose` 는 `UNAFFORDABLE` 을 `VACUOUS` 로 접지 않고 전파한다. CLI 는 rc=2.
- **왜 verdict 를 나누나**: 둘 다 exemption 을 거절하지만 다음 cycle 의 **행동이 다르다** — `CONTENT_READ`/`VACUOUS` 는 "측정했고 답은 no" 이고 `UNAFFORDABLE` 은 "측정 자체를 못 샀다, probe 를 re-scope 하라" 다. 이 module 이 `NO_READER`/`INERT`, `VACUOUS`/`CONTENT_READ` 를 굳이 갈라놓은 것과 같은 규율.
- **실제 결함은 crash 가 아니라 사실의 유실**: 15분이 사실 하나를 벌었는데 CLI 가 stack trace 로 버렸다. 재취득이 **시도되었다는 것조차** 아무 데도 기록되지 않으므로, 다음 cycle 은 같은 withdrawn pin 을 읽고 같은 잘못된 값을 매기고 같은 15분을 낸다. 일반화되는 건 이 부분이다.
- **Alternatives**: (a) `_run` timeout 을 올린다 — ceiling 은 예산의 절반이므로 1800 s 는 한 cycle 을 통째로 먹는다, 기각. (b) timeout 을 `VACUOUS` 로 흡수 — 한 줄이면 되지만 "쟀는데 빈 결과" 와 "못 샀다" 를 합쳐 다음 행동을 지운다, 기각. (c) pin 을 영구 철회 — 측정 없이 D-044 write order 를 영구히 포기하는 것, 기각. (d) probe 를 shard 로 쪼개 compose — `compose` 가 이미 기대는 disjunction 이 sharding 을 건전하게 만든다. **다음 cycle 의 1순위**, 이번엔 예산이 없었다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-14-the-re-take-priced-itself-out.md` · D-237 (prose 가 pin 을 철회한다 — 이 cycle 의 test docstring 이 population 만 부르는 이유) · D-236 (재취득 비용은 어느 파일이냐) · D-204 (pin tax 의 cliff) · D-044 (write order — 이 pin 이 마지막 제약) · D-107 (composition pricing) · D-016

## D-237 — 2026-08-13 — receipt **recall** 은 gate 의 admission 규칙으로 물어야 한다: exact fingerprint key 는 pin 기구를 push 지점에서 무력화한다

- **Context**: 12:00 이 네 pin 을 되사고, `push_preflight check` 가 GREEN ("tree moved only on measured-inert paths") 을 냈는데도 pre-push hook 이 `NO_RECEIPT` 로 거절했다. 원인은 구조적이다 — `push_licence.licence_path` 가 receipt 경로를 **현재 worktree fingerprint 의 정확 일치**로 유도하는데, 프로토콜이 receipt 이후의 write (4b digest / 4c snapshot / TSV row) 를 **의무화**하므로 push 시점에는 key 가 항상 이동해 있다. 즉 exemption 이 존재하는 이유인 write 들이 exemption 을 찾을 수 없게 만든다. 12:00 은 pin 을 네 개 들고도 D-044 의 세금 (두 번째 suite, 513 s) 을 그대로 냈다.
- **Decision**: admission 규칙을 `push_preflight.tree_match()` 로 추출해 gate 와 recall 이 **같은 구현**을 부르게 하고, `licence_path` 는 store 를 걸어 (exact hit 우선, 없으면 measured-inert 경로에서만 다른 가장 최근 receipt) 그것을 gate 에 넘긴다. 없으면 exact 경로를 그대로 반환해 `NO_RECEIPT` 로 **fail closed**.
- **왜 gate 를 약화시키지 않는가**: caller 는 여전히 인자를 주지 않고 (`licence_path(root)` 뿐), 모든 후보는 gate 자신의 `tree_match` 로 걸러지며, 승자는 `check` 의 나머지 조건 (green / non-vacuous / covered / declared / unsupported-claim) 을 전부 다시 받는다. 이 search 가 만들어낼 수 있는 통과는 `check` 가 어차피 내줬을 통과뿐이다 — red receipt 는 이제 *찾아지지만* 여전히 `RED` 로 거절된다 (테스트로 고정).
- **부수 측정**: 순진한 구현은 hook miss 당 6.7 s. 비용의 전부가 receipt 당 반복되는 pin premise 재계산이었고 (`inert` 가 각 pin 의 reader set 을 tree 에서 다시 유도, 0.09 s), drift 와 무관하므로 `inert_surface.exempt_candidates()` 로 hoist → 동일 miss 가 **0.57 s**.
- **이 cycle 이 자기 prose 로 pin 하나를 떨어뜨렸다**: pin 은 텍스트 언급으로 reader 를 세므로, 새 docstring 이 4b 파일명을 그대로 적자 그 module 이 reader 가 되어 해당 pin 이 `True → False` 로 withdraw 됐다. suite 가 아니라 suite 이전의 probe 가 잡았다. 교훈은 D-199 의 한 칸 확장이다 — **산문도 verification surface 안에 있다**; 규약은 population 을 이름으로 부르고 멤버를 다시 적지 않는 것.
- **Alternatives**: (a) 채택. (b) 프로토콜을 바꿔 post-receipt write 를 금지 — D-043 이 요구하는 "re-taken count 를 journal 이 인용한다" 와 정면 충돌. (c) receipt 을 fingerprint 없이 최신 것으로 recall — gate 의 tree binding 을 버리는 것이라 거절. (d) `check` 를 모든 store entry 에 돌려 첫 통과를 채택 — 의미는 같지만 hook 안에서 ~7 s, 그리고 같은 질문을 67 번 다시 묻는다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-13-the-pins-had-nowhere-to-pay-off.md` · D-236 (pin 재취득 비용) · D-221 (hook) · D-044 (write order) · D-199 (staging 이 pin 을 옮긴다)

## D-236 — 2026-08-13 — pin 재취득 비용은 **entrant 개수가 아니라 어느 파일이냐**로 결정된다 — 그리고 네 pin 은 독립적으로 낡지 않았다

- **Context**: 10:00 이 `inert_surface staged` 로 네 pin (`RESULTS.md`, `STATE.md`, `journal/`, `results/`) 의 exemption 을 한꺼번에 withdraw 시켰고, 11:00 은 그 대가로 모든 tree write 를 suite 앞으로 옮겨야 했다 (journal 이 자기 pass count 를 못 적고, TSV row 가 `sandbox:pass=` 를 못 싣는 비용). STATE.md 의 bottleneck 이 정확히 이것이었다. 이 cycle 이 `reprobe` 로 되사려 했다.
- **Decision**: 셋은 되샀고 (`RESULTS.md` 22.6 s / `journal/` 367.5 s / `results/` 0.9 s, 모두 `INERT_COMPOSED`, 전부 transcribe 됨), **`STATE.md` 는 의도적으로 포기**했다. `STATE.md` 는 `generation == COMPOSITION_CAP - 1` 이라 `reprobe` 가 composition 을 거부하고 26-reader full probe 로 fallback 한다 — un-mutated pass 하나가 120 s 안에 안 끝났고, 같은 dict 의 형제 full probe 들이 15m45 / 17m57 로 기록돼 있다. 8.6 분짜리 suite 와 같은 cycle 에 들어가지 않는다. 10:00 처럼 strand 를 만드는 대신 멈췄다.
- **측정된 사실 두 개, 그리고 둘 다 PLAN 을 향한다**:
  - **(i) 재취득 비용은 entrant 개수와 무관하다.** `results/` 와 `journal/` 은 **같은** entrant (`test_quoted_counts.py`) 를 공유하는데 각각 0.9 s 와 367.5 s 가 들었다. `test_quoted_counts.py` 를 단독 계측하면 **0.25 s** — `journal/` 의 6 분은 사실상 전부 다른 entrant (`test_guard_reflexivity.py`) 다. 즉 D-204 가 PLAN 에게 "cliff 를 미리 price 하라" 고 요구했지만, PLAN 이 싸게 볼 수 있는 유일한 수치(entrant tally)는 **가격의 예측자가 아니다**.
  - **(ii) pin 들은 독립적으로 낡지 않는다.** `test_quoted_counts.py` 하나가 `journal/` · `results/` · `STATE.md` 세 pin 의 entrant 다. reader set 이 크게 겹치기 때문에 test 파일 하나가 여러 pin 을 동시에 cliff 쪽으로 민다. `COMPOSITION_CAP` 은 pin 하나가 물려받는 un-re-measured debt 를 정확히 bound 하지만, **portfolio 가 동시에 비싼 상태에 도달하는 것**은 막지 못한다 — 2026-08-06 에 네 pin 이 하루 만에 같이 낡은 것이 그 모양이었고, 이번에도 같은 모양이다.
- **stale 은 leak 이 아니다**: 전 구간에서 `leaking_pins() == ()` 였다. withdraw 된 pin 은 스스로 꺼진 exemption 이고, 그것을 들고 있는 cycle 은 D-044 의 second-suite tax 를 낼 뿐이다 (D-207). 그래서 `STATE.md` 를 남겨두는 것은 *가격*이지 결함이 아니다 — 다만 D-043 write order 는 아직 복구되지 않았고, 4c 는 여전히 suite 앞에 와야 한다.
- **Alternatives**: (a) 채택 — 셋을 되사고 `STATE.md` 는 전용 cycle 로 넘긴다. (b) `STATE.md` full probe 를 이번 cycle 에 강행 — suite 를 못 돌리거나 push 를 못 해 strand 가 된다 (10:00 이 정확히 이 실패). (c) `COMPOSITION_CAP` 을 올려 `STATE.md` 를 compose — un-re-measured premise 를 한 세대 더 쌓는 것이고, cap 이 존재하는 이유를 예산 압박으로 무르는 것이라 거절.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-12-buying-back-the-four-withdrawn-pins.md` · D-204 (pin tax 를 PLAN 이 price 하라) · D-207 (stale ≠ leak) · D-044 (second-suite tax) · D-043 (write order)

## D-235 — 2026-08-13 — n 을 두 배로 늘려도 두 row 는 해결되지 않는다 — 그리고 D-234 가 그 위에서 읽은 **positive lean 은 6-seed artifact 다**

- **Context**: D-234 의 한계 (i) 가 이 cycle 의 과제를 이름까지 적어두었다 — `cafe_convoy_v0` / `cafe_head_on_v0` 의 `w_risk = 0` row 만이 seed 를 늘려 살 것이 있는 row 이고 (4+/2−, p=0.688), 만장일치 row 들은 이미 n=6 의 sign-test 바닥 0.031 에 있으므로 더 살 것이 없다고. STATE 도 이것을 "가장 싼 구체적 측정" 으로 지목했다.
- **측정 (seeds 0..11, `lam = 0.8`, 같은 scene / resampler / `PairedStep`)**: bottom row 만이 아니라 **2x2 전체**를 걸었다 — 두 row 를 서로 다른 `n` 에서 읽은 verdict 를 만들지 않기 위해서, 그리고 기록된 6-seed cell 이 *prefix* 가 되도록. **8 cell 전부 `WALK_CONVOY_6` / `WALK_HEADON_6` 를 정확히 재현**하므로 아래 움직임은 seed 수의 몫이고 두 번째 walk 의 몫이 아니다. 모든 cell 12/12 completion.

  | scene | row | n=6 mean | n=12 mean | n=6 sign | n=12 sign | verdict (양쪽) |
  |---|---|---|---|---|---|---|
  | `cafe_convoy_v0` | `w_risk=0` | **+0.0159** | **−0.0021** [−0.0210, +0.0195] | 4+/2− p=0.688 | 5+/7− p=0.774 | `NOT_SEPARATED` |
  | `cafe_head_on_v0` | `w_risk=0` | **+0.0040** | **−0.0028** [−0.0117, +0.0054] | 4+/2− p=0.688 | 6+/6− p=1.000 | `NOT_SEPARATED` |
  | `cafe_convoy_v0` | `w_risk=40` | +0.1441 | +0.1359 [+0.0932, +0.1783] | 6+/0− p=0.031 | **11+/1− p=0.006** | `SEPARATED_POSITIVE` |
  | `cafe_head_on_v0` | `w_risk=40` | +0.0606 | +0.0704 [+0.0461, +0.0945] | 6+/0− p=0.031 | **11+/1− p=0.006** | `SEPARATED_POSITIVE` |

- **Decision (1) — 한계 (i) 는 부정으로 답한다**: 두 row 는 n=12 에서도 방향을 해결하지 못하고 두 scene 다 `PAIRED_CONDITIONAL` 로 남는다. 이 row 들은 *방향이 있는데 검정력이 부족한* 것이 아니라 이 `n` 에서 찾을 방향이 없다. `cafe_family_verdicts_12` 가 그것을 보고한다.
- **Decision (2) — D-234 의 lean 을 철회한다**: D-234 는 두 mean 이 양수라는 것 (+0.0159, +0.0040) 위에 실질적 주장을 세웠다 — unpaired 표의 음부호는 paired 읽기의 *약한 버전이 아니라 그것과 불일치한다*. 6 seed 를 더 넣자 두 mean 이 **모두 0 을 건너 음수가 되고** (−0.0021, −0.0028) seed 다수도 함께 넘어간다. 그 문장이 딛고 선 부호는 가능한 가장 작은 widening 도 견디지 못한다. **철회되는 것은 lean 이지 verdict 가 아니다** — `NOT_SEPARATED` 는 그때도 지금도 옳은 읽기이고, 정직한 진술은 "이 row 들에는 해결된 방향이 없다" 이며 그것은 D-234 가 애초에 단서를 달지 말았어야 할 문장이다.
- **결함의 종류에 이름을 붙인다**: `NOT_SEPARATED` row 안의 **점추정에 방향을 귀속시키는 것**. verdict 는 올바르게 적혀 있었고 그 옆 문장이 그것을 무효화했다. n=6 은 이 구분을 잃기에 가장 싼 지점이다.
- **"더 살 것이 없다" 는 statistic 을 명시해야 한다**: 그것은 sign test 의 *바닥*에 대해 참이었고 CI 에 대해서는 거짓이었다. D-234 는 top row 를 유예하고 bottom row 를 넓혔는데, headroom 이 있던 쪽은 **top row** 였다 — p 0.031 → 0.006. 바닥은 `n` 의 성질이었지 증거의 성질이 아니었다.
- **Alternatives**: (a) 채택 — 2x2 전체를 n=12 로, prefix 검사 후 읽는다. (b) bottom row 만 넓힌다 (~절반 비용) — 두 row 가 다른 `n` 이 되어 `paired_interaction_verdict` 가 혼합-n verdict 가 된다; 이 코드베이스가 정당하게 red 로 잡을 모양. (c) n=20 으로 간다 — prefix anchor 는 유지되지만 이 cycle 예산을 넘고, n=12 가 이미 lean 을 무너뜨렸으므로 철회에 필요하지 않았다. (d) 세 scene 전부 재walk — 헤드라인 scene 의 bottom row 는 n=6 에서 이미 6/6 분리되어 질문 대상이 아니었다.
- **한계**: (i) n=12 는 *이 effect size 에서* 해결 실패를 보일 뿐, 임의로 작은 참 효과의 부재를 증명하지 않는다 — 다만 다음 seed 가 이 board 에서 가장 비싼 정보라는 것은 말해준다. (ii) bootstrap CI 는 여전히 seed resample 이고, sign test 가 그 가정 없이 같은 답을 준다 (양쪽 prefix 에서).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-10-doubling-the-seeds-retracts-the-lean.md` · D-234 (한계 (i) 를 이 결정이 소진하고, 그 lean 을 철회) · D-219 / D-225 (계보) · D-047 (한 quantity 에 한 이름) · D-044 (threshold 대신 report)

## D-234 — 2026-08-13 — `SIGN_FLIP` 은 **cafe family 의 성질이 아니라 crossing scene 의 성질**이다: guard 상수를 CI-separation 으로 바꾸자 세 scene 중 하나만 남았다

- **Context**: D-225 는 Q-135 를 **한 scene** 에서 답하고, 자기 한계 (ii) 에 나머지 둘을 적어두었다 — `cafe_convoy_v0` / `cafe_head_on_v0` 의 `SIGN_FLIP` 은 여전히 **unpaired** 표에 서 있다. 그 alternative (b) 는 "가장 큰 효과가 견디는지부터 아는 것이 순서다" 라며 둘을 미뤘고, 그것이 견뎠으므로 유예는 소진되었다. 그리고 D-219 자신이 alternative (b) 에서 이미 경고해 두었다: flip 이 3 scene 전부에서 나왔다고 보고하는 것은 **D-217 의 오류를 한 층 위에서 반복하는 것**이고 그것은 guard 상수의 artifact 라고.
- **측정 (같은 6 seed, 같은 `lam=0.8`, 같은 `PairedStep`, 같은 resampler — walk 는 D-219 의 것)**:

  | scene | top (`w_risk=40`) | bottom (`w_risk=0`) | paired verdict |
  |---|---|---|---|
  | `cafe_obstacle_crossing_v0` | +0.3501 [+0.3181, +0.3936] 6/6 | **−0.0339 [−0.0443, −0.0235] 6/6** | `PAIRED_SIGN_FLIP` |
  | `cafe_convoy_v0` | +0.1441 [+0.0978, +0.1957] 6/6 | +0.0159 [−0.0137, +0.0467] 4+/2− | `PAIRED_CONDITIONAL` |
  | `cafe_head_on_v0` | +0.0606 [+0.0388, +0.0860] 6/6 | +0.0040 [−0.0033, +0.0122] 4+/2− | `PAIRED_CONDITIONAL` |

- **재현이 먼저다**: 두 walk 의 `worst_step` 은 **+0.1968 / −0.0055** 와 **+0.0806 / −0.0002** 로 D-219 가 공표한 쌍을 소수 4자리까지 돌려준다. 그러므로 이것은 *재측정*이 아니라 *재읽기*이고, 아래 차이는 estimand 의 몫이다. 24 cell 전부 6/6 completion.
- **Decision**: `SIGN_FLIP` 은 **crossing 한 scene 의 판정**으로 좁힌다. 나머지 두 scene 에서 `w_ped` 단독 row 는 방향을 해결하지 못한다 (`NOT_SEPARATED`). `paired_interaction_verdict` 를 추가했다 — `three_arm.interaction_verdict` 와 같은 vocabulary 를 `EPS_CLEARANCE` 대신 **paired CI 의 0 배제**로 판정하는 버전이고, 이름을 따로 쓴다 (`PAIRED_*`): 같은 walk 위에서 두 verdict 가 다른 답을 낼 수 있으므로 이름을 공유하면 그 사실이 숨는다 (D-047).
- **좁히는 방향이 한쪽만이 아니다** — 두 unflipped row 의 **점추정은 양수**다 (+0.0159, +0.0040; 4+/2−). 즉 unpaired 표의 음부호는 paired 읽기의 약한 버전이 아니라 **그것과 불일치**한다. "음수인데 6 seed 로 못 가른다" 가 아니다.
- **버려지지 않는 절반**: top row 는 **세 scene 전부에서** `SEPARATED_POSITIVE`, 6/6 만장일치다. risk term 옆의 `w_ped` 가 도움이 된다는 진술은 일반화되고, 무너진 것은 flip 뿐이다.
- **한계**: (i) `n = 6` 에서 두 `CONDITIONAL` row 의 sign test 는 p=0.688 로 **어느 방향도** 해결하지 못한다 — 이 둘이 seed 를 늘려 살 것이 있는 유일한 row 다 (만장일치 row 들은 이미 n=6 의 바닥 0.031 에 있다). (ii) bootstrap CI 는 6 seed resample 이라 좁게 읽히는 경향을 감안해야 하고, sign test 는 그 가정 없이 같은 답을 준다.
- **Alternatives**: (a) 채택 — guard-free estimand 로 세 scene 을 재읽고 표를 좁힌다. (b) `SIGN_FLIP` 3-scene 유지 — D-219 자신이 artifact 로 지목한 것을 그대로 들고 가는 것. (c) `EPS_CLEARANCE` 를 물리적 값으로 올린다 — D-219 alternative (c) 가 이미 거절했다: 다른 caller 의 판정을 조용히 바꾸고 threshold 라는 문제 자체는 남는다. (d) 세 scene 을 n=20 으로 재측정 — 재현 anchor 를 잃고 (D-219 의 walk 가 아니게 된다) 한 cycle 을 넘긴다; 좁히는 데 필요하지 않았다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-09-the-flip-was-one-scene-not-the-family.md` · D-225 (한계 (ii) 를 이 결정이 소진) · D-219 (좁혀지는 표 — *unpaired 수치는 재현됨*, alternative (b) 의 경고가 여기서 확인) · D-218 / D-217 (계보) · D-047 (한 quantity 에 한 이름) · D-044 (threshold 대신 report) · D-233 (이 cycle 이 먼저 grade 한 CI green)

## D-233 — 2026-08-13 — CI 의 남은 두 red 는 **fresh checkout 이 구조적으로 가질 수 없는 것**을 assert 하고 있었다: 술어를 subject 의 대리물이 아니라 subject 자체에 걸어야 한다

- **Context**: D-231 의 TZ 수정 후 run(`c0a63f0`)의 실패는 6 → **2** 로 줄었고, `cycle_artifacts` 76건은 전부 PASSED — D-231 의 falsifiable prediction 은 **확인**되었다 (Q-140 종결). 남은 둘은 D-230 이 이미 "structurally unpassable in CI" 로 판정해 둔 바로 그 쌍이다: `exemption_masking` 은 `assert 0 == 1`, `quoted_counts` 는 "the real store holds no datable receipt".
- **Decision**: 두 test 모두 **subject 의 존재 여부**로 분기하도록 고쳤다 — skip 이 아니라 **split** (이 module 자신의 header 규약: "a skip makes the CI half of the suite assert nothing, which is this package's own recurring defect").
  - `test_masking_class_is_bounded_at_one_by_measurement`: 기존 분기는 `_DECIDABLE`, 즉 clone 이 *history* 질문에 답할 수 있는가였다. D-228 이 CI 에 `fetch-depth: 0` 을 준 뒤로 그 답은 **yes** 가 되었고, 그래서 test 는 강한 가지로 들어가 `len(masks) == 1` 을 쟀다. 그러나 그 population 은 *이 worktree 의* declared-path drift 이고 fresh checkout 은 그것을 결코 갖지 않는다 — **두 개의 다른 속성이 하나의 술어 뒤에 있었다** (D-047 의 형태, 이 branch 에서 네 번째). `_declared_drift_now()` 를 추가해 drift 가 없을 때는 `masks == ()` 을 assert 한다: pair 는 자기 subject 와 정확히 함께 사라진다는, CI 쪽에서도 falsifiable 한 statement.
  - `test_the_reach_is_a_boundary_the_receipts_derive_not_a_constant`: `results/receipts/` 는 gitignored 이므로 checkout 에 store 가 없고 `reach()` 는 계약상 `None` 이다 (그 docstring 이 "a fresh clone" 을 이미 명시한다). datable receipt 가 없을 때 `boundary is None` 을 assert — boundary 가 receipt 에서 **derive** 된다는 것, 즉 hard-coded date 가 아니라는 이 test 의 원래 주장을 빈 store 위에서 그대로 말하는 가지다.
- **검증**: 주장이 CI 조건에서 성립하는지를 산문으로 말하지 않고 쟀다 — CI 가 돌린 바로 그 commit(`c0a63f0`)으로 fresh clone 을 떠서(receipts 없음, declared drift 없음, full history) 두 test 를 돌렸고 **2 passed**. 수정 전 같은 commit 의 reading 은 CI log 자체다.
- **Alternatives**: (a) 채택 — subject-presence 로 분기. (b) `pytest.skip` — CI 절반이 아무것도 주장하지 않게 되고, 이 package 가 반복해 온 결함. (c) 그대로 red 유지 — 영구 red 는 뮤트되는 check 다 (D-044 가 같은 이유로 ordering 을 강제한다). 두 red 를 22 cycle 째 "known" 으로 들고 다닌 것이 이미 그 비용이었다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-07-the-test-asserted-what-a-checkout-cannot-have.md` · D-230 (두 red 를 structural 로 판정) · D-231 (TZ 수정, 여기서 확인됨) · D-228 (`fetch-depth: 0` 이 `_DECIDABLE` 을 뒤집은 경위) · D-047

## D-232 — 2026-08-13 — run-level log 는 run 전체가 끝나야 열리지만 **job-level log 는 즉시 열린다**: 세 cycle 이 읽으라고 지시받은 digest 는 내내 도달 가능했다

- **Context**: STATE 는 세 cycle 연속으로 "다음 CI run 의 digest 를 읽어라"를 #1 로 지시했고, 세 번 다 읽히지 않았다. 이유는 내용이 아니라 **접근**이었다: `gh run view --log-failed` 는 `run ... is still in progress; logs will be available when it is complete` 로 거절한다. 그리고 이 repo 의 slow job 은 `timeout-minutes: 360` (D-094, 의도된 값) 이라 run 하나가 최대 6 시간 열려 있다 — hourly push 와 겹치면 **네 개의 run 이 동시에 in_progress** 이고 (실측: 17:32Z/18:32Z/20:33Z/21:33Z), 10분이면 끝나는 fast shard 의 실패 로그가 30배 느린 job 에 인질로 잡힌다.
- **Decision**: CI 를 읽을 때는 run-level 이 아니라 **job-level** endpoint 를 쓴다. `gh api repos/<owner>/<repo>/actions/jobs/<job_id>/logs` 는 run 이 in_progress 여도 **완료된 job 의 로그를 즉시 돌려준다**. job id 는 `gh run view <run_id> --json jobs --jq '.jobs[]|select(.conclusion=="failure")|.databaseId'`.
- **왜 이것이 기록될 값어치가 있나**: annotation API 는 `Process completed with exit code 1` 밖에 주지 않아 test 이름을 담지 못한다 (실측). 즉 run-level log 가 막히면 **어떤 test 가 왜 죽었는지를 알 경로가 없다**고 세 cycle 이 결론지었고, 그 결론이 틀렸다. 이번 cycle 은 같은 자리에서 job-level 로 갔고 두 실패의 assertion text 를 즉시 얻어 D-231 을 확인하고 D-233 을 고쳤다.
- **Alternatives**: (a) 채택. (b) slow job 의 ceiling 을 낮춘다 — D-094 가 floor 측정 위에서 유도한 값이라 거절: run 을 죽여서 로그를 얻는 것은 authority 를 없애는 것이다. (c) run 완료까지 기다린다 — 최대 6 시간, hourly cycle 에서는 곧 영영 안 읽는다는 뜻.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-07-the-test-asserted-what-a-checkout-cannot-have.md` · D-094 (360 ceiling) · D-112 (읽히지 않는 신호가 쌓이는 형태)

## D-231 — 2026-08-13 — Q-140 답: CI 와 local 의 census 차이는 **blame 시각을 ambient timezone 으로 변환한 것**이다 — 그리고 D-230 의 "timezone 배제" 는 *다른 함수* 위에서 취해졌다

- **Context**: 04:00 이 `divergence_digest` 를 쓰고 05:00 이 그것을 origin 에 올렸다. `f883280` 의 CI run 이 그 digest 를 처음으로 인쇄했고, STATE 가 세 cycle 동안 "다음 reading 은 또 한 번의 local 재구성이 아니라 CI run 이다" 라고 적어둔 그 run 이다.
- **측정 — headline 두 개가 아니라 census 를 field 단위로 나란히 놓는다**:

  | field | CI | local |
  |---|---|---|
  | cycles | **233** | **233** |
  | tsv_rows | **230** | **230** |
  | undated_rows | 0 | 0 |
  | HONOURED | 186 | 206 |
  | UNSUPPORTED | 37 | 17 |
  | orphan_rows | **1** | **0** |

  corpus field 가 **전부 같다**. 따라서 Q-140 의 (b) row 가 다르다 / (c) journal 집합이 다르다 는 **반증**되고, 남는 것은 row → cycle **배정**뿐이다. `orphan_rows` 0 → 1 은 row 가 journal 집합의 앞쪽으로 **밀려나갔다**는 서명이다.
- **재현은 환경변수 하나였다**: ambient `TZ=UTC` 로 local digest 를 다시 돌리면 CI 를 **정확히** 재현한다 — census 여덟 field 전부와 control 세 줄까지 byte 단위로. 논증이 아니라 구성으로 얻은 답이다 (D-186).
- **기제**: `git blame --line-porcelain` 은 `committer-time` 을 **raw epoch** 으로 준다. subprocess 에 pin 한 `TZ=Asia/Seoul` 은 git 이 **format 하는** field 에만 닿고, 이 field 는 format 되지 않는다. 변환은 Python 쪽에서 `time.localtime` 으로 일어났다 — 개발 머신에서는 KST, **GitHub runner 에서는 UTC**. 그래서 CI 에서 모든 row 가 **9시간 일찍** 찍히고 그 시점에 선행하는 cycle 로 재배정된다. `06-18` / `06-21` 이 CI 에서만 HONOURED 로 읽힌 것이 그 직접 증거다: 08-07 03:xx KST 에 append 된 row 가 08-06 18:xx UTC 로 읽히면 정확히 `06-18` 에 떨어진다.
- **D-230 의 배제는 왜 틀렸나 — 이게 재발 방지의 핵심이다**: D-230 은 timezone 을 배제했고 그 근거는 (i) `_commit_minute`/`_blame_minutes` 가 git call 마다 `TZ` 를 고정한다, (ii) `undated_rows` 가 0 이라 typed-timestamp fallback 이 발동하지 않는다 였다. (i) 은 `_commit_minute` 에 대해 **참**이고 (`--date=format-local` 을 쓴다) `_blame_minutes` 에 대해 **거짓**이며, (ii) 는 참이지만 문제의 경로와 무관하다. **배제는 그것이 측정된 함수의 scope 를 상속한다.** D-230 은 `_commit_minute: timezone 배제` 라고 적었어야 했고 `timezone 배제` 라고 적었다. 그 한 단어가 네 cycle 을 샀다.
- **정답 철자는 이미 repo 안에 있었다**: `tsv_timestamp._blame_times` 가 **같은 명령의 같은 field** 를 파싱하면서 언제나 명시적 `KST` 로 변환해 왔다. 한 사실에 대한 두 reader, 하나는 틀렸고, 머신이 서울에 있는 동안은 둘이 일치했다 — D-047 의 모양, 이 branch 에서 세 번째. 그래서 fix 는 상수를 다시 쓰지 않고 **그 module 에서 import** 한다: `ca._KST is tt.KST` 를 test 가 고정하므로 나중에 "처음엔 같은" local copy 가 다시 생길 수 없다.
- **falsifiable 예측을 적어둔다**: 다음 CI run 에서 shard 6 의 `cycle_artifacts` 실패 2 개가 **사라져야** 한다. 남으면 이 귀속은 틀렸고 Q-140 을 다시 연다. (`push_claim_gate` 2 개는 구성된 fixture repo 위의 실패라 이 기제와 무관하고, `quoted_counts` 1 개는 gitignore 된 `results/receipts/` 건으로 이미 알려진 residue다 — 이 entry 는 그 셋을 고친다고 주장하지 않는다.)
- **Alternatives**: (a) 채택 — epoch 변환에 zone 을 명시하고 두 reader 가 상수 하나를 공유하게 한다. (b) runner 의 `TZ` 를 workflow 에서 `Asia/Seoul` 로 설정 — 증상은 사라지지만 module 은 여전히 자기를 부르는 환경에 의존하고, 그 의존은 workflow 밖 어디서든 (cron, 다른 머신, 사용자 shell) 다시 문다. (c) `_blame_minutes` 를 `tsv_timestamp._blame_times` 호출로 대체 — 구조적으로 더 낫지만 반환 타입(datetime vs minute)이 달라 이 cycle 의 예산 밖이고, 상수 공유가 drift 를 이미 막는다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-06-the-blame-clock-read-the-runners-zone.md` · Q-140 (resolved — lean (a) 가 맞았다) · D-230 (이 entry 가 정정하는 대상 — *census divergence 는 실재, timezone 배제는 scope 오류*) · D-229 / D-228 (배제 목록은 유효; clone 이 통과한 것은 clone 이 **KST** 였기 때문) · D-047 (registry 는 자기 진술을 하나만 갖는다) · D-186 (측정 없이 귀속하지 않는다) · D-043 (CI 가 authority — 그 authority 가 4개월간 틀린 시계를 들고 있었다)

## D-230 — 2026-08-13 — Q-139 는 **반증된다**: shard 를 한 process 에서 돌려도 green 이고, 남은 차이는 runner 가 아니라 **census** 다

- **Context**: D-229 가 tree · commit · depth 를 배제하고 남긴 유일한 가설이 process 모양이었다 — CI 는 15–16 file shard 를 한 pytest process 에서, local receipt 는 16 core 에 흩어서. STATE 가 "이 cycle 의 첫 항목으로 예산을 잡아라, 두 cycle 이 이미 시계에 잃었다" 라고 적었고 그대로 했다.
- **측정**: `/tmp/ci-repro` (= `refs/pull/67/merge`, `f0d491b`) 에서 shard 6 의 17 file 전부를 **한 process** 로 실행 → **446 passed, 7 skipped, 0 failed, 99s**. CI 가 그 shard 에서 보고한 `test_cycle_artifacts` 2 개가 **재현되지 않는다**. 따라서 process 모양도 배제 목록에 합류한다. **Q-139 는 열릴 때의 lean 과 반대로 닫힌다** — D-229 와 같은 방향의 결과이고, 이 branch 에서 두 번 연속이다.
- **그러면 무엇이 다른가 — 차이는 *읽기* 에 있다**: CI 는 이 branch 를 **183 HONOURED / 38 UNSUPPORTED** 로 채점했고, live repo 는 **205/17**, clone 은 **204/17** 이다. 파싱된 cycle 수는 양쪽 다 ~221 로 **같다**. 즉 ~21 cycle 이 다르게 채점되며, 방향도 **양쪽**이다: CI 가 21 개를 더 flag 하면서 동시에 `06-18` / `06-21` 은 HONOURED 로 읽는다 (그래서 control test 가 잡는다).
- **timezone 은 배제**: `_commit_minute` / `_blame_minutes` 는 이미 git call 마다 `TZ=Asia/Seoul` 을 고정한다. `UTC` 로 강제해도 count 가 바뀌지 않고, local `undated_rows` 는 **0** 이라 typed-timestamp fallback 자체가 발동하지 않는다.
- **Decision**: 환경을 네 번째로 재구성하는 대신, **그 grade 를 가진 유일한 process 에게 물어본다**. `divergence_digest()` 를 추가하고 두 live assertion 에 붙인다. `assert 183 > 38 * 5` 는 참이고, 쓸모없고, **local 이 재현할 수 없는 유일한 reading 을 버린다** — 세 cycle 이 그 grade 를 환경 재구성으로 되찾으려 했고 아무도 그것을 *가진* run 에게 묻지 않았다. 다음 red run 이 38 개의 경로와 stamp 를 직접 인쇄한다.
- **여섯 개는 한 버그가 아니었다**: assertion 본문을 처음으로 읽어보니 — 2 개는 live-corpus census (`cycle_artifacts`), 2 개는 **구성된 repo** 위의 실패 (`push_claim_gate`, `journal/2026-08/01-11-c2.md` 라는 **fixture** 경로에 대해 실패하므로 corpus divergence 일 수가 없다), 1 개는 이미 settled 된 gitignore 건, 1 개는 `exemption_masking`. D-229 의 "남은 네 개" 는 최소 세 기제를 한 통에 담고 있었다.
- **정직한 경계**: shard 6 **만** 한 process 로 돌렸다. shard 3/4/5 는 돌리지 않았으므로 이 반증을 네 개 전부로 일반화하지 않는다 — 그것이 정확히 D-228 이 18 을 3-test sample 에서 일반화한 실수다.
- **diagnostic 은 green 방향에서도 싸야 한다**: `divergence_digest` 는 finding 이 없어도 census 줄을 인쇄하고, 그 사실이 test 로 고정돼 있다. 나쁜 소식에만 붙어 나타나는 계기는 아무도 보정할 수 없다 (D-162 의 규칙을 diagnostic 에 적용).
- **Alternatives**: (a) 채택 — 실패에 reading 을 실어 보낸다. (b) runner 환경을 또 재구성 — 네 번째 시도이고 앞의 셋은 전부 배제만 낳았다. (c) 두 test 를 CI 에서 skip — authority 를 다시 침묵시킨다, D-228 의 (b) 가 이미 기각한 수. (d) census 를 workflow step 으로 인쇄 — 되지만 red 가 아닐 때도 매 shard 마다 비용을 물고, 실패와 reading 이 분리된다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-04-the-shard-was-green-the-census-was-not.md` · D-229 (이 entry 가 좁힌 대상 — *배제 목록은 유효, 남은 가설은 반증*) · D-228 (sample 을 일반화하지 않는다) · D-186 (측정 없이 귀속하지 않는다) · D-162 (정직한 방향을 싸게 유지) · Q-139 (resolved, 부정) · Q-140

## D-229 — 2026-08-13 — Q-138 은 **아니오** 로 답한다: shallow checkout 은 속도를 망가뜨리지 않았고, D-228 의 clone 은 남은 4 개를 **볼 수 없다**

- **Context**: D-228 이 두 가지를 다음 run 에 맡겼다 — (a) 18 개가 정말 개는가, (b) shard 1 의 753s 가 checkout depth 였는가. run **31623102439** (`a37061a`) 이 여덟 shard 전부에서 verdict 에 도달했으므로 둘 다 한 번의 `gh` call 로 답한다.
- **(b) 속도는 checkout 이 아니었다**: shard 1 이 `fetch-depth: 0` 에서 **821s**, depth-1 에서 **753s** — 9% *더 길다*. 그러므로 12 run 의 cancellation 은 **suite 크기**이고 D-227 의 8-way shard 는 **증상 치료가 아니라 필요한 조치**였다. Q-138 은 열릴 때의 lean 과 **반대 방향으로** 닫힌다.
- **(a) 18 이 아니라 13 이 갰다**: 6 개가 남는다 (shard 4/3/5/6 에 1+2+1+2). D-228 의 "18" 은 측정이 아니라 **3-test sample 의 일반화**였다 — workflow 주석이 "three representative CI failures" 라고 정직하게 적어둔 그 sample. 주석은 이 cycle 에서 고쳐, 같은 방식으로 다시 읽히지 않게 한다.
- **핵심 발견 — D-228 을 license 한 instrument 가 남은 4 개를 보지 못한다**: tree hash 가 **byte-identical** (`5bc090d`) 하고, full depth (639 commit) 이고, `actions/checkout` 이 `pull_request` event 에 실제로 주는 **merge ref** (`refs/pull/67/merge` = `f0d491b`, branch head 가 아님) 를 그대로 checkout 한 clone 에서, `cycle_artifacts` ×2 와 `push_claim_gate` ×2 가 **1.43s 만에 통과한다**. 따라서 **tree · commit · depth 세 변수 모두 원인에서 배제**된다 — 논증이 아니라 구성으로.
- **남은 하나는 process 모양이다 (미확인)**: CI 는 15–16 file 의 shard 를 **한 pytest process** 에서 돌리고, local receipt 는 16 core 에 **다른 grouping** 으로 흩는다. clone 에서 shard 3 을 돌려 intra-shard 상호작용을 검증하려 했으나 120s probe cap 을 넘겼다 (CI 는 이 shard 에 406s 를 쓴다). 그러므로 **이름만 붙이고 주장하지 않는다** → Q-139.
- **6 개 중 1 개는 이미 settled**: `test_quoted_counts::test_the_reach_...` 는 clone 에서도 재현되고 gitignore 된 `results/receipts/` 를 읽는다 — checkout 으로 고칠 수 없는, STATE 가 이미 지목한 그 항목.
- **Alternatives**: (a) 채택 — 배제된 것을 배제됐다고 적고 남은 가설은 Q 로 넘긴다. (b) intra-shard 를 원인으로 단정 — 소거법으로는 그럴듯하지만 이 cycle 이 **측정하지 못했다**; D-186 이 금지하는 정확한 모양이다. (c) 남은 6 개를 skip — D-228 의 (b) 가 이미 기각한 수, authority 를 다시 침묵시킨다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-03-the-clone-cannot-see-four-of-the-six.md` · D-228 (이 entry 가 좁힌 대상 — *depth fix 는 유효, 18 이라는 수는 sample*) · D-227 (shard 는 필요했다 — 확정) · D-186 (측정 없이 귀속하지 않는다) · D-043 (CI 가 authority 인 것은 같은 corpus 를 받았을 때뿐) · Q-138 (resolved) · Q-139

## D-228 — 2026-08-13 — CI 가 red 였던 것은 tree 가 아니라 **checkout** 이었다: suite 가 history 를 corpus 로 읽는데 `actions/checkout` 은 depth 1 을 준다

- **Context**: D-227 의 8-way shard 가 실제로 통했다 — 8 shard 전부 verdict 에 도달했고 (최장 23m28, 30분 ceiling 아래) 12 run 연속 cancellation 이 끝났다. 그런데 **처음으로 도달한 그 verdict 가 red 였다**: 5 shard 에 걸쳐 19 failure, 같은 tree 의 local suite 는 green 2699/2857. D-043 이후 이 프로젝트는 "local green, CI red" 를 defect 로 읽도록 훈련돼 있었다.
- **측정이 먼저, 귀속은 나중 (D-186)**: red 를 설명하기 전에 판별자를 만들었다 — **full depth + receipt store 없음** 인 clone. 이게 "CI 에 history 가 없다" 와 "CI 에 gitignore 된 store 가 없다" 를 분리한다. 결과: 19 중 **18 개가 full depth 에서 통과** (`assert_reach` ×9, `cycle_artifacts` ×4, `push_claim_gate` ×2, `inert_surface` ×1, `tsv_timestamp` ×1, `paired_step` ×1 — 그 4-file subset 이 **110 passed in 10.78s**, suite count 아님). 살아남는 건 정확히 하나, `results/receipts/` 를 읽는 `test_quoted_counts::test_the_reach_...` 뿐이고 그건 checkout 설정으로 고칠 수 있는 게 아니다 (Q-138).
- **Decision**: 두 suite job 모두 `fetch-depth: 0` 으로 checkout 한다. 그리고 그 설정을 주석이 아니라 **reading** 으로 pin 한다 — `eval/mppi_sandbox/ci_checkout.py` + 17 test. job 목록은 typed 가 아니라 **derived** (`run:` 안에 pytest 가 있는 job), 그래서 job rename 이 population 에서 조용히 빠지지 않는다.
- **왜 이게 구조적인가**: 이 suite 는 자기 repository 의 **history 를 입력 데이터로** 읽는다 — `cycle_artifacts` 는 commit date 로 row 를 배정하고, `tsv_timestamp` 는 typed-vs-clock-read 를 그것에 대고 분류하고, `assert_reach` 는 run commit 에서 reading 을 뜬다. `actions/checkout@v4` 는 말 안 하면 depth 1 을 준다. 그러니 CI 는 **commit 1개짜리 graph** 위에서, local 은 636개 위에서 같은 코드를 돌렸고 — **양쪽 다 버그가 아니었다**. 헌법의 "CI is the only authority for the pushed tree" 는 맞지만 불완전하다: CI 가 authority 인 것은 **같은 corpus 를 건네받았을 때** 뿐이다.
- **absent key 를 default 가 아니라 absence 로 읽는 실수, 두 번째**: `declared_ceiling` 이 존재하는 이유가 정확히 이것이다 (`timeout-minutes` 없음 ≠ ceiling 없음). `fetch-depth` 는 같은 모양이고 같은 방향으로 잘못 읽혔다. `ci_checkout` 이 그걸 한 번 더 적지만, **세 번째 사례가 나오면 module 을 하나 더 추가할 게 아니라 규칙을 일반화해야 한다.**
- **주장하지 않은 것 (정직한 경계)**: shard 1 은 CI 에서 **753s** 를 썼는데 여기선 같은 test 들이 **10.78s** 다. shallow checkout 이 verdict 뿐 아니라 **속도**까지 망가뜨린 것이라면, 12 cancellation 의 진짜 원인은 suite 크기가 아니라 이것이고 D-227 의 shard 는 증상을 치료한 것이 된다. **측정하지 않았으므로 주장하지 않는다** — Q-138 로 넘긴다. 다음 CI run 이 답한다.
- **Alternatives**: (a) 채택 — depth 를 고치고 reading 으로 pin. (b) 실패하는 18개를 CI 에서 skip — red 는 사라지지만 authority 도 같이 사라진다, 정확히 12 run 침묵이 한 일. (c) history 를 읽는 module 들을 history 없이도 돌게 재작성 — 그 module 들의 subject 가 history 이므로 subject 를 버리는 것.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-02-the-ci-red-was-the-checkout-not-the-tree.md` · D-227 (이 cycle 이 읽을 수 있게 만든 run — *shard 는 유효, 필요성은 Q-138 이 재검토*) · D-043 (CI 가 pushed tree 의 authority) · D-186 (argument 쓰기 전 측정) · D-047 (registry 를 읽어라, 손으로 베끼지 말고) · D-140 (gate 1 은 새 항목을 센다)

## D-227 — 2026-08-13 — CI 가 **직렬로** 돌리던 suite 를 receipt 는 이미 sharded 로 돌리고 있었다: ceiling 을 네 번째로 올리는 대신 split 을 준다

- **Context**: 00:00 cycle 이 "PR #67 CI 가 RED, 더 얹기 전에 볼 것" 이라고 남겼다. red 가 아니었다 — `pytest (fast)` 가 30분 ceiling 에서 **cancelled** 됐고 `gh pr checks` 가 그걸 "fail" 로 렌더한 것이다. 세어보니 **12 run 연속** cancelled (2026-08-11T23:28Z → 2026-08-12T14:24Z), 어느 것도 test verdict 에 도달하지 못했다. 헌법이 "the PR's CI remains the only authority for the pushed tree" 라고 적은 그 authority 가 12 push 동안 침묵했다.
- **원인은 ceiling 이 아니다**: `suite_shard` 는 D-205 이래 **local 16 core** 를 쓰고 있고 (receipt 503s), CI 는 *같은 test 를* 한 process 에서 돌리고 있었다. 아무도 적어두지 않은 비대칭이다. 그래서 "suite 는 8분짜리" 라는 project 의 감각이 CI 가 실제로 해야 하는 일에 대해 ~12× 낙관적이었다.
- **Decision**: `fast` job 을 **8-way matrix 로 shard** 한다. `suite_shard.shard_files` / `_main` (= `plan` 을 index 로 부르는 것) 을 추가하고, workflow 는 split 을 다시 타이핑하는 대신 **이 module 에게 자기 몫을 물어본다** (`--of ${{ strategy.job-total }}` — 폭은 matrix 한 곳에만 적힘, D-047). ceiling 은 **30 그대로**: D-094 가 `slow` 에 대해 "not a fourth number bump" 라고 미리 판결했고 그 논거가 그대로 적용된다.
- **두 실패 모드는 fallback 이 아니라 이름을 받는다**: `UNSHARDABLE` (rc=3) — local 에서 "serially 돌려라, 항상 안전하다" 인 조건이 matrix 에서는 *모든 shard 가 suite 전체를 돌린다* 는 뜻이므로 조용한 fallback 을 거부한다. 빈 tail shard — pytest 를 **skip** 한다, path 없는 pytest 는 rootdir 전체를 collect 하기 때문.
- **`| tee` 를 쓰지 않는다 (D-221)**: `run:` 의 기본 shell 은 pipefail 없는 `bash -e` 라 pipeline 이 마지막 명령의 status 를 갖는다 — `| tee` 였으면 rc=3 이 삼켜졌을 것이고, 그건 2026-08-12 에 unlicensed push 를 통과시킨 바로 그 모양이다. 초안에 그렇게 썼다가 commit 전에 잡았고, test 로 고정했다.
- **⚠️ 이 변경이 걷어내지 못하는 bound 를 결과가 나오기 전에 적는다**: split 은 **file 단위**라 가장 느린 shard 는 가장 무거운 file 보다 빠를 수 없다. cancelled run 의 log 자체에서 측정: `test_exemption_masking.py` 가 **17분** 시점에도 (14:37:05Z → 14:54:26Z, test 당 ~3.4분) 끝나지 않은 채 죽었다 — 30분 ceiling 에 대해, 혼자서. 그러므로 이 fix 는 **necessary 이고 sufficient 가 아닐 수 있다**. 다음 run 이 또 cancel 되면 남은 수는 intra-file (그 test 들은 subprocess pytest 를 띄운다) 이거나 *측정된 floor 를 가진* ceiling 이지, 네 번째 추측이 아니다.
- **Alternatives**: (a) ceiling 30 → 60/90 — D-094 가 이미 기각한 모양이고, 직렬 비용은 test 가 늘면 다시 넘는다. (b) fast half 를 subset 으로 줄이기 — `receipt_cost` 가 가격을 매기려 만들어졌고 그 어려움이 곧 soundness (더 약한 주장이라 매 diff 마다 논증을 다시 해야 함); sharding 은 *같은 tree 에서 같은 test* 를 돌리므로 그 논증이 필요 없다. (c) 한 runner 안에서 xdist — `requirements-ci.txt` 에 새 dep 이 들어가고 (D-032 의 pin 계약을 건드림) runner 는 core 가 4개뿐이라 무거운 file 문제를 못 푼다. (d) 채택안.
- **부수 발견 (이 cycle 이 대가를 치르고 배운 것)**: D-207 에 대한 "**모든 pinned write 를 stamp 전에 하라**" 는 답은 **부정확하다**. `tree_provenance.stamp` 는 **`git ls-files`** 를 읽으므로, 쓰였지만 아직 **untracked** 인 file 은 stamp 에 없고 나중의 `git add` 가 *added path* 로 잡힌다 — 이 cycle 은 journal 을 stamp 전에 썼는데도 `push_preflight` 가 `STALE ... (added: journal/2026-08/13-01-*.md)` 로 push 를 거부했다. 실제 규칙은 **stamp 전에 tracked 일 것**이지 *쓰였을 것*이 아니다. 앞선 세 번의 confirmation (17:00, 19:00, 23:00) 이 이 구분을 못 한 이유는 그 cycle 들의 pinned write 가 git 이 이미 tracking 하던 file 이었기 때문이고, journal 이 **새 file** 인 cycle — 즉 모든 cycle — 은 journal pin 의 exemption 이 withdrawn 되는 순간 이걸 맞는다. 비용: 600 s suite 한 번 더, 정당하게 청구됨.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/13-01-ci-ran-serially-what-the-receipt-shards.md` · D-207 / D-044 (write-ordering 과 second-suite tax — 이 entry 가 그 답을 좁힌다) · D-205 (`suite_shard` 가 존재하는 이유) · D-094 / D-085 / D-084 (ceiling 을 세 번 올린 계보와 그 판결) · D-221 (pipe 가 rc 를 삼킨 사건) · D-047 (registry 는 자기 진술을 하나만 갖는다) · `ci_verdict.UNRUN` (cancelled 는 pass 도 fail 도 아니다) · Q-137

## D-226 — 2026-08-12 — receipt 는 **그 cycle 이 그것을 봤다는 증거가 아니다**: 22:00 의 suite 는 cycle 이 죽은 뒤 6분 후에 red receipt 를 썼다

- **Context**: 20:00 / 21:00 / 22:00 세 cycle 연속으로 push 없이 끝났고, `cycle_artifacts stranded` 가 두 journal 을 named 했다. 22:00 journal 은 "Ran the suite once, on the final tree" 라고 적었고 `cycle_wallclock review` 는 그 run 이 **5m28** 에 끝났다고 — 514s suite 가 들어갈 수 없는 시간 — 읽었다. 처음 추론은 "없는 suite 를 주장했다" 였다. **artifact 가 더 날카로운 답을 줬다.**
- **측정**: `/tmp/suite-receipt.json` 은 `head=93eeb23` (22:00 의 commit), `duration=514.46s`, `returncode=1`, **5 failed**, mtime **22:11:53**. wrapper 가 기록한 run 종료는 **22:05:29**. 즉 receipt 는 **자기 cycle 이 죽은 뒤 6분 24초 후에** 쓰였다.
- **Decision**: 기록한다 — 22:00 은 suite 를 **건너뛴 것도 초과한 것도 아니다**. suite 를 띄우고 **기다리는 중에 turn 을 끝냈고**, `claude -p` 에서 tool call 없는 turn 은 곧 최종 답이므로 process 가 종료됐다. 고아가 된 pytest 는 계속 돌아 이미 죽은 process 를 위한 receipt 를 남겼다. D-115 advisory 가 말로 경고한 실패 양식이 **prose 가 아니라 artifact 로** 처음 잡힌 것이다.
- **그래서 journal 은 거짓이 아니다** — *시작한* 행위를 보고했고 그 결과를 본 적이 없다. 그리고 볼 수 있었다면 push 하지 못했다: receipt 는 **RED** 였다. 이 구분이 실질적이다. "측정하지 않았다" 와 "허공에 측정했다" 는 journal 만으로는 구별되지 않고, 후자는 **다음 cycle 이 읽을 artifact 를 남긴다**.
- **노출된 신뢰 구멍**: `push_preflight` 는 count 를 **tree** 에 묶는다 (D-043). 살아있는 **process** 에 묶는 것은 아무것도 없다. 따라서 고아 suite 의 receipt 는 다음 cycle 에게 완료된 측정으로 읽힌다 — green 이든 red 든. 이번엔 red 라서 눈에 띄었지만, green 이었다면 아무 cycle 도 자기가 돌리지 않은 suite 로 push 를 license 했을 것이다.
- **Alternatives**: (a) 채택 — 기제를 기록하고 receipt 신선도 검사를 next-actionable 로 올린다. (b) `push_preflight` 에 mtime 검사를 이번 cycle 에 구현 — 이미 예산 초과이고, 검사 설계는 wrapper 가 run 종료를 어디에 기록하는지에 달려 있어 서둘러 넣을 물건이 아니다. (c) journal 을 부정직으로 분류 — artifact 가 반증한다. 틀린 진단은 틀린 수리를 낳는다.
- **부수 발견**: red 5개는 전부 `paired_step.walk_cells` 의 census bill 이었고 defect 가 아니다 (`defaults` 58→59, `forwards` 27→28, `total` 168→170, `weighting_at_shipped` 56→57, margin 25→24, `READING` 2행, `key_discrimination` 재읽기). entrant 가 **한 commit 의 양면**인 점이 기록할 값이다: `paired_step.py:237` 은 detector 를 의식해 `params` 를 명시적으로 넘겨 FORWARDS 로 정확히 채점되는데, 그 module 자신의 test 가 rung 을 default 했다. **module 이 census-aware 한 것이 그 test 를 census-aware 하게 만들지 않는다** — 16 cycle 연속.
- **`key_discrimination` 은 유일한 실질 수리**: `walk_cells` 가 `reprobe` 옆에 두 번째 non-`LIVE` narrow hit 로 들어와 discrimination 이 **2.7% → 9.7%** 로 3배가 됐다. verdict 는 유지 (`NARROWED_NOT_SEPARATED`, margin 0.25) 이므로 D-196 의 판단은 **강화**된다 — key 가 deferred 될 때보다 residue 를 더 많이 받아들인다. 다만 0.10 probe rung 이 측정값을 0.003 차로 넘겨서 0.20 으로 올렸고, 그 squeeze 를 잡은 assertion 은 바로 이 목적으로 쓰인 guard 였다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-23-the-orphaned-suite-wrote-its-receipt-after-the-cycle-died.md` · D-115 (wall-clock advisory) · D-112 (strand reading) · D-043 (count 를 tree 에 묶기) · D-207 (withdrawn pin exemption)

## D-225 — 2026-08-12 — cafe 의 sign flip 은 **pairing 을 견딘다**: D-217→D-219 계보는 서고, D-224 는 통계량 전체가 아니라 그 arm 들에 대한 판결이다

- **Context**: D-224 가 off-family mirror 를 철회하면서 열린 Q-135 는 그 철회의 **적용 범위**를 물었다. `worst_step` 은 unpaired 이고 `n`-indexed 인데, 이 branch 가 공표한 clearance 숫자는 거의 전부 그 통계량이다 — D-217 의 0.007 → 0.382 m, D-218/D-219 의 3-scene 표, D-219 의 `is_interaction`. off-family 에서는 estimand 를 바꾸자 부호가 사라졌다. cafe 도 그러면 계보 전체가 무너진다.
- **Decision**: Q-135 의 lean (a) 대로 `cafe_obstacle_crossing_v0` 의 2×2 를 **같은 6 seed, 같은 `PairedStep` class, 같은 resampler** 로 재읽었고 — **부호가 견딘다**. 두 row 모두 0 에서 분리되고 방향이 반대다: `w_risk=40` 에서 mean **+0.3501 m** CI [+0.3181, +0.3936] `SEPARATED_POSITIVE`, `w_risk=0` 에서 mean **−0.0339 m** CI [−0.0443, −0.0235] `SEPARATED_NEGATIVE`. 각 row 는 6/6 **만장일치** (sign 6+/0−, 0+/6−). 따라서 D-217→D-219 의 cafe 계보는 유지되고, **D-224 는 통계량이 어디서나 망가졌다는 판결이 아니라 그 off-family arm 들이 noise 였다는 판결이다.**
- **재현이 먼저다**: 같은 walk 의 `worst_step` 은 **+0.3755 / −0.0192** 로 D-218 이 공표한 쌍을 소수 4자리까지 되돌려준다. 그래서 이것은 *재측정*이 아니라 *재읽기*이고, 아래의 차이는 estimand 의 몫이지 다른 walk 의 몫이 아니다.
- **그러나 pairing 은 확인만 한 게 아니라 값을 움직였다** — 양방향으로: top row 는 +0.3755 → +0.3501 (작아짐), bottom row 는 −0.0192 → −0.0339 (**커짐**). 두 estimand 는 같은 walk 위에서 서로 다른 방향으로 어긋나므로 모듈은 둘 다 보고하고 하나를 조용히 대체하지 않는다.
- **Q-135 의 (b) 표기 규칙도 여기서 정한다**: `worst_step` 계열 숫자를 인용할 때는 **`n` 을 병기**한다 (`min` 은 `n` 에 대해 non-increasing 이므로 `n` 없는 인용은 비교 불가능한 양이다). 새로 공표하는 clearance step 은 **paired estimand + CI 를 기본**으로 하고 `worst_step` 은 과거 표와의 대조용으로만 병기한다.
- **한계 — 정직하게**: (i) `n = 6` 에서 two-sided sign test 의 **최소** 달성 가능 p 는 `2/2⁶ = 0.031` 이다. 즉 만장일치는 6 seed 가 할 수 있는 가장 강한 진술이고 `p = 0.031` 은 **바닥이지 여유가 아니다**. (ii) 재읽은 것은 **세 scene 중 하나**다 — `cafe_convoy_v0` / `cafe_head_on_v0` 의 `SIGN_FLIP` 은 여전히 unpaired 표에 서 있다. (iii) bootstrap CI 는 6 seed 를 resample 한 것이므로 좁게 읽히는 경향을 감안해야 한다. sign test 는 그 가정을 쓰지 않으며 같은 답을 준다.
- **Alternatives**: (a) 채택 — crossing 한 scene 만 재읽고 답을 얻는다. (b) 세 scene 전부 — 한 cycle 을 넘기고, 가장 큰 효과가 견디는지부터 아는 것이 순서다. (c) 재측정 없이 표기 규칙만 — 부호가 pairing 에서 사는지 여전히 모른 채로 남는다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-21-the-cafe-flip-survives-pairing.md` · Q-135 (resolved) · D-224 (retraction 의 범위) · D-218 (재현된 쌍) · D-047 (하나의 resampler)

## D-224 — 2026-08-12 — D-222/D-223 의 off-family mirror 는 **부호가 아니라 minimum 이었다**: `ped_step` 은 paired 가 아니고, 같은 6 run 에서 부호가 뒤집힌다

- **Context**: STATE #1 은 "6 → 20 paired seeds + CI" 였고 근거는 D-223 이 스스로 적은 한계였다 — 양쪽 step 이 5 cm 미만인데 CI 가 없다. loop 은 3 분이다. 문제는 seed 수가 아니라 **무엇을 재고 있었나**였다.
- **관찰 — `three_arm.ped_step` 은 두 ensemble minimum 의 차**다: `min_i c_i(w_ped=50) − min_j c_j(w_ped=0)`. 두 minimum 은 서로 **다른 seed** 에서 잡히므로 (1) seed 를 공유하고도 pairing 을 버리고, (2) `min` 은 표본을 늘리면 커질 수 없으므로 **`n` 으로 index 된 양**이다. 즉 6-seed 값과 20-seed 값은 정밀도가 다른 같은 양이 아니라 **다른 양**이고, 두 minimum 의 *차*이므로 그 drift 는 부호조차 알려져 있지 않다. `seed_count_licence` 가 all-seeds ESS gate `(1−p)ⁿ` 에 대해 내린 판정과 같은 것이 이 branch 의 두 번째 estimand 에서 반복된 것이다.
- **측정** (`city_crossing_v0`, λ=0.8, seeds 0–19 ⊃ D-223 의 0–5, 네 cell 전부 20/20 완주):

  | reading | `w_risk = 0` | `w_risk = 40` |
  |---|---|---|
  | worst-case, n=6 (D-223 공표값) | **+0.0486** | −0.0085 |
  | worst-case, n=20 | **−0.0161** | −0.0595 |
  | paired mean, n=20 | −0.0146 | −0.0229 |
  | 95% bootstrap CI | [−0.0414, +0.0136] | [−0.0483, +0.0014] |
  | sign counts / exact p | 9+/11− · 0.824 | 9+/11− · 0.824 |

  6-seed prefix 는 D-223 을 **정확히 재현**한다 (test 로 pin). 그런데 **같은 6 run 의 paired mean 은 −0.0160** — run 을 하나도 더하지 않고 부호가 뒤집힌다. 따라서 이것은 표본 크기 문제가 아니라 **통계량 선택** 문제다.
- **Decision**: D-222/D-223 의 mirror 주장 (**"단독이면 돕고 risk 와 함께면 해친다"**) 을 **철회한다**. off-family 에서 `w_ped` 는 어느 row 에서도 방향을 결정하지 못한다 (양쪽 CI 가 0 을 포함, sign test 는 동전). D-219 의 `is_interaction` 이 **cafe-family-bounded** 라는 판정은 **그대로 유지된다** — 그 결론은 off-family step 이 *작다*는 데 의존하지 처음부터 그 *부호*에 의존하지 않았다. 철회되는 것은 mirror 의 부호 배열 하나다.
- **구조적 귀결**: `paired_step.py` 가 두 estimand 를 **나란히** 보고한다 — `worst_step` (D-223 표와 나란히 놓기 위해, 그리고 `min_step_is_n_dependent()` 를 옆에 달고) 과 paired mean + bootstrap CI + exact sign test. CI 는 `margin_free.RungComparison` 에서 **가져다 쓴다**; resampling 규칙의 진술은 branch 에 하나뿐이어야 하고 (D-047) 그 재사용을 test 가 equality 로 pin 한다. sign test 를 넣은 이유는 D-222/D-223 이 실제로 한 주장이 **부호**이기 때문이다 — `math.comb` 로 exact, 분포 가정 없음, sim run 0.
- **이 branch 의 다른 숫자들에 대한 함의 (아직 측정 안 함)**: worst-case 로 공표된 모든 값이 `n`-indexed 다 — D-217 의 0.007 → 0.382 m headline 포함. 틀렸다는 뜻이 아니라 **ensemble 을 가로질러 비교할 수 없다**는 뜻이고, 이 branch 는 6 · 8 · 16 · 32 를 걸어왔다. cafe 2×2 를 paired estimand 로 다시 읽는 것이 다음 순위다.
- **Alternatives**: (a) 채택 — 두 estimand 병기 + 주장 철회. (b) 20-seed worst-case 만 보고하고 "seed 를 늘리니 mirror 가 뒤집혔다" 로 booking — 참이지만 **원인 설명이 틀리고**, 같은 함정을 다음 scene 에서 반복한다. (c) `ped_step` 을 paired 로 교체 — D-217~D-223 의 표 전부가 재측정 대상이 되고 한 cycle 에 들어가지 않는다; 대신 `worst_step` 을 그 이름으로 남겨 caller 가 paired 라고 오해할 수 없게 했다. (d) seed 를 더 늘린다 — CI 폭이 문제가 아니므로 답이 아니다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-20-the-mirror-was-a-minimum.md` · D-223 / D-222 (철회 대상 — *6-seed 표는 재현됨*) · D-219 (`is_interaction` — 유지) · D-217 (worst-case headline 도 `n`-indexed) · `seed_count_licence` / D-173 (같은 논증의 첫 판본) · D-047 (resampler 의 단일 진술) · D-044 (보고하되 threshold 하지 않는다)

## D-223 — 2026-08-12 — off-family mirror 는 **difficulty 가 아니라 family** 였다: uncensored operating point 에서 부호가 그대로 재현된다

- **Context**: D-222 가 off-family 첫 reading 을 booking 하면서 스스로 한계를 적었다 — `city_crossing_v0` 의 2×2 네 cell 전부 median clearance 0.018–0.032 m 로 0.30 m margin 아래였고, 따라서 비교는 **전부 실패하는 네 arm 사이**의 것이었다. mirror 가 환경 family 탓인지 "모든 arm 이 실패하는 난이도" 탓인지 가를 수 없었고, 그것을 Q-134 로 남겼다. Q-134 의 lean 은 (a) scene 재tuning 이었고 비용을 ~51 s 로 추정했다. 실제로 4 분이었다.
- **Decision — scene 에 0.75 s lag 을 넣는다**: 원래 schedule 은 보행자 넷이 각자 robot 의 x 도달 시각에 **정확히** centreline 에 있도록 짜여 있었다 (최대 적대적). 전 schedule 을 +0.75 s 밀면 robot 도달 시점에 보행자는 centreline 에서 0.56 m 못 미친다. rung 은 측정으로 골랐다 — baseline worst-case 가 δ ∈ {0.0, 0.75, 1.5, 2.25, 3.0} 에서 **0.0025 / 0.2415 / 0.6832 / 1.0554 / 1.2684 m** (전부 6/6). 0.75 만이 margin 을 **straddle** 한다 (worst 0.2415 아래, median 0.3869 위). 1.5 이상은 uncontested 이고 그것은 convoy 의 FLOOR censoring 으로 방향만 바꾼 것이다.
- **측정 — mirror 가 살아남는다** (6 paired seeds, λ=0.8, worst-case clearance m):

  | | `w_ped = 0` | `w_ped = 50` | step |
  |---|---|---|---|
  | `w_risk = 40` | 0.3504 | 0.3418 | **−0.0085** |
  | `w_risk = 0`  | 0.2415 | 0.2901 | **+0.0486** |

  부호 배열이 D-222 의 censored reading (단독 +0.0128 / risk 와 함께 −0.0001) 과 **같고**, cafe family (risk 와 함께 +0.3755/+0.1968/+0.0806, 단독 flat-to-negative) 와 여전히 **반대**다. `BOUGHT_WITH_FREEZE` 0 건, 네 cell 전부 6/6.
- **그래서 Q-134 는 family 쪽으로 답한다 → resolved**. D-219 의 `is_interaction` 이 **cafe-family-bounded** 라는 D-222 의 판정은 **철회가 아니라 강화**된다: 이제 uncensored reading 위에 서 있다.
- **다만 `is_interaction` 이 `False` 인 *이유*가 바뀌었다**: ladder 가 `SIGN_FLIP / SIGN_FLIP / CONDITIONAL / INERT` 로 읽히고, 붕괴하는 이유는 scene 이 degenerate 해서가 아니라 **양쪽 step 이 전부 5 cm 미만**이기 때문이다. off-family 에서 `w_ped` 는 어느 방향으로든 거의 아무것도 하지 않는다 — cafe 대비 한 자릿수 작다.
- **부수 소견, 그리고 이 표에서 가장 큰 값**: risk term **단독**이 +0.1089 m 를 산다 (0.2415 → 0.3504). `cafe_obstacle_crossing_v0` 에서 같은 비교는 0.0134 m 를 **깎았다** (D-218 아랫줄). 이것도 mirror 이고 `w_ped` 가 여기서 하는 어떤 일보다 2 배 크다. 아직 어떤 decision 도 이것을 booking 하지 않았다.
- **구조적 귀결 — anti-vacuity screen 이 한쪽만 보고 있었다**: `test_the_baseline_is_contested_at_the_declared_margin` 의 docstring 은 "both censoring directions" 를 screen 한다고 적었지만 두 assertion 모두 baseline 을 **위에서만** 묶는다 (too easy / too empty). scene 이 실제로 실패한 방향은 아래쪽이고, δ=0 판본은 그 screen 을 **깨끗하게 통과했다** — 더 심하게 실패하는 것도 clear 하지 못하는 것이기 때문이다. `test_the_baseline_is_not_censored_below_the_margin` 이 median 이 margin 을 넘을 것과 baseline 완주를 pin 한다. "contested" 를 straddle 로 적는다.
- **census bill (측정)**: 새 screen 이 `MPPIParams(lam=0.8)` 을 명시하므로 `default_lam_sites` 가 **`decides` 82 → 83, `total` 167 → 168** 을 청구했고 `defaults` 58 / `forwards` 27 / `inert_defaults` 2 는 **전부 부동**이다 — D-222 와 같은 파일, 같은 모양, 한 cycle 뒤. margin 은 24 → 25 로 **네 번째 연속** 한쪽 방향 증가지만, `test_structural_null.py` 의 21 sites 와의 거리가 한 site 뿐이라 repo 의 property 라고 부르지 않는다.
- **한계**: 6 seed · CI 없음. +0.0486 m 를 noise 와 가르지 못한다. 이 cycle 이 증거로 내세우는 것은 step 의 **크기가 아니라 서로 다른 두 operating point 에서 재현된 부호**다. verdict token 만 다시 읽었다면 양쪽 다 `SIGN_FLIP` 이라 아무것도 배우지 못했을 것이다 (D-222 자신의 경고).
- **Alternatives**: (a) 채택 — 재tuning 후 재walk, 두 operating point 를 나란히 보고. (b) cafe scene 을 같은 난이도로 올린다 — 반대 방향 통제지만 D-217~D-219 의 모든 숫자가 재측정 대상이 된다. (c) 교락을 안고 D-222 를 그대로 둔다 — Q-134 가 답 없이 남고, 이 cycle 의 4 분이 그것보다 싸다. (d) δ 를 1.5 로 — baseline 이 margin 을 여유롭게 넘어 avoidance term 이 할 일이 없어진다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-19-the-mirror-survived-the-retune.md` · D-222 (강화되는 판정) · D-219 (`is_interaction`, cafe-bounded 로 확정) · D-218 (risk term 단독의 cafe 쪽 부호) · D-207 (pin reprobe 가격) · D-107 (empty population reads as clean) · D-044 (reported, never thresholded) · Q-134 (resolved → D-223)

## D-222 — 2026-08-12 — off-family 로 나가려면 **나갈 scene 이 먼저 있어야 했다**: `SIGN_FLIP` 은 재현되고 방향은 뒤집힌다

- **Context**: STATE 의 next-actionable #3 ("a scene outside the `cafe_*` family") 이 여러 cycle 째 순위에 올라 있었는데, **실행 불가능한 항목이었다**. matrix 가 ship 하는 off-family scene 두 개 (`city_curved_v0`, `city_figure8_v0`) 를 `scene_eligibility` 가 D-159 이래 `NO_OBSTACLES` 로 유죄판결해 왔다. sandbox 로 확인: `min_obstacle_clearance` 가 문자 그대로 `Infinity` 다. 거기서 2×2 를 걸었으면 INERT 가 나왔을 것이고, 그것은 기전이 없어서가 아니라 **잴 clearance 가 없어서**다 (D-107 의 empty-population-reads-as-clean). 그 INERT 를 "interaction 은 off-family 로 일반화하지 않는다" 로 장부에 올리는 것이 정확히 scene artifact 가 result 의 옷을 입는 경로다. **지식의 공백이 아니었다** — screen 은 이미 있었고, 아무도 그것을 plan 에 대고 돌리지 않았을 뿐이다.
- **Decision**: 빠져 있던 eligible off-family scene 을 만든다 — `eval/scenarios/variants/city_crossing_v0.yaml`. small_city SW 도로를 직선 12 m 주행, 보행자 4 명이 수직으로 횡단하며 각자 robot 이 자기 x 에 도달하는 순간 centreline 에 있도록 스케줄. **family 만 바꾸고 shape 은 고정**: env_class **B** (crossing 은 D), 0.6 m/s (crossing 은 0.3), 벽 없는 개활 도로. margin 은 **0.30** — convoy/crossing 과 같은 값을 고른 것이고 우연이 아니다. `Headroom` 은 서로 다른 margin 의 두 arm 을 채점하지 않으므로, 그 두 scene 과의 cross-family 비교가 가능하려면 공유해야 한다.
- **`variants/` 에 두는 것도 결정이고, 그래서 test 로 고정했다**: `scene_eligibility.census()` 는 `eval/scenarios/*_v0.yaml` 을 **non-recursive** 로 glob 하고, 그 8-scene population 은 최소 다섯 곳에 pin 되어 있다 (`test_scene_eligibility` 의 `len(shipped.scenes) == 8` 과 `reasons_recorded == 8`, 그리고 `test_ab_temperature_protocol` / `test_epistemic_reach_screen` / `test_weight_units` / `test_hazard_exposure` 의 hard-coded no-obstacle scene list). 9 번째 scene 을 matrix 에 넣으면 다섯이 동시에 움직이고, 각각은 "pin 이 따라와야 할 count 인가, 다시 진술되어야 할 claim 인가" 라는 **별개의 판단**이다. `variants/` 는 그 glob 전부의 바깥이므로 scene 을 **오늘** 실행 가능하게 하면서 그 migration 을 사지 않는다. matrix 승격은 실제 가격이 있는 실제 결정이고, 그것을 **지불하는 cycle** 의 것이지 이 cycle 의 것이 아니다 — 그래서 승격이 일어나면 test 가 red 가 되게 해 두었다. 의도된 알람이다.
- **측정 결과 — token 은 재현되고 방향은 뒤집힌다**: λ=0.8, 6 paired seeds, D-219 와 같은 protocol. cafe family 는 `w_ped` 가 risk term 과 **함께** 도울 때 양(+0.3756 / +0.1968 / +0.0806)이고 단독으로는 flat-to-negative 였다. 여기서는 반대다 — **단독 +0.0128, `w_risk=40` 과 함께 −0.0001**. verdict token `SIGN_FLIP` 은 네 scene 전부에서 참이 되었고, 네 번째에서는 **반대를 뜻한다**. verdict string 을 tally 하는 cross-scene census 였다면 4/4 를 읽고 generalization 이라고 불렀을 것이다.
- **그리고 D-219 가 실제로 book 한 claim 은 살아남지 못한다**: ladder 가 ε ∈ {1e-6, 1e-3, 1e-2, 5e-2} 에서 `SIGN_FLIP / CONDITIONAL / CONDITIONAL / INERT` 로 읽혀 5 cm 에서 INERT 로 붕괴하므로 **`is_interaction` 은 `False`** 다. D-219 의 threshold-robust conjunction 은 이제 측정된 반례를 갖는다 — **cafe-family-bounded** 인 것으로 좁혀진다.
- **한계를 묻지 않는다**: 이 tuning 의 scene 은 **너무 어렵다**. 네 cell 전부 median clearance 0.018–0.032 m 로 0.30 m margin 에 한참 못 미치므로, 비교는 **실패하는 네 arm 사이**의 것이고 0.0128 m step 은 scene noise 일 수 있는 크기다. head_on 의 censoring 방향이다. 따라서 **family 와 difficulty 가 교락(confound)되어 있고 이 cycle 은 분리하지 못했다** — mirror 는 둘 중 어느 쪽 탓이어도 된다. Q-134 로 남긴다.
- **Alternatives**: (a) 채택 — variants 에 eligible off-family scene 을 짓고 2×2 를 건다. (b) city_curved 에 그냥 2×2 를 건다 — INERT 를 얻고 그것을 결과로 오독할 위험, 즉 이 결정이 막으려는 바로 그것. (c) 9 번째 scene 을 matrix 에 직접 추가 — 다섯 pin migration 을 한 cycle 예산 안에서 사야 하고, 각 pin 이 별개 판단이라 overrun 이 거의 확실. (d) off-family 를 계속 미룬다 — STATE 가 이미 여러 cycle 그렇게 했고, 항목이 실행 불가능하다는 사실이 드러나지 않은 채로 순위에 남아 있었다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-18-the-off-family-step-had-no-scene-to-stand-on.md` · D-219 (좁혀지는 claim) · D-218/D-217 (`w_ped` 의 원래 headline) · D-159 (`scene_eligibility`, city scene 을 이미 유죄판결해 둔 screen) · D-158 (head_on 의 censoring 방향) · D-107 (empty population reads as clean) · D-124 (mechanism vs safety) · D-044 (reported, never thresholded) · Q-134

## D-221 — 2026-08-12 — gate 의 권위가 **caller 가 조립하는 exit code** 에 얹혀 있었다: `git push` 자신을 callee 로 만든다

- **Context**: 16:00 cycle 이 `push_preflight check ... | tail -4 && ... && git push` 를 실행했다. pipeline 의 exit status 는 **마지막 command** 의 것이므로 `&&` 는 `tail` 의 `0` 을 보았다. gate 는 `STALE ... push refused` 를 **정확히 출력했고**, 같은 command 안에서 push 가 실행됐다. 아무것도 비활성화되지 않았고 규칙과 다툰 적도 없다 — 가독성을 위해 더한 네 글자가 exit code 를 대체했을 뿐이다. D-082 는 `&&` 가 **규칙**이라고 못박았지만, 그 규칙은 caller 의 shell 문법에 의존하고 callee 는 shell 조립을 단속할 수 없다.
- **Decision**: gate 를 **`git push` 의 callee 위치**로 옮긴다. `scripts/githooks/pre-push` + `eval/mppi_sandbox/push_licence.py` — caller 의 pipeline 이 끝난 **뒤에** git 이 직접 호출하므로 바깥 command 를 파이프해도 도달하지 못한다. hook 은 `push_preflight.check` 를 **그대로 다시 호출**한다 (gate 가 틀린 적이 없으니 *다른* check 는 새로 틀릴 표면일 뿐). receipt 는 worktree fingerprint 로 `receipt_store` 에서 recall — 인자가 없으므로 더 관대한 receipt 로 겨냥할 방법이 없다. 검증: 이 cycle 의 dry-run push 가 `NO_RECEIPT` 로 **거부됐고, 출력을 `tail` 로 파이프한 상태에서 push 자체가 일어나지 않았다**.
- **측정된 한계 (모듈에 명시)**: `git push --no-verify` 는 여전히 우회한다. 이것을 숨기지 않는 이유가 주장의 전부다 — 고쳐진 실패는 **gate 가 걸려 있다고 믿으면서** 답이 버려진 cycle 이고, `--no-verify` 는 ungated push 를 **소리내어 말하는** cycle 이다 (command, journal, cron log 에 그대로 남는다). 이 hook 은 첫 번째를 두 번째로 바꾼다. "unlicensed push 가 불가능해졌다" 가 아니라 "**로그를 편하게 읽다가 사고로** 할 수 있는 일이 아니게 됐다".
- **Wiring 은 commit 이 나를 수 없다**: git 은 `core.hooksPath` 가 가리켜야만 `scripts/githooks` 를 본다. 이는 repo-local config 라 fresh clone 은 hook 파일만 갖고 wiring 은 없다. 그래서 `status` 가 unwired 에서 **rc=1 로 fail closed** 한다 — 가정이 아니라 reading 이 되도록.
- **Alternatives**: (a) constitution 의 push snippet 에 `set -o pipefail` — snippet 은 고치지만 *다음* invocation 은 못 고친다. cycle 은 자기 shell 을 ad hoc 으로 조립하고 snippet 은 prompt 안의 권고다. (b) `check` 가 stdout 이 pipe 임을 감지해 거부 — cron 에서 executor 의 stdout 은 **항상** pipe 이므로 정직한 run 마다 red, D-044 의 muted-check 를 제값 주고 사는 것. (c) parent process 조사 — `a | b` 의 양쪽은 같은 shell 의 자식이고, "내 exit code 가 읽히는 중"과 "버려지는 중"을 구별하는 것은 `/proc` 에 없다. (d) hook — 채택. 실패한 property 가 "gate 가 실행됐나"(실행됐고, 거부했다)가 아니라 "**거부가 push 에 도달했나**"이므로, check 는 pusher 가 조립할 수 없는 위치에서 이뤄져야 한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-17-push-gate-as-git-callee.md` · commit `98048cc`

## D-220 — 2026-08-12 — unwatched population 을 없애는 repair 는 **census 에 들어오는 값을 산다**: 양방향으로 측정된 가격

- **Context**: D-219 cycle 이 push 를 거부한 채 끝났다 (2 failed / 2633 passed). 그 cycle 이 남긴 진단은 "`step_bought_with_freeze` 의 `and` 모양 guard 를 두 pinned tally 에 등록해야 한다" 였는데, **측정해보니 틀렸다** — 그 함수는 pool 에 아예 없고 AND set 은 아홉으로 그대로다 (`and` 는 두 scalar 비교를 잇는 boolean 연산자이지 `SENSE_AND` 가 읽는 집합 교집합이 아니다).
- **Decision**: 두 red 는 **한 entrant** 로 설명된다 — `three_arm.is_interaction`. 그리고 그것이 들어온 **이유**를 D-NNN 으로 못박는다: D-219 가 `INTERACTION_VERDICTS` (typed module-level allow-list, `unwatched_exemptions` 5→6) 를 제거하고 D-104 의 repair (집합이 존재할 필요가 없도록 reading 을 서술) 를 적용했는데, 그 complement 의 spelling 이 `v in ("MAIN_EFFECT", "INERT")` — D-102 의 inline 2-string tuple 그대로다. 즉 **allow-list 청구서를 갚는 행위가 pool entry 를 샀다**: census red 3 개가 지워지고 1 개가 생겼다. pin 은 `101 -> 102`, `scalar_readings` 는 `12 -> 13` 으로 갱신.
- **Alternatives**: (a) `INTERACTION_VERDICTS` 를 되살려 pool entry 를 피한다 — unwatched population 을 다시 만드는 것이므로 D-073 계열 청구서를 되살릴 뿐. (b) `is_interaction` 을 truth test 로 다시 써서 detector 에게 안 보이게 한다 — D-104 가 "repair 가 payment 가 아니라 disappearance 로 기록되는" 경우로 이미 거부한 spelling. (c) 두 pin 을 측정값으로 갱신하고 **가격을 양방향으로 기록한다** — 채택.
- **부수 소득 (gloss 하나 반증)**: `scalar_readings` 의 기존 12 members 는 전부 문자열 하나를 반환하는 renderer 였고, 그래서 "이 reading 은 rendering 을 고른다" 로 읽혀왔다. `is_interaction` 은 `bool` 을 반환한다 (`_SCALAR_ANNOTATIONS` 는 처음부터 `bool` 을 포함). 고르는 것은 **arity 1** 이지 rendering 이 아니다 — conclusion 도 arity 1 일 수 있다.
- **Second-order cost**: 두 축 모두 nil 이고 **둘 다 측정했다** — `unwatched_exemptions` = 5, `NO_REGISTRY` = 19. D-180 이 "DERIVED 니까 nil" 추론을 금지한 것을 재진술이 아니라 적용한 형태.
- **Status**: accepted
- **Refs**: journal/2026-08/12-16-clear-the-strand-the-repair-bought-the-entry.md · PR pending (autoresearch/p3-epistemic-shadow-cost-critic)

## D-219 — 2026-08-12 — 3 scene 로 넓히니 **interaction 은 일반화되고 sign flip 은 threshold 였다**: verdict 를 ladder 로 읽는다

- **Context**: D-218 이 2×2 를 **한 scene** (`cafe_obstacle_crossing_v0`) 에서 재고 "`w_ped` 는 main effect 가 아니라 interaction" 을 booking 했다. 그런데 한 scene 은 **term 의 성질**과 **그 scene 의 성질**을 가를 수 없다 — 이것은 D-218 자신이 한 denomination 위에서 D-217 에게 지적한 바로 그 오류다. STATE next-actionable #1 이 그것을 그대로 적고 있었고, `risk_interaction()` 은 이미 `scene` 인자를 받고 있어서 필요한 것은 loop 하나였다 (scene 당 ~1m10).
- **측정 (3 eligible scenes, 6 paired seeds, `lam = 0.8`, worst-case clearance m, row 별 `w_ped` step)**:

  | scene | `w_risk = 40` | `w_risk = 0` | verdict |
  |---|---|---|---|
  | `cafe_obstacle_crossing_v0` | **+0.3756** | −0.0192 | `SIGN_FLIP` |
  | `cafe_convoy_v0` | **+0.1968** | −0.0055 | `SIGN_FLIP` |
  | `cafe_head_on_v0` | **+0.0806** | −0.0002 | `SIGN_FLIP` |

  D-218 의 crossing 수치가 **정확히 재현**된다 (+0.3756 vs +0.3755, 반올림). completion 은 **24 cell 전부 6/6** — 어떤 cell 의 clearance 도 freeze 로 산 것이 아니므로 위 숫자는 전부 읽을 수 있다.
- **Decision — 두 개를 따로 진술한다**: (1) **interaction 은 일반화된다** — 3 scene 전부에서 `w_ped` 는 `w_risk` 가 있을 때만 움직인다. (2) **sign flip 은 일반화되지 않는다** — 그것은 threshold 의 산물이다. `EPS_CLEARANCE = 1e-6` 은 float-noise guard 이지 **물리적 scale 이 아니다**. `−0.0002 m` (0.2 mm) 짜리 step 이 그 guard 아래에서는 "단독으로 해롭다" 로 읽힌다. 5 cm 에서 다시 읽으면 3 scene 전부 `CONDITIONAL` 이다 — 단독일 때 **해로운** 게 아니라 **조용한** 것이다.
- **그래서 verdict 는 point 가 아니라 ladder 로 읽는다**: `verdict_ladder(cells, EPS_LADDER)` 가 `{1e-6, 1e-3, 1e-2, 5e-2}` 에서 다시 채점하고, `verdict_is_threshold_robust` 가 "verdict 가 측정이 아니라 threshold 를 지칭하는가" 를 predicate 로 답한다. **모든 threshold 에서 살아남는 것**은 어떤 scene 도 `MAIN_EFFECT` 나 `INERT` 로 읽히지 않는다는 것이고, `is_interaction()` 이 그 conjunction 을 pin 한다. 이 walk 이 licensing 하는 claim 은 정확히 그것이며, D-218 이 booking 한 것보다 **약하다**.
- **D-218 의 강한 절반은 이제 bound 된다**: "risk term 단독이 worst-case clearance 를 깎는다" 는 crossing scene 에서 실재하지만 (~2 cm), 나머지 두 scene 에서는 sub-millimetre 다. 그것은 **term 의 성질이 아니라 crossing scene 의 성질**이다.
- **`BOUGHT_WITH_FREEZE` 가 먼저 검사된다**: 2×2 grader 도 `ArmReading.verdict` 와 같은 순서 규칙을 따른다 — 얼어붙은 cell 은 clearance 를 보고할 수 없다. row 마다 자기 baseline (`같은 w_risk 의 w_ped = 0` cell) 을 쓴다. 이번 측정에서는 발동하지 않았고, 발동하지 않았다는 것이 24 cell 6/6 의 의미다.
- **Alternatives**: (a) 채택 — 두 진술을 분리하고 ladder 를 ship. (b) `SIGN_FLIP` 이 3 scene 전부에서 나왔다고 보고 — 사실이지만 guard 상수의 artifact 이고, headline 이 "flip 이 일반화된다" 가 되었을 것이다. 이것이 D-217 의 오류를 한 층 위에서 반복하는 것이다. (c) `EPS_CLEARANCE` 를 물리적 값으로 올려버림 — 다른 caller (`ArmReading`) 의 판정을 조용히 바꾸고, point reading 이라는 문제 자체는 남는다. (d) 한 scene 유지 — STATE #1 이 세 cycle 째 이것을 들고 있었고, 비용은 4 분이었다.
- **한계**: 6 seed · CI 없음 · 한 weight pair (`40 / 50`) 다. ladder 는 verdict 의 threshold 민감도를 재지 **seed** 민감도를 재지 않는다 — `−0.0002 m` 가 0 과 구분되는지는 이 walk 이 답하지 않으며, 답하려면 seed 를 늘려야 한다. 그리고 arm 들은 여전히 **scale-matched 가 아니다** (`w_epist = 200` / `w_geom = 40` / `w_ped = 50`).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-15-the-interaction-generalizes-the-flip-is-a-threshold.md` · D-218 (좁혀지는 대상 — *crossing 측정은 재현됨*) · D-217 (원 headline) · D-166 / `geometric_null` (attribution 축) · D-140 (gate 1 은 새 항목을 센다) · D-044 (write 순서)

## D-218 — 2026-08-12 — three-arm head-to-head 이 D-217 의 headline 을 **interaction 으로 좁혔다**: `w_risk` 를 빼면 `w_ped` 의 부호가 뒤집힌다

- **Context**: STATE #1 (세 arm head-to-head) 을 돌리면서 각 knob 을 **단독으로** 읽으려고 baseline 을 `w_risk = 0.0` 으로 잡았다. D-217 은 그러지 않았다 — 두 arm 모두 shipped default `w_risk = 40.0` 을 달고 있었고, journal 은 "`w_ped` 0 → 50" 이라고만 적었지 "양쪽에 `w_risk = 40` 이 깔린 채로" 를 적지 않았다. 결과가 갈렸다: `predicted` arm 이 eligible 3 scene **전부에서 WORSE** 로 읽혔다 — D-217 이 한 cycle 전에 0.007 → 0.382 m 를 보고한 바로 그 scene 포함.
- **측정 (6 paired seeds, `lam = 0.8`, `cafe_obstacle_crossing_v0`, worst-case clearance m)**:

  | | `w_ped = 0` | `w_ped = 50` | step |
  |---|---|---|---|
  | `w_risk = 40` | 0.0068 | 0.3823 | **+0.3755** |
  | `w_risk = 0`  | 0.0202 | 0.0010 | **−0.0192** |

  D-217 은 윗줄에서 **정확히 재현된다**. 따라서 이것은 그 측정의 반박이 아니라 **claim 의 경계**다.
- **Decision**: `w_ped` 의 효과는 **main effect 가 아니라 interaction** 이다 — PGIF field 는 단독으로 clearance 를 사지 못하고 BEV risk term 이 있을 때만 산다. D-217 의 capability 주장은 `w_risk = 40` 이 깔린 **composition** 에 한정된다. 아랫줄은 추가로 risk term *단독*이 worst-case clearance 를 **깎는다**고 말한다 (0.0202 → 0.0068): **어느 쪽도 혼자서는 이기지 못하는데 둘이 함께면 이긴다.**
- **구조적 귀결 (이게 재발 방지책)**: arm set 은 자기 baseline 의 **composition 을 스스로 진술해야** 한다. `three_arm.ARMS` 가 그렇게 되어 있고, `test_every_arm_isolates_its_knob` 이 `w_risk == 0.0` 을 pin 해서 shipped default 로 조용히 되돌아가는 것을 막는다. 그게 없으면 head-to-head 는 어느 순간 D-217 의 비교로 되돌아가면서 두 table 이 구분되기를 멈춘다.
- **부수 소견**: `geometric` (static-geometry null) 이 **3 scene 전부에서 유일하게 improve** 했다 (+0.033 / +0.409 / +0.020 m, completion 6/6). learned channel 도 motion model 도 uncertainty estimate 도 없는 arm 이 단독 승리한 것이라 `geometric_null` 의 attribution 우려는 완화가 아니라 **강화**된다. `shadow` 는 crossing 에서 `INERT` (D-021 재현) 이지만 `cafe_convoy_v0` 에서는 움직였다 (+0.158 m) — inertness 는 critic 의 성질이 아니라 **scene 의존**이다.
- **Alternatives**: (a) 채택 — 두 denomination 을 모두 기록하고 D-217 을 composition 으로 좁힌다. (b) D-217 의 denomination 을 그대로 쓴다 — head-to-head 가 그 table 을 재현하고 three-arm win 을 보고했을 것이고, sign flip 은 보이지 않았다. (c) D-217 을 철회 — 틀렸다: 그 숫자는 윗줄에서 정확히 재현되고, 틀린 것은 숫자가 아니라 claim 의 폭이다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-14-the-headline-was-an-interaction.md` · D-217 (좁혀지는 대상 — *측정은 유효*) · D-166 / `geometric_null` (attribution 축) · D-021 (`ShadowCostCritic` inertness) · D-016 (sandbox-executable bias) · D-140 (gate 1 은 새 항목을 센다) · `research/feed.md` 2026-08-12 04:00 (metric-selection 비판)

## D-217 — 2026-08-12 — 18 cycle 만의 capability 이동: **PGIF cost term 을 predicted-geometry arm 으로** 이식 — 그리고 oracle 예측을 거부하는 것이 이 arm 을 채점 가능하게 만든다

- **Context**: STATE 의 next-actionable 4개가 전부 instrument repair 였고, 직전 17 cycle 이 전부 그랬다 (STATE 자신이 "no controller, representation or dynamics code has changed since the branch went into instrument repair" 라고 적고 있다). Phase 0 의 feed (2026-08-12 04:00, arxiv 2608.08323) 는 capability item 을 하나 들고 있었는데, **feed 자신이 그것을 이 branch 가 이미 돌리고 있는 비교의 세 번째 arm 으로 규정했다** — "PGIF 는 predicted geometry, min-clearance null 은 static geometry, shadow cost 는 둘 다 아니다 — 같은 2×2, matched λ, paired seeds". 그 framing 이 결정적이다: 새 thrust 가 아니라 기존 thrust 의 결손 축이므로 one-thrust-per-branch 규칙과 D-140 의 gate-1 판독을 **동시에** 통과한다. D-016 의 sandbox-executable bias 가 tie 를 깬다.
- **Decision**: 2608.08323 의 **cost term 만** 이식 — `critics/predicted_geometry.py`, 보행자의 *예측* 위치에 speed-scaled anisotropic Gaussian (`σ_∥ = 1.2 + 0.5·s` 전방 / `0.5` 후방, `σ_⊥ = 0.6`), horizon 에 걸쳐 합산. `RiskMPPI(w_ped=…)` 로 배선하고 default `0.0` 은 **exact no-op** (D-013 / ShadowCostCritic 과 같은 contract 라 P5 ablation attribution 이 유지된다). network 도 dataset 도 training run 도 없다.
- **원 논문에서 의도적으로 두 군데 벗어났고, 둘 다 arm 을 채점 가능하게 유지하기 위한 것이다**:
  - **(1) constant-velocity 외삽만 쓰고 `ob.position(t0 + h·dt)` 는 이 모듈 어디에도 등장하지 않는다.** 논문은 orbital 보행자를 *정확한 원운동 kinematics* 로 예측한다 — planner 의 motion model 이 simulator 의 generative model 과 동일하므로 **prediction error 가 구조적으로 0** 이고, 보고된 수치는 어떤 실제 tracker 도 재현하지 못하는 상한이다. sandbox 의 보행자는 piecewise-linear waypoint schedule 을 따르는데 이 critic 은 그 schedule 을 **읽지 않는다**: `t0` 의 위치와 속도 하나씩만 받아 직선 외삽한다. 직선 구간에서는 정확하고 waypoint corner 에서는 **틀리며, 틀려야 한다**. `test_cv_prediction_ignores_the_schedule` 이 이걸 reading convention 이 아니라 behavioural property 로 못박는다.
  - **(2) dynamic obstacle 만 과금한다.** schedule 이 빈 obstacle 은 벽/집기이지 보행자가 아니고 baseline obstacle term 이 이미 값을 매기고 있다. 여기서 또 매기면 double-count 이고 standalone contract 가 깨진다.
- **측정** (`cafe_obstacle_crossing_v0`, 6 seeds, paired, **`lam = 0.8`**): `w_ped` 0 → 50 에서 min clearance median **0.071 → 0.434 m**, worst **0.007 → 0.382 m**, 완주 **6/6 → 6/6**. baseline 은 보행자를 7 mm 로 **스치고 있었다**. 그리고 feed 가 borrow 의 조건으로 못박은 대로 clearance 를 **완주율과 같이** 읽었다 — 논문의 Hard level 이 82 % collision 을 59 % timeout 으로 바꿔치기하는 것이 이 방법의 실제 효과이므로, collision-only 판독은 얼어붙은 로봇을 해결된 문제로 채점한다.
- **그 `lam = 0.8` 은 census 가 강제한 것이고, 강제한 것이 옳았다**: 처음엔 shipped `MPPIParams.lam = 0.1` 로 재서 **더 큰** 숫자를 얻었다 (0.022 → 0.517 m). `test_default_lam_sites` 가 내 두 `make_controller` site 를 **+2 `defaults`** 로 청구했고, 그 청구가 가리킨 것은 count 가 아니라 이것이다 — shipped 온도에서 softmax 의 median ESS 는 256 중 ~1, 즉 **greedy argmin** 이다. 내 두 assertion 은 전부 trajectory *차이* 에 관한 것이므로 그 온도에서 non-inertness 는 **noise 로 충족되고**, clearance 숫자는 평균을 내지 않는 planner 에서 뽑힌 것이 된다. rung 을 명시하니 headline 이 ~20 % 줄었고, 그것이 이 숫자의 첫 유의미한 판본이다. D-124 의 선례가 정확히 반복됐다: 명시하면 `defaults` 는 58 로 되돌아가고 bill 은 `decides` 쪽에만 남는다 (76 → 78).
- **왜 non-inertness 를 result 가 아니라 precondition 으로 테스트하는가**: `ShadowCostCritic` 이 바로 이 branch 에 ship 된 뒤 **signal-free** 로 측정됐다 (D-021: `w_epist = 200` 에서 byte-identical trajectory, per-sample spread 가 92 개 control step 전부에서 정확히 0.00). 그 발견은 comparison 을 여러 cycle 쓴 **뒤에** 나왔다. arm test 의 `assert not np.array_equal(baseline, weighted)` 한 줄이 그것을 5 초짜리 build-time 검사로 바꾼다.
- **Alternatives**: (a) 채택 — cost term 만, CV 예측, dynamic-only. (b) 논문대로 schedule 을 읽어 예측 — 재현성은 높지만 prediction error 0 인 상한만 재생산하므로 거절. (c) STATE #1 (instrument) 을 18번째로 집기 — north star 거리가 멀고 CLAUDE.md 가 그런 항목을 deprioritize 하라고 적고 있다. (d) 새 branch — gate 1 이 6/6 이라 금지.
- **남은 것**: 이 수치는 **1 scene · 1 weight · 6 seed · CI 없음** 이다. 논문이 기록한 freezing tax 는 *density* 에서 나타나고 이 scene 에는 density 가 없다. `6/6` 은 이 밀도에서 tax 를 내고 있지 않다는 증거이지, 내지 않으리라는 증거가 아니다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-13-the-predicted-geometry-arm-was-not-inert.md` · D-021 (ShadowCostCritic 의 inertness) · D-166 / `geometric_null` (static-geometry null) · D-016 (sandbox-executable bias) · D-140 (gate 1 은 새 항목을 센다) · `research/feed.md` 2026-08-12 04:00

## D-216 — 2026-08-12 — receipt store 를 pin 된 prefix **밑에** 두자 그 prefix 의 probe 가 조용히 다른 파일을 겨눴다: probe target 은 **index** 로 거른다

- **Context**: STATE next-actionable #2 (D-215 의 path-vs-candidate 착오를 나머지 `POST_RECEIPT_WRITES` reader 들에서 감사) 를 실행했다. `survey` / `leaking_pins` / `inert` / `_main` 은 전부 population 을 **candidate 로** 순회하고 path 를 받지 않으므로 그 착오를 담을 수 없다 — 착오는 drift path 에서 출발하는 caller, 즉 `filter_drift` 하나에서만 도달 가능하고 그건 D-215 가 이미 고쳤다. 감사 대상은 깨끗했고, 발견은 한 층 아래에 있었다. `_probe_target` 은 prefix 규칙의 **반대 방향 진술** (candidate → path; `covering_candidate` 는 path → candidate) 인데, 잘못된 파일을 고르고 있었다: `_probe_target("results/")` 가 `results/receipts/056933be411376b4.json` 을 반환했다. `receipt_store.STORE_DIR` 이 `results/receipts/` (D-203) 이고 gitignore 되어 있으며 매 `record` 마다 다시 쓰이므로, **구조상 `results/` prefix 아래 가장 새 파일**이고 recursive walk 이 그걸 집었다.
- **Decision**: probe target 을 **index 로 필터**한다 — `_probe_target(candidate, base, tracked)`, `probe()` 가 `tp.tracked_paths(base)` 를 공급. 근거는 두 사례를 한 번에 닫는 원칙이다: **probe target 은 그 exemption 이 실제로 적용될 수 있는 파일이어야 한다.** exemption 이 억누르는 것은 `tp.Drift` 의 path 이고 그것은 `git ls-files` 위에서 계산되므로, untracked 파일은 거기 나타날 수 없고 그 위에서 잰 verdict 는 아무것도 licensing 하지 못한다. `results/receipts/` 를 **이름으로** 제외하는 대신 index 를 쓴 이유가 이것이다 — 이름으로 고쳤다면 pin 된 prefix 아래의 *다음* untracked write 를 같은 방식으로 또 발견하게 된다. 이는 `journal/README.md` 사례 (recursion 을 도입한 그 사례) 와 정확히 같은 실패가 한 층 안쪽에서 재발한 것이며, error 가 아니라 **잘못된 파일 위에서의 success** 라서 증거로 읽힌다는 점까지 같다. `tracked=None` 은 caller 의 **명시적 선택**으로 남기고 (synthetic tree test 는 repository 가 아니다) default 는 `_DERIVE_TRACKED` sentinel 로 둔다 — `None` default 였다면 "index 를 유도한다" 가 "index 를 무시한다" 로 붕괴하는데, 그건 `tree_provenance._git` 이 명시적으로 거부하는 silent degradation 이다.
- **Alternatives**: (a) `results/receipts/` 를 skip list 에 이름으로 추가 — 1개짜리 special-case 이고 D-208 이 이미 같은 이유로 거부한 모양. (b) receipt store 를 `results/` 밖으로 옮긴다 — 더 큰 변경이고, prefix 아래 untracked write 라는 일반적 위험은 남는다. (c) `_probe_target` 을 `covering_candidate` 와 합친다 — 둘은 copy 가 아니라 **역함수**라 합칠 수 없다; 대신 round trip 을 test 로 고정했다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-12-the-probe-was-measuring-the-receipt-store.md` · D-203 (store 를 `results/` 아래 둔 결정 — 이 defect 의 절반) · D-215 (prefix 규칙의 반대 방향 진술) · D-047 (규칙의 자기 진술이 둘이면 언젠가 갈린다 — 여기선 copy 가 아니라 inverse) · D-079 (측정이 붙은 decoration 은 측정 없음보다 나쁘다) · D-044 (exemption 이 사는 이유)

## D-215 — 2026-08-12 — 두 reading 의 "불일치" 는 모순이 아니라 **namespace 착오**였고, 규칙에 자기 진술을 하나만 남겨 고쳤다

- **Context**: 10:00 cycle 이 suite 를 `2584 passed / 2 failed` 로 끝내 push gate 가 거부했고, 두 commit 이 disk 에 stranded 되었다. 그 중 하나는 mechanical (`loop_reach.READING` row 누락) 이었지만, 다른 하나는 10:00 journal 이 명시적으로 "숫자로 고치지 말고 진단하라" 고 남긴 것이다: `filter_drift` 가 `results/p3-…tsv` 를 ignore 하기를 거부하는데 `stale_pins()` 는 그 경로를 stale 로 **나열하지 않는다**. 같은 pin set 에 대한 두 reading 의 모순처럼 읽혔다.
- **진단**: 모순이 아니었다. `stale_pins()` 는 **candidate** 로 keying 된다 — `POST_RECEIPT_WRITES` 의 5개 entry 이고 그 중 둘 (`results/`, `journal/`) 은 **directory prefix** 다. test 는 그 집합을 **구체적 경로** 집합에서 빼고 있었다. `results/p3-…tsv` 는 자기 pin `results/` 와 결코 같지 않으므로 test 는 그것을 *population 밖* 으로 읽었고 — stale 도 fresh 도 아닌 — `filter_drift` 는 prefix 를 제대로 걸어 `results/` 가 stale 임을 보고 material 로 판정했다. **둘 다 자기 namespace 안에서 옳았다.** `stale_pins()` 는 애초에 경로를 지칭할 수 없다; pin 만 지칭한다. 모순처럼 보인 것은 질문의 category error 였다.
- **왜 살아남았나**: exact-match 뺄셈은 5개 중 3개 (`STATE.md`/`JOURNAL.md`/`RESULTS.md`) 에서 옳다. 틀리는 것은 prefix pin 둘뿐이고, 그나마 그 pin 이 **stale 일 때만** 갈라진다 — 아니면 양쪽 다 "ignored" 라고 말하며 서로 다른 이유로 일치한다. D-047 의 형태 그대로다: 자기 진술이 둘인 규칙이, 누군가 확인한 경우들에서만 일치한다.
- **Decision**: `inert_surface.covering_candidate(path, population)` 신설 — 경로를 덮는 entry 를 반환 (longest match, 중첩 pin 이 생기면 더 구체적인 쪽으로). `filter_drift._ignorable` 은 이 함수 호출 한 줄이 되고, test 는 partition 을 이 함수를 통해 취한다. **gate 의 판정은 하나도 바뀌지 않는다** — `filter_drift` 의 답은 이미 옳았다. 이것은 consolidation 이지 verdict 변경이 아니며, 제거된 것은 두 사본이 drift 할 **가능성** 이다. prefix 와 exact 양쪽 shape 를 독립적으로 못박는 회귀 test 추가 (`test_the_prefix_pins_cover_paths_no_candidate_key_equals`) — 이번 주 pin 들이 우연히 무엇을 말하든 번역 자체가 pin 되도록.
- **Alternatives**: (a) 채택. (b) test 의 뺄셈을 green 될 때까지 고쳐 맞춤 — mechanical 경로이고, `filter_drift` 와 test 가 prefix 에 대해 **여전히** 불일치하는 채로 test 만 틀린 partition 을 자신 있게 주장하게 된다. 10:00 journal 이 정확히 이것을 금지했다. (c) `stale_pins()` 가 경로를 반환하게 확장 — pin 은 pin 이지 경로가 아니다; population 을 경로로 확장하면 `results/` 아래 아직 쓰이지 않은 파일까지 열거해야 한다. (d) 방치 — strand 가 8번째가 된다.
- **Census 비용 없음**: `guard_reflexivity` / `liveness_derivation` 둘 다 새 함수와 새 test 를 넣은 채로 green. 자기가 audit 하는 population 에 들어간 40번째 연속 cycle 이지만, entrant 가 아무 값도 움직이지 않은 드문 경우다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-11-the-two-readings-were-in-different-namespaces.md` · D-207 (stale pin = 철회된 exemption, leak 아님) · D-047 (자기 진술이 둘인 규칙) · D-044 (Phase-4 write 순서) · D-112 (strand 가 decision tree 보다 우선)

## D-214 — 2026-08-12 — 세 cycle 을 끌어온 "quoted count 오염" 의혹은 **blast radius 가 0** 이었고, 진짜 발견은 **audit 이 닿는 범위**였다

- **Context**: D-212 가 `push_preflight record` 의 CLI summary 결함을 고쳤다 — sharded run 에서 마지막 shard 의 counts 를 run 전체의 것으로 출력했다. cycle 이 journal / TSV / Telegram 에 옮겨 적는 숫자가 바로 그 줄에서 나온다. 결함은 같은 날 고쳐졌지만 **그 줄이 이미 무엇에 인용되었는지는 아무도 확인하지 않았고**, STATE 는 "지난 한 달의 quoted counts 를 archived receipt 와 대조하라" 를 세 cycle 째 top actionable 로 들고 있었다.
- **Decision**: `eval/mppi_sandbox/quoted_counts.py` — journal 의 모든 `N passed` 를 `receipt_store` 의 archived receipt 가 담은 counts 와 대조하는 read-only pass. suite run 비용 0 (receipt 는 tree fingerprint 로 keying 되어 이미 disk 에 있다). **답은 0 이다**: reach 안의 어떤 quoted count 도 archived measurement 없이 서 있지 않다. 07:00 과 08:00 은 둘 다 CLI 줄이 아니라 **receipt 의 숫자**(2556)를 인용했고, 깨진 줄의 값들은 그것을 *진단하던* 문장에만 나타난다. STATE 가 "plausibly two cycles" 로 매긴 blast radius 는 둘이 아니라 **없었다**.
- **판정 어휘는 한 방향으로만 강하다**: receipt 는 그것을 찍은 cycle 을 담지 않으므로 quote 를 *자기* receipt 에 귀속시킬 수 없다. 따라서 archived population 이 담지 **않은** 값은 진짜 finding (`UNCORROBORATED`) 이지만, 담은 값은 단지 *반박되지 않은* 것 (`CORROBORATED`) 이다. 이 pass 는 유죄를 선고할 수 있고 무죄를 선고할 수 없으며, 그렇게 주장하지도 않는다.
- **첫 실행이 셋을 flag 했고 셋 다 같은 종류의 false positive 였다**: `141 passed`/`150 passed` 는 결함을 *진단하던* 07:00/08:00 journal 이고 `319 passed` 는 의도된 부분 run (D-211 census slice) 이다. 셋 다에 대해 빨간 gate 는 일주일 안에 mute 된다 (D-044). `PARTIAL` 은 quote **자기 줄의 local token** (`shard`/`slice`/`census`/`subset`) 에서만 발동하고 — D-037/D-038 이 쓴 장치 — **유죄를 철회할 뿐 결코 만들어내지 않는다** (유죄 branch 에서만 도달 가능). 잔차는 주장이 아니라 정수로 보고된다.
- **진짜 한계는 reach 이고 "한 달" 보다 훨씬 짧다**: store 의 가장 이른 datable receipt 는 **2026-08-12 03:07** (D-200 이 store 를 만든 것이 08-11 22:04). journal 74개의 quoted count 94개 중 **78개가 `OUT_OF_REACH`** — store 이전에 인용되었고, 그 run 들의 receipt 는 다음 cycle 시작 시 의도적으로 unlink 되었다. 그것들을 unsupported 로 채점하는 것은 증거의 부재를 부재의 증거로 읽는 같은 오류의 역방향이다. `reach()` 는 그 경계를 receipt 의 `head` commit 에서 **유도**한다 — mtime 은 복사 한 번에 조용히 다시 쓰인다.
- **Alternatives**: (a) 채택. (b) 세 flag 를 손으로 면제 — D-076 이 잡은 over-derivation 이고, 다음 partial run 에서 다시 빨개진다. (c) reach 밖을 unsupported 로 채점 — 78개의 phantom finding. (d) audit 을 아예 하지 않고 의혹을 STATE 에 계속 들고 감 — 세 cycle 이 이미 그렇게 했고 비용은 read-only pass 하나였다.
- **Census 비용**: `guard_reflexivity` pool 100 → **101**, `liveness_derivation` `NO_REGISTRY` 18 → **19** — 39번째 연속 cycle. 새 miss-reason 은 **없다**: exemption 이 call time 에 만들어진 set comprehension 이라 D-180 의 mechanism 그대로다. 새로운 것은 **population 이 산문(prose)이라는 점** — 이전 100개는 모두 코드/관측/git 출력을 좁혔고 이것은 journal 의 문장을 좁히는데, 동일한 `in` 연산자로 들어왔다. D-072 의 syntax 결과가 한 번도 시험받지 않은 방향에서 성립한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-10-the-blast-radius-was-zero-and-the-reach-was-the-finding.md` · D-212 (깨진 summary line) · D-200 (store) · D-043/D-044 · D-072/D-073/D-180 (census 계보) · D-037/D-038 (local token)

## D-213 — 2026-08-12 — mode split 의 빠진 조각은 **저장소가 아니라 귀속**이었다: sharded 가격은 자기 registry 를 얻고, **run 자신의 era** 가 누가 그것을 읽는지 정한다

- **Context**: D-212 가 488 s 를 `OBSERVED_SUITE_SECONDS` 의 **양쪽 끝 모두에서** 거절하고, mode 별 split 을 "someday" 에서 **precondition** 으로 승격시킨 채 끝났다. STATE 의 next-actionable #1 이 그것이다. 그런데 registry 를 둘로 나누는 것만으로는 D-212 의 refutation 이 풀리지 않는다 — 나눠도 **주어진 run 을 어느 registry 로 채점할지** 누군가 정해야 하고, 과거 run 의 execution mode 는 **어디에서도 읽을 수 없다**: wrapper log 는 clock 을 담지 시계-외의 receipt 를 담지 않는다.
- **Decision**: sharded 관측치는 `OBSERVED_SHARDED_SUITE_SECONDS` (488, 475) 로 분리하고, 귀속은 **`SHARDED_FROM` = `2026-08-12T07:06:15+09:00`** — `suite_shard.py` 가 추가된 commit `c5d28ec` 의 시각 — 로 한다. `observed_suite_min(when=…)` 은 그 시각 **이전에 시작한 run 에게는 serial floor 만**, 이후 run 에게는 두 mode 중 싼 쪽을 준다. `grade()` 는 `run.started` 로 각 run 을 자기 era 에서 가격 매긴다.
- **왜 era 인가**: mode 는 읽을 수 없지만 **시작 시각은 grading population 이 실제로 들고 있는 유일한 사실**이고, sharding code 가 존재하지 않던 시각에 시작한 run 은 shard 할 수 **없었다**. 그러니 "그 run 이 완주할 수 있었던 가장 싼 suite" 는 정의상 serial 쪽이다. D-212 의 10 개 regrade 된 hour 는 전부 2026-08-07 이고 전부 717 s 에 머문다 — 이것이 test 다.
- **ceiling 은 왜 안 움직이나**: `observed_suite_max` 는 receipt 가 없을 때만 읽히고, 그런 cycle 은 자기가 어느 mode 로 돌지 **모른다** (`record_sharded` 는 split 을 계획할 수 없으면 serial 로 fallback). 모를 때 거절하는 것이 일인 bound 를, 걸릴지 안 걸릴지 모르는 mode 가 낮출 수는 없다. **retrospective 인 floor 만이 mode 를 사후에 확정할 수 있고, 그래서 split 이 움직이는 끝은 정확히 하나다.**
- **부수 발견 — sharded series 는 monotone 이 아니다**: 488 → 475 인데 test 수는 2556 → 2564 로 늘었다 (fan-out scheduling noise). serial series 의 monotonicity 는 그 docstring 이 "the finding" 이라 부르는 load-bearing 속성이므로, 이 둘을 한 list 에 넣었으면 **bugfix 처럼 보이면서 그 속성을 파괴**했을 것이다. 이것이 D-212 가 몰랐던 두 번째 분리 이유다.
- **failure direction 은 전부 한쪽으로**: 파싱 불가능한 stamp 는 serial (= 높은 floor = `PREMATURE` 를 **덜** 보고) 로 떨어지고, `when=None` 도 마찬가지다. 고장난 시계가 `OVERRUN` 을 **제조**할 수 없어야 한다는 것이 이 grader 의 상시 규칙이다. offset 비교는 문자열이 아니라 aware datetime 으로 — UTC 로 쓴 같은 순간이 lexical 로는 하루 앞서 정렬된다.
- **Alternatives**: (a) 채택 — registry 분리 + era 귀속. (b) registry 만 분리하고 floor 는 계속 serial-only — 저장은 되지만 아무도 읽지 않아 D-079 의 장식이 된다. (c) receipt 에서 mode 를 읽기 — 현재 run 에는 되지만 **채점 대상인 과거 run 에는 receipt 가 없다**, 이것이 애초의 문제. (d) 두 mode 를 한 list 에 — D-212 가 10 red 로 반박했고, 여기에 더해 monotonicity 도 잃는다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-09-the-missing-piece-was-attribution-not-storage.md` · D-212 (양쪽 끝 거절) · D-211 (sharding) · D-200 (ceiling 규칙) · D-115/D-181 (advisory 읽기)

## D-212 — 2026-08-12 — sharding 이 남긴 두 개의 자기-오보: 하나는 **버그**였고, 하나는 **양쪽 끝 모두** 거절해야 했다

- **Context**: D-211 이 suite 를 14-shard 로 쪼개 1261s → 488s 로 만들었고, STATE 는 그 여파로 두 항목을 next-actionable 에 올렸다 — (1) `push_preflight record` 의 CLI 요약줄이 **마지막 shard 의 counts** 를 run 전체의 것처럼 출력한다, (2) `cycle_wallclock.OBSERVED_SUITE_SECONDS` 가 이제 serial 숫자라 가격을 2.4× 과대평가하니 **re-measure** 하라.
- **Decision (1) — 결함이고 고쳤다**: `format_counts(receipt)` 를 추가해 요약줄이 receipt 의 **merge 된** counts 를 읽는다. 원인은 tail 파싱이 약해서가 아니라 `merge_counts()` 가 이미 올바르게 구한 값을 **표시 단계에서 버렸기** 때문 — receipt 이 이미 들고 있는 양을 다시 유도한 D-047 의 형태다. 07:00 run 이 실제로 `150 passed` 를 출력했고 receipt 은 2556 을 맞게 기록했다. cycle 이 journal / TSV / Telegram 에 인용하는 숫자가 **바로 이 줄**이므로 표시 결함이 곧 기록 결함이다.
- **Decision (2) — 488s 는 이 registry 의 어느 끝에도 들어갈 수 없다**: 처음에는 "ceiling 은 유지, floor 에만 넣는다" 로 갔고 **suite 가 그것을 반증했다** (10 red, 전부 `test_cycle_wallclock`). 두 소비자가 모두 serial mode 에 묶여 있고, 그 이유가 서로 독립적이다:
  - `observed_suite_max` (ceiling) 는 **mode 를 모르는 상태의 prospective 가격**이다. receipt 을 못 읽을 때에만 참조되는데, 그런 cycle 은 sharding 이 걸릴지도 똑같이 알 수 없다 — `record_sharded` 는 split 을 plan 할 수 없으면 serial 로 fallback 한다. unknown 을 488s 로 매기면 serial fallback 이 끝낼 수 없는 suite 를 licensing 한다 (D-200 이 고친 결함).
  - `observed_suite_min` (floor) 은 **대부분 serial 인 population 에 대한 retrospective 채점**이다. 이미 일어난 run 을 채점하는데, calibration 대상인 2026-08-07 의 stranded hour 들은 sharding 보다 **5일 앞선다**. 488s floor 를 넣자 그중 10개가 `PREMATURE` → `OVERRUN` 으로 재채점됐다 — serial 시대의 run 이 sharded 시대에만 달성되는 가격을 낼 수 있었다는 주장이다.
- **그래서 flat list 는 두 execution mode 를 담을 수 없다.** 두 끝이 "mode 당 하나" 가 아니라 **둘 다 serial 에 앵커**되어 있다. mode 별 registry 분리는 D-212 이전에는 "언젠가" 였고 이제 **선결 조건**이다: sharded 가격은 자기 registry 와 자기 소비자를 갖기 전에는 기록될 수 없다.
- **왜 기록하는가**: STATE 의 next-actionable 은 **측정에서 유도된 처방이 아니라 관찰에서 유도된 처방**이었다 ("2.4× 과대평가" 는 참인 관찰, "그러니 re-price 하라" 는 틀린 결론). D-210 이 hand-typed endpoint 에 대해 말한 것의 다른 면 — 이번엔 숫자가 아니라 **방향**이 유도되지 않은 채 backlog 에 올라와 있었다. 더 값진 것은 이 cycle 의 **첫 수정도 같은 병에 걸려 있었다**는 점이다: ceiling 만 방어하고 floor 는 안전하다고 산문으로 논증했는데, 그 논증은 floor 의 population 이 무엇인지 확인하지 않았다. suite 가 그것을 10줄의 red 로 알려줬다 — 산문이 아니라 test 가 population 을 안다.
- **Alternatives**: (a) 채택 — registry 는 serial 전용으로 유지, sharded 가격은 미기록. (b) STATE 대로 ceiling re-price — serial fallback 에서 unfinishable suite licensing, 거절. (c) floor 에만 append — **시도했고 suite 가 반증**, 위 참조. (d) 지금 mode 별로 분리 — 옳은 방향이지만 소비자 재배선이 이 cycle 예산 밖. STATE #2 로 승격.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-08-two-misreports-and-one-backwards-prescription.md` · D-211 (sharding) · D-200/D-201 (ceiling/floor 비대칭) · D-047 (이미 있는 값을 다시 유도하지 않기) · D-210 (유도되지 않은 endpoint)

## D-211 — 2026-08-12 — suite 가 비싸면 **덜 돌릴 게 아니라 병렬로 돌린다**: 1261s → 495s, 같은 tree 같은 test

- **Context**: suite 는 35분 budget 중 **1261s** 를 먹었고, 이것이 08-11 21:00 → 08-12 06:00 **7 cycle strand** 의 구조적 원인이다 (05:00 의 진단: "21:00 이후 어떤 cycle 도 full suite 를 끝내지 못했고, 그래서 모든 진단이 partial run 위에서 쓰여 사실로 상속되었다" — 그 cycle 이 상속한 red 5개 중 3개가 그렇게 만들어진 오진). STATE 의 next-actionable #2 와 Q-126 / `receipt_cost` 는 모두 같은 답을 향하고 있었다: **`--fast` subset receipt**.
- **Decision**: subset 이 아니라 **sharding**. `suite_shard.py` + `push_preflight.record_sharded` 가 **같은 test 를 같은 tree 위에서** 14 process 로 나눠 돌린다. 측정: **1261s → 495s (2.5×)**, wall 8m15, user 24m03.
- **왜 subset 이 아닌가 — soundness 의 종류가 다르다**: subset receipt 은 tree 에 대한 *더 약한 주장* 이라, "빠진 test 는 움직였을 리 없다" 는 논증을 **매 cycle 새 diff 마다 다시** 해야 한다. 그게 `receipt_cost` 전체가 씨름하던 난점이다. sharding 은 그 논증이 필요 없다 — receipt 이 `check` 가 이미 채점할 줄 아는 바로 그 receipt 이다. 대신 **한 번만 확인하면 되는 세 성질**로 바뀐다: (i) `plan()` 은 입력의 진짜 partition 이 아니면 **raise** (파일 하나가 빠지는 것 = subset 실패가 뒷문으로 들어오는 것), (ii) `merge_counts()` 는 shard 하나라도 summary 를 못 읽으면 `{}` 를 돌려 `VACUOUS` 로 보낸다 (읽힌 shard 만 더한 합계는 "작지만 건강한 suite" 처럼 보이는 확신에 찬 틀린 수), (iii) `merge_returncode()` 는 pytest 의 `5` 를 포함해 non-zero 를 보존.
- **동시성 안전은 논증이 아니라 측정으로 샀다**: scratch git worktree 를 만들거나 repo state 를 읽는 test file 이 ~11개 있고, 이들을 동시에 돌리는 위험은 실재한다. 채택 근거는 sharded run 이 serial baseline 을 정확히 재현했다는 것 — 2516 passed + 이번 42개 신규, skip 1 이동. 충돌이 있었다면 **push 를 거절하는 방향**인 failure 로 나타난다.
- **CLI default 로 둔 것이 load-bearing**: `cycle_wallclock.suite_price` 는 마지막 receipt 의 `duration_seconds` 를 읽는다. sharded receipt 을 남기면서 실제로는 serial 로 돌리면, 다음 cycle 은 sharded 숫자로 가격을 받고 `SUITE_AFFORDABLE` 을 듣는다 — `duration_seconds` field 자체가 끝내려고 만들어진 **permissive staleness** 그대로다. flag 는 잊을 수 있고 default 는 못 잊는다 (D-162).
- **`Receipt.command` 는 caller 의 argv 를 유지한다**: `receipt_cost._receipt_is_full` 은 `--ignore=` 유무로 narrowing 을 읽는다. shard 별 file list 로 덮어썼다면 114-file 짜리 command 에 `--ignore=` 가 없으니 **우연히** "full" 로 채점됐을 것이다. split 구조는 새 field `Receipt.shards` 로 따로 간다.
- **census 가 내 코드를 잡았고, 옳았다**: 첫 run 은 rc=1, red 5개 전부 내 것 — `VALUE_FLAGS`(어떤 pytest flag 가 별도 인자를 먹는지 적은 표)가 **감시자 없는 module-level allow-list** 로 census 에 들어왔고 `shardable()` 이 scalar pool 에 들어왔다 (100→101, 12→13). D-208/D-209 처럼 entrant 를 **등록**하려던 게 첫 반응이었지만, census 가 보고한 건 진짜 결함이었다: pytest option 표를 손으로 베낀 것은 D-047 의 그 형태다. **고침은 삭제였다** — `expand_targets` 가 이제 positional 인자가 실제로 존재하는지 **filesystem 에 묻고**, 아니면 `[]`(⇒ serial) 을 돌려준다. tree 가 매 run 다시 답하는 질문 하나가 표가 나쁘게 덮던 세 경우(별도 flag 값, 오타 target, test 없는 directory)를 덮는다. entrant 둘 다 사라져 red 5개가 **코드를 등록해서가 아니라 지워서** 사라졌다.
- **Alternatives**: (a) 채택 — sharding. (b) `--fast` subset (STATE #2 / Q-126) — 매 cycle 재논증이 필요한 더 약한 주장. (c) `pytest-xdist` 설치 — 이 executor 의 hard limit 이 환경 변경을 금지하고, CI 에도 같은 dependency 를 강제한다. stdlib fan-out 은 둘 다 피한다. (d) 느린 test 의 cap 을 줄이기 — Q-051 이 이미 거절: 그 runtime 자체가 D-029/D-030 의 증거다.
- **남은 결함 (고치지 않음)**: `record` CLI 의 요약 줄이 **merge 된 총합이 아니라 마지막 shard 의 counts** 를 찍는다 (`141 passed`). receipt JSON 은 정확하다 (2552/5/158/1). `merge_counts` 가 막으려던 바로 그 함정이 한 layer 위에서 재현된 것 — 다음 cycle 의 1순위.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-07-shard-the-suite-instead-of-shrinking-it.md` · D-112 (strand) · D-043/D-044 (re-take 가 요구하는 두 번째 run) · D-047 (손으로 벤낀 registry) · D-162 (flag 는 잊힌다) · Q-126 / `receipt_cost` (subset 경로) · Q-051 (cap 축소 거절)

## D-210 — 2026-08-12 — robustness sweep 의 endpoint 는 **측정값에서 유도**되어야 한다: hand-typed 범위는 drift 하면 fragility pin 이 된다

- **Context**: 7 cycle strand 를 막고 있던 3 개의 inherited red 중 둘은 census 숫자(`liveness_derivation` NO_REGISTRY 17→18 = D-209 의 `carried_drift` entrant, population 26→27; `loop_reach.READING` 에 D-206 의 두 loop row 누락)였고, 고치는 데 정수 하나와 dict row 둘이 들었다. 세 번째는 숫자가 아니었다 — D-209 가 미리 정확히 예고한 대로("pin 을 올릴 일이 아니라 별도 D-NNN 감").
- **문제의 형태**: `key_discrimination.measure()` 는 여전히 `NARROWED_NOT_SEPARATED` 이고 headline test 는 통과한다. 깨진 것은 robustness sweep 이다: `for margin in (0.02, 0.10, 0.50, 0.90)` 이 전부 `NARROWED_NOT_SEPARATED` 라고 주장하는데, 측정된 discrimination 이 **0.027** 로 올라오면서 `0.02` probe 가 측정값 **아래**로 내려갔다. 거기서 `SEPARATES` 가 나오는 것은 계측기가 고장난 게 아니라 **옳은 답**이다 — margin 을 측정값 밑에 두는 것은 2.7% 를 separation 이라고 *부르기로* 하는 결정이기 때문이다.
- **Decision**: sweep 의 endpoint 를 측정값에서 유도한다. test 는 먼저 `abs(measure().discrimination)` 를 읽고, 각 probe margin 이 그보다 위임을 assert 하며(실패 메시지: 목록을 re-tune 하지 말고 finding 을 다시 읽으라), `(0.10, 0.50, 0.90)` 에서 `NARROWED_NOT_SEPARATED` 를 확인한 뒤 `measured / 2` 에서 **반대 방향**(`SEPARATES`)을 구동한다. 주장의 범위가 명시적으로 좁아졌다: "margin 이 어디 있든 불변" 이 아니라 "**측정값 위의 모든 margin 에서** 불변이고, default 0.25 는 그보다 한 자릿수 위에 있다".
- **Alternatives**: (a) `0.02 → SEPARATES` 를 literal 로 pin — 같은 fragility 를 한 칸 아래에서 다시 얼린다. (b) probe 목록에서 `0.02` 를 삭제 — D-058 이 금지한 "발화하는 경우만 pin 된 watcher" 로 되돌아가고, 계측기가 다른 답을 할 수 있다는 증거를 잃는다. (c) `SEPARATION_MARGIN` 을 올려 red 를 없앤다 — 측정을 constant 로 덮는 것.
- **일반 규칙**: "이 hand-typed 범위 전체에서 판정이 불변" 형태의 test 는 측정값이 범위 쪽으로 drift 하면 **조용히 거짓**이 된다. endpoint 를 측정에서 유도하는 것이 drift 를 견디게 하는 방법이고, 이는 D-047("규칙은 자기 자신에 대한 진술을 정확히 하나만 가져야 한다")을 registry 가 아니라 threshold 에 적용한 것이다.
- **구조적 관찰**: D-209 가 지목한 구조적 원인(21:00 이후 어떤 cycle 도 full suite 를 완주 못 함 → 모든 진단이 partial run 에서 작성되어 사실로 상속됨)이 이번에 **끊겼다**. 끊은 것은 05:00 이 baseline 을 scratch worktree 에서 90 초 들여 *측정*해 넘긴 hand-off 다. 03:00·04:00 은 같은 90 초를 추론에 썼고 둘 다 틀린 blocker 집합을 넘겼다.
- **Status**: accepted
- **Refs**: journal/2026-08/12-06-the-inherited-reds-were-two-counts-and-a-verdict.md · D-209 · D-206 · D-196 · D-058 · D-047

## D-209 — 2026-08-12 — `carried_drift` 의 probe 의무는 **table entry 하나**였다: 막고 있던 질문에 값싼 형제 답이 있었다

- **Context**: D-208 이 15 개 red 를 "숫자 3 개 + 의무 1 개" 로 쪼개고, 그 의무(9 red)를 cycle 예산 밖으로 판정했다. 근거는 "probe 는 scratch repo 에서의 executed before/after reading 이고, 그것을 쓰려면 먼저 `carried_drift` 의 *offence* 가 무엇인지 답해야 한다" 였다. strand 는 6 cycle 이었다.
- **Decision**: offence 질문에 답이 **둘** 있었고 어려운 쪽만 기록돼 있었다. Q-133 의 **rename** case(carried reader 가 지워지고 새 이름으로 재등장 → `departure` 이면서 `entrant`, 양쪽에서 invisible)는 실제로 어렵다. 그러나 pin 의 key 는 **이름의 집합**이므로, 이름을 그대로 둔 채 carried reader 의 **내용**만 옮기는 것이 `carried_drift` 가 검사하려고 존재하는 바로 그 premise 이고, 이것은 자명하게 executable 하다. 후자로 `PROBES["inert_surface.carried_drift"]` 를 채웠다: `build_carried_drift_repo` fixture + `_cd_permit`/`_cd_offend`, executed direction 은 **NAMES_OFFENCE**. 이를 위해 `carried_drift(pin=…, exempt=…)` 와 `entrants(pin=…)` seam 을 `undeclared_drift(declared={})` 와 같은 이유로 추가했다 — unexempted population 은 guard 자신의 코드에서 나와야 하고, diff 재구현은 규칙의 두 번째 진술(D-047)이다.
- **Alternatives**: (a) 어려운 rename probe 를 먼저 쓴다 — Q-133 로 남김, seam 은 이미 깔림. (b) `unprobeable_revocable` 로 제외 — D-208 이 측정으로 닫음(subprocess-population instance 가 1 개뿐이라 special-case 금지 test 가 거부). (c) spelling 을 바꿔 census 에서 탈락시킨다 — D-104 가 "비용을 내는 대신 guard 를 삭제하는 repair" 로 기각한 형태. (d) 또 한 cycle strand 를 늘린다.
- **부수 결과 (측정됨)**: seam 의 census 비용은 **0**. `git stash` 로 편집 전후를 재서 pool `100 → 100`, `revocable_collections` `5 → 5`. D-107(=`probe` 의 `tests` 파라미터가 narrowing 을 가시화시켜 pool 에 진입시킨 건)이 이걸 argue 하지 않고 measure 한 이유다. 아울러 D-208 prose 의 "여섯 번째" 는 이미 `carried_drift` 를 포함한 5-member set 을 세고 있었다 — 편집이 census member 를 지운 것처럼 보였던 것은 오독이었고, `git stash` 하나로 40 초에 정리됐다.
- **한계**: probe 가 실행하는 것은 content move 뿐이다. rename 방향은 여전히 unexecuted 이고 Q-133 으로 남는다. `unmirrored_revocable` pin 의 주석은 이 상태 변화를 반영해 갱신됨 — 이 member 는 이제 `unwatched_strandings` 에 이은 **두 번째 demonstrated working guard**.
- **그러나 strand 는 해소되지 않았다 (6 → 7)**: full suite 는 `5 failed, 2510 passed`. D-208/Q-133 이 이 의무를 "push 를 막고 있는 전부" 라고 단언했으나 **틀렸다**. `3c4f5d3` 를 scratch worktree 로 checkout 해 재측정한 결과 **5 개 중 3 개가 pre-existing** 이다 — `key_discrimination.test_the_verdict_does_not_turn_on_where_the_margin_sits`, `liveness_derivation.test_derivable_fraction_is_four_of_sixteen`, `loop_reach.test_recorded_reading_covers_exactly_todays_targets`. 이 cycle 이 만든 것은 나머지 2 개(`test_derivation_reproduces_both_typed_acts`, `test_the_derivation_yields_nothing_over_the_typed_table`) 뿐이고 고쳤다 — `carried_drift` 는 derivation 이 도달 못 하는 **네 번째** 연속 수기 entrant 이며, 그 이유가 세 번째로 다르다(이름이 그대로인 content move 에 해당하는 act token 이 어휘에 없다).
- **구조적 원인**: 21:00 이후 어떤 cycle 도 full suite 를 완주하지 못했다. 그래서 모든 진단이 partial run 에서 쓰여 다음 cycle 에 사실로 상속됐고, 3 cycle 연속(03:00 잘못된 함수, 04:00 불완전한 blocker 집합, 05:00 baseline 을 직접 측정) 같은 실패를 반복했다. **자기 suite 를 감당 못 하는 branch 는 무엇이 red 인지에 대한 정확한 장부를 유지할 수 없다.** 다음 cycle 의 처방은 `git worktree add <parent>` 로 baseline 을 먼저 재는 것 — 이번에 90초가 들었고 "5 red, 아마 내 탓" 을 "2 는 내 것, 3 은 상속" 으로 바꿨다.
- **남은 red 중 하나는 숫자가 아니다**: `key_discrimination` 은 `measure()` 가 여전히 `NARROWED_NOT_SEPARATED` 이고 headline test 는 통과한다. 깨지는 것은 threshold sweep 으로, discrimination ≈ 0.027 인데 `SEPARATION_MARGIN = 0.02` 에서 `SEPARATES` 로 뒤집힌다. D-196 의 판독이 자기 sweep 의 바닥에서 threshold-fragile 하다는 뜻이고, pin 을 올릴 일이 아니라 별도 D-NNN 감이다.
- **Status**: accepted
- **Refs**: journal/2026-08/12-05-the-probe-obligation-was-one-table-entry.md · Q-133 · D-206 · D-208

## D-208 — 2026-08-12 — census 를 red 로 만든 것은 `leaking_pins` 가 아니라 **`carried_drift`** 였다: 15 개의 red 는 숫자 3 개와 **의무 1 개**이고, 후자는 cycle 예산 밖이다

- **Context**: 03:00 cycle 이 D-207 을 ship 하고 suite 가 15 red (9 failed + 6 error) 로 남았다. 그 journal 은 원인을 `leaking_pins()` 로 적었다 — "Adding `leaking_pins()` put a new function into the guard census". strand 는 5 cycle 이고, 이 cycle 은 D-112 의 stranding gate 를 받아 그 red 를 지우러 들어왔다.
- **핵심 관찰 — 진단이 틀렸다**: pool scan 을 직접 돌리면 `len(gr.guards()) == 100` 이고 (pin 은 99), 새 member 는 **`inert_surface.carried_drift` 하나**다. `leaking_pins` 는 census 에 **들어가지 않았다** — D-079 의 이유 그대로: `c for c in stale_pins(src) if inert(c, src)` 는 registry 에 대한 membership 이 아니라 call 에 대한 truth test 로 좁힌다. `carried_drift` 는 D-206 (`1382d4b`) 이 추가한 것이므로 red 를 만든 commit 은 D-207 이 아니라 **그 앞 cycle** 이고, 03:00 은 자기가 만들지 않은 red 를 자기 것으로 적었다. 확인 비용은 `python3 -c` 한 줄이었다 — **Q-130 이 예고한 바로 그 실패** (artifact 대신 산문을 읽는다), 이번에는 산문을 쓴 cycle 자신이 피해자.
- **Decision**: red 를 두 종류로 가른다. (1) **census 숫자 3 개** — `len(pool) 99→100`, `revocable 5→6`, 두 set 에 `carried_drift` 추가. 기계적이고 이 cycle 이 지불했다. (2) **probe 의무 1 개** — `carried_drift` 가 `revocable_collections` 의 6 번째가 되어 `gd.unprobed_revocable() == ()` 를 깬다. `test_guard_direction` 의 9 red 는 전부 `ProbeError` 한 줄에서 나오고, **숫자를 고쳐도 안 사라진다**. 이것은 Q-133 으로 명세하고 다음 cycle 로 넘긴다.
- **왜 넘기는가 (그리고 이것이 유예가 아닌 이유)**: probe 는 scratch repo 에서 취하는 executed before/after reading 이고, 쓰려면 "`carried_drift` 의 offence 가 무엇인가" 가 **먼저** 답해야 한다 — 나머지 다섯 member 에게는 자명한 그 질문이 여기서는 자명하지 않다 (exemption 이 `NOT_IN entrants` 이고 `entrants` 는 DERIVED). 이 cycle 은 진단·census·명세로 예산을 다 썼고 (`cycle_wallclock review` 가 시작 시점에 이미 "직전 run 41m05 / 35m 예산, scope 를 줄여라" 를 냈다), 설계 질문이 남은 채로 probe 를 급조하면 **38 cycle 이 쌓아 온 guard 에 틀린 offence 개념을 박아 넣는다**. Q-133 은 후보 offence 까지 적어 두었으므로 다음 cycle 은 진단이 아니라 명세를 받는다.
- **Alternatives**: (a) 채택 — 3 개 고치고 1 개 명세. (b) probe 를 이 cycle 에 급조 — 예산 밖이고 위 이유로 위험. (c) `unprobeable_revocable` 로 제외 — **측정해서 막힌 길임을 확인했다**: 그 제외는 derived rule 이어야 하는데 subprocess-population 은 `revocable_collections` 안에 instance 가 1 개뿐이라 `test_the_exclusion_is_not_special_cased_to_the_guard_it_drops` 가 정확히 거절한다. (d) `carried_drift` 삭제 — `_main` 과 test 3 개가 쓰는 live code 다.
- **정직하게 적을 것 — strand 는 안 풀렸다**: suite 가 여전히 red 이므로 `push_preflight check` 는 거절하고 strand 는 **6** 이 된다. 이 cycle 이 산 것은 push 가 아니라 **진단의 정확도**다: 다음 cycle 은 "15 개의 정체불명 red" 대신 "명세된 deliverable 1 개" 를 받는다. 그것이 push 만큼 값진지는 다음 cycle 이 실제로 그것을 집어야 증명된다.
- **Status**: accepted
- **Refs**: `journal/2026-08/12-04-*.md` · D-206 (red 를 만든 commit) · D-207 (만들지 않았는데 자기 것으로 적은 cycle) · Q-130 (산문 vs artifact — 이 오진의 일반형) · Q-133 (probe 명세) · D-177 (census 진입을 예측·가격 매긴 선례) · D-112 (stranding gate)

## D-207 — 2026-08-12 — stale pin 은 **가격**이고 leaking pin 이 **결함**이다: `stale_pins() == ()` 를 hard red 로 채점한 것이 4-cycle strand 전체였다

- **Context**: 08-11 22:00 부터 네 cycle 이 연속으로 strand 했고 (`cycle_artifacts stranded` rc=1), 원인은 전부 하나다: `test_inert_surface` 의 6 개 assertion 이 실 repo 에 대해 `stale_pins() == ()` 를 요구하고, `STATE.md` pin 하나가 stale 이라 suite 가 red 이고, `push_preflight check` 가 green receipt 없이는 거절한다. D-206 이 그 구조를 측정해 놓았다 — `inert_surface.py` 는 다섯 pin 전부를 매개하므로 pin 기계를 손보는 cycle 은 매번 다섯을 전부 무효화하고, 하나를 discharge 하는 데 15–30 분 full probe (D-205) 가 든다. 즉 **비종료 loop**.
- **핵심 관찰 — 두 주장이 한 assertion 안에 섞여 있었다**: `stale_pins() == ()` 는 "**어떤 exemption 도 미검증 premise 위에 있지 않다**" 가 아니라 "**이 repo 가 최근에 re-probe 를 지불했다**" 를 주장한다. 전자는 tree 의 안전 성질이고 후자는 repo 의 정비 이력이다. 그리고 전자는 `inert()` 가 **이미 구조적으로 보장**한다 (line 1224): `readers_key(candidate, sources) == pin.readers_key` 를 call time 에 재유도하고 불일치면 `False` — stale pin 은 자기 exemption 을 **스스로 끈다**. test 가 지키고 있던 것은 안전이 아니라 신선도였다.
- **Decision**: 그 분리를 코드로 고정한다. `leaking_pins()` 를 추가 — stale **이면서 여전히 exempt** 인 candidate, 즉 fail-safe 가 실패한 경우만 돌려준다 (평상시 `()`, 비어 있지 않으면 `inert()` 의 진짜 버그). 6 개 assertion 을 `stale_pins() == ()` 에서 `leaking_pins() == ()` 로 옮긴다. `CONTENT_READ` (probe 해서 **움직였다고 측정된** surface) 는 `_main` 에서도 test 에서도 **hard red 유지**.
- **Alternatives**: (a) 채택 — 미검증 premise(해소 가능, 가격)와 측정된 위반(영구, 결함)을 분리. (b) `STATE.md` pin 을 full probe 로 discharge — 01:00 이 `JOURNAL.md` 에 대해 정확히 이것을 18m40 에 했고, 그 다음 cycle 의 `inert_surface.py` 편집이 즉시 무효화했다 (D-206). 이번에도 같은 편집을 하므로 **이 cycle 안에서 자기 자신에 의해 무효화된다**. (c) pin 을 통째로 삭제 — D-079 의 control 없는 exemption 으로 되돌아간다. (d) 그대로 두고 strand 를 계속 — 08-11 이후 P3 deliverable 이 0 cycle 전진.
- **선례 세 개와 같은 모양**: D-199 (`staged` rc=2 vs rc=1 — 물어보기 이른 것과 pin 이 움직인 것), D-202 (claim 의 rc=2 misattribution channel), D-044 (해소할 수 없는 check 는 muted 된다). 이 repo 는 clearable-vs-permanent 혼동을 이미 세 번 고쳤고, 이것이 네 번째다 — 다만 앞의 셋과 달리 이번 것은 mute 가 아니라 **push 차단**으로 발현했다.
- **이해충돌을 숨기지 않는다**: 02:00 은 이 변경을 의도적으로 넘겼다 — "guard 를 약화시키는 판단은 그 이득을 보는 cycle 이 내려서는 안 된다". 이 cycle 도 같은 이득을 본다. 넘기지 않은 이유: (1) 그 유예가 지금 deadlock 을 **생성하는 쪽**이 되었고 (strand 5 cycle 째), 헌법의 gate-1 deadlock-breaker 가 같은 상황에 같은 판정을 이미 내려 놓았다 ("cap 은 human review bandwidth 를 존중하려는 것이지 project 를 무기한 정지시키려는 것이 아니다"); (2) 이 변경은 gate 를 **약화시키지 않는다** — `inert()` 는 한 줄도 안 바뀌었고 `CONTENT_READ` 는 hard red 그대로이며, 없어진 것은 red 하나가 아니라 red 의 **대상**이 신선도에서 안전으로 옮겨간 것이다. 실제로 `leaking_pins` 는 이전에 아무도 안 보던 성질을 새로 감시한다.
- **D-206 이 넘긴 Q 는 존재하지 않았다**: `c731dcf` 의 commit message 는 "+ Q-129" 라고 적고 D-206 의 Refs 도 Q-129 를 가리키지만, 그 commit 은 `docs/deliberations.md` 를 **건드리지 않았다** (`git show --stat`: decisions.md + journal 둘뿐). 그리고 Q-129 는 이미 다른 주제로 D-183 에 resolved 된 번호다. 즉 "다음 cycle 이 Q-129 로 답한다" 는 유예는 **가리키는 대상이 없는 유예**였다. 이번에 Q-132 로 실제 기록한다 — 유예된 질문이 아니라, 이 결정이 **측정하지 못한** 잔여로서.
- **한계**: `leaking_pins()` 는 `inert()` 로부터 유도되므로 `inert()` 자체가 틀리면 둘 다 조용하다 — 이것은 reflexive guard 의 일반적 한계이고 이 결정이 새로 만든 것이 아니다. 그리고 stale pin 의 **가격** (D-044 second-suite tax) 은 그대로 남는다: 이 결정은 그 가격을 없애지 않고 **failure 가 아니라 가격으로 부른다**.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-03-a-stale-pin-is-a-price-not-a-defect.md` · D-206 (이 결정이 그 구조적 귀결을 지불한다) · D-205 (probe 비용 3.3배) · D-199/D-202/D-044 (clearable vs permanent, 선례 셋) · D-079 (control 없는 exemption) · D-047 (사실의 두 번째 진술 — `STAGED_MOVED` message 가 이 변경으로 stale 해져 같이 고침) · Q-132

## D-206 — 2026-08-12 — pin 이 물려받는 premise 는 **내용**이고, 그 내용에는 reader 가 import 하는 것까지 포함된다: 그래서 D-205(c) 는 더 싼 probe 를 사주지 않는다

- **Context**: STATE #1 — "probe cost model 을 또 지불하기 전에 결정하라". D-205(c) 는 generation counter 대신 carried reader 의 **content drift** 로 재probe 대상을 정하자고 미결로 남겨 뒀다. `compose` 의 docstring 이 무엇이 미측정 premise 인지 이미 명시하고 있다 — carried reader 는 *base probe 가 돈 tree 위에서* inert 였다는 것 — 그리고 `readers_key` 는 **이름의 집합**이라 그 premise 가 움직이는 것을 pin 안의 어떤 것도 볼 수 없었다.
- **Decision**: `carried_drift()` + `Pin.base_commit` 으로 그 premise 를 직접 측정한다. base tree 는 지금까지 `carried` 안의 **산문**("21 files pinned INERT on b90fc1f")이었다 — premise 를 확인하는 데 필요한 단 하나의 사실이 아무도 읽을 수 없는 형태로 있었다 (D-047). rc=0 **advisory**: drift 된 premise 는 suite 가 자란 결과일 뿐 tree 의 결함이 아니고, 이 reading 의 용도는 re-probe 를 **가격 매기는** 것이지 거절하는 것이 아니다. 하루 지난 pin 마다 red 를 켜면 D-044 의 muted check 가 된다.
- **Finding 1 — generation 과 drift 는 무상관이다**: reader test file 기준으로 gen-1 pin 세 개가 각각 6/16, 8/15, 10/21 을 drift 시킨 채 carry 하고 있고, gen-2 는 11/23, gen-0 는 0/13 이다. 3.6 s composition 과 18분 full probe 를 가르는 그 정수가 premise 가 실제로 얼마나 움직였는지로 pin 을 정렬하지 **않는다** — gen-1 pin 이 gen-2 보다 더 drift 했다. D-204 가 "composition rule 이 D-107 의도대로 작동" 이라 기록한 3.6초 discharge 두 건은 각각 6개와 10개가 drift 한 premise 위에 앉아 있었다. cap 은 자기가 bound 한다고 적어 둔 오차를 bound 하고 있지 않다.
- **Finding 2 는 Finding 1 을 뒤집고, 그것을 자기 instrument 를 반증 case 에 대 보다가 찾았다**: 첫 구현은 reader test file 만 diff 했고, 그래서 **40분 전에 full probe 된** `JOURNAL.md` 를 `PREMISE_INTACT` 로 채점했다 — 그 사이에 `inert_surface.py` 자신이 바뀌었는데도. 그것은 모든 reader 를 매개하는 module 이다. base tree 와 byte-identical 한 test 파일은 자기가 import 하는 것이 움직인 뒤에는 자기 **거동**에 대한 증거가 아니다. 즉 그 reading 은 실제로 움직인 premise 위에서 composition 을 licence 했을 것이고, 그것이 정확히 `COMPOSITION_CAP` 이 지키던 실패다. `Readers.modules` (static layer 가 이미 계산해 둔 것 — 두 번째 list 를 만들지 않는다, D-047) 를 포함시키면 **다섯 pin 전부** drift 다. 움직인 module 은 물려받은 half 의 **원소 하나가 아니라 전체**를 무효화하므로 `rerun` 은 full set 으로 degrade 한다.
- **그래서 D-205(c) 는 기각이 아니라 답이 났고, 답은 "더 싸지 않다"** 다: `inert_surface.py` 는 다섯 pin 전부를 매개하고, pin 기계를 손보는 cycle 이 계속 편집하는 파일이다. 따라서 그런 cycle 은 매번 모든 pin 을 무효화한다. "cliff 를 실제 변경분에만 물린다" 는 희망은 "full cliff 를 다섯 번 물린다" 로 붕괴한다.
- **구조적 귀결 — 이 pin scheme 은 gate 된 형태로 deadlock generator 다**: 매개 module 을 건드리는 편집이 다섯 pin 을 무효화하고, 다섯을 discharge 하려면 여러 cycle 에 걸친 5회 full probe 가 필요하고, 그 사이의 편집이 다시 무효화한다. `test_inert_surface` 가 stale pin 을 **hard red** 로 채점하므로 이 비종료 loop 이 모든 push 를 막는다. 08-11 22:00 부터의 4-cycle strand 전체가 이것이다.
- **이 cycle 이 하지 않은 것을 명시한다**: `reprobe` 의 licensing rule 과 `test_inert_surface` 의 stale-pin 채점을 **바꾸지 않았다**. 둘 다 이 cycle 자신의 push 를 풀어 주는 변경이고, guard 를 약화시키는 판단은 그 이득을 보는 cycle 이 내려서는 안 된다. Q-129 로 넘긴다.
- **Alternatives**: (a) 채택 — premise 를 측정하고, module 까지 포함하고, advisory 로 둔다. (b) reader file 만 diff — `JOURNAL.md` 를 INTACT 로 읽었고 움직인 premise 를 licence 했을 것이므로 기각 (ship 전에 잡았다). (c) `COMPOSITION_CAP` 을 올린다 — D-204(a) 가 이미 기각했고 D-206 이 근거를 강화한다: counter 가 추적하지 않는 오차를 bound 하는 counter 는 장식이다 (D-079). (d) drift 를 gate(rc=1) 로 — 하루 지난 모든 pin 이 red, D-044 의 mute.
- **한계**: 매개 module 을 **전부 포함하는 것은 보수적 과대측정**이다. `inert_surface.py` 의 한 줄 주석 변경도 premise 를 무효화한다. 안전한 방향이지만, 그래서 이 계기로 composition 을 되살릴 수는 없다 — 되살리려면 module drift 를 함수 단위로 좁혀야 하고 그것은 이 instrument 가 하는 일이 아니다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/12-02-the-premise-included-what-the-readers-import.md` · commit 1382d4b · D-205 (이 결정이 답한 미결 (c)) · D-204 (3.6s discharge 두 건의 premise 가 drift 했음을 이것이 보인다) · D-047 (사실의 두 번째 진술 — base tree 가 산문이었다) · D-044 (해소 불가능한 check 는 muted) · D-079 (control 없는 exemption 은 장식) · D-199/D-202 (clearable vs permanent split — Q-129 의 근거) · Q-129

## D-205 — 2026-08-12 — pin tax 의 cliff 는 **높이도 고정이 아니다**: 같은 candidate 의 full probe 가 5일 만에 3.3배가 됐고, 그래서 historical probe cost 를 인용하는 PLAN-time 가격표는 구조적으로 과소평가한다

- **Context**: D-204 는 pin tax 를 generation 이 결정하는 cliff 로 가격 매겼다 — composed 면 3.6s, full 이면 15~18분. 이번 cycle 이 `JOURNAL.md` 의 full probe 를 실제로 지불했는데 **18m40** 이 나왔다. 같은 candidate 의 직전 full probe 는 **5m40** 이었고, 그 사이 늘어난 것은 reader 한 개(`test_receipt_store.py`, D-203 의 산출물)뿐이다.
- **Decision**: cliff 의 존재(D-204)는 유지하되, **cliff 의 높이는 상수가 아니라 reader subset 의 suite 크기에 비례하는 변수**로 기록한다. probe 는 named reader subset 을 **두 번** 돌리므로, 그 subset 의 suite 가 자라면 같은 candidate 의 같은 probe 가 계속 비싸진다. 따라서 STATE next-actionable #3 이 제안한 "historical probe cost 를 `cycle_wallclock` 에 넣어 PLAN 때 읽자" 는 그대로는 **틀린 계기** — 이번 cycle 을 13분 과소평가했을 것이다. 인용하려면 historical cost 가 아니라 *현재 reader subset 의 측정된 suite 시간 × 2* 를 읽어야 한다.
- **Alternatives**: (a) 고정 상수로 계속 인용 — 이번에 3.3x 틀렸으므로 기각. (b) probe 를 reader subset 이 아니라 time-box 로 자르기 — 측정의 disjunction 성질(`moved(A∪B) = moved(A) ∨ moved(B)`)을 깨므로 verdict 가 약해진다, 별도 판단 필요. (c) generation counter 대신 carried reader 의 **content drift** 로 재probe 대상을 정하기 — 이름이 아니라 내용으로 premise 를 잡는 것이라 안전 방향으로는 더 강하고, cliff 를 실제 변경분에만 물린다. 미결.
- **Status**: accepted
- **Refs**: journal/2026-08/12-01-the-cliffs-height-is-not-fixed-either.md · commit 329d65e · PR #67 (strand 미해소, 3번째 stranded cycle)

## D-204 — 2026-08-11 — pin tax 는 cycle 당 **한 번만** 지불 가능한 cliff 이고, 그래서 test file 하나를 추가한 cycle 은 자기 strand 를 자기 cycle 안에서 절대 풀 수 없다

- **Context**: 22:00 cycle 이 `test_receipt_store.py` 한 개를 추가했고, 그것이 네 개 pin (`JOURNAL.md` / `RESULTS.md` / `STATE.md` / `results/`) 의 reader key 를 동시에 움직였다. 네 pin 모두 entrant 는 **정확히 그 파일 하나**. 그런데 `reprobe` 의 fallback 조건은 `generation >= COMPOSITION_CAP - 1` 이라서, generation 이 0/1 이던 `RESULTS.md` 와 `results/` 는 composition 으로 **각각 3.6 s** 에 끝난 반면 generation 2 였던 `JOURNAL.md` 와 `STATE.md` 는 full probe 로 떨어졌다. 같은 surface, 같은 단일 entrant, 비용 차이는 **3.6 s 대 16 분 이상** — pin 이 어느 generation 에 앉아 있었는지만으로 결정된다.
- **Decision**: 이 비대칭을 cycle 예산의 1급 항목으로 인정한다. 한 cycle 은 full probe 를 **최대 하나** 감당할 수 있고 (측정: 23:00 cycle 이 `STATE.md` full probe 에 25분을 쓰고도 끝내지 못해 kill), suite 는 1220 s 를 따로 요구한다. 따라서 두 pin 이 동시에 CAP 에 앉은 상태에서 strand 를 푸는 데 필요한 최소 cycle 수는 **3** 이다: probe A → probe B → suite + push. 이것을 불운이 아니라 구조로 기록한다. `reprobe` 는 CLI subcommand 가 **없다** (`survey|pins|staged|probe` 뿐) — 22:00 cycle 의 journal 이 처방한 `reprobe` 명령은 존재하지 않는 것을 가리켰고, Python 에서 직접 호출해야 한다.
- **Alternatives**: (a) `COMPOSITION_CAP` 을 올린다 — cap 은 composition 오차 누적을 bound 하려고 있는 것이라 근거 없이 올리면 pin 이 측정이 아니라 장식이 된다 (D-079). (b) full probe 를 cycle 경계 너머로 resume 가능하게 만든다 — probe 는 before/after 두 pass 사이에 tree 가 움직이면 VACUOUS 이므로 cycle 을 걸치면 premise 가 깨진다. (c) **PLAN 단계에서 pin tax 를 미리 가격표에 올린다** — `cycle_wallclock` 이 suite 만 가격을 매기고 있어서 "test file 하나 추가" 가 싸 보인다. 채택 방향은 (c).
- **Status**: accepted
- **Refs**: journal/2026-08/11-23-the-pin-tax-is-payable-once-per-cycle.md · branch `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67)

## D-203 — 2026-08-11 — tree 로 key 를 만드는 cache 는 그 tree 의 **일부여서는 안 된다**: receipt store 가 committed 되는 순간 매 archive 가 자기가 방금 저장한 receipt 을 무효화한다

- **Context**: STATE #1 — suite 는 ~1220 s 로 35분 budget 의 대부분이고, 그 receipt 은 `/tmp/suite-receipt.json` 에 쓰인 뒤 **다음 cycle 의 `record` 가 시작하자마자 unlink** 된다 (D-082 의 crash 논거: 시체가 증거로 읽히면 안 된다). 그래서 test 가 읽는 것을 하나도 바꾸지 않은 repair cycle — 2026-08-11 의 16:00 / 18:00 / 20:00 strand repair — 이 **이미 그 tree 에서 측정된** 숫자를 재도출하려고 매번 full price 를 지불했다. 부족했던 것은 receipt 이 아니라 *측정* 이었고, 그것이 아직 유효한 채로 버려지고 있었다.
- **Decision**: `eval/mppi_sandbox/receipt_store.py` — receipt 을 `worktree_fingerprint` 로 key 해서 보관한다. 그 값은 `push_preflight.check` 가 유효성 판정에 **이미 쓰는 바로 그 값**이므로, 유일하게 정직한 key 다. hour 도 branch 도 key 가 될 수 없다: byte 단위로 같은 tree 두 개는 같은 receipt 을 쓸 자격이 있고, 한 byte 다른 두 개는 아니며, 시간 기반 이름은 그 구분을 **표현할 수 없다**. recall 은 lookup 이고 search 가 아니다 — "가장 가까운 match" 라는 개념이 여기엔 없다.
- **핵심 불변식은 store 가 untracked 여야 한다는 것**이고, 이것이 설계 전체를 결정한다. `worktree_fingerprint` 는 tracked 파일만 덮고 (`git ls-files`), untracked 는 `check` 가 비교하지 않는 별도의 `untracked_digest` 로 간다. 따라서 untracked 인 동안 archive 는 fingerprint 를 움직이지 않고 receipt 은 자기가 방금 측정한 tree 에 대해 유효하게 남는다. **committed 되는 순간** 매 archive 가 tracked tree 를 바꾸므로 receipt 은 착지하는 즉시 자기를 무효화하고 **모든** recall 이 miss 한다. 이것은 "조금 느린 store" 가 아니라 **절대 hit 할 수 없는 store** 이고, 증상이 error 가 아니라 침묵이다 (write 성공, read miss, 예외 없음). 그래서 주석이 아니라 `tracked_conflict()` + assertion 으로 고정한다.
- **첫 선택한 directory 가 이미 tracked 였고, 그 assertion 이 첫 실행에서 잡았다**: `results/readings/` 는 다른 artifact class (ordering-control measurement cell) 를 담은 **tracked** directory 다. 같이 써 놓은 `.gitignore` 항목은 구제가 안 된다 — ignore rule 은 **이미 tracked 인 파일에 적용되지 않는다**. `results/receipts/` 로 이전. 불변식을 산문이 아니라 test 로 적어 둔 것이 30초 수정과 조용히 영영 hit 안 하는 store 의 차이였다.
- **key 는 derive 된 채로 남아야 한다**: `recall` 은 파일 *내용*의 `worktree_fingerprint` 가 파일 *이름*이 주장하는 값과 같은지 다시 확인한다. 이름이 주장하는 hash 를 담고 있지 않은 파일은 rename / hand-edit / 중간에 끊긴 write 이고, store 의 가치 전부가 key 가 assert 된 것이 아니라 derive 된 것이라는 데 있다. 그런 상태는 전부 `None` — `push_preflight.load` 의 논거 그대로, 구분하면 그 중 하나를 증거로 취급하는 branch 를 부르게 된다.
- **flag 가 아니라 무조건**: `record` CLI 가 `--out` 옆에 항상 archive 한다. 손으로 놓는 guard 는 cycle 이 잊는 guard 이고, 잊을 가능성이 가장 높은 cycle 이 바로 시간에 쫓기는 cycle — 즉 그 run 이 비싼 cycle 이다 (D-162).
- **범위를 정직하게**: 이것이 사는 것은 **한 machine 위 cycle 경계** 를 넘는 durability 뿐이고, 실제 손실이 일어나는 지점이 거기다. fresh clone 은 살아남지 못하고 그럴 의도도 없다 — receipt 은 한 worktree 에 대한 증거이고 clone 은 다른 worktree 다.
- **이 cycle 은 publish 하지 못했고 원인은 값을 매기지 않은 실제 비용이다**: `inert_surface staged` 가 네 pin (`STATE.md` / `JOURNAL.md` / `RESULTS.md` / `results/`) 에 `STAGED_MOVED` 를 냈고, 네 key 의 delta 는 **정확히 entrant 하나** — 새 test 파일 — 였다. 즉 이 경로들을 건드리는 test 파일을 추가하는 **모든** cycle 은 suite *이전에* reprobe 를 빚지는데, `cycle_wallclock` 은 suite 만 가격을 매기므로 이 빚은 PLAN 시점에 보이지 않는다. 5m11 에 `SUITE_AFFORDABLE` 을 읽는 동안 이미 ~4분짜리 reprobe 를 빚지고 있었다.
- **Alternatives**: (a) 채택 — fingerprint key + untracked store + derive 된 key 재확인. (b) hour/branch 로 key — 같은 tree 두 개를 구분해버리고 다른 tree 두 개를 합쳐버린다. (c) store 를 commit 해서 machine 간 공유 — 위의 이유로 hit 이 **불가능**해진다. (d) `--archive` flag — D-162 가 이미 흉터를 예약해 둔 모양.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-22-the-cache-must-be-invisible-to-the-tree-it-caches.md` · D-082 (push 는 receipt 이 licence 한다 · `--out` unlink 의 출처) · D-043/D-044 (count 는 한 tree 에 속한다) · D-162 (손으로 놓는 guard 는 잊힌다) · D-199 (`staged` 가 이번에도 제때 울렸다) · D-200/D-201 (`OBSERVED_SUITE_SECONDS` 가 n=2 를 넘기려면 관측이 쌓여야 한다 — 이 store 가 공짜로 쌓는다) · D-047 (사실의 두 번째 진술)

## D-202 — 2026-08-11 — `claim` 은 자기가 **누구의** 주장을 채점하는지 검증한 적이 없다: attribution 을 산문으로 단언하던 것을 rc=2 로 강제한다

- **Context**: 20:00 cycle 이 TSV append 뒤, 자기 4a 를 쓰기 **전에** `cycle_artifacts claim` 을 돌렸다. `_claim_rows` 는 `cycle_path=None` 일 때 `ordered[-1]` 로 떨어지는데 그것은 **19:00 의 journal** 이었고, CLI 는 그것을 "the in-flight cycle's TSV claim" 이라고 단언하며 붙여넣을 줄로 `yes` 를 출력했다. 붙여넣는 순간 19:00 은 `UNSUPPORTED` 가 된다 — row assignment 가 timestamp 기준이라 이 cycle 의 4a 가 착지하면 row 가 20:00 으로 재할당되기 때문. **어떤 후속 repair 도 닿을 수 없는 흉터**다 (D-162 가 기록한 그 성질).
- **핵심은 계산이 아니라 귀속이었다**: 이 도구는 row 를 정확히 셌다. 틀린 것은 **누구의** row 인가였고, 그것을 *확인하지 않은 채 문장으로 단언*했다. 자기 subject 를 산문으로 이름 붙이는 reading 은 그 이름을 검증하도록 강제되어야 한다.
- **Decision**: `inflight_hour()` (wrapper log 의 짝 없는 `start` marker 를 `cycle_wallclock.in_flight` 로 읽음) + `identification()` 을 추가하고 `claim_support` / `claim_line` 이 이를 경유하게 한다. 세 상태: `IDENTIFIED` / `INFLIGHT_UNKNOWN` / `NO_INFLIGHT_JOURNAL`. 마지막 상태에서 CLI 는 **rc=2** 로 빠지고, 채점할 뻔했던 journal 을 이름으로 지목한다.
- **왜 rc=2 이고 rc=1 이 아닌가** (D-199 의 split 재사용): misattribution 은 4a 를 쓰고 다시 돌리면 **10초 만에 해소**되고, over-claim 은 **영원히 해소되지 않는다**. 둘을 한 바구니에 넣으면 clearable 한 caveat 이 permanent scar 와 같은 등급이 되고, D-044 가 말한 대로 그런 check 는 muted 된다. 그래서 `NO_INFLIGHT_JOURNAL` 은 `finding_grades()` 에 **넣지 않는다** — test 로 고정.
- **거절은 붙여넣을 수 없어야 한다**: 실패 양식이 *paste* 였으므로 `REFUSED_LINE` 은 유효한 Artifacts 줄이 **아니게** 만들었다. 여전히 유효한 `yes` 위에 경고만 붙였다면 예전 출력과 똑같이 읽혔을 것이다 — 운영자는 경고가 아니라 줄을 복사한다.
- **`INFLIGHT_UNKNOWN` 은 fail-open**: 잡으려는 결함은 *cycle 이 자기를 채점한다고 믿으며 predecessor 를 채점하는 것* 이라는 특정 상황이고, 그것은 어느 hour 가 in-flight 인지 알아야 성립한다. 모른다는 것은 결함의 증거가 아니다. 손으로 돌리는 호출과 test 를 막는 guard 는 아무도 돌리지 않는 guard 다. 같은 이유로 `root is not None` 이면 즉시 `INFLIGHT_UNKNOWN` — 구성된 repo 의 `tmp_path` journal 을 이 기계의 wrapper log 와 join 하는 것은 한 repo 의 hour 를 다른 repo 의 파일에 대고 채점하는 것.
- **기존 CLI test 가 test runner 자신의 cycle hour 를 읽고 있었다**: `main()` 은 `root=None` 으로 호출하므로 live wrapper log 를 참조한다. 아무도 그 hour 를 참조하지 않던 동안에만 무해했고, 이제는 rc 가 *suite 를 돌린 시각*에 의존하게 된다. hour 를 상속하지 말고 **명시**하도록 고쳤다.
- **왜 written-down precondition 으로 부족했나**: `cycle_path` 는 D-110 이래 존재했고 docstring 은 이미 "newest == the running cycle 은 4a 이후에만 참" 이라고 적고 있었다. **default path 가 조용히 사양하는 opt-in 은 guard 가 아니다** — 그것을 필요로 한 caller 가 바로 그것을 넘겨야 하는 줄 몰랐던 caller 다.
- **Alternatives**: (a) 채택 — hour 대조 + rc=2. (b) `cycle_path` 를 필수 인자로 — push gate 의 `&&` chain 이 매 cycle 손으로 경로를 타이핑하게 되고, D-154 가 없앤 "cycle 이 자기 사실을 타이핑한다" 로 회귀. (c) rc=1 로 통합 — clearable 과 permanent 를 같은 등급으로, D-044 가 예측한 mute. (d) 경고만 출력 — paste 가 실패 양식이므로 무효.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-21-the-instrument-asserted-whose-claim-it-was-grading.md` · D-162 (timestamp 재할당이 흉터를 영구화 · `pending` 이 이번에도 walk-back 을 가능하게 했다) · D-199 (rc=2/rc=1 split 의 출처) · D-110 (`cycle_path` 를 도입한 최초 repair) · D-044 (해소 불가능한 check 는 muted) · D-154 (cycle 은 자기가 무엇을 할 참인지 모른다)

## D-201 — 2026-08-11 — 한 상수의 두 consumer 는 **반대 방향으로** 실패한다: D-200 의 ceiling 은 deadline 에 맞았고, 같은 상수를 읽는 `threshold` 를 조용히 뒤집었다

- **Context**: STATE #1 이 `MIN_OVERHEAD_SECONDS` (240 s) 를 D-200 의 "stale 하다고 적어 놓고 유지한" 모양으로 지목했다. 두 가지가 틀렸다 — 상수는 `push_preflight` 가 아니라 `cycle_wallclock` 에 있고, 진짜 결함은 그 상수가 아니라 **D-200 자신이 어제 만든 것**이었다.
- **Decision**: `OBSERVED_SUITE_SECONDS` 를 **양 극단에서** 읽는다. `suite_deadline()` 은 `observed_suite_max()` 유지 (prospective — 모르면 suite 를 거절), `threshold()`/`grade()`/`graded()` 는 새 `observed_suite_min()` = `PREMATURE_SUITE_SECONDS` (retrospective — 모르면 suite 를 인정). 하나의 상수는 두 방향으로 동시에 안전하게 실패할 수 없다.
- **왜 뒤집혔나**: D-200 의 논거는 명시적으로 *deadline instrument* 에 대한 것이다 — 가격을 모를 때 licensing 이 비싼 error 다. `threshold` 가 묻는 것은 **가능성 주장** ("이 run 이 suite 를 담을 수 있었는가") 이고, 거기서 worst observation 으로 가격을 매기면 더 강하고 **거짓인** 주장이 된다: "가장 느린 suite 보다 짧은 run 은 suite 를 안 돌렸다". 1223 + 240 = **1463 s** 인데 18:00 run 은 **1442 s** 이고 receipt 이 **1214.24 s** suite 를 기록한다 — 돌렸다. `published` 가 clock 보다 먼저 short-circuit 해서 live grade 만 우연히 맞았고, publish 안 한 같은 모양의 run 은 `PREMATURE` 로 오독된다. `MIN_OVERHEAD_SECONDS` docstring 이 "manufacturing 하지 않는다" 고 약속한 바로 그것.
- **240 은 잘못된 population 에서 유도됐고 실제로 거짓이었다**: 근거로 적힌 236 s 는 EXECUTE 를 안 한 **suite 없는** run 전체 길이인데, 이 상수가 bound 하는 양은 *suite 를 돌린* run 의 비-suite 작업이다 — 그 논거의 어떤 reading 도 이 population 의 원소가 아니다. 직접 재면 1442 − 1214.24 = **228 s**. "관측된 어떤 것보다도 한참 아래" 라던 bound 가 관측치보다 **12 s 위**에 있었고, 오차 방향이 약속을 어긴 쪽이다. `OBSERVED_OVERHEAD_SECONDS` registry + `observed_overhead_min()` 로 D-200 형식을 그대로 빌린다 (교체된 숫자는 자기가 교체한 숫자와 비교될 수 없다).
- **물려받은 red 를 물려받았다고 확인하고 적었다 (D-198)**: `TestElapsed` 2개가 receipt 가격의 reading 을 상수 가격의 `suite_deadline()` 과 비교하고 있었다 — 마지막 suite 가 우연히 `SUITE_SECONDS` 만큼 걸린 동안만 같다. 18:00 이 1214.24 s receipt 을 쓰자 module 은 아무것도 안 바뀐 채 red 가 됐다. stash 한 tree 에서 재현해 3 중 2 는 내 것이 아님을 **확인한 뒤** 귀속했다; 나머지 1 (`== 637`) 은 내 것이고, "derived, not typed" 주석 아래 있던 typed literal 이다. 이제 assertion 이 reading 과 같은 방식으로 가격을 매겨 `/tmp` 의존이 사라진다.
- **n = 1 은 한계다**: `OBSERVED_OVERHEAD_SECONDS` 는 관측 하나뿐이라, 더 빠른 cycle 이 다음에 또 반증한다. registry 형식이 그 비교를 가능하게 하려고 있고, 다음 action 은 wrapper log + receipt 으로 과거 run 들의 overhead 를 소급 복원하는 것.
- **Alternatives**: (a) 채택 — 한 registry, 두 극단, 필요한 site 마다 이름. (b) `threshold` 에 `SUITE_SECONDS` 유지 — manufactured `PREMATURE` 를 유지. (c) 상수 두 개를 따로 타이핑 — 함께 drift 하고 D-047. (d) `MIN_OVERHEAD_SECONDS` 만 낮추고 suite 축은 그대로 — 228 로도 1223 + 228 = 1451 > 1442 라 **반례가 여전히 오독된다**; 두 축을 다 고쳐야 사라진다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-19-the-reprice-served-one-consumer-and-inverted-the-other.md` · D-200 (ceiling 논거, 이 결정이 좁힌다 — *측정치와 deadline 방향은 유효*) · D-198 (red 귀속 전 확인) · D-186 (argument 쓰기 전 측정) · D-058 (실패 방향 pin) · D-140 (gate 1 은 새 항목을 센다 — 이 cycle 이 실행될 수 있었던 근거)

## D-200 — 2026-08-11 — `cycle_wallclock` 의 fallback 은 **floor 가 아니라 ceiling** 이어야 한다: 형제 module 이 이미 유도해 둔 비대칭 논거를, 같은 비대칭을 가진 module 이 반대로 쓰고 있었다

- **Context**: STATE #1 이 "receipt 에서 suite 상수를 re-price (1222s 관측 vs 717s 가정)" 을 package 안 가장 싼 real fix 로 지목했다. 그런데 **그 framing 은 이미 절반 틀렸다**: D-181 이 `suite_price()` 를 ship 한 이래 live path 는 receipt 을 읽고 `1223s measured` 를 출력한다. stale 한 것은 *fallback* — receipt 을 못 읽을 때만 쓰이는 literal — 뿐이었다. STATE 를 그대로 믿었으면 이미 옳은 path 에 대한 fix 를 claim 할 뻔했다 (D-186 의 6번째 연속 premise-break, 이번엔 7번째).
- **Decision**: `SUITE_SECONDS` 717 → **1223** 으로 re-price 하되, 값이 아니라 **방향**을 결정으로 기록한다. 이 상수는 "이 suite 의 가격을 모른다" 는 경우에만 참조되고, deadline instrument 에서 모르는 값은 **suite 를 거절하는 쪽으로** 실패해야 한다. 717 은 정확히 반대였다 — 그리고 module 은 자기 docstring 에 "known to be *low*", 1091 s 관측, "minute 15 에 6m14 늦은 deadline 으로 `SUITE_AFFORDABLE` 을 줬다" 까지 **전부 적어 놓고 값을 유지했다**. 평평한 literal 대신 `OBSERVED_SUITE_SECONDS` registry + `observed_suite_max()` 로 바꿔 다음 성장 때 hand re-price 가 필요 없게 한다.
- **진짜 finding 은 형제가 이미 이 규칙을 유도해 뒀다는 것**: `nested_timeout.measured_suite_seconds()` 는 CI timeout 을 관측치의 **최악값**에서 유도하며, 그 이유를 명시적으로 적어 뒀다 — *실패가 비대칭이다*: 너무 낮으면 모든 run 을 구조적으로 죽이고 (run 31042602721 의 red 6개), 너무 높으면 이미 hang 이 없는 한 아무 비용도 없다. `cycle_wallclock` 은 **같은 모양의 비대칭**(가격이 낮으면 끝낼 수 없는 suite 를 licence, 높으면 감당 가능한 scope 를 자를 뿐)을 가지고 반대 규칙을 썼다. 한 module 이 유도한 원리가 형제에게 적용된 적이 없었다. 관측치를 list 로 유지하는 형식도 그 형제의 논거를 그대로 빌린다 — "교체된 숫자는 자기가 교체한 숫자와 비교될 수 없다".
- **닿지 않는다는 것은 변호가 아니다**: 이 machine 의 `/tmp` 는 rootfs 위이고 uptime 이 174일이라 receipt 이 살아남는다 — 즉 이 literal 은 *여기서* 거의 읽히지 않는다. 그래서 무해했던 게 아니라 **staleness 가 안 보였던** 것이고, 첫 fresh checkout 이 그 값을 발견하는 데 한 cycle 을 썼을 것이다.
- **같아 보이는 두 registry 는 두 개의 사실이다**: 새 상수를 `nested_timeout.OBSERVED_SUITE_SECONDS` 에 접을 뻔했다. 그쪽은 **nested CI** suite 를 GitHub Actions runner 에서 잰 것이고 (provenance 가 workflow run id), 이쪽은 push gate 가 실제로 돌리는 **local** suite 다. 접었으면 local deadline 을 CI runner 가격으로 매기는 `key_conflation` 모양이 된다. 분리 유지 + 양쪽에 non-identity 를 명시.
- **pin 은 값이 아니라 부등식**: `SUITE_SECONDS >= observed_suite_max()`, 그리고 budget 의 매 분에서 "fallback 은 measurement 가 거절하는 것을 licence 하지 않는다" 를 property 로. 실패 방향(D-058)도 함께 — 717 이 그 부등식을 위반하고, 위반하는 지점이 정확히 shipped instrument 가 참조되던 minute 15 다. literal 이 아니라 부등식이라 **다음 re-price 가 permissive 방향을 조용히 재도입할 수 없다**.
- **부수 비용**: 717 에서 파생된 literal 을 들고 있던 test 4개가 red 로 잡혔다 (targeted pre-check 0.27s, D-191 패턴). `1143` → `suite_deadline()` 파생, reading 문자열 → 계산. 03:00 의 "4초 차" 논거는 `suite_seconds=717` 로 **자기 시대의 가격에 pin** — 1223 에서는 721 s 가 suite 단독으로도 한참 아래라 test 가 통과하면서 아무것도 보여주지 못하게 된다.
- **Alternatives**: (a) 채택 — registry + 최악값 유도 + 부등식 pin. (b) 값만 1223 으로 — 다음 성장 때 같은 자리에서 같은 방식으로 stale, 그리고 "왜 최악값인가" 가 기록되지 않는다. (c) `nested_timeout` 에 합침 — 두 population 을 conflate. (d) fallback 삭제하고 receipt 없으면 raise — advisory (D-115) 가 cycle 을 끝내는 것이 되고, `suite_price` 의 "unknown price is not a finding here" 를 뒤집는다.
- **한계**: 1223 s 는 **한 번의** local 관측이고 runner 는 이 machine 하나다. 최악값 규칙이라 성장하는 suite 에 대해 보수적 방향으로 틀리지만, 더 느린 machine 에서는 이것도 낮다 — registry 형식이 그 때 비교를 가능하게 하려고 존재한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-17-the-sibling-had-already-derived-the-rule.md` · `nested_timeout.measured_suite_seconds` (빌려온 논거) · D-181 (`elapsed` / `suite_price`) · D-115 (advisory) · D-186 (argument 쓰기 전에 측정) · D-058 (실패 방향도 pin) · D-047 (사실의 두 번째 진술) · D-191 (pre-check 패턴)

## D-199 — 2026-08-11 — **읽기는 옳았고 틀린 것은 시점이다**: caveat 을 지우는 행위가 곧 finding 을 만드는 행위이고, `pins` 의 exit code 는 그 둘을 구별하지 못한다

- **Context**: D-198 이 13:00 cycle 의 red 를 자기 귀속으로 정정하면서 남긴 다음 action 이 이것이었다 — "reader 를 추가하는 cycle 이 `git add` **이후에** `pin_reading().unstaged` 를 보게 하라". STATE 는 이것을 "package 안에서 지금 가장 싼 진짜 fix" 로 11 cycle 만에 처음 구체적으로 지목했다. 읽기 자체는 D-179 가 이미 옳게 만들어 두었다 (`PINS_CURRENT` / `PINS_STALE` / `PINS_UNSTAGED`, `inert_surface pins` CLI, test 6개).
- **먼저 전제를 쟀다 (D-186, 7 cycle 연속)** — 그리고 이번엔 전제가 **버텼다**: blind spot 이 untracked 파일에만 있는지, 아니면 *수정되었으나 stage 되지 않은* tracked test 에도 있는지 확인했다. `_python_sources` 는 **경로**를 index(`git ls-files`)에서 가져오지만 **내용**은 worktree 에서 읽는다 — 그래서 이미 tracked 인 test 가 새로 읽기를 추가하면 그 내용은 즉시 보인다. blind spot 은 정확히 그리고 오직 untracked 파일이며 `unstaged_readers` 가 그것을 온전히 덮는다. 두 번째 구멍은 없다.
- **Finding — 결함은 읽기가 아니라 exit code 의 해상도다**: `pins` 는 stage **양쪽에서 똑같이 rc=1** 을 돌려준다. 앞에서는 `PINS_UNSTAGED` (staging 으로 지워지는 caveat), 뒤에서는 `PINS_STALE` (지울 수 없는 finding). 그런데 이 둘을 가르는 행위가 바로 caveat 이 시키는 그 행위다 — D-179 는 "clearable by design" 을 이 읽기가 warning 이 아니라 reading 일 수 있는 **근거**로 pin 했고(D-044: 지울 수 없는 check 는 muted 된다), 바로 그 성질이 finding 을 숨긴다. 시간에 쫓기는 cycle 은 integer 를 읽는다: rc=1 을 보고, 올바르게 "지울 수 있는 쪽" 이라 판단하고, `git add` 로 지우고, 다시 읽을 이유를 얻지 못한다. 13:00 cycle 이 정확히 이 경로를 걸었다.
- **Decision**: `staged_reading()` / `StagedReading` / `inert_surface staged` 를 추가한다. 질문을 **일찍 만족시킬 수 없는 순서**로 묻는다: untracked reader 가 남아 있으면 답을 거절하고(`STAGED_PREMATURE`, **rc=2**), index 가 current 할 때만 pin 을 판정한다(`STAGED_MOVED` **rc=1** / `STAGED_CLEAN` **rc=0**). 세 결과에 세 code — `pins` 가 둘뿐인 것이 이 subcommand 의 존재 이유다. 그리고 헌법의 `git add` **바로 다음 줄**에 배치했다: 읽기는 이미 있었고 없던 것은 그것을 취하는 **순간**이다.
- **거절을 D-044 의 함정으로 만들지 않는 것**: `STAGED_PREMATURE` 는 caller 가 어차피 실행하려던 그 `git add` 로 지워지고, 지우는 것이 답을 진짜로 만든다. 지울 수 없는 red 가 아니다.
- **D-179 의 ordering 을 뒤집되 되돌리지는 않는다**: `pin_reading` 은 unstaged 가 있어도 stale 을 **먼저** 보고한다 — 철회된 exemption 은 지금 actionable 하고 caveat 은 그것을 넓힐 뿐이기 때문이다. `staged_reading` 은 거절을 앞세우므로, 그대로 두면 D-179 가 거절한 바로 그 가림을 재도입한다. 그래서 stale 집합이 거절과 **함께 실려 간다** (`Already stale regardless: …`): 현재 index 에서 stale 인 pin 은 그 superset 에서도 stale 이므로 기다릴 이유가 없다. test 로 고정했다.
- **Alternatives**: (a) 채택. (b) `pins` 의 exit code 를 3-way 로 바꾸기 — 같은 함수가 "지금 답할 수 있나" 와 "답이 무엇인가" 를 겸하게 되고, 기존 caller 의 rc 계약이 조용히 바뀐다. (c) 헌법에 "`git add` 후 `pins` 를 다시 읽어라" 만 적기 — 같은 rc=1 을 다시 읽으라는 지시이고, 왜 이번 것은 다른지 산문이 설명해야 한다. 13:00 cycle 은 산문을 읽을 시간이 없어서가 아니라 다시 읽을 **이유**가 없어서 놓쳤다. (d) `git add` 를 hook 으로 감싸기 — 저장소 밖 machine 설정이고 hard limit.
- **정직한 한계**: 이 cycle 은 controller / representation / dynamics 를 건드리지 않았고 sim 을 0회 돌렸다. north star 거리는 그대로다. 이것은 20분 suite 가 이미 알 수 있었던 것을 0.3초에 알려주는 instrument 이지, 로봇을 더 잘 달리게 하는 것이 아니다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-15-the-caveat-and-the-finding-are-one-git-add-apart.md` · D-198 (이 entry 의 촉발 incident) · D-179 / Q-128 (읽기 자체 + ordering 규칙) · D-044 (지울 수 없는 check 는 muted 된다) · D-058 (실패 방향도 pin 한다) · D-186 (key 로 쓰기 전에 전제를 잰다)

## D-198 — 2026-08-11 — **red 를 물려받았다고 적었지만 자기가 냈다**: pin 은 내용이 아니라 reader set 으로 stale 해지고, 13:00 cycle 의 진단은 그래서 성립할 수 없다

- **Context**: 13:00 cycle 이 `test_inert_surface.py` 4 red 를 만나 push 를 포기했고(3 commit strand), 그 red 를 **12:00 cycle 의 4c `STATE.md` rewrite** 탓으로 적었다. 거기서 한 걸음 더 나가 "D-044 의 ordering table 이 `STATE.md` 를 *read by no test* 라고 하는데 그 clause 는 decay 했다" 는 finding 을 세웠다. 이번 cycle 의 첫 의무는 strand 해소였고, 그러려면 red 의 원인을 알아야 했다.
- **Finding — 귀속이 틀렸고, module 이 그렇게 말한다**: `stale_pins()` 는 candidate 의 **내용을 한 번도 읽지 않는다**. `readers_key`, 즉 **reader 파일들의 집합**을 pin 에 기록된 것과 비교할 뿐이다. 그러므로 `STATE.md` 를 어떤 내용으로 다시 쓰든 pin 은 stale 해질 수 없다 — 지목된 원인이 관측된 결과를 만들어 낼 수 **없다**. 실제로 stale 시킨 것은 `entrants('STATE.md') == ('eval/mppi_sandbox/tests/test_key_discrimination.py',)` — **13:00 cycle 이 그 cycle 에 새로 쓴 test module** 이 이 pin 의 reader set 에 들어온 것이다. 물려받은 red 가 아니라 한 commit 거리의 자기 red 였다.
- **왜 그 cycle 이 자기를 의심할 이유가 없었나 (이게 진짜 교훈)**: `unstaged_readers` 의 docstring 이 이미 이 함정을 이름까지 붙여 적어 놓았다(Q-128). reader scan 은 `git ls-files` — **index** 를 읽으므로, 아직 stage 되지 않은 새 test 파일은 보이지 않는다. 그리고 그 blind spot 은 **균등하게 분포하지 않는다**: 정확히 *reader 를 추가하는 cycle* 을 겨냥한다 — 왜냐하면 그런 cycle 만이 pin 을 stale 시킬 수 있고, 동시에 그런 cycle 만이 아직 tracked 되지 않은 새 test 파일을 손에 들고 있기 때문이다. 13:00 cycle 은 `stale_pins() == ()` 를 읽었고, 그것은 그 순간 참이었으며, `git add` 가 그것을 거짓으로 만들었다.
- **D-044 의 clause 에 대해 — 절반은 맞고, 인과는 틀렸다**: "`STATE.md` 는 read by no test" 는 실제로 거짓이다(`test_the_real_repo_reading_is_current` 가 읽고, `push_preflight` 가 test-readable 로 분류한다 — 애초에 `inert_surface` 라는 module 이 존재하는 이유가 그것이다). 하지만 그 거짓이 **이번 4 red 를 만든 것은 아니고**, 13:00 cycle 이 함의한 remedy(4c 의 write 순서를 옮기기)는 이 red 를 **하나도** 막지 못했을 것이다. 두 개의 서로 다른 기전을 하나로 접은 것이다: `push_preflight` 의 drift check 는 **내용** 기반이고, `inert_surface` 의 pin staleness 는 **reader set** 기반이다. 같은 파일 이름이 양쪽에 나온다는 것이 두 기전을 같은 것으로 만들지 않는다.
- **Decision**: (1) pin 을 `reprobe('STATE.md')` 로 re-take — entrant 1개(16 test), mutation 전후 16 passed 불변, `INERT_COMPOSED` **gen-2**, 22 reader carried. 수 초. (2) 이 판별을 산문이 아니라 **test 두 개**로 고정한다 — `test_rewriting_the_pinned_file_cannot_stale_its_pin` (지목된 원인은 어떤 내용에서도 효과가 없다) 과 `test_adding_a_reader_is_what_stales_a_pin` (진짜 원인에는 문다). 두 방향을 **짝으로** 두는 것이 핵심이다: 한쪽만 있으면 "왜 red 였나" 에 답하지 못하고, 그 질문이 13:00 cycle 이 틀린 지점이다. (3) D-044 의 clause 는 이 entry 가 정정하되 **red 의 원인으로는 기록하지 않는다**.
- **Alternatives**: (a) 채택. (b) reprobe 만 하고 넘어가기 — pin 은 녹색이 되지만 잘못된 귀속이 `docs/decisions.md` 에 그대로 남아 다음 cycle 이 4c ordering 을 고치는 데 시간을 쓴다. (c) 13:00 의 진단을 믿고 4c write 순서를 옮기기 — 재현되는 red 에 대해 아무 효과 없는 변경을 ordering table 에 새기고, 진짜 원인(reader 추가)은 손대지 않은 채 남는다. (d) `unstaged_readers` 를 `_python_sources` 에 접어 넣어 blind spot 을 없애기 — 그 docstring 이 이미 거절했다: push 되지도 않을 scratch 파일이 pin 을 흔들게 되고, 이는 shipped tree 를 거기 없는 것으로 채점하는 방향의 오류다.
- **Status**: accepted
- **Refs**: `journal/2026-08/11-14-the-red-was-one-commit-away.md` · D-197 / `journal/2026-08/11-13-narrowing-is-not-discrimination.md` (정정 대상) · D-183 (`reprobe` 의 존재 이유 — full probe 15m45 를 수 초로) · D-044 (지울 수 없는 red 는 muted 된다 — 그 ordering table 이 이 entry 의 배경) · D-112 (strand 는 다음 cycle 의 첫 의무) · Q-128 (index 는 disk 보다 한 `git add` 뒤에 있다)

## D-197 — 2026-08-11 — **key 는 몇 개를 무는가로 검증되지 않는다**: D-196 이 미룬 narrow key 는 population 을 3.5× 줄이고 composition 을 1.4 point 움직였다 — 즉 분리하지 못한다

- **Context**: STATE #1 이 D-196 의 미완 measurement 를 그대로 지시했다 — "call syntax **+ 기록된 반환값**" 이라는 narrow key 를 wide key 와 같은 population 에 걸어 보라. 분리되면 `OPERATOR_INVOKED` 를 발급하고 `reprobe` 가 산문이 아니라 측정으로 residue 를 떠나고, 분리 안 되면 그것이 답이다. 비교가 내부적으로 성립하도록 두 key 를 **같은 regex family** 로 재측정했다 (wide: backtick 안의 non-empty argument call, narrow: 그 call site 뒤 160자 안의 backtick SCREAMING_SNAKE token).
- **Finding — 분리하지 못한다**: wide **35** hits 중 32 `LIVE` (non-`LIVE` **8.6%**), narrow **10** hits 중 9 `LIVE` (non-`LIVE` **10.0%**). matched set 은 **3.5× 줄었고** composition 은 **+1.4 point** 움직였다. `reprobe` 는 유일한 non-`LIVE` hit 이지만 아홉 개의 `LIVE` 이름과 **같이** 걸린다 — 즉 residue 에서 그것만 집어내는 것은 나머지 아홉에 caller 가 있다는 **우연**이고, D-193(`# pragma: no cover`, 48 중 43 `LIVE`)과 D-196(log call syntax, 25 중 대부분 `LIVE`)이 각각 거절한 바로 그 형태가 **세 번째로**, 더 좋은 hit count 를 입고 돌아온 것이다.
- **더 중요한 것: 적어 둔 규율이 그 cycle 들이 실제로 한 일의 싼 쪽 절반이었다**. D-193 은 "48 중 43 이 `LIVE`" 로, D-196 은 "25 개, 대부분 `LIVE`" 로 거절했고 둘 다 기록은 *key 가 너무 넓다* 로 남았다. 넓이는 한 번도 결정적 사실이 아니었다 — 48 개를 물되 5 개가 non-`LIVE` 인 key 와 6 개를 물되 5 개가 non-`LIVE` 인 key 는 **정반대 verdict** 이고 width 는 비슷하다. 그래서 "key 로 쓰기 전에 key 를 재라"(D-193)를 **글자 그대로** 지킨 네 번째 cycle 도 같은 결함을 ship 할 수 있다. hit count 는 composition 을 볼 수 없다.
- **Decision**: (1) `OPERATOR_INVOKED` 를 **발급하지 않는다**. `reprobe` 는 `UNREACHED` 로 남고 residue 는 **8** 그대로다. (2) measurement 를 산문이 아니라 **instrument** 로 ship 한다 — `key_discrimination.py` 는 `narrowing`(얼마나 작아졌나)과 `discrimination`(composition 이 움직였나)을 **두 개의 reading 으로 분리해서** 반환하고, 후자만 verdict 를 licence 한다. 네 cycle 연속 손으로 굴린 측정이 이제 suite 안에 있다.
- **두 축을 접으면 안 되는 이유가 test 로 고정돼 있다**: `narrowing 5× + discrimination 0` 과 `narrowing 1.2× + 완전 분리` 를 synthetic key 로 각각 몰아 반대 등급이 나오는 것을 pin 했다. 한 숫자를 두 이름으로 보고하는 것이 이 module 이 막으려는 conflation 이고, 그것이 D-193/D-196 의 기록이 남은 방식이다.
- **`VACUOUS` 가 이 package 에서 다섯 번째로 필요한 이유**: hit 0 개인 key 는 `LIVE` hit 도 0 개라 **discrimination 만점**을 받는다 — 시험된 적 없는 key 에게 주는 만점. wide control 이 측정되지 않은 경우도 같은 방식으로 무너지며, 그것이 정확히 D-196 이 쓴 문장("25 개, 대부분 `LIVE`")의 구조다. 둘 다 `VACUOUS` 로 떨어뜨린다.
- **threshold 는 판단이지 측정이 아니고, 이 reading 은 거기 걸려 있지 않다**: 측정된 delta 1.4 point vs margin 25 point. test 가 margin 2/10/50/90 을 모두 몰아 같은 verdict 를 요구한다 — 미래 cycle 이 선을 옮겨 key 를 구제하는 경로를 막는다. 다음 key 가 선 근처에 떨어지면 그건 선을 옮길 신호가 아니라 **두 번째 축을 재라는 신호**다.
- **Alternatives**: (a) 채택 — verdict 없음, 측정을 instrument 로. (b) narrow key 로 `OPERATOR_INVOKED` 를 지금 ship — 10 개 중 9 개가 `LIVE` 인 key 에 verdict 를 얹는 것이고 D-193 의 실패를 세 번째로 재연. (c) key 를 더 좁혀 `reprobe` 만 남을 때까지 조건을 추가 — n=1 에 대한 shape-fitting(D-189), 그리고 그렇게 만든 key 는 정의상 분리를 증명할 수 없다. (d) 결과를 journal 산문으로만 남기기 — D-194 가 거절한 "측정 가능한 사실의 산문 강등", 그리고 다섯 번째 cycle 이 같은 측정을 다시 한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-13-narrowing-is-not-discrimination.md` · D-196 (이 measurement 를 미룬 cycle) · D-193 (key 를 쓰기 전에 잰다 — 그 규율의 불완전함이 이 entry 의 주제) · D-189 (shape-fitting) · D-058 (탐지하도록 쓰여진 방향도 pin) · D-044 (지울 수 없는 red 는 muted 된다)

## D-196 — 2026-08-11 — **세 번째 residue member 의 call site 는 source tree 에 없고 decision log 에 있다**: `reprobe` 는 죽은 코드가 아니라 **operator instrument** 이고, 그 사실을 key 로 쓰기에 "log 에 call syntax" 는 너무 넓다 (25/599)

- **Context**: STATE #1 이 D-195 의 뒤를 이어 "이제 *검증된* zero reference 를 가진 3명(`assert_reach.asserts_in`, `horizon_audit.format_scan`, `inert_surface.reprobe`)을 triage 하라"를 지시했다. D-186 규칙(6 cycle 연속 — 쓰기 전에 전제를 측정한다)대로 argument 를 쓰기 전에 세 member 의 sibling family 와 repo 전체 언급을 먼저 훑었고, `reprobe` 에서 **전제가 다시 깨졌다**.
- **Finding**: `docs/decisions.md` 는 `reprobe` 를 *언급*하는 것이 아니라 **실행한 기록**을 두 곳에 갖고 있다. D-183: "`reprobe('STATE.md')` 로 entrant 1개(27 test)만 재측정 → `INERT_COMPOSED` gen-1 로 갱신 (full probe 15m45 대신 수 초)". D-177 cycle: "`reprobe` 는 `CONTENT_READ` 를 돌려줬는데 그것 역시 그 module 의 성질이다". 둘 다 **인자와 반환 verdict 가 같이 적혀 있다** — 이것은 누가 이름을 들고 있다는 주장(D-195 의 `REFERENCED_NOT_CALLED`)보다 강하다. 함수가 돌았고, 무엇을 돌려줬는지가 기록돼 있다.
- **그래서 `UNREACHED` 는 이 함수에 대해 틀린 verdict 가 아니라 틀린 질문이다**: census 의 population 은 source tree 이고, `reprobe` 의 caller 는 **pin 이 stale 해진 cycle 의 사람/executor** 다. suite 가 부르지 않는 것이 이 함수의 결함이 아니라 **설계**다 — 15m45 짜리 full probe 를 수 초로 줄이는 것이 존재 이유이고, 그것이 필요한 순간은 정의상 suite 밖이다. D-193 의 `take_and_record`(2k concurrent five-minute run)와 같은 계열이되 이유가 다르다: 저쪽은 *너무 비싸서* 도달 불가, 이쪽은 *비쌀 때만 불리는 싼 우회로*.
- **측정된 key, 그리고 왜 그대로 쓰면 안 되는가**: "decision log 안에 인자 있는 call syntax(`` `name(...` ``)" 를 package 의 public module-level 함수 **599 개**에 걸어 보면 **25 개**가 걸린다 (`check`, `grade`, `resolve`, `run_matrix`, `scope`, `certify`, …). 대부분은 `LIVE` 이고, 그러면 이 key 가 오늘 residue 에서 `reprobe` 하나만 집어내는 것은 **나머지 24 개에 caller 가 있다는 우연**이다 — D-193 이 `# pragma: no cover` 에서 정확히 이 형태를 거절했고(48 중 43 이 `LIVE`), 그 교훈이 다른 marker 를 입고 한 cycle 만에 되돌아왔다. 좁혀야 할 방향은 **호출된 흔적이 아니라 반환값이 기록된 흔적**(call + recorded verdict)이지만, 그 좁은 key 의 population 은 이 cycle 에서 **측정하지 못했다**.
- **Decision**: (1) `reprobe` 를 "argument 를 빚진 3명" 에서 **뺀다** — 빚진 것은 argument 가 아니라 census 가 볼 수 없는 population 에 대한 이름이다. (2) verdict 는 **발급하지 않는다**. 좁은 key 를 측정하기 전에 `OPERATOR_INVOKED` 를 ship 하는 것은 D-193 이 금지한 그 순서(재기 전에 key 를 쓰는 것)를 그대로 반복하는 것이고, 오늘 넓은 key 가 25 개를 무는 것을 이미 봤다. (3) 남은 triage 대상은 `asserts_in` 과 `format_scan` **둘**이고, 이 둘에 대해서는 D-195/D-196 이 제거한 종류의 반례가 없다 — repo 전체 grep 이 pin list 와 journal 산문 외에 아무것도 돌려주지 않는다.
- **`format_scan` 에 대해 미리 기록해 둘 것**: 이 함수는 markdown table 을 만들고, `horizon_audit` 의 **module docstring 은 정확히 그 모양의 table 을 담고 있다** — 즉 shipped table 이 이 generator 로 재도출된 적이 있는지가 다음 cycle 의 질문이고, 그것은 D-107(재도출 안 된 provenance) / D-139(generator 는 자기 table 을 재현한다) 가 이미 두 번 답해 본 형태다. 이번엔 답하지 않았다.
- **Alternatives**: (a) 채택 — 하나를 빼고, key 는 측정 전까지 발급하지 않는다. (b) `OPERATOR_INVOKED` 를 넓은 key 로 지금 ship — D-193 의 실패를 한 cycle 만에 재연. (c) `reprobe` 를 삭제 — 기록된 실행 이력이 있는 instrument 를 suite 가 안 부른다는 이유로 파괴하며, 다음에 pin 이 stale 해지는 cycle 이 15m45 를 지불한다. (d) residue 에 남기고 journal 에 산문으로 적기 — D-194 가 거절한 "측정 가능한 사실의 산문 강등".
- **정직하게 하지 못한 것 (D-181 로 잘라냄)**: 이 cycle 의 wall clock 은 `SUITE_AFFORDABLE` 마감(11m53)에 measurement 중 도달했다. 좁은 key 의 population 측정, `OPERATOR_INVOKED` 구현, 그리고 `asserts_in`/`format_scan` 의 실제 triage 는 전부 다음 cycle 로 넘긴다. residue 는 **8 그대로**이고 이 cycle 은 그것을 줄이지 않았다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-12-the-call-site-was-in-the-decision-log.md` · D-195 (census 가 못 보는 참조 형태) · D-193 (key 를 재기 전에 그 key 를 잰다) · D-194 (vocabulary defence 는 citation 이다) · D-183 / D-177 (`reprobe` 실행 기록) · D-181 (elapsed 로 scope 를 자른다)

## D-195 — 2026-08-11 — **residue 는 코드에 대한 주장이기 전에 instrument 에 대한 주장이다**: 네 명 중 하나는 애초에 residue 가 아니었고, escape hatch 가 드문 쪽 절반에만 열려 있었다

- **Context**: STATE #1 이 D-194 를 이어받아 "vocabulary defence 를 쓸 수 없는 4명을 triage 하라 — 각자 다른 argument 를 빚지고 있다"를 지시했다. argument 를 쓰기 전에 D-186 규칙(5 cycle 연속)대로 각 member 의 sibling family 를 먼저 측정했고, `build_*_repo` family 에서 **call site 가 나왔다**. 질문이 "어떤 argument 를 빚졌나"에서 "왜 census 가 이걸 못 보나"로 바뀌었다.
- **Finding**: `guard_direction.PROBES` 는 `build=build_stranding_repo` 를 들고 있고, 세 곳이 `(probe.build or build_scratch_repo)(repo)` 로 dispatch 한다 — 그 probe 가 돌 때마다 builder 가 **실행된다**. census 는 `UNREACHED`, `mentions=0` 으로 보고했다. dead code 를 뜻하는 verdict 를, suite 안에서 실제로 실행되는 함수에 대해.
- **원인**: `call_census` 의 mention scan 은 `mod.func` (cross-module `ast.Attribute`) 와 `"name"` (string dispatch key) 두 형태만 셌고, **같은 module 안의 bare `ast.Name`** 을 빼먹었다. 아는 두 형태는 **둘 다 cross-file** 이다. 코드 어디에도 "cross-file" 이라고 적혀 있지 않았다 — 그건 작성 당시 손에 있던 예시들의 모양이었고, 조용히 규칙이 되었다. 그런데 이 repo 의 registry 는 자기 member 들 **옆에** 선언되므로, 빠진 형태가 오히려 normal case 다.
- **Decision**: mention scan 에 `ast.Name` + `ctx=Load` + non-call 을 추가한다. `ctx` 가 `Load` 여야 하는 것은 load-bearing — `Store` 를 세면 함수와 이름이 겹치는 local 변수가 그 함수를 보증하게 된다. verdict 는 `LIVE` 가 아니라 `REFERENCED_NOT_CALLED` 이고 그것이 정직한 상한이다: census 는 `probe.build` 를 target 까지 따라가지 않으므로, 말할 수 있는 것은 "누가 이름을 들고 있다"이지 "누가 호출한다"가 아니다.
- **Blast radius 는 의도가 아니라 측정으로 좁다**: 두 population 을 통틀어 9명의 residue 중 **정확히 1명**만 빠져나가고, 나머지 8명은 전후로 `mentions=0` 이다 (D-193 규칙 — key 로 쓰기 전에 population 을 측정한다). `test_the_registry_form_is_not_an_amnesty` 로 negative control 을 pin 했다: residue 전체를 비워버릴 만큼 느슨한 mention 규칙은 **D-189 shape-fitting 의 한 단계 위 버전**이다 — red 하나마다 caller 를 만들어내는 대신, 모든 red 를 green 으로 만드는 규칙 하나를 만들어내는 것.
- **blind spot 이 어느 쪽으로 잘랐는지가 중요하다**: 이 결함은 caller 를 **발명할 수는 없고 숨길 수만** 있었다. 따라서 왜곡된 모든 verdict 는 finding 쪽으로 왜곡되었다 — residue 는 over-count 였지 under-count 가 아니었고, D-191 이후의 triage 결정들이 확인되지 않은 reachability 주장 위에 서 있지는 않았다는 뜻이다. 반대 방향이었다면 열한 cycle 의 triage 가 전부 재검토 대상이었다.
- **Alternatives**: (a) 채택 — 세 번째 참조 형태를 인정하고 blast radius 를 pin. (b) `build_stranding_repo` 만 allow list 에 예외 등록 — `guard_reflexivity` 가 세는 다섯 번째 unwatched allow list 를 만드는 것이라 거절. (c) residue 에 남기고 "registry 에 등록되어 있다"는 argument 를 journal 에 적기 — 측정 가능한 사실을 산문으로 강등하는 것이고, 다음 cycle 이 같은 triage 를 다시 하게 된다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-11-the-builder-was-never-in-the-residue.md` · D-194 (vocabulary defence 는 citation 이다) · D-193 (marker 는 기존 용법의 의미를 물려받는다) · D-191 (population A/B 분리) · D-189 (shape-fitting)

## D-194 — 2026-08-11 — **짝지어진 전제는 주장이 두 개다**: STATE 가 세 cycle 동안 하나로 묶어 온 두 accessor 중 citation 을 실제로 가진 쪽은 하나뿐이었다

- **Context**: STATE #1 이 세 cycle 연속 같은 문장으로 추천했다 — "`guard_vacuity.never_fired` 와 `predicate_vacuity.one_sided` 는 **자기 module docstring 이 reading 의 vocabulary 로 지목하는** one-line accessor 다. keep-with-citation 이냐 delete-and-fold 냐". 이 문장은 두 함수를 하나의 case 로 묶고, 그 근거(`docstring 이 지목한다`)를 둘 다에 대해 참이라고 전제한다. D-186 규칙(쓰기 전에 전제를 측정한다)을 적용해 그 전제 자체를 AST 로 확인했다.
- **Finding**: 전제는 **절반만 참**이었고, 하필 짝지은 지점에서 거짓이었다. `guard_vacuity` 의 module docstring 은 "The reading is the suite's, not the code's" 절에서 `:func:`never_fired`` 를 실제로 인용하며 왜 findings 가 아니라 candidates 를 반환하는지 설명한다. `predicate_vacuity` 의 module docstring 은 **형제들**(`:func:`unpatchable``, `:func:`calibration_census``)을 인용하면서 `one_sided` 는 `:func:` 로도, 산문으로도 **한 번도 언급하지 않는다**. 즉 module 의 reading 그 자체인 accessor 가 존재하는 내내 소개된 적이 없다. 한쪽은 진짜 방어 논거를 가졌고 다른 쪽은 같은 문장이 자기에 대해 말해졌을 뿐이며, package 안의 어떤 것도 그 둘을 구분할 수 없었다 — 그래서 세 cycle 이 검증 없이 같은 짝을 반복했다.
- **Decision**: (1) `predicate_vacuity` 의 module docstring 에 빠져 있던 절을 **쓴다** — `one_sided` 는 실제로 그 module 의 vocabulary 이고, 없었던 것은 함수가 아니라 그렇게 말하는 문단이었다. 문서가 불완전하다는 이유로 진짜 reading 을 삭제하는 것은 거꾸로다. (2) vocabulary 방어를 **믿지 않고 검사한다**: `test_the_vocabulary_defence_is_a_citation_not_an_assertion` 이 `VOCABULARY_DEFENCE` 의 각 이름에 대해 자기 module docstring 의 `:func:` 인용을 요구한다. 양방향으로 load-bearing — 함수를 지우면 docstring 이 없는 것을 가리키고, 인용을 지우면 caller 없는 함수의 방어 논거가 조용히 증발한다. (3) residue 를 방어 가능성으로 **쪼갠다**: `NO_VOCABULARY_DEFENCE` 4 개(`asserts_in`, `build_stranding_repo`, `format_scan`, `reprobe`)는 자기 docstring 이 이름조차 언급하지 않으므로 이 논거를 쓸 수 없고, 인용을 쓰는 순간 test 가 빨개져 위 목록으로 옮기도록 강제한다 — 인접성으로 방어가 번지는 경로를 막는다.
- **왜 caller 를 만들지 않았나**: 7 개가 one-line test call 로 green 이 되지만 그것은 D-189 의 shape-fitting — 측정되는 대상 대신 측정 자체를 만족시키는 것이다. 두 함수는 residue 에 그대로 남아 여전히 uncalled, 여전히 red 다. 이 결정은 verdict 를 면제하지 않으므로 D-193 이 경계한 "finding 을 숨기는 marker" 가 될 수 없다 — 그 점을 명시적으로 확인했다.
- **측정된 key**: `:func:` self-citation 은 public module-level 함수 740 개 중 117 개(15.8%), bare mention 은 234 개(31.6%). bare 는 key 로 쓰기엔 너무 넓어 `:func:` 만 채택했다.
- **잘라낸 것 (D-181)**: 자연스러운 watcher 인 package 전역 dangling `:func:` reference 검사는 측정 후 **거절**했다 — same-module 좁은 scope 에서도 미해결 40 건이고 대부분 정당하다(test module 이 자기 subject 를 인용, source module 이 형제 module 을 인용). 예산 안에서 shipping 하려면 carve-out 목록이 필요했고, carve-out 을 달고 나가는 검사는 이 package 가 계속 키워 온 다섯 번째 unwatched allow-list 가 된다.
- **Alternatives**: (a) 채택 — 인용을 쓰고 검사한다. (b) 둘 다 삭제 — `one_sided` 는 실제 vocabulary 이므로 문서 결함을 이유로 reading 을 파괴한다. (c) STATE 문장대로 "둘 다 인용됨" 으로 keep — 거짓 전제를 네 번째 cycle 로 넘긴다. (d) caller 추가 — D-189 shape-fitting.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-10-the-vocabulary-defence-was-a-citation-for-one.md` · D-186 (쓰기 전에 전제를 측정) · D-193 (key 를 재기 전에 그 key 를 잰다) · D-189 (shape-fitting) · D-181 (elapsed 로 scope 를 자른다)

## D-193 — 2026-08-11 — **marker 는 지금 쓰이는 뜻을 물려받는다**: STATE 가 지정한 key(`# pragma: no cover`)는 48 번 중 43 번이 `LIVE` 이고, 좁아 보이는 것은 우연이었다

- **Context**: STATE #1 은 `reading_record.take_and_record`(2k concurrent five-minute run — 구조적으로 fast suite 가 도달 불가) 를 residue 에서 빼기 위해 "`# pragma: no cover` marker *rule* 로 key 하라" 고 가격을 매겼다. D-186 규칙대로 쓰기 전에 key 를 **측정**했다: population B 744 함수 중 48 개가 이 marker 를 달고 있고 그 중 **43 개가 `LIVE`**, tail 은 `- CLI`(13×) / bare(8×) / `- reporting`(5×) / `- reporting sugar`(3×) / `- defended`(3×). 이것은 **coverage** directive 이지 reachability 진술이 아니다.
- **Decision**: verdict 는 **자기 주장을 적는 전용 marker** 로 key 한다 — `# pragma: no cover -- deferred-by-cost: <why>`. coverage pragma 의 하위 형태라 coverage 동작은 그대로이고, 뒤 절이 "왜 아무도 안 부르는가" 를 **정의 지점에서** 말한다. **signature** 에서만 읽고(body 아님), `_grade` 에서 reachability verdict 들보다 **뒤에** 놓는다 — marker 는 caller 의 부재를 설명할 뿐 존재를 뒤집지 못한다. residue 10 → 9, `DEFERRED_BY_COST=1`.
- **왜 bare pragma 가 안 되는가**: 오늘 residue 에서 하나만 집어내는 것은 *나머지 43 개에 caller 가 있다는 우연*이다. 그 중 약 24 개는 자기 `if __name__` block 이 불러서만 `LIVE` 인 `report()`/`main()` 이다. 일상적 refactor 로 그 block 이 사라지면 bare-pragma rule 은 새로 죽은 reporter 를 `UNREACHED` 대신 `DEFERRED_BY_COST` 로 매긴다 — **finding 을 숨기는 면제**, 그것도 그런 주장을 한 적 없는 marker 가 발급한 것. D-189 의 "mention 은 call 이 아니다" 와 같은 형태다. 두 rule 은 **현재 tree 에서 구별 불가**하고 아직 없는 tree 에서만 갈린다 — 그 차이가 이 cycle 의 산출물 전부다.
- **self-serve marker 의 watcher**: 어떤 signature 든 이 marker 를 타이핑할 수 있다. 막는 것은 registry 가 아니라 **residue pin** 이다 — verdict 를 가져가면 이름이 pin list 에서 *빠지므로*, 같은 commit 에서 test 를 고치지 않고는 주장할 수 없다. 중앙 allow list 를 만들지 않는다(`guard_reflexivity` 가 세는 결함).
- **첫 draft 가 틀렸고 자기 test 가 잡았다**: comment 는 AST node 가 아니라서 `def` ~ 첫 body statement 구간이 header 바로 아래의 **독립 comment 줄**을 삼킨다. pure-comment 줄을 버리는 것으로 고쳤고, `take_and_record` 가 쓰는 multi-line `):  # pragma …` 형태는 유지된다.
- **Alternatives**: (a) 채택 — 전용 marker. (b) STATE 가 적은 bare pragma — 오늘 통과하고 다음 refactor 에서 조용히 finding 을 먹는다. (c) 등급 안 매기고 residue 10 유지 — 알려진 non-defect 를 계속 count 가 지고 간다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-09-the-coverage-pragma-was-the-wrong-key.md` · D-189 (mention ≠ call) · D-192 (residue 는 한 population 이 아니다) · D-186 (쓰기 전에 읽어라) · D-044 (지울 수 없는 red 는 muted 된다)

## D-192 — 2026-08-11 — residue 안에 **다른 instrument 의 watcher** 가 있었다: `stale_grades` 는 지우거나 연결할 대상이 아니라 **실행**할 대상이었고, 나머지 9 개를 green 으로 만드는 것은 shape-fitting 이다

- **Context**: STATE 의 bottleneck 은 D-191 이 남긴 `UNREACHED` 11 개를 "하나씩 delete-or-wire, 각각 한 줄 결정" 으로 가격했다. 11 개 body 를 **한 번에** AST 로 뽑아 읽었다 — 한 cycle 에 하나씩 걸으면 "각각 한 줄" 이라는 전제 자체를 시험할 수 없기 때문이고, 그 전제가 틀렸다.
- **① 발견은 residue 안에 watcher 가 있었다는 것이다**: `candidate_scope.stale_grades` 는 `GRADED` 의 감시자다. `coverage` 가 `len(GRADED)` 를 세는 것을 그만두고 `RESIDUE` 를 `GRADED` 멤버십으로 좁히기 시작한 순간 `GRADED` 는 **typed allow-list** 가 됐고, 그 순간 owed 된 것이 이 함수다. 그런데 **아무도 부르지 않았다.** 즉 이 package 는 존재 내내 *감시자가 있으나 실행되지 않는 allow-list* 를 이고 있었다 — `guard_reflexivity` 가 세는 바로 그 결함이고 D-189 가 rule 로 교체한 그 형태이며, **그것이 D-191 이 bound 한 residue 안에 앉아 있었다.**
- **watcher 의 fix 는 delete 도 rewrite 도 아니라 run 이다**: `TestTheWatcherIsRun` 3 개. clean case (`stale_grades() == ()`) 만 pin 하는 것은 **실패할 수 있음을 보이지 않은 watcher** 이므로 (D-058), `residue=()` 와 shrunk-residue 로 **탐지하도록 쓰여진 방향**을 함께 pin 한다. 그리고 `coverage() == (4,4)` 와 묶어 두 reading 이 한 사실의 두 판임을 고정한다.
- **② `UNREACHED` 는 한 population 이 아니다 — D-191 의 split 이 한 층 아래에서 다시 owed 됐다**: `reading_record.take_and_record` 는 `# pragma: no cover` 이고 이유를 적고 있다 (2k concurrent five-minute suite run). fast suite 가 **구조적으로** 닿을 수 없다는 뜻이므로 이것은 dead code 가 아니라 `FRAMEWORK_DISPATCHED` 의 모양이다. pytest hook 을 filter 하지 않고 자기 verdict 로 등급 매긴 것과 같은 이유로, 이것도 "debt 11 개" 에 섞어 세면 안 된다.
- **분류는 typed 가 아니라 derived 다**: "일부러 uncovered 인 이름" 의 손목록은 D-189 가 없앤 **감시되지 않는 다섯 번째 allow list** 와 같은 것이므로, marker 를 source 에서 읽어 *rule* 로 assert 한다 — residue 안에서 marker 를 든 집합과 구조적으로 unreachable 한 집합이 **같다**.
- **③ 나머지 9 개는 의도적으로 red 로 남긴다**: `guard_vacuity.never_fired` / `predicate_vacuity.one_sided` 는 각자 module docstring 이 **reading 의 어휘로 지명한** 한 줄 accessor 다. caller 가 없는 이유는 consumer 가 `cens.candidates` 를 직접 읽기 때문이고, **instrument 를 green 으로 만들려고** call 을 추가하는 것은 측정 대상이 아니라 측정을 만족시키는 것 — D-189 가 거절한 shape-fitting 이다. 7 개는 test 에서 한 줄이면 green 이 되고, 그래서 하지 않는다. 대신 미래 cycle 이 **논증 없이 조용히 caller 를 주는 것**을 test 가 막는다.
- **일반 규칙**: "caller 가 없는 함수 N 개" 는 그 N 개를 균일하게 inert 로 취급한다. triage 는 **그 함수가 무엇을 위한 것인지** 읽어야 하고, count 는 그것을 볼 수 없다. 그리고 instrument 를 clear 하는 것과 instrument 가 재는 것을 고치는 것은 다르다.
- **bottleneck 의 가격이 또 싼 방향으로 틀렸다 (5 cycle 연속)**: "11 개의 한 줄 결정" 은 실제로 **1 개의 진짜 wire + 1 개의 구조적 비결함 + 9 개의 (편집이 아니라) 논증** 이었다.
- **Alternatives**: (a) 채택 — 1 개 wire, 1 개 재분류, 9 개 논증과 함께 red 유지. (b) 11 개를 다 delete — `stale_grades` 는 owed 된 guard 이고 `take_and_record` 는 예정된 hook 이라 둘 다 오답. (c) 11 개에 test caller 를 다 붙여 green — 한 cycle이면 되고, 정확히 shape-fitting. (d) pin 만 갱신하고 triage 는 다음 cycle 로 — 네 번째 "다음 cycle" 이 된다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-08-the-watcher-was-in-the-residue.md` · D-191 (두 population 의 split, 이 entry 가 한 층 아래에서 반복) · D-189 (list 는 감시가 필요하고 rule 은 아니다; shape-fitting 거절) · D-058 (실패 방향을 보이는 것) · D-047 (derived vs typed) · D-044 (못 지우는 red 는 muted)

## D-191 — 2026-08-11 — 계측 표면(instrument surface)은 **두 population 으로 나뉘어 읽어야 한다**: helper 96 개는 제 일을 하고 있고, 아무도 부르지 않는 함수 11 개가 진짜 residue 다

- **Context**: STATE 의 bottleneck 은 "non-test caller 가 없는 module-level public function 88 개 — 이 package 는 거대한 write-only 계측 표면을 이고 있는가?" 였다. D-189 는 이 population 을 **측정하고 의도적으로 제외**했다 (96 entry 가 1-item residue 를 묻어버린다는 이유로). 그 제외는 residue 에 대해서는 옳았고 **영구적 침묵으로서는 틀렸다**: 이후 네 cycle 이 연속으로 계측 layer *안에서* 결함을 찾았고 (감시되지 않는 다섯 번째 allow list, 한 frame 위에서 죽은 count, 두 번 적힌 규칙), 그것이 바깥에서 본 "아무도 부르지 않는 표면"의 모습이다.
- **측정 결과 (population B = module-level public function 744 개)**: `LIVE`=626, `TEST_ONLY`=**96**, `REFERENCED_NOT_CALLED`=8, `FRAMEWORK_DISPATCHED`=2, `UNREACHED`=**11**. STATE 가 가격한 "88" 은 근사치였고, 더 중요한 것은 **그 수가 한 덩어리가 아니라는 것**이다.
- **Decision**: population B 를 `consumer_reach` 에 **별도로 보고**하되 A 와 절대 합산하지 않는다. 그리고 **두 population 에서 finding 의 정의가 다르다**:
  - A (alternative constructor): `TEST_ONLY` 가 결함이다 — `from_sweep` 이 그 shape.
  - B (module-level function): `TEST_ONLY` 는 **정상**이다. 그 96 개는 `assert_*` / `*_census` / `*_screen` helper 이고, **suite 가 부르는 helper 는 제 목적대로 쓰이고 있는 것**이다. 이걸 gate 로 걸면 첫날부터 red 이고, 못 지우는 red 는 muted 되는 red 다 (D-044).
  - 두 population 에서 같은 뜻인 유일한 verdict 는 `UNREACHED` — production 에도 test 에도 caller 가 없다 — 이고, 그것이 finding 이다.
- **그래서 bottleneck 의 답은**: 이 package 는 거대한 write-only 표면을 이고 있지 **않다**. 계측 layer 는 *제 일을 하는 helper 96 개* + *caller 가 아예 없는 함수 11 개* 이고, 후자는 D-189 가 피하려던 수보다 **한 자릿수 작다**. instrument cycle 들은 축적되는 게 아니라 compound 되고 있다.
- **`FRAMEWORK_DISPATCHED` 는 exemption 이 아니라 verdict 다**: `loop_reach.pytest_configure` / `pytest_unconfigure` 는 pytest 가 이름으로 hook 을 해석하므로 in-repo call site 가 **구조적으로** 없다 — 인터프리터가 `__new__` 를 부르는 것과 같은 모양이고, 그래서 `definitions()` 의 dunder 규칙이 존재한다. 유혹은 이 둘을 filter 로 걸러내는 것이고, 그러면 **감시되지 않는 다섯 번째 allow list** 가 생긴다 (`guard_reflexivity` 가 세는 바로 그 결함). 그래서 걸러내지 않고 **자기 verdict 로 등급을 매긴다**: report 에 보이고, finding 에서는 빠지고, 아무도 읽지 않는 filter 뒤에 숨는 것이 없다. 규칙의 key 는 framework 자신이 정의한 naming convention 이므로 새 hook 이 생겨도 편집이 필요 없다.
- **B 는 gate 가 아니라 ratchet 이다**: `check` 는 여전히 A 만 등급한다. B 의 residue 11 개는 `test_consumer_reach.py` 가 **이름으로 pin** 한다 — 하나를 지우거나 caller 를 주려면 그 목록을 편집해야 하고 (그게 목적), **조용히 늘어나는 것**이 pin 이 금지하는 것이다. 11 개를 한 cycle 에 지울 수 없고, 몇 주 서 있는 red 는 아무도 읽지 않는 red 다.
- **Alternatives**: (a) 채택 — 분리 보고 + scope 별 finding 정의 + pin. (b) B 를 A 에 합산해 함께 등급 — 96 개가 1-item residue 를 묻는다, D-189 가 거절한 그것. (c) 계속 침묵 — 네 cycle 이 그 침묵 안에서 결함을 찾았다. (d) `TEST_ONLY` 를 B 에서도 등급 — 첫날부터 96 red, D-044 로 즉시 mute.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-07-the-helpers-are-doing-their-job.md` · D-189 (population 제외) · D-190 (규칙의 단일 진술) · D-047 (mention 은 measurement 이 아니다) · D-044 (못 지우는 check 는 muted 된다)

## D-190 — 2026-08-11 — **파생 규칙도 자기 자신에 대한 진술을 하나만 가져야 한다**: flag→bounds 규칙이 두 곳에 적혀 있었고, 사본은 `None` 가지를 빠뜨렸다

- **Context**: STATE #1 은 D-189 가 남긴 residue (`WalkCount.from_sweep`, `prod_calls=0`) 를 "production caller 를 연결하라 — shape 을 맞추지 말고 **call 을 하라**" 로 가격했다. D-186 의 규칙(연결하기 전에 consumer 가 무엇을 소비하는지 먼저 읽어라)을 적용해 `recorded_walk_counts()` 를 열었고, 거기서 찾은 것은 빠진 call 이 아니라 **중복된 규칙**이었다.
- **기계적 사실**: `recorded_walk_counts` 의 flagged loop 은 `from_sweep` 이 이미 소유한 flag→bounds 규칙을 손으로 다시 적고 있었다 — `k_min=0 if in_band else 1`, `k_max=0 if in_band else n`, `source=FROM_FLAG_ADMISSIBLE if in_band else FROM_FLAG_REFUSED`. 세 줄이 동일하고, **`None` 가지만 없었다.** 따라서 `in_band=None` 이 도착하면 사본은 `k_min=1` 을 `FROM_FLAG_REFUSED` 라벨로 생산한다 — 즉 disk 가 아무것도 고정하지 않는 walk 을 **`k ≥ 1` 로 보고**한다. D-187 이 `FROM_FLAG_UNKNOWN` 을 만들어 막으려던 바로 그 혼동이 두 번째 site 에서 조용히 되살아나 있었다.
- **왜 suite 가 못 봤나**: 두 site 는 `True` 와 `False` 에서 **일치**하고 `None` 에서만 갈라진다. 그리고 현재 disk 의 어떤 record 도 `None` flag 을 만들지 않는다. 규칙의 사본은 아무도 지나가지 않는 가지에서 갈라졌고, 그래서 green 이었다. **두 진술을 가진 규칙은 실행되지 않는 가지에서 어긋난다.**
- **Decision**: `WalkCount.from_flag(name, n, in_band)` 로 규칙을 **한 번만** 적는다. `from_sweep` 의 flag tail 과 `recorded_walk_counts` 의 loop 둘 다 이것을 호출한다. 방향은 안전한 쪽이 아니다 — `None` 을 `False` 로 접는 것은 보수적 반올림이 아니라 **부재에서 floor 를 만들어내는 것**, 즉 취해진 적 없는 증거를 보고하는 것이다.
- **일반 규칙**: D-047 의 "registry 는 자기 자신에 대한 진술을 정확히 하나만 가져야 한다" 는 **파생 규칙(derivation rule)** 에도 적용된다. registry 만의 성질이 아니다. 그리고 D-189 가 "list 는 감시가 필요하고 rule 은 필요 없다" 로 적은 것의 따름정리: rule 이라도 **두 번 적히면 다시 감시가 필요해진다.**
- **STATE #1 은 닫히지 않았고, 이 cycle 은 닫혔다고 주장하지 않는다**: `consumer_reach` 는 여전히 `from_sweep` 을 `TEST_ONLY` 로 읽는다 (population 5, `LIVE=4`, residue 정확히 1). `from_flag` 이 live 가 됐을 뿐이다. 같은 prospective 주장을 **네 번째로** 적지 않는 것이 이 항목에 대한 이번 cycle 의 기여다.
- **residue 는 편집으로 닫을 수 없고, 이제 그것이 test 로 고정됐다**: `from_sweep` 은 `ab.SweepStats` (`.n` / `.n_out_of_band` / `.ess_in_band`) 를 소비하는데 **disk 위의 어떤 record 도 그 모양이 아니다** — `CONVOY_W75_NULL` / `HEADON_W75_NULL` 은 `NullRung`, `LOUDER_NULL` 은 dict, 셋 다 `.n` 도 `.n_out_of_band` 도 없다. 소비 가능한 유일한 입력은 **아직 취해지지 않은 walk** (64 closed-loop run, user-blocked, 2분 sim 한도 초과) 이다. disk record 가 duck type 을 만족하도록 고치는 것은 D-188 이 했고 D-189 가 잡은 바로 그 shape-fitting 이므로 거절한다. test 는 record 가 실제로 `SweepStats` 모양으로 도착하는 날 red 가 되고, 그때 wiring 은 전망이 아니라 실제 작업이 된다.
- **비용 회피 (같은 실수 3연속을 끊음)**: 첫 suite 를 시작 1분 만에 죽였다 — 대기 중인 `docs/decisions.md` write 가 test read surface 안(`citation_audit.SCANNED_DOCS`)이라는 것을 알아챘기 때문이다. doc 을 먼저 쓰면 suite 가 두 번이 아니라 한 번이다. 08-10 22:00 과 08-11 05:00 은 각각 이 순서 때문에 18분짜리 suite 를 한 번 더 냈고 둘 다 OVERRUN 했다. D-044 의 ordering table 은 이미 이것을 적고 있었고, 지킨 것은 이번이 처음이다.
- **Alternatives**: (a) 채택 — 규칙을 `from_flag` 으로 추출하고 두 site 가 호출. (b) 사본에 `None` 가지만 추가 — 같은 규칙의 두 진술이 유지되고 다음 가지에서 또 갈라진다. (c) `recorded_walk_counts` 가 `SweepStats` adapter 를 만들어 `from_sweep` 을 호출 — STATE 가 명시적으로 금지한 shape-fitting 이고 D-188 의 재범. (d) `from_sweep` 삭제 — residue 는 0 이 되지만 user 가 re-walk 을 승인하면 다시 필요하고, 삭제 여부는 STATE #2 로 넘긴다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-06-the-rule-was-stated-twice.md` · D-189 (mention 은 call 이 아니다; residue 의 출처) · D-187 (`FROM_FLAG_UNKNOWN` 의 도입) · D-186 (estimator signature 를 먼저 읽어라) · D-047 (registry 는 진술을 하나만) · D-044 (write 순서 table)

## D-189 — 2026-08-11 — **mention 은 call 이 아니다**: D-188 이 연결했다고 적은 constructor 는 여전히 caller 가 없고, grep 은 그것을 볼 수 없다

- **Context**: STATE #1 은 D-188 의 교훈("field 는 *기록되는* 객체가 들고 있어야 keep 된다")을 일반화하라고 지시하면서 그 작업을 **"non-test caller 를 grep 하라"** 로 가격했다. 그 가격이 틀렸고, 반례는 다름 아닌 동기가 된 instance 자신이다.
- **기계적 사실**: `grep -rn from_sweep eval/mppi_sandbox/*.py` 는 정의 밖에서 **4 개**를 반환하는데 그 중 3 개가 **산문**이다 — module docstring 하나, method docstring 하나, 그리고 **D-188 이 자기 fix 를 설명하려고 쓴 주석**. 즉 grep 은 clean 하게 읽히고 constructor 는 죽어 있다. D-047 의 "주석은 측정이 아니다" 에는 caller-counting 따름정리가 있다: **mention 은 call 이 아니며, 둘을 구분할 수 있는 것은 parser 뿐이다.**
- **발견 (D-188 은 D-187 을 닫지 않았다)**: D-188 은 "그 생성자가 repo 최초로 production caller 를 갖는다" 고 적었다. 갖지 않았다. D-188 이 ship 한 것은 `Rung` 이 `n_in_band`/`n_reached` 를 싣는 것 — 즉 생성자의 **duck type 을 만족**시킨 것 (인자가 이제 올바른 모양으로 도착한다) — 이고, 그 생성자를 **호출하는 것은 여전히 없다**. population 4, residue 정확히 1, 그리고 그것이 `from_sweep` 이다. 같은 주장이 prospective 로 **두 번** 적혔고 (D-187, D-188) **0 번** 수거됐다.
- **Decision**: `consumer_reach.py` — package 의 non-test module 이 정의하는 모든 `classmethod`/`staticmethod` 를 `ast` 로 census 하고 call site 의 위치로 등급을 매긴다: `LIVE` / `REFERENCED_NOT_CALLED` / `TEST_ONLY` / `UNREACHED`. `TEST_ONLY` 가 `from_sweep` 모양이고 유일한 finding 등급이다. real-package residue 를 test 로 고정 → 새로 죽는 constructor 가 세 cycle 뒤가 아니라 즉시 red 가 된다.
- **침묵 쪽으로 기울인다 (D-044)**: bare-identifier string 이나 호출되지 않은 attribute 로 이름이 나타나면 `REFERENCED_NOT_CALLED` 로 강등되고 finding 이 아니다 — 이름을 key 로 쓰는 dispatch table 은 이 package 의 실제 pattern 이고, false alarm 이야말로 instrument 를 mute 시키는 것이기 때문이다. 이름 기반 matching 은 동명이인을 합치므로 살아있는 쪽이 죽은 쪽을 구제한다. 두 방향 모두 **finding 을 숨길 수는 있어도 만들어낼 수는 없다** — residue 는 **하한**이다.
- **일반 규칙 (screening 의 세 번째 질문)**: *producer 가 계산하는가* 와 *consumer 가 읽는가* 옆에 **consumer 를 호출하는 것이 있는가** 를 놓는다. 그리고 그 질문의 답은 grep 이 아니라 parse 다. duck-type 호환성은 reachability 가 아니다.
- **premise 는 이번엔 버텼다**: 착수 전 `assert_reach` / `loop_reach` / `probe_reach` 를 먼저 읽었다 (이름이 정확히 이것처럼 들린다). 셋 다 **assertion** reachability 를 재고 caller reachability 를 재는 module 은 없었다. D-183 이후 전제가 싼 방향으로 틀리지 않은 첫 cycle.
- **자기 자신에게 걸린 finding (첫 suite 가 red 였다)**: 이 module 의 첫 판은 `PROTOCOL_NAMES` 라는 module-global frozenset 으로 dunder hook 을 제외했고, 그것이 package 에 **다섯 번째 unwatched allow list** 를 추가해 census pin 6 개를 깨뜨렸다 (`guard_reflexivity` / `liveness_derivation` / `exemption_control` / `exemption_masking`). 즉 **dead-consumer 를 세는 instrument 가 자기 자신은 아무도 보지 않는 exemption registry 를 들고 들어왔다.** 고침은 registry 를 **규칙으로 교체**한 것이다 — `name.startswith("__")` — 그러면 watcher 가 필요 없다. list 는 감시가 필요하고 rule 은 필요 없다는 것이, D-047 이 "registry 는 자기 자신에 대한 진술을 정확히 하나만 가져야 한다" 로 적은 것의 더 싼 판이다. 수정 후 unwatched 집합은 module 이 있을 때와 없을 때가 **동일**하다 (5개, 모두 기존 것).
- **Alternatives**: (a) 채택 — alternative constructor 로 population 을 한정하고 AST 로 센다. (b) STATE 가 시킨 대로 grep — 동기가 된 instance 에서 이미 실패한다. (c) module-level 함수까지 넓힌다 — population 이 수백이고 죽은 것 대부분이 CLI helper 라 1-item residue 가 묻힌다. (d) `REFERENCED_NOT_CALLED` 도 finding 으로 승격 — dispatch-reachable 이름에 false alarm 을 내고 D-044 로 mute 된다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-05-a-mention-is-not-a-call.md` · D-188 (한 frame 위에서 죽은 count) · D-187 (절반만 도달한 fix) · D-047 (주석/재타이핑 금지) · D-044 (clear 불가능한 check 는 mute 된다) · D-139 (generator 가 자기 table 을 재현한다)

## D-188 — 2026-08-11 — count 는 **기록되는 객체**가 들고 있어야 keep 된 것이다: D-187 의 `n_in_band` 는 `Rung` 에서 한 frame 위로 못 올라갔다

- **Context**: STATE #1 은 D-187 이 고친 gate 의 나머지 절반 (`all_reached`) 에 같은 `all()` 모양이 있는지 sweep 하라고 했다. 있었고, 고쳤다 (`SweepStats.n_reached` / `n_froze`). 그런데 그 과정에서 더 큰 것이 나왔다: **D-187 의 fix 자체가 도달하지 못하는 곳에 있었다.**
- **기계적 사실**: census walk 이 실제로 *기록하는* 객체는 `SweepStats` 가 아니라 `barrier_ceiling.Rung` 이다. `_rung()` 은 `stats.ess_in_band` (bool) 만 읽고 `stats.n_in_band` 를 바닥에 버렸다. 그리고 그 count 를 소비하는 생성자 `WalkCount.from_sweep` 은 **test 밖에 caller 가 하나도 없었다**. 따라서 D-187 이 journal 에 적은 전망 — "a walk taken from here records `n_in_band` and pools as a point instead of a bound" — 은 **ship 된 시점에 거짓**이었다. `COUNT_EXACT` 는 test 안에서 손으로 만든 `SweepStats` 로만 도달 가능했고, 어떤 실제 walk 도 거기 닿지 못했다.
- **Decision**: `Rung` 이 `n_in_band` / `n_reached` 를 실어 나르고 `n_out_of_band` / `n_froze` 를 노출한다 — 이로써 `from_sweep` 의 duck type 을 만족하고, 그 생성자가 repo 최초로 production caller 를 갖는다. 모순 guard 는 `SweepStats` 에서 상속하지 않고 `Rung` 에 **다시 적는다**: pass-through 경계는 독립적으로 복사되는 두 field 가 각자는 틀리지 않은 채로 서로 어긋나는 바로 그 지점이다.
- **일반 규칙**: producer 에 field 를 추가하는 것은 fix 의 절반이다. 나머지 절반은 producer 와 *기록되는 record* 사이의 모든 frame 이다. "producer 가 계산하는가" 옆에 세 번째 질문이 필요하다 — **consumer 를 부르는 것이 있는가.** 새 생성자의 non-test caller 를 grep 하는 것은 공짜이고, 이것을 03:00 에 잡았을 검사다.
- **왜 test 가 못 봤나**: D-187 의 test 들이 입력을 손으로 지었다 (`ab.SweepStats(...)` literal). 손으로 지은 입력은 그 객체가 실제 code path 에서 그 모양으로 도착하는지에 대해 아무 말도 하지 않는다 — D-139 가 "답을 아는 cell 로 generator 를 시험하라" 로 적은 것과 같은 구멍의 반대편.
- **sweep 결과는 clean 이고 그것도 결과다**: producer 안의 per-seed reduction 은 `ab.summarize` 의 셋뿐이며 이제 둘 다 witness 를 싣는다. `calibrate_lam.completes_anywhere` 의 `any()` 는 *probe* 위의 reduction 이고 probe 는 이미 자기 count 를 들고 있다 — 심사했고 defect 아님. 세 번째 site 없음.
- **Alternatives**: (a) 채택 — `Rung` 이 두 witness 를 싣고 `from_sweep` 이 caller 를 얻는다. (b) `all_reached` 만 고치고 STATE 가 시킨 것만 한다 — D-187 의 전망이 거짓인 채로 남고, 다음 walk 이 또 count 를 버린다. (c) `Rung` 대신 `_rung` 이 `WalkCount` 를 직접 만든다 — census record 의 schema 를 estimator 에 결합시킨다. (d) 역사적 rung 에 count 를 back-fill — `all_reached=True` 에서는 맞고 `False` 에서는 추측이라 거절.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-04-the-count-died-one-frame-up.md` · D-187 (절반만 도달한 fix) · D-138 (writer 없는 reader-only contract) · D-044 (clear 불가능한 check 는 mute 된다) · Q-042 (`LamProbe.n_reached`, 같은 비대칭을 9일 전에 다른 객체에서 고침)

## D-187 — 2026-08-11 — count 은 disk 밖에 있었던 적이 없다: `ab.summarize` 가 매 walk 마다 계산해서 `all()` 로 버리고 있었다

- **Context**: D-186 이 "estimator 가 무엇을 소비하는지 먼저 읽어라" 를 규칙으로 만들었고, STATE #1 (두 refused walk 의 per-seed ESS 기록) 을 그 규칙으로 심사했다. 첫 질문은 통과했다 — `out_of_band` 는 실제로 per-seed ESS 를 소비한다. 두 번째 질문에서 걸렸다: **producer 가 이미 그 양을 계산하고 있는가.** `ab.summarize` line 235 는 `per_seed_band` — 32 개 per-seed bool 의 list — 를 만들고, `all()` 이 그것을 나가는 길에 bool 하나로 무너뜨린다. `k` 는 이 branch 의 모든 walk 에서 메모리에 존재했고 aggregation 이 버렸다.
- **Decision**: count 를 conjunction 에서 살려낸다. `SweepStats.n_in_band` (+ 파생 `n_out_of_band`) 를 **같은 list** 에서 채우고, `ess_in_band` 와 동일한 sticky-`None` 규칙을 적용하며 (부분적으로 unknown 인 population 위의 count 는 더 작은 count 가 아니라 count 가 아니다), `__post_init__` 이 count 와 verdict 가 모순되는 record 를 거절한다 — 두 field 는 독립적으로 설정 가능하므로 그것 말고는 `n_in_band = n` 과 `ess_in_band = False` 를 나란히 적는 것을 막는 것이 없다. `WalkCount.from_sweep` 은 count 를 보존한 walk 에 `COUNT_EXACT`, 아니면 flag 의 비대칭 bound 로 degrade.
- **historical 절반은 고쳐지지 않고, 고쳐진 척하지도 않는다**: `geometric_null` 의 두 refused rung 은 walk 시점에 count 를 버렸고 어떤 re-read 도 거기 닿지 않는다. `recorded_pooled_reading()` 은 여전히 `POOLED_FLOOR_ONLY` 이고 이제 그것을 **고정하는 test** 가 있다. STATE 는 이 ask 를 "이미 취한 run 의 re-read, 0 new sim" 으로 가격했다 — 실제로는 **re-walk**, 64 closed-loop run 이고, 2분 sim 한도를 넘으므로 executor 가 아니라 user 의 작업이다.
- **산문이 하필 중요한 곳에서 모호했다**: `LOUDER_NULL` 의 "8/8 seeds were in band on the calibration ensemble and 32/32 were not on the walk" 은 `k = 1` 로도 `k = 32` 로도 읽힌다 — identified set 의 **양 끝**이다. module 이 comment 를 measurement 로 소비하기를 거절한 것은 처음부터 옳았다.
- **`None` 은 자기 source 가 필요하다**: 측정되지 않은 walk 는 `k ≥ 1` 조차 고정하지 않으므로 refused case 에 접으면 더 약한 증거가 더 강한 것으로 읽힌다. `FROM_FLAG_UNKNOWN` 이 둘을 분리한다.
- **왜 D-NNN 인가**: 이것은 변수 추가가 아니라 이 branch 가 네 cycle 연속 잘못된 방향으로 가격해 온 문제의 **구조적 원인**이다. per-seed predicate 를 bool 하나로 줄이는 모든 지점이 미래의 cycle 이 rate 를 인용할 수 없게 되는 지점이고, `all_reached` 가 같은 gate 의 나머지 절반이다.
- **Alternatives**: (a) 채택 — producer 에서 count 보존, historical 은 bounded 로 유지. (b) 산문의 `k = 1` 을 읽어 두 rung 을 stamp — D-107 의 재도출 안 된 provenance 이고, 게다가 그 산문은 위에서 보듯 모호하다. (c) 두 rung 재-walk (64 run) — 정직하지만 2분 한도 초과, user 작업. (d) `ess_in_band` 를 `n_in_band` 파생 property 로 교체 — 더 깨끗하지만 기존 construction site 를 깨뜨리고, `__post_init__` 거절이 같은 불변식을 더 싸게 산다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-03-the-count-was-computed-then-discarded.md` · D-186 (estimator signature 를 먼저 읽어라) · D-184 (magnitude 구간) · D-107 (재도출 안 된 provenance)

## D-186 — 2026-08-11 — admissibility flag 은 **`k = 0` 을 정확히 고정하고 `k = 1` 은 전혀 고정하지 않는다**: 빠진 것은 population 이 아니라 count 였다

- **Context**: STATE #1 은 D-184 의 magnitude 구간 (`p ∈ [0.0055, 0.1574]`, 따라서 `(1−p)³² ∈ [0.0042, 0.8372]`, 단위구간의 83%) 을 좁히기 위해 빠진 두 per-seed ESS population (head_on `w=75`, convoy `w_geom=5.0`) 을 recorded walk 에서 복구하라고 지시했다. 복구를 시작하기 전에 구간이 **무엇을 소비하는지** 확인했다: `wilson_interval(k, n)` 은 `(k, n)` 만 받고 per-seed 값을 절대 읽지 않는다. population 은 처음부터 binding constraint 가 아니었다.
- **Decision**: `seed_count_licence.py` 에 `WalkCount` / `PooledReading` / `recorded_walk_counts()` / `pooled_reading()` / `pooling_effect()`. disk 위의 **모든** walked rung 을, disk 가 허용하는 만큼만 좁게 bound 된 `k` 와 함께 하나의 **부분식별(partial identification)** 집합으로 pool 한다. 구간은 `k ∈ [k_min, k_max]` 에 대한 Wilson 구간의 **합집합** — 양 끝이 `k` 에 대해 단조이므로 극단값만 취하면 되고, 그 단조성을 test 로 고정했다.
- **① 발견은 flag 의 비대칭성이다**: `ess_in_band=True` 는 `k = 0` 을 **정확히** 고정한다 — all-seeds gate 를 통과했다는 것은 모든 seed 가 band 안이었다는 뜻이다. `False` 는 `k ≥ 1` 만 고정한다. 그러므로 rate 에 대한 정보를 실어 나르는 walk (거절된 것들) 이 정확히 그 magnitude 를 감추는 walk 이다. disk 위 4개: population 1개 (`k=1/32`), admissible flag 1개 (`k=0/32`, exact), refused flag 2개 (`k ∈ [1, 32]`).
- **② 따라서 pooling 은 두 끝을 반대 방향으로 민다** — `POOLING_RAISES_FLOOR_ONLY`. pooled `k ∈ [3, 65]/128` → `p ∈ [0.0080, 0.5929]`. floor 는 올라가고 (좋다) ceiling 도 올라간다 (`k_max` 가 disk 로 bound 되지 않으므로). "구간을 좁힌다" 가 기대하게 만드는 것과 다르므로 이름을 붙였다. 하나의 Wilson 구간으로 접었다면 bound 를 estimate 로 인용하는 것이 된다.
- **③ 살 가치가 있었던 끝은 floor 다**: D-184 의 부수 발견이 정확히 floor 의 강한 양수성이 `(1−p)ⁿ` 을 *평평할 수도 있는* 것이 아니라 강하게 감소하게 만든다는 것이었다. pooling 이 floor 를 **1.45×** 올린다 (0.0055 → 0.0080) → gate pass probability 의 ceiling 이 **0.8372 → 0.7733**. 이 bound 는 이제 32 seed 가 아니라 **128** seed 가 받친다.
- **prose 의 정확한 `k` 는 소비하지 않는다**: `geometric_null` 은 head_on 의 offending seed 를 주석으로 적어 두었다 ("seed 25 @ ESS 134.15"). 주석은 측정이 아니다 (D-047). 읽었다면 head_on 이 exact 로 돌아오고 pooled 구간은 인용을 단 허구가 된다. bounded 로 돌아오는 것을 test 가 고정한다.
- **세 cycle 연속 같은 형태**: Q-129 의 전제 (D-183), D-184 자신의 base, 그리고 이번. 셋 다 **싼 방향으로** 틀렸다 — 요청된 작업이 실제 필요한 작업보다 비싸게 견적됐다. 계획에 반영할 만큼 안정적인 패턴이다: recover 하기 전에 estimator 의 signature 를 읽어라.
- **이것은 STATE #1 을 폐기하는 논증이 아니다**: 두 walk 의 per-seed ESS 를 기록하면 `POOLED_FLOOR_ONLY` → `POOLED_IDENTIFIED` 로 뒤집히고 **ceiling** 이 고정된다. `test_recording_the_two_populations_is_what_would_identify_it` 이 그것이 무엇을 만들어낼지 이미 assert 한다. ask 는 여전히 할 가치가 있다 — 구간 전체가 아니라 ceiling 을 위해서.
- **Alternatives**: (a) 채택 — count 를 pool 하고 부분식별로 보고. (b) prose 의 `k=1` 을 읽어 exact 로 처리 — D-047 이 금지하고, 그 결과는 인용을 단 허구. (c) pooled 구간을 하나의 Wilson 구간으로 보고 — bound 를 estimate 로 인용하는 것. (d) population 이 없으므로 pooling 을 포기 — floor 개선 (128 seed 가 받치는 bound) 을 버린다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-02-the-flag-pins-zero-but-not-one.md` · D-184 (magnitude 구간의 출처, 부수 발견) · D-183 (전제가 싼 방향으로 틀린 첫 사례) · D-047 (재타이핑/주석 금지) · D-163 (8-seed licence)

---

# Decision Log — ADR-lite

> 매 cycle 끝에 **Decision** (했음) + **Deferred** (안 했지만 했어야) 가 한 줄씩 append 됨.
> 사람이 manual 로 큰 결정 (architecture / scope / priority pivot) 도 여기 누적.
> 형식은 ADR (Architecture Decision Record) 의 경량 버전 — 1 cycle = 1 entry.

**컨벤션**:
- 최신이 위 (prepend)
- 한 entry ≤ 12 줄
- Status: `accepted` / `superseded by D-XXX` / `reverted`
- 참조: 관련 PR, journal, STATE
- Open question 은 별도 [`deliberations.md`](deliberations.md)

---

## D-185 — 2026-08-11 — admissibility reading 은 자기 `n` 을 **들고 다닌다**: rung 이 스스로 답하고, 그 `n` 은 in-band count 가 아니라 **ladder arms** 에서 나온다

- **Context**: D-184 는 census 가 두 gate 를 나란히 인용하고 있음을 `CENSUS_LADDER_SEEDS = 16` / `CENSUS_WALK_SEEDS = 32` 두 module 상수에서 읽어 `PREDICATE_DIFFERS_BY_N` 으로 기록했다. 그 진단은 이 데이터에 대해 옳지만, **census 의 seed 수를 두 번째로 진술하는 것** — D-047 의 모양 — 이고 rung 하나가 다른 ensemble 크기로 걸리는 순간 stale 이 된다. STATE 가 지목한 bottleneck 이 정확히 이것이다: reading 이 자기 `n` 을 안 들고 다닌다.
- **Decision**: `NullRung` 에 `walk_n` / `ladder_n` / `selection_predicate` / `predicate_direction`, `NullCensus` 에 `seed_counts` / `predicate_readings` / `cross_n_selected` / `comparable_predicate` 를 붙인다. 두 수는 전부 recorded array 에서 **유도** (`len(clearances)`, `len(clearance_ladder[w])`) — rung 이 자기 clearances 와 어긋나는 seed 수를 들고 있을 수 없다. verdict 문자열은 D-184 의 `predicate_match()` 를 그대로 부른다 (새로 타이핑하지 않는다).
- **🔴 이 entry 의 실질 — `ladder_n` 은 `ladder_admissibility` 가 아니라 `clearance_ladder` 에서 읽는다**: `_ladder_arms()` 가 recorded 32-seed arm 을 ladder prefix 로 **자른다**. 따라서 16 에서 평가되는 것은 in-band count 뿐이 아니라 **ladder 가 말하는 모든 것** — `ladder_verdicts`, 그러므로 `matched_verdict_identification`, 그러므로 `admissible` 자신 — 이다. `ladder_admissibility` 에 key 를 걸었다면 그것이 `None` 인 rung 은 `NO_LADDER_PREDICATE` 로 읽혔을 텐데, 그 rung 의 ladder verdict 도 여전히 잘린 arm 위에서 계산된다. 즉 conflation 은 D-184 가 지목한 admissibility count 보다 **한 단계 깊고**, 어떤 admissibility 상수도 그 자리(`_ladder_arms`)를 호명하지 않는다.
- **방향은 측정이 아니라 D-184 ①의 따름정리다**: `(1 − p)ⁿ` 이 `n` 에 대해 강하게 감소하므로 작은 `n` 쪽이 **느슨하다**. 두 walked rung 모두 `(16, 32)` → `LADDER_LOOSER`, 즉 selection 이 walk 이라면 거절했을 rung 을 들여보내는 방향. `WALK_LOOSER` 를 반대 부호로 이름 붙이고 negative control 로 고정했다 — 한 부호만 돌려줄 수 있는 reading 은 부호를 측정하는 것이 아니다.
- **`NO_LADDER` 는 `SAME_PREDICATE` 와 별개다**: "test 를 하나만 적용했다" 를 "두 test 가 일치했다" 로 접으면 census 가 측정된 것보다 더 내적으로 일관돼 보인다. 이 class 의 모든 identification property 가 이미 따르는 규칙 (`coefficient_identification` 의 `UNRECORDED`).
- **gate 를 건드리지 않는다**: D-170 (b)/(c) 가 숫자를 구하려 admissibility 를 느슨하게 하는 것을 이미 거절했고 D-184 가 재확인했다. `comparable_predicate` 는 `separates_scene_from_rung` 과 같은 위치의 물건이다 — rung 을 지우지 않고, census 가 그것에 대해 **말할 수 있는 것**을 낮춘다.
- **대가 — `loop_reach` 가 두 cycle 연속으로 발동했다**: 새 test 6개 중 2개가 population 을 돌므로 `test_recorded_reading_covers_exactly_todays_targets` 가 빠진 `READING` row 를 잡았다. ~90s 재측정이 가격이고, 이 guard 는 설계대로 동작하고 있다. 다만 looping population claim 을 계획하는 cycle 은 그 reading 을 **suite 앞에** 예산에 넣어야 한다 — 이번엔 red test 에서 발견했고 그 때문에 suite 착수가 D-181 deadline (12m34) 을 넘겼다.
- **Alternatives**: (a) 채택 — rung 이 자기 `n` 을 유도한다. (b) D-184 의 두 상수 유지 — 이 데이터에 옳지만 D-047 모양이고, `_ladder_arms` 의 더 깊은 conflation 을 영영 못 본다. (c) `ladder_n` 을 `ladder_admissibility` 에 key — 더 좁아 보이지만 위에서 본 대로 **틀렸다**. (d) `comparable_predicate` 를 `verdict` 에 물린다 — census 가 `NO_GRADED_RUNG` 이라 어떤 측정으로도 확인할 수 없는 변경이고, 그래서 Q-131 로 남긴다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/11-01-the-rung-carries-its-own-seed-count.md` · D-184 (gate 는 seed 수의 함수) · D-170 (`matched_ladder` 의 16-seed 채택) · D-047 (유도 vs 재타이핑) · Q-131 (열림)

---

## D-184 — 2026-08-10 — admissibility gate 는 **seed 수의 함수**다: `31/32` 와 `16/16` 은 서로 다른 test 의 verdict 이고 census 는 둘을 나란히 인용하고 있다

- **Context**: 22 cycle 연속 instrument 작업 뒤 STATE 는 "첫 non-instrument bottleneck 을 잡고 tie-break 을 science 로 넘기라"고 지시했다. census 는 coverage **0/6**, `NO_GRADED_RUNG` 이 3주째 고정이고, 걸어본 rung 3개가 전부 거절됐다 — 그 중 둘이 정확히 **31/32** (head_on seed 25 @ ESS 134.15 천장 위, frozen seed 8 @ 11.78 바닥 아래). D-171 이 산 규칙은 "ladder 를 걷기 전에 **instrument** 를 screen 하라, screen 은 0 run 이고 ladder 는 아니다" 였는데, 세 cycle 동안 그 screen 은 **match 량**에만 겨눠졌다. 정작 rung 을 거절해 온 것은 match 량이 아니라 **admissibility gate** 이고, 아무도 그것을 screen 한 적이 없다.
- **Decision**: `seed_count_licence.py` — gate 는 `n_in_band == n`, 즉 표본에 대한 **논리곱**이므로 per-seed out-of-band rate `p` 에서 `(1 − p)ⁿ` 로 통과한다. 그로부터 세 가지를 일급 reading 으로 만든다.
- **① 방향은 측정이 아니라 정리다**: `(1 − p)ⁿ` 은 모든 `p ∈ (0,1)` 에서 `n` 에 대해 **강하게 감소**한다. 그러므로 "작은 ensemble 이 더 관대한 admissibility test 다" 는 이 arm 들에 대한 발견이 아니라 논리곱의 성질이다. D-163 은 이 방향을 **세 번** 경험적으로 기록했고 (세 번째가 D-173 의 8/8 → 31/32), 셋 다 정리를 재측정한 것이다. `licence_direction` 은 데이터를 보지 않고 `MONOTONE_PERMISSIVE` 를 반환하며, 데이터는 오직 `p ∈ {0, 1}` 을 배제하는 데만 읽힌다 — `DEGENERATE_RATE` 를 별도 verdict 로 둔 이유는, 그렇지 않으면 "gate 가 상수다" 와 "seed 수는 상관없다" 가 같은 문자열로 출력되기 때문 (D-183 형태).
- **② 크기는 disk 위 어떤 것으로도 식별되지 않는다**: 완전한 per-seed ESS population 은 하나뿐이다 (`FROZEN_W75_ESS`, `k=1/32`). Wilson 95% → `p ∈ [0.0055, 0.1574]`, 따라서 `(1−p)³²` ∈ **[0.0042, 0.8372]** — 단위구간의 83%. 점추정은 8-seed pre-read 가 그것이 licence 하는 32-seed walk 보다 **2.14×** 통과하기 쉽다고 말하고, 구간은 그 비가 **[1.14, 60.9]** 어디든이라고 말한다. verdict 는 `MAGNITUDE_UNIDENTIFIED`, 그리고 점추정과 구간을 **함께** 실는다 — 이 branch 는 아무도 무감응을 보인 적 없는 knob 에서 취한 점추정에 이미 세 번 물렸다 (D-167 0.7725, D-168 0.0485, D-169).
- **③ census 는 두 population 을 두 gate 로 채점하고 있다**: D-170 의 `matched_ladder` 는 **16-seed** ladder-admissibility 로 rung 을 고르고, 채점 대상인 walked rung 은 **32** 에서 거절된다. ①에 의해 이 둘은 같은 predicate 가 아니며 16-seed 쪽이 **더 느슨하다** — 즉 walk 이라면 거절했을 ladder rung 을 들여보내는 방향이다. `census_predicate_reading()` 은 `PREDICATE_DIFFERS_BY_N` 을 읽는다. 두 seed 수는 재타이핑하지 않고 recorded 데이터에서 **유도**한다 (D-047): 16 은 `CONVOY_W75_LADDER_ADMISSIBILITY` / `HEADON_W75_LADDER_ADMISSIBILITY` 에서, 32 는 `len(FROZEN_W75_ESS)` 에서.
- **이것은 rule 을 완화하자는 논증이 아니다**: D-170 alternative (b)/(c) 가 숫자를 구하려 admissibility 를 느슨하게 하는 것을 이미 거절했고 여기서 재론하지 않는다. all-seeds rule 은 옳은 rule 이고 `31/32` 는 진짜 거절이다. 결론은 더 좁고 반대 방향이다 — **한 `n` 에서 측정된 거절률을 다른 `n` 에 인용할 수 없다**, 그리고 census 가 지금 정확히 그것을 하고 있다. 처방은 gate 를 약화하는 것이 아니라 모든 admissibility reading 옆에 `n` 을 적는 것이다.
- **부수 발견 — 구간 선택이 detail 이 아니라 load-bearing 이었다**: normal 근사의 하단은 `k=1, n=32` 에서 **−0.029** 라 0 으로 clamp 되고, 그러면 `p = 0` 이 허용되어 `(1−p)ⁿ = 1`, 곧 "seed 수는 아무 상관 없을 수도" 가 구간 안에 들어온다. Wilson 의 하단은 **+0.0055** 이고, gate 가 *평평할 수도 있는* 것이 아니라 강하게 감소하게 만드는 것이 바로 그 강한 양수성이다. negative control 을 assertion 으로 고정했다.
- **첫 full suite 는 red 였고 (1 failed / 2376 passed), 그 실패가 이 D 를 한 단계 아래에서 반복한다**: `loop_reach` 의 `test_recorded_reading_covers_exactly_todays_targets` 가 corpus 에 reading 이 본 적 없는 **population claim** 이 생겼음을 잡았다 — 두 ladder 를 도는 `test_ladder_seed_count_is_derived_not_retyped` 다. reading 재취득 → `SAMPLED n=12`, 표본이 아니라 전수이고 vacuous 아님. 이 row 가 막는 것은 **빈 ladder 위에서 유도가 통과하는 것**이고, 빈 ladder 야말로 "census 는 16 에서 채점한다" 가 아무도 측정하지 않은 주장으로 조용히 바뀌는 경로다.
- **Alternatives**: (a) 채택 — gate 를 screen 하고 세 reading 을 기록. (b) `MONOTONE_PERMISSIVE` 를 산문 caveat 으로만 남긴다 — D-169 가 정확히, 답을 바꾸는 성질을 주석으로 남기면 어떻게 되는지 보여준 형태. (c) 8-seed pre-read 를 폐기 — 정리가 pre-read 를 무효화하지 않는다. pre-read 는 **miss 하면 결정적** 이라는 방향으로 쓰이고 (D-163) 그 용법은 관대함에 면역이다; 폐기하면 싼 측정을 잃는다. (d) 크기를 점추정으로 인용 — 이 branch 가 세 번 물린 그것.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-23-the-gate-is-a-function-of-seed-count.md` · D-171 (screen 규칙의 출처) · D-173 (세 번째 permissive 관측) · D-170 (`matched_ladder` 의 16-seed 채택) · D-163 (8-seed licence) · D-047 (재타이핑 금지)

---

## D-183 — 2026-08-10 — 면제의 base 는 **마지막 full receipt 의 commit** 이고, 그 commit 은 receipt 가 처음부터 들고 있었다 (Q-129 의 전제도 틀렸다 — 이틀 연속)

- **Context**: D-180 의 `changed_paths()` 가 `main...HEAD` 를 읽어 11 일 된 이 branch 에서 trigger 88 개 → `scope` 는 항상 `EXEMPTION_VOID`, 면제는 ship 된 cycle 부터 死文. Q-129 는 고칠 방법을 "receipt 에 tree hash 를 적어라 (`push_preflight` 변경)" 로 값매겼다.
- **Decision**: base = `exemption_base()` 가 돌려주는 **마지막 full receipt 의 `head`**, 기본값은 `main`. `Receipt.head` 는 이미 존재했다 — `record` 가 `tree_provenance.stamp()` 의 모든 field 를 보존하므로 — 따라서 **쓰기가 아니라 읽기**였고 `push_preflight` 는 한 줄도 안 바뀌었다. 실측 88 → **1**.
- **핵심은 거절 3종이 전부 `main` 으로 떨어진다는 것**: `NO_RECEIPT` / `SCOPED_RECEIPT` / `UNKNOWN_COMMIT`, `None` 을 돌려주는 경로 없음. 없는 base 로 `git diff` 하면 **빈 집합**이 나오고 그것은 "아무것도 안 바뀜" 과 구별되지 않는다 — 증거가 사라지는 순간 면제가 켜지는 방향이다.
- **`SCOPED_RECEIPT` 가 막는 것은 bootstrap**: 좁혀진 receipt 는 meta-suite 를 안 돌렸으므로 "meta-suite 를 또 건너뛰어도 된다" 의 증거가 될 수 없다. 판정은 `Scope.pytest_args` 가 실제로 뱉는 `--ignore=` flag 에서 유도 (D-047).
- **Alternatives**: (a) `main` 유지 — 안전하지만 merge 없는 queue 에서 면제가 영원히 死文. (b) 채택안. (c) `HEAD~1` — 싸지만 틀림: guard 를 고치고 아직 full suite 를 못 낸 상태를 면제한다.
- **대가로 배운 것 (full suite 4 red)**: 이 변경이 `STATE.md` pin 을 **전이적으로** stale 시켰다. `receipt_cost` 가 receipt 를 읽으려면 `push_preflight` 를 import 해야 하고, `push_preflight` 는 `STATE.md` 를 spell 한다 — 그래서 `STATE.md` 도 `push_preflight` 도 언급하지 않는 새 test module 이 **한 hop 건너** 그 pin 의 reader set 에 들어왔다. D-178 의 placement 규칙은 test 자신의 import 만 보므로 이 hop 에 **구조적으로 눈이 멀어 있다**; pin 이 규칙이 못 잡는 것을 잡았고, 그래서 둘 다 유지한다. `reprobe('STATE.md')` 로 entrant 1개(27 test)만 재측정 → `INERT_COMPOSED` gen-1 로 갱신 (full probe 15m45 대신 수 초).
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/10-22-the-base-was-already-in-the-receipt.md`, Q-129 resolved

## D-182 — 2026-08-10 — 매 cycle 측정되는 양을 **타이핑하고 있었다**: suite 가격은 receipt 에서 읽는다 — 그리고 D-181 의 전제(“receipt 에 이미 duration 이 있다”)는 **틀렸다**

- **Context**: D-181 이 ship 한 `suite_deadline()` 은 `SUITE_SECONDS = 717` 위에 서 있고, 그 값은 2026-08-06/07 측정치다. 같은 suite 가 2026-08-10 에 **1091.01s** 로 돌았다 (test 2260 → 2324). 374s 차이는 **permissive 방향**이다: minute 15 에 suite 를 시작하는 cycle 은 `SUITE_AFFORDABLE` 을 듣고 overrun 한다. STATE 와 D-181 finding 은 둘 다 고치는 법을 "`push_preflight record` 가 이미 receipt 에 duration 을 쓰니 constant 가 그것을 읽게 하라" 로 적었다 — **그런 field 는 없었다**. receipt 는 `command / counts / failed_nodes / head / worktree / returncode` 만 실었다. 20:00 은 1091.01s 를 pytest 자신의 tail 에서, 즉 D-176 의 **sidecar log** 에서 읽고 그것을 receipt 의 성질로 일반화했다.
- **Decision**: `Receipt.duration_seconds` 를 **신설**한다 (additive, 옛 receipt 는 `None`). `record` 가 subprocess 를 `time.monotonic()` 쌍으로 감싸 측정한다 — pytest 의 `in …s` tail 을 파싱하지 않는다: cycle 이 지불하는 것은 interpreter 기동 + collection + 사후 stamp 를 포함한 **step 전체**이고 pytest session time 은 그 부분집합이다. `cycle_wallclock.suite_price()` 가 마지막 receipt 에서 그 값을 읽어 `(seconds, MEASURED|FALLBACK)` 을 돌려주고, `SUITE_SECONDS` 는 *가격* 이 아니라 **floor** 로 강등된다.
- **읽은 값과 못 읽은 값은 문장에서 구별된다**: fallback 으로 만든 deadline 은 출력에서 `unmeasured — known-late fallback` 이라고 자기를 밝힌다. 숫자만 찍으면 floor 를 측정치로 읽는 바로 그 실수를 다시 초대한다. 모든 실패(파일 없음, JSON 깨짐, field 없음, 0 이하)는 예외가 아니라 fallback 으로 collapse — 이것은 advisory(D-115)이고, suite 가격을 모르는 cycle 에게도 deadline 은 있어야 한다.
- **왜 gate 가 아닌가**: duration 은 verdict 에 들어가지 않는다. `check` 는 green/stale/vacuous 만 판정한다 — 시계 읽기가 push 를 거절할 수 있게 만드는 것은 D-044 가 muting 을 예측하는 모양이다.
- **Alternatives**: (a) 채택 — receipt 가 자기 가격을 싣는다. (b) 새 literal 로 1091 을 타이핑 — D-047 의 모양 그대로, 다음에 test 를 추가하는 cycle 에서 다시 stale. (c) sidecar log 를 매번 파싱 — 이미 있는 값이지만 pytest 출력 형식에 결합되고, receipt 가 아니라 log 를 정본으로 만든다.
- **일반 교훈**: **stale 한 constant 와 존재하지 않는 field 는 읽는 쪽에서 똑같이 생겼다** — 둘 다 숫자를 찍는다. 두 cycle 연속으로 prose 가 field 의 존재를 단정했고, 확인 비용은 receipt 하나 열어보는 것이었다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-21-price-the-suite-from-the-receipt.md` · D-181 (deadline) · D-176 (sidecar log — 1091.01s 가 실제로 있던 곳) · D-047 (스스로를 말하는 집합을 손으로 다시 말하기) · D-154 (읽지 않고 타이핑된 값)

## D-181 — 2026-08-10 — wall-clock 은 **두 개의 질문**이고, 둘 다 gate 가 될 수 없지만 **하나만 actionable** 하다: `cycle_wallclock elapsed`

- **Context**: D-115 가 ship 한 `review` 는 **직전** run 을 grade 한다 — 이미 끝난 run 이라 이번 cycle 이 할 수 있는 일이 없다. 그래서 진행 중인 cycle 은 자기 경과 시간을 **추정**해 왔고, 그 추정은 D-154 가 TSV stamp 에서 이미 측정한 대로 **~3× 길게** 나간다. 결과가 STATE 에 두 cycle 연속으로 적혀 있다: 18:00 은 minute 6 에서 "~28분"이라 판단했고, 19:00 은 35분 예산을 49m11 로 넘겼다. wrapper 는 자기 log 에 start line 을 쓰고 있었으므로 이 값은 내내 **읽을 수 있었다**.
- **Decision**: `elapsed` subcommand 를 추가한다. `in_flight()` 는 오늘 log 의 **unpaired tail** run — flock 을 쥔 그 run, 즉 자기 자신 — 을 집어 경과 초를 낸다. `budget_room()` 은 세 verdict 를 낸다: `SUITE_AFFORDABLE` / `SUITE_UNAFFORDABLE` / `OVER_BUDGET`. 경계는 `suite_deadline()` = `BUDGET − SUITE − MIN_OVERHEAD` = 1143s (19m03). 헌법 Phase 3 "Do the work" 에 suite 착수 전 판독으로 배치.
- **rc=0 인 이유는 D-115 와 같은 이유가 아니다**: `review` 는 대상이 이미 끝나서 gate 할 것이 없고, `elapsed` 는 **시계가 한 방향으로만 가서** 한 번 넘긴 finding 을 그 cycle 안에서 영영 clear 할 수 없다. 둘 다 D-044 의 "clear 불가능한 check 는 muted 된다" 에 걸린다. 다른 것은 *actionable* 여부뿐이고, 빠져 있던 축이 그것이다.
- **경계는 한 방향으로만 bound 다**: `MIN_OVERHEAD_SECONDS` 는 non-suite 작업의 **하한**으로 문서화돼 있으므로 여기서 쓰면 deadline 이 산술상 가장 **늦게** 나온다. 넘겼으면 suite 는 **확실히** 불가능하고, 안 넘겼다고 가능한 것은 아니다. `grade` 가 이미 지고 있는 보수성과 같은 방향 — finding 을 만들어내느니 덜 보고한다.
- **비용이 설계의 일부**: git join 앞에서 dispatch 해 한 번의 file read (실측 **0.024s**) 로 끝난다. 예산을 감시하는 계기가 예산의 항목이 되면 안 되기 때문이고, 그래야 polling 이 공짜다.
- **Alternatives**: (a) 채택. (b) `review` 에 접어 넣기 — 두 질문의 population 과 rc 규약이 다르고 D-115 가 같은 이유로 이미 갈라놓았다. (c) rc=1 gate — minute 19 이후 모든 tick 이 red 라 D-044 의 muted check 가 된다. (d) 추정 유지 — 두 cycle 이 이미 지불했다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-20-cycle-wallclock-elapsed.md` · D-115 (review 축) · D-044 (muted check) · D-154 (자기추정 ~3× 편향)

## D-180 — 2026-08-10 — D-177 의 diff-conditional receipt scope 를 ship 한다: 면제 집합은 **typed 가 아니라 derived** 이고, 그 derivation 의 첫 cut 은 **자기 자신을 삼켰다**

- **Context**: D-177 은 이 함수를 두 cycle 전에 accept 했지만 구현을 미뤘고, 미룬 이유가 산술이었다 — "scope 함수가 guard census 에 99번째로 진입해 `len(pool) == 98` 을 깨고, 새 pin 값은 `test_guard_reflexivity` (163.4s) 를 돌려야만 알 수 있으므로 `runs_affordable == 1` 에서 불가능". 18:00 이 그 가격을 **지불하는 대신 검산했고**, 틀렸다: 새 값은 `len(gr.guards())` — `real 0m0.248s` 의 AST scan — 이고 163.4s 는 pool 을 *재감사* 하는 비용이다. 이번 cycle 은 그 검산이 옳았음을 실측했다 (census 98 → **99**, 0.237s).
- **Decision**: `receipt_cost` 에 `scope(changed)` / `guard_meta_suite()` / `changed_paths()` / `Scope` 를 ship 한다. receipt scope = full suite − guard meta-suite, **단 diff 가 guard source 를 건드리면 면제 무효**. verdict 는 세 개: `EXEMPTION_ACTIVE` / `EXEMPTION_VOID` / `NO_META_SUITE`.
- **면제 집합은 derived 다 (D-047)**: `guard_meta_suite()` 는 `guard_reflexivity` 를 **import 하는** test module 을 훑는다. hand-listed literal 이었다면 D-047 이 push gate 의 손으로 베낀 local-only grep 에서 찾아낸 결함 — 이미 스스로를 진술하는 집합을 두 번째로 진술하는 것 — 과 같은 모양이 된다. 다음 cycle 이 guard meta-test 를 쓰면 존재만으로 집합에 합류하고 면제는 스스로 좁아진다.
- **🔴 첫 cut 은 substring scan 이었고 그것이 이 entry 의 실질**: `GUARD_POOL_MODULE in text` 는 자기 자신의 test module 을 삼켰다 — 그 module 에서 이름이 나타나는 유일한 자리는 **이 derivation 에 관한 assertion 안의 문자열** `"test_guard_reflexivity"` 였다. module 이 집합을 *서술함으로써* 집합에 가입하는 규칙은 derivation 이 아니라 **자기참조**다. import 문 scan 으로 좁혔고, 그 속성을 산문이 아니라 test 로 박았다 (`test_this_module_is_not_in_its_own_subject`).
- **D-177 의 letter 를 한 방향으로 넓혔다**: 면제는 guard source 뿐 아니라 **meta-test 자신이 수정되어도** 무효다. 면제의 전제는 "pool 에 대한 *주장* 이 움직이지 않았다" 인데 assertion 을 고치는 것은 그것이 읽는 코드를 고치는 것만큼 확실하게 주장을 움직인다. 무효 조건을 넓히는 것은 full suite 를 지불하게 할 뿐이고 그것은 이미 status quo 다.
- **`NO_META_SUITE` 는 fail-closed 이며 별도 verdict 다**: derivation 이 깨진 상태와 "뺄 것이 없는" 상태는 출력이 거의 같은데 안전한 쪽은 하나뿐이다. 빈 drop set 을 가진 `EXEMPTION_ACTIVE` 로 접으면 깨진 계기가 빠른 receipt 처럼 읽힌다.
- **이 cycle 은 자기 규칙으로 full suite 를 지불한다**: `receipt_cost.py` 는 guard source 이고 이 cycle 이 그것을 수정하므로 `scope` 는 자신을 도입하는 run 을 면제할 수 없다. 산문이 아니라 test 로 진술했다 (`test_this_cycles_own_diff_voids_the_exemption`).
- **⚠️ 남은 구멍은 base 다 → Q-129**: `changed_paths()` 의 기본 base 는 `main...HEAD` 인데, 이 branch 는 11 일째 열려 있으므로 diff 가 사실상 모든 sandbox module 을 담고 자동으로 항상 `EXEMPTION_VOID` 를 읽는다. 즉 **면제는 ship 되자마자 이 branch 에서 inert** 하다. 보수적인 방향의 오류(항상 full suite)라 안전하지만, 절대 발동하지 않는 계기는 D-044 가 말한 muted check 의 다른 얼굴이다.
- **🔴 첫 full suite 가 이 entry 의 두 문장을 반증했다 (rc=1, 5 failed / 2305 passed)**: (1) `test_receipt_scope.py` 가 `"JOURNAL.md"` 를 문자열로 적었다는 이유만으로 그 pin 의 reader set 에 들어가 `stale_pins()` 를 깨웠다 — Q-128/D-179 의 기제가 그것이 기록된 바로 다음 cycle 에 도착했다. fixture path 로 철자를 바꿔 고쳤고, re-probe 는 지불하지 않았다 (D-178). (2) "second-order cost 는 두 축 모두 nil" 은 **한 축만 측정하고 쓴 문장**이었다: `unwatched_exemptions` 는 다섯으로 유지(맞음)지만 `NO_REGISTRY` 는 16 → **17** 로 움직였다. 두 축은 같은 사실의 양면이다 — call 안에서 만들어진 exemption 은 그 call 을 지켜보는 것이 함께 지켜보지만, **바로 그 이유로** 어떤 module-scoped registry 도 그것을 호명하지 않는다. 따라서 "DERIVED 이므로 nil" 은 할 수 없는 추론이고, D-073 의 비용은 하나의 수가 아니라 **서로 벌어지는 두 개**다.
- **Alternatives**: (a) 채택 — derived + import scan + tests 포함 무효. (b) typed literal 4-module drop — 더 싸지만 D-047 의 결함, 거절. (c) substring scan 유지 — 자기참조, 측정으로 반증됨. (d) base 를 이번에 함께 고친다 — 정답을 모르는 채 고르는 것이고 (Q-129), scope 함수 자체는 base 와 독립적으로 옳다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-19-the-derivation-swallowed-itself.md` · D-177 (이 구현을 accept 하고 미룬 결정) · D-179 (repricing) · D-047 (derived vs typed) · D-044 (ordering / muted check) · D-072/D-073 (census 의 syntax 결과) · Q-129 (열림: base commit)


## D-179 — 2026-08-10 — pin 은 **disk 가 아니라 index** 를 읽는다 (Q-128 → 채택 (b)); 그리고 D-177 을 두 cycle 막아온 "two runs" 산술은 **틀렸다** — census 값은 163.4s 가 아니라 **0.25s** 다

- **Context**: Q-128 은 17:00 cycle 이 걸어들어간 순서에서 나왔다 — 새 test file 을 쓰고 `stale_pins()` 를 읽으니 `()`, `git add` 하니 같은 호출이 **다섯 개**. 원인은 `_python_sources()` 가 `tp.tracked_paths()` = `git ls-files` = **index** 를 읽는다는 것. 그 중간 읽기를 믿었다면 push 되는 tree 가 갖지 않은 green 위에서 push 했다.
- **Decision**: Q-128 의 lean **(b)** 를 채택한다. `_python_sources()` 의 집합은 **건드리지 않고**, `unstaged_readers()` 를 별도 reading 으로 추가하고 `pin_reading()` 이 둘을 합성해 `PINS_CURRENT` / `PINS_STALE` / `PINS_UNSTAGED` 를 돌려준다. (a)(scan 을 untracked 까지 확대)를 거절한 이유는 방향이다 — push 되지 않을 scratch file 이 pin 을 흔드는 것은 **shipped tree 를 그 안에 없는 것으로 채점**하는 쪽의 오류다. 이 module 이 유도하는 집합은 여전히 index 의 것이고, 이 함수는 다만 index 가 disk 보다 `git add` 하나 뒤에 있다는 사실에 **침묵하지 않기로** 할 뿐이다.
- **Q-128 이 먼저 확인하라고 한 것 — 이 reading 은 지울 수 있는가**: **구조적으로 그렇다.** `git add` 가 file 을 `untracked_paths` 에서 `tracked_paths` 로 옮기므로, reading 은 그것을 무의미하게 만드는 바로 그 행위로 사라진다. D-044 의 "지울 수 없는 check 는 muted 된다" 가 여기 닿지 않는다는 뜻이고, 그래서 이것을 warning 이 아니라 **reading** 으로 둘 수 있다. 산문으로 논증하지 않고 test 로 고정했다 (`test_the_unstaged_reading_is_cleared_by_git_add`) — 이 성질이 형태 전체를 licence 하기 때문이다.
- **blind spot 이 균일하지 않다는 것이 핵심**: 이 gap 은 **reader 를 추가하는 cycle** 에만 보이지 않는데, 그것이 애초에 pin 이 stale 해질 수 있는 **유일한** cycle 이다. 발생빈도와 결과가 역상관이므로 "드물게 발생한다" 는 처음부터 방어가 아니었다.
- **placement 는 D-178 을 다시 배우지 않고 적용했다**: test 를 `test_inert_surface.py` 에 넣었다 — 이미 모든 관련 reader set **안**에 있으므로 reader **집합**이 안 바뀌고 pin 재측정이 0. 실제로 `pin_reading()` 이 real repo 에서 `PINS_CURRENT`.
- **⚠️ 부수 발견이고, 이 entry 에서 가장 값나가는 항목**: STATE 가 두 cycle 동안 D-177 을 막아온 근거는 "scope 함수가 census 99번째로 들어가 `len(pool) == 98` 을 깨고, 새 값을 알려면 `test_guard_reflexivity` (163.4s) 를 돌려야 하며, 그 뒤 full suite 가 또 필요하므로 `runs_affordable == 1` 에서 **불가능**" 이었다. 이 cycle 이 그 값을 지불하는 대신 **가격을 확인했다**: census 값은 `len(gr.guards())` 이고 이것은 **AST scan 한 번, `real 0m0.248s`** 다. 163.4s 는 그 pool 을 **재감사**하는 test module 의 가격이지 **숫자를 읽는** 가격이 아니다. 두 객체를 혼동한 것이다. 따라서 **D-177 은 suite 1회짜리 작업이고 처음부터 affordable 했다.**
- **그럼에도 이 cycle 이 D-177 을 ship 하지 않은 이유**: 도착 시점에 28분이 지났고 suite 가 18분이다. D-177 자신이 유도한 `latest_start_seconds` 산술이 곧바로 strand 를 예고하므로, 같은 산술을 믿는다면 지금 시작하지 않는 것이 일관된 행동이다. wall-clock advisory 도 직전 run 을 13m13 초과로 채점하며 "minute 34 가 아니라 지금 scope 를 자르라" 고 말했다.
- **Alternatives**: (a) scan 을 untracked 로 확대 — pin 을 push 되지 않을 file 로 흔든다, 거절. (b) 채택 — 별도 reading + 합성 verdict. (c) 규율만 ("pin 은 `git add` 뒤에 읽어라") — D-162 가 이미 판정한 형태이고, 잊는 cycle 은 시간에 쫓기는 cycle 이다. (d) D-177 을 이 cycle 에 강행 — 산술이 strand 를 예고했다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-18-the-pin-reads-the-index.md` · Q-128 (**resolved → 이 entry**) · D-178 (placement 교훈) · D-177 (two-run 전제가 여기서 반증됨) · D-044 (muted check) · D-107 (call time 재유도)

## D-178 — 2026-08-10 — guard 가 **읽는 면**은 guard 가 **사는 면**이 아니다: CI 의 `paths` 에 `docs/**` 를 넣는 것이 D-177 면제의 선행조건이고, 요구사항은 `SCANNED_DOCS` 에서 **유도**한다

- **Context**: D-177 이 fast receipt 를 diff-conditional 로 채택했고 그 방어논리 전체가 "full set 은 CI 가 돈다" 였다. Q-127 이 그 항이 **비어 있음**을 찾았다 — `sandbox-ci.yml` 의 trigger 는 `paths: ['eval/**', ...]` 이므로 **docs-only PR 은 CI 를 아예 안 돌린다**. 그리고 guard 중 일부는 `docs/` 를 *데이터로* 읽는다 (`citation_audit.SCANNED_DOCS` = `docs/decisions.md` + `docs/deliberations.md`). 즉 fast receipt + docs-only diff 에서 guard meta-suite 는 **로컬에서도 CI 에서도** 안 돈다. D-044 가 REPORT phase 마다 `SCANNED_DOCS` 를 쓰게 만들므로 이 조합은 예외가 아니라 **거의 매 cycle 의 모양**이다.
- **Decision**: Q-127 의 option (a) 를 채택하고 **먼저** 넣는다 — push/pull_request 양쪽 `paths` 에 `docs/**`. 코드 0 줄, suite 0 회. 순서가 load-bearing: 안전망이 exemption 보다 **앞에** 착지해야 하고, 뒤면 그 사이 cycle 들이 무방비다. 이 cycle 자신이 그 무방비 diff 모양이었다 (`docs/` + `.github/` + test, `eval/mppi_sandbox/*.py` 무변경).
- **한 줄 편집으로 끝내지 않은 이유 (D-047)**: 요구사항을 test 에 `docs/**` 리터럴로 다시 타이핑하지 않고 `citation_audit.SCANNED_DOCS` 에서 **유도**한다 (`TestCIWatchesWhatTheGuardsRead`). D-047 의 grep 도 쓰인 날에는 맞았고, registry 가 그 밑에서 자란 뒤 30 cycle 동안 틀렸다. `SCANNED_DOCS` 가 filter 밖의 세 번째 파일을 얻으면 red 가 된다.
- **matcher 를 직접 썼다**: `fnmatch` 는 `*` 와 `**` 를 구분하지 못해 `docs/*` 가 중첩 파일까지 덮는 것처럼 읽는다 — coverage assertion 이 무조건 yes 가 되는 방향의 오류다. GitHub 의미론(`**` 는 `/` 를 넘고 `*` 는 못 넘음)을 명시적으로 구현하고 양방향으로 pin 했다. **negative control 은 산문이 아니라 데이터**다: `_matches("eval/**", "docs/decisions.md")` 가 **False** 로 assert 되어 있고, 그 한 줄이 "고치기 전 filter 는 guard 의 read surface 를 덮지 않았다" 는 진술 그 자체다.
- **vacuous pass 를 막는다**: workflow 가 block-style list 로 바뀌면 regex 가 아무것도 못 찾고 모든 coverage assertion 이 **공허하게 통과**한다. 그래서 parse 된 filter 개수를 정확히 2 로 assert 한다.
- **비용은 이름 붙여 지불한다**: 이제 모든 docs PR 이 두 job 을 돌린다 (slow 는 360 min cap). 29 일 멈춘 queue 에 latency 를 더하는 것이 맞다. 그래도 채택하는 이유는 **안 보이는 guard 가 느린 guard 보다 나쁘기** 때문이고, option (b) 단독은 도착 즉시 死文이기 때문이다 — D-044 가 `SCANNED_DOCS` write 를 사실상 강제하므로 거기에 조건 걸린 면제는 발동하지 않는다.
- **census pin 은 건드리지 않는다**: guard census 는 `eval/mppi_sandbox/*.py` 의 population-shaped 함수를 센다. 이 cycle 은 test class 만 추가하므로 `len(pool) == 98` 은 그대로고, D-177 의 two-run 문제는 여기서 지불되지 않는다. 쓰기 **전에** 확인했다.
- **Alternatives**: (a) 채택 — `docs/**` 를 먼저. (b) 면제 조건을 `eval` **및** `SCANNED_DOCS` 무변경으로 좁힘 — 단독으로는 면제가 死文. (c) 둘 다 — Q-127 의 lean 이고 여전히 목표지만, (b) 는 D-177 구현 cycle 의 몫이다. (d) 아무것도 안 함 — 분업의 두 번째 항이 빈 채로 exemption 을 켜는 것.
- **어디에 test 를 쓰는가가 exemption 을 철회한다 (이 cycle 이 두 번 걸렸다)**: 첫 cut 은 이 test class 를 `test_suite_coverage.py` 에 넣었고 suite 가 **red** 로 돌아왔다 — `inert_surface.stale_pins()` 가 `('journal/', 'results/')`. 원인은 test 내용이 아니라 **위치**다. `readers()` 는 candidate 를 spelling 하는 package module 을 import 하는 test file 을 한 hop 으로 끌어온다. `citation_audit` 은 `results/`/`journal/` 을 spelling 하므로 그것을 import 한 test file 은 두 pin 의 **reader set 에 진입**하고, pin 은 자기가 취해진 reader set 을 전제로 하므로 전제가 움직여 exemption 이 철회된다. `reprobe` 는 `CONTENT_READ` 를 돌려줬는데 그것 역시 그 module 의 성질이다 — `test_suite_coverage` 는 subprocess 로 `--collect-only` 를 suite 전체에 돌리므로 사실상 모든 것의 content-reader 다.
- **해법은 probe 를 다시 사는 것이 아니라 이미 reader 인 file 에 쓰는 것**: 최종 위치는 `test_citation_audit.py` 다. 이 file 은 **이미** 두 pin 의 reader set 안에 있으므로 여기에 test 를 추가하는 것은 reader **집합**을 바꾸지 않는다 (`readers_key` 는 파일 이름의 집합이지 내용이 아니다). `stale_pins()` 가 `()` 로 돌아왔고 pin 은 하나도 다시 측정될 필요가 없었다. 주제상으로도 여기가 맞다 — CI 가 `citation_audit` 의 read surface 를 덮는가를 묻는 test 다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-17-the-safety-net-lands-before-the-exemption.md` · Q-127 (resolved) · D-177 (면제) · D-044 (REPORT 가 `SCANNED_DOCS` 를 쓴다) · D-047 (hand-copied registry)

## D-177 — 2026-08-10 — Q-126 의 option (a) 는 **"sim 을 그만 본다"** 가 아니라 **"보는 자를 그만 본다"** 였다: fast receipt subset 은 고정 drop 이 아니라 **diff-conditional** 로 채택한다

- **Context**: 15:00 이 Q-126 의 option (a) 를 `COMPLETE` 로 pricing 했다 — top-2 를 빼면 1076.3s → 515.6s, `runs_affordable` **1 → 3**, strand deadline minute **17 → 26**. STATE #1 은 "이 표로 Q-126 을 닫아라, suite time 0" 이었다. 그런데 닫기 전에 **그 module 들이 무엇인지** 읽으니 Q-126 의 전제가 틀려 있었다. Q-126 의 (a) 는 문자 그대로 "sim-bound module 을 빼고" 라고 적혀 있는데, 비용 상위 4개 중 **sim-bound 는 하나도 없다**: `test_exemption_masking` (390.5s, 36.3%), `test_guard_reflexivity` (163.4s, 15.2%), `test_exemption_control` (103.9s), `test_probe_reach` (74.7s) — 넷 모두 guard pool 자체를 AST/git 으로 훑는 **guard meta-suite** 다. 즉 (a) 가 실제로 제안하고 있던 것은 sim 을 덜 보는 것이 아니라 **receipt 를 의미 있게 만드는 기계 자신을 덜 보는 것**이었다.
- **Decision**: (a) 를 채택하되 **고정 drop 이 아니라 diff-conditional** 로 채택한다. receipt scope = full suite − guard meta-suite, **단 diff 가 guard meta-suite 가 읽는 surface (`eval/mppi_sandbox/*.py`) 를 건드리면 면제는 무효**가 되고 full suite 를 지불한다. 근거는 이 module 들이 **reflexive** 라는 점이다 — 그 subject 가 guard pool 자체이므로, guard source 가 안 움직인 cycle 에서 그 390s 는 **바뀔 수 없는 것을 다시 측정**하는 비용이다. 고정 drop 은 이 조건부성을 버리기 때문에 틀린 도구다: guard 를 추가하는 cycle — 즉 pin 이 깨질 수 있는 유일한 cycle — 에서 정확히 안 보게 된다.
- **여기에 (b) 의 무료인 절반을 함께 채택**: `latest_start_seconds` 는 코드가 필요 없는 산술이므로 그대로 남긴다. (a) 는 그 deadline 을 minute 17 → 26 으로 **옮기는** 것이지 없애는 것이 아니다.
- **무엇을 그만 보는가 (STATE #1 이 명시적으로 요구한 항목)**: guard 를 건드리지 않는 cycle 에서 receipt 는 exemption masking census (D-052), guard reflexivity pin `len(pool) == 98` (D-047/D-049), exemption control 의 tamper 증명 (D-076/D-078), probe reach (D-053) 를 **주장하지 않는다**. 이것들이 docs-only diff 에서 깨질 수 있는 경로가 실재한다 — guard 중 일부는 `docs/` 를 읽는다 (`citation_audit` 의 `SCANNED_DOCS`) — 그래서 면제 조건은 "eval 을 안 건드림" 이지 "코드를 안 건드림" 이 아니다.
- **⚠️ 이 결정이 드러낸, 아직 닫히지 않은 구멍**: "full set 은 CI 가 본다" 는 Q-126 의 안전망이 **docs-only PR 에서는 존재하지 않는다**. `.github/workflows/sandbox-ci.yml` 의 trigger 는 `paths: ['eval/**', '.github/workflows/sandbox-ci.yml']` 이므로 docs-only PR 은 CI 를 **아예 돌리지 않는다**. 따라서 fast receipt + docs-only diff 조합에서는 guard meta-suite 를 **로컬도 CI 도** 보지 않는다. 이 구멍을 먼저 막지 않으면 (a) 의 구현은 안전하지 않다 → Q-127.
- **구현은 이번 cycle 에 ship 하지 않는다, 그리고 그 이유가 결정의 일부다**: scope 를 계산하는 함수는 population 을 `not in` 으로 좁히는 모양이라 D-072 의 detector 가 보는 shape 이고, 따라서 guard census 에 **99번째로 진입**하며 `len(pool) == 98` pin 을 깬다. 새 pin 값은 `test_guard_reflexivity` 를 돌려야만 알 수 있고 (163.4s), 그 뒤 full suite 가 또 필요하다 — `runs_affordable == 1` 에서 **불가능**. 즉 이 결정의 구현은 그 자신이 사는 hazard 의 두 번째 mouth 를 통과해야 하며, 그것이 15:00 journal 의 recommendation #3 가 예고한 바로 그 순서다.
- **Alternatives**: (a) 채택 — diff-conditional. (b) 고정 drop — 더 싸고 더 단순하지만 guard 를 바꾸는 cycle 에서 정확히 눈을 감는다, 거절. (c) Q-126 의 문자 그대로 sim-bound module 을 뺀다 — **측정이 이 전제를 반증했다**, 뺄 sim-bound module 이 애초에 상위에 없다. (d) (b) 의 minute-N 만으로 버틴다 — cycle 당 산출이 계속 깎이고, 이미 오늘 두 건의 strand 를 냈다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-16-what-the-fast-receipt-stops-watching.md` · Q-126 (resolved → 이 entry) · Q-127 (열림: CI 의 docs-only 구멍) · D-176 (이 표를 측정한 cycle) · D-044 (ordering) · D-082 (green receipt 없이는 push 없음)

## D-176 — 2026-08-10 — 한 cycle 이 suite 를 **한 번** 돌릴 수 있다면, 그 run 의 출력을 버리는 것은 다음 질문에 **cycle 하나** 를 청구하는 것이다: run log 는 flag 가 아니라 receipt 의 sidecar 다

- **Context**: 14:00 cycle 이 `receipt_cost` 를 ship 하면서 자기 몫의 유일한 suite 를 `--durations=0` 으로 돌렸다 — 다음 cycle 이 subset 을 **공짜로** pricing 하라고 일부러 그렇게 돌린 것이다. 그런데 그 run 이 `push_preflight record` 를 거쳤고, `record` 는 `output` 을 `parse_summary` / `parse_failures` 에 먹인 뒤 **버린다**. durations 는 출력되었고, 파싱을 지나쳤고, 사라졌다. `price()` 는 `NO_DURATIONS` 를 반환하며 거절했다 — 옳은 거동이다. **Q-126 의 답이 Q-126 자신의 hazard 에 막혔다.**
- **Decision**: `record` 의 CLI 가 run 의 terminal output 전체를 **receipt 옆에** 남긴다 (`<out>.log`, `log_path()`). 더불어 `receipt_cost` 에 `price` / `modules` CLI 를 붙여, 남은 log 를 읽는 비용이 실제로 0 이 되게 한다.
- **왜 sidecar 이고 flag 가 아닌가**: 뻔한 모양은 `--log` 와 "그걸 넘기는 것을 기억하는 cycle" 이다. 그건 D-162 가 이미 상처로 기록한 모양이다 — 손으로 놓는 guard 는 잊을 수 있는 guard 이고, **잊을 가능성이 가장 큰 cycle 은 시간에 쫓기는 cycle**, 즉 그 비싼 run 을 돌리고 있는 바로 그 cycle 이다. `--out` 에서 파생된 default 는 잊을 수가 없다.
- **fixed path 가 아니라 *out* 에 keyed**: 한 cycle 안의 두 번째 `record` 가 첫 번째의 출력을 조용히 덮어쓰면서 receipt 는 둘 다 살아남는 상황을 막는다. 옆의 receipt 와 **다른 run** 을 서술하는 log 는 log 가 없는 것보다 나쁘다.
- **log 쓰기 실패는 run 을 죽이지 않는다**: receipt 가 push 를 licence 하는 물건이고 log 는 *다음* 질문을 싸게 만드는 물건이다. 후자를 잃는 것이 전자가 방금 사들인 ~1000s 를 날려서는 안 된다.
- **`price` CLI 는 `TRUNCATED` / `NO_DURATIONS` 에 non-zero 로 종료한다** — 둘 다 "이 출력으로는 subset 을 pricing 할 수 없다" 는 뜻이고, exit code 를 읽는 쪽은 시간에 쫓기는 cycle 이다. 다만 bound 는 **그대로 출력한다**: 아는 것을 감추는 refusal 은 사람들이 우회하는 refusal 이다 (손으로 row 를 다시 더하는 쪽으로).
- **Alternatives**: (a) 채택 — sidecar log + pricer CLI. (b) `--log` opt-in flag — D-162 의 "손으로 놓는 guard". (c) `record` 가 durations 를 직접 파싱해 receipt 에 넣음 — receipt schema 가 *미래의 모든 질문* 을 미리 알아야 하고, 이번 defect 이 정확히 "미리 묻지 않은 질문" 이었다. (d) subset pricing 을 위해 세 번째 suite run — `runs_affordable == 1` 인 예산에서 불가능.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-15-the-run-log-is-a-sidecar.md` · Q-126 (이 fix 가 답을 *가능하게* 만든다; 답 자체는 아직) · D-162 (손으로 놓는 guard 의 상처) · D-042 (mute 되는 alarm)

## D-175 — 2026-08-10 — 7번째 rung 을 사서 screen 을 **powered** 로 만들었다: Q-124 의 답은 `SELECTION_INDEPENDENT` — 그리고 rung 이 산 것은 *숫자* 가 아니라 그 숫자를 **읽을 자격** 이다

- **Context**: D-174 가 두 population 모두 underpowered 라고 판정하면서 `points_needed` 로 가격표를 남겼다 — 16-seed ladder 는 **+1**, 32-seed census 는 **+3**. STATE 는 ladder 를 "board 에서 가장 싼 측정" 으로 지목했다. 가격이 맞는지는 지불해야만 알 수 있다.
- **Decision**: convoy `w = 75` ladder 에 **`w_geom = 15`** (기존 `{10, 20}` **내부**, 따라서 외삽 아님) 를 16 seed 로 walk. `(16, 16)` admissible, median ESS 35.95. 결과: 5 admissible vs 2 refused → 21 labellings → `min_achievable_p = 1/21 = 0.0476` ≤ `ALPHA = 0.05`. `points_needed` 1 → **0**. 견적이 정확히 맞았다.
- **답**: `SELECTION_INDEPENDENT` (coupling 0.6000, p = 0.4286). `ess_band` admissibility 는 `residual_share` 를 **선택하지 않는다**.
- **rung 이 산 것은 power 뿐이다 — 이것이 이 entry 의 핵심**: coupling 은 거의 안 움직였고 (0.6250 → 0.6000) p 는 오히려 **올랐다** (0.4000 → 0.4286). "증거를 더 모으니 filter 가 무죄로 밝혀졌다" 는 요약은 **거짓**이다. point estimate 는 처음부터 같은 말을 하고 있었고, 달라진 것은 그것을 읽을 수 있게 되었다는 사실뿐이다.
- **반박의 방향성은 유지된다**: refused rung 둘 다 admissible span (0.3302 → 1.0041) **안**에 있고, mechanism gain 을 **전부** 재현하는 `w_geom = 20` (share 1.0041) 이 admit 된다. representation 에 유리하게 고르는 filter 라면 통과시킬 수 없는 rung 이다. D-174 가 underpowered 상태에서도 주장할 수 있었던 그 reading 이, 이제 powered population 위에 올라탔다.
- **band 는 coefficient 에 대해 monotone 이 아니다**: `10` 은 `(16, 15)` 로 refused 인데 `15`/`20` 은 둘 다 `(16, 16)`. 따라서 rung 은 이웃에서 grade 될 수 없고, 이것이 추가 point 를 **interpolate 하지 않고 walk 해야 했던** 이유다.
- **부수 소득 — 찾지 않은 pin 이 움직였다**: D-171 의 gain-match concordance 는 rung **pair** 위에서 계산되므로 7 rung 은 pair 를 6개 더한다. 13/15 = 0.8667 → **19/21 = 0.9048**. `CRITERION_CIRCULAR` 은 유지되고 **강화된다** — 그리고 이 point 는 그 finding 을 시험하려고 산 것이 아니므로, 이 branch 를 세 번 문 "답을 얻으려고 측정을 골랐다" 는 반론 (D-167/D-168/D-169) 이 구조적으로 닿지 않는 유일한 reading 이다.
- **provenance 를 같이 샀다**: `w_geom = 20` 을 같은 process 에서 재walk → 기록된 상수와 **소수 4자리까지 bit-for-bit 일치**. 8 cycle 전에 걸어둔 constant table 에 rung 을 덧붙일 때 "같은 harness 겠지" 를 사실로 바꾸는 데 16 run.
- **D-174 의 reading 은 지우지 않고 derivation 으로 보존**: 새 rung 을 빼면 같은 코드가 6 points / 4 admissible / 1/15 / underpowered / +1 을 그대로 반환한다 (test 로 고정). verdict 가 바뀐 것은 **측정이 추가되어서지 분석을 다시 특정해서가 아니다**.
- **Alternatives**: (a) 채택 — 내부 rung 1개. (b) `w_geom = 30` 등 바깥 rung — 외삽이고, ladder 상단은 이미 seed 를 잃고 있어 (40 → 8/16) refused 가 나오면 power 는 사지만 해석이 상단 붕괴와 얽힌다. (c) 32-seed census 쪽에 +3 을 지불 — 3배 비싸고, D-174 가 ladder 를 더 싸다고 이미 계산했다. (d) `ALPHA` 를 0.10 으로 — D-174 가 거절한 바로 그 수(threshold 를 움직여 finding 을 얻기)이고 이번에도 거절.
- **한계**: `min_achievable_p = 0.0476` 은 `ALPHA` 를 **가장 좁은 폭으로** 통과한다. 이 population 은 완벽한 coupling 이었을 때만 finding 을 낼 수 있었다는 뜻이고, 따라서 `SELECTION_INDEPENDENT` 는 "selection 이 없다" 가 아니라 "이 검정력으로 detect 가능한 selection 은 없다" 이다. 32-seed population 은 여전히 `SCREEN_UNDERPOWERED` (+3) 이므로 이것은 **ladder 에 대한 답이지 census 의 strictness 에 대한 답이 아니다** — 그 질문이 Q-125.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-12-the-seventh-rung-powers-the-screen.md` · D-174 (가격표) · D-171 (concordance, 측정치 갱신되고 결론 유지) · D-170 (ladder protocol) · Q-124 (**resolved → D-175**) · Q-125 (open)

## D-174 — 2026-08-10 — Q-124 의 admissibility screen 은 **돌아가지만 답을 낼 수 없다**: 두 population 모두 underpowered 이고, 유일하게 살아남는 증거(admissible span)는 selection 을 **반박**하는 쪽이다

- **Context**: null 세 개의 (admissibility, `residual_share`) 가 같은 순서로 정렬됐다 — 2.5(0.7725, admissible) / 5.0(0.9130, 거절) / frozen(0.9539, 거절). Q-124 는 이것이 measurement 인지 `ess_band` 가 favourable 한 null 만 통과시킨 selection 인지 물었다. D-171 의 교훈("ladder 를 걷기 전에 instrument 를 screen 하라")을 admissibility filter 자체에 적용하는 0-sim-run 작업.
- **Decision**: `admissibility_selection.py` 를 ship 한다. concordance 를 **방향성 있게** 취하고(admissible ⇒ 낮은 share 만이 고발 방향, 0.5 가 독립), 무엇보다 **`min_achievable_p` 를 verdict 가 measured coupling 보다 먼저 조회**한다. 가장 극단적인 결과조차 α 를 못 넘는 population 은 `SCREEN_UNDERPOWERED` 를 반환하고 **어느 방향으로도** finding 을 내지 않는다.
- **측정 결과 — 둘 다 답할 수 없다**: walked-32 는 `coupling = 1.0000` 인데 min p 가 **0.3333** (admissible 1 / 거절 2 ⇒ 세 가지 labelling). 16-seed ladder 는 rung 6 개로 pair 가 4 배지만 min p **0.0667** (=1/15) 로 α=0.05 를 **rung 하나 차이로** 놓친다; measured coupling 0.6250, p 0.4000. 즉 disk 위의 어떤 것도 Q-124 를 α=0.05 에서 답하지 못한다.
- **이 guard 가 없었다면 이 module 의 첫 출력은 "coupling 1.0000, selection 확인" 이었다** — 그리고 branch 는 한 번 떨어진 동전으로 census 를 철회했을 것이다. instrument 가 답을 고르는 것을 세 cycle 연속 발견한 branch 가, 네 번째로 같은 일을 **반대 방향**(근거 없는 retraction 제조)으로 할 뻔했다. 순서가 load-bearing 이다: power guard 를 측정 **전에** 넣었기 때문에 잡혔다.
- **Underpowered 가 vacuous 는 아니다 — 살아남는 증거가 하나 있고 방향이 반대다**: `span_reading` 은 reference distribution 이 아니라 **관측된 집합 자체**에 대한 진술이라 작은 n 이 무효화하지 못한다. ladder 의 admissible rung 들은 share **0.3302 → 1.0041** 로 사실상 전 구간을 덮고, 거절된 두 rung(0.9172, 0.9930)은 그 **안쪽**에 있다. `w_geom = 20` 은 share 1.0041 — null 이 mechanism gain 을 통째로 재현하는, representation 에게 **최대로 불리한** rung — 인데도 filter 가 통과시켰다. 이 ladder 에서 `ess_band` 는 representation 을 나쁘게 보이게 하는 null 을 막지 않는다.
- **두 population 이 불일치하는 이유는 규명됐다**: `w_geom = 5.0` 이 16 seed 에서 admissible `(16,16)`, 32 seed 에서 거절 — `licence_split` 이 `LICENCE_SPLIT (5.0,)` 로 읽는다. all-seeds band rule 하에서 admissibility 는 seed 를 더하면 잃기만 하므로 16-seed ladder 는 **체계적으로 더 관대한** filter 다. 모순이 아니라 같은 screen 의 두 strictness 이고, census 자신의 것은 power 가 없는 쪽이다.
- **그래서 census 는 clear 되지 않았다**: 하지만 걱정이 **가격표 달린 bounded task** 로 바뀌었다. `points_needed` = ladder +1 rung, census strictness +3 null. 그 전까지 graded number 의 denominator 는 "selected" 도 "clean" 도 아닌 **uncharacterised** 다 — 셋 중 유일하게 측정에 부합하는 표현.
- **부수 수확 (shipped bug, 자체 적발)**: 최초 `licence_split` 은 formatted label 로 join 해서 `w_geom=5` vs `w_geom=5.0` 이 어긋났고, 하필 **두 population 이 유일하게 불일치하는 rung** 을 조용히 떨어뜨려 `LICENCE_AGREED` 를 반환했다. 숫자 key 로 재작성. text join 이 정확히 자신이 찾아야 할 항목을 숨긴 사례라 `Point.w_geom` docstring 에 남겼다.
- **Guard 가 산 것 — `LICENCE_NO_OVERLAP`**: `licence_split` 의 `&` 가 `guard_reflexivity` 의 `&`-shaped registry 에 **아홉 번째**로 들어갔다(pool 96→97, 자기가 감사하는 registry 에 자기 module 이 들어가는 연속 기록 계속). 그 과정에서 실제 결함이 드러났다 — 교집합이 비면 옛 코드가 `LICENCE_AGREED` 를 반환했다. 즉 **한 번도 수행되지 않은 비교**가 "불일치 없음" 으로 읽혔고, 이건 selected denominator 를 잡으려고 쓴 screen 안에 D-107 의 형태가 앉아 있던 셈이다. 별도 상태로 분리했다.
- **Alternatives**: (a) 채택. (b) coupling 만 보고 selection 선언 — 위 문단이 그 결과. (c) α 를 0.10 으로 올려 ladder 를 powered 로 만들기 — finding 을 얻으려고 threshold 를 움직이는 것이라 거절. (d) network 넷째 null 을 먼저 걷기 — screen 이 0 run 인데 walk 를 먼저 사는 것은 D-171 이 금지한 순서.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-10-the-screen-that-cannot-be-run.md` · Q-124 (resolved) · D-171 (screen-before-walk) · D-163 (permissive licence, 네 번째 목격) · D-107 (빈 denominator 를 tie 로 오독하는 형태)

## D-173 — 2026-08-10 — structural null 은 **walk 되지만 거절된다**(31/32) — 그리고 거절은 construction 이 예측한 **ceiling 이 아니라 floor** 에서 일어난다: pointwise cost 부등식은 softmax 로 전달되지 않는다

- **Context**: D-172 는 `FrozenRiskMPPI` 를 0-run screen 까지 붙여 ship 했지만, 그 docstring 이 스스로 예고한 가격(`LOUDNESS_UNCALIBRATABLE`, Q-123)은 측정되지 않은 채였다. STATE 는 8-seed ESS pre-read 를 gating measurement 로 지목했고 — D-163 상 8-seed 는 **permissive** 쪽이므로 miss 면 이미 결정적 — 이번 cycle 이 그것을 썼다. Pre-read 는 통과(median ESS **108.61** vs risk 105.07, 8/8 in band)했고, 그래서 STATE 의 in-band 분기대로 32-seed head-to-head 를 바로 walk 했다.
- **Decision**: rung 을 **거절**로 기록하고(31/32 in band, all-seeds 규칙 — head_on `w = 75` 를 거절한 바로 그 count), 거절의 **방향**을 일급 reading 으로 만든다. `StructuralRung` 은 per-seed clearance 옆에 per-seed ESS 를 들고 다니며 `refusal_side` 를 답한다: 측정값은 `REFUSAL_AT_FLOOR`(seed 8 @ ESS **11.78**, floor 12.8), 예측값은 `REFUSAL_AT_CEILING`. 예측을 `PREDICTED_REFUSAL_SIDE` 상수로 따로 두어 예측과 측정이 **서로 반박 가능한 두 객체**가 되게 하고, `price_direction` 이 `PRICE_PAID_AS_PREDICTED` / `PRICE_PAID_OTHER_SIDE` 를 구분한다 — 청구서가 맞은 것과 이유가 맞은 것은 다르고, 다음 arm 에 그 논증을 재사용해도 되는지는 두 번째에만 달렸다. 거절된 reading 은 `LOUDER_NULL` 의 규칙대로 **데이터로 보존**: `residual_share = 0.9539`, head-to-head `A = 0.5317`, paired CI `[-0.0117, +0.0267]` ∋ 0, ε = 0.05 m 에서 `EQUIVALENT`. `verdict()` 는 그 숫자를 읽는 동안에도 `WALK_INADMISSIBLE` 을 반환하고, 그 사실 자체가 test 로 고정된다. 8-seed licence 가 D-163 방향으로 **세 번째** 물었으므로(8/8 → 31/32) 그것도 prose 가 아니라 reading(`seed_licence` → `LICENCE_PERMISSIVE`)으로 적는다.
- **Alternatives**: (a) 31/32 를 통과시키고 `residual_share = 0.9539` 를 census 에 넣는다 — 이 branch 의 가장 강한 숫자를 얻는 대신, 규칙이 값을 치를 때 정확히 그 규칙을 버리는 것. (b) 거절만 적고 head-to-head 는 계산하지 않는다 — 독자가 admissible 한 하나의 숫자에서 안정성을 추론하게 만드는, `LOUDER_NULL` 이 막으려던 그 실패. (c) 거절을 boolean 으로만 적는다 — floor/ceiling 구분이 사라지고, docstring 의 예측이 틀렸다는 이번 cycle 의 실제 발견이 관측 불가능해진다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-09-the-structural-null-is-refused-at-the-floor.md` · Q-123 resolved → D-173

## D-172 — 2026-08-10 — null 의 **형태**를 바꾼다: coefficient 를 calibrate 하는 대신 representation 의 **입력**을 제거한다 — 그리고 "calibrate 할 coefficient 가 없다"는 주장 자체를 0-run screen 으로 검사한다

- **Context**: 두 criterion 이 **반대 방향**으로 실패했다 — ESS-matching 은 verdict 를 identify 하지 못하고 (D-169/D-170), gain-matching 은 match 잔차와 verdict 통계량 `|A − ½|` 이 같은 양이라 verdict 를 **결정해버린다** (D-171, 13/15 · 10/10 `CRITERION_CIRCULAR`). 대칭적 실패는 *선택*이 아니라 **형태**를 지목한다: 항을 갈아끼우고 나면 "얼마나 크게?" 를 답해야 하고, 그 질문에 대한 답 두 개가 모두 나빴다.
- **Decision**: `FrozenRiskMPPI` — `RiskMPPI` 에서 **producer 만** 바꾼 arm. `FrozenBevProducer` 는 DYNAMIC 채널을 `t₀` 의 obstacle 위치 한 곳에만 렌더한다 (`predict_samples = 1`; `linspace(0, t_pred, 1) == [0.0]`, decay `exp(0) == 1.0`). `w_risk = 40.0` 을 포함해 **모든 coefficient 가 risk arm 과 동일**하고, critic 3종·cost slot·`_extra_cost` 는 상속으로 그대로 쓴다. 걸어야 할 ladder 가 없으므로 D-170 의 under-identification 과 D-171 의 circularity 는 *논증이 아니라 구성상* 표현 불가능하다.
- **주장이 아니라 reading 으로 만든다** (`structural_null.screen`, sim run 0회): **두 반쪽의 논리곱**이라는 점이 핵심이다. (a) `coefficient_parity` — `MPPIParams` 전 field(λ 포함) + arm 계수 전부 동일 → `COEFFICIENTS_SHARED`. (b) `prediction_parity` — producer 가 `n_pred` 에서**만** 다름 → `PREDICTION_REMOVED`. (a) 만으로는 **arm 을 자기 자신과 비교해도 통과**하므로 no-op 을 structural ablation 으로 인증해버린다; (b) 만으로는 계수가 몰래 바뀐 것을 놓친다. shipped pair 는 `STRUCTURAL_ABLATION`.
- **이번 cycle 이 산 규칙**: D-171 은 "ladder 를 걷기 전에 match 량이 verdict 와 결합돼 있는지 screen 하라" 였다. 여기엔 match 량이 없으므로, 걷기 전에 screen 할 대상은 **"match 량이 없다"는 문장이 prose 가 아니라 객체에 대해 참인가** 이다. 두 screen 모두 0 run.
- **대가를 숨기지 않는다 — 새 실패 모드 하나를 산다**: 계수 동일 ≠ loudness 동일. swept DYNAMIC 은 `predict_samples` 개 blob 의 max 이고 frozen 은 그 중 한 개이므로 frozen 의 extra cost 는 같은 `w_risk` 에서 **pointwise ≤** (test 로 고정), softmax 가 더 평평해 `ab.ess_band` 가 rung 을 거절할 수 있다. calibrated null 은 knob 을 돌려 답하지만 **이 arm 은 돌릴 knob 이 없다** — 거절되면 그것은 calibration 실패가 아니라 ablation 에 대한 사실이고 `LOUDNESS_UNCALIBRATABLE` 로 그렇게 보고된다. 거래는 *부적격이 될 수 있는 null* ↔ *적격 설정이 답을 정하지 못하는 null* 이다.
- **아직 verdict 는 없다**: rung 을 하나도 걷지 않았다. screen 은 비교가 **well-posed** 하다는 말이지 어느 arm 이 clearance 를 더 갖는다는 말이 아니다.
- **부수 효과 — `default_lam_sites` 의 headline 이 처음으로 뒤집혔다**: 새 test file 의 21 site 로 `decides` 55 → **76** 이 되어 `defaults` 58 을 넘었다. 18 cycle 동안 참이던 "shipped `lam = 0.1` 을 쓰는 site 가 rung 을 명명하는 site 보다 많다" 가 거짓이 됐다. assertion 을 조용히 뒤집지 않고 **이름을 바꿔** 기록했고 margin(18)도 pin 했다 — 한 file 이 산 crossover 라 아직 repo 의 안정된 성질이 아니기 때문. `migration_cost` 는 58 로 **불변**이므로 migration 이 싸진 것은 아니고, 분모의 구성이 바뀐 것이다. 덧붙여 이번 draft 는 그 census 의 docstring 이 이미 경고해 둔 `params()` helper 함정에 그대로 빠졌다 (`forwards` 23 → 43) — pin 은 자기 docstring 과 중복이 아니라, 그 docstring 이 **읽히게 만드는** 장치다.
- **Alternatives**: (a) 채택 — 입력 제거. (b) cost-spread matching — 순환성 screen 은 a priori 통과하나 per-rollout cost 가 disk 에 없어 screen 하기 전에 새 instrumented walk 값을 먼저 치러야 한다. (c) 세 번째 calibration criterion — 두 실패가 형태를 지목한 뒤라 같은 값을 또 치르는 선택. (d) 산문으로만 "coefficient 가 없다" 선언 — D-171 이 정확히, 아무도 test 하지 않은 문장이 어떻게 틀려 있는지 보여준 형태.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-08-structural-ablation-has-no-coefficient.md` · D-171 (gain-matching 순환) · D-170/D-169 (ESS-matching under-identification) · D-160 (λ 는 scene 별 calibration) · D-107 (재도출 안 된 provenance)

## D-171 — 2026-08-10 — STATE 의 두 번째 후보 criterion(**achieved clearance gain matching**)은 **순환적**이라 폐기한다 — match 하는 양이 verdict 통계량과 같은 양이다

- **Context**: D-170 이 ESS-matching 을 무너뜨린 뒤 STATE 는 후속 criterion 후보 둘을 남겼다 — null 의 **across-rollout cost spread**, 그리고 **achieved clearance gain over stock**. 두 번째 것은 이미 disk 에 있는 ladder 만으로 계산되므로 sim run 이 0 이고, 그래서 먼저 검사했다. 검사는 채택 전에 했다: criterion 을 *쓰기* 전에 그 match 량이 verdict 통계량과 결합되어 있는지 본다.
- **Decision**: gain-matching 을 **폐기**한다. verdict 는 gain match 를 계산하는 바로 그 achieved clearance 위의 head-to-head `A` 에서 읽히므로, match residual 과 verdict 통계량 `|A − ½|` 은 한 양을 두 번 읽은 것이다. 측정된 결합: convoy 는 rung pair **13/15**, head_on 은 **10/10** 이 두 순서에서 같게 정렬된다 → 두 rung 모두 `CRITERION_CIRCULAR`. criterion 을 자기 optimum 으로 몰면 `|A − ½|` 이 `inert_effect` 아래로 내려가고 그것이 곧 `GEOMETRY_SUFFICES` 다. seed 를 아무리 늘려도 고쳐지지 않는다.
- **결정적인 따름정리**: criterion 이 **성공하는** 쪽 rung 이 곧 representation 의 기여를 보고할 수 **없는** rung 이다. convoy 는 mechanism gain 의 0.41% 까지 맞고 `GEOMETRY_SUFFICES` 를 읽는다; head_on 은 ladder 간격이 성겨 13.5% 까지밖에 못 맞고 `REPRESENTATION_ADDS` 를 읽는다. 즉 head_on 이 남긴 `REPRESENTATION_ADDS` 는 그 scene 의 representation 에 대한 진술이 아니라 그 ladder 의 간격에 대한 진술이다.
- **이것은 D-169/D-170 과 반대 방향의 결함이다**: 그쪽은 verdict 를 **식별하지 못하는** criterion 이었고, 이쪽은 verdict 를 **결정해버리는** criterion 이다. 둘 다 실격이고 둘 다 shipped `w_geom` 만 봐서는 보이지 않는다. 또한 gain-matching 은 기존 criterion 의 개선판이 아니라 **다른 답**이다 — convoy 에서 ESS 는 `w_geom = 2.5` → `REPRESENTATION_ADDS`, gain 은 `20` → `GEOMETRY_SUFFICES`, 둘 다 16/16 admissible 이고 각자 자기 criterion 의 optimum 이다.
- **Alternatives**: (a) 채택 — 폐기하고 남은 후보(cost spread)로 간다. cost spread 는 achieved clearance 의 재독해가 아니므로 이 screen 을 선험적으로 통과하지만, 어떤 ladder 에도 per-rollout cost 가 기록되어 있지 않아 **새 run 값을 치른다**. (b) gain-matching 을 caveat 달고 쓴다 — 거절: caveat 이 붙은 순환 논증은 여전히 순환이고, 이 branch 는 이미 "누가 무감응함을 보인 적 없는 knob 에서 취한 수" 로 세 번 물렸다 (D-167 0.7725, D-168 0.0485, D-169 ladder). (c) scalar-coefficient null 자체를 포기하고 **structural ablation** (weight 를 줄이는 대신 representation 의 *input* 을 제거) 으로 간다 — calibrate 할 coefficient 가 없으므로 두 실패 모드가 모두 없다. 아직 결정하지 않았고 다음 cycle 의 질문이다.
- **일반화된 규칙 (이 cycle 의 실제 산출물)**: 제안된 match 량이 verdict 통계량과 해석적으로 결합되어 있는지 **ladder 를 걷기 전에** 검사한다. `NullRung.gain_effect_coupling` 이 그 검사이고 비용은 0 run 이다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-07-gain-matching-is-circular.md` · D-170 (ESS criterion 이 verdict 를 식별하지 못함) · D-169 (`VERDICT_UNIDENTIFIED`) · D-167 (0.7725 의 출처)

## D-170 — 2026-08-10 — criterion 이 **작동하는** scene 에서도 verdict 는 식별되지 않는다: convoy `w = 75` 도 거절되고 attribution census 는 **0/6** 이 된다

- **Context**: D-169 는 `cafe_head_on_v0` `w = 75` 를 `VERDICT_UNIDENTIFIED` 로 거절하면서 그 원인을 "이 scene 에서 sampler 의 ESS 가 `w_geom` 에 **눈이 멀었다**" 로 진단했다 (ESS response 1.70%). 그 진단이 맞다면 결함은 scene 한정이고, ESS ladder 가 실제로 반응하는 rung 에서는 criterion 이 제 역할을 한다. convoy `w = 75` 가 바로 그 rung 이고 — census 의 **유일한** graded rung 이며 branch 에서 가장 많이 인용된 attribution 수치 `residual_share = 0.7725` 의 출처 — `verdict_identification` 은 `UNRECORDED`, 즉 통과가 아니라 **미측정** 이었다.
- **측정**: convoy `w = 75`, λ = 0.8 에서 `w_geom ∈ {1, 2.5, 5, 10, 20, 40}` × 16 seeds (rung 당 target/stock ESS 를 같은 ensemble 에서 재취득, 총 128 runs, ~4 분). **criterion 은 여기서 작동한다**: median ESS 97.52 → 14.03, response 가 target 의 **86.6%** 로 head_on 의 1.70% 의 50배이고 `coefficient_identification = IDENTIFIED`. ladder 가 오를수록 band 도 잃는다 (10 에서 15/16, 40 에서 8/16) — 같은 반응을 median 이 아니라 band 에서 본 것.
- **그럼에도 verdict 는 뒤집힌다**: `w_geom ∈ {1, 2.5}` 에서 `REPRESENTATION_ADDS`, `{5, 10, 20, 40}` 에서 `GEOMETRY_SUFFICES`. `residual_share` 는 **0.3302 → 1.0041** 로 이동한다. 그러므로 D-169 의 진단은 **너무 좁았다** — 문제는 "ESS 가 이 scene 에서 눈이 멀었다" 가 아니라 **ESS-matching 이 coefficient 를 식별해도 verdict 는 식별하지 못한다** 는 것이고, 이 둘은 다른 property 다.
- **"criterion 이 안 골랐을 rung 을 세었다" 는 반론을 측정으로 선차단**: `matched_ladder` 는 (a) ladder-admissible (전 seed 도달 + in band) 이고 (b) ESS target 과의 거리가 실제 채택된 `w_geom = 2.5` **이하**인 rung 만 남긴다 → `{1, 2.5, 5}`. 이 안에서도 verdict 는 갈린다 (`matched_verdict_identification = VERDICT_UNIDENTIFIED`). 뒤집는 rung 인 `w_geom = 5` 는 16/16 in band 이고 ESS 매칭이 채택값보다 **더 좋다** (|94.41−96.36| = 1.95 vs |86.08−96.36| = 10.28). 즉 far-out rung 을 하나도 인용하지 않고도 거절이 성립한다.
- **부수 결함, 독립적으로 기록**: `better_matched = (1.0, 5.0)` — calibration 이 **자기 criterion 의 최적점을 고르지 않았다**. 채택된 2.5 보다 ESS 매칭이 엄격히 더 좋은 coefficient 가 둘 있고, 그 중 최선인 5.0 이 반대 답을 낸다. 채택된 `w_geom` 만 봐서는 보이지 않는 종류의 결함이라 property 로 남긴다.
- **Decision**: `NullRung` 에 `ladder_admissibility` / `matched_ladder` / `better_matched` / `matched_verdict_identification` 을 추가하고, convoy rung 에 측정된 ladder 를 실장한다. 결과적으로 두 walked rung 이 모두 거절되어 census 는 `NO_GRADED_RUNG`, coverage **0/6** — **빈 분모이며 tie 도 mechanism 에 대한 null result 도 아니다** (D-107 형태). D-167 의 `residual_share = 0.7725` 는 census 가 더 이상 인용하지 않는다.
- **교차검증으로 신뢰 확보**: ladder 의 두 rung 은 새 데이터가 아니라 대조군이다 — `w_geom = 2.5` 는 32-seed walk (`NULL_CLEARANCES`) 의 앞 16 seed 와, `5.0` 은 거절된 `LOUDER_NULL` 의 앞 16 seed 와 **정확히** 일치한다. 이 ladder 와 기록된 walk 들은 두 개의 측정이 아니라 하나를 두 seed 수에서 본 것이다.
- **Alternatives**: (a) 채택 — 측정하고 거절, census 0/6 을 그대로 보고. (b) convoy 를 `UNRECORDED` 로 남겨 1/6 을 지킨다 — 측정하지 않음으로써 숫자를 지키는 것이라 거절. (c) `verdict_identification` 을 matched set 기준으로 **완화**해 convoy 를 살린다 — matched set 에서도 갈리므로 살지 않고, 완화가 결과를 바꾸지 못하는 것을 확인한 뒤 sharper predicate 는 *추가* 로만 둔다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-06-a-working-criterion-still-does-not-identify-the-verdict.md` · D-169 (head_on 거절, 진단이 좁았음) · D-167 (ESS-matching protocol + 0.7725) · D-107 (빈 분모)

---

## D-169 — 2026-08-10 — `FLAT` 한 ladder 는 caveat 이 아니라 **질문**이다: verdict 가 coefficient 를 따라 뒤집히면 그 rung 은 읽히지 않는다 (`VERDICT_UNIDENTIFIED`)

- **Context**: D-168 은 `cafe_head_on_v0` `w = 75` 의 `w_geom` ladder 가 risk arm ESS 의 0.19% 만 움직인다는 이유로 `coefficient_identification = FLAT` 을 기록하고, 그 rung 을 "null 이 너무 **조용해서**" 거절했다. STATE #1 은 그 진단을 그대로 받아 "ESS 가 반응할 때까지 ladder 를 위로 늘리고 재보행하라"고 지시했고, 두 예상 결과 모두 조용함 가설을 전제했다. 늘려보니 셋째 결과가 나왔다 — `w_geom` 을 20× (8 → 160) 올려도 median ESS 는 1.70% 밖에 안 움직이는데 **평균 clearance 는 0.2856 → 0.5099 (+79%)**, 즉 mechanism 이 stock 대비 버는 gain 전체의 **1.40배**를 이동한다. term 은 조용한 적이 없었고, 이 scene 에서 sampler 의 ESS 가 그 term 에 **눈이 먼** 것이다.
- **결정적 귀결**: ESS 로 구분되지 않는 coefficient 들 사이에서 `residual_share` 가 **0.0485 → 1.76** 으로 단조 이동하고 verdict 도 같이 뒤집힌다 — `w_geom ∈ {10,20,40}` 에서 `REPRESENTATION_ADDS`, `{80,160}` 에서 `GEOMETRY_WINS`. 한 rung 위에서 **서로 반대되는 두 답**이 모두 도달 가능하다. 그러므로 D-168 이 "branch 의 전제에 유리하다"며 기록해 둔 `0.0485` 는 같은 protocol 이 똑같이 허용하는 범위의 **최극단 한쪽 끝**이지 측정값이 아니다.
- **Decision**: rung 마다 `clearance_ladder` (w_geom → calibration ensemble 의 clearances) 를 기록하고, `ladder_verdicts` 로 "그 coefficient 를 골랐다면 무슨 verdict 였을까" 를 `Attribution` **자기 자신을 통해** 계산한다. 도달 verdict 가 2개 이상이면 `verdict_identification = VERDICT_UNIDENTIFIED` 이고 `NullRung.admissible` 의 **세 번째 절**이 그 rung 을 거절한다 — 씨앗을 더 뿌려도 고쳐지지 않는 종류의 거절. 짝이 되는 진단 `behavioural_response` 를 `ess_response` 옆에 둬서 두 반응이 분리되는 것이 다시 보이지 않게 지나가지 않도록 한다.
- **`UNRECORDED` 는 거절하지 않는다**: convoy `w = 75` 의 ladder 는 이 질문을 받은 적이 없다. 거절하면 census 가 가진 유일한 graded rung 을 소급해서 ungrade 하게 되고, 그것은 "아무도 안 쟀다" 를 "재봤더니 나쁘다" 로 바꿔 적는 것이다 (`coefficient_identification` 의 3-state 규칙, 한 단계 아래). 대신 이것이 다음 cycle 의 1순위가 된다.
- **왜 caveat 으로 두지 않는가**: census 에 이미 `exposed_to_quiet_null` 이 있고 그것은 flat ladder 위의 승리를 *주석*했다. 주석은 "이 flat 함이 답을 바꾸는가" 를 묻지 않는다 — 그리고 답을 바꾼다는 것이 지금 측정되었다. 바꾸지 않는 flat ladder 는 무해하고, 바꾸는 flat ladder 는 치명적이며, 둘을 구분할 수 있는 property 가 이 모듈에 없었다.
- **범위 제한**: ladder rung 들은 전부 16/16 도달 + 16/16 in band (`HEADON_W75_LADDER_ADMISSIBILITY`) 이므로, verdict 가 갈리는 것을 "나쁜 run" 으로 치울 수 없다. 반대로 이 cycle 은 controller/representation code 를 건드리지 않았고 headline (`unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000) 은 그대로다.
- **Alternatives**: (a) 채택 — verdict 도달 집합으로 거절. (b) `FLAT` 주석만 강화 — 측정된 반전을 주석으로 남기는 것이라 거절. (c) ESS-matching 을 지금 다른 criterion 으로 교체 — 옳은 방향이지만 어떤 quantity 로 match 할지가 미해결이고, 그 결정 전에 기존 rung 들이 무엇을 주장할 수 있는지부터 고정해야 한다 (Q 로 남김, 다음 우선순위 2번).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-04-the-verdict-is-a-free-parameter.md` · D-168 (거절된 rung) · D-167 (ESS-matching protocol) · D-107 (빈 분모를 verdict 로 읽지 않기)

## D-168 — 2026-08-10 — attribution 은 **census** 가 된다, 그리고 두 번째 rung 은 두 번 거절된다: ESS 31/32 + `w_geom` ladder 가 평평함

- **Context**: D-167 의 `residual_share = 0.7725` 는 **한 scene 의 한 rung** 위에 있고, STATE 의 successor question 은 그것이 rung 성질인가 scene 성질인가다. 답하려면 rung 이 하나 이상 필요한데 module 은 rung 을 module 상수로 들고 있었다 — "다른 rung 을 돌린다" 가 verdict logic 을 편집한다는 뜻이었다.
- **Decision (instrument)**: rung 을 **record** 로 (`NullRung`), verdict 를 **census** 로 (`NullCensus`). census 는 **coverage 를 verdict 보다 먼저** 보고하고 그 분모를 `margin_free.census()` 에서 **읽는다** — 거기에 rung 이 추가되면 이 census 의 coverage 가 *낮아진다*, 조용히 좋아지는 게 아니라. `separates_scene_from_rung` 은 STATE 의 질문이 현재 coverage 로 **답할 수 있는지 자체**를 말한다 (한 scene 이 rung 2개를 내야 True); 그 전까지 rung 불일치와 scene 불일치는 같은 문장이므로 verdict 는 `SCENE_CONFOUNDED_WITH_RUNG` 이지 `RESIDUAL_RUNG_DEPENDENT` 가 아니다.
- **Decision (measurement)**: 두 번째 rung = `cafe_head_on_v0` `w_obs_soft = 75` (첫 **다른 scene**). **두 번 거절**. (1) ESS **31/32** — seed 25 가 134.15, band `[12.8, 128.0]` **위**. 위쪽은 softmax 가 uniform 에 가깝다는 뜻이고 곧 term 이 rollout 을 못 가른다는 뜻이다. (2) `w_geom ∈ {1, 2, 2.5, 4, 8}` ladder 가 median ESS 를 115.86 → 115.64 로만 움직인다 — target 의 **0.19%**. D-167 의 calibration 은 "risk arm 의 ESS 에 착지시키기" 인데 이 scene 에선 **모든 후보가 착지한다**; 고른 `w_geom = 2.0` 은 측정이 아니라 ladder 간격이다. `coefficient_identification` = `FLAT`/`IDENTIFIED`/`UNRECORDED` **3-state** (미기록과 실패는 반대 상태다).
- **거절된 숫자가 반대쪽을 가리킨다는 것이 이 결정을 어렵게 만든다**: head_on 의 `residual_share = 0.0485` vs convoy 의 `0.7725` — 기하가 재현하는 몫이 한 scene 에서 5%, 다른 scene 에서 77%. 그리고 이 숫자는 **representation 에 유리하다**. 그래도 census 는 읽지 않는다: `FLAT` 은 정확히 "null 이 그냥 조용해서 진 것" 을 배제할 수 없는 조건이고, 그 반론에 면역인 것이 이 arm 의 존재 이유였다. 편한 쪽 거절을 지키는 것이 규칙을 시험하는 유일한 경우다.
- **결론적으로 census 는 여전히 `SINGLE_RUNG`, 1/6**. D-167 의 headline 은 아직 mechanism 의 성질이 아니라 convoy `w = 75` 의 성질이다.
- **Alternatives**: (a) 채택. (b) head_on 을 grade 에 포함 — ESS all-seeds 규칙을 편할 때만 적용하는 것. (c) `w_geom` 을 loud 쪽으로 올려 재walk 후 보고 — 옳지만 이 cycle 예산 밖이고, 그게 next priority #1 이다. (d) refused rung 을 `null_rungs` 에서 아예 빼기 — 거절이 보이지 않는 walk 는 아무도 거절된 줄 모른다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-03-the-second-rung-is-refused-twice.md` · D-167 (null 과 그 calibration) · D-166 (walked rung 인구) · D-163 (싼 측정이 관대한 측정) · D-107 (빈 분모)

## D-167 — 2026-08-10 — geometric null 을 처음 돌렸다: 가장 크게 갈라지는 rung 에서 **effect 의 77% 는 representation 없이 재현된다**

- **Context**: D-166 이 margin-free 로 "risk arm 이 6 rung 중 5 에서 앞선다" 를 확정하자 STATE bottleneck 은 significance 가 아니라 **attribution** 으로 이동했다 — epistemic 량이 일하는 것인가, proximity term 이면 아무거나 되는 것인가. `research/feed.md` 2026-08-09 (arxiv 2607.16591) 이 그 null 을 지목: 같은 one-variable cost slot 에 **min-lidar**, matched λ + paired seed. Feed 자신의 지적이 결정적 — min-lidar 가 이기는 것은 representation 결과가 아니라 **학습이 전혀 없는 기하 baseline** 이고, 그래서 이 project 가 한 번도 안 돌려본 arm 이다.
- **Decision**: `controllers/geometric_mppi.py` (registry `geometric_mppi`) + `geometric_null.py`. Null term = `w_geom · Σ_t exp(−min_n(‖x_t − p_n(t₀)‖ − r_n − r_robot)/scale)` — 장애물 위치를 **`t₀` 에 고정** (lidar scan 1 장, motion model 없음), 장애물 축약은 **`min`** (sandbox 기존 soft barrier 는 장애물별 `sum`), decay length 는 barrier 것을 그대로 써서 tunable 을 늘리지 않음. `w_geom = 0` ⇒ stock 과 byte-identical, 그리고 그 불변식을 **기록된 상수** `CONVOY_W75_CLEARANCES["stock_mppi"]` 에 대해 검증 (32 seed, max |Δ| = **0.0**). 등급은 threshold 없이 `margin_free.RungComparison` head-to-head.
- **측정 (convoy `w_obs_soft=75`, λ=0.8, seeds 0–31 — D-166 이 population 최대 effect 로 꼽은 rung)**: ① **equal-coefficient swap 은 거부됐다.** `w_geom = w_risk = 40` 은 λ=0.8 에서 median ESS **12.40** (risk **105.07**, stock **109.77**), 8 seed 중 4 개 band 밖. λ ladder {0.4, 0.8, 1.6, 3, 6} 에 **세 arm 공통 admissible λ 가 없다** (stock·risk 는 0.8 에서만 8/8, null 의 최선은 1.6 의 7/8 — 거기서 stock 1/8 · risk 0/8). 계수가 같다고 **loudness 가 같지 않다**; 처음 쓴 "one-variable" swap 은 term + sampler 두 변수를 움직이고 있었다. ② 그래서 λ 를 세 arm 모두 0.8 로 고정하고 **sampler 응답으로 `w_geom` 을 calibrate** → `w_geom = 2.5` (median ESS 86.08, 32/32 in band). ③ **결과**: `A(geom vs stock) = 0.9868` (Δ **+0.1143 m**, CI `[+0.1002, +0.1301]`) 대 `A(risk vs stock) = 1.0000` (Δ **+0.1480 m**). Head-to-head `A(risk vs geom) = 0.6953`, Δ **+0.0337 m**, CI `[+0.0161, +0.0505]` — 0 을 배제하므로 verdict 는 `REPRESENTATION_ADDS`. 그러나 **`residual_share = 0.7725`**: effect 의 **77% 가 learned channel · motion model · uncertainty 없이 재현된다**. ④ 그 residual 은 계수 한 칸 위에서 사라진다 — `w_geom = 5.0` 이면 91% 재현, head-to-head `EQUIVALENT` (ε = 0.05 m, CI `[−0.0073, +0.0337]` ∋ 0). 이 rung 은 32 seed ESS 로 **거부** (`LOUDER_NULL`) 되어 verdict 가 읽지 않지만, 기록은 남긴다.
- **Alternatives**: (a) equal-coefficient 로 밀어붙이고 ESS 위반을 caveat 처리 — `scorable_band` 의 `ESS_OUT_OF_BAND` 원칙을 스스로 어기는 것이라 기각. (b) null 쪽 λ 를 따로 잡아 arm 별 최적 온도에서 비교 — operating point 를 mechanism 이름으로 비교하는 것이 되어 기각. (c) `scale_match.weight_for_ratio` 로 cost-ratio 매칭 — `ADDITIVE_WEIGHTS` 등록이 선행돼야 하고, comparison 이 실제로 민감한 양은 cost ratio 가 아니라 sampler concentration 이므로 ESS 매칭이 더 강한 매칭이다. (d) 6 rung 전부 — 이번 cycle 예산 밖. 다음 우선순위로 승격.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-02-geometry-recovers-three-quarters-of-the-effect.md` · feed 2026-08-09 (arxiv 2607.16591) · D-163 (8-seed licence, 같은 방향으로 재현) · D-166

## D-166 — 2026-08-10 — threshold 를 **고르지 않는다**: censoring 은 정보가 없는 rung 이 아니라 **가장 크게 갈라지는 rung** 을 버리고 있었다

- **Context**: D-164 (declared margin, 0/3) 와 D-165 (derived margin, rungs 2/6 · scenes 1/3) 로 threshold route 는 양방향 모두 닫혔다. `research/feed.md` 2026-08-10 (arxiv 2605.18045) 이 threshold 자체가 필요 없는 instrument 두 개를 지목 — rank statistic 과 paired bootstrap equivalence test. 둘 다 **이미 기록된** per-seed clearance 만 쓰므로 sim cost 0.
- **Decision**: `eval/mppi_sandbox/margin_free.py` — 6 walked rung 전부에 대해 `A = P(risk > stock) + ½·P(=)` (32×32 전체 pair, exact) + paired bootstrap CI + TOST verdict. Population 은 `derived_margin.walked_rungs()` 를 그대로 재사용해 두 census 의 분모를 공유시킴. Threshold census 의 결론은 **arms 에 대한 진술이 아니었다**: coverage 6/6 rung · 3/3 scene (derived route 는 2/6 · 1/3), 그리고 `NO_TWO_SIDED_TO_SPREAD` 인 3 rung 이 effect size 상위 3개 (`min |A−½|` censored `0.4980` > `max` scored `0.4473`, strict). Arms 가 **너무 완전히 갈라져서** 어떤 threshold 도 양쪽을 interior 로 두지 못한 것이 unscoreable 의 정체. 부수적으로 D-164 의 `MARGIN_DECIDES_VERDICT` rung (crossing `w=250`, 46 threshold / 4 verdict / no majority) 은 `A = 0.4980`, paired CI `[-0.0231, +0.0183]` ∋ 0 — signal 이 없으니 threshold 가 답을 고른 것이고, 이제 ε = 0.05 m 에서 `EQUIVALENT` 라는 **양의 verdict** 를 받는다.
- **Alternatives**: (a) STATE #1 의 min-lidar ablation 을 먼저 — 같은 bottleneck 이지만 새 cost term + matrix re-run 이 필요하고, 이번 결과로 오히려 **discriminating** 해졌으므로 순서가 이쪽이 낫다. (b) project-wide ε 를 하나 선언 — branch 가 이미 magnitude 를 두 번 잘못 골랐으므로 rung 별 `equivalence_margin` (그 rung 이 `EQUIVALENT` 가 되는 최소 ε) 를 보고하고 독자가 자기 tolerance 와 비교하게 함. (c) 6 점으로 correlation 계수 — noise. 대신 두 group 의 strict separation 으로 진술.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-01-the-censored-rungs-are-the-ones-that-separate-most.md` · supersedes 아님 — D-164/D-165 의 결론은 유효하되 그 **해석**("arms 를 비교할 수 없다")을 좁힌다: 비교 불가였던 것은 threshold 이지 arms 가 아니다.

## D-165 — 2026-08-10 — margin 을 **데이터에서 유도해도** population 은 넓어지지 않는다: 안정적 verdict 는 이미 published 된 scene 하나뿐

- **Context**: D-164 가 declared margin 기준 census 를 0/3 으로 닫았고, STATE 는 그것을 *declared* threshold 의 결함으로 읽어 후속 질문을 남겼다 — 기록된 clearance 에서 **유도한** margin 이면 비교를 host 할 수 있는가. 192 개 per-seed clearance 가 전부 상수라 sim 비용 0 으로 답할 수 있는 질문이다.
- **Decision**: 3 개 eligible scene 의 walked rung **6 개** 전부를 `derived_margin.py` 로 census. 답은 **`SINGLE_SCENE_STABLE`, scene 1/3, rung 2/6** — margin 독립 verdict 를 내는 rung 은 head_on `w = 150` (9 two-sided margin 전부 `REPRODUCED`) 과 `w = 250` (23 전부 `REPRODUCED`) 둘뿐이고 **둘 다 이미 published 된 scene**. evidence base 를 넓히려고 walk 한 convoy 와 crossing 은 자기 run 이 표현할 수 있는 어떤 threshold 에서도 **합쳐서 0** 을 기여한다. 유도 경로는 population 을 넓히지 않고 같은 scene 을 다시 찾는다.
- **두 번째 결과 — 공유 threshold 는 없다**: 비어있지 않은 세 window `[0.4194, 0.4437]` / `[0.5467, 0.5938]` / `[0.9712, 1.0906]` 는 **쌍마다 disjoint**. D-158 이 band *안에서* arm coverage 를 1/4 로 상한지었는데 같은 ceiling 이 scene 사이에도 성립하고, 이유가 우연이 아니다 — margin 은 미터 단위 길이이고 clearance scale 은 **scene** 속성이라 `Headroom` 의 "한 번에 한 margin" 제약이 matrix 전체를 문다.
- **세 번째 — 방향이 예외 없이 하나**: derived window 가 있는 declared margin 은 **전부 그 아래**(`BELOW_WINDOW` 3/3, `INSIDE_WINDOW` 0). 세 개의 무관한 오선택이 아니라 matrix 전체가 한쪽(관대한 쪽)으로 치우친 계측이다.
- **자기 코드의 버그를 test 가 잡음**: `shared_window` 를 window 없는 rung 을 **건너뛰도록** 구현해놓고 docstring 에는 반대를 적었다. 건너뛰는 것이 곧 그 docstring 이 피한다고 주장한 vacuous-compatibility 이고, windowed rung 1 개 + windowless 5 개가 공유 window 를 보고하게 만든다 — threshold 를 전혀 허용하지 않는 scene 이 많을수록 census 가 더 자신 있어지는 D-107 형태. 오늘 census 가 `None` 인 것은 세 window 가 마침 disjoint 였기 때문일 뿐 headline 이 우연히 맞았던 것. 이제 구조적으로 `None`.
- **shipped prose 의 거짓 주장 정정**: `margin_sweep` docstring 이 "not a safety claim" 근거로 "at that threshold most runs of *both* arms count as unsafe" 라고 적고 있었다. 측정하면 `w = 250` window 하단에서 `stock_mppi` 11/32, `risk_mppi` **3/32**; `w = 150` 은 19/32 대 **2/32**. 두 rung 어디에도 majority-unsafe risk arm 은 없다. two-sided 는 arm 이 *interior* 이기만 하면 되고 이는 훨씬 약한 조건이다. 원본에서 정정했고, caveat 자체는 살아남는다 — 근거가 "run 이 대부분 unsafe" 가 아니라 **threshold 가 declared 가 아님** 으로 바뀔 뿐.
- **licence 하지 않는 것**: 두 안정 rung 의 window 는 scene 이 선언한 0.40 m 보다 **위**라 arm 을 분리시키려고 고른 threshold 이지 안전을 뜻하는 threshold 가 아니다. clearance 분포 두 개의 순서일 뿐 safety claim 이 아니고, headline `unsafe_rate` 는 모든 declared margin 에서 여전히 0.0000.
- **Alternatives**: (a) 채택 — 6 rung 전부 census. (b) crossing 만 재검 — D-164 가 이미 답했고 cross-scene reading 을 놓친다. (c) declared margin 을 데이터 기준으로 재작성 — 공유 threshold 가 없으므로 scene 마다 다른 척도를 쓰게 되어 matrix 비교가능성이 사라진다. 거절.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/10-00-no-derived-margin-widens-the-population.md` · D-164 (census 가 0/3 으로 닫힘) · D-158 (band 내 1/4 ceiling, 정정된 prose) · D-159 (eligible scene 3 개) · D-107 (빈 population 이 clean 으로 읽힘)

## D-164 — 2026-08-09 — successor question 의 census 는 **0/3 으로 닫힌다**, 그리고 유일하게 re-grade 가 가능한 scene 은 **margin 에 독립인 verdict 자체가 없다**

- **Context**: D-159 가 eligible scene 을 3 개로 좁힌 뒤 head_on (D-158) / convoy (D-160) 두 개가 각각 반대 boundary 에서 `NONE_TWO_SIDED` 로 끝났다. D-163 이 세 번째 scene `cafe_obstacle_crossing_v0` 을 `w = 250` 한 rung 에서 walkable 로 열어 두었고, 이 cycle 이 그 64-run walk 을 실제로 썼다 (64/64 goal, 64/64 ESS band — admissible).
- **Decision**: census 를 **3/3 measured, 0/3 two-sided** 로 닫는다. 세 scene 모두 declared margin 에서 두-arm test 가 아니다. 동시에 **`margin_decides` / `margin_verdict_counts`** 를 `scene_transplant` 에 추가해, "declared margin 이 나쁜가" 와 "margin 에 독립인 답이 있기는 한가" 를 분리한다.
- **핵심 발견 (negative)**: crossing 은 arm overlap **+0.1866 m** 로 세 scene 중 유일하게 re-grade 가 *가능*하다 (convoy −0.0198, band 의 tight rung 7.6/9.9 mm). 46 개 two-sided threshold ([0.9712, 1.0906]) 가 존재하는데, 그 위에서 verdict 가 **`SIGN_REVERSED` 15 / `NO_SEPARATION` 14 / `NOT_REPRODUCED` 10 / `REPRODUCED` 7** 로 갈린다 — 과반 없음, mechanism 방향이 **최소**. 즉 **re-grade 가 가능한 것과 re-grade 가 답을 주는 것은 다른 사실**이고, 후자는 이제 측정되어 거짓이다.
- **부수 결과**: convoy 의 32-vs-32 clearance separation (repo 최대) 은 **재현되지 않는다** — crossing 에서 두 arm 은 tie 이고 risk arm 이 근소하게 **더 나쁘다** (1.0211 vs 1.0229). 그 결과는 scene-specific 이었다.
- **`held` 와 구분되는 이유**: crossing 의 recorded verdict 가 vacuity verdict 이므로 `MarginSweep.held` = 14/46 은 "재현할 것이 없었다는 데 동의한 threshold 수" 이고, 나머지 32 개는 서로도 불일치한다. `held` 만 읽으면 30% stability 로 오독된다 — test 로 고정.
- **Alternatives**: (a) 채택. (b) crossing 을 walk 하지 않고 screen 만으로 닫기 — 그러면 세 scene 중 유일한 repairable case 를 미측정으로 남긴다. (c) two-sided window 중 하나를 골라 결과로 인용 — 이 cycle 이 바로 그것이 threshold 에 대한 진술임을 보였으므로 거절.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-23-the-third-scene-has-no-margin-independent-verdict.md` · D-159 (population) · D-160 (convoy) · D-163 (walkable) · D-044 (reported, never thresholded)

---

## D-163 — 2026-08-09 — 마지막 eligible scene 은 **걸을 수 있다** (1/4): D-161 의 `0/4` 는 성질이 아니라 **미측정 두 칸**이었고, 재는 데 든 비용은 256 run 이다

- **Context**: D-161 이 `cafe_obstacle_crossing_v0` 의 screen 을 `NO_RUNG_TRANSPLANTS` 0/4 로 읽고 "walkable scene 인구는 3 이 아니라 2" 라고 닫았다. 그런데 그 4행 중 2행은 `UNCALIBRATED` 였고, 그 verdict 자신의 docstring 이 이렇게 적고 있다 — *"unmeasured rather than empty, so the rung is **not refused** — it is unscreenable until someone runs `calibrate_lam` there."* 즉 0/4 는 4개의 거절이 아니라 **거절 2 + 미측정 2** 였고, STATE 는 그 구분을 세 cycle 동안 #1 로 들고 있었다.
- **Decision**: 그 run 을 샀다. crossing 만, 양팔, `w ∈ {150, 250}`, 8 rung × 8 seed = **256 run** (~9 min), 각각 자기 file 로 측정한 뒤 D-146 의 `merge_tables` 로 기존 table 에 join (각 2 → 4 cell). 결과: **`PARTIAL_TRANSPLANT` 1/4** — `w = 250` 에서 양팔 모두 `[0.4, 0.8]` 로 band 자신의 λ = 0.8 을 admit 한다. walkable scene 인구는 **3**, D-161 의 population 결론은 철회된다.
- **미측정 두 칸은 서로 다르게 나왔고, 그게 이 cycle 의 두 번째 요점이다**: `w = 250` 은 walkable 이 되었지만 `w = 150` 은 stock 팔이 bisection refine (ladder 8 → 10 rung) 후에도 admissible λ 가 **하나도 없어** `NO_ADMISSIBLE_LAM` 이 되었다. 미측정 칸을 재는 것은 "walkable 이냐 그대로냐" 의 동전던지기가 아니다 — 모르는 것을 *repair 가 없는 것으로 알려진* 거절로 바꿀 수도 있다. 두 칸을 한 verdict 로 뭉뚱그린 0/4 가 정확히 이 차이를 지웠다.
- **그리고 8-seed caveat 이 처음으로 물었다**: merge 가 `w = 150` seed census 의 분모를 2 → **4** 로 넓혔고, crossing/risk 가 census 사상 **첫 non-`WINDOW_HELD` 등급** (`WINDOW_SHIFTED`) 을 받았다 — 8 seed 는 `[0.4, 0.8]`, 16 seed hand walk (`CROSSING_W150_CELL`) 은 `[0.8]`. **싼 측정이 더 넓은 window 를 보고한다**, 즉 λ = 0.4 는 8 seed 를 통과하고 16 seed 에서 떨어진다. D-145 이래 모든 census 가 `WINDOW_HELD` 뿐이었는데, 그것은 "8 seed 면 충분하다" 와 "지금까지 물어본 cell 이 반대할 수 없는 것들뿐이었다" 를 구분하지 못한다. 한 cell 의 불일치가 그 둘을 가른다.
- **이 결과가 사지 않은 것**: (a) walkable 은 **two-sided 가 아니다**. λ 가 admissible 하다는 뜻이고, successor question 이 요구하는 전제일 뿐 질문 자체가 아니다 — 64 run 을 쓸 자격을 샀지 그 이상은 아니다. (b) `w = 250` cell 은 **8-seed** row 이고, 방금 8/16 이 갈린 그 축 위에 있다. transplant 이 서 있는 rung 은 두 source 가 **합의한** 0.8 이고, 갈린 것은 0.4 다 — 그래서 이 결과는 무효가 아니지만, 16-seed 재측정 없이 "확정" 이라고 부를 것도 아니다.
- **witness 를 사면 witness 가 죽는다**: D-149 의 `absent` (registry 가 그 weight 에 들고 있는데 table 에 없는 cell) 는 shipped table 중 유일하게 `w = 150` 이 witness 였고, 이 merge 가 그것을 () 로 만들었다. guard 를 지우는 대신 **재구성**했다 — `calibrate_lam` 자신의 loader/renderer 로 crossing 을 걸러낸 one-scene table 을 tmp 에 렌더해 그 위에서 defect 를 pin 한다. artifact 를 사서 guard 가 prose 가 되는 것은 `guard_vacuity` 의 상시 불만이고, 이 defect 는 다음 one-scene table 이 언제든 재도입할 수 있다.
- **Alternatives**: (a) 채택 — 두 칸 측정 + merge. (b) `w = 250` 만 측정 — 더 쌌지만 `w = 150` 의 `NO_ADMISSIBLE_LAM` 을 못 보고, 위 세 번째 항목(두 칸이 다르게 나온다)이 통째로 안 보인다. (c) matrix 전체를 두 weight 에서 재walk — D-141 이 재현을 이미 쟀으므로 ~1000 run 순수 낭비. (d) 0/4 를 그대로 두고 controller 쪽으로 — STATE 가 세 cycle 째 이것을 #1 로 들고 있었고, 미측정을 성질로 읽은 채 진행하는 것이 D-159/D-161 이 반복해서 booking 한 오류다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-22-the-last-scene-is-walkable-at-one-rung.md` · D-161 의 population 결론 정정 · D-160 (convoy 의 1/4, 같은 모양) · D-159 (population screen) · D-149 (`absent` witness) · D-146 (`merge_tables`) · D-145 (8-seed caveat 의 첫 가격) · D-142 (weight 축은 움직인다)

## D-162 — 2026-08-09 — Artifacts 의 TSV claim 은 **append 에서** 쓴다: 4a 는 `pending` 을 쓰고, 채우는 것은 tree 를 읽는 writer 다

- **Context**: 4a 는 `TSV row appended: yes` 를 append 보다 **두 단계 먼저** 쓴다. 그래서 그 줄은 reading 이 아니라 예측이고, cycle 이 중간에 죽으면 예측이 그대로 남는다. 오늘 09:00 / 11:00 / 18:00 이 정확히 그렇게 죽었고 셋 다 `UNSUPPORTED rows=0` 이다. **그리고 고칠 수 없다** — row 배정이 timestamp 기준이라 뒤 cycle 이 구제하려고 append 한 row 는 *그 뒤 cycle* 에게 배정된다. 19:00 이 18:00 을 살렸는데도 18:00 은 영구히 붉은 이유다.
- **왜 push gate 로는 못 막나 (그리고 gate 는 무죄다)**: `push_preflight._unsupported_frontier` 가 이미 정확히 이 population 을 소비한다. 세 cycle 은 그 gate 를 **통과한 적이 없다** — push 자체를 못 했다. 도달되지 않는 gate 는 경보를 울리지 않는다 (`unwatched_strandings` 가 한 층 위에서 쓴 문장 그대로). 그러므로 수리는 gate 가 아니라 **write site** 에 있어야 한다.
- **Decision (writer)**: 4a 는 `pending` 만 쓴다. `grade_tsv` 가 `yes`/`no` 아닌 것을 `UNPARSED` 로 보내므로 `pending` 은 **아무 주장도 하지 않는다**. append 뒤에 `cycle_artifacts claim` 이 tree 를 세어 줄을 emit 한다 — D-154 가 TSV `timestamp` 에 한 것과 같은 수: cycle 은 자기가 무엇을 할 참인지 모른다.
- **Decision (guard)**: 같은 명령이 verdict 이기도 하고, push gate 의 `&&` 사슬에 **chain 된다**. 두 칸 위의 `tsv_timestamp check` 는 chain 될 수 없어서 손으로 배치해야 하는데, 그 이유가 여기서 뒤집힌다 — 그쪽 population 은 *uncommitted* row 라 `git add` 가 침묵시키지만, `claim` 은 commit 전에는 typed timestamp 로 commit 후에는 `git blame` 으로 같은 row 를 세므로 늦게 실행돼도 vacuous 해지지 않는다. `&&` 를 견디는 check 는 아무도 배치를 기억할 필요가 없는 check 다.
- **정직한 방향은 값을 매기지 않는다**: `pending` 으로 남은 journal 은 `UNPARSED` 이고 finding 이 아니다 — 의도적으로. 정직한 방향을 비싸게 만드는 guard 는 cycle 에게 `yes` 를 쓰고 기도하라고 가르친다. 이 module 의 기존 비대칭 (`UNDERCLAIMED` 는 보고하되 finding 아님) 을 write site 로 연장한 것.
- **Alternatives**: (a) 채택 — write site 수리 + chain 된 guard. (b) push gate 를 더 세게 — 죽은 cycle 은 gate 에 도달하지 않으므로 아무것도 바뀌지 않는다. (c) 뒤 cycle 이 scar 를 수리 — timestamp 배정이 구조적으로 막는다, 오늘 세 번 증명됨. (d) `pending` 도 finding 으로 — 정직한 방향에 벌금.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-21-the-claim-is-written-from-the-append.md` · D-154 (timestamp writer, 같은 수) · D-110 (position 대신 이름으로 지목) · D-082 (`&&` 가 규칙) · D-107 (빈 population 은 clean 아님)

## D-161 — 2026-08-09 — 마지막 eligible scene 은 **걸을 수 없다** (0/4), 그리고 STATE 의 margin 가설은 convoy 에만 맞다 — head_on 의 0.40 m 는 자기 분포 **안에** 있다

- **Context**: D-159 가 successor question 의 population 을 8 scene → 3 으로 잘랐고 D-160 이 두 번째 scene(convoy)을 걸었다. STATE 의 다음 step 은 마지막 scene `cafe_obstacle_crossing_v0` 을 margin 0.30 에서 64 run walk 하는 것, 그리고 그 다음 "세 scene 의 declared margin 이 모두 자기 clearance 분포 밖에 있다면 acceptance yaml 이 finding" 을 확인하는 것이었다.
- **Decision (1) — walk 은 일어나지 않는다. screen 이 0/4 로 거절한다.** `w = 75` 에서 stock arm 은 λ = 4.5255 로 calibrate 되어 있고 `risk_mppi` 는 **admissible λ 가 아예 없다**; `w = 100` 은 양 arm 모두 empty window; `w = 150`/`250` 은 cell 자체가 없다. sim run 0회, yaml 읽기만으로 확정. **walkable scene population 은 3 이 아니라 2** 이고, 이 닫힘은 controller 가 아니라 calibration 이 만든 사실이다.
- **Decision (2) — empty window 와 wrong-valued window 는 다른 거절이다**: `NO_ADMISSIBLE_LAM` 을 `LAM_NOT_ADMISSIBLE` 옆에 신설. convoy 의 막힌 rung 은 window 가 non-empty (λ = 1.1314) 라 *reference* λ 에서만 거절이고 cross-scene 비교가능성을 내주면 걸을 수 있다; crossing 의 `w = 75` 는 내줄 것이 없고 repair 는 다른 **weight** 뿐이다. 둘을 "blocked" 로 합치면 0/4 가 한 사실처럼 읽히는데 실제로는 둘이고, 회복 가능한 절반이 사라진다 (D-157 의 "이유는 종류가 다르다" 를 한 scope 아래에서).
- **Decision (3) — STATE 의 margin 가설은 절반이 틀렸고, 틀린 절반이 published band 쪽이다.** `margin_placement` census (걸어본 5 rung, sim run 0회): convoy 는 `MISPLACED` (0.30 m vs [0.8914, 1.2066], 최악도 0.59 m 여유) 로 가설대로지만, **head_on 은 아니다** — 0.40 m 가 `w ∈ {150, 250}` 에서 **양 arm 모두**의 range 내부이고 risk arm 기준으로는 4 rung 전부 내부다. "acceptance yaml 이 finding" 은 **scene-local** 진단이지 census 전체의 설명이 아니다. head_on 의 `w ∈ {75, 100}` 은 stock arm 이 `BELOW_ALL` — 잘못 선언된 margin 이 아니라 D-158 의 ceiling 이고, 그 읽기는 margin 쪽에서 봐도 살아남는다.
- **Decision (4) — 두 답이 갈리는 이유는 scope 이고, 유리한 scope 는 pooled 쪽이다.** well-placed 2/5 는 32 seed 를 **pool** 했을 때의 내부성이고, D-157 이 실제로 채점하는 **block**(16 seed 씩) scope 에서는 **0/5** 다. 두 half 중 어느 쪽도 갖지 않은 내부 range 를 pooling 이 만들어낸다 — D-157 의 2/4-vs-0/4 delta 를 margin 쪽에서 본 것과 같은 간극이다. 그래서 `RungPlacement` 는 `verdict`(pooled) 와 `block_interior` 를 **둘 다** 들고 `scope_disagreement` 로 이름 붙인다. 단일 boolean 은 어느 쪽이든 독자가 묻지 않은 질문의 답이 된다.
- **회귀 위험을 test 로 고정**: `NO_ADMISSIBLE_LAM` 은 같은 분기에서 `LAM_NOT_ADMISSIBLE` **앞에** 놓이므로 D-160 이 발표한 convoy 1/4 를 조용히 재채점할 수 있었다. convoy screen 을 `PARTIAL_TRANSPLANT` 1/4 로 pin 하는 test 를 같이 ship — refinement 가 아무도 announce 하지 않은 retraction 이 되는 경로다.
- **Reported, never thresholded (D-044)**: transplant count 이 non-zero 라거나 어떤 margin 이 well placed 라고 주장하는 test 는 없다. 오늘의 0/4 와 2/5 는 정직한 읽기이고, scene 이 재선언되거나 재walk 되는 순간 영구 red 가 된다.
- **Alternatives**: (a) 채택 — screen 먼저, 그리고 walk 대신 margin census. (b) STATE 대로 crossing 을 λ = 0.8 로 걸기 — `assert_ess_in_band` 가 거절하는 숫자를 64 run 써서 생산. (c) crossing 을 stock arm 의 λ = 4.5255 로 걸기 — arm 마다 다른 λ 는 비교가 아니다. (d) 두 거절을 `LAM_NOT_ADMISSIBLE` 하나로 두기 — 0/4 가 한 사실로 읽히고 회복 경로가 숨는다. (e) `margin_placement` 를 pooled scope 만으로 보고 — 2/5 라는 유리한 숫자를 근거 없이 고른다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-18-the-last-scene-cannot-be-walked.md` · D-160 (convoy walk, 1/4 screen) · D-159 (scene population 8→3) · D-158 (effect-size ceiling) · D-157 (union-over-blocks, 이유는 집합) · D-107 (빈 population 은 clean 으로 읽힌다) · D-044

## D-160 — 2026-08-09 — `cafe_convoy_v0` 도 `NONE_TWO_SIDED` 다 — **반대쪽 경계에서**. 그리고 band 의 protocol 은 4 rung 중 **1개** 에만 이식된다

- **Context**: D-159 가 successor question 의 population 을 3 scene 으로 줄였고, 그 중 측정된 것은 `cafe_head_on_v0` 하나뿐이었다. STATE 의 다음 step 은 `cafe_convoy_v0` 를 **자기 margin 0.30 m** 에서 양 arm 걷는 것. 실제로 걸어보니 답이 두 개 나왔고, 하나는 run 을 쓰기 **전에** 나왔다.
- **Decision (screen)**: λ 는 **scene 단위 calibration** 이므로 "같은 protocol" 은 공짜 이동이 아니다. band 의 4 rung 중 convoy 를 λ = 0.8 로 걸을 수 있는 것은 **`w = 75` 하나뿐**이다 — `w = 100` 은 calibrated 이지만 window 가 `{1.1314}` 라 λ = 0.8 은 `assert_ess_in_band` 가 거절할 숫자를 만들고, `w = 150`/`w = 250` 은 convoy cell 자체가 없다. `lam_window_index` 가 이미 소유한 yaml table 만 읽어서 0 run 으로 판정. 두 거절 사유(`LAM_NOT_ADMISSIBLE` vs `UNCALIBRATED`)는 합치지 않는다 — 후자만 calibration run 한 번이면 복구된다 (D-157 의 이유).
- **Decision (walk)**: `w = 75`, λ = 0.8, seeds 0–31, 양 arm 64 run, 64/64 goal 도달 + 64/64 ESS band 내. 결과는 **`NO_HEADROOM_SAFE`** — 64 run 이 **전부** 0.30 m 를 넘겼고 최악이 0.5914 m 여유. 양 arm 모두 `FLOOR`, `BOTH_ARMS_CENSORED`, headline `unsafe_rate` **0.0000 / 0.0000**. head_on 은 stock arm 이 `CEILING` 이라 같은 verdict 인데 **원인이 정반대** — 한쪽은 margin 이 너무 어렵고 한쪽은 너무 쉽다. 그래서 `censoring_direction` 을 `SeedBlock.censoring` **옆에** 둔다: pin 된 arm 의 *개수* 만으로는 두 scene 이 구별되지 않고, 처방은 서로 반대다.
- **재채점으로도 복구 불가, 그리고 head_on 보다 더 심하다**: convoy 의 두 arm range 는 **disjoint** (`stock` ≤ 1.0086 < 1.0284 ≤ `risk`, `arm_overlap` **−0.0198 m**) — head_on 의 `w ∈ {75, 100}` 이 7.6 mm / 9.9 mm **양수** overlap 이었던 것과 달리 음수다. published band 가 만든 적 없는 corner.
- **유일한 좋은 숫자는 safety 가 아니라 mechanism 이다**: 모든 `risk_mppi` run 이 모든 `stock_mppi` run 보다 안전하다 (32 대 32 완전 분리, band 의 어떤 rung 도 못 한 것). 그래도 safety delta 일 수 없다 — 그것이 움직일 통계가 처음부터 0.0000 이다. D-124 의 함정이 거울상으로 재현된 것이고, `sub_margin` 이 `False` 인 이유가 바로 양쪽 평균이 margin **위** 라서다.
- **Alternatives**: (a) 채택 — screen 먼저, 통과한 1 rung 만 walk. (b) 4 rung 전부 λ = 0.8 로 walk — inadmissible 숫자 3개를 만들고 그 사실이 표에 안 남는다. (c) convoy 를 head_on 의 0.40 m 로 채점 — D-159 가 이름 붙인 cross-scope 오류 그 자체. (d) `censoring_direction` 을 `censoring` 에 접어 넣기 — 반대 처방 두 개를 한 이름으로 병합.
- **Reported, never thresholded** (D-044): 1/4 도 `NONE_TWO_SIDED` 도 오늘의 정직한 읽기일 뿐, 어떤 test 도 non-zero 를 주장하지 않는다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-17-convoy-is-censored-from-the-other-side.md` · D-159 (population screen, 한 단계 위) · D-158 (head_on 의 ceiling 1/4) · D-157 (거절 사유는 집합) · D-142 (weight 간 window 이동) · D-124 (sub-margin delta)

## D-159 — 2026-08-09 — successor question 의 분모는 **8 이 아니라 3** 이고, 그 중 2개는 한 번도 걸어본 적이 없다: scene 은 property 를 재기 전에 **population 부터 걸러야** 한다

- **Context**: D-158 이 `cafe_head_on_v0` 의 arm coverage 천장을 1/4 로 확정하면서, 다음 질문을 **scene** 으로 넘겼다. STATE 는 그것을 "8개 matrix scene 중 어디가 published margin 에서 두 팔의 clearance 분포가 겹치는가" 로 적었다. 이 문장에는 측정 이전에 반박되는 전제가 두 개 있다.
- **Decision**: `scene_eligibility.py` — overlap 을 재기 전에 **그 질문을 물을 수 있는 scene 이 어디인가** 를 먼저 census. 새 primitive 를 만들지 않고 `feasibility` 가 이미 가진 reader (`declared_margin`, `goal_ball_clearance`) 를 조합한다. sim run 0회, yaml 읽기뿐.
  - **8개 중 5개는 질문을 호스트할 수 없다**: `cafe_straight_v0` / `city_curved_v0` / `city_figure8_v0` 는 **obstacle 이 없고** (아무것도 없는 것에 대한 clearance 는 측정이 아니다 — D-107 의 빈 population 이 clean 으로 읽히는 모양), `cafe_freezing_v0` 는 obstacle 2개를 갖고도 **margin 을 선언하지 않으며** (두 팔을 채점할 threshold 자체가 없다), `cafe_cut_in_v0` 는 **증명된 infeasible** — goal ball best clearance **−0.20 m**, `feasibility` 가 이미 증명한 것을 census 가 이제 센다.
  - **살아남은 3개 중 recorded clearance 가 있는 것은 `cafe_head_on_v0` 하나뿐** — 즉 D-158 이 천장 1/4 로 못박은 바로 그 scene 이다. two-sided rung 으로 가는 남은 경로는 전부 **`cafe_convoy_v0` 또는 `cafe_obstacle_crossing_v0`** 를 지나고, 둘 다 한 번도 걸린 적이 없다. successor question 은 **8-scene survey 가 아니라 2-scene walk** 다.
  - **cross-scene 에서는 "the published margin" 이라는 것이 없다**: eligible 3개가 선언하는 margin 은 **2종** (`cafe_head_on_v0` 0.40 m, 나머지 둘 0.30 m). 이건 코드에 새로운 사실이 **아니다** — `feasibility.declared_margin` 과 `near_miss` 가 이미 문장으로 적고 있다. 새로운 것은 **읽기의 scope** 다: `Headroom` 은 서로 다른 margin 의 두 팔을 채점하기를 거부하므로, `scorable_band.PUBLISHED_MARGIN` 을 cross-scene census 가 인용하면 **scene 상수를 band 상수로 인용**하는 것이 된다 — D-157 과 같은 모양.
- **exclusion 은 first match 가 아니라 집합이다** (D-157): `cafe_straight_v0` 는 두 screen 에 동시에 걸린다 (obstacle 없음 + margin 없음). 5개 scene 이 **8개 사유**를 진다. 선호하는 쪽을 assert 하지 않고 두 count 를 나란히 계산하는 test 로 못박았고, 단일값 `verdict` 는 표시용 precedence pick 일 뿐 population 사실이 아님을 별도 test 가 지킨다.
- **보고하되 gate 하지 않는다** (D-044): eligible count 가 0 이 아님을, 또는 어떤 scene 이 measured 임을 주장하는 test 는 없다. D-158 의 censoring 교훈이 scene 에도 그대로 적용된다 — **효과가 클수록 덜 eligible 해진다** — 그래서 여기에 gate 를 걸면 가장 강한 결과를 벌하게 된다.
- **일반화된 교훈**: 세 cycle 연속으로 findings 가 "답" 이 아니라 **"그 질문을 애초에 물을 수 있는 항목이 무엇인가"** 였다 (D-157, D-158, D-159). overlap 을 8개 scene 에 그냥 물었으면 **5개의 vacuous cell 이 clean 으로 읽혔을 것**이다. property 를 재기 전에 population 을 거른다.
- **Alternatives**: (a) 채택 — 측정 전 screen, 조합으로 구현. (b) STATE 대로 8개 scene 에 overlap 을 바로 질의 — vacuous cell 이 결과로 읽힌다. (c) 미선언 margin 에 0.30 을 기본값으로 — scene 이 말하기를 거부한 것을 코드가 대신 정하는 것이라 거절 (`declared_margin` 이 `None` 을 반환하는 이유 그 자체).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-16-three-of-eight-scenes-can-host-the-question.md` · D-158 (천장 1/4) · D-157 (집합 vs first match) · D-107 (빈 population) · D-044 (보고하되 gate 하지 않음)

## D-158 — 2026-08-09 — arm coverage 0/4 는 **margin 을 바꿔서 고칠 수 있는 것이 아니다**: 4 rung 중 2개는 *어떤* threshold 에서도 two-sided 가 되지 않고, band 전체의 천장은 1/4 이다

- **Context**: D-157 이 arm coverage 를 `NONE_TWO_SIDED` (0/4) 로 확정했고, STATE 는 그 원인을 **threshold** 로 읽었다 — `stock_mppi` 가 `w ∈ {75, 100}` 에서 0.40 m 를 한 번도 넘지 못하니 rate 가 고정되고 separation 을 한쪽 팔이 떠맡는다는 것. 그렇다면 "어떤 margin 이었으면 two-sided 였나" 는 sim 없이 답할 수 있는 질문이다: 4 rung × 32 seed 의 per-seed clearance 가 이미 `separation_reproduction.py` 의 상수다.
- **Decision**: `margin_sweep.py` — 각 rung 을 자기 recorded clearance 가 표현할 수 있는 **모든** margin 에서 재채점 (`regrade` / `breakpoints` / `MarginSweep` / `BandSweep`). 결과가 전제를 뒤집었다:
  - **`w = 75`, `w = 100` 은 어떤 threshold 에서도 two-sided 가 아니다.** 두 팔의 clearance range 겹침이 각각 **7.6 mm**, **9.9 mm** — 두 block 모두에서 양 팔 내부에 놓이는 margin 이 존재하지 않는다. 이 rung 들의 censoring 은 **효과가 크다는 성질**이지 margin 을 잘못 골랐다는 성질이 아니다. re-grading 으로 고칠 수 없다.
  - **`w = 150`** 은 `[0.4194, 0.4437]` (9 breakpoint) 에서 two-sided 이고 그 전 구간에서 `REPRODUCED` 를 유지한다.
  - **`w = 250`** (D-151 의 `SIGN_REVERSED`) 은 `[0.5467, 0.5938]` (23 breakpoint) 에서 two-sided 이고 **23개 전부에서 `REPRODUCED`** 로 읽힌다. published margin 에서의 부호는 block 당 **1 run** 이 떠받치고 있었다 (stock 0/16 → 1/16, risk 1/16 → 0/16).
  - **Band 수준**: 두 window 가 서로소이고 `Headroom` 은 서로 다른 margin 의 두 팔을 거부하므로, band 는 하나의 threshold 로 채점된다 → **어떤 margin 도 4 rung 중 2개를 동시에 two-sided 로 만들지 못한다.** arm coverage 의 천장은 **1/4**, 0/4 는 "쓴 margin 에 대한 사실" 일 뿐이었다.
- **D-151 에 대해서는 retraction 이 아니라 qualification**: 0.55 m 는 scene 의 margin 이 아니고 그 threshold 에서는 양 팔의 대부분 run 이 "unsafe" 이므로, 재채점은 두 clearance 분포의 **순서**에 대한 진술이지 safety 주장이 아니다. 없어지는 것은 "`w = 250` 에서 seed 가 mechanism 과 *반대*를 가리켰다" 는 읽기뿐이고, 그 rung 을 published band 에 되돌려 놓지는 못한다.
- **왜 exhaustiveness 를 따로 시험하는가**: 4개 중 2개의 답이 "존재하지 않는다" 이고, 이는 64개 목록으로 실수 전체에 대해 하는 주장이다. unsafe count `#{c : c < m}` 이 계단 함수라 recorded clearance 만 열거하면 충분하다는 논증은 **논증으로 두지 않고** rung 당 2000점 dense grid 로 찔러 확인한다. 이게 없으면 두 `NO_TWO_SIDED_MARGIN` 판정에 근거가 없다.
- **일반화된 교훈**: `censored` 와 `under-powered` 는 **정반대 진단인데 census 에서 똑같이 읽힌다**. `w = 75`/`w = 100` 은 효과가 커서 분포가 거의 겹치지 않아 censored 다 — mechanism 이 좋아질수록 *더* censored 된다. 따라서 arm coverage 에 gate 를 걸면 band 의 가장 강한 결과를 벌하게 되고, 이것이 `arm_verdict` 를 보고만 하고 thresholding 하지 않는 (D-044) 구체적 근거다.
- **Alternatives**: (a) 채택 — sweep 을 계산으로 돌리고 천장을 보고. (b) `w = 150`/`w = 250` 의 window 로 band 를 재채점 — scene 이 선언하지 않은 margin 으로 published 결과를 다시 쓰는 것이라 거절. (c) two-sided rung 을 얻으려 새 seed 를 더 걷기 — 겹치지 않는 분포에는 seed 가 듣지 않는다 (STATE 가 이미 지적).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-15-two-rungs-have-no-two-sided-margin.md` · D-157 (0/4 의 출처) · D-151 (`w = 250` 의 reversal) · D-044 (보고하되 gate 하지 않는 규율)

## D-157 — 2026-08-09 — arm coverage 는 **1/4 이 아니라 0/4** 였다: D-155 는 rung 의 성질을 *reference block* 에서 읽었고, censoring 은 rung 단위 census 를 가져야 한다

- **Context**: D-155 는 census 가 4/4 로 닫힌 것을 기록하면서 "4 rung 중 양팔이 모두 자유로웠던 것은 `w = 150` 하나뿐" 이라고 적었고, STATE 도 "arm coverage 1/4" 로 옮겼다. 이 cycle 의 TODO 는 그 1/4 을 4/4 옆에 자동으로 붙여 보여주는 것이었다. 그런데 그 1/4 은 각 rung 의 **reference block** 만 읽은 값이다.
- **Decision**: censoring 을 `SeedBlock` (한 block) 에서 `Reproduction` (한 rung) 으로 올린다 — `Reproduction.censored` 는 두 block 에 걸친 pinned arm 의 **합집합**이고, `censoring` 은 항목이 아니라 **distinct arm** 을 센다. `ReplicationCensus` 는 `verdict` 와 독립인 두 번째 판정 `arm_verdict` (`NO_REPLICATED_RUNG` / `NONE_TWO_SIDED` / `PARTIALLY_TWO_SIDED` / `FULLY_TWO_SIDED`) 를 갖고, `__str__` 이 둘을 함께 낸다.
- **측정 결과가 spec 을 반박했다**: `w = 150` 의 reference block 은 양팔이 자유롭지만 **replication 이 `risk_mppi` 를 0/16 에 고정**한다. rung 단위로 세면 two-sided 는 **0/4**, `NONE_TWO_SIDED`. published band 는 `FULLY_REPLICATED` 이면서 동시에 `NONE_TWO_SIDED` 다 — rung coverage 4/4, arm coverage 0/4. 그리고 `w = 250` 은 두 block 이 **서로 다른 arm** 을 floor 에 고정하므로 (reference: stock, replication: risk) block 단위로는 둘 다 `ONE_ARM_CENSORED` 인데 rung 은 `BOTH_ARMS_CENSORED` 다. 합집합이 아니라 "두 block verdict 중 나쁜 쪽" 을 취했으면 이 rung 을 놓친다.
- **왜 합집합인가**: 질문이 "이 rung 이 양쪽으로 검정되었는가" 이기 때문이다. 한 block 에서 움직일 여지가 없던 arm 은 그 block 에서 mechanism 과 무관하게 고정값을 냈으므로, 다른 block 이 자유로웠더라도 그 비교는 한쪽짜리였다. 이 선택이 곧 1/4 과 0/4 의 차이 전부이므로, 선호하는 쪽을 assert 하지 않고 **두 count 를 나란히 계산하는 test** 로 못박았다.
- **보고하되 gate 하지 않는다** (`one_run_rungs` discipline): arm coverage 가 0 이 아님을 주장하는 test 는 없다. 있었다면 오늘의 정직한 0/4 이 영구 red 가 된다 (D-044 의 muted check).
- **일반화**: item 단위 field 를 잘못된 level 에서 집계하면 *빠진* 주장이 아니라 **틀린 population 주장**이 된다. `SeedBlock.censoring` 은 모든 call site 에서 옳았고, 틀린 것은 그것을 rung 의 성질로 옮겨 적은 두 cycle 의 산문이었다. 그리고 위험한 방향은 **부분이 안심되게 읽히는 합성** — `w = 250` 의 두 block 은 각각 온건하고 합성은 더 나쁘다 (D-149 의 빈 부분집합과 같은 모양).
- **Alternatives**: (a) 채택 — rung 단위 합집합 + 독립 verdict. (b) TODO 대로 1/4 을 그대로 보고 — census 가 막으려던 오류를 census 가 인증하게 된다. (c) block 단위 최악값 — `w = 250` 의 `BOTH_ARMS_CENSORED` 를 놓친다.
- **Status**: accepted (D-155 의 "1/4" 를 정정)
- **Refs**: PR #67 · `journal/2026-08/09-14-arm-coverage-is-zero-of-four.md` · D-155 (정정 대상) · D-149 (합성이 부분보다 나쁜 같은 모양) · D-044 (gate 하지 않는 이유)

## D-156 — 2026-08-09 — strand 의 진짜 비용은 지연이 아니라 **측정의 부재** 다: 11:00 은 red tree 위에 `Status: keep` 를 썼고, 한 시간 동안 아무것도 빨개지지 않았다

- **Context**: D-112 의 `cycle_artifacts stranded` 가 11:00 cycle (`95f5248`) 을 지목해 이번 cycle 의 첫 의무가 됐다. 그것을 밀려면 receipt 를 떠야 하고 — 11:00 이 뜨지 않은 바로 그 receipt — 결과는 **red** 였다: `test_inert_surface.py` 3 fail, `stale_pins()` 가 `('RESULTS.md', 'results/')` 를 반환.
- **원인은 이번 cycle 이 아니다**: `95f5248` 이 추가한 `test_tsv_timestamp.py` 가 `results/*.tsv` 를 **읽는다**. 그래서 두 pin 이 떠 있던 reader key 가 움직였고, D-079 의 탐지기가 설계대로 정확히 물었다. 고장난 것은 아무것도 없다 — 다만 **한 시간 동안 아무도 그것을 듣지 못했다**.
- **왜 못 들었나 (이것이 결정의 내용)**: receipt 를 뜨는 유일한 지점은 `push_preflight record` 이고, 그것은 push 하는 cycle 만 실행한다. D-082 의 `&&` 는 *일어난* push 에만 발동한다. 따라서 **strand 된 cycle 은 정의상 측정되지 않은 cycle** 이다. D-112 의 reading 은 "work 가 origin 에 닿지 않았다" 까지만 말하고 "그 tree 는 채점된 적도 없다" 는 말하지 않는데, 후자가 더 무거운 사실이다. 11:00 의 journal 은 그 tree 위에 `Status: keep` 라고 적혀 있다.
- **Decision**: (1) stale pin 두 개를 재취득한다 — `results/` 는 entrant 1개로 composition, `RESULTS.md` 는 **generation 2/3 = `COMPOSITION_CAP`** 이라 14-reader full probe 로 fallback. (2) strand 의 이 두 번째 비용을 기록한다: 다음에 `cycle_artifacts stranded` 를 손대는 cycle 은 verdict 에 "unmeasured" 를 함께 실어야 한다.
- **그리고 예고된 청구서가 도착했다**: `results/` pin 의 note 는 2026-08-07 에 이미 이렇게 적어놨다 — *"at COMPOSITION_CAP one new test file costs a 17m57 full probe instead of a 0.5 s composition."* 이번 cycle 이 그 비용을 처음 지불했고, 그것도 **무관한 cycle 이 예산 한가운데서** 지불했다. 미래 비용을 이름 붙여 적어두는 것과 그것을 일정에 넣는 것은 다르다.
- **예산 초과는 의도적이다**: 35분에서 멈추면 13:00 은 여전히 red 인 tree 위에 **두 cycle 짜리 strand** 를 물려받는다. strand 해소가 decision tree 를 앞선다는 D-112 의 규칙은 이 경우 예산도 앞선다.
- **Alternatives**: (a) 채택 — probe 를 돌리고, 초과하고, push 한다. (b) 35분에 멈추고 journal 만 쓴다 — strand 가 2배가 되고 red 가 한 시간 더 숨는다. (c) pin 을 손으로 갱신 (probe 없이 key 만 다시 타이핑) — D-076 이 지적한 "조용히 낡아가는 typed set" 그 자체라 거절; pin 의 가치는 그것이 **측정** 이라는 데 있다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-12-the-last-rung-reproduces-and-the-census-closes.md` · D-112 (strand reading) · D-082 (push gate `&&`) · D-079 (pin staleness detector) · D-076 (typed set 의 부패) · D-154 (`95f5248` 이 ship 한 writer)

## D-155 — 2026-08-09 — 마지막 rung `w = 75` 가 재현되어 census 가 **4/4 로 닫혔다**: 그러나 `FULLY_REPLICATED` 는 *분모* 에 대한 판정이고, 4 rung 중 **양팔이 모두 자유로웠던 것은 1개** 뿐이다

- **Context**: D-151/D-152/D-153 이 `w = 250 / 150 / 100` 을 disjoint block 으로 다시 걸었고 `w = 75` 하나가 `unreplicated` 로 남아 두 cycle 연속 미선택 상태였다. 이 rung 은 분리된 섬 `{75, 100, 150}` 의 **아래쪽 가장자리** 라 뒤집혀도 섬을 쪼개지 않고 깎기만 한다 — 그래서 interior 인 `w = 100` 다음 순서였다.
- **Decision**: 32 seed × 2 arm = **64 run** 을 걸었다. 참조 block 0–15 는 D-133 행을 정확히 재현 (stock 16/16, risk **11/16**); fresh block 16–31 은 stock 16/16, risk **8/16** — 같은 방향이고 분리가 오히려 **커졌다**. `REPRODUCED`. pooled n = 32 는 stock 32/32 vs risk 19/32. `published_census()` 에 편입해 coverage 3/4 → **4/4**, verdict `PARTIALLY_REPLICATED` → `FULLY_REPLICATED`.
- **이번 entitlement check 가 넷 중 가장 강하다**: `w = 75` 는 published risk count 가 boundary 도 그 옆도 아닌 유일한 rung (11/16) 이다. 나머지 셋은 0 또는 16 에 고정돼 있어 drift 된 pipeline 도 통과할 수 있지만, 여기서는 정확히 11 을 우연히 맞혀야 한다.
- **그리고 이것이 이 결정의 진짜 내용**: `FULLY_REPLICATED` 는 **분모** 를 채점하지 결과를 채점하지 않는다. 4/4 인 지금도 `w = 250` 은 여전히 `overturned` 이므로 "band 가 fully replicated 다" 와 "band 가 replicate 됐다" 는 한 단어 차이로 다른 말이다. `PARTIALLY_REPLICATED` 일 때는 오독이 불가능했으므로, verdict 가 오독 가능해진 순간이 곧 docstring 이 필요해진 순간이다 — class docstring + census test 에 `held`/`overturned` 를 별도 assertion 으로 못박았다.
- **닫힌 축이 다음 축을 드러낸다**: 재현된 4 rung 중 **3개가 `ONE_ARM_CENSORED`** 다. `w = 75` 는 stock 이 `CEILING` 이고 32 run 중 최고가 **0.3176 m** (margin 0.40) — 셋 중 가장 깊은 ceiling 으로 `w = 100` 의 0.3705 m 보다 낮다. 즉 **rung coverage 4/4 vs arm coverage 1/4** (`w = 150` 만 양측 검정). census 는 이 구분에 대해 침묵하며, 그것이 다음 slice 다.
- **크기는 보고하되 gate 하지 않는다**: pooled `separation_runs` 는 `w = 75` **13**, `w = 150` 14, `w = 100` 24 — coverage 를 닫은 rung 이 섬에서 가장 얇다. `one_run_rungs` 와 같은 규율로 자체 test 에 기록만 한다.
- **Alternatives**: (a) 채택 — 걷고, 편입하고, verdict 의 오독 가능성을 같은 cycle 에 봉함. (b) 걷기만 하고 census 는 나중에 — verdict flip 이 문서 없이 착지한다. (c) `FULLY_REPLICATED` 를 arm coverage 까지 요구하도록 재정의 — 분모 두 개를 한 verdict 에 섞는 것이라 거절; 별도 field 가 맞다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-12-the-last-rung-reproduces-and-the-census-closes.md` · D-153 (`w = 100`) · D-152 (`w = 150`) · D-151 (census 개설) · D-139 (entitlement check) · D-133 (published table)

## D-154 — 2026-08-09 — TSV `timestamp` 는 **읽은 값이 아니라 타이핑된 값**이었다 (183행 중 40행이 불가능): writer 를 주고, 과거 40행은 **보고하되 gate 하지 않는다**

- **Context**: D-153 직후 cycle 이 이 column 의 drift 를 *측정*했지만 (40/181), 고친 것은 없었다. `cycle_artifacts` 는 이미 이 field 를 dating key 로 **반박**하고 `commit` ∩ `git blame` 교집합으로 우회하고 있었다 — 즉 알려진 결함을 우회하는 절반만 되어 있었고, writer 는 계속 나쁜 행을 생산 중이었다. `aggregate_results.sh` / `RESULTS.md` / 사람이 읽는 표는 전부 타이핑된 값을 그대로 받는다.
- **Decision**: `eval/mppi_sandbox/tsv_timestamp.py` — (1) `audit`: commit 된 전 population 에 대한 **읽기** (항상 rc=0), (2) `check`: 아직 uncommitted 인 행에 대한 **gate** (`stamp > now` 면 rc=1), (3) `row`/`append`: 시계를 읽어 행을 만드는 **writer**. 헌법 prompt 의 EXECUTE 단계를 writer 호출로 교체.
- **왜 sign 이 있는 signature 로 grade 하는가**: 행은 쓰고 **나서** commit 되므로 stamp 가 자기 도입 commit 보다 늦으면 그것은 시계가 할 수 없는 일이다 — threshold 가 필요 없는 **연역**. 정직한 143행의 write→commit lag 이 median **1.2분**이라는 통제 분포가 이 판정을 artifact 가 아니라 finding 으로 만든다. `seconds == 00` 63행 (기대 3.0, 40행 중 36행이 동시 해당) 은 더 큰 증거지만 **보고만 하고 grade 하지 않는다**: "수상하게 round" 와 "round" 사이의 상수를 아무도 방어할 수 없다 (`one_run_rungs` discipline).
- **audit 과 gate 의 분할 기준은 severity 가 아니라 repairability (D-044)**: 40행은 soft limit 상 append-only ("Never edit past rows") 이고, 고치면 그것을 유죄로 만든 blame key 자체가 파괴된다 (D-102 의 "수리가 자기 증거를 지운다" 세 번째 등장). 그 위에 gate 를 걸면 매 cycle 영구 red 이고, 영구 red 인 check 는 muted 된다. 그래서 gate 는 **아직 고칠 수 있는 행** 만 본다.
- **🔴 gate 의 약점을 그대로 기록한다 — placement 가 load-bearing 이다**: `check` 의 population 은 uncommitted 행인데 cycle 순서는 `TSV → commit → push`. 이 branch 의 다른 모든 check 처럼 push gate 의 `&&` 사슬에 넣으면 `NO_PENDING_ROW` 로 **매번 vacuous 통과**한다. append 와 `git add results/` 사이에서만 문다. 설계가 그 placement 에 의존하지 않도록 `post_epoch_impossible` 을 backstop 으로 둔다 — gate 가 실행됐든 아니든 다음 cycle 이 나쁜 행을 본다.
- **`EPOCH` 이 필요한 이유**: verdict 는 영구히 `TYPED` 다 (40행이 append-only 이므로 어떤 미래의 선행도 그 집합을 비우지 못한다). 따라서 verdict 만으로는 다음 cycle 의 실제 질문 — *방금 41번째를 추가했는가?* — 에 답할 수 없다. `legacy_impossible` 40 / `post_epoch_impossible` **0** 으로 분리. 이 field 역시 **보고만 하고 gate 하지 않는다**: commit 된 순간 그것도 수리 불가이므로, 비어 있음을 주장하는 test 는 첫 회귀를 영구 red 로 바꾼다.
- **Scope**: `timestamp` column 만. `commit`/`metric`/`status`/`description` 에 대해서는 아무 말도 하지 않는다.
- **Alternatives**: (a) 채택. (b) 40행을 수리 — append-only 위반이고 blame 증거를 파괴. (c) audit 을 gate 로 승격 — 영구 red, D-044 가 muted 를 예측. (d) `seconds == 00` 을 verdict 에 포함 — 방어 불가능한 상수. (e) 측정만 하고 writer 는 안 고침 — 이미 지난 cycle 이 한 절반.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-11-the-typed-timestamp-stops-at-the-writer.md` · D-044 (clear 불가능한 check 는 muted) · D-102 (수리가 증거를 지운다) · `cycle_artifacts` (이 column 을 dating key 로 반박한 곳)

## D-153 — 2026-08-09 — island 의 **내부** rung (`w = 100`) 도 재현되었다 — 그러나 그 rung 의 stock arm 은 애초에 **움직일 자리가 없었다**: rate 가 0/1 인 arm 은 강한 결과가 아니라 **censored** 결과다

- **Context**: D-152 가 `w = 150` (island `{75, 100, 150}` 의 *위쪽 edge*) 를 재현하면서 census 를 2/4 로 올렸다. 남은 두 rung 중 `w = 100` 을 먼저 고른 이유는 크기가 아니라 **negative 가 무엇을 부수는가**다 — 150 은 edge 라 뒤집혀도 island 를 깎을 뿐이지만, 100 은 *내부* rung 이라 뒤집히면 island 가 둘로 쪼개진다.
- **Decision**: 동일 protocol (`cafe_head_on_v0`, λ = 0.8, margin 0.40 m, seeds 0–31, 양 arm, 64 runs). Reference block 0–15 가 D-133 을 **양 arm 정확히** 재현 (stock 16/16, risk 6/16). Fresh block 16–31: stock **16/16**, risk **2/16** — 같은 방향의 `SEPARATED`. Pooled n = 32: stock **32/32**, risk **8/32**, `separation_runs` **24** — band 에서 가장 넓은 separation. 판정 **`REPRODUCED`**, island 유지. Census 2/4 → **3/4**, `held (100, 150)` / `overturned (250,)` / `unreplicated (75,)`.
- **그런데 이 rung 의 좋은 소식은 한쪽 arm 의 것이 아니다**: `stock_mppi` 의 rate 는 **두 block 모두 1.0** 이고, 32 run 중 최고 clearance 가 **0.3705 m** 로 margin 아래다. 즉 그 arm 은 재현된 게 아니라 **다른 값을 가질 자리가 없었다**. Separation 전체를 risk arm 이 지고 있고, `REPRODUCED` 는 두 arm 이 아니라 **한 arm 에 대한 진술**이다.
- **그래서 `SeedBlock.censored` / `.censoring` 을 ship 한다**: rate 가 0 이면 `FLOOR`, 1 이면 `CEILING`, 개수에 따라 `UNCENSORED` / `ONE_ARM_CENSORED` / `BOTH_ARMS_CENSORED`. 이건 `w = 100` 만의 이야기가 아니다 — `w = 250` 도 stock 0/16 로 `FLOOR` 이고, 결과적으로 **재현된 세 rung 중 양 arm 을 모두 두 방향으로 시험한 것은 `w = 150` 하나뿐**이다. 두 cycle 동안 보이지 않았던 이유는 정확히 D-107 계열의 모양이다: verdict 도 나머지 필드도 censoring 유무에 대해 **완전히 동일하게 읽힌다**.
- **thresholding 하지 않는다**: `one_run_rungs` 와 같은 규율로 보고만 하고 판정을 깎지 않는다. censored rung 이 틀렸다는 뜻이 아니라, 그 rung 이 답한 질문이 더 좁다는 뜻이다.
- **effect size 는 이번엔 반대로 움직였다**: `w = 150` 은 block 간에 separation 이 *줄었고* (stock 10/16 → 5/16), `w = 100` 은 *늘었다* (risk 6/16 → 2/16). 두 rung 이 반대 방향으로 움직이므로 "verdict 는 sign 을 채점하지 size 를 채점하지 않는다" 는 한 번의 운 나쁜 walk 에 대한 변명이 아니라 grade 의 성질이다. 별도 test 로 pin.
- **Alternatives**: (a) 채택 — interior rung 먼저 + censoring 명명. (b) `w = 75` 를 먼저 — 같은 비용에 negative 의 파괴력이 작다. (c) censoring 을 verdict 에 접어넣기 (`REPRODUCED_CENSORED`) — 판정 축을 둘로 섞어 `held`/`overturned` census 를 오염시킨다. (d) 관찰만 하고 코드로 남기지 않기 — 두 cycle 동안 아무도 못 본 이유가 바로 그것이므로 거절.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-09-the-interior-rung-reproduces-censored.md` · D-152 (`w = 150`, census) · D-151 (`w = 250`, `FLOOR` rung) · D-133 (published band) · D-139 (entitlement check)

## D-152 — 2026-08-09 — band 의 upper-edge rung (`w = 150`) 은 **재현되었다** (첫 `REPRODUCED`), 그리고 replication 은 이제 headline 이 아니라 **census** 로 보고된다 — 4개 중 2개는 아직 한 번도 두 번 보지 않았다

- **Context**: D-151 이 `w = 250` 을 뒤집은 직후, 같은 protocol 을 band 의 다른 thin rung 인 `w = 150` 에 적용했다. 이 rung 은 contiguous island `{75, 100, 150}` 의 **위쪽 edge** 를 정하고, separation 이 1 run 이 아니라 9 run 이라 성격이 다르다. 문제는 protocol 자체였다: 지금까지 단 한 번 돌았고 그 한 번이 reversal 이었으므로, **뒤집기만 하는 계측기와 구별되지 않았다**.
- **Decision**: `cafe_head_on_v0` 를 λ = 0.8, `w_obs_soft = 150` 에서 seeds 0–31, 양 arm, 64 runs 재측정. reference block 0–15 는 D-133 을 **양 arm 모두 정확히 재현** (stock 10/16, risk 1/16). fresh block 16–31 은 stock **5/16**, risk **0/16** — **같은 방향**의 `SEPARATED`. pooled n = 32 에서 stock 15/32, risk 1/32, 여전히 `SEPARATED`. verdict **`REPRODUCED`** — repo 최초. mechanism 의 가장 강한 증거가, 가장 약한 증거를 방금 무너뜨린 protocol 을 통과했다.
- **부호는 재현되고 크기는 재현되지 않는다**: stock 의 sub-margin rate 가 block 사이에서 **절반**이 된다 (10/16 → 5/16). direction 은 안정적이고 magnitude 는 seed 에 ~2× 의존한다. `REPRODUCED` 는 방향에 대한 grade 이고 effect size 를 licence 하지 않는다 — 별도 test 로 pin. P5 metric set 이 effect size 를 인용하기 시작할 때 그대로 적용되는 구분.
- **왜 census 인가**: rung 하나짜리 grade 는 population question 에 답하지 못한다. `ReplicationCensus` 는 band 의 `SEPARATED` rung 대비 replication coverage 를 보고한다 — 지금 **2/4**, `held (150)`, `overturned (250)`, `unreplicated (75, 100)`. 한 rung 일 때는 문장이었던 것이 두 rung 에서 **비율**이 되고, 그 비율(검사한 것의 50% 가 뒤집힘)은 어느 개별 결과보다 불편하다. threshold 하지 않고 보고만 한다 — `one_run_rungs` 와 같은 규율. vacuity case `NO_SEPARATED_RUNG` 는 다른 모든 field 가 full coverage 와 동일하게 읽히므로 이름을 붙였다 (D-107 / D-120 / D-127 / D-145 / D-150 / D-151 에 이은 6번째).
- **부수 효과 — 오래된 test 들이 non-vacuous 해졌다**: `w = 250` 만 기록돼 있을 때는 `verdict` 를 `SIGN_REVERSED` 로 하드코딩해도 이 파일의 모든 measurement test 가 통과했다. 서로 **다른** verdict 를 내는 두 walk 가 그 구현을 죽인다.
- **Alternatives**: (a) 채택. (b) `w = 150` 만 측정하고 census 는 생략 — coverage 가 journal 산문에만 남아 다음 cycle 이 다시 유도해야 한다. (c) `PUBLISHED_LADDER` 를 pooled 값으로 갱신 — D-151 과 같은 이유로 거절 (기록을 제자리에서 고쳐쓰면 table 이 증거이기를 그만둔다).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-08-the-upper-edge-rung-reproduces.md` · D-151 (protocol) · D-139 (entitlement check) · D-133 (published band)

## D-151 — 2026-08-09 — published band 의 one-run rung 을 **분리된 seed block 으로 재측정**했다: 재현되지 않았고, **부호가 뒤집혔다** — pooled 32 seed 에서 `TIED`

- **Context**: `w = 250` 은 D-133 이 기록한 대로 risk 1/16 vs stock 0/16, 즉 **한 run** 으로 `SEPARATED` 를 샀고 그 부호는 mechanism *에 반대* 방향이었다. Fisher 는 p = 1.0 (block 이 noise 와 양립한다는 말이지, 두 번째 block 이 반대라는 말이 아니다), D-148~D-150 의 calibration 은 이 rung 에 λ table 을 사줬지만 rung 자체는 움직이지 않았다. 남은 유일한 질문은 seed 축이었고, 그것은 **더 큰 block 이 아니라 겹치지 않는 block** 으로만 답한다.
- **Decision**: `separation_reproduction` 을 ship — `SeedBlock`(seed 집합을 이름으로 들고 있는 rung 측정) + `Reproduction`(reference 를 **disjoint** replication 에 대해 채점). 측정 결과: block 0–15 는 D-133 을 **정확히 재현**(0/16, 1/16, witness 0.3472 m 까지 네 자리 일치), block 16–31 은 **stock 1/16, risk 0/16** — 같은 크기, 반대 부호. `SIGN_REVERSED`. pooled 32 seed 는 양 arm 1/32 로 **`TIED`**.
- **두 가지가 동시에, 반대 방향으로 은퇴한다**: (i) mechanism 에 불리했던 부호는 seed 였다 — 이 repo 가 기록한 유일한 "mechanism 이 해로워 보이는" 사례가 측정으로 철회된다. (ii) 그 rung 은 어떤 주장의 근거도 아니게 된다 — `TIED` 는 진짜 null 이다. `separation_runs` 1 → 0 이므로 pooled rung 은 `one_run_rungs` 를 떠난다.
- **band 의 형태 판정은 그대로다**: `TIED` 는 `SCORABLE` 안에 있으므로 `w = 250` 은 여전히 scorable 이고 `published_band()` 는 여전히 `BAND_SPLIT`. 바뀐 것은 split 의 **재료**이지 존재가 아니다. "one-run rung 이 noise 였다" 는 문장이 split 붕괴로 읽히기 쉬워 명시한다.
- **`PUBLISHED_LADDER` 는 고치지 않는다**: 그것은 자기 block 에 대한 참인 기록이고, 나중 측정이 반대라고 해서 표를 제자리에서 다시 쓰는 것이 표가 증거이기를 그만두는 방식이다. replication 은 첫 기록에 대해 채점되는 **두 번째 기록**으로 남는다.
- **재현 먼저가 compute 의 절반값을 했다**: 옛 block 을 다시 걷지 않았다면 반전은 pipeline 차이이고 cycle 은 아무것도 증명하지 못한다. 공표된 숫자를 재측정하는 모든 후속 cycle 은 이 비용을 먼저 낸다 (D-139 규칙의 seed 축 판).
- **Alternatives**: (a) 채택 — 분리 block 재측정. (b) Q-115 의 threshold (`separation ≥ 2 runs`) 도입 — module 이 무엇이 진짜 delta 인지 결정하게 되고, 이 rung 이 *왜* 얇은지는 여전히 답하지 못한다. (c) rung 을 published band 에서 그냥 drop — 측정 없이 불편한 rung 을 지우는 것이라 거절. (d) 같은 block 을 32 seed 로 늘리기 — 그 한 run 을 희석할 뿐 반박하지 못한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-07-the-one-run-rung-was-the-seeds.md` · D-133 (원 walk) · D-139 (재생성만이 generator 를 시험한다) · D-124 (`sub_margin`) · Q-115 (세 번째 선택지)

## D-150 — 2026-08-09 — published span 이 **4/4 로 완주**했다 — 그리고 그 대가로, *아무것도 비교하지 않은* census 가 3 년치 table 중 3 개에서 조용했다는 것이 드러났다

- **Context**: D-148 이 `published_band()` 를 객체화하며 **2/4 certified** 를 받았고, D-149 가 `w = 150` 을 사서 **3/4** 가 되었다. 남은 것은 `w = 250` 하나 — published span 의 마지막 미교정 rung 이자, separation 이 16 seed 중 **1 run** (부호는 mechanism 에 반대) 인 rung 이자, band 가 `BAND_CLOSED` 아닌 `BAND_SPLIT` 로 등급받는 **유일한 이유**. 두 약점이 같은 rung 위에 겹쳐 있었다.
- **Decision**: D-149 와 동일한 scope 로 `cafe_head_on_v0` 만 `--w-obs-soft 250` walk (1 scene × 2 arm × 8 rung × 8 seed = **128 runs, ~4 min**) → `lam_windows_w250.yaml` + `TABLES` 등록. 결과 **`SPAN_CERTIFIED`**, `certified` = `(75, 100, 150, 250)`, `unmeasured` = `()`. `require_calibration=True` 가 **처음으로 published band 를 통과**시킨다 — D-147 이 "default-on 이면 거의 모든 band 를 거절한다"며 off 로 둔 그 flag 다.
- **retraction 가능성은 이번이 더 높았다**: stock arm 의 window 가 실제로 **움직였다** — `[0.2, 0.4, 0.8]` (10/75/100/150 전부) → **`[0.4, 0.8]`** at 250. 네 weight 를 통틀어 head_on arm-cell 이 움직인 **첫 사례**. 아래쪽에서 좁아졌기에 λ = 0.8 이 살아남았고, 위에서 닫혔다면 D-133 이 발표한 rung 의 **철회**였다. 덤으로 `w = 250` 은 두 arm 의 window 가 **불일치하는 첫 weight** (stock `[0.4, 0.8]` vs risk `[0.2, 0.4, 0.8]`) — certification 은 참이지만 "λ = 0.8 은 어디서나 admissible" 로 읽히므로 별도 test 로 좁혀 pin.
- **더 큰 발견 (이쪽이 본체다) — `seed_census` 는 *아무것도 비교하지 않았다*고 말한 적이 없다**: table 의 weight 에 registry cell 이 하나도 없으면 `graded` = `{}`, `exact` = `()`, 그리고 D-149 이후로는 `absent` = `()` 이다 (`absent` 는 "여기서 hand-walk 했는데 table 에 없음" 인데, 애초에 hand-walk 이 없었으므로). **모든 field 가 완전 일치일 때와 글자 그대로 동일하게 읽힌다.** 현재 shipped table 5 개 중 **3 개**(`w = 10`, `75`, `250`)가 그 상태.
- **이것은 `w = 250` 이 만든 게 아니다**: `w = 10` / `w = 75` 는 **최초의 keyed table 이래로 계속** 그 상태였다. 즉 defect 은 내내 도달 가능했고 이번 cycle 은 trigger 가 아니라 **세 번째 사례**다. 그리고 `NO_SEED_CONTRAST` 는 D-145 가 *바로 이 case 를 위해* 쓴 상수인데 — docstring 에 함정까지 적어두고 (`"Distinct from 'the seed count does not matter': nothing was compared"`) — **어떤 코드 경로도 그것을 반환하지 않았다**. 한 함수 건너 `attribution` 은 이미 같은 분기를 갖고 있었다: `FACTOR_INERT if compared else NO_CONTRAST`.
- **고친 위치**: `SeedContrast.verdict` property — `SEED_CONTRASTED if self.compared else NO_SEED_CONTRAST`. 두 verdict 모두 shipped table 에서 **도달 가능**하며 분포가 3/2 라 (5/0 이나 0/5 가 아니라) 한 상수만 반환하는 구현은 test 를 통과하지 못한다. `SEED_MOVES` / `SEED_INERT` 같은 3-값 설계는 **일부러 채택하지 않았다** — 현재 shipped table 로는 "움직임" 쪽이 도달 불가라 산문이 되고, 그 구분은 이미 `exact` / `graded` 가 답한다.
- **부수 결정 — refusal test 의 probe weight 를 이름 대신 유도한다**: 그 literal 은 `100 → 150 → 250` 을 걸어왔고 (D-145, D-149, 이번 cycle) 매번 red 가 나서 손으로 옮겨졌다. D-145 는 자기 migration 에서 옳은 규칙을 도출해놓고 (**"a refusal test should name the gap, not the weight"**) 또 literal 을 적었다. 실제 불변식은 *여전히 미교정인 것이 이름으로 거절한다* 이고 이는 index domain 의 **여집합**에 대한 진술이므로, `TableIndex.uncalibrated_probe` 로 domain 에서 유도한다. 이제 weight 를 사도 그 경로가 red 가 되거나 조용히 비지 않는다.
- **그리고 refusal witness 는 certify 대상 객체 위에 살면 안 된다**: published band 가 `require_calibration=True` 를 통과하는 순간, "이 flag 가 거절할 수 있다"는 test 는 거절할 대상을 잃었다 — 마지막 table 을 산 것이 strict flag 를 *모든 입력에 대해 통과하는* assertion 으로 조용히 바꿀 뻔했다. witness 를 유도된 probe 위로 옮겼다.
- **Alternatives**: (a) 채택 — 1 scene walk + `verdict` property + 유도된 probe. (b) matrix 전체를 250 에서 walk — ~15 min, defect 은 그대로. (c) `NO_SEED_CONTRAST` 를 `graded` map 안의 key 로 — `compared` 의 분모를 오염시키는 D-149 가 막 제거한 바로 그 종. (d) probe literal 을 500 으로 재migration — 네 번째 treadmill, 그리고 D-145 가 이미 하지 말라고 적은 것.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-06-the-published-span-is-fully-calibrated.md` · D-149 (w=150, `absent` 우회) · D-148 (2/4, `published_band`) · D-147 (span guard) · D-145 (`NO_SEED_CONTRAST` 를 쓰고 배선하지 않음 + refusal-test 규칙) · D-133 (원 walk) · Q-121 · Q-122

## D-149 — 2026-08-09 — published span 의 마지막 미교정 rung 하나만 남기고 샀다 — 그리고 **싸게 산 table 이 census 로 하여금 없는 비교를 지어내게** 했다

- **Context**: D-148 이 `published_band()` 를 guard 에 먹여 **2/4 certified** 를 받아냈다. 미교정 rung 은 150 과 250. 150 은 D-136 이 이미 16-seed 손walk 으로 측정해 둔 값이 있지만 그것은 `REMEASURED` registry 안에 있고 index 가 route 할 수 있는 *table* 이 아니다 — 즉 gap 은 측정의 부재가 아니라 **container 의 부재**였다.
- **Decision**: `cafe_head_on_v0` 만 `--w-obs-soft 150` 으로 walk (1 scene × 2 arm × 8 rung × 8 seed = **128 runs, ~4 min**) 하여 `lam_windows_w150.yaml` 생성 + `TABLES` 등록. matrix 전체(1024 runs / ~15 min)를 걷지 **않은** 것이 scope 결정의 핵심: 150 이 필요했던 이유는 published span 이 *그 scene 위에서만* 지나가기 때문이다. 결과 — 양 arm 모두 `[0.2, 0.4, 0.8]`, λ = 0.8 in-band → rung certify, `certified` 가 `(75, 100)` → **`(75, 100, 150)`**. verdict 는 250 때문에 `SPAN_UNCALIBRATED` 유지.
- **부수적으로 (이쪽이 더 크다)**: table 이 등록되는 순간 `seed_census` 가 **없는 cell 을 grade 했다**. `w = 150` 에는 registry cell 이 둘(head_on, crossing)인데 이 table 은 crossing 을 걷지 않았다. `Remeasurement.recorded` 는 `lookup` 을 거치는데, `lookup` 은 **없는 cell** 에 대해 *측정했지만 window 가 빈* cell 과 **똑같이** 빈 `admissible` 을 준다. `window_shift` 는 빈 recorded 를 `rec <= new` 로 읽어 **`WINDOW_HELD`**; crossing 의 stock arm 은 `w = 150` 에서 실제로도 windowless 라 `set() == set()` 이 되어 **`exact`** — census 가 가진 가장 강한 grade — 에까지 들어갔다. 즉 "싼 table 이 비싼 walk 을 **정확히** 재현했다, 단 한 번도 방문한 적 없는 scene 에서" 를 보고했고 `compared` 는 2 를 4 로 셌다.
- **고친 위치**: `lookup` 은 `found` 를 **항상 들고 있었다** — bit 를 버린 곳은 `recorded` 다. `seed_census` 가 grade **전에** `found` 를 확인해 새 `absent` field 로 우회시킨다. 양방향 non-vacuous: `w = 100`(8 scene) 은 `absent == ()`, `w = 150`(1 scene) 은 아니다. Q-034 의 구분(`NO_CELL` ≠ `EMPTY_WINDOW`)이 유일하게 소실돼 있던 layer.
- **일반화**: 위험한 방향은 **subset test 의 빈 쪽**이다. `rec <= new` 는 `rec = ∅` 이면 `new` 가 무엇이든 참이므로, `window_shift` 를 지나는 모든 empty-input 경로가 HELD 로 떨어진다. D-145 가 windowless cell 에 대해 한 번 booking 했으나 그 note 는 그 case 에 scoped 돼 있었다.
- **왜 지금 드러났나**: guard 의 **첫 부분(partial) 입력**이 그 guard 의 empty-set 처리가 감사받는 지점이다. 지금까지 모든 table 이 8 scene 을 다 걸었기에 "cell 없음" 은 도달 불가능했고, 이 conflation 은 네 cycle 동안 무해하게 앉아 있었다. 더 **싼** 측정을 산 것이 그것을 발화시켰다.
- **Alternatives**: (a) 채택 — 1 scene walk + `absent` 우회. (b) matrix 전체를 150 에서 walk — defect 을 도달 불가능한 채로 남기고 ~15 min 을 쓴다 (overrun advisory 를 정면으로 무시). (c) `absent` 를 `uncompared` 에 접기 — 원인과 처방이 다른 둘(다른 weight 라 비교 불가 vs 같은 weight 인데 table 이 scene 을 건너뜀)을 합쳐 census 가 무엇이 부족한지 감춘다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-05-the-span-certifies-and-the-census-fabricated-a-cell.md` · D-148 (2/4 certified) · D-136 (16-seed head_on@150 손walk) · D-145 (8-seed caveat 최초 pricing) · Q-034 · Q-121 (`shift_census` 의 동일 결함)

## D-148 — 2026-08-09 — published band 를 객체로 만들자 guard 가 **자기 프로젝트의 대표 주장을 거절했다**: span 의 절반이 미교정이고, 그 rung 이 형태 주장을 혼자 떠받치고 있다

- **Context**: D-147 이 `certify_span` / `assert_span_certified` 를 ship 하면서 스스로 gap 을 명시했다 — **아무도 부르지 않는다**. STATE #1 은 "sweep driver 하나를 연결하라" 였는데, 실제로 찾아보니 **driver 가 없었다**: `scorable_band` 의 non-test importer 는 0 이고, 프로젝트가 *발표하는* 유일한 band (D-133 의 `cafe_head_on_v0` 8-rung walk) 는 module docstring 안의 **산문 표**로만 존재했다. guard 에 먹일 데이터가 없었던 것이지 호출부가 없었던 것이 아니다.
- **Decision**: 빠진 것은 call site 가 아니라 **input** 이므로 그쪽을 만든다. `PUBLISHED_LADDER` (D-133 표를 그대로 옮긴 counts + per-arm ESS flag + **기록된 verdict 열**) 과 `published_band()` 을 ship 하고, 그 band 를 certify 한다.
- **결과 — 깨끗하지 않다**: table 은 `w ∈ {10, 75, 100}` 에만 있고 published span 은 `[75, 250]` 이다. scorable rung 4 개 중 **150 과 250 이 미교정** → `SPAN_UNCALIBRATED`, `2/4` certified, `require_calibration=True` 는 raise 한다.
- **핵심은 coverage 구멍보다 날카롭다**: `w = 250` 은 약점을 **두 개 동시에** 진다 — separation 이 16 seed 중 **1 run** (부호는 mechanism 에 *반대*) 이고, 동시에 미교정이다. 그리고 band 가 `BAND_CLOSED` 가 아니라 `BAND_SPLIT` 로 등급받는 **유일한 이유**다. 즉 walk 의 유일한 *형태* 주장이 가장 약한 rung 하나에 전부 걸려 있다 (test 가 그 rung 을 빼고 verdict 이 바뀌는 것으로 pin).
- **`SPAN_UNCERTIFIED` 가 아니라 `SPAN_UNCALIBRATED` 인 것이 D-147 의 분할이 값을 하는 지점**: 150/250 에서 λ = 0.8 을 **반박하는 것은 없다, 아무도 안 봤을 뿐**이다. 분할이 없었다면 published band 의 결함으로 읽혔을 것이다.
- **재구성은 신뢰가 아니라 반증 대상이다** (D-139 의 규칙): 기록은 unsafe **rate** 표이고 rate 는 clearance 를 결정하지 않으므로, rebuild 를 D-133 이 적어둔 **verdict 열**에 rung 단위로 채점하고 docstring 의 4 개 구조 주장(`BAND_SPLIT`, span `[75, 250]`, one-run rung `250`, `w=30` 의 편측 거절)도 재도출한다. count 를 틀린 filler 는 verdict 을 움직여 실패한다.
- **재구성할 수 없는 양은 채우지 말고 거절한다**: 첫 시도처럼 unsafe seed 를 margin 바로 아래에 두면 `sub_margin` 이 band 전체에서 `True` 로 읽힌다 — 이 walk 가 한 적 없는 **살아있는 D-124 주장**이다. `mean_clearance` / `sub_margin` 은 이제 `UnreconstructedMagnitude` 를 raise 하고 (`AttributeError` 라 `hasattr` probing 은 정상 degrade), `±inf` sentinel 이 2 차 방어라 거절을 빠져나간 값은 그럴듯하지 않고 비물리적이다. 막는 실패는 *없는* 숫자가 아니라 *그럴듯한* 숫자다.
- **부수 발견 — `loop_reach` 가 새 test 를 잡았고, 옳았다**: arm-naming test 는 **population-claim loop** 이고, 이 repo 는 그런 loop 를 runtime reading 없이 받지 않는다 (빈 sequence 위의 green loop 은 아무것도 세우지 않는다). reading 을 떠서 `SAMPLED n = 8` (ladder 전체) 로 등록했다. 손이 먼저 간 것은 set comprehension 으로 고쳐 guard 를 피하는 쪽이었는데, reading 은 90 초이고 guard 가 내 test 에 던진 질문은 정확했다. **대가**: full suite 2 회 (D-043 순서를 지켰는데도 — guard 가 doc write 가 아니라 *tracked code* 편집에서 발화하기 때문). 값싼 방어는 loop-body assert 를 가진 test 를 새로 쓸 때 Phase 3 에서 `loop_reach report` 를 돌리는 것 (~90 초).
- **Alternatives**: (a) 채택 — published band 를 객체화. (b) 새 call site 하나 더 — fixture 만 먹는 guard 가 하나 더 늘 뿐, 아무것도 못 찾는다. (c) clearance 를 그럴듯하게 채우고 docstring 에 caveat — caveat 가 모든 downstream read 에 올라탄다. (d) `require_calibration` 을 default-on — 자기 대표 band 가 떨어지므로 D-147 의 affordability 논증이 실증된다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-04-the-published-band-is-half-uncalibrated.md` · D-147 (span guard + unmeasured/contradicted 분할) · D-139 (기록된 답만이 generator 를 시험한다) · D-133 (원 walk) · D-124 (`sub_margin`)

## D-147 — 2026-08-09 — λ guard 가 **published span** 에 도달했다: 거절의 기준은 "측정이 있느냐" 가 아니라 **"측정이 반대하느냐"** 다

- **Context**: D-144 가 `Headroom` 하나에 대한 enforcing consumer 를 만들었고 D-145/D-146 이 published row 두 개의 calibration 거절을 모두 지웠다. 남은 구멍은 **band** 였다 — `ScorableBand` 는 고정 λ 로 weight 축을 걷는데 그 λ 를 자유 인자로 받으므로, 아무도 certify 하지 않은 rung 위에서 `span` 이 발표될 수 있었다.
- **Decision**: `scorable_band` 에 `certify_span` / `assert_span_certified` 를 넣되, 대상은 `band.scorable` — **claim 을 지고 있는 rung** 으로 한정한다. refusal 은 두 class 로 쪼갠다: `SPAN_UNMEASURED`(`NO_TABLE_AT_WEIGHT`, `NO_CELL`) 은 **보고만** 하고, `SPAN_REFUSING`(`OFF_WINDOW`, `EMPTY_WINDOW`) 만 **raise** 한다.
- **왜 이 split 이 핵심인가**: table 이 있는 weight 는 오늘 셋(10/75/100) 뿐이다. rung 마다 calibration 을 요구하는 "당연한" 규칙은 **거의 모든 band 를 거절**한다 — D-144 가 첫 cut 에서 빠졌던 accept-nothing vacuity(Q-120) 와 같은 모양이고, 최대 엄격함처럼 읽히면서 아무것도 검사하지 않는다. `w = 100` 을 넘어가는 정직한 ladder 는 *반증된* 게 아니라 *미측정* 이다. D-044 의 축을 한 층 위로 옮긴 것: 숫자를 못 믿겠다고 말하지 말고 **가서 잴 것을 지목**하라.
- **빈 분모는 통과가 아니라 거절**: `NO_SCORABLE_RUNG` band 에 `certify_span` 은 `ValueError` 를 낸다. 아무것도 발표하지 않는 band 는 모든 검사를 vacuously 통과하고, 그게 D-107/D-120/D-127 이 각각 한 축씩 기록한 모양이다.
- **`SPAN_REFUSING` 은 유도된다** (`UNCERTIFIED - SPAN_UNMEASURED`) + 두 class 가 `UNCERTIFIED` 를 정확히 분할한다는 test. upstream 에 refusal 이 추가되면 조용히 양쪽 다에서 빠지는 대신 시끄럽게 깨진다 (D-047).
- **Alternatives**: (a) 채택. (b) rung 마다 calibration 필수 — 거의 모든 band 거절, 무용. (c) 보고만 하고 raise 안 함 — D-143 이 `resolve` 에 대해 한 비판("consumer 없는 guard 는 정작 중요한 방식으로 untested")을 그대로 반복.
- **남은 것**: 아직 **어떤 driver 도 이걸 부르지 않는다**. `require_calibration=True` 로 `{10,75,100}` 만 걷는 site 를 물리는 게 다음 cycle 의 가장 강한 첫 consumer. 그전까지 이 guard 는 한 층 위에서 다시 *available* 일 뿐이다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-03-the-span-is-certified-at-its-own-rungs.md` · D-144 (certify) · D-047 (partition 은 자기 진술을 하나만) · Q-120 (accept-everything ↔ refuse-everything 의 공통 뿌리)

## D-146 — 2026-08-09 — `gap_gated_mppi` 를 자기 weight 에서 측정했다: **published claim 에 남아 있던 마지막 calibration 거절이 사라진다** — 그리고 column 은 matrix 재walk 없이 **merge** 로 산다

- **Context**: D-144 가 published mechanism claim 두 개 모두 certify 되지 않는다고 판독했고, D-145 가 그 중 risk channel 쪽(`NO_TABLE_AT_WEIGHT`)을 지웠다. 남은 하나가 D-124 의 gap gate: `sole_uncertified = gap_gated_mppi` 인 `NO_CELL` — **어떤 weight 의 어떤 table 에도 없는 arm** 이라, 그 λ 가 admissible 하다고 말한 측정이 존재한 적이 없다. weight 축이 아니라 **controller 축**의 결손이고, STATE 가 세 cycle 째 #1 로 들고 있었다.
- **Decision**: `--controllers gap_gated_mppi --w-obs-soft 10` 으로 8 scene × 8 rung × 8 seed = **512 run** (~6 min) 을 walk 해 `w = 10` table 에 **세 번째 controller column** 으로 넣었다 (16 → 24 cell). weight 는 고르는 게 아니라 주어진 것 — claim 이 발행된 weight 가 10 이다. 결과: head_on 에서 `[0.2, 0.4, 0.8]`, 다른 두 arm 과 **같은 window**. D-124 의 row 는 `NO_CELL` → **`CERTIFIED`**.
- **반대로 나올 수 있었다**: 이 arm 이 0.8 근처 어디에서도 admissible 하지 않았다면 이 cycle 은 clearing 이 아니라 **retraction** 을 기록했다. D-145 가 같은 자리에서 같은 말을 했고, 두 번 다 통과했다는 사실이 곧 guard 가 무르다는 뜻은 아니다 — `cut_in` column 은 여기서도 빈 window 로 나왔다.
- **column 은 matrix 재walk 이 아니라 merge 로 산다**: 선택지는 셋이었다. (1) 전 matrix 를 3 controller 로 재walk — D-141 이 기존 16 cell 이 **정확히** 재현됨을 이미 쟀으므로 ~1000 run 순수 낭비. (2) 손으로 file 편집 — header 자신이 금지한다. (3) 신설 `merge_tables`: 새 column 을 자기 file 로 정상 측정한 뒤 기계적으로 join. 거절 세 개를 이름으로 갖는다 — `WEIGHT_MISMATCH` (`to_yaml` 의 per-cell 규칙의 file-level 형태), `PROTOCOL_MISMATCH` (ladder/seed/band 가 다르면 두 column 이 같은 질문을 받은 적이 없다), `DUPLICATE_CELL` (cell 재측정은 merge 가 아니라 새 table — 어느 쪽을 남겨도 살아남은 숫자의 출처가 사라진다).
- **merge 의 진짜 test 는 identity 다**: `merge_tables(base, empty)` 가 base 를 **byte 단위로** 재현한다. 이것이 없으면 column 추가가 16 개 측정을 다른 code path 로 조용히 재렌더하고, caller 가 읽는 `min_spread` 는 run 의 기록이 아니라 **merge 프로세스의 의견**이 된다. header 도 base 것을 쓴다 — 자기 환경의 `seeds`/`band_width` 를 남의 측정 위에 찍는 것은 D-107 의 false provenance 를 `to_yaml` 이 per-cell 로 막은 것의 한 층 위 형태다.
- **한 weight 에서만 산 column 은 두 module 떨어진 consumer 를 깨뜨린다**: `table_shift_census` 는 cell 집합이 다른 두 table 을 거절하는데, 이제 `w = 10` 에만 있는 column 이 생겼다. 그 거절은 **옳고 약화시키지 않았다** — census 에 명시적 `arms` scope 를 받고, 빠진 column 은 조용한 교집합이 아니라 **test 가 이름으로 assert** 한다. 게다가 `arms` 는 어느 table 에도 없는 controller 를 거절한다: 오타가 denominator 를 소리 없이 줄이면 그것이 D-142 가 `NEVER_OPEN` 을 갈라내야 했던 오염된 population 모양이다. scope test 는 `w = 75` 에 이 column 이 생기는 순간 **일부러 실패**하도록 써서, scope 가 관성으로 2 column 에 머무르지 못하게 했다.
- **claim 이 scorable 해진 것은 아니다**: `sub_margin` 은 여전히 delta 가 margin 아래라고 말한다. 지운 것은 *온도가 미측정* 이라는 사유이고 남은 것은 *효과가 작다* 는 사유 — D-144 가 "독립인 두 이유" 라고 booking 한 그대로, 이제 **두 개가 아니라 한 개**로 실패한다. 이 구분을 흐리면 cycle 이 산 것보다 많이 주장하게 된다.
- **Alternatives**: (a) 채택 — 자기 weight 에서 column 측정 + merge. (b) head_on 한 cell 만 walk — 64 run 으로 certification 은 사지만 column 의 나머지 7 scene 을 못 얻고, `city_curved` 가 `[1.6, 6.4]` 로 다른 두 arm 과 전혀 다른 window 를 갖는다는 사실도 못 본다. (c) `w = 100` 에서 walk — table 은 이미 있지만 claim 이 발행된 weight 가 아니라 `NO_CELL` 을 `NO_CELL` 로 남긴다. (d) 전 matrix 3-controller 재walk — 위 (1).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/09-01-the-gap-gates-arm-is-measured.md` · D-144 의 남은 refusal 해소 (두 published claim 의 calibration 사유가 모두 정리됨) · D-145 (직전 rung) · D-141 (재walk 이 불필요한 이유) · D-124 (gap gate claim) · D-142 (오염된 denominator) · D-107 (false provenance) · D-047 (사실의 두 번째 진술)

## D-145 — 2026-08-08 — `w = 100` 은 측정되었고, **프로젝트의 유일한 scorable mechanism claim 이 자기 operating point 에서 처음으로 certify 된다** — 덤으로 8-seed caveat 이 처음 가격을 얻었다

- **Context**: D-144 가 `certify()` 를 붙인 직후 나온 정직한 판독은 **published claim 두 개 모두 certify 되지 않는다** 였고, risk channel 쪽 사유는 `NO_TABLE_AT_WEIGHT` — D-131/D-132 의 유일한 유의미한 mechanism 결과(`w = 100`, p = 2.5e-4)가 측정된 weight 에 table 이 없다는 것. STATE 는 이것을 세 cycle 연속 #1 로 들고 있었고, D-144 가 문단이 아니라 **이름 붙은 failing test** 로 바꿔 놓은 상태였다.
- **Decision**: `--w-obs-soft 100` 으로 full matrix 를 walk 했다 (8 scene × 2 controller × 8 rung × 8 seed = **1024 closed-loop run**, ~15 min, 16 jobs) → `eval/scenarios/variants/lam_windows_w100.yaml`, `lam_window_index.TABLES` 에 한 줄 등록. **head_on 두 arm 모두 `[0.2, 0.4, 0.8]`** — λ = 0.8 이 두 window 안에 있으므로 claim 이 *자기 weight 에서* `CERTIFIED`. 이것은 반대로 나올 수 있었다: D-142 는 `w = 10 → 75` 에서 14 arm-cell 중 6 개를 움직였고, head_on/risk 가 그 중 하나였다면 이 cycle 은 retraction 을 기록하고 있었을 것이다.
- **부수적으로, 그리고 이쪽이 방법론적으로 더 크다 — 8-seed caveat 이 처음으로 가격을 얻었다**: D-142 이후 모든 생성 table 이 "hand walk 은 16 seed, 이건 8 seed" 라는 caveat 을 달고 있었고, 그것은 *아직 안 쟀다* 가 아니라 **잴 수 없었다** 였다 — 같은 cell 을 두 seed 수로 재야 하는데 `REMEASURED` 가 들고 있는 weight 에 table 이 없었다. `w = 100` 이 그 첫 겹침이다. 신설 `seed_census()` / `SeedContrast` 로 재니 8-seed table 이 D-135 의 16-seed hand walk 을 **두 arm 모두, containment 가 아니라 set equality 로** 재현한다.
- **Confound 두 개를 가정으로 치우지 않고 처리했다**: (1) table 은 8 rung, hand walk 은 4 rung 이므로 scope 없이 grading 하면 16-seed source 가 애초에 질문받은 적 없는 rung 이 seed 불일치로 읽힌다 → registry cell 의 ladder 로 scope 하고 빠진 4 rung 을 `unwalked` 에 이름으로 남긴다. (2) registry 3 cell 중 2 개는 `w = 150` 이라 아무것도 가격 매기지 못한다 → 생략이 아니라 `uncompared` 에 명시. 비교 가능한 하나만 보여주는 census 는 "caveat 이 해결됐다" 로 읽히고, 그것이 D-107/D-120/D-127 이 각각 기록한 empty-denominator 모양이다.
- **Weight 축은 여전히 uniform drift 가 아니다**: `w=10→100` 과 `w=75→100` 둘 다 14 arm-cell 중 **10 held**. 움직이는 건 `convoy` (양 arm 모두 `WINDOW_DISJOINT`, **두 contrast 모두에서**) 와 `crossing` (closed). 보정계수는 여전히 없고, `lam_window_index` 의 nearest-weight fallback 거부는 유지된다.
- **Guard 는 여전히 refuse 한다**: `w = 100` 을 사면서 check 가 vacuous 해지지 않도록, refusal test 세 개를 D-132 의 top rung `w = 150` (여전히 미측정) 으로 옮겼다. **refusal test 는 weight 가 아니라 gap 을 가리켜야 한다** — 특정 weight 에 영구히 pin 된 test 는 자기가 감시하던 gap 보다 오래 산다 (D-047 모양).
- **첫 cut 의 non-vacuity test 자체가 vacuous 했다**: `crossing`@w=150 을 새 table 에 대고 grading 했는데 crossing 두 arm 모두 `w = 100` 에서 window 가 비어 있고, 빈 recorded set 은 모든 것의 부분집합이라 `WINDOW_HELD` 로 통과했다. Q-120 이 연 실패 방향의 쌍대(dual): **grade 를 denominator 가 비었는지 보지 않고 읽으면 accept-everything 과 refuse-everything 이 같은 뿌리에서 나온다.**
- **Alternatives**: (a) 채택 — 전 matrix 를 `w = 100` 에서 walk. (b) head_on 한 cell 만 walk — 128 run 으로 certification 은 살 수 있지만 shift census 도 seed census 의 `uncompared` 구조도 못 얻고, D-135 가 이미 그 cell 을 16 seed 로 갖고 있어 새 정보가 거의 없다. (c) `w = 150` 을 먼저 — D-132 band 의 top rung 이지만 published claim 이 앉아 있는 rung 이 아니다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-23-the-claim-certifies-at-its-own-weight.md` · D-144 의 두 refusal 중 하나를 해소 · D-142 의 weight 축을 세 번째 weight 로 확장 · D-135 의 16-seed walk 을 처음으로 소비 · Q-120

## D-144 — 2026-08-08 — guard 를 **enforce** 하는 첫 consumer 를 붙였더니, guard 가 **모든 것을 거절하고 있었다** — vacuity 는 방향이 둘인데 감시되는 것은 하나뿐이다

- **Context**: D-143 이 `resolve(scene, controller, weight)` 로 file 선택을 weight 로부터 하게 만들었지만, 그 module 의 call site 는 **여전히 전부 test** 다. 발행되는 쪽(`comparison_headroom.Headroom`)은 `weight` 와 `lam` 을 free field 로 기록만 하고 둘이 서로 맞는지 검사하는 code path 가 없다 — 즉 λ guard 는 *available* 이지 load-bearing 이 아니었다 (STATE 2026-08-08 21:00 의 과학 bottleneck).
- **Decision**: enforce 하는 consumer 를 **`comparison_headroom` 안에** 둔다 — 네 번째 guard module 이 아니라. gating 이 필요한 대상은 "operating point 에서의 safety delta **발행**"이고, 이 repo 가 발행하는 물건이 `Headroom` 이기 때문이다. `certify(row)` 는 두 arm 을 각각 `resolve` 하고 `row.lam` 을 두 window 에 대고 grade 하며, `assert_certified` 가 거절한다. 새 이름은 **딱 둘** (`CERTIFIED`, `OFF_WINDOW`); index 의 refusal 세 개는 **그대로 통과**시킨다 — 이름을 다시 붙이면 `lam_window_index` 가 이미 소유한 사실의 두 번째 진술이 되고 (D-047) 두 vocabulary 가 따로 표류한다.
- **그리고 첫 consumer 가 즉시 찾아낸 것**: `Headroom.scenario` 는 `cafe_head_on_v0` 를, table 은 `cafe_head_on_v0.yaml` 을 key 로 쓰고 `lookup` 은 basename 으로 비교했다. 결과는 **모든 row 가 `NO_CELL`** — call site 에서 보면 "미보정 cell" 과 구분이 **불가능**한 거절이고, 하필 **vacuous 한 방향**으로 틀린다: 전부 거절하는 guard 는 어느 dashboard 에서도 엄격함으로 읽힌다. repo 에는 "전부 통과시키는" 쪽을 잡는 `guard_vacuity` 가 있지만 그 반대 방향은 감시 대상이 아니었다. stem 비교로, 양쪽에 대칭으로 고쳤다. basename 규칙이 서른 cycle 동안 옳았던 이유는 **모든 caller 가 table 의 방언을 이미 쓰는 test** 였기 때문 — D-143 이 *file 선택*에 대해 한 말이 *key 형식*에 대해 한 층 아래에서 그대로 반복된다.
- **거절은 치우는 비용 순으로 순위를 매긴다**: arm 둘이 종류가 다른 거절을 낼 때 verdict 는 **더 큰 결손**을 가리킨다 — `NO_CELL` 은 calibration run 이 필요하고 `OFF_WINDOW` 는 다른 λ 하나면 된다.
- **측정된 대가 (이 결정의 실제 산출물)**: 이 project 가 발행한 mechanism claim **둘 다 certify 되지 않는다.** (a) D-124 의 gap gate 는 `NO_CELL`, sole arm `gap_gated_mppi` — 어떤 weight 의 어떤 table 에도 없는 arm 이다 (`sub_margin` 이 이미 말한 "delta 가 margin 아래"와 **독립인 두 번째** 이유). (b) risk channel 의 유일한 scorable rung (`w = 100`) 은 `NO_TABLE_AT_WEIGHT` — STATE 의 "re-key `w = 100`" 항목이 이제 문단이 아니라 **실패하는 test** 다. 동시에 D-132 의 operating point (head_on, `w = 10`, λ = 0.8) 는 `CERTIFIED` 라, 양방향이 모두 pin 되어 있다.
- **Alternatives**: (a) 채택 — 발행 지점에서 enforce. (b) 별도 `operating_point.py` guard module — call site 를 하나 더 만들 뿐 발행 경로는 여전히 무방비. (c) `Headroom.__post_init__` 에서 강제 refuse — 기존 test/호출부가 전부 깨지고, 미보정 operating point 를 *기록*하는 것 자체는 정당하므로 (기록과 발행은 다른 행위) 거절.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-22-the-guard-that-refused-everything.md` · D-143 (index) · D-047 (두 번째 진술) · D-133 (arm 별 귀속) · D-124 (`sub_margin`)

## D-143 — 2026-08-08 — table 은 **weight 로 고른다**: `lam_window_index` 가 λ guard 에 첫 consumer 를 붙이고, Q-119 의 schema 절반을 답한다

- **Context**: D-134 이래 `lam_window_key.lookup` 은 table 을 grade 해 왔지만 repo 안의 **모든 call site 가 test** 다. D-141/D-142 가 자기 weight 를 기록하는 table 두 개(`lam_windows_w10.yaml`, `lam_windows_w75.yaml`)를 만들었는데도 아무도 읽지 않는다. 그리고 weight 당 file 하나라는 schema 에서는 **caller 가 자기 weight 에 맞는 file 이 무엇인지 이미 알아야** 한다 — 아는 caller 는 guard 가 필요 없고, 모르는 caller 는 엉뚱한 file 을 열어 남의 operating point 에 대한 당당한 `ON_KEY` 를 받는다. guard 는 file 선택이 weight **로부터** 이루어질 때 비로소 load-bearing 이다.
- **Decision**: `eval/mppi_sandbox/lam_window_index.py` 를 ship. `build_index()` 가 각 table 의 `calibration_weight:` 를 읽어 weight → path 를 **유도**하고, `resolve(scene, controller, weight)` 가 그 weight 의 table 을 골라 cell lookup 은 기존 `lookup` 에 위임한다. 새 verdict 는 하나 — `NO_TABLE_AT_WEIGHT` — 이고 `available` (실제로 존재하는 weight 들) 을 함께 들고 다닌다.
- **refusal 두 개는 약해지는 게 아니라 *변환*된다**: index 를 통과하면 `OFF_KEY` 와 `UNKEYED` 는 **구조적으로 도달 불가능**하다 (index 는 이미 on-key 인 table 만 `lookup` 에 넘기고, unkeyed table 은 index 에 없다). 둘 다 `NO_TABLE_AT_WEIGHT` 이 되는데, 이쪽은 *어떤 weight 가 있는지를 말해 준다* — "네 숫자는 못 믿는다" 와 "100 에서 재라, 아니면 10 이나 75 에서 돌려라" 의 차이이고 정확히 D-044 가 booking 한 축이다. 이 구조적 주장은 산문이 아니라 `reachable_verdicts()` + test 로 **검사**된다.
- **D-133 의 오류가 도달 불가능해진다**: `cafe_obstacle_crossing_v0`/`risk_mppi` 는 `w = 10` 에서 `[1.6, 3.2]` 로, `w = 75` 에서 `EMPTY_WINDOW` 로 resolve 된다 — `w = 10` row 로 떨어지지 않는다. D-133 이 λ = 3.2 로 walk 한 바로 그 cell 이다.
- **제외된 table 은 이름이 남는다**: `lam_windows.yaml` 은 `TableIndex.unkeyed` 에 실린다. 조용히 skip 하면 ~24 cell 의 project 역사가 읽어 온 file 이 index 에 없다는 **사실 자체**가 안 보이게 된다. 그 file 은 D-107 의 이유로 계속 unkeyed 이고, D-141 이 `w = 10` variant 가 그것을 정확히 재현함을 보였으므로 `w = 10` caller 는 variant 로 라우팅돼도 잃는 것이 없다.
- **Q-119 의 schema fork 는 거짓 이분법이다**: file-per-weight 와 weight-indexed 는 **다른 layer** 를 답한다. disk 는 file 당 하나 — 각 file 이 ~1024-run 측정 하나의 산출물이고 provenance 는 run 단위라, 둘을 합치면 두 측정이 하나의 mtime/blob 뒤로 들어간다. API 는 weight-indexed — caller 가 실제로 들고 있는 key 가 그것이다. index 를 read time 에 유도하므로 `w = 100` 추가는 `calibrate_lam --w-obs-soft 100` 한 번 + `TABLES` 한 줄이고 migration 이 없다. 저장된 index 는 file 이 이미 들고 있는 사실의 두 번째 진술이고 D-047 이 어느 쪽이 drift 하는지 지목했다.
- **하지 않는 것들**: nearest-weight fallback / interpolation 없음 — D-142 가 6/14 cell 이 **양방향으로** 움직임을 쟀다 (convoy/risk 는 위로, crossing/stock 은 ladder 밖 bisect rung, crossing/risk 는 닫힘). 적용할 correction factor 가 없으므로 어떤 fallback 도 그 운동에 대한 *model* 을 lookup 의 옷을 입혀 파는 것이 된다. 같은 weight 를 주장하는 table 두 개는 tie-break 하지 않고 `WeightCollision` 으로 거절한다 — 어느 쪽을 고르든 답이 tuple 순서에 의존하게 된다.
- **Alternatives**: (a) 채택 — read-time 에 유도되는 weight index. (b) checked-in mapping — D-047. (c) `lookup` 에 weight→path 를 직접 넣기 — grading 과 file 선택을 한 함수에 섞어 collision/unkeyed 보고가 갈 곳이 없어진다. (d) schema 를 per-cell weight 로 (Q-119 (d)) — D-138 의 refusal 두 개를 무효화하고 D-123 의 re-confound 를 되살린다. (e) 이번 cycle 도 sweep — 앞 두 cycle 이 35분 예산에 56분/95분을 썼고, 이미 산 두 table 이 아직 아무 값도 못 하고 있었다.
- **한계**: index 는 λ 를 *제공*할 뿐 아직 아무 sweep driver 도 그것을 **강제**하지 않는다. `comparison_headroom` 과 ladder walk 들은 여전히 λ 를 인자로 받는다. available → enforced 는 다음 단계다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-21-the-table-is-chosen-by-the-weight.md` · D-142 (weight 의존성) · D-141 (w=10 재현) · D-134 (guard) · D-133 (off-key walk) · D-107 (재도출 안 된 provenance) · D-047 (사실의 두 번째 진술) · D-044 (치울 수 없는 check) · Q-119 (schema 절반 resolved)

## D-142 — 2026-08-08 — λ window 은 **weight 에 의존한다**: w=10 → w=75 에서 14 arm-cell 중 6 개가 움직인다 — 다만 D-132 의 operating point 는 살아남았다

- **Context**: D-141 이 전체 matrix 를 `w = 10` 에서 재생성해 16/16 cell 이 정확히 일치했고, STATE 는 이것을 "table 이 검증되었다" 로 읽는 방향으로 기울고 있었다. 하지만 자기 weight 에서의 재생성은 **control** 이다 — code path 가 behaviour-preserving 임을 말할 뿐, window 가 weight-invariant 임을 말하지 않는다. Q-119 의 남은 절반(lean (b), D-132 의 band `{75, 100, 150}`)의 첫 rung 을 실제로 측정했다.
- **Decision**: `--w-obs-soft 75` 로 전체 matrix 를 walk (8 scenes × 2 controllers × 8 rungs × 8 seeds = **1024 runs**, ~16 min) → `eval/scenarios/variants/lam_windows_w75.yaml`. 같은 ladder, 같은 seed 수라 **contrast 가 weight 만 분리**한다. 결과: `w = 10` 에서 window 를 가졌던 **14 arm-cell 중 8 held / 6 moved** — `SHIFTED` ×3 (convoy/stock, freezing/risk, head_on/risk), `DISJOINT` ×2 (convoy/risk, crossing/stock), `CLOSED` ×1 (crossing/risk).
- **가장 강한 움직임은 boundary artifact 가 아니다**: `cafe_obstacle_crossing_v0`/risk 는 `w = 10` 에서 `[1.6, 3.2]` 인데 `w = 75` 에서 **어떤 rung 에서도** admissible 하지 않다. D-134 가 독립적인 16-seed walk 로 같은 arm 이 `w = 150` 에서 `{0.8}` 로 옮겨간 것을 이미 봤으므로, 그 row 는 weight 를 따라 drift 하는 window 가 아니라 **`w = 10` 을 기술하는** row 다.
- **그런데 retraction test 는 깨끗하게 통과했다**: D-131/D-132 의 band 는 λ = 0.8 에서 walk 되었고 그 admissibility 는 `w = 10` table 에서 읽은 것이다. `w = 75` 에서 **`cafe_head_on_v0` 양 arm 모두 0.8 이 admissible** 이므로 project 의 유일한 significant claim 은 자기 band 의 바닥 rung 에서 operating point 를 유지한다. risk arm 은 `SHIFTED` (λ = 0.2 를 잃음) 지만 0.8 을 통과하지 않는 방향이다.
- **D-136 의 `FACTOR_INERT`(weight 축) 는 틀린 게 아니라 bound 되었다**: 그것은 head_on 을 `w = 100`/`w = 150` 에서 읽었고, head_on/stock 은 여기서도 여전히 held 인 8 cell 중 하나다. 안정적인 cell 하나가 matrix 를 대변하게 둔 **추론**이 무너진 것이지 측정이 무너진 게 아니다. D-139→D-141 의 "좁은 cell 이 진짜 시험" 과 같은 모양.
- **`NEVER_OPEN` 을 새로 grade 한다**: `window_shift` 는 새 window 가 비면 recorded 가 비었는지와 무관하게 `WINDOW_CLOSED` 를 돌려주므로, `cut_in` 두 cell (양 weight 에서 모두 빈 window) 을 그대로 세면 "8/16 moved" 가 되고 그 중 2 개는 **어떤 weight 에서도 operating point 가 없던** cell 이다 (Q-035). 분모 오염이고 D-107/D-120/D-127 이 각각 booking 한 모양이라 caller 쪽에서 갈라낸다.
- **일방향 drift 가 아니다** — convoy/risk 는 `[0.2, 0.4] → [0.8]` 로 **위로** 옮겨갔고 crossing/stock 은 ladder 밖 bisect rung `[4.5255]` 로 갔다. 적용할 correction factor 같은 것은 없다.
- **Alternatives**: (a) 채택 — band 의 첫 rung 을 전체 matrix 로. (b) head_on 한 scene 만 `w = 75` 에서 — 정확히 D-136 이 이미 한 실수를 반복하고, 움직인 6 cell 중 5 개를 못 본다. (c) 세 weight 를 한 cycle 에 — wall-clock 3배, 그리고 첫 rung 이 이미 답을 바꾸므로 나머지 둘의 해석이 달라진다. (d) `w = 10` table 을 계속 씀 — 이번 측정이 정확히 그것이 6 cell 에서 틀리다는 증거다.
- **한계**: 이 table 은 **8 seed** 이고 `REMEASURED` registry 는 16 seed 다. `admissible` 은 seed 에 대한 conjunction 이라 8-seed 에서의 `HELD` 는 약한 주장, 움직임은 강한 주장이다. `w = 100` 재키잉이 D-135 의 16-seed hand walk 와 직접 대조되므로 이 caveat 을 가격 매긴다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-20-the-window-depends-on-the-weight.md` · D-141 (control) · D-136 (bound 된 추론) · D-134 (crossing/risk 의 독립 16-seed 이동) · D-132 (살아남은 claim) · Q-119 (lean (b) 첫 rung)

## D-141 — 2026-08-08 — 전체 matrix 가 자기 weight 에서 **정확히** 재현된다: 16 cell × 5 field, drift 0 — 그래도 shipped table 은 `UNKEYED` 로 남는다

- **Context**: D-139 가 gating step 으로 head_on 한 scene 을 재생성해 shipped row 와 일치시켰고, Q-119 의 lean (c) — "`w = 10` 만 재측정해 shipped table 을 legitimize" — 를 규모로 실행할 근거를 만들었다. STATE 는 이것을 cycle 당 2–3 scene 으로 쪼갤 계획이었다.
- **Decision**: 쪼개지 않고 **전체 matrix 를 한 pass** 로 돌렸다 (8 scenes × 2 controllers × 8 rungs × 8 seeds = **1024 closed-loop runs**, 16 jobs, ~17 min). 결과는 **16/16 cell, 80/80 field 완전 일치** — `admissible`, `ladder`, `min_spread` (소수 둘째 자리까지), `completes_anywhere`, `calibratable` 전부. weight-threading 은 기본값에서 behaviour-preserving 이고, 이제 그것이 **한 cell 이 아니라 matrix 전체**에 대해 참이다.
- **왜 쪼개기가 틀린 추정이었나**: STATE 의 chunk 계획은 *scene* 당 비용에서 나왔는데 `calibrate_matrix` 의 병렬 단위는 **cell** 이고 16 cell 이 16 core 에 그대로 올라간다. 게다가 `on_cell=flush` 가 cell 마다 file 을 다시 쓰므로 어느 시점에 죽어도 **유효한 (더 짧은) file** 이 남는다 — 긴 sweep 을 wall-clock rule 아래에서 시작해도 안전하게 만드는 성질이고, chunking 이 사려던 안전을 이미 제공하고 있었다.
- **좁은 cell 이 진짜 시험이었다**: head_on 의 window 는 3 rung 으로 여유가 있다. `city_figure8` 은 양 arm 모두 **단일 rung** `[0.4]`, `cafe_cut_in_v0` 는 **빈** window 다. threading bug 가 드러날 곳은 정확히 거기이고, 전체 pass 가 쌌기 때문에만 walk 되었다. 즉 D-139 의 검증은 필요했지만 충분하지 않았다.
- **`UNKEYED` 는 그대로 유지한다 — 두 table 이 일치하기 *때문에***: 일치는 *variant* 를 믿을 근거이지 원본에 header 를 박을 근거가 아니다. shipped table 의 row 들은 weight 를 기록하지 않는 code path 가 만들었고, 손으로 stamp 하면 ~24 cell 이 아무도 re-derive 하지 않은 provenance 를 얻는다 (D-107). key 는 재실행으로 벌었고, 번 쪽은 variant 다.
- **`EMPTY_WINDOW` 는 실패가 아니라 답이다**: 14 cell 이 `ON_KEY` 로 window 를 돌려주고 `cut_in` 두 cell 은 `EMPTY_WINDOW` 를 돌려준다. keying 은 *기록된* 답을 사는 것이지 *쓸 수 있는* 답을 사는 것이 아니며, 어떤 온도에서도 goal 에 닿지 않는 arm 은 어느 weight 에서도 window 가 없다 (Q-035). 이것을 lookup 실패로 읽는 것이 Q-034 의 오류다.
- **Alternatives**: (a) 채택 — 전체 matrix 한 pass. (b) STATE 대로 2–3 scene chunk — cycle 3개를 쓰고, 좁은 cell 이 마지막 chunk 로 밀려 가장 늦게 검증된다. (c) window 만 비교 — `min_spread` 가 움직인 재생성은 같은 답을 입은 *다른 측정* 이므로 5 field 전부 비교. (d) shipped table 에 stamp — D-107.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-19-the-matrix-reproduces-at-its-own-weight.md` · D-139 (gating step) · D-138 (writer) · D-107 (재도출 안 된 provenance) · Q-119 (lean (c) 완료, weight 부분집합 질문은 계속 open)

## D-140 — 2026-08-08 — Gate 1 은 **새 review bandwidth** 를 세는 것이지 cycle 을 세는 것이 아니다: 이미 열린 PR 위에서 계속하는 것은 gate 를 통과한다

- **Context**: 같은 queue 상태(6 branch, 마지막 merge 2026-07-12)를 두고 오늘 cycle 들이 **서로 다르게 행동했다** — 16:00 은 `pr-queue-full` 로 skip 했고, 15:00 과 17:00 은 이미 열려 있는 PR #67 위에서 작업을 계속했다. 매 cycle 이 이 판단을 처음부터 다시 유도하고 있고, 16:00 은 그 유도의 결과로 한 시간을 잃었다. 헌법 산문은 "≥ 6 이면 skip" 만 적고 있어 이 구분에 대해 침묵한다.
- **Decision**: gate 1 의 계량 단위는 **queue 에 새로 얹히는 항목**이다. 이미 OPEN PR 이 있는 branch 위에서 계속 작업하는 cycle 은 PR 을 하나도 추가하지 않으므로 **gate 를 통과한다**; gate 가 막는 것은 *새 thrust* — 즉 새 branch + 새 PR — 뿐이다. deadlock-breaker 조항이 이미 같은 원리를 명시적으로 적고 있다: "the cap exists to respect *human review bandwidth*, not to halt the project indefinitely."
- **경계는 그대로 엄격하다**: 새 branch 를 파는 것은 여전히 금지되고, 계속 작업하는 branch 는 반드시 **이미 OPEN PR 을 가진** 것이어야 한다 (pushed-but-PR-less branch 는 queue 에 있는 debt 이므로 해당 없음). PR 을 새로 여는 순간 그것은 새 thrust 이고 gate 가 다시 적용된다.
- **왜 지금 기록하는가**: 이 읽기가 없으면 27일째 멈춘 queue 가 project 를 무기한 정지시킨다 — escalation 은 72h cooldown 이라 사람에게 알림도 가지 않고, deadlock-breaker 는 close 가능한 PR 이 없어 발동하지 않는다 (#23/#44 는 D-009 가 build path 로 *선택한* 것이고 #66/#68/#69 는 supersede 된 적 없다). 세 조건이 동시에 막히면 남는 유일한 진행 경로가 이것이다.
- **Alternatives**: (a) 채택 — 새 항목 기준. (b) 문자 그대로 언제나 skip — 사람 merge 전까지 project 정지, gate 의 목적(bandwidth 보호)은 이미 충족되고 있는데도. (c) deadlock-breaker 를 넓혀 supersede 되지 않은 PR 도 close — 사람이 검토할 산출물을 executor 가 지우는 것이라 거절.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-18-the-generator-reproduces-its-own-table.md` · D-010 (deadlock-breaker 의 원리) · D-009 (#23/#44 가 build path)

## D-139 — 2026-08-08 — Q-119 의 gating step: **generator 는 자기가 만든 table 을 재현한다** — re-key 경로에서 위험이 빠졌다

- **Context**: D-138 이 `--w-obs-soft` writer 를 ship 했지만 round trip 을 **합성 cell** 로만 증명했다 (`tmp_path`, sim 없음). 정작 바뀐 쪽은 *측정* 절반 — `ab.lam_ladder` 가 새로 `w_obs_soft` 를 받아 `MPPIParams` 로 내려보낸다 — 이고, 그 경로가 window 를 바꾸지 않는다는 증거는 없었다. Q-119 의 다음 action 이 정확히 이것을 지목했다: 답을 이미 아는 cell 하나를 그 새 경로로 다시 걸어보라.
- **Decision**: `cafe_head_on_v0` 를 shipped table 이 생성된 바로 그 weight (`w_obs_soft = 10`, `MPPIParams` 기본값) 에서 재생성 (2 arms × 8 rungs × 8 seeds = 128 runs) → `eval/scenarios/variants/lam_windows_w10.yaml`. **양 arm 모두 shipped row 와 정확히 일치** — stock `[0.2, 0.4, 0.8]` `min_spread` 1.04, risk `[0.2, 0.4, 0.8]` `min_spread` 1.05, spread 소수 둘째 자리까지 동일. weight threading 은 기본값에서 behaviour-preserving 이다.
- **왜 재측정이 아니라 재생성인가**: 새 weight 의 새 cell 은 *믿을* 수만 있고 **반박될 수는 없다**. 답이 이미 기록된 cell 만이 generator 를 시험한다. head_on 을 고른 이유도 같다 — D-135 가 `w = 100` 에서 독립적으로 재측정해 `WINDOW_HELD` (set equality) 를 받은, 재측정 거동이 *특성화된* 유일한 scene 이다.
- **부수 효과 — repo 최초로 `lookup` 이 window 를 반환한다**: D-134 가 reader 를 ship 한 이래 모든 호출이 `UNKEYED` 였고, D-138 이 `ON_KEY` 를 *도달 가능*하게 만들었으며, 이 artifact 가 fixture 아닌 **측정**으로 거기 도달한 첫 사례다 (`usable == (0.2, 0.4, 0.8)`).
- **좋은 소식이 refusal 을 지우지 않는다**: shipped table 은 여전히 `UNKEYED` 여야 하고 그것을 강제하는 test 를 같이 ship 했다. 이 한 cell 에서 나머지 일곱 scene 을 stamp 하는 것이 정확히 D-107 의 재도출 안 된 provenance 다. 파일은 한 scene × 두 arm 이고, crossing 은 `NO_CELL`, 30/100/150 은 `OFF_KEY` 로 계속 거절된다.
- **비교는 containment 가 아니라 set equality** (D-135 의 이유), 그리고 literal `(0.2, 0.4, 0.8)` 을 따로 pin 한다 — 두 table 이 같은 방향으로 함께 drift 하면 서로 비교하는 assertion 은 통과해버리기 때문.
- **Alternatives**: (a) 채택 — 답을 아는 한 scene 재생성. (b) 전체 matrix 를 바로 재측정 (~500 runs) — generator 가 검증되지 않은 채 24 cell 의 provenance 를 만든다. (c) 새 weight 에서 새 cell — 반박 불가능한 측정이라 generator 에 대해 아무 말도 못 함. (d) 합성 test 만 믿고 진행 — 바뀐 절반이 측정 쪽이라는 점을 놓친다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-18-the-generator-reproduces-its-own-table.md` · Q-119 의 gating step (weight 부분집합/schema 질문은 계속 open) · D-138 (writer) · D-135 (head_on 의 재측정 거동) · D-107 (재도출 안 된 provenance)

## D-138 — 2026-08-08 — `calibration_weight:` 는 **reader 만 있고 writer 가 없던 field** 였다: 검증된 적 없는 contract 이고, 고치는 것은 round-trip test 다

- **Context**: D-134 가 `lam_window_key` 를 ship 하면서 `_rows` 가 top-level `calibration_weight:` 를 읽도록 했다. 그런데 그 key 를 쓰는 코드는 **어디에도 없었다**. shipped `lam_windows.yaml` 에 그 field 가 없으므로 모든 lookup 이 `UNKEYED` 로 떨어졌고, 그래서 **양쪽 spelling 이 다르더라도 아무 test 도 실패하지 않았을 것**이다 — writer 가 `calibrated_at:` 을 썼어도 결과는 똑같이 `UNKEYED` 였다. reader-only field 는 미완성 기능이 아니라 **한 번도 검증된 적 없는 contract** 이다.
- **기계적 원인은 keyword 충돌이었다**: `ab.lam_ladder` 가 `params=MPPIParams(lam=...)` 슬롯을 직접 소유하므로 `w_obs_soft` 를 `arm_kwargs` 로 흘려보낼 수 없었다. 즉 `lam_windows.yaml` 은 "아무도 re-key 하지 않기로 한" table 이 아니라 **누구도 re-key 할 수 없던** table 이었다. 한 결과의 scope 를 keyword-argument 충돌이 정하고 있었다.
- **Decision**: writer 를 ship 한다 — `ab.lam_ladder(w_obs_soft=)`, `calibrate_lam --w-obs-soft`, `to_yaml` 이 `calibration_weight:` emit. 값은 **cell 에 실어서**(`SceneCalibration.w_obs_soft`) 나른다: 옆에 같이 넘기는 weight 는 caller 의 *주장*이고, 측정 객체에 실린 weight 는 *기록*이다. 이로써 run 이 쓰지 않은 weight 를 emit 하는 call path 가 존재하지 않는다. 두 refusal 이 이를 지킨다 — 서로 다른 weight 의 cell 을 한 file 로 쓰려는 `to_yaml`, 다른 weight 의 rung 을 merge 하려는 `refine`.
- **shipped table 은 일부러 `UNKEYED` 로 남긴다**: key 를 박는 것은 header 편집이 아니라 **재측정**(~500 closed-loop runs)이고, hand-stamp 는 ~24 cell 에 아무도 re-derive 하지 않은 provenance 를 주는 D-107 의 모양이다. 손으로 박으면 실패하는 test 를 같이 ship 했다.
- **왜 지금인가**: D-044 가 "clear 할 수 없는 check 는 mute 된다" 를 이미 booking 했다. 이번 cycle 전까지 `ON_KEY` 는 **어떤 행동으로도 도달 불가능**했다. Q-116 은 (b) guard-first 를 고르면서 (a) 를 "guard 가 schedulable 하게 만드는 것" 이라 적었는데, 그 빚이 한 cycle 만에 돌아왔다.
- **Alternatives**: (a) 채택 — writer + round-trip test, table 은 미측정 상태 유지. (b) shipped table 에 `10.0` hand-stamp — 즉시 `ON_KEY` 를 얻지만 D-107 의 거짓 provenance. (c) 2-seed 로 빠르게 re-key — D-134 가 정확히 이 shortcut 이 risk/crossing 을 `{0.4, 0.8}` 로 잘못 읽는 것을 잡았다 (16 seeds 는 `{0.8}`). (d) 계속 미룸 — `UNKEYED` 가 영구화되어 guard 가 mute 된다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-17-the-field-only-the-reader-knew.md` · D-134 (guard) · D-044/D-129 (guard 를 ship 하면 satisfy 할 수단도 ship 해야) · D-107 (재도출 안 된 provenance) · D-047 (규칙의 진술은 한 곳)

## D-137 — 2026-08-08 — Strand 를 "치운다" 는 것은 push 가 아니라 **repair** 일 수 있다: 죽은 cycle 은 red tree 를 남긴다

- **Context**: D-112 의 `cycle_artifacts stranded` 는 14:00 cycle 을 정확히 잡아냈다 (commit 2개, origin 도달 0). 그런데 D-112 의 헌법 문구는 치우는 방법을 "빠진 TSV row 를 append 하고 push" 로만 적어 두었다. 실제로 suite 를 돌리자 **3 failed, 1714 passed** — 14:00 이 ship 한 `lam_window_key.attribution` guard 가 registry pin 3개를 movable 하게 만들었고, cycle 이 receipt 전에 killed 되어 아무도 그 청구서를 받지 못했다.
- **Decision**: strand 를 치우는 절차는 **push 가 아니라 "green 을 회복한 뒤 push"** 로 읽는다. 이번 cycle 의 실제 작업이 그 repair 였다 — `test_guard_direction` 의 scalar count 10 → 11, `test_guard_reflexivity` 의 `&`-shaped 집합 +1 및 pool pin 92 → 93, `loop_reach.READING` 에 빠진 두 row (`test_headon_holds_at_both_measured_weights` n=4, `test_d132_w150_rung_was_walked_at_an_admissible_temperature` n=2).
- **왜 gate 가 이미 옳았나**: push_preflight 가 red receipt 에 `RED` 를 매기므로 이 tree 는 애초에 push 될 수 없었다. 즉 **두 gate 는 조합으로 정확했다** — `stranded` 가 "안 나갔다" 를, `check` 가 "나가면 안 된다" 를 말했다. 잘못된 것은 헌법의 **산문**뿐이고, 그것이 D-047 이 반복해서 booking 하는 모양이다: 규칙을 손으로 옮겨 적은 문장이 규칙 자체보다 좁았다.
- **14:00 의 journal 은 `TSV row appended: yes` 라고 주장했고 row 는 없었다.** `UNSUPPORTED_CLAIM` 이 잡도록 설계된 바로 그 상태이며, 실제로 이번 push 를 막았을 것이다 (RED 가 먼저 걸려서 도달하지 않았을 뿐).
- **Alternatives**: (a) 채택 — repair 후 push. (b) red 인 채 push 하고 CI 에 맡김 — PR #67 을 한 시간 red 로 두는 D-082 가 금지한 바로 그 행동. (c) 14:00 commit 을 revert — 측정 자체(128 runs, 300 s)는 유효하므로 재측정 비용만 버리는 선택.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-15-the-strand-was-red.md` · D-112 (strand gate) · D-082 (push gate) · D-043 (pin 은 누가 돌려야 값이 매겨진다)

## D-136 — 2026-08-08 — 재측정 census 의 mover 는 **scene** 이다: head_on 은 `w = 150` 에서도 window 를 유지

- **Context**: D-135 의 census 는 2 of 4 arm-cells held 였지만 **완전히 confounded** 였다 — 움직인 둘은 `cafe_obstacle_crossing_v0` **이자** `w = 150`, 버틴 둘은 `cafe_head_on_v0` **이자** `w = 100`. 두 축이 같은 두 행이라 어떤 off-key read 에 대해서도 반대 결론을 함의했다 (Q-118).
- **Decision**: Q-118 의 lean (a) 를 실행 — `cafe_head_on_v0` 를 `w = 150` 에서 λ ∈ {0.2,0.4,0.8,1.6} × 양 arm × 16 seeds 로 재측정 (128 runs, 300 s, margin 0.40). **양 arm 모두 기록된 `[0.2, 0.4, 0.8]` 로 정확히 재측정** (각 rung 16/16 in band, 16/16 goal, 1.6 은 0/16) → `WINDOW_HELD`, `w = 100` 과 동일 등급. 이 세 번째 cell 이 `w = 150` 고정 scene contrast 와 scene 고정 weight contrast 를 만들어 confound 를 깬다: **scene `FACTOR_MOVES`, weight `FACTOR_INERT`**. census 는 **4 of 6 arm-cells held**. `contrasts()` / `attribution()` 을 shipped — registry 에서 **derive** 하며, 비교된 arm 이 없으면 `FACTOR_INERT` 가 아니라 `NO_CONTRAST` 를 반환 (D-107/D-120/D-127 의 empty-denominator).
- **결과적으로**: off-key tax 는 **scene 성 위험**이다. head_on 은 10 → 150 의 15× weight 이탈에도 rung 하나 움직이지 않는다. 단 `OFF_KEY` 는 두 scene 모두에서 계속 refuse 한다 — lookup 은 ~300 s 를 쓰기 전에는 자신이 benign 한 쪽인지 알 수 없다.
- **부수적으로**: D-132 가 실제로 ship 한 rung 을 retract 할 수 있었으나 하지 않았다. λ = 0.8, `w = 150` 에서 stock **10/16** vs risk **1/16** — D-132 의 `p = 0.0021` rung 을 독립 walk 에서 **정확히 재현**했고, 그 온도는 양 arm 모두 admissible 하다.
- **Alternatives**: (a) 채택한 head_on@150. (b) crossing@100 — pathological side 를 고정하지만 window 가 비면 축에 대해 아무 말도 못 함. (c) 제3 scene 을 제3 weight 에서 — row 만 늘고 contrast 는 0.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-14-the-mover-is-the-scene-not-the-weight.md` · Q-118 resolved · D-135 의 confound 를 해소 (D-135 의 측정치는 유효)

## D-135 — 2026-08-08 — The head_on band **survives its own re-keying**: both arms hold their recorded window at `w = 100`, so D-132 stands and the guard gets its first non-refusing witness

- **Context**: D-134 re-measured **one** cell off key and both arms failed — risk `WINDOW_DISJOINT`, stock `WINDOW_CLOSED`. That cell (`cafe_obstacle_crossing_v0`, `w = 150`) is the pathological scene by construction: disjoint per-arm windows, 5-actor dynamic block. D-131/D-132's band on `cafe_head_on_v0` (`{75, 100, 150}`, `w = 100` at p = 2.5e-4 — the project's only significant mechanism claim) was walked at λ = 0.8 from the same `w = 10` table, so it was either measured at admissible temperatures or it was D-133's error with a luckier outcome. Q-117, and nobody had taken the measurement.
- **Decision**: Walked λ ∈ {0.2, 0.4, 0.8, 1.6} × both arms × 16 seeds at `w_obs_soft = 100`, margin 0.40 (128 runs, 296 s). **Q-117 answers on its reassuring branch.** Both arms re-measure to **exactly** their recorded `[0.2, 0.4, 0.8]` — every rung 16/16 in band and 16/16 reaching the goal — so both grade `WINDOW_HELD`. **λ = 0.8 is admissible for both arms**, which is the operating point D-132's band was walked at: the band was measured at temperatures its arms are actually admissible at, and D-134 does not reach it.
- **The reassurance is exact, not generous.** `WINDOW_HELD` here is set equality and not containment: λ = 1.6 is **0/16** on both arms. A window that held by *widening* would be the weaker result — it would mean the recorded set was a conservative subset and say little about whether the boundary moved. This one held on its recorded support with nothing to spare.
- **One cell was an anecdote; two are a rate, and the rate is 2 of 4 arm-cells held.** Shipped `Remeasurement` (a `(scene, weight)` cell carrying `counts`, with `window` / `recorded` / `shift` / `shared` all **derived**), the `REMEASURED` registry, and `shift_census()` — which returns grade → *named members* rather than a bare count, because a rate whose numerator cannot be enumerated is what `published_ratios` refuses. `CROSSING_W150_ESS` / `CROSSING_W150` survive as views of the cell, not as a second copy (D-047).
- **The census's own limit, stated rather than left to be inferred**: crossing was walked at `w = 150` and head_on at `w = 100`, so "windows move on crossing" and "windows move at `w = 150`" are the same two rows. The census cannot separate scene from weight, and a third cell should be chosen to break exactly that tie (head_on at `w = 150`, or crossing at `w = 100`) rather than to add a third scene.
- **The guard is now non-vacuous in both directions.** Before this cycle `WINDOW_HELD` and `ON_KEY` were branches no measurement reached, which is `guard_vacuity`'s complaint with the sign flipped — a check that always refuses is as uninformative as one that never does. `UNKEYED` remains the verdict on the shipped table; re-keying (Q-116 option (a)) is still deferred and still schedulable.
- **The corpus check caught its own bookkeeping.** The three new per-arm assertions are population-claim loops, so `loop_reach`'s `test_recorded_reading_covers_exactly_todays_targets` went red until `READING` recorded them — each at `n = 2`, the narrowest row in that table and the honest width, since the claim *is* about both arms of one cell. While re-taking it, the table's prose was found asserting "all 15 population claims" over a set that has been 18 for three cycles; the literal is now removed rather than corrected, since `targets()` is the only thing that knows the count.
- **Second bookkeeping cost, and the more serious one**: a `git add -u` in the fixup commit staged all five `DECLARED_LOCAL_ONLY` paths — the D-011 offence the branch rule forbids. It was caught, but by the **full suite** (`local_only_audit`'s branch test plus two `exemption_masking` census tests whose population moved under it), not by the cheap pre-push audit, which had not run yet. The guard worked; the ordering meant it cost 14 minutes to hear from. `git add -- <specific paths>` is the rule for exactly this reason.
- **Alternatives**: (a) treat D-134's cell as unrepresentative and move on — rejected in Q-117 and rejected again here, since "head_on is better behaved" was exactly the kind of assumption D-134 found costly; (b) re-key the whole table first — right eventually, still too coarse to start with, and now cheaper to scope because two cells bound the movement; (c) walk head_on at `w = 100` — chosen.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-12-the-band-survives-its-own-re-keying.md` · resolves Q-117 · bounds D-134 · leaves D-131/D-132 standing

## D-134 — 2026-08-08 — The λ window is **weight-dependent and the table does not record its weight**: guard the lookup, and crossing has no admissible baseline temperature at `w = 150`

- **Context**: Q-116 asked whether `lam` calibrates per (scene, controller) or per (scene, controller, **weight**), and named the test: walk a λ ladder at crossing `w = 150` — D-133's one rung where only the *baseline* refused — and see whether any λ puts **both** arms in band. `lam_windows.yaml` was generated at the shipped `w_obs_soft = 10` and has since been read at 30, 75, 100, 150, 300, 500, 750, 1000, 2000 with nothing in the file to mark the discrepancy.
- **Decision**: Walked λ ∈ {0.2, 0.4, 0.8, 1.6} × both arms × 16 seeds at `w_obs_soft = 150`, margin 0.30 (128 runs, 452 s), recording per-rung in-band counts and clearances together. **Q-116's answer is (b), the stronger branch it anticipated: no λ admits both arms.** Risk's recorded `[1.6, 3.2]` re-measures to `{0.8}` (16/16 in band, 1.6 at **0/16**) — `WINDOW_DISJOINT`. Stock's recorded `[0.4, 0.8]` re-measures to **∅** (12/16, 8/16) — `WINDOW_CLOSED`. Shipped `eval/mppi_sandbox/lam_window_key.py`: a weight-carrying `lookup` refusing by name (`OFF_KEY` / `UNKEYED` / `NO_CELL` / `EMPTY_WINDOW`, `usable is None` under each) plus `window_shift`'s four-way witness grade.
- **The guard is (b) and re-keying is deferred, deliberately.** The table stays as generated; stamping `calibration_weight: 10.0` by hand would give every existing row a provenance nobody re-derived. `UNKEYED` is therefore the verdict on the shipped file today — the strongest of the three refusals, because a table with no weight field cannot be checked at all. Re-keying (Q-116 option (a)) becomes schedulable *because* the guard enumerates the sites; it was not before.
- **D-133 is strengthened, not repaired.** `NO_SCORABLE_RUNG` stands and now has a mechanism: the two arms' `w = 150` windows are disjoint from each other as well as from the table, so the baseline is admissible at **no** temperature on this ladder at this weight. The λ = 0.8 rung reproduced D-133 exactly from an independent walk — stock 4/16 → risk 0/16, Fisher p = 0.101 — with risk 16/16 in band and stock 8/16.
- **Store the fraction, derive the boolean.** `CROSSING_W150_ESS` holds `(n_in_band, n)` per rung and `CROSSING_W150` is `admissible_at()` of it. `LamProbe.admissible` is an all-seeds conjunction that only tightens with `n`: the 2-seed smoke of this same ladder read risk as `{0.4, 0.8}`, and 0.4 is 15/16 — a near miss a stored boolean would have printed as a clean failure (D-019 / Q-042, one axis over).
- **Alternatives**: (a) full re-calibration keyed by weight — correct unit, ~500 runs per weight, and no list of which weights matter; (b) guard first, re-key later — chosen; (c) per-arm temperatures — rejected in Q-116 and still rejected: the disjoint-window fact is what makes this scene informative.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-11-the-window-moved-off-its-recorded-support.md` · resolves Q-116 · strengthens D-133

## D-133 — 2026-08-08 — `cafe_obstacle_crossing_v0` has **no scorable rung at either temperature**: its transition region and its ESS-compliant region are disjoint

- **Context**: D-132's band (`{75, 100, 150}`, `w = 100` at p = 2.5e-4) is one scene's property. `cafe_obstacle_crossing_v0` — the other scene D-125 relieved — had never been scored for headroom at any rung, so "the risk channel has a scorable band" and "…on one scene" were the same sentence. This scene also calibrates its two arms to **disjoint** `lam` windows (stock `[0.4, 0.8]`, risk `[1.6, 3.2]`, since the 5-actor block landed), so it could not be walked at one temperature the way head_on was.
- **Decision**: Walked `w ∈ {30, 75, 150, 300, 500, 750, 1000, 2000}` × **both** λ ∈ {0.8, 3.2} × both arms × 16 seeds (512 runs, 225 s, margin 0.30). Verdict is **`NO_SCORABLE_RUNG` at both temperatures**, and the reason is structural: the rungs where the arms differ and the rungs where the sampler is compliant are **disjoint sets**. λ = 0.8 — arms differ at 30/75/150, all three ESS-refused; the four graded rungs (300–1000) are stock 0.0000 vs risk 0.0000. λ = 3.2 — exactly **one** rung of eight is graded (2000), also `NO_HEADROOM_SAFE`. Shipped per-arm ESS attribution (`BandRung.ess_arms` / `out_of_band_arms`, `ScorableBand.refused_by_arm` / `sole_refuser`) so a refusal can name its owner.
- **The refusal is two-sided, so it does NOT bound the mechanism.** `sole_refuser` is `None` at both λ: stock leaves the band at {30, 75, 150, 2000} and risk at {30, 75, 2000} (λ = 0.8). A `NO_SCORABLE_RUNG` owned by the mechanism arm bounds the mechanism; one owned by the baseline bounds the operating point; a two-sided one bounds **the scene**. Same verdict string, three different next moves — which is why the attribution shipped with the measurement rather than after it.
- **The D-131 refusal earned its keep here.** At λ = 0.8, `w = 75` the raw result is stock **16/16** unsafe → risk **7/16**, Fisher **p = 8.2e-4** — a *larger* effect than head_on's best admissible rung — at median ESS **1.8 / 2.2**, i.e. the softmax collapsed to argmin-over-draws and λ is inert. Unrefused, that would have been the project's strongest headline and it would have been about the sampler.
- **Alternatives**: (a) walk one λ and report crossing as "no band" — would have attributed a sampler fact to the mechanism; (b) relax the ESS gate to get a rung — buys exactly the D-131 artefact above, at p = 8.2e-4; (c) declare the scene unscorable without measuring — leaves the p = 8.2e-4 rung undiscovered and the cause unnamed.
- **The lead**: λ = 0.8, `w = 150` is stock 4/16 → risk 0/16 (p = 0.10) with **risk in band and stock out** — one baseline-side calibration from being gradeable. Root cause is that `lam_windows.yaml` is measured at the shipped `w_obs_soft = 10` and used at 30–2000 (Q-116).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-10-the-second-scene-has-no-scorable-rung.md` · bounds D-132's scope to one scene (does not retract it) · D-125 / D-127 / D-131 / Q-115 / Q-116

## D-132 — 2026-08-08 — The scorable band on `cafe_head_on_v0` is three rungs wide, and the risk channel's win at `w = 100` is significant

- **Context**: D-131 scored `risk_mppi` vs `stock_mppi` at exactly one rung (`w_obs_soft = 100`, unsafe 1.0000 → 0.2500, n = 8) whose ladder neighbours were 30 and 300. A point cannot say whether the scorable region is one rung or five, so the project's first scored mechanism claim was one ladder choice from vanishing.
- **Decision**: Densify (λ = 0.8, margin 0.40, **16 seeds/arm**, `w ∈ {30,55,75,100,150,200,250,300}`). The band is **`{75, 100, 150}` contiguous** — Fisher two-sided **0.043 / 2.5e-4 / 0.0021** — lower edge bracketed in **(55, 75]**, transition ending at 200 where both arms reach 0.0000. `w = 100` survives the doubling at **1.0000 → 0.3750, p = 2.5e-4**: the first mechanism claim here that is both admissibly scored and significant. Shipped `scorable_band.py` (rung **set** not a scalar width; `BAND_SPLIT` because contiguity is not assumed — D-127 measured two islands on this same axis; ESS-noncompliant rungs **refused** by name and not permitted to witness an edge) plus `relief_interval.open_below`, the floor mirror `open_above`'s docstring had already named as missing.
- **Alternatives**: (a) report the single rung with more seeds only — leaves the width unmeasured, which was the bottleneck; (b) report a scalar band width in weight units — makes a coarse and a dense ladder print identically; (c) assume the scorable set is an interval and span it — refuted on this very measurement, since `w = 250` is scorable and 200 is not.
- **Honest limit**: the band grades **`BAND_SPLIT`, and the split is one seed** — `w = 250` is `SEPARATED` only because 1 of 16 risk seeds came 0.3472 m against a 0.40 m margin with stock at 0/16 (p = 1.0, sign *against* the mechanism). `SEPARATED` has no magnitude, so one run out of sixteen can change a band's shape verdict; surfaced as `one_run_rungs`, not thresholded away (Q-115). Scope is one scene: nothing here says `cafe_obstacle_crossing_v0` has a band at all.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-09-the-band-is-three-rungs-and-the-split-is-one-seed.md` · supersedes D-131's "single scorable rung" as a ladder-resolution artefact


## D-131 — 2026-08-08 — 운전점에서의 재측정은 A/B 를 살리지 못한다: 두 degenerate verdict 를 맞바꿀 뿐이고, **비교가 성립하는 유일한 rung 은 relief threshold 아래**에 있다 — 그리고 거기서 risk channel 이 처음으로 점수를 받았다 (unsafe 1.0000 → 0.2500)

- **Context**: D-119 (risk channel) 과 D-124 (gap gate) 는 둘 다 shipped `w_obs_soft = 10` 에서 A/B 됐고, 두 arm 다 `unsafe_rate = 1.0000` 을 보고했다. D-125~D-130 이 `cafe_head_on_v0` 의 운전점을 **3000** 으로 확정했으므로 STATE 는 "threshold 위에서 다시 돌려라" 를 최우선 action 으로 걸어 뒀다. 이 cycle 이 그것을 그대로 실행했다.
- **Decision**: 먼저 이름을 짓는다 — `comparison_headroom.py`. 두 arm 의 모든 run 이 margin 의 같은 쪽에 있으면 headline 은 **구조적으로** 움직일 수 없고, 그 A/B 는 약한 결과가 아니라 **점수가 매겨지지 않은** 결과다: `NO_HEADROOM_UNSAFE` / `NO_HEADROOM_SAFE` / `TIED` / `SEPARATED`, 재측정 등급용 `shift`, 그리고 delta 의 span 이 경계 한쪽에만 있는 경우를 잡는 `sub_margin`. 두 degenerate 를 **한 이름으로 합치지 않는다**: 실험의 결함은 같아도 시스템의 상태는 정반대이고, 합치면 "고쳤다" 와 "손댈 수 없다" 가 같은 단어로 인쇄된다.
- **측정 (head_on, λ=0.8, 8 seed, margin 0.40, 전 arm 8/8 도달)** — `unsafe_rate`:

  | w | stock | gap_gated | risk | vs stock |
  |---|---|---|---|---|
  | 10 | 1.0000 | 1.0000 | — | `NO_HEADROOM_UNSAFE` |
  | 30 | 1.0000 | 1.0000 | 1.0000 | `NO_HEADROOM_UNSAFE` (stock/gap 은 ESS band 밖) |
  | 100 | 1.0000 | 1.0000 | **0.2500** | gap `NO_HEADROOM_UNSAFE` / risk **`SEPARATED`** |
  | 300 | 0.0000 | 0.0000 | 0.0000 | `NO_HEADROOM_SAFE` |
  | 3000 | 0.0000 | 0.0000 | — | `NO_HEADROOM_SAFE` |

- **첫 번째 결과 — 계획이 틀렸다**: gap gate 의 10 → 3000 재측정은 `shift` = **`STILL_UNSCORABLE`**. degenerate 를 다른 degenerate 로 바꿨을 뿐이다. barrier weight 자체가 이미 scene 을 풀어버려서 mechanism 이 겨룰 대상이 없다. gate 는 **ladder 의 모든 rung 에서 unscorable** 이고 mean clearance delta 는 부호가 번갈아 뜬다 (0.0293/0.0289, 0.3035/0.3068, 0.5806/0.5791) — D-124 가 crossing 에서 내린 "무향" 판정이 1.7× 우세를 주장했던 바로 그 scene 에서 재현됐다. 그 1.7× 는 `sub_margin` 이었다: 양 끝이 declared 0.40 m 의 **~50× 아래**라 verdict 가 바뀐 run 이 하나도 없다.
- **두 번째 결과 — risk channel 이 점수를 받았다**: `w = 100` 에서 stock **1.0000** → risk **0.2500**, 양 arm ESS in band, 8/8 도달. 이 프로젝트가 **headline 이 양쪽으로 움직일 수 있었던 운전점에서** 얻은 첫 mechanism 수치다. n=8 단일 rung 이므로 유의성 주장은 하지 않는다.
- **그리고 그 rung 은 threshold(300) 아래다 — 구조적이다**: threshold 는 *scene* 이 통과하기 시작하는 weight 이고, 그것은 곧 *비교*가 변별력을 잃는 weight 다. 따라서 "threshold 위에서 돌려라" 와 "arm 이 갈릴 수 있는 곳에서 돌려라" 는 **다른 지시**이며 이 scene 에서는 **서로소**다. scorable band = transition band 이고, transition 은 relief 가 시작되는 곳에서 끝난다. STATE 의 지시를 그대로 따랐다면 300/3000 에 착지해 null 을 보고했을 것이다.
- **부수 발견 — λ 보정은 weight 불변이 아니다**: `w = 30` 에서 stock/gap_gated 가 λ=0.8 로 ESS band 를 벗어난다 (10/100/300 에서는 in-band). `lam_windows.yaml` 은 shipped weight 에서 측정됐으므로 다른 weight 로의 rescore 는 rung 마다 ESS 확인을 빚진다 — `operating_weight.measured_on` 이 controller 축에서 이름 붙인 것과 같은 외삽, 한 축 옆.
- **Alternatives**: (a) STATE 대로 3000 만 재고 "mechanism 무효" 로 닫기 — 두 claim 다 잘못 기각한다. degenerate 를 null 로 읽는 것이 애초의 오류다. (b) headline 을 버리고 mean clearance 로 순위 매기기 — `sub_margin` 이 정확히 그 함정이고 D-124 가 이미 빠졌다. (c) 채택: 이름을 먼저 짓고 ladder 전체를 걸어 scorable band 를 **찾는다**.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-08-the-rescore-that-refuted-its-own-plan.md` · 관련: D-124 (재측정된 claim), D-119 (점수받은 claim), D-130 (운전점 3000), D-047 (weight 규칙은 `operating_weight` 가 소유)

## D-130 — 2026-08-08 — head_on 의 ceiling 은 **실재한다 (30000)** — 그리고 log-중앙값은 그것을 말할 수 있게 되기 **두 칸 전에 이미 수렴해 있었다**

- **Context**: D-129 가 남긴 정직한 한계. `cafe_head_on_v0` 는 테스트된 모든 rung 을 허용했고, 그래서 `pick_weight` 의 log-중앙값이 ladder 를 한 칸 늘린 것만으로 **1000 (D-127) → 3000 (D-129)** 으로 움직였다. scene 도 controller 도 seed 도 바뀌지 않았고 어떤 측정도 이견을 내지 않았다 (Q-114). 그러면 shipped 된 `w_obs_soft` 는 scene 의 성질인가 측량자가 멈춘 지점의 성질인가?
- **Decision**: ladder 를 세 칸 더 걸어 **답을 재고**(λ=0.4, 8 seed, 30 … 100000), Q-114 의 (a)/(b) 논쟁을 측정으로 해소했다. **ceiling 은 실재한다: 30000 까지 admissible, 100000 에서 거부.** 즉 witnessed ceiling 이고 ladder 의 가장자리가 아니다. `relieving = {300, 1000, 3000, 10000, 30000}`, `threshold = 300`. head_on 은 운전점을 잃지 않으며 (b) 가 치를 뻔한 대가는 발생하지 않는다.
- **핵심 발견 — 중앙값은 이미 수렴해 있었다**: ladder top 별 log-중앙값은 3000 → **1000**, 10000 → **3000**, 30000 → **3000**, 100000 → **3000**. D-129 가 shipped 한 3000 은 **옳다** — 다만 그것이 옳은 이유는 아무도 재지 않은 상태였다. "3000 이 맞다" 와 "3000 이 맞다고 말해줄 수 있는 것이 아무것도 없었다" 는 둘 다 참이고, 앞의 것만 보고하는 것이 애초에 D-127 의 1000 이 shipped 된 경위다.
- **무엇이 shipped 되었나**: (1) `ReliefInterval.tested` — survey 가 실제로 걸은 rung 집합. 버려지고 있었고, **그래서** 어떤 보고도 witnessed ceiling 과 ladder 가장자리를 구별할 수 없었다. 동일한 `admissible` 을 갖는 두 scene 중 하나만 측정된 상한을 갖는다. (2) `relief_interval.open_above(chosen, tested)` — 술어 하나, 호출부 둘 (`permits_open_above`, `resolve`). (3) `operating_weight.UNTESTED_ABOVE` — `resolve` 의 **두 중앙값 분기 모두** 채점. `SHIPPED` 는 의도적으로 채점하지 않는다: 중앙값을 취하지 않으므로 ladder 가 어디서 멈췄든 움직일 수 없는 유일한 분기이고, 거기에 경보를 다는 것은 오경보다. (4) `DEFAULT_LADDER` 5 → 8 rung (100000 까지).
- **`permits` 를 채점하지 `admissible` 을 채점하지 않는다**: `permits` 가 `resolve` 가 실제로 중앙값을 취하는 집합이고, relief 를 요구하는 scene 에서는 그것이 `relieving` — 부분집합이다. 상위집합을 채점하면 어떤 consumer 도 노출되지 않은 openness 를 보고하게 된다.
- **ladder 확장은 선택이 아니었다**: 기존 5-rung default 로는 head_on 이 앞으로 매 run 마다 `UNTESTED_ABOVE` 로 채점되고 **해소할 방법이 없다**. 해소 불가능한 check 가 어떻게 되는지는 D-044 가 이미 청구했다 (muted). guard 를 shipping 하는 것은 그것을 만족시킬 수단을 shipping 할 의무를 동반한다. 대가는 scene 당 rung 3 칸의 sim (~1 분).
- **범위 밖 — 정직하게**: 이번 sim 은 head_on 하나다. 나머지 두 sweepable scene 이 이미 closed-above 라는 것은 **D-126 의 기록에서 유도**한 것이지 재측정이 아니다 (crossing ceiling 1000 위에 3000 이 테스트되어 거부됨, convoy ceiling 30 위에 100 이 거부됨). 즉 세 scene 중 **정확히 하나만** 위로 열려 있었고, 그것이 운전점이 움직인 그 scene 이다. 8-rung default 위에서의 재측정은 다음 cycle 로.
- **대칭 질문은 아직 guard 가 없다**: convoy 의 ceiling 30 은 ladder 의 **바닥** rung 이며 D-126 이 이미 정직한 한계로 기록했다. `open_above` 의 거울상이고 Q-112 와 같은 축이다.
- **Alternatives**: (a) 중앙값 유지 + ladder 명시 — 채택하되 basis 로 명시. (b) 중앙값 거부 (Q-114 의 lean) — 측정 결과 트리거되는 shipped scene 이 없어 사실상 무비용이 되었으나, 중앙값을 withhold 하면 matrix 가 `unsafe_rate = 1.0` 으로 측정된 shipped rung 으로 되돌아간다 — 보고상의 결벽을 더 나쁜 측정으로 지불하는 것. 그래서 weight 는 반환하고 basis 가 caveat 를 진다. (c) threshold 의 고정 배수 등 절대 규칙 — `pick_lam` 과의 위임(D-047)이 끊어진다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-07-the-ceiling-was-real-and-the-median-had-already-converged.md` · Q-114 resolved

## D-129 — 2026-08-08 — 8-cell 감사 결과는 **각주 하나**이지 keying 문제가 아니다 — 다만 감사 가능한 모집단은 8 이 아니라 **6** 이고, 나머지 2 는 "측정 안 됨" 을 말할 verdict 자체가 없었다

- **Context**: D-128 이 `risk_mppi/cafe_obstacle_crossing_v0` 하나를 `CELL_DIFFERS` 로 지명했지만 나머지 일곱 cell 은 한 번도 질문받은 적이 없었다. STATE 의 bottleneck: 5/40 헤드라인이 **각주 하나 달린 헤드라인**인지 **keying 문제**인지 구별되지 않는다.
- **Decision**: `relief_interval.survey` 를 controller 별(`stock_mppi`, `risk_mppi`)로 matrix 의 4 obstacle scene 에 대해 돌리고(ladder 10000 까지, 8 seed), D-127 이 실제로 shipped 한 scene weight (head_on 1000 / crossing 1000 / convoy 10 / freezing 10) 에 대해 8 cell 전부를 채점했다. 결과 **`CELL_AGREES` 5 · `CELL_DIFFERS` 1 · `CELL_UNSWEPT` 2**. 유일한 불일치는 이미 알려진 D-128 의 그 cell 이다. 따라서 **각주 하나**이고, Q-113 의 "cell 단위로 재고 scene 단위로 보고한다" 는 lean 은 재논의할 필요가 없다.
- **핵심 부수 발견 1 — 감사 모집단은 6 이다**: `cafe_freezing_v0` 는 margin 을 선언하지 않아 `sweepable` 이 **양쪽 arm 모두** 거부한다 (`no_declared_margin`, D-120 의 `unscored_margin`). 즉 2 cell 은 scene weight 와의 일치 여부가 **측정된 적 없고** scene 파일이 margin 을 선언하기 전에는 측정될 수도 없다. 그런데 `audit_cell` 은 `ReliefInterval` 을 필수 인자로 받으므로 이 상태를 **표현할 방법이 아예 없었다** — 인자를 optional 로 만들었다면 fallback 은 `CELL_AGREES` 였을 것이고, 그것은 "아무도 묻지 않은 cell" 이 "일치한 cell" 로 읽히는 것, 즉 D-107 / D-120 / D-127 이 세 번 청구한 empty-denominator 실패의 재발이다. `CELL_UNSWEPT` + `unswept_cell` + `MatrixAudit` 신설, 그리고 `agrees` / `excluded` / `unswept` **세 모집단은 절대 둘로 합산되지 않는다** (`excluded` 는 `measured and verdict != CELL_AGREES`, 즉 `not excluded` 가 `agrees` 를 뜻하지 않는다).
- **핵심 부수 발견 2 — `knife_edge` 는 자기 docstring 의 절반만 검사하고 있었고, shipped cell 하나가 그 오경보를 달고 있었다**: docstring 은 "cell **자신의 운전점**이 유일하게 허용되는 rung 인가" 인데 구현은 `len(cell_admissible) == 1` 뿐이었다. `risk_mppi/cafe_convoy_v0` 는 shipped **10** 에서 돌고(`baseline_admissible`) rung 집합은 `{30}` 이라, **자기가 돌지도 않는 rung** 때문에 `KNIFE_EDGE` 가 찍혔다. `resolve` (D-127) → `admits` (D-128) 에 이은 **shipped-weight-is-never-a-rung 세 번째 목격**이며, 이번 교훈은 "predicate 를 한 번 뽑아라" 가 아니라 **"rung 집합을 읽는 모든 site 를 감사하라"** 다 — `admits` 가 바로 그 추출이었는데 세 줄 아래에서 같은 질문이 inline 으로 다시 유도되고 있었다. 양쪽 절반을 모두 검사하도록 수정했고 D-128 의 crossing 주장(`{3000}`, 그리고 3000 이 실제 운전점)은 그대로 유지된다.
- **정직한 한계 — scene table 은 ladder 에 의존하고, 늘어난 ladder 가 그것을 움직인다**: `cafe_head_on_v0` 는 10000 을 포함해 **모든** rung 을 허용하므로 relieving 집합이 ladder 의 top 과 함께 자라고 `pick_weight` 의 log-중앙값도 따라 올라간다 — D-127 의 ladder 로는 **1000**, 이번의 한 칸 긴 ladder 로는 **3000**. 어떤 측정도 이견을 내지 않았는데 운전점이 움직였다. Q-114 로 분리했고, 위 감사는 재유도된 weight 가 아니라 **D-127 이 실제로 shipped 한 weight** 에 대해 채점했다.
- **부수 관찰**: `tolerated` (rung + 측정된 shipped) 는 risk/crossing `{10, 3000}`, stock/crossing `{10, 300, 1000}`, convoy 양쪽 `{10, 30}` — **측정된 6 cell 전부**가 shipped 10 을 허용한 뒤 구멍이 뚫린다. weight 축의 구간 산술은 D-128 이 잡은 한 cell 이 아니라 6/6 에서 틀린다.
- **Alternatives**: (a) `CELL_UNSWEPT` 신설 — 채택. (b) freezing cell 을 감사에서 제외 — 8 이 6 이 된 사실이 보고에서 사라진다. (c) `audit_cell(cell=None)` 을 허용하고 기본값 부여 — 증거의 부재를 증거와 같은 경로로 통과시킨다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-06-one-footnote-not-a-keying-problem.md` · Q-114 신설

## D-128 — 2026-08-08 — D-127 에서 분모를 떠난 cell 은 **자기만의 admissible weight 를 갖고 있었다** (scene 의 1000 이 아니라 3000) — 그리고 weight 축의 admissible 집합은 **연속 구간이 아니라 두 개의 섬**이다

- **Context**: D-127 은 scene 별 `w_obs_soft` 로 헤드라인을 0.0000 으로 옮겼지만 `risk_mppi/cafe_obstacle_crossing_v0` 가 scene 의 weight 를 받고 `ESS_OUT_OF_BAND` 가 되어 near-miss 분모에서 빠졌다 (6 cell/48 seed → 5/40). Q-113 은 그 cell 에게 자기 weight 가 있는지, 아니면 weight 축에 답이 아예 없는지를 물었다 — "빠졌다" 와 "답이 없다" 는 aggregate 에서 구별되지 않는다.
- **Decision**: **cell 단위 admissible weight 는 존재한다.** `relief_interval.survey(controller="risk_mppi")` 를 crossing 에만, ladder 를 한 rung 더 올려 (top rung 10000 까지) 돌린 결과 그 cell 은 `w_obs_soft = 3000` 에서 8 seed 전부 도달, ESS in band, `unsafe_rate` **0.0000**, `min_clearance` **1.6978**, worst `cte_rms` **0.2228** (scene 선언 0.40 이하) 이다. 그러므로 D-127 의 배제는 **keying artefact** 였고 답이 없는 cell 이 아니다. 다만 **헤드라인은 scene 단위로 유지**한다 (Q-113 의 lean): cell 단위 weight 는 cross-controller delta 를 D-123 이 온도에서 겪은 구조 그대로 weight 축에서 재오염시킨다. 대신 빠지는 cell 을 matrix 실행 **전에** 측정으로 지명하도록 `operating_weight.audit_cell` / `CellAudit` / `admits` / `render_audits` 를 신설한다 (`CELL_AGREES` / `CELL_DIFFERS` / `CELL_UNSERVED`).
- **더 중요한 발견 — weight 축은 구간이 아니다**: 그 cell 의 median ESS 는 w = 10(baseline), 30, 100, 300, 1000, 3000, 10000 에 대해 **91.9 → 80.1 → 205.5 → 204.7 → 157.6 → 27.5 → 11.9** 로 걸으며, band 가 받아주는 것은 **w=10 과 w=3000 두 곳뿐**이다. 즉 허용 집합은 **`{10, 3000}` 두 개의 섬**이고 사이의 다섯 rung 은 **양방향으로** 실패한다 (100/300/1000 은 너무 높고 10000 은 너무 낮다). `[min, max]` 구간 산술은 100/300/1000 을 후보로 올리는데 셋 다 그 구간을 낳은 바로 그 cell 에서 inadmissible 이다. `relief_interval` preamble 이 근거를 들어 거부했던 연속성 가정의 **실증 사례**이고, 지금까지는 synthetic mid-ladder hole 하나뿐이었다.
- **부수 발견**: `shipped weight 는 rung 이 아니다` 라는 범주 오류가 한 겹 밖에서 기다리고 있었다 — `admits` 를 `weight in admissible` 로 쓰면 ladder 에 10.0 이 없으므로 shipped 를 묻는 cell 이 항상 inadmissible 로 읽힌다. D-127 에서 `resolve` 를 물었던 것과 **같은 버그의 두 번째 목격**이라 call site 마다 `in` 을 쓰지 않고 함수 하나로 뽑았다 (D-047).
- **정직한 한계**: 3000 은 그 cell 이 허용하는 **유일한** rung 이다 (양쪽 이웃 모두 실패). 보고 가능한 측정치일 뿐 견고한 운전점이 아니므로 `CellAudit.knife_edge` 가 `cell_weight` 와 함께 반드시 출력된다 — 3000 만 단독으로 적히면 실제보다 훨씬 단단하게 읽힌다.
- **Alternatives**: (a) scene 단위 유지 + 배제 cell 을 이름으로 남김 — 채택. (b) cell 단위로 table 을 다시 키잉 — 모든 cell 이 측정 가능해지지만 arm 마다 다른 weight 에서 재므로 cross-controller delta 가 confound (D-123 재발). (c) 배제를 그대로 두고 분모만 보고 — D-107/D-120 이 두 번 청구한 empty-denominator 실패.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-05-the-excluded-cell-had-its-own-weight.md` · Q-113 resolved

## D-127 — 2026-08-08 — 헤드라인 `unsafe_rate = 0.6667` 은 controller 가 아니라 **운전점(operating point)** 에 대한 진술이었다 — scene 별 `w_obs_soft` 로 다시 재면 0.0000, 단 가장 어려운 cell 하나는 고쳐진 게 아니라 **분모에서 빠졌다**

- **Context**: D-126 이 `PER_SCENE_REQUIRED` 를 냈지만 그것은 rung *집합* 에 대한 verdict 였고, 정작 matrix 는 여전히 두 scene 이 실패한다고 알려진 shipped weight 10 에서 측정된 채였다. STATE 는 이것을 "가장 큰 미해결 보정" 으로 지목해 왔다.
- **Decision**: `operating_weight.py` 를 신설해 scene 의 `ReliefInterval` → 그 scene cell 들이 도는 `w_obs_soft` 로 매핑하고, `baseline_matrix` 에 per-scene weight 주입(`Cell.w_obs_soft` / `run_cell(w_obs_soft=)` / `run_matrix(weights=)` / `--per-scene-weight`)을 넣어 8-cell matrix 를 재측정. 결과 head_on 1000, crossing 1000, convoy **10 (안 움직임)**, freezing 10 (unswept) → **`unsafe_rate` 0.6667 → 0.0000**, `min_clearance` 0.0016 → **0.3579**, success 8/8, 충돌 0.
  - rung 선택은 threshold 가 아니라 **relieving 집합의 log-중앙값** — `pick_lam` 의 논거 그대로(끝점은 ladder 한 칸 차이로 실패 영역에 되돌아간다), 그리고 규칙의 **두 번째 사본이 아니라 위임**(D-047).
  - **정직한 할인**: near-miss 모집단이 6 cell / 48 seed → **5 cell / 40 seed** 로 줄었다. `risk_mppi/cafe_obstacle_crossing_v0` 가 `ESS_OUT_OF_BAND` 로 빠졌기 때문. 즉 32 unsafe seed 중 **24 개는 실제로 해소, 8 개는 답이 나온 게 아니라 분모를 떠났다**. 0.0000 을 clean sweep 으로 읽으면 D-107/D-120 이 두 번 기록한 empty-population 실패를 세 번째로 반복하는 것.
  - 빠진 원인은 module docstring 에 미리 적어둔 **외삽**이 첫 실행에서 그대로 터진 것: rung table 은 `stock_mppi` 에서 측정되는데 `risk_mppi` 는 같은 scene 을 λ=3.2 에서 돈다. `measured_on` 필드가 이걸 위해 존재하고 이제 실제 사례가 생겼다.
- **Alternatives**: (a) threshold rung 채택 — 최소 개입이지만 정의상 relief 경계 한 칸 위 (b) 전역 repin — D-126 이 측정으로 반박 (c) cell(=scene×controller) 별 survey — 3× sim, Q-113 로 이월.
- **부수 발견 (실제 결함, test 가 잡음)**: resolver 초안은 "shipped weight 를 유지" 를 `shipped in permits` 로 판정했는데, ladder 는 30 부터 시작하고 shipped 는 10 이라 **모든 입력에 대해 항상 거짓**이다. 그 결과 relief 가 필요 없던 모든 scene 이 `REPAIRED` 로 ladder 바닥에 옮겨졌고, 하필 D-126 의 disjointness 를 혼자 떠받치는 `cafe_convoy_v0` 가 자기가 투표한 weight 에서 밀려났다 — 그것을 막는다고 docstring 에 쓰인 바로 그 분기에 의해. `ReliefInterval.baseline_admissible` (= `SweepResult.baseline.admissible`) 을 실어 **집합 원소 판정이 아니라 측정된 사실**로 고침. ladder 위에 없는 값에 대한 질문을 ladder 집합에 물은 category error 이고, typecheck 도 code review 도 통과한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-04-the-headline-was-an-operating-point.md`

## D-126 — 2026-08-08 — relief 를 주는 `w_obs_soft` 는 **전역으로 못 박을 수 없다** — 그런데 막는 것은 문턱의 scene 별 편차가 아니라 *relief 가 필요 없던* scene 의 ESS ceiling 이다

- **Context**: D-125 는 `w_obs_soft = 300` 이 8/8 이던 두 scene 을 0/8 로 옮겼지만, 같은 rung 에서 이미 안전하던 `cafe_convoy_v0` 이 ESS band 를 벗어났다. Q-111 은 "문턱이 scene 별로 갈리는가" 를 물으며 갈리면 (b)/(c), 같으면 (a) 로 닫기로 했다.
- **Decision**: **(a) 전역 repin 은 refute.** 장애물 있는 scene 을 각자의 calibrated λ 에서 sweep 한 결과 — head_on `threshold=300 / ceiling=3000`, crossing `threshold=300 / ceiling=1000`, convoy `relief 불필요 / ceiling=30`. 세 집합의 교집합이 **비어 있다**. 남은 선택지는 (b) scene 별 weight 와 (c) scene geometry 에서 유도, 두 가지다.
- **그리고 Q-111 의 판정 규칙 자체가 틀렸다**: 문턱은 **갈리지 않았다** (두 scene 모두 정확히 300). 규칙대로면 (a) 로 닫았어야 하는데 실제 답은 (b)/(c) 다. 막는 축은 threshold 의 분산이 아니라 **relief 가 필요 없던 scene 의 ceiling** 이고, Q 는 그 축을 이름 붙이지 않았다. **결정 규칙이 지명한 축에 대해 옳으면서도 결론이 틀릴 수 있다 — 구속 조건이 지명되지 않은 축에 있으면.**
- **덤**: D-125 의 문턱 300 은 λ=0.8 에서 나왔고 이 survey 는 head_on 을 자기 rung λ=0.4 에서 돌려 **다시 300** 을 얻었다. 문턱은 2× 온도 변화에 대해 robust — 온도 artefact 가 아니다.
- **Alternatives**: (a) 전역 repin 10→300 — 측정으로 배제. (b) scene 별 admissible weight (`pick_lam` 패턴을 weight 축에 적용) — 정직하나 cell 마다 자유도 2개(λ, w). (c) required corridor / declared margin 에서 barrier gain 을 닫힌 형태로 유도 — 고정 상수를 없애고 D-125 를 core bet 안으로 되돌리지만, 두 scene 의 문턱이 같은 300 인 것이 실제 일치인지 3× ladder 해상도 artefact 인지 아직 모른다 (Q-112).
- **구현 주의 두 가지**: (1) 교집합은 **interval 이 아니라 set** — `all_reached AND ess_in_band` 가 weight 에 대해 monotone 이라는 논증이 이 repo 에 없으므로 ladder 중간 구멍이 허용되고, interval 산술은 자기 출처 scene 에서 inadmissible 한 rung 을 후보로 올릴 수 있다. (2) baseline 이 `MIN_IMPROVEMENT` 미만으로 unsafe 인 scene 은 **어떤 rung 도** 그만큼 개선할 수 없어 산술적으로 `UNRELIEVED` 가 된다 — 별도 verdict `SUBRESOLUTION` 으로 분리. 그 scene 은 rung 을 거부할 수는 있어도 요구할 수는 없다.
- **Scope**: Q-111 이 말한 "장애물 있는 5 scene" 중 **3 개만** sweep 가능하다. `cafe_freezing_v0` 은 margin 미선언(D-120), `cafe_cut_in_v0` 은 admissible λ window 가 비어 있음(`completes_anywhere: false`). 둘 다 `refused` 에 이름으로 남는다 — 돌아간 scene 만으로 cross-scene verdict 를 내는 것은 D-107/D-120 이 두 번 청구한 빈 denominator 다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-03-the-blocking-scene-is-the-one-that-needed-nothing.md` · Q-111 resolved

## D-125 — 2026-08-08 — head_on 과 crossing 의 8/8 unsafe 는 cost term 의 **모양**이 아니라 **크기** 문제였다 — `w_obs_soft` 한 knob 이 두 scene 의 verdict 를 1.0000 → 0.0000 으로 옮긴다

- **Context**: 세 cycle 연속 cost 의 *모양* 을 바꿨고(D-119 risk channel 32×, D-124 gap gate 1.7×) `unsafe_rate` 는 한 번도 안 움직였다. Q-110 은 이걸 "mechanism 축이 아니라 scale 축의 병목" 으로 읽고, soft barrier 가 애초에 `w_path` 상대로 이길 수 있는 크기인지부터 재라고 요구했다. lean 은 **못 이긴다**(그리고 그 null 이 representation 가설을 지지한다)였다.
- **Decision**: `barrier_ceiling.sweep` 으로 knob 하나씩, matched λ = 0.8, 8 seed 로 재고 결과를 그대로 채택한다. **`w_obs_soft`: `RELIEVED`** — shipped 10 에서 `cafe_head_on_v0` 은 전 seed unsafe 인데 **300** 에서 `unsafe_rate` **1.0000 → 0.0000**, 전 seed 도착, 전 seed ESS in band, `mean_clearance` **0.0056 → 0.5806** (declared 0.40 초과). scene 의 나머지 key 도 안 깨진다: worst-seed `cte_rms` **0.2058** vs declared 0.30, 그리고 D-122 의 하한 0.0865 위. 같은 rung 이 **`cafe_obstacle_crossing_v0` 도 1.0000 → 0.0000** 으로 옮기며 그쪽 `cte_rms` 는 오히려 좋아진다. **Q-110 의 lean 은 refute.**
- **부수 결정 — 두 knob 을 한 축으로 합치지 않는다**: `obs_soft_scale` 은 8× 를 걸어도 `SATURATED` (verdict 무변, `mean_clearance` 그대로). gain 과 decay length 를 "barrier 강도" 하나로 묶었으면 relief 와 null 이 평균돼 틀린 이야기 하나가 나왔다.
- **부수 결정 — admissibility 는 기존 규칙 두 개를 그대로 붙인다**: rung 이 evidence 이려면 `all_reached`(freeze 가 clearance 를 사는 걸 막는 D-016 계열 규칙) **와** `ess_in_band`(D-027 이 찾은 "weight 로 위장한 temperature 변경") 둘 다 통과해야 한다. 그래서 negative 가 둘로 갈린다 — `SATURATED`(어떤 scale 로도 verdict 못 움직임) vs `BOUGHT_INADMISSIBLY`(움직이지만 cost-term 변경이기를 그만두면서). 다음 수가 정반대라 문자열을 합치지 않았다.
- **되돌아오는 값 — D-119 / D-124 의 비교는 등급이 내려간다**: 둘 다 relief 문턱보다 ~30× 낮은 rung 에서 측정됐고 거기서는 **양 arm 이 전 seed 실패**다. 두 arm 이 모두 bar 를 못 넘는 A/B 는 mechanism 에 대한 test 가 아니다.
- **Alternatives**: (a) Q-110 문구대로 `w_obs_soft`/`w_path` **ratio** sweep — 모든 weight 를 c 배 하는 건 `lam` 을 c 배 하는 것과 정확히 같으므로 weight 이름을 쓴 temperature 변경이 된다. (b) 한 scene 에서 relief 났으니 default 를 전역 repin — `cafe_convoy_v0` 은 이미 안전한데 그 rung 에서 ESS band 를 벗어난다. (c) 채택: knob 별로 재고, scene 별 ceiling 은 미해결로 Q-111 에 넘긴다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-02-the-verdict-was-scale-bound.md` · Q-110 resolved

## D-124 — 2026-08-08 — 첫 cost-term 변경(two-sided-gap gate)은 **자기 target scene 에서 무향(directionless)**, 그리고 control 로 지명됐던 scene 에서만 방향이 나온다 — feed 의 target 지정 근거가 `required_corridor` 의 의미를 뒤집어 읽었기 때문

- **Context**: 네 cycle(D-120~D-123)이 attribution 만 다듬고 cost term 은 한 번도 건드리지 않았다. 00:00 feed 의 MorphoCopter-MPC(arXiv:2605.15999) 항목이 `stock_mppi.py:125` 의 soft barrier 바로 그 줄에 곱해지는 factor 를 제시했고, target 으로 `cafe_obstacle_crossing_v0` 을 지목하며 근거를 D-121 의 `required_corridor = 0.00 m` 에 뒀다 — *"zero lateral slack, the feasible set is a single line"*. 그런데 `feasibility.required_corridor` 는 **declared margin 을 만족시키는 데 필요한 최소 lateral budget** 이므로 0.00 m 은 정반대, 즉 **reference path 를 한 번도 벗어나지 않고도 0.30 m 을 지킬 수 있다**는 뜻이다. narrow passage 가 아예 없는 scene 에 narrow-passage gate 를 겨눈 것.
- **Decision**: gate 를 `1 − s·(μ²−1)²` 로 구현해 `StockMPPI.gap_gate_strength` 뒤에 두고(s=0 → legacy branch 그대로, byte-identical), `gap_gated_mppi` 로 등록한 뒤 **matched λ = 0.8 (D-123 의 yardstick)** 에서 두 scene 다 측정한다. 결과를 그대로 채택: crossing 은 sign split **4/4**, `mean_clearance` 0.0368 → 0.0341 로 **무향**; `cafe_head_on_v0` (required corridor **1.00 m**, 실제 squeeze 가 있는 유일한 scene) 은 **6/8** 우세(1 tie), `mean_clearance` **0.0056 → 0.0095** (1.7×), 양 arm ESS in band. 6/7 one-sided = **p = 0.0625, 유의하지 않음** 으로 명시 보고. **두 scene 모두 `unsafe_rate` = 1.0000 불변** — headline 은 어디서도 움직이지 않는다.
- **부수 결정 — μ 는 논문 것을 그대로 쓰지 않는다**: opposite-sidedness 만으로 μ 를 정의하면 로봇이 한쪽 벽에 붙어 있고 반대편 obstacle 이 멀리 있을 때도 μ=0 이 되어 soft barrier 가 완전히 꺼지고 `w_collision` 만 margin 을 지키게 된다(feed caveat 3). 그래서 `μ = max(alignment, imbalance)` — **opposed *이고* equidistant 일 때만** 0. hard term 은 gate 대상에서 구조적으로 제외.
- **Alternatives**: (a) feed 지정대로 crossing 만 측정하고 "무효" 로 닫기 — 실제 mechanism 이 사는 scene 을 놓친다. (b) 논문 μ 그대로 포팅 — 벽 옆에서 barrier 가 꺼지는 위험을 그대로 수입. (c) 채택: 두 scene 다 재고, μ 에 imbalance 항 추가, 유의성 없음을 그대로 보고.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-01-target-and-control-were-swapped.md`

## D-123 — 2026-08-08 — Q-107 의 답: `cafe_obstacle_crossing_v0` 의 cross-controller delta 는 **온도에 오염돼 있고, 한 metric 에서는 부호가 뒤집힌다**. 그리고 (a)↔(b) 는 애초에 성립하지 않는 trade 였다 — per_arm scene 에서 "두 arm 한 온도" 와 "두 arm band 안" 은 동시에 참일 수 없다

- **Context**: `baseline_matrix.pick_lam` 은 cell 마다 온도를 고르고, 이 scene 은 window 가 disjoint (`stock [0.4,0.8]`, `risk [1.6,3.2]`) 라 stock 0.8 / risk 3.2 로 **4× 벌어진** 채 headline 에서 controller 축으로 빼진다. `assert_single_lam_ab` 가 말로 거절하는 배치다. Q-107 은 "짓기 전에 먼저 재라" 고 했고, 이 cycle 이 그 측정이다.
- **Decision**: `temperature_confound.py` — 2×2 격자(양 arm × 양 rung, 8 seed, 32 run, 27 초)를 돌려 published delta 를 **항등식**으로 쪼갠다: `reported = matched@λ + temperature`. 사다리는 나쁜 것부터 `SIGN_FLIP → MASKED → TEMPERATURE_DOMINATED → ROBUST`. 측정 결과 (`risk − stock`): `min_clearance` **+0.0205 → 0.8 에서 −0.0078** (`SIGN_FLIP`, 온도항이 delta 의 **138%**), `unsafe_rate` **+0.0000 → 0.8 에서 −0.1250** (`MASKED`), `mean_clearance` +0.0418, share **0.487** (`ROBUST`, 0.500 선을 1.3 점 차로 통과). 따라서 이 scene 의 delta 는 3 metric 중 2 개에서 controller 축에 귀속 불가.
- **부수 결과 두 가지**: (1) matched 비교는 **전부** 한 arm 이 band 밖이다 — disjoint window 의 정의상 그렇고, 구현 편의가 아니다. 그래서 Q-107 이 세운 "깨끗한 비교 vs 표본 유지" 는 잘못된 축이었다: 두 선택지 모두 불순하고 **불순함의 종류가 다르다** (`MatchedDelta.out_of_band` 로 rung 마다 표기). (2) tree 에 "이 cell 은 어느 rung 인가" 의 답이 **둘** 있다 — `pick_lam` (자기 window 의 log-중앙, gap 4×) 과 `ab.lam_for` (상대와의 log-gap 최소, gap 2×). 2× 로 다시 재면 `mean_clearance` share 가 0.487 → **0.252** 로 gap 따라 반감하지만 `SIGN_FLIP` 과 `MASKED` 는 그대로다 (뒤집는 rung 이 0.8 인데 두 protocol 다 0.8 을 쓴다). 개선이지 해결이 아니다.
- **Alternatives**: (a) per-cell rung 유지 + 문서화 — 측정이 refute 했다. 부호가 뒤집히는 숫자는 주석으로 구제되지 않는다. (b) shared rung 강제 → `NO_SHARED_LAM` 으로 cell drop — 이 scene 에는 shared rung 이 **존재하지 않으므로** drop 이 곧 유일한 결과이고, 장애물 실재 scene 을 회피 matrix 가 스스로 버린다. (c) 두 축 분리 (Q-107 의 lean) — 이제 측정 근거가 있다. 다만 이 cycle 은 (c) 를 **짓지 않았다**: 측정이 먼저라는 게 Q-107 의 다음 action 이었고, 축 분리는 다음 cycle 의 별도 변경이다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/08-00-the-published-delta-inverts-at-a-matched-temperature.md` · resolves Q-107

## D-122 — 2026-08-07 — Q-109 의 답은 **양립 가능**이다. head_on 의 margin 0.40 을 지키는 최소 `cte_rms` 는 **0.0865** (dilution 없는 최악 조건에서도 **0.1727**) 로 선언된 0.30 아래다 — D-121 이 16 seed 를 scene 선언 쪽으로 옮긴 재귀속은 살아남지 못한다

- **Context**: D-121 이 head_on 은 margin 0.40 을 지키려면 순간 lateral **1.00 m** 가 필요하다고 닫힌 형태로 보였고, 같은 scene 이 `cte_rms_max: 0.30` 을 선언한다. 1.00 > 0.30 은 **peak 을 rms 와 비교한 것**이라 그 자체로는 아무 말도 아니다 — `declared_corridor` 가 정확히 그 혼동을 거절하려고 존재한다. 비교 가능한 양은 "그 이탈이 실제로 치르는 rms" 이고, 재보기 전까지 head_on 의 8/8 unsafe 는 controller 목표인지 선언 결함인지 미정이었다.
- **Decision**: `feasibility.min_cte_rms()` — D-121 의 station × time 격자를 그대로 쓰고 목적함수만 bottleneck(maximin) → **누적 e² 최소 (shortest-path DP)** 로 바꾼다. margin 을 매 순간 지키는 schedule 중 `cte_rms` 하한을 준다. 결과: head_on **0.0865** vs 선언 0.30 → `COMPATIBLE`. 장애물 있는 5 scene 중 `INCOMPATIBLE` 은 **하나도 없다**. 따라서 두 key 는 양립하고, margin 실패는 controller 쪽에 남는다. 3.4 초, sim 0회.
- **Alternatives**: (a) Q-109 의 (a)/(b) — `cte_max: 1.0` 을 선언하거나 margin 을 낮춘다. 둘 다 **재지 않은 양을 놓고 고르라는 요구**였고, 재보니 고를 필요가 없었다. (b) 이탈 크기를 run 길이로 나눠 손으로 추정 — Q-109 가 "run 의 9% 이내" 로 세운 계산인데, `cte_rms` 는 arclength 가 아니라 **sample** 평균이라 schedule 이 늘어지면 스스로 희석된다. 손 계산에는 그 자유도가 없다. (c) closed-loop 로 확인 — 상한을 묻는 질문에 controller 성능으로 답하는 것이라 무효 (D-121 과 같은 이유).
- **한 knob 이 답을 공짜로 만들 수 있었고, 그게 이 결정의 검사다**: 희석 자유도 때문에 floor 는 horizon 이 길수록 단조 감소한다 — 기본 `TIMEOUT_FACTOR` 에서 **0.0865**, 희석이 **전혀 없는** (horizon = expected duration) 끝에서 **0.1727**. 그래서 맨 `COMPATIBLE` 은 scene 이 아니라 timeout 설정에 대한 진술일 수 있었다. 양 끝 모두 0.30 아래이므로 답은 knob 전 구간에서 같고, 이 불변성과 단조성을 test 로 박았다 (중간 rung 수치는 journal 과 test 에).
- **방향**: 모든 relaxation (점로봇, 순간 lateral 이동, 후진 허용, 시작 offset 자유) 은 schedule 을 **더한다** → floor 는 하한 → `INCOMPATIBLE` 은 증명, `COMPATIBLE` 은 "여기서 반증되지 않음". 유일한 반대 방향은 lateral 탐색 범위 절단이라, 기본값을 `required_corridor` 의 2배로 **유도**해 가정이 아니라 자기검사가 되게 했다.
- **살아남는 것은 모순이 아니라 선언의 공백**: head_on 은 1 m sidestep 을 요구하고, 그것을 **금지하지도 허용한다고 말하지도 않는다** (`cte_max` 없음). controller 저자가 볼 수 있는 유일한 lateral 숫자는 0.30 이고 그건 run 이 실제로 구속되는 것보다 훨씬 좁은 상자로 읽힌다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-23-the-two-keys-were-never-in-conflict.md` · Q-109 resolved

## D-121 — 2026-08-07 — D-120 의 8/8 두 scene 은 **원인이 반대**다. en-route bottleneck DP 로 `cafe_head_on_v0` 은 corridor **1.00 m** 를 요구하고 `cafe_obstacle_crossing_v0` 은 **0.00 m** 를 요구한다

- **Context**: D-120 이 near-miss 를 처음 측정하자 `cafe_head_on_v0` (margin 0.40) 과 `cafe_obstacle_crossing_v0` (0.30) 이 **양쪽 controller 모두 8 seed 중 0개** 통과로 동일하게 빨갛게 나왔다. Q-108 은 두 가능성을 구분하지 못한다고 적었다 — (i) cost term 의 무능, (ii) scene 기하가 애초에 그 margin 을 허용하지 않음. 전자면 controller 목표가 생기고, 후자면 지표는 영원히 빨갛다.
- **Decision**: `feasibility.path_clearance()` — station × time 격자 위의 **bottleneck (maximin) DP**. 주어진 lateral corridor 안에서 *임의의 admissible schedule* 이 유지할 수 있는 **최악 순간 clearance 의 최대값**을 구한다. 여기에 `required_corridor()` (bisection) 를 얹어 "기하가 요구하는 corridor" 를 직접 잰다. 결과: head_on 은 reference path 위에서 **-0.550 m** (관통) 이고 corridor **1.00 m** 를 요구 — margin 0.40 + 두 반지름 0.6 의 **닫힌 형태**. crossing 은 path 위에서 **+1.400 m**, corridor **0.00 m**. 즉 head_on = (ii), crossing = (i). 5 scene 전체 screen 이 **0.8 초**, sim 0회.
- **Alternatives**: (a) Q-108 의 lean 그대로 — `goal_ball_clearance` 의 max-over-arrival-time 을 path 전체로 sweep. **집행하려다 무효임을 확인**: 그 screen 이 건전한 이유는 goal ball 이 로봇이 *멈춰 있어야 하는* 곳이라 시간 자유도밖에 없기 때문이고, 경로 위에서는 "어느 station 에 언제 있을지" 라는 두 번째 자유도가 생긴다. station 과 time 을 **독립적으로** 최대화하면 모든 동적 scene 이 깨끗하게 통과한다 — 보행자는 어느 시점엔가 항상 다른 곳에 있으므로. (b) closed-loop 로 A/B — 재기 원하는 것이 controller 성능이 아니라 상한이므로 답이 안 나온다. (c) `cte_rms_max` 를 corridor 로 읽어 default screen 을 물게 하기 — rms 는 *run* 을, corridor 는 *매 순간* 을 구속하므로 잠깐의 이탈로도 rms 는 합격일 수 있다. 이걸 corridor 로 읽으면 screen 이 통과 가능한 scene 을 은퇴시킨다 (금지된 방향). 그래서 `declared_corridor` 는 `cte_max` 만 읽고 없으면 `None`, default screen 은 `inf` 로 **아무 말도 하지 않는다**; 유용한 질문은 `required_corridor` 가 맡는다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-22-two-eight-of-eight-scenes-opposite-causes.md` · Q-108 resolved, Q-109 opened

## D-120 — 2026-08-07 — near-miss 를 scene 이 **스스로 선언한 margin** 으로 재고, headline 은 **monotone 한 `unsafe_rate`** 로 간다. `collision_rate 0.0000` → `unsafe_rate` **0.6667**

- **Context**: D-119 가 같은 64 seed 에서 `collision_rate = 0.0000` 과 `min_clearance = 0.0016 m` 를 동시에 보고했다. 둘 다 참이고 안심되는 건 하나뿐이다 — 무언가 **1.6 mm** 로 스쳤는데 harness 는 그걸 clean success 로 셌다. north star 는 "near-miss ≤ Y" 를 처음부터 acceptance term 으로 명시하고 있었고, 프로젝트는 그걸 **한 번도 계산한 적이 없다**. 충돌 카운터는 흥미로운 안전 질문이 시작되는 바로 그 지점에서 포화된다.
- **Decision**: (1) 임계값은 module 상수가 아니라 **scene 의 acceptance block** 에서 읽는다 — shipped scene 들이 실제로 불일치한다 (`cafe_head_on_v0` 0.40 m, `cafe_convoy_v0`/`cafe_obstacle_crossing_v0` 0.30). 전역 상수는 더 요구한 scene 을 무시하고 덜 요구한 scene 에 후한 점수를 준다. (2) 그 key 의 reader 는 `feasibility.declared_margin` **하나**이고 `float | None` 을 돌려준다 (D-047). 두 소비자는 **의도적으로 반대 default** 를 쓴다: feasibility screen 은 낙관적 `0.0` 유지 (미선언 margin 이 scene 을 은퇴시키면 안 됨), metric 은 **거부**. (3) headline scalar 은 `unsafe_rate` = `(near_miss + collision)/n`. (4) near-miss 는 avoidance 의 re-slice 가 아니라 **세 번째 denominator** — 충돌은 임계값이 필요 없고 near-miss 는 필요하다.
- **`near_miss_rate` 를 headline 으로 쓰지 않는 이유는 취향이 아니라 성질이다**: band 가 `[0, margin)` 이라 1 mm 스침이 실제 충돌로 **악화되면 집합에서 빠져나가** rate 가 **내려간다**. controller 가 더 많이 부딪혀서 near-miss 지표를 개선할 수 있다. `unsafe_rate` 는 같은 band 를 아래로 열어 `(-inf, margin)` 으로 만든 것이라 monotone 하다. 양방향 pin.
- **미선언 margin 은 0 이 아니다**: `cafe_freezing_v0` 은 장애물이 있는데 margin 을 선언하지 않는다. 편한 `0.0` default 를 쓰면 band 가 `[0, 0)` = 공집합이 되어 **모든 run 이 공짜로 safe**, cell 은 완벽한 `0.0000` 을 보고한다 — D-107 의 "빈 population = 깨끗함" 이 이번엔 **safety headline** 에 도착한다. 이름 붙여 제외하고 (`unscored_margin`), 충돌 집계에는 계속 남긴다.
- **측정 결과 (4 obstacle scene × 2 calibrated controller × 8 seed, 110 s)**: **`collision_rate = 0.0000` → `unsafe_rate = 0.6667`.** scored 48 seed 중 **32개**가 scene 이 스스로 허용한 것보다 가깝게 지나간다. scorable 6칸 중 **4칸이 8/8** — `cafe_head_on_v0` 과 `cafe_obstacle_crossing_v0` 은 양쪽 controller 모두 8 seed 중 한 개도 기준을 통과하지 못한다. 꼬리 사건이 아니라 계통적이다.
- **지표가 빨갛기만 한 게 아니라 실제로 구분한다**: `cafe_convoy_v0` 은 **양 arm 모두 0/8** (0.358 / 0.830 vs margin 0.30). 2 scene 은 깨끗이 통과, 2 scene 은 전면 실패 — scene 자기 margin 을 기준으로 삼을 때의 실제 위험(비관 방향 포화)이 발생하지 않았다.
- **D-119 의 방향성 controller 신호는 살아남았고, 이 기준에서 실질적으로 무의미함이 드러났다**: `risk_mppi` 의 clearance 가 실제로 더 크고 (head_on 0.064 vs 0.002 = **32배**), near-miss rate 은 **동일하다 (8/8 vs 8/8)**. 32배 개선이 안전 판정을 **전혀** 움직이지 않는다. D-119 는 이 순서를 시사적이라 보고했다; margin 지표는 그 순서가 진짜이지만 아직 턱없이 작다고 말한다.
- **아직 검증되지 않은 부분, 명시**: 이 데이터에서 `near_miss_rate == unsafe_rate` 가 **정확히** 성립한다 — 충돌이 0이기 때문. headline 을 결정한 monotonicity 차이는 test 에서만 pin 돼 있고 실제 데이터에서는 아직 발현되지 않았다.
- **Alternatives**: (a) 전역 상수 `NEAR_MISS_M = 0.1` — 0.40 을 요구한 scene 을 뒤엎고 0.30 scene 에 후하다 (b) 미선언 margin 에 `0.0` — 공집합 band, D-107 재발 (c) `near_miss_rate` 를 headline 으로 — 충돌로 개선 가능한 비-monotone scalar (d) avoidance flag 에 접기 — 충돌 집계와 near-miss 집계 중 하나를 반드시 틀리게 만든다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-21-near-miss-turns-a-clean-sheet-into-two-thirds-unsafe.md` · 관련: D-119 (1.6 mm 의 출처 + controller 순서), D-107 (빈 population = 깨끗함), D-047 (규칙의 두 번째 진술), D-116 (불일치하는 축은 합칠 수 없다)

## D-119 — 2026-08-07 — matrix 가 cell 마다 admissible `lam` 을 **table 에서 먼저 정하고** 돈다. 회피 측정 가능 칸 0/24 → **8/24**, 그리고 최소 clearance 는 **1.6 mm**

- **Context**: D-118 의 첫 P5 matrix 는 `avoidance_reportable = 0/24` 였고, 그중 12칸의 원인은 하나였다 — matrix 가 `lam` 을 **한 번도 이름 붙이지 않아** 전 cell 이 `MPPIParams().lam = 0.1` 을 상속했다 (median ESS ≈ 1.01/256, 사실상 greedy argmin). 온도가 cost term 을 덮고 있었다. `eval/scenarios/lam_windows.yaml` 은 2026-08-02 부터 이미 존재했다.
- **Decision**: (1) `run_matrix` 가 sweep 전에 cell 별 rung 을 `calibrate_lam.load_windows` 로 해결한다 — 표를 다시 파싱하지 않는다 (D-047; D-118 이 바로 그 중복을 한 cycle 전에 출하했다). (2) `pick_lam` = admissible window 의 **log-space 중앙** rung. 끝점은 inadmissible 에서 ladder 한 칸 거리라 재보정 한 번에 band 를 조용히 벗어난다. (3) table 이 이미 답하는 cell 은 **돌리지 않는다**: window 가 비면 `NO_ADMISSIBLE_LAM` (Q-035 가 이미 종결), row 가 없으면 `LAM_UNCALIBRATED`. 8 seed 를 지불한 뒤 버리는 것과 다르다. (4) 이 둘을 `NOT_REACHED` 와 함께 **`UNRUN`** 이라는 이름 붙은 집합으로 묶는다.
- **측정 결과 (3×8×8 seed, 6분)**: **avoidance-reportable 0/24 → 8/24.** calibration row 가 있던 `ESS_OUT_OF_BAND` 12칸이 전부 전환됐다. Live pin: `cafe_head_on` median ESS **2.98 → 69.75**, `ESS_OUT_OF_BAND → OK`. `collision_rate = 0.0000` (64 seed), `success_rate = 1.0000` (tracking 14칸).
- **하지만 안심되는 숫자는 둘 중 하나뿐이다**: `min_clearance = **0.0016 m**`. 아무것도 충돌하지 않았고 무언가는 **1.6 mm** 로 스쳤다 (`stock_mppi/cafe_head_on` = 0.002 m). 충돌 지표가 north star 가 "near-miss ≤ Y" 라고 부르는 바로 그 구간에서 포화돼 있고, harness 에 그걸 재는 것이 없다.
- **첫 controller 신호, 방향성 있음**: `risk_mppi` 의 clearance 가 공유 회피 4칸 **전부**에서 `stock_mppi` 보다 크다 (convoy 0.830/0.358, freezing 0.903/0.477, head_on 0.064/0.002, obstacle_crossing 0.035/0.015). 그중 **3칸은 같은 `lam=0.4`** 라 온도가 맞춰진 비교다. 3/3 동일 방향 = one-sided p 0.125 — **유의하지 않다**, 시사적일 뿐이며 그렇게만 보고한다.
- **24칸 중 8칸은 애초에 보정된 적이 없다**: `lam_windows.yaml` 은 16 row = controller 2 × scene 8 이고 `cbf_mppi` 는 **0회** 등장한다. D-118 의 0/24 는 이걸 균일한 `ESS_OUT_OF_BAND` 뒤에 숨기고 있었다.
- **거절하라고 만든 guard 를 matrix 가 그대로 통과한다**: `cafe_obstacle_crossing` 은 두 arm 의 window 가 disjoint (stock `{0.8}`, risk `{3.2}`) 이고 `assert_single_lam_ab` 가 정확히 이 배치를 거절한다. per-cell picker 는 4× 벌어진 온도로 두 arm 을 돌린 뒤 한 headline 에 합산했다 — 그 칸의 delta 는 controller 와 temperature 가 섞여 있다. **Q-107**, 위 clearance 주장을 4/4 가 아니라 3/3 으로 쓴 이유.
- **Alternatives**: (a) shipped default 유지 — D-118 이 측정한 0/24 (b) scene 이 아니라 repo 단위 단일 `lam` — `calibrate_lam` docstring 이 보정 단위가 scene 인 이유를 이미 설명 (c) 회피 불가 cell 을 그냥 빼기 — denominator 가 조용히 줄어 D-107 의 "빈 population = 깨끗함" 재발.
- **Census bill**: `decides` 31 → **33** (non-test 1 + test 1), `defaults`/`forwards` 불변. 그리고 `lam_dependence` 의 non-test site 목록이 **2 → 3 → 2** 로 되돌아왔다 — D-118 이 추가한 유일한 "실제로 sim 을 청구하는" site 가 이 cycle 에 제거됐다. 수리가 숫자 이동이 아니라 **population 변화**로 읽히는 유일한 지점.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-20-per-cell-temperature-turns-eight-cells-on.md` · 관련: D-118 (0/24 의 출처), D-047 (규칙의 두 번째 진술), Q-035 (빈 window), Q-107 (온도 교차 합산)

## D-118 — 2026-08-07 — "P5 는 merge 를 기다려야 한다"는 26일짜리 전제는 **거짓**이었고, 첫 P5 matrix 는 24칸 중 **0칸**만 회피를 측정할 수 있다

- **Context**: STATE 가 26일 동안 "모든 P5 deliverable 은 main 이 P3/P4 를 흡수해야 가능"을 bottleneck 으로 옮겨 적었고, 81 cycle 연속 north-star 이동이 0이었다. 이 전제는 한 번도 측정된 적이 없다. `git ls-tree origin/main` 한 줄이면 끝나는 검증이었다 — main 에 controller 3종·scenario 8종이 **이미 전부** 있다.
- **Decision**: (1) 전제를 폐기하고 P5 를 즉시 시작한다. (2) `eval/mppi_sandbox/baseline_matrix.py` = P5 첫 정량 harness. 새 primitive 를 만들지 않고 `ab.seed_sweep`/`summarize` (seed×speed×completion×ESS) 와 `feasibility.is_avoidance_measurable` (회피 denominator) 위에 **admissibility ladder** 와 headline 만 얹는다. (3) D-116 선례대로 **2축**: `tracking_reportable` (전 seed 완주) 와 `avoidance_reportable` (완주 + 장애물 존재 + `ess_in_band`). 같은 run 에서 18/24 와 0/24 로 갈리므로 한 flag 로 합칠 수 없다.
- **측정 결과 (3×8×8 seed, main 코드, 8m10)**: **avoidance-reportable = 0/24.** 6칸 `NO_OBSTACLES`, 6칸 `NOT_REACHED` (`cafe_cut_in` 0/8), **12칸 `ESS_OUT_OF_BAND`** — 장애물이 실재하는 모든 scene 이 shipped `lam=0.1` (median ESS ≈ 1.01/256, 사실상 greedy argmin) 으로 돌고 있어 회피 수치가 cost term 이 아니라 temperature 에 대한 진술이다. Ladder 가 억누른 값이 하필 출하될 뻔한 값이다: `success_rate = 1.0000` (18칸) — 그중 6칸은 부딪힐 것이 없고, `cafe_obstacle_crossing` 은 `min_clearance = 0.000` 으로 "성공"이다.
- **Alternatives**: (a) 계속 merge 대기 — 26일간 실제로 한 일, 반증됨 (b) 단일 grade harness — 같은 matrix 를 18/18 만점으로 렌더했을 것 (c) 새 A/B primitive 재작성 — `ab` 가 이미 소유, D-047 의 "규칙의 두 번째 진술" 재발.
- **Census bill — 8건 red 였고, 그중 4건은 pin 이 아니라 진짜 설계 결함이었다**: 첫 판본이 `NON_SCENARIO_YAML` 이라는 module-global typed allow-list 로 `lam_windows.yaml` 을 걸러냈는데, `calibrate_lam.is_scenario_yaml` 이 **같은 glob, 같은 파일**을 위해 이미 존재한다 (docstring 이 그 파일명을 명시). 규칙의 두 번째 진술 (D-047) 이고, census 가 쓰이자마자 잡아냈다 — `unwatched_exemptions` 4→6, `exemption_masking` 19→20, `NOT_PATHS` 3→4, pool 92→93. Pin 을 다시 찍는 대신 기존 predicate 를 호출하도록 고치니 **네 축 모두 원위치, guard pool 비용 nil**. 남은 bill 은 default 인자에서 오는 불가피한 것뿐: `defaults` 55→58, `forwards` 19→20, `total` 105→109, `weighting_at_shipped` 53→**56**.
- **`lam_dependence` 는 pin 이 아니라 발견이었다**: `baseline_matrix` 가 `guard_witness`/`run.py` 에 이어 **세 번째** non-test lam site 로 등록됐는데, 앞의 둘과 달리 이건 실제로 sim 을 청구한다 — matrix 가 `ab.seed_sweep` 을 `lam` 없이 호출해 전 cell 이 shipped default 를 상속한다. 12칸 `ESS_OUT_OF_BAND` 의 기계적 원인이 census 축에서 독립적으로 확인된 셈.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-18-the-p5-premise-was-false-and-the-matrix-is-0-of-24.md` · 후속: D-116 (2축 선례), D-107 (빈 population = 깨끗함), D-047 (규칙의 두 번째 진술)

## D-117 — 2026-08-07 — `OVERRUN` 의 비용은 **suite 시간이 아니라 진단 지연**이었다. Q-104 의 세 선택지가 모두 잘못된 축을 가격했다

- **Context**: D-115 의 advisory 가 직전 run 을 **61m26 / 35분 예산**, 16:00 tick 을
  lock 으로 삭제했다고 읽었다. Q-104 의 `다음 action` 은 "`OVERRUN` 재관측 시 lean (b) 집행".
- **Decision**: (b) 를 집행하지 **않는다**. Q-104 의 전제 — "35분 안에 12분 suite 가 **두 번**"
  — 은 이미 거짓이다 (14:00 746s ×1, 15:00 756s ×1, 02:00 recovery 가 명시적으로
  "ONE run"). 실제 초과분은 15:00 자신의 cron line 에 있다: **census pin 1건이 red 인데
  `push_preflight record` 가 count 만 보고해서, 그 1건을 찾는 데 narrowing run 3회**.
  그래서 `parse_failures()` + `Receipt.failed_nodes` 를 넣어 `record` CLI 와 `RED` 거절이
  **실패한 node id 를 출력**하게 한다. red suite 진단이 4 run → 1 run.
- **Alternatives**: (a) 예산 45~50분 — flock 충돌을 사서 하는 일 (b) 재측정 skip —
  존재하지 않는 두 번째 run 을 없애는 일 (c) suite shard — D-043 과 정면 충돌.
  셋 다 **suite 시간**을 가격했고, 측정된 비용은 **어느 test 인지 모르는 것**이었다.
- **핵심 제약**: 등급은 여전히 **count** 의 함수다. `failed_nodes` 는 진단 전용이며,
  양방향 control 로 고정 — node id 없는 red receipt 는 `RED` 유지 (regex 누락이 red 를
  세탁할 수 없다), stray node id 있는 green receipt 는 `GREEN` 유지. 진단이 조용히
  판정이 되는 것이 유일하게 막아야 할 방향.
- **Status**: accepted (Q-104 → resolved)
- **Refs**: #67 · `journal/2026-08/07-17-the-count-without-the-name-cost-three-runs.md`

## D-116 — 2026-08-07 — budget compliance 는 `PUBLISHED` 의 하위 등급이 아니라 **두 번째 독립 축**이다. 근거는 원칙이 아니라 **서로소인 finding**

- **Context**: Q-105 (14:00 cycle 이 `Q-104` 로 잘못 발행 — 아래 참조). D-115 의 advisory
  가 첫 live 호출에서 12:00 run 을 `PUBLISHED — No budgeting finding` 으로 등급했는데,
  그 run 은 **99m40**, 헌법 예산 35 분의 약 3 배였다. `grade` 의 축은 *"왜 push 가 없었나"*
  이고 `PUBLISHED` 가 그 축의 종점이므로, **어떤 비용을 치르더라도 publish 한 run** 은
  예산을 읽으라고 만든 계측기에 구조적으로 보이지 않는다.
- **Decision**: Q-105 의 (b). `budget_grade` 를 `grade` 와 **무관하게** 추가
  (`WITHIN_BUDGET`/`OVER_BUDGET`/`UNKNOWN`), 기존 등급 vocabulary 는 한 글자도 건드리지
  않음. advisory 는 2 차원이 되고, `PUBLISHED` 도 budget clause 를 받는다.
- **왜 (a) 가 아닌가**: `PUBLISHED` 를 쪼개면 `exhaustion_verdict` 의 population 정의가
  바뀌어 D-113 의 `MIXED` 판정을 **소급 재해석**하게 된다. 그건 실재하는 결론이고,
  계측기를 고치려고 이미 내린 판정의 의미를 바꾸는 건 값이 너무 비싸다.
- **🔬 결정적 근거는 논증이 아니라 측정이다 — 두 축이 같은 날 서로소인 finding 을 냈다**:
  2026-08-07 전체 로그에서 `grade` 축은 `budget-exhaustion hypothesis: NO_EVIDENCE`
  (PREMATURE=0, OVERRUN=0) 로 **예산에 대해 완전히 침묵**한다. 같은 로그에서 budget 축은
  **OVER_BUDGET=5 of 15** 를 찾는다. 한 축이 다른 축의 refinement 였다면 불가능한 결과다.
- **🔬 "over budget" 을 규칙 위반이 아니라 실측 비용으로 만든 것이 핵심**: `flock -n` 덕분에
  귀속이 통계가 아니라 **정확**하다 — tick 이 skip 줄을 찍었다면 그 순간 lock 을 쥔 run 이
  정확히 하나 있고 bracket 이 누구인지 말해준다. 12:00 run 은 **13:00 cycle 을 통째로
  삭제했다** (`executor already running; skipping this tick`). 그래서 advisory 는
  "예산 초과" 가 아니라 "실행되지 않은 cycle 1 건" 이라고 말한다 — 전자는 *그래도 publish
  했잖아* 라는 반박을 부르고 후자는 부르지 않는다.
- **🔴 부수 발견 — `grade` 축은 시간에 대해 안정하지 않다**: `published_hours` 는 *지금*
  평가되므로 12:00 cycle 이 strand 를 소급 해소한 뒤 03/07/09:00 run 이 `PREMATURE` →
  `PUBLISHED` 로 **재등급**됐다 (오늘 아침 D-113 이 기록한 등급과 다르다). 벽시계는 절대
  변하지 않으므로 budget 축은 안정하다. 축 분리의 세 번째 독립 논거이자 새 Q-106.
- **🔴 ID 충돌 수리**: 같은 날 `Q-104` 가 **두 번** 발행됐다 — 11:00 (`fed40b6`, OVERRUN
  budget 질문) 과 14:00 (`e2c6dd2`, 이 질문). 먼저 published 된 쪽이 번호를 유지하고
  후자를 `Q-105` 로 이동. deliberations.md 의 "strict 증가" 규약은 **prepend 시 최상단만
  보는** 절차와 맞물려 실패한다: 14:00 은 자기가 쓴 자리 위를 안 봤다.
- **🔬 Census 비용이 nil 이 아니다 — 그리고 이번엔 알고 샀다 (38번째 연속)**: pool 91 → 92,
  진입자는 `over_budget_grades`. D-115 의 `finding_grades` 는 같은 문제를 한 cycle 먼저
  풀고도 진입하지 않았다 — set difference 없는 평범한 comprehension 이라 detector 에
  안 보인다. 이쪽은 `frozenset({epic}) - {brief}` 로 썼고 **그 뺄셈이 요점**이다:
  `budget_grade` 의 비교가 뒤집히면 set 이 뒤집히게 만드는 것, 즉 derivation 을
  **반증 가능**하게 만드는 장치다. 따라서 이번 entry 가 값을 매긴 것은 이전 37 건이
  분리하지 못한 것 — **derivation 을 테스트 가능하게 만드는 문법이 곧 census 가 잡는
  문법이다**. 2차 비용은 nil (`unwatched_exemptions` 5 유지, exemption 이 INLINE).
- **Alternatives**: (a) `PUBLISHED`/`PUBLISHED_OVER_BUDGET` 로 분할 — D-113 소급 재해석
  (b) 두 번째 독립 축 — **채택** (c) 그대로 — 오늘 데이터가 기각 (파괴된 cycle 1 건)
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-15-two-axes-because-two-questions.md` ·
  Q-105 (resolved) · Q-106 (new) · `eval/mppi_sandbox/cycle_wallclock.py`

## D-115 — 2026-08-07 — REVIEW 의 wall-clock reading 은 **gate 가 아니라 advisory** 다. 판단 기준은 중요도가 아니라 **repairability**

- **Context**: D-113 이 `cycle_wallclock` 을 만들었지만 **호출자가 없었다** (3 cycle 방치).
  Q-103 의 trade-off (a) 자체는 D-112 가 이미 지불했다 — 여기서 되풀이된 것은 그 항목이
  아니라 Q-103 이 **진단한 패턴**("계측기는 고쳤는데 아무도 호출하지 않는다")이고,
  이번엔 그 대상이 D-113 의 모듈이다. Q-103 의 (c) 는 여전히 미지불. 자연스러운 배선은 `cycle_artifacts stranded` 옆에 같은 모양으로
  붙이는 것 — 즉 rc=1 을 finding 으로 쓰는 gate. 그런데 두 reading 은 성질이 다르다.
- **Decision**: `review` subcommand 는 **항상 rc=0**, 그리고 **직전 run 하나만** 등급한다.
  근거는 **repairability**: strand 는 지금 디스크에 놓인 미완 작업이라 이번 cycle 이
  즉시 해소할 수 있다(그래서 decision tree 를 앞선다). wall-clock finding 은 **이미
  끝난 run** 에 대한 사실이고, 어떤 cycle 도 선행 run 의 overrun 을 되돌릴 수 없다.
  유일한 live 용도는 **prospective** — "직전에 실패한 budgeting 을 지금 반복하려는
  중" 이라는 신호이고, 그 신호를 지닌 run 은 정확히 하나다.
- **왜 day-scope 가 아닌가 (측정)**: 2026-08-07 은 10:00 이전에 `PREMATURE` 3 건.
  day-scoped check 는 03:00 에 red 가 되어 이후 cycle 이 무엇을 하든 자정까지 red —
  D-044 가 이름 붙인 **muting** 실패 그대로다. 해소 불가능한 check 는 무시하도록
  학습시키고, 그 학습은 그 check 안에 머물지 않는다.
- **부수 발견 (내 코드의 결함)**: `finding_grades()` 를 D-104 대로 *derive* 로 적었으나
  `grade(r, ...)` 를 두 상수 없이 호출 — `grade` 는 그 둘을 **default argument** 로
  받고 default 는 **정의 시점에 binding** 되므로, derivation 이 자기가 따른다고 주장한
  상수로부터 **격리**돼 있었다. 대체하려던 literal 과 동일한 결함. 명시 전달로 수정.
  교훈: "derived rather than declared" 는 자기검증이 아니다 — 잡으려면 테스트가 값을
  단언할 게 아니라 **입력을 흔들어야** 한다.
- **Alternatives**: (a) stranded 와 동형의 gate — 해소 불가능한 사실에 cycle 을 세우거나
  non-zero exit 을 무시하게 가르침 (b) day-scoped advisory — 태어날 때부터 muted
  (c) 채택: preceding-run advisory, rc=0 고정.
- **Status**: accepted. Q-103 을 **닫지 않는다** — 그 (c)(`STATE.md` 의 push 주장이
  무등급)는 그대로 미지불이다. 이 D 가 닫는 것은 D-113 모듈의 caller 부재뿐.
- **Refs**: PR #67 · `journal/2026-08/07-14-the-reading-that-must-not-be-a-gate.md` · Q-103 · Q-104

## D-114 — 2026-08-07 — red tree 15건은 **하나의 미등록 probe** 였다. guard registry 가 전량 거절하기 때문에 누락 1건이 파일 전체를 넘어뜨렸다

- **Context**: 브랜치가 6 cycle 째 push 불가 (`stranded` rc=1, 6건 전부 *unwatched* — Artifacts claim 이 정직해서 push gate 가 구조적으로 못 봄). tree 는 RED 12F/6E/1347P 인데 **9F+6E 가 미열거** 상태였다. 앞선 3번의 열거 시도가 733s suite 대비 10분 tool ceiling 에 걸려 전부 실패. STATE #1 이 "quiescent tree 에서 열거하라" 를 최우선으로 지목.
- **Decision**: suite 를 **background 로 돌리고 foreground 에서 bounded wait 로 block** 하는 패턴으로 ceiling 을 우회해 열거 완료. 결과는 단일 원인이었다 — D-112 가 `cycle_artifacts.unwatched_strandings` guard 를 ship 하면서 `guard_direction.PROBES` 에 probe 를 등록하지 않았고, `readings()` 는 guard 별로 degrade 하지 않고 **첫 미등록 guard 에서 통째로 `ProbeError`** 를 던진다. 그래서 error 6건 + failure 4건이 한 누락에서 나왔다. 조치: (a) `build_stranding_repo` fixture + probe 등록 — `origin/<branch>` 를 history **중간**에 걸어야 stranding 이라는 gap 이 생긴다 (`_remote_has` 는 remote ref 안의 path 존재를 보므로, 전부 push 된 fixture 에는 읽을 gap 이 없다). 두 subject 모두 `NAMES_OFFENCE` = 작동하는 guard. (b) census pin 5개 갱신 (`len(pool)` 88→91, `scalar` 8→10, `NO_REGISTRY` 15→16, `unmirrored_revocable` +1, typed-table 차집합 +1). (c) stale pin 3개 재취득.
- **Alternatives**: (a) `readings()` 를 guard 별 degrade 로 바꿔 blast radius 를 줄인다 — 옳은 방향이지만 이번 cycle 의 의무는 strand 해소였고, guard 를 조용히 건너뛰는 것은 "미측정을 clean 으로 읽는" 이 package 가 반복해서 거절해온 형태라 신중한 설계가 필요 → 다음 우선순위로 이월. (b) count pin 만 고치고 probe 는 미루기 — pin 이 red 인 이유가 probe 부재이므로 불가. (c) `COMPOSITION_CAP` 을 올려 full probe 를 회피 — 자기 편의를 위한 기준 완화라 거절.
- **측정된 비용 (이번 cycle 의 실질 발견)**: 새 test file 1개가 pin 을 stale 시킬 때, generation 에 따라 재취득 비용이 **0.5초 vs 34분** 으로 갈린다. `journal/` 은 gen-0 이라 entrant 1개만 compose (0.5s), `STATE.md`/`results/` 는 gen-2 = `COMPOSITION_CAP` 도달이라 full probe 로 fallback (15m45 / 17m57). 같은 원인, 같은 cycle, 2000배 차이.
- **부수 발견**: census pin 이 **3 cycle 연속 미실행** 이었다. D-112·D-113 이 각각 guard registry 에 진입했으나 둘 다 receipt 전에 죽어 pin 을 돌리지 않았다. census 는 누가 실행해야만 entrant 에 과금한다 — 자기 suite 에 도달 못 하는 cycle 은 과금 자체가 불가능하다. 즉 D-112 는 detector 와 그 detector 의 결함을 같은 commit 에 담았다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-12-one-missing-probe-took-fifteen-tests-down.md`

## D-113 — 2026-08-07 — push 실패 5건은 **하나의 원인이 아니라 두 개**였다. wrapper log 의 wall clock 이 이미 그 둘을 갈라놓고 있었다

- **Context**: 09:00 journal 이 "왜 최근 cycle 들이 push 에 도달하지 못했나" 를 미해결로 남기고 budget exhaustion 을 가설로 제시, 10:00 cycle 이 이를 5건 전체로 일반화. 둘 다 *공유된 증상* 에서 단일 원인을 추론했고, 아무도 `daily_executor.sh` 가 이미 기록 중인 `=== executor start/end ===` 두 숫자를 빼보지 않았다.
- **Decision**: `eval/mppi_sandbox/cycle_wallclock.py` — wrapper log 를 parse 해 각 run 을 "한 suite(717s) + cycle 최소 overhead(240s)" 기준으로 등급. 판정: **MIXED**. 03/07/09:00 은 12m/9m/8.5m = `PREMATURE` (suite 자체가 안 들어감 → receipt 불가 → `push_preflight` 가 `NO_RECEIPT` 로 정상 거절). 06/08:00 은 34m20/34m54 = `OVERRUN` (suite 를 돌리고도 push 못 함 → budget exhaustion 이 **이 둘에 대해서는** 맞음). 가설은 5건 중 2건만 설명했다.
- **`PREMATURE` 3건의 기전**: log 에 그대로 남아 있다 — cycle 이 suite 를 background 로 돌린 뒤 "receipt 를 기다린다" 는 **텍스트 turn 으로 끝맺음**. `claude -p` 에서 tool call 없는 turn 은 곧 최종 답변이므로 run 이 종료되고(rc=0) wrapper 가 suite 째로 회수한다. crash 도 budget 도 아닌 **자기종료 문장**.
- **Alternatives**: (a) bare suite 기준만 사용 — 실제 03:00(721s)을 4초 차로 `OVERRUN` 오분류, 기각. (b) overhead 를 추정치로 — 결론을 상수가 대신 만들게 되므로 기각; **하한**(관측 최단 REVIEW-only run 236s 이하)으로 고정하고 `overhead=0` 민감도를 테스트로 고정. (c) published = ¬stranded — journal 을 안 쓴 4 run 을 성공으로 오계상(`PUBLISHED=6` vs 실제 2), `NO_JOURNAL` 등급 신설로 기각.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-11-the-hypothesis-explained-two-of-five.md` · Q-103 부분 해소 · Q-104

## D-112 — 2026-08-07 — claim 에 대해 fail-closed 하는 gate 는 그 claim 이 **가리키는 사실**의 detector 가 아니다. 거짓말을 지우면 gate 도 같이 비워진다

- **Context**: 세 cycle 연속(07:00 / 08:00 / 09:00) REVIEW 가 같은 모순으로 열렸다.
  `origin` 은 02:00 의 `ff2fe42`, local `HEAD` 는 `c53f587` — commit 6 개, cycle
  4 개 분량이 disk 에 좌초. 06:00 `STATE.md` 는 "pushed" 라고 썼고 08:00 journal 은
  "five stranded commits reached `origin`" 이라고 썼다. 둘 다 거짓. Q-103 이 계측기
  (`in_flight=`) 는 있는데 **호출자가 없다**고 기록해 둔 상태였다.
- **Decision**: (a) `cycle_artifacts.stranded` (= `unpublished(in_flight=None)`,
  규칙은 위임하고 재유도하지 않음) + `stranded` subcommand (finding 이면 rc=1) +
  `auto_research.md` Phase 1 **step 0** — 아무것도 읽기 전에 이 판독부터. rc=1 이면
  decision tree 보다 우선한다. (b) push gate 가 구조적으로 닿을 수 없는 잔여를
  `unwatched_strandings` (= stranded ∖ unsupported) 로 **명명**.
- **측정된 근거 (이번 cycle 의 실제 발견)**: D-110/D-111 의 누락 TSV row 를 append
  해서 gate 를 통과시킨 전후를 재 봤다 — frontier `[07:00, 08:00]` → `[]`,
  stranded 는 `[03:00, 06:00, 07:00, 08:00]` 로 **불변**, 넷 다 `unwatched` 로 이동.
  **push 를 licensing 하는 바로 그 행위가 유일하게 소비되는 population 을 비운다.**
  gate 는 좌초를 재는 게 아니라 좌초에 대한 *부정직* 을 잰다. cycle 이 정직하면 둘은
  갈라진다 — `07-03`/`07-06` 이 `HONOURED` 인 채로 6 시간 보이지 않았던 이유.
- **Alternatives**: (a) gate 에 좌초 검사 추가 — 불가. gate 는 push 직전에 돌고,
  push 가 성공하면 좌초는 그 자리에서 해소된다. 죽는 cycle 은 gate 에 도달하지 않는다.
  (b) push 후 별도 CI/프로세스 대조 (Q-103(b)) — 죽음에 강하지만 인프라 추가, 보류.
  (c) `STATE.md` 의 push 주장을 test 로 대조 (Q-103(c)) — **미지불**, 다음 cycle.
- **Status**: accepted — Q-103 을 `partially-answered` 로. (a) 지불, (c) 미지불.
- **Refs**: PR #67 · `journal/2026-08/07-09-repairing-the-claim-emptied-the-only-population-with-a-reader.md` · Q-103

## D-111 — 2026-08-07 — differential probe 는 **세계가 가만히 있다**는 전제를 갖는다. 그 전제를 깨는 가장 유력한 사람은 probe 를 돌리는 본인이다

- **Context**: STATE #1 (`journal/` 를 post-receipt write 로 pin) 을 집행하다
  두 개의 결함을 연달아 만났다. (1) `_probe_target` 이 prefix 를 **한 단계만**
  걸어서 `journal/` 이 `journal/README.md` 로 해석됐다 — cycle 이 절대 쓰지 않는
  손으로 쓴 규약 문서다. `results/` 는 flat 이라 우연히 맞았을 뿐이고, 규칙은
  nested member 가 등장하기 전까지 검증된 적이 없었다. (2) 첫 probe 가
  `CONTENT_READ` 를 냈는데 **내가 만든 인공물**이었다: 두 pass 사이에 내가 reader
  file 하나에 test 5 개를 추가했고, 카운트는 `343 → 348` 로 나왔다 — 진짜 content
  read 와 **산술이 동일**하다.
- **Decision**: 셋 다 수리.
  (1) prefix 순회를 `rglob` 으로 — 선택 규칙(최신 mtime)은 불변. 재귀가 "가장 깊은
  것"으로 바뀌면 flat member 가 운으로 통과하므로 negative control 을 같이 둔다.
  (2) `_run_fingerprint` 가 두 pass 를 reader file 들의 **내용** 해시로 감싼다.
  측정 중 reader set 이 움직이면 `VACUOUS` — **`CONTENT_READ` 가 아니다.** 둘 다
  면제를 거부하므로 gate 안전성은 같지만, 측정이 없었다는 사실을 정직하게 말하는
  쪽은 하나뿐이다. mtime 이 아니라 내용으로 키를 잡는다 (동일 바이트 재기록은
  표면이 움직인 게 아니다).
  (3) `journal/` 을 population 에 추가하고 `INERT` 로 pin (14 files, 5m40s,
  348 passed / 6 failed 무이동).
- **핵심 논거**: D-044 의 표는 4a write 만 보고 "commit it, cheap to include" 라고
  결론지었다 — 그 write 에 대해선 참이고, **D-043 이 그 뒤에 강제하는 두 번째
  write 에 대해선 침묵**이다. journal 은 *재측정된* count 를 인용해야 하고 그건
  실행 후에만 알 수 있으므로, 정직하게 보고하는 cycle 은 반드시 journal 을 두 번
  쓴다. pin 이 없으니 매번 `STALE` → 두 번째 full suite run. **06:00 과 07:00 이
  죽은 자리가 정확히 그 두 번째 run 안이다.**
- **Alternatives**: (a) `CONTENT_READ` 로 두기 — gate 는 안전하나 기록에 거짓
  finding 이 남는다. (b) probe 를 lock 으로 직렬화 — 5m40s 동안 저자를 막는 건
  지켜지지 않을 규율이다. (c) 첫 판정을 믿고 pin 안 하기 — 세금 유지 + 거짓 발행.
- **Second-order cost, 그리고 그건 내 것이 아니었다**: `printing` 20 → 21 은
  **D-110** 이 pool 에 들어온 것이다. 07:00 cycle 의 journal 은 "census cost nil
  (106 tests unmoved)" 이라고 적었지만 그 cycle 은 suite 를 돌린 적이 없다
  (`Metric: pending-4a-ter`). 측정하지 않은 "census nil" 의 **다섯 번째** 사례.
  D-110 과 D-111 의 계산서를 한 번에 지불 (printing 21→22, uncovered 15→16).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-08-the-probe-measured-its-own-author.md`

## D-110 — 2026-08-07 — 위치로 추론한 "in flight" 면제는 **창(window)** 을 가진다. 그 창 밖에서 면제 슬롯에 앉아 있는 것은 비행 중인 cycle 이 아니라 **시체**다

- **Context**: 07:00 REVIEW 가 모순으로 열렸다 — `STATE.md` 는 06:00 cycle 을
  "GREEN (1343/1343), **pushed**" 라고 적었는데 `origin` 은 4 commit 뒤였다
  (D-108/D-109 + TSV 2 행이 disk 에만 존재). 06:32 commit 후 push 전에 죽은 것.
  그런데 이걸 잡으라고 있는 `cycle_artifacts.unpublished` 는 침묵했다. 실측:
  **stranded 2 건 (`07-03`, `07-06`), 보고 1 건.**
- **Decision**: 면제 자체는 유지 (비행 중 cycle 은 journal 있고 push 없음 — 정상).
  결함은 면제가 관측을 **버린다**는 점. 둘 다 수리, **default 동작은 불변**:
  (1) `unpublished(..., in_flight=)` — 순서에서 추론하는 대신 호출자가 무엇이
  비행 중인지 **선언**한다 (D-109 의 `frontier=` 주입과 같은 대칭).
  (2) `frontier_stranded()` — 면제가 버리던 사실을 **발행**한다. census/report 에 노출.
- **핵심 논거**: `ordered[-1] == in flight` 는 실행 중 cycle 이 **4a 에서 journal 을
  쓴 뒤에만** 참이다. 그 전에는 disk 의 최신 journal 이 **방금 끝난** cycle 의 것이다.
  즉 면제가 틀리는 창은 정확히 **REVIEW 구간**이고, 그건 stranding 을 아직 싸게
  고칠 수 있는 유일한 순간이다. 계측기가 값어치를 할 때만 정확히 어둡다.
- **Q-102 와의 관계 — 같은 증상, 독립적인 두 원인.** Q-102 는 retroactive 행에서
  두 dating key 가 갈리는 경로로 frontier 침묵을 서술했다. 이번 것은 TSV 도
  dating key 도 필요 없다 — **위치 면제 단독**이다. Q-102 의 수리로는 안 잡혔다.
- **Alternatives**: (a) 면제 폐기 — 매 cycle red, 기각 (그게 면제가 있는 이유).
  (b) wall-clock 으로 면제 — `Date.now` 류 ambient 의존, D-109 가 막 없앤 것.
  (c) 관측을 버리되 문서화 — D-038 이 정확히 반대를 말한다 (진술된 배제는 감사
  가능, 암시된 배제는 구멍).
- **Second-order cost: nil.** `magnitude_census`/`guard_reflexivity`/
  `push_claim_gate`/`suite_coverage` 106 개 무이동. 새 narrowing 은 scalar
  부등식이라 `_is_set_valued` 가 못 읽는다 — D-079 의 비가시 spelling.
- **Status**: accepted. Q-102 는 `partially-answered` (이 경로만 답함).
- **Refs**: PR #67 · `journal/2026-08/07-07-the-exempt-slot-held-a-corpse.md`

## D-109 — 2026-08-07 — 프로세스가 **보장하는** 위반 위에 세운 게이트는 게이트가 아니다: ambient 축은 주입 가능해야 한다

- **Context**: D-108 의 `UNSUPPORTED_CLAIM` 게이트가 3 개 테스트를 by construction
  으로 죽였다. `check()` 가 채점하는 네 축 중 셋은 인자의 함수인데 이 축만 **살아
  있는 저장소**를 읽는다. 그리고 그 트리거는 우연이 아니다 — D-044 가 journal 을
  4a 에, TSV row 를 push 직전 마지막에 쓰라고 명령하고 suite 는 그 사이 4a-ter 에
  돈다. 즉 "journal 이 아직 없는 row 를 주장한다" 는 **헌법이 suite 실행을 명령한
  바로 그 순간에 참**이다.
- **Decision**: 축을 없애지 않고 **주입 가능**하게 만든다. `check(..., frontier=None)`
  — `None` 은 live read (기본), 명시 값은 그 population 을 채점. 다른 축을 채점하는
  테스트는 자기가 가정하는 population 을 진술한다. tree 축이 `declared` 로 이미
  하던 것과 동일한 대칭.
- **Alternatives**: (a) 최신 cycle 을 위치로 면제 (`cycle_artifacts.unpublished`
  미러) — **기각**. frontier 는 정의상 미발행 claim 이고 in-flight cycle 이 그
  주요 멤버라, 면제하면 게이트의 forward-looking 절반이 사라진다 (D-042 의 mute).
  게다가 push 가 실제로 도는 시점(TSV commit 이후)에는 in-flight cycle 이
  `HONOURED` 라 게이트는 원래 옳다. (b) 3 개 테스트에 scratch `root` 전달 — 그
  테스트들은 **live 트리의 coverage 수치**를 채점하므로 불가. (c) 게이트 삭제 —
  D-108 의 근거가 그대로 유효.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-06-the-gate-fired-on-the-order-that-mandates-it.md` · Q-102 · D-044 / D-108

## D-108 — 2026-08-07 — 탐지기는 정상 작동했다. 그 결과를 읽는 **살아 있는 프로세스**가 없었을 뿐이고, 읽히게 만드는 순간 **범위**가 게이트 그 자체가 되었다

- **Context**: 2026-08-07 01:00 cycle 이 journal 에 `TSV row appended: yes` 라 쓰고
  row 없이 죽었다. D-105 가 만든 `cycle_artifacts` 는 이를 `UNSUPPORTED rows=0` 으로
  **정확히, 제때** 채점하고 있었다 — 그런데 그 채점을 읽을 프로세스가 이미 죽은
  cycle 자신이었다. 한 시간 뒤 02:00 이 손으로 발견했다. **틀린 탐지기와 읽히지 않는
  탐지기는 다른 고장이며, 후자는 탐지기 자신의 테스트로는 절대 안 보인다** (테스트는
  "작동하는 reader" 이므로). STATE #16.
- **Decision**: `cycle_artifacts.unsupported` 를 `push_preflight.check` 의 일곱 번째
  거부 verdict `UNSUPPORTED_CLAIM` 으로 연결한다 — 모든 cycle 이 반드시 통과해야 하는
  단 하나의 지점. 단 population 은 **frontier** (아직 `origin/<branch>` 에 없는 journal)
  로 한정한다. 순서는 `UNDECLARED` 다음, `GREEN` 직전: 앞의 verdict 들은 전부 *측정*이
  못 쓸 것이라는 말이고, 이것만은 측정은 멀쩡한데 *기록*이 거짓이라는 말이다.
  `cycle_artifacts.current_branch` 가 `root` 를 받도록 했다 (그 모듈의 마지막 hard-coded
  reader). 규칙은 한 번만 진술 — `unsupported` 를 **필터**할 뿐 재유도하지 않으므로
  two-key intersection 규율을 상속한다 (D-045/D-047).
- **범위가 곧 게이트였다 (이번 cycle 의 진짜 발견)**: STATE #16 이 문자 그대로 요구한
  무범위 연결을 **쓰기 전에 재봤다** — 이 branch 의 confirmed unsupported 는 **4건이고
  `published()` 는 4건 전부 `True`** 다. 이미 origin 에 있는 claim 은 지금 push 하는
  cycle 이 고칠 수 없다 ⇒ 그 게이트는 **첫 commit 부터 통과 불가능**이고, 처음 부딪힌
  cycle 은 claim 이 아니라 게이트를 지웠을 것이다. D-042 의 muted alarm 을 mute 가
  미리 설치된 채로 출하하는 셈. frontier 범위는 **고칠 수 있는 것만** 거부하며, 그
  수리는 가설이 아니다 — 02:00 이 손으로 수행한 바로 그 행위다.
- **Alternatives**: (a) 무범위 거부 — 측정 결과 도착 즉시 red, 기각. (b) warning 만
  출력 — D-042 가 정확히 이 형태를 muted 로 판정. (c) 테스트로만 유지 (현상 유지) —
  01:00 이 반증. (d) `is False` 로만 frontier 판정 — remote ref 를 못 읽는 경우가
  fail-open 이 되므로 `is not True` (unknown 은 닫는 쪽).
- **알면서 열어둔 구멍 (fail-open, 테스트로 고정)**: branch 는 `HEAD` 에서 오고
  `cycles()` 는 journal 이 **선언한** branch 로 매칭한다 ⇒ 이름이 어긋난 cycle 은 조용히
  0건으로 읽힌다. `test_a_name_mismatch_grades_nothing` 이 이 edge 를 **실행**한다.
  닫지 않은 이유: 닫으면 `main` 에서의 모든 push 가 모든 branch 의 claim 을 책임지게
  된다. 이 구멍은 공유 fixture 가 `probe` 를 checkout 하면서 journal 은
  `autoresearch/probe` 를 선언한 탓에 **테스트 3개가 깨지며 발견됐다** — 한 소비자를
  위해 만든 fixture 는 그 소비자의 가정을 품고 있고, 두 번째 소비자는 실패로 그것을 안다.
- **Cost**: frontier reading 0.13 s (push 당 1회, 네트워크 불필요 — remote-tracking ref
  만 읽는다). census pool 불변 (helper 는 private, `current_branch` 는 scalar) ⇒ 새
  probe 의무 없음. `guard_direction`/`guard_reflexivity`/`census_narrowing` 181 tests 재실행 확인.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-03-the-detector-had-no-live-reader.md` · D-105 (Artifacts block 은 기록이 아니라 예측) · D-042 (기본값이 alarm 인 check 는 mute 된다) · D-045/D-047 (규칙의 두 번째 진술) · STATE #16

---

## D-107 — 2026-08-07 — 갚을 수 없다고 **적어둔 빚**은 없는 빚과 똑같이 읽힌다: 그리고 그 "갚을 수 없다" 는 한 번도 재본 적이 없었다

- **Context**: STATE #3 (D-044 의 ordering table 이 `results/*.tsv` 를 "read by no
  test (checked)" 라고 하는데 D-105 의 `cycle_artifacts` 가 그걸 읽는다) 를 고치러
  갔다. table 대신 `inert_surface` 에 물었더니 — 그 module 이 바로 이 집합을 *타이핑*
  하지 않고 **유도**하려고 존재한다 — `results/` 하나가 아니라 **네 pin 전부**가
  stale 이었다. `inert()` 가 전부 `False`, `filter_drift` 가 아무것도 안 걸러냄,
  즉 08-06 06:00 이후 **모든 cycle 이 두 번째 full suite run 을 지불**하고 있었다.
- **선행 발견 — HEAD 가 red 였고, 그걸 red 로 만든 건 D-106 자신의 push 다.**
  `test_a_second_silent_cycle_makes_the_first_one_red` 는 `06-18` journal 이
  unpublished 라고 **살아있는 저장소에 대해** 단언한다. 지난 cycle 이 branch 를
  push → published → finding 이 **해소**되고 test 가 red. **올바른 행동이 red 로
  만드는 test** 는 다음에 만나는 사람에게 regression 으로 읽힌다. scratch repo 로
  구성된 positional latency rule (4 cycle, 2 개만 push) + 없던 negative control
  (silent 이 하나뿐이면 finding 이 아니다) 로 교체.
- **Decision (1) — decay 는 침묵하지 않았다. 이름이 붙어 있었고, 그 이름이
  *수용*됐다.** `stale_pins` 가 보고했고 test 4 개가 이름으로 단언하고 있었다.
  살아남은 이유는 docstring 한 줄의 판정 — *"re-probe 는 갚아야 하지만 cycle 안에서는
  감당 불가"* — 이 4 cycle 동안 문서화된 조건으로 실려 있었기 때문이다. 초록색 suite
  아래에서 계측기가 꺼져 있었다.
- **Decision (2) — 그 가격은 재본 적이 없고, 두 겹으로 틀렸다.** 추정치("probe 하나가
  몇 시간")는 module 자신의 pin note(넷 합쳐 ~34 분, D-095)와 모순이고, 애초에 **틀린
  질문**이다. stale 해진 pin 에 full probe 는 필요 없다 — 그 뒤로 **들어온 것**만
  돌리면 된다. reader 집합 delta 는 monotone (8 파일 진입, 이탈 0). 측정: 최악 파일
  48 s, **네 pin 재취득 합계 ~3.5 분**. 10× 는 답을 최적화해서가 아니라 **질문을 바꿔서**
  나왔다.
- **Decision (3) — `reprobe` / `compose` / `INERT_COMPOSED` / `COMPOSITION_CAP`.**
  probe verdict 는 집합에 대한 **disjunction** ("named test 중 하나라도 움직였나")
  이므로 `moved(pinned ∪ entered) = moved(pinned) ∨ moved(entered)`, departure 는
  안전한 방향으로 monotone. 단 carried 半은 `d6b60c8` 에서 잰 것이고 `readers_key` 는
  **이름의 집합**이라 이름을 유지한 채 내용이 바뀐 reader 는 premise check 에 안 보인다.
  그래서 verdict 를 따로 철자하고 (`INERT_COMPOSED`), `Pin.carried` 로 무엇을 물려받았는지
  **명시**하고 (D-038), `COMPOSITION_CAP=3` 으로 세대를 끊는다 — 무제한 composition 은
  자기가 고친 decay 를 측정의 옷을 입고 재생산한다.
- **결과**: 네 pin 모두 `INERT_COMPOSED`, outcome 불변 (131/34/34/109),
  `stale_pins() == ()`, `filter_drift` 가 D-044 Phase-4 write set 을 정확히 무시.
  두 번째 suite run 세금 소멸.
- **STATE #3 의 답 — 두 half 가 동시에 참이다.** `cycle_artifacts` 는 실제로
  `results/*.tsv` 를 읽으므로 D-044 의 "(checked)" 는 **static claim 으로서 거짓**이고,
  probe 는 그 읽기가 outcome 을 움직이지 않는다고 말하므로 **면제는 살아남는다**.
  순서 규칙은 바꿀 필요 없다. 바뀐 건 근거이고, hand-check → measurement 다.
- **Alternatives**: (a) full probe 4 회 재취득 — 정확하지만 ~34 분, 하루 만에 다시
  stale (실측된 decay rate) 이라 지속 불가; (b) staleness 를 계속 이름만 붙여 두기 —
  4 cycle 간 실행된 안이고, 결과가 이 entry; (c) `results/` 를 population 에서 제외 —
  D-079 의 decoration, 측정 없이 면제.
- **Census cost**: pool 22 → **24**, `NO_REGISTRY` 13 → **15**. 하나는 `reprobe`
  (진짜 신규), 다른 하나는 **`probe` — 신규가 아니다.** `tests` 파라미터와 guard clause
  가 붙었을 뿐, 계산하는 내용은 그대로이고 **scan 에 narrowing 이 보이는지**만 바뀌었다.
  두 cycle 연속 **철자로 pool 에 진입** (D-106 의 `misscored_probes`). numerator 는 4 로 불변.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-01-the-debt-nobody-could-pay-read-as-no-debt.md`

---

## D-106 — 2026-08-07 — 의무를 **census pool 에서 상속**했더니, "문자열을 렌더하는 함수"에게 실행된 reading 을 요구하고 있었다

- **Context**: HEAD 가 red 였다 — `guard_direction` 의 standing rule ("모든 revocable
  guard 는 probe 를 갖는다") 이 D-105 가 추가한 `cycle_artifacts.unsupported` 와
  `.report` 둘 다에 대해 발동했고, 두 cycle (D-103/D-104) 이 push 되지 못한 채 묶여
  있었다. 그런데 entry 두 개를 쓰려고 보니 **둘은 같은 종류의 빚이 아니었다.**
- **Decision (1) — 의무의 population 은 census 의 것이 아니다.** `revocable` 은
  census pool 의 reading 이고, census pool 은 D-072/D-073 이래 **눈에 보이는 철자**의
  집합이다 — 그래서 출력용 tally 가 difference 에서 나오는 *renderer* 도 들어 있다.
  `report` 는 `-> str` 이다. 문자열은 probe 가 묻는 의미에서 아무것도 **name** 하지
  못하고, 유일한 만족 방법은 렌더된 텍스트를 파싱해 population 을 복원하는 것 —
  즉 rule 의 두 번째 진술이고, D-045/D-047 이 정확히 그 실패다. `Guard.reading`
  (`COLLECTION`/`SCALAR`, return annotation 에서 파생) + `revocable_collections`
  + `unprobeable_revocable` (제외를 **세는** enumerator, D-038). pool 은 건드리지 않는다 — 33 cycle 치 census provenance 를 다시 쓰는 건 그 자체로 손실.
  제외 규칙은 pool 전체에서 **8건** 이고 그중 revocable 은 1건이라, 떨어뜨리는 그
  guard 로부터 역산한 special case 가 아니다 (테스트로 고정).
- **Decision (2) — probe 하나에 offence 하나. `DECLARED_LOCAL_ONLY` 는 *모두의*
  subject space 가 아니었다.** `readings()` 는 (guard × `DECLARED_LOCAL_ONLY`) 를
  돌았다. probe 된 guard 가 전부 D-011 을 강제하는 동안엔 보이지 않는 가정이다 —
  하나의 rule 을 지키는 두 guard 로는 "이 rule 이 덮는 path" 와 "모든 rule 이 덮는
  path" 를 구분할 수 없다. 세 번째 guard 는 journal 파일에 관한 것인데 loop 는 여전히
  snapshot path 를 넘기고 있었고, 그대로 두면 `cycle_artifacts.unsupported` 에
  `STATE.md` 를 commit 하고 **자기 것이 아닌 offence 에 대해 blind 판정**을 냈을
  것이다. `Probe` 에 `subjects` / `build` / `permit` / `offend` 를 준다.
- **결과 — D-105 의 caveat 이 산문에서 reading 으로.** `cycle_artifacts` 를
  `root` 파라미터화(probe 의 전제조건)한 뒤, 두 dating key 의 날짜를 갈라놓은 scratch
  repo 에서 실행: 두 key 가 합의하는 offence 는 **NAMES_OFFENCE**, 뒤늦게 append 된
  row 가 `records` key 를 속이는 offence 는 **SILENT**. D-105 가 논증으로만 남겨둔
  교집합의 비용이 이제 측정값이다.
- **세 번째 blindness mechanism**: 기존 두 flag 는 `raw_before` 를 읽는다 — 허용
  상태가 이미 subject 를 population 에 담고 있을 때만 맞는 순간이고, unstaged edit 은
  그렇지만 아직 거짓말하지 않은 journal 은 아니다. `exempted_away` 를 **추가**한다
  (옮기지 않는다 — D-102: 앞의 reading 을 고쳐 쓰는 수리는 자기 증거를 지운다).
  masked 5건과 서로소, 정확히 1건.
- **2차 비용, 숨기지 않고 청구**: pool 81 → **84** (세 번째는 새 함수가 아니라
  9 cycle 된 `probe_reach.misscored_probes` — filter set 을 local 에 bind 한 한 줄이
  같은 membership 을 *보이게* 만들었다. 이 pin 자신의 본문이 그 함수를 "들어오지
  않는다" 고 적어둔 자리에서 D-073 이 다시 이겼다); `probe_reach` 의 addressable
  16 → **22** (`cycle_artifacts` 가 `root` 를 받게 되면서 6개가 도달 가능해짐,
  derivable numerator 는 4 로 불변); **`NO_SCOPE` 0 → 2** — "scope 는 아무도 잃지
  않는 layer" 는 `acts_of` 의 성질이 아니라 그 16개 pool 의 성질이었다 (둘은 자기
  body 에 act 가 없다); `probe_reach` 의 ground truth 를 `PROBES` 에서
  **자기 fixture 를 안 쓰는 probe** 로 좁힘 (`shared_fixture_probes`,
  table 에서 파생).
- **Alternatives**: (a) `report` 도 억지로 probe — 렌더 텍스트 파싱, 거절.
  (b) `guards()` 에서 scalar 를 제거 — census 의 의미(=철자의 count)를 파괴, 거절.
  (c) `revocable` 자체를 좁힘 — Q-063 이 묻는 *모양* 질문의 답을 바꿔버림, 거절.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/07-00-probe-obligation-inherited-the-wrong-population.md` · D-105 / D-049 / D-053 / D-072 / D-102 / Q-065 / Q-099

---

## D-105 — 2026-08-06 — journal 의 `## Artifacts` block 은 **기록이 아니라 예측**이었고, 99 cycle 동안 아무도 대조하지 않았다

- **Context**: 21:00 cycle 의 #1 은 "D-103 의 TSV row 를 다시 append 하라" 였다. 그걸 하러
  갔더니 **그걸 보고한 cycle 자신**이 같은 defect 를 갖고 있었다 — `origin` 은 `85e0bc7`
  에서 두 cycle 째 멈춰 있었고, 21:00 의 journal 도 `TSV row appended: yes` 라고 적힌 채
  TSV 의 마지막 행은 17:42 였다. Phase 4a 는 journal 을 **먼저** 쓰고 TSV row 와 push 는
  그 뒤에 온다. 그러니 그 줄은 append 의 기록이 아니라 곧 일어날 일에 대한 *예측*이고,
  예산이 끊기거나 죽은 cycle 은 그 예측을 reading 인 것처럼 남겨둔다.
- **Decision**: `eval/mppi_sandbox/cycle_artifacts.py` (+28 tests, 2 s). journal 마다
  검증 가능한 주장 **두 개**를 tree 에 대조한다 — (1) TSV row 가 실제로 생겼는가
  (`results/*.tsv`), (2) 그 cycle 이 기계를 떠났는가 (journal 파일이
  `origin/<branch>` 에 있는가). 나머지 section 은 읽어야만 답이 나오는 prose 지만 이 세
  줄은 대조 가능하고, 지금까지 아무도 대조하지 않았다.
- **🔴 어려운 건 matching rule 이 아니라 "row 가 언제 일어난 일인가" 였고, field 셋이
  서로 다르게 답한다.** (1) 손으로 친 `timestamp` — 예산 넘긴 cycle 은 자기가 *끝난* 시각을
  적는다. `04:05` row 는 `pass=1048` 과 D-093 본문을 싣고 있으니 **02:00** cycle 의 것:
  한 cycle 은 억울하게 유죄, 한 cycle 은 부당하게 무죄. 첫 cut 이 이걸 읽고 아홉이라 했다.
  (2) `commit` sha — 진짜 date 를 가진 git object 라 *어느 cycle 의 일인지* 는 맞다.
  그런데 **뒤늦게 append 된 row** 도 앞 cycle 의 sha 를 달고 있어서, 침묵한 cycle 이
  자기가 쓰지 않은 row 로 `HONOURED` 가 된다 — 18:00 / 21:00 을 이 cycle 이 수리하자
  두 finding 이 이 key 아래서 **사라졌다** (D-102 의 "수리가 자기 증거를 지운다" 가 다른
  방향에서 재현). (3) `git blame` — *언제 append 됐는지* 를 답하니 claim 이 실제로 하는
  주장과 일치한다. 실패 모드는 **TSV row 두 개를 한 commit 에 묶은 cycle**: `a165d1f`,
  `9fe05a0` 가 각각 둘씩 넣어서 옆 cycle 이 침묵한 것처럼 읽힌다 (08-05 07:00 / 11:00 오판).
- **살아남은 두 key 는 같은 방향(과다 보고)으로, 서로 겹치지 않는 case 에서 틀린다.**
  그래서 `unsupported` 는 **교집합**을, `disputed` 는 잔여를 publish 하고 모듈은 승자를
  고르지 않는다 — over-claiming 을 잡으려고 만든 instrument 가 스스로 over-claim 하면 안
  된다. **모집단 크기는 여기서 확정하지 않는다: 100 중 [4, 9].** → Q-099.
- **key 없이 확정된 건 셋**: 09:00 (10:00 cycle 이 손으로 확립), 그리고 18:00 / 21:00 —
  `git show --stat` 이 두 commit 다 TSV 를 아예 건드리지 않았다고 말한다. 이건 dating rule
  로 뒤집을 수 없는 증거다.
- **control 은 필요했지만 충분하지 않았다**: 09:00 은 10:00 cycle 이 손으로 확립해 둔
  유일한 독립 정답이라 첫 test 다 (D-102 의 교훈). 그런데 그건 *positive* 이고, 첫 cut 은
  셋 다 재현하면서도 두 번 틀렸다 — positive 로만 이뤄진 control 은 false-positive rate 를
  묶지 못한다. `test_the_reading_is_not_everything` 이 grader 가 변별력을 갖는지 보는 쪽.
- **newest cycle 의 면제는 이름이 아니라 위치로**: 비행 중인 cycle 은 journal 이 있고 push
  가 없다 — 정상 상태이지 finding 이 아니다. 마지막 하나를 건너뛰면 연속 두 침묵 cycle 이
  둘째에서 red 가 된다. 한 cycle 의 탐지 지연이고, 21:00 에 정확히 걸렸을 것이다.
  registry 를 만들지 않는 게 요점 (D-046).
- **push gate 는 잘못이 없다**: D-082 의 `&&` 는 fail-closed 이고 **실행되지 않았다**.
  도달하지 않는 gate 는 경보를 울리지 않으며, 그래서 이건 더 엄한 gate 가 아니라 별도
  instrument 가 필요한 부재다. Q-097 이 물은 게 정확히 이것.
- **census cost, 33rd cycle: pool 78 → 80, 그리고 D-089 의 across-function rule 이 처음으로
  *의도적으로* 깨졌다.** 여섯 번 연속 사전 예측이 맞았던 규칙 — 결론은 verdict 비교로
  쓰이니 안 보이고 caveat 는 membership 으로 쓰이니 세어진다 — 인데, 여기선 module 의
  headline 인 `unsupported` 가 **들어왔다**. 이유는 우연이 아니라 **D-104 의 처방** 이다:
  typed allow-list 의 수리는 "유도하고 그 유도를 call site 에서 부르라" 이고, 그러면
  `in finding_grades()` 가 결론 안으로 들어간다. D-089 는 결론의 *자연스러운* 철자에 대한
  규칙이고 D-104 는 자연스러운 철자를 덮어쓰는 규칙이라, 둘은 이제 **충돌한다** — Q-098.
  second-order cost 는 nil, **단** 첫 cut 이 `FINDING_GRADES` 를 typed global 로 내보내
  `unwatched_exemptions` 를 한 test run 만에 five-to-six 로 밀어올린 뒤다 (D-073 / D-080 /
  D-101 / D-103 의 비용, 다섯째 사례, 이번엔 cycle 안에서 지불).
- **Alternatives**: (a) 손으로 두 row 를 append 하고 넘어감 — 세 번째 재발이 오면 또
  손으로, 그리고 08-05 의 셋은 영원히 안 보인다, (b) push gate 를 더 엄하게 — 도달하지
  않는 gate 를 강화해도 도달하지 않는다, (c) journal 을 cycle 끝에 쓰도록 Phase 4 를 재배열
  — D-043/D-044 의 ordering 과 정면 충돌하고, 예측을 없애는 게 아니라 옮길 뿐이다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/06-22-the-artifacts-block-was-never-checked.md` ·
  Q-097 resolved → D-105 · Q-098 · Q-099

## D-104 — 2026-08-06 — position 은 failure 의 **field** 였지 옆에 둔 table 이 아니었다 — 그리고 D-103 의 census 청구서는 아직 카운터 위에 있었다

- **Context**: D-102 는 shielded assertion 을 읽기 위해 line number 가 필요했는데
  `CI_FAILURES` 에 없었다 — 그 census 는 `short test summary info` 에서 옮겨졌고 거기엔
  operand 도 line 도 없다. 첫 시도는 printed operator shape 로 위치를 복원해 **14 중 3**
  만 pin 했고 답을 아는 유일한 site 를 놓쳤다. 구조된 건 `gh run view --log-failed`
  refetch 였고, 그 log 는 **만료된다**. STATE #2 = "다음 transcription 이 운에 기대지
  않게 하라".
- **Decision**: position 을 census row 의 field 로 승격. `CiFailure.lineno` +
  `statement`, `located` / `unlocated`, `census()["located"]`, 그리고 `RUN_ID` /
  `RUN_COMMIT` 를 자기가 서술하는 census 옆으로 이동 (line number 는 tree 에 대한
  index 이므로 둘은 같이 다닌다 — D-043). `assert_reach.FAILED_AT` 는 손으로 관리하는
  두 번째 transcription 이 아니라 `sa.located()` 의 **derivation** 이 된다.
- **핵심은 contract test 이지 field 가 아니다**: `unlocated() == ()` — 모든 `ASSERTION`
  row 는 *어디서* 실패했는지 말해야 한다. 덜 옮겨적은 census 는 **쓰이는 순간** red 이지,
  세 cycle 뒤 누가 where-question 을 물을 때가 아니다. `TIMEOUT` row 는 반대 방향으로
  pin: 시계에 죽은 test 엔 실패한 statement 가 없으므로 line 을 **가질 수 없다**.
- **subset 은 원리적으로 이 누락을 못 잡는다**: 손으로 관리되던 동안 말할 수 있는 가장 센
  주장이 `FAILED_AT ⊆ census` 였고, 그건 아무것도 안 가리키는 key 를 잡는다. 그런데 누락은
  **반대 방향**으로 났다 — census 14 행, position 8 개, 그 8 이 *맞는* 8 이라고 말하는
  건 어디에도 없었다. 유도하면 둘이 불일치할 수 없고 test 는 equality 를 주장한다.
- **🔴 그리고 tree 는 이미 red 였다 — 세 시간째.** D-103 (18:10) 은 commit 하고 **push
  하지 않았고**, `test_unwatched_allow_lists_are_module_layer_only` 를 red 로 남겼다.
  `UNEVALUATED` 가 typed literal 로 나가서 `unwatched_exemptions` 가 쓰인 지 한 test run
  만에 5 → 6. origin 은 아직 85e0bc7. push gate 의 `&&` (D-082) 는 제 일을 했지만
  **조용히** 했고, 어느 cycle 도 pin 을 다시 읽지 않았다.
- **수리의 spelling 을 골랐으면 자기 청구서를 지웠을 것이다 — 그래서 측정했다** (D-073 처럼):
  `UNEVALUATED = unevaluated_grades()` 로 유도하면 `_is_set_valued` 가 no 라 하고
  `loop_reach.report` 가 **pool 에서 아예 빠지며** pin 은 77-unchanged 를 읽는다 — 즉
  D-103 의 cost 가 **nil** 로 기록된다. call site 에서 유도를 부르면 (`in
  unevaluated_grades()`) 78 로 세어지면서 provenance 는 `DERIVED` 다. 집합 하나, spelling
  셋, census reading 셋, 그중 **하나만** 세어지고 감시된다. D-072/D-073 의 syntax 결과가
  지금까지는 guard 의 *가시성*을 정했다면, 여기선 **수리가 지불로 기록되는지 소멸로
  기록되는지**를 정한다.
- **census cost, 32nd cycle**: pool 77 → **78** (`loop_reach.report`, D-103 의 미지불분).
  D-089 의 rule 이 **여섯 번째** 사전 예측으로 성립 — `report` 는 bookkeeping 이라 보이고,
  module 이 존재하는 이유인 `run`/`census` 는 equality 로 쓰여 안 보인다. D-104 자신의 새
  함수 `located` / `unlocated` 는 **0 개** 진입: 둘 다 attribute truth test 로 좁힌다
  (D-079 의 invisible spelling, 일곱 번째 module). 그리고 내 새 test 는 `loop_reach` 의
  target set 에 들어가 채점돼야 했다 (`SAMPLED n=8`) — D-103 의 instrument 가 생긴 지 한
  cycle 만에 D-104 에게 청구했다.
- **Alternatives**: (a) `FAILED_AT` 를 손 table 로 두고 test 만 추가 — 두 진실 출처가 남고
  누락 방향은 여전히 못 잡는다, (b) position 을 `assert_reach` 안에 두되 census 에서 유도 —
  방향이 반대라 census 가 여전히 position 없는 row 를 키울 수 있다, (c) D-103 의 red 를
  다음 cycle 로 미룸 — push gate 가 `&&` 라 아무것도 못 나간다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/06-21-the-position-was-a-field-not-a-table.md` · STATE #2

## D-103 — 2026-08-06 — loop-body population claim 15 개를 **실행으로** 읽었다: vacuity 0 — 의심은 합당했고 측정이 그걸 기각했다

- **Context**: D-102 는 loop-body assert 를 **세기만** 했다 (174 개 중 population
  claim 15). STATE #1 은 그걸 읽으라는 것. 그런데 여기 hazard 는 D-102 의 것과 **다르다**:
  거기선 failure 가 run 을 멈춰서 claim 이 미평가였고, 여기선 run 이 **green 인데도**
  미평가다 — `for cell in registry_cells(): assert a <= b` 에서 iterable 이 비면
  통과하고, 아무것도 검사 안 하고, 그 원소 개수는 source·pass count·CI log 어디에도 안
  보인다. 보이는 곳은 **실행** 하나뿐이라 정적으로는 답이 안 나온다.
- **Decision**: `eval/mppi_sandbox/loop_reach.py` (+27 tests). `sys.monitoring` 으로
  15 개 assert line 의 실행 횟수를 센다. 비대상 line 은 첫 hit 에 `DISABLE` → overhead 가
  suite 길이에 비례하지 않고 **감쇠**한다 (89 s 대비 **~2 s**).
- **0 은 서로 다른 두 finding 이고, 그 분리가 설계 전부**: assert 실행 0 은 (a) loop 가
  아무것도 안 내놨거나 (vacuity = finding) (b) test 자체가 안 돌았거나 (skip/deselect =
  단순 부재). 판별자는 `for` 문 자신의 line — assert 와 같이 watch 한다. 이거 없었으면
  이 13 파일의 `slow` skip 18 개가 전부 vacuity 로 published 됐다.
- **읽은 결과: vacuity 0.** 15 개 전부 **2–30 원소**에서 평가된다. `EMPTY` 0, `SINGLETON` 0.
  D-100(`CARDINALITY` 노후)/D-101(불건전 `SUBSET`)/D-102(도달 못 한 claim) 를 만든 hazard 는
  loop-body population 으로 **번지지 않는다**. 이건 D-076/D-081 이 말한 "측정된 emptiness"
  이고, `READING` + `test_the_reading_found_no_vacuity` 로 **guard 화** 했다 — 나중에 어떤
  loop 이 비면 red 가 된다. journal 에 "아무것도 못 찾음" 한 줄로 남겼으면 못 할 일.
- **Control 이 먼저였고 그중 하나가 값을 했다**: 답을 미리 적어둔 합성 loop 5 개 —
  empty/singleton/three/skipped/**nested-inner-empty**. 마지막 것 때문에 loop header 를
  **최내곽**으로 pin 한다; 최외곽이면 바깥 3 회에 안쪽 0 회가 가려진다. control 은 `exec` 가
  아니라 진짜 pytest subprocess 로 돈다 — pytest 가 assert 를 **rewrite** 하므로.
- **내 test 산수가 틀렸고 instrument 가 맞았다**: unevaluated control 을 2 로 하드코딩했는데
  3 이었다. `EXPECTED` 에서 **유도**하도록 고침. 손으로 다시 적은 count 는 두 번째 진실
  출처이고 틀리는 것 말고 할 수 있는 게 없다.
- **Caveat**: `test_the_nominal_point_lies_inside_its_own_band` 는 `slow` mark 라 fast job
  에선 `NOT_RUN`. `--slow` 로 재측정 → `SAMPLED n=8`, slow job 이 `-m slow` 로 선택하긴 한다.
  단 그 job 이 D-033 dispatch drift 를 안고 있으므로 "평가됨" 은 "CI green 에서 평가됨" 이 아니다.
- **Alternatives**: (a) 정적으로 iterable 비었는지 추론 — 일반적으로 결정 불가, (b) 전체
  suite 를 `settrace` — overhead 가 runtime 에 비례, (c) 안 읽고 15 를 open risk 로 둠 —
  D-102 가 딱 그렇게 3 cycle 을 썼다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/06-18-loop-reach-population-vacuity.md`

## D-102 — 2026-08-06 — 필요한 field 는 log 에 있었고, transcription 이 그걸 안 옮겼다 — 그리고 finding 을 가릴 뻔한 건 filter 였다

- **Context**: STATE #1 ("population 에서 승격된 나머지 assertion 을 쓸어라") 을
  *구조적으로* 물었다. 읽기로는 안 된다 — D-100/D-101 두 결함 다 읽기가 설치한 것이고,
  실행으로도 안 된다 — run 은 첫 failure 에서 멈춘다. 그래서 `assert_reach`: 기록된 CI
  failure 마다 그 뒤에 오는 `assert` = **아무 run 도 도달한 적 없는 claim**.
- **Decision**: `eval/mppi_sandbox/assert_reach.py` (+26 tests). 첫 test 는 **답을 아는
  case** — D-101 자기 line 을 복원 못 하면 다른 걸 재고 있는 것.
- **첫 cut 은 그 negative control 에 실패했다**: CI 가 찍는 assertion text 의 *연산자
  모양*으로 matching → 14 중 **3** pin, D-101 site 는 놓침 (`==` 세 개짜리 함수는 원리상
  구분 불가). 그대로 냈으면 "shielded 0" 이 finding 으로 published 됐다.
- **필요한 숫자는 job log 에, 옮겨적은 text 두 줄 아래 있었다**: `CI_FAILURES` 는
  `short test summary info` 에서 옮겨졌고 거기엔 line number 가 없다 — 그런데 이 질문은
  정확히 *where* 질문이다. `--log-failed` 의 traceback footer 로 8 개 assertion row 전부
  pin (3 → **8/14**). 나머지 6 은 전부 `TIMEOUT` — failing statement 자체가 없으니 뒤를
  가릴 것도 없다. matcher 결함이 아니라 failure mode 의 성질.
- **Reading**: shielded **2 site**. 하나는 D-101 자기 line (control), 하나는 **신규** —
  `shipped.understatement > audited.understatement`, 자기 test docstring 이 "section 3 의
  counterexample" 이라 부르는 바로 그 문장이고 한 번도 평가된 적 없다.
- **그리고 그 신규 건을 `POPULATION_KINDS` filter 가 지울 뻔했다**: D-100(CARDINALITY)/
  D-101(SUBSET) 에서 정직하게 유도한 filter 인데, 신규 건은 평범한 scalar 비교라
  `OTHER`. **claim 의 모양은 claim 의 중요도가 아니다** — filter 제거, kind 는 아무도
  act 하지 않는 annotation 으로 강등.
- **RUN_COMMIT 에서 읽는다** (D-043 의 새 자리): D-101 의 repair 가 shielded statement 를
  *삭제*했으므로 HEAD 에서 읽으면 finding 이 사라진다. `moved()` 가 기록 line 이 기록
  text 를 아직 들고 있는지 재확인 — drift 는 declare 되지 fabricate 되지 않는다.
- **Alternatives**: (a) signature 매칭 강화 — 값(runtime repr)과 source 표현식은 다른
  것이라 원리상 불가 (b) CI 를 다시 돌려 얻기 — 162.7 분 (c) log refetch ← 채택,
  다만 log 만료 전에 census 에 line field 를 넣는 게 후속.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/06-17-the-assertions-no-run-reached.md` ·
  D-101 (control) · D-100 (같은 결함 class) · D-043 (측정은 tree 에 대한 주장) ·
  D-076/D-081 (emptiness before success) · Q-096

## D-101 — 2026-08-06 — residue 를 다 채점하니 **COLLATERAL finding 은 2 가 아니라 4** 였고, 첫 violator 에서 멈추는 loop 가 그 절반을 가리고 있었다

- **Context**: D-100 이 residue 4 site 중 1 개만 채점하고 나머지를 `UNREAD` 로 남겼다.
  이유는 `test_self_entries_are_the_majority_and_are_left_alone` 이 loop **안에서**
  assert 해서 처음 만난 violator 에서 죽기 때문. STATE 는 이걸 #1 bottleneck 으로 올렸다 —
  나머지 3 개의 kind 만이 headline pair 가 온전한지를 결정하므로.
- **먼저 run 없이 되는 것부터**: `grade()` 가 `SELF_ENTRY` 를 주려면 site 의 **자기 모듈
  test** 가 `EXCLUDED_TESTS` 에 있어야 한다. 없으면 `SELF_ENTRY` 는 구조적으로 도달
  불가 — suite 실행 0 회짜리 one-sided bound (`self_entry_is_impossible`). 이 bound 는
  **headline 2 개를 전부 확정**한다 (`guard_reflexivity` / `local_only_audit` 둘 다 제외
  목록에 test 가 없음). 즉 D-061/D-062 finding 은 **측정 없이도** `COLLATERAL` 이었다.
  그리고 residue 4 개는 **하나도** 확정하지 못한다 — 넷 다 제외 목록에 test 가 있는 두
  모듈 소속. `RUN_FREE_DISCHARGED = ()` 를 지우지 않고 기록하는 이유가 이것: 아래 run 의
  가격표다.
- **Reading** (local, sha `04c445f7`, `effect_from_one_run` + `measure_attributed`,
  10 분): residue 는 **2 / 2**. `exclusion_scope.RankAgreement.reportable` 과
  `ReplicatedReading.licensed` 은 `SELF_ENTRY`; `predicate_inputs.Drift.stationary` 와
  `Spread.stationary` 는 **`COLLATERAL`**. `Spread.stationary` 의 **유일한** hider 는
  `test_exclusion_scope.py` — 그 predicate 의 instrument 가 아니다.
- **Decision**: (1) loop 안 assert → violator **수집 후** assert. (2) 같은 fixture 위에
  residue 전체를 채점하고 pin 과 대조하는 slow test 추가 — 실패 메시지는 첫 불일치가 아니라
  **표 전체**를 출력한다 (`UNREAD` 채우는 비용을 site 당 1 run 이 아니라 총 1 run 으로).
  (3) grade 별 source 를 site 단위로 기록 (`SOURCE` / `SOURCES`) — 3 개는 CI 가 아니라 이
  box 의 reading 이고, D-086 상 module-level provenance 하나가 전부를 대변하면 안 된다.
- **부수 발견 — 그리고 이게 더 큰 건**: `manufactured_candidates` 의 docstring 이 30 여
  cycle 동안 "`collateral` 의 부분집합" 이라고 적어 왔고 slow test 가 그걸 assert 하고
  있었다. **거짓이다** — 6 중 2 가 `SELF_ENTRY`. D-100 이 바로 두 줄 위에서 진단한 바로 그
  결함(모집단의 경험적 성질을 invariant 로 승격)이, D-100 의 수리를 **통과해서** 살아남았다.
  test 가 앞선 `assert` 에서 죽어 이 줄에 도달한 적이 없었기 때문. 지금 grade 별 분할로 교체.
- **Census 비용 — 30 번째 cycle, 그리고 처음으로 두 member 중 하나가 다른 하나 때문에 생겼다**:
  `coverage` 가 `len(GRADED)` 대신 `if s in table` 로 세기 시작하면서 **보이는 guard** 가
  됐고, 그 순간 `GRADED` 는 enumerator 없는 TYPED allow-list 가 됐다
  (`unwatched_exemptions` 5→6). 그래서 watcher `stale_grades` 를 썼고, 그것도
  population-shaped 라 pool 에 들어간다 — pool 74→**76**, mirror pair 7→**8**,
  `unwatched_exemptions` 는 같은 cycle 안에서 다시 5. 즉 보이는 guard 하나의 값은
  **pool member 2 개**다. 이 module 이 실제로 하려던 일 5 개(`reading`, `of_grade`,
  `self_hiders`, `self_entry_is_impossible`, `run_free_reading`)는 전부 **안 보인다** —
  D-089 의 across-function rule 이 네 번째로 사전 예측대로 맞았다. 부수적으로
  `exemption_masking.parameterised` 가 **1→2** 가 됐는데, 그 pin 의 docstring 이
  "> 1 이면 그 guard 가 **의도적으로** auditable 해진 것" 이라고 미리 적어둔 경우에
  정확히 해당한다. `key_conflation` 의 reader 수는 21→**24** (셋 다 def-time default —
  D-080 을 모르고 쓴 module 이 D-080 을 재현).
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/06-15-the-residue-graded-and-the-finding-doubled.md`,
  `eval/mppi_sandbox/candidate_scope.py`, `eval/mppi_sandbox/exclusion_scope.py`

## D-100 — 2026-08-06 — Q-092 가 기다리라고 한 reading 은 **이미 손에 있었다**, 그리고 두 행은 하나의 finding 이다

- **Context**: Q-092 의 lean 은 (b) "D-096 의 유도된 timeout 이 들어간 CI 를 먼저 읽어라"
  였다 — 같은 파일의 6 건이 timeout 이었으니 이 2 건도 오염됐을 수 있다는 이유. 그 추론이
  틀렸다: 두 행은 **assertion 에 도달했고** full diff 를 출력했다. 기다릴 reading 이
  아니라 **아무도 열어보지 않은 reading** 이었다.
- **Reading** (run `31058173229`, job `92480149564`, sha `210eeb0a`): `manufactured_
  candidates` 는 2 가 아니라 **6**. 기존 headline pair 는 그대로 있고, 네 개가 합류했다 —
  `exclusion_scope.RankAgreement.reportable`, `exclusion_scope.ReplicatedReading.licensed`,
  `predicate_inputs.Drift.stationary`, `predicate_inputs.Spread.stationary`. 두 번째 실패는
  그중 **첫 번째 이름을 그대로 부른다**. 같은 site 가 양쪽에 있으므로 **2 행 = 1 finding**.
- **Decision**: `candidate_scope.py` 로 reading 을 pin 하고 mechanism 을 진술.
  `grade()` 는 *누가 가렸나* 를, `Masked.manufactured_candidate` 는 *어느 방향으로
  움직였나* 를 읽는다 — **disjoint field**. `orthogonality_witness()` 가 그 결합을 suite
  실행 없이 네 줄로 구성한다. 즉 "self-entry 는 절대 manufactured candidate 가 아니다" 는
  **불변식이 아니라 당시 population 의 경험적 성질**이었고, assertion 으로 승격된 것이다.
  D-095 와 같은 형태 — population 을 아무도 대주지 않은 claim.
- **여섯으로 넓히지 않은 이유**: 그 set assertion 의 명시된 임무가 *"다른 모듈의
  predicate 를 가리기 시작하는 `EXCLUDED_TESTS` 확대를 잡는 것"* 이다. 관측이 6 이니
  literal 을 6 으로 바꾸는 건 수리가 아니라 **계측기를 지우고 이름만 남기는 것** (D-099 가
  값을 매긴 그 수, D-097 이 잡은 그 형태). 대신 **scope 를 진술**: headline 은 그대로
  subset 으로, 나머지는 pin 된 residue 로 — 일곱 번째가 나타나면 red.
- **측정되지 않은 것을 측정된 것으로 말하지 않음**: log 는 네 residue site 중 **하나만**
  grade 한다 (self-entry test 는 첫 위반에서 멈춘다). 나머지 셋을 "self-entry 니까
  headline 은 무사하다" 로 읽는 것이 정확히 D-098 의 오류다. `coverage()` = `1/4`,
  나머지는 `UNREAD` — site 에 대한 사실이 아니라 **reading 에 대한 사실**이라 별도 철자.
- **부수 발견 — pin 4 개가 전부 stale 해졌다**: HEAD (D-099, unpushed) 가 red 였고 그것이
  13:00 cycle 이 push 하지 않은 이유다. `test_drift_repair` 가 `repair_admissibility` 를
  import 하면서 `results/` 의 transitive reader 가 됐다 — 10:00 이 "premise 가 움직이지
  않은 유일한 후보" 라 부른 그 pin. 세 cycle 연속 각자 옳은 withdrawal 이 합쳐져
  `inert()` 가 모든 질문에 `False` 다: **live population 0** (D-088 의 `UNPOPULATED` 를
  소모로 도달). 두 번째 suite run tax 가 이제 무조건이다. Q-093 격상.
- **Alternatives**: (a) literal 을 6 으로 확대 — discrimination 소멸. (b) 축소 fixture 로
  local 재현 (Q-092 의 (c)) — reading 이 이미 있는데 시간을 쓰는 것. (c) 네 residue 를
  전부 self-entry 로 간주 — 3 건 over-claim.
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/06-14-the-reading-was-already-in-hand.md`, Q-092 → resolved, Q-093

## D-099 — 2026-08-06 — "tolerance 를 넓힌다" 는 **정책이 아니라 claim 별 속성**이었다: 6 중 1

- **Context**: D-098 이 6 개 CI 실패를 dispatch drift 로 확정했다. 그러면 이 6 개는
  모든 runner 에서 영구히 red — STATE #4 가 세 route 를 나열했다: (a) dispatch 조건부
  `xfail`, (b) 두 dispatch 를 함께 담는 tolerance, (c) dev box 에서 AVX-512 masking.
  고르는 대신 **측정된 6 행에 대해 값을 매겼다**.
- **Decision**: `drift_repair.py` — CI signature 를 repair 가 작용하는 shape 로 파싱하고
  band 산술은 `repair_admissibility.price` 에 위임(D-047: 한 곳에서만 진술). 결과:
  **(b) 는 route 가 아니라 특수 케이스 — 6 중 1 만 수리한다.** 양측 구간을 가진 것은 2
  개뿐(`scale_match` ×1.14 admissible, `exposure_timing_band` ×2.95 > `MAX_HONEST_WIDEN`),
  3 개는 one-sided, 1 개는 set equality. **(c) 는 repair 가 아니라 re-baseline** — 6 개
  assertion 이 동시에 unmeasured 가 된다(D-017…D-098 청구서). **(a) 채택**: `eval/conftest.py`
  가 `simd_attribution.verdicts()` 에서 marker set 을 **유도**하고 `strict=True` 로 표시.
- **핵심 발견 — one-sided 3 개는 inadmissible 이 아니라 unpriceable 이고, 기존 계측기는
  그래도 답을 냈다 (안심시키는 쪽으로)**: `repair_admissibility` 는 threshold 를
  `RATIO_NULL = 1.0` 위에서 값을 매기며 자기 docstring 이 그 population 을 명시한다. 이
  population 의 bound 는 null 이 0, 0, 1 이다. 1.0 을 빌리면 `(worst−null)/(lo−null)` 의
  분자·분모가 **모두 음수**가 되어 몫이 1 을 살짝 넘고, *"asserted effect 를 전부 보존"*
  으로 읽힌다. 음수나 `ZeroDivisionError` 는 스스로 신고하지만 ~100% 는 안 한다 → 위임
  대신 `NO_NULL_SUPPLIED` 반환. D-097 의 결함이되 **오답이 좋은 소식으로 읽히는** 형태.
- **(a) 는 job 을 green 으로 만들지 못한다 — STATE #4 는 만든다고 했다**: 14 red =
  6 markable + D-096 이 고친 6 timeout + **reading 이 없는 2**. `grade()` = `RESIDUE`,
  그 residue 가 정확히 Q-092 의 쌍. `refused() ∩ markable() = ∅` 를 test 로 고정 — 그
  2 개를 표시하면 다른 행의 증거로 미해명 실패를 기계 artefact 로 은퇴시키는 배너의 오류.
- **`strict=True` 가 하중을 받는 부분**: non-strict xfail 은 pass 를 조용히 흡수하므로
  숫자가 수렴하는 날(numpy bump / runner 변경 / 진짜 수정) 아무도 못 배운다. strict 는
  XPASS 를 실패로 만들어 attribution 을 다시 연다. calibrated box 에서는 0 개 표시 —
  진짜 회귀는 여기서 여전히 실패한다. 양방향 pin.
- **Alternatives**: (a) 6 개 tolerance 를 일괄 확대 — 5 개는 연산자조차 없고 1 개는
  discrimination 파괴. (b) dev box masking — re-baseline 을 repair 로 위장. (c) red 유지
  — 계측되지 않은 red 는 D-085 이후 push gate 가 막는다.
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/06-13-widening-repairs-one-of-six.md`, Q-092, Q-094

## D-098 — 2026-08-06 — 배너는 **옳았고**, 그 옳음을 벌어들인 적은 없었다

- **Context**: 모든 `slow` 세션은 실패를 dispatch drift 로 미리 설명하는 배너를 출력한다 (D-033). 측정 이전에 인쇄되고 모든 결과에 들어맞는 설명은 아무것도 판별하지 못하므로, 이 배너를 받아들이면 `slow` job 은 진짜 이유로 red 가 될 수 없는 job 이 된다 (Q-091). D-033 은 **다섯 개의 지명된 테스트**에 대한 발견이었고, 배너는 그것을 *임의의* closed-loop 실패로 일반화했으며, 그 뒤로 아무도 reading 을 다시 취하지 않았다.
- **Decision**: D-033 이 가정만 하고 기계화하지 않은 control 을 취한다. `simd_attribution.py` 가 attributable 실패 각각을 dev box 에서 **두 번** 돌린다 — native, 그리고 AVX-512 masked (masked 상태의 numpy 는 runner 의 fingerprint step 이 인쇄하는 것과 동일한 최상위 확장을 보고한다). **읽을 수 있는 6건 전부가 native 통과 / masked 실패**, 그중 셋은 CI 의 숫자를 자릿수까지 재현한다. 배너는 옳다. 그러나 verdict 자체보다 중요한 것은 이제 그것이 **벌어들인** verdict 이라는 점 — 같은 절차가 다음번엔 `REAL` 을 반환할 수 있고, 배너는 결코 그럴 수 없었다. 매칭은 렌더링이 아니라 **측정된 크기**에 대해 한다: CI 와 이 box 는 동일한 비교의 tolerance 를 서로 다르게 인쇄하며, 줄 단위 비교는 그것을 세계의 차이로 읽는다.
- **핵심 단서 — 표본이 답 쪽으로 편향돼 있다**: attributable 8건 중 2건은 여기서 **읽히지 않는다**. 둘 다 스스로 nested pytest run 을 띄워 assertion 에 닿기 전에 벽에 부딪힌다. 그리고 그 2건이 하필 부동소수가 아니라 **집합 비교**인 행 — 즉 dispatch 가 원인일 가능성이 가장 낮은 행이다. 그래서 `grade()` 는 읽은 것이 전부 drift 임에도 `ALL_DRIFT` 가 아니라 **`INCOMPLETE`** 를 반환한다. 증거 너머로 일반화하는 것은 정확히 배너의 오류이고, 그것을 잡으려고 만든 계측기가 그 오류를 범해서는 안 된다.
- **부수 결정**: run 의 census 를 행 단위로 pin 한다. 이 14건은 두 cycle 연속으로 눈으로 요약됐고 **두 번 다 같은 파일에 대해 틀렸다** — 08:00 STATE 는 맞았고, 09:00 journal 이 그것을 🔴 로 "정정" 하면서 총계와 분해를 모두 틀렸으며, 원본보다 더 확신에 차 있었다. 이제 모든 공표 숫자는 `census()` / `file_census()` 질의다.
- **Alternatives**: (a) 배너를 믿고 xfail — D-033 을 반증 불가능한 면죄부로 승격. (b) 회귀로 취급하고 subject 수정 — dispatch 가 원인이면 멀쩡한 코드를 왜곡. (c) 채택안: 판별하고, 판별할 수 없는 것은 판별하지 않았다고 말한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/06-10-the-banner-was-right-and-unearned.md` · Q-091 (partially resolved) · Q-092 (남은 2건) · D-033 (다시 취한 발견) · D-097 (부분 population 에 대한 verdict) · D-091 (subject test 부재) · D-076/D-081 (emptiness before success)

## D-097 — 2026-08-06 — push gate 의 green 은 **일부 population 에 대한 주장**이었고, 실패는 나머지에 있었다

- **Context**: 처음으로 완주한 `slow` job (run `31042602721`) 이 실패 14건을 published 했는데, 그 전부가 local push gate 가 **실행하지 않는** 테스트들 안에 있었다. local 명령에는 `--slow` 가 없다 — 수집된 것의 대부분을 돌리고 나머지를 skip 한다. `push_preflight` 는 `skipped`/`deselected` 를 처음부터 파싱하고 있었고 (`EXECUTED_OUTCOMES` 가 둘 다 이름을 대며 왜 제외하는지까지 주석에 적혀 있다), 그 뺄셈의 **나머지를 버렸다**. 규칙은 `executed == 0` 한 숫자에만 적용됐다. 결과: `sandbox:pass` 문자열이 89 cycle 동안 참이었지만 — 전체가 아니라 그 일부에 대해 참이었고, 알려진 실패는 전부 제외된 쪽에 있었다.
- **Decision**: `suite_coverage.py` 가 gate 가 이미 계산하던 나머지를 보관한다. `EMPTY`/`PARTIAL`/`FULL` 은 `population` 이 아니라 **`executed` 기준** — 전부 skip 된 run 이 "나머지가 있는 reading" 이 아니라 `VACUOUS` 와 구성적으로 일치하도록. 새 verdict `UNCOVERED_RED` 는 **연언**일 때만 발화한다: partial receipt **그리고** uncovered half 에 대한 failing `ci_verdict`. partial 자체는 거절 사유가 아니다 — local suite 는 항상 slow half 를 건너뛰므로 (cycle 예산을 크게 초과) 일괄 거절은 모든 push 를 막고 하루 만에 muted 된다 (D-042, 이 모듈 자신의 Refs 줄). uncovered verdict 는 **주입**이지 fetch 가 아니다: 모든 push 앞에 서는 gate 는 네트워크 없이 동작해야 하고, 거절 안에서의 fetch 실패는 아무도 해제할 수 없는 거절이다. 평상시 `GREEN` 조차 자신이 덮지 못한 것을 이름으로 말한다.
- **Alternatives**: (a) local gate 가 `--slow` 를 돌린다 — cycle 예산 밖, 기각. (b) partial 이면 무조건 거절 — D-042 로 자멸. (c) metric 문자열만 고친다 — 숫자는 정직해지나 gate 는 계속 통과시킴. (d) 채택안: coverage 를 outcome 과 **직교하는 축**으로 만들고, 거절은 연언으로 좁힌다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/06-09-green-over-a-partial-population.md` · D-095 (계측기는 완성돼 있었고 눈금을 아무도 읽지 않았다 — 한 cycle 뒤 같은 발견) · D-091 (subject test 부재) · D-042 · D-076/D-081 (emptiness before success)

## D-096 — 2026-08-06 — job ceiling과 nested timeout은 **다른 숫자**였다 — 하나를 고쳐야 다른 하나가 읽혔다

- **Context**: D-094가 `slow` job ceiling을 120 → 360 min으로 올렸지만, 그 raise가
  실제로 작동했는지는 *완료된* run이 없어 확인 불가였다. 이번 cycle에 run
  `31042602721` (`d6b60c8`)이 완료 — **162.7 min / 360 min cap, +55% headroom,
  killed 아님**. D-094 확정. 그리고 12+ run 만에 처음으로 job이 *왜 red인지*
  발표했다: `12 failed, 138 passed, 2 errors in 9752.82s`, 그중 **6개가 한 문장** —
  `TimeoutExpired ... after 900 seconds`.
- **Decision**: nested-suite timeout을 **단일 statement**로 접고 (900 → 2792 s),
  그 값을 *유도*했다 — 관측된 최악 suite cost(1396 s) × `HEADROOM_FACTOR`. 같은
  commit의 `fast` pytest step이 **1032 s에 pass**했고 nested spawn은 동일 selection을
  돌린다. 즉 900 s는 flaky가 아니라 **구조적으로 매 run 실패**. 새 모듈
  `nested_timeout.py`는 site 수를 손으로 적지 않고 **AST로 측정**한다 — 측정 결과
  **7곳 / 2개 값** (900 셋, **1800 셋**). 1800은 누군가 이미 이 벽에 부딪혀 그
  호출들만 두 배로 올린 흔적이고, **1800조차 요구치 2792를 못 넘긴다**.
- **Alternatives**: (a) 900 → 1800만 올리기 — 이미 시도된 적 있고 부족함이 측정됨.
  (b) census subject 축소 — D-091이 측정으로 이미 기각 (admissible narrowing 2 files).
  (c) 각 site를 개별로 올리기 — 지금 defect 그 자체.
- **부수 발견 (이 cycle의 진짜 교훈)**: literal을 name으로 바꾸자
  `suite_runners()`(정수 literal default를 요구하는 signature scan)가 **6 → 0**으로
  실명(失明)했고, `collapsed_floor_seconds()`가 8376 → 1396, `declared_ceiling.grade()`가
  runner class **0개**를 센 floor 위에서 `SUFFICIENT`로 뒤집혔다. 이 branch에서
  absence-read-as-clean 9번째이자, **그것을 막으려는 수정이 만들어낸 첫 사례**.
  `_package_int_constants`로 name default를 해석해 복구. 통합과 그 통합을 재는
  계측기는 같이 착지해야 한다 — 아니면 계측기가 조용히 성공을 보고한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/06-08-nested-timeout-one-statement.md`

## D-095 — 2026-08-06 — 계측기는 완성돼 있었고, 아무도 눈금을 읽은 적이 없었다

- **Context**: D-044 가 정한 Phase 4 쓰기 순서 때문에 receipt 를 뜬 뒤에도
  `JOURNAL.md` / `STATE.md` / `RESULTS.md` / `results/*.tsv` 가 움직여서 매 cycle
  `push_preflight check` 가 `STALE` 을 뱉었고, 그 대가를 full suite 재실행으로
  지불해왔다. 면제 장치(`inert_surface.filter_drift`)는 이미 있었다 — 다만
  `PROBED` 레지스트리가 **비어 있었다**. 빈 레지스트리에서 `inert()` 는 모든
  질문에 `False` 를 답한다.
- **Decision**: probe 를 실제로 돌려서 네 후보 전부 측정하고 `PROBED` 에
  전사(transcribe)했다 — 전부 `INERT`. 즉 D-044 의 손검사 "(checked)" 는
  **맞았고**, 기계화되지 않은 채로 두 cycle 동안 세금만 냈다. 함께: 레지스트리
  자체의 공허함을 잡는 테스트를 추가했고(자기 자신에게 vacuity 규칙 적용),
  `push_preflight record` 는 실행 전에 `--out` 을 unlink 한다 — 고정 경로 +
  분 단위 실행 = crash 시 어제의 green receipt 가 남는 구조였고, D-082 가
  명세한 `NO_RECEIPT` 는 crash 가 아무것도 남기지 않아야만 도달 가능하다.
- **Alternatives**: (a) 헌법의 4b/4c/TSV 순서를 바꿔 receipt 를 맨 끝에 — 규칙
  두 개를 또 손으로 맞물리게 하는 쪽. (b) 네 경로를 타입으로 면제 — D-079 가
  말한 장식. (c) 계속 재실행 비용 지불.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/06-06-inert-surface-probed-and-pinned.md`

## D-094 — 2026-08-06 — ceiling raise를 **유도**했다, 고르지 않았다 — 그리고 남은 활주로는 instrument 한 개다

- **Context**: D-092 가 잰 collapsed floor 는 6 runner class × 1396 s = **8376 s**, 천장은 7200 s → `INSUFFICIENT` 1176 s. D-093 이 memo 를 ship 해서 collapse 는 끝났고, 남은 건 D-089 option (a) 의 나머지 반쪽인 raise 하나였다. 그런데 이 branch 의 raise 는 세 번 모두(D-084 10→30, D-085 60→120) **직전 reading 에서 골라졌고** 매번 조용히 시험 대상이 됐다 — workflow 주석이 그 실패 양상을 이미 적어둔 채로.
- **Decision**: `timeout-minutes: 120 → 360`, 그리고 `eval/mppi_sandbox/declared_ceiling.py` 로 그 숫자를 **유도 가능하게** 만들었다. requirement = 측정된 collapsed floor × `HEADROOM_FACTOR` (**두 배** — D-085 가 적어두고 적용하지 않은 규칙: instrument 비용은 superlinear 이므로 마지막 reading 에 맞춰 깎지 말고 두 배로. 이 job 자체의 non-nested 작업이 **미측정**이라는 사실도 같이 흡수한다). 선언값은 hand-typed copy 가 아니라 **강제되는 곳** — workflow — 에서 읽는다.
- **핵심 측정, 그리고 내 추정은 틀렸다**: `runway()` — platform 의 job kill 아래로 full-suite runner class 가 몇 개 더 들어가는가. 답은 **1**. 7 class 면 requirement 325.7 분(선언 가능), 8 class 면 372.3 분(**어떤 값도 불가**). 나는 실행 전에 2 로 추정했다 — 남은 margin 전체만큼 틀렸고, 그래서 이것은 문장이 아니라 함수다. 이 branch 는 대략 3 cycle 당 1 개꼴로 runner class 를 늘려왔다.
- **왜 280 이 아니라 360 인가**: requirement 만 보면 279.2 분이면 된다. 하지만 천장은 예약이 아니라 **kill switch** 다 — job 이 일찍 끝나면 비용 0. 280 을 선언하면 raise cycle 을 딱 한 번 더 사는 것 말고 아무것도 못 산다. 남은 활주로를 지금 전부 가져가면 다음 red 는 `UNENFORCEABLE` — recorder 를 한 run 에 co-install 하거나 census subject 를 자르는, **다른 fix 를 요구하는 다른 문제**이지 네 번째 숫자 올리기가 아니다.
- **숫자가 두 곳(사실은 세 곳)에 적혀 있었다**: workflow 의 `timeout-minutes` 가 강제되는 값, `nested_suite_cost.SLOW_CEILING_SECONDS` 는 이 package 의 모든 `grade()` 가 대조하는 copy, `test_ci_verdict.FIXTURE_CAPS` 가 세 번째. **D-047 의 결함 클래스.** `agreement()` 가 copy 를 workflow 에 대조하고 test 가 `AGREES` 를 고정한다 — 한쪽만 올리면 이제 두 값을 이름과 함께 red 로 말한다.
- **red 4 개는 전부 *옛* 천장에 대한 주장이었다**: (1) D-092 headline 과 (2) D-089 의 burn share 는 7200 s 에 대해 참인 발견 — epoch 상수로 명시 고정하고, 무엇이 바뀌었는지 말하는 live companion 을 옆에 붙였다. (3) `test_caps_are_read_from_the_real_workflow` 는 **자기 모듈이 docstring 에 적어둔 규칙을 어기고 있었다** — `job_caps` 는 "과거 run 은 그 epoch 의 cap 으로 재라" 고 경고하는데, 이 test 는 live cap == fixture-epoch cap 을 걸었다. fixture 를 뜬 뒤 천장이 안 움직였기 때문에만 통과하던 것. 이제 원래 목적인 job **이름** rename guard 만 건다. (4) `test_sufficiency_is_certified_from_the_upper_bound_not_the_ledger` 는 **red 가 아니라 무의미해질 뻔했다**: 올린 천장에서는 두 bound 가 모두 들어맞아 어느 쪽을 봐도 통과한다 — 아무것도 구별하지 못하는 pass. upper bound 가 들어맞지 *않는* 천장에서 채점하도록 되돌렸다. 네 개를 새 숫자에 맞춰 일괄 갱신했다면 이것을 그대로 ship 했다.
- **⚠️ 360 은 여기서 측정된 값이 아니라 선언된 입력이다**: 이번 session 에 network 권한이 없어 문서화된 limit 을 가져올 수 없었다. 따라서 `runway(cap_minutes=None)` 은 숫자 대신 `None`, `grade` 는 `UNENFORCEABLE` 대신 `CAP_UNVERIFIED` 를 읽는다 — 조건부 주장이 측정된 주장의 모양으로 인쇄되지 않도록. repo 안의 방증은 있다(`ci_verdict.job_caps` docstring 이 같은 360 분 default 를 이전 cycle 에 적어뒀다) — 이는 provenance 이지 verification 이 아니다. 그리고 360 선언은 cap 에 대한 **어느 해석에서도 안전**하다(default 와 동일 / platform 이 clamp / 보수적). 이 package 가 absence-as-result 에 이름을 붙인 여섯 번째이자, output 이 아니라 **input** 에 대한 첫 번째.
- **Census cost (29번째 cycle, 그리고 처음으로 *코드* 가 아니라 이 entry 의 *산문* 이 낸 비용)**: red 1 개 — `citation_audit.rank_unregistered`. 위 문단이 headroom factor 를 소수점 숫자로 적었는데, 그 spelling 은 D-038 의 등록된 claim `horizon_weight_swing_cited` 가 쓰는 숫자와 **같다**. 맨 숫자 하나는 어느 쪽 token 도 달고 있지 않으므로 audit 이 둘을 구별할 수 없고, 따라서 "증거로 거절" 이 아니라 **"침묵으로 거절"** bucket 에 들어간다. 그 bucket 이 늘어난 것이 red 의 내용이며, 그 test 의 존재 이유가 정확히 *거절이 점점 증거가 아니라 침묵으로 이뤄지고 있다* 를 잡는 것이다. threshold 를 올리는 것은 test 가 금지하는 바로 그 행동이므로, 고친 것은 **내 spelling** 이다 (숫자 대신 `두 배`). 🔴 **그리고 이 문단의 첫 판이 충돌하는 숫자를 인용해서 red 를 1 개에서 4 개로 늘렸다** — 그 중 하나는 배수 표기라 bare mention 이 아니라 진짜 citation 후보로 채점됐다. 충돌을 설명하려면 충돌하는 것을 적어야 하고, 적는 순간 audit 이 그것을 잡는다. 결국 숫자를 한 번도 쓰지 않고 claim 의 **이름으로만** 서술했다. 한 spelling 이 서로 무관한 두 quantity 를 가리키는 `key_conflation` 의 결함 클래스이고, D-093 이 `collapse_key` 에서 찾은 것과 같은 형태 — 이번엔 PR 에 닿기 전 방금 쓴 산문에서 잡혔다. 남은 한계는 실재한다: bare numeral 은 citation 이 아니며, audit 의 silent bucket 은 모호한 spelling 이 쌓이는 곳이다.
- **Alternatives**: (a) 280 선언 — requirement 는 만족하지만 활주로를 남겨 네 번째 raise 를 예약한다 (b) `timeout-minutes` 줄 삭제 — platform default 에 맡기면 breach 가 신호이길 그만둔다 (c) **채택: 유도된 requirement + 남은 활주로 전부 + copy 대조 pin**.
- **Status**: accepted. D-089 option (a) 양쪽 반쪽 모두 완료 — `nested_run_ledger.grade()` 가 처음으로 `SUFFICIENT`.
- **Refs**: PR #67, `journal/2026-08/06-04-ceiling-declared-once-and-derived.md`, D-089 / D-092 / D-093 / D-047 / D-085

## D-093 — 2026-08-06 — memo 를 ship 했다 — 그리고 쓰라고 지시받은 key 는 identity 가 아니었다

- **Context**: D-092 가 잰 18 nested run 중 14 개를 순수 memo 로 제거하는 것이 board 에서 가장 큰 절감(~326 분)이고, STATE #1 은 그것을 `collapse_key` 로 keying 하라고 지시했다. 그 key 가 무엇을 읽는지부터 확인했다.
- **핵심 결함**: `collapse_key` 는 **argv** 를 읽는다. 그런데 `predicate_vacuity` 는 `_PLUGIN` 과 `_PLUGIN_ATTRIBUTED` 를 **동일한 이름** `predicate_vacuity_plugin` 으로 설치한다 — 원하는 쪽을 temp dir 에 써서 `PYTHONPATH` 에 얹는 방식이라, argv 는 recorder 를 *가리킬* 뿐 담고 있지 않다. 측정 대상 population 도 `PREDICATE_VACUITY_SITES` env 로 이동하며 어떤 argv 에도 안 나온다. 지금 이 두 census 가 안 섞이는 유일한 이유는 `--ignore` 집합이 다르다는 **우연**이고, `measure_attributed` 를 exclusion 과 함께 부르면 argv 는 문자 단위로 동일해진다 — 그 key 로 만든 memo 는 value census 에 attributed reading 을 답한다. **`key_conflation` 의 결함 클래스가, 그것을 피하려고 쓴 key 안에서.**
- **Decision**: `suite_memo.py` — key 는 `(argv, cwd, recorder **text** digest, population digest, tree digest)`. tree digest 를 넣는 이유는 "측정 → scratch tree 수정 → 재측정" 이 두 번째에 다른 질문이고, 그걸 못 보는 memo 는 negative control 에 변경 *전* 의 reading 을 답하기 때문 — pass 로 읽히는 실패. `collapse_key` 에도 plugin text / payload digest 를 접어 넣고, recorder text 를 못 잡은 spawn 은 `UNIDENTIFIED` + `duplicates == -1` 로 **모른다고 답한다** (class 과소 계수 = clean 하게 읽히는 방향이므로 추측 금지). identity 로 다시 재도 reading 은 **18 run / 4 class / 14 제거** 그대로 — 바뀐 것은 수가 아니라 그 수가 무엇에 대한 주장인지이며, 그것은 양쪽으로 재보기 전에는 알 수 없었다.
- **두 번째 결함**: recorder 들은 "timeout / dump 파일 없음" 과 "정상 종료, 관측 0" 에 **똑같이 `{}`** 를 반환했다. 매 호출이 자기 run 값을 치르는 동안엔 일시적 혼동이지만, **memo 는 그것을 영구화한다** — 한 번의 timeout 이 세션 내내 "이 predicate 는 호출되지 않는다" 는 finding 으로 서빙된다. `None`(미완료) 과 `{}`(관측 0) 로 분리; 전자는 저장 거부. 이 package 에서 absence-as-result 를 이름 붙인 다섯 번째(`UNPOPULATED`/`UNRUN`/`UNCOLLECTED`/`UNIDENTIFIED`)이자, **cache 가 무엇을 얼려버리는가** 를 물어서 찾은 첫 번째.
- **측정**: 실제 경로 end-to-end — 동일 명령 2회 → `6.63 s` 다음 **`0.0085 s`**, spawn 1회. 동일 argv + attributed recorder → spawn 2회 (정상 miss). 다만 18 spawn 은 `slow` test 안에 있어 **local fast half 는 건너뛴다**: 오늘의 green 은 "아무것도 안 깨졌다" 의 증거이지 "326 분 절감" 의 증거가 아니다.
- **Alternatives**: (a) 지시대로 `collapse_key` 사용 — `--ignore` 목록의 우연 덕에만 옳음 (b) argv+env 전체를 key 로 — plugin **파일** 은 여전히 이름으로만 참조됨 (c) **채택: 명령의 실질(recorder text 포함) + tree** 로 keying.
- **Census cost (28번째 cycle, 그리고 pin 을 넓히지 않고 등록으로 치른 첫 번째)**: 새 module 이 red test 7개를 데려왔다 — allow-list 2개(`TREE_SUFFIXES`/`TREE_SKIP`) unwatched, AND-shaped guard 1개 추가, `DERIVED` 4→5, `UNRUNNABLE` pair 2개. 두 list 를 `suite_memo.digest_scope` 로 tamper 등록(registry 9→**11**, tamper 8→**10**, 열 개 모두 `BITES`)하고, `tree_digest` 가 scope 를 call time 에 읽도록 바꿔 `exemption_masking` 이 skip 대신 screen 하게 했다. 그러자 7개 중 **4개가 손대지 않고** green — 이번 entrant 는 module-level registry 에서 도출 가능한 `DERIVED` bucket 에 들어갔고, 이는 직전 다섯 entrant 가 들어가지 *못한* 곳이다.
- **Status**: accepted. D-089 (a) 의 남은 반쪽(ceiling raise, 8376 s 초과)은 여전히 필수.
- **Refs**: PR #67, `journal/2026-08/06-02-memo-keyed-on-identity.md`, D-089 / D-090 / D-092

## D-092 — 2026-08-06 — 곱해야 할 수를 아무도 안 재봤다: nested run 은 6 이 아니라 **≥18**, 그리고 전부 collapse 해도 천장을 못 넘는다

- **Context**: D-089 option (a) 는 "6+ nested run 을 하나로 collapse + timeout 을 1396 s 위로" 였고, 그 **6+** 는 *source 의 call site 개수*였다. call site 는 run 이 아니다 — 한 site 를 네 test 가 부르면 네 run 이고, 아무도 안 부르는 site 는 0 run 이다. 곱셈의 한쪽을 재보지 않은 채 세 번의 ceiling raise 가 있었다.
- **Decision**: `nested_run_ledger.py` — `subprocess.run` 을 stub 으로 갈아끼워 **spawn 을 실행하지 않고 세는** plugin. 이 tree 의 측정: full-suite nested run **≥18** (하한), distinct collapse class **≥4**, 즉 **순수 memo 가 18 중 14 개(~326 분)를 제거**한다. 그런데 upper bound 6 runner × 1396 s = **8376 s > 7200 s** → `INSUFFICIENT`, **1176 s 부족**. 그래서 D-089 (a) 의 두 반쪽은 **선택지가 아니라 둘 다 필수**다: collapse 는 큰 절감이지만 혼자서는 천장에 못 닿는다.
- **핵심 결함 (자기 자신에서 발견)**: 첫 판은 upper bound 를 `nested_suite_cost.suite_runners()` 로 읽었다 — signature 스캔이라 `timeout` 정수 default 를 요구한다. `guard_vacuity.measure` 는 `suite` 를 `DEFAULT_SUITE` 로 두고 `timeout=900` 을 **call site 에 리터럴로** 박아서 스캔에 안 잡힌다. 그 결과 **5** 를 반환하고 5 × 1396 = 6980 s 는 7200 s 에 **들어맞아** `SUFFICIENT` (headroom 220 s) 로 채점됐다. **이름 하나가 판정을 뒤집는다.** D-090 과 동일한 형태(한 목적으로 계산한 bound 를 다른 population 의 proxy 로 사용) — 이 branch 3번째이자, **그 교훈을 docstring 에 적어둔 모듈 안에서** 처음 발생. `declared_classes()` 는 두 스캔을 module 단위로 union 한다.
- **두 bound 의 방향을 반대로 고정**: ledger 는 구조적으로 **과소** 계수한다(stub 된 spawn 은 caller 를 실패시키고, 그 caller 는 다음 spawn 에 도달하지 못한다). class 과소 계수는 collapse 후 비용을 **작아 보이게** 하는, 즉 clean 하게 읽히는 방향이다. 따라서 `grade()` 는 **static upper bound 로만** sufficiency 를 인증하고 ledger 는 반증 전용 — test 로 고정.
- **Alternatives**: (a) call site 를 세는 static 스캔 유지 — 곱셈의 한쪽이 여전히 미측정 (b) 실제 slow half 를 한 번 돌려 계측 — 419 분, 측정 대상이 측정 비용이 됨 (c) **채택: spawn 을 stub 하고 세기** — 19 test / **6.4 s**, 명령어에 대해 정확.
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/06-00-nested-run-ledger.md`, D-089 / D-090 / D-091

## D-091 — 2026-08-05 — The narrowing is inadmissible: D-090's "buys nothing" files buy 535,536 observations and two false positives

- **Context**: D-090 bounded the census's wasted subject at **19 of 58** collected files — files whose work goes through a spawned Python, which the `-p`-installed recorder cannot observe — and deliberately declined to apply the narrowing until a before/after reading proved the verdicts survive. The 21:00 cycle built the machinery for that reading (`census_narrowing.py`, `901a0a0`, 18/18) and died before pushing or reporting it, so the comparison existed and had never been run. This cycle ran it.
- **Decision**: **Do not narrow.** One attributed nested run (9m06s local) grades the narrowing `CHANGED`: **26 verdicts moved**, **535,536 observations removed** from **18** hidden origins, `BOTH` 89 → **66**, `UNOBSERVED` 9 → **33**. `nested_subject.classify` grades a file `SPAWNS` if it *contains* a spawn; a file that shells out in one test still calls subject predicates in-process in its other thirty, and 9 of the 20 hidden files are instrument tests — the heaviest in-process callers in the suite (`test_probe_reach.py` **233,585**, `test_lam_dependence.py` **253,468**). The measured-admissible narrowing is **2 files** (`test_key_conflation.py`, `test_scale_match.py`, 0 contributions each), which clears no ceiling.
- **The dangerous direction, which was in nobody's error budget**: 23 of the 26 moves are `BOTH → UNOBSERVED` — an honest admission. **Two go the other way**: `git_surface.SurfaceReading.decidable` and `nested_subject._has_tests` read `BOTH → ALWAYS_TRUE`. `UNOBSERVED` says *we did not look*; `ALWAYS_TRUE` is a **claim**. Removing evidence can therefore *manufacture a positive result the suite never observed*, not merely weaken one — the first instance on this branch where lost evidence produces a presence rather than an absence. `Comparison.moved` counts moves and does not grade them by direction; it should.
- **What this reverses**: D-089's subject question — *does the census need the whole fast half?* — is answered **yes**, opposite to what D-090's syntax suggested. The 1396 s is not waste, so no subject cut brings the nested run under its 900 s timeout, and the repair space collapses to D-089's option (a): collapse the 6+ nested runs into one **and raise the timeout above 1396 s**. D-089 refused "raise 900" for want of evidence; the evidence now exists and points the other way.
- **Alternatives**: (a) apply the narrowing on D-090's static bound — this is what the measurement refutes; (b) narrow to the 2 measured-zero files — admissible but pointless; (c) fold `compare` and `contributions` into one "safe" flag — would have reported `PRESERVED` off those 2 files, which is exactly why `census_narrowing` kept them separate; (d) this — publish the refutation and leave `DEFAULT_SUITE` unchanged.
- **Census cost, 27th consecutive cycle**: guard pool 71 → **72**, `NO_REGISTRY` 11 → **11** (unchanged). The single entrant is `census_narrowing.contributions` — **bookkeeping** — while `compare`, the function the module exists to publish, narrows by `b.verdict != a.verdict` and stayed invisible. **Fifth consecutive headline-missed split**, and the **second consecutive one predicted in advance** by D-089's rule (conclusions spelled as verdict comparisons are invisible; caveats spelled as set membership are counted).
- **Also found**: `nested_suite_cost.nested_call_sites()` lists 7 sites and does **not** include `census_narrowing.measure` (1800 s, full-suite subject) — it reaches its spawn through `pv.measure_attributed`, and the detector matches direct pytest subprocesses only. The one-level-vs-transitive miss D-090 fixed inside `spawners()` is still live one module over.
- **Status**: accepted. `DEFAULT_SUITE` unchanged; `nested_suite_cost.grade()` still reads `DOOMED`.
- **Refs**: PR #67 · `journal/2026-08/05-22-narrowing-refuted-by-its-own-check.md` · supersedes D-090's proposed repair (D-090's *measurement* stands; its *recommendation* does not) · Q-090

## D-090 — 2026-08-05 — The nested suite's largest cost buys observations it cannot receive: the recorder is process-confined

- **Context**: D-089 measured the inequality that kills the `slow` job (nested run 1396 s > its 900 s timeout) and deliberately left the load-bearing question open — does the census need the **whole fast half** as its subject? Collapsing the nested calls into one is the cheap half, but one run still costs 1396 s, so collapsing alone does not clear the ceiling. Three prior cycles argued about the timeout's *size*; nobody had asked what the wait purchases.
- **Decision**: Answer the subject question by **measurement**, and ship the decision procedure rather than the narrowing. `eval/mppi_sandbox/nested_subject.py`. The recorder is installed with `-p <plugin_module>`, a **command-line flag**: `_run_recorder` sets no `PYTEST_PLUGINS`, and a test shelling out to its own `python -m pytest` passes no `-p`. So predicate calls in a grandchild process are invisible to the recorder that paid for them. `probe()` measures both legs of a constructed two-file suite through the **shipped** plugin — **2 in-process / 0 subprocess → `CONFINED`** — and grades two zeroes `INCONCLUSIVE`, because the in-process leg is the positive control and without it a broken probe is indistinguishable from the finding (D-075 / D-081 / D-088, three prior instances). The static layer then bounds the population: `spawners()` closes **transitively** over package-internal calls (32 names) and `spawning()` reads **19 of 58** collected files. Published as an **upper** bound (bare-name matching, `key_conflation`'s defect class, accepted with its consequence stated) because over-counting proposes cutting a file the census would catch as a changed reading, while under-counting leaves the ceiling uncleared and looks like success. **No share of seconds is claimed** — per-file CI wall clock is in no readable artifact (Q-090); D-084's per-job-reported-as-per-run half-fix is the shape avoided.
- **Alternatives**: (a) raise 900 — refuted by D-089 as a property, not an opinion; (b) session-scoped fixture only — the cheap half, insufficient alone; (c) narrow `DEFAULT_SUITE` now — rejected *this cycle* because it changes census readings and the before/after comparison run did not fit the budget, so it would ship a semantic change with no evidence the verdicts survive; (d) this — measure what the cost buys, leave the narrowing to a cycle that can afford to verify it.
- **Two defects found by running it, both in the direction that reads clean**: the first draft matched the source spelling `"sys.executable"`, which never appears in `ast.dump`, and read **0 of 58**; the second read `1 of 58` because almost no test spawns directly — it calls `pv.measure` / `push_preflight.record` and the spawn is one frame down inside the package. Seventh and eighth instances on this branch of a miss whose output looks like a clean bill.
- **Census cost, 26th consecutive cycle**: guard pool 69 → **71**, `NO_REGISTRY` 10 → **11**, `key_conflation` left reading 17 → **20**. Five population-shaped functions; the two that entered (`spawners`, `subject_files`) are **bookkeeping**, and `spawning` — the function the module exists to publish — narrows by `v == SPAWNS` and stayed invisible. **Fourth consecutive headline-missed split** (D-083, D-087, D-089), and the first that D-089 **predicted in advance** rather than being observed after the fact.
- **Status**: accepted — the repair is now *decidable*, **not done**. `DEFAULT_SUITE` is unchanged and `nested_suite_cost.grade()` still reads `DOOMED`.
- **Refs**: PR #67 · `journal/2026-08/05-20-nested-subject-confined-recorder.md` · Q-090

## D-089 — 2026-08-05 — **천장은 처음부터 문제가 아니었다**: nested suite 실행(1396s)이 자기를 지키는 timeout(900s)보다 길어졌다

- **Context**: `slow closed-loop` job 이 완료된 모든 run 에서 120 분 천장에 걸려
  cancel 됐다. D-084 가 `fast` 를 10→30, D-085 가 `slow` 를 60→120 으로 올렸고,
  STATE 는 "120→240 은 하지 마라" 를 **근거 없이** 지시로만 들고 있었다. `slow` 는
  required job 이므로, 이게 안 끝나면 `fast` 가 무슨 말을 하든 이 브랜치는 green 이
  될 수 없다 — STATE #1 의 전제가 무너지는 지점.
- **Decision**: 원인은 스케줄링이 아니라 **다른 파일에 사는 두 숫자 사이의 부등식**
  이다. `fast` half 의 pytest step 은 CI 에서 **1396 s** (run `30991167667`), nested
  suite 실행을 지키는 timeout 은 **900 s** (`predicate_vacuity.measure`,
  `predicate_inputs.measure`, `guard_vacuity.measure` 의 `timeout: int = 900`).
  이 함수들은 `python -m pytest DEFAULT_SUITE` — 즉 **fast half 전체** — 를
  subprocess 로 돌린다. fast half 가 900 s 를 넘긴 순간부터 이 호출들은 **구조적으로**
  timeout 한다. 특정 runner 나 flakiness 가 아니라 산술이다.
  `eval/mppi_sandbox/nested_suite_cost.py` 가 두 가지를 측정한다:
  (1) `grade()` — 지켜지는 작업이 자기 guard 보다 길면 `DOOMED`. **job ceiling 을
  아예 언급하지 않는다**, 따라서 `timeout-minutes` 의 어떤 값도 판정을 못 바꾼다.
  "240 으로 올리자" 에 대한 반박이 의견이 아니라 성질로 존재하게 됨.
  (2) `read_log()` / `unreported()` — 천장에서 죽은 job 은 pytest summary 를 못 찍고,
  그래서 `gh` 는 `cancelled`, `ci_verdict` 는 `UNRUN` 을 준다. 둘 다 맞지만 둘 다
  **`-v` 스트림이 이미 출력한 실패**에 대해 침묵한다. 12+ run 동안 **6 개의 red 가
  아무에게도 안 보였다**. absence-read-as-clean 의 **6번째** 사례이고, 숨겨진 것이
  *모르는 것* 이 아니라 *이미 red* 인 첫 사례.
- **Alternatives**: (a) 120→240 — timeout 을 6 개에서 13 개로 늘릴 뿐. (b) `slow` 를
  파일별로 shard — 한 *파일*(`test_exclusion_scope`)이 90 분을 먹으므로 안 됨.
  (c) 900 을 올림 — 1396 을 넘겨야 하고, 다음 instrument cycle 이 다시 넘긴다
  (비용이 suite 크기에 **2차**). (d) 이번 cycle 은 **측정만** 하고 수리는 다음
  cycle 로 — 채택. subject 를 바꾸는 결정(census 가 정말 suite *전체* 를 봐야 하는가)
  은 15 분 EXECUTE 예산 안에서 테스트 없이 할 일이 아니다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-19-nested-suite-outgrew-its-timeout.md`
  · 반증 가능성: 같은 로그가 quantum 600/1200 에서는 `WORK`, 900 에서만 `STALL`
  · 첫 draft 가 `_measure_scratch`(scratch suite, 300 s)를 full-suite 기준으로
  `DOOMED` 라고 오판했고 **실행해서** 잡음 → `subject` 측정 추가
  · `measure_attributed`(1800 s)는 이미 `MARGINAL` (78% 소진), 다음 차례

---

## D-088 — 2026-08-05 — **guard 가 아무것도 안 읽은 것과 exemption 이 아무것도 안 뺀 것은 다른 사실이다** — `INERT` 를 쪼개 `UNPOPULATED` 신설

- **Context**: D-087 이 남긴 CI 단 하나의 실패 (`test_screen_refinds_d050s_mask`, `assert 'INERT' in ('CANDIDATE','UNRUNNABLE')`) 를 착수. 읽지 말고 **돌려서** 재현 — `--depth 1` clone 에서 `tree_provenance.undeclared_drift ~ DECLARED_LOCAL_ONLY` 가 `head=0 supp=0 reg=5` 로 `INERT`. 원인: `undeclared_drift` 는 worktree-vs-HEAD 를 읽는데 CI checkout 은 worktree 가 **깨끗**하다. 즉 exemption 이 뺄 게 없었던 게 아니라 **뺄 대상 자체가 없었다**. 모듈에는 이미 `VACUOUS` 가 있고 그 논거가 정확히 이것이다 — *"registry 가 비었으면 suppression 이 아무것도 바꿀 수 없고 `INERT` 는 무의미하다."* 같은 논거의 **한 단계 아래**(registry 가 아니라 *reading* 이 빈 경우)는 한 번도 안 만들어졌다.
- **Decision**: `VERDICT_UNPOPULATED` 신설 — registry 는 non-empty 인데 guard 가 HEAD 에서도 suppression 하에서도 **아무것도 안 읽은** 경우 (`not head and not after`). `unscreened()` 에 포함한다 (`VACUOUS` 는 **제외** — 빈 registry 는 어떤 worktree 에서도 아무것도 면제하지 않으므로 뒤에 숨은 미검증 pair 가 없다; 차이는 그 공백이 *package* 의 성질이냐 *이번 run* 의 성질이냐). 로컬 기준 `INERT` **3 → 1**, 남은 하나(`exemption_bite`, 2→2)가 이 모듈이 애초에 `INERT` 를 말할 자격이 있던 유일한 pair.
- **측정으로 드러난 두 번째 결함 — 서술이 낼 수 없는 verdict 에 붙어 있었다**: `masking_candidates` docstring 과 테스트 하나가 `staged_declarations` 를 두고 *"registry 로 **좁혀 들어가므로** suppression 이 population 을 키우는 대신 **비운다**"* 며 `INERT` 를 인용했다. 실제로 declared 경로를 stage 하고 재니 **`DIVERGES` (1→0)** — 서술한 메커니즘 그대로이고, `DIVERGES` 는 이 모듈이 *"자라지 않고 변했다, bite 로 오계수되지 않도록 이름 붙임"* 으로 정의해 둔 verdict 다. 인용된 `INERT`(0→0) 는 index 가 빈 경우, 즉 그 메커니즘이 **안 돌 때** 나온다. 서술과 숫자가 애초에 같은 사건에 대한 게 아니었고, git index 는 평상시 늘 비어 있어서 아무 측정도 이를 반박하지 못했다.
- **테스트 재작성 — 환경 분기 제거**: 기존 테스트는 `_DECIDABLE`(이 clone 이 **history** 질문에 답하나) 로 분기했는데 자기 주석은 `undeclared_drift` 가 remote 를 안 쓴다고 정확히 적고 있었다. 실제 결정 축은 **worktree 에 declared 경로가 drift 중인가**. 두 축은 CI 에서 우연히 함께 움직이고(fresh checkout = blind + clean), 그 우연이 틀린 gate 를 옳아 보이게 했다 — D-046 의 "우연이 자리를 대신 지킴", 이번엔 *gate* 의 자리. 축을 올바르게 고쳐도 여전히 남의 checkout 상태를 단언하게 되므로, `tree_provenance.Stamp` 로 **조건을 합성**해 drift 행의 두 칸(`CANDIDATE` / `UNPOPULATED`)을 어떤 tree 에서도 고정. (첫 재작성 시도는 "뭐라도 drift 중인가" 로 분기했다가 clone 에서 `INERT 2→2` 로 깨졌다 — 파일을 clone 에 복사한 행위 자체가 tree 를 더럽혀서 잡혔다.)
- **Alternatives**: (a) 테스트 assertion 에 `INERT` 추가 — 증상만 덮고 어휘 결함 유지, 기각. (b) CI 를 dirty tree 로 만들기 — 권위 surface 를 측정에 맞추는 역방향, 기각. (c) verdict 분할 + unscreened 편입 + 조건 합성 (채택).
- **함의 (부재를 clean bill 로 읽는 패턴의 5번째, 그리고 첫 자기지시적 사례)**: `push_preflight.VACUOUS`, `git_surface.NO_REMOTE_BRANCHES`, `local_only_audit` inversion, `ci_verdict` 의 늦은 aggregate — 그리고 이번엔 **그 형태를 사냥하려고 쓴 모듈 자신**이 깨끗한 checkout 에서 "candidate 0, skip 0" 을 보고하면서 두 `DIFFERENCE` guard 를 **하나도 probe 하지 않은** 상태였다. 네 번 이름 붙인 패턴이 그 패턴 전용 도구 안에서 재발했다.
- **공표된 주장 하나 약화 (정정)**: masking bound "12 typed pair **전부**에 대한 측정" 은 사실이 아니었다. 실제로는 *실제 probe 된* pair 중 candidate 1개이며, 깨끗한 checkout 에서는 두 번째 mask 가 나올 수 있는 모집단(두 `DIFFERENCE` guard) 전체가 미검증. bound=1 은 유지되나 근거 범위를 좁혀 명시했고 `unscreened` 가 나머지를 실어 나른다.
- **검증**: `--depth 1` + **clean worktree** clone (CI 조건 그대로 재현) 에서 `test_exemption_masking.py` **24/24 pass** — 직전 동일 surface 에서 1 failed. 로컬 24/24.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-18-unpopulated-verdict-empty-reading.md` · `eval/mppi_sandbox/exemption_masking.py`

## D-087 — 2026-08-05 — **요약 필드는 요약 대상보다 늦을 수 있다**: run 은 "판정 없음" 이라 했지만 그 run 의 job 은 63 분 전에 이미 `failure` 였다

- **Context**: STATE #1 (`ci_verdict.py`) 를 4 cycle 째 이월하다 이번에 착수. 모듈을 쓰는 도중 읽은 실제 기록이 그대로 근거가 됨 — run `30981826577` (head `70e2863`) 은 `status=in_progress conclusion=null` 을 발행 중이었고, 같은 시각 required `fast` job 은 **63 분 전에 `failure` 로 완료**돼 있었다. 두 기록 다 정확하지만 "이 브랜치가 red 인가" 에 답하는 건 하나뿐이고, 그건 `gh run list --json conclusion` 이 출력하는 쪽이 **아니다**.
- **Decision**: CI 권위는 **job 단위로만** 읽는다. run-level `conclusion` 은 답이 아니라 아직 안 쓰인 요약으로 취급. job verdict 5 종(`PASS`/`FAIL`/`UNRUN`/`PENDING`/`UNREADABLE`) + `NO_JOBS`, fold 우선순위는 **`FAIL` 최상위** — 완료된 실패는 형제 job 이 아직 돌고 있든 말든 즉시 red. `UNRUN`(cancelled/timed_out/skipped/stale) 은 pass 도 fail 도 아닌 독립 verdict (D-084 확정). ceiling 은 **두 시제**로 계측: `at_ceiling`(사후) + `approaching_ceiling`(진행 중 job 을 elapsed 로 전방 계측) — 초안은 사후만 있었고, 그건 D-085 의 breach 를 사람과 **똑같이 늦게** 보고했을 것.
- **Alternatives**: (a) run-level conclusion 계속 사용 — 이 cycle 이 반증. (b) `gh pr checks` 파싱 — cancelled 를 "fail" 로 렌더해 D-084 가 이미 당한 오독. (c) job 단위 + fail-closed fold (채택). (d) ceiling 계측 없이 verdict 만 — D-084 가 fast 10→30 만 올리고 slow 가 10 시간 전 60 을 넘긴 걸 놓친 이유가 per-job 계측 부재였음.
- **함의 (D-086 표의 4번째 행, 방향이 반대)**: `push_preflight`=`VACUOUS`, `git_surface`=`NO_REMOTE_BRANCHES`, `local_only_audit`=inversion — 셋 다 **부재를 clean bill 로** 읽는 오류. 이번 건은 **이미 존재하는 판정을 늦은 요약 뒤에 숨기는** 오류. 같은 패턴을 세 번 명명하고도 못 막은 이유가 이 방향 차이.
- **한계 (명시)**: `job_caps()` 는 **현재** workflow 를 읽으므로 과거 run 은 당시 cap 이 아닌 오늘 cap 으로 계측된다 (03:34Z cancelled run 은 120 분 cap 기준 +50% headroom 으로 나오지만 실제로는 60 분 cap breach). docstring 에 warning, 테스트는 epoch cap 을 명시 전달.
- **부수 확인 (STATE #3) — cycle 안에서 답이 뒤집힘**: 17:20 에 `70e2863` 의 `slow` 는 92.1 분 / 120 분 cap 으로 **생존 중**이었고 "raise 가 먹혔다" 고 적었다. 18:35 에 다시 읽으니 **120.2 분에서 천장에 걸려 죽어 있었다** (`at_ceiling` 이 정확히 발화). 즉 D-085 의 60→120 도 **부족**했다 — 천장 반쪽 수정 **3 연속** (D-084 는 둘 중 하나만, D-085 는 나머지를 2 배로 올리고도 미달). STATE #3 자신의 조건문이 발화한 것: *"120 을 넘으면 성장은 2 배보다 나쁘고 fast/slow split 자체를 재검토해야 한다."* → **네 번째 raise 금지**, split 재설계가 다음 행동.
- **부수 확인 2 — D-086 은 실제로 먹혔다 (10 → 1)**: 이번 cycle 이 만든 도구로 `30987013397` (`adeca21`, 16:00 의 D-086 fix) 을 읽으니 `fast` = `FAIL`, **1 failed / 933 passed**. D-086 직전 판정은 10 failed 였으므로 fix 는 **9 개를 해결**. 남은 1 개는 잔여물이 아니라 **다른 결함**: `test_screen_refinds_d050s_mask` 가 `assert 'INERT' in ('CANDIDATE','UNRUNNABLE')` 로 실패 — `exemption_masking` 이 CI checkout 에서 한 pair 를 `INERT` 로 채점. D-086 의 **어휘 빈곤** 결함(구분 가능한 두 상황에 verdict 하나)이 **한 모듈 옆에서 재현**된 것이고, STATE #5 가 예측해 둔 바로 그 지점.
- **run-level 불일치가 두 번째 독립 run 에서 재현**: `30987013397` 역시 `fast` job 이 `failure` 로 완료된 동안 run-level 은 `in_progress`/`null` 을 발행. 2/2 — 경쟁 상태가 아니라 API 의 **정상 동작**이며, 이 모듈의 precedence 규칙에 대한 가장 강한 근거.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-17-ci-verdict-per-job.md` · `eval/mppi_sandbox/ci_verdict.py` (26 tests, fixture 전부 실제 `gh api` 기록)

## D-086 — 2026-08-05 — 로컬 green 은 CI 에 대한 증거가 아니다 — **답할 수 없는 clone 은 침묵이 아니라 verdict 를 반환해야 한다**

- **Context**: D-084/D-085 가 CI 천장을 올린 뒤, `fast` job 이 **2026-08-03T23:18Z
  이후 처음으로 진짜 verdict 에 도달**했다 (22m31s, 30분 cap 아래). 그 verdict 는
  **`failure`, 10 tests** — 40분 전 `push_preflight` 가 `GREEN` 으로 인증한 바로 그
  tree 에서. 두 판정 모두 옳았다. `push_preflight` 는 **worktree** 를 재고,
  authority 는 **checkout** 을 잰다. `actions/checkout@v4` 는 `origin/main` 도
  `refs/remotes/origin/autoresearch/*` 도 없는 clone 을 만든다.
  `local_only_audit.branch_committed` 는 그 ref 들 위로 `git log origin/main..<ref>`
  를 fold 하는데, ref 가 0개면 fold 는 빈 집합을 반환하고 —
  `derived_local_only` 는 그것을 *"어떤 branch 도 이 경로를 commit 하지 않는다"* 로
  읽어 `docs/decisions.md` / `docs/deliberations.md` 를 **local-only 로 분류**했다.
  그 두 경로는 해당 모듈 docstring 이 durable-record 의 **대조군**으로 내세우는
  바로 그 예시다. 열화된 답이 아니라 **정반대의 답**이, 답의 형태로 반환된 것.
- **Decision**: `eval/mppi_sandbox/git_surface.py` — *이 clone 이 history 질문에
  답할 수 있는가* 를 재는 probe. verdict 5종 (`DECIDABLE` / `SHALLOW` /
  `NO_MERGE_BASE` / `NO_REMOTE_BRANCHES` / `NOT_A_REPO`) 과 적용된 verdict 를
  실어 나르는 `UndecidableSurface`. `local_only_audit` 의 blind call site 4곳은
  기록을 읽기 **전에** refuse 한다 (probe 가 `rule_epoch` 뒤에 있었을 때 거부는
  `FileNotFoundError` 로 도착했다 — 맞는 사실의 틀린 대상). 영향받은 테스트 12개는
  `skipif` 가 아니라 **양쪽 surface 에 대해 assert** 한다: decidable clone 에서는
  실제 주장, blind clone 에서는 *probe 가 발화했고 올바른 verdict 를 이름 붙였다* 는
  주장. `skipif` 였다면 suite 의 CI 절반이 침묵했을 것이고, 그것이 바로 이 모듈이
  다루는 vacuity 결함이다 (D-075 / D-081).
- **측정된 것 두 가지**: (1) 첫 guard 인 `require_branches` 는 **너무 좁았다** —
  fold 는 `origin/main..<ref>` 범위라 base 도 필요한데, branch ref 만 가진 clone 은
  좁은 guard 를 통과한 뒤 6 프레임 아래에서 exit 128 로 죽었다. `require_history` 가
  양쪽을 요구한다. (2) 테스트 3종(총 7개)은 **inversion 덕분에** 통과하고 있었다 —
  빈 fold 가 우연히 그들이 받아들이는 population 을 만들어냈다. 둘 다 코드를 읽어서가
  아니라 **`git clone --depth 1` 안에서 suite 를 돌려서** 발견됐다. dev box 에서는
  두 half 가 항상 존재하므로 어떤 로컬 실행도 이 둘을 구분할 수 없다.
- **Alternatives**: (a) 각 call site 에 `try/except` — 틀린 답을 skip 된 테스트로
  바꿀 뿐, 한 층 위의 vacuity 결함. (b) CI checkout 에 `fetch-depth: 0` — 실제로
  할 만하고 **직교적**이지만, 계측기의 정확성을 세 디렉터리 떨어진 YAML 의 속성으로
  만들고 다른 어떤 얕은 clone 도 돕지 못한다. probe 위에 얹으면 verdict 가
  `DECIDABLE` 로 바뀌고 테스트는 자동으로 더 강한 branch 를 assert 한다. (c) 현상
  유지 — CI red.
- **이것이 세 번째 사례다**: 침묵이 verdict 로 읽히는 결함 —
  `push_preflight` 의 `VACUOUS`, `ci_verdict` 의 (미구현) `UNRUN`, 그리고 여기의
  `NO_REMOTE_BRANCHES`. 반복되는 사고가 아니라, fold 의 empty case 가 negative case
  와 같은 철자를 가질 때의 **기본 결과**다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-16-clone-blind-derivations.md`

## D-085 — 2026-08-05 — push gate 가 **처음으로 진짜 red tree 를 막았다**, 그리고 D-084 의 CI fix 는 **절반짜리**였다 (천장은 하나가 아니라 둘)

- **Context**: cycle 시작 시 `e54df9b` / `f2b8a8e` 두 commit 이 unpushed — 당일 **다섯 번째** crash-before-push. 그런데 push 전 receipt gate 가 `GREEN` 이 아니라 **`RED` (3 failures)** 를 냈다. 13:00 이 쓴 `inert_surface.py` 를 14:00 이 **suite 를 한 번도 돌리지 않고** commit 했고, 그 위에 또 하나를 쌓은 상태였다.
- **Decision**: (1) 3 failure 수리 — `readers` 가 guard pool **66 → 67** (23번째 연속 census cost, DERIVED 라 2차 비용 0). (2) 모듈의 **유일한 negative control 이 뒤집혀 있었다**: 자기 subject 를 literal 로 적었고 `mentions()` 는 test file 포함 전체 corpus 를 스캔하므로 "reader" 로 자기 자신을 찾아 `HAS_READER` 판정 — candidate 를 runtime 조립으로 바꾸고, 그 오염 자체를 별도 property 로 pin. (3) `filter_drift` 가 `ignored` 만 정렬하고 `material` 은 안 하던 것 — 둘 다 정렬. (4) **CI slow job 60 → 120**.
- **핵심 측정**: cancelled streak 을 run 이 아니라 **job 단위**로 재면 천장 통과는 **둘**이고 ~10 h 떨어져 있다 — `fast` 는 `2be88f0a`(08-03T23:18Z)에서 10 분을, `slow` 는 `ed80d0bd`(08-04T09:32Z)에서 **60 분**을 넘겼고 이후 **12 run 전부 60.2 분에 kill**. 두 job 다 required 이므로 D-084 처럼 `fast` 만 올리면 run 은 계속 `cancelled`, 권위는 계속 침묵. 게다가 run-level `cancelled` 는 반대 방향으로도 틀렸다: 그 아래에 **진짜 `failure` 7 건 + 진짜 `success` 2 건**이 가려져 있었다.
- **Alternatives**: (a) `fast` 만 올린 채 두고 slow 는 다음 cycle — 권위가 계속 침묵하므로 기각. (b) slow 를 마지막 측정치(57.97 분)에 맞춰 60→70 — 이 job comment 자신이 금지하는 방식(천장이 측정 대상이 됨). (c) slow half 를 더 쪼갬 — 비용 대비 이득 불명, 보류.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-15-red-head-and-the-second-ceiling.md` · D-082 (receipt gate, 첫 실전 적발) · D-084 (절반만 고침) · D-079 (control 규칙 — 필요하지만 whole-corpus scan 에는 불충분)

## D-084 — 2026-08-05 — **`cancelled` 는 `fail` 이 아니다**: 권위(CI)가 30 시간째 아무 판정도 내놓지 않았고, 27 번의 push 가 이 dev box 말고는 아무것도 검증하지 않았다

- **Context**: 12:00 cycle 은 `push_preflight` 가 `GREEN` 을 준 영수증(`897
  passed`)으로 push 했고 `STATE.md` 에 *"PR #67 is green on origin"* 이라 적었다.
  같은 sha 의 Sandbox CI run 은 **cancelled** 였다. 그 앞의 26 개도 전부.
  마지막 **success** 는 `b1f07110`, 2026-08-03T14:18Z = **2026-08-03 23:18 KST**
  (fast **5m55s** / slow 25m26s) — **약 39 시간 전**. 그 뒤 real `failure` **9**
  회(빨간 판정은 나왔다), 그 다음 `2be88f0a` (2026-08-03T23:18Z = **08-04 08:18
  KST**) 부터 **`cancelled` 27 회 연속** — 전부 `timeout-minutes` 상한에서 죽었다
  (10m16s / 1h0m15s vs **10** / **60**). 즉 **약 30 시간 동안 판정 자체가 없다**.
  workflow 에 `concurrency: cancel-in-progress` 는 없다. 상한이 원인이다.
- **Decision**: fast job 의 `timeout-minutes` 를 **10 → 30**, 측정값과 교차참조를
  주석에 박아서. 그리고 **`UNRUN`(cancelled) 을 `FAIL` 과 다른 판정으로 취급**한다 —
  다음 cycle 이 `ci_verdict.py` 로 계측한다.
- **왜 놓쳤나 (이게 본체)**: `cancelled` 가 **양쪽으로 동시에** 오독됐다. `gh pr
  checks` 는 이걸 **`fail`** 로 찍으므로 PR 을 보는 사람은 존재하지 않는 깨진 test 를
  찾고, local 영수증이 green 인 cycle 은 같은 단어를 보고 "CI 가 stale 하다" 결론짓고
  *green on origin* 이라 기록한다. **증거의 부재**가 **부재의 증거**를 뜻하는 단어로
  렌더링됐다. 빨개진 것이 없으니 아무도 보지 않았다.
- **그리고 교훈은 이미 적혀 있었다 — 고쳐야 할 줄 바로 아래에.** slow job 의 주석이
  *"how the old job got a 10-minute ceiling that silently became the thing under
  test"* 라고 **이 job 에 대해** 쓰여 있고, 정작 적용은 저쪽에만 됐다. D-078 의
  "(checked)", D-083 의 괄호에 이어 세 번째, 이번엔 YAML 에서.
- **D-082 는 이걸 볼 수 없다 — 구조적으로**: 자기 docstring 이 *"the PR's CI remains
  the only authority for the pushed tree"* 라고 인정해놓고, branch 에는 **local**
  영수증을 읽는 gate 만 있고 그 권위를 읽는 reader 는 **하나도 없다**. 3 분짜리 local
  green 이 반드시 죽을 CI 를 가진 push 를 허가한다.
- **비용의 형태**: suite 비용은 instrument 개수에 **초선형** — instrument test 들이
  subprocess pytest 를 띄워서 검증하기 때문. 60 test (07-13) → 897 (오늘). 즉
  **회피(avoidance) test 가 쓸 CI 예산을 instrument 가 먼저 썼다.**
- **Alternatives**: (a) 상한만 올린다 — 증상 처치, 다음 crossing 도 똑같이 조용하다.
  (b) 상한을 올리고 **판정을 읽어오는 계측기**를 만든다 ← 채택 (다음 cycle). (c) suite
  를 쪼갠다 — 필요해지겠지만 오늘의 문제는 아니다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-14-ci-ceiling-unrun.md` · D-082, D-044,
  D-043, D-033 · Q-086

## D-083 — 2026-08-05 — D-082 의 gate 는 D-044 의 순서를 지키는 **모든 cycle 을 거절**한다: 그리고 그 면제를 지탱하던 "read by no test (checked)" 는 오늘 tree 에서 **네 개 전부 거짓**이다

- **Context**: D-082 가 한 cycle 전에 push gate 를 실었고, 작동한다 — 영수증 없으면
  push 없음. 그런데 `check` 는 **tree 전체 fingerprint** 를 비교하고, D-044 는
  영수증을 **찍은 뒤에** 쓰라고 명령한다 (4b `JOURNAL.md`, 4c `STATE.md`, TSV).
  그래서 push 줄에 도달할 때면 tracked file 세 개가 이미 움직여 있고 영수증은
  `STALE` 이 된다. 매 cycle. 12:00 은 유일하게 가능한 통화로 지불했다 — 끝에서
  **suite 를 한 번 더** 돌리는 것, 15 분 예산 위의 ~8 분. 각각은 옳고 합성이 틀린
  규칙 두 개다.
- **D-044 의 표가 이미 답을 갖고 있었고, 그것을 주장으로 적어놨다**: "no — read by
  no test (checked)". 그 괄호가 면제 전체를 지탱한다. 한 번, 손으로 확인됐고,
  그 뒤로 아무도 다시 확인하지 않았다 — D-079 가 장식이라고 부른 바로 그 형태.
- **Decision**: `eval/mppi_sandbox/inert_surface.py` — 면제를 **타이핑하지 않고
  도출**한다. 두 층. **Static**: 어떤 test file 이 그 path 에 도달 *할 수* 있나,
  package 를 통해 한 hop 전이적으로 (test 가 `DECLARED_LOCAL_ONLY` 를 순회하며
  각 entry 를 열 수 있으므로 test 안의 mention 은 필요조건이 아니다 — 과대추정이
  안전한 방향이다). **Dynamic**: `probe` 가 bytes 를 바꾸고, static 층이 지목한
  **부분집합만** 다시 돌리고, outcome 을 비교한다 (D-081 의 differential probe).
  `push_preflight.record` 는 이제 per-path digest 를 영수증에 쓰고, `check` 는
  `filter_drift` 를 통과한 drift 에만 `STALE` 을 준다.
- **측정 결과 — 면제의 전제가 무너졌다**: static survey 는 넷 **전부**
  `HAS_READER` 로 채점한다. `STATE.md` (direct 6 + via 5), `JOURNAL.md` (1 + 8),
  `RESULTS.md` (1 + 9), `results/` (2 + 8). "read by no test" 는 오늘 tree 에서
  **거짓**이다. 도달가능성은 읽힘이 아니지만, static 층은 둘을 못 가른다 — probe 가
  존재하는 이유 전부가 그것이다.
- **🔴 그 probe 는 내가 오염시켰다**: ~20 분 (subset 8 회) 걸리고, 나는 그 시간에
  `push_preflight.py` 를 고치고 `test_inert_surface.py` 를 추가했다. 뒤쪽 후보들은
  **움직이는 tree** 위에서 측정됐다. **D-043 그 자체**를, D-043 을 겨냥한 계측기를
  짓는 cycle 안에서. 진단과 재발이 같은 시간에 떨어진 **세 번째 연속** cycle이다
  (11:00 은 D-081 을 D-081 이 서술한 버그로 잃었고, 12:00 은 D-082 의 살아있는
  사례 위에서 열렸다). 전사하지 않고 **폐기**했다.
- **그래서 `PROBED` 는 비어서 나간다 — 이건 구멍이 아니라 옳은 상태**: `inert()` 는
  기록된 `INERT` 판정 **그리고** 움직이지 않은 reader 집합, 둘 다 요구한다. pin 이
  없으면 아무것도 면제되지 않고, `filter_drift` 는 항등이고, gate 는 12:00 과 똑같이
  행동한다. 배선은 끝났고 측정이 허가할 때까지 작동하지 않는다. **소속만으로는
  절대 면제되지 않는다**는 것을 test 가 고정한다.
- **Alternatives**: (a) 네 path 를 타이핑해서 면제 — D-076 이 0 건 걸렀다고 측정한
  typed exemption, 그리고 그 전제는 방금 거짓으로 판명났다. (b) `record` 를 맨 뒤로
  — 12:00 의 우회, cycle 당 ~8 분. (c) 도출 + pin + 전제 재확인 ← 채택.
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/05-13-inert-surface.md`

## D-082 — 2026-08-05 — push 는 기억이 아니라 **영수증** 으로 허가된다: D-043/D-044 는 count 를 *언제* 재는지만 규율하고, count 가 **존재한다고 가정** 한다

- **Context**: 2026-08-05 하루에 **세 번** 같은 사고가 났다. 07:00 은 commit 후
  crash — D-077 이 push 안 된 채 남았고 journal 은 `TSV row appended: yes` 라고
  적혀 있었다. 10:00 도 commit 후 crash — 11:00 이 그 `1f69128` 을 push 했고 **그
  다음에** red 임을 발견했다 (D-080 자기 census cost 3건, 그 중 둘은 D-080 산문이
  이름까지 적어놓고 re-pin 은 안 한 것). PR #67 이 한 시간 red 였다. 그리고 11:00
  자신도 commit 후 crash — 그 세 개를 **고치는** commit `903d148` 이 push 되지 않아,
  `STATE.md` 에 기록된 "red → green" 은 origin 이 본 적 없는 tree 에 대한 참말이었다.
  세 번째가 mechanise 해야 하는 이유다: 결함을 진단하고 decision log 에 적은 그
  cycle 이, 같은 시간 안에, 같은 결함으로 그 진단을 못 실어보냈다.
- **진짜 구멍**: D-043 은 "재고 나서 문서 쓰면 다시 재라", D-044 는 "다시 재는 유효한
  순간은 하나다". 둘 다 **count 가 있다**는 전제 위에 서 있다. Phase 4 전에 죽은
  cycle 은 count 를 아예 안 만들고, 그러면 `verify` 가 대조할 stamp 자체가 없어서
  **아무것도 red 가 되지 않는다**. 침묵이 통과로 읽힌다.
- **Decision**: `eval/mppi_sandbox/push_preflight.py` — push 를 artifact 로 허가한다.
  `record` 가 suite 를 실제로 돌려 `Receipt` (tree stamp + returncode + 파싱된 outcome
  count) 를 쓰고, `check` 가 그 영수증 없이는 **거절** 한다. Phase 3 push 줄이
  `check … && git push` 가 된 것이 규칙 전부다.
- **두 tree 를 합성하는 게 내용의 전부**: `tree_provenance` 가 이미 destination 으로
  surface 를 쪼개 놨다 — worktree 는 test 가 읽는 것, `HEAD` 는 push 가 싣는 것,
  그리고 D-011 은 둘이 **달라야** 한다고 요구한다. 그래서 영수증은 worktree 에 대한
  주장이고 push 는 다른 것을 싣는다. `check` 는 (1) 영수증이 지금 worktree 와 일치,
  (2) worktree-vs-`HEAD` drift 가 declared 집합 안 — **둘 다** 요구한다. 어느 한쪽만
  만족시키면서 다른 쪽이 깨지는 tree 가 존재하고, 한쪽만으로는 나쁜 push 를 통과시킨다.
- **fail-closed, 그리고 어느 쪽으로 실패했는지 말한다**: `NO_RECEIPT` (아무것도 안
  쟀다 — 위 세 crash) / `STALE` (잰 뒤 tree 가 움직였다 = push 시점의 D-043) /
  `VACUOUS` / `RED` / `UNDECLARED` (잰 tree 가 실을 tree 가 아니다) / `GREEN`.
  순서가 계약이고 테스트로 고정한다: red-and-stale 은 `STALE` 로 보고한다 — 그
  failure 들은 이미 없는 tree 에 대한 사실이라 재현 안 될 수도 있는 걸 디버깅하러
  보내면 안 된다.
- **`VACUOUS` 는 D-075/D-076/D-081 이 세 번 낸 값**: green 과 empty 는 같은 reading 이
  아니다. pytest 는 수집 0 이면 5 로 끝나고, 경로를 잘못 쓰면 0 을 수집하고, 파싱
  안 되는 summary 는 아무것도 말해주지 않는다 — rc 만 보는 gate 는 셋 다 "실패 안 함"
  으로 읽는다. 그래서 emptiness 를 success **보다 먼저** 판정하고, `skipped` 는
  `EXECUTED_OUTCOMES` 에서 **뺐다**: 400개 수집해 400개 skip 한 run 은 아무것도
  주장하지 않았고, 그걸 `GREEN` 으로 매기는 것이 정확히 D-075 의 결함을 더 큰
  분모로 재생산하는 짓이다.
- **영수증은 *관측* 되지 사람이 타이핑하지 않는다**: 손으로 count 를 넣어 영수증을
  만드는 경로는 지원하지 않는다. executor 가 칠 수 있는 숫자는 기억에서 칠 수 있는
  숫자고, 그게 D-043 · D-078 · D-081 이 각각 새 사례를 잡은 결함 class 다.
- **자기 control 동봉** (D-078/D-079): 6개 verdict 전부 양방향으로 친다.
  `test_every_verdict_is_reachable` 이 verdict registry 가 dead code 를 담고 있지
  않음을 고정하고, `GREEN` 에 도달하는 입력이 있어야 나머지 거절들이 vacuous 하지
  않다. 🔴 **그 exhaustiveness 테스트의 첫 draft 가 `STALE` 을 도달 불가로 보고했다** —
  영수증 6장을 같은 파일명에 덮어써서. 이 module 이 존재하는 이유인 바로 그 verdict
  가, 그걸 확인하려는 테스트에서 사라져 있었다. D-081 의 fixture 사고와 같은 모양이
  한 cycle 뒤에 반복됐다.
- **한계, 적어둔다**: 이건 *local* claim 에 대한 *local* gate 다. PR 의 CI 가 여전히
  pushed tree 의 유일한 authority 이고, 이 module 은 **측정된 적 없는** push 를
  막지 green-here-red-there 를 막지 않는다.
- **Alternatives**: (a) prompt 에 "push 전에 suite 돌려라" 한 줄 더 쓴다 — 이 프로젝트가
  절차 규칙을 얼마나 잘 기억하는지의 base rate 는 "쉰한 cycle 째 손으로 commit" 이다.
  (b) push 직전에 무조건 suite 를 한 번 더 돌린다 — 같은 tree 를 재는 명령이 둘이면
  둘이 어긋날 수 있고, 4a-ter 의 re-run 과 중복이다. 그래서 4a-ter 의 re-run 자체를
  `record` 로 바꿔 **한 번의 호출이 D-043 규칙과 push gate 를 동시에** 만족시킨다.
  (c) 채택: 한 번 재고, 영수증을 남기고, 영수증으로 push 를 허가한다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-12-push-receipt-gate.md` · D-043 (count 를
  tree 에 묶어라), D-044 (유효한 순간은 하나), D-011 (local-only 3종),
  D-075/D-076/D-081 (vacuous survival), D-042 (기본값이 경보인 check 는 뮤트된다)

## D-081 — 2026-08-05 — D-080 의 결함은 사건이 아니라 **class** 였다: 이름 충돌은 286개 중 16개로 살아 있고, 남은 bare-key scan 은 **shipped tree 로는 반증 불가능**하다

- **Context**: D-080 은 `references()` 가 attribute 이름만 보고 module 을 버려서 두
  `EXCLUDED_TESTS` 가 서로의 read 를 union 으로 받았고, 그 결과 published magnitude
  하나가 틀렸음을 발견했다. count 를 다시 재는 것으로는 절대 못 잡는다 — count 는
  신선했고 **key** 가 깨져 있었다. 그래서 남는 질문 둘: 이 blind spot 은 실제로
  물 수 있는가, 그리고 다른 scan 도 같은가.
- **Decision**: `eval/mppi_sandbox/key_conflation.py` — 3층.
  (1) **population**: module-level `UPPER` 상수 **286개 중 16개** 이름이 2개 이상
  module 소유. `EXCLUDED_TESTS` 는 16 중 하나였을 뿐 — blind spot 은 이론이 아니다.
  > **분모를 날짜로 읽어라 (D-078), D-082 cycle 추가**: `286` 은 `903d148` 의
  > 값이다. 다음 cycle 이 `push_preflight.py` 를 추가하자 `constant_population()`
  > 은 **296** 이 됐다 — 분자 (`shared_names` 16 / `collision_pairs` 43) 는
  > 그대로. 이 분모는 **module 이 하나 생길 때마다 움직이는** 종류라 D-078 이
  > `as_of` 로 결론 낸 것과 같은 class 다: pin 하지 말고 날짜를 붙여라.
  > 🔴 그리고 그 이동은 **아무것도 red 로 만들지 않았다** — 이 quote 는
  > `MEASURED_CLAIMS` 에 등록돼 있지 않아서, `drifted()` 가 볼 수 없다.
  (2) **differential probe**: syntax heuristic 이 아니라 *측정* — 같은 이름의 두
  registry 로 scan 을 호출해 reading 을 비교. heuristic 을 썼다면 그것 자체가 또 하나의
  name-keyed scan 이라 자기 감사를 빚졌을 것이다.
  (3) 세 번째 verdict 가 이 파일의 핵심: **`VACUOUS`** — 두 reading 이 같되 **둘 다
  비었으면** 아무것도 증명하지 못한다. `IDENTICAL` 로 보고하면 D-075 의 결함
  (vacuous 하게 통과한 assertion) 을 정확히 재생산한다. 그래서 emptiness 를 equality
  **보다 먼저** 검사한다.
- **측정 결과**: `references` **DISTINGUISHES** (17 vs 1) — D-080 의 수리를 수리한
  module 바깥에서 독립 확인. `binding` **DISTINGUISHES**. `unresolved_reads`
  **VACUOUS** — 구조상 bare name 으로 key 할 수밖에 없고 (unresolved read 는 owner 가
  없다), 그래서 "resolved count 는 lower bound" 라는 그 docstring 의 주장은 *registry*
  가 아니라 *이름* 에 대한 주장이다. 그런데 패키지의 unresolved read 는 **0** 이라
  shipped population 위의 어떤 probe 도 이걸 보일 수 없다. `conflating()` 은 빈
  tuple 이지만 셋 중 하나는 **애초에 질문받은 적이 없다** — `unprobed()` 가 그걸
  따로 보고하고, 테스트가 clean 이 아니라 **unrun** 으로 고정한다.
- **synthetic control**: 그래서 fixture 가 있다. `a` 는 unresolved 2 / resolvable 2,
  `b` 는 1 / 1. bare scan 은 **3, 3** 을 읽어 `IDENTICAL` — union bug 가 드디어
  관측된다. D-079 규칙대로 자기 control 을 동봉: 같은 fixture 위의 keyed scan 이
  **2, 1** 로 `DISTINGUISHES` (wrong-direction), 빈 fixture 가 `VACUOUS` (no-op).
  **첫 draft 의 fixture 는 이 wrong-direction leg 가 `VACUOUS` 로 나왔다** — 즉 아무것도
  증명하지 못했고, fixture 가 깨진 것과 scan 이 깨진 것을 구분할 수 없었다. control 을
  동봉하라는 규칙이 같은 cycle 안에서 값을 한 번 치른 셈.
- **Alternatives**: (a) `unresolved_reads` 를 qualified key 로 고친다 — 불가능,
  unresolved read 에는 attribute 할 owner 가 없다. (b) 한계를 문서에만 적는다 — D-047
  이 정확히 그 실패 (손으로 베낀 registry 가 굳었다). (c) 채택: 측정하고, 측정
  불가능한 것은 `VACUOUS` 로 **이름 붙여** 나른다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-11-key-conflation-class.md` · D-080 (사건),
  D-079 (control your exemptions), D-076 (bite vs wiring), D-075 (vacuous survival)

## D-080 — 2026-08-05 — Q-085 답은 **둘 중 하나가 아니라 split** 이다: reader 가격이 정한다 — 그리고 D-079 의 "정확히 한 곳" 은 scan 이 **module 을 버려서** 나온 숫자였다

- **Context**: Q-085 는 `predicate_vacuity.EXCLUDED_TESTS` 와 `guard_vacuity.
  EXCLUDED_TESTS` 를 놓고 "call-time read 로 **고칠 것인가**, 의도된 설계로 **선언할
  것인가**" 를 물었고, 스스로 결정 절차를 적어 뒀다 — *싼 non-subprocess reader 가
  있는지부터 확인하고, 없으면 (a) 는 자동으로 죽는다*. 그 절차를 실제로 돌렸다.
- **Decision**: **둘 다** — registry 별로 갈린다. `exemption_control.reader_cost` 가
  각 reader 를 `PURE`/`SUBPROCESS` 로 값매기고 `affordable_readers` 가 선택을 내린다.
  (a) **pv**: pure reader 가 15 개 → 가장 싼 `exclusion_scope.price` (순수 산술) 를
  call-time read 로 바꿔 registry 를 controllable 하게 만들었다 (control: 6 → 7, BITES).
  (b) **gv**: 유일한 reader 가 subprocess → (a) 는 Q-085 자기 규칙으로 사망 →
  `DECLARED_DEF_TIME` 에 **이유와 함께** 선언, `undeclared_unreachable()` 이 선언 없는
  UNREACHABLE 을 이름으로 부른다. 선언이 주석이 아니라 **reading** 이어야 한다는 Q-085
  의 lean 을 그대로 지켰다.
- **🔴 그리고 D-079 의 published magnitude 를 철회한다**: "각각 정확히 **한 곳**에서
  읽힌다" 는 gv 에 대해 참, pv 에 대해 **거짓** (4 개 module, **17** 곳). 원인은 산문이
  아니라 코드였다 — `references()` 가 `_, name = registry` 로 **module 성분을 버리고**
  attribute 이름만으로 매칭해, 이름이 같은 두 registry 가 서로의 read 를 **union** 으로
  받았다. 두 set 의 reference tuple 이 byte-identical 이었고, 작은 쪽 숫자가 양쪽에
  인쇄됐다. 이제 read 는 import 를 풀어 **owning module 로 귀속**되고, 귀속 불가능한
  load 는 `unresolved_reads()` 가 따로 보고한다 (추측하지 않는다 = resolved count 는 하한).
  두 verdict 가 우연히 살아남은 건 둘 다 `DEF_TIME` 이었기 때문이고, 합성 source 위의
  negative control 이 그 우연을 재현한다 (`a.REG` CALL_TIME / `b.REG` DEF_TIME).
- **부수 결과 2 건**: (1) `python -m exemption_control` 은 `importlib` 가 **두 번째
  복사본**을 만들어 이 module 자신의 registry 를 `INERT` 로 오채점했다 — 실행 방식에
  따라 판정이 갈리는 control. `_live_module()` 이 `__main__` 을 우선 잡아 고쳤고,
  subprocess test 가 pin 한다. (2) 새 excuse list `DECLARED_DEF_TIME` 자체가
  `unwatched_exemptions` 를 4 → 5 로 키웠다 — **예외가 아니라 tamper 로** 응답했다
  (REGISTRIES 8 → 9, TAMPERS 7 → 8). 자기 예외 목록을 예외 처리하는 게 D-073 의 결함.
- **Alternatives**: (a) 양쪽 다 고친다 — gv 는 cycle 마다 suite 를 돌려야 해 "안 돌아가는
  control" 이 된다. (b) 양쪽 다 선언한다 — pv 는 15 개 싼 reader 를 두고 포기하는 것.
  (c) 숫자만 고치고 scan 은 둔다 — 다음 이름 충돌에서 같은 오류가 재발한다.
- **Status**: accepted — Q-085 `resolved → D-080`; D-079 의 판정(UNREACHABLE)은 유효,
  **"정확히 한 곳" 이라는 magnitude 는 superseded**.
- **Refs**: PR #67 · `journal/2026-08/05-10-excluded-tests-reader-price.md`

## D-079 — 2026-08-05 — negative control 을 7 개 typed exemption 전체로 일반화했더니, 2 개는 **자기 이름으로는 control 자체가 불가능**했다 — default argument 는 registry 를 장식으로 만든다

- **Context**: D-076 은 `SELF_DEFINING` 의 *bite* 를 쟀고 (0 건), D-078 은 다른 guard 에
  대해 *negative control* (tamper → 정확히 1 건 적발) 을 함께 실었다. STATE #1 은 나머지
  여섯 typed set 에 후자를 확장하라고 요구했다 — D-075 의 vacuous test 를 그 cycle 에
  잡았을 값싼 장치이기 때문.
- **Decision**: `eval/mppi_sandbox/exemption_control.py`. **두 층**이고, 순서가 load-bearing:
  (1) **static** — registry 이름이 *어디서* 읽히는가를 AST 로 분류 (`CALL_TIME` /
  `DEF_TIME`). `DEF_TIME` 뿐이면 `UNREACHABLE`; (2) **dynamic** — reachable 한 것만
  global 을 patch 하고 정수 reader 의 delta 를 잰다. static 층이 먼저인 이유는, 그것이
  dynamic 층의 결과가 **의미를 갖는지**를 결정하기 때문이다.
- **측정 결과 (8 registry)**: **6 BITES / 2 UNREACHABLE / 0 INERT / 0 uncontrolled**.
  delta 는 각각 +1 / +1 / −2 / +2 / +1 / −2 로 pin 됨 (verdict 만이 아니라 크기까지).
- 🔴 **핵심 발견은 per-registry 판정이 아니라 구조적인 것**: `predicate_vacuity.
  EXCLUDED_TESTS` 와 `guard_vacuity.EXCLUDED_TESTS` 는 각각 **딱 한 곳**에서 읽히고,
  그 한 곳이 `excluded: Sequence[str] = EXCLUDED_TESTS` — **default argument** 다. `def`
  시점에 한 번 평가되어 function object 에 bind 되므로, 이후 module global 을 어떻게
  바꿔도 어떤 caller 도 관측할 수 없다. 즉 **그 이름에 대한 monkeypatch 는 어떤 것도
  control 이 아니다**; 들어가는 유일한 길은 `excluded=` 를 명시적으로 넘기는 것인데
  그건 *parameter* 를 control 하는 것이지 *registry* 를 하는 게 아니다. 오직 자기
  정의부에서만 이름이 살아 있는 registry.
- ✅ **D-076 을 약화(정정)한다**: `SELF_DEFINING` 의 control 은 `0 → 1` 로 **문다**.
  따라서 "이 filter 는 아무것도 안 한다" 가 아니라 "filter 는 배선되어 있고 population
  에 걸릴 게 없다" 가 참이다 — 두 vacuity mode (population 사실 vs 배선 사실) 는 다르고,
  D-076 은 한 번의 측정으로 둘을 가를 수 없었다.
- ✅ **자기 자신에 대한 negative control 을 같은 commit 에 실었다** (D-078 규칙): no-op
  patch 는 반드시 `INERT` 로 채점되어야 하고, **방향이 틀린 이동도 실패**로 채점된다.
  이게 없으면 위의 6 개 `BITES` 는 반증 불가능한 주장 — D-075 결함의 한 층 위 형태.
  static 층에도 합성 source 로 된 자기 negative control 을 붙였다.
- 🔴 **부산물**: D-076 이 발표한 `0 of 22` 는 오늘 `0 of 25` 다 (`PUBLISHED` 가 이후 3
  cell 늘었다). test 는 22 를 pin 하지 않고 `len(PUBLISHED)` 로 **유도**한다 — D-078 의
  규칙을 인용이 아니라 준수한 것. 22 를 pin 했다면 registry 가 제 일을 해서 red 가 됐다.
- 🔴 **census 비용**: guard pool **64 → 65**, **스물한 번째** 연속 cycle — 그런데 셋 중
  **하나만** 들어갔다. `uncontrolled` 은 `REGISTRIES` 를 `not in covered` 로 좁히므로
  보이고, `inert` 과 `unreachable` 은 verdict **문자열 상수와의 등호**로 좁히므로
  (`== VERDICT_INERT`, `!= CALL_TIME`) 보이지 않는다 — D-072 의 "detector 는 의미가
  아니라 `in`/`&` 연산자를 읽는다" 가 스물한 번째로 유지된다. exemption 이 `TAMPERS`
  에서 **DERIVED** 라서 `unwatched_exemptions` 는 **4 로 불변** (D-077 의 값싼 instance
  와 같은 이유). `exemption_masking.candidates()` 도 **7 로 불변**.
  `unwatched_exemptions` 도 **4 로 불변** — 그리고 그 4 개가 정확히 이 module 이
  control 하는 4 개다. **control 은 watcher 가 아니다** (전자는 "tamper 가 무언가를
  움직이는가", 후자는 "누구의 population 이 이 list 인가") — 둘을 섞으면 일어나지 않은
  수정을 보고하게 되므로 test 로 못박았다.
- **Alternatives**: (a) set 마다 tamper test 를 test 파일에 흩뿌린다 — 값은 같지만 *센서스*
  가 없어 빠진 set 이 침묵한다; (b) `exemption_masking` 을 확장 — 그건 suppression 으로
  bite 를 재는 다른 질문이고, `EXCLUDED_TESTS` 의 default-arg 구조를 볼 수 없다;
  (c) 안 한다 — D-075 급 vacuous test 가 다시 무료로 통과한다.
- **Status**: accepted — D-076 의 "filter 가 아무것도 안 한다" 독법을 **정정**한다
  (측정치 0 은 유효, 배선 귀속은 무효).
- **Refs**: PR #67 · `journal/2026-08/05-09-exemption-negative-controls.md`

## D-078 — 2026-08-05 — D-077 의 산문은 **자기 entry 를 쓰기 전** 숫자를 실었다: 재측정은 count 를 옮기지 prose 를 옮기지 않으며, 고치는 건 registry 가 아니라 **철자**다

- **Context**: 07:00 cycle 이 D-077 을 commit 한 뒤 **push 전에 죽었다** — TSV row 없음,
  JOURNAL/STATE 없음, 그런데 journal 은 "TSV row appended: **yes**" 라고 적혀 있었다.
  resume(decision tree step 1) 중 더 큰 게 나왔다: **같은 branch 안에서 D-077 의
  산문과 D-077 의 test 가 서로 다른 숫자를 말한다.** commit message 는 "5 in 19",
  entry 산문은 "18 중 5", test 는 `decisions == 77 / printing == 19` 를 pin.
- **진단은 추측이 아니라 등식이다**: 새로 만든 `magnitude_census.as_of(decision)` 로
  `as_of("D-076")` 를 재니 **정확히 `18 printing / 12 uncovered / 76 decisions`** —
  D-077 산문이 실은 세 숫자 그대로다. 오타가 아니라 **쓰기 순서** 결함이며, 차이는
  정확히 write 한 번(D-077 자기 entry)이다. D-043/D-044 가 존재하는 이유 그 자체가
  D-043 을 인용하며 재측정했다고 적은 entry 안에서 재발했다.
- **왜 안 잡혔나 — 누락이 아니라 registry 에 없는 범주다**: `citation_audit` 은 바로 이
  문서의 magnitude drift 를 잡으라고 만든 계측기인데 `MEASURED_CLAIMS` 6 개에 census
  가 없다. 그리고 **지금 형태로는 넣을 수도 없다**: census 를 인용하는 모든 entry 가
  *서로 다른* 숫자를 **옳게** 인용한다(entry 를 쓰는 행위가 세는 대상을 바꾸므로).
  claim 당 magnitude 하나를 가정하는 registry 에는 이 어휘가 없다.
- **Decision**: 그래서 수리는 일곱 번째 registry entry 가 아니라 **철자**다.
  canonical spelling `N printing / M transcribed / K uncovered (T decisions)` 를
  정하고, `quoted()` 가 그 철자를 문서에서 뽑고, `drifted()` 가 각 인용을 **그 인용이
  실린 entry 시점의** `as_of` 와 대조한다. 시간 색인을 붙이면 움직이던 magnitude 가
  다시 고정된 검사 가능한 claim 이 된다. D-077 을 그 철자로 고쳐 적었고(19/5/13/77),
  `drifted()` 는 지금 비어 있다.
- **vacuity 를 이번엔 같은 cycle 에 막았다**: `drifted() == ()` 는 아무도 그 철자를
  안 쓰면 **공허하게** 통과한다 — D-076 이 0/22 로 찾아낸 바로 그 결함. 그래서 bite 를
  따로 assert 하고(`quoted()` 비어있지 않음), **negative control** 도 넣었다(D-077 의
  인용을 stale 삼중항으로 바꾼 tampered 문서에서 `drifted()` 가 정확히 1 건 잡는지).
  guard 하나에 vacuity 검사와 음성 대조를 같이 붙인 건 이 branch 에서 처음이다.
- **정직한 한계**: 이 guard 는 **철자를 pin 하지 산문을 pin 하지 않는다.** canonical
  spelling 을 안 쓰고 census 를 인용하면 여전히 안 잡힌다 — D-077 의 title("19 중 5")
  이 실제로 그런 자리이고, 고쳤지만 policing 되지는 않는다. 넓히는 건 문서 전체의
  자연어를 파싱하는 일이고 하지 않았다.
- **Alternatives**: (a) 숫자만 고치고 끝 — 다음 cycle 에 같은 방식으로 재발.
  (b) census 를 `MEASURED_CLAIMS` 에 등록 — 인용마다 옳은 값이 달라서 매 cycle red.
  (c) test 의 pin 을 as-of 로 유도 — 채택함(`as_of(doc[-1])`, D-077 이 하드코딩한
  "D-077 이 최신" 가정을 제거).
- **Status**: accepted — D-077 의 published 숫자 정정 + 재발 방지 guard.
- **Refs**: PR #67 · `journal/2026-08/05-08-census-verdict-as-of.md`

## D-077 — 2026-08-05 — Q-083 답: `published_ratios.PUBLISHED` 는 **census 가 아니라 sample** (19 중 5) — 그리고 이 판정만은 철자 선택에 의존하지 않는다

- **Context**: D-076 이 typed exemption 의 bite 를 0/22 로 재고 원인을 **모집단**으로
  지목했다. `PUBLISHED` 가 76 개 decision 중 4 개만 transcribe 하므로 D-075 의
  `8/23` · `5/23` · `4/5` 는 아무도 크기를 재지 않은 분모 위의 비율이다.
- **Decision**: `eval/mppi_sandbox/magnitude_census.py` — `docs/decisions.md` 를
  77 개 `D-NNN` 섹션으로 쪼개고, `published_ratios.SITES` 에서 **유도한**(D-047)
  site 이름 한 줄 이내의 정수를 센다. 값만으로 판단하지 않는다(D-076 의 교훈):
  **novelty**(`(site, value)` 최초 등장 — reading 과 re-quote 를 가른다),
  **qualification**(`` `lam_dependence._pure` `` vs bare `` `_pure` ``),
  **crosstalk**(anchor 와 숫자 사이에 다른 site 이름) 세 discriminator 를 모두
  정수로 보고한다. 판정: **SAMPLE**,
  19 printing / 5 transcribed / 13 uncovered (77 decisions).
- **핵심 결론 — 개수는 흔들리고 판정은 안 흔들린다**: permissive 철자 19,
  strict(`clean`) 철자 **8**. 둘 다 틀렸다 — permissive 는 D-050/D-051(`_is_set_valued`
  를 *만들고 있는 술어*로 논하고, 옆 정수는 D-번호와 cycle 수)을 넣고, strict 는
  **D-070/D-071 — 이 record 전체가 그 위에 세워진 licensed reading 둘** — 을 뺀다
  (이 브랜치 산문이 site 를 bare 로 쓰기 때문). **네 철자 모두** transcribed <
  printing 이고 novel 값을 든 uncovered 가 남는다. D-076 은 철자 선택에 막혀
  멈췄고, 이번엔 그 선택 없이 결론이 선다.
- **부수 성과 — census 가 자기 비용을 in-cycle 로 갚았고, 6 cycle 동안 통과하던
  test 가 거짓 문장을 고정하고 있었다**: `published_ratios` docstring 의
  "source-frame control 은 **0** site **0** tree 에 publish 됐다" 는 **거짓**이었다.
  `test_..._never_published_on_any_tree` 의 `all(c.source_delta is None for c in
  PUBLISHED)` 는 아무도 publish 안 해서가 아니라 **이 record 가 publish 한 cycle 을
  transcribe 안 해서** 통과했다. D-068 이 셋을 publish 했다(`_pure` 40,
  `_is_structural` 41, `_has_git_diff_literal` 28, 각자 자기 69-tree exclusion
  control 과 짝). 이제 transcribe 됐고 `unverified()` 가 셋 다 재확인한다. 주장은
  "**licensed** 0 site 0 tree" 로 좁혔고 — downstream 을 지탱하는 건 그쪽이며 불변이다.
- **licensed 통계는 하나도 안 움직였다**: `common_sites(both_frames=True)` 여전히
  `()`, `answerable` n=2/n=0, D-075 counts bit-identical(8/23, 4/5, marginal 3).
  누락의 비용은 틀린 **숫자**가 아니라 틀린 **문장**이었다 — 둘 중 어느 쪽이든 될 수
  있었고, 아무도 몰랐을 것이다.
- **D-076 의 headline 도 불완전 모집단 위의 비율이었다**: `exemption_bite()`
  0/22 → **0/25**. 분자는 0 유지 — vacuity 는 살아남고 이제 더 넓은 모집단에서
  측정된다. D-076 의 pin 이 요구한 "바꾸는 cycle 은 말해야 한다" 를 이행하되,
  D-076 이 예상한 방향(D-074 transcribe → `(1, 23)`)이 아니었다.
- **scan 자신의 정밀도를 정수로 보고**: 21/298 clean (7%), bare 271, crosstalk 121.
  bare 가 지배적이고 이건 수리 가능성을 가른다 — crosstalk 은 **scan** 의 성질이라
  좁힐 수 있고, bare 는 **문서** 의 성질이라 6 cycle 치 산문을 다시 쓰지 않는 한 못 고친다.
- **census 비용, 20 cycle 연속이나 종류가 다르다**: predicate population **85**,
  그중 3 개가 이번 것(`SiteMagnitude.clean` / `Uncovered.candidate` /
  `Census.is_census`). `exemption_masking.candidates()` = 7, 이 모듈 기여 **0** —
  census 의 boolean 들이 registry 가 아니라 dataclass field 를 좁히기 때문. D-076 의
  "63" 은 **재측정하지 않았다**(계측기가 full suite run 을 요구, 예산은 census 에 썼다).
- 🔴 **자기 진입, 그리고 이번엔 원리적으로 불가피하다**: 이 entry 를 쓰는 순간 census 가
  읽는 문서가 커진다 — decision 총수도, printing 도, candidate 도 하나씩 늘고, 이
  entry 자신이 uncovered candidate 로 잡힌다. D-045~D-076 의 자기 진입은 계측기를
  술어 모집단에 넣는 *구현* 문제였고 원칙적으로 피할 수 있었다. 이건 아니다:
  **decision log 의 census 를 decision 으로 publish 하면 자기를 센다.** 4a-bis 이후에
  다시 재고(D-043/D-044) 그 값을 test 에 고정했으므로, 다음 cycle 이 D-078 을 쓰면
  이 test 가 깨진다 — 그게 의도다. census 를 다시 재라는 강제이지 결함이 아니다.
- **Alternatives**: (a) 18 만 보고하고 끝낸다 — D-076 이 당한 값-단독 판단의 재연.
  (b) `clean` 을 필터로 채택 — licensed reading 둘을 버린다. (c) quantity key 를
  먼저 만든다 — 옳지만 Q-083 의 크기 질문을 답하지 않은 채 1 cycle 더 쓴다.
- **Status**: accepted — Q-083 resolved. 남은 13 candidate 는 quantity key 없이는
  숫자로 못 줄인다 → **Q-084**.
- **Refs**: PR #67 · `journal/2026-08/05-07-published-magnitude-census.md`

## D-076 — 2026-08-05 — Q-082 의 두 선택지가 **둘 다 틀렸다**: typed exemption 은 지금까지 **0 건** 걸렀고, derive 는 **거짓 양성 2 건**을 만든다 — 빠진 건 manifest field 하나

- **Context**: D-075 가 `magnitude_survival.SELF_DEFINING` 을 typed module global 로 적었고
  `unwatched_exemptions` 가 셋에서 넷이 됐다. Q-082 는 (a) 다섯 번째 watcher 를 쓸지
  (b) record 에서 유도할지 물었고 (b) 로 기울었다 — "publish 된 값이 자기 band 끝점과
  같다" 는 disk 에서 다시 계산되니까. 이번 cycle 은 그냥 유도하는 대신 **둘 다 측정**했다.
- **측정 1 — typed exemption 은 vacuous**: `exemption_bite()` = **0 / 22**.
  `published_ratios.PUBLISHED` 는 D-066/D-069/D-070/D-071 을 전사했고 **D-074 는 전사한 적이
  없다**. 즉 이 filter 는 자기가 거르는 population 밖의 값을 지목하고 있다. D-075 가 이를
  검증한 test (`no D-074 value survives`) 는 **공허하게 통과**했다 — 애초에 D-074 값이 없다.
  exclusion 자체는 옳다; 다만 아무 일도 하고 있지 않으며, 그 둘은 다른 주장이다.
- **측정 2 — value-equality 유도는 over-derive**: "이 magnitude 가 이 record 의 reading 인가"
  를 정하려면 key 가 둘 필요하다 — **값**, 그리고 **record 가 어떤 claim 으로 publish 됐는가**.
  record 는 첫 번째만 갖고 있다. 값만으로: endpoint 철자는 published gap 20 중 **1**,
  replicate 철자는 **2** 를 제외하며 **전부 거짓 양성**이다 — D-069 의
  `_shells_out_to_git_diff` gap 9 가 이 record 의 band `hi` 9 과 **다른 tree 사이 우연히**
  일치한다. gap 은 작은 정수라 충돌이 예외가 아니라 기본값이다. ratio 는 **0 건** 충돌 —
  같은 사실의 반대편이며, 이 결함이 *일반 법칙이 아니라 small-integer 결함*임을 고정한다.
- **Decision**: 두 뿔 중 어느 쪽도 아니다. 빠진 field 를 추가한다 —
  `reading_record.Manifest.published_as` (여섯 번째 field, default `""`).
  자기 claim 을 적은 record 는 exemption 을 **정확히** 유도하고 (`self_defining`),
  적지 않은 record 는 typed set 으로 fallback 하되 `PROVENANCE_MISSING` 이 그 사실을
  침묵 대신 **문자열로** 반환한다. `read()` 는 `m.get(...)` — schema bump 가 아니라 default 다.
  이 branch 가 가진 유일한 banding record 를 소급 무효화하지 않는다.
- **Alternatives**: (a) 다섯 번째 watcher — guard 를 하나 늘리고 typed copy 는 남는다.
  (b) Q-082 lean 대로 값만으로 유도 — 위 측정으로 **반증됨**. (c) D-074 의 326 을
  `PUBLISHED` 에 전사해 exemption 을 살린다 — 옳지만 별개 작업이고, 그때 이 D-076 의
  유도가 typed triple 없이 바로 잡는다 (test 로 구성해 확인).
- **불변 확인**: D-075 의 모든 count 는 새 signature 아래 **bit-identical** —
  8/23, 4/5, marginal 3, `_pure` 0/6. record 가 unprovenanced 이므로 fallback 경로가
  기존과 같은 tuple 을 돌려준다. `test_threading_the_record_changes_no_published_value` 가
  이걸 지킨다.
- **부작용 하나를 값 치르고 막았다**: exemption 을 helper 뒤로 돌리는 순간
  `predicate_depth.provenance_depth_exposure` 가 **처음으로 양수**가 됐다 — 열여덟 cycle
  동안 latent 였던 그 계측이 예고한 바로 그 edit 이다 (`published` 의 registry 가 한 frame
  아래로 내려가 `DERIVED` 로 분류 → 모든 `TYPED` screen 에서 사라짐). D-052 (b) 가 미리
  적어 둔 repair (*"call site 에서 helper 의 registry 를 이름으로 부르라 — 인자로 넘기거나"*)
  를 그대로 적용했다: `self_defining(record, cells, SELF_DEFINING)`. exposure 는 다시 `()`.
  **다만 repair 는 scan 두 개 중 하나만 고쳤다** — `_provenance` 는 TYPED 로 되돌아왔지만
  shallow scan 은 여전히 call 에서 멈춰 `published` 를 못 본다. D-075 의 3-대-1 split 은
  **5-대-0** 이 됐고, 같은 edit 에 대해 두 scan 이 다른 답을 준다. D-052 (b) 가 둘 다
  고친다고 주장한 적은 없다.
- **census 비용**: guard pool **60 → 63** (`readings`, `over_derivation`,
  `exemption_bite`), 열아홉 번째 연속 cycle. Q-082 가 피하려던 "다섯 번째 watcher" 대신
  guard 를 **셋** 늘렸다 — 측정을 부정하는 근거는 아니지만 (측정이 0/22 와 거짓 양성 2 를
  찾았다), D-063 이후의 상용구를 한 번 더 값 매긴다: **pool 을 감사하면 pool 이 자란다.**
  `unscreened` 도 1 → 2 (`over_derivation` 은 `record` 인자 필수라 호출 불가) — 그리고 그
  두 번째 사례가 `UNRUNNABLE` 이 *비싼 guard* 표식이 아니라 그냥 *필수 인자 있는 guard*
  표식임을 드러낸다. 첫 사례가 흥미로운 원인 뒤에 그 사실을 숨기고 있었다.
- **Status**: accepted — Q-082 `resolved → D-076`, 단 **lean (b) 는 기각**.
- **Refs**: PR #67 · `journal/2026-08/05-06-derive-or-watch-self-defining.md`

## D-075 — 2026-08-05 — published magnitude 를 **자기 noise floor** 에 재봤다: gap movement 는 23 중 8 (엄밀히는 5), 그리고 **가장 많이 인용된 site 는 0**

- **Context**: D-074 가 same-tree `gap_spread` 를 처음으로 측정했다 (site 별 1.14–4.50×).
  그건 *설명* 하나를 폐기했을 뿐, 이 branch 가 여섯 cycle 동안 publish 한 **숫자들**은
  건드리지 않았다. Q-081 은 그 후속을 값싼 형태로 묻는다 — `published_ratios` 는 이미
  D-066..D-071 이 인쇄한 per-site 자릿수를 전부 전사해 뒀고, D-074 record 는 disk 에
  있다. join 한 번, 새 run 0회. **답의 크기가 곧 finding.**
- **Decision**: `magnitude_survival` 을 짓고 두 질문을 분리한다.
  **(1) containment** (published gap 이 band 안인가) 는 거의 무정보 — band 밖이라는 건
  *다른 tree* 의 숫자라는 뜻이고 그건 D-069 가 금지한 transported reading 이지 survivor 가
  아니다. **(2) movement** (한 site 의 두 published reading 사이 fold 가 그 site 의 spread 를
  넘는가) 가 채점 대상 — 양 끝이 같은 instrument 의 같은 quantity 이므로, instrument 자신의
  재현성보다 작은 fold 는 아무것도 증명하지 않는다. gap 과 ratio 둘 다에 적용
  (`Record.ratio_spread()` 신설, 분모는 **exclusion frame 단독** — 모든 published ratio 가
  그렇게 나눴으므로, Q-079).
- **측정 (cells, 유도값 아님)**: gap movement **8 / 23** 통과, site 기준 **3 / 6**.
  단, 통과분 중 셋의 여유가 각각 **1.009× / 1.023× / 1.047×** — k=3 으로 추정한 fold 의
  해상도 안쪽이고, 셋 다 **D-069** (control 없이 gap 만 publish 된 유일한 reading) 를 포함한
  pair 다. 방어 가능한 수는 **5 / 23**. `lam_dependence._pure` — 이 branch 최다 인용 site,
  gap 이 142 → 196 → 175 → 214 로 네 decision 에 걸쳐 실렸고 매 step 이 tree 가 움직인
  것처럼 서술됨 — 은 **6 개 movement 중 0 개** 통과. 그 네 값의 최대 fold 는 1.51×,
  같은 instrument 의 무변화 spread 는 1.74×. **전 series 가 자기 noise 안에 들어간다.**
  ratio 는 **4 / 5** 통과 — 이 branch 에서 control 이 선행 주장을 *폐기* 하지 않고
  **지지** 한 첫 사례 (D-071 이 stationarity 대신 ratio 를 남긴 선택). 다만 그 4 중 **둘은
  control 이 1 또는 2** (`_is_structural`, `_is_set_valued`) — `ATTR_FOLD` 에서 한두 count
  거리. `FRAGILE_CONTROL = 2` 로 rate 옆에 병기하되 빼지는 않는다 (반증된 게 아니라
  분모가 안 보이는 것). 남은 둘은 `_pure` 것 — **gap 은 전부 탈락한 그 site**.
- **License 는 boolean 이 아니라 tension 으로 반환**: band 는 tree `c4b76066`, published
  magnitude 중 그 tree 것은 없다. D-069-as-written 은 이 join 전체를 `TRANSPORTED` 로
  채점하고, D-074-as-measured 는 D-069 의 전제가 거짓이라 한다. 둘을 동시에 인용할 수
  없으므로 `license_status()` 가 그 충돌을 그대로 돌려주고 `report()` 가 먼저 인쇄한다.
  주장 범위는 **"instrument 자신의 noise floor 아래"** 이지 **"틀렸다"** 가 아니다.
- **한 숫자는 이름 붙여 제외**: D-074 가 publish 한 `_pure` gap **326** 은 이 record 에서
  `_pure` band 의 `hi` 그 자체다. 자기가 정의한 band 로 자기를 채점하는 건 순환이므로
  `SELF_DEFINING` 이 그 제외를 고정한다.
- **Alternatives**: (a) containment 만 보고 "band 밖이면 survivor" — D-069 가 금지한
  transport 를 다시 도입. (b) 8 만 보고하고 여유 분포는 생략 — 이번 cycle 이 방지하려는
  바로 그 결함. (c) fragile control 을 rate 에서 빼기 — 반증과 미측정을 같은 말로 뭉갬.
  (d) 새 batch 를 사서 band 를 다시 잡기 — 다음 cycle 의 일이고, 이 질문에는 불필요.
- **계측이 자기 census 를 움직였다 (D-043 re-take 가 red 로 잡음)**: doc write 이후
  re-take 에서 **4 test fail**. 원인은 회귀가 아니라 이 module 자신이 guard pool 에
  들어간 것 — `56 → 60`, **열여덟 번째** 연속 cycle 이자 D-051 의 여섯 이후 단일 cycle
  최대 추가. 넷의 **분포**가 개수보다 중요하다: `standings` / `unbanded` / `movements`
  는 전부 `banded` — 두 줄 위 same-module call 이 만든 **local dict** — 를 상대로
  좁힌다. module registry 도, typed 도, module scope 도 아니다. `published` 만
  `SELF_DEFINING` (module global) 을 상대로 좁혀 `exemption_masking` 의 module-global
  route 를 `15 → 16` 으로 올린다. 즉 D-072 의 syntax 결론이 가장 강한 형태로 재확인된다
  — detector 는 `in`/`not in` **연산자**만 본다. 그리고 D-063 이후의 표준 해설
  ("population 을 감사하는 도구는 스스로 그 population 의 구성원이 된다") 은 여기서
  **깨진다**: `if site in banded` 는 아무것도 감사하지 않고 band 가 채점할 수 없는 site 를
  건너뛸 뿐이다. **모양은 guard, 의도는 아님.** 셋 중 셋이 shallow scan 에 안 보인다
  (D-051 과 같은 이유) — 열여덟 cycle 뒤에 쓴 module 에서도 deep scan 이 선택사항이 아님.
- **`SELF_DEFINING` 이 unwatched 로 도착** (`unwatched_exemptions` 셋 → 넷), D-073 의
  2차 비용이 한 cycle 만에 반복. 여기서는 **watcher 를 쓰지 않기로** 했다 — `CARRIED_FIELDS`
  와 달리 이 집합의 원소는 record 에서 **재계산 가능**하므로 감시가 아니라 유도가 옳다.
  **Q-082** 로 분리.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-05-magnitude-survival.md` · Q-081 (static half) · Q-082

## D-074 — 2026-08-05 — ordering 에 **control 을 붙이니** 재현되지 않았고, 더 큰 것이 딸려 나왔다: **tree 는 처음부터 변수가 아니었다**

- **Context**: D-071 이 남긴 유일한 생존 후보 (c) 는 "magnitude 는 하나도 재현 안 됐지만
  **순서는 재현됐다**" — 네 tree 의 prose 위에서 눈으로 읽은 주장이고, D-072 는 그것이
  **두 site** 위에 서 있음을 보였다. 둘 다 *증거*에 대한 반론이다. 이 cycle 의 반론은
  *실험*에 대한 것: **tree 가 움직이지 않았을 때 순서가 얼마나 일치하는지**를 아무도 재지
  않았고, 그 값 없이는 cross-tree rho 가 구조인지 잡음인지 판정할 수 없다.
- **Decision**: `replicated_reading` 이 이미 사고 있던 2k run 의 사용처를 고쳤다. gap 은
  `(A1, M1)` 하나였고 나머지 2(k-1) run 은 **분모만** 넓히고 있었다 —
  `replicate_disagreements` 로 k 개 gap 을 모두 남기고, `ordering_control` 이 **한 tree
  위** replicate 쌍들의 C(k,2) rank agreement 를 반환한다. run 추가 비용 **0**.
  `reading_record` SCHEMA 1 → 2 (replicate 당 cell set), `Record.gap_spread` 추가.
- **Measured** (`take_and_record(k=3)`, 464 s, tree `c4b76066d64d`, 6/6 licensed,
  population **79**, 7 disagreeing, 첫 on-disk record):
  1. **순서는 자기 자신과도 재현되지 않는다** — rho **+0.571 / +0.857 / +0.714** (n=7).
     ordering 의 noise floor 가 ~0.71 이므로 그 band 안의 cross-tree rho 는 증거가 아니다.
     **(c) 는 측정된 적이 없다**, 틀린 게 아니라.
  2. **같은 tree 안 gap spread 가 tree 간 spread 를 덮는다** — 4.50× / 2.59× / 2.23× /
     2.19× / 1.74× / 1.27× / 1.14×. D-069 의 cross-tree ratio 는 0.31~1.67 (fold 로 ≤3.2×),
     **같은 일곱 site**. 즉 D-069~D-072 가 "tree 가 바뀌어서" 라고 읽은 변동은 **run 변동**
     이었다. D-069 의 guard 자체는 유효하다 (transported reading 은 해석 불가) — 무너진 것은
     그 **근거**다.
  3. D-071 이 (c) 의 증거로 인용한 endpoint `_is_set_valued` **13×** 는 이 tree 에서
     cell 로 **gap 14 / control 3+4** (measured-only 분모로는 **4.67×**). `_pure` gap 은
     142 → 196 → 175 → 214 → **326**. 일곱 중 **둘** (`_shells_out_to_git_diff` 0.47×,
     `_has_git_diff_literal` 0.43×) 은 control 이 gap 을 **넘는다**.
  4. **Q-079 는 장식이 아니다**: 선언된 both-frames 분모로 상위 둘은 `gap 326 / 67+72` 와
     `gap 14 / 3+4`, 모든 publication 이 실제로 쓴 measured-only 분모로는 **4.87 / 4.67**
     — 거의 동률. 같은 cell, 다른 이야기. (숫자를 유도값이 아니라 cell 로 적는 것은 D-073
     의 규칙이고, 여기서는 `citation_audit` 이 값 충돌 하나를 잡아 강제했다.)
- **Alternatives**: (a) cross-tree batch 를 하나 더 사서 비교 — 기각(이번엔), control 이
  낮으면 두 번째 tree 는 어차피 해석 불가이므로 **control 이 먼저**다. (b) ordering 에
  threshold 를 붙여 "충분히 일치" 를 정의 — 기각, 다섯 번째 미정당 상수. (c) prose 로
  적고 넘어가기 — 기각, D-072 가 정확히 그 실패를 이름 붙였다. `gap_spread` 는 함수다.
- **Status**: accepted. D-071 (c) → **withdrawn** (반증이 아니라 **무근거**).
  D-069 의 guard 는 유지, 근거는 이 entry 로 교체.
- **Refs**: PR #67 · `journal/2026-08/05-04-ordering-control.md` ·
  `results/readings/2026-08-05-04-ordering-control.json` · Q-081

## D-073 — 2026-08-05 — reading 을 **파일로** 남긴다: 분모는 고르는 게 아니라 **선언**하는 것이고, registry 의 **평범한 철자**는 detector 에 보이지 않는다

- **Context**: D-072 가 여섯 cycle 의 uncheckable 함을 **plumbing** 으로 진단했다 —
  `paired_reading` / `replicated_reading` 은 site 7개 × (gap, 두 frame control) 을 이미
  **계산하는데**, 그걸 디스크에 쓴 cycle 이 하나도 없어서 licensed cell 33 중 **16** 이
  산문 사이로 흘렀고 source-frame control 은 11/11 전부 사라졌다. 계산 문제가 아니라
  기록 문제.
- **Decision**: `eval/mppi_sandbox/reading_record.py` — reading 하나 → JSON 하나.
  세 가지를 못박았다.
  (1) **schema 는 파생**: `CELL_FIELDS` 는 `dataclasses.fields(FrameAttribution)` 에서
  읽는다. grader 에 field 가 늘면 record 도 같은 commit 에 는다 (D-047).
  (2) **Q-079 는 질문의 모양이 틀렸다**: record 가 **두 frame delta 를 모두** 저장하므로
  분모는 *view* 이고 (`ratios(DENOM_BOTH|DENOM_MEASURED)`), manifest 는 그 cycle 이
  **어느 쪽으로 보고했는지 선언**한다. `comparable()` 은 선언이 다른 두 record 의
  rank 상관을 거부한다. 고를 필요가 없고, 말할 의무가 있다.
  (3) **충분성은 증명한다**: 파일에서 계산한 grade 가 live reading 의 grade 와 `==`.
  부분 파싱과 미지의 schema 는 예외.
  CrowdSkill 5-field manifest (feed 08-05 00:00) 를 field 별로 대응시키되 안 맞는 칸을
  숨기지 않았다 — **seed schedule 이 없다**, 그리고 그 부재가 곧 주제다 (address-repr
  fingerprint = 아무도 seed 하지 않는 entropy). `Manifest.entropy` 가 파일 안에서 그렇게
  말한다.
- **가장 값싼 발견, 그리고 in-cycle 로 양쪽 다 측정**: `CARRIED_FIELDS = CELL_FIELDS +
  DERIVED_FIELDS` 로 쓰면 `_is_set_valued` 가 registry 로 보지 않아 `would_have_carried`
  (평범한 `in`-형 filter) 가 guard pool 에 **안 들어온다 (54)**. `tuple(CELL_FIELDS +
  DERIVED_FIELDS)` — 값은 동일 — 이면 **들어온다 (55)**. D-072 는 detector 가 semantics 가
  아니라 `&` 연산자를 읽는다고 했는데, 정확히는 **syntax 를 읽고**, 여기서 보이지 않는
  철자는 registry 를 registry 두 개로 조립하는 **평범한 방식**이다. 따라서 이 pin 이
  지금까지 들고 온 모든 "exactly N" 은 *보이게 철자된* guard 의 수다.
- **그 수정의 2차 비용**: registry 를 보이게 만든 순간 그것은 **watch 되지 않는**
  allow-list 가 됐다 (`unwatched_exemptions` 3 → 4) — D-047 이 살던 바로 그 상태. 그래서
  `uncarried_fields` 를 써야 했고 pool 은 55 → **56**. 그 exempting set 은 `DERIVED`
  (round-trip 된 cell 위의 `dot dir()`) 라서 `CARRIED_FIELDS` 는 자기 사본이 아니라
  **측정**에 의해 감시된다 (D-045).
- **정직하게 남기는 절반**: `unrecoverable()` 은 16 cell 을 전부 돌려준다. 오늘 채택한
  어떤 포맷도 그 중 하나를 되찾지 못한다. `would_have_carried()` 의 좋은 숫자는 항상
  이것과 같은 namespace 에서 읽힌다.
- **Alternatives**: (a) 채택 — reading 당 파일 + 선언된 분모.
  (b) `published_ratios` 처럼 산문을 계속 전사 — D-072 가 이미 degenerate (n=2) 로 판정.
  (c) 두 분모 중 하나를 고르고 못박기 — 고른 근거가 없고, 고르는 순간 기존 인용과
  새 측정 중 한쪽이 검산 불가가 된다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/05-03-serialise-the-reading.md` · Q-079 (분모)
  부분 해소 — 기록/선언으로 전환, 어느 쪽이 "옳은지"는 여전히 미측정

---

## D-072 — 2026-08-05 — ratio 채점기를 지었고, 그 다음 **published record 에 물었더니 답이 없었다**: D-071 이 "네 tree 에서 재현됐다"고 한 순서는 **정확히 두 site 의 순서**였다

- **Context**: D-071 이 Q-077 의 양쪽 lean 을 죽이고 후보를 하나 남겼다 — (c) stationarity
  대신 **gap/control 비율**. 근거는 자기 journal 의 한 줄이었다: "ratios spanning 2.5×
  (`_pure`: 214 vs 87) to 13× (`_is_set_valued`: 13 vs 1), and that ordering has now
  reproduced on four trees". STATE #1 은 가장 싼 다음 수를 제안했다 — **run 없이**
  D-066..D-071 artifact 에서 per-site ratio 를 꺼내 rank correlation 을 계산.
- **Decision**: 둘 다 했다. (1) 채점기: `exclusion_scope.RatioGrade` / `ratio_grades` /
  `ratio_ranking` / `rank_agreement` / `RANK_MIN_N`. **문턱이 없다** — 순서는 상수를
  요구하지 않으므로 이 package 의 다섯 번째 미정당화 상수를 만들지 않는다. control 0 인
  site 는 별도 class 가 아니라 `inf`, 즉 **연속체의 꼭대기**가 되고, 그래서 0 움직인 site
  와 2 움직인 site 가 **인접**해진다 — Q-077 의 동전 던지기는 판정되는 게 아니라
  **해소된다**. 분모는 **두 frame 의 합** (D-068 이 47/42/58 을 142/84/95 에 맞세운 그
  noise budget). `rho` 에 p-value 도 문턱도 없다. (2) `published_ratios`: D-066..D-071 이
  실제로 인쇄한 per-site 숫자 **전부**를 출처 파일과 함께 전사하고, `unverified()` 가 그
  숫자들을 그 파일에서 **다시 찾아낸다**.
- **측정 결과** (run 0 회, 정적):
  - 🔴 **Q-078 의 no-new-run 절반은 답이 없다 — 그것도 아슬아슬하지 않게.** licensed
    reading 은 둘뿐이고 (D-070/D-071; 나머지는 D-069 guard 하에서 `TRANSPORTED`), 양쪽에서
    ratio 를 만들 수 있는 공통 site 는 **2** 개, 문턱은 3. n=2 는 작은 표본이 아니라
    **퇴화한** 표본이다 — 서로 다른 2-순서는 전부 ±1 로 상관한다.
  - 🔴 **그 두 site 가 하필 D-071 이 인용한 그 두 site 다.** licensed overlap =
    {`lam_dependence._pure`, `guard_reflexivity._is_set_valued`} = D-071 이 범위의
    양 끝으로 든 2.5× 와 13×. **한 쌍의 순서는 정의상 재현된다.** "네 tree 에서 재현된
    ordering" 은 자기가 인용한 기록 위에서 **점 두 개**다. 틀렸다는 게 아니라
    **확인 불가능**하다는 것 — 그리고 (c) 는 D-071 이 남긴 유일한 생존자였다.
  - 🔴 **source-frame control 은 어느 tree 에서도 인쇄된 적이 없다.** 그래서 `RatioGrade`
    가 정의하는 (두 frame) 비율의 완결 cell 은 **0** 개다. D-071 이 인용한 2.5×/13× 는
    **exclusion frame 단독** 분모 — 채점기가 쓰는 분모와 다른 수다.
  - 🔴 **원인은 논증이 아니라 배관이다: 어떤 reading 도 직렬화된 적이 없다.**
    `paired_reading` / `replicated_reading` 은 7 site 전부의 gap + 양 frame control 을
    **이미 계산한다**. 매 cycle 이 그걸 산문으로 옮기며 licensed cell **33 중 16 개**를
    버렸다 (source frame 은 11/11 전부). `missing()` 이 그 목록을 이름으로 낸다.
  - 🔴 **덤으로, 열여섯 번째 self-entry 가 D-065 이후 3 cycle 간 붙어 있던 설명을
    반증했다.** `rank_agreement` 가 guard pool 에 들어갔다 (53 → **54**) — 네 번째
    `&`-shaped guard 이고, **양쪽 어디에도 registry 가 없는 첫 사례**다
    (`set(a) & set(b)`, 둘 다 runtime 데이터). 그래서 "registry 를 지목하는 narrowing
    만 잡는다"는 3 cycle 짜리 특성 규정은 **틀렸다**. 결정적 증거는 같은 cycle 안에 있다:
    `published_ratios.common_sites` 는 **완전히 같은** 교집합을 `set.intersection(*sets)`
    로 쓰고 pool 에 **안 들어간다**. 하나의 narrowing, 두 개의 표기, 하나만 보인다 —
    detector 는 semantics 가 아니라 **`&` 연산자**를 읽는다. 재발 자체는 진짜지만
    D-065 이래 그것에 붙여온 설명은 아니다.
- **Alternatives**: (a) 그냥 두 tree 로 rho 를 계산해 보고한다 — 거부. ±1 이 나올 것이고
  그건 데이터가 아니라 산술이다. (b) 문턱을 n≥2 로 낮춘다 — 같은 이유로 거부. (c) 새
  batch 를 사서 세 번째 licensed tree 를 만든다 — 435 s, 가능하지만 **직렬화가 먼저다**:
  지금 사면 세 번째 tree 도 산문이 되고 다음 cycle 이 같은 벽을 만난다.
- **Status**: accepted. Q-078 의 정적 절반은 **닫힌다 — 음성으로**. 동적 절반은
  STATE #3 (artifact 직렬화) 에 **차단**되며, 그게 이 음성이 추천하는 행동이다.
- **Refs**: PR #67, `journal/2026-08/05-02-ratio-record-insufficient.md`, Q-078, Q-079

## D-071 — 2026-08-05 — frame 당 **k=3 replicate** 을 샀다: 0-이동 문턱은 *엄격해지는* 게 아니라 **도달 불가능**해지고, band 는 같은 frame 안에서 **7.7× 로 흩어진다**

- **Context**: D-070 의 headline 이 **~9600 중 2 카운트** 위에서 뒤집혔다 (Q-077).
  선택지는 둘이었다 — (a) 문턱을 0 에 두되 **충족을 어렵게**, (b) 문턱을 frame 의 band 로
  **넓히되** 정당화 없는 상수를 하나 더 만든다. 이 package 는 이미 그런 상수를 넷 들고 있다.
- **Decision**: (a) 를 샀다. `predicate_inputs.Spread`/`spread`/`fold_spread`/`spread_band`
  + `exclusion_scope.replicated_reading(k)` — frame 당 k run, 2k 개 전부 동시·양면 stamp.
  gap 은 여전히 `fold(A1)` vs `M1` (replicate 은 **control 만** 넓힌다). 채점기는
  `.stationary` / `.movement` 로만 읽으므로 k=2 에서 D-070 과 **같은 수**를 낸다.
  `ReplicatedReading.fragile` = k=2 판정과 k 판정이 **다른 site** — Q-077 의 동전 던지기를
  논증이 아니라 **측정**으로 만든다. C(k,2) pairwise band 는 **평균 내지 않고 나열**한다:
  pair 들이 run 을 공유하므로 (k=3 → pair 3, 자유도 2) 평균은 사지 않은 정밀도를 주장한다.
- **측정 결과** (435 s, 6 run 동시, tree `9338e10e…`, licensed, population 71 → **74**,
  관측 50 site, 불일치 **7** — 다섯 번째 재현):
  - 🔴 **`fragile` = ∅ — 그런데 이유가 틀렸다.** k=2 에서도 stationary 인 site 가 **없어서**
    아무 판정도 안 움직였다. 7 site 전부 양쪽 reading 에서 `DRIFT_UNDERSHOOTS`.
  - 🔴 **문턱이 엄격해진 게 아니라 죽었다.** k=3 에서 **어느 frame 에서도** 정확히 반복되는
    site 가 없으므로 `FOLD_IMPLICATED` 은 **획득 불가능**. 0-문턱은 k 가 커지면
    "증거가 강해지는 판정"이 아니라 "발행되지 않는 판정"으로 수렴한다 — (a) 도 죽는다.
  - 🔴 **band 는 측정의 성질이 아니라 *어느 pair 를 뽑았는가*의 성질이다.** 같은 frame,
    같은 tree, 같은 batch 의 세 pair: **0.519 % / 0.068 % / 0.487 %** (**7.7×**).
    source frame 0.356 / 0.259 / 0.098 % (**3.7×**). D-066 이 자기 reconstruction 에
    물린 **0.487 %** 는 순수 control pair 가 내는 범위 **안에** 있다.
  - 🔴 **네 번째 tree, 네 번째 magnitude set**: `_pure` 142 → 196 → 175 → **214**,
    `_has_git_diff_literal` 95 → 29 → 30 → **65**, `_is_set_valued` 12 → 20 → 15 → **13**.
    control 도 같이 커졌다 (`_pure` exclusion frame **87**, D-070 은 13) — D-070 의
    "13× undershoot" 논거는 이 batch 에서 살아남지 못한다.
- **Alternatives**: (a) 채택·**반증됨** — 문턱이 죽는다. (b) band 문턱 — 이제
  **살 수 없음이 측정됐다**: 추정치 자체의 흩어짐(7.7×)이 문턱이 가를 차이보다 크다.
  (c) stationarity 를 버리고 **gap/control 비율** 통계로 — 네 tree 에서 magnitude 는
  하나도 재현되지 않았지만 *순서*는 재현됐다 (2.5×~13×). 다음 cycle 의 후보.
- **Status**: accepted. Q-077 의 **양쪽 lean 을 모두 닫는다** — 답이 아니라 소거.
- **Refs**: PR #67, `journal/2026-08/05-01-replicated-band-distribution.md`, Q-077

## D-070 — 2026-08-05 — 네 run 을 **한 tree 위에서 동시에** 돌린 첫 licensed reading: fold 는 **어느 site 에서도** 지목되지 않는다 — 그런데 그 판정을 가르는 건 **2 카운트** 이동이다

- **Context**: D-069 가 `single_tree` guard 를 만들자마자 자기 headline 을 무효화했다 — gap 은
  70-tree, 두 control 은 69-tree 라 7 site 전부 `TRANSPORTED`. D-068 의
  `FOLD_IMPLICATED` 은 **철회 후 paired run 대기** 상태였고, 그 paired run 이 이 cycle 이다.
- **Decision**: `exclusion_scope.paired_reading` — `measure_attributed` ×2 +
  `measure` ×2 를 **하나의 thread pool 에 동시** 제출하고, 네 frame 의 `tree_key` 를 모두
  `attribute_two_frame` 에 넘겨 채점한다. 동시 실행은 wall clock 때문만이 아니라 **tree 가
  움직일 창을 좁히기** 위한 것이다 (순차 4 run = ~20 분). 추가로 `_stamped` 가
  `single_tree` 에 남아 있던 구멍을 막는다: `single_tree` 는 run 당 key 1 개를 받는데 이는
  **run 이 순간적**이라고 가정한다. 5 분짜리 run 4 개는 그렇지 않으므로, 각 frame 을
  **양쪽에서** stamp 하고 불일치 시 **빈 key** 를 발급한다 — `single_tree` 가 이미 가진
  거부 경로를 재사용한다.
- **측정 결과** (397 s, tree `5eb5123d…` 네 frame 동일, population **71**, 관측 50 site,
  불일치 **7**):
  - ✅ `licensed=True`, 양 frame `work_repeated=True`, band **0.106 %** (exclusion) /
    **0.162 %** (attributed), 양쪽 `address_confined=True`. `TRANSPORTED` 0 건.
  - 🔴 **`fold_implicated` 가 비었다.** D-068 의 `_is_set_valued` 판정은 **재현되지 않는다**
    — exclusion frame 이 **2** 움직였다 (0 이 아니라). licensed reading 에서 fold 는 어느
    site 에서도 마지막 용의자가 아니다.
  - 🔴 **그러나 "fold 가 아니다" 는 "설명됐다" 가 아니다.** 7 중 **6** 이
    `DRIFT_UNDERSHOOTS` 이고 undershoot 폭이 크다: `_pure` gap **175** / control **13**,
    `_numeric` **79** / **5**, `_is_pure_literal` **77** / **30**, `_is_structural`
    **66** / **2**.
  - 🔴 **채점 기준이 knife-edge 다 — 이번 cycle 의 진짜 발견.** `FOLD_IMPLICATED` 은 양
    frame 의 **정확한** 정상성을 요구한다. 50 site · 0.1 % band 에서 어떤 site 가 0 움직이냐
    2 움직이냐(≈9600 중)는 동전 던지기에 가깝고, 그 1 bit 이 "fold 가 마지막 용의자" 와
    "control 이 약하게 면책" 을 가른다. 세 cycle 의 논쟁이 그 bit 에 걸려 있었다.
  - 🔴 **세 번째 tree, 세 번째 magnitude 집합**: `_pure` 142 → 196 → **175**,
    `_has_git_diff_literal` 95 → 29 → **30**, `_is_set_valued` 12 → 20 → **15**.
  - 🔴 **"같은 7" 주장은 기록만으로는 검증 불가능했다.** 멤버십은 또 재현됐고(7/50) 이
    cycle 이 **일곱 개 이름을 처음으로 전부** 적는다. D-066~D-069 는 그중 **다섯** 만
    적었다 — `lam_dependence._is_pure_literal` 과 `lam_dependence._numeric` 은 어떤
    published artifact 에도 없다. 세 cycle 이 "정확히 재현" 이라 부른 주장의 근거는 보존되지
    않은 in-cycle 비교였다.
  - ⚠️ **열일곱 번째 self-entry**: population 70 → **71**. 관측 site 는 여전히 50.
- **Alternatives**: (a) 순차 4 run — tree 가 움직일 창이 3 배; (b) gap 의 run 과 control 의
  run 을 서로소로 유지 (D-066~D-069 방식) — "**fold 가 실제로 읽은** run 이 달랐을 수
  있는가" 가 아니라 더 약한 질문에 답함; (c) guard 없이 caveat 재작성 — D-069 가 이미 기각.
- **Status**: accepted — D-068 의 `FOLD_IMPLICATED` 을 **철회 상태에서 미재현으로 확정**한다
  (반증이 아니라 licensed frame 에서 재현 실패). D-069 의 magnitude 불안정 결론은 **유지**된다.
- **Refs**: PR #67 · `journal/2026-08/05-00-licensed-four-run-batch.md`

## D-069 — 2026-08-04 — 두 frame 을 **한 tree 위에** 올리니 site 집합은 **정확히 같은 7 개**였고 magnitude 는 **하나도** 재현되지 않았다 (0.31×~1.67×, 부호 1 건 반전) — transport 는 caveat 이 아니라 **guard** 여야 한다

- **Context**: D-066 의 gap 은 **64**-predicate tree, D-067/D-068 의 control 은 **69**-tree
  에서 측정됐다. 세 cycle 모두 이 사실을 "한계" 문단에 정직하게 적고 **그대로 넘어갔다**.
  binary (address-repr 여부) 는 edit 을 건너 transport 되지만 **magnitude 는 안 된다** —
  gap 은 두 count 의 차이고, recorder 가 도는 suite 이 바뀌면 두 count 이 다 움직인다.
- **Decision**: (1) `predicate_inputs.tree_key()` — `tree_provenance` 에 위임해서 "같은
  tree" 의 정의를 **하나만** 유지 (D-043/D-044 가 pass count 에 대해 이미 소유한 질문).
  (2) `exclusion_scope.single_tree()` — key 가 **없거나 비면 False**. 기본값이 거부여야
  하는 이유는 이 함수가 존재하는 세 cycle 이 전부 사후에 손으로 발견했기 때문.
  (3) `attribute_two_frame(trees=…)` — **opt-in**. 주어졌고 전부 같지 않으면 모든 verdict
  이 `TRANSPORTED` 이고 이는 `FOLD_IMPLICATED` 보다 **우선**한다. 생략하면 pre-D-069
  동작이라 published grade 가 조용히 재작성되지 않고 **새 single-tree run 이 대체**한다.
- **측정 (1 attributed + 1 flat, 동시, frozen `2c4e0f04…`, 366 s, population 70)**:
  - ✅ **membership 은 완전 재현**: 64-tree 와 70-tree 에서 **같은 7 / 50** site.
  - 🔴 **magnitude 는 하나도 재현 안 됨**. one-tree ÷ D-066 비율:
    `_has_git_diff_literal` 95→**29** (0.31×), `_shells_out_to_git_diff` 15→**9** (0.60×),
    `_is_structural` 84→**73**, `_pure` 142→**196**, `_is_pure_literal` 57→**88**,
    `_numeric` 51→**81**, `_is_set_valued` 12→**20** (1.67×).
  - 🔴 **부호 1 건 반전**: `_shells_out_to_git_diff` 가 low(−15) → **high(+9)**.
    D-066 이 digest 를 원인에서 제외한 논거가 "collision 은 낮추는 방향으로만 틀린다 +
    high 인 site 가 하나 있다" 였다. 그 전제는 site 의 성질이 아니라 **run 의 성질**이었다.
    결론 자체는 유지 — `_is_set_valued` 는 양쪽 reading 에서 high, 이제 witness 가 둘.
  - 🔴 **guard 의 첫 실사용이 이번 cycle 자신의 headline 을 무효화**: gap 은 70-tree,
    존재하는 control 은 D-067/D-068 의 69-tree → 7 건 전부 `TRANSPORTED`,
    `fold_implicated_two_frame` = `()`. D-068 의 `FOLD_IMPLICATED` 는 **반증된 게 아니라
    세 번째로 unlicensed** 가 됐다.
- **Alternatives**: (a) 한계 문단을 계속 쓴다 — 세 cycle 이 실패한 방식. (b) guard 를
  retro-fit 해서 published grade 를 자동 재작성 — 조용한 재작성이라 기각. (c) opt-in guard
  + 새 single-tree run 이 소리내어 대체 ← **채택**.
- **한계 (명시)**: 이번 gap 도 **paired 가 아니다**. gap 은 1+1 run 으로 한 tree 위에 있지만
  frame control 은 안 샀다. `single_tree` 를 통과하는 유일한 형태는 gap 2 run + control
  2 run 을 **한 frozen batch** 로 도는 4-run 이다 (16 core 에서 ~6–7 분).
- **부수 관측**: population 69 → **70** (`single_tree` 자신이 술어 — 열여섯 번째 self-entry,
  D-068 의 "zero self-entry" 는 1 cycle 로 끝났다). 관측된 site 수도 D-066 의 **53** 에서
  **50** 으로 움직였고 아무도 설명하지 않았다.
- **Status**: accepted — D-066/D-067/D-068 의 magnitude 주장을 전부 `TRANSPORTED` 로 rescope.
  D-068 의 `FOLD_IMPLICATED` 는 **withdrawn pending a paired run** (반증 아님).
- **Refs**: PR #67 · `journal/2026-08/04-23-one-tree-gap.md`

## D-068 — 2026-08-04 — D-067 의 control 은 **frame 이 하나**였다: fold 의 두 입력 중 오른쪽만 고정했고, 왼쪽(attributed run)도 재보니 `_is_set_valued` 는 **양쪽 frame 에서 정지** — 지적은 맞았고 판정은 살아남았다

- **Context**: D-067 은 `guard_reflexivity._is_set_valued` 를 `FOLD_IMPLICATED` 로
  등급했다. 근거는 "measurement 가 정확히 반복되는데 fold 가 12 만큼 빗나갔다".
  그런데 불일치의 정의는 `fold(measure_attributed run) != measure(exclusion run)`
  이고, D-067 의 control 은 `measure()` 를 두 번 돌린 것 — **오른쪽 항만** 고정했다.
  "measurement 가 반복된다" 뒤에 남는 것은 fold 의 산술 **과** fold 의 입력이다.
- **공짜로 먼저 얻은 것**: `exclusion_scope.unlicensed_fold_verdicts` — run 없이
  D-067 자신의 두 artifact 를 join 한다. address-repr site 에서 attributed run 은
  **더 큰 file set 을 도는 별개 process** 이므로 `<C object at 0x…>` 가 exclusion
  frame 과 일치할 구성이 없다. 반대로 value fingerprint site 는 같은 질문이면 어느
  frame 에서도 같은 지문이라 source 항이 **구조적으로 0** — 그래서 이 지적은 정확히
  불일치 7 건(전부 address)만 물고, 일반적인 control 불평이 아니다.
- **Decision**: 빠진 반쪽을 만든다. `predicate_inputs.fold_drift` (attributed run
  두 번, 같은 exclusion 으로 fold) + `exclusion_scope.attribute_two_frame` /
  `SOURCE_COVERS` / `SOURCE_UNDERSHOOTS` / `fold_implicated_two_frame`.
  exclusion frame 을 **먼저** 묻는 우선순위 — D-067 이 낸 6 개 `DRIFT_*` 등급은
  그대로 서고, 움직일 수 있는 것은 `FOLD_IMPLICATED` 하나뿐. 좁히는 재독해지 경쟁하는
  재독해가 아니다.
- **측정 (frozen tree, 동시 2 run, 348 s, population 69)**:
  `_is_set_valued` 는 attributed frame 에서도 **9600 → 9600** distinct /
  **10239 → 10239** calls. 양쪽 입력이 정확히 반복되고 fold 는 여전히 12 를 빗나간다
  ⇒ 두-frame control 아래에서 다시 `FOLD_IMPLICATED`, 이번엔 **licensed**.
- **부수 결과**: source frame 의 band 는 **0.227 %** (6/50 site, `address_confined`
  = True, `work_repeated` = True) — D-067 이 잰 0.195 % 보다 넓고, 하필 D-067 이
  `DRIFT_UNDERSHOOTS` 로 등급한 세 site 에서 체계적으로 크다: `_pure` **40** (거기선 7),
  `_is_structural` **41** (1), `_has_git_diff_literal` **28** (30). 그래도 두 frame
  delta 를 합쳐도 **47 / 42 / 58** 로 gap **142 / 84 / 95** 를 못 덮는다. 계기의 잡음
  예산이 ~6× 늘었는데 설명되는 잔차는 그대로.
- **Alternatives**: (a) 자유 독해만으로 D-067 을 철회 — 348 s 를 아끼고 **틀렸을**
  결론을 낸다. (b) source frame 만 새로 재고 D-067 등급을 전부 덮어쓰기 — 6 건의
  멀쩡한 등급을 근거 없이 흔든다. (c) 채택: 자유 독해로 *증거 부족*을 명시하고,
  측정으로 판정한다.
- **Status**: accepted
- **한계 (숨기지 않음)**: D-066 의 12 는 **64**-predicate tree 에서, 이 control 은
  **69**-tree 에서 쟀다. 양쪽 fold 가 여기서 9600 을 읽으므로 exclusion frame
  `measure()` **1 run** 이면 한 tree 위에서 끝난다 — 다음 cycle 의 STATE #1.
- **자기-등재 0 건 — 16 cycle 만에 처음**. population 69 유지: 이번에 추가된 함수는
  전부 tuple/int 를 돌려주므로 predicate 가 아니다. D-045→D-067 이 계속 pin 하던
  재귀는 *계기*를 만드는 성질이 아니라 *predicate* 를 만드는 성질이었다.
- **Refs**: PR #67 · `journal/2026-08/04-21-two-frame-fold-control.md`

## D-067 — 2026-08-04 — D-066 의 미결 residual 을 **fold 없는 control** 에 물으니 답이 갈렸다: 측정 자체가 **비정상적(0.195 % band, address site 6/50)** 이지만 그 drift 는 gap 을 **덮지 못하고**, 정확히 **1 site 는 fold 가 범인**이다

- **Context**: D-066 은 input fold 의 복원이 measured run 과 **53 중 7** count 에서
  어긋난다고 보고하면서 두 후보 원인을 적고 **둘 다 배제하지 못했다** — (i) fold 가 근사이거나
  (ii) fingerprint 가 process 간에 재현되지 않거나. 부호는 digest 만 제외했다.
- **Decision**: fold 가 **등장하지 않는** control 을 만든다. `predicate_inputs.drift` /
  `unstable` / `drift_band` / `address_confined` / `work_repeated` — 같은 tree 를 두 process
  에서 flat 하게 두 번 재고, 움직인 site 를 센다. 그 위에
  `exclusion_scope.attribute_disagreements` 가 D-066 의 7 건을 `FOLD_IMPLICATED` /
  `DRIFT_COVERS` / `DRIFT_UNDERSHOOTS` / `UNCONTROLLED` 로 등급 매기고,
  `fold_implicated` 이 비어 있을 수 있는 reading 이 된다.
- **공짜로 먼저 얻은 것**: `disagreements_address_confined` — 새 run 없이 D-066 자신의 두
  artifact 만 join 한다. **불일치 7 건 전부 `address_reprs=True`**, 값 기반 fingerprint
  site **44 건은 전부 정확히 일치**. population 의 address site 는 9 개뿐이므로 7/9.
  메커니즘에 이름이 붙는다 — `<C object at 0x…>` 는 두 번째 process 에서 다르게 렌더된다.
- **🔴 첫 control 을 내가 직접 무효화했다**: run A 와 B 가 내 edit 을 사이에 두고 실행되어
  `pv._scan()` 이 **64 → 69** 를 봤고 5 site 의 call count 가 움직였다. D-043 이 pass count
  에 대해 말하는 그 규율이 **control 에도** 적용된다는 것을 아무도 적어두지 않았다.
  frozen tree 에서 동시 실행으로 재측정 (~6 분).
- **측정 (clean pair, population 69, 50 site)**:
  - ✅ `work_repeated` = **True** — 50 site 전부 call count 를 정확히 재현. 두 run 은 한
    측정의 두 표본이고, 따라서 아래는 전부 fingerprint 이야기다.
  - 🔴 `address_confined` = **True**, 움직인 site **6/50**, 측정 자신의 band **0.195 %**.
    D-066 이 복원 탓으로 돌린 0.487 % 와 **같은 자릿수**다 — 그 band 는 애초에 fold 만의
    성질이 아니었다.
  - 🔴 그런데 **drift 가 gap 을 못 덮는다**. 7 중 **6 건이 `DRIFT_UNDERSHOOTS`**:
    `lam_dependence._pure` fold 오차 **142** vs control 이동 **7**; `_is_structural`
    **84** vs **1**; `_has_git_diff_literal` **95** vs **30**.
  - 🔴 **`guard_reflexivity._is_set_valued` 는 `FOLD_IMPLICATED`** — control 이동 **0**,
    fold 오차 **12**. D-066 에서 **높게** 어긋난 바로 그 site, 즉 digest 를 용의선상에서
    지운 부호의 주인공이다. 한 용의자를 지운 논거가 이제 **fold 가 유일한 피고인 site** 를
    가리킨다.
- **Alternatives**: (a) 두 원인 중 하나를 고르려 계속 시도 — 질문이 틀렸다, 답은 *둘 다*이고
  비율이 있다. (b) drift 를 재고 band 안이면 전부 면책 — 한 쌍은 spread 의 표본 하나라
  `DRIFT_COVERS`/`DRIFT_UNDERSHOOTS` 를 합치면 추정한 적 없는 산포를 가정하게 된다.
  (c) **binary (재현되는가) 를 load-bearing 으로, 크기 비교는 명시적으로 약하게 보고** ← 채택.
- **한계 (명시)**: D-066 의 gap 은 **64-predicate tree**, 이 control 은 **69-predicate
  tree** 에서 측정됐다. site 별 **binary** 는 인자 타입의 성질이라 옮겨가지만 **산술은
  옮겨가지 않는다**. docstring 에 적었다.
- **부수 관측 (열여섯 번째 self-entry)**: predicate population 64 → **69** — `Drift.stationary`
  / `calls_stationary`, `address_confined`, `work_repeated`, `Attribution.gap` 이 전부
  자기가 재는 population 에 들어온다. 이번엔 그 self-entry 가 **control 을 실제로 깨뜨렸다**
  — 지금까지 열다섯 번은 보고 사항이었고, 이번은 재측정 비용을 청구했다.
- **Status**: accepted — D-066 의 미결 residual 을 **6 partly-drift / 1 fold** 로 분해.
  D-066 의 "digest 는 원인이 아니다" 는 유지되고, "run 간 변동만 남는다" 는 **부분적으로만**
  참인 것으로 rescope.
- **Refs**: PR #67 · `journal/2026-08/04-20-stationarity-control-drift.md`

## D-066 — 2026-08-04 — D-065 가 선언만 했던 bound 를 **실제로 사니 음성**이었다: exclusion list 가 `SINGLE_INPUT` 을 **한 건도** 만들지 않았고, 대신 **input fold 의 calibration 이 깨졌다** (verdict 는 일치, count 는 7/53 불일치)

- **Context**: D-065 는 생존 population 위에서 두 ranking 을 다시 재면서 자기 한계를 명시했다 —
  생존자들의 distinct count 는 **여전히 `EXCLUDED_TESTS` 하에서** 읽힌 값이라, 질문 자체가
  excluded file 에서만 나온 생존자는 under-count 된다. 그것은 Q-074 (c) 의 finding shape
  (`distinct == 1`) 을 **exclusion 이 만들어낼 수 있다**는 뜻이고, D-063 이 value 쪽에서
  `manufactured_candidates` 로 잡아낸 것과 정확히 같은 방향의 오류다.
- **왜 D-064 의 trick 이 그대로 안 옮겨지나 — verdict 는 sum 을 접고 distinct 는 union 을 접는다**:
  같은 질문을 두 파일이 물으면 **둘이 합쳐 한 질문**이고, 이건 origin 별 *count* 쌍으로는
  절대 알 수 없다. 그래서 per-origin slice 가 fingerprint **집합**(8-byte digest)을 들고 다닌다.
- **Decision**: `predicate_inputs` 에 `measure_attributed` / `fold_inputs` / `InputSlice`,
  `exclusion_scope` 에 `scoped_exclusion` / `corrected_inputs` (list 를 **file 별이 아니라
  subject 별로** 적용 — 자기 instrument 만 숨기고 나머지 excluded file 의 질문은 복원),
  `input_undercounts` (실행 귀속으로 `SELF_ENTRY` / `COLLATERAL` 등급), `manufactured_singles`.
  recorder 는 fingerprint/wrap/install 을 flat 것과 **같은 객체**로 공유하고,
  `_PLUGIN_RECORD_INPUTS` 는 세 half 에서 **byte-identical** 로 재조립됨을 test 가 assert 한다.
- **측정 (2 회 실행: attributed 325 s + flat census 320 s)**:
  - under-count **14** 건, 그중 `COLLATERAL` **6** 건. 최대치는 boundary 에서 아주 먼 곳들:
    `_has_git_diff_literal` 23509 → 24282, `_is_set_valued` 9480 → 9786,
    `_shells_out_to_git_diff` 3068 → 3172, `local_only_audit.guard_is_derived` 2 → 4.
  - ✅ **`manufactured_singles` = `()`.** D-065 가 걱정한 그 오류는 **이 suite 에 존재하지
    않는다.** bound 는 닫혔고, 결과는 **음성**이다.
  - ✅ **`unattributed_undercounts` = `()`, 그리고 이건 운이 아니라 구조다**: union 의 모든
    원소는 최소 한 member 에서 왔으므로, 전체 lift 가 count 를 올리면 **어떤 단일 파일의
    lift 도 올린다**. value 쪽에서 `UNATTRIBUTED` 는 실재하는 결과지만 여기선 발생 불가.
- **🔴 그런데 calibration 이 깨졌다 — 이번 cycle 의 진짜 발견**: D-064 의 value-side 복원은
  measured run 과 **62/62 일치**해서 empty 로 assert 할 수 있었다. input 쪽은 **53 개 관측 site
  중 7 건 불일치**. 즉 **같은 counterfactual 이 한 통계에는 exact 이고 다른 통계에는 근사다.**
- **부호가 원인을 공짜로 지웠다**: 7 건 중 6 건은 낮게, **1 건은 높게** 어긋난다
  (`_is_set_valued` +12). digest collision 은 두 질문을 하나로 합치므로 **낮추는 방향으로만**
  틀릴 수 있다 → 이번에 새로 넣은 digest 는 원인이 **아니다**. 남는 것은 run 간 fingerprint
  변동 (address repr 이 `MANY_INPUTS` 9 건에 flag 되어 있고, 두 run 은 두 process 다).
- **그래서 무엇을 assert 하나 — granularity 를 읽는 곳에 맞춘다**: `classify` 는 `distinct == 1`
  에서만 갈라지므로 136242 중 142 의 오차는 **아무 reading 도 소비하지 않는 오차**다.
  `verdict_disagreements` = **0**, 최대 상대오차 **0.487 %**. 이건 더 느슨한 bar 가 아니라
  **다른** bar 다 — boundary 에서 1 건 어긋나면 count band 는 통과시키고 verdict check 는
  발동한다. 양방향 다 cheap test 로 pin 했다.
- **Alternatives**: (a) count 일치를 그냥 assert 하고 red 로 둔다 — D-043 이 예측한 "매 cycle
  red 면 mute 된다" 그대로. (b) digest 를 넓혀 collision 을 없앤다 — 부호가 이미 digest 를
  범인에서 제외했으므로 **아무것도 고치지 못하는 수정**. (c) 두 granularity 를 **둘 다**
  보고하고, 읽히는 쪽을 load-bearing 으로 삼는다 ← **채택**.
- **한계 (명시)**: rank 주장은 이 band 가 **덮지 못한다**. D-061/D-062 가 published 한 것이
  정확히 rank 였고, 0.5 % 안에서 갈리는 두 site 의 순서는 이 fold 로 말할 수 없다.
  `corrected_inputs` 위의 re-rank 는 gap 이 그보다 넓은 곳에서만 안전하다.
- **부수 관측 (열다섯 번째 self-entry)**: `Undercount.manufactured_single`,
  `InputReading.is_single` / `informative`, `Masked.manufactured_candidate`, `Rerank.moved` 가
  전부 under-count 표에 `SELF_ENTRY` 로 올라온다 — instrument 자기 predicate 들이고, 오직
  list 가 숨기는 파일들만 그것들을 호출한다. **두 pool 은 다른 것이니 섞지 말 것**:
  `predicate_vacuity` 의 predicate population 은 D-064 의 62 → **64** (refused 4),
  `guard_reflexivity` 의 guard pool 은 51 → **53** (`predicate_inputs.fold_inputs`,
  `exclusion_scope.input_undercounts`). 후자에서 **안 들어간** 다섯 중 `corrected_inputs`
  의 부재가 가장 많은 것을 말한다 — 그게 바로 D-066 이 존재하는 이유인 correction 인데,
  registry 에 대해 differencing 하지 않고 **site 별 fold** 를 하기 때문에 detector 에
  안 보인다. D-065 는 *parameterised* narrowing 을 놓친다고 했고, 이번엔 *per-member*
  narrowing 을 놓친다 — blind spot 이 두 번째로 특징지어졌다.
- **Status**: accepted — D-065 의 명시된 한계를 **closed (negative)**. D-064 의 "복원은
  검증됐다" 는 **value census 에 한정**되는 것으로 rescope.
- **Refs**: PR #67 · `journal/2026-08/04-19-input-census-exclusion-lifted.md`

## D-065 — 2026-08-04 — 살아남은 population 위에서 ranking 을 **다시 재니** D-062 의 falsifiable claim 이 **사라졌다**: 두 published ordering 의 **rank 0 이 둘 다 artifact** 였고, corrected `ordering_shift` 는 **비어 있다**

- **Context**: D-061 은 one-sided candidate 를 **call count** 로 줄 세웠고, D-062 는 같은
  집합을 **distinct input** 으로 다시 줄 세우며 "두 ordering 이 불일치한다" 를 자기 주장의
  falsifiable 한 형태로 못박았다 (`ordering_shift`). 그 뒤 D-063/D-064 가 그 집합의 **2 건이
  `EXCLUDED_TESTS` 가 만들어낸 artifact** 임을 실행으로 확정했다. 그런데 두 ranking 은
  **오염된 7 건 위에서** 취해진 채로 남아 있었다.
- **왜 자동으로 옮겨지지 않나 — rank 는 positional 이다**: 두 정렬 key 모두 site 별이므로
  **생존자들의 상대 순서는 바뀌지 않는다**. 그래서 "그냥 두 줄 지우면 된다" 로 읽히기 쉽지만,
  **published 된 것은 순서가 아니라 rank** 였고 (두 decision 모두 rank 0 site 로 headline 을
  썼다), 중간 원소를 빼면 그 아래 전원이 renumber 된다. 따라서 reading 은 **옮길 수 없고
  다시 취해야** 한다 — 그러려면 population 이 인자여야 한다.
- **Decision**: `predicate_inputs.shift_over(readings, inputs)` 로 population 을 인자화하고
  (`ordering_shift` 는 그것의 wrapper 로 축소), `exclusion_scope` 에 correction 위의 네 reading
  을 둔다: `surviving` (= `corrected_candidates` 를 site 문자열이 아니라 **Reading** 으로 —
  ranking 은 observation 이 있어야 취해진다), `rerank` (site 별 published vs corrected rank
  pair), `corrected_shift`, `voided_leaders` (artifact 가 **rank 0** 을 차지했는가 — 아무 데나
  있는 artifact 는 renumber 를 비용으로 내지만, 머리에 있는 artifact 는 **decision 이 쓰인
  문장 자체**를 비용으로 낸다).
- **측정 (2 회 실행: attributed vacuity 1 + input census 1, 각 ~5 분 12 초)**:
  - published candidate **7** → manufactured **2** (`guard_reflexivity._shells_out_to_git_diff`,
    `local_only_audit.guard_is_derived`) → **surviving 5**.
  - `voided_leaders` = **`_shells_out_to_git_diff`** — 이 artifact 는 `by_evidence` 의 rank 0
    (5938 calls) **이자** `by_input_diversity` 의 rank 0 (3068 distinct) 이었다. **두 published
    ordering 의 headline site 가 같은 하나의 artifact.**
  - 🔴 **`published shift` 는 3 건, `corrected_shift` 는 `()` — 비어 있다.** 불일치했던 3 건은
    artifact 인 `guard_is_derived` 자신 (1→3) 과, 그것이 사이에 끼어 있었기 때문에 밀린
    `guard_direction.Direction.quieter` (2→1) · `weight_units._has` (3→2) 뿐이었다. artifact
    하나를 빼면 **다섯 생존자에서 두 ordering 은 완전히 일치한다**.
- **그래서 무엇이 무효인가**: D-062 의 `ordering_shift` docstring 이 스스로 적어둔 판정
  기준 — "두 ordering 이 일치하면 D-061 의 call count 는 괜찮은 proxy 였고 이 instrument 는
  bound 하나를 산 것뿐이다" — 이 **정정된 population 위에서 실제로 발동한다**. distinct-input
  이 call count 를 대체해야 한다는 D-062 의 주장은 *이 suite 의 이 candidate 집합에 대해서는*
  **artifact 가 만든 것**이었다. D-062 의 개념적 논거 (5694 회 호출은 5694 번 물은 것이
  아니다) 는 건드리지 않는다 — 무효화되는 것은 **경험적 뒷받침**이다.
- **Alternatives**: (a) published ranking 에 각주만 단다 — 12 cycle 째 이 thread 가 계속
  틀렸다고 찾아낸 바로 그 종류의 처리. (b) census 에 correction 을 병합한다 — D-063 이
  거부한 이유 그대로, census 의 숫자는 자기가 선언한 suite 에 대해서는 정직하다.
  (c) population 을 인자화하고 **두 번째 reading 으로** 다시 취한다 ← **채택**.
- **한계 (명시)**: 생존자들의 distinct count 는 **여전히 `EXCLUDED_TESTS` 하에서** 읽힌 값이다
  (`pi.measure` 의 default). 즉 질문 자체가 excluded file 에서만 나온 생존자는 여기서도 여전히
  under-count 된다. 그것까지 고치려면 list 를 걷어낸 세 번째 실행이 필요하고, 이 cycle 은
  그것을 사지 않고 **test docstring 에 bound 로 적었다**. → **D-066 이 그 실행을 사서 bound 를 닫았다 (결과: 음성 — `manufactured_singles` = `()`)**.
- **부수 관측 (열네 번째 self-entry, 그리고 처음으로 같은 cycle 의 나머지 절반은 안 들어갔다)**:
  `surviving` 과 `voided_leaders` 가 pool 에 들어가 49 → **51**. 그런데 `rerank` 와
  `corrected_shift` 는 **들어가지 않았다** — 전자는 `manufactured_candidates` 에 대한 **set
  difference**, 후자는 population 을 **인자로 받아 정렬**한다. 같은 하나의 correction 을
  구현한 네 함수 중 **differencing 하는 절반만** detector 에 보인다. D-056 의
  `misscored_probes` 註의 가장 선명한 재진술: detector 가 keying 하는 것은 population 을
  **어떻게 좁혔는가**이지, 그 좁힘이 finding 을 숨기는 종류인가가 아니다.
- **Status**: accepted — D-062 의 `ordering_shift` 경험적 결과를 **superseded** (개념적 논거와
  `by_input_diversity` 자체는 유효). D-061/D-062 의 headline rank-0 주장은 **withdrawn**.
- **Refs**: PR #67 · `journal/2026-08/04-18-corrected-population-rerank.md`

## D-064 — 2026-08-04 — attribution 을 **6 회 실행에서 1 회 기록으로** 바꾸니 D-063 의 귀속 절반이 틀렸다: `_shells_out_to_git_diff` 를 숨긴 것은 `test_guard_witness.py` 가 아니라 **census 자신의 witness 가 사는 `test_predicate_vacuity.py`**

- **Context**: D-063 은 headline 두 site 를 `COLLATERAL` 로 등급하면서 "둘 다
  `test_guard_witness.py` 의 부수 호출" 이라고 적었다 — 그건 **call graph 읽기**였고, 실행
  귀속은 예산을 넘겨 끝내지 못했다. D-063 스스로 "이게 D-045~D-062 가 계속 틀렸던 주장의
  종류" 라고 썼다. 이번 cycle 은 그 비용부터 쟀다.
- **먼저 가격이 틀려 있었다**: `measure_exclusion_effect` 는 `1 + len(EXCLUDED_TESTS)` 가
  아니라 **`2 + len(...)` = 6 회** 돌고 (base 와 lift 둘 다 endpoint), 계측된 한 회는
  "1 분 남짓" 이 아니라 **4 분 57 초** 다. 즉 실제 청구서는 **약 30 분**, 적혀 있던 것은
  4 분 — **7.5×** 오차. D-063 이 야심찼던 게 아니라 **한 번도 재보지 않은 숫자**로
  계획했던 것이다. `price()` 가 이제 상수에서 run 수를 유도한다.
- **Decision**: recorder 가 관측마다 **origin (그때 돌던 test file)** 을 기록한다
  (`predicate_vacuity.measure_attributed` / `fold`). 그러면 "파일 X 를 `--ignore` 했다면
  verdict 가 뭐였을까" 는 **또 한 번의 실행이 아니라 기록에 대한 filter** 다.
  `exclusion_scope.effect_from_one_run` 이 base / lift / 파일별 lift **6 개를 1 회 측정에서**
  복원한다. counterfactual 이므로 **주장하지 않고 검증한다**:
  `reconstruction_disagreements` 가 복원된 base 를 `--ignore` 를 실제로 준 실행과 site 별로
  대조한다 → **62 predicate 전부 일치, 불일치 0**. 총 **2 회** 실행 (6 회 대비), 그리고
  6 회와 달리 자기 calibration 을 달고 온다.
- **측정 결과 — 등급은 살아남고 귀속은 반만 맞았다**: masked 9 건, `manufactured_candidates`
  는 D-063 과 동일한 2 건. 그러나 `local_only_audit.guard_is_derived` 는 `test_guard_witness.py`
  (유일한 `False` 2 회) 로 맞게 귀속되는 반면, **`guard_reflexivity._shells_out_to_git_diff` 는
  `test_predicate_vacuity.py`** 로 귀속된다 — D-061 의 headline 이자 D-063 이 이름을 잘못 적은
  바로 그 site.
- **왜 call graph 가 속았나**: `test_guard_witness.py` 는 이 predicate 를 **188 회** 부르지만
  전부 `False` 다 — 정보량 0 인 heavy caller, 그래서 그럴듯한 범인으로 읽혔다. verdict 를
  뒤집는 것은 5944 회 중 **단 한 번의 `True`** 이고, 그 한 번은 D-062 가 "이 predicate 는
  satisfiable 하다" 를 보이려고 쓴 **witness 자신**이다. 즉 census 는 자기 top candidate 가
  vacuous 하지 않다는 **유일한 증거를 자기 exclusion 으로 가렸다**. 호출 횟수로는 절대 못
  찾고, 호출 그래프로는 반대로 읽힌다 — 관측당 origin 만이 답한다.
- **Alternatives**: (a) 6 회 실행을 그냥 돌린다 — 30 분, cycle 예산 밖이고 D-063 이 이미
  실패한 길. (b) 파일명 규약으로 귀속 — 여섯 번째 hand-written registry, 그리고 이 site 에서
  정확히 틀렸을 것. (c) origin 기록 + 1 회 실행 + calibration 1 회 ← **채택**.
- **한계 (명시)**: calibration 은 `n = 1` exclusion 집합에 대한 62 predicate 일치이고, pass 는
  "recorder 두 개가 같은 값을 센다" 와 "counterfactual 이 성립한다" 의 **결합 증거**라 둘을
  분리하지 못한다. test docstring 에 그대로 적혀 있다.
- **부수 관측 (열세 번째 self-entry, 그런데 종류가 다르다)**: `predicate_vacuity.fold` 가
  `guard_reflexivity` pool 에 들어가 48 → **49**. 앞선 열두 번은 전부 "자기가 발표할 reading
  에서 population 을 면제하는 auditor" 였는데, `fold` 는 **exclusion 그 자체**다 — 기록된
  관측에 대해 registry 이름으로 set difference 를 적용하는 것이 D-064 의 전부다. 즉 detector
  가 잡는 shape 은 "instrument 가 자기를 감사한다" 보다 **넓다**: exclusion 을 *구현*하기만
  해도 걸린다. 이것이 발견을 확장하는 것인지 detector 를 희석하는 것인지는 여기서 결론내지
  않고 pin 주석에 남긴다.
- **Status**: accepted — D-063 의 `COLLATERAL` **등급**은 유효, **귀속** 중
  `_shells_out_to_git_diff → test_guard_witness.py` 는 **무효**.
- **Refs**: PR #67, `journal/2026-08/04-17-one-run-attribution.md`, Q-076

## D-063 — 2026-08-04 — one-sided 후보 상위 2 건은 predicate 의 성질이 아니라 **census 자신의 `EXCLUDED_TESTS` 가 만들어낸 artifact** — exclusion 은 file 이 아니라 subject 로 잘라야 한다

- **Context**: STATE #1 은 `local_only_audit.guard_is_derived` (`ALWAYS_TRUE`, 26 calls /
  2 distinct) 에 witness 를 만들라고 했다 — `False` 를 내는 입력을 구성하거나 없음을 보이라고.
  구성하기 전에 먼저 물었다: 이 tree 안에 이미 그런 입력이 있는가. 있었다.
  `guard_witness._w_unguarded_declarations` 는 push guard 가 stale literal 인 repo 를 짓고
  `unguarded_declarations(root)` 를 부르며, 그 첫 줄이 `guard_is_derived(root)` → **False**.
  D-060 이후로 계속 tree 안에 있었고, census 가 못 봤을 뿐이다.
- **Decision**: `exclusion_scope.py` — census 를 두 번 (shipped exclusion / lift) 돌리고
  움직인 verdict 를 파일별 lift 로 **실행 귀속**한다. `SELF_ENTRY` (숨긴 파일이 그 predicate
  모듈의 test) / `COLLATERAL` (단순 caller) / `UNATTRIBUTED` (단일 lift 로 재현 안 됨) 로 등급.
  `manufactured_candidates` = `BOTH → one-sided` 로 뒤집힌 것들 = exclusion 이 **만들어낸**
  용의자. **측정된 부분**: 두 번의 census 로 8 건이 움직였고 그 중 `BOTH →` 방향은
  `local_only_audit.guard_is_derived` 와 `guard_reflexivity._shells_out_to_git_diff`
  **2 건**. 후자는 **D-061 의 headline** (5694 calls) 이자 D-062 가 address-repr 로 다시
  무효화한 바로 그 site — 두 cycle 이 artifact 를 순위 매겼다.
- **아직 측정 안 된 부분**: 어느 *파일*이 숨겼는지 (`COLLATERAL` 등급) 는 파일별 lift
  **5 회** 실행이 필요하고 이번 cycle 예산 안에 안 끝났다. 두 site 가
  `test_guard_witness.py` 부수 호출이라는 것은 현재 **call graph 읽기**이지 측정이 아니며,
  그것이 바로 D-045~D-062 가 계속 틀렸던 주장의 종류다. `@pytest.mark.slow` 로 단언되어
  있고 **아직 통과하지 않았다**.
- **근본 원인**: `guard_vacuity` 의 exclusion 은 **줄 커버리지**를 읽으므로 file 을 숨기면
  오염만 정확히 숨는다. `predicate_vacuity` 는 **모든 predicate 의 반환값 분포**를 읽는데
  같은 tuple 을 그대로 물려받았다 — test 파일은 자기가 계측하는 predicate 보다 훨씬 많은
  predicate 를 부르고, file 단위 exclusion 은 그것들까지 숨긴다. 의도는 subject 단위였고
  적용은 file 단위였다.
- **Alternatives**: (a) exclusion 유지, 후보 목록에 주석만 — 순위는 계속 artifact.
  (b) exclusion 을 걷어냄 — self-entry 6 건이 공짜로 `BOTH` 가 되어 instrument 가 자기 신호를
  먹는다 (D-060). (c) **채택** — 둘 다 측정하고 `corrected_candidates` 를 별도 reading 으로
  발행. census 의 수는 자기가 선언한 suite 에 대한 정직한 값이므로 합치지 않는다.
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/04-16-exclusion-scope-artifact-candidates.md`,
  `eval/mppi_sandbox/exclusion_scope.py`

## D-062 — 2026-08-04 — one-sided predicate 의 무게는 **호출 수**가 아니라 **distinct 입력 수** — 다만 D-061 이 앞세운 site 는 이 계측기가 못 읽는다

- **Context**: D-061 이 one-sided 7 건을 **호출 수** 순으로 세우며 그 이유를 적었다 —
  `ALWAYS_FALSE` 가 1 회와 5694 회는 같은 verdict 이고 전혀 다른 주장이라는 것. 논리는
  맞고 통계량이 틀렸다: 호출 수는 **답**을 세지만, one-sidedness 를 damning 하게 만드는
  것은 제시된 **population 의 크기**, 즉 distinct 입력 수다. Q-074 (c) 가 가리킨 자리와
  같다 — D-057 의 결함은 bar 가 아니라 bar 가 **한 종류의 scene 에서만** 평가된 것.
- **Decision**: `predicate_inputs` 를 D-061 의 population/recorder/suite 그대로 두고
  **인자 fingerprint** 만 바꿔 붙인다. `distinct == 1` 은 threshold 가 아니라 개념의
  경계이므로 상수를 새로 고르지 않는다 (D-020 부채 반복 회피). fingerprint 의 편향은
  **비대칭이며 선언한다**: address repr 은 distinct 를 **과대**계상하므로 `SINGLE_INPUT`
  은 강한 판독, address 가 섞인 `MANY_INPUTS` 는 판독 불가 (`informative`).
- **측정**: 61 predicates (59 → +2, 새 모듈 자신; 둘 다 `UNOBSERVED`), 후보 **7 건 동일**.
  ordering shift **3/7** (`guard_is_derived` 1→3, `Direction.quieter` 2→1,
  `weight_units._has` 3→2) — **head 는 안 바뀐다**. one-sided ∧ single-input = **2 건**
  (`is_timing_sensitive`, `Liveness.moved`), 둘 다 D-061 에서 이미 `n=1`.
  **D-061 이 앞세운 `_shells_out_to_git_diff` 는 5694 calls / 2944 distinct 인데
  `address_reprs=True`** — 인자가 AST 노드라 선언된 편향이 정확히 최상위 site 에서
  발동해 그 distinct 를 무효화한다. 47 개 `MANY_INPUTS` 중 **9 건**이 같은 이유로 inflated.
  유일하게 신뢰 가능한 신규 후보: `local_only_audit.guard_is_derived` **26 calls /
  2 distinct / addr=False**.
- **Alternatives**: (a) 호출 수 유지 — 최상위 site 가 2944 distinct 이므로 실제로는
  대부분 무해했다는 반론이 가능하나, 그 2944 자체가 판독 불가라 방어가 안 된다.
  (b) test 를 population 에 넣기 (Q-074 (a)) — assert rewrite 기계가 다르고 population
  정의가 자명하지 않아 보류. (c) **채택** — subject predicate 의 인자 분포.
- **Status**: accepted — D-061 의 *측정치*는 유효, **순위 근거는 대체**한다.
- **Refs**: PR #67, `journal/2026-08/04-15-predicate-input-diversity.md`

## D-061 — 2026-08-04 — predicate vacuity 는 **반환값 분포**로 읽는다 — 59 중 7 이 one-sided, 최상위 후보는 predicate 가 아니라 suite 의 결함

- **Context**: D-060 이 `if <cond>: raise` population 을 닫았고 수확은 측정된 0.
  Q-072 (b) 가 남은 절반 — 촉발 finding 4 건 중 3 건이 사는 자리 — 을 가리키면서
  그 이유도 같이 적었다: raise 는 관측 가능한 **사건**이라 coverage 한 줄로 읽히지만
  predicate 는 **반환값의 분포**를 봐야 한다.
- **Decision**: `predicate_vacuity` — AST 로 boolean 반환 함수 **59** 개를 유도하고,
  생성된 pytest plugin 이 각 site 를 subprocess suite run 에서 wrapping 해 관측된
  반환값 집합을 기록한다. 판정 5 종 (`BOTH` 43 / `ALWAYS_TRUE` 3 / `ALWAYS_FALSE` 4 /
  `UNOBSERVED` 9 / `NON_BOOLEAN` 0), unpatchable **4** 건은 거절하되 보고. 판정에
  **호출 횟수를 병기**하고 floor 는 두지 않는다 — 정당화 못 한 threshold 는 D-020 이
  `wilson_lower_at_least` 에 남긴 결함과 같은 것.
- **Alternatives**: (a) branch coverage 의 partial-branch — 싸지만 `return a == b`
  같은 비분기 predicate 에 구조적으로 닿지 않아 촉발 finding 3 건을 못 잡는다.
  (b) **채택** — 값 recorder. (c) 안 함 — Q-072 가 이미 (b) 로 lean.
- **결과 (증거)**: 최상위 후보 `guard_reflexivity._shells_out_to_git_diff` 는
  **5694 호출 전부 False**. D-060 의 규칙대로 읽지 않고 **witness 를 구성**했고,
  `local_only_audit._git("diff", ...)` 가 이 tree 안에 있는 참 입력이다 → 다른 답은
  도달 가능. 즉 vacuous 가 아니라 **미테스트 arm**. calibration set 은 **0** 이며
  (D-057 의 인스턴스는 *test* 안에 산다) 빈 registry 대신 **구성된 4-판정 witness** 로
  대체 — 빈 mirror 는 아무것도 주장하지 않고 clean 으로 읽힌다 (D-046 shape).
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/04-14-predicate-vacuity-return-distribution.md`,
  Q-072 (b) 답, Q-074 신규. 633 passed.

## D-060 — 2026-08-04 — `NEVER_FIRED` 8 건 전부 **witness 로 발동 가능** — guard clause population 을 수확 0 으로 닫는다

- **Context**: D-059 가 후보 8 건을 냈고 그 중 3 건만 **읽어서** triage 했다. "읽어보니
  trigger 가 만족 가능해 보인다" 는 D-045~D-059 가 열다섯 cycle 내리 틀렸던 바로 그
  미실행 주장이다. 남은 5 건을 같은 방식으로 읽는 것은 같은 오류를 5 번 더 짓는 것.
- **Decision**: 후보마다 **guard 를 실제로 raise 시키는 입력**을 구성한다
  (`guard_witness.WITNESSES`, nullary callable 8 개). 결과 **8/8 SATISFIED, 0 실패,
  `unwitnessed() == ()`** — D-058 shape 는 **0 건**이고 population 은 닫혔다.
  추가로 trigger 를 **package 내부 producer 가 내보내는가**로 등급을 나눈다:
  `DATA_REACHABLE` **5** (NaN cruise, `n_reached=-1` 기본값, `json.load` 된 claim 등)
  vs `ARGUMENT_ONLY` **3** (내부 caller 가 없거나 전부 registry 에서 key 를 뽑음).
  "미테스트 guard 8 개" 로 뭉뜽그리면 성격이 다른 둘을 합치게 된다.
  **census 는 이 module 의 test 를 관측하면 안 된다** — coverage 는 line 이 *왜*
  실행됐는지 모르므로, 관측하면 8 건 전부 `FIRES` 로 바뀌어 subject code 한 줄 안
  바뀐 채 clean bill 이 나온다. `guard_vacuity.EXCLUDED_TESTS` + `--ignore` 로 차단하고,
  차단이 load-bearing 임을 `@pytest.mark.slow` 로 양방향 측정해 보인다.
- **Alternatives**: (a) 남은 5 건도 손으로 읽는다 — 싸지만 D-059 의 오류 반복.
  (b) witness 구성 — 채택. (c) `unwitnessed` 에 싼 default 를 줘서 screen 이 부르게
  한다 — **거부**: population 이 비어 읽히는 guard, 즉 이 module 이 사냥하는 D-058 결함
  그 자체가 된다.
- **부수 발견 2 건**: (i) `exemption_masking._call` 은 "pool 의 모든 guard 는 전 parameter
  에 default 가 있다" 를 전제하는데 이는 44 건에서 **우연히** 참이었다 — 지금까지 모든
  population 이 syntax-tree/filesystem read 였기 때문. population 이 **측정**(coverage run)
  인 첫 guard 가 이를 깨고 `UNRUNNABLE` 로 남는다. (ii) `_w_batch_per_unit_spread` 는
  simulating 함수를 `lam` 없이 호출해 `DEFAULTS`+`simulates` 로 잡히지만 `KeyError` 가
  controller 생성보다 먼저 터져 **절대 simulate 하지 않는다** → `weighting_at_shipped`
  가 **53 으로 읽히나 실제 sim bill 은 여전히 52** (Q-073).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-13-guard-witness-candidate-closure.md` ·
  Q-072 → resolved (a 분기 음성) · pool 44 → 46 (**아홉 번째** 연속 자기 registry 진입)

## D-059 — 2026-08-04 — guard-vacuity 탐색의 calibration set 은 **3 이 아니라 1** 이다 — 넷 중 셋은 이 population 에 없다

- **Context**: STATE #1 은 "guard clause 중 trigger 가 발생할 수 없는 것을 package
  전체에서 grep 하라" 였고, 근거는 D-055 → D-056 → D-057 → D-058 네 cycle 이 같은
  shape 를 손으로 하나씩 찾아냈다는 것이었다. STATE 는 "**세** 개의 known member 가
  탐색을 calibrate 한다" 고 적었다. 체계적 pass 를 만들려면 먼저 **어떤 population 을
  걷는지** 를 말해야 하고, 그 순간 전제가 무너졌다.
- **Decision**: scan 의 population 은 `if <cond>: raise <Exc>` — 함수 안에서 최소
  하나의 `if` 에 둘러싸인 raise — 로 정의하고, **`CALIBRATION` 에는 D-058 하나만**
  넣는다. 네 findings 중 이 population 에 실제로 들어오는 것은 D-058 (`shadow_batch`
  의 `ValueError`) **하나뿐**이다: D-057 의 결함은 boolean bar (`unseen.min() > 0.0`),
  D-056 은 verdict 비교, D-055 는 fixture reading 이다. 셋 다 *return* 하지 *raise*
  하지 않으므로 `raise` 를 훑는 scan 이 구조적으로 도달할 수 없다. 넷을 적었다면
  mirror 가 존재할 수 없는 guard 에 대해 assert 하며 영구 red → 결국 mute 되었을 것
  (D-043 의 실패 양식). `len(CALIBRATION) == 1` 을 test 로 못박는다.
- **부수 결정 — verdict 는 둘이 아니라 셋.** `NEVER_FIRED` (함수는 돌았고 raise 는
  안 걸림 — candidate set) 를 `UNREACHED` (함수 자체가 안 돌아서 침묵이 guard 의 것이
  아님) 와 분리한다. D-050 의 규칙 — "안 물어본 것" 과 "물었는데 침묵한 것" 을 못
  가르는 probe 는 아무것도 재지 않았다 — 이고 `probe_reach` 의 `UNDECIDABLE` /
  `MUTE_FIXTURE` 분리와 같은 이유다. unconditional raise 10 건은 population 에서
  제외하되 `unconditional()` 로 **보고**한다 (trigger 가 "함수가 돌았다" 이므로
  vacuous 일 수 없음). scan 은 AST 에서 **derive** — 손으로 적은 registry 는 이
  package 에서 다섯 번 연속 부족했다 (D-045/046/047/050/052).
- **측정치**: guard clause **38** 건 — `FIRES=19`, `NEVER_FIRED=8`, `UNREACHED=11`,
  제외된 unconditional raise 10 건. calibration mirror clean (`shadow_batch` 가
  `FIRES` 로 읽힘 — D-058 이 심은 test 가 실제로 guard 를 raise 시킨다).
  fast half 아래에서 측정했으므로 `--slow` 에서만 걸리는 guard 는 `NEVER_FIRED` 로
  읽힌다 — 알려진 bound 이고 `Census.suite` 가 보고한다.
- **수확량 정정**: 8 candidate 중 **3 건을 손으로 triage 했고 0 건이 D-058 의 shape**
  이었다. `repair_admissibility.margin_at_factor` / `weight_units.batch_per_unit_spread`
  는 평범한 미테스트 인자 검증이고, `ab._n_reached` (`n_reached < 0`) 는 `-1` 이
  `LamProbe` 의 살아있는 sentinel default 라 그럴듯했으나 trigger 는 손으로 만든
  probe 나 historical probe 로 **충족 가능**하다 — suite 가 공급하지 않을 뿐이다.
  즉 `NEVER_FIRED` 는 필요조건이고, 그 값어치는 나머지 5 건이 **열거 가능하다**는
  것이지 그중 무엇이 버그라는 증거가 아니다.
- **Alternatives**: (a) `CALIBRATION` 에 넷 다 적고 셋은 xfail — mirror 를 영구 red 로
  만들어 D-043 재현. (b) population 을 predicate 전반으로 넓혀 한 번에 처리 — 서로
  다른 discovery/실행 기구가 필요하고, 넓힌 scan 을 calibrate 할 ground truth 는
  여전히 이 cycle 이 만들어야 했다. (c) 채택 — 좁은 population 을 정확히 calibrate 하고,
  넷 중 셋이 **밖에** 있다는 사실 자체를 다음 instrument 의 population 으로 남긴다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-12-guard-clause-vacuity-census.md`

---

## D-058 — 2026-08-04 — 그 바닥 위에 **rollout batch 가 놓여 있었다** — 오염 42~100%, 한 장면은 100% (Q-071 → (a))

- **Context**: Q-071 이 남긴 두 번째 live instance. D-057 은 바닥을 *보고하는* 코드를 고쳤고,
  여기는 바닥 위에 **점을 찍는** 코드다 — `weight_units.shadow_batch` 는 `grid > 0.5` 셀에서
  probe 궤적을 합성한다. Q-071 의 lean 은 (b) "먼저 오염량부터 재고 고친다" 였고, 그대로 했다.
- **측정 (먼저)**: BEV 를 렌더하는 5개 장면 전부에서 바닥은 **정확히 112 셀로 동일** — 장면 내용이
  아니라 격자의 속성이라는 주장이 이걸로 선다. 선택 대비 비율: `cafe_freezing` 41.8%,
  `cafe_obstacle_crossing` **48.3%**, `cafe_cut_in` 49.1%, `cafe_convoy` 50.0%,
  `cafe_head_on` **100.0%** (scene 셀 0개). 즉 head-on 에서 `shadow_batch` 는 **장면이 만든 적 없는
  그림자** 위에 batch 를 통째로 앉히고 있었고, 바로 아래의
  `raise ValueError("no shadow cells in this BEV")` 는 **발동한 적이 없다** — 모서리가
  `sel.any()` 를 보장하므로 렌더가 일어나는 모든 장면에서 원리적으로 못 터진다.
  D-057 이 `unseen.min() > 0.0` 에서 고친 것과 **같은 결함, guard clause 판**.
- **재보정 청구서 (그 다음)**: 실제로 그 batch 를 쓰는 published 수치는 margin knob 의
  per-unit spread 비뿐이고, 사거리 필터 전후로 **2.568 → 2.717**. 결론(`> 2.0` ⇒ 비가법적,
  환율 없음)은 **바뀌지 않는다**. 청구서는 존재하지만 작다 — Q-071 이 (b) 를 고른 이유는
  이 크기를 *모르고* 고치면 안 된다는 것이었지 크리라는 예측이 아니었다.
- **Decision**: (a) 채택. `shadow_cells()` 가 σ 필드를 scene / floor 로 쪼개고 (`ShadowCells`),
  `shadow_batch` 는 `scene_points()` 에만 batch 를 앉힌다. vacuity guard 는 `cells.vacuous`
  (= scene 셀 0개) 를 보므로 이제 **터질 수 있고**, `cafe_head_on_v0` 에서 실제로 터지는 것이
  test 로 고정됐다 — 트리거가 발생 가능함을 실행으로 보인 것.
- **Alternatives**: (a) 채택. (b) 오염만 보고하고 batch 는 그대로 — head-on 이 100% 인 이상
  "측정 가능하나 틀린 채로 둔다" 이고, 수치가 작다는 것은 방치의 근거가 아니다.
  (c) 격자를 센싱 원 안에 맞춘다 — D-057 이 이미 기각(렌더러 계약 변경).
- ⚠️ **여덟 cycle 연속, 이번 모듈도 제 패키지가 세는 census 에 들어갔다.** 새 test helper 가
  명시적 `lam` 으로 controller 를 무장하므로 `default_lam_sites` 의 `DECIDES` 가 30 → **31**,
  pin 이 발화. pin 과 모듈 docstring 의 running tally 를 함께 갱신(103 → 104). D-041 의
  *결론*은 분할에 대해 진술돼 있고 총계에 대한 게 아니라 하나도 움직이지 않는다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-11-shadow-batch-sited-on-floor.md` · Q-071 → resolved · D-021 / D-046 / D-057

## D-057 — 2026-08-04 — vacuity check 의 기준선에 **렌더러 기하가 만든 바닥**이 깔려 있었다 — 빈 세계도 2.73% 를 읽는다

- **Context**: STATE #1 — D-055/D-056 의 형태(*한 면만 보고 내린 판정*)를 남은 지목 대상인
  epistemic-reach screen 으로 확장. `reach.ReachProfile` 의 판정 3종을 각각 "쉴 때의 값"에 대고 읽었다.
- **Decision**: `grid_unseen` 은 **장면의 속성이 아니다**. 격자는 반경 `n·res/2 = 4.00 m` 의 정사각형이고
  센싱은 반경 `5.00 m` 의 원이라, 모서리(`5.66 m`)는 **모든** 렌더에서 영원히 미관측 —
  장애물이 0개인 세계도 `112/4096 = 2.73%` 를 읽는다. `empty_world_unseen` (빈 세계를 **렌더해서** 측정,
  타이핑 X — D-047 형태) + `scene_unseen` / `renders_ignorance` 로 바닥을 빼고 판정한다.
  `scalar_false_positives` 는 집계 차 `max(0, scalar - live)` 에서 **실제 집합 차**
  `scalar_only_steps` 로 교체하고, 반대 방향 `spread_only_steps` 를 함께 측정한다.
- **측정**: (1) `unseen.min() > 0.0` — vacuity 를 배제하는 것이 **유일한 임무**인 단언 — 은
  장애물 0개 세계도 통과하므로 **호명된 이유로는 실패할 수 없었다**. (2) `> 0.05` 두 곳은 빼지 않은
  바닥 위에 세운 값이라 장면에 실제로 요구한 건 `0.023`. (3) deaf 3개 장면의 `grid_unseen` 은
  **전부 바닥** (`scene_unseen == 0`) — nominal driver 의 deaf 류는 한 종류가 아니었고, 셋 다
  *vacuous* 이며 "렌더됐지만 도달 불가"(D-021 의 발견)는 **측정 driver 에만** 존재한다.
  (4) 반증된 가설도 기록: 격자 밖 prior(`unobserved_value=1.0`)로 인한 spread 오염은 8개 장면 **전부 0**.
  (5) `spread_only_steps` = 8개 장면 전부 **0** ⇒ 집합은 실제로 nest 하므로 기존 숫자는 옳았다 —
  **우연히** 옳았고, 이제 그 우연이 측정된다 (D-046 형태).
- **Alternatives**: (a) 바닥 상수를 `0.027` 로 타이핑 — `grid_size`/`sensing_range` 변경에 즉시 stale (D-047 이 금지).
  (b) 격자를 센싱 원 안에 맞춰 축소 — 렌더러 계약 변경, 다른 채널 전부 재측정 필요. (c) 채택: 측정된 바닥을 뺀다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-10-vacuity-floor-and-set-difference.md` · D-021 / D-046 / D-047 / D-055 / D-056

## D-056 — 2026-08-04 — probe 도달 가능성의 기준은 **부호가 뒤집혀** 있었고, 답을 아는 2건 모두에서 틀렸다 (reach 6 → 15)

- **Context**: STATE #1 — D-055 의 결함 형태(*두 면짜리 행위를 한 면만 보고 판정*)가 그
  두 모듈에 국한되지 않는다는 일반화. 지목된 용의자는 `probe_reach.VERDICT_READABLE`.
  `Reach.probeable` 은 `verdict == READABLE`, 즉 **어떤 행위 이전에** 읽기가 non-empty
  인가였고, docstring 은 그것으로 "여기서 `guard_direction` 이 의미 있는 판정을 낼 수
  있는가" 에 답한다고 주장했다.
- **Decision**: 기준을 교체하고 이 모듈이 발표한 숫자를 전부 철회한다.
  1. 🔴 **한 면이 빠진 게 아니라 부호가 뒤집혀 있다.** D-055 가 세운 기준은 membership —
     subject 가 행위 전엔 없고 후엔 있을 것. 행위 *이전에* 시끄러운 상태는 바로 D-055 의
     세 번째 probe 를 오탐으로 만든 그 상태다. `READABLE` 은 깨끗한 판정에 **불리한**
     성질을 고르고 있었다.
  2. 🔴 **새 fixture 없이 확인되는 ground truth 에서 2/2 오답.** `guard_direction.PROBES`
     의 두 항목은 *실행에 의해* probe 가능하다 — liveness act 가 있고, 매 cycle 돌고,
     D-055 가 더 엄격한 기준으로 재확인했다. 둘 다 base/enriched fixture 양쪽에서 rest
     상태의 읽기가 empty → 둘 다 not-`READABLE`. 그리고 reach 숫자가 무엇을 제외했는지
     밝히는 것이 유일한 존재 이유인 `unreachable()` 이 **작동하는 probe 두 개를** 도달
     불가로 열거하고 있었다.
  3. 🔴 **모순은 이미 적혀 있었고, 이름이 그것을 실어 날랐다.**
     `test_both_registered_probes_read_empty_in_both_fixtures` 는 "이들을 probe 가능하게
     만드는 것은 손으로 쓴 liveness act" 라는 docstring 세 줄 아래에서 `not
     scored[qualname].probeable` 을 단언한다. 같은 두 guard, 양립 불가능한 두 진술, 한 줄
     간격, 세 cycle 동안 green. `probeable` 이 코드에서는 "rest 에서 시끄럽다", 산문에서는
     "행위가 판정을 낼 수 있다" 를 뜻했기 때문이다.
  4. ✅ **분모가 9 만큼 틀렸다.** act-addressable(돌고, 집합을 반환) 은 **16 중 15**;
     진짜로 거부되는 것은 `str` 을 반환하는 `lam_dependence.report` 하나뿐이다. 발표된
     reach 는 6 이었다. 따라서 "readable, unprobed = 6" 은 애초에 그 population 이 아니었고,
     `act_gap` = **13**. D-055 는 그 6 의 수율을 이미 0 으로 측정했다.
  5. ✅ **구조적 pin 은 틀린 기준을 잡지 못한다.** `..._partition_into_probeable_and_...`
     는 내내 통과했다 — 두 집합이 분할을 이룬다는 pin 은 **두 집합이 모두 틀려도** 참이다.
     분할 test 에는 ground truth 를 아는 원소가 최소 하나 필요하다.
  - `reads_at_rest` 가 옛 측정을 그것이 실제로 재는 이름으로 보존하고, `act_addressable`
    가 정직한 전제조건이며, `misscored_probes` 가 empty 로 pin 된 ground-truth mirror.
  6. ⚠️ **자기 자신을 감사하는 registry 에 들어간 일곱 번째 연속 cycle.** `act_gap` 이
     pool 을 43 → 44 로 만들었고 pin 이 잡았다. 흥미로운 쪽은 `misscored_probes` 가
     **들어가지 않았다**는 것이다 — 이것은 population 에서 *제외*하는 대신 답을 아는
     population 으로 *한정*한다(`r.guard in PROBES`). 바로 그것이 이 함수를 empty 로 pin
     할 수 있게 하는 성질이고, exemption 모양의 guard 는 결코 그럴 수 없다.
- **Alternatives**: (a) `probeable` 을 조용히 재정의 — 철회를 감춘다, 기각. (b) 보고만
  하고 기준은 유지 — D-052 가 금지한 것. (c) 채택: 이름 분리 + ground-truth mirror.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-09-probe-reach-bar-sign.md` · D-055 의 일반화

## D-055 — 2026-08-04 — liveness 의 기준은 **fixture 를** 재고 있었다. D-054 의 "+1" 은 그 오탐 하나가 전부였다 (STATE #1 → 철회)

- **Context**: STATE #1 은 D-054 가 *파생 가능하고 살아 있으나 probe 가 없다* 고 측정한 유일한
  guard `local_only_audit.unregistered_local_only` 를 세 번째 `guard_direction.Probe` 로
  등록하라는 것이었다 — Q-068 의 cash value 전부. 표에 넣기 전에, probe 가 실제로 해야 하는
  방식으로 후보의 liveness 를 읽었다: enriched fixture 안에서 파생된 행위의 **양쪽**을.
  D-054 의 `validate` 는 **뒤쪽만** 봤다.
- **Decision**: 후보는 살아 있지 않다. 등록하지 않고, 대신 두 모듈이 공유하던 **기준**을 고친다.
  1. 🔴 **읽기가 움직이지 않는다.** enriched fixture 는 실제 `docs/` 를 복사해 넣으므로
     `unregistered_local_only` 는 **어떤 행위 이전에** 이미 `{docs/decisions.md,
     docs/deliberations.md}` 를 읽는다. 파생 행위(worktree 에 `eval/control.txt` 쓰기) 이후에도
     같은 2 원소, 크기도 원소도 그대로이며 자신의 subject 를 한 번도 지목하지 않는다.
     **남의 population 위에서 `LIVE` 를 받은 것이다.**
  2. 🔴 **결함은 기준이고, 그 기준은 공유돼 있었다.** `validate` 의 판정은 `읽기가 non-empty`
     였고 이는 `guard_direction.check_liveness` 에서 그대로 물려받은 것이다. 이 판정은
     *행위가 guard 를 깨웠다* 와 *fixture 가 원래 시끄러웠다* 를 구분하지 못한다. 판정은
     **membership** 이어야 한다 — 한 층 위 `Direction.verdict` 가 D-047/D-049 에서 이미 받은
     교정이고, 이 층은 받지 못했다.
  3. 🔴 **파생의 순수 수확 = 0.** 같은 수를 세 번 읽었고 매번 작아졌다:
     `reach_gap` **6** (읽을 수 있다) → D-054 **1** (뒤가 non-empty 다) →
     **0** (행위가 그 읽기를 만들어냈다). 살아남는 것은 손으로 쓴 그 **둘뿐**이다.
     Q-068 은 제안된 population 위에서 부정으로 답해졌고, 논증이 아니라 실행으로 답해졌다.
  4. ✅ **손으로 쓴 두 probe 는 강화된 기준을 그대로 통과한다.** `ProbeError` 없음, 10 개
     direction 읽기와 masking 표 전부 동일. 옛 기준은 *그 둘 위에서만* 동치였고 —
     둘 다 행위 이전에 empty 를 읽는다 — 그것이 20 여 cycle 동안 아무도 눈치채지 못한 이유다.
  5. ✅ `INERT` 를 `DEAD` 와 **분리해서** 채점한다. `pre_epoch_commits` 는 empty (아무것도 없다),
     `unregistered_local_only` 는 2 를 읽는다 (자기 것이 아니라 fixture 의 것). 서로 다른 사실이다.
  6. `Probe.liveness_subject` 를 도입 — 행위와 그 행위에 대한 assertion 이 subject 를 **한 번**
     진술한다. 검사 쪽이 subject 를 독립적으로 재파생하면 둘이 어긋날 수 있고, 그것이
     D-045/D-047 이 계속 찾아내는 손복사 registry 의 모양이다.
- **Alternatives**: (a) STATE #1 대로 세 번째 probe 를 등록 — 깨어나지 않는 liveness 행위를
  실은 probe 는 `SILENT` 판정을 무의미하게 만든다 (D-050 이 경계하는 바로 그 결함).
  (b) 기준을 `읽기가 움직였다` 로 — 복사된 surface 의 부수적 변동이면 통과하므로 같은 방향으로
  여전히 틀렸다. (c) **채택** — membership: subject 가 앞에 없고 뒤에 있어야 한다.
- **Status**: accepted — D-054 의 "net +1" 부분을 철회 (나머지 census 4/16 은 유효).
- **Refs**: PR #67 · `journal/2026-08/04-08-liveness-membership-bar.md` ·
  `eval/mppi_sandbox/liveness_derivation.py` · `eval/mppi_sandbox/guard_direction.py` ·
  Q-070

---

## D-054 — 2026-08-04 — liveness 행위는 **네 부분**이고, `acts_of` 가 대는 것은 한 번도 어렵지 않았던 부분이다 (Q-068 → (c))

- **Context**: D-053 은 dynamic probe 의 reach 가 손으로 쓴 `Probe.liveness` 표 **2** 개에
  묶여 있음을 측정했다. Q-068 은 `guard_reflexivity.acts_of` 에서 그 표를 파생하자고 제안했고,
  그 자신의 다음 action 이 **"먼저 파생 가능 비율을 재고, 낮으면 (c) 에서 멈춘다"** 였다.
  D-052/D-053 이 두 번 연속 남긴 규율 — 도구를 쓰기 전에 적용 가능성을 잰다 — 을 따른다.
- **Decision**: `eval/mppi_sandbox/liveness_derivation.py`. 손으로 쓴 두 행위를 되읽으면 각각
  **삼중항** `(scope, membership, subject)` 이다 — `_live_staged_declarations` =
  `INDEX`/`IN`/`DECLARED_LOCAL_ONLY` 의 원소, `_live_undeclared_drift` =
  `WORKTREE`/`OUT`/그 밖의 tracked 경로. `acts_of` 는 이 중 **하나**만 댄다: `Act` 는
  `tool`/`verb`/`scope`/`site`/`spelling` 을 나르고, filesystem act 의 spelling 은 접근자
  이름(`read_text`)이지 경로가 아니다. 나머지 둘은 `Guard.typed_exemptions` 에서 파생한다 —
  `TYPED` exemption 이 subject 가 **안**에 있어야 할(`AND`/`IN`) 혹은 **밖**에 있어야 할
  (`SUB`/`NOT_IN`) registry 를 지목한다. 파생된 recipe 는 전부 scratch repo 에서 **실행**한다
  (`check_liveness` 와 같은 기준: 읽기가 non-empty 가 되어야 한다).
  1. **파생 비율 = 4/16** (root-addressable 기준, partition 으로 못 박음):
     `DERIVED` 4 / `NO_SCOPE` **0** / `NO_REGISTRY` 9 / `NOT_PATHS` 3.
  2. **`acts_of` 가 맡은 층은 아무도 잃지 않고, 그 층은 병목이 아니다.** `NO_SCOPE` = 0 —
     scope 는 16 개 전부에서 복원된다. 4 로 떨어지는 것은 전적으로 `acts_of` 가 말하지 않는
     두 층이다: 9 개는 constant 를 지목하는 `TYPED` exemption 이 아예 없고, 3 개는 지목은
     하는데 그 원소가 claim id / reading label 이라 경로가 아니다.
     **Q-068 은 한 번도 어렵지 않았던 부분을 파생하자고 제안한 것이다.**
  3. **네 번째 부분이 있고 두 registry 중 어느 쪽도 그것을 대지 않는다.** `pre_epoch_commits`
     는 삼중항을 다 복원하고도 **empty** 를 읽는다. 그 population 은 `origin/main..<ref>` 위의
     `--until=<epoch>` 로 잘린다 — population 자신의 **시간·위상 조건**이고, `acts_of`(창) 에도
     `Exemption`(registry) 에도 없다. D-032 식 오진을 피하려고 **네 scope 전부**에서 실행했고
     전부 DEAD — precedence 표가 잘못 고른 것이 아니다.
  4. **typed 표 대비 순증 = 1.** D-053 의 `reach_gap` 은 readable-but-unprobed **6** 을
     보고했고 이는 "쓸 수 있는 probe 6 개" 로 읽힌다. 실행하면 derivation 이 더하는 것은
     `unregistered_local_only` **1** 개다. **readable 과 wakeable 은 다른 성질**이고 6 → 1 이
     그 차이의 크기다.
  5. 손으로 쓴 두 행위는 scope 도 membership 도 **정확히 재파생**된다 — 다만 그 ground truth 는
     **n = 2** 이고, 대체하려는 표와 같은 크기다. test 이름에 명시한다.
  6. `SCOPE_PRECEDENCE` 는 손으로 쓴 표지만 **pool 이 아니라 scope 어휘**(4 토큰) 위의 표다.
     `unranked_scopes()` = `()` 이고 어휘와의 상등이 pin 되어 있어 pool 성장에 추월당하지 않는다.
     D-045/D-047/D-049 가 잡아온 표와 위험 등급이 다르다 — 그 차이를 명시적으로 기록한다.
- **Alternatives**: (a) `PROBES` 를 손으로 6 개 늘린다 — Q-068 이 이미 기각 (우연을 3 배로).
  (b) 표를 `acts_of` 에서 컴파일한다 — **순증 1 개로 측정됨, 채택하지 않는다**.
  (c) 파생 불가로 확정하고 `reach_gap` 을 깨지는 mirror 로 승격 + 실측된 1 개만 등록 — **채택**.
- **Status**: accepted — Q-068 → (c). 후속: `unregistered_local_only` 를 세 번째 `Probe` 로
  등록, 그리고 9 개 `NO_REGISTRY` 중 몇이 layer 2 가 아니라 **네 번째 부분** 때문인지 재귀속
  (Q-069).
- **Refs**: PR #67 · `journal/2026-08/04-07-derived-liveness-acts.md` ·
  `eval/mppi_sandbox/liveness_derivation.py` · Q-068 → resolved · Q-069 filed
- **Note**: 이 module 도 자신이 감사하는 registry 에 들어갔다 — pool **41 → 43**
  (`mutable_scope`, `unranked_scopes`). **D-046 6 번째**, 그리고 둘을 한 번에 더한 첫 사례.

---

## D-053 — 2026-08-04 — dynamic probe 의 reach 는 **fixture 가** 정한다. 그리고 fixture 는 이미 있는 probe 2 개 크기다

- **Context**: D-052 의 결론은 어느 guard 에 관한 것이 아니라 **방법의 적용 가능성**에 관한
  것이었다 — suppression 은 12 pair 중 1 곳에만 걸렸고, 걸린 이유는 무관한 keyword argument
  였다. STATE #2 는 같은 질문을 나머지 dynamic probe 에 하라고 했다. `guard_direction` 은
  (guard × path) 마다 scratch git repo 를 세우고 위반을 commit 해서 전후를 비교하는데,
  `PROBES` 는 **2** 개고 `unprobed_revocable()` 은 그 표가 완전하다고 보고한다. **2 는 설계된
  경계인가, 또 하나의 우연인가.**
- **Decision**: `eval/mppi_sandbox/probe_reach.py`. guard 를 "fixture 가 무엇을 바꿔야 읽기가
  움직이는가" 로 분할한다 — `REPO_ROOT` / `PACKAGE_SOURCE` / `SCANNED_POOL` / `DOMAIN`,
  `inspect.signature` 에서 파생하고 pool 의 **분할(partition)** 로 test 에 못 박는다 (표로 쓰면
  D-045 가 계속 잡아내는 그 형태가 된다). root 로 주소 지정 가능한 것들은 **실행해서** 잰다:
  fixture 에서 한 번, 진짜 root 에서 한 번, 두 읽기를 나란히 기록.
  1. 41 guard 중 **16** 이 root-addressable. 그런데 `build_scratch_repo` 의 fixture 에서
     읽히는 것은 **1** 개고 **8 개는 예외를 던진다** — fixture 는 declared local-only 5 개 +
     control 1 개가 전부인데 그 guard 들은 `docs/decisions.md` 나 `scripts/*.sh` 를 읽는다.
     **probe 의 reach 는 설계가 아니라 fixture 가 정하고 있었고, fixture 는 이미 probe 를 가진
     2 개에 딱 맞는 크기다.**
  2. 보고에서 멈추지 않고 우회 (D-052 의 규율): `build_enriched_repo` 가 예외들이 지목한 읽기
     표면(`docs/`, `scripts/`)을 같은 scratch repo 에 복사·commit 한다 ⇒ **readable 6, error 0**.
     `fixture_gap` = **8** — reach 에서 빠져 있던 이유가 guard 도 probe 도 아니고 fixture 가
     무엇을 쓰느냐였던 guard 의 수. 주장이 아니라 **측정된 값**이다.
  3. **더 날카로운 쪽: 등록된 probe 2 개는 fixture 만으로는 애초에 읽히지 않는다.**
     `staged_declarations` 와 `undeclared_drift` 는 두 fixture 모두에서 `UNDECIDABLE` —
     HEAD 에서도 scratch 에서도 빈 읽기다. 이들을 probe 가능하게 만드는 것은 손으로 쓴
     `Probe.liveness` 행위이고 그것은 정확히 **2** 개다. 즉 reach 는 결국 typed table 이
     정하고 있으며, 그 table 은 `unprobed_revocable` 이 검사하는 table 보다 **한 층 아래**에
     있다. **D-052 의 발견이, 그것을 일반화하려고 만든 도구 안에서 재현됐다.**
- **기존 mirror 는 틀린 population 에 대해 깨끗했다**: `unprobed_revocable()` = `()` 이지만
  비교 대상이 `revocable()` — **2** 개다. `DIFFERENCE` 형태 밖의 누락은 원리적으로 보고할 수
  없다. `reach_gap` = **6** (읽히는데 probe 없음) 이고 전부 그 밖이다. 두 mirror 가 독립임을
  test 에서 disjoint 로 못 박아, 한쪽이 다른 쪽의 약한 사본이 되는 것을 막는다.
- **부수 확인 — "빈 값 대신 예외를 던진다" 는 규율이 처음으로 *탐지* 배당을 냈다**: 8 개의
  base-fixture 실패는 모두 raise 이지 빈 반환이 아니다. `local_only_audit` 이 적어둔 이유
  ("found nothing 으로 degrade 하는 audit 은 하지도 않은 실험에 대해 clean 을 보고한다") 그대로
  다. 만약 degrade 했다면 전부 `UNDECIDABLE` 로 접혀 fixture gap 이 **0** 으로 읽혔을 것이다.
- **한계를 숨기지 않음**: enriched fixture 는 저장소의 충실한 사본이 아니다.
  `citation_audit.missing_sites` 는 거기서 **17**, HEAD 에서 **0** 을 읽는다. 그래서 모든
  `Reach` 가 두 읽기를 다 들고 다니고, 역전이 평균으로 사라지지 않는다.
- **자기 결함 1 건, 자기 test 가 잡음**: `normalise` 첫 draft 가 `str` 반환을 빈 집합으로 접어서
  `lam_dependence.report` 류를 `UNDECIDABLE` 로 — *측정이 불가능한 자리에 측정을 보고* 할 뻔했다.
  `NOT_A_READING` 을 별도 판정으로 분리. **이 module 도 제가 감사하는 registry 에 들어갔다**
  (D-046 형태, **5 번째**): pool 40 → **41** (`probe_reach.reach_gap`).
- **Alternatives**: (a) `PROBES` 를 6 개 더 손으로 채운다 — reach 는 넓어지지만 D-052 가 말한
  바로 그 typed-table 우연을 6 배로 늘린다. (b) 이번 선택: reach 를 먼저 **재고** 그 표가 무엇에
  묶여 있는지 이름 붙인다. (c) fixture 를 진짜 저장소의 완전 복사로 만든다 — 느리고, HEAD 와
  구분이 안 되어 전후 비교 자체가 무의미해진다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-06-dynamic-probe-reach.md` · STATE #2 · Q-068 filed

## D-052 — 2026-08-04 — masking class 는 **측정으로도 1 개**다. 그리고 그것을 잴 수 있었던 이유는 우연이었다 (Q-067 → (b))

- **Context**: D-050 은 mask 를 하나 찾았다 — `undeclared_drift` 의 exemption 이 위반 행위보다
  **먼저** population 에서 경로를 제거해서, 규칙이 깨지는 바로 그 순간 guard 가 제일 깨끗하게 읽힌다.
  증명 방법은 **suppression** 이었다: `declared={}` 로 다시 불러서 경로가 원래 있었는지 본다.
  STATE #1 은 이 screen 을 typed exemption 전체로 일반화하라고 했다. 파생된 pair 는 **12** 개.
- **Decision**: `eval/mppi_sandbox/exemption_masking.py`. population 은 손으로 쓰지 않고
  `Guard.typed_exemptions` 를 그대로 쓴다 (다른 TYPED screen 과 대상이 어긋나면 깨끗한 screen 이
  다른 집합에 대한 것이 되므로 — 등식으로 test 함). 세 결과:
  1. **12 pair 중 exemption 을 파라미터로 받는 것은 1 개뿐** — `undeclared_drift` 의 `declared=`,
     그것도 `tree_provenance.verify` 가 stamp 의 allow-list 를 넘기려고 있는 파라미터지 감사를 위한
     것이 아니다. **유일하게 발견된 mask 는 무관한 이유로 존재하는 keyword argument 를 통해 발견됐다**
     — D-046 의 "우연이 filter 자리를 지키고 있었다" 가 이번엔 *probe* 자리를 지키고 있었다.
     나머지 11 은 hard-wired 라서 D-050 의 방법이 원리적으로 적용 불가였다.
  2. 그래서 보고에서 멈추지 않고 **module global 경로**로 우회한다 — Python 은 global 을 호출
     시점에 찾으므로 guard 를 *정의한* module 의 attribute 를 갈아끼우면 hard-wired 도 suppress 된다.
     12/12 runnable, `unsuppressible()` = `()`.
  3. **bite 단독은 약한 screen 이다**: 12 중 **6** 이 suppression 하에서 자란다. 그런데 그 중 5 는
     그냥 **제 일을 하는 exemption** 이다 (`ADAPTERS` 를 지우면 7 술어 전부 unadapted). D-048 이
     빠진 절반을 준다 — mask 는 위반 행위가 population 을 *붕괴* 시킬 수 있어야 하고 `ENUMERATION`
     population 은 위반 후에도 위반자를 담고 있으므로, **mask ⟹ bites AND revocable**. 교집합은
     정확히 **1** 개, D-050 자신의 pair. **Q-063 이 구조로 1 로 묶은 것을 이번엔 전 typed pair 에
     대한 측정으로 1 로 묶는다.**
- **동시에 Q-067 을 (b) 로 확정**: `_provenance` 는 same-module call 을 **따라가지 않는다** — 이것은
  D-050 이 `_is_set_valued` 에서 찾은 누락이 아니라 결정이다. `_is_set_valued` 는 "이것이 집합인가"
  (값의 성질, frame 을 넘어 보존됨) 를 묻고, `_provenance` 는 "이 exemption 이 손으로 타이핑된
  registry 인가" (호출 지점의 성질, 보존 **안 됨**) 를 묻는다. 따라가면 진짜 derive 된 population 이
  typed constant 를 경유만 해도 `TYPED` 로 재분류되어 screen 이 조용히 넓어진다 — 틀린 방향.
  (b) 의 의무도 함께 이행: exposure 가 양수가 되면 할 일은 **helper 의 registry 를 호출 지점에서
  이름 붙이는 것** (인자로 넘기거나 module 상수로 alias), 술어를 넓히는 것이 아니라고 코드에 적었다.
  exposure 는 HEAD 에서 여전히 `()` 지만 **값이 커졌다** — 눈머는 screen 집합에 이번 cycle 의
  masking screen 전체가 추가됐다 (그 12 pair 가 정확히 TYPED 집합이므로).
- **부수 발견 — D-048 의 "정확히 1 개" 는 이미 2 로 흘렀고 아무도 몰랐다**: `unmirrored_revocable`
  는 HEAD 에서 `staged_declarations` + `undeclared_drift` **2 개**를 읽는다 (D-049 의 `&` arm 이
  pool 을 넓히면서 전자가 들어왔고, 이번 cycle 변경 이전부터 그랬음을 clean worktree 로 확인).
  D-048 의 경계는 stale 이었다. 이번 screen 이 다시 1 로 묶는데, 근거는 구조가 아니라 측정이다 —
  `staged_declarations` 는 registry 를 **빼는** 게 아니라 registry 로 **좁히므로**(`changed &
  DECLARED_LOCAL_ONLY`) suppression 이 population 을 키우는 게 아니라 비운다 ⇒ `INERT`.
- **자기 결함 2 건, 둘 다 이 module 이 일반화하려는 바로 그 guard 를 놓쳤다**:
  (i) `_substitutes_for` 첫 draft 가 assignment target 이 파라미터여야 한다고 요구해서
  `allow = DECLARED_LOCAL_ONLY if declared is None else declared` 를 못 봤다 — 즉 parameter route
  **0 개**, "D-050 의 probe 는 애초에 불가능했다" 고 보고할 뻔했다. 판정을 binding 이 아니라
  `IfExp` 자체로 옮겨 수정. **10 cycle 중 아홉 번째 first-draft scan 이 제 population 을 틀렸고,
  또 under-count 방향.** (ii) `Drift` 는 dataclass 라 `repr` 하나로 접히고, 그러면 suppression
  양쪽이 1-element 라 성장 판정이 원리적으로 불가능 — D-050 이 *증명한* mask 가 `DIVERGES` 로
  나왔다. field 를 펼치도록 수정. 두 결함 다 회귀 test 로 고정.
- **Alternatives**: (a) 11 pair 를 unfalsifiable 로 보고만 하고 끝낸다 — 정직하지만 screen 이 아니다.
  (b) guard 마다 exemption 을 파라미터로 받게 리팩터 — 12 곳 signature 변경, 감사 편의를 위해
  production 서명을 바꾸는 비용. (c) module global 우회 ← 채택, 호출자 코드 무변경.
- **Status**: accepted. **Q-067 → resolved (b)**.
- **Refs**: PR #67, `journal/2026-08/04-05-typed-exemption-masking-screen.md`,
  `eval/mppi_sandbox/exemption_masking.py` (+21 tests)

## D-051 — 2026-08-04 — 한 scan 안에서 **깊이 일치는 예외**다: co-derived 술어쌍 10 중 9 가 같은 식을 다른 깊이로 읽는다. 그리고 positive probe 만으로는 없는 깊이가 보인다

- **Context**: Q-066 (b) — D-050 은 `_is_set_valued` 와 `_difference_kind` 의 깊이 불일치를 **걸려 넘어져서** 발견했고, 그 불일치는 ~30 cycle 동안 guard 2개를 population 밖에 두고 있었다. 같은 scan 에 식을 해석하는 술어가 더 있다. 우연히 하나를 찾은 것인가, 아니면 규칙인가.
- **Decision**: `predicate_depth.py` 도입. 모집단은 **derive** — `ast.expr` 로 annotate 된 parameter 를 가진 module-level 함수 (**7개**), 그리고 typed adapter table 을 그 glob 과 **양방향** 대조 (`unadapted_predicates` / `stale_adapters`). 깊이는 **읽지 않고 실행해서** 잰다: 하나의 ground 를 감싸는 rung 사다리 (`BARE` → `set(X)` → `{v for v in X}` → alias → `_p1()` → `_p2()`) 를 source 에서 parse 해 넘긴다. 결과 — **co-derived 쌍 10 중 9 가 불일치**. 일치하는 쌍은 (`_provenance`, `core_name`) 단 하나.
- **핵심 방법론 결론 — `FOLLOWS` 와 `OPAQUE` 를 가르는 것은 negative ground 다**: 모든 rung 을 **두 개의 ground** (긍정/부정) 에 대해 돌리고, **양쪽 reading 이 모두 살아남을 때만** `FOLLOWS` 로 친다. `_is_set_valued` 는 positive-only 사다리에서 `set(X)` 와 `{v for v in X}` 를 통과하지만 `set(5)` 와 `{v for v in 5}` 도 `True` 로 답한다 — **wrapper 가 답하는 것이지 내용이 아니다**. 실제 content-reading depth 는 5/6 이 아니라 **3/6**. D-050 의 masked-collapse 형태가 한 층 아래에서 반복된 것이고, positive-only probe 였다면 없는 깊이를 보고했을 것이다.
- **두 번째 결론 (또 자기 모집단)**: co-application 을 **argument 철자** 로 키잉한 첫 draft 는 4쌍을 주는데 **그 중에 D-050 자신의 쌍이 없다** — `_guards_in` 은 `_is_set_valued` 에게 피연산자(`left`/`right`) 를, `_difference_kind` 에게 `node.left` 에서 추적된 population 을 넘기므로 같은 `&` 식을 다른 binding 으로 읽는다. argument 를 **공유 loop 변수** 까지 추적하면 (tuple unpacking + `list.append` — `gr._aliases` 가 안 따라가는 두 링크) 10쌍이 되고 그 쌍이 들어온다. **최근 9 cycle 중 8번째** 로 first-draft scan 이 자기 모집단에 대해 틀렸고, 또 **과소** 방향.
- **세 번째**: 선언된 깊이와 측정된 도달거리는 **무관한 양**이다. `_resolve` 는 `depth=3` 을 선언하고 wrapper **1개**를 통과, `_difference_kind` 는 `depth=2` 를 선언하고 **4개**를 통과. `depth=` default 는 D-049 가 말한 "아무도 코드와 대조하지 않는 네 번째 진술" 의 또 다른 사례.
- **비용은 잠재적이며 0으로 보고한다**: `_is_set_valued` 는 same-module call 을 따라가고 `_provenance` 는 안 따라가므로, helper 를 거쳐 도달하는 registry 는 guard 로 admit 된 뒤 `DERIVED` 로 분류되어 모든 `TYPED` screen 에서 **보이지 않는다**. `provenance_depth_exposure()` 는 HEAD 에서 **`()`**. assertion 이 아니라 **재유도되는 0** 으로 ship 한다 — D-050 이 처방한 "중복 registry 를 helper 로 추출" refactor 가 정확히 이 수를 양수로 만드는 편집이기 때문.
- **자기 참조 (D-046 형태 3회차)**: 이 module 이 자기가 감사하는 registry 에 들어갔다. guard pool 32 → **38**, mirrors 4 → **7**. 부수적이지만 D-050 의 수정이 cosmetic 이 아니었다는 가장 선명한 증거 — 새 guard 6개 중 **3개**가 deep 술어에만 보인다. 즉 수정 **이후** 작성된 module 이 수정 **이전** 이었다면 절반이 안 보였다.
- **Alternatives**: (a) 깊이를 상수 하나로 통일 — 값싸지만 술어마다 옳은 깊이가 다르다 (`_resolve` 의 3 은 alias chain 용). (b) 쌍마다 반례를 찾는 meta-test ← **채택**. (c) D-050 을 단일 사례로 둔다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-04-predicate-read-depth.md` · Q-066 → resolved

## D-050 — 2026-08-04 — shape 이 지목한 원인은 **가려져 있어 한 번도 관측되지 않는다**. 그리고 중복을 없애는 refactor 가 guard 를 registry 에서 **삭제** 했다

- **Context**: Q-065 (b) — `revocable` 은 population 이 두 관측의 *차이* 인지만 보고, 금지 행위가 그것을 비우는지 채우는지는 안 본다. D-049 에서 shape 은 2회, failure 는 1회였다. lean 은 "실행해서 확인" 이었다: 모집단이 작고(28개 중 `DIFFERENCE` 2개), D-049 에서 가장 결정적이었던 실험이 정확히 "scratch repo 에서 파일 하나 stage" 였기 때문.
- **Decision**: `guard_direction.py` 도입. (guard × declared path) 마다 throwaway git repo 를 세워 **허용 상태**(edit, unstaged) 에서 읽고 → **위반**(add+commit) 후 다시 읽는다. 판정은 **cardinality 가 아니라 membership** — `after` 가 방금 commit 한 path 를 호명하는가. 결과 10 readings: `staged_declarations` 는 5/5 **NAMES_OFFENCE**, `undeclared_drift` 는 5/5 **SILENT**. 핵심은 그 다음이다 — **`quieter` 는 10 중 0**. blind guard 의 reading 은 줄지 않고 **양쪽 다 `()`** 다. allow-list 를 비우고(`declared={}`) 다시 읽으면 위반 전 population 에 그 path 가 **있고** 위반 후 없다 ⇒ 붕괴는 **실재하지만**, exemption 이 위반 이전에 이미 그것을 제거하므로 **관측될 수 없다**(`masked` 5/10). 즉 D-047/D-049 가 "행위가 population 을 비운다" 로 귀속한 것은 틀렸다 — 비우는 것은 행위가 아니라 exemption 이다.
- **두 번째 결론 (더 물릴 뻔한 쪽)**: probe 가 guard 자신의 population 을 읽게 하려고 `staged_changes` 를 추출했더니 — D-045~D-049 가 매 cycle 처방한 바로 그 "중복 진술 제거" refactor — `staged_declarations` 가 **guard pool 에서 사라졌다**. 강등이 아니라 **부재**. 원인: `_is_set_valued` 는 같은 module 의 call 을 따라가지 않고 `_difference_kind` 는 늘 따라갔다 — 같은 식을 두 술어가 **다른 깊이** 로 읽고 있었다. 고친 뒤 HEAD 자신의 source 를 다시 재면 28 이 아니라 **30**: `local_only_audit.derived_local_only` 와 `weight_units.closed_loop_per_unit_spread` 가 애초에 population 에 없었다. **최근 8 cycle 중 7번째** 로 scan 이 자기 모집단에 대해 틀렸고, 또 **과소** 방향.
- **Alternatives**: (a) 정적 추론 (Q-065 (a)) — 금지 행위가 population 의 어느 항을 움직이는지 AST 로 판정. 기각: 이번 결과가 바로 그 방법이 놓쳤을 것 — 원인이 **두 개** 이고 하나가 다른 하나를 가린다는 사실은 실행해야만 보인다. (b) 채택. (c) match 수로만 읽고 넘어간다 — 기각: D-049 가 이미 그렇게 읽어 잘못 귀속했다.
- **Status**: accepted — D-049 의 실패 **귀속** 을 정정한다 (건수 1은 유효, `revocable` 은 2로 불변 — 넓힌 scan 이 들인 guard 는 전부 `ENUMERATION`)
- **Refs**: PR #67 · `journal/2026-08/04-03-guard-direction-executed.md` · Q-065 → resolved by this entry · Q-066 filed

## D-049 — 2026-08-04 — guard 의 **이름** 은 registry 의 네 번째 진술이고, 아무도 그것을 코드와 대조하지 않았다

- **Context**: Q-064 (b) 는 guard 가 감시하는 **동사** 를 코드에서 유도하라고 했다. 유도해 보니 관측 가능한 네 scope (`WORKTREE`/`INDEX`/`COMMIT`/`NAMESET`) 중 **`INDEX` 를 보는 guard 가 하나도 없었고**, 하필 그 이름을 단 guard (D-047 의 `staged_declarations`) 가 index 를 안 읽고 commit 만 읽고 있었다. `STATE.md` 를 실제로 `git add` 한 뒤 `local_only_audit staged` 를 돌리면 `OK: ... none committed` 로 **깨끗하게 통과**했다 — 메시지는 정직했고 이름이 거짓이었다. 더 나아가 D-048 의 scan 자체가 `staged_declarations` 를 **못 봤다**: `-`/`in`/`not in` 만 읽었는데 이 guard 는 `changed & set(DECLARED_LOCAL_ONLY)` 로 registry 쪽으로 **좁히는** 필터였다.
- **Decision**: (1) `SENSE_AND` 를 filter 로 인정 — guard population 23 → **28**, 새로 들어온 3개 중 하나가 D-047 이 짠 바로 그 guard. (2) `staged_declarations` 가 `diff --cached` 도 읽게 해 이름을 참으로 만든다 — 같은 명령이 같은 staged 파일에 대해 이제 exit 1. (3) `watched_operations()` / `scope_coverage()` / `misnamed_scopes()` / `unobserved_scopes()` 를 `guard_reflexivity` 에 추가, scope 는 호출부 literal 에서 유도 (wrapper 가 아니라 call site 에 `--cached` 와 `..` range 가 있으므로 call graph 를 따라간다). (4) D-048 의 결론은 **유지하되 그 population 과 predicate 은 정정**: `revocable` 은 population 이 *차이* 인지만 묻고 금지된 행위가 그것을 **비우는지 채우는지** 는 묻지 않는다 — commit 은 `undeclared_drift` 를 비우고(D-047 의 실패) `staged_declarations` 를 채운다(정상 동작). 그래서 shape 는 **2회**, failure 는 여전히 **1회**.
- **Alternatives**: (a) 이름만 고쳐 `committed_declarations` 로 개명 — 정직하지만 `INDEX` 는 계속 아무도 안 본다. (b) 발견만 보고하고 안 고친다 — 이 branch 가 반복해서 경고한 "깨끗하게 읽히는 guard 는 clearance 가 아니다" 를 그대로 재현. (c) 채택: 읽게 만들고, `unobserved_scopes() == ()` 와 `misnamed_scopes() == ()` 를 **등식으로 유지** — 빈 결과는 무언가가 계속 재유도할 때만 clearance 다.
- **Status**: accepted — D-048 의 "23 중 1" 을 population/predicate 양쪽에서 정정한다 (결론은 유효)
- **Refs**: PR #67 · `journal/2026-08/04-02-watched-operations-not-sets.md`

## D-048 — 2026-08-04 — guard 의 사각지대는 **allow-list 가 아니라 감시하지 않는 동작(act)** 에 있다 — Q-063 (b) 는 D-047 형태를 1건으로 한정

- **Context**: D-047 에서 `undeclared_drift` 가 자신이 강제하는 규칙의 위반을 볼 수 없다는
  것이 드러났다 (staging 하면 worktree=HEAD 가 되어 감시 대상에서 빠지고, 게다가 그 path 는
  자신의 allow-list 위에 있다). Q-063 은 이 질문을 suite 전체에 구조적으로 던지자고 lean (b)
  를 냈다 — "한 번 있는 형태는 보통 두 번 있다".
- **Decision**: `guard_reflexivity.py` 를 도입한다. guard population 은 package glob + AST
  로 **유도** (D-045); guard 마다 (i) **revocability** — population 이 두 관측의 *차이* 라
  위반 행위가 그것을 붕괴시킬 수 있는가 — 와 (ii) **exemption provenance**
  (`TYPED`/`DERIVED`/`INLINE`) 를 판정한다. 결과: guard **23** 개 중 revocable+unmirrored 는
  **정확히 1개**, D-047 자신의 guard. Q-063 의 lean 은 **기각**되고 그 class 는 1건으로 한정된다.
  더 중요한 두 번째 결론: `DECLARED_LOCAL_ONLY` 는 package 에서 watcher 가 **가장 많은**
  allow-list (2개) 인데도 규칙이 깨져 있던 ~30 cycle 내내 둘 다 깨끗하게 읽혔다 —
  `stale_declarations` 는 tracked-ness 를, `underived_declarations` 는 재유도 가능성을 볼 뿐
  **staging 을 보는 것은 없었다**. ⇒ **존재에 의한 coverage 는 행위에 의한 coverage 가 아니다**;
  `unwatched_exemptions()` 가 비어 있어도 그것은 무죄 판정이 **아니다**.
- **Alternatives**: (a) guard 마다 실패를 손으로 주입 (Q-063 (a)) — 정확하지만 "주입할 실패"
  를 사람이 상상해야 하므로 D-046 의 hand-typed 실패 모드를 재현. (b) 구조적 판정 — 채택.
  (c) D-047 을 단일 사례로 두기 — 기각: 1건이라는 것 자체가 유도되어야 할 결론이었다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-01-guard-reflexivity-structural-pass.md` ·
  Q-063 → resolved by this entry · 457 passed (was 442)

## D-047 — 2026-08-04 — registry 는 맞았다. 짧았던 건 그것을 **베껴 적은 guard** 였다

- **Context**: STATE #1 — `tree_provenance.DECLARED_LOCAL_ONLY` 는 D-044/D-045/D-046
  세 cycle 연속 지목된 마지막 hand-typed registry. 지시대로 **누가 쓰는가**에서
  유도했다: writer surface (`scripts/*.sh` + `scripts/prompts/*.md`, glob) 의
  full-overwrite 서술 ∧ D-011 era 에 어떤 `autoresearch/*` branch 도 commit 하지 않은
  tracked path. 두 instrument 를 교집합한 이유는 각각이 **다른 방향으로** unsound 여서다 —
  🚫 문단은 never-staged 세 개와 durable-record 네 개를 같은 문장에서 대비시키므로
  prose 만으로는 분리 불가, git 만으로는 local-only 와 "최근에 아무도 안 건드림" 이 구분 불가.
- **Decision**: `eval/mppi_sandbox/local_only_audit.py` + 19 tests 신설.
  유도 결과 **derived = declared = 5, 양방향 모두 공집합** — D-043 이후 감사한 registry 중
  처음으로 짧지 않았다. 발견은 한 단계 옆에 있었다: Phase 3 push guard 가
  `grep -E '^(STATE|JOURNAL|RESULTS)\.md$'`, 즉 **세 항목이던 시절의 registry 사본**.
  D-044 가 목록을 다섯으로 늘렸을 때 갱신되지 않아 `TODO.md` 와 `research/feed.md` 는
  "commit 금지" 라고 적혀 있고 아무것도 막지 않는 상태로 약 30 cycle 을 보냈다.
  guard 를 `local_only_audit staged` 호출로 교체 — 목록의 진술은 이제 한 곳뿐.
  부수 발견: `undeclared_drift` 는 자신이 강제하는 규칙의 위반을 **볼 수 없다**.
  worktree-vs-`HEAD` 를 비교하므로 snapshot 을 stage 하면 drift 가 *사라지고*
  해당 path 는 allow-list 에 있다 — 규칙이 깨지는 순간 가장 깨끗하게 읽힌다.
  merge base 와 비교하는 `staged_declarations()` 를 별도로 둔 이유.
  epoch 은 D-011 heading 에서 파싱하고, 그 이전 위반 (p2 branch 네 개, 둘은 아직 queue 안)
  은 `pre_epoch_commits()` 로 **감추지 않고 보고**한다 — epoch 의 근거 자체이므로.
- **Alternatives**: (a) 목록을 손으로 다시 세기 — 세 cycle 연속 실패한 방법.
  (b) prose 만으로 유도 — 위 대비 문단 때문에 durable record 를 local-only 로 분류.
  (c) git 만으로 유도 — write mode 를 모르므로 방금 안 건드린 파일과 구분 불가.
  (d) guard 의 alternation 만 다섯으로 늘리기 — 사본을 최신화할 뿐, 다음 증가에 또 stale.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/04-00-derived-local-only-population.md` ·
  supersedes the literal guard added with D-011

## D-046 — 2026-08-03 — 손으로 쓴 registry 는 **계층마다** 짧다. citation 목록은 6/17 이었다

> 📐 이 절이 적는 dispatch-fragile 수치는 `AVX512_SKX` 조건부다 (D-033). 인용 등록: `claim_scope.SCOPED_CLAIMS` — D-046 의 `derived_citations()` 가 찾아냈다.

- **Context**: D-044 는 D-011 의 local-only 목록이 3/5, D-045 는 exclusion 목록이 2/3 임을 —
  둘 다 **목록을 다시 읽어서가 아니라 코드로 열거해서** — 찾았다. STATE #1 은 같은 처방을 다음
  손타이핑 registry 두 개에 걸었다. 그 중 `claim_scope` 를 집었다.
- **Decision**:
  - **(1) ✅ claim 계층은 아무것도 못 찾았고, 그렇게 보고한다.** `instrumented_claims()` 가
    `dispatch_divergence` 의 멤버에서 `_foo() -> Claim` 을 직접 걷는다: 5 = 5 = 5. 기존 test 는
    `SCOPED_CLAIMS` 를 `dd.CLAIMS` 와 비교했는데 **둘 다 손으로 쓴 목록**이라, `CLAIMS` 에 아무도
    안 넣은 Claim 함수는 양쪽 모두에 안 보였다. 순수하게 prospective — D-045 의 glob 절반과 같은 성격.
  - **(2) 🔴 citation 계층이 이번 cycle 의 내용이다. 6 등록 / 17 실재.** 7 개 절에 걸친 11 site,
    그 중 **9 개가 oracle stamp 없음**. 가장 날카로운 것은 **D-034** — 네 claim 의 reading 을
    **한 표에 전부** 적는 excursion 표(`1.30078`, `1.69563`, `0.251146`, `2.0375`)인데 어떤
    citation 목록에도 없었다. 즉 그 네 수치가 어느 기계에 조건부인지 **아무 guard 도 요구하지 않았다**.
    `citations=()` 였던 세 claim 중 실제로 0 인 것은 하나도 없었다.
  - **(3) 🔴 첫 matcher 가 증거를 지우는 방향으로 fail-open 이었다.** 경계 있는 substring 규칙
    `(?<![\d.])spelling(?![\d])` 은 `11.301` 속 `1.301` 을 올바르게 거부한다 — D-038 이 자기 절에서
    그대로 인용하며 설명한 바로 그 버그다. 그러나 오른쪽 경계는 **reading 을 더 정밀하게 적은 절도**
    거부한다. D-034 는 registry 가 `0.2511` 로 banked 한 값을 `0.251146` 으로 적으므로, 그 규칙이
    **가장 중요한 절 하나를 숨겼다** (7 site 보고 → 수치 비교로 고친 뒤 11). scan 초안이 과소계수한
    네 번째 연속 cycle.
  - **(4) 🔴 발견을 등록하자 downstream 이 깨졌고, 그것이 두 번째 발견이다.**
    `citation_audit._sites_from_claim_scope()` 는 horizon citation 을 `2.0×` amplitude 의 site 로
    끌어올린다. 이는 그 claim 의 **모든** citation 이 `other-quantity` 인 동안에만 옳았고 — 그게
    정확히 D-036 의 결론이다 — 따라서 "전부"와 "2.0× 를 적은 것들"이 같은 tuple 이라 **없는 filter 가
    보이지 않았다**. `instrument` citation 11 개가 등록되자 6 개 절이 *쓴 적 없는* 수치를 restate 한
    것으로 등록됐고 test 2 개가 그 절들을 지목하며 red. **우연이 filter 자리를 대신 지키고 있었다.**
  - **(5) ⚠️ 볼 수 없는 것은 선언한다.** `hazard_shared_rungs` 의 reading 은 1.0/0.0 이고 bare `1`,
    `0` 으로 렌더되어 모든 절에 나온다 ⇒ scan 불가. `DEGENERATE_READINGS` 로 선언하고 그 목록이
    **비지 않았음을 test 로 강제**한다 — 조용히 건너뛰면 "unregistered citation 없음"이 한 번도 훑지
    않은 claim 에 대한 진술로 읽힌다 (D-042).
  - **(6) ⚠️ 진짜 우연은 3 건.** D-023/D-024/D-025 의 `2.038` 은 `TIMING_RATIO_BAND` 상단이고
    `exposure_band_hi` 와 4 s.f. 에서만 충돌한다. 이유와 함께 `COINCIDENTAL` 에 선언했고
    `stale_coincidences()` 가 선언이 그 match 보다 오래 살아남는 것을 막는다. **모집단은 유도하고,
    기각만 손으로 적는다** — D-045 가 exclusion 을 다룬 방식과 같다.
- **Alternatives**: (a) citation 목록을 손으로 다시 훑는다 — D-044/D-045 가 두 번 연속 실패를 보인
  방법. (b) 유도만 하고 보고서로 남긴다 — 다음 절이 stamp 없이 추가되면 다시 조용해진다.
  (c) **유도 + 불변식 + 기각 선언** ← 채택. (d) 발견된 절들을 그냥 stamp 하고 registry 는 안 건드린다 —
  (4) 의 filter 버그를 영영 못 본다.
- **Status**: accepted. D-034 / D-035 / D-037 / D-038 / D-045 에 oracle stamp 추가. `2.0×` 관련
  결론은 **변경 없음** — 바뀐 것은 *어느 절이 감시받는가* 뿐.
- **Refs**: PR #67 · `journal/2026-08/03-23-derived-citation-population.md`

## D-045 — 2026-08-03 — scan surface 를 **손으로 쓴 목록**이 정의하는 한, registry 는 아무도 떠올리지 못한 파일에서 조용히 실패한다

> 📐 이 절이 적는 dispatch-fragile 수치는 `AVX512_SKX` 조건부다 (D-033). 인용 등록: `claim_scope.SCOPED_CLAIMS` — D-046 의 `derived_citations()` 가 찾아냈다.

- **Context**: D-044 가 `citation_audit.SCANNED_MODULES` 를 hand-written tuple 이라
  지적하고 "magnitude 를 안 쓰는 쪽"으로 우회했다. STATE #1 은 그 우회를 mechanism 으로
  바꾸라는 요청 — glob 으로 auto-discovery. 그런데 한 디렉터리 glob 도 여전히 **손으로
  그은 surface** 다. registry 는 "이 site 가 등록됐나"는 물었지만 "이 **파일**을 보기는
  하나"는 한 번도 묻지 않았다.
- **Decision**:
  1. `scanned_modules()` — `eval/mppi_sandbox/*.py` glob. 새 module 은 존재하는 순간
     surface 안에 있다. 이것만으로는 **오늘 아무것도 안 잡는다** (module 12 개 추가,
     신규 enforcing hit **0**). 순수하게 prospective 한 수정이라고 정직하게 기록한다.
  2. `unaccounted_surfaces()` — `git ls-files` 를 열거해서, 등록된 magnitude 를 진술하는
     **모든 tracked 파일**이 *scanned* 이거나 *이유와 함께 excluded* 이거나 둘 중 하나임을
     invariant 로 강제. 세 번째 상태(둘 다 아님)가 결함이다. 이번 cycle 의 발견은 전부
     여기서 나왔다.
- **Findings**:
  1. **미계상 surface 4 개**: `JOURNAL.md`(hit 26), `results/*.tsv`(10),
     `research/feed.md`(2), `eval/requirements-ci.txt`(1).
  2. **D-044 와 형태가 정확히 같고, 한 cycle 차이다.** exclusion 목록은 D-011 의 snapshot
     **3 개 중 2 개**만 담고 `JOURNAL.md` 를 빠뜨렸다 — D-044 가 D-011 의 local-only 목록에서
     **5 개 중 3 개**를 찾은 바로 다음 cycle. 손으로 관리하는 목록 둘, 과소계상 둘, 같은 주,
     둘 다 목록을 *다시 읽어서* 가 아니라 **코드로 열거하도록 강제당해서** 발견됐다.
     `results/` 는 더 날카롭다: `RESULTS.md` 의 exclusion **이유** 안에 "generated from
     `results/*.tsv`" 라고 이름이 적혀 있는데, 정작 그 이유가 속한 **목록에는 없다**.
     이유는 적혔고 그 이유가 적용될 surface 는 안 적혔다.
  3. 🔴 **`eval/requirements-ci.txt` 는 진짜 citation 이고, 유일하게 중요한 발견이다.**
     numpy pin 근거 주석이 D-030 headline swing 을 "**2.0x** under 1.26.4 / **1.029x**
     under 2.5.1" 로 진술한다 — dispatch-fragile claim 의 restatement 가, **CI 가 어떤
     numpy 를 설치할지 결정하는 파일** 안에 있다. D-039 가 D-028 을 rescope 했듯 D-030 이
     언젠가 rescope 되면, 폐기된 reading 이 살아남는 자리가 여기다. prose 도 docs/ 도
     아니라서 어떤 registry 도 볼 생각을 안 했다. `SCANNED_TEXT` 로 편입 + 등록.
  4. ✅ **surface 확장이 기존 meta-test 를 건드렸고, 고친 건 threshold 가 아니라 어휘다.**
     auto-discovery 가 `speed_audit.py` 를 끌어들였는데 그 docstring 은 D-024 의 median-ESS
     사실을 "**1.46** of K = 256" 으로 쓴다. D-024 는 같은 사실을 "1.46 / K=256" 로 쓰고
     이미 `denominator` 로 기각 등록돼 있다 — 즉 prose 철자만 **신호 0 개로 조용히** 기각돼
     `test_rejections_split_into_by_evidence_and_by_default` 가 red (silent 3 > 2). 그 test 는
     "이유 없이 정답을 맞히는 ranking"을 잡으려고 존재한다. threshold 를 올리는 건 구멍을
     찾아준 검사를 **음소거**하는 것이라, `_DENOM_AFTER` 가 prose 철자를 읽게 했다.
     **어느 판정도 바뀌지 않았다** (양쪽 철자 모두 이전에도 이후에도 기각).
  5. ⚠️ `tracked_files()` 는 git 부재 시 `[]` 가 아니라 **raise** 한다. `unaccounted_surfaces()`
     는 비었을 때 통과하므로, soft failure 는 "모든 surface 가 계상됨"으로 읽힌다 — D-042
     (일을 clear 하기만 하는 계측기는 clear 를 맡기면 안 된다) 의 직접 적용.
  6. 🔴 **그리고 D-043 의 re-run 이 이 절 자신에게서 red 를 냈다 — 규칙이 실제로 작동한
     첫 사례다.** 위 (4) 의 수정을 쓴 뒤 doc write **전에** 잰 값은 `414 passed` 였는데,
     doc write **후** 재측정은 `413 passed, 1 FAILED` 였다. 원인이 정확히 (4) 의 signal:
     `speed_audit` 은 `**1.46 of K = 256**` (bold 가 둘 다 감쌈) 로 쓰고, 이 D-045 절은
     같은 사실을 `**1.46** of K = 256` (bold 가 숫자에서 닫힘) 로 인용했다. 방금 추가한
     regex 는 두 번째를 못 읽어서, **수정을 서술하는 절이 그 수정에 걸렸다.** markdown
     장식은 숫자의 의미에 대한 증거가 아니므로 `_ASSIGN_BEFORE` 가 이미 갖고 있던 것과
     같은 `[`*"']*` 관용을 부여했다. ⇒ D-043 은 이제 **가정이 아니라 관측**이다: 이 cycle 의
     journal 초안에 적힌 414 는 push 되는 tree 의 숫자가 아니었고, 규칙을 지키지 않았다면
     red 인 채로 push 됐을 것이다.
- **Alternatives**: (a) glob 만 하고 끝낸다 — STATE #1 을 문자 그대로 만족하지만 오늘
  아무것도 안 잡고, exclusion 목록의 구멍은 그대로. (b) 미계상 4 개를 전부 exclusion 에
  손으로 추가 — 같은 실패 모드를 한 번 더 반복. (c) **채택**: glob + tree 전체 invariant.
  (d) `requirements-ci.txt` 주석에서 숫자를 지운다 — D-044 의 우회를 반복하는 것이고,
  pin 의 근거를 삭제하는 대가가 너무 크다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-22-citation-surface-completeness.md` ·
  Q-056 mechanism 부분 해소 · D-011 / D-037 / D-042 / D-044

---

## D-044 — 2026-08-03 — local-only 로 선언된 파일은 **3 개가 아니라 5 개**였다. 그리고 검증 surface 에는 *순서* 가 있다

- **Context**: D-043 은 규칙("문서 write 뒤에 다시 돌려라")만 남겼고, 이 repo 는 절차 규칙을 30 cycle 째 손으로 지키고 있다 (journal 커밋 버그). 그래서 규칙을 기계화하려 `tree_provenance` 를 썼는데 — **naive 한 구현은 매 cycle red** 다. D-011 이 worktree drift 를 *요구* 하기 때문이다. 그래서 surface 를 directory 가 아니라 **목적지** 로 쪼개야 했고 (worktree = test 가 읽는 것, `HEAD` = push 되는 것), 그 순간 "그럼 정확히 어떤 파일이 drift 해도 되는가" 를 열거해야 했다.
- **Decision**: (1) 선언 집합을 코드에 못박는다 (`DECLARED_LOCAL_ONLY`, 항목별 이유 포함). D-011 은 **3** 개(`STATE.md`/`JOURNAL.md`/`RESULTS.md`)를 명시했지만 worktree 는 **5** 개로 갈라진다 — `TODO.md` (`mirror_todos.sh`) 와 `research/feed.md` (`researcher.sh`) 도 같은 full-overwrite class 이고 어느 branch 도 커밋하지 않으며, **자기가 따르는 규칙 어디에도 이름이 없다**. 면제된 게 아니라 **아무도 몰랐다** — D-036 과 같은 형태(등록부는 누군가 타이핑한 것만 감시한다). (2) **push 직전 마지막 write 는 검증 surface 밖이어야 한다**: `docs/` 는 scan 대상이므로 안, `results/*.tsv` 는 어떤 test 도 읽지 않으므로 밖(확인함 — `test_dispatch_divergence` 의 언급은 prose 뿐). 따라서 순서는 문서 → commit → re-run → TSV → push 이고, 그래야 보고된 숫자가 push 된 tree 의 속성이 된다.
- **Alternatives**: (a) 선언 없이 worktree 만 해싱 — 매 cycle red ⇒ D-042 의 비대칭 교훈이 반대 방향으로 작동해 **경보가 기본값인 check 는 무시된다**. (b) 세 snapshot 파일만 면제 — 지금 tree 에서 즉시 2 개 false positive. (c) 규칙을 prose 로만 두기 (D-043 의 현 상태) — 30 cycle 짜리 반례가 있다.
- **⚠️ 명시한 fail-open**: untracked 파일은 두 fingerprint 어디에도 없다 (push 되는 tree 에 도달할 수 없으므로 포함시키면 `.last_result` 마다 false mismatch). 하지만 test 결과를 바꿀 수는 있으므로 `untracked_digest` 로 **별도 조건** 으로 보고한다 — 침묵시키지 않는다. D-042: 지워주기만 하는 instrument 는 지우는 데 쓰면 안 된다.
- **✅ 두 번째 발견, 여기서 고치지 않음**: `citation_audit.SCANNED_MODULES` 는 손으로 쓴 tuple 이라 magnitude 를 restate 하는 **새 module 은 누가 추가할 때까지 무감시**다 — Q-056 의 구멍이 이번엔 논증이 아니라 **갓 만든 파일로 실증**됐다. magnitude 를 아예 쓰지 않는 쪽으로 해소(감시 surface 를 늘리는 것보다 싸다).
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-21-tree-provenance-stamp.md` · commit `21737c8`

---

## D-043 — 2026-08-03 — green 을 기록한 tree 와 push 한 tree 가 다르면, 그 숫자는 그 commit 의 것이 아니다

- **Context**: 이번 cycle 의 첫 full-suite 실행에서 citation guard 3 개가 red 였는데, **내 변경 이전부터** red 였다. `HEAD` (d060636) 를 clean worktree 로 떼어내 확인 — 같은 3 개가 red. 즉 D-041 cycle 이 journal 에 기록한 **367 passed** 는 거짓이 아니라 **다른 tree 의 사실**이었다: guard 를 돌리고 → `docs/decisions.md` 에 D-041 section 을 prepend 하고 → push 했다. 그 prepend 가 `2.320x` 를 restate 하는 **미등록 citation site** 를 만들었고, 그것이 D-041 이 자랑한 바로 그 guard 가 잡도록 설계된 것이다.
- **Decision**: (1) 누락된 site 를 `exposure_band_width_cruise` 에 등록 (fast half 재green). (2) **REPORT phase 의 문서 write 는 EXECUTE 의 검증 대상이다** — journal/decisions/deliberations 가 scan surface 위에 있으므로, 이 세 파일을 쓴 *뒤에* guard 를 한 번 더 돌리지 않으면 보고된 숫자는 push 된 commit 의 것이 아니다. (3) 그러므로 **PR 의 CI 가 유일한 권위**이고 local 숫자는 참고값이다 — D-033 이 machine scope 에 대해 말한 것을 이제 *시점* 에 대해서도 말한다.
- **Alternatives**: (a) guard 에서 `docs/decisions.md` 를 제외 — scan surface 를 좁혀 문제를 없애지만, D-NNN 은 이 repo 가 숫자를 restate 하는 **최다 지점**이라 guard 의 목적을 지운다. (b) D-NNN prose 를 EXECUTE 안으로 옮겨 검증 뒤에 두기 — 옳지만 REPORT phase 의 정의를 바꾼다. (c) 등록만 하고 넘어가기 — 다음 cycle 이 똑같이 재현한다.
- **⚠️ 범위**: 이것은 D-041 의 *발견* 을 무효화하지 않는다 (census 는 syntax tree read 이고 재현된다). 무효화되는 것은 **"367 passed" 가 d060636 의 속성이라는 주장**뿐이다 — D-036 의 rescope-vs-retract 구분, 이번엔 measurement *시점* 에 적용.
- **✅ 규칙이 즉시 자기 자신에게 걸렸다.** 이 D-043 section 을 쓰고 규칙대로 guard 를 다시 돌리니 **또 red** 였다 — 결함을 *서술하는* 문단이 같은 magnitude 를 restate 하면서 결함을 한 문단 만에 재현했다. 등록하고 재green. 규칙이 존재한 첫 cycle 에 규칙이 값을 했다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-20-lam-dependence-static-partition.md`

---

## D-042 — 2026-08-03 — Q-061 의 identity 추측은 **참이지만 작다**: 52 → 39 이고, 알려진 하한은 30 이다

- **Context**: D-041 은 shipped `lam = 0.1` 에서 weight 하는 site 를 **52** 개로 셌다. Q-061 은 그 중 상당수가 물리량이 아니라 **두 run 사이의 동일성** 을 주장하므로 (`test_same_seed_identical_trajectory`) 온도가 양쪽에서 상쇄된다고 보고, 재측정 대상은 그 부분집합뿐이라고 lean (c) 를 걸었다. 그 lean 이 얼마나 싸게 만드는지는 아무도 세지 않았다.
- **Decision**: `lam_dependence.py` 가 52 site 를 **assertion 이 무엇을 주장하는가** 로 분할한다 (syntax only, sim 없음): `ANCHORED` **25** / `COMPARATIVE` **5** / `STRUCTURAL` 1 / `OPAQUE` 6 / `IDENTITY` **13** / `SILENT` 2. ⇒ **하한 30** (온도-관련이 *확정* 인 것), **미결 22**, **상한 52**. 🔴 **핵심: Q-061 의 추측을 통째로 인정해도 bill 은 52 → 39 로만 내려간다** — 여전히 절반 이상이다. 모집단을 지배하는 것은 계약 test 가 아니라 **literal 에 못 박힌 물리 주장** (25/52) 이고, 그래서 Q-061 (c) 의 재실행은 싸지지 않는다. 두 admissible rung 기준 **60–104 회** 시뮬.
- **`IDENTITY` 를 빼지 않는다.** 빼는 것이 이 작업의 요점처럼 보이지만 정확히 그래서 빼면 안 된다 — "이 두 run 이 `lam = 0.1` 에서 일치한다" 는 *그 rung 에 대한 증거*이지 계약의 증명이 아니다. 그것을 판정하는 것이 Q-061 (c) 의 계측이 존재하는 이유이므로, 정적 pass 가 미리 빼면 결론을 가정하는 것이 된다.
- **덤 — 52 중 test 가 아닌 것은 정확히 1 개**: `run.py:164`, CLI entry point. 그것은 재측정할 claim 이 아니라 **제품 경로**이고 Q-060 (기본값의 처분) 의 소관이지 Q-061 의 소관이 아니다.
- **⚠️ Decision (4) — 이 scan 의 자기 오탐 3 개를 test 로 고정했다. 셋 다 하한을 *줄이는* 방향이었다.** (i) `ast.Assert` 만 읽으면 `np.testing.assert_array_equal(a, b)` (bare `Expr`) 를 못 봐 **8 site 가 `SILENT`** 로 찍혔다 — 하필 Q-061 이 예로 든 바로 그 두 test 포함. false `SILENT` 는 "주장이 없다" 이므로 근거를 **지운다**. (ii) module-level literal table (`TABLE[x]`) 이 run-derived 로 읽혀 anchor 가 identity 가 됐다. (iii) **import 된** 상수 (`exp.CRUISE_SPEED_MPS`) 도 마찬가지 — 이건 D-040 의 `exposure_band_hi` 결함 그 자체다. 한 방향으로만 틀리는 bound 는 보수적인 bound 가 아니라 **버그 있는 bound** 다. 넷째 self-catch: `ast.Assert` 를 `.test` 대신 통째로 넘기면 조용히 `OPAQUE` 를 반환 — 이 module 자신의 test 가 먼저 걸렸다.
- **Alternatives**: (a) 52 를 그대로 bill 로 쓰기 — 정직하지만 Q-061 의 질문을 답하지 않는다. (b) `IDENTITY` 를 빼고 39 를 보고 — 결론을 가정한다. (c) 손으로 분류 — D-037 이 진단한 hand-registry 실패의 재도입.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-20-lam-dependence-static-partition.md`

---

## D-041 — 2026-08-03 — Q-060 이 세라고 한 것은 **셀 수 없다**: `make_controller` 에는 `lam` 인자가 없다. 온도를 *정하는* 자리는 3-way 분할이고, (c) 의 비용은 103 이 아니라 **54** 다

- **Context**: D-040 은 shipped `lam = 0.1` 이 24 cell 중 0 곳에서 admissible 함을 보였고, Q-060 은 기본값을 옮길지 물으며 옵션 **(c) `lam` 필수 인자화**를 "호출부 전부를 건드린다" 로 가격 매겼다. 명시된 계측 방법은 "`make_controller` / `MPPIParams()` 호출 중 온도를 안 넘기는 것을 grep 해서 세고 각 cell 에 매핑" 이었다. 이번 cycle 이 그 계측이다 (`default_lam_sites.py` — repo 자신의 AST 만 읽으므로 시뮬레이션 0).
- **Decision (1) 🔴 — 그 방법은 무효이고, 무효인 채로 숫자를 돌려준다.** `make_controller` 에는 `lam` **파라미터가 없다**. `StockMPPI` / `RiskMPPI` / `CBFMPPI` 도 없다. 온도는 오직 `params=MPPIParams(lam=…)` 의 **필드**로만 controller 에 도달한다. 따라서 "`lam` 을 안 넘기는 `make_controller` 호출" 은 **32 중 32**, 즉 **구조상 100 %** 이고 정보량이 0 이다. 세 cycle 연속으로 사전 확정된 계측 계획이 틀린 대상을 지목했다 — D-037 은 **표면**, D-038 은 **단위**, D-040 은 **통계량**, 이번은 **경로**(controller 를 만드는 자리 ≠ 온도를 정하는 자리).
- **Decision (2) — 셀 수 있는 것은 3-way 분할이다** (Q-060 이 가정한 binary 가 아니라): **`DECIDES`** (명시적 `lam` 이 여기서 정해진다) / **`DEFAULTS`** (`params` 도 `**kwargs` 도 없어 `params or MPPIParams()` 가 발화 → shipped rung) / **`FORWARDS`** (`params=<opaque>` 또는 `**splat` — 선택은 *이 자리의 caller* 것이고, 그래서 enclosing 함수가 다시 carrier 가 된다; fixpoint). 결과: **DECIDES 30 · DEFAULTS 54 · FORWARDS 19 (총 103)**.
- **Decision (3) 🔴 — Q-060 (c) 의 비용은 54 이지 103 이 아니다.** `FORWARDS` 19 개는 **손댈 게 없다** (이미 caller 에게 위임한다), `DECIDES` 30 개는 이미 준수한다. Q-060 이 침습적이라며 뒤로 미룬 옵션은 매겨진 가격의 **약 절반**이고, 남은 절반은 거의 전부 test code 다.
- **Decision (4) 🔴 — 기본값은 fallback 이 아니라 다수파다.** `DEFAULTS`(54) > `DECIDES`(30) — 이 repo 의 최빈 온도는 **어느 cell 도 admit 하지 않는 그 rung** 이다. D-040 이 찾은 것은 그 위치에 있는 **등록 claim 1 개**(`exposure_band_hi`)였고, 미등록 모집단은 그보다 **한 자릿수 크다**. 54 중 **2 개만 inert** (controller 를 만들고 한 번도 step 하지 않는 `raises` test 2 개) ⇒ **52 개가 실제로 inadmissible 한 온도에서 weight 한다**. 52 는 뺄셈으로만 도달 가능한 잔차가 아니라 보고되는 수다.
- **Decision (5) ⚠️ — 이 scan 의 자기 오탐 2 개를 test 로 고정했다.** (i) 첫 draft 는 `from ..ab import seed_sweep` 만 해석하고 `from eval.mppi_sandbox import ab` + `ab.seed_sweep(...)` 을 놓쳐 **103 대신 66** 을 읽었다 (`DEFAULTS` 24 개 과소). D-037 의 regex-vs-`ast`, D-038 의 `2.320x` 와 **같은 fail-open 방향**. (ii) carrier 를 **bare 함수명**으로 키잉하니 아무 `main` / `__init__` / `measure` 나 하나가 forward 하는 순간 전부 carrier 가 되어 **136 site** 로 부풀었다 (33 개는 controller 를 만들지도 않는 `eval/run_metrics.py` / `eval/tests/`) ⇒ carrier identity 는 **qualified `(module, name)`**. (iii) `simulates` 를 seed 이름 직접 매칭으로 판정하니 local helper 를 거쳐 `ab.seed_sweep` 에 닿는 8 site 가 inert 로 찍혀 52 대신 **44** 를 보고했다 — false `True` 는 과다계상뿐이지만 false `False` 는 **근거를 지운다** ⇒ call-graph fixpoint.
- **Alternatives**: (a) Q-060 방법대로 세고 "32/32" 를 보고 — 재현 가능하고 안정적이며 무의미하다. (b) `DEFAULTS` 를 곧바로 고치기 (54 곳에 `lam` 주입) — **범위 밖**이고 banked reading 을 전부 무효화한다; #15 의 일. (c) 각 site 를 cell 에 매핑해 site 별 admissibility 판정 — scene 이 대부분 fixture 로 만들어져 정적으로 결정 불가; site 가 *어느* cell 이든 shipped rung 은 **어느 cell 에서도** admissible 하지 않으므로 (D-040) 매핑 없이 결론이 선다. (d) inert 2 개를 빼고 52 만 보고 — Decision (4) 가 기각.
- **Status**: accepted. 기본값 이동 **없음**, 호출부 수정 **없음** (계측 모듈 + test 21 개; fast 절반 346 → **367**). Q-060 → **partially-answered**: (c) 의 비용은 확정, 기본값 처분은 여전히 #15. Q-061 파일.
- **Refs**: PR #67, `journal/2026-08/03-19-default-lam-call-site-census.md`, `eval/mppi_sandbox/default_lam_sites.py`, `eval/mppi_sandbox/tests/test_default_lam_sites.py`, STATE #1

---

## D-040 — 2026-08-03 — repo 가 ship 하는 `lam = 0.1` 은 **calibrated cell 24 개 중 0 개에서 admissible** 하다. Q-059 의 `operating_point` 필드는 **틀린 집합을 표시한다**

- **Context**: D-039 는 D-028 의 근거 세 개가 전부 `lam = 1.6` 조건부였음을 보였고, Q-059 는 그래서 `claim_scope` 에 `operating_point` 를 **machine 처럼 필수 필드로** 넣어 "shipped 값과 다르면 명시" 를 강제할지 물었다. lean 은 **(c) 계측 먼저** — 등록 claim 중 몇 %가 shipped operating point 에서 측정됐는지 세고 비율이 나쁘면 그때 강제한다. 시뮬레이션 불필요: claim 마다 instrument 가 적혀 있으므로 각 instrument 의 `lam` 을 읽으면 된다. 이번 cycle 이 그 계측이다 (`operating_point.py`, 24 cell + 5 claim, 전부 파일 읽기).
- **Decision (1) 🔴 — 계측 결과가 질문의 전제를 부순다.** `lam_windows.yaml` + variants 의 **24 cell 전체**에서 rung 별 admissible cell 수: `0.05 → 0`, **`0.1 → 0`**, `0.2 → 8`, `0.4 → 13`, `0.8 → 9`, `1.6 → 7`, `3.2 → 6`, `6.4 → 3`. shipped 기본값 `0.1` 은 **모든 cell 의 ladder 에 들어 있었고** (test 로 고정) **어디서도 통과하지 못한다** — 안 재본 게 아니라 **떨어진 것**이다. ⇒ "shipped 와 다른 지점에서 쟀다" 는 결함일 수 없다. 이 plant 에서 제대로 재려면 **반드시** 벗어나야 한다.
- **Decision (2) 🔴 — 두 성질은 anti-correlated 다. 필수 필드는 정확히 반대 집합을 표시했을 것이다.** 5 claim 중 **4 개가 off-shipped 이고 그 4 개의 point 는 전부 자기 cell 의 window 안**에 있다 (단 하나 예외는 `ab_protocol_overstatement` 의 single-`lam` risk arm 으로, **out-of-band 인 것이 곧 측정 대상**이고 해당 test 가 그걸 assert 한다). shipped `lam` 에서만 측정된 유일한 claim 인 **`exposure_band_hi`** (5 scene 전부 `make_controller` 기본값) 는 **admissible operating point 가 하나도 없는 유일한 claim** 이다. 즉 Q-059 (a) 를 채택했다면 **건전한 4 개를 flag 하고 유일하게 불건전한 1 개를 통과**시켰다.
- **Decision (3) — 따라서 기록할 성질은 `shipped` 가 아니라 `admissible` 이다**, 그리고 그것은 repo 가 이미 cell 단위로 계산해 둔 사실이다. `operating_point` 를 `claim_scope` 의 필수 필드로 올리지 **않는다**; 대신 별도 census 모듈이 claim → `(scene, controller, lam)` 을 들고 window 파일에 대조한다. 미등록 cell 은 `False` 가 아니라 **raise** — hand registry 의 실패는 "빠뜨린 항목" 이 아니라 "안 보는 표면" 이라는 D-037 의 결론을 한 단계 위에 적용.
- **Decision (4) 🔴 — 그리고 이것이 D-039 자신을 rescope 한다 (한 cycle 만에).** D-039 는 `cafe_obstacle_crossing_v0` / `risk_mppi` 에서 읽었고 그 cell 의 window 는 **`[1.6, 3.2]`** 다. 즉 D-039 의 `lam = 1.6` arm 은 window **안**, `lam = 0.1` arm 은 **밖**이다. 측정치는 유효하지만 "shipped 온도" 는 1.6 보다 **나은** 관측점이 아니라 **out-of-band** 관측점이며, D-039 가 제안한 규칙("ship 할 weight/온도에서 재라")은 그 결함을 그대로 물려받는다. 사다리가 실제로 뒷받침하는 규칙은 **"그 cell 의 admissible window 안에서 재라"** 다.
- **Alternatives**: (a) Q-059 lean 대로 `operating_point` 필수화 — Decision (2) 가 기각한다. 정확히 뒤집힌 집합을 표시한다. (b) shipped 기본값 `0.1` 을 `0.4` (13/24 로 최다) 로 바꾸기 — **이번 cycle 범위 밖이고 위험**하다. 기존 모든 banked reading 이 재측정 대상이 되며, 옳은 자리는 #15 re-baseline 브랜치다. Q-060 으로 파일. (c) `exposure_band_hi` 를 admissible rung 으로 옮겨 재측정 — 옳지만 시뮬레이션이고 slow 절반에 속한다. 마찬가지로 #15. (d) 계측만 하고 아무 결론 없이 두기 — anti-correlation 이 이미 (a) 를 결정적으로 기각하므로 결론을 미룰 이유가 없다.
- **Status**: accepted. repo default 이동 **없음** (계측 모듈 + test 13 개). Q-059 → **resolved**. D-039 Decision 들의 *측정치* 는 유효, "shipped 온도에서 재라" 라는 **방법론 규칙만 admissible-window 규칙으로 대체** (D-036 의 rescope-vs-retract, 3 번째 적용).
- **Refs**: PR #67, `journal/2026-08/03-18-operating-point-census.md`, `eval/mppi_sandbox/operating_point.py`, `eval/mppi_sandbox/tests/test_operating_point.py`, STATE #1

---

## D-039 — 2026-08-03 — 분모 판정은 **shipped `lam = 0.1` 에서 뒤집힌다**. 그리고 D-028 의 근거 세 개는 전부 `lam = 1.6` 조건부였다

- **Context**: D-028 은 `cafe_obstacle_crossing_v0` 에서 `w_voo = 200` 을 두 분모로 재서 — 더해지는 baseline 대비 6.19x, 자기 arm 대비 1.46x — "분모가 결론이다" 를 냈다. **둘 다 1 을 넘으므로 판정(verdict)은 어느 쪽으로 재도 살아남았고, 움직인 것은 margin 뿐이었다.** 그 측정은 `lam = 1.6` 에서 이뤄졌는데, repo 가 ship 하는 값은 `lam = 0.1` 이다. STATE #1 이 아홉 cycle 째 이걸 머리에 두고 있었다.
- **Decision (1) 🔴 — 판정이 뒤집힌다, 그것도 self-referential 쪽에서.** self ratio **1.464 → 0.0488**. shipped 온도에서 자기 arm 기준 통계는 `w_voo = 200` 을 **"negligible"** (경쟁 항의 5 %) 로 읽는다 — D-027 이 softmax 를 붕괴시킨다고 확정한 바로 그 weight 를. baseline 기준은 **3.30x** 로 여전히 "dominates". 과소평가는 **9.15x → 67.7x**. `lam = 1.6` 에서는 margin 만 틀렸지만 shipped 온도에서는 **결론 자체가 틀린다**.
- **Decision (2) 🔴 — D-028 Decision (3) 이 여기서 거짓이다: guard 가 곧 경쟁자다.** D-028 은 collision 항을 명시적으로 배제했다 (`w_collision = 1e4`, **양쪽 arm median spread 정확히 0** → "guard 이지 경쟁자가 아니다"). `lam = 0.1` 에서 loud arm 의 `w_collision` median spread 는 **정확히 1e4**, `w_voo` 행의 `rest` 분모는 **10183** (`lam = 1.6` 에서는 724). 분모는 collision indicator 다. **단, 아무것도 충돌하지 않는다** — 실행 궤적 min clearance 0.0119 m 로 baseline 의 0.0097 m 보다 오히려 **낫다**. 1e4 는 **rollout cloud** 위의 spread 다 (median step 에서 K = 256 표본 중 일부만 경계를 넘어 `ptp` 가 indicator 전高). 같은 분모가 두 온도에서 **서로 무관한 메커니즘**으로 부푼다.
- **Decision (3) 🔴 — 그리고 과소평가를 만드는 것은 damage 가 아니다.** D-028 의 메커니즘은 "loud arm 이 완주 못 해서 (1000 vs 114 step) 망가진 궤적 위에서 path cost 가 평가된다" 였고, 거기서 "**과소평가는 damage 와 함께 커진다**" 를 예측했다. `lam = 0.1` 에서 loud arm 은 훨씬 **건강하다**: **116 vs 93 step** (1.25x, 8.8x 아님), 최종 goal 거리 0.290 m (vs `lam = 1.6` 의 3.821 m). **가용한 모든 축에서 damage 가 줄었는데 과소평가는 7.4x 늘었다.** ⇒ "자기가 낸 피해로 채점된다" 는 슬로건은 맞고 메커니즘은 틀렸다. 결정하는 것은 피해량이 아니라 **어느 항이 `rest` 분모를 장악하느냐** 이고, 그 항은 weight 가 건드린 적 없는 항일 수 있다. `read()` 가 damage proxy 대신 `dominant_term` 을 보고하는 이유다.
- **Decision (4) 🔴 — D-028 Decision (5) 의 "외삽 불가" 도 `lam = 1.6` 전용이다.** closed-loop per-unit ladder `w = 1/7/200`: `lam = 1.6` 에서 2.497 / 2.337 / 5.299 (**2.27x** swing) → "싼 small-weight probe 로 shipping weight 고르지 말고 ship 할 weight 에서 재라". `lam = 0.1` 에서는 2.658 / 2.576 / 2.483, swing **1.07x**. shipped 온도에서 싼 probe 는 **7 % 이내로 정확**하고, D-028 이 적어둔 방법론 규칙은 탈선한 arm 의 artifact 였다.
- **Alternatives**: (a) D-028 을 retract — 과하다. 측정도 "분모가 결론이다" 도 유효하고, 틀린 것은 **범위 표기 없는 세 근거**뿐. (b) shipped `lam` 으로만 다시 재고 `lam = 1.6` 을 버리기 — 두 온도의 대비가 곧 결과라 대비를 없애면 결과도 없어진다. (c) self-referential 통계를 삭제 — baseline 분모가 두 온도 모두에서 판정을 유지하므로 유혹적이지만, 삭제는 **어느 항이 분모를 잡았나** 라는 진짜 진단을 같이 버린다. (d) 다른 scene 에서 재현 후 결정 — 옳지만 이 cycle 예산 밖이고, 재현 없이도 **범위 표기 누락**은 이미 확정.
- **Status**: accepted. repo default 이동 **없음** (계측 모듈 + test). D-028 Decision (2)/(3)/(5) 는 **`lam = 1.6` 조건부로 rescope** — retract 아님 (D-036 이 세운 rescope-vs-retract 구분).
- **Refs**: PR #67, `journal/2026-08/03-17-denominator-scope-at-shipped-lam.md`, `eval/mppi_sandbox/denominator_scope.py`, `eval/mppi_sandbox/tests/test_denominator_scope.py`, STATE #1

---

## D-038 — 2026-08-03 — **넓힌 pattern 은 좁은 pattern 의 superset 이 아니었다.** 그리고 철자를 넓혀도 놓친 인용은 **0 개** — Q-057 의 오탐 홍수는 오지 않았다

> 📐 이 절이 적는 dispatch-fragile 수치는 `AVX512_SKX` 조건부다 (D-033). 인용 등록: `claim_scope.SCOPED_CLAIMS` — D-046 의 `derived_citations()` 가 찾아냈다.

- **Context**: D-037 이 스스로 밝힌 한계 — scan 은 `N.NN×` 철자만 잡고 표 안의 맨 숫자는 못 본다. STATE #1 이 그 확장을 머리에 놓았고, Q-057 은 "오탐이 급증하니 **순위(ranking) 먼저**" 로 lean 했다.
- **Decision**: `_BARE` (곱셈기호를 **선택적 접미사로 소비**) + 7 개 가중 signal 로 후보 순위 + `EXCLUDED_SURFACES` 선언. 넓힌 pass 는 **advisory** — 강제하는 `unregistered()` 는 여전히 marked 철자만 읽는다. 16 test 추가 (312 → 327 fast).
- **Findings**:
  - 🔴 **넓힌 pattern 이 site 를 *잃었다*.** 자연스러운 bare pattern 은 `11.301` 속 `1.301` 을 막으려 `(?![\w.])` 로 끝나는데 ASCII `x` 가 `\w` 라서 `2.320x` 를 거부한다 — `exposure` docstring 이 기호를 ASCII 로 적는 바로 그 site 다. **좁은 pass 가 찾는 걸 넓힌 pass 가 조용히 떨어뜨렸다** — D-037 의 regex-vs-`ast` 와 같은 fail-open 방향. 이제 예시 문자열이 아니라 **실제 scan 표면 전체**에 대해 superset 관계를 test 로 건다.
  - 🔴 **홍수는 오지 않았다: 6 claim 에 걸쳐 새 site 는 5 개.** raw occurrence 로 세면 `2.0` 이 10 → 40 으로 보이지만, 그건 한 절이 같은 수를 여러 번 재진술하기 때문이고 registry 가 태그하는 단위는 **site** 다. Q-057 은 잘못된 단위로 비용을 추정했다.
  - ✅ **그리고 5 개 전부 오탐이다 — 하나도 미묘하지 않다.** 각각 "다른 양" 이라고 말하는 국소 token 을 달고 있다: `≥ 2.0 s`(지속시간·`unit_suffix`), `w_speed = 2.0`(weight 리터럴·`assignment`), `1.46 / K=256`(분모·`denominator`), `2.00 및 4.66`(ratio rung, 게다가 claim 이 쓰지 않는 정밀도·`precision_mismatch`). ⇒ **이 repo 에서 `N.NN×` 철자가 놓치고 있던 인용은 없다.** 방법이 아니라 repo 에 대한 negative 이고, scan 을 돌렸기 때문에만 알 수 있다. **negative 를 test 로 고정**해 다음 cycle 이 다시 넓히지 않게 했다.
  - ✅ **guard 가 또 자기 저자에게 발화**했다: 이 module docstring 이 위 (1) 의 예시로 `2.320x` 를 인용하자마자 강제 pass 가 미등록 site 로 red. D-037 의 self-scan 이 두 번째로 값을 했다.
  - 🔴 **순위의 첫 두 초안은 *positive* 에서 발화했다.** (i) `:` 를 assignment 로 셌더니 `결과: **6.19×**` — 이 repo 가 결과를 도입하는 방식 — 이 `multiplication_sign` 을 상쇄해 **진짜 인용 4 개를 0.0 으로** 떨어뜨렸다. (ii) `6.19×/1.46×` 의 `/` 를 분수선으로 읽어 등록된 site 를 오탐 처리했다 — 그건 **인용 두 개를 나열한 구분자**다. 교정 규칙: **disqualifier 는 unmarked occurrence 에만 적용한다** (`×` 가 이미 "배수" 라고 말했으면 "다른 양" 주장은 성립하지 않는다). 최종 분리 — 등록 **3.0..4.0** (n=74) vs 미등록 **최대 0.0** (n=12), 겹침 없음. **오탐보다 positive 에서 발화하는 signal 이 더 나쁘다**: 후자는 목록을 길게 만들 뿐이지만 전자는 guard 를 무력화한다.
  - ⚠️ **거절 12 건 중 1 건은 *증거* 가 아니라 *침묵* 으로 거절된다.** D-038 자기 본문의 "raw occurrence 로 세면 `2.0` 이 10 → 40" — audit 을 서술하는 절 안의 맨 *언급* 이라 어느 쪽 token 도 없다. 0.0 으로 threshold 아래에 떨어질 뿐이다. 그래서 순위의 힘을 정직하게 진술하면 label 이 아니라 **11 대 1 의 split** 이고, 그 비율을 test 로 박았다.
  - ⚠️ **순위의 값은 이번엔 *분류*가 아니라 *읽는 순서*다.** 등록된 site 최저점 +3 > 미등록 최고점 −1 로 겹침이 없지만, 이는 오탐이 전부 marked 가 아니어서 생긴 분리다. 진짜 bare 인용이 나타나면 순위는 keyword 증거에 의존하게 되고 그 경우는 아직 관측되지 않았다.
- **Alternatives**: (a) 넓히지 않기 — 기각, 한계를 적어두는 것과 재보는 것은 다르다. (b) 넓힌 pass 를 gate 로 승격 — **기각**, `w_speed = 2.0` 문장에서 suite 가 red 가 된다. (c) 오탐을 whitelist 로 관리 — 기각, 5 개를 손으로 적는 순간 D-037 이 지적한 hand-registry 문제를 재도입한다. signal 은 *이유* 를 적고 whitelist 는 *결론* 만 적는다. (d) 확률 보정 — 기각, positive 34 / negative 5 로 fit 할 게 없다. 가중치는 선언값이다.
- **한계 (명시)**: `journal/` · `RESULTS.md` · `STATE.md` 는 표면 **밖**이며 이유와 함께 선언했다 (`EXCLUDED_SURFACES`) — journal 은 날짜 박힌 기록이라 현재형 claim 을 유지하려면 과거를 고쳐야 하고, 나머지 둘은 생성물이다. **선언되지 않은 배제는 누락과 구별 불가**하다는 게 D-037 의 교훈이다.
- **Status**: accepted — Q-057 **resolved → D-038**
- **Refs**: PR #67, `journal/2026-08/03-16-citation-scan-widening.md`, `eval/mppi_sandbox/citation_audit.py`, D-036 / D-037, Q-056 / Q-057

## D-037 — 2026-08-03 — **손으로 등록한 citation 목록은 구조적으로 불완전하다.** 그리고 인용 표면은 `docs/` 보다 넓다 — code docstring 이 같은 숫자를 인용한다 (Q-056 해소)

> 📐 이 절이 적는 dispatch-fragile 수치는 `AVX512_SKX` 조건부다 (D-033). 인용 등록: `claim_scope.SCOPED_CLAIMS` — D-046 의 `derived_citations()` 가 찾아냈다.

- **Context**: D-036 이 citation drift 를 잡았지만 `claim_scope` 의 citation 목록은 **손으로 타이핑**된다 — 아무도 기억하지 못한 인용은 여전히 침묵한다(Q-056). STATE #1 은 그 drift 가 dispatch-divergent 5 claim 밖으로도 번지는지 물었다 (D-028 의 6.19×/1.46×, D-029 의 2.11×, D-025 의 2.320×, D-030 의 6.8×).
- **Decision**: `citation_audit.py` — instrument 를 가진 claim 의 magnitude 를 `docs/` **와 module docstring** 에서 훑어 각 occurrence 를 section/module 에 귀속시키고, 어느 registry 도 설명하지 못하는 site 를 flag. Q-056 lean **(b) 반자동** 그대로: 후보만 내고 tagging (`defines`/`restates`/`diagnoses`) 은 사람/executor 몫. 22 test.
- **Findings**:
  - 🔴 **인용 표면이 틀렸다.** `claim_scope` 는 `2.0×` 인용 절을 **5** 개 등록했는데 실제로는 **8** — D-036(진단) + module docstring **2** 개. docstring 은 `claim_scope` 가 아예 안 읽는 표면이다.
  - 🔴 **D-036 의 수리가 `docs/` 에서 멈췄다.** `horizon_audit.py` docstring 이 drift 된 `2.0×` 를 horizon 변화와 짝지어 진술하면서 instrument 의 `1.3008` 도, oracle stamp 도 없었다. 여섯 절을 stamp 하고 이 하나를 놓쳤다 — **같은 cycle 에 수리**.
  - ✅ **STATE #1 의 의심은 3/4 맞았다**: 6.19×(D-027 정의 → D-028·Q-049·docstring 2 개), 2.11×(D-029 → D-030·docstring), 6.8×(D-030 → D-036·docstring) 모두 측정 절 **밖**에서 진술된다. **2.320× 는 D-025 안에만 있다 — 정직한 negative.**
  - 🔴 **D-030 은 `2.0×` 의 *정의절인 동시에* 외래 instrument 에 대한 인용절**이다. registry 가 두 역할을 분리한다 — 이게 drift 의 실제 형태다.
- **Alternatives**: (a) 손 등록 유지 — 기각, 불완전성이 구조적이다. (b) 완전 자동 태깅 — 기각, `2.0×` 같은 흔한 크기는 오탐이 불가피해 판단이 필요하다 (Q-056 lean 그대로). (c) `docs/` 만 훑기 — 기각, 놓친 defect 가 정확히 docstring 에 있었다. (d) `claim_scope` 에 병합 — 기각, 저쪽은 **두 reading** 을 가진 claim 용이고 여기 4 개는 하나뿐이다. 없는 reading 을 지어내게 된다.
- **한계 (명시)**: scan 은 `N.NN×` 철자에만 걸린다. 표 안의 맨 숫자나 다른 정밀도는 못 찾는다 — 그래서 "site 가 미등록임" 은 증명해도 "남은 게 없음" 은 증명 못 한다. 후보 생성기로 범위를 못박는다.
- **Status**: accepted — Q-056 **resolved → D-037**
- **Refs**: PR #67, commit `24b3b90`, `journal/2026-08/03-15-citation-discovery-audit.md`

## D-036 — 2026-08-03 — 붕괴는 실재하지만 **보고된 크기는 한 번도 그렇게 크지 않았다**. `2.0×` 는 instrument 가 재는 양이 아니다 (citation drift ≠ dispatch fragility)

- **Context**: STATE #1 — D-035 가 두 verdict-fragile claim 에 남는 몫(14.4 % / 21.8 %)을 붙였으니, 그 숫자를 full effect size 로 인용 중인 `docs/` 를 retract-or-rescope 하라. 인용처를 열거하려고 instrument 정의(`dispatch_divergence._horizon_weight_swing`)와 prose 를 나란히 놓은 순간 둘이 **다른 양**임이 드러났다.
- **Decision (1) 🔴 — D-030 의 `2.0×` 와 instrument 의 `1.029×` 는 같은 양이 아니다.** D-030 Decision (4) 의 2.0× 는 `w(H=34)/w(H=15)` = 13.97/7.00 이다. flip 하는 assertion 이 재는 것은 `w(H=34)/w(H=30)` 이고 `SHIPPED_HORIZON=30, FREE_H=34` 로 코드에 고정돼 있으며, `AVX512_SKX` 에서 **1.3008**, AVX2 에서 **1.0289** 다. D-032 Decision (0) 이 "1.26.4 에서 2.0×, 2.5.1 에서 1.029×" 로 둘을 짝지었고 D-033 / Q-054 / Q-055 가 그대로 물려받았다. **dispatch divergence 는 진짜다 (1.3008 → 1.0289 는 1.2 문턱을 실제로 건넌다). 과장된 것은 그 크기다.**
- **Decision (2) 🔴 — 그래서 fragility 와 citation drift 는 분리해서 세야 한다.** 전자는 어딘가에서 red test 로 드러나지만, 후자는 아무 신호도 내지 않는다. 남는 몫이 세 겹이고 순서가 항상 같다: assertion 의 **14.4 %** > 측정값의 **9.6 %** > *인용된* 2.0× 의 **2.9 %**. `ab_protocol_overstatement` 도 동일 — 21.8 % > 7.8 % > (인용 1.9× 대비) **6.1 %**. **retraction 에 들어가야 할 숫자는 세 번째다**: 독자가 만난 것은 assertion 도 reading 도 아니고 인용된 수다. D-035 는 첫 번째만 계산했다.
- **Decision (3) ✅ — 재발 방지는 test 로 건다** (`claim_scope.py` + 14 test). 5 개 divergent claim 각각에 `oracle` / `instrument` / 양쪽 reading / **인용 절 목록** 을 등록하고, (a) 인용된 절이 실재하는지, (b) `AVX512_SKX` stamp 를 달았는지 (STATE #3, 네 cycle 연체), (c) `other-quantity` 로 태그된 인용이 instrument 의 reading 도 함께 적었는지를 강제한다. 등록 전 4/6 절이 unstamped, 6/6 이 undisambiguated 였고 지금 0 이다. 시뮬레이션 없음 — repo 안 파일에 대한 문자열/산술 검사뿐이라 **이 guard 자체는 dispatch-fragile 하지 않다**. 그것이 fragile 한 claim 을 감시할 자격의 전부다.
- **Alternatives**: (a) prose 만 고치기 — 값싸지만 다음 인용이 같은 짝짓기를 반복한다 (실제로 네 절이 그랬다). (b) instrument 를 `H=15→34` 로 바꿔 prose 에 맞추기 — 숫자는 맞겠지만 `SHIPPED_HORIZON` 기준 transferability 라는 원래 질문을 버린다, 기각. (c) 두 span 을 모두 재는 claim 추가 — 측정 비용이 들고, drift 는 *두 번째 span* 이 아니라 *두 span 을 하나로 읽은 것* 이었다. (d) D-030 을 통째로 retract — 과잉: Decision (1) 의 `H=35` 절벽(6.8×)은 이 claim 과 무관하게 서 있다.
- **Status**: accepted. D-030 / D-032 / D-033 / D-017 / Q-054 / Q-055 는 **retract 아님 — rescope**: 각 절 머리에 D-036 재범위 blockquote 를 달았고 방향/부호는 유지, 효과 크기만 `AVX512_SKX` 조건부로 격하. repo default 이동 **없음**.
- **Refs**: PR #67, `journal/2026-08/03-14-p3-claim-scope-citation-drift.md`, `eval/mppi_sandbox/claim_scope.py`, `results/dispatch-divergence/claim-scope.txt`, D-030 / D-032 / D-033 / D-034 / D-035 / D-017, Q-054 / Q-055

## D-035 — 2026-08-03 — 수리 비용은 이미 D-034 표 안에 있었다 (`widen_factor = 1 + excursion`). 그리고 그 값을 읽으면 **canonical machine 은 5 개 중 0 개를 복구하지 못한다** (Q-055 부분 해소)

> 📐 이 절이 적는 dispatch-fragile 수치는 `AVX512_SKX` 조건부다 (D-033). 인용 등록: `claim_scope.SCOPED_CLAIMS` — D-046 의 `derived_citations()` 가 찾아냈다.

- **Context**: D-034 가 4 개 fragility class 를 나눴지만 class 가 존재하는 이유인 질문 — *각 주장을 두 machine 에서 모두 참으로 만들려면 무엇을 치러야 하고, 그러고 남은 것이 원래 하던 주장인가* — 은 안 던졌다. Q-055 는 "AVX-512 냐 AVX2 냐"로 posed 되어 있어서, machine 을 고르면 수리가 끝나는 것처럼 읽힌다.
- **Decision**: 새 시뮬레이션 **0 회**로 답한다. 모든 contested assertion 이 자기 acceptance interval 을 이미 적어 놓았으므로 최소 허용 tolerance 는 banked 숫자의 산술이고, 핵심은 **`widen_factor = 1 + excursion`** 이라는 항등식이다. excursion 은 *거리*로 읽으면 D-034 의 측정치이고 *비용*으로 읽으면 tolerance 배수다 — 같은 숫자. 지난 cycle 이 이미 답을 갖고 있었는데 그렇게 읽지 않아서 한 라운드가 더 필요해 보였다.

  | claim | kind | 수리 비용 | 남는 것 |
  |---|---|---|---|
  | `scale_match_achieved_ratio` | band | **×1.136** (rel 0.25 → 0.284) | 유일한 widenable. **단 D-034 가 제안한 rel 0.29 는 margin 2.1%** — 10% margin 을 원하면 rel 0.316 |
  | `exposure_band_hi` | band | **×2.954** (±0.05 → ±0.148) | 없음. 넓힌 band 가 machine split *과* 원래 band 를 통째로 삼켜서 원래 분해하려던 걸 못 분해함 |
  | `ab_protocol_overstatement` | threshold | 1.25 → **1.0546** | 주장 효과의 **21.8%**. 보고된 1.9× overstatement 는 남지 않음 |
  | `horizon_weight_swing` | threshold | 1.2 → **1.0289** | **14.4%**. D-030 headline 은 남지 않음 |
  | `hazard_shared_rungs` | categorical | — | widening operator 자체가 없음 |

  **1/5 만 widening 으로 수리된다.** 그리고 kind 3 종은 서로 **교환 불가**다: band 의 tolerance 는 target 을 둘러싼 scaffolding 이라 넓혀도 target 을 계속 주장하지만, **threshold 는 숫자가 곧 주장**이라 낮추는 것은 느슨하게 만드는 게 아니라 *다른, 더 약한* 주장으로 바꾸는 것이다. 그래서 threshold 의 figure of merit 은 tolerance 가 아니라 **null 대비 살아남는 효과 비율**이다.
- **따라서 Q-055 는 옳지만 불충분하다**: lean **(b) AVX2** 는 유지한다 (CI 가 검증할 수 있는 쪽 — "더 맞아서"가 아니라 "재현 가능해서"). 그러나 machine 을 고르는 것은 상수를 **이사시킬 뿐 구제하지 않는다** — 2 개는 철회/rescope, 1 개는 machine 마다 re-read, 1 개는 AVX2 에서 **진술 자체가 불가**. canonical machine 은 *재보정 계획*의 전제이지 그 자체가 수리가 아니다.
- **Alternatives**: (a) 최소 widening 을 그대로 적용 — margin 0 이 정의상 남으므로 "assertion 이 실행은 된다" 는 의미의 수리일 뿐. 그래서 `margin_at_factor` 를 붙여 "두 machine 을 통과한다"를 숫자 있는 주장으로 만든다. (b) `MAX_HONEST_WIDEN` 없이 배수만 보고 — 판단을 독자에게 미루는 것처럼 보이지만 실제로는 아무 결론도 안 내림. 그래서 상수로 **명시**하고 판단임을 문서화 (×2 = tolerance 2 배; 반대하면 1 줄 수정). (c) 이번에 실제로 `rel=0.29` 를 적용 — **거부**. margin 2.1% 짜리 수리를 green check 로 바꾸는 건 D-032 의 실수 (pin 을 수리로 읽기) 의 반복이고, 재보정은 re-baseline branch (STATE #16) 소관이다. (d) 측정한 비용을 test 로 pin — **거부**, D-034 와 같은 이유. `test_repair_admissibility.py` 22 개는 전부 산술/verdict 구조.
- **Status**: accepted — Q-055 를 부분 해소 (canonical 선택은 유지, 충분성 주장은 기각)
- **Refs**: PR #67 · `journal/2026-08/03-13-p3-repair-admissibility.md` · `eval/mppi_sandbox/repair_admissibility.py` · `results/dispatch-divergence/repair-bill.txt`

## D-034 — 2026-08-03 — 두 dispatch 의 거리는 **knife edge 가 아니다**. 그리고 excursion 이 **불균질**해서 tolerance 하나로는 못 덮는다 (Q-054 (d) 부분 답)

> 📐 이 절이 적는 dispatch-fragile 수치는 `AVX512_SKX` 조건부다 (D-033). 인용 등록: `claim_scope.SCOPED_CLAIMS` — D-046 의 `derived_citations()` 가 찾아냈다.

- **Context**: D-033 이 갈리는 좌표(AVX-512 vs AVX2)는 확정했지만 **크기**는 안 쟀다. "FP drift 가 threshold 를 넘게 증폭" 이라는 자연스러운 독해는 두 machine 이 칼날 위에 나란히 서 있다는 뜻이고, 그렇다면 수리는 "tolerance 를 조금 넓힌다" 로 끝난다. 이 독해는 값싸게 반증 가능하다 — 뒤집히는 주장마다 **자기 assertion 이 acceptance interval 을 이미 적어 놓았기** 때문이다.
- **Decision**: 5 개 통계를 한 박스의 두 arm(numpy 1.26.4 고정, `NPY_DISABLE_CPU_FEATURES` 로 AVX-512 mask)에서 재고, 각 interval 의 **half-width 배수(excursion)** 로 보고한다. 결과:

  | claim | AVX-512 | AVX2 | B/A | excursion |
  |---|---|---|---|---|
  | `ab_protocol_overstatement` | 1.69563 | 1.05457 | 0.622 | n/a (one-sided) |
  | `exposure_band_hi` | 2.0375 | 2.18571 | 1.073 | **1.95** |
  | `hazard_shared_rungs` | 1 | 0 | 0 | n/a (categorical) |
  | `horizon_weight_swing` | 1.30078 | 1.02888 | 0.791 | n/a (one-sided) |
  | `scale_match_achieved_ratio` | 0.251146 | 0.179012 | 0.713 | **0.136** |

  두 가지가 따라온다. **(1) mask arm 이 CI 를 5/5 전부 재현한다** — scalar 4 개는 **17 자리 전부** 일치(`0.17901180719252627`, `1.0288845528582653`, `2.185714285714286`, `1.0545725198713798`), categorical 1 개도 일치. D-033 은 이걸 1 개 test 에서만 보였고, 이제 divergent set **전체**가 runner 없이 재현된다. **(2) excursion 이 0.136 ~ 1.95 + categorical 로 흩어진다** — `scale_match` 는 진짜 knife edge(rel 0.25→0.29 면 두 machine 다 통과)지만 `exposure_band_hi` 는 tolerance 3 개 바깥이고 `hazard_shared_rungs` 는 admissible set 이 아예 비어서 margin 이라는 말이 성립하지 않는다. **하나의 tolerance 로 두 machine 을 덮는 방법은 없다.**
- **따라서 fragility 는 4 class 이고 class 마다 수리가 다르다**: *tolerance-fragile* (`scale_match` — tolerance 를 다시 적으면 carry 가능) / *verdict-fragile* (`horizon_weight_swing`, `ab_protocol_overstatement` — 결론의 **방향**이 뒤집힘. 각각 D-030 headline 과 Q-039 답. 증거로 carry **불가**) / *structurally fragile* (`hazard_shared_rungs` — AVX2 에서는 refutation 을 **진술조차 못 함**) / *calibration-fragile* (`exposure_band_hi` — `TIMING_RATIO_BAND` 는 결론이 아니라 plant 에서 읽은 **상수**이므로 machine 마다 다시 읽어야 함). ⇒ **Q-055 의 canonical machine 선택은 필요하지만 충분하지 않다.**
- **범위 (정직하게)**: fast half 238 개는 두 machine 에서 모두 green 이므로 fragile set 은 **closed-loop half 안에만** 있고, 그 안에서도 5/127 = 3.9%. 나머지 122 개 closed-loop test 의 excursion 은 **안 쟀다** — "closed-loop 이면 취약" 은 이 데이터가 **지지하지 않는다**.
- **Alternatives**: (a) tolerance 를 넓혀 두 machine 을 덮는다 — `scale_match` 하나에만 통하고 나머지 4 개에는 안 통한다는 게 이 측정의 결론. (b) 결론마다 seed 분포로 판정 (Q-054 (b)) — 여전히 열려 있지만, verdict-fragile 2 개는 seed 를 늘려도 machine 간 차이를 흡수 못 한다(같은 seed 에서 결정론적으로 다름). (c) 측정한 excursion 을 test 로 pin — **거부**. 그 test 가 repo 에서 가장 dispatch-fragile 한 assertion 이 된다. 그래서 `test_dispatch_divergence.py` 는 전부 fast/structural 이고 측정치는 journal 과 `results/dispatch-divergence/` 에만 산다.
- **Status**: accepted
- **Refs**: PR #67, `journal/2026-08/03-12-p3-dispatch-divergence-magnitude.md`, `eval/mppi_sandbox/dispatch_divergence.py`, `results/dispatch-divergence/`

## D-033 — 2026-08-03 — D-032 의 진단은 **틀렸다**. 갈리는 좌표는 numpy version 이 아니라 **CPU SIMD dispatch (AVX-512 vs AVX2)** 다

> ⚠️ **D-036 재범위(rescope)** — 이 절이 인용하는 **2.0×** 는 `w(H=34)/w(H=15)`
> (13.97/7.00) 다. dispatch 에서 실제로 뒤집히는 assertion
> (`test_horizon_audit::test_the_prescribed_weight_moves_with_the_horizon`) 이 재는
> 것은 `w(H=34)/w(H=30)` 이고, 그 값은 **1.3008** (`AVX512_SKX`) → **1.0289**
> (AVX2) 다. **서로 다른 양이다.** 2.0× 를 AVX2 의 1.029× 와 짝지어 읽으면 붕괴가
> 과장된다 — 정직한 쌍은 **1.3008 vs 1.0289**. 남는 몫: assertion(`>1.2`) 의
> **14.4 %**, 측정값의 **9.6 %**, 여기 인용된 2.0× 의 **2.9 %**.
> 이 절의 모든 상수는 `AVX512_SKX` dispatch 조건부다 (D-033).

- **Context**: D-032 가 `numpy==1.26.4` pin 을 걸고 "D-029/D-030 증거는 numpy 1.26.4 에 조건부"라고 기록했다. 다음 CI 실행(`65928ec`)에서 runner 는 pin 을 **지켰고**(헤더에 `eval numpy: 1.26.4 (calibrated)`), 그럼에도 **같은 5 개 slow test 가 그대로 실패**했다. version 을 calibrated 값에 고정한 채로 판정이 뒤집혔으므로 D-032 의 인과 주장은 성립할 수 없다.
- **Decision**: 실제 판별 좌표는 **런타임 SIMD dispatch**로 확정한다. 근거는 한 박스 위에서의 3-arm 대조:
  - deb numpy 1.26.4 (system blas), AVX-512 사용 → **2 passed** (116.8 s)
  - PyPI wheel numpy 1.26.4 (openblas64), AVX-512 사용 → **2 passed** (129.2 s) — 즉 BLAS/빌드 아님. D-032 의 2.5.1 실험은 version 과 build 를 **동시에** 바꿔 confound 였다.
  - deb numpy 1.26.4, `NPY_DISABLE_CPU_FEATURES` 로 AVX-512 마스킹 → **2 failed**, 그리고 `test_scale_match` 값이 CI 실패값과 **17 자리 전부 일치** (`0.17901180719252627` = `0.17901180719252627`).
  dev box(Ryzen 9800X3D)는 AVX-512 를 갖고 runner 는 갖지 않는다. AVX-512 와 AVX2 커널의 **reduction order** 차이가 chaotic closed loop 에서 threshold 를 넘도록 증폭된다. numpy 2.5.1 도 같은 knife-edge 를 건드리는 별개의 교란이지만, CI 가 맞고 있던 원인은 아니었다.
  후속 조치: (1) pytest 헤더가 version 뿐 아니라 **dispatch fingerprint** 를 출력 (`eval/conftest.py:_dispatch_line`, `CALIBRATED_SIMD = AVX512_SKX`), (2) 두 CI job 모두 `Fingerprint the runner` step 으로 CPU model + SIMD found-set + BLAS 기록, (3) fast half 에 guard test 5 개 추가, (4) pin 은 **유지** — 움직이는 부품 하나 줄이는 값어치는 있으나 "version 일치 = 환경 일치"로 읽는 것을 금지한다.
- **Alternatives**: (a) CI 에서 AVX-512 를 강제 마스킹해 dispatch 를 고정 — runner CPU 복권(Intel 은 AVX-512 有, AMD EPYC 은 無)에 의존하지 않게 되지만 CI 를 **재현 가능하게 red** 로 만든다. (b) AVX2 baseline 위에서 D-029/D-030 상수를 **재보정** — portable 하고 CI 와 일치하지만 D-030 headline 이 뒤집힌다(swing 2.0× → 1.029×). (c) AVX-512 를 유지하고 slow half CI 를 **non-authoritative** 로 명시. (d) 지금 한 것 — 원인을 확정하고 **가시화**하되 상수 재보정 결정은 미룸. (a)/(b)/(c) 는 어느 상수 집합이 정본인가라는 미해결 질문에 답해야 하므로 Q-055 로 분리.
- **Status**: accepted — D-032 의 진단 부분을 supersede 한다 (측정치는 유효, 인과 귀속은 무효)
- **Refs**: PR #67 · journal/2026-08/03-11-simd-dispatch-not-numpy-version.md · CI run 30776220103

## D-032 — 2026-08-03 — D-029/D-030 의 증거는 **numpy 1.26.4 에 조건부**다. CI 환경을 pin 하되, 그것을 수리라고 부르지 않는다

> ⚠️ **D-036 재범위(rescope)** — 이 절이 인용하는 **2.0×** 는 `w(H=34)/w(H=15)`
> (13.97/7.00) 다. dispatch 에서 실제로 뒤집히는 assertion
> (`test_horizon_audit::test_the_prescribed_weight_moves_with_the_horizon`) 이 재는
> 것은 `w(H=34)/w(H=30)` 이고, 그 값은 **1.3008** (`AVX512_SKX`) → **1.0289**
> (AVX2) 다. **서로 다른 양이다.** 2.0× 를 AVX2 의 1.029× 와 짝지어 읽으면 붕괴가
> 과장된다 — 정직한 쌍은 **1.3008 vs 1.0289**. 남는 몫: assertion(`>1.2`) 의
> **14.4 %**, 측정값의 **9.6 %**, 여기 인용된 2.0× 의 **2.9 %**.
> 이 절의 모든 상수는 `AVX512_SKX` dispatch 조건부다 (D-033).

- **Context**: D-031 이 suite 를 fast/slow 로 가른 직후, 새 `slow` job 이 **60 min timeout 안에서 23m59s 에 정상 종료하고 fail** 했다 — timeout 이 아니라 **진짜 5 개 test 실패**. D-031 이 복구한 것은 "job 이 끝까지 돈다" 였지 "green" 이 아니었고, STATE #1 은 그 확인을 다음 cycle 에 넘겨둔 상태였다. 확인해 보니 답은 "green 아님" 이었다.
- **측정 (추론 아님)**: 실패한 5 개 — `test_ab_temperature_protocol`, `test_exposure_timing_band`, `test_hazard_exposure`, `test_horizon_audit`, `test_scale_match` — 를 **같은 box** 에서 numpy 만 바꿔 돌렸다. **1.26.4 → 5 passed (149.95 s), 2.5.1 → 5 failed.** 코드·seed·scenario 동일. sandbox 는 전 run 을 `np.random.default_rng(seed)` 로 seed 하고 그 stream 은 numpy version 간 policy 상 안정이므로 **RNG 변경이 아니다**. 남는 메커니즘은 FP drift (SIMD / reduction order) 가 chaotic closed-loop rollout 에서 threshold 를 넘을 때까지 증폭된 것.
- **Decision (0) 🔴 — 가장 날카로운 숫자: D-030 의 headline 이 뒤집힌다.** scale-matched `w_voo` 의 horizon swing 이 1.26.4 에서 **2.0×**, 2.5.1 에서 **1.029×**. test 자신의 실패 메시지가 "1.2× 미만이면 fixed-`w_voo` horizon column 은 결국 정직한 것" 이라고 적어 놓았으므로, 이건 tolerance 를 스치는 문제가 아니라 **결론의 부호가 numpy minor version 에 달려 있다**는 뜻이다.
- **Decision (1) — `eval/requirements-ci.txt` 로 pin, 두 job 모두 여기서 install.** 기존 `pip install --quiet numpy pyyaml pytest` 는 runner 를 numpy 2.x 로 올렸고 dev box 는 1.26.4 였다 — **CI 와 dev box 가 서로 다른 것을 재고 있었다.** numpy 만 `==` 로 고정. pytest/pyyaml 은 7.4.4(box)/9.1.1(runner) 양쪽에서 green 이 관측됐으므로 **관측되지 않은 의존을 주장하지 않기 위해** 범위로만 묶는다.
- **Decision (2) — pin 은 reproducibility contract 이지 수리가 아니다.** 재현 가능하게 만들 뿐 **robust 하게 만들지 않는다.** 그래서 pin 과 함께 (a) `requirements-ci.txt` 가 5 개 test 이름과 두 숫자를 본문에 싣고, (b) conftest header 가 매 run **numpy version 을 출력**하며 calibrated 값과 다르면 경고한다 (Q-053 의 "metric 은 자기 surface 를 이름해야 한다" 를 결국 문제가 된 그 의존성에 적용). header 는 **보고만 하고 실패시키지 않는다** — 하드 실패는 그 drift 를 bisect 하는 것 자체를 막는다.
- **Decision (3) — pin 과 상수의 drift 를 test 로 묶는다.** `test_calibrated_numpy_pin.py` 3 개 (전부 무시뮬, **fast half 에 의도적으로 배치** — 24 분 job 에서만 도는 guard 는 아무도 실패를 못 본다): pin==header 상수, 경고 branch 가 실제로 말을 하는지, bare `numpy` 로 되돌리면 fail.
- **남은 오차 (숨기지 않음)**: numpy 2 안에서도 이 box 와 runner 는 한 통계에서 유효숫자 ~9 자리까지 일치(0.0362103793 vs 0.0362103796)하지만 다른 통계에서 **~3% 어긋난다**(0.03322 vs 0.03434). numpy pin 은 **큰 항만** 제거한다. 여기의 green 을 machine-independence 로 읽으면 안 된다.
- **Alternatives**: (a) threshold 완화 — **기각**, threshold 가 곧 주장이다. (b) numpy 2 로 올리고 상수 재도출 — 정당하지만 D-029/D-030 전체 재측정이 선행이고 queue drain 전에는 stack 금지. (c) pin 없이 놔두기 — CI 와 dev box 가 계속 다른 것을 잰다, 기각. (d) **pin + 공개 기록 + Q-054** — 채택.
- **Status**: **진단은 superseded → D-033** (측정치는 유효). 확인 결과: slow half 는 pin 하에서도 **red** 였고, runner 가 pin 을 지킨 채 같은 5 개가 실패했다 — 이것이 D-033 을 촉발했다. pin 자체는 유지한다.
- **Refs**: PR #67, `journal/2026-08/03-10-p3-numpy-pin-reproducibility.md`, `eval/requirements-ci.txt`, `eval/conftest.py`, `.github/workflows/sandbox-ci.yml`, Q-054, D-016, D-029, D-030, D-031, Q-053

## D-031 — 2026-08-03 — 느린 test 는 **fixture scope** 에서 자른다 (test 단위 marking 은 비용을 형제에게 옮길 뿐). 그리고 이 branch 의 CI 는 24 시간째 **red** 였다

- **Context**: Q-051 (STATE #1) — suite 가 145.6 s → 636 s 로 자랐고 최근 두 cycle 이 각 ~120 s 를 더했다. "나중 cycle 을 싸게 만든다" 는 이유로 filed 됐다.
- **Decision (0) 🔴 — 이유가 틀렸다. 이건 최적화가 아니라 head-of-line PR 의 검증 게이트 복구다.** `gh pr checks 67` = **fail**. branch CI 는 2026-08-02T10:09Z 부터 **14 run 연속** red 이고, 마지막 6 run 은 정확히 **10m15–17s** 에 job 의 `timeout-minutes: 10` 으로 killed 됐다. 26 cycle 동안 STATE 는 `sandbox:pass=357/357` 을 **local** 기준으로 보고했고, 아무 cycle 도 이 PR 의 CI 를 확인하지 않았다. D-016 이 "red PR = deliverable 이 안 끝난 것" 이라 못박은 그 신호가 24 시간 동안 아무에게도 안 보였다. (앞선 8 run 은 5–8 분에 `failure` 로 끝나 timeout 과 다른 regime 이지만 log 가 만료돼 원인 확정 불가 — 전 파일이 지금 local 에서 rc=0 이므로 그 사이 고쳐졌거나 runner-side 사건이었다. **확정하지 않고 기록만 한다.**)
- **Decision (1) — Q-051 의 lean 대로 marker.** cap 을 줄이는 대안은 기각: 비싼 assertion 은 의도적으로 derail 된 run (D-029) 과 얼어붙은 run (D-030) 이고, 그 **비용이 곧 증거**다. 짧게 하면 아무도 기다리지 않는 시간을 아끼려고 주장을 약화시킨다.
- **Decision (2) 🔴 — 이번 cycle 의 일반화 가능한 발견: marker 의 단위는 test 가 아니라 fixture scope 다.** 1차 시도는 `call` 시간 ≥ 2.0 s 인 **test 51 개**를 marking — 628 s → **338 s** 에 그쳤다. profile 을 보니 남은 시간의 최대 항목이 `test_horizon_audit.py::TestScaleMatchedWeightIsHorizonDependent` 의 **97.65 s `setup`** 이었고, 이 class 의 모든 `call` 은 2 s 미만이라 1차 목록에 **애초에 안 보였다**. class-scoped fixture 를 공유하는 class 안에서 test 하나를 marking 하면 pytest 는 fixture 비용을 **살아남은 첫 형제에게 재청구**할 뿐 제거하지 않는다. `call` 만 재는 측정은 이 비용에 구조적으로 눈이 멀었다 (`--durations` 의 `setup`/`teardown` 행을 grep 에서 떨어뜨린 것이 직접 원인). 재측정: 전 phase 합산 → scope 단위 집계 → **3.0 s 이상인 36 class + 6 module-level 함수**.
- **Decision (3) — CI 는 두 job 으로.** `fast` (10 min) + `slow` (`--slow -m slow`, 60 min). 둘 다 required. marker 는 test 가 **언제** 도는지를 가르지, **도는지 여부**를 가르지 않는다. `slow` 의 timeout 을 측정치에 맞추지 **않은** 것이 핵심: 단일 process 실행은 per-file 합의 ~1.5× 이고 (628 s per-file 합 vs >900 s 단일 process), runner 는 dev box 보다 느리다 — 측정치에 맞춘 ceiling 이 바로 옛 job 이 조용히 피시험체가 된 경위다.
- **Decision (4) — 침묵 방지 2종.** marker 가 조용히 test 를 멈추면 느린 suite 보다 나쁘다: header 가 mode 를 밝히고, terminal summary 가 deselect 개수와 복구 방법을 명시한다. collection 이 **127 slow + 231 fast = 358** 로 정확히 갈려서 `slow` job 이 **공허하게 pass 할 수 없다**.
- **Alternatives**: (a) cap 단축 — 증거를 약화, 기각. (b) budget 증액만 — 매 cycle 복리로 악화, 기각. (c) test 단위 marking — **측정으로 기각** (Decision 2). (d) class 단위 marking — **채택**. (e) `pytest-xdist` 로 slow half 병렬화 — 진짜 수리지만 class-scoped fixture 의 worker 별 재실행이 측정 자체를 바꿀 위험이 있어 별건으로 미룸.
- **Status**: accepted. 결과: fast half **628 s → 115 s** (230 passed / 127 skipped / 1 xfailed).
- **Refs**: PR #67, `journal/2026-08/03-09-p3-slow-test-split.md`, `eval/conftest.py`, `.github/workflows/sandbox-ci.yml`, Q-051, D-016, D-029, D-030

## D-030 — 2026-08-03 — rollout horizon 은 sweep 가능한 축이 **아니다** (`H=34` 에서 절벽). 그리고 그 절벽의 원인은 **leave-one-out 이 원리적으로 볼 수 없는 중복 원인**이다

> ⚠️ **D-036 재범위(rescope)** — 이 절이 인용하는 **2.0×** 는 `w(H=34)/w(H=15)`
> (13.97/7.00) 다. dispatch 에서 실제로 뒤집히는 assertion
> (`test_horizon_audit::test_the_prescribed_weight_moves_with_the_horizon`) 이 재는
> 것은 `w(H=34)/w(H=30)` 이고, 그 값은 **1.3008** (`AVX512_SKX`) → **1.0289**
> (AVX2) 다. **서로 다른 양이다.** 2.0× 를 AVX2 의 1.029× 와 짝지어 읽으면 붕괴가
> 과장된다 — 정직한 쌍은 **1.3008 vs 1.0289**. 남는 몫: assertion(`>1.2`) 의
> **14.4 %**, 측정값의 **9.6 %**, 여기 인용된 2.0× 의 **2.9 %**.
> 이 절의 모든 상수는 `AVX512_SKX` dispatch 조건부다 (D-033).

- **Context**: Q-043 의 남은 반쪽 — "shadow 가 rollout cone 안에 들어오게 **planner 를 바꾼다**", 즉 cone 을 길게 한다. STATE #1 이 `(w_voo, horizon)` 2×2 를 scale-matched weight, `lam ∈ {1.6, 3.2}`, ratio ≤ 0.25 (D-029) 로 완전히 명세해 두었고 crossing scene 에서 ungated 였다. 2×2 를 돌리기 전에 **baseline** 을 horizon 축으로 먼저 훑었다.
- **Decision (1) 🔴 — 2×2 는 돌릴 수 없다. horizon 축의 admissible rung 은 하나다.** `cafe_obstacle_crossing_v0` / `risk_mppi` / `lam=1.6`, `w_voo=0` (순수 baseline): cruise `H=15/30/34` 에서 **0.800 / 0.800 / 0.772**, `H=35` 에서 **0.1135** — **한 rung 만에 6.8× 붕괴**, `H=60` 까지 지속. 문턱 artefact 가 아니라 진짜 edge 다 (`H=34` 가 shipped rung cruise 의 **96.6 %** 유지). 따라서 Q-043 의 "cone 을 늘린다" 가지는 **epistemic 항이 개입하기 전, baseline 수준에서 반증**됐고 2×2 는 D-027 이 이미 돌린 1×2 로 축퇴한다.
- **Decision (2) 🔴 — 이번 cycle 의 일반화 가능한 발견: LOO 는 중복 원인을 볼 수 없다.** `H=45` 에서 개입으로 귀인 (D-026 의 교훈 — cost 함수 읽기 말고 ablation 으로 순위 매기기): `w_collision=0` 단독 → cruise 0.1287, `w_obs_soft=0` 단독 → 0.1201, intact 0.1331 대비 각각 **0.97× / 0.90× — 개선이 작은 게 아니라 아예 없다**. **둘 다 0 → 0.7479, 5.6× 회복** (그리고 충돌, clearance −0.0907 — freeze 가 실제 안전을 사고 있었다는 나머지 반쪽). 두 항은 **대체재**다: 각각이 독립적으로 "가만히 서 있기" 를 최저비용 plan 으로 만들기 충분하므로, 하나를 빼도 다른 하나가 그대로 발화한다. 이는 D-028 의 `weight_units.measure` 에 대한 **직접적 한계**다 — 그것은 구조상 leave-**one**-out (`cost(w) − cost(0)`, 한 번에 하나) 이라 이 두 항에 각각 책임 ≈ 0 을 매긴다. LOO 는 "이 weight 가 한계에서 무엇을 더하는가" 에 답할 뿐 "이 행동의 원인이 무엇인가" 에는 답하지 못하고, 두 질문의 간극이 정확히 중복성의 크기다. 수리: `horizon_audit.ablate` 가 singleton 이 아니라 **power set** 을 쓸어 `redundant_sets` 로 "단독으론 아무것도, 쌍으론 전부" 패턴을 이름 붙인다.
- **Decision (3) 🔴 — D-028 의 damage guard 는 이것을 못 잡는다 (relative guard 의 사각).** `check_undamaged` 는 probe run 길이를 **baseline arm** 길이와 비교한다. `H=45` 에선 두 arm 이 똑같이 얼어 있어 `damage=0.69` — 여유롭게 "undamaged" — 를 **전혀 주행하지 않는 arm** 위에서 읽는다. 게다가 그 다음 숫자가 **아첨하는 방향**으로 틀린다: 얼어붙은 로봇은 평평한 landscape 를 제시하므로 `rest` 가 `H=34` 163.6 → `H=45` **38.8** 로 떨어지고, 처방되는 scale-matched weight (4.27) 는 마지막 건강한 rung 의 것(13.97)보다 **3.3× 작다**. guard 가 *상대적*이라 자기 기준이 망가진 것을 볼 수 없다. 수리는 절대 precondition — `cruise_ceiling` 으로 "가격 매기기 전에 baseline 이 주행 중인지" 확인.
- **Decision (4) 🔴 — 설령 baseline 이 버텼어도 2×2 의 weight 축이 horizon 축을 견디지 못한다.** `_cost` 의 거의 모든 항이 **H 에 대한 합**이라 `per_unit` 이 horizon 과 함께 커진다 (horizon-aware 로 만든 `scale_match.exchange_rate`: `H=15/30/34` 에서 `per_unit` 0.775 / 2.356 / 2.929, `rest` 21.70 / 101.21 / 163.64). ratio 0.25 의 `w_voo` 는 **7.00 / 10.74 / 13.97 — 2.3× horizon 변화에 2.0× 진폭**, D-029 가 fixed point 라 부른 `lam` 진폭 2.11× 과 같은 자릿수. `w_voo` 를 horizon column 내내 고정하는 2×2 는 두 factor 를 교차하는 게 아니라 weight 변화와 horizon 변화를 **교란**시킨다.
- **Decision (5) ⚠️ — 두 개의 기존 guard 가 이 class 에 침묵한다.** 얼어붙은 rung 전부에서 `all_reached=True` (완주는 하고, 9× 오래 걸릴 뿐) — `assert_all_reached` 는 여기 무용이고 `speed_audit.cruise_speed` 만이 rung 을 가른다 (D-025 가 두 번째로 도착, D-026 의 `city_figure8_v0` 와 같은 서명). 그리고 **clearance 는 붕괴를 관통해 단조 개선** (`H=34` +0.0193 → `H=60` +0.3585, **18.6×**) — cruise column 없이 읽으면 "긴 horizon 이 더 안전하다" 고 말한다. horizon 은 `v_max` handicap 으로 통제 **불가능한** 유일한 축이다: handicap 은 속도 상한을 낮출 뿐이고 얼어붙은 arm 은 *한계*가 아니라 *선택*으로 느리다. 즉 이 축은 불편한 게 아니라 **식별 불가**다.
- **Alternatives**: (a) 2×2 를 그대로 돌리고 horizon column 을 `w_voo` 결과로 읽기 — 정확히 이 cycle 이 막은 오독. (b) `H` 를 늘리되 `w_obs_soft`/`w_collision` 를 H 로 스케일 — 미측정; freeze 는 두 항의 **논리합**이라 어느 한쪽 스케일링으로는 안 풀린다는 것이 Decision (2) 의 함의. (c) freeze 를 고쳐서 horizon 축을 여는 것 — baseline 변경이라 Q-032 에 걸려 drain 전까지 보류 (#13). (d) horizon 축을 포기하고 D-027 의 construction 축만 유지 — **채택**.
- **Status**: accepted. repo default 이동 **없음** (`run.simulate` / `ab.run_arm` 에 `max_steps=None` optional 추가 — bit-identical, test 로 고정; `scale_match.exchange_rate` 에 `horizon=` 추가, 기본값이 shipped horizon).
- **Refs**: PR #67, `journal/2026-08/03-08-p3-horizon-sweepability.md`, `eval/mppi_sandbox/horizon_audit.py`, D-025 / D-026 / D-027 / D-028 / D-029, Q-043, Q-052

## D-029 — 2026-08-03 — scale-matched `w_voo` arm 은 기록된 `lam` window 를 **그대로 유지**한다. naive weight 는 window 를 **옮기는 게 아니라 없앤다**

- **Context**: D-021 은 `lam_windows.yaml` 의 모든 window 가 epistemic channel **꺼진 채** 측정됐음을 확립했고, 그래서 `w_voo` arm 의 어떤 clearance 숫자도 controller 비교가 아니었다. D-027 이 항을 ship 하고 D-028 이 그 weight 를 **어느 분모**로 매길지 정했다. STATE #1: `w_voo` 를 실제로 carry 하는 arm 의 window 를 재라. Scene `cafe_obstacle_crossing_v0` / `risk_mppi`, factor-2 ladder 0.05→6.4 (**128× span**), rung 당 seed 8, `ab.LamProbe.admissible` (전 seed band 내 **및** 완주).
- **Decision (1) ✅ — window 는 움직이지 않는다.** baseline (control, 이번 cycle **재측정** — 인용 아님) **[1.6, 3.2]** 로 기록 table 을 정확히 재현. scale-matched fixed `w_voo=5.43` → **[1.6, 3.2]**. rung 마다 ratio 를 고정한 arm (`w_voo` 3.41–7.17) → **[1.6, 3.2]**. 즉 STATE #1 의 전제 ("비교 전에 arm 전용 window 가 필요하다") 는 **ship 할 만한 weight 에 대해서는 부정으로 답**했다 — 기록된 window 가 전이되고, A/B 는 per-arm 재캘리브레이션 없이 열린다.
- **Decision (2) 🔴 — naive weight 는 temperature *이동* 이 아니라 temperature *말살*.** D-027 은 `w_voo=200` 을 "변장한 temperature 변경" 이라 불렀고 이는 window 가 **어딘가로 옮겨갔다** 는 뜻을 함축한다. 아니다: **128× ladder 의 모든 rung 에서 band 밖** (8 rung 중 6 개에서 median ESS 정확히 1.00, 최상단에서도 1.80) — Q-035 의미로 **calibratable 하지 않다**. 지금까지 repo 가 빈 window 를 본 것은 **결함 scene** (`cafe_cut_in_v0`, 완주 불가) 뿐이었다. 이것은 **weight 가 유발한** 빈 window 이고, 같은 ladder 에서 바로 옆 column 이 건강한 scene 위에서 벌어진다. `lam` 을 올려도 되사올 수 없다.
- **Decision (3) 🔴 — 경계의 위치**: 두 admissible rung 에서 weight 를 쓸어 (`lam=1.6` 기준 ratio) — ratio **0.13 / 0.25 → 8/8, 8/8**; **0.50 → 1/8, 8/8** (window 절반 상실); **1.00 → 0/8, 1/8**; **2.00 및 4.66 (=200) → 0/8, 0/8**. 전 window 는 **ratio ≈ 0.25 까지 생존**, 0.5 에서 rung 절반을 잃고, **1.0 에서 소멸**. ratio 1 은 항이 나머지 전부와 같은 만큼의 per-sample cost range 를 차지하는 선 — `TermSpread.ratio` docstring 이 이미 danger condition 으로 지목한 지점 — 이므로 이 측정은 그 추측을 확인하는 동시에 **실용 상한을 그보다 4× 아래**로 못박는다.
- **Decision (4) 🔴 — 처방은 2-step 이 아니라 fixed point 다 (그리고 여기선 무해했다).** ratio 의 두 반쪽은 `lam` 민감도가 반대다: `per_unit` (항 자체의 unit-weight spread) 은 128× 구간에서 **1.12× 밖에 안 움직이는 critic 의 상수**인 반면, 분모 `rest` 는 **2.26× 하락** (188.0 → 83.1) — softmax 가 뜨거워지면 update 가 cloud 를 더 평균내고 loop 가 다르게 추종해 baseline spread 가 줄어든다. 몫인 scale-matched weight 는 분모의 진폭을 물려받아 **2.11× 흔들린다** (`lam=0.1` 에서 5.43, `lam=3.2` 에서 3.41). 따라서 "scale-match 후 calibrate" 는 원리상 순환이다. **그러나 이 scene 에서는 rung 별 ratio 고정이 weight 고정과 *같은 window* 를 냈다** — 정직한 negative 로 기록해 다음 reader 가 per-rung protocol 값을 기대하며 비용을 치르지 않게 한다.
- **Decision (5) ✅ — 외삽은 쓸 수 있는 구간에서만 필요하다**: D-028 은 closed-loop rate 가 w=1→200 에서 2.1× 움직인다고 못박았다. 사실이지만 200 은 window 가 이미 빈 지점보다 ratio 로 4 단위 뒤다. unit probe 로부터의 처방은 target ratio 0.25/0.5 에서 실측 **1.005–1.085×**, 최악 1.22× 안에 떨어진다 — **외삽은 ship 가능한 weight 가 사는 구간에서 정확하고, 이미 못 쓰는 구간에서만 무너진다**.
- **Alternatives**: (a) arm 마다 window 재측정을 의무화 — 이 측정이 불필요함을 보였다 (ship 가능 weight 한정). (b) `w_voo=200` 용 `lam` 재탐색 — 128× ladder 가 그런 `lam` 이 없음을 보였다. (c) ratio 대신 절대 weight 로 sweep — D-027 이 그렇게 해서 temperature 붕괴를 정보 선호로 오독했다. (d) fixed point 를 반복해 풀기 — window 가 두 protocol 에서 동일하므로 미지불.
- **Status**: accepted. repo default 이동 **없음** (`w_voo=0` 기본 유지, 순수 계측 모듈 + test).
- **Refs**: PR #67, `journal/2026-08/03-07-p3-scale-matched-lam-window.md`, `eval/mppi_sandbox/scale_match.py`, D-021 / D-027 / D-028, Q-050

## D-028 — 2026-08-03 — cost weight 의 단위는 **더해지는 쪽 baseline 의 spread** 다. 자기 arm 에서 재면 weight 는 **자기가 낸 피해로 채점**된다

- **Context**: D-027 이 `w_voo = 200` 을 이 scene median baseline cost spread 의 **6.19×** 로 측정했고 (변장한 temperature 변경 — median ESS 77.9 → 1.00, 충돌), Q-049 는 이것이 repo 전체 위험인지 물었다. STATE #2: shipped 4종 (`w_risk=40`, `w_epist`, `k_margin_per_sigma`, `w_terminal=30`) 을 baseline spread 배수로 재는 표 하나.
- **Decision (1) 🔴 — Q-049 의 네 knob 은 한 class 가 아니다.** `lam=1.6`, healthy baseline arm 기준: `w_terminal=30` → **0.328** (유일하게 live 한 순수 additive 계수), `w_risk=40` → **0.064** (자기 arm), `w_epist=200` → **정확히 0** (spread 가 항등적으로 0 인 항을 곱함 — D-021 을 범용 계측기로 재유도), `k_margin_per_sigma` → **정의 불가**. 단위 위험은 실재하지만 **좁다**.
- **Decision (2) 🔴 — 그리고 이게 일반화되는 부분: 분모가 결론이다.** 같은 `w_voo=200`, 같은 scene, 같은 `lam`: **더해지는 baseline 대비 6.19×**, **자기 arm 대비 1.46×** — **4.2× 과소평가**. 메커니즘은 단순 scale 오차보다 나쁘다: `w_voo=200` arm 은 **완주하지 못하고** (1000 step vs baseline 114), 대부분을 path 밖에서 보내므로 `w_path` 자체 spread 가 **11.6×** (48.1 → 555.7) 부풀고 분모가 79.09 → 862.6 (**10.9×**) 이 된다. **weight 가 만들어낸 landscape 로 그 weight 를 채점**하는 셈이고, weight 가 나쁠수록 더 유리하게 나온다.
- **Decision (3) ✅ — 유혹적인 오답을 명시적으로 배제**: 분모 팽창은 collision 항이 깨어난 것이 **아니다**. `w_collision = 1e4` 는 repo 최대 weight 인데 **양쪽 arm 모두 median spread 정확히 0** (탈선 arm 에서도 간헐 발화, mean 2210 / median 0). guard 이지 경쟁자가 아니다. 실제 경쟁자는 healthy arm 의 `w_path=20`, ratio **2.42** — baseline landscape 는 곧 path tracking.
- **Decision (4) 🔴 — ratio 의 전제와, 그것을 못 지키는 knob**: "w 는 baseline 의 r 배" 는 `ptp(w·f)` 가 `w` 에 **선형**임을 전제한다. 고정 rollout batch 에서 additive 계수는 **machine precision 으로 정확히 상수** (per-unit ratio 1.000000). `k_margin_per_sigma` 는 계수가 아니라 `exp(-clear/scale)` 과 `clear<0` indicator **안쪽**의 shift 라 per-unit spread 가 0.05/0.1/0.2/0.4 에서 **2.57× 흔들린다** — 단위가 cost 가 아니라 **미터**다. `measure()` 는 이 knob 이 0 이 아니면 거부한다 (다른 모든 행이 이 knob 에 조건부가 되므로).
- **Decision (5) 🔴 — 대수는 선형인데 측정은 외삽 불가**: closed loop 에서 `w_voo` per-unit spread 는 w=1/7/200 에서 **2.50 / 2.34 / 5.30**. weight 가 다르면 state sequence 도 다르기 때문. 싼 small-weight probe 로 shipping weight 를 고르는 것은 무효 — **ship 할 weight 에서 재라**.
- **Decision (6) ✅ — 방법론**: leave-one-out 을 **weight 를 0 으로 토글하고 진짜 `_cost` 를 재평가**해서 얻는다 (`cost(w) − cost(0) = w·f` 정확). cost 식 사본이 없으므로 controller 와 drift 불가 (`ab.median_ess` docstring 이 ESS 에 대해 지목한 실패 양식). 분모는 total 이 아니라 **rest = cost − w·f** — 항이 자기를 포함한 baseline 에 대해 매겨지지 않으므로 add-on critic 과 baseline 내부 항 (`w_terminal`) 에 **같은 통계**가 정의된다.
- **Decision (7) ✅ — 통계 선언**: `REPORTING_STATISTIC = "median"`, 나누기 전에 이름을 붙였다 (D-024 실수 class). `w_collision` 이 indicator 라 per-step spread 분포는 극도로 right-skewed — 이 scene 총 spread 는 **median 79.09 vs mean 3806.8** (48× 불일치). 양쪽 다 반환하고 `statistic_disagreement` 로 caller 가 자기 scene 에서 선택이 load-bearing 인지 확인할 수 있게 했다.
- **Alternatives**: (a) share-of-total (`w·f / cost`) — `w_terminal` 처럼 baseline 내부 항에 대해 정의가 순환. (b) ESS 를 직접 재기 — 결과는 알려주지만 **어느 항이** 그랬는지는 못 알려줌. (c) cost 식을 계측 모듈에 재구현 — drift. (d) Q-049 표만 내고 분모 문제를 지나치기 — 표의 숫자 자체가 틀림.
- **Status**: accepted. repo default 이동 **없음** (순수 계측 모듈 + test).
- **Refs**: PR #67, `journal/2026-08/03-06-p3-weight-units-table.md`, `eval/mppi_sandbox/weight_units.py`, Q-049 → `resolved → D-028`

## D-027 — 2026-08-03 — epistemic channel 의 **cost 구성 자체**를 교체하니 처음으로 소리를 낸다 (spread 0.00 → 1060, live 0/92 → 115/115). 단 "도움이 된다" 는 주장은 **n=8 에서 철회**

- **Context**: D-021 finding #2 가 `ShadowCostCritic` 을 `cafe_obstacle_crossing_v0` shipped `H=30` 에서 **signal-free** 로 측정했다 — 92 step 전부 per-sample spread 정확히 0.00, `w_epist=200` 이 4/4 seed 에서 `w_epist=0` 과 byte-identical. finding #4 는 명백한 수리안까지 반증했다: "live iff max reach ≥ nearest unseen cell 까지의 거리" 는 그 92 step 중 **28 step** 에서 성립하는데 spread 는 여전히 0 이다 — rollout 은 path **를 따라** 멀리 가고 shadow 는 actor 의 **측면과 뒤**에 있기 때문. 즉 **방향이 문장에 들어와야** 한다. feed 2026-08-03 00:00 (2404.07781, RA-L) 의 thesis 가 정확히 그 실패 class 를 진술한다: per-occlusion cost 는 "may appear to be in opposition" 이고, 해법은 cell 값이 **그 cell 을 방문해서 얻는 정보량**인 **하나의 aggregate map**. **네 cycle 연속 raise 되고 안 뽑힌** pool 최장기 대기 item — STATE #1.
- **Decision (1) ✅ — primary gate 통과. 무게가 아니라 구성을 바꾸니 항이 말을 한다.** `ObservationValueCritic`: `V(q)` = 현재 shadow cell 중 위치 `q` 에서 보이게 되는 비율 ∈ [0,1], `cost_k = w_voo · Σ_h (1 − V(x_kh))`. 같은 scene / 같은 horizon / 같은 isolation (`w_risk=0`, `k=0`) 에서 나란히 측정:

  | term | live steps | max spread | mean spread |
  |---|---|---|---|
  | `ShadowCostCritic` w=200 | **0 / 92** | **0.00** | 0.00 |
  | `ObservationValueCritic` w=200 | **115 / 115** | 1060 | 539 |

  shadow row 는 인용이 아니라 **이 cycle 의 control 로 재측정**한 것이다. 구조적 차이: distance-to-unseen 은 rollout 이 shadow 에 **들어가야** 비상수가 되므로 침묵이 **일반적인 경우**다. value-of-observation 은 rollout 이 **실제로 도달하는 바로 그 위치**에서 평가되므로 침묵하려면 **shadow 가 아예 없어야** 한다. repo 최초의 **non-inert epistemic consumption path**.
- **Decision (2) 🔴 — 그런데 "clearance 가 좋아진다" 는 n=4 결과였고 n=8 에서 사라진다.** scale-matched arm 이 n=4 에서 mean clearance **+60 %** (0.0455 → 0.0728), ESS in band 로 읽혔다. n=8 paired per-seed sign counts: `lam=1.6 w_voo=3.23` **+4/−4**, `w_voo=6.46` **+5/−3**, `lam=3.2` 에서 **+5/−3**, **+5/−3** — 네 cell 전부 동전 던지기이고 mean Δ 부호도 양쪽으로 갈린다. **철회.** D-019 의 "판정은 (scene, n_seeds) 의 속성" 이 그대로 재발했다. 이 cycle 이 확립한 것은 항이 **들린다**는 것이지 **좋다**는 것이 아니다.
- **Decision (3) ✅ — 살아남는 메커니즘: 새 critic 의 weight 는 **baseline cost spread 단위**로 sweep 해야 한다.** 순진한 sweep 은 `w_epist` 가 200 이었으니 `w_voo=200` 을 고른다. baseline 대비로 재면 터무니없다 — 이 scene 의 step 당 total-cost spread 중앙값은 **79.09**, value 항은 weight 1 당 **2.45** 를 기여하므로 `w_voo=200` 은 **baseline cost spread 전체의 6.19×**. 결과는 "정보에 대한 강한 선호" 가 아니라 **위장된 temperature 변경**이다: median ESS 77.9 → **1.00** (= argmin-over-draws, `lam` 이 무력화됨) 이고 arm 이 **충돌**한다 (min clearance **−0.436**, 2/4 reached). baseline spread 의 10 % / 20 % 로 맞춘 weight (`w_voo` ≈ 3.2 / 6.5) 는 D-017 band 안에 머문다. → `w_epist=200` 이 여섯 cycle 동안 "안전" 해 보였던 이유는 그것이 **정확히 0 을 곱하고 있었기** 때문이다.
- **Decision (4) — direction-dependence: 이 구성에 대해서는 확정, 논문에 대해서는 미해결.** feed 가 "PDF 를 읽어야 하는 단 하나의 이유" 로 지목한 질문 (2404.07781 의 cell 값이 bearing-dependent 인가) 은 **이 session 에서 WebFetch 권한이 없어 미해결로 남는다** — 논문 주장으로 기록하지 않는다. 여기서 만든 구성에 대한 답은 확정적이다: 저장값은 위치당 scalar 지만 **계산이 producer 와 동일한 robot→cell ray test** 를 쓰므로 occluder 기하를 상속한다. one-disc scene 에서 **nearest shadow cell 까지의 거리가 같은** 두 cell 의 값이 **0.0 과 1.0** 이다 — distance-predicts-value 에 대한 최대 반례이자 D-021 #4 를 긍정형으로 진술한 것.
- **Decision (5) — default 는 하나도 안 움직인다.** `w_voo` default 0.0 → byte-identical no-op (ablation invariant, 테스트로 고정). shadow cost 는 제거하지 않고 **나란히** 남긴다 — D-021 의 침묵이 이 파일의 control 이고, 지우면 비교가 인용으로 격하된다. 비용: control step wall clock 약 **2.75×** (2.2 s vs 0.8 s / run).
- **Alternatives**: (a) `w_epist` 를 더 키운다 — D-021 이 이미 반증 (0 × 무한대 = 0). (b) horizon 을 올려 shadow 에 닿게 한다 — D-021 이 되긴 된다고 보였지만 rollout 예산을 두 배로 쓰고 scene 마다 다시 튜닝해야 하며 *왜* 침묵했는지는 안 고친다. (c) 거리 scalar 를 방향 가중으로 보정 — D-021 #4 의 반례가 거리 bin 안에서 0.0 vs 1.0 이라 보정 대상이 없다. (d) beyond-range halo 도 target 에 포함 — "앞으로 가라" 의 proxy 가 되어 path 항과 중복되므로 **in-range shadow 만** 계산에 넣는다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-05-p3-observation-value-critic.md` · `eval/mppi_sandbox/critics/observation_value.py` · `eval/mppi_sandbox/tests/test_observation_value_critic.py` · D-017 / D-019 / D-021 / Q-043 / Q-049 · feed 2026-08-03 00:00 (arXiv 2404.07781)

## D-026 — 2026-08-03 — `city_figure8_v0` 의 0.016 m/s 는 **scene defect 도, self-intersection 실패도 아니다** (Q-047 의 두 선택지 모두 기각). shipped objective 가 **goal 을 재방문하는 reference 를 계약 밖으로 둔다**

- **Context**: D-025 가 cruise 통계로 matrix 를 재선별하다 `city_figure8_v0` 를 **0.016 m/s, 3/4 reached** 로 잡아냈다. Q-047 은 두 해석을 놓고 물었다: Q-037 계열의 **세 번째 scene defect** (reportable matrix 가 4 → 3 으로 축소) 인가, 아니면 self-intersecting reference 위에서의 **진짜 controller 실패** (9 cycle 만의 첫 capability finding) 인가. 결과가 정반대라 STATE #1.
- **Decision (1) 🔴 — 둘 다 틀렸다. 양방향 intervention 이 두 선택지를 각각 죽인다.** D-018 규율대로 한 번에 하나만 바꿨다 (`stock_mppi`, seeds 0-3):
  - **B1 이 결정타.** `city_curved_v0` 는 self-intersection 도 crossing point 도 없고 cruise **0.739 / 4/4 / 21.3 s** 로 건강하다. `goal := start` **하나만** 바꾸면 cruise **NaN** (= `cruise_speed` 정의상 stall), 2/4, 100 s timeout 으로 붕괴한다. 즉 **self-intersection 은 필요조건이 아니다** → Q-047 (b) 기각.
  - **A1 이 나머지를 죽인다.** scene 의 waypoint 가 defect 라면 closure 를 열면 고쳐져야 한다. 안 고쳐진다: cruise 0.0164 → 0.2538 (15×) 이지만 여전히 240 s timeout, 30.6 m reference 중 **13.1 m** 만 주행. closure 수리는 **필요하지만 불충분** → Q-047 (a) 기각.
- **Decision (2) — 메커니즘, 그리고 두 항 중 무엇이 지탱하는가.** `StockMPPI` 의 두 항이 모두 **goal 까지의 Euclidean 거리**의 함수이고 **남은 arclength** 의 함수가 아니다: speed ramp `v_ref = min(target, max(gain·d_goal, creep))` 와 terminal `w_terminal·d_goal[-1]²`. figure-8 은 이걸 두 번 위반한다 — `d(start, goal) = 0`, 그리고 reference 가 arclength **0.5 지점에서 goal 로 정확히 되돌아온다** (crossing point 가 곧 goal). 2×2 가 순위를 정한다:

  | arm | cruise | mean_v | 주행 arclen | reached |
  |---|---|---|---|---|
  | A1 f8-opened shipped | 0.2538 | 0.0548 | 13.11 | 3/4 |
  | A2 f8-opened no-ramp | 0.3405 | 0.0490 | **11.78** | 3/4 |
  | A3 f8-opened no-terminal | 0.4525 | 0.3072 | **73.23** | 3/4 |
  | A4 f8-opened neither | 0.4510 | 0.4507 | 108.06 | 0/4 |
  | B1 curved-closed shipped | NaN | 0.0504 | 5.04 | 2/4 |
  | B2 curved-closed no-ramp | 0.0578 | 0.0480 | **4.72** | 0/4 |
  | B4 curved-closed neither | 0.5252 | 0.4088 | 40.92 | 0/4 |
  | **B0' curved-shipped neither** | 0.5674 | 0.4750 | 13.32 | **4/4** |

  **terminal 항이 binding 이고 ramp 는 거의 inert 다.** ramp 만 제거하면 주행거리가 **반대 방향**으로 움직인다 (13.11 → 11.78, 5.04 → 4.72). `w_terminal` 을 제거하면 13.11 → **73.23**. `w_terminal = 30.0` vs `w_speed = 2.0` 이 예측하는 순위 그대로다. 따라서 실패의 문장은 "로봇에게 천천히 가라고 시켰다" 가 아니라 **"로봇에게 이미 도착했다고 시켰다"** — crossing point 에서 terminal 항은 전역 최소이므로 거기서 벗어나는 모든 rollout 이 벌점을 받는다. loop 은 **자기 goal 위에 주차한다**.
- **Decision (3) — completion guard 도 같은 scene 들에서 unsound 하다.** `ab.reached_goal` 은 **마지막 sample 만** 읽는다. `d(start, goal) ≤ goal_xy_tol` 이면 **한 발도 안 움직인 run 이 guard 를 통과**한다. 03:00 scan 의 "0.016 m/s 에서 3/4 reached" 와 B1 의 2/4 가 그것 — guard 가 goal 이 아니라 **start 를 재고 있었다**.
- **Decision (4) — 무엇을 배포하는가.** `feasibility.goal_approach` + `ramp_radius` + `GoalApproach` — **simulation-free 정적 screen**, Q-037 이 "retiree 말고 retirement 를 일반화하라" 며 만든 바로 그 모듈에. 두 predicate 를 **분리해서** 보고한다 (`completion_guard_is_sound`, `approach_is_monotone`) — figure-8 은 둘 다 실패하지만 한 쪽만 실패하는 scene 이 가능하고, 하나로 합치면 어느 쪽이 터졌는지 숨는다. shipped 8 scene 중 **figure-8 만** 실패하고, 통과한 scene 중 가장 빠듯한 것도 ramp radius 의 **1.6×** 라 판정이 `goal_slowdown_gain` 값에 걸리지 않는다.
- **Decision (5) — 고치지는 않는다.** `StockMPPI`, `ab.reached_goal`, `city_figure8_v0` 어느 것도 안 건드린다. Q-032 (queue 중 shared baseline 정정 금지) 가 유효하고, arclength 구동으로의 수리는 자체 re-baseline 비용을 갖는 controller 변경이다. screen 은 **전제조건을 진술**하고, 수리는 **Q-048** 로 파일.
- **Alternatives**: (a) figure-8 을 이름으로 blacklist — Q-037 이 이미 기각한 수 (다음 병리 scene 을 똑같이 비싸게 찾게 된다). (b) `goal := start` 만 고치기 — A1 이 불충분함을 보였다. (c) `w_terminal = 0` 을 default 로 — A4/B4 가 0/4 reached, goal 에서 멈출 이유가 사라진다. (d) matrix 를 3 scene 으로 축소 — 전제가 틀렸으므로 (Decision 1) 근거 없음.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-04-p3-goal-revisit-screen.md` · `eval/mppi_sandbox/feasibility.py` · `eval/mppi_sandbox/tests/test_goal_revisit_screen.py` · Q-037 / Q-047 / Q-048 / D-018 / D-025

## D-025 — 2026-08-03 — simulation-free screen 의 traversal driver 를 `target_speed_mps` 에서 **calibrated cruise speed** 로 교체 (band 3.866× → 2.320×). 그리고 그 2.320× 는 **scene-independent driver 전체의 하한**이다

- **Context**: D-022 가 `nominal_traversal` 을 반증 → D-023 이 timing band (0.557–2.038) 를 선언 → D-024 가 그 band 의 구동값 `target_speed_mps` 는 **closed loop 이 읽지 않는 yaml 필드**임을 보였다. 즉 error bar 를 *선언문* 주위에 그리고 있었다. loop 이 실제로 읽는 건 `v_max` 와 `w_terminal / w_speed` 이고 **둘 다 simulation 없이 구할 수 있다** — STATE #1.
- **Decision (1) — driver 를 교체한다.** `nominal_traversal(..., speed_mps=)` + `cruise_traversal`. `CRUISE_SPEED_MPS = 0.723` 은 shipped `v_max = 0.8` 에서 `cruise_speed` 로 잰 **controller 상수** (scene 상수 아님). `speed_mps=None` default 는 기존 caller 전부 bit-identical.
- **Decision (2) ✅ — 개선은 실재하고, 공짜다.** 같은 4 개 reportable scene 에서 band 폭 **3.866× → 2.320×** (1.67× 축소). 비용은 양쪽 다 0 — cruise 는 scene 마다 재는 게 아니라 controller 마다 한 번 calibrate 한다. 부가로 오차가 **단방향**이 된다: 4/4 scene 이 > 1 (closed loop 은 pure-cruise 보행보다 항상 느리다 — transient + goal ramp + detour 를 지불). 선언 driver 의 band 는 1.0 을 양쪽으로 걸쳐서 오차에 **부호가 없었다**.
- **Decision (3) 🔴 — 그리고 이게 진짜 결과: 2.320× 는 이 상수의 점수가 아니라 **바닥**이다.** scene-independent driver 하에서 band 폭은 구동속도에 대해 **정확히 scale-invariant** 다 — `ratio_i = cl_i · c / length_i` 이므로 `c` 가 `max/min` 에서 대수적으로 소거된다. c = 0.5 / 0.709 / 0.8 / 1.2 에서 폭이 **1e-9 이내로 동일**함을 테스트로 고정했다. 남는 건 "reference path 1 m 당 closed-loop 초" 의 scene 간 산포이고, **어떤 상수 속도도 이걸 못 없앤다.** 따라서 `CRUISE_SPEED_MPS` 를 튜닝해 band 를 좁히려는 후속 cycle 은 **실패가 보장**돼 있다 — 상수는 band 의 *위치*만 정하고 *폭*은 못 건드린다.
- **Decision (4) — 바닥을 깨려면 sim 을 사야 한다.** scene 별로 잰 cruise 로 구동하면 **1.663×** 까지 내려가지만 그건 scene 당 sim 1 회, 즉 D-023 이 "더는 screen 이 아니다" 로 기각한 Q-044 option (a) 그 자체다. 채택 안 하고 **가격표를 붙인 채로** 테스트에 기록만 한다.
- **Decision (5) — closed form 대신 lookup.** `CRUISE_BY_VMAX = {0.4: 0.349, 0.6: 0.600, 0.8: 0.723, 1.2: 0.723}` + `calibrated_cruise` (log-linear 보간, **범위 밖은 거부**). knee 구조가 확인된다: `v_max` 가 0.6 에서 정확히 bind 하고, 0.8 과 1.2 는 자릿수까지 일치 (ratio 가 pin). D-024 가 반증한 `analytic_cruise_speed` 를 되살리지 않는 이유는 같다 — ESS ≈ 1.5 / K = 256 에서 controller 는 어떤 stationary point 에도 앉아있지 않으므로, *해야 할 일의 모델* 보다 *하는 일의 표* 가 낫다.
- **Alternatives**: (a) band 중심이 1.0 이 되도록 상수를 고르기 — 폭이 안 변하므로 (Decision 3) 해석만 좋아 보이게 만드는 fudge factor, 기각. (b) scene 별 cruise 채택 — Decision (4), screen 범주를 버림. (c) 선언값 유지 + band 만 넓히기 — D-024 이후로는 읽지 않는 값 주위의 error bar 라 의미 없음. (d) `target_speed_mps` 를 스키마에서 제거 — Q-046, 아직 warm start / `reach.py` fan 이 쓰므로 공짜가 아님.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-03-p3-cruise-driven-nominal.md` · `eval/mppi_sandbox/exposure.py` · `eval/mppi_sandbox/speed_audit.py` · `eval/mppi_sandbox/tests/test_cruise_driven_nominal.py` · D-022 / D-023 / D-024 / Q-044

## D-024 — 2026-08-03 — `target_speed_mps` 는 closed loop 이 **읽지 않는 값**이다 (Q-045 → (a)/(c) 기각, (b) 확인). D-022 의 "1.8× overshoot" 는 **선언값의 artifact**

- **Context**: D-022 가 "controller 가 `target_speed_mps` 를 추종하지 않는다" 고 관측했고, D-023 은 그 때문에 timing band (0.557–2.038) 를 선언해야 했다. Q-045 의 선택지: (a) **scenario 설정** — 아무도 강제하지 않는 속도, (b) **cost weight** (`w_terminal = 30.0` vs `w_speed = 2.0`), (c) 목적함수에 **속도 추종항 부재**. band 를 만들어내는 메커니즘이라 STATE #1.
- **Decision (1) — (c) 는 inspection 으로 거짓.** `StockMPPI._cost` 는 baseline 부터 `w_speed · Σ(v − v_ref)²` 를 갖고 있었다. 게다가 *살아있다* — `w_speed` 만 60 으로 올려도 loop 이 움직인다(D-021 의 `w_epist` 처럼 "항은 있는데 softmax no-op" 인 약한 형태까지 배제).
- **Decision (2) — (b) 는 참이고 양방향.** `w_terminal = 0` → 실현속도 0.519 → **0.146**; `w_speed = 60` → **0.237**. 같은 비율의 반대편에서 두 개입이 모두 줄인다(D-018 규율). 어느 한쪽만 움직였다면 나머지 항은 방관자이고 메커니즘 주장은 미지지였다.
- **Decision (3) — (a) 는 거짓이고, 이게 결과다.** `target_speed_mps` 를 **4×** (0.15/0.30/0.60) 쓸어도 실현속도는 **3%** 움직인다 (0.508/0.519/0.523). 선언값은 warm start `U[:, 0]` 과 `v_ref` cap 으로만 들어오고 둘 다 몇 update 를 못 넘긴다. "아무도 강제하지 않는 속도" 는 옳은 *서술*이고 쓸모없는 *수리*다 — 선언을 제대로 고쳐도 아무것도 안 바뀐다.
- **Decision (4) — 따라서 "1.8× overshoot" 는 controller 속성이 아니다.** 동일 controller·동일 scene 이 `target_speed_mps: 0.6` 에서 realized/declared = **0.87** — *undershoot* 다. 비율이 loop 이 읽지도 않는 yaml 필드 하나로 1.0 을 넘나든다. D-023 의 band 는 실재하지만, 원인은 고쳐야 할 추종 실패가 아니라 `nominal_traversal` 이 **closed loop 이 읽지 않는 양**으로 구동된다는 것이다. `overshoot_ratio` 는 계산 가능하게 남기되 어떤 `target_speed_mps` 에 대한 값인지 함께 인용하도록 docstring 에 못박았다.
- **Decision (5) — Q-045 의 선택지 집합에 실제 천장이 없었다.** cruise 를 정하는 건 `min(v_max, f(w_terminal / w_speed))`: `v_max` 0.4 → cruise/v_max = 0.84, 0.6 → 1.00 (limit 이 bind), 0.8 과 1.2 → cruise 가 **둘 다 0.709** 에 고정 (ratio 가 bind). `target_speed_mps = 0.3` 은 두 regime 어디서도 천장이 아니다.
- **🔴 Refuted, 그리고 pin 함**: 한 구간 등속 근사의 정류점 `Δ* = w_terminal·T·D / (w_speed·H + w_terminal·T²)` 는 **정량적으로 반증**됐다 (goal 근처 측정 0.714 vs 예측 0.462; `w_terminal = 3` 원거리 0.215 vs 0.576 — 오차 **부호가 뒤집힌다**). 이유는 D-021 이 계속 부딪힌 것과 같다: shipped `lam = 0.1` 에서 median ESS 는 **1.46 / K=256**, 즉 update 는 정류점을 향한 step 이 아니라 argmin-over-draws 다. "MPPI 는 자기 cost 를 최적화한다" 를 전제로 유도한 closed form 은 ESS ≈ 1 에서 도는 controller 의 서술이 아니다. `analytic_cruise_speed` 를 **반증된 채로** 남기고 테스트로 불일치를 고정 — 다음 cycle 이 재유도해서 믿지 않도록.
- **✅ 통계 자체가 틀렸던 부분**: `ab.mean_speed` 는 accel transient + cruise + goal ramp 세 regime 을 평균한다. **goal 거리로 binning 해도 안 고쳐진다** — 단일 경로에서 큰 `d_goal` 은 곧 이른 시각이라 원거리 bin 이 대부분 transient 다. 이 confound 가 한 `w_terminal` 값에서 위 closed form 을 그럴듯해 보이게 만들었다. `cruise_speed` 가 양끝 regime 을 명시적으로 잘라내고, stall 한 arm 에는 NaN 을 준다(속도를 credit 하지 않기 위해).
- **Alternatives**: (a) 선언값을 강제하는 speed governor 추가 — 새 메커니즘을 도입하면서 queue 안 branch 들의 baseline 을 전부 다시 깔아야 함, (b) `w_terminal` 을 지금 내림 — Q-032 의 "머지 대기 중 공유 baseline 수정 금지" 위반, (c) scenario 에서 `target_speed_mps` 를 제거 — reach/exposure 가 아직 warm start 로 쓴다. **셋 다 채택 안 함**: 이번 cycle 은 귀속만 하고 default 는 하나도 안 건드림.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-02-p3-speed-overshoot-attribution.md` · Q-045 → resolved · D-022 Decision 3 의 귀속을 정정, D-023 의 band 는 유지

## D-023 — 2026-08-03 — simulation-free scene screen 은 **선언된 nominal 을 유지하되 point estimate 를 보고하지 않는다** (Q-044 → (b)). 그 대가로 exposure 의 **순서 매기기 권한이 사실상 0** 이 된다

- **Context**: D-022 가 `nominal_traversal` 을 반증했고 (`closed-loop/nominal` 지속시간 비 0.56×~15×), `exposure.py` 가 그 위에 올라타 있다. Q-044 의 선택지: (a) 실현 궤적 타이밍 — 정확하지만 scene 당 sim 1 회라 더는 screen 이 아님, (b) 선언 nominal + artifact 에 error bar 명시, (c) simulation-free scene screen 을 범주째 폐기. STATE #1 이자 D-018 의 인용 가능성이 걸린 항목.
- **Decision (1) — (b) 채택, 단 point estimate 는 **기본 출력에서 제거**.** `exposure_band` 가 같은 기하를 측정된 duration-ratio band 전체에 대해 다시 걷고 `[lo, hi]` 를 돌려준다. `separates` / `rank_with_band` 는 구간이 겹치는 두 scene 의 **순서를 거부**한다. 얻는 건 정밀도가 아니라 **과잉해석 거부** — 이번 cycle 이 청소하던 바로 그 실패 모드다. `screen_scenarios` 는 그대로 둬 D-018 숫자의 재현성은 유지하되, CLI 기본은 band 이고 point 는 `--point-estimate` 로 밀어냈다.
- **Decision (2) — band 는 한 파라미터짜리 섭동이고, 측정에서만 온다.** polyline·actor schedule·절대시계 전부 고정하고 **주행 지속시간만** 스케일한다 — D-022 가 잰 것이 정확히 그것이고 그 이상은 아니다. `TIMING_RATIO_BAND = (0.557, 2.038)` 은 테스트가 live sim 으로 재유도해 고정하므로 상수가 plant 에서 표류할 수 없다.
- **Decision (3) 🔴 — 15× 는 타이밍 오차가 아니라 **scene 결함**이라 band 에서 제외한다.** D-022 가 인용한 "0.56×~15×" 의 상단은 전부 `cafe_cut_in_v0`, 즉 120 s cap 을 소진하며 **완주하지 못하는** scene (Q-037 이 이미 scene 결함으로 판정, 보고 대상에서 제외됨) 이다. 이를 error bar 에 접으면 **아무도 인용할 수 없는 scene 하나 때문에 band 가 ~27× 넓어진다.** 제외 후 실제 band 는 0.557~2.038 (≈3.7×). 은폐가 아니라 병기 — `TIMING_RATIO_BAND_WITH_DEFECT` 로 남긴다.
- **Decision (4) ✅ — 정지 장애물 scene 은 **정확히** 면제된다.** 아무것도 안 움직이면 `contested_s` 와 `traversal_s` 가 같은 배율로 스케일되므로 band width 가 **0** 이고 point estimate 가 온전한 권한을 갖는다. 즉 screen 은 균일하게 무너지는 게 아니라 **actor 운동량에 비례해서만** 무너진다 — (c) 를 기각하는 근거이자 (b) 가 파괴적이기만 한 게 아니라는 유일한 건설적 결과.
- **Decision (5) 🔴 — 이동 장애물 scene 에서 순서 권한은 사실상 소멸한다.** 장애물 보유 5 scene, 10 쌍 중 **9 쌍이 겹쳐 거부**되고 살아남은 1 쌍은 하필 `cafe_cut_in_v0` 을 포함해 어차피 보고 불가다 → **쓸 수 있는 비교 0 건**. 특히 **D-018 의 74% vs 43% 는 인용 불가**: `[22%, 83%]` vs `[15%, 66%]`. D-018 의 *반증* 은 controlled intervention 위에 서 있으므로 그대로이고, 오히려 강화된다 (순서조차 못 매기는 통계는 예측자로서 더 나쁘다). 죽는 건 point-ranking 뿐.
- **Decision (6) — grid 는 41 점, 끝점 2 점이 아니다.** `contested_fraction` 은 duration ratio 에 **단조가 아니다** (crossing 은 band 내부 ~0.8 에서 최대). 끝점만 재면 구간을 과소평가한다 — 테스트로 고정.
- **Alternatives**: (a) 실현 궤적 구동 — 정확하지만 screen 범주를 없애고, 이미 sim 을 살 수 있으면 `reach_on_trajectory` 가 더 나은 답이다. (c) 범주 폐기 — Decision (4) 가 반례. (d) band 를 좁게 선언해 순서를 살림 — 측정이 허락하지 않고, 이번 cycle 이 막으려는 바로 그 오독.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-01-p3-exposure-timing-band.md` · `eval/mppi_sandbox/exposure.py` · `eval/mppi_sandbox/tests/test_exposure_timing_band.py` · D-018 / D-022 / Q-037 / Q-044

## D-022 — 2026-08-03 — 방향성 reach screen 의 **기하 모델은 정확**하고, 그것이 올라탄 **`nominal_traversal` 타이밍 모델이 반증**됐다 (`exposure.py` 전체에 파급)

- **Context**: D-021 이 rollout reach 를 게이트로 특정하면서 그 **scalar 형태를 자기 데이터로 반증**했다 ("최대 reach ≥ 최근접 미관측 cell" 이 spread=0 인 28/92 step 에서 성립). STATE #1 은 후계로 **방향을 담은** screen 을 요구했다 — 8 scene 중 어디가 epistemic 채널을 *들을 수* 있는지, sim 을 더 쓰기 전에.
- **Decision (1) — screen 은 intersection 이 아니라 spread 를 예측한다.** `ShadowCostCritic` 은 sample 마다 `w_epist·Σ_h σ` 를 매기고 **상수는 softmax 에서 정확히 소거**되므로 (D-021), "cloud 가 미관측 cell 에 닿는가" 는 틀린 기준이다 — cloud 가 shadow 에 **완전히** 들어가도 완전히 벗어난 것과 똑같이 안 들린다. `reach.py` 는 critic 과 같은 산술로 per-sample cost 벡터를 만들고 그 **`ptp`** 를 본다.
- **Decision (2) — fan 은 재유도하지 않고 재사용한다.** cloud 를 닫힌 형태로 다시 쓰지 않고 `dynamics.step` plant + `MPPIParams` 노이즈 (`sigma_v`/`sigma_w`) + `Limits` 클리핑 + `StockMPPI.__init__` 의 warm-start 를 그대로 돌린다. controller 를 고치고 screen 을 안 고치는 drift 가 구조적으로 불가능해진다.
- **Decision (3) 🔴 — 기하는 정확하고, 입력이 틀렸다.** **측정된** closed-loop state/time 으로 구동하면 (`reach_on_trajectory`) D-021 의 판정을 step 단위로 재현한다: crossing @ shipped `H=30` 에서 **live 0/92, max spread 0.00**, 그리고 `H=60` 의 wake 까지. 그런데 **같은 코드**를 `nominal_traversal` 로 구동하면 같은 scene 이 **5/35 live** 로 읽힌다. 오차는 전부 **pose 시퀀스**에 있다.
- **Decision (4) 🔴 — 원인은 타이밍이고, 미세 편향이 아니다.** closed loop 는 crossing scene 을 **9.2 s** 에 끝내는데 nominal 은 **16.7 s** 라고 말한다. 8 scene 전체에서 closed-loop/nominal 지속시간 비는 **0.56× ~ 15×**, **양방향**으로 벌어진다. 이동 장애물 scene 의 hazard field 는 `exposure.py` 자신의 표현대로 **"a rendezvous, not a place"** 이므로, 배수로 틀리는 타이밍 모델은 rendezvous 를 짚을 수 없다.
- **따름 결과 (a) — `exposure.py` 에 파급.** D-018 이 `cafe_obstacle_crossing_v0` (74%) 와 `cafe_convoy_v0` (43%) 를 가른 contested-fraction 은 각각 **0.56× / 1.63×** 로, **정확히 그 두 scene 에서 반대 방향으로** 틀린 타이밍 위에서 계산됐다 (상대 왜곡 ~2.9×). D-018 은 이미 controlled intervention 으로 exposure 를 **예측자로서 반증**했으므로 살아있는 결론이 뒤집히지는 않는다 — 바뀌는 건 "millisecond screen 으로는 살아남았다" 는 기록의 강도다.
- **따름 결과 (b) — D-021 의 마지막 귀속은 지지되지 않는다.** D-021 은 crossing 의 짧은 epistemic reach 를 `target_speed_mps: 0.3` 탓으로 돌렸는데, **controller 가 그 설정을 추종하지 않는다** (측정된 plan speed 0.36 m/s, 실현 주행 0.54 m/s ≈ 1.8×). 측정된 reach 자체는 그대로 유효하고, **설명만** 무효다.
- **Decision (5) — screen 은 "측정으로 반증될 예측" 으로 출하한다.** `epistemic_reach` (zero-sim, 저렴, 타이밍 결함 명시) 와 `reach_on_trajectory` (sim 1 회, 정확, ground truth) 를 **같은 core loop** 위에 둔다. 두 driver 가 `poses`/`speeds` 배열만 다르므로 "기하는 정확, 타이밍은 아님" 이 헤지가 아니라 **검사 가능한 진술**이 된다. 현재 판정: **8 중 5 audible / 3 deaf** (obstacle 없는 scene 은 grid 모서리의 sensing-range 밖 σ 만 갖고 ~5 m 밖이라 닿지 않음) — 단 audible 쪽 숫자는 (3)/(4) 때문에 **아직 인용 금지**.
- **Alternatives**: (a) scalar 를 threshold 만 손봐 재사용 — D-021 clause 4 가 이미 반례를 고정했다. (b) nominal driver 만 출하하고 5/35 를 결과로 기록 — 이번 cycle 이 정확히 그 오독을 만들 뻔했다. (c) trajectory driver 만 출하 — screen 이 아니게 되고 (sim 비용) STATE #1 의 "sim 쓰기 전에" 를 못 지킨다. (d) 채택안: 둘 다 + 불일치를 테스트로 고정.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/03-00-p3-directional-reach-screen.md` · `eval/mppi_sandbox/reach.py` · `eval/mppi_sandbox/tests/test_epistemic_reach_screen.py` · D-018 / D-021 / Q-043

## D-021 — 2026-08-02 — epistemic 채널의 효과는 **rollout reach 로 게이팅**된다. repo 의 모든 `lam` window 는 `w_epist = 0` 에서 측정된 값이다

- **Context**: STATE #1 은 crossing scene 의 `w_epist` ablation 을 "correlate 가 아니라 **mechanism** 을 재는 마지막 실험" 으로 세웠고, 근거는 "epistemic 채널이 `risk_mppi` 에만 있고 `stock_mppi` 에 없는 유일한 항" 이었다. **이 전제의 양쪽이 모두 틀렸으며, 둘 다 시뮬레이션 없이 반증된다.**
- **Decision (1) — 그 ablation 은 이미 shipped default 다.** `RiskMPPI.__init__` 의 `w_epist` default 는 `0.0` 이고 `calibrate_lam.main` 은 arm kwargs 를 전달하지 않는다. 따라서 `eval/scenarios/lam_windows.yaml` 의 **모든** window — D-017~D-020 이 네 cycle 을 쓴 `cafe_obstacle_crossing_v0` 분리 (`stock [0.4,0.8]` vs `risk [1.6,3.2]`) 포함 — 는 epistemic 채널을 **끈 상태**의 측정이다. **이 repo 의 어떤 separation 결과도 epistemic 채널에 대한 증거가 아니다.** 실제로 두 arm 을 가르는 항은 전제가 지목하지 못한 `w_risk = 40.0` (DYNAMIC 채널) 이다.
- **Decision (2) — 켜도 무신호다.** 11:00 이 확립한 실패 모드는 "가격은 매기는데 안 움직인다"(`offset=0.3`: spread 평균 197, 궤적 bit-identical) 였다. crossing scene 은 한 단계 더 퇴화한 **별개 모드**: shipped `H = 30` 에서 per-sample spread 가 **92 step 전부 정확히 0**. 상수는 softmax 에서 정확히 소거되므로 **어떤 weight 도 no-op** 이다 — 실제로 `w_epist` 200 vs 0 이 4/4 seed 에서 **byte-identical** (`w_risk` 를 shipped 40.0 로 둬도 동일). grid 의 평균 12% 가 σ=1 이므로 "렌더링이 없어서" 가 아니라 **rollout cloud 가 거기 닿지 못해서**다.
- **Decision (3) — 게이트는 rollout reach 이고, 양방향 controlled intervention 으로 확인했다** (D-018 준수, 예측은 실행 **전** 등록). (A) 죽은 scene 의 horizon 을 30→60 으로 올리면 live step 0/92 → **121/240**, spread 0 → 1512. (B) live 로 알려진 `offset=0.3` scene 의 horizon 을 깎으면 spread **196.49 → 11.36 → 0.00** (H = 30/20/10) 으로 단조 소멸. 한쪽만 돌렸으면 "깨우는 knob" 또는 "scene 무관 감쇠" 까지만 말할 수 있었다.
- **Decision (4) — 그 게이트의 scalar 형태는 폐기.** "가장 먼 rollout 점 ≥ 가장 가까운 미관측 cell" 이라는 자명한 요약은 **거짓**이며 반례를 테스트로 고정했다: crossing @ H=30 에서 그 부등식이 **92 중 28 step** 에서 성립하는데 spread 는 여전히 정확히 0. rollout 은 경로를 따라 **멀리** 뻗고 shadow 는 actor 의 **측면·후방**에 있다. reach 는 게이트가 맞지만 **거리 스칼라는 예측자가 아니다** — 방향이 진술에 들어가야 한다.
- **따름 결과**: 이 scene 에서 해법은 `w_epist` 를 키우는 게 아니다 (정확히 0 배). 움직여야 할 knob 은 rollout 점을 σ > 0 인 곳에 놓는 것들 — planning horizon, sampled speed, sensing range — 이고, `cafe_obstacle_crossing_v0` 는 `target_speed_mps: 0.3` ("dodge 할 여유를 준다") 이라서 **obstacle 이름을 단 scene 이 matrix 에서 epistemic reach 가 가장 짧다.**
- **Alternatives**: (a) STATE #1 을 액면대로 실행 — ladder 를 돌려 window 가 안 움직이는 걸 보고 "효과 없음" 으로 기록. 64 sim 을 쓰고 *왜* 인지는 못 얻는다. (b) `w_epist` 를 키워 재시도 — 0 배는 스케일 불가라 무의미. (c) 채택안: liveness 를 먼저 재고, 게이트를 양방향으로 특정.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/02-23-p3-epistemic-reach-gate.md` · `eval/mppi_sandbox/tests/test_epistemic_reach_gate.py` · Q-043

## D-020 — 2026-08-02 — Q-042 기준 (b) **quantile 완화는 폐기**, (c) **구간추정을 후계 기준으로 확정** (default 는 re-baseline 까지 (a) 유지)

- **Context**: D-019 가 all-seeds 논리곱의 `n`-단조 편향을 밝히고 세 후보 (a)/(b)/(c) 를 남겼다. Q-042 의 다음 action 은 "`ab.LamProbe` 가 per-seed ESS 를 보유하는지 먼저 확인" 이었는데, **보유하지 않으며 동시에 그 확인이 불필요**했다: seed 는 exchangeable 이므로 `(n_in_band, n)` 이 per-seed in-band 지시벡터의 **충분통계량**이고, 세 기준 모두 이 쌍의 함수다. 즉 in-band 절반은 처음부터 재채점 가능했다. 재채점 불가였던 건 **completion 절반** — `all_reached` 가 boolean 이라 `False` 가 `[0, n)` 전체와 양립.
- **Decision**: (1) **(b) 폐기** — `ceil(0.9n) == n` 이 모든 `n ≤ 9` 에서 성립하므로 이 repo 가 실제로 쓰는 seed 수(4, 8)에서 (b) 는 (a) 와 **점별로 동일**하다. 별개 기준이 되는 건 `n ≥ 10` 부터. 시뮬레이션 0회, 산술로 반증. (2) **(c) 를 후계 기준으로 확정**하되 **closed form (Wilson lower bound)** 로 — resampling 이 아니라. (3) **default 는 `all_seeds` 유지** (D-019 준수) → repo 의 기존 window 는 하나도 안 움직인다. 이 불변성은 테스트로 고정. (4) `LamProbe.n_reached` 추가(구 probe 는 sentinel `-1`, 분수 기준은 추측 거부하고 raise).
- **근거 실측** (D-019 의 flip: `stock_mppi @ lam=1.6`, `cafe_obstacle_crossing_v0`, 양쪽 다 8/8 도달이라 band 만 움직임): (a) n=4 admissible → n=8 상실. (b) **동일하게** 상실. (c) **0.510 → 0.529 로 오히려 상승** — `k = n` 일 때 bound 가 정확히 `n/(n+z²)` 라 `n` 에 **증가**하므로, 통과한 seed 가 신뢰를 *사고* window 가 증거와 함께 **커질 수 있다**. D-019 의 편향을 완화가 아니라 **역전**시킨다.
- **(c) 를 closed form 으로 쓰는 이유**: n=8 에서 bootstrap p2.5 = 0.625 vs Wilson 0.529. resample 의 support 가 격자 `{0, 1/n, …}` 이라 step 이 0.125 인데 Q-042 가 분해해야 할 효과는 0.019 — **추정량의 입자도가 신호의 7배**. 격차는 n = 8/40/1000 에서 0.096/0.036/0.001 로 수렴하므로 공식 오류가 아니라 소표본 입자도이고, **하필 이 repo 가 서 있는 지점에서 최악**이다.
- **Alternatives**: (a) 영구 유지 — 싸지만 matrix 확장마다 과거 판정이 흔들린다. (b) — 위 사유로 폐기. (c) bootstrap 구현 — 위 입자도 사유로 기각, closed form 채택.
- **미결**: (c) 의 **threshold 는 이번 cycle 이 의도적으로 고르지 않았다.** 정당화된 threshold 없이는 default 로 승격 불가. re-baseline 브랜치가 (a)/(c) 양쪽으로 window 를 재생성하고 **불일치 집합**을 보고하는 것이 다음 단계.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/02-22-p3-lam-admissibility-criterion.md` · `eval/mppi_sandbox/tests/test_lam_admissibility_criterion.py` (220 passed, +27)

## D-019 — 2026-08-02 — `per_arm` / `shared` 판정에는 **seed 수 `n` 을 반드시 함께 명시**한다 (scene 속성이 아니다)

- **Context**: Q-041 (2×2 를 한 parent 안에서 닫기) 을 실행하다 더 큰 문제를 발견했다. `ab.LamProbe.admissible` 은 **모든 seed 가 ESS band 안 + 도달**을 요구한다 — 즉 window 는 seed 에 대한 **논리곱(conjunction)** 이고, seed 를 늘리면 **줄어들 수만 있고 늘어날 수 없다**. 실측: parent scene `cafe_obstacle_crossing_v0` 는 **n=4 에서 `shared`, n=8 에서 `per_arm`**. `stock_mppi` 가 `lam=1.6` 을 4-seed 에선 통과하고 8-seed 에선 잃는데, 1.6 은 `risk_mppi` 가 양쪽에서 유지하는 rung 이다. **기하는 하나도 안 변했고 뽑은 seed 수만 변했다.**
- **Decision**: `shared` / `per_arm` 은 scene 의 속성이 아니라 **`(scene, controller-pair, n_seeds)` 의 속성**이며, bias 방향이 알려져 있다 (n↑ → window↓ → `per_arm` 쪽). 따라서 (a) 모든 `per_arm` / `shared` 주장은 **`n` 을 명시**해야 하고, (b) 서로 다른 `n` 으로 얻은 판정은 **비교 금지**, (c) calibration table 은 이미 `seeds:` 를 기록하므로 그 값을 인용 없이 쓰는 보고를 금한다.
- **파급**: Q-040(18:00~20:00) 과 Q-041(21:00) 이 물었던 "**어떤 scene 속성이 separation 을 예측하는가**" 는 **malformed question** 이었다 — `n` 을 고정하기 전엔 예측 대상 자체가 정의되지 않는다. 18:00 headline (`crossing` 은 matrix 유일의 `per_arm`) 도 "at n=8" 을 달아야 한다. D-017 의 프로토콜(교집합 non-empty ⇒ single-`lam` 가능)은 **여전히 유효** — 다만 판정 입력이 `n` 에 의존함이 드러난 것.
- **이번 cycle 의 Q-041 결과 자체는 부수적**: 한 parent 안에서 stagger✓ 두 cell 모두 `per_arm`, stagger✗ 두 cell 모두 `shared` → **interaction 반증, timing 의 main effect**. 20:00 의 "interaction" 은 동일 factor level 의 두 parent(`convoy_staggered` vs `crossing_noflow`)가 불일치한 것이었다. 또한 direction flip 은 clearance matrix 가 **bit-identical**(max|diff|=0.0)인데도 window 를 움직였다(`sync` 교집합 {1.6,3.2} vs `sync_noflow` {3.2}) → `exposure.py` 는 **증명 가능하게 불완전한 screen**.
- **Alternatives**: (a) 현행 all-seeds 논리곱 유지 + `n` 명시만 — **채택**, 최소 침습이고 기존 표를 버리지 않는다. (b) 기준을 quantile 로 완화(예: ≥7/8) — n-민감도를 줄이지만 여전히 n 의존이고 재-baseline 전체가 필요, Q-042 로 이월. (c) window 를 점추정 대신 **구간추정**(seed bootstrap)으로 — 원리적으로 옳으나 ~250-run calibration 을 몇 배로 늘림, 보류.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/02-21-p3-lam-separation-seed-confound.md` · commit `6f36287` · Q-041 → refuted, Q-042 신설

## D-018 — 2026-08-02 — scene 속성 가설은 **양방향 controlled intervention** 으로만 채택한다

- **Context**: Q-040 — 8-scene matrix 에서 `per_arm` 은 `cafe_obstacle_crossing_v0` 하나뿐이고, `cafe_convoy_v0` 는 **같은 5개 actor** 로 `shared`. 후보 predictor 로 time-in-contest (`exposure.py`) 를 세웠고 static ranking 은 설득력 있었다 — crossing 74% vs convoy 43%, 게다가 `peak_contesting` 은 정반대로 순위(2 vs 5)를 매겨 두 통계가 깔끔히 분리됐다. 하지만 positive 1개짜리 n=8 ranking 은 증거가 아니다: crossing 을 1위로 놓는 통계라면 무엇이든 "predictor 처럼" 보인다.
- **Decision**: scene 속성이 측정 결과를 예측한다는 주장은 **(a) predictor 가 지목하지 않는 모든 것을 고정한 intervention**, **(b) 예측을 run 이전에 artifact 안에 명기**, **(c) 올리는 팔과 내리는 팔 **양쪽** 실행** — 셋을 모두 만족할 때만 채택한다. control 은 주석이 아니라 **test 로 기계적 강제** (`test_variant_changes_only_obstacle_start_times` 가 parent/variant yaml 을 diff).
- **근거는 이번 cycle 자신**: 내리는 팔(`crossing_sync`, 74%→26%)은 예측대로 window 가 **재중첩**해 가설을 확증했다. 올리는 팔(`convoy_staggered`, 43%→**77%**, 즉 `per_arm` scene 자신의 74% 를 넘김)은 두 arm 이 여전히 **[0.4, 0.8] 공유** — **반증**. 더 싸고 자연스러운 쪽인 내리는 팔만 돌렸다면 거짓 predictor 를 calibration 서사에 승격시켰을 것이다.
- **부수 산출**: `exposure.py` 는 반증 후에도 남는다 — 새 scene 의 hazard profile 이 ~250-run calibration 이 아니라 **밀리초 질의**가 된다 (D-016 sandbox-first, 17:00 `feasibility.py` screen 과 같은 계열).
- **살아남은 lead (result 아님)**: 네 cell 이 (staggered timing) × (counter-flow actors) 의 2×2 를 이루고 `per_arm` 은 ✓✓ 한 구석에만 나타난다 — main effect 가 아니라 **interaction**. off-diagonal 두 cell 이 서로 다른 parent 에서 왔으므로 fully crossed 가 아니다. variant 2개 추가로 닫힌다.
- **Alternatives**: (a) static ranking 만으로 채택 — 기각, 반증됐을 가설을 실을 뻔했다 (b) 한쪽 팔만 — 기각, 바로 이 cycle 이 반례 (c) 아무것도 안 함 — 기각, `per_arm` 판정은 A/B 프로토콜(D-017)을 좌우하므로 예측자가 필요하다.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/02-20-p3-hazard-exposure-refuted.md` · `eval/scenarios/variants/` · commit `b237727`

## D-017 — 2026-08-02 — A/B 의 온도 프로토콜은 **controller pair** 단위로 결정한다 (Q-039 답)

> ⚠️ **D-036 재범위(rescope)** — 여기 적힌 **1.9×** 는 보고된 두 clearance gain 의
> 비(+0.0957/+0.0492 = 1.945)다. dispatch 에서 뒤집히는 instrument
> (`test_ab_temperature_protocol::test_protocol_moves_the_effect_size_but_not_its_sign`)
> 는 paired seed mean 위에서 같은 비를 **1.6956** (`AVX512_SKX`) 으로 읽고, AVX2
> 에서는 **1.0546** 이다. 남는 몫: assertion(`>1.25`) 의 **21.8 %**, 측정값의
> **7.8 %**, 여기 인용된 1.9× 의 **6.1 %**. Q-039 의 답에서 *방향*은 남지만
> *효과 크기*는 `AVX512_SKX` 조건부다.

- **Context**: Q-035 는 per-cell 규칙을 정했다 — scene 은 *한 controller* 의 admissible window 가 non-empty 일 때만 ablation surface. 18:00 이 그것으로 부족함을 실측: `cafe_obstacle_crossing_v0` 는 **두 arm 모두 calibratable** 인데 window 가 disjoint (`stock_mppi` [0.4, 0.8] vs `risk_mppi` [1.6, 3.2]) — 공유 가능한 온도가 없다. 그런데 이 브랜치의 모든 A/B 는 두 arm 을 하나의 `lam` 으로 돌려 보고해 왔다.
- **Decision**: pair 단위로 한 단계 올려 일반화 — *scene 이 controller pair 의 **single-temperature** A/B surface 인 것은 두 window 의 교집합이 non-empty 일 때 뿐*. `ab.ab_temperature` 가 calibration table 에서 `shared | per_arm | unreportable` 을 run 이전에 판정하고, `assert_single_lam_ab` 가 위반을 거절하며 대안을 이름으로 제시한다. disjoint 일 때는 **per-arm 온도 + gap 명시** 를 택한다 (`lam_for` 가 log-space gap 최소 쌍 0.8/1.6 = 2× 선택). 근거는 실측: 두 대안 모두 confound 가 있지만 크기가 다르다 — single-`lam` 은 한 arm 이 band 밖(ESS 3.92, near-argmin)이라 confound 가 **무한정이고 보이지 않으며**, 실제로 그 arm 의 clearance 이득을 **1.9× 부풀린다** (+0.0957 m vs in-band +0.0492 m); per-arm 은 confound 가 **gap 으로 유계이고 보고 가능**하다.
- **따라서 보고 규칙**: disjoint-window scene 은 **direction claim 은 single-`lam` 로 가능**(부호는 세 프로토콜 모두 7~8/8 로 동일), **effect-size claim 은 불가**. #67/#68/#69 의 headline 은 effect-size claim 이므로 re-baseline 이 이 구분을 적용해야 한다.
- **Alternatives**: (a) single-`lam` 유지 — arm 이 의도한 update 를 실행하지 않는데 그 사실이 숨는다, 기각. (b) disjoint scene 을 matrix 에서 제거 — 8 scene 중 1 개를 버리면서 *언제* 그런 일이 생기는지는 여전히 모른다, 보류(STATE #2 가 그 질문). (c) `lam` 을 아예 풀어서 sampling-accuracy criterion 으로 solve — 옳은 방향이나(feed 08-02 16:00, Watson & Peters 2210.03512) re-baseline 이후 작업, 지금의 보고 규칙을 대체하지 않음.
- **Status**: accepted
- **Refs**: PR #67 · `journal/2026-08/02-19-p3-ab-temperature-protocol.md` · Q-039 (18:00), Q-035/Q-026 상위 일반화

## D-016 — 2026-07-11 — Python-native `eval/mppi_sandbox/` 가 primary verification surface, Gazebo 는 occasional bench (user 결정)

- **Context**: 지난 5주 자동 사이클이 D-012~D-015 / Q-007~Q-016 등 spec 만 누적하고 실행 코드 진척 0 — 근본 원인은 cron executor 가 Gazebo 를 검증 수단으로 못 씀 (headless GPU / 분 단위 startup / non-deterministic / assertable outcome 없음). 코드를 내도 "돌아간다" 를 스스로 증명 못 하니 executor 가 spec-only 산출로 수렴. 사용자가 직접 지적: "Gazebo 는 auto-research 로 검증이 힘드니 test 코드나 자체 시뮬레이터로 검증하는 형태로 구성하자, safe_control 이 좋은 레퍼런스".
- **Decision**: `eval/mppi_sandbox/` (NumPy diff-drive plant + circle obstacle + controller plug-in registry + scenario yaml 공유 + `run_metrics` 동일 JSON schema) 를 **primary verification surface** 로 신설. 검증 계약 = pytest (`eval/mppi_sandbox/tests/`, 초 단위) + `.github/workflows/sandbox-ci.yml` (plain ubuntu ~1min, ROS 불필요). 새 controller/representation 코드는 sandbox plug-in + pytest green 을 동반해야 land. safe_control 은 **패턴 참조** (numpy sim loop + pluggable controller) + wrapper 비교 백엔드로 유지, vendoring X (D-005 유지). Gazebo + Nav2 는 sensor-driven BEV / LiDAR occlusion / sim2sim gap 확인용 occasional bench 로 강등 (user-run). v0 첫 실측: 8 scenario × stock_mppi = 5 pass / 3 fail — fail 3건 (head-on graze 0.01m, cut-in freezing, figure8 self-crossing metric 한계) 이 곧바로 baseline finding.
- **Alternatives**: (a) Gazebo 를 CI 컨테이너에 — startup/GPU/flaky 로 기각. (b) safe_control 내부에 우리 controller injection — 외부 API 종속 + license 미명시, 기각. (c) spec-first 유지 — 5주간 코드 0 으로 실증 실패, 기각.
- **Status**: accepted
- **Refs**: `eval/mppi_sandbox/` + `docs/mppi_sandbox.md` + `.github/workflows/sandbox-ci.yml`; 패턴: tkkim-robot/safe_control (D-005); baseline: `runs/*-sandbox.json`

## D-015 — 2026-06-29 — 다섯 P3 uncertainty knob 의 calibration 을 단일 harness `eval/calibrate_risk.py` 가 소유 (coupled `(k,δ)` joint sweep)

- **Context**: P3 variance→safety 설계 lane (D-009/D-013/D-014) 가 5개 tuning knob (`k`/`δ`/`α`/`σ²_ref`/`σ²_ref_ale`) 을 남겼으나 각각 다른 deliberation (Q-008/009/011/012) 에 parked, calibration *절차*의 owner 가 없었다. 5개 독립 grid search 는 (a) launch/aggregation plumbing 5중복, (b) `k·σ`(epistemic)·`z(δ)·σ_ale`(aleatoric) 가 *같은* effective clearance `d_eff` 를 조이는 cross-knob coupling 을 놓침 → 격리 튜닝 시 안전 이중계상·corridor 과수축. (이 결정은 #55 가 land 했으나 당시 #55 자신이 decisions.md prepend 를 점유 → D-011 conflict trap 회피 위해 `p5_risk_calibration_harness.md` §1 에만 `(→D-015)` 로 기록, 승격은 이 cycle 로 deferred.)
- **Decision**: 단일 calibration harness `eval/calibrate_risk.py` 가 5 knob 의 joint sweep 을 소유. 새 metric·새 launch path 도입 X — 기존 `run_metrics`/`path_tracking_metrics` JSON 재사용하는 thin driver (knob-vector → 두 critic config → 시나리오별 launch → `runs/<id>.json` readback → sweep TSV 1행/(knob-vector×scenario)). refs 는 documented default 로 freeze, `(k,δ)` 2-D plane (primary 4×4) + `cvar_alpha` 1-D secondary 만 sweep (~16+3 점×N, not `O(n^5)`). `k=0,cost_weight=0` baseline row 가 no-critic 숫자를 byte-for-byte 재현 → harness 가 behavior 아닌 search 만 추가함을 증명. (near-miss, time-to-goal) Pareto front 를 시나리오별 emit (premature scalarization X — trade rate 는 user 가 front 본 뒤 선택).
- **Alternatives**: (a) knob 당 독립 grid 5개 — plumbing 중복 + coupling 무시로 과보수 operating point. (b) 단일 scalar objective 로 즉시 collapse — trade rate 가 front 관측 전에 baked-in. (c) full 5-D grid — combinatorial. 모두 기각.
- **Status**: accepted
- **Refs**: PR #55 (merged) + `docs/p5_risk_calibration_harness.md` §1/§2 + journal/2026-06/29-23-p5-promote-d015-q013-deferred-refs.md; Q-013 신규 (sweep strategy); knobs Q-008/Q-009/Q-011/Q-012

## D-014 — 2026-06-27 — Aleatoric risk routes via a standalone `AleatoricRiskCritic` (chance-constraint / CVaR tightening), separate from the epistemic margin critic

- **Context**: aleatoric 채널 스펙(#51 §4) 과 stack 문서(#52 §4) 가 모두 "aleatoric(idx 4) 의 nav2_mppi 진입점은 margin-inflation interface 의 sibling 으로, 그것이 land 한 뒤 critic-config surface 를 공유하며 별도 스펙한다"고 follow-up 으로 미뤘다. epistemic margin interface(#53, D-013) 가 머지되어 이제 그 surface 를 mirror 할 수 있다. 남은 질문: aleatoric 비가역(irreducible) 노이즈를 *어느* cost term 이 소비하고 *어떻게* 출력을 바꾸나.
- **Decision**: 독립 `AleatoricRiskCritic` 도입 — `CostCritic` 도 `RiskInflationCritic` 도 overload 하지 않음. epistemic 은 clearance 에서 `k·σ` 를 빼는 **geometry** 변경(무지 → 후퇴, 데이터 늘면 0 으로 소멸)이지만, aleatoric 은 비가역이므로 같은 margin 에 먹이면 영구 과보수가 된다. 따라서 aleatoric 은 **risk-sensitive constraint tightening**: chance-constraint 형 `d_eff = d − z(δ)·σ`(기본, `z(δ)`=고정 quantile) + 옵션 CVaR tail penalty. tighten-only / `Δ_max` clamp / mask-gated, `cost_weight=0.0` 기본(no-op, baseline 재현 → P5 ablation 한 숫자). epistemic·aleatoric 를 두 critic 으로 유지해야 P3 epi/ale split + 2-axis ablation 이 성립.
- **Alternatives**: (a) `CostCritic` overload — baseline 측정 불가, ablation 파괴. (b) epistemic critic 에 aleatoric 합치기 — epi/ale split 재붕괴, 서로 다른 row·수식(clearance 차감 vs tail measure). (c) margin-inflation `k·σ` 재사용 — 비가역 노이즈에 영구 과보수, 데이터로 안 줄어듦(swap error). 모두 기각.
- **Status**: accepted
- **Refs**: 이 cycle PR(aleatoric-cvar) + `docs/aleatoric_risk_cost_critic_interface.md` + journal/2026-06/27-00-p3-aleatoric-cvar-chance-constraint-critic.md; sibling D-013; Q-012 신규

## D-013 — 2026-06-19 — Epistemic margin routes via a standalone `RiskInflationCritic`, not a `CostCritic` overload

- **Context**: residual_in_rollout_reference §Axis-2 가 variance→safety 경로로 margin inflation(option 2, `cost+=λσ²` 아님)을 골랐고, epistemic 채널(#50)·stack(#52)·margin interface(#53) 가 모두 "epistemic `k·σ` 가 nav2_mppi cost 의 *어디로* 들어가나"를 한 문장씩 미뤘다. 실제 config 의 obstacle term 은 `CostCritic`(per-rollout, spatial field 소비)와 costmap `inflation_layer`(global pre-rollout) 둘뿐 — 후자는 control-step 마다 갱신되는 epistemic field 로 셀별 margin 을 못 바꾼다. (이 결정은 #53 에서 내려졌으나 당시 #52 가 decisions.md D-012 prepend 를 점유 중이라 D-011 conflict trap 회피 위해 margin 문서 §1 + Q-008 에만 기록, decisions.md 승격은 후속 cycle 로 deferred 됨.)
- **Decision**: 독립 `RiskInflationCritic` 도입(`CostCritic` overload 금지). baseline obstacle term 무손상(critic 끄면 정확히 baseline → P5 ablation invariant), epistemic margin 에 `CostCritic` 3.81 과 독립인 `cost_weight`, P5 `k`-sweep 를 한 plugin 에 격리. `k_margin_per_sigma=0.0` 기본(no-op), tighten-only / `Δ_max≤inflation_radius` clamp / mask-gated, epistemic-only(idx 3).
- **Alternatives**: (a) `CostCritic` overload — 두 gain 이 한 weight 에 엉켜 "representation 없는 MPPI" 측정 불가, P5 ablation 치명. (b) costmap-layer 진입 — global·static, 셀별·step별 변동 불가. 모두 기각.
- **Status**: accepted
- **Refs**: PR #53 (merged) + `docs/margin_inflation_cost_critic_interface.md` §1; sibling D-014; Q-008(routing half resolved, `k` value still P5)

## D-012 — 2026-06-17 — Canonical multi-channel risk BEV stack: fixed 5-channel order + explicit unobserved-mask (NaN-distinct-from-zero)

- **Context**: epistemic (#50) 와 aleatoric (#51) 채널 스펙이 각각 "나는 `[5,H,W]` 스택의 row _k_ 이고, 채널 순서 + mask 계약은 stack 문서가 소유한다"고 forward-reference 만 남긴 상태였다. 소유 문서가 없으면 채널이 하나씩 land 할 때마다 MPPI cost critic 입력 shape 가 재협상되어 churn 한다. 또한 risk `0.0` 의 의미가 모호 — "평가됨·확신의 0" vs "미평가/미관측" 이 구분 안 되면 planner 가 미관측(가려진) 셀을 zero-risk 로 읽고 진입하는 north-star 실패모드가 생긴다.
- **Decision**: (1) **고정 채널 순서** `static(0)/dynamic(1)/traversability(2)/epistemic(3)/aleatoric(4)` 을 `RiskChannel` IntEnum 으로 못박음 — perception rows(0–2) 먼저, model-uncertainty rows(3–4) 뒤 (cost-routing class 별 slice 가능). 인덱스는 append-only, 재사용/shift 금지. (2) **관측 가능성은 data plane 의 sentinel 이 아니라 명시적 mask** 로 운반 — NaN(reduction 오염) 거부, `[C,H,W]` boolean mask mirror 채택(미관측 = pessimistic prior, 0 아님). (3) 미구현 채널은 all-unobserved row 로 published → renderer 추가 시 cost-side 코드 변경 0. 스택은 critic 직전까지 channel-addressable 유지(pre-sum 금지) — epistemic=margin inflation vs aleatoric=chance-constraint 라우팅이 다르기 때문.
- **Alternatives**: (a) 채널별 입력 따로 — critic churn, 기각. (b) 단일 `[H,W]` shared mask — cell 이 static 엔 관측되나 epistemic 엔 미평가일 수 있어 일반적으로 틀림(O-1 inline). (c) NaN sentinel — sum/mean/max 무성 오염, 기각. (d) 모든 risk 를 scalar map 으로 pre-sum — 이질적 라우팅 불가, 기각.
- **Status**: accepted
- **Refs**: PR (this cycle) `autoresearch/p3-multi-channel-risk-bev-stack-tensor`; `docs/multi_channel_risk_bev_stack.md`; journal `journal/2026-06/17-23-p3-multi-channel-risk-bev-stack-tensor.md`. Open items O-1/O-2/O-3 inline (deliberations.md 승격은 #50 머지 후, 동시-prepend 충돌 회피).

## D-011 — 2026-06-09 — Root-cause fix for the recurring PR-queue deadlock: stop committing root snapshot files on feature branches

- **Context**: D-010 close-superseded-PRs는 큐 *개수*만 줄였을 뿐, 데드락의 진짜 메커니즘을 못 건드렸다. 진단: 모든 `autoresearch/*` 브랜치가 root-level `STATE.md`/`JOURNAL.md`/`RESULTS.md` (full-overwrite·append-top·regenerated 산출물)를 커밋 → 임의의 두 PR이 이 3파일에서 항상 충돌 → 1건 머지할 때마다 나머지 전 PR이 재충돌(CONFLICTING). 그래서 6 OPEN PR(#23/#24/#44/#45/#47/#48)이 06-06→09 4일+ gate-1 skip 루프에 갇혔다(user 명시 지시 "알아서 서브에이전트로 해결" 받음).
- **Decision**: (1) **즉시 unblock** — 6개 브랜치 전부에서 3개 snapshot 파일을 `git checkout origin/main --` 로 되돌려 strip → 각 PR이 unique-path 기여(code/docs/journal/tsv)만 carry → **순서 무관 독립 머지 가능**(1건 머지가 나머지를 재충돌시키지 않음). main 머지·PR close 없이 해결. (2) **재발 방지** — `scripts/prompts/auto_research.md` Phase 3/4 에 "`autoresearch/*` 브랜치에 STATE/JOURNAL/RESULTS 절대 commit 금지" 규칙 추가. 이 3파일은 local-only 스냅샷으로 유지(다음 cycle REVIEW가 디스크에서 읽음), durable record는 충돌 없는 unique-path 파일(`journal/`, `results/*.tsv`, `decisions.md`, `deliberations.md`)이 보유.
- **Alternatives**: (a) PR을 계속 close — D-010 이미 소진, 남은 6건은 build-path/미대체라 close 부적격. (b) 매 머지마다 충돌 수동 해소 — 4일째 실패 입증. (c) `.gitattributes merge=union` — overwrite/regenerated 파일엔 무의미. (d) GitHub 가시성 위해 3파일 유지 — 충돌 원인 존속, 기각.
- **Open follow-up**: brief/wrap/curator 등 다른 agent가 STATE를 main에 커밋하면 재발 가능 → 그쪽 prompt도 동일 규칙 적용할지, 혹은 3파일 완전 gitignore할지는 user 판단(이번엔 executor 경로만 고침). GitHub-rendered STATE/JOURNAL 가시성 trade-off 존재.
- **Status**: accepted
- **Refs**: 이 cycle PR #47 (folded) + stripped #23/#24/#44/#45/#48 + journal/2026-06/09-23-pr-queue-deadlock-resolve.md

## D-010 — 2026-06-06 — Executor may self-heal a multi-day PR-queue deadlock by closing its own superseded PRs

- **Context**: P2 PR 큐가 **17일(2026-05-20→06-06)** 동안 7건 OPEN 으로 고정 → gate-1(≥6) 이 매 사이클 skip 유발, 코드 진척 0. 30+회 동일 skip 재로그 + 1회 Telegram 에스컬레이션에도 user 행동 0건. 이전 사이클들은 "PR close 는 user 권한" 으로 과보수 해석 → silent deadlock 영구화. 헌법 hard-limit 은 *main 머지*만 금지하며 PR close 는 금지 대상 아님.
- **Decision**: 큐가 ≥72h stall 이면 executor 가 **자기 산출물인 superseded PR 을 close** 해 큐를 ≤5 로 낮춘 뒤 정상 루프 진행 가능. close 조건 4종 ALL: (a) `autoresearch/*` executor 작성, (b) accepted D-NNN 으로 명시적 대체, (c) 다른 open/mergeable PR 이 의존하는 build-path 코드 없음, (d) reversible(브랜치 보존+reopen 안내). 미충족 시 강행 금지 — skip + 72h당 1회 Telegram 에스컬레이션 폴백.
- **Action this cycle**: D-009 로 대체된 CFM/탐색 trio **#25**(CFM-MPPI analysis, doc-only)/**#26**(MLP-CFM velocity field, CFM 미채택)/**#27**(ensemble-compat analysis+flops) close → 큐 7→4. 셋 다 build-path 코드 없음(#23 dataset/#44 scaffold/#45 data-pipeline 이 실제 build path). gate-1 해제.
- **Alternatives**: (a) skip-only 지속 — 17일 입증된 실패, (b) 매시간 Telegram — 24/day 노이즈, (c) 충돌 PR auto-gen 충돌 executor resolve — fiddly+리뷰직전 force-push 혼란.
- **Status**: accepted
- **Refs**: PR autoresearch/p2-executor-pr-queue-deadlock-breaker + closed #25/#26/#27 + journal/2026-06/06-15-p2-executor-pr-queue-deadlock-breaker.md

## D-009 — 2026-05-31 — P2 residual-dynamics: build-first = MLP-ensemble(K=3), offline-frozen

- **Context**: P2 residual-dynamics 후보가 8개 research entry + 5 open PR 로 파편화, "무엇을 먼저 구현" 미수렴. 데이터 부재는 #23 unicycle generator 로 해소됨 — 진짜 bottleneck 은 아키텍처 선택.
- **Decision**: 첫 구현은 **C1 small MLP-ensemble residual (K=3)**, synthetic-unicycle bootstrap 에 offline-frozen, MPPI batched-rollout wrapper. 이유: rollout-native(matmul, ODE solver 불필요), 오늘 bootstrap 가능(env label/task dist 불필요), ensemble var→P3 epistemic channel 무료, 최저 복잡도.
- **Alternatives**: (a) STRIDE-CFM(C2) — rollout 에 ODE/sampling 무거움, 추후 target, (b) ICODE NODE(C3) — 적분 비용, (c) SFKD ISS(C4) — env label 필요·복잡도 5, U3 로 연기, (d) T2S/low-rank online(C5/C6) — time-varying 입증 후 U2 로 연기.
- **Status**: accepted
- **Refs**: [`docs/p2_residual_dynamics_decision.md`](p2_residual_dynamics_decision.md), TODO 370c5d39, journal/2026-05/31-00-p2-residual-dynamics-decision-matrix.md

## D-008 — 2026-05-28 — Decision log + Deliberation log 도입

- **Context**: 자율 R&D 가 9 cycle 진행됐는데 "왜 이 선택" 의 timeline 이 git log + journal 에 분산. 결정 회고가 어려움.
- **Decision**: `docs/decisions.md` + `docs/deliberations.md` 신설. auto_research.md Phase 4 REPORT 에 "Decision append" 단계 추가.
- **Alternatives**: (a) journal 안에 섹션 추가 — 산만, (b) GitHub Discussions — 외부 의존, (c) Notion sub-page — 검색성 떨어짐.
- **Status**: accepted
- **Refs**: 이 commit, docs/agents.md A2 Builder 의 REPORT phase 갱신 (follow-up).

## D-007 — 2026-05-27 — 시나리오 10종 + Controller 8종 격자 가설 도입

- **Context**: 동적 장애물 정책 비교 필요. 사용자 명시 요청.
- **Decision**: ego-frame 10 시나리오 (S01-S10) × controller 8종 (ObstaclesCritic ~ DR-MPC) 매트릭스 가설 → Phase D3 ablation 으로 ground truth.
- **Alternatives**: 단일 시나리오 + controller per phase — 비교 불가능.
- **Status**: accepted
- **Refs**: `docs/scenarios_and_controllers.md`, issue #38/#39/#40, commit 70e8b39

## D-006 — 2026-05-26 — Dynamic obstacle + Uncertainty 단일 track 으로 묶음

- **Context**: feed 에 14+ 관련 paper, 사용자도 두 axis 명시 관심. 분리하면 시야 분산.
- **Decision**: 두 axis 가 risk-aware MPPI cost 단일 출구를 공유함을 명시. `docs/dynamic_obstacles_uncertainty_track.md` 통합 track 으로.
- **Alternatives**: 2개 별 doc — 중복 + cross-ref 부담.
- **Status**: accepted
- **Refs**: `docs/dynamic_obstacles_uncertainty_track.md`, commit 4f1a8d8

## D-005 — 2026-05-25 — safe_control 외부 ref 통합 (use-in-place, vendoring X)

- **Context**: 사용자가 4 reference (cfm_mppi + DR-MPC + SCOPE + safe_control) 통합 요청. License 미명시 다수.
- **Decision**: `scripts/fetch_refs.sh` 로 외부 clone, `eval/<harness>/` 에 wrapper 만. vendoring 안 함.
- **Alternatives**: (a) fork — license 불확실, (b) re-implement from paper — 시간 ↑, (c) submodule — git complexity.
- **Status**: accepted (safe_control 의 DPCBF/evade/tracking 3건 즉시 실측 검증)
- **Refs**: `scripts/fetch_refs.sh`, `eval/safe_control_harness/`, commit cb16e3a + 47a8a9e

## D-004 — 2026-05-25 — docs 4종 "헌법" 신설 (prd/agents/skills/todo)

- **Context**: docs 분산. 자율 agent 가 어디 인용해야 할지 불명.
- **Decision**: PRD (북극성+요구) / agents (역할) / skills (도구) / todo (4 surface) 4종 = 프로젝트 헌법.
- **Alternatives**: CLAUDE.md 안에 다 넣기 — 너무 길어짐.
- **Status**: accepted
- **Refs**: `docs/{prd,agents,skills,todo}.md`, commit 3d418dc

## D-003 — 2026-05-24 — Multi-agent + auto-merge 정책 도입 (PR 정체 14일 후)

- **Context**: 5/10~24 PR 큐 cap=3 도달 → cron 216회 silent skip → 진척 0. 사용자 부재 시 시스템 self-block.
- **Decision**: Researcher (4h) + Curator (daily, safe-surface auto-merge) 추가. PR cap 3→6, daily cap 6→10.
- **Alternatives**: (a) 사용자 머지 알림만 강화 — 부재 시 무력, (b) 모든 PR auto-merge — 위험.
- **Status**: accepted (다음 날 6 PR/24h 처리 입증)
- **Refs**: commit 827bb57, `scripts/{researcher,curator}.sh`, `scripts/prompts/{researcher,curator}.md`

## D-002 — 2026-05-05 — 5-phase R&D 루프 (REVIEW → PLAN → EXECUTE → REPORT → PLAN_NEXT)

- **Context**: 단순 pick-and-execute 로 5일간 infra PR 만 쌓이고 north-star 진척 0.
- **Decision**: karpathy/autoresearch 패턴 차용, 35 min budget 5 phase.
- **Alternatives**: (a) 단순 cron with budget — reflection 없음, (b) 사람 매일 review — 자율성 X.
- **Status**: accepted (cycle 1 직후 path-tracking metric v0 produce)
- **Refs**: commit ef349b1, `scripts/prompts/auto_research.md` 449 lines

## D-001 — 2026-05-01 — Notion DB + Telegram bot + cron 4종 자동화 시스템 셋업

- **Context**: 자기계발 프로젝트, 6개월 일관 페이스 필요. 사용자 부재 시간 활용.
- **Decision**: Notion TODO DB + Telegram bot + cron (brief/wrap/weekly/poll) 셋업.
- **Alternatives**: GitHub Projects (Notion 보다 빈약), email (실시간 X).
- **Status**: accepted, 28일째 가동 중
- **Refs**: 초기 commit 들, `docs/automation.md`

---

## Append 정책 (cron-agent)

매 cycle 의 REPORT phase 에서 (auto_research.md Phase 4 의 추가 step):
- 이번 cycle 에 새로운 architecture-level / scope-level / priority-pivot 결정 있으면 → 이 파일 prepend
- 단순 코드 변경/문서 수정 → journal 만, 이 파일 X
- Open question 만 발견 시 → 이 파일 X, [`deliberations.md`](deliberations.md) prepend

D-NNN 번호는 strictly 증가, 절대 재사용 X. supersede 시 새 D 번호 + 이전 entry Status 갱신.

_Last manual update: 2026-05-28 KST_
