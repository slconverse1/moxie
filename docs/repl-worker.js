// Runs a moxie REPL session under Pyodide in a worker, so a runaway input can be stopped.
let py = null, start = null, feed = null, more = null;
const PY = `
import io, sys
sys.setrecursionlimit(2500)
from moxie.interp import Interp
from moxie.values import ArrayV, DictV, GC
from moxie.perms import Perms
from moxie.repl import Session, needs_more

OUT, ERR, S = io.StringIO(), io.StringIO(), None

def repl_start(gc=False):
    global S
    GC[0] = bool(gc)
    I = Interp(out=OUT, err=ERR)
    I.platform = "browser"          # no network or ffi, and calls the browser lacks are check-time errors
    I.perms = Perms.browser()
    I.prelude.vars["args"] = ArrayV([])
    I.prelude.vars["env"] = DictV({}, 0)
    S = Session(I, OUT, ERR)

def repl_feed(text):
    for b in (OUT, ERR):
        b.seek(0)
        b.truncate()
    try:
        S.feed(text)
    except EOFError:
        ERR.write("there is nothing to quit in the browser; reload the page to leave\\n")
    except RecursionError:
        ERR.write("stack overflow: the input recursed too deeply\\n")
    return [OUT.getvalue(), ERR.getvalue()]

def repl_more(text):
    return needs_more(text)
`;
self.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.type === 'init') {
      importScripts(m.pyo + 'pyodide.js');
      py = await loadPyodide({ indexURL: m.pyo });
      py.unpackArchive(await (await fetch(m.zip)).arrayBuffer(), 'zip');
      py.runPython(PY);
      start = py.globals.get('repl_start'); feed = py.globals.get('repl_feed'); more = py.globals.get('repl_more');
      start(!!m.gc);
      postMessage({ type: 'ready' });
    } else if (m.type === 'more') {
      postMessage({ type: 'more', id: m.id, more: !!more(m.text) });
    } else if (m.type === 'feed') {
      const [out, err] = feed(m.text).toJs();
      postMessage({ type: 'done', out, err });
    }
  } catch (err) {
    postMessage({ type: m.type === 'init' ? 'failed' : 'done', out: '', err: 'The interpreter stopped: ' + err, message: String(err) });
  }
};
