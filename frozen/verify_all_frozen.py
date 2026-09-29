#!/usr/bin/env python3
"""M2-004 (Rev-2 + clarification) unified freeze verifier.
Per experiment:
 (a) BYTE integrity: verify each file in freeze_source (BYTE oracle) vs resolved bytes;
     hard-fail on pointer-shaped files (C1). For exp005/exp008 freeze_source is the
     read-only legacy internal file (cross-experiment coverage).
 (b) I2 exact-set: experiment dir committed file set == exactset_source key set
     (M2-generated directory key set, for ALL experiments).
Legacy verify_exp005/exp008 are INVOKED (authoritative) and never modified.
"""
import json, hashlib, subprocess, sys, os
LFS_PTR=b"version https://git-lfs.github.com/spec"
def sha256_bytes(path):
    data=open(path,"rb").read()
    if data[:40]==LFS_PTR[:40]: raise RuntimeError(f"POINTER-SHAPED (C1 violation): {path}")
    return hashlib.sha256(data).hexdigest()
def committed_set(expdir):
    out=set()
    for r,_,fs in os.walk(expdir):
        for f in fs: out.add(os.path.join(r,f).replace("\\","/"))
    return out
def main():
    surface=json.load(open("index/freeze_surface.json"))["experiments"]; all_ok=True
    for exp in sorted(surface):
        rec=surface[exp]; cov=rec["coverage"]
        byte_src=json.load(open(rec["freeze_source"]))          # BYTE oracle
        exact_src=json.load(open(rec["exactset_source"]))       # I2 key set
        exp_ok=True
        # (a) byte integrity + C1
        for path,want in byte_src.items():
            try: got=sha256_bytes(path)
            except RuntimeError as e: print(f"[FAIL] {e}"); exp_ok=False; continue
            if got!=want: print(f"[FAIL] hash mismatch: {path}"); exp_ok=False
        # (b) I2 exact-set vs exactset_source key set
        keyset=set(exact_src.keys()); present=committed_set(exp)
        miss=keyset-present; extra=present-keyset
        if miss: print(f"[FAIL] I2 missing in {exp}: {sorted(miss)}"); exp_ok=False
        if extra: print(f"[FAIL] I2 extra in {exp}: {sorted(extra)}"); exp_ok=False
        if cov=="internal":
            script={"experiments/exp005_convergent_generator":"verify_exp005_frozen.py",
                    "experiments/exp008_generator_v2_verification":"verify_exp008_frozen.py"}[exp]
            r=subprocess.run([sys.executable,script],capture_output=True,text=True)
            if r.returncode!=0: print(f"[FAIL] legacy {script} exit {r.returncode}"); exp_ok=False
            else: print(f"[ok]   legacy {script}: PASS")
        print(f"{'[OK]  ' if exp_ok else '[FAIL]'} {exp} ({cov}: byte={len(byte_src)} dir={len(exact_src)})")
        all_ok=all_ok and exp_ok
    print("\nverify_all_frozen:", "ALL PASS" if all_ok else "FAILURES PRESENT")
    return 0 if all_ok else 1
if __name__=="__main__": sys.exit(main())
