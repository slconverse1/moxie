"""Run the helper cases in both dialects:  python tests/run_helpers.py"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
sys.setrecursionlimit(20000)
from moxie.values import GC
from moxie.interp import Interp
from helper_cases import CASES
bad = 0
for gc in (False, True):
    GC[0] = gc
    for name, src, exp, code_exp in CASES:
        out, err = io.StringIO(), io.StringIO()
        try:
            code = Interp(out=out, err=err).run_source(src, name)
        except Exception as e:
            code = 'CRASH %s: %s' % (type(e).__name__, e)
        got = out.getvalue().rstrip('\n').split('\n') if out.getvalue() else []
        if code != code_exp or got != exp:
            bad += 1
            print('FAIL', 'gc' if gc else 'plain', name, '| exit', code, 'got', got, err.getvalue().strip()[:200])
print('%d / %d' % (2 * len(CASES) - bad, 2 * len(CASES)))
sys.exit(1 if bad else 0)
