"""Re-derive the behavioral (exp010) and sensitivity (exp011) results and their
figure data from the policy implementation, and compare them byte-for-byte with
the stored results.

The frozen runners write into their own experiment directories, so they are run
on a temporary copy of frozen/; the stored files are never touched.

Exit code 0 only if every stored CSV and figure_data.csv is reproduced exactly.
"""
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = os.path.join(ROOT, 'frozen')

CHECKED = [
    'experiments/exp010_trap_baseline/raw_results.csv',
    'experiments/exp010_trap_baseline/processed_results.csv',
    'experiments/exp010_trap_baseline/figures/baseline_figure_data.csv',
    'experiments/exp010_trap_baseline/figures/trajectory_figure_data.csv',
    'experiments/exp011_trap_sensitivity/sweep_weights.csv',
    'experiments/exp011_trap_sensitivity/sweep_theta_e.csv',
    'experiments/exp011_trap_sensitivity/sweep_theta_r.csv',
    'experiments/exp011_trap_sensitivity/sweep_k.csv',
    'experiments/exp011_trap_sensitivity/figures/sensitivity_figure_data.csv',
]
FIGURES = [
    'experiments/exp010_trap_baseline/figures/trajectory.png',
    'experiments/exp011_trap_sensitivity/figures/sensitivity.png',
]
SCRIPTS = [
    'experiments/exp010_trap_baseline/run.py',
    'experiments/exp011_trap_sensitivity/run.py',
    'experiments/exp010_trap_baseline/make_figures.py',
    'experiments/exp011_trap_sensitivity/make_figures.py',
]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        work = os.path.join(tmp, 'frozen')
        shutil.copytree(FROZEN, work)
        # Remove the stored outputs so each one must be regenerated.
        for rel in CHECKED + FIGURES:
            os.remove(os.path.join(work, rel))
        for rel in SCRIPTS:
            r = subprocess.run([sys.executable, os.path.join(work, rel)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print('FAIL running', rel, '\n', r.stderr[-2000:])
                return 1
        ok = True
        for rel in CHECKED:
            same = filecmp.cmp(os.path.join(FROZEN, rel), os.path.join(work, rel),
                               shallow=False)
            ok &= same
            print('%-9s %s' % ('IDENTICAL' if same else 'DIFFERS', rel))
        for rel in FIGURES:
            same = filecmp.cmp(os.path.join(FROZEN, rel), os.path.join(work, rel),
                               shallow=False)
            print('%-9s %s (image; not required to be byte-identical)'
                  % ('IDENTICAL' if same else 'DIFFERS', rel))
    print('\ncheck_behavioral:', 'ALL RESULTS REPRODUCED' if ok else 'MISMATCH')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
