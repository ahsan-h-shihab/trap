#!/usr/bin/env python3
"""M3 TRAP freeze verifier (A6) -- milestone-owned, additive to and separate from
`verify_all_frozen.py` (which is byte-unchanged and retains its M2 scope).

Verifies the TRAP-scope experiments (exp010, exp011) against the milestone-scoped
manifest A3 (`index/trap_manifest.sha256`):

 (a) BYTE integrity: every experiment file's bytes hash to the value A3 records
     for that path; hard-fail on pointer-shaped files (C1 bytes-not-pointers).
 (b) I2 exact-set: the experiment directory's committed file set equals the
     `exactset_source` key set (the A4 sidecar for that experiment).

The experiment set is obtained solely from the keys of
`index/trap_freeze_surface.json` (A5) -- list-driven, no filesystem discovery of
the experiment set -- mirroring M2 Erratum E-1. Run from the repository root.
"""
import json
import hashlib
import os
import sys

LFS_PTR = b"version https://git-lfs.github.com/spec"


def sha256_bytes(path):
    data = open(path, "rb").read()
    if data[:40] == LFS_PTR[:40]:
        raise RuntimeError(f"POINTER-SHAPED (C1 violation): {path}")
    return hashlib.sha256(data).hexdigest()


def load_manifest(path):
    """Parse a sha256sum-style manifest ('<hash>  <path>' per line)."""
    m = {}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        h, p = line.split("  ", 1)
        m[p] = h
    return m


def committed_set(expdir):
    out = set()
    for r, _, fs in os.walk(expdir):
        for f in fs:
            out.add(os.path.join(r, f).replace("\\", "/"))
    return out


def main():
    a3 = load_manifest("index/trap_manifest.sha256")
    surface = json.load(open("index/trap_freeze_surface.json"))["experiments"]
    all_ok = True
    for exp in sorted(surface):
        rec = surface[exp]
        exact_src = json.load(open(rec["exactset_source"]))
        exp_ok = True
        # (a) byte integrity vs A3 + C1 pointer check
        for path in rec["paths"]:
            if path not in a3:
                print(f"[FAIL] not covered by A3: {path}")
                exp_ok = False
                continue
            try:
                got = sha256_bytes(path)
            except RuntimeError as e:
                print(f"[FAIL] {e}")
                exp_ok = False
                continue
            if got != a3[path]:
                print(f"[FAIL] hash mismatch vs A3: {path}")
                exp_ok = False
        # (b) I2 exact-set vs exactset_source key set
        keyset = set(exact_src.keys())
        present = committed_set(exp)
        miss = keyset - present
        extra = present - keyset
        if miss:
            print(f"[FAIL] I2 missing in {exp}: {sorted(miss)}")
            exp_ok = False
        if extra:
            print(f"[FAIL] I2 extra in {exp}: {sorted(extra)}")
            exp_ok = False
        print(f"{'[OK]  ' if exp_ok else '[FAIL]'} {exp} "
              f"(sidecar: paths={len(rec['paths'])} dir={len(exact_src)})")
        all_ok = all_ok and exp_ok
    print("\nverify_trap_frozen:", "ALL PASS" if all_ok else "FAILURES PRESENT")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
