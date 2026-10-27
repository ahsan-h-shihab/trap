# exp012 — Gradual degradation and excess-authority duration

Post-freeze, additive experiment. It reads the frozen simulator, policies and
metrics from `frozen/` without modifying them and writes only to
`postfreeze/exp012_gradual_degradation/results/`.

This protocol, including every metric definition, analysis set and comparison,
was written before exp012 was run. The results of exp010 and exp011, and the
analytic property of Algorithm 1 that motivates this experiment, were known when
it was written.

## Question

Algorithm 1 lowers the authorization level only when a single-interval drop in
the Authorization Readiness Score (ARS) exceeds θr. The frozen experiments
contain only an abrupt degradation at t_F. exp012 asks how the five policies
behave when the same total degradation is spread over several intervals, and how
long each policy holds more authority than current readiness supports.

## Conditions

All conditions use the frozen horizon (T_END = 100), degradation onset t_F = 40,
recovery onset t_R = 60, and the frozen baseline parameters
w = (0.5, 0.3, 0.2), θe = 0.05, θr = 0.10, k = 3.

| Condition | Degradation schedule |
|---|---|
| `abrupt` (control) | frozen `sim.gen_trace`, unchanged: the full drop at t = t_F |
| `L5`, `L10`, `L20` | the same drop spread linearly over L = 5, 10, 20 intervals, t = t_F … t_F + L − 1 |

L = 20 ends the ramp at t = 59, the last interval before recovery onset.

### Ramp generator

`gen_trace_ramp(rng, L)` consumes the random stream in exactly the order of the
frozen `gen_trace`, so every random draw (initial values, noise, the drop
magnitudes and the risk draws) is identical across conditions for a given trace.
Only the schedule on which the drawn degradation is applied differs.

Let f(t) = 0 for t < t_F and f(t) = min(1, (t − t_F + 1)/L) for t ≥ t_F.

* Trust and stability: the frozen generator draws ΔT ~ U(0.20, 0.40) and
  ΔS ~ U(0.10, 0.25) at t = t_F and subtracts them at t = t_F. The ramp
  generator draws them at the same point in the stream and subtracts ΔT/L and
  ΔS/L at each t in t_F … t_F + L − 1. The scheduled total is ΔT and ΔS
  (before the frozen clamping to [0, 1], which is applied every step as in the
  frozen generator).
* Risk: the frozen generator draws R_t ~ U(0.15, 0.30) before t_F and
  R_t ~ U(0.60, 0.85) during degradation. With u_t the same uniform draw, the
  ramp generator sets R_t = lo(f) + (hi(f) − lo(f)) u_t for t_F ≤ t < t_R, with
  lo(f) = 0.15 + 0.45 f and hi(f) = 0.30 + 0.55 f. At f = 0 and f = 1 the exact
  frozen bounds are used. Risk is ramped because the abrupt risk step alone
  lowers the ARS by about 0.1, close to θr; ramping trust and stability alone
  would not make the degradation gradual.
* Recovery (t ≥ t_R) is unchanged.

With L = 1 the ramp generator must reproduce the frozen `gen_trace` bit for bit;
this is checked on all 100 traces.

### Traces

For each condition and each policy the random stream is restarted with
`numpy.random.default_rng(42)` and 100 traces are drawn in sequence, as in
exp010. The same 100 traces are therefore seen by every policy, and trace i in
every condition shares all its random draws with trace i of the control.

## Policies

The five frozen policies via `make_policy`: static, trust-only, risk-only,
symmetric, TRAP, at the baseline parameters.

## Metrics

Frozen metrics, from the frozen `sim.metrics`, unchanged: AS, RR, RT, PER, PRR.

New metrics, defined here. Let g_t be the ARS with the baseline weights,
g_t = 0.5 T_t + 0.3 S_t − 0.2 R_t (the frozen ARS expression), and let
σ_t = `to_state`(g_t) be the level that readiness maps to under the frozen band
substrate. The same readiness reference is used for every policy, including
trust-only and risk-only, whose own decision signals differ. Let a_t be the
policy's level, and let D = {t_F, …, t_R − 1} = {40, …, 59} be the degradation
window (20 intervals).

* **EAD** (primary), excess-authority duration: the number of intervals t in D
  with a_t > σ_t. Range 0–20.
* **EAM** (secondary), excess-authority magnitude: Σ_{t∈D} max(0, a_t − σ_t), in
  level-intervals.
* **EAD_all** (secondary): the number of intervals t in 0 … 99 with a_t > σ_t.
* **RW** (secondary): 1 if the level falls at least once in D (a_t < a_{t−1}
  for some t in D), else 0.

## Gradual-condition validity

Let δ_t = g_{t−1} − g_t be the one-interval ARS decline, and W_L = {t_F, …,
t_F + L − 1} the ramp window (W = {t_F} for the control).

* **V1** (the intended gradual condition, per trace): max_{t∈W_L} δ_t ≤ θr.
  A trace violates the gradual condition if any single-interval ARS decline in
  the ramp window exceeds θr.
* Also reported: the largest δ_t in W_L; the largest δ_t over the whole trace;
  the number of traces with any δ_t > θr anywhere in t = 1 … 99; the same
  window check on the trust-only signal T and the risk-only signal 1 − R; the
  realized severity g_{t_F − 1} − g_{t_F + L − 1}; and the number of clamping
  events in W_L.

Violations are reported, not removed.

## Analysis

* Analysis set: all 100 traces in every condition (primary). Secondary: the
  traces satisfying V1 in that condition.
* Per condition and policy: the mean of each metric over the traces on which it
  is defined, the number of such traces, and a 95% percentile bootstrap interval
  (10,000 resamples; a fresh generator seeded 20261027 for every interval, so
  identical data give identical intervals).
* Paired, on the shared traces, per condition:
  TRAP − symmetric for EAD, EAM, AS, RR and RT;
  TRAP − trust-only and TRAP − risk-only for EAD and EAM;
  TRAP(L) − TRAP(abrupt) for EAD.
  Each reports the number of pairs, the mean difference, the bootstrap interval,
  the counts of negative, zero and positive differences, and, for RR and RT, the
  number of traces on which only one policy of the pair has the metric defined.
* Intervals are not reported when fewer than 20 values are available; the
  number and the mean are still reported.
* Intervals are per comparison and unadjusted for multiplicity. They describe
  sampling variation of the trace generator only.

## Predictions recorded before running

From Algorithm 1: on traces satisfying V1, TRAP does not lower its level within
W_L; TRAP's EAD grows with L; the symmetric rule, which steps down after k
consecutive low observations, is less affected by the schedule. These are
predictions, not results, and are reported against the outcome.

## Reproduction

    python postfreeze/exp012_gradual_degradation/run.py     # writes results/
    python postfreeze/exp012_gradual_degradation/check.py   # regenerates in memory and compares
