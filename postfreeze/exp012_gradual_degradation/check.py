"""Verify exp012: control checks, then regenerate every result file in memory and
compare it with the stored copy in results/ (line endings normalized).

Exit code 0 only if the control checks pass and every file matches exactly.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gradual


def main():
    ok, msgs, files = gradual.build()
    for m in msgs:
        print('  ' + m)
    for name, text in sorted(files.items()):
        path = os.path.join(gradual.RESULTS, name)
        if not os.path.isfile(path):
            print('  MISSING', name); ok = False; continue
        stored = open(path, 'rb').read().decode('utf-8').replace('\r\n', '\n')
        same = stored == text
        ok &= same
        print('  %-22s %s' % (name, 'identical' if same else 'MISMATCH'))
    print('exp012 check:', 'PASSED' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
