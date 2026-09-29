"""exp011 figure -- TRAP sensitivity across the four one-factor sweeps.

Per M3-004: reads ONLY the stored sweep CSVs (no simulator call). Emits one .png
(integrity record; not required byte-regenerable) and one figure_data.csv
(LF, UTF-8) that is the reproducible data behind the figure.

Determinism: figure_data.csv passes stored sweep-CSV values through verbatim, so
re-derivation is byte-identical whenever the sweep CSVs are unchanged.
"""
import os
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)


def read_csv(name):
    with open(os.path.join(HERE, name), newline="") as f:
        return list(csv.DictReader(f))


def write_lf_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")  # LF, UTF-8
        w.writerow(header)
        for r in rows:
            w.writerow(r)


w_rows = read_csv("sweep_weights.csv")
te_rows = read_csv("sweep_theta_e.csv")
tr_rows = read_csv("sweep_theta_r.csv")
k_rows = read_csv("sweep_k.csv")

# --- combined long-format figure data (verbatim stored values) ---------------
data = []
for r in w_rows:
    data.append(["weights", "%s/%s/%s" % (r["w0"], r["w1"], r["w2"]), r["AS"], r["RR"], r["RT"]])
for r in te_rows:
    data.append(["theta_e", r["te"], r["AS"], r["RR"], r["RT"]])
for r in tr_rows:
    data.append(["theta_r", r["tr"], r["AS"], r["RR"], r["RT"]])
for r in k_rows:
    data.append(["k", r["k"], r["AS"], r["RR"], r["RT"]])

write_lf_csv(
    os.path.join(FIG, "sensitivity_figure_data.csv"),
    ["sweep", "setting", "AS", "RR", "RT"],
    data,
)

# --- 2x2 panel: AS and RT vs each swept factor -------------------------------
panels = [
    ("SENS A: weights (w0/w1/w2)", ["%s/%s/%s" % (r["w0"], r["w1"], r["w2"]) for r in w_rows], w_rows),
    ("SENS B: theta_e", [r["te"] for r in te_rows], te_rows),
    ("SENS C: theta_r", [r["tr"] for r in tr_rows], tr_rows),
    ("SENS D: k", [r["k"] for r in k_rows], k_rows),
]
fig, axes = plt.subplots(2, 2, figsize=(9, 6))
for ax, (title, labels, rows) in zip(axes.ravel(), panels):
    xs = range(len(labels))
    as_v = [float(r["AS"]) for r in rows]
    rt_v = [float(r["RT"]) for r in rows]
    ax.plot(xs, as_v, "o-", color="#4472c4", label="AS")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("AS", color="#4472c4")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, fontsize=7, rotation=15)
    ax.set_title(title, fontsize=9)
    ax.grid(alpha=0.3)
    axr = ax.twinx()
    axr.plot(xs, rt_v, "s--", color="#d62728", label="RT")
    axr.set_ylabel("RT", color="#d62728")
fig.suptitle("exp011 sensitivity: TRAP (TDAA) AS and RT across one-factor sweeps")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "sensitivity.png"), dpi=130)
plt.close()

print("exp011 figure: wrote sensitivity.png/sensitivity_figure_data.csv")
