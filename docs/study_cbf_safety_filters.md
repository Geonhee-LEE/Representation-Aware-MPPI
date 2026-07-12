# 📖 공부 노트 — CBF 와 Safety Filter, 그리고 MPPI 와의 합성

> `eval/mppi_sandbox/controllers/cbf_mppi.py` 가 구현한 것을 **개념부터** 이해하기 위한
> 자습 문서. 수식은 유도 과정을 생략하지 않고, 용어는 처음 나올 때 정의한다.
> 관련 코드: [`cbfkit_analysis.md`](cbfkit_analysis.md), [`mppi_sandbox.md`](mppi_sandbox.md)

---

## 0. 왜 이걸 공부하나

MPPI 는 **성능** 을 잘 낸다 — cost 를 잘 설계하면 자연스러운 회피가 나온다. 하지만
MPPI 의 회피는 *확률적* 이다: 샘플이 운 나쁘면, cost 가중치가 어긋나면, 뚫는다.
우리 sandbox 실측이 정확히 그랬다: vanilla MPPI 가 head-on 보행자를 **clearance
0.005 m** 로 스쳤다. cost 를 아무리 키워도 "절대 안 뚫는다" 는 **보장** 은 없다.

CBF (Control Barrier Function) 는 반대편 극단이다: 성능은 모르겠고, **안전 집합을
절대 벗어나지 않는다** 는 수학적 보장을 준다. 그래서 실무 아키텍처는 둘을 합성한다:

```
MPPI (성능: 경로추종 + 부드러운 회피)  →  u_nom
CBF-QP (안전: u_nom 을 안전한 방향으로 최소 수정)  →  u
```

이 구조가 cbfkit 의 "safety filter" 파이프라인이고, 우리 `cbf_mppi` 다.
실측에서 **cbf(risk_mppi) 조합이 4-way 매트릭스 일관 1위** 였다 — 성능 layer 와
안전 layer 의 분리가 실제로 작동한다는 첫 정량 증거.

---

## 1. 안전을 "집합" 으로 정의하기

### 1.1 Safe set

시스템 상태 $x \in \mathbb{R}^n$ (우리: $x = [p_x, p_y, \theta]$).
**안전 집합(safe set)** $\mathcal{C}$ 를 어떤 함수 $h$ 의 0-초과집합(superlevel set)으로 정의:

$$\mathcal{C} = \{ x : h(x) \ge 0 \}, \qquad \partial\mathcal{C} = \{x : h(x) = 0\}$$

예 — 반지름 $d_{safe}$ 원형 장애물 회피:

$$h(x) = \|p - p_o\|^2 - d_{safe}^2$$

- $h > 0$: 장애물 밖 (안전)
- $h = 0$: 경계에 정확히 접촉
- $h < 0$: 침투 (위험)

**핵심 발상의 전환**: "장애물을 피하라" 라는 행동 지시 대신, "이 스칼라 함수가
음수가 되지 않게 하라" 라는 **불변식(invariant)** 으로 안전을 서술한다. 함수 하나가
안전의 전부를 담는다.

### 1.2 Forward invariance (전방 불변성)

> **정의**: 집합 $\mathcal{C}$ 가 *forward invariant* 하다 ⟺ $x(0) \in \mathcal{C}$
> 이면 모든 $t \ge 0$ 에 대해 $x(t) \in \mathcal{C}$.

즉 "안에서 시작하면 영원히 안에 머문다". 안전 보장 = safe set 의 forward invariance.

어떻게 보장하나? 직관: **경계에 도달하는 순간, 상태가 밖으로 나가는 방향의 속도
성분이 없으면 된다** (Nagumo's theorem, 1942). 수식으로:

$$h(x) = 0 \;\Rightarrow\; \dot{h}(x) \ge 0$$

경계에서 $h$ 가 감소하지만 않으면 절대 음수로 못 넘어간다.

---

## 2. Control Barrier Function — 핵심 정리

### 2.1 제어-아핀 시스템과 Lie derivative

CBF 이론은 **제어-아핀(control-affine)** 시스템을 가정한다:

$$\dot{x} = f(x) + g(x)\,u$$

- $f(x)$: drift (제어 없이 저절로 흐르는 부분)
- $g(x)$: 제어 입력이 상태에 작용하는 방향
- 우리 unicycle: $\dot{p}_x = v\cos\theta,\ \dot{p}_y = v\sin\theta,\ \dot\theta = \omega$,
  $u = [v, \omega]$ → $f = 0$, $g(x) = \begin{bmatrix} \cos\theta & 0 \\ \sin\theta & 0 \\ 0 & 1 \end{bmatrix}$

$h$ 의 시간 미분을 chain rule 로 전개하면:

$$\dot{h} = \nabla h(x)^\top \dot{x} = \underbrace{\nabla h^\top f(x)}_{L_f h} + \underbrace{\nabla h^\top g(x)}_{L_g h}\,u$$

> **용어 — Lie derivative**: $L_f h = \nabla h^\top f$ 는 "벡터장 $f$ 를 따라 흐를 때
> $h$ 가 변하는 속도". $L_g h$ 는 "제어가 $h$ 를 미는 지렛대". 그냥 방향미분이다 —
> 기호가 무섭게 생겼을 뿐.

**중요한 관찰**: $\dot h$ 이 $u$ 에 대해 **선형** 이다. 이게 나중에 QP (2차계획법) 로
풀리는 이유의 전부다.

### 2.2 class-K 함수와 zeroing CBF 조건

Nagumo 조건 ($h=0$ 에서만 $\dot h \ge 0$) 은 경계에서 갑자기 발동해서 제어가
불연속이 된다. 대신 **경계에 가까울수록 점진적으로 제동** 을 거는 조건을 쓴다:

$$\boxed{\;\dot{h}(x, u) \ge -\alpha\big(h(x)\big)\;}$$

> **용어 — class-K 함수** $\alpha(\cdot)$: $\alpha(0)=0$ 이고 순증가(strictly
> increasing)인 함수. 실무에선 거의 항상 선형 $\alpha(h) = \alpha_0 h$ ($\alpha_0 > 0$
> 상수) 를 쓴다 — cbfkit 의 `linear_class_k(10.0)` 이 바로 이것.

이 부등식을 읽는 법 ($\alpha(h) = \alpha_0 h$ 기준):

- **장애물에서 멀 때** ($h$ 큼): $\dot h \ge -\alpha_0 h$ 는 매우 느슨 — $h$ 가
  빠르게 감소해도 됨 (접근 허용)
- **경계 근처** ($h \to 0$): 허용 감소율이 0 으로 조임 — 지수적 감속
- **결과**: $h(t) \ge h(0)e^{-\alpha_0 t} \ge 0$ (비교 정리) — **$h$ 는 절대 0 을
  뚫고 내려갈 수 없다**

$\alpha_0$ 는 "공격성 다이얼": 크면 경계 직전까지 빠르게 접근 후 급제동, 작으면
멀리서부터 살살 감속. 우리 `cbf_alpha=1.0`.

> **용어 — zeroing CBF vs reciprocal CBF**: 위처럼 $h$ 자체를 쓰는 것이 *zeroing*
> CBF (현대 표준). 옛 문헌의 *reciprocal* CBF 는 $B = 1/h$ 처럼 경계에서 발산하는
> 함수를 썼는데 수치적으로 나빠서 요즘은 잘 안 쓴다.

### 2.3 CBF 의 공식 정의

> **정의** (Ames et al.): $h$ 가 시스템의 **CBF** 다 ⟺ 어떤 class-K $\alpha$ 에 대해
>
> $$\sup_{u \in U}\Big[ L_f h(x) + L_g h(x)\,u \Big] \ge -\alpha(h(x)) \quad \forall x \in \mathcal{C}$$

말로: "**어떤 상태에서도, 허용 입력 중에 위 부등식을 만족시키는 $u$ 가 최소 하나는
존재한다**". 이 존재성이 깨지는 순간 (입력 한계 $U$ 때문에 아무 $u$ 도 부등식을 못
맞추는 상태) 이 바로 **QP infeasibility** — §5.3 에서 다시 만난다.

**정리** (Ames et al. 2017): $h$ 가 CBF 이고 제어기가 항상 위 부등식을 만족하는 $u$
를 선택하면, $\mathcal{C}$ 는 forward invariant. □

---

## 3. CBF-QP — Safety Filter 의 수학

성능 제어기 (우리: MPPI) 가 $u_{nom}$ 을 제안한다. filter 는 **안전 제약을 만족하는
입력 중 $u_{nom}$ 에 가장 가까운 것** 을 고른다:

$$u^* = \arg\min_{u \in U} \;\|u - u_{nom}\|^2 \quad \text{s.t.} \quad L_f h_i + L_g h_i\, u \ge -\alpha(h_i) \;\; \forall i$$

- 목적함수: $u$ 에 대해 볼록 2차 (quadratic)
- 제약: $u$ 에 대해 선형 (§2.1 의 관찰)
- → **QP (Quadratic Program)**. 항상 유일해, 밀리초 해석 가능

> **용어 — QP**: 2차 목적함수 + 선형 제약의 볼록 최적화. 장애물 $i$ 마다 제약 한
> 줄. cbfkit 은 이걸 위해 자체 interior-point solver 까지 만들었다 (2×5 문제에서
> 880× 빠름).

**기하적 직관**: 제약들이 입력 공간 $(v, \omega)$ 를 halfplane 들로 자른다. 교집합이
"지금 이 순간 안전한 명령들의 집합". $u_{nom}$ 이 그 안이면 **그대로 통과** (filter
는 투명 — 우리 pytest 가 byte-identical 로 보증하는 것), 밖이면 집합 경계로 **수직
투영** 된다. filter 라는 이름이 여기서 나온다: 평소엔 없는 듯, 위험할 때만 개입.

### 우리의 QP solver (`solve_qp_2d`)

입력이 2차원 ($v, \omega$) 이라는 점을 이용해 **active-set 전수조사** 로 정확해를 얻는다:

> **용어 — active set**: 최적해에서 등호로 성립하는 제약들. 2D QP 의 최적해는
> (a) 무제약 최소점 ($u_{nom}$ 자체), (b) 제약 1개의 경계로 투영한 점, (c) 제약
> 2개의 교점 — 이 셋 중 하나다 (KKT 조건의 기하). 제약이 $m$ 개면 후보
> $1 + m + \binom{m}{2}$ 개를 다 확인해도 몇십 개 — 외부 solver 없이 정확해.

---

## 4. Unicycle 의 함정 — Relative Degree

### 4.1 문제

거리 barrier $h = \|p - p_o\|^2 - d_{safe}^2$ 를 unicycle 에 그대로 쓰면:

$$\dot h = 2(p - p_o)^\top \dot p = 2\Delta^\top \begin{bmatrix} v\cos\theta \\ v\sin\theta \end{bmatrix}, \qquad \Delta := p - p_o$$

$\dot h$ 에 $v$ 는 있는데 **$\omega$ 가 없다**. $L_g h$ 의 $\omega$ 열이 0 —
조향이 barrier 에 즉각 영향을 못 준다 ($\omega$ 는 $\theta$ 를 바꾸고, $\theta$ 가
다음 미분에서야 위치에 작용).

> **용어 — relative degree**: 입력 $u$ 가 출력 $h$ 에 나타날 때까지 미분해야 하는
> 횟수. 위 경우 $v$ 에 대해선 1, $\omega$ 에 대해선 2. CBF-QP 는 relative degree 1
> 을 가정하므로 이대로면 QP 가 조향을 활용하지 못한다 — 최악의 경우 정면 장애물
> 앞에서 "감속" 만 가능하고 "회피" 불가.

### 4.2 해법 1 — Offset point (우리가 쓴 것)

로봇 중심 대신 **차축에서 $l$ 만큼 앞의 점** 을 제어점으로 삼는다
(Olfati-Saber 2002 의 near-identity diffeomorphism; cbfkit 의
`olfatisaber2002approximate` 모델이 이것):

$$p_l = p + l\begin{bmatrix}\cos\theta\\\sin\theta\end{bmatrix} \;\;\Rightarrow\;\; \dot p_l = \underbrace{\begin{bmatrix}\cos\theta & -l\sin\theta\\ \sin\theta & \phantom{-}l\cos\theta\end{bmatrix}}_{J(\theta)} \begin{bmatrix}v\\\omega\end{bmatrix}$$

$\det J = l > 0$ — **$J$ 가 full-rank**. 이제 barrier 를 $p_l$ 기준으로 다시 쓰면:

$$h = \|p_l - p_o\|^2 - d_{safe}^2, \qquad \dot h = 2\Delta_l^\top \big(J(\theta)\,u - v_o\big)$$

$v$ 와 $\omega$ 둘 다 $\dot h$ 에 1차로 등장 → relative degree 1 회복, QP 한 방.
비용: 안전이 로봇 중심이 아니라 offset 점 기준으로 보장됨 → $d_{safe}$ 에 $l$ 만큼
여유를 얹는다 (우리 `offset_l=0.15`, `safety_margin` 에 흡수).

### 4.3 해법 2 — HOCBF / Exponential CBF (참고)

barrier 를 층층이 쌓는 정공법: $\psi_0 = h$, $\psi_1 = \dot\psi_0 + \alpha_1(\psi_0)$,
… 마지막 층에서 $u$ 가 나올 때까지. cbfkit 의 `rectify_relative_degree(...,
form="exponential")` 이 이 계열 (Exponential CBF, Nguyen & Sreenath 2016; 일반형
HOCBF, Xiao & Belta 2019). 우리는 v0 에서 offset point 가 더 단순해서 채택 안 함.

---

## 5. 현실의 세 가지 균열 — 우리가 직접 밟은 것들

### 5.1 움직이는 장애물: time-varying barrier

$p_o(t)$ 가 움직이면 $h(x, t)$ 가 되고 편미분 항이 추가된다:

$$\dot h = \frac{\partial h}{\partial t} + L_f h + L_g h\, u, \qquad \frac{\partial h}{\partial t} = -2\Delta_l^\top v_o$$

**직관**: 장애물이 나에게 다가오면 ($\Delta_l^\top v_o > 0$ 방향) 이 항이 $\dot h$ 를
갉아먹는다 → QP 제약이 그만큼 타이트해져 **더 일찍, 더 세게** 회피가 발동한다.
이게 "velocity feedforward". 코드에선 `ob.velocity(t)` (central difference) 가 이 항.

이걸 안 넣으면? 장애물을 정지물로 취급 — 다가오는 보행자에 대해 늘 한 박자 늦는다.
더 정교한 계열이 collision-cone CBF (C3BF) / **DPCBF** (상대속도 기하까지 barrier 에
넣음, §7).

### 5.2 이산시간: 연속 이론 vs 0.1 s 제어주기

이론은 연속시간 ($\dot h$) 인데 구현은 $\Delta t = 0.1$ s 마다 명령. 한 스텝 안에서
상태가 이론이 모르는 곳까지 가버릴 수 있다 → 경계를 약간 파고드는 **침투 잔차**.
이산시간 CBF 조건은:

$$h(x_{k+1}) \ge (1-\gamma)\,h(x_k), \qquad \gamma \in (0, 1]$$

우리는 연속 조건 + margin 으로 잔차를 흡수하는 실용 노선 (실측 잔차 ~0.05 m).

### 5.3 입력 지연: kinematic CBF vs accel-limited plant — **실제로 당한 사고**

CBF 는 "명령 = 실현" 을 가정한다. 우리 plant 는 가속 제한이 있다
(`accel_max=1.0 m/s²`): $v$ 명령을 줘도 실제 속도는 스텝당 $\pm 0.1$ m/s 씩만 움직인다.

**증상 (2026-07-11 실측)**: margin 0.15 를 걸었는데 clearance **0.054** — barrier
침투. QP 는 "지금 당장 $v=0$" 이 가능하다고 믿고 늦게까지 버텼는데, plant 는 0.4 →
0 까지 0.4 초가 걸렸다.

**수리**: QP 의 입력 box 를 명목 한계가 아니라 **1-step 도달가능 집합** 으로 교체:

$$v \in [\,v_k - a_{max}\Delta t,\; v_k + a_{max}\Delta t\,] \cap [v_{min}, v_{max}]$$

이러면 "QP 가 고르는 명령" = "실제로 실현되는 명령" 이 되어 제약 평가가 정직해진다.
결과: clearance 0.054 → **0.205** (≈ margin). 교훈: **CBF 의 보장은 모델 가정만큼만
유효하다**. 가정(순간 속도 변경)이 깨지면 보장도 깨진다 — 이 gap 을 정식으로 다루는
계열이 robust CBF (§7).

이것이 QP infeasibility 문제와도 연결된다: box 가 좁아질수록 "만족 가능한 $u$" 가
없어질 수 있다. 우리 fallback 은 최소위반해 반환 (전문 계열: gatekeeper — §7).

---

## 6. MPPI 복습 — 그리고 왜 "합성" 인가

### 6.1 MPPI 한 장 요약

(이미 아는 내용이니 notation 맞추기용으로만.)

제어열 $U = (u_0, \dots, u_{H-1})$ 에 노이즈 $\epsilon^{(k)} \sim \mathcal{N}(0,\Sigma)$
를 얹어 $K$ 개 rollout, 각 비용 $J^{(k)}$ 계산, softmax 가중 평균으로 갱신:

$$w^{(k)} = \frac{\exp(-\frac{1}{\lambda}(J^{(k)} - \beta))}{\sum_j \exp(-\frac{1}{\lambda}(J^{(j)} - \beta))}, \qquad U \leftarrow U + \sum_k w^{(k)}\epsilon^{(k)}$$

$\beta = \min_k J^{(k)}$ (수치 안정화), $\lambda$ = temperature. 이 형태는
free-energy / KL 최적화의 importance sampling 근사에서 유도된다 (Williams et al.,
information-theoretic MPC).

### 6.2 왜 MPPI 단독으론 안전 보장이 안 되나

1. **표본 유한성**: 안전한 rollout 이 $K$ 개 샘플 안에 없으면 그 방향은 후보에도 없다
2. **soft cost**: collision penalty $10^4$ 도 결국 유한 — 다른 항과 *교환 가능* 하다.
   보장이 아니라 흥정이다
3. **분포 가정**: 노이즈 공분산이 상황과 안 맞으면 탐색이 위험 지대를 못 벗어난다

우리 실측이 증거: stock MPPI, head-on clearance **0.005 m**. cost 로 안전을 사려면
비쌀 때 (w_risk↑) 성능(cte)을 내주는 Pareto 흥정이 될 뿐, 하한은 없다.

### 6.3 합성의 논리 — 그리고 우리 프로젝트의 자리

$$u = \Pi_{\mathcal{S}(x)}\big[\,u_{MPPI}(x)\,\big], \qquad \mathcal{S}(x) = \{u : \text{CBF 제약 만족}\}$$

(투영 $\Pi$ 가 QP.) 역할 분담이 코드 경계로 강제된다:

| layer | 담당 | 실패 모드 |
|---|---|---|
| MPPI (+representation) | 성능: 경로추종, 예측적 회피, 부드러움 | 확률적 miss (graze) |
| CBF-QP | 안전: 최악의 순간 하한 | liveness 없음 (멈춰버림) |

4-way 실측이 이 표 그대로 나왔다: risk_mppi 는 **미리** 넓게 돌고 (예측 smear),
CBF 는 마지막 순간 **하한** 을 지킨다 (h ≥ 0). 조합 cbf(risk) 이 일관 1위,
그러나 cut-in 의 freezing (goal=0) 은 **둘 다 못 푼다** — 안전 filter 는 살아있음
(liveness) 을 보장하지 않는다.

> **용어 — safety vs liveness**: safety = "나쁜 일이 절대 안 일어남" (충돌 없음),
> liveness = "좋은 일이 결국 일어남" (목표 도달). CBF 는 safety 전용. 정지도
> 안전하므로 filter 는 기꺼이 영원히 멈춘다 — freezing robot problem. 해법 계열:
> gatekeeper (backup trajectory 검증), CLF 병용 (§7).

---

## 7. 확장 계열 지도 — 각 한 문단 + 우리 매핑

**CLF-CBF-QP** — CLF (Control Lyapunov Function) 는 CBF 의 쌍둥이: "수렴" 을
$V(x) \to 0$ 불변식으로 인코딩. QP 에 $\dot V \le -c V + \delta$ (slack $\delta$) 로
같이 넣으면 안전(hard) + 수렴(soft) 동시. slack 이 안전과 수렴이 충돌할 때 수렴을
양보시키는 밸브다. cbfkit `vanilla_cbf_clf_qp_controller`. 우리는 수렴을 MPPI 가
담당하므로 CLF 생략.

**Stochastic CBF** — plant 가 SDE $dx = (f + gu)\,dt + \sigma(x)\,dw$ 일 때. Itô
공식 때문에 $\dot h$ 에 2차 보정항이 붙는다:
$\mathcal{L}h = L_f h + L_g h\,u + \tfrac{1}{2}\mathrm{tr}\!\big(\sigma^\top \nabla^2 h\, \sigma\big)$.
노이즈가 클수록 (trace 항) 제약이 타이트해짐 → **불확실성이 자동으로 margin 을 산다**.
우리 D-013 epistemic $k\sigma$ margin 의 원리적 대응물 — feed 에 "k·σ heuristic 이
stochastic CBF 의 근사인가" 를 open TODO 로 걸어둠.

**Robust CBF** — bounded disturbance $\|w\| \le \bar w$ 의 최악을 가정해 제약을
$\dot h \ge -\alpha(h) + L_w h\,\bar w$ 로 조임. §5.3 의 accel-lag 을 정식으로
다루려면 이 틀 (lag 를 disturbance 로 모델링). 우리는 v0 에서 margin 흡수로 대체.

**Risk-aware CVaR-CBF** — 안전을 확률로: $\mathrm{CVaR}_\delta[h] \ge 0$.
> **용어 — VaR / CVaR**: $\mathrm{VaR}_\delta$ = 최악 $\delta$-분위수,
> $\mathrm{CVaR}_\delta = \mathbb{E}[X \mid X \le \mathrm{VaR}_\delta]$ — "최악
> $\delta$ 꼬리의 평균". 평균보다 보수적, worst-case 보다 관대한 중간 지대.

우리 D-014 `AleatoricRiskCritic` (chance-constraint $d_{eff} = d - z(\delta)\sigma$ /
CVaR tightening) 가 정확히 이 계열의 cost-side 번역. cbfkit 구현이 검증 기준.

**C3BF (Collision Cone CBF)** — barrier 를 거리 대신 **상대속도 기하** 로: 상대속도
벡터가 충돌 원뿔(collision cone) 밖을 향하게 강제. 다가오는 장애물에 거리 CBF 보다
훨씬 덜 보수적. safe_control 에 구현 있음.

**DPCBF (Dynamic Parabolic CBF, ICRA 2026)** — C3BF 의 원뿔 경계를 **포물선** 으로
바꿔 dense crowd (100 obstacles) 에서 cone 계열의 과보수/데드락을 풀었다. 우리
issue #33/#65 S1 잔여 — cut-in freezing 의 1순위 후보.

**gatekeeper (Agrawal & Panagou)** — filter 대신 **궤적 단위 검증**: nominal 궤적의
접두사 + 검증된 backup 궤적 (정지/선회) 을 이어 붙여 "영원히 안전한" 복합 궤적만
집행. liveness 문제를 backup 의 존재로 우회. safe_control `run_evade.sh` 가 이것
(nominal 91% / backup 9% 실측).

**Neural CBF** — $h(x)$ 자체를 데이터에서 학습 (safe/unsafe 라벨 → NN). 해석적으로
못 쓰는 장애물 (point cloud, 학습된 occupancy) 에 CBF 를 확장. **우리 북극성과의
접점**: P3 의 학습된 risk field 가 충분히 좋아지면, 그 field 의 level set 을 neural
CBF 로 인증하는 경로가 열린다 — "학습 representation + classical 보장" 의 종착점 후보.

---

## 8. 수식 ↔ 코드 대응표 (`cbf_mppi.py`)

| 수식 | 코드 |
|---|---|
| $p_l = p + l[\cos\theta, \sin\theta]^\top$ | `p_l = np.array([x + self.l*c, y + self.l*s])` |
| $J(\theta)$ | `J = np.array([[c, -self.l*s], [s, self.l*c]])` |
| $h = \|\Delta_l\|^2 - d_{safe}^2$ | `h = delta @ delta - d_safe**2` |
| $\dot h = 2\Delta_l^\top(J u - v_o) \ge -\alpha h$ | `rows_a.append(2*delta @ J)`; `rows_b.append(-alpha*h + 2*delta @ v_o)` |
| $\partial h/\partial t$ (velocity feedforward) | `ob.velocity(t)` — schedule central difference |
| 1-step 도달가능 box (§5.3) | `v_lo = max(lim.v_min, v - lim.accel_max*self.dt)` … |
| $\arg\min \|u - u_{nom}\|^2$ s.t. $Au \ge b$ | `solve_qp_2d(u_nom, A, b)` — active-set 전수조사 |
| filter 투명성 (제약 비활성 시 $u = u_{nom}$) | pytest `test_no_obstacles_passes_nominal_through_exactly` |

파라미터 감각:

| 파라미터 | 값 | 의미 | 키우면 |
|---|---|---|---|
| `cbf_alpha` | 1.0 | class-K 기울기 | 경계까지 과감히 접근 후 급제동 |
| `safety_margin` | 0.25 | $d_{safe}$ 의 여유분 | 안전↑, cte·시간↑ (Pareto) |
| `offset_l` | 0.15 | 제어점 offset | 조향 지렛대↑, 보장 지점이 중심에서 멀어짐 |

---

## 9. 용어집 (알파벳순)

| 용어 | 정의 |
|---|---|
| **active set** | 최적해에서 등호로 성립하는 제약 집합. 2D QP 는 전수조사 가능 |
| **class-K function** | $\alpha(0)=0$, 순증가. CBF 제약의 "제동 곡선" |
| **CBF** | safe set 의 forward invariance 를 입력 존재성으로 보장하는 함수 |
| **CLF** | 수렴( $V \to 0$ )을 같은 틀로 보장하는 쌍둥이 |
| **control-affine** | $\dot x = f(x) + g(x)u$ — $u$ 에 선형. QP 가 성립하는 전제 |
| **CVaR** | 최악 $\delta$-꼬리의 기대값. 평균과 worst-case 의 중간 위험 척도 |
| **forward invariance** | 집합 안에서 시작하면 영원히 안에 머무는 성질 |
| **freezing robot problem** | 안전 제약이 모든 전진을 막아 로봇이 굳는 것 (safety ≠ liveness) |
| **Lie derivative** $L_f h$ | 벡터장 $f$ 방향의 $h$ 방향미분 |
| **liveness** | "좋은 일이 결국 일어남" — CBF 가 보장하지 **않는** 것 |
| **Nagumo's theorem** | 경계에서 바깥 방향 속도가 없으면 불변 — CBF 의 존재론적 뿌리 |
| **QP** | 2차 목적 + 선형 제약 볼록 최적화. safety filter 의 계산 형태 |
| **relative degree** | 입력이 출력에 나타날 때까지의 미분 횟수. unicycle 조향 = 2 |
| **safety filter** | nominal 입력을 안전 집합으로 최소 수정하는 투영 연산자 |
| **superlevel set** | $\{x : h(x) \ge c\}$. safe set 은 $h$ 의 0-superlevel set |
| **zeroing CBF** | $h$ 자체로 조건을 쓰는 현대 표준 형식 (↔ reciprocal) |

---

## 10. 레퍼런스 — 읽기 순서 추천

**1순위 (이 문서 다음에 바로)**
1. Ames, Coogan, Egerstedt, Notomista, Sreenath, Tabuada — *Control Barrier
   Functions: Theory and Applications*, ECC 2019 tutorial. **arXiv:1903.11199**.
   CBF 를 처음 정리하는 사람을 위한 canonical survey — §2~§3 의 원전
2. cbfkit 논문 — *CBFKit: A Control Barrier Function Toolbox for Robotics
   Applications*. **arXiv:2404.07158**. 우리가 차용한 아키텍처의 설명서

**2순위 (구현 깊이)**
3. Ames, Xu, Grizzle, Tabuada — *Control Barrier Function based Quadratic
   Programs for Safety Critical Systems*, IEEE TAC 2017. **arXiv:1609.06408**.
   CBF-QP 정식화의 원 논문
4. Xiao & Belta — *Control Barrier Functions for Systems with High Relative
   Degree*, CDC 2019. **arXiv:1903.04706**. §4.3 HOCBF 의 원전
5. Williams et al. — *Information Theoretic MPC for Model-Based Reinforcement
   Learning*, ICRA 2017. MPPI 의 free-energy 유도 (§6.1)

**3순위 (우리 로드맵 직결 확장)**
6. DPCBF — *Beyond Collision Cones: Dynamic Obstacle Avoidance for Nonholonomic
   Robots via Dynamic Parabolic CBFs*, ICRA 2026. **arXiv:2510.01402**.
   cut-in freezing 의 1순위 해법 후보 (issue #33)
7. Agrawal & Panagou — *gatekeeper: Online Safety Verification and Control for
   Nonlinear Systems in Dynamic Environments* (backup-trajectory 계열).
   liveness 문제의 대안 노선
8. 검색 키워드로: "collision cone control barrier function" (C3BF),
   "stochastic control barrier functions" (§7 SDE 계열),
   "learning control barrier functions" (Neural CBF)

**코드 (실행하며 읽기)**
- `~/.local/share/representation-aware-mppi/refs/cbfkit/examples/unicycle/reach_goal/`
  — 특히 `unicycle_reach_avoid_cbf.py` (offset-point + linear class-K 최소예제),
  `examples/pedestrian/navigate_among_pedestrians/head_on.py` (우리 S02 대응)
- `eval/mppi_sandbox/controllers/cbf_mppi.py` — 이 문서의 §4~§5 가 전부 들어있는 120줄
- safe_control `run_evade.sh` — gatekeeper 실행 (nominal/backup 스위칭 로그 관찰)

---

## 11. 스스로 점검 (이해했으면 답할 수 있어야 함)

1. $\alpha_0$ 를 10배 키우면 로봇 행동이 어떻게 바뀌는가? clearance 궤적은?
2. 왜 $h = \|p - p_o\| - d$ (제곱 없는 버전) 대신 제곱 형태를 쓸까?
   (힌트: $\Delta = 0$ 근방의 미분 가능성, 그리고 gradient 크기)
3. offset point $l \to 0$ 이면 무슨 일이 생기나? ($\det J = l$)
4. 우리 head-on 에서 CBF filter 단독 (cbf(stock)) 의 cte 가 risk_mppi 보다 나쁜
   구조적 이유는? (힌트: filter 는 언제 개입하는가 — 예측 vs 반응)
5. cut-in freezing 을 gatekeeper 는 어떻게 우회하나? DPCBF 는 어떻게 우회하나?
   두 접근의 실패 모드는 각각 무엇일까?

_2026-07-12 KST · 작성 계기: cbf_mppi (S1) 구현 후 개념 정리_
