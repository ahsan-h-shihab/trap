# exp011 — TRAP sensitivity sweeps

**Objective.** Persist the currently-unstored TRAP sensitivity results as
verifiable artifacts: sweep the canonical TRAP (TDAA) policy across four
one-factor grids and record the reported metrics (AS, RR, RT) per sweep point.

**Design.** Import the read-only core unchanged (`sim.run`, `policies.py`);
capture output only. Hold n=100, seed=42, and the baseline parameters fixed
except for the swept factor. Four sweeps on method 'tdaa':
- A (weights w): (0.3,0.4,0.3), (0.4,0.4,0.2), (0.5,0.3,0.2), (0.6,0.2,0.2);
- B (theta_e): 0.03, 0.05, 0.07;
- C (theta_r): 0.05, 0.10, 0.15;
- D (k): 2, 3, 4.
Metrics per `sim.metrics`: AS, RR, RT.

**Parameters (transcribed from `sim.py` `__main__` SENS A/B/C/D blocks and
`run()` defaults; substrate from `policies.py`).**
policy = tdaa; n = 100; seed = 42; baseline w = (0.5, 0.3, 0.2), te = 0.05,
tr = 0.10, k = 3; bands = [0.20, 0.35, 0.50, 0.65, 0.80];
signal ARS = w0*T + w1*S - w2*R.

**Provenance / no science.** Every grid above is transcribed verbatim from the
frozen core; no algorithm, parameter, sweep grid, or result is authored. Results
are obtained by importing the core unchanged.

**Status.** M3-001 scaffold — metadata only (config.json, parameters.json,
seed.txt, log.md). Runner and the four sweep CSVs: M3-003. Sensitivity figure
with `figure_data.csv`: M3-004. `code_commit` = "C5" names the runner-bearing
commit and resolves in history once Commit 5 is created (M3-005). All exp011
artifacts are committed additively in Commit 5 and frozen under manifest A3
(`index/trap_manifest.sha256`) at the M3 tag.
