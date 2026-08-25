# `unwatched_exemptions` — domain declaration vs real allow-list

Answers **Q-166**. Static classification of all 9 keys returned by
`guard_reflexivity.unwatched_exemptions()` as of 2026-08-18, using the
discriminant Q-166's *Lean* proposed:

> **Does any consumer supply the tested value from *outside* the registry?**
>
> - **No** (every consumer draws the argument from the registry itself) ⇒ the
>   membership test filters nobody ⇒ it is a **domain declaration**.
> - **Yes** ⇒ the test genuinely narrows an outside-sourced population ⇒ it is
>   a **real allow-list**.

The discriminant needs no new constant: it is read off the call site that
performs the test plus the callers of the enclosing function. No code changed
to produce this table.

## The table

| key | test site | value under test comes from | verdict |
|---|---|---|---|
| `DECLARED_DEF_TIME` | `exemption_control.py:869` — `n not in DECLARED_DEF_TIME` | `unreachable(package)`, an AST scan | **allow-list** |
| `DEGENERATE_READINGS` | `claim_scope.py:525,543` — `value in DEGENERATE_READINGS` | `sc.reading_calibrated` / `sc.reading_other`, i.e. `SCOPED_CLAIMS` — a *different* registry | **allow-list** |
| `HULL_REPAIRED_BY` | `extremum_reading.py:277` — `(key[0], key[1]) not in HULL_REPAIRED_BY` | `SITE_CLASSES.items()` — a *different* registry | **allow-list** |
| `OBSERVABLES` | `scene_separability.py:743` — `observable in OBSERVABLES` | the `observable` parameter; **every** caller draws it from `OBSERVABLES` (see below) | **domain declaration** |
| `RESOLVERS` | `window_axis_migration.py:280` — `(modname, fn.name) in definitions`, `definitions = frozenset(RESOLVERS)` | `ast.walk` over the package sources | **allow-list** |
| `SCOPED_CLAIMS` | `claim_scope.py:557` — `registered` set subtracted in `unregistered_citations` | `derived_citations()`, whose `doc`/`anchor` come from `_sections()` doc scanning | **allow-list** |
| `SELF_DEFINING` | `magnitude_survival.py:279,294` — `t not in SELF_DEFINING`, `(c.decision, c.site, kind) in SELF_DEFINING` | `derived` / scanned claims | **allow-list** |
| `SITE_CLASSES` | `extremum_reading.py:312` — `SITE_CLASSES.get(k) == cls` | `found_keys`, from `scan_sites(root)` | **allow-list** |
| `TEMPERATURE_RELEVANT` | `lam_dependence.py:396` — `self.kind in TEMPERATURE_RELEVANT` | the instance's `kind` field, set by the caller | **allow-list** |

**Split: 8 allow-list, 1 domain declaration.**

## The one domain declaration, checked rather than asserted

`OBSERVABLES` is the category's only member, and it is the case D-339 argued
for, so it gets the closest reading. `constant_at_every_index(observable)` has
exactly one module-level caller and two test callers:

- `scene_separability.py:766` — `tuple(o for o in OBSERVABLES if constant_at_every_index(o))`. Drawn from the registry.
- `tests/test_scene_separability.py:340` — iterates `OBSTACLE_SIDE_OBSERVABLES`, which is a **subset** of `OBSERVABLES` (`("obstacle_speed", "path_lateral_speed")`).
- `tests/test_scene_separability.py:343` — passes the literal `"bearing_rate"`, which **is in** `OBSERVABLES` (verified: `OBSERVABLES == ('lateralness', 'closing_speed', 'bearing_rate', 'obstacle_speed', 'path_lateral_speed', 'min_ttc')`).

The third is the one that looked like a counterexample — a hand-typed literal
argument is exactly the shape of an outside-sourced value — and it is not one.
Nothing anywhere passes a name absent from `OBSERVABLES`, so the membership
test excludes no call that is actually made. It states the function's domain.

## What this answers, and what it does not

Q-166 asked whether the distinction splits the 9 cleanly or was a post-hoc
category invented to save `OBSERVABLES`. The honest answer is **both readings
survive, and they are not in conflict**:

- The discriminant **is** well-defined and computable, and it does classify all
  9 without a judgement call — so this is Q-166 option (a), not (b).
- But the domain-declaration category has **exactly one member**, which is the
  member it was proposed for. A rule with one instance is not yet evidence that
  the category recurs.

So the classification is real but its predictive value is untested. The
follow-up that would settle it is not another audit of these 9 — it is the
**next** entrant to `unwatched_exemptions`: if it lands in the allow-list
column, as 8 of 9 did, D-330's existing rule was right for the common case and
`OBSERVABLES` is a genuine but rare exception.

## Consequence for D-330

D-330 says: when a category constant enters `unwatched_exemptions`, delete the
membership test rather than bumping the pin. That rule is **correct for 8 of
the 9** — deleting an allow-list test would change behaviour, so the rule's
"delete it" branch is only ever reachable for the domain-declaration class.

The precise amendment D-330 needs is therefore narrow, and is **not made here**
(it touches guard code and so costs a suite):

> D-330 applies to membership tests that do **not** state a domain. Before
> deleting, apply the Q-166 discriminant; if every consumer draws the argument
> from the registry, the test is a domain declaration — keep it, and record the
> control instead.

## Known limit of the method

`consumer_reach`'s caller resolution is **bare-name** based (Q-163), so a
same-named function in another module can pollute the caller set. The three
`constant_at_every_index` call sites above were read directly rather than
through that machinery, so this table does not inherit the defect — but a
future automated version of this classification would.
