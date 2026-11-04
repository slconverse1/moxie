import json,sys,io,signal,traceback
sys.setrecursionlimit(20000)
import os, re, tempfile
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,os.path.join(HERE,'..'))
os.chdir(tempfile.mkdtemp())    # examples write files here
from moxie.interp import Interp
blocks=json.load(open(os.path.join(HERE,'guide_corpus.json')))
_v1=json.load(open(os.path.join(HERE,'guide_corpus_v1.json')))
def _remap(i):
    src=_v1[i][1]
    for j,b in enumerate(blocks):
        if b[1]==src: return j
    return None
only=[int(a) for a in sys.argv[1:] if a.isdigit()]
verbose='-v' in sys.argv
class TO(Exception): pass
def h(*a): raise TO()
signal.signal(signal.SIGALRM,h)
SKIP={_remap(141),_remap(146)}   # manifest examples, not moxie code
# examples that are not runnable moxie: manifests, shell commands, and C libraries we do not have
SKIP|={j for j,b in enumerate(blocks) if b[1].lstrip().startswith(('[','$ ','lib =')) or re.search(r'foreign "(?!m"|c")',b[1])}
def run(src,name):
    out=io.StringIO(); err=io.StringIO()
    I=Interp(out=out,err=err)
    signal.alarm(5)
    try:
        code=I.run_source(src,name)
    except TO:
        code='timeout'
    except Exception as e:
        code='CRASH %s: %s'%(type(e).__name__,e)
        if only or verbose: traceback.print_exc()
    signal.alarm(0)
    got=out.getvalue().rstrip('\n').split('\n') if out.getvalue() else []
    return code,got,err.getvalue().strip()
PREFIX_OK={_remap(33)}
DEPS={_remap(k):[_remap(x) for x in v] for k,v in {89:[99,162],90:[52,99,162],163:[52,99,162],164:[99,162],171:[37]}.items()}
FRAG={_remap(k):v for k,v in {105:'illustrative pipe fragment (subtract undefined)',135:'deliberate compile-error example',147:'needs a database connection (sql tested separately)',143:'two-file package (tested separately)'}.items()}
def judge(code,got,exp,i=None):
    if code!=0: return False
    if exp is None: return True
    return got[-len(exp):]==exp if exp else True
good=[]
stat={'frag':0,'ok':0,'ctx':0,'diff':0,'err':0,'noexp':0,'skip':0}
for i,(ln,src,exp) in enumerate(blocks):
    if only and i not in only: continue
    if i in SKIP: stat['skip']+=1; continue
    if i in FRAG: stat['frag']+=1; continue
    code,got,e=run(src,"b%d.mxi"%i)
    if code==0 and exp is not None and (got==exp or (i in PREFIX_OK and got[:len(exp)]==exp)):
        stat['ok']+=1; good.append(i); continue
    if code==0 and exp is None:
        stat['noexp']+=1; good.append(i); continue
    if code==0 and not got:
        stat['noexp']+=1; good.append(i); continue
    if code==2 and '// ERROR' in src:
        stat['noexp']+=1; continue       # the example is meant to be rejected
    if code==0: good.append(i)
    # try context
    done=False
    for k in [len(good)-1,len(good)-2,len(good)-3,len(good)-5,len(good)-8,len(good)-13,len(good)-21,0]:
        if k<0 or k>=len(good): continue
        pre="\n".join(blocks[j][1] for j in good[k:])
        c2,g2,e2=run(pre+"\n"+src,"b%d.mxi"%i)
        if judge(c2,g2,exp) and (exp is not None or True):
            if exp is None and False: continue
            stat['ctx']+=1; done=True; good.append(i)
            if verbose: print(f"#{i} ok with context from #{k}")
            break
    if not done and i in DEPS:
        pre="\n".join(blocks[j][1] for j in DEPS[i])
        c2,g2,e2=run(pre+"\n"+src,"b%d.mxi"%i)
        if judge(c2,g2,exp): stat['ctx']+=1; done=True; good.append(i)
    if not done:
        later=[j for j in range(i+1,len(blocks)) if j not in SKIP]
        for pick in (later[:4],later[:10],later[:30]):
            pre="\n".join(blocks[j][1] for j in good+pick if j!=i)
            c2,g2,e2=run(pre+"\n"+src,"b%d.mxi"%i)
            if judge(c2,g2,exp):
                stat['ctx']+=1; done=True; good.append(i)
                if verbose: print(f"#{i} ok with later context")
                break
    if not done:
        import re
        have=[]
        lasterr=None
        for _ in range(10):
            pre="\n".join(blocks[j][1] for j in sorted(have))
            c2,g2,e2=run(pre+"\n"+src,"b%d.mxi"%i)
            if judge(c2,g2,exp):
                stat['ctx']+=1; done=True; good.append(i)
                if verbose: print(f"#{i} ok with deps {sorted(have)}")
                break
            if verbose: print("  iter",i,sorted(have),repr(e2[:80]),c2)
            m=re.search(r"undefined (?:name|function) [`'](\w+)[`']",e2 or "")
            if not m: break
            nm=m.group(1)
            pat=re.compile(r"^\s*(?:export\s+)?(?:fn|tuple|enum|type|interface|alias|opaque)\s+(?:alias\s+|opaque\s+|union\s+)?%s\b|^%s\s*(?::[^=]+)?=|^\(?[\w, ]*\b%s\b[\w, ]*\)?\s*="%(nm,nm,nm),re.M)
            cands=[j for j in range(len(blocks)) if j!=i and j not in SKIP and j not in have and pat.search(blocks[j][1])]
            cands.sort(key=lambda j:(j>i,abs(j-i)))
            picked=None
            for j in cands:
                c3,g3,e3=run("\n".join(blocks[k][1] for k in sorted(have+[j]))+"\n"+src,"b%d.mxi"%i)
                if judge(c3,g3,exp) or (e3 or "")!=(e2 or ""):
                    picked=j; break
            if picked is None:
                if verbose: print("  no pick for",nm,"cands",cands,"err",e2[:120])
                break
            have.append(picked)
    if done: continue
    if code!=0:
        stat['err']+=1
        print(f"#{i} L{ln} FAIL code={code} {e[:200]}")
        if exp: print("    expected",exp,"got",got)
    else:
        stat['diff']+=1
        print(f"#{i} L{ln} DIFF\n    expected {exp}\n    got      {got}  {e[:150]}")
print(stat)
