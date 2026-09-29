"""exp010 figures -- baseline policy comparison + seed-42 trajectory.

Per M3-004:
  * The baseline figure reads ONLY the stored processed_results.csv.
  * The trajectory figure additionally uses the seed-42 `gen_trace` from the
    frozen core (imported unchanged), as explicitly authorized.
Each figure emits a .png (integrity record; not required byte-regenerable) and a
figure_data.csv (LF, UTF-8) that is the reproducible data behind the figure.

Determinism: baseline figure_data.csv passes stored CSV values through verbatim;
trajectory figure_data.csv is a pure function of gen_trace(default_rng(42)).
"""
import os
import sys
import csv

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)


def write_lf_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")  # LF, UTF-8
        w.writerow(header)
        for r in rows:
            w.writerow(r)


# --- Figure 1: baseline AS by policy (reads processed_results.csv only) -------
with open(os.path.join(HERE, "processed_results.csv"), newline="") as f:
    proc = list(csv.DictReader(f))

policies = [r["policy"] for r in proc]
AS_text = [r["AS"] for r in proc]        # verbatim stored text -> byte-determinism
ASsd_text = [r["ASsd"] for r in proc]

write_lf_csv(
    os.path.join(FIG, "baseline_figure_data.csv"),
    ["policy", "AS", "ASsd"],
    [[p, a, s] for p, a, s in zip(policies, AS_text, ASsd_text)],
)

x = np.arange(len(policies))
as_vals = [float(v) for v in AS_text]
sd_vals = [float(v) for v in ASsd_text]
plt.figure(figsize=(6, 4))
plt.bar(x, as_vals, yerr=sd_vals, capsize=4, color="#4472c4")
plt.xticks(x, policies)
plt.ylabel("Authorization Stability (AS)")
plt.title("exp010 baseline: AS by policy (mean +/- SD, n=100, seed=42)")
plt.ylim(0, 1.05)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "baseline.png"), dpi=130)
plt.close()

# --- Figure 2: seed-42 trajectory (frozen core: gen_trace + TRAPPolicy) -------
from sim import gen_trace, TF, TR
from policies import TRAPPolicy

rng = np.random.default_rng(42)
T, S, R = gen_trace(rng)
pol = TRAPPolicy()
ars = pol.signal(T, S, R)          # 0.5T + 0.3S - 0.2R
a = pol.update(T, S, R)            # TRAP authorization band trajectory

rows = []
for t in range(len(T)):
    rows.append([t,
                 repr(float(T[t])), repr(float(S[t])), repr(float(R[t])),
                 repr(float(ars[t])), int(a[t])])
write_lf_csv(
    os.path.join(FIG, "trajectory_figure_data.csv"),
    ["t", "trust", "stability", "risk", "ars", "auth_band"],
    rows,
)

fig, ax1 = plt.subplots(figsize=(7, 4))
ax1.plot(T, label="trust", color="#1f77b4")
ax1.plot(S, label="stability", color="#2ca02c")
ax1.plot(R, label="risk", color="#d62728")
ax1.plot(ars, label="ARS", color="#7f7f7f", linestyle="--")
ax1.set_xlabel("timestep")
ax1.set_ylabel("signal value")
ax1.set_ylim(-0.2, 1.05)
ax1.axvline(TF, color="grey", alpha=0.4, linestyle=":")
ax1.axvline(TR, color="grey", alpha=0.4, linestyle=":")
ax2 = ax1.twinx()
ax2.step(range(len(a)), a, where="post", label="auth band", color="k", linewidth=2)
ax2.set_ylabel("authorization band")
ax2.set_ylim(-0.2, 5.2)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="lower left")
plt.title("exp010 trajectory: TRAP response to seed-42 trace (fault@%d, recovery@%d)" % (TF, TR))
plt.tight_layout()
plt.savefig(os.path.join(FIG, "trajectory.png"), dpi=130)
plt.close()

print("exp010 figures: wrote baseline.png/baseline_figure_data.csv and "
      "trajectory.png/trajectory_figure_data.csv")
