"""exp011: TRAP sensitivity -- capture the four one-factor sweeps of the
canonical TRAP (TDAA) policy.

Imports the read-only core UNCHANGED (`sim.run`) and captures its output only.
No algorithm, parameter, grid, or result is authored; every sweep grid is
transcribed verbatim from `sim.py` `__main__` SENS A/B/C/D blocks. Each call
mirrors the frozen block exactly -- only the swept parameter is passed; all other
parameters (n=100, seed=42, and the untouched baseline factors) take `run()`'s
defaults.

Artifacts written (into this experiment directory only), all CRLF:
  * sweep_weights.csv  (SENS A: w0,w1,w2, AS, RR, RT)
  * sweep_theta_e.csv  (SENS B: te, AS, RR, RT)
  * sweep_theta_r.csv  (SENS C: tr, AS, RR, RT)
  * sweep_k.csv        (SENS D: k,  AS, RR, RT)
"""
import os
import sys
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sim import run  # read-only core, imported unchanged

METHOD = "tdaa"

# --- grids transcribed from sim.py __main__ SENS A/B/C/D ------------------------
W_GRID = [(0.3, 0.4, 0.3), (0.4, 0.4, 0.2), (0.5, 0.3, 0.2), (0.6, 0.2, 0.2)]
TE_GRID = [0.03, 0.05, 0.07]
TR_GRID = [0.05, 0.10, 0.15]
K_GRID = [2, 3, 4]


def write_csv(name, fieldnames, rows):
    with open(os.path.join(HERE, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


# SENS A -- weights
rows_a = []
for w in W_GRID:
    r = run(METHOD, w=w)
    rows_a.append({"w0": w[0], "w1": w[1], "w2": w[2],
                   "AS": r["AS"], "RR": r["RR"], "RT": r["RT"]})
write_csv("sweep_weights.csv", ["w0", "w1", "w2", "AS", "RR", "RT"], rows_a)

# SENS B -- theta_e
rows_b = []
for te in TE_GRID:
    r = run(METHOD, te=te)
    rows_b.append({"te": te, "AS": r["AS"], "RR": r["RR"], "RT": r["RT"]})
write_csv("sweep_theta_e.csv", ["te", "AS", "RR", "RT"], rows_b)

# SENS C -- theta_r
rows_c = []
for tr in TR_GRID:
    r = run(METHOD, tr=tr)
    rows_c.append({"tr": tr, "AS": r["AS"], "RR": r["RR"], "RT": r["RT"]})
write_csv("sweep_theta_r.csv", ["tr", "AS", "RR", "RT"], rows_c)

# SENS D -- k
rows_d = []
for k in K_GRID:
    r = run(METHOD, k=k)
    rows_d.append({"k": k, "AS": r["AS"], "RR": r["RR"], "RT": r["RT"]})
write_csv("sweep_k.csv", ["k", "AS", "RR", "RT"], rows_d)

print("exp011 sensitivity: wrote sweep_weights.csv (%d), sweep_theta_e.csv (%d), "
      "sweep_theta_r.csv (%d), sweep_k.csv (%d)"
      % (len(rows_a), len(rows_b), len(rows_c), len(rows_d)))
