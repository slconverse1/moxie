// Runs the moxie interpreter under Pyodide in a worker, so a runaway program can be stopped.
let py = null, runner = null;
const PY = `
import io, sys
sys.setrecursionlimit(2500)
from moxie.interp import Interp
from moxie.values import ArrayV, DictV, GC

def run_moxie(src, mode, gc=False):
    GC[0] = bool(gc)
    out, err = io.StringIO(), io.StringIO()
    try:
        I = Interp(out=out, err=err)
        I.prelude.vars["args"] = ArrayV([])
        I.prelude.vars["env"] = DictV({}, 0)
        if mode == "test":
            code = I.run_tests(src, "main.mxi")[2]
        elif mode == "check":
            code = I.check_source(src, "main.mxi")
        else:
            code = I.run_source(src, "main.mxi")
    except RecursionError:
        return [out.getvalue(), err.getvalue() + "stack overflow: the program recursed too deeply\\n", 1]
    return [out.getvalue(), err.getvalue(), code]
`;
self.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.type === 'init') {
      importScripts(m.pyo + 'pyodide.js');
      py = await loadPyodide({ indexURL: m.pyo });
      py.unpackArchive(await (await fetch(m.zip)).arrayBuffer(), 'zip');
      py.runPython(PY);
      runner = py.globals.get('run_moxie');
      postMessage({ type: 'ready' });
    } else if (m.type === 'run') {
      const [out, err, code] = runner(m.src, m.mode, !!m.gc).toJs();
      postMessage({ type: 'done', out, err, code });
    }
  } catch (err) {
    postMessage({ type: m.type === 'init' ? 'failed' : 'done', out: '', err: 'The interpreter stopped: ' + err, code: 1, message: String(err) });
  }
};
