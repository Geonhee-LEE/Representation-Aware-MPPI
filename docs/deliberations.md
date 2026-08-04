# Deliberation Log — 풀리지 않은 고민

> 의사결정 이전 단계. **답이 아직 없는 질문** + **trade-off 의 양쪽 모두 무게 있는 사안**.
> 답을 내면 `decisions.md` 로 승격 (D-NNN entry 추가, 여기서 strikethrough).
> 사람도 cron-agent 도 추가 가능.

**컨벤션**:
- 최신이 위 (prepend), 한 entry ≤ 15 줄
- Status: `open` / `partially-answered` / `resolved → D-NNN`
- Tag: `[scope]` `[arch]` `[priority]` `[license]` `[meta]` `[uncertainty]`

---

## Q-081 — 2026-08-05 — `[uncertainty]` 이 branch 가 publish 한 magnitude 중 **자기 `gap_spread` 를 견디는 것**이 하나라도 있나

- **Question**: D-074 가 한 tree 위 replicate 만으로 gap 이 1.14×~4.50× 흩어짐을 보였다.
  D-066 이후 모든 cycle 은 두 조건 사이의 magnitude **차이**를 근거로 문장을 썼다 —
  "142 vs 95", "12 는 사실 20", "13× undershoot", "0.487 % 는 band 안". 그 차이들이
  전부 이 spread 보다 작다면 남는 주장은 **membership (7/50, 여섯 번 재현)** 하나뿐이다.
- **Trade-off**: (a) `docs/decisions.md` 의 모든 인용 magnitude 를 static 하게 훑어
  spread 와 대조 — run 0, 1 cycle, 그리고 **답의 크기가 곧 결론**이다. (b) 각 주장을
  licensed batch 로 다시 사기 — 정직하지만 site 당 ~8 분이고 이미 42 cycle 이 계측만 했다.
- **Lean**: (a). D-073 의 `published_ratios` 가 이미 자릿수 단위로 transcribe 해 뒀으므로
  대조는 join 한 번이다. (b) 는 그 결과가 "0 건 생존" 이 아닐 때만 정당하다.
- **다음 action**: 다음 cycle, executor, static. `gap_spread` 는 record 에서 읽는다.
- **Status**: static half **resolved → D-075** (lean (a) 로 수행). 답: gap movement
  23 중 8 통과, 여유 분포를 반영하면 **5**; ratio 는 5 중 4 통과이나 그 중 둘은 control 이
  1~2. `_pure` 는 6 중 **0**. "0 건 생존" 은 아니었으므로 trade-off (b) 는 여전히 열려
  있고, 실제로 남은 세 marginal 을 가르려면 k≥5 batch 가 필요하다. **ordering half 는
  미해결** — D-074 가 one tree 위 rho 를 줬을 뿐, published *span* (D-071 의 "2.5×~13×")
  은 어떤 band 로도 채점된 적이 없다.

## Q-080 — 2026-08-05 — `[meta]` guard pool 의 "exactly N" 은 **guard 의 수**인가 **보이게 철자된 guard 의 수**인가

- **Question**: D-073 이 같은 guard·같은 registry·같은 `in` sense 를 두 철자로 측정했다 —
  `A + B` 면 pool 54, `tuple(A + B)` 면 55. `_is_set_valued` 는 module constant 의
  **initializer 형태**를 읽는다. D-065/D-066/D-072 가 각각 다른 설명을 붙였던 recurrence 는
  이제 하나로 모인다: detector 는 syntax 를 읽는다. 그렇다면 D-048 이후 열여덟 cycle 이
  들고 온 23 → 56 의 모든 중간값은 *그 시점에 보이게 철자돼 있던* guard 의 수다.
- **Trade-off**: (a) **detector 를 값 기준으로 고친다** — module constant 를 실제로
  평가(또는 상수 폴딩)해서 set-valued 인지 본다. 정확해지지만 import side-effect 를
  실행하게 되고, AST-only 라는 이 scan 의 저비용 성질을 잃는다.
  (b) **static 하게 넓힌다** — `BinOp(Add)` 양변이 set-valued constant 면 결과도 그렇다고
  본다. 싸고, `A + B` 를 잡고, `A + f()` 같은 건 여전히 놓친다.
  (c) **못 고치고 선언한다** — pin 의 N 을 "visible guards" 로 개명하고, 놓치는 형태를
  D-038 식으로 명시. 정직하지만 숫자의 쓸모가 줄어든다.
- **Lean**: (b) 먼저, 그 다음 (c). (b) 는 반나절짜리고 이번 cycle 이 만든 실제 miss 를
  잡는다. 그런데 (b) 를 하고 나면 **얼마나 늘어나는지가 그 자체로 답** — 늘어난 수가
  0 이면 이 blind spot 은 이론적이고, 3 이상이면 지금까지의 모든 N 이 짧았다는 뜻.
- **다음 action**: package 전체에서 `NAME = A + B` 꼴 module constant 를 찾아 `in`/`not in`
  filter 의 피연산자로 쓰이는 것만 세는 static scan. sim 불필요, 1 cycle.

---

## Q-078 — 2026-08-05 — `[uncertainty]` 판정을 **stationarity (클래스)** 대신 **gap/control 비율 (연속량)** 위에 세울 것인가

- **Question**: D-071 이 Q-077 의 두 lean 을 모두 소거했다 — 0-문턱은 k 가 커지면 도달
  불가능해지고, band 문턱은 band 자체가 같은 frame 안에서 7.7× 흩어져 살 수 없다. 남은
  관측: 네 tree 에서 **magnitude 는 하나도 재현되지 않았는데 *순서*는 재현됐다**.
  `gap / max(frame movement)` 는 이 batch 에서 `_pure` 2.5× (214/87) ~ `_is_set_valued`
  13× (13/1) 로 퍼져 있다. 클래스를 발행하지 말고 이 비율의 **분포를 보고**해야 하는가?
- **Trade-off**: (a) **비율 분포 보고** — 문턱이 없으므로 정당화할 상수가 없고, 네 tree 에서
  재현된 유일한 구조(순서)를 직접 읽는다. 대신 "fold 가 범인이다"라는 **이산 판정을 포기**
  하고, 독자가 스스로 선을 긋게 된다 — 즉 문턱을 없앤 게 아니라 **미룬** 것일 수 있다.
  (b) **현행 클래스 유지** — 읽기 쉽지만 D-071 이 셋 다 죽었음을 측정했다.
  (c) 비율에 문턱 — (b) 의 결함을 이름만 바꿔 다시 만든다.
- **Lean**: (a). 단 **비율의 재현성 자체가 아직 미측정**이다: 네 tree 의 순서 재현은
  eyeball 이지 통계가 아니고, 분모(`max(frame movement)`)는 D-071 이 방금 7.7× 흔들린다고
  보고한 바로 그 양이다. 분모가 흔들리면 비율도 흔들린다.
- **다음 action**: 새 run 없이 시작 — D-066..D-071 의 네 tree 산출물에서 site 별 비율을
  뽑아 **순위 상관**을 계산한다. 상관이 없으면 (a) 도 죽고, 이 잔차는 4 cycle 째 설명되지
  않은 채로 남는다는 게 결론이 된다. Executor, static, no sim.
- **Status**: `partially-answered → D-072`. 채점기는 지어졌고 (문턱 없음, (a) 대로), 정적
  절반은 **음성으로 닫혔다**: licensed reading 이 둘뿐이고 공통 site 는 **2** 개 (문턱 3),
  두 frame 분모로는 **0** 개. 그리고 D-071 이 근거로 든 "네 tree 에서 재현된 순서"가 바로
  그 두 site 의 순서였다 — 한 쌍은 정의상 재현된다. (a) 는 죽지 않았지만 **아직 한 번도
  검사된 적이 없다**. 남은 절반은 STATE #3 (per-site artifact 직렬화) 에 차단.

## Q-079 — 2026-08-05 — `[uncertainty]` ratio 의 분모는 **exclusion frame 단독**인가 **두 frame 의 합**인가

- **Question**: D-072 의 `RatioGrade.control` 은 `measured_delta + source_delta` — D-068 이
  자기 noise budget 을 두 frame 합으로 셈한 전례를 따랐다. 그런데 D-071 이 (c) 의 근거로
  인용한 2.5×~13× 는 **exclusion frame 단독** 분모다. 두 수는 같은 site 를 다르게 순위
  매길 수 있고, published record 는 **단독 분모만** 인쇄했으므로 (source frame control 은
  어느 tree 에서도 0 건) 지금까지 인용된 모든 비율은 후자로 검산할 방법이 없다.
- **Trade-off**: (a) **두 frame 합** — fold 는 각 frame 에서 run 을 하나씩 읽으므로 두 run
  이 흔들릴 수 있다는 게 D-068 이 확립한 사실. 보수적이고, gap 을 넘기 더 어렵게 만든다.
  (b) **exclusion frame 단독** — 지금까지 인쇄된 모든 비율과 호환되고, gap 의 우변이 바로
  그 frame 이라 인과적으로 더 직접적이다. 대신 좌변(attributed run)의 재현성을 무시하는데,
  그건 D-067 이 저질러 D-068 이 고친 바로 그 실수다.
- **Lean**: (a), 근거는 D-068 의 전례. 다만 **양쪽 다 보고**하는 게 지금은 더 정직하다 —
  둘이 순위를 다르게 매기는지가 아직 미측정이고, 그 자체가 값싼 발견이다.
- **다음 action**: 다음 licensed batch 를 직렬화할 때 두 분모의 ranking 을 **모두** 기록하고
  `rank_agreement` 로 서로 비교한다. run 을 새로 사지 않는다 — 이미 사는 run 에 붙는다.

## Q-077 — 2026-08-05 — `[uncertainty]` `FOLD_IMPLICATED` 의 문턱을 **정확히 0 이동** 에서 frame 의 측정 band 로 바꿀 것인가

- **Question**: `attribute_two_frame` 은 두 frame 이 **정확히** 정상적일 때만 fold 를
  지목한다. D-070 에서 `_is_set_valued` 의 exclusion frame 이 **2** (약 9600 중) 움직였고,
  그 하나로 D-068 의 판정이 뒤집혔다. 0.1 % band 를 가진 측정에서 "이동 = 0" 은 유일하게
  살아남을 수 없는 문턱이다. band 기준(예: 이동 ≤ frame 의 `drift_band` × 해당 site 크기)
  으로 바꿔야 하는가?
- **Trade-off**: (a) **정확히 0 유지** — 정당화가 필요 없고 해석이 명확하지만, 판정이
  1~2 카운트에 뒤집히고 실제로 세 cycle 이 그 bit 위에서 논쟁했다. (b) **band 기준** —
  측정의 실제 noise 를 반영하지만, band 자체가 **한 쌍**에서 나온 추정이고 (D-067 이 이미
  경고한 "one pair is one sample"), 문턱을 고르는 순간 STATE #21 이 `wilson_lower_at_least`
  에 대해 아직 들고 있는 **정당화 없는 floor** 결함을 새로 하나 만든다.
- **Lean**: (b) 쪽으로 기운다 — 단, band 를 **단일 쌍이 아니라 반복된 batch** 에서
  추정한 뒤에. D-070 의 batch 는 frame 당 쌍이 하나뿐이라 지금은 (b) 를 살 수 없다.
  그 전까지는 `FOLD_IMPLICATED` 을 **판정이 아니라 후보** 로 읽는 게 정직하다.
- **다음 action**: `paired_reading` 을 frame 당 k 쌍으로 일반화 (k=3 이면 12 run, ~20 분
  동시 실행) → band 의 분포를 얻고 나서 문턱을 정한다. Executor, static, no sim.
- **Status**: **resolved → D-071 — 단, 답이 아니라 양쪽 소거**. 세 군데가 예상과 다르다.
  (1) 비용은 12 run 이 아니라 **6** 이다: k run 에서 pair 는 C(k,2) 이므로 frame 당 k 쌍을
  사려고 2k run 을 살 필요가 없다. (2) **(a) 가 죽는다** — k=3 에서 어느 frame 에서도
  정확히 반복되는 site 가 없어 `FOLD_IMPLICATED` 은 도달 불가능해진다. 0-문턱은 k 가
  커지면 엄격해지는 게 아니라 **발행되지 않는다**. (3) **(b) 도 죽는다** — 같은 frame·
  같은 tree·같은 batch 의 세 pair band 가 **0.519 / 0.068 / 0.487 %** (7.7×) 로 흩어져,
  추정치의 흩어짐이 문턱이 가를 차이보다 크다. 남는 후보는 Q-078 (비율 통계).

## Q-076 — 2026-08-04 — `[meta]` exclusion 을 `--ignore` 대신 **관측 시점의 nodeid 필터**로 바꿔서 subject 단위로 만들 것인가

- **Question**: D-063 은 file 단위 exclusion 이 subject 를 넘어 숨긴다는 것을 측정했고,
  보정치를 **두 번째 reading** 으로 발행했다 (census 자신의 수는 자기가 선언한 suite 에 대해
  정직하므로 합치지 않음). 하지만 recorder 는 이미 pytest 안에서 돈다 — 관측마다
  **실행 중인 test 의 nodeid** 를 같이 기록하면 exclusion 은 run-time `--ignore` 가 아니라
  classify-time 필터가 되고, "이 파일은 이 모듈의 predicate 에 대해서만 안 보인다" 가
  구조적으로 표현된다.
- **Trade-off**: (a) 현행 유지 — 정직하지만 보정에 **5 회** suite 실행이 든다.
  (b) nodeid 기록 + classify 필터 — **1 회** 실행으로 끝나고 `SELF_ENTRY` 가 파일명 규약이
  아니라 파생이 된다. 대신 recorder 가 커지고 (관측 slot 당 문자열 집합), 과거 reading 과
  숫자가 비교 불가능해진다. (c) `EXCLUDED_TESTS` 를 `(file, module)` 쌍으로 손으로 좁힘 —
  이 package 가 D-045~D-052 에서 계속 틀렸던 **여섯 번째 hand-written registry**.
- **Lean**: **(b)**. nodeid 는 plugin 이 이미 접근 가능하고, 5→1 회는 이 계측기를 CI 에
  올릴 수 있는지를 가르는 차이다. 다만 (b) 는 D-063 의 측정이 **먼저 존재해야** 검증
  가능하다 — 필터로 재현한 수가 lift 로 측정한 수와 같아야 하므로, (a) 가 (b) 의 calibration 이다.
- **다음 action**: 다음 cycle. `_PLUGIN_RECORD_VALUES` 에 nodeid slot 추가 → classify 에
  `hidden_for(module)` 필터 → D-063 의 `manufactured_candidates` 2 건을 1 회 실행으로 재현.
- **Status**: **resolved → D-064** (lean (b) 채택, 실행됨). 예상과 두 군데 다르다.
  (1) 비용은 5 회가 아니라 **6 회**였고 한 회가 5 분이라 (a) 는 30 분 — (b) 를 "있으면 좋은
  최적화" 가 아니라 **유일하게 실행 가능한 경로**로 만든다. (2) "(a) 가 (b) 의 calibration"
  이라는 전제는 절반만 맞았다: (a) 를 통째로 돌릴 필요는 없고 **base 한 회**면 충분하며
  (`reconstruction_disagreements`, 불일치 0/62), 그렇게 아낀 덕분에 (b) 가 D-063 의 귀속
  자체를 반증할 수 있었다 — (a) 를 먼저 완주시켰다면 같은 답을 30 분에 얻었을 것이다.
  남은 조각: `SELF_ENTRY` 는 여전히 **파일명 규약**이다 (origin 은 파일이지 subject 가 아님).
  파생으로 만드는 것은 별도 질문으로 남는다.

## Q-075 — 2026-08-04 — `[meta]` fingerprint 이 **읽을 수 없는 인자 클래스**를 만나면 순위에서 빼야 하는가, 아니면 그 클래스를 읽게 만들어야 하는가

- **Question**: D-062 의 편향 선언은 "address repr 은 distinct 를 과대계상하므로
  `SINGLE_INPUT` 은 강하다" 였다. 측정해 보니 그 편향이 **정확히 최상위 후보**에서
  발동했다 — `_shells_out_to_git_diff` 는 5694 calls / **2944 distinct** 인데 인자가
  AST 노드라 인스턴스마다 다른 repr 을 갖는다. 즉 2944 는 "질문 2944 개"가 아니라
  "객체 2944 개"일 수 있고, 진짜 distinct 는 1 일 수도 2944 일 수도 있다. 47 개
  `MANY_INPUTS` 중 **9 건**이 같은 상태다. 지금 계측기는 이 9 건을
  `informative=False` 로 **표시**만 하고 여전히 순위에 넣는다.
- **Trade-off**: (a) 판독 불가 클래스를 순위에서 **제외** — 정직하지만 최상위 후보가
  목록에서 사라져 D-061 이 24 cycle 동안 앞세운 site 에 대해 아무 말도 못 하게 된다.
  (b) AST 노드에 **값 기반 fingerprint** (`ast.dump`) 를 준다 — 이 tree 에서는 통하지만
  다음 판독 불가 타입이 나오면 같은 문제가 반복되고, 타입별 특례는 이 package 가 아홉
  cycle 내리 틀렸던 hand-written registry 의 shape 다. (c) 현상 유지 — 표시하되 순위
  유지. 독자가 플래그를 무시하면 D-061 의 오류가 그대로 재생산된다.
- **Lean**: (b) 를 **일반형으로**. 타입 목록이 아니라 "값 기반 `__repr__`/`__eq__` 가
  있는가" 를 실행으로 물어 없으면 표준 직렬화(`ast.dump`, `dataclasses.asdict`)로
  내려가는 fallback 사다리. 특례가 이름이 아니라 **능력**에서 나온다.
- **다음 action**: `guard_is_derived` witness 다음. static, sim 불필요.

---

## Q-074 — 2026-08-04 — `[meta]` vacuity scan 이 닿아야 할 population 에 **test 자신**이 들어가는가 — D-057 의 인스턴스는 거기 산다

- **Question**: `guard_vacuity` 와 `predicate_vacuity` 는 둘 다 `tests/` 를 population
  에서 뺀다 — "test 안의 predicate 는 그 test 의 assertion 기계지 subject 가 아니다".
  그런데 이 탐색을 촉발한 네 findings 중 가장 값비쌌던 D-057 (`unseen.min() > 0.0` 가
  renderer 바닥 위에 앉아 빈 world 에서도 통과) 은 **정확히 test 안의 assertion** 이다.
  그래서 D-061 의 calibration set 이 0 이다: shape 에는 닿았는데 instance 에는 못 닿는다.
  **절대 실패할 수 없는 assertion** 은 이 defect 의 가장 순수한 형태인데, 지금 두 scan
  모두 그것을 구조적으로 못 본다.
- **Trade-off**: (a) test 를 population 에 넣는다 — D-057 을 잡지만 기계가 다르다.
  pytest 가 assert 를 rewrite 하므로 `assert <expr>` 의 값 분포를 읽으려면 wrapping 이
  아니라 assertion-rewrite hook 이나 별도 AST 변환이 필요하고, "이 assert 는 항상 참"
  은 **통과한 test 전부**에 대해 참이라 신호가 아니다 — 신호는 *조건이 scene 에 의존해야
  하는데 안 하는* 경우뿐이라 population 정의가 자명하지 않다. (b) subject 만 유지하고
  calibration 0 을 명시 — **현재 상태**, 정직하지만 가장 값비싼 defect class 를 방치.
  (c) 중간 — assert 가 아니라 **test 안에서 호출되는 subject predicate 의 인자 분포**를
  본다 (`grid_unseen` 이 항상 같은 scene 집합에서만 불렸는가). 기계는 이미 있다.
- **Lean**: (c). (a) 의 population 문제를 피하면서 D-057 을 실제로 잡는다 — D-057 의
  진짜 결함은 bar 자체가 아니라 bar 가 **한 종류의 scene 에서만** 평가된 것이었다.
- **다음 action**: 남은 6 후보를 witness 로 triage 한 다음. static, sim 불필요.

**Status: partially-answered → D-062 (분기 (c)).** (c) 를 구현해 측정했다:
인자 분포는 D-061 의 순위를 **3/7** 에서 바꾸지만 **head 는 안 바꾼다**. one-sided
∧ single-input 은 **2 건**이고 둘 다 이미 `n=1` 이라 신규 정보가 없다. 신뢰 가능한
신규 후보는 `local_only_audit.guard_is_derived` (26 calls / 2 distinct) **1 건**.
calibration 은 더 이상 0 이 아니다 — 구성된 `recited_bar` 가 50 calls / 1 distinct
로 D-057 의 shape 을 담는다. **다만 (c) 는 (a) 를 대체하지 못했다**: D-057 의
*instance* 는 여전히 test 안에 있고, 이번에 닿은 것은 subject 쪽 인자 분포뿐이다.
판독 불가 인자 클래스 문제는 **Q-075** 로 분리.

---

## Q-073 — 2026-08-04 — `[meta]` 정적 reachability 는 **먼저 raise 하는 호출**을 sim bill 에 청구한다

- **Question**: `default_lam_sites.simulates` 는 call-graph 도달성이라
  `_w_batch_per_unit_spread` 처럼 simulating 함수를 부르지만 인자 검증에서
  `KeyError` 로 즉시 빠져나오는 호출도 "controller 를 step 한다" 로 센다. 그래서
  `weighting_at_shipped` 가 **53** 으로 읽히지만 실제 re-run 해야 할 site 는 **52**.
  D-042 의 sim bill 이 곧 이 숫자다 — 1 건이 작지만, 규칙이 없으면 계속 는다.
- **Trade-off**: (a) 손으로 관리하는 exemption 목록 — 싸지만 이 package 가 아홉 cycle
  내리 틀렸던 hand-written registry 바로 그 shape. (b) detector 에게 "guard clause 가
  선행하면 도달 불가" 를 가르친다 — `guard_vacuity` 가 이미 AST 로 guard clause 를
  뽑으므로 재료는 있으나, "인자 검증이 *항상* 먼저 터진다" 는 호출 인자에 달린 문제라
  일반해가 없다. (c) 아무것도 안 하고 pin 에 두 숫자를 병기 — **현재 상태**.
- **Lean**: (b) 의 축소판 — "이 호출은 도달 불가" 를 **witness 가 증명**하게 한다.
  `guard_witness` 는 이미 그 호출이 raise 함을 실행으로 보이고 있으므로, detector 가
  witness 를 읽으면 exemption 이 손이 아니라 **실행**에서 나온다.
- **다음 action**: Q-072 (b) 다음. sim 불필요, static.

---

## Q-072 — 2026-08-04 — `[meta]` guard **clause** 가 애초에 옳은 population 인가 — 손으로 찾은 넷 중 셋은 raise 하지 않는다
**Status: resolved → D-060 (분기 (a), 음성).** 남은 5 건을 읽는 대신 8 건 전부에 witness 를
구성해 실행했다: **8/8 SATISFIED, `unwitnessed() == ()`, D-058 shape 0 건.** guard clause
population 은 **닫혔고 수확은 0**. 등급은 `DATA_REACHABLE` 5 / `ARGUMENT_ONLY` 3 —
D-059 가 손으로 "미테스트 인자 검증" 이라 부른 것에 기준이 붙은 형태. 따라서 lean 대로
**(b) 로 넘어간다**, 그리고 그 사전확률은 이번 결과가 정한다: 촉발 finding 4 건 중 3 건이
(b) 쪽에 살고 (a) 쪽 수확은 측정된 0 이다.
**(b) 수행 완료 → D-061**: boolean 반환 함수 **59** 중 one-sided **7** — guard 절 쪽과
달리 후보 집합이 비어 있지 않다. 다만 최상위 후보(5694 호출 전부 False)는 witness 로
**satisfiable** 임이 드러나 vacuous 가 아니라 미테스트 arm 이었다. 남은 잔여 질문은
Q-074 (test 표면).

- **Question**: D-059 가 `if <cond>: raise` 38 건을 census 해 candidate 8 건을 냈고,
  손으로 triage 한 3 건 중 **0 건**이 D-058 의 shape 이었다. 반면 이 탐색을 촉발한 네
  findings 중 **셋** (D-055 fixture reading, D-056 verdict 비교, D-057 boolean bar) 은
  raise 하지 않고 **return** 한다. 수확이 있는 자리는 raise 가 아니라 predicate 쪽인가?
- **Trade-off**: (a) 남은 5 candidate 를 마저 triage — 싸고, 유한하고, D-059 의 숫자를
  닫는다. 다만 3/3 이 미테스트 인자 검증이었으므로 기대 수확은 낮다. (b) scan 을
  non-raising predicate (boolean property, 비교를 return 하는 함수) 로 확장 — findings
  3/4 가 사는 자리지만, "trigger 가 발생할 수 없다" 를 raise 없이 정의하는 방법이
  자명하지 않다. raise 는 관측 가능한 사건이라 coverage 한 줄로 읽히는 반면, predicate
  는 **반환값의 분포**를 봐야 하고 그건 다른 계측기다.
- **Lean**: (b) 쪽이 값어치가 크되 (a) 가 먼저다 — 5 건은 한 cycle 안에 끝나고, 그
  결과가 (b) 의 사전확률을 정한다. 만약 5/5 도 미테스트 검증이면 guard clause 라는
  population 은 **닫힌 것으로 선언**하고 predicate 로 넘어간다.
- **다음 action**: 다음 cycle 이 (a) 를 수행하고 그 자리에서 이 Q 에 답한다. static,
  sim 불필요.

---

## Q-071 — 2026-08-04 — `[uncertainty]` D-057 의 바닥을 빼야 하는 site 가 `reach.py` 말고 또 있는가 — `weight_units` 의 guard 는 못 터진다
**Status: resolved → D-058.** lean (b) 대로 오염을 먼저 측정: 렌더하는 5개 장면 전부 바닥이 **112 셀로 동일**,
비율 41.8~**100.0%** (`cafe_head_on_v0` 는 scene 셀 0개 — batch 전체가 렌더러 기하 위였다).
그 다음 (a) 로 고침. 청구서는 margin knob per-unit spread 비 **2.568 → 2.717** 하나뿐이고
결론(비가법적)은 불변. guard 는 이제 발동 가능하며 head-on 에서 터지는 것이 test 로 고정됐다.

- **Question**: D-057 은 `grid > UNSEEN_SIGMA` 를 **장면의 그림자**로 읽는 모든 site 에 해당한다.
  코드베이스에 그런 site 는 3곳이고, 이번 cycle 은 그중 1곳(`reach.grid_unseen`)만 고쳤다.
- **측정된 것**: `critics/observation_value.py:120` 은 `(grid > 0.5) & (d_robot <= producer.r_sense)`
  로 **이미** 사거리 밖 모서리를 걸러낸다 — 면역이고, 기제를 알던 작성자가 최소 한 명 있었다는 증거다.
  `weight_units.py:336` 의 `sel = grid > 0.5` 는 걸러내지 않는다. 바로 아래
  `if not sel.any(): raise ValueError("no shadow cells in this BEV — pick another pose")` 는
  바닥이 `> 0` 이므로 **호명된 이유로 절대 발동할 수 없다** — D-057 이 gate test 에서 고친
  `unseen.min() > 0.0` 과 **같은 형태**, 이번엔 guard clause 에서.
- **Trade-off**: (a) `weight_units` 도 사거리로 거른다 — 하지만 그 함수는 probe *궤적*을 만들고,
  모서리 셀로 만든 궤적이 지금까지의 weight-unit 측정에 얼마나 섞여 있었는지가 **미측정**이라
  고치면 기존 수치가 움직일 수 있다. (b) 먼저 오염량부터 측정하고 고친다.
- **Lean**: **(b)**. D-057 이 고친 것은 판정이지 측정치가 아니었고(숫자는 안 움직였다), 여기는 반대다 —
  선택된 셀이 곧 입력이므로 고치는 순간 수치가 바뀐다. 얼마나 바뀌는지 모르고 고치면
  D-046 이 반복된다: 우연이 자리를 지키고 있었는지조차 모르게 된다.
- **다음 action**: 다음 cycle. `weight_units._shadow_trajectory` 가 고르는 셀 중 `d_robot > r_sense`
  비율을 장면별로 측정 → 0 이면 (a) 는 무해한 정리, 양수면 그 크기가 재보정 청구서다. sim 불필요.

## Q-070 — 2026-08-04 — `[meta]` fixture 가 **살아 있는 repo 를 복사**한다. 읽기가 오늘의 저장소 내용의 함수여도 괜찮은가

- **Question**: `probe_reach.build_enriched_repo` 는 실제 `docs/` 와 `scripts/` 를 그대로
  복사해 넣는다. D-055 는 그 결과 `unregistered_local_only` 가 **어떤 행위 이전에** 이미 2 를
  읽는다는 것을 측정했고, membership 기준이 그 오탐을 잡아냈다. 하지만 기준을 고친 것은
  *판정*이지 *fixture* 가 아니다. 남는 질문: fixture 의 읽기가 저장소가 오늘 담고 있는 내용에
  따라 달라져도 되는가 — 즉 `docs/decisions.md` 에 한 entry 를 더 쓰는 것만으로 어떤 guard 의
  before-읽기가 바뀌는 상태를 유지할 것인가.
- **Trade-off**: (a) **복사 유지** — fixture 가 실물과 같은 모양이라 guard 가 실제로 읽는
  구조(중첩된 md, 실제 verb 어휘)를 그대로 만난다. 대신 before-읽기가 재현 불가능하고, 어떤
  수치도 "그날의 저장소" 위에서만 참이다. (b) **합성 fixture** — 최소한의 `docs/`/`scripts/`
  를 손으로 지어 넣는다. 재현 가능하고 before 가 알려진 값이지만, 손으로 쓴 또 하나의 population
  이고 D-045/D-047 이 반복해서 찾아낸 바로 그 모양이다 (실물이 자라면 조용히 뒤처진다).
- **Lean**: 약하게 (a) + **before-읽기를 기록**. D-055 이후 판정은 이미 fixture 의 소음에
  면역이므로 (b) 의 이득은 재현성뿐인데, 그 재현성은 `Liveness.before` 를 남기는 것으로 훨씬
  싸게 얻어진다 — 실제로 이번 cycle 에 그 필드를 넣었다. (b) 로 가면 fixture 자체가 mirror 를
  필요로 하는 새 registry 가 된다.
- **다음 action**: 복사되는 두 surface 위에서 before-읽기가 non-empty 인 guard 가 몇 개인지
  센다 (DERIVED 4 개는 이미 알고 있다 — 1 개). 그 수가 1 이면 (a) 로 확정하고 Q 를 닫는다.
  여러 개면 그 population 위에서 (b) 의 비용을 다시 잰다. 값싸고 sim 불필요.

---

## Q-069 — 2026-08-04 — `[meta]` liveness 의 **네 번째 부분** — population 자신의 창 — 은 9 개 `NO_REGISTRY` 중 몇 개의 진짜 병목인가

- **Question**: D-054 는 liveness 행위를 `(scope, membership, subject)` 삼중항으로 파생하고
  16 중 4 를 얻었다. 그런데 `pre_epoch_commits` 는 삼중항을 다 갖고도 죽어 있다 — population 이
  `origin/main..<ref>` 위 `--until=<epoch>` 로 잘리기 때문이고, 이 조건은 `acts_of` 에도
  `Exemption` 에도 없다. census 는 나머지 9 개를 전부 layer 2(`NO_REGISTRY`) 에 귀속시켰는데,
  그 중 몇은 registry 가 없어서가 아니라 **창이 없어서** 안 깨어나는 것일 수 있다. 귀속이
  틀렸다면 4/16 은 파생 가능성의 상한을 과대평가한 것이다 (혹은 병목의 위치를 잘못 짚은 것).
- **Trade-off**:
  (a) 9 개에 대해 registry 를 **손으로 공급**하고 그래도 죽는지 본다 — 귀속을 실측으로
      가르지만, 손으로 공급한 registry 자체가 D-045 형태의 새 표가 된다.
  (b) `Guard.population` / `population_kind` 에서 창(시간 범위, ref 위상)을 **파싱**해 네 번째
      부분을 파생 대상에 추가한다 — 일관되지만, D-054 가 방금 잰 것처럼 파생 층을 하나 더
      늘려도 순증이 1 근처일 수 있다.
  (c) 귀속을 **`UNATTRIBUTED` 로 표시**하고 census 를 그대로 둔다 — 9 를 "layer 2 에서 탈락"
      이 아니라 "layer 2 **이상**에서 탈락" 으로 정직하게 약화.
- **Lean**: (c) 를 즉시, (a) 를 표본 2 개로. (c) 는 D-054 의 census 가 지금 실제보다 강하게
  읽히는 것을 0 비용으로 고친다. (a) 는 전수 대신 2 개만 해도 귀속이 대략 어느 쪽인지 가르고,
  9 개 전부에 표를 쓰는 비용을 치르지 않는다. (b) 는 (a) 의 결과가 "창이 병목" 으로 나올 때만.
- **다음 action**: 다음 instrument-lane cycle. (c) 를 census 에 반영하고, `NO_REGISTRY` 9 개
  중 2 개를 골라 registry 를 손으로 공급한 뒤 실행 — 깨어나면 귀속이 맞고, 안 깨어나면 네 번째
  부분이 진짜 병목이다.
- **Status**: open

---

## ~~Q-068~~ — 2026-08-04 — `[meta]` probe 의 liveness 행위를 `acts_of` 에서 **파생**할 수 있는가, 아니면 손으로 쓸 수밖에 없는가

- **Question**: D-053 은 `guard_direction` 의 reach 가 결국 손으로 쓴 `Probe.liveness` 표
  (**2** 개) 에 묶여 있음을 측정했다. 그런데 `guard_reflexivity.acts_of` 는 이미 각 guard 가
  감시하는 git / filesystem **동작**을 scope (`WORKTREE`/`INDEX`/`COMMIT`/`NAMESET`) 까지
  붙여 열거한다 (D-049). liveness 행위란 "그 guard 가 잡도록 되어 있는 act 를 실제로 수행하는
  것" 이므로, 표기(表記)상으로는 같은 지식이다. 파생 가능한가?
- **Trade-off**:
  (a) `PROBES` 를 reach gap 의 6 개만큼 손으로 늘린다 — 즉시 되고, D-052 가 지목한 typed-table
      우연을 3 배로 키운다. 다음 cycle 이 "이 8 개는 왜 없나" 를 또 묻게 된다.
  (b) `acts_of` 에서 act 를 읽어 실행 가능한 행위로 **컴파일**한다 — 표가 파생되므로 새 guard 가
      probe 없이 들어오는 일이 원리적으로 사라진다. 다만 `acts_of` 는 *어떤 subcommand 를
      부르는가*를 알지 acts 의 **인자**(어느 경로를 stage 할 것인가)를 모른다. 그 절반은 여전히
      fixture 지식이고, D-053 이 이미 fixture 를 넓히는 길(`build_enriched_repo`)을 냈다.
  (c) 파생 불가로 확정하고, 대신 `reach_gap` 을 **깨지는 mirror** 로 승격해 새 readable guard 가
      probe 없이 들어오면 test 가 붉어지게 한다 — 표는 손으로 쓰되 누락은 조용할 수 없게.
- **Lean**: (b) 를 시도하되 (c) 를 먼저 깐다. (c) 는 이번 cycle 의 test 로 사실상 반쯤 서 있고
  (`test_reach_gap_is_the_mirror_unprobed_revocable_could_not_be`), 비용이 0 에 가깝다. (b) 의
  진짜 질문은 "act 의 인자까지 파생되는가" 이고, 그건 D-053 의 fixture 확장이 답의 절반을
  이미 갖고 있다 — declared local-only 경로 5 개는 `DECLARED_LOCAL_ONLY` 에서, 읽기 표면은
  `READ_SURFACES` 에서 파생된다. (a) 는 명시적으로 기각: D-052 가 우연이라 부른 것을 늘리는 일.
- **다음 action**: 다음 instrument-lane cycle. `acts_of` 가 뱉는 `Act.key()` 를 실행 가능한
  callable 로 옮길 수 있는 비율을 먼저 **재고**, 그 비율이 낮으면 (c) 에서 멈춘다 — D-052/D-053
  의 규율대로 도구의 적용 가능성을 도구를 쓰기 **전에** 측정한다.
- **Status**: `resolved → D-054, 수치 D-055 로 정정` — 비율은 **4/16** (census), 실행하면
  ~~3/16~~ → **2/16**, typed 표 대비 순증 ~~1~~ → **0**. lean 이 정한 문턱대로 (c) 에서 멈춘다.
  그리고 lean 의 예측 하나가 틀렸다: 어려운 절반은 act 의 *인자*가 아니라 애초에 registry 를
  지목하는 exemption 이 **9 개에서 없다는 것** 이었고, `acts_of` 가 대는 층(scope)은 16/16 으로
  한 번도 병목이 아니었다. D-055: 순증 1 은 liveness 판정이 non-empty 였던 탓의 오탐이었고,
  membership 으로 고치면 살아남는 것은 손으로 쓴 그 둘뿐이다 — 파생의 순수 수확은 **0**.

---

## ~~Q-067~~ — 2026-08-04 — `[meta]` `_provenance` 도 same-module call 을 따라가야 하는가 — **따라가지 않는 것이 옳다** — **resolved → D-052 (b)**

- **Question**: D-051 이 잰 가장 값비싼 불일치는 (`_is_set_valued`, `_provenance`) 다 — 같은 `right` 를
  받는데 4/6 rung 에서 갈린다. 결과: helper 를 거쳐 도달하는 hand-typed registry 는 guard 로 admit 되지만
  `DERIVED` 로 분류되어 `typed_exemptions` / `bite` / `unwatched_exemptions` 모두에서 사라진다.
  HEAD 에서 노출은 **0** (`provenance_depth_exposure()`), 즉 지금은 잠재적이다. 그런데 D-050 이 다섯
  cycle 연속 처방한 "중복 registry 를 helper 로 추출" 이 정확히 이 수를 양수로 만든다.
- **Trade-off**: (a) `_provenance` 에 `_is_set_valued` 가 받은 same-module-call arm 을 준다 —
  두 술어가 일치하고 노출이 닫히지만, `DERIVED` 의 의미가 "call 을 거친다" 에서 "끝까지 따라가도 typed 가
  아니다" 로 바뀐다. `glob → set` 처럼 *진짜* derive 된 population 이 typed constant 를 경유하기만 해도
  `TYPED` 로 재분류될 위험. (b) 안 따라가는 것이 옳다고 **코드에 명시** 한다 — provenance 는 "이 자리에
  무엇이 쓰여 있나" 를 묻는 구문적 질문이고, 한 frame 아래는 다른 질문이다. 그러면
  `provenance_depth_exposure()` 가 0 이 아니게 되는 순간이 **경고** 지 결함이 아니게 된다.
  (c) 아무것도 안 한다 — 0 이니까.
- **Lean**: **(b)**. `_is_set_valued` 는 "이것이 집합인가" 를 묻고 그 답은 frame 을 넘어 보존되지만,
  `_provenance` 는 "이 exemption 이 손으로 타이핑된 registry 인가" 를 묻고 그 답은 보존되지 **않는다** —
  helper 뒤에 숨은 registry 는 실제로 다른 감사 대상이다. 다만 (b) 를 택하면 exposure 를 0 으로 두는 것이
  아니라 **양수일 때 무엇을 해야 하는지** 를 같이 적어야 한다.
- **다음 action**: STATE #2 (`TYPED` exemption masking screen) 이 이 질문을 지나갈 수밖에 없다 —
  그 cycle 이 (a)/(b) 를 고르고 D-NNN 으로 승격한다.
- **Status**: **resolved → D-052, (b) 채택.** 두 술어는 다른 질문을 받는다: `_is_set_valued` 의
  "이것이 집합인가" 는 값의 성질이라 frame 을 넘어 보존되고, `_provenance` 의 "이 exemption 이 손으로
  타이핑된 registry 인가" 는 **호출 지점의 성질**이라 보존되지 않는다. 따라가면 진짜 derive 된
  population 이 typed constant 를 경유만 해도 `TYPED` 로 재분류된다 — screen 이 조용히 넓어지는
  틀린 방향. Lean 이 요구한 의무도 이행: exposure 가 양수가 되면 할 일은 **helper 의 registry 를
  호출 지점에서 이름 붙이는 것**이지 술어를 넓히는 것이 아니라고 `_provenance` 와
  `provenance_depth_exposure` 양쪽 docstring 에 적었고 test 로 고정했다. HEAD 에서 exposure 는
  여전히 `()` 지만 **값은 커졌다** — D-052 의 masking screen 이 정확히 그 12 개 TYPED pair 를
  population 으로 쓰므로, `DERIVED` 로 미끄러진 exemption 은 masking screen 에서도 사라진다.

## Q-066 — 2026-08-04 — `[meta]` 한 scan 안의 술어들이 같은 식을 **같은 깊이** 로 읽는가

- **Question**: D-050 은 `_is_set_valued` 가 같은 module 의 call 을 안 따라가고 `_difference_kind`
  는 따라간다는 것을 발견했다 — 두 술어가 같은 식을 다른 깊이로 읽었고, 그 불일치가 ~30 cycle 동안
  guard 2개를 population 밖에 두고 있었다. `guard_reflexivity` 에는 식을 해석하는 술어가 더 있다
  (`_provenance`, `_enclosing_population`, `core_name`, `_resolve` 의 depth=3). 이들의 해석 깊이는
  서로 일치하는가, 아니면 D-050 이 하나만 우연히 발견한 것인가?
- **Trade-off**: (a) 깊이를 하나의 상수로 통일하고 전부 그것을 쓰게 한다 — 값싸지만 술어마다 옳은
  깊이가 다를 수 있다 (`_resolve` 의 3 은 alias chain 용, `_difference_kind` 의 2 는 call frame 용).
  (b) 술어 쌍마다 **같은 식에 대해 답이 갈리는 사례** 를 찾는 meta-test — 정확하고 D-050 을 재현
  가능하게 만들지만, 반례를 생성해야 하므로 어휘를 사람이 짜야 한다. (c) 안 한다 — D-050 을 단일
  사례로 둔다.
- **Lean**: **(b)**, 그리고 D-050 의 사례 자체를 첫 fixture 로 쓴다 (`test_set_valuedness_follows_same_module_calls`
  가 이미 그 형태다). (a) 는 술어별 깊이의 근거를 지우므로 기각 쪽.
- **다음 action**: 다음 instrument cycle. 술어 목록을 손으로 쓰지 말고 `guard_reflexivity` 의
  `_`-prefixed 함수 중 `ast.expr` 를 받는 것으로 유도 — D-045 의 교훈을 이 registry 에도.
- **Status**: open

## ~~Q-065~~ — 2026-08-04 — `[meta]` shape predicate 을 failure predicate 으로 바꿀 수 있는가 — 방향은 구조에 없다 — **resolved → D-050**

- **Question**: `revocable` 은 population 이 두 관측의 *차이* 인지만 본다. 금지된 행위가 그 차이를
  **비우는지**(D-047 의 실패) **채우는지**(정상 guard) 는 구조에 없다 — D-049 에서 shape 은 2회,
  failure 는 1회였다. 방향을 정적으로 판정할 수 있는가, 아니면 실행해야만 하는가?
- **Trade-off**: (a) 정적 — 금지 행위가 population 의 어느 항을 움직이는지 AST 로 추론. 값싸지만
  "금지 행위" 자체가 규칙 쪽 지식이라 Q-064 (a) 의 hand-typed 문제를 물려받는다. (b) 동적 — scratch
  worktree 에서 실제로 행위를 저지르고 guard 의 before/after 를 비교. 정확하고 이미 한 guard 에
  대해 손으로 해봤다(`test_the_index_read_is_real_not_inferred`); 비용은 guard 당 git 저장소 하나.
  (c) 안 한다 — "bounded at N" 을 match 수로만 읽는다.
- **Lean**: **(b)**. D-049 에서 가장 값싸고 결정적이었던 것이 정확히 이 동작(파일 하나 stage)이었고,
  28개 guard 중 `DIFFERENCE` 는 2개뿐이라 모집단이 작다. (a) 는 모집단이 커지면.
- **다음 action**: 다음 instrument cycle. `revocable` 에 방향 인자를 붙이지 말고 별도 `fails_quietly()` 로.
- **Status**: **resolved → D-050**. (b) 가 답을 냈고, 답은 "방향이 구조에 없다" 보다 강하다: shape 이
  지목하는 붕괴는 **실재하지만 exemption 에 가려 한 번도 관측되지 않는다** (`quieter` 10 중 0,
  `masked` 10 중 5). 정적 경로 (a) 로는 원인이 둘이고 하나가 다른 하나를 가린다는 사실을 볼 수
  없었을 것이다. `fails_quietly()` 는 지시대로 별도 함수로 배치.

## ~~Q-064~~ — 2026-08-04 — `[meta]` guard 가 감시하는 **동작** 을 열거할 수 있는가 — 집합이 아니라 동사를 — **resolved → D-049**

- **Question**: D-048 은 `DECLARED_LOCAL_ONLY` 가 watcher 2개를 두고도 ~30 cycle 동안
  뚫려 있었음을 보였다. 둘 다 **집합** 은 맞게 봤고 **동사** 를 못 봤다 (tracked-ness,
  재유도 가능성 — staging 아님). 그렇다면 guard 마다 "이것이 감시하는 행위" 를 열거하고,
  규칙이 금지하는 행위 집합과 비교할 수 있는가? 예: D-011 은 `write locally` 와
  `never stage` 두 동사를 금지하는데 D-047 이전에는 첫 번째만 mechanism 이 있었다.
- **Trade-off**: (a) 규칙마다 금지 동사를 손으로 선언하고 guard 를 매핑 — 정확하지만
  선언 자체가 hand-typed registry 라 D-045~D-047 의 실패 모드를 그대로 물려받는다.
  (b) guard 가 읽는 **git/파일시스템 연산** 에서 동사를 유도 (`diff HEAD` vs
  `diff origin/main...` vs `ls-files`) — 유도 가능하지만 어휘가 git 명령에 갇힌다.
  (c) 하지 않는다 — D-048 을 서술로 남긴다.
- **Lean**: **(b)**. D-048 의 세 watcher 는 실제로 서로 다른 git 연산을 부르고, 그 차이가
  정확히 놓친 동사와 일치한다 — 즉 동사는 이미 코드에 있고 아무도 그것을 **비교** 하지
  않았을 뿐이다. (a) 는 (b) 가 규칙 쪽 절반을 못 채울 때 보완으로.
- **다음 action**: 다음 instrument cycle. `guard_reflexivity` 에 `watched_operations()` 추가.
- **Status**: **resolved → D-049**. (b) 가 답을 냈다: 동사는 이미 코드에 있었고 `INDEX` 를 보는 guard 가 0개였다. (a) 의 규칙 쪽 절반은 여전히 미착수.

## ~~Q-063~~ — 2026-08-04 — `[meta]` guard 의 "깨끗함" 은 그것이 잡으려는 실패에서 살아남는가 — **resolved → D-048**

- **Question**: D-047 에서 `undeclared_drift` 는 자신이 강제하는 D-011 위반을 볼 수
  없다는 것이 드러났다 — worktree 를 `HEAD` 와 비교하므로 snapshot 파일을 **commit 하면**
  drift 가 사라지고, 게다가 그 path 는 자신의 allow-list 에 있다. 규칙을 어기는 순간
  계기가 가장 깨끗하게 읽힌다. 이 질문을 suite 전체에 던지면 몇 개가 살아남는가?
  각 guard 에 대해: 그것이 잡도록 만들어진 실패를 실제로 일으켰을 때, 그 guard 는
  붉어지는가 아니면 **더 조용해지는가**?
- **Trade-off**: (a) guard 마다 손으로 실패를 주입해 확인 — 정확하지만 guard 수만큼 비용,
  그리고 "주입할 실패" 를 사람이 상상해야 하므로 D-046 의 hand-typed 실패 모드를 재현.
  (b) 구조적 판정 — guard 가 읽는 surface 와 그것이 금지하는 행위가 겹치는지를 정적으로
  본다. 값싸지만 `undeclared_drift` 같은 "allow-list 가 곧 사각지대" 형태만 잡을 것.
  (c) 하지 않고 D-047 을 단일 사례로 둔다.
- **Lean**: (b) 부터. D-047 의 사각지대는 **allow-list ∩ 감시 대상** 이라는 한 줄짜리
  술어로 표현 가능했고, 그런 형태가 하나 있었다면 더 있을 가능성이 높다 — D-046 의
  "우연히 성립하는 invariant" 와 같은 사전 확률. (a) 는 (b) 가 아무것도 못 찾을 때.
- **다음 action**: 다음 instrument cycle 에서 (b) 를 ~30 LOC 로 시도. STATE #2
  (coincidence-held invariant 감사) 와 같은 pass 에서 하는 것이 자연스럽다 — 둘 다
  "술어가 무의미해지는 조건" 을 묻는다.

## Q-062 — 2026-08-03 — `[meta]` bill 을 **site** 로 매기는 것이 옳은 단위인가 — 52 site 는 52 회 시뮬이 아니다

- **Question**: D-042 는 Q-061 (c) 의 비용을 **60–104 회 시뮬** 로 매겼다 (하한 30 / 상한 52, × 2 rung). 그런데 이 test 들은 `_CACHE` 를 공유한다 — `test_epistemic_reach_screen` 의 세 site 는 `("dur", path)` 키로 같은 run 을 재사용하고, `_response` / `_closed_loop` / `_ratio` 같은 helper 는 정의상 여러 caller 가 한 run 을 나눠 쓴다. 실제 단위는 site 가 아니라 **구별되는 `(scenario, controller, seed, params)` tuple** 이다.
- **Trade-off**: (a) site 로 매긴 채 두고 상한으로 읽는다 — 보수적이고 지금 있는 수지만, D-038 이 진단한 **"잘못된 단위로 값을 매겼다"** 와 같은 형태의 오류다 (Q-057 은 site 를 occurrence 로 세어 flood 를 예상했다). (b) tuple 로 다시 센다 — 옳은 단위지만 `_CACHE` 키가 test 마다 손으로 지어져 있어 정적으로 정규화하기 어렵고, cache 는 **session-scoped** 이라 rung 을 바꾸면 어차피 전부 miss 난다. (c) 그냥 계측하며 센다 — `#15` 가 (c) 를 실행할 때 실제 `simulate` 호출 수를 세면 답이 공짜로 나온다.
- **Lean**: **(c)**, 그리고 그때까지 60–104 는 **상한으로만** 읽는다. (b) 의 어려움이 실은 답의 일부다 — rung 을 바꾸는 순간 cache 가 전부 무효화되므로, 재실행 비용은 캐시 공유로 줄지 않고 오히려 **site 수에 가깝다**. 즉 (a) 가 우연히 옳을 수 있는데, 그것을 아는 방법은 세는 것뿐이다.
- **다음 action**: `#15` re-baseline 브랜치가 Q-061 (c) 를 실행할 때 `simulate` 호출을 계수한다.
- **Status**: open

---

## Q-061 — 2026-08-03 — `[uncertainty]` shipped 온도에서 도는 **52 개 site** 중, 그 assertion 이 실제로 `lam` 에 의존하는 것은 몇 개인가 — determinism test 에게 out-of-band 는 결함인가

- **Question**: D-041 은 52 개 site 가 admissible 하지 않은 rung 에서 weight 한다고 셌다. 그런데 그 중 상당수는 **물리량이 아니라 계약을 주장**한다 — `test_same_seed_identical_trajectory`, `test_all_knobs_zero_reproduces_stock_byte_for_byte`, `test_instrumented_copy_matches_the_shipped_controller` 는 두 실행의 **동일성**을 보므로 온도가 무엇이든 양쪽에 똑같이 걸린다. 이런 test 에게 out-of-band 는 결함인가, 아니면 무관한가?
- **Trade-off**: (a) **전부 결함으로 센다** — 정직하고 보수적이지만, 52 라는 수가 "재측정해야 할 claim 52 개" 로 읽히면 **과대**다. 재측정 대상은 물리량을 보고하는 부분집합뿐이다. (b) **`lam`-의존 assertion 만 센다** — 결정적으로 옳은 수지만 판정이 어렵다: "이 assert 가 온도에 의존하는가" 는 정적으로 결정 불가에 가깝고, 손으로 분류하면 D-037 이 진단한 hand-registry 실패를 재도입한다. (c) **계측으로 답한다** — 각 site 를 admissible rung 에서 한 번 더 돌려 assertion 이 여전히 통과하는지 본다. 통과하면 그 site 는 온도-무관(계약), 실패하면 온도-의존(물리량). 판정을 **의견이 아니라 실행**에 맡긴다.
- **Lean**: **(c)**, 단 이것은 시뮬레이션이므로 slow 절반이고 #15 의 일이다. D-040/D-041 과 같은 성질의 함정을 조심해야 한다 — (c) 는 "통과 = 무관" 을 가정하는데, 우연히 통과할 수도 있다 (rung 하나만 보면). 최소 2 개 admissible rung 에서 봐야 하고, 그러면 52 × 2 회 실행이다.
- **다음 action**: #15 re-baseline 브랜치. 그 전까지 D-041 의 census 가 모집단을 고정하고, 52 는 **상한**으로 읽는다 — 하한이 아니라.
- **부분 답 (D-042) — 추측은 참이지만 작다.** 52 site 를 assertion 별로 분할하니 `IDENTITY` 는 **13** 개뿐이고 `ANCHORED` (literal 에 못 박힌 물리 주장) 가 **25** 개다. ⇒ 추측을 통째로 인정해도 bill 은 **52 → 39**, 알려진 하한은 **30** (ANCHORED 25 + COMPARATIVE 5). 두 rung 기준 **60–104 회** 시뮬 (단위 문제는 **Q-062**). `IDENTITY` 를 빼서 보고하지 **않는다** — 한 rung 에서의 일치는 그 rung 에 대한 증거이지 계약의 증명이 아니고, 그것을 판정하는 것이 (c) 의 계측이 존재하는 이유다.
- **남은 것**: 어느 site 가 실제로 온도-의존인지는 여전히 (c) 만 답한다. 정적 pass 는 **아무것도 clear 하지 않았다** — 22 개는 미결이지 무관이 아니다.
- **Status**: **partially-answered → D-042**

---

## Q-060 — 2026-08-03 — `[scope]` shipped 기본값 `lam = 0.1` 은 24 cell 중 **0 곳에서 admissible** 하다. 기본값을 옮길 것인가, 아니면 "기본값은 측정용이 아니다" 를 명시할 것인가 → **partially-answered → D-041** (비용은 확정, 처분은 미정)

- **Question**: D-040 의 계측은 `MPPIParams.lam = 0.1` 이 calibrated cell **전부**에서 ESS band 밖임을 보였다 (`0.4` 는 13/24 로 최다). 아무 온도도 넘기지 않고 `make_controller` 를 부르는 코드는 전부 out-of-band 로 도는데, `exposure_band_hi` 가 정확히 그 경우다. 기본값을 옮길 것인가?
- **Trade-off**: (a) `0.4` 로 이동 — 가장 많은 cell 을 만족시키지만 **banked reading 전부가 재측정 대상**이 되고, `shared_window: []` 이므로 어떤 단일 값도 matrix 를 만족시키지 못한다는 사실은 그대로다. (b) 기본값 유지 + docstring/test 로 "기본값은 데모용이며 측정은 cell 의 window 에서 하라" 를 명시 — 싸고 정직하지만, 잘못 부르는 코드를 막지 못한다. (c) 기본값을 **없애기** (`lam` 필수 인자화) — 잘못 부르는 것이 구조적으로 불가능해지지만 호출부 전부를 건드린다. (d) `make_controller` 가 scene 의 window 를 읽어 자동 선택 — 가장 옳아 보이지만 cell 마다 controller 별로 다르고 window 가 빈 cell (`cafe_cut_in_v0`) 이 있다.
- **Lean 이었던 것**: **(b) 먼저, (c) 를 #15 에서 검토.** (a) 는 D-040 이 명시적으로 기각했다. (d) 는 빈 window cell 에서 정의되지 않는다. 다음 action 은 "#15 가 **(c) 의 호출부 수를 세고** 결정" 이었다.
- **부분 답 (D-041) 🔴 — 세라고 한 것이 셀 수 없는 것이었다.** `make_controller` 에는 `lam` 인자가 **없다** (`StockMPPI`/`RiskMPPI`/`CBFMPPI` 도 없다); 온도는 `params=MPPIParams(lam=…)` 의 필드로만 도달한다. 그래서 "온도를 안 넘기는 `make_controller` 호출" 은 **32/32**, 구조상 100 % 이고 정보량이 0 이다. 온도를 만드는 자리는 **3-way** 다 — `DECIDES` 30 / `DEFAULTS` 54 / `FORWARDS` 19 (총 103).
- **그래서 (c) 의 가격이 바뀐다**: "호출부 전부" 가 아니라 **54** 다. `FORWARDS` 19 는 이미 caller 에게 위임하므로 손댈 게 없고 `DECIDES` 30 은 이미 준수한다. **(c) 는 매겨진 가격의 약 절반이고, lean 이 (b) 를 먼저 둔 근거가 그만큼 약해졌다.** 덤으로 나온 것: `DEFAULTS` > `DECIDES` 이므로 **기본값은 fallback 이 아니라 이 repo 의 최빈 온도**이고, 그 중 52 개가 실제로 weight 한다 (2 개는 `raises` test 라 inert).
- **남은 것 (이 Q 가 계속 open 인 이유)**: 기본값을 **옮길지** 는 여전히 미정이다. D-041 은 (c) 의 *비용* 만 확정했지 (a)/(b)/(c)/(d) 중 무엇을 할지는 정하지 않았고, `shared_window: []` 이므로 **어떤 단일 값도 matrix 를 만족시키지 못한다**는 D-040 의 사실은 그대로다. 그리고 52 는 **상한**이다 — 그 중 몇 개의 assertion 이 실제로 `lam` 에 의존하는지는 별개 질문 → **Q-061**.
- **다음 action**: #15 re-baseline 브랜치가 (b) vs (c) 를 결정. 이제 (c) 의 수는 알려져 있다.
- **Status**: **partially-answered → D-041**

---

## Q-059 — 2026-08-03 — `[uncertainty]` claim 의 scope 는 **machine** 만 기록된다. **operating point** (`lam`, horizon, seed) 는 왜 안 기록되는가 → **resolved → D-040**

- **Question**: D-036 이후 `claim_scope` 는 모든 등록 claim 에 **어느 기계에서 쟀는가** (`AVX512_SKX` stamp) 를 강제한다. D-039 는 D-028 의 근거 세 개가 전부 **`lam = 1.6` 조건부**였고 repo 는 `lam = 0.1` 을 ship 한다는 걸 보였다 — machine scope 는 전부 붙어 있었는데도. **측정 지점(operating point)이 shipped 값과 다르면 그 자체가 scope 결함**인가, 아니면 정상적인 sweep 결과인가?
- **Trade-off**: (a) `claim_scope` 에 `operating_point` 필드 추가 + shipped 값과 다르면 명시 요구 — D-039 류 결함을 test 로 잡지만, sweep 결과는 **본질적으로** 여러 지점에서 나므로 거의 모든 claim 이 필드를 채워야 한다. (b) shipped 값에서 잰 claim 만 무조건 표기 — 싸지만 D-028 처럼 *전부* 비-shipped 인 경우를 못 잡는다. (c) 계측만 — `docs/` claim 중 몇 %가 shipped operating point 에서 측정됐는지 세고, 비율이 나쁘면 그때 강제한다.
- **Lean 이었던 것**: **(c) 계측 먼저.** 세는 비용은 낮다: `claim_scope` 는 이미 instrument 를 기록하므로 각 instrument 의 기본 `lam` 을 읽으면 된다. 계획된 판정 규칙은 "비율이 높으면(대부분 non-shipped) (a) 로, 낮으면 D-039 를 단발 결함으로 남긴다" 였다.
- **답 (D-040)**: **(c) 로 셌고, 그 판정 규칙 자체가 틀렸다.** 비율은 4/5 로 **높게** 나왔지만 — 계획대로면 (a) 강제 — 같은 census 가 shipped 값 `0.1` 이 **24 cell 중 0 곳에서 admissible** 임을 보였다. `0.1` 은 모든 cell 의 ladder 에 있었고 어디서도 통과하지 못했다. ⇒ off-shipped 는 결함이 아니라 이 plant 에서 제대로 재기 위한 **필요조건**이다.
- **결정적인 것은 비율이 아니라 두 열의 관계였다**: off-shipped 4 claim 의 point 는 전부 자기 cell 의 window 안이고 (유일한 예외는 out-of-band 인 것이 곧 측정 대상), shipped 에서만 잰 유일한 claim (`exposure_band_hi`) 이 **admissible point 가 하나도 없는 유일한 claim** 이다. (a) 는 건전한 4 개를 flag 하고 불건전한 1 개를 통과시켰을 것이다. 기록할 성질은 `shipped` 가 아니라 **`admissible`**.
- **남은 것**: 기본값 `0.1` 을 어떻게 할지는 별개 질문 → **Q-060**. 그리고 D-039 의 "ship 할 온도에서 재라" 규칙도 이 결과에 걸려 rescope 됐다 (D-040 Decision (4)).
- **Status**: **resolved → D-040**

---

## Q-057 — 2026-08-03 — `[meta]` `citation_audit` 는 `N.NN×` 철자만 잡는다. 표 안의 **맨 숫자**까지 넓히면 오탐이 급증하는데, **후보 순위** 없이 넓히는 게 의미가 있는가 → **resolved → D-038**

- **Question**: D-037 의 명시된 한계를 걷어낼 때, 순위 없이 넓히면 미등록 site 목록이 잡음에 묻히지 않는가?
- **Trade-off**: (a) 넓히지 않고 한계로 두기. (b) **순위 먼저** — 신뢰도 정렬을 붙인 뒤 넓힌다. (c) 넓히고 전부 whitelist 로 관리.
- **Lean 이었던 것**: (b).
- **답 (D-038)**: **(b) 채택 — 그러나 전제였던 "오탐 급증" 이 틀렸다.** 6 claim 에 걸쳐 새로 생기는 site 는 **5 개**뿐이다. 40 이라는 수는 raw occurrence 이고 registry 가 태그하는 단위는 site 다 — **질문이 비용을 잘못된 단위로 추정했다.** 그리고 5 개 전부 국소 token (`unit_suffix` / `assignment` / `denominator` / `precision_mismatch`) 으로 걸러지는 오탐이라, **철자가 놓치고 있던 진짜 인용은 0 개**였다.
- **진짜 위험은 다른 데 있었다**: 넓힌 pattern 이 좁은 pattern 의 **superset 이 아니었다** (ASCII `x` 가 `\w` 라서 `2.320x` 를 잃는다). 오탐이 아니라 **미탐**이 실제 defect 였고, 순위는 그걸 못 잡는다 — superset 관계를 직접 test 로 걸어야 한다.
- **남은 것**: 순위의 분리(등록 최저 +3 vs 미등록 최고 −1)는 오탐이 전부 unmarked 라서 생긴 것이다. **진짜 bare 인용은 아직 한 번도 관측되지 않았으므로** keyword 증거만으로 판정하는 경로는 미검증이다. (c) whitelist 는 기각 — hand-registry 문제의 재도입이다.

## Q-056 — 2026-08-03 — `[meta]` citation registry 를 **손으로 등록**하면 등록되지 않은 인용은 여전히 침묵한다 — 인용을 *발견*하는 쪽까지 자동화해야 하는가 → **resolved → D-037**

- **Question**: `claim_scope` 는 claim 마다 인용 절을 손으로 적는다. 아무도 기억 못 한 인용은 D-036 이 찾아낸 drift 와 정확히 같은 정도로 조용하다. 숫자 grep → instrument 역참조까지 자동화할 것인가?
- **Trade-off**: (a) 손 등록 유지 — 정밀하지만 불완전성이 **구조적**이다. (b) 반자동: scan 이 후보만 내고 tagging 은 사람/executor. (c) 완전 자동 태깅 — 흔한 크기(예: 진폭 상수)에서 오탐이 불가피.
- **Lean 이었던 것**: (b).
- **답 (D-037)**: **(b) 그대로 채택, 그리고 lean 이 예상 못 한 게 나왔다** — 문제는 *얼마나 많이 놓쳤나* 가 아니라 **어느 표면을 아예 안 봤나** 였다. `claim_scope` 는 `docs/` 만 읽는데 **module docstring 이 같은 숫자를 인용**하고 있었고, 놓친 defect 가 하필 거기 있었다 (`horizon_audit` docstring 이 D-036 이 여섯 절에서 고친 그 짝짓기를 그대로 들고 있었다). 즉 hand registry 의 실패는 "빠뜨린 절" 이 아니라 **"scan 범위 밖 표면"** 이다.
- **부수 결과**: STATE 가 지목한 drift 용의자 4 개 중 3 개는 실제로 측정 절 밖에서 진술되고, 1 개(D-025)는 깨끗하다 — **정직한 negative 를 test 로 고정**해 다음 cycle 이 다시 손으로 확인하지 않게 했다.
- **남은 것**: scan 은 `N.NN×` 철자만 잡는다. 표 안의 맨 숫자는 못 찾으므로 "미등록 site 존재" 는 증명해도 "남은 게 없음" 은 증명 못 한다 — 후보 생성기다.

## Q-055 — 2026-08-03 — `[uncertainty]` AVX-512 상수와 AVX2 상수 중 **어느 쪽이 정본**인가 → **부분 해소 → D-035**: 질문은 옳지만 **불충분**하다. canonical machine 은 5 개 중 **0 개**를 복구하지 못한다 (widening 으로 고쳐지는 건 1 개, 그마저 최소 수리가 margin 2.1% — lean (b) AVX2 는 유지하되, 그것은 *재보정 계획*이지 *수리*가 아니다)

> ⚠️ **D-036 재범위(rescope)** — 이 절이 인용하는 **2.0×** 는 `w(H=34)/w(H=15)`
> (13.97/7.00) 다. dispatch 에서 실제로 뒤집히는 assertion
> (`test_horizon_audit::test_the_prescribed_weight_moves_with_the_horizon`) 이 재는
> 것은 `w(H=34)/w(H=30)` 이고, 그 값은 **1.3008** (`AVX512_SKX`) → **1.0289**
> (AVX2) 다. **서로 다른 양이다.** 2.0× 를 AVX2 의 1.029× 와 짝지어 읽으면 붕괴가
> 과장된다 — 정직한 쌍은 **1.3008 vs 1.0289**. 남는 몫: assertion(`>1.2`) 의
> **14.4 %**, 측정값의 **9.6 %**, 여기 인용된 2.0× 의 **2.9 %**.
> 이 절의 모든 상수는 `AVX512_SKX` dispatch 조건부다 (D-033).

- **Question**: D-033 이 D-029/D-030 상수가 **AVX-512 dispatch 에 조건부**임을 확정했다. dev box 는 AVX-512 를 갖고 GH runner 는 갖지 않으며, 두 machine 은 서로 다른 숫자를 낸다 (D-030 headline swing **2.0× vs 1.029×** — 결론의 부호가 갈린다). 그러면 프로젝트가 들고 갈 상수는 어느 쪽인가?
- **Trade-off**: **(a) AVX-512 유지** — 지금까지 측정한 모든 것과 연속적이고 재측정 비용 0. 그러나 CI slow half 는 영구 red 이고, north star 가 요구하는 "모든 환경"에 CPU 는 명백히 포함된다. **(b) AVX2 로 재보정** — portable 하고 CI 와 일치하며 더 흔한 baseline. 그러나 D-029/D-030 전체 재측정이 필요하고 D-030 의 headline 이 **뒤집힌다**. **(c) 둘 다 보고** — 정직하지만 모든 표가 2 배가 되고, 어느 쪽으로도 결정을 못 내린다.
- **Lean**: **(b) 쪽으로 기운다**, 단 재보정 전에 Q-054(d) 의 fragility sweep 이 선행되어야 한다. 이유: 부호가 CPU 에서 뒤집히는 상수는 어느 machine 에서 쟀든 **주장이 약한 것**이지 AVX-512 가 틀린 게 아니다. AVX2 를 고르는 실질적 근거는 "더 맞아서"가 아니라 **검증 가능해서** — CI 가 재현할 수 없는 상수는 다음에도 똑같이 조용히 썩는다. 다만 (b) 는 D-030 을 철회하는 것과 같으므로 sweep 없이 하면 안 된다.
- **다음 action**: re-baseline branch (STATE #16) 에서, Q-054 의 fragility sweep 직후. **stack 금지** — queue drain 이 선행. 그 전까지 D-029/D-030 은 `AVX512_SKX 에서 측정됨` 이라는 scope line 을 달고 다닌다.

## Q-054 — 2026-08-03 — `[uncertainty]` numpy minor version 에서 **부호가 뒤집히는 결과**를 증거로 계속 들고 갈 수 있는가 → **전제 정정 (D-033): 뒤집는 것은 version 이 아니라 CPU SIMD dispatch 였다.** 질문 자체(FP-fragile 한 결론이 증거가 되는가)는 그대로 open 이고, (d) fragility sweep 이 여전히 다음 action — 다만 sweep 의 축은 numpy version 이 아니라 **dispatch** 다.

> ⚠️ **D-036 재범위(rescope)** — 이 절이 인용하는 **2.0×** 는 `w(H=34)/w(H=15)`
> (13.97/7.00) 다. dispatch 에서 실제로 뒤집히는 assertion
> (`test_horizon_audit::test_the_prescribed_weight_moves_with_the_horizon`) 이 재는
> 것은 `w(H=34)/w(H=30)` 이고, 그 값은 **1.3008** (`AVX512_SKX`) → **1.0289**
> (AVX2) 다. **서로 다른 양이다.** 2.0× 를 AVX2 의 1.029× 와 짝지어 읽으면 붕괴가
> 과장된다 — 정직한 쌍은 **1.3008 vs 1.0289**. 남는 몫: assertion(`>1.2`) 의
> **14.4 %**, 측정값의 **9.6 %**, 여기 인용된 2.0× 의 **2.9 %**.
> 이 절의 모든 상수는 `AVX512_SKX` dispatch 조건부다 (D-033).

- **Question**: D-032 가 측정했다 — scale-matched `w_voo` 의 horizon swing 이 numpy **1.26.4 에서 2.0×**, **2.5.1 에서 1.029×**. 같은 box, 같은 seed, 같은 코드. D-030 은 그 2.0× 위에 "rollout horizon 은 sweep 가능한 축이 아니다" 를 세웠고, test 의 실패 메시지 스스로가 1.2× 미만이면 반대 결론이라고 적어 놓았다. pin 은 이 숫자를 **재현 가능**하게 만들었지 **참**으로 만들지 않았다. 그렇다면 D-029/D-030 은 planner 에 대한 사실인가, 아니면 `planner × FP 환경` 에 대한 사실인가?
- **Trade-off**: (a) **pin 을 계약으로 받아들이고 진행** — 값싸고 지금 상태. 하지만 "이 결과는 numpy 1.26.4 에서 참" 은 north star("모든 환경에서") 가 요구하는 주장보다 훨씬 약하고, 그 약함이 어디에도 안 적혀 있으면 다음 독자는 강한 주장으로 읽는다. (b) **결론을 내는 test 는 threshold 가 아니라 seed 분포로 판정** — `n` seed 에서 swing 의 CI 가 1.2 를 넘는지. FP drift 를 noise 로 흡수하지만 지금 4-seed 를 훨씬 키워야 하고 slow half 비용이 곧 증거인 상황에서 직격이다. (c) **두 numpy 에서 모두 재도출하고 겹치는 결론만 carry** — 가장 정직하고 가장 비싸다 (D-029/D-030 전체 재측정 × 2). (d) **chaotic amplification 자체를 측정** — 같은 arm 을 FP 섭동만 주고 여러 번 돌려 결론의 fragility 를 수치화. 그러면 어떤 주장이 취약한지 *알고* 고를 수 있다.
- **Lean**: **(d) 먼저, 그다음 (c) 를 선택적으로.** 지금 모르는 것은 "어느 결론이 취약한가" 이지 "어떻게 고치나" 가 아니다 — 5 개가 뒤집혔고 353 개는 안 뒤집혔으므로 fragility 는 **suite 전반의 성질이 아니라 특정 주장의 성질**이고, 그 경계를 긋는 것이 가장 정보량이 큰 다음 한 걸음이다. (b) 는 (d) 의 답이 "대부분 취약" 일 때만 정당화된다.
- **선결 문제 / 규모**: `w_voo` 계열 결론 대부분이 D-029 의 scale-matched weight 위에 서 있고 그게 다시 D-028 의 quotient 위에 선다 — 이 stack 이 통째로 같은 FP 민감성을 공유하는지는 미확인. 또한 D-032 가 기록한 **numpy 2 내부의 machine 간 ~3% 잔차**는 pin 이 문제를 줄였을 뿐 없애지 않았다는 뜻이므로, (d) 의 섭동 규모는 임의로 고를 게 아니라 그 3% 에서 잡는 게 자연스럽다.
- **다음 action**: queue drain 후 re-baseline branch (STATE #16) 에서. 그 branch 는 이미 "모든 baseline 수정 + 전면 재측정" 이므로 (d) 의 자연스러운 집이고, 그전에 stack 하면 안 된다.
- **Status**: **부분 답 → D-034** ((d) 의 sweep 을 dispatch 축에서 실행함). 남은 open 부분: 나머지 **122 개 closed-loop test 의 excursion 은 미측정**이므로 fragile/robust 경계는 아직 5 개 표본으로만 그어져 있다. D-034 가 확정한 것: excursion 이 불균질(0.136~1.95+categorical)이라 **tolerance 하나로 두 machine 을 덮을 수 없고**, fragility 는 4 class (tolerance / verdict / structural / calibration) 로 갈리며 class 마다 수리가 다르다. verdict-fragile 2 개(D-030 headline, Q-039 답)는 증거로 carry 불가.

## Q-053 — 2026-08-03 — `[meta]` executor 의 REVIEW 는 **자기 PR 의 CI 상태**를 읽어야 하는가

- **Question**: 이 branch 의 CI 는 **14 run 연속 red** 였고 (2026-08-02T10:09Z 이후), 마지막 6 run 은 job timeout 으로 killed 됐다. 그 24 시간 동안 매 cycle 은 `sandbox:pass=357/357` 을 **local** 기준으로 보고했고 STATE 는 "#67 ... 21 (PR #67)" 로만 적었다 — #68/#69 에는 "CI green" 이 붙어 있는데 #67 에는 아무 표기가 없었고, 아무도 그 부재를 눈치채지 못했다. D-016 은 "red PR = deliverable 이 안 끝난 것" 이라 선언했지만 그것을 **읽는 단계**를 어디에도 넣지 않았다.
- **Trade-off**: (a) **REVIEW Phase 1 에 `gh pr checks <own-PR>` 한 줄 추가.** 비용 ~2 초, 26 cycle 짜리 사각을 닫는다. 단 gate-1 이 먼저 fire 하면 REVIEW 까지 못 가는 cycle 도 있어 위치가 애매하다. (b) **EXECUTE 끝, push 직후에 확인** — 방금 민 commit 의 CI 는 아직 안 돌았으므로 항상 *직전* commit 을 보는 셈이라 한 cycle 늦다. 그래도 지금(무한)보다 낫다. (c) **local pass 를 metric 으로 쓰는 것을 금지하고 CI 결과만 TSV 에 기록** — 가장 엄격하지만 cycle 이 CI 를 기다려야 해 15 분 EXECUTE 예산과 충돌.
- **Lean**: **(a) + (b) 병행, (c) 는 기각.** 진짜 결함은 "확인을 안 했다" 가 아니라 **`sandbox:pass=N/N` 이라는 metric 문자열이 어느 surface 에서 잰 값인지 표기가 없다** 는 것이다. 그래서 최소 수리는 TSV/commit 의 metric 을 `sandbox:pass=...` → `sandbox-local:pass=...` 로 정규화하고, CI 값은 별도 이름으로 두는 것. 그러면 "local 만 있고 CI 가 없다" 가 표에서 **보인다**.
- **선결 문제**: gate 1 이 51 cycle 연속 fire 하는 상황에서 executor 가 같은 PR 에 계속 쓰는 것 자체가 이 사각을 만든다 — 새 PR 이라면 생성 직후 CI 를 봤을 것이다. 즉 이건 queue stall 의 **2차 피해**이고, drain 이 되면 압력이 줄어든다. 그래도 표기 수리는 drain 과 무관하게 유효하다.
- **Status**: `open`

## Q-051 — 2026-08-03 — `[meta]` suite 가 636 s 다. `slow` marker 인가, cap 단축인가, 예산 증액인가 → **~~open~~ resolved → D-031**

- **Question**: 원안 그대로. 답은 marker 였고, lean 이 맞았다.
- **답이 바꾼 것**: 질문의 **전제**가 틀렸다. 이건 "나중 cycle 을 싸게 만드는" 최적화가 아니라 **head-of-line PR 의 CI 가 이미 red 였던 것의 수리**였다 (→ Q-053). 그리고 marker 의 **단위**가 비자명했다: test 단위 marking 은 class-scoped fixture 비용을 살아남은 형제에게 옮길 뿐이라 628 s → 338 s 에서 멈췄고, `call` 시간만 재는 측정은 97.65 s 짜리 `setup` 을 구조적으로 못 봤다. fixture scope 로 자르니 **115 s**.
- **Status**: `resolved → D-031`

## Q-052 — 2026-08-03 — `[meta]` closed-loop 행동의 귀인은 leave-one-out 을 버리고 **power set** 으로 가야 하는가

- **Question**: D-030 이 `H=45` freeze 의 원인이 `w_collision` 과 `w_obs_soft` 의 **논리합**임을 보였다 — 각각을 끄면 cruise 가 0.97× / 0.90× (개선 없음), 둘 다 끄면 5.6×. LOO 는 두 항에 각각 책임 ≈ 0 을 매긴다. D-028 의 `weight_units.measure` 는 구조상 LOO 다. 그렇다면 이 repo 의 귀인 도구 기본값을 `2**g` power set 으로 바꿔야 하는가?
- **Trade-off**: (a) **LOO 유지, power set 은 opt-in** (`horizon_audit.ablate` 가 지금 그 위치). 싸고 (`g` runs), *cost 기여도* 질문에는 정확하다 — LOO 는 틀린 게 아니라 **다른 질문**에 답한다. 대신 중복 원인은 아무도 찾지 않으면 안 보인다. (b) **행동 주장에는 power set 을 필수화**. `g=3` 이면 8 arm × seed — 이미 504 s 인 suite 에 감당 안 되고, 후보 term 선정 자체가 cost 함수 읽기라 D-026 이 경고한 바로 그 단계에 의존한다. (c) **중간 — LOO 로 훑고, "아무 singleton 도 안 움직이는데 행동은 설명이 필요한" 경우에만 power set 으로 승격.** 이번 cycle 이 실제로 밟은 경로.
- **Lean**: **(c)**, 단 발동 조건을 명시적으로 적을 것. 이번엔 "LOO 가 전부 ≈0 인데 행동은 명백히 달라졌다" 가 신호였고, 그건 자동으로 검사 가능하다 — `redundant_sets` 가 그 검사의 절반이다. 나머지 절반 (LOO 표가 전부 0 일 때 경고) 은 `weight_units` 쪽에 있어야 하는데 아직 없다.
- **선결 문제**: 중복성은 term 쌍의 성질이 아니라 **(scene, horizon, lam) 의 성질**일 수 있다. `H=30` 에서는 freeze 자체가 없으므로 이 쌍의 중복성도 없다. 한 scene · 한 rung 의 관찰을 도구 기본값 변경 근거로 쓰기 전에 최소 한 개의 다른 scene 에서 재현이 필요하다.
- **Status**: `open`

## Q-049 — 2026-08-03 — `[uncertainty]` 새 cost 항의 weight 는 **무엇의 단위**로 sweep 되어야 하는가

- **Question**: D-027 이 `w_voo=200` — 직전 항의 weight 를 그대로 물려받은 값 — 이 이 scene baseline total-cost spread 의 **6.19×** 임을 측정했고, 그 결과는 "정보 선호가 강한 planner" 가 아니라 median ESS **1.00** 인 argmin-over-draws, 즉 **위장된 temperature 변경**이었다. 그렇다면 repo 의 모든 critic weight (`w_risk=40`, `w_epist`, `k_margin_per_sigma`, `w_terminal=30`) 는 무엇에 대해 상대적으로 진술되어야 하는가?
- **Trade-off**: (a) **절대 단위 유지 + weight 마다 ESS band 를 검사** — 지금 방식. 싸고 arm 재현이 쉽지만, band 를 벗어난 cell 이 나올 때까지 그 sweep 이 controller 비교가 아니었다는 걸 모른다. (b) **weight 를 baseline spread 의 비율로 선언** (`w_voo = 0.1 · median ptp`) — 항끼리, scene 끼리 비교 가능해지고 D-017 의 lam 문제와 직교하지만, 계수가 **scene 의존적이고 measured** 가 되어 simulation-free screen 계열의 자산 (D-023/D-025) 과 성질이 달라진다. (c) cost 를 **step 마다 정규화** — softmax 를 계산 순간에 scale-free 로 만들지만 `lam` 의 의미와 이미 calibrate 된 `lam_windows.yaml` 전체를 무효화한다.
- **Lean**: **(b), 단 보고 단위로만.** 계수를 코드에 넣지 말고 **결과를 진술할 때** baseline spread 배수를 함께 적는다 — D-027 의 6.19× 가 그 한 줄로 collision 을 설명했다. (c) 는 `lam` 축 전체를 다시 열므로 지금 값이 없다.
- **선결 문제**: baseline spread 의 중앙값은 scene·seed·step 에 따라 크게 흔들린다 (이 scene 에서 median 79.09 vs mean 3806.8, **48×** 차이). 비율을 쓰려면 **어느 통계**인지부터 못박아야 하고, D-024→D-025 가 정확히 그 종류의 실수 (읽히지 않는 값으로 나눈 비율) 를 두 cycle 잡아먹으며 고쳤다.
- **Status**: `resolved → D-028` (2026-08-03 06:00).
- **답**: **(b), 보고 단위로만 — lean 대로.** 단 표는 Q 가 예상한 두 결말 중 어느 쪽도 아니었다. (1) 네 knob 은 **한 class 가 아니다**: `w_terminal` 만 live 한 순수 additive 계수 (0.328), `w_epist` 는 spread 가 항등적으로 0 인 항을 곱하므로 ratio **정확히 0**, `k_margin_per_sigma` 는 애초에 계수가 아니라 `exp()` 안쪽 shift 라 **cost 단위 자체가 없다** (미터). (2) 그리고 일반화되는 건 분자가 아니라 **분모**였다 — 같은 weight 를 자기 arm 에서 재면 1.46×, 더해지는 baseline 에서 재면 6.19×. 나쁜 weight 일수록 자기가 만든 landscape 로 채점되어 **유리하게** 나온다. **선결 문제(어느 통계인가)는 `REPORTING_STATISTIC = "median"` 으로 선언 후 계측**했다.
- **남은 것**: 이 비율을 실제 sweep 의 **보고 형식**으로 채택할지는 미결 — 계측기 (`weight_units.py`) 는 있고 default 는 하나도 안 움직였다.

## Q-048 — 2026-08-03 — `[arch]` goal 재방문 reference 를 **screen 으로 막을 것인가, controller 를 고칠 것인가**

- **Question**: D-026 이 shipped objective 의 계약을 특정했다 — `v_ref` 와 `w_terminal` 이 둘 다 **Euclidean `d_goal`** 의 함수라, goal 근방을 중간에 재방문하는 reference 에서 loop 이 자기 goal 위에 주차한다. 수리 경로는 둘: (a) `feasibility.goal_approach` screen 으로 그런 scene 을 **matrix 에서 배제**한다 (이번 cycle 이 배포한 것), (b) 두 항을 **remaining arclength** 구동으로 바꾸고 `reached_goal` 이 근접뿐 아니라 completion 도 요구하게 한다.
- **Trade-off**: (a) 는 지금 당장 공짜고 기존 수치를 하나도 안 건드리지만, **north star 의 "모든 환경" 을 깎아서 산다** — loop / patrol / return-to-start 미션을 영구히 계약 밖에 둔다. (b) 는 진짜 capability 를 되찾지만 `d_goal` 은 shipped cost 의 **두 항 모두**에 들어있어 repo 의 모든 기존 수치를 무효화하고, arclength 추적은 self-intersecting path 에서 **projection 이 모호**해진다 (figure-8 의 crossing point 에서 "남은 거리" 가 두 값을 갖는다 — 이게 애초에 문제가 어려운 이유).
- **Lean**: **(b), 단 re-baseline branch (#11) 에서.** (a) 를 영구 답으로 두면 D-026 이 찾아낸 게 "고칠 결함" 이 아니라 "선언된 한계" 가 되는데, 그건 이 cycle 이 실제로 측정한 것보다 약한 결론이다. 다만 Q-032 (queue 중 shared baseline 정정 금지) 가 유효하므로 지금은 아니다. arclength 모호성은 **monotone progress state** (되돌아가지 않는 arclength 커서) 로 풀리는 게 표준이고, 그 자체가 P3 representation 축과 무관하지 않다.
- **선결 문제**: A4/B4 가 보여주듯 `w_terminal = 0` 은 답이 아니다 — **0/4 reached**, goal 에서 멈출 이유가 사라진다. 즉 terminal 항은 제거 대상이 아니라 **재-매개변수화** 대상이다.
- **다음 action**: #11 re-baseline branch 에서 (b) 를 구현하고, `city_figure8_v0` 를 **회귀 테스트**로 승격 (현재는 screen 이 배제하는 대상). screen 은 그 뒤에도 남는다 — 정적 전제조건은 수리와 무관하게 유효하다.

## Q-047 — 2026-08-03 — `[scope]` `city_figure8_v0` 의 0.016 m/s → **~~open~~ resolved → D-026: 두 선택지 모두 기각**

- 제기된 이분법 (Q-037 계열 scene defect vs self-intersecting reference 에서의 controller 실패) 은 **partition 이 아니라 가설**이었고, 양방향 intervention 이 양쪽을 각각 죽였다. self-intersection 없는 `city_curved_v0` 에 `goal := start` **하나만** 적용해도 동일 붕괴 (→ (b) 기각); figure-8 의 closure 를 열어도 30.6 m 중 13.1 m 만 주행 (→ (a) 기각). 실제 원인은 **controller 계약** — 자세히는 D-026, 수리 경로는 Q-048.
- reportable matrix 는 **4 로 유지** (축소 분기가 반증됨).

## Q-043 — 2026-08-02 — `[uncertainty]` epistemic 채널을 들리게 하려면 **scene 을 고를 것인가, planner 를 바꿀 것인가** → **partially-answered → D-027: 제3안 (cost 구성을 바꿈) 이 scene 선택도 horizon 증가도 없이 통함**

- **D-027 (2026-08-03)**: 이 이분법은 다시 한번 partition 이 아니었다. shadow 가 rollout cone 안에 들어오게 만드는 대신 **cost 를 rollout 이 이미 도달하는 위치에서 평가되도록** 구성을 바꾸면 (value-of-observation), shipped `H=30` 그대로 그리고 shipped scene 그대로 spread 0.00 → 1060 이 된다. 즉 (a) 도 (b) 도 필요 없었다. **단** "들린다" 와 "돕는다" 는 별개이고 후자는 n=8 에서 철회됐으므로, `(w_voo, horizon)` 2×2 는 여전히 할 일로 남는다 — 이제 **항이 0 이 아닌 상태에서** 돌릴 수 있다는 점만 다르다.

- **Question**: D-021 이 `w_epist` 의 효과를 **rollout reach** 로 게이팅된다고 특정했다. 그러면 P3 의 epistemic 축을 측정 가능하게 만드는 방법은 둘 중 하나다 — (a) rollout 이 이미 shadow 에 닿는 **scene 을 고른다** (blind-corner 계열, PR #68), 또는 (b) planner 를 **바꿔서** 닿게 만든다 (horizon↑, sampled speed↑, sensing range↓). 어느 쪽이 정직한 실험인가?
- **Trade-off**: (a) 는 controller 를 안 건드리므로 A/B 가 깨끗하지만, "epistemic 채널이 도움이 된다" 가 **shadow 가 rollout 안에 들어오도록 고른 scene 에서만** 성립하는 주장이 된다 — north star 의 "모든 환경" 과 정면 충돌. (b) 는 모든 scene 에 적용되지만 **horizon 을 늘리면 stock 도 같이 좋아진다** — epistemic 항의 기여와 지평 확장의 기여가 교란되어 D-017 이 금지한 종류의 uncontrolled 비교가 된다. 게다가 horizon 은 shipped `MPPIParams` 기본값이라 바꾸면 repo 의 **모든** 기존 수치가 무효.
- **Lean**: (b) 를 **factor 로 승격**하되 default 는 안 건드린다 — 즉 `horizon` 을 A/B 의 **명시된 축**으로 만들어 `(w_epist, horizon)` 2×2 를 돌린다. 그러면 "epistemic 이 돕는가" 와 "지평이 돕는가" 가 분리되고, D-021 의 reach 게이트가 교란이 아니라 **측정 대상**이 된다. (a) 는 그 2×2 를 어느 scene 에서 도느냐의 문제로 흡수된다.
- **선결 문제**: D-021 은 reach 게이트의 **scalar 형태를 반증**했다 (거리만으로는 예측 불가, 방향이 필요). 따라서 "이 scene 에서 epistemic 이 들릴 것인가" 를 **돌리기 전에** 판정하는 screen 은 아직 없다. `exposure.py` 가 정적 스크린의 선례이므로, rollout cone × σ-field 교집합을 재는 유사 스크린이 자연스러운 후보.
- **다음 action**: 위 2×2 를 blind-corner scene (#68) 에서 — 단 **#68/#69 merge 이후**. 그 전에 할 수 있는 것: 방향을 담은 reach screen 을 `exposure.py` 옆에 8 scene 전체로 돌려 **어느 scene 이 애초에 epistemic 을 들을 수 있는지** 표로 만드는 일 (시뮬레이션 없음, merge 불필요).

## Q-042 — 2026-08-02 — `[uncertainty]` window admissibility 기준을 **all-seeds 논리곱**에서 무엇으로 바꿔야 하나

- **Question**: D-019 가 밝혔듯 "모든 seed 가 band 안" 기준은 `n` 이 커질수록 단조로 엄격해져, `shared`/`per_arm` 판정이 seed 수의 함수가 된다 (parent scene: n=4 `shared`, n=8 `per_arm`). 그렇다면 기준은 무엇이어야 하나?
- **Trade-off**: (a) **현행 유지 + `n` 명시** — 싸고 기존 표 보존, 그러나 판정이 여전히 n 의존이라 matrix 확장 때마다 과거 판정이 흔들린다. (b) **quantile 완화** (≥⌈0.9n⌉ seeds) — n-민감도는 낮추지만 없애지 못하고, threshold 자체가 새 자유 파라미터. (c) **구간추정** — seed bootstrap 으로 window 에 신뢰구간을 붙이고 "교집합이 비었다"를 유의성으로 판단. 원리적으로 옳고 `n` 을 명시적 통계량으로 흡수하지만 calibration 비용이 몇 배.
- **Lean**: (c) 가 옳은 방향이되 **re-baseline 이후**. 당장은 (a) — D-019 가 채택한 것. 판단 근거: 지금 필요한 건 판정의 정밀도가 아니라 **판정이 무엇의 함수인지 아는 것**이고, 그건 이미 얻었다.
- **2026-08-02 22:00 답**: 세 기준을 **새 run 없이** 채점 완료 → **D-020**. per-seed ESS 는 보유하지 **않지만** `(n_in_band, n)` 이 충분통계량이라 무관했다. **(b) 폐기** (`ceil(0.9n) == n` for `n ≤ 9` → 이 repo 의 seed 수에서 (a) 와 점별 동일, 산술 반증). **(c) 확정** — `k=n` 에서 bound 가 `n/(n+z²)` 로 `n` 에 증가하므로 D-019 편향을 **역전**; 실측 flip 에서 0.510 → 0.529. bootstrap 이 아니라 **closed form** 으로 (n=8 격자 step 0.125 ≫ 분해할 효과 0.019). default 는 (a) 유지.
- **남은 질문 (여전히 open)**: (c) 의 **threshold** 를 무엇으로 정당화하나. 이번 cycle 은 의도적으로 고르지 않았고, 그 전엔 default 승격 불가.
- **다음 action**: re-baseline 브랜치(STATE #7)가 window 를 (a)/(c) **양쪽으로** 재생성하고 **불일치 집합**을 보고 — 그 집합이 D-019 `n` stamp 가 실제로 필요한 범위다.
- **Status**: partially-answered → (b) refuted / (c) adopted by **D-020**; threshold 미정

## Q-017 — 2026-07-13 — `[uncertainty]` 가려진 obstacle 을 피하려면 epistemic σ 를 어떻게 소비해야 하나 — margin inflation vs additive shadow cost

- **Question**: EPISTEMIC 채널(σ, occlusion shadow + beyond-range)을 MPPI cost 로 소비하는 두 경로 — (a) **additive** `w_epist·σ` (rollout point 마다 σ 비례 가산, field-absolute), (b) **margin inflation** `k·σ` (D-013, 알려진 obstacle clearance 를 σ 만큼 축소, obstacle-relative) — 중 어느 것이 '가려진 obstacle' class 를 실제로 피하게 하나?
- **이번 cycle 결과 (negative, 기하학적)**: `ShadowCostCritic` (a) 를 sandbox 에 구현·검증했으나 **단일 볼록 obstacle 시나리오에서는 (a) 도 (b) 와 똑같이 closed-loop inert**. 근거: 단일 obstacle 의 occlusion shadow = robot→obstacle ray-cone 정확히 그 뒤. rollout 이 그 shadow 에 들어가려면 obstacle 쪽으로 향해야 하고, 그 지점은 이미 stock soft/collision cost 가 지배 → shadow-avoidance ⊆ obstacle-avoidance. 측정: centered obstacle 에서 `w_epist` 0→200 min_clearance Δ=1.9e-12; pre-obstacle pose 에서 softmax-weighted E_w[σ]=~0 already at w_epist=0 (uniform mean 1.234). 즉 **가산항이 재분배할 weight 가 없다**.
- **Trade-off / 남은 갈림길**: (a) 가 정보를 더하는 건 shadow 가 *obstacle-cost 낮은 shortcut* 일 때뿐 — **blind corner / wall (다중·확장 occluder)** geometry, 또는 **beyond-range frontier** 차등(현재 r_sense=5m ≫ rollout reach 1.2m 라 common-mode 로 softmax 에서 상쇄). 대안: reachability risk-region (2503.04563) 또는 CVaR-over-occluded-prior 재정식화.
- **Lean**: (a) mechanism 은 유지(구현 완료, ablation-invariant, w_epist=0 no-op). 다음은 **blind-corner sandbox scenario** 를 만들어 (a) 가 non-inert 임을 closed-loop 로 입증 — 그 전까진 단일 obstacle 벤치로 epistemic gain 을 판단 금지.
- **다음 action**: `eval/scenarios/` 에 wall/L-corner occlusion scenario 추가(가려진 free-space shortcut) → `test_shadow_cost_moves_needle_in_blind_corner` GREEN 목표. resolve 시 D-MMM. refs: PR(이 cycle) + `journal/2026-07/13-*-p3-epistemic-shadow-cost-critic.md`, research feed `research/2026-07/159.md` (occlusion-aware CMPC 2503.04563).
- **Status**: partially-answered (mechanism 구현·검증 완료; 단일 obstacle inert 확인 → blind-corner 시나리오 대기)

## Q-016 — 2026-07-08 — `[arch]` HOLO-MPPI prior interface: 학습된 sampling prior 는 어떤 representation 을 conditioning 입력으로 써야 하나

- **Question**: HOLO-MPPI 패턴으로 offline-trained policy 가 nav2_mppi 의 sampling distribution parameters 를 출력할 때, 그 policy 의 observation input 을 (a) raw P1 BEV features 만 쓸지, (b) P2 latent / residual encoder output 을 쓸지, (c) 둘을 합칠지. 즉, sampling prior 가 *perception representation* 만 조건화되어야 하나 *dynamics latent* 까지 조건화되어야 하나.
- **Trade-off**:
  - **(a) P1 BEV only**: P2 독립 → prototype 지금 시작 가능, 학습 파이프라인 단순; 단, dynamics-regime 정보(venue-specific friction, speed profile) 가 prior 에 없어 cafñe → small_city 이동 시 covariance 적응 제한.
  - **(b) P2 latent only**: dynamics context 풍부하나 #44 merge 전까지 blocked; BEV 시각 맥락 없이 latent 만 쓰면 obstacle geometry 정보 손실.
  - **(c) both (fusion)**: 가장 완전하나 두 encoder 의 학습·inference pipeline 결합 → staging / dependency 복잡화; P5 ablation 전엔 (a) vs (c) contribution 분리 불가.
- **Lean**: **(a) P1 BEV-only prior 먼저** — P2 독립, HOLO-MPPI 핵심 thesis ("representation drives sampler") 을 가장 빠르게 검증; (c) 는 P2 land 후 P4/P5 ablation fork (HOLO-MPPI-fused vs HOLO-MPPI-BEV-only). 근거: 현재 P2 stall 21일 — P2 gated 작업은 scheduling 열위, BEV-only prior 가 thesis 입증 선행 조건.
- **다음 action**: P1 BEV feature extractor (semseg pretrained) prototype 후 `BEVConditionedPrior` 모듈 설계 → P2 land 시 (c) extension 분기. resolve 시 D-MMM. ref: [`research_feed_synthesis_2026_07_05.md`](research_feed_synthesis_2026_07_05.md) Entry 3 + 02:00 feed HOLO-MPPI [[2606.16480]].
- **Status**: open

## Q-015 — 2026-07-05 — `[uncertainty]` P5 harness σ-calibration-quality 축: 소비자 gain sweep 전에 σ 자체가 calibrated 인가를 검증·metric 화해야 하나

- **Question**: §2 의 모든 gain (`k·σ`, `z(δ)·σ_ale`, `σ²_ref`) 은 upstream σ 가 신뢰할 수 있다고 가정한다. §3 metric 은 downstream 결과(near-miss, time-to-goal, cte)만 본다 — σ 의 stated coverage 가 empirical coverage 와 맞는지 않는다. σ 가 mis-calibrated 이면 `(k,δ)` sweep 은 miscalibration 을 gain 에 흡수해 scenario 간 mis-generalize 하고, frozen config 가 "geometry 필요" vs "σ 불신" 구분 불가. **harness 에 σ-calibration stage + calibration-quality metric axis (ECE / interval-coverage / reliability-diagram) 가 §2 gain sweep 의 *upstream* 으로 필요한가, 아니면 gain sweep 의 흡수로 충분한가?**
- **Trade-off**:
  - **gain sweep 이 흡수**: 구현 최소; 그러나 `k` 가 geometry vs σ 불신 구분 불가 → cross-scenario mis-generalization 위험
  - **(a) parametric recalibration** (Rethinking-Gaussian `2603.10407`): 가장 저렴, Gaussian head 가정; §3 ECE axis 는 새 σ 소스 없이 즉시 추가 가능
  - **(b) global conformal coverage** (Scenario-aware UQ `2512.05682`): distribution-free 1 quantile; local variation 무시
  - **(c) perception-conditioned local conformal** (OCULAR `2605.13028`): per-cell BEV-feature 기반; 가장 강하나 non-linear residual+ensemble 에서 linear-Gaussian 가정 포기
- **Lean**: stage warranted (P4 pedestrian covariance 가 miscalibration 가장 쉽게 물림). 시작 = **(a) parametric recalibration + §3 ECE/coverage metric axis** (새 σ 소스 없이 즉시 추가); local conformal (c) 는 P5 ablation fork (vs OCULAR).
- **다음 action**: P4/P5 cycle 이 첫 `(k,δ)` Pareto front 대비 "recalibrated σ 가 front 를 움직이나?" 검증 → yes: D-MMM (stage 추가); no: D-MMM (gain 흡수 충분). 구별: Q-013 (sweep *전략*), D-015 (sweep *소유자*). ref: [`p5_risk_calibration_harness.md`](p5_risk_calibration_harness.md) §3½.

## Q-014 — 2026-07-02 — `[uncertainty]` epistemic 채널의 *response mode*: passive `k·σ` margin 만인가, active-perception / tube 도 필요한가

- **Question**: 설계(§5, stack §4, margin critic §2)는 epistemic vs aleatoric 를 *routing* 으로만 가르고, epistemic 의 *response* 는 암묵적으로 passive back-off (`k·σ` 로 clearance 확대)라 가정한다. 그러나 epistemic uncertainty 는 정의상 **sensing / replanning / data 로 감소 가능** — 그래서 올바른 대응은 물러서기가 아니라 *능동적으로 줄이기* 일 수 있다. epistemic 채널이 `k·σ` margin 에 **더해 (또는 대신)** 두 번째 response term (info-gather / active-perception cost) 을 가져야 하나, 그리고 tube 가 swept scalar `k` 보다 나은 σ→margin map 인가.
- **Trade-off**:
  - **margin-only (`k·σ`)**: 단순, `k=0`⇒baseline 깔끔한 ablation, 구현 최소. 그러나 epistemic 의 reducible 성질을 안 씀 — 미관측 영역을 계속 회피만 하고 관측하러 안 감.
  - **+ active-perception term (PA-MPPI 2509.14978)**: rollout 을 미관측 pose 관측 쪽으로 bias — unobserved-mask(§3)의 능동 짝. 그러나 새 cost term + weight knob, MPPI objective 복잡화.
  - **tube-margin (GP-contraction-tube 2507.02098)**: hand-set `k` 대신 contraction-bounded reachable tube 로 σ→margin 을 *원리적으로* 매핑. 그러나 contraction metric 추정 필요, 무거움.
- **Lean**: shipping default 는 margin-only (`k·σ`, D-013 critic) 유지 — 깔끔한 ablation baseline 이 먼저. active-perception / tube 는 **P3-design / P5-ablation fork** 로 둔다 (margin-only vs margin+active-perception vs tube-margin 3-way). Q-008(margin `k` 의 *value*)과 구별됨 — 이건 response *mode* 자체를 물음. 근거: 2026-06-29 feed 4건 수렴 (TRIAGE 2603.08128 routing-by-dominant-type, PA-MPPI 2509.14978 in-sampler perception cost, GP-contraction-tube 2507.02098, BC-MPPI 2510.00272 aleatoric 짝).
- **다음 action**: P2 ensemble land + P3 critic 구현 후 baseline `k·σ` 먼저 세우고, P5 harness 에서 3-way ablation 추가. resolve 시 D-MMM. ref: [`margin_inflation_cost_critic_interface.md`](margin_inflation_cost_critic_interface.md) §7 (O-2 원문), [`residual_in_rollout_reference.md`](residual_in_rollout_reference.md).

## Q-013 — 2026-06-29 — `[uncertainty]` coupled knob-vector 의 sweep 전략: 2-D `(k,δ)` plane vs full grid vs coordinate-descent

- **Question**: D-015 의 calibration harness 가 5 knob (`k`/`δ`/`α`/`σ²_ref`/`σ²_ref_ale`) 을 어떤 전략으로 sweep 하나. full 5-D grid (기각, combinatorial) vs **2-D `(k,δ)` plane + refs frozen** (harness 문서 default) vs coordinate-descent (저렴하나 `k`↔`σ²_ref` 결합 valley 에서 stall).
- **Trade-off**:
  - **full grid**: unbiased 이나 `O(n^5)` — 사실상 실행 불가
  - **2-D `(k,δ)` plane + refs frozen**: refs 가 gain 과 separable 가정 (1차 근사 true, §1) — 가장 적은 점수로 coupling 의 핵심(`k`·`δ` 가 같은 `d_eff` 조임)을 본다
  - **coordinate-descent**: 최저가이나 `k`↔`σ²_ref` redundancy 를 가장 못 다룸 — 결합 valley 에서 stall
- **Lean**: 2-D `(k,δ)` plane + refs 를 documented default 로 freeze; ±2× ref perturbation 에 Pareto front 가 움직이면 그때만 1-D ref sensitivity pass 추가.
- **다음 action**: P5 cycle 이 첫 measured `(k,δ)` Pareto front 에 대해 resolve → D-MMM 승격. ref: [`p5_risk_calibration_harness.md`](p5_risk_calibration_harness.md) §2/§5.

## Q-012 — 2026-06-27 — `[uncertainty]` aleatoric risk level `δ` / `α`: 어떻게 set 하나 (chance-constraint / CVaR tightening)

- **Question**: `AleatoricRiskCritic` 가 aleatoric `σ` 로 clearance 를 `z(δ)·σ` 만큼 조이거나 CVaR_α tail 을 벌점할 때, target collision prob `δ` (quantile) / tail fraction `α` 를 어디서 얻나. Q-008 의 `k` (epistemic margin gain) 의 aleatoric 형제 knob.
- **Trade-off**:
  - **measured near-miss rate 로 sweep**: 의미 있는 risk 수준, 그러나 P5 eval harness (near-miss/success/time-to-goal) 전엔 없음
  - **hand-pick (예: δ=0.05)**: 즉시 진행, 그러나 임의 — 노이즈 분포·환경에 안 맞을 수 있음
- **Lean**: documented placeholder (`chance_delta=0.05`, `cvar_alpha=0.10`), `cost_weight=0.0` no-op 기본 → P5 measured near-miss 로 calibrate. `k`(Q-008)·`σ²_ref`(Q-009)·`σ²_ref_ale`(Q-011) 와 함께 한 sweep 에 묶음. epistemic `k` 와 달리 데이터 늘어도 0 으로 안 감 (비가역).
- **다음 action**: P5 risk-calibration harness 확보 시 `δ`/`α` set → resolve 시 D-MMM. ref: [`aleatoric_risk_cost_critic_interface.md`](aleatoric_risk_cost_critic_interface.md) §3/§5.

## Q-011 — 2026-06-15 — `[uncertainty]` aleatoric homoscedastic degeneracy guard: spatial-CoV floor 값은

- **Question**: variance head 가 global 단일 노이즈(homoscedastic) 로 collapse 하면 aleatoric 채널이 spatial 정보 0 인 flat raster 가 되는데(유효해 *보이는* 무효 출력), 이를 acceptance 에서 거르는 spatial coefficient-of-variation floor 값을 얼마로.
- **Trade-off**:
  - **엄격한 floor**: collapse 확실히 거름, 그러나 진짜로 균일하게 노이지한 환경을 false-fail
  - **느슨한 floor**: false-fail 적음, 그러나 부분 collapse 통과
- **Lean**: floor 는 #44 가 학습된 뒤에야 set 가능 (`k`/`σ²_ref` 와 같은 un-set 상태). varied-terrain/varied-`(v,ω)` slice 의 측정 CoV 분포로 정함. 채널이 flat ⇒ upstream head-training 버그(렌더러 아님).
- **다음 action**: #44 (heteroscedastic head) land + 학습 후 측정 → floor set. ref: [`aleatoric_channel_bev_rendering.md`](aleatoric_channel_bev_rendering.md) §2/§4.

## Q-010 — 2026-06-15 — `[arch]` D-009 ensemble head: heteroscedastic (NLL) vs MSE point — aleatoric 채널 존재 여부를 가름

- **Question**: D-009 scaffold (PR #44) 의 ensemble head 가 per-dim 예측분산 `σ²_k` 를 내는 heteroscedastic(NLL 학습) 인가, 단순 MSE point regression 인가. 후자면 aleatoric 신호가 *아예 없어* aleatoric 채널·`AleatoricRiskCritic` 둘 다 build 불가. epistemic 은 means 만 필요해 영향 없음.
- **Trade-off**:
  - **NLL variance heads**: epi/ale split (핵심 P3 deliverable) unlock, 비용은 출력 dim +1 + Gaussian NLL loss
  - **MSE point heads**: 단순, epistemic-only, 그러나 P3 의 절반(aleatoric)을 포기
- **Lean**: NLL heads — epi/ale split 이 P3 의 reason-for-being 이고 추가 비용이 새 모델이 아니라 출력 1차원 + loss 교체뿐.
- **다음 action**: #44 머지 전 scaffold 가 head type 확정해야 함 (user/구현 cycle). resolve 시 D-MMM. ref: [`aleatoric_channel_bev_rendering.md`](aleatoric_channel_bev_rendering.md) §1/§7.

## Q-009 — 2026-06-13 — `[uncertainty]` epistemic channel 정규화 기준 `σ²_ref`: 어떻게 set 하나

- **Question**: ensemble `σ²` 를 BEV 채널 `[0,1]` 로 매핑할 때 fixed reference `σ²_ref` 가 필요한데 (per-frame min-max 는 cross-frame 비교성 파괴 → P5 calibration metric 무력화), 그 값을 어디서 얻나. Q-008 의 `k` margin gain 과 형제 knob.
- **Trade-off**:
  - **held-out OOD percentile (예: 95th)**: 의미 있는 기준, 그러나 OOD set 이 real rosbag/terrain-shift 데이터 생기기 전엔 없음
  - **hand-pick 임시값**: 즉시 진행 가능, 그러나 의미 없는 스케일 → 채널이 임의적
- **Lean**: 문서화된 placeholder 로 두되 hard-code 금지 (config), P5 measured OOD spread 로 calibrate. Q-008 (`k`) 와 함께 sweep.
- **다음 action**: P5 uncertainty-calibration harness (epi↑ on OOD) 확보 시 `σ²_ref` + `k` 동시 set → resolve 시 D-MMM. ref: [`epistemic_channel_bev_rendering.md`](epistemic_channel_bev_rendering.md) §2.3/§5.

## Q-008 — 2026-06-12 — `[uncertainty]` epistemic-margin gain `k`: 어떻게 set 하나 (variance→safety routing)

- **Question**: ensemble `σ` 를 안전 margin 으로 라우팅할 때 (additive `λσ²` 아닌 margin-inflation) margin = `k·σ` 의 gain `k` (m / unit σ) 를 어떻게 정하나. Stochastic-MPPI 는 chance-constraint level `ε` 에서 유도하나 우리는 `ε` target 도 정량 harness 도 P5 전엔 없음.
- **Trade-off**:
  - **measured near-miss 로 sweep (P5)**: 의미 있는 값, 그러나 eval harness 전엔 측정 불가
  - **hand-pick 임시값**: 즉시 진행, 그러나 임의 스케일 → margin 이 의미 없는 보수성
- **Lean**: config 로 노출 (`k_margin_per_sigma`), **default `0.0` ⇒ exact-baseline no-op** 로 plumbing 먼저 landing, P5 near-miss metric 으로 sweep. `σ²_ref`(Q-009) 와 형제 knob — 함께 calibrate.
- **다음 action**: (1) routing **resolved** this cycle — `k·σ` 가 standalone `RiskInflationCritic` (overload `CostCritic` 아님) 으로 진입, mask-gated/tighten-only/bounded by `inflation_radius`. → D-013 으로 승격 예정 (decisions.md 가 #52 prepend 와 충돌 안 할 때). (2) `k` **값** 은 P5 harness 확보 시 set → resolve 시 D-MMM. ref: [`margin_inflation_cost_critic_interface.md`](margin_inflation_cost_critic_interface.md), [`residual_in_rollout_reference.md`](residual_in_rollout_reference.md) §Axis-2.
- **Status**: partially-answered (routing → D-013 pending; `k` value open for P5)

## Q-007 — 2026-05-31 — `[arch]` residual 의 nominal model: analytic unicycle vs 학습 LNN

- **Question**: C1 ensemble residual 의 nominal 항을 analytic unicycle (현재 bootstrap) 로 둘지, STRIDE-style 학습 LNN 으로 둘지.
- **Trade-off**:
  - **analytic unicycle**: 즉시 구현, residual 이 순수 mismatch 만 학습 → 해석 쉬움. 위험: real diff-drive 에서 nominal 자체가 부정확하면 residual 부담 ↑
  - **학습 LNN**: nominal 이 데이터로 보정 → residual 가벼움. 위험: 학습 nominal+학습 residual 이중 학습, unicycle bootstrap 만으론 식별 어려움
- **Lean**: analytic-nominal 우선 (D-009). real diff-drive/Gazebo 데이터 생기면 재평가.
- **다음 action**: U1 distribution-shift probe 결과 + 실데이터 확보 후 결정. resolve 시 D-MMM.

## Q-006 — 2026-05-28 — `[arch]` Decision log 의 cron-agent append 권한 범위

- **Question**: cron Builder/Curator 가 `decisions.md` 에 직접 append 할 수 있는가? doc 인데 doc 자체에 대한 결정이 있을 수 있어서 self-reference.
- **Trade-off**:
  - **자율 append**: 매 cycle 의 큰 결정 즉시 기록, 정체 없음. 위험: agent 가 trivial 한 변경도 D-NNN 으로 부풀림 → 가독성 ↓
  - **사람 only**: 신호 대 잡음 ↑, 그러나 사용자 부재 시 timeline 결손
- **Lean**: agent append 허용하되 prompt 에 "architecture/scope/priority pivot 만" 명시. trivial → journal 만.
- **다음 action**: Phase 4 REPORT step 갱신 (issue 신규 #41) 시 prompt 검증.

## Q-005 — 2026-05-28 — `[priority]` reference paper 8건 모두 분석할 시간 있나

- **Question**: feed 에 14+ paper, issue #17-21 + #28-31 + #33-37 + #38-40 = 24개 open. Builder cycle 당 1 issue. 24일 backlog → DPCBF/DRA-MPPI/DualGuard 실측 ablation (#34) 진입 시간 ↓.
- **Trade-off**:
  - **순차 처리**: 정착 보장, 늦음
  - **병렬 우선순위**: DPCBF Stage A (#33) + 5채널 spec (#35) + scenario yaml (#38) 세 thread 동시 → 다른 issues 는 Backlog
- **Lean**: 병렬 3 thread, 나머지 Backlog 유지. Researcher 가 새 paper 추가 시 자동 Priority=P3 (낮춤).
- **다음 action**: 다음 Builder cycle 의 PLAN 단계가 이 lean 반영하는지 모니터.

## Q-004 — 2026-05-27 — `[uncertainty]` 5채널 가중치 — fixed / env-conditioned / learned?

- **Question**: P3 의 5 risk channel (static/dynamic/traversability/epistemic/aleatoric) 각 `w_c` 를 어떻게 결정?
  - (a) hand-tuned constant
  - (b) environment-class lookup (`docs/environment_taxonomy.md` A~E 별)
  - (c) 학습 (context → weights regression)
- **Trade-off**: (a) 단순/투명, (b) 적당히 일반화, (c) 일반화 ↑ but black-box + 학습 데이터 필요
- **Lean**: P3 v0 = (a), P5 calibration 단계에서 (b), P6 outputs 단계에서 (c) 비교.
- **참조**: `docs/dynamic_obstacles_uncertainty_track.md` § 7 open question 첫 항목
- **다음 action**: issue #35 (5채널 spec) 작성 시 § "weighting strategy" 섹션에 위 3 옵션 명시.

## Q-003 — 2026-05-26 — `[arch]` HuNav (반응형 보행자) 도입 시점

- **Question**: 현재 scripted actor 가 한계 (S05 overtaken, S06 cut-in 의 "반응" 검증 X). HuNav/PedSim 도입 = P4 본격? 아니면 P3 와 병행?
- **Trade-off**:
  - **P4 본격**: 5채널 spec (P3) 안정화 후 도입 → 안전
  - **P3 와 병행**: 반응형 actor 가 5채널 검증 신뢰도 ↑ but install 무거움 (RVO2 cmake + Gazebo plugin 포팅 등)
- **Lean**: P3 와 병행하되 작은 prototype (1-2 명) 부터. issue 별도 작성 예정.
- **다음 action**: HuNav ROS2 Jazzy fork 가용성 조사 (research feed item 만들기).

## Q-002 — 2026-05-26 — `[meta]` Decision/Open-question 자동 추출 신뢰도

- **Question**: cron Builder 가 journal 에 적은 "Recommended next priorities" 가 진짜 우선순위인가? 그냥 task 끝의 형식적 한 줄 아닌가?
- **Trade-off**: 신뢰하면 자동 Today 승격 가능 (자율성 ↑), 의심하면 사람 review 필요 (정확성 ↑)
- **Lean**: 신뢰하되 매주 wrap 의 회고에서 "지난 주 next priorities 중 실현 비율" 측정 (calibration metric).
- **다음 action**: wrap.md 에 "지난 주 priority 명중률" 한 줄 추가 (issue 별도).

## Q-001 — 2026-05-25 — `[license]` reference 4종 모두 license 미명시 — 어디까지 vendoring?

- **Question**: safe_control (264⭐), cfm_mppi, DR-MPC, TCFM 모두 LICENSE 파일 X. 차용 어디까지?
- **Trade-off**: vendoring → 빠른 통합 + license 위험 / use-in-place → license 안전 + setup 비용
- **Lean**: D-005 로 결정 — use-in-place + wrapper. **resolved → D-005**.
- ~~Status: open~~
- **Status**: resolved → D-005

---

## Append 정책 (cron-agent)

매 cycle 의 REPORT phase 에서:
- 이번 cycle 중 결론 안 났지만 의미 있는 trade-off 만났으면 → 이 파일 prepend (Q-NNN)
- 트리비얼한 모호함 (단순 어떤 변수명 쓸까) → journal 의 "open question" 섹션만
- 이미 결정 났으면 → `decisions.md` 의 D-NNN 으로 직접 가고 여기 X

Q 번호도 strictly 증가, 절대 재사용 X. 답 나면:
1. Q-NNN 의 Status `resolved → D-MMM` 으로 변경
2. `decisions.md` 에 D-MMM entry 추가하면서 Refs 에 Q-NNN 인용

_Last manual update: 2026-05-28 KST_
