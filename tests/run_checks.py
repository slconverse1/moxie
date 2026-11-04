import sys; import os; H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,H); sys.path.insert(0,os.path.join(H,'..'))
from check_cases import CASES
from moxie.interp import Interp
from moxie.parser import parse_program
I=Interp(); bad=0
for name,src,exp in CASES:
    try:
        d=[str(x) for x in I.static_check(parse_program(src,'t'))]
    except Exception as e:      # a syntax error is a diagnostic too
        d=[str(e)]
    ok = (not d) if exp is None else any(exp in x for x in d)
    if not ok: bad+=1; print("FAIL",name,d)
print(len(CASES)-bad,"/",len(CASES))
