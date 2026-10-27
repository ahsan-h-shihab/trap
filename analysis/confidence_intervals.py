"""Interval estimates for the behavioral (exp010; paper Tables III-IV) and
sensitivity (exp011; paper Table V) results, computed from per-run records of
the frozen artifact.

This analysis is additive. It reads frozen/ and writes only to analysis/output/.

  exp010    : the stored per-run records
              frozen/experiments/exp010_trap_baseline/raw_results.csv
              (100 traces per policy). Their aggregates are first checked
              against the stored processed_results.csv.
  exp011    : exp011 stores aggregates only. Per-run records are regenerated
              with the frozen sim.run_records() at each sweep setting, and the
              aggregates of those records are checked against the stored
              sweep_*.csv before any interval is computed.

For each metric the script reports the mean over the traces on which the metric
is defined (with the number of such traces), a 95% Student-t interval, and a 95%
percentile bootstrap interval (10,000 resamples; every interval uses a fresh
generator with the same fixed seed, so identical data give identical
intervals). It also reports paired TRAP - Symmetric differences on the traces
where both are defined, since both policies see the same traces.

The intervals describe sampling variation of the trace generator only: the 100
traces of a run are independent draws from the simulator, so the intervals say
how precisely the reported means estimate the simulator's expected values. They
say nothing about behavior outside the simulator.

  python analysis/confidence_intervals.py           # writes analysis/output/
  python analysis/confidence_intervals.py --check   # compares with analysis/output/ instead

Exit code 0 only if every regenerated or recomputed aggregate matches the stored
value and, with --check, every output file matches its stored copy.
"""
import contextlib
import csv
import io
import math
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = os.path.join(ROOT, 'frozen')
EXP010 = os.path.join(FROZEN, 'experiments', 'exp010_trap_baseline')
EXP011 = os.path.join(FROZEN, 'experiments', 'exp011_trap_sensitivity')
OUT = os.path.join(ROOT, 'analysis', 'output')
METRICS = ['AS', 'RR', 'RT', 'PER', 'PRR']
POLICIES = ['static', 'trust', 'risk', 'sym', 'tdaa']
B = 10000
BOOT_SEED = 20261027
CHECK = '--check' in sys.argv

# t quantiles (two-sided 95%) for the degrees of freedom that can occur here.
T975 = {df: q for df, q in [(93, 1.9858), (94, 1.9855), (95, 1.9853), (96, 1.9850),
                            (97, 1.9847), (98, 1.9845), (99, 1.9842)]}


def t_interval(x):
    n = len(x)
    m = float(np.mean(x))
    if n < 2:
        return m, float('nan'), float('nan')
    se = float(np.std(x, ddof=1)) / math.sqrt(n)
    q = T975[n - 1]
    return m, m - q * se, m + q * se


def boot_interval(x):
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    means = x[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarize(values):
    v = [x for x in values if not math.isnan(x)]
    if not v:
        return dict(n=0, mean=float('nan'), t_lo=float('nan'), t_hi=float('nan'),
                    b_lo=float('nan'), b_hi=float('nan'))
    m, tl, th = t_interval(v)
    bl, bh = boot_interval(v)
    return dict(n=len(v), mean=m, t_lo=tl, t_hi=th, b_lo=bl, b_hi=bh)


def close(a, b):
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    return abs(a - b) <= 1e-12


def load_sim():
    sys.path.insert(0, FROZEN)
    with contextlib.redirect_stdout(io.StringIO()):   # sim.py prints at import
        import sim
    return sim


def main():
    os.makedirs(OUT, exist_ok=True)
    ok = True

    # ---- exp010 from stored per-run records --------------------------------
    rows = list(csv.DictReader(open(os.path.join(EXP010, 'raw_results.csv'))))
    stored = {r['policy']: r for r in csv.DictReader(open(os.path.join(EXP010, 'processed_results.csv')))}
    per_policy = {p: {m: [float(r[m]) for r in rows if r['policy'] == p] for m in METRICS} for p in POLICIES}
    for p in POLICIES:
        assert len(per_policy[p]['AS']) == 100
        for m in METRICS:
            v = [x for x in per_policy[p][m] if not math.isnan(x)]
            agg = float(np.mean(v)) if v else float('nan')
            if not close(agg, float(stored[p][m])):
                ok = False
                print('MISMATCH exp010', p, m, agg, stored[p][m])
        if not close(float(np.std(per_policy[p]['AS'])), float(stored[p]['ASsd'])):
            ok = False
            print('MISMATCH exp010', p, 'ASsd')
    print('exp010: per-run records reproduce stored aggregates:', ok)

    behavior = []
    for p in POLICIES:
        for m in METRICS:
            s = summarize(per_policy[p][m])
            behavior.append(dict(policy=p, metric=m, **s))

    # Paired TRAP - Symmetric on the same traces.
    paired = []
    for m in METRICS:
        a, b = per_policy['tdaa'][m], per_policy['sym'][m]
        d = [x - y for x, y in zip(a, b) if not (math.isnan(x) or math.isnan(y))]
        s = summarize(d)
        s.update(trap_better=sum(1 for x in d if x < 0), tie=sum(1 for x in d if x == 0),
                 trap_worse=sum(1 for x in d if x > 0))
        paired.append(dict(metric=m, **s))

    # TRAP against every adaptive comparison policy, on the same traces.
    paired_all = []
    for other in ['trust', 'risk', 'sym']:
        for m in METRICS:
            a, b = per_policy['tdaa'][m], per_policy[other][m]
            d = [x - y for x, y in zip(a, b) if not (math.isnan(x) or math.isnan(y))]
            s = summarize(d)
            s.update(trap_lower=sum(1 for x in d if x < 0), tie=sum(1 for x in d if x == 0),
                     trap_higher=sum(1 for x in d if x > 0))
            paired_all.append(dict(other=other, metric=m, **s))

    # ---- exp011: regenerate per-run records, verify against stored sweeps --
    sim = load_sim()
    base = dict(w=(0.5, 0.3, 0.2), te=0.05, tr=0.10, k=3)
    sweeps = [('weights', 'sweep_weights.csv', 'w',
               [(0.3, 0.4, 0.3), (0.4, 0.4, 0.2), (0.5, 0.3, 0.2), (0.6, 0.2, 0.2)]),
              ('theta_e', 'sweep_theta_e.csv', 'te', [0.03, 0.05, 0.07]),
              ('theta_r', 'sweep_theta_r.csv', 'tr', [0.05, 0.10, 0.15]),
              ('k', 'sweep_k.csv', 'k', [2, 3, 4])]
    sensitivity = []
    steps = []
    ok3 = True
    for name, fname, key, values in sweeps:
        stored_rows = list(csv.DictReader(open(os.path.join(EXP011, fname))))
        assert len(stored_rows) == len(values)
        prev = None
        for val, srow in zip(values, stored_rows):
            params = dict(base)
            params[key] = val
            recs = list(sim.run_records('tdaa', n=100, seed=42, **params))
            if prev is not None:
                # Paired change in RT from the previous setting on the same traces.
                d = [r['RT'] - q['RT'] for r, q in zip(recs, prev[1])
                     if not (math.isnan(r['RT']) or math.isnan(q['RT']))]
                s = summarize(d)
                s.update(up=sum(1 for x in d if x > 0), tie=sum(1 for x in d if x == 0),
                         down=sum(1 for x in d if x < 0))
                steps.append(dict(sweep=name, step='%s -> %s' % (prev[0], val), **s))
            prev = (val, recs)
            live = sim.run('tdaa', n=100, seed=42, **params)
            for m in ['AS', 'RR', 'RT']:
                v = [r[m] for r in recs if not math.isnan(r[m])]
                agg = float(np.mean(v))
                if not (close(agg, float(live[m])) and close(agg, float(srow[m]))):
                    ok3 = False
                    print('MISMATCH exp011', name, val, m, agg, live[m], srow[m])
            for m in ['AS', 'RT']:
                s = summarize([r[m] for r in recs])
                sensitivity.append(dict(sweep=name, setting=str(val), metric=m, **s))
    print('exp011: regenerated per-run records reproduce stored sweep values:', ok3)
    ok &= ok3

    def write(fname, recs):
        buf = io.StringIO(newline='')
        w = csv.DictWriter(buf, fieldnames=list(recs[0].keys()))
        w.writeheader()
        for r in recs:
            w.writerow({k: (('%.6f' % v) if isinstance(v, float) else v) for k, v in r.items()})
        path = os.path.join(OUT, fname)
        if CHECK:
            # Compare with the stored copy instead of overwriting it.
            nonlocal ok
            norm = lambda s: s.replace('\r\n', '\n')
            same = os.path.isfile(path) and norm(open(path, 'rb').read().decode('utf-8')) == norm(buf.getvalue())
            ok &= same
            print('stored %-40s %s' % (fname, 'identical' if same else 'MISMATCH'))
        else:
            with open(path, 'w', newline='') as f:
                f.write(buf.getvalue())
    write('behavior_intervals.csv', behavior)
    write('behavior_paired_trap_minus_sym.csv', paired)
    write('behavior_paired_trap_vs_all.csv', paired_all)
    write('sensitivity_intervals.csv', sensitivity)
    write('sensitivity_paired_rt_steps.csv', steps)

    print('\nexp010, 95% intervals (t | bootstrap):')
    for r in behavior:
        if r['n']:
            print('  %-6s %-3s n=%3d mean=%.4f  t[%.4f, %.4f]  boot[%.4f, %.4f]'
                  % (r['policy'], r['metric'], r['n'], r['mean'], r['t_lo'], r['t_hi'], r['b_lo'], r['b_hi']))
    print('\nPaired TRAP - Symmetric:')
    for r in paired:
        print('  %-3s n=%3d mean=%.4f  t[%.4f, %.4f]  boot[%.4f, %.4f]  lower/tie/higher=%d/%d/%d'
              % (r['metric'], r['n'], r['mean'], r['t_lo'], r['t_hi'], r['b_lo'], r['b_hi'],
                 r['trap_better'], r['tie'], r['trap_worse']))
    print('\nPaired TRAP - each adaptive policy (bootstrap):')
    for r in paired_all:
        if r['n']:
            print('  vs %-5s %-3s n=%3d mean=%+.4f  boot[%+.4f, %+.4f]  lower/tie/higher=%d/%d/%d'
                  % (r['other'], r['metric'], r['n'], r['mean'], r['b_lo'], r['b_hi'],
                     r['trap_lower'], r['tie'], r['trap_higher']))
    print('\nexp011, RT 95% intervals (t | bootstrap):')
    for r in sensitivity:
        if r['metric'] == 'RT':
            print('  %-8s %-16s mean=%.2f  t[%.2f, %.2f]  boot[%.2f, %.2f]'
                  % (r['sweep'], r['setting'], r['mean'], r['t_lo'], r['t_hi'], r['b_lo'], r['b_hi']))
    print('\nexp011, paired RT change between adjacent settings:')
    for r in steps:
        print('  %-8s %-34s n=%3d mean=%+.2f  t[%+.2f, %+.2f]  boot[%+.2f, %+.2f]  up/tie/down=%d/%d/%d'
              % (r['sweep'], r['step'], r['n'], r['mean'], r['t_lo'], r['t_hi'], r['b_lo'], r['b_hi'],
                 r['up'], r['tie'], r['down']))
    print('\nconfidence_intervals:', ('AGGREGATES AND STORED OUTPUTS VERIFIED' if CHECK else 'AGGREGATES VERIFIED')
          if ok else 'MISMATCH')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
