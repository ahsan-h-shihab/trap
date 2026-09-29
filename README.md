# TRAP — Trust-Responsive Runtime Authorization Policy

**Reproducibility artifact for:**
*Trust-Responsive Runtime Authorization for Agentic AI with Empirical
Characterization of Policy Behavior and Parameter Sensitivity*

Ahsan Habib Shihab\* (Al-Farabi Kazakh National University) ·
Štefan Gubo, Ladislav Végh, Imre Gábor Felde (J. Selye University) ·
Amir Mosavi (Obuda University; J. Selye University)
<br><sub>\* Corresponding author</sub>

## Overview

The Trust-Responsive Authorization Policy (TRAP) maps an Authorization Readiness
Score (ARS), a weighted combination of runtime trust, operational stability and
contextual risk, onto discrete authorization levels through an asymmetric rule:
escalation requires a run of consecutive observations that reach a band edge
plus a margin, while a sufficiently sharp drop in readiness restricts authority
at once. On identical Monte Carlo traces with scripted degradation and recovery,
the paper compares TRAP with static, trust-only, risk-only and symmetric
policies, and sweeps its parameters one factor at a time.

**This repository reproduces** every table and figure of the paper from the
frozen artifact (tag `trap-v1-frozen`): the policy behavior comparison
(Table II), the sensitivity sweeps (Table III), Figures 1–3, and the structural
statistics of Section VI-D. Stored results are re-derived and compared
byte-for-byte, and all files are checked against SHA-256 manifests.

## Key results

Policy behavior on identical runtime traces (Table II; *n* = 100, seed 42,
*w* = (0.5, 0.3, 0.2), θ<sub>e</sub> = 0.05, θ<sub>r</sub> = 0.10, *k* = 3).
AS is mean ± SD; n/a denotes a metric undefined on every trajectory; for PER and
PRR, lower is better.

| Policy | AS | RR | RT | PER | PRR |
|---|:-:|:-:|:-:|:-:|:-:|
| Static | 1.0000 ± 0.0000 | n/a | n/a | n/a | n/a |
| Trust-only | 0.9673 ± 0.0100 | 0.00 | 15.13 | 0.0096 | 0.5053 |
| Risk-only | 0.9385 ± 0.0148 | 0.00 | 2.28 | 0.2405 | 0.7950 |
| Symmetric | 0.9646 ± 0.0104 | 2.00 | 17.14 | 0.0000 | 0.4798 |
| **TRAP** | **0.9699 ± 0.0064** | **0.00** | **10.72** | **0.0000** | 0.5550 |

<sub>AS: Authorization Stability · RR: Restriction Responsiveness ·
RT: Recovery Time · PER: Protective Efficiency Ratio ·
PRR: Progressive Recovery Ratio (defined in the paper).</sub>

## Figures

<p align="center">
  <img src="assets/fig1_trajectory.png" alt="Figure 1: TRAP response trajectory" width="720">
</p>

**Figure 1. TRAP response trajectory.** TRAP response over one seed-42
trajectory: trust, stability, risk and ARS (left axis) with the authorization
level (right axis). Dotted lines mark degradation (*t* = 40) and recovery onset
(*t* = 60).

<p align="center">
  <img src="assets/fig2_sensitivity.png" alt="Figure 2: parameter sensitivity" width="720">
</p>

**Figure 2. Parameter sensitivity.** AS (left axes) and RT (right axes) across
the four one-factor sweeps.

<p align="center">
  <img src="assets/fig3_multilevel_conditions.png" alt="Figure 3: multi-level condition recurrence" width="560">
</p>

**Figure 3. Multi-level condition recurrence.** Share of recurring conditions
observed at two or more authorization levels against bin width, per seed and
averaged.

<sub>The images in `assets/` are byte-identical copies of the frozen figures
listed in the mapping below.</sub>

## Experiments

From Table I of the paper. The behavioral contribution rests on exp010 and
exp011; exp003–exp009 were committed by the companion study and are drawn on as
supporting evidence.

| ID | Role | Scale |
|---|---|---|
| exp003 | Multi-level condition prevalence | 5×5 settings, 4000 ep. each |
| exp004 | Admissibility envelope | 20,000 episodes |
| exp005 | Generator verification (pilot) | 264 histories |
| exp006 | Pilot path-dependence (null result) | 50 targets |
| exp007 | Reachable memory enumeration | BFS, 500 score bins |
| exp008 | Generator verification (final) | 200 histories |
| exp009 | Primary path-dependence measurement | 50 targets × 2 seeds |
| exp010 | Policy behavior comparison | 5 policies × 100 runs |
| exp011 | Parameter sensitivity | 13 sweep points |

Each lives in `frozen/experiments/<id>_*/` with its metadata, runner and stored
results.

## Reproduce

Python 3.12. No GPU, network access or external data are needed.

```bash
pip install -r requirements.txt
python scripts/run_all_checks.py            # integrity, harness, exp010/exp011 (under a minute)
python scripts/run_all_checks.py --exp003   # additionally regenerate exp003 (about 6 minutes)
```

<details>
<summary>Individual steps</summary>

```bash
python scripts/check_behavioral.py      # Tables II-III, Figs. 1-2 data
python scripts/regenerate_exp003.py     # Sec. VI-C values, Fig. 3
cd frozen
python reproduce_all.py                 # Sec. IV / VI-D statistics (31 checks)
python verify_all_frozen.py             # exp003-exp009 digests and file sets
python verify_trap_frozen.py            # exp010-exp011 digests and file sets
python verify_exp005_frozen.py
python verify_exp008_frozen.py
```

On a Windows console, set `PYTHONIOENCODING=utf-8` before running
`reproduce_all.py` directly; `run_all_checks.py` sets it automatically.
</details>

Stored results are compared byte-for-byte. Figure images are also regenerated,
but only their underlying data files are required to match exactly.

## Paper ↔ Artifact

Paths below are relative to `frozen/experiments/` unless shown in full.

| Paper element | Files | Reproduced by |
|---|---|---|
| Table II / Sec. VI-A | `exp010_trap_baseline/raw_results.csv`, `processed_results.csv` | `scripts/check_behavioral.py` |
| Table III / Sec. VI-B | `exp011_trap_sensitivity/sweep_*.csv` | `scripts/check_behavioral.py` |
| Figure 1 | `exp010_trap_baseline/figures/trajectory.png`, `trajectory_figure_data.csv` | `scripts/check_behavioral.py` (data) |
| Figure 2 | `exp011_trap_sensitivity/figures/sensitivity.png`, `sensitivity_figure_data.csv` | `scripts/check_behavioral.py` (data) |
| Figure 3 / Sec. VI-C | `exp003_robustness/figures/pct_multi_vs_binwidth.png`, `raw_results.csv`, `processed_results.csv` | `scripts/regenerate_exp003.py` |
| Sec. VI-D structural statistics | exp004–exp009, `frozen/pdi.py`, `frozen/generator*.py` | `frozen/reproduce_all.py` |
| Algorithm 1 / Sec. III | `frozen/policies.py`, `frozen/sim.py`, `frozen/variants.py` | digest-verified (`MANIFEST.sha256`) |
| Sec. IX (integrity) | `frozen/index/`, `frozen/verify_*.py` | `scripts/run_all_checks.py` |

The structural results of Sections IV and VI-D are those of the companion study
(A. H. Shihab, A. Mussa and M. Mansurova, "When Identical Conditions Yield
Different Authority: Measuring Path-Dependence in Trust-to-Authorization
Policies", MIWAI 2026, to appear in Springer LNAI), which shares this frozen
artifact.

## Repository structure

```
README.md, LICENSE            this file; MIT License
requirements.txt               pinned environment
assets/                        copies of Figures 1-3 for this page
scripts/                       run_all_checks.py, check_behavioral.py, regenerate_exp003.py
frozen/                        the frozen artifact (tag trap-v1-frozen)
  sim.py, policies.py, variants.py        simulator and policies
  pdi.py, generator.py, generator_v2.py   path-dependence instruments
  reproduce_all.py, verify_*.py           reproduction harness and verifiers
  index/                                  SHA-256 manifests and digests
  experiments/exp003 ... exp011           runners, stored results, figures
```

## Provenance

`frozen/` is the file tree of tag `trap-v1-frozen`, commit
`ede109c1d392e26788c1980611d825c07387f2c4`, with four internal
project-management files removed. None of the removed files is covered by a
manifest or used by any script here. Every remaining file is byte-identical to
that commit; `frozen/index/MANIFEST.sha256` (73 files) and
`frozen/index/trap_manifest.sha256` (28 files) record their digests.

<details>
<summary>Notes</summary>

- `frozen/README.md` and `frozen/requirements.txt` are the original package
  files, kept unchanged because they are covered by the integrity manifest. The
  per-experiment commands in `frozen/README.md` for exp003–exp009 assume the
  original working directory `/tmp/tdaa`, which those runners hard-code; use the
  scripts above instead. `frozen/requirements.txt` omits the plotting library;
  the root `requirements.txt` is complete.
- The runners for exp004–exp009 are included as the record of how those results
  were produced. Their results are regenerated here through `reproduce_all.py`
  rather than by re-running those runners.
</details>

## Licence

Released under the [MIT License](LICENSE).
