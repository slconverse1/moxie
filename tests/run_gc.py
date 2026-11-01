"""Run the moxie/gc cases:  python tests/run_gc.py [-v]"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
sys.setrecursionlimit(20000)
from moxie.values import GC
GC[0] = True
from moxie.interp import Interp
from gc_cases import CASES
verbose = '-v' in sys.argv
bad = 0
for name, src, exp, code_exp in CASES:
    out, err = io.StringIO(), io.StringIO()
    I = Interp(out=out, err=err)
    try:
        code = I.run_source(src, name)
    except Exception as e:
        code = 'CRASH %s: %s' % (type(e).__name__, e)
    got = out.getvalue().rstrip('\n').split('\n') if out.getvalue() else []
    ok = code == code_exp and got == exp
    if not ok:
        bad += 1
    if not ok or verbose:
        print(('ok   ' if ok else 'FAIL ') + name)
        if not ok:
            print('  exit', code, 'expected', code_exp, '| got', got, 'expected', exp)
            if err.getvalue().strip():
                print('  stderr:', err.getvalue().strip()[:300])
print('%d / %d' % (len(CASES) - bad, len(CASES)))
sys.exit(1 if bad else 0)
