"""ml: machine learning for learning the ideas (moxie/std/ml.mxi), in both dialects.  Run: python3 tests/run_ml.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEAD = '''import ml
xs Array[Double] = (0.0, 1.0, 2.0, 3.0)
ys Array[Double] = (0.0, 0.0, 1.0, 1.0)
'''

# (name, source, how, text): how is "run" (exit 0 and text in output) or "fail" (nonzero exit and text in output)
CASES = [
 ("sigmoid is one half at zero and approaches 1 for large inputs",
  'import ml\nprintln(ml.sigmoid(0.0))\nprintln(ml.sigmoid(20.0) > 0.99)\nprintln(ml.sigmoid(-20.0) < 0.01)\n', "run", "0.5\ntrue\ntrue"),
 ("fit learns a boundary between the two groups",
  HEAD + 'when ml.fit(xs, ys, 0.5, 2000)\n  Err(e) -> println("no model")\n  Ok(m) -> println("${ml.classify(m, 0.0)} ${ml.classify(m, 3.0)}")\n', "run", "0.0 1.0"),
 ("fit returns the model it trained",
  HEAD + 'println(ml.fit(xs, ys, 0.5, 2000))\n', "run", "Ok(Model(weight: 7.347140700860213, bias: -10.779184952249604))"),
 ("fit with no steps keeps the starting model",
  HEAD + 'println(ml.fit(xs, ys, 0.5, 0))\n', "run", "Ok(Model(weight: 0.0, bias: 0.0))"),
 ("fit rejects labels that are not 0.0 or 1.0",
  'import ml\nxs Array[Double] = (0.0, 1.0)\nbad Array[Double] = (0.0, 2.0)\nprintln(ml.fit(xs, bad, 0.5, 10))\n', "run", "labels must be 0.0 or 1.0"),
 ("examples and labels of known, different sizes are a compile error",
  'import ml\nxs Array[Double] = (0.0, 1.0)\nys Array[Double] = (0.0, 1.0, 1.0)\nprintln(ml.fit(xs, ys, 0.5, 10))\n', "fail", "needs one type"),
 ("nearest_label copies the closest example's label",
  HEAD + 'println(ml.nearest_label(xs, ys, 2.4))\nprintln(ml.nearest_label(xs, ys, 0.2))\n', "run", "Ok(1.0)\nOk(0.0)"),
 ("nearest_label needs examples",
  'import ml\nxs Array[Double] = Array()\nprintln(ml.nearest_label(xs, xs, 1.0))\n', "run", "at least one example"),
 ("two_means splits two clusters around their centres",
  'import ml\nprintln(ml.two_means((1.0, 2.0, 10.0, 11.0), 5))\n', "run", "Ok((1.5, 10.5))"),
 ("two_means needs at least two values",
  'import ml\nprintln(ml.two_means((1.0,), 3))\n', "run", "at least two values"),
]

fails = []
for name, src, how, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        want_fail = how == "fail"
        ok = ((r.returncode != 0) if want_fail else (r.returncode == 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:300]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
