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
