"""exp012 core: gradual-degradation traces, excess-authority metrics, analysis.

Implements PROTOCOL.md. Reads the frozen simulator, policies and metrics without
modifying them. build() returns every result file as text; run.py writes them and
check.py compares them with the stored copies.

offset_diagnostic.csv is not part of PROTOCOL.md. It was added after the results
were seen, to explain the EAD of trust-only and risk-only, which apply the band
edges to their own signals (T and 1 - R) rather than to the ARS. Per condition
and policy it gives the number of traces whose initial level exceeds the
ARS-mapped level, the mean number of the 40 pre-onset intervals with excess
authority, and EAD measured against the policy's own mapped signal instead of
the ARS. It is descriptive only and leaves every protocol output unchanged.
"""
import contextlib
import io
import math
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FROZEN = os.path.join(ROOT, 'frozen')
EXP010_RAW = os.path.join(FROZEN, 'experiments', 'exp010_trap_baseline', 'raw_results.csv')
RESULTS = os.path.join(HERE, 'results')

sys.path.insert(0, FROZEN)
with contextlib.redirect_stdout(io.StringIO()):   # sim.py prints at import
    import sim
from policies import to_state, TRAPPolicy

TF, TR, T_END = sim.TF, sim.TR, sim.T_END
N, SEED = 100, 42
W, TE, THR, K = (0.5, 0.3, 0.2), 0.05, 0.10, 3
POLICIES = ['static', 'trust', 'risk', 'sym', 'tdaa']
CONDITIONS = [('abrupt', 1), ('L5', 5), ('L10', 10), ('L20', 20)]
FROZEN_METRICS = ['AS', 'RR', 'RT', 'PER', 'PRR']
NEW_METRICS = ['EAD', 'EAM', 'EAD_all', 'RW']
B = 10000
BOOT_SEED = 20261027
MIN_N = 20
DEG = range(TF, TR)                                # degradation window D


def gen_trace_ramp(rng, L):
    """gen_trace with the t_F drop spread over L intervals (PROTOCOL.md).

    Consumes the random stream in the frozen order. Returns T, S, R and the
    number of clamping events inside the ramp window.
    """
    T = np.zeros(T_END); S = np.zeros(T_END); R = np.zeros(T_END)
    T[0] = rng.uniform(0.60, 0.75); S[0] = rng.uniform(0.65, 0.85)
    dT = dS = 0.0
    clamps = 0
    for t in range(T_END):
        if t > 0: T[t] = T[t-1] + rng.normal(0, 0.015); S[t] = S[t-1] + rng.normal(0, 0.01)
        if t == TF: dT = rng.uniform(0.20, 0.40); dS = rng.uniform(0.10, 0.25)
        if TF <= t < TF + L: T[t] -= dT / L; S[t] -= dS / L
        if t >= TR: T[t] += rng.uniform(0.005, 0.015); S[t] += rng.uniform(0.003, 0.010)
        if t < TF:
            R[t] = rng.uniform(0.15, 0.30)
        elif t < TR:
            f = min(1.0, (t - TF + 1) / L)
            if f >= 1.0:
                R[t] = rng.uniform(0.60, 0.85)
            else:
                lo, hi = 0.15 + 0.45 * f, 0.30 + 0.55 * f
                R[t] = lo + (hi - lo) * rng.random()
        else:
            R[t] = rng.uniform(0.30, 0.50)
        if TF <= t < TF + L and not (0 <= T[t] <= 1 and 0 <= S[t] <= 1):
            clamps += 1
        T[t] = min(1, max(0, T[t])); S[t] = min(1, max(0, S[t]))
    return T, S, R, clamps


def traces(cond, L):
    """The 100 traces of a condition; the control uses the frozen gen_trace."""
    rng = np.random.default_rng(SEED)
    shadow = np.random.default_rng(SEED)            # control: clamp count from the L=1 ramp twin
    out = []
    for _ in range(N):
        if cond == 'abrupt':
            T, S, R = sim.gen_trace(rng); c = gen_trace_ramp(shadow, 1)[3]
        else:
            T, S, R, c = gen_trace_ramp(rng, L)
        out.append((T, S, R, c))
    return out


def ars(T, S, R):
    return TRAPPolicy(w=W).signal(T, S, R)          # the frozen ARS expression


def excess(a, g):
    sig = np.array([to_state(x) for x in g])
    over = a > sig
    return dict(EAD=int(sum(over[t] for t in DEG)),
                EAM=int(sum(max(0, int(a[t] - sig[t])) for t in DEG)),
                EAD_all=int(over.sum()),
                RW=int(any(a[t] < a[t-1] for t in DEG)))


def control_checks():
    """Ramp generator at L = 1 equals frozen gen_trace; abrupt records equal exp010;
    random draws are aligned across conditions."""
    msgs, ok = [], True
    r1, r2 = np.random.default_rng(SEED), np.random.default_rng(SEED)
    same = all(all(np.array_equal(x, y) for x, y in zip(sim.gen_trace(r1), gen_trace_ramp(r2, 1)[:3]))
               for _ in range(N))
    ok &= same
    msgs.append('ramp generator with L=1 reproduces frozen gen_trace on %d traces: %s' % (N, same))

    import csv
    stored = {(r['policy'], int(r['run_id'])): r for r in csv.DictReader(open(EXP010_RAW))}
    tr = traces('abrupt', 1)
    bad = 0
    for p in POLICIES:
        pol = sim.make_policy(p, w=W, te=TE, tr=THR, k=K)
        for i, (T, S, R, _) in enumerate(tr):
            vals = sim.metrics(pol.update(T, S, R), T)
            for m, v in zip(FROZEN_METRICS, vals):
                s = float(stored[(p, i)][m])
                if not ((math.isnan(s) and math.isnan(v)) or s == float(v)):
                    bad += 1
    ok &= bad == 0
    msgs.append('abrupt control reproduces stored exp010 per-run records (5 policies x %d traces x 5 metrics): %s'
                % (N, bad == 0))

    # Draw alignment: before t_F and from t_R on, every condition equals the
    # control exactly; inside D the risk draw u_t is the same uniform number.
    aligned = True
    for cond, L in CONDITIONS[1:]:
        for (T0, S0, R0, _), (T1, S1, R1, _) in zip(tr, traces(cond, L)):
            aligned &= np.array_equal(T0[:TF], T1[:TF]) and np.array_equal(S0[:TF], S1[:TF])
            aligned &= np.array_equal(R0[:TF], R1[:TF]) and np.array_equal(R0[TR:], R1[TR:])
            for t in DEG:
                f = min(1.0, (t - TF + 1) / L)
                lo, hi = 0.15 + 0.45 * f, 0.30 + 0.55 * f
                u0 = (R0[t] - 0.60) / 0.25
                u1 = (R1[t] - lo) / (hi - lo) if f < 1 else (R1[t] - 0.60) / 0.25
                aligned &= abs(u0 - u1) < 1e-9
    ok &= aligned
    msgs.append('random draws aligned across conditions (pre-onset, risk draws in D, recovery risk): %s' % aligned)
    return ok, msgs


def boot(x):
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    m = x[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def summ(v):
    v = [x for x in v if not math.isnan(x)]
    if not v:
        return dict(n=0, mean=float('nan'), b_lo=float('nan'), b_hi=float('nan'))
    lo, hi = boot(v) if len(v) >= MIN_N else (float('nan'), float('nan'))
    return dict(n=len(v), mean=float(np.mean(v)), b_lo=lo, b_hi=hi)


def paired(a, b):
    both = [(x, y) for x, y in zip(a, b) if not (math.isnan(x) or math.isnan(y))]
    d = [x - y for x, y in both]
    s = summ(d)
    s.update(neg=sum(1 for x in d if x < 0), zero=sum(1 for x in d if x == 0),
             pos=sum(1 for x in d if x > 0),
             only_first=sum(1 for x, y in zip(a, b) if not math.isnan(x) and math.isnan(y)),
             only_second=sum(1 for x, y in zip(a, b) if math.isnan(x) and not math.isnan(y)))
    return s


def fmt(v):
    if isinstance(v, float):
        return 'nan' if math.isnan(v) else repr(v)
    return str(v)


def fmt6(v):
    if isinstance(v, float):
        return 'nan' if math.isnan(v) else '%.6f' % v
    return str(v)


def table(rows, f=fmt):
    keys = list(rows[0].keys())
    return '\n'.join([','.join(keys)] + [','.join(f(r[k]) for k in keys) for r in rows]) + '\n'


def build():
    ok, msgs = control_checks()
    raw, val, offset = [], [], []
    rec = {}                                         # (cond, policy) -> list of per-trace dicts
    v1 = {}                                          # cond -> list of bools
    for cond, L in CONDITIONS:
        tr = traces(cond, L)
        win = range(TF, TF + L)
        v1[cond] = []
        for i, (T, S, R, c) in enumerate(tr):
            g = ars(T, S, R)
            dg = np.concatenate([[0.0], g[:-1] - g[1:]])           # dg[t] = g[t-1] - g[t]
            dT_ = np.concatenate([[0.0], T[:-1] - T[1:]])
            dR_ = np.concatenate([[0.0], R[1:] - R[:-1]])          # decline of 1 - R
            ok1 = bool(max(dg[t] for t in win) <= THR)
            v1[cond].append(ok1)
            val.append(dict(condition=cond, run_id=i,
                            max_drop_window=float(max(dg[t] for t in win)),
                            max_drop_all=float(dg[1:].max()),
                            n_drops_over_thr_all=int((dg[1:] > THR).sum()),
                            v1=int(ok1),
                            trust_window_violation=int(max(dT_[t] for t in win) > THR),
                            risk_window_violation=int(max(dR_[t] for t in win) > THR),
                            realized_severity=float(g[TF-1] - g[TF+L-1]),
                            clamps=c))
        for p in POLICIES:
            pol = sim.make_policy(p, w=W, te=TE, tr=THR, k=K)
            lst = []
            above = pre = own = 0
            for i, (T, S, R, _) in enumerate(tr):
                a = pol.update(T, S, R)
                d = dict(zip(FROZEN_METRICS, [float(x) for x in sim.metrics(a, T)]))
                d.update(excess(a, ars(T, S, R)))
                lst.append(d)
                raw.append(dict(condition=cond, policy=p, run_id=i, **d, final_state=int(a[-1])))
                # Post-hoc offset diagnostic (not in PROTOCOL.md; see module docstring).
                sig = np.array([to_state(x) for x in ars(T, S, R)])
                sig_own = np.array([to_state(x) for x in pol.signal(T, S, R)])
                above += int(a[0] > sig[0])
                pre += int(sum(a[t] > sig[t] for t in range(TF)))
                own += int(sum(a[t] > sig_own[t] for t in DEG))
            rec[(cond, p)] = lst
            offset.append(dict(condition=cond, policy=p, traces=N,
                               traces_initial_level_above_ars=above,
                               pre_onset_excess_mean=pre / N,
                               ead_mean=float(np.mean([r['EAD'] for r in lst])),
                               ead_own_signal_mean=own / N))

    # Validity summary per condition.
    vs = []
    for cond, L in CONDITIONS:
        rows = [r for r in val if r['condition'] == cond]
        sev = [r['realized_severity'] for r in rows]
        vs.append(dict(condition=cond, L=L, traces=len(rows),
                       v1_violations=sum(1 - r['v1'] for r in rows),
                       max_drop_window_max=max(r['max_drop_window'] for r in rows),
                       max_drop_window_mean=float(np.mean([r['max_drop_window'] for r in rows])),
                       traces_with_any_drop_over_thr=sum(1 for r in rows if r['n_drops_over_thr_all'] > 0),
                       trust_signal_window_violations=sum(r['trust_window_violation'] for r in rows),
                       risk_signal_window_violations=sum(r['risk_window_violation'] for r in rows),
                       realized_severity_mean=float(np.mean(sev)),
                       realized_severity_min=float(np.min(sev)),
                       realized_severity_max=float(np.max(sev)),
                       clamps=sum(r['clamps'] for r in rows)))

    # Per-policy summaries: all traces, and the V1 subset.
    summary = []
    for cond, _ in CONDITIONS:
        for subset in ['all', 'V1']:
            keep = [True] * N if subset == 'all' else v1[cond]
            for p in POLICIES:
                for m in FROZEN_METRICS + NEW_METRICS:
                    v = [float(r[m]) for r, k_ in zip(rec[(cond, p)], keep) if k_]
                    summary.append(dict(condition=cond, set=subset, policy=p, metric=m, **summ(v)))

    # Paired comparisons.
    pairs = []
    plan = [('sym', ['EAD', 'EAM', 'AS', 'RR', 'RT']), ('trust', ['EAD', 'EAM']), ('risk', ['EAD', 'EAM'])]
    for cond, _ in CONDITIONS:
        for subset in ['all', 'V1']:
            keep = [True] * N if subset == 'all' else v1[cond]
            for other, ms in plan:
                for m in ms:
                    a = [float(r[m]) for r, k_ in zip(rec[(cond, 'tdaa')], keep) if k_]
                    b = [float(r[m]) for r, k_ in zip(rec[(cond, other)], keep) if k_]
                    pairs.append(dict(condition=cond, set=subset, comparison='tdaa-' + other, metric=m, **paired(a, b)))
            if cond != 'abrupt':
                a = [float(r['EAD']) for r, k_ in zip(rec[(cond, 'tdaa')], keep) if k_]
                b = [float(r['EAD']) for r, k_ in zip(rec[('abrupt', 'tdaa')], keep) if k_]
                pairs.append(dict(condition=cond, set=subset, comparison='tdaa-tdaa_abrupt', metric='EAD', **paired(a, b)))

    files = {'raw_results.csv': table(raw), 'validity.csv': table(val),
             'validity_summary.csv': table(vs, fmt6), 'summary.csv': table(summary, fmt6),
             'paired.csv': table(pairs, fmt6), 'offset_diagnostic.csv': table(offset, fmt6)}
    return ok, msgs, files
