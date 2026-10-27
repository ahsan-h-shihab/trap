"""Run exp012 (PROTOCOL.md) and write results/. Refuses to write if the control checks fail."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gradual


def main():
    ok, msgs, files = gradual.build()
    for m in msgs:
        print(m)
    if not ok:
        print('exp012: CONTROL CHECK FAILED; nothing written')
        return 1
    os.makedirs(gradual.RESULTS, exist_ok=True)
    for name, text in files.items():
        with open(os.path.join(gradual.RESULTS, name), 'w', newline='\n') as f:
            f.write(text)
    print('exp012: wrote', ', '.join(sorted(files)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
