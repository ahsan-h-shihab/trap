"""Run every verification in this artifact and report a summary.

  python scripts/run_all_checks.py            # integrity + reproduction harness + exp010/exp011
                                              # + interval estimates + exp012
  python scripts/run_all_checks.py --exp003   # additionally regenerate exp003 (slower)

Exit code 0 only if every check passes.
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = os.path.join(ROOT, 'frozen')


def manifest_check(name):
    path = os.path.join(FROZEN, 'index', name)
    total = bad = 0
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n').rstrip('\r')
        if not line.strip():
            continue
        digest, rel = line.split('  ', 1)
        total += 1
        f = os.path.join(FROZEN, rel)
        if not os.path.isfile(f) or hashlib.sha256(open(f, 'rb').read()).hexdigest() != digest:
            bad += 1
            print('   digest mismatch or missing:', rel)
    print('   %s: %d entries, %d failures' % (name, total, bad))
    return bad == 0


def run(label, args, cwd):
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    r = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True, env=env,
                       encoding='utf-8', errors='replace')
    tail = [l for l in r.stdout.strip().splitlines() if l.strip()][-1:] or ['']
    print('   %s: exit %d  %s' % (label, r.returncode, tail[0]))
    if r.returncode != 0:
        print(r.stdout[-1500:], r.stderr[-1500:])
    return r.returncode == 0


def main():
    results = []
    print('Artifact integrity (SHA-256 manifests):')
    results.append(manifest_check('MANIFEST.sha256'))
    results.append(manifest_check('trap_manifest.sha256'))
    print('Experiment-directory verifiers:')
    for v in ['verify_all_frozen.py', 'verify_exp005_frozen.py',
              'verify_exp008_frozen.py', 'verify_trap_frozen.py']:
        results.append(run(v, [v], FROZEN))
    print('Reproduction harness (envelope, reachability, condition grid, PDI/HSF, digests):')
    results.append(run('reproduce_all.py', ['reproduce_all.py'], FROZEN))
    print('Behavioral and sensitivity re-derivation (Sections VI-A, VI-B; Figs. 1-2):')
    results.append(run('check_behavioral.py', [os.path.join('scripts', 'check_behavioral.py')], ROOT))
    print('Interval estimates (post-freeze analysis; verifies per-run records first):')
    results.append(run('confidence_intervals.py', [os.path.join('analysis', 'confidence_intervals.py'), '--check'], ROOT))
    print('Gradual degradation, exp012 (post-freeze; control checks, then exact regeneration):')
    results.append(run('exp012 check.py', [os.path.join('postfreeze', 'exp012_gradual_degradation', 'check.py')], ROOT))
    if '--exp003' in sys.argv:
        print('Multi-level condition analysis (Section VI-D; Fig. 3):')
        results.append(run('regenerate_exp003.py', [os.path.join('scripts', 'regenerate_exp003.py')], ROOT))
    print('\nrun_all_checks: %d/%d passed' % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
