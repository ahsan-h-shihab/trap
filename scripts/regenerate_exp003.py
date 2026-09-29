"""Regenerate the multi-level condition analysis (exp003; paper Section VI-C and
Fig. 3) and compare it byte-for-byte with the stored results.

The frozen runner frozen/experiments/exp003_robustness/run.py hard-codes the
directory it originally ran in (/tmp/tdaa). It is covered by integrity digests
and is therefore not edited. Instead, this script copies frozen/ to a temporary
directory and executes the runner's unmodified source with that one path string
substituted in memory, so it imports the frozen core and writes only into the
temporary copy. Nothing else in the runner is changed.

The runner also records the git commit of its working directory in
config.json; outside the original repository it records "nogit", so config.json
is expected to differ in that field only and is not compared.

Exit code 0 only if raw_results.csv and processed_results.csv are reproduced
exactly.
"""
import filecmp
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = os.path.join(ROOT, 'frozen')
EXP = 'experiments/exp003_robustness'
CHECKED = [EXP + '/raw_results.csv', EXP + '/processed_results.csv']
FIGURE = EXP + '/figures/pct_multi_vs_binwidth.png'
ORIGINAL_ROOT = '/tmp/tdaa'


def main():
    with tempfile.TemporaryDirectory() as tmp:
        work = os.path.join(tmp, 'frozen').replace('\\', '/')
        shutil.copytree(FROZEN, work)
        for rel in CHECKED + [FIGURE]:
            os.remove(os.path.join(work, rel))
        src = open(os.path.join(FROZEN, EXP, 'run.py'), encoding='utf-8').read()
        assert src.count(ORIGINAL_ROOT) >= 1
        src = src.replace(ORIGINAL_ROOT, work)
        cwd = os.getcwd()
        try:
            os.chdir(work)
            exec(compile(src, os.path.join(work, EXP, 'run.py'), 'exec'),
                 {'__name__': '__main__'})
        finally:
            os.chdir(cwd)
        ok = True
        for rel in CHECKED:
            same = filecmp.cmp(os.path.join(FROZEN, rel), os.path.join(work, rel),
                               shallow=False)
            ok &= same
            print('%-9s %s' % ('IDENTICAL' if same else 'DIFFERS', rel))
        same = filecmp.cmp(os.path.join(FROZEN, FIGURE), os.path.join(work, FIGURE),
                           shallow=False)
        print('%-9s %s (image; not required to be byte-identical)'
              % ('IDENTICAL' if same else 'DIFFERS', FIGURE))
        new_cfg = json.load(open(os.path.join(work, EXP, 'config.json')))
        old_cfg = json.load(open(os.path.join(FROZEN, EXP, 'config.json')))
        diff = sorted(k for k in set(new_cfg) | set(old_cfg) if new_cfg.get(k) != old_cfg.get(k))
        print('config.json fields differing from stored:', diff or 'none')
    print('\nregenerate_exp003:', 'RESULTS REPRODUCED' if ok else 'MISMATCH')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
