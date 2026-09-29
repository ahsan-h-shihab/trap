# exp010 — TRAP baseline (policy comparison)

**Objective.** Persist the currently-unstored TRAP baseline results as verifiable
artifacts: evaluate the five authorization policies (Static, Trust-Only,
Risk-Only, Symmetric, TRAP/TDAA) under identical Monte-Carlo conditions and
record the reported metrics (AS with standard deviation, RR, RT, PER, PRR).

**Design.** Import the read-only core unchanged (`sim.run` / `sim.run_records`,
`policies.py`); capture output only. For each policy key in
[static, trust, risk, sym, tdaa], run n=100 Monte-Carlo trajectories at seed=42
with baseline parameters w=(0.5, 0.3, 0.2), te=0.05, tr=0.10, k=3. `gen_trace`
runs independently of the policy, so a fixed seed yields identical traces across
policies. Metrics are computed by `sim.metrics`: AS, RR, RT, PER, PRR.

**Parameters (transcribed from `sim.py` `__main__` BASELINE block and `run()`
defaults; substrate from `policies.py`).**
policies = [static, trust, risk, sym, tdaa]; n = 100; seed = 42;
w = (0.5, 0.3, 0.2); te = 0.05; tr = 0.10; k = 3;
bands = [0.20, 0.35, 0.50, 0.65, 0.80]; signal ARS = 0.5T + 0.3S - 0.2R.

**Provenance / no science.** Every parameter above is transcribed verbatim from
the frozen core; no algorithm, parameter, or result is authored. Results are
obtained by importing the core unchanged.

**Status.** M3-001 scaffold — metadata only (config.json, parameters.json,
seed.txt, log.md). Runner and stored results: M3-002. Baseline and trajectory
figures with per-figure `figure_data.csv`: M3-004. `code_commit` = "C5" names the
runner-bearing commit and resolves in history once Commit 5 is created (M3-005).
All exp010 artifacts are committed additively in Commit 5 and frozen under
manifest A3 (`index/trap_manifest.sha256`) at the M3 tag.
