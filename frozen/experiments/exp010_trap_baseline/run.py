"""exp010: TRAP baseline -- capture the five-policy baseline comparison.

Imports the read-only core UNCHANGED (`sim.run`, `sim.run_records`) and captures
its output only. No algorithm, parameter, or result is authored; every parameter
is transcribed verbatim from `sim.py` `__main__` BASELINE block and `run()`
defaults (see config.json / parameters.json).

Artifacts written (into this experiment directory only):
  * raw_results.csv       -- one row per Monte-Carlo trajectory, per policy
                             (n rows/policy; unfiltered RR/RT/PER/PRR, tagged
                             with policy + run_id + final_state), CRLF.
  * processed_results.csv -- per-policy aggregates equal to a live `run()`
                             (AS, ASsd, RR, RT, PER, PRR), CRLF.

Run from anywhere: the repository root is resolved relative to this file so the
core is imported unchanged and nothing outside this directory is written.
"""
import os
import sys
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sim import run, run_records  # read-only core, imported unchanged

# --- parameters transcribed from sim.py __main__ BASELINE block + run() defaults
POLICIES = ["static", "trust", "risk", "sym", "tdaa"]
N = 100
SEED = 42
W = (0.5, 0.3, 0.2)
TE = 0.05
TR = 0.10
K = 3

# --- raw: per-run records (n rows per policy), unfiltered, tagged with policy ---
raw_fields = ["policy", "run_id", "seed", "AS", "RR", "RT", "PER", "PRR", "final_state"]
raw_rows = []
for method in POLICIES:
    count = 0
    for rec in run_records(method, n=N, seed=SEED, w=W, te=TE, tr=TR, k=K):
        row = {"policy": method}
        row.update(rec)
        raw_rows.append(row)
        count += 1
    assert count == N, f"{method}: expected {N} records, got {count}"

with open(os.path.join(HERE, "raw_results.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=raw_fields)
    w.writeheader()
    for r in raw_rows:
        w.writerow(r)

# --- processed: per-policy aggregates equal to a live run() ---
proc_fields = ["policy", "AS", "ASsd", "RR", "RT", "PER", "PRR"]
with open(os.path.join(HERE, "processed_results.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=proc_fields)
    w.writeheader()
    for method in POLICIES:
        agg = run(method, n=N, seed=SEED, w=W, te=TE, tr=TR, k=K)
        w.writerow({
            "policy": method,
            "AS": agg["AS"], "ASsd": agg["ASsd"],
            "RR": agg["RR"], "RT": agg["RT"],
            "PER": agg["PER"], "PRR": agg["PRR"],
        })

print("exp010 baseline: wrote raw_results.csv (%d rows) and processed_results.csv (%d policies)"
      % (len(raw_rows), len(POLICIES)))
