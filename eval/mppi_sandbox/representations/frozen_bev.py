# SPDX-License-Identifier: BSD-3-Clause
"""The **structural** null's producer — the BEV with its motion model removed.

Two calibrated nulls have been walked on this branch and both failed, in
*opposite* directions:

- **ESS-matching** (D-169/D-170) picks `w_geom` by the sampler's response and
  does not **identify** the verdict — several admissible coefficients on one
  ladder read `REPRESENTATION_ADDS` and `GEOMETRY_SUFFICES` alike.
- **Gain-matching** (D-171) picks `w_geom` by the null's achieved clearance
  gain and **over**-identifies it: the match residual and the verdict statistic
  `|A − ½|` are one quantity read twice, so 13/15 convoy rung pairs and 10/10
  head_on ones order the same way under both → `CRITERION_CIRCULAR`.

Symmetric failures of one *form*, which is what indicts the form rather than
the choice. Both are properties of a null that swaps the term and must then
answer *how loud*. The structural ablation has no such question to answer,
because it does not introduce a coefficient at all.

What is removed, and what is deliberately not
----------------------------------------------

`RiskMPPI`'s live term is `w_risk` × the BEV **DYNAMIC** channel, which
:class:`~.gt_bev.GTBevProducer` renders as the union of Gaussian blobs laid
along each scripted obstacle's *predicted* sweep over `predict_horizon_s`,
decayed over prediction time. The anticipation — "yield early, give a wide
berth" — lives entirely in that forward render.

:class:`FrozenBevProducer` renders the same blob at the obstacle's position
**now** and nowhere else. Concretely it is `GTBevProducer` with
`predict_samples = 1`: `np.linspace(0, t_pred, 1) == [0.0]`, so the only sample
is `ob.position(t)` and its decay weight is `exp(-0/t_pred) == 1.0`. That is
not a tuning value dressed up as an ablation — it is the smallest number of
prediction samples that exists, and the resulting channel is pinned against a
hand-computed blob by test rather than against `GTBevProducer`'s own output.

Everything else is byte-identical to the arm it ablates: same grid, same
resolution, same sensing range, same occlusion geometry, same `blob_scale`,
same STATIC / EPISTEMIC / TRAVERSABILITY / ALEATORIC rows. And — the part that
makes this a structural ablation rather than a third calibrated null — the
consuming controller keeps `w_risk = 40.0` **unchanged**. There is no ladder to
walk, so neither D-170's under-identification nor D-171's circularity is
expressible here; :mod:`structural_null` checks that mechanically rather than
taking this paragraph's word for it.

The new failure mode this trades for the two old ones
------------------------------------------------------

Honesty requires naming it, because it is not free. Coefficient parity is not
loudness parity: a max over ten swept blobs is a larger number than one blob,
so the frozen arm's cost is quieter at the same `w_risk`, and its softmax may
sit outside `ab.ess_band`. A calibrated null answers that by turning a knob.
This one **cannot** — that is the whole point — so if the frozen arm is out of
band, the rung is refused and there is no remedy short of a different ablation.
The trade is a null that can be inadmissible for a null whose admissible
settings do not determine the answer. Which of those is the better bargain is
an empirical question about this scene, not a thing to argue in a docstring.
"""

from __future__ import annotations

from .gt_bev import GTBevProducer


class FrozenBevProducer(GTBevProducer):
    """`GTBevProducer` whose DYNAMIC channel carries no prediction.

    `predict_samples` is forced to 1 and is **not** a constructor argument:
    accepting it would make the removal of the motion model look like a setting
    with a default, and a later caller could restore prediction while still
    naming the class `Frozen*`. `predict_horizon_s` stays accepted-and-ignored
    for the DYNAMIC render (with one sample the horizon only scales a decay
    weight that is evaluated at τ = 0), so a caller transplanting kwargs from a
    `GTBevProducer` call site does not get a `TypeError` for a parameter that
    no longer changes anything.
    """

    def __init__(self, obstacles, **kwargs):
        kwargs.pop("predict_samples", None)
        super().__init__(obstacles, predict_samples=1, **kwargs)
