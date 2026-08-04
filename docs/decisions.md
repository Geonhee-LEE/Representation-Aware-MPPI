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
