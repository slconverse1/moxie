"""stats: statistics and prediction for learning (moxie/std/stats.mxi), in both dialects.  Run: python3 tests/run_stats.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The expected numbers were computed independently with Python's statistics module and numpy.
HEAD = '''import stats
xs: Array[Double] = (2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0)
hours: Array[Double] = (1.0, 2.0, 3.0, 4.0, 5.0)
score: Array[Double] = (52.0, 58.0, 65.0, 70.0, 78.0)
'''

# (name, source, how, text): how is "run" (exit 0 and text in output) or "fail" (nonzero exit and text in output)
CASES = [
 ("mean, variance, standard deviation, median",
  HEAD + 'println("${stats.mean(xs)} ${stats.variance(xs)} ${stats.stddev(xs)} ${stats.median(xs)}")\n', "run", "5.0 4.0 2.0 4.5"),
 ("sample variance divides by n - 1",
  HEAD + 'println("${stats.sample_variance(xs):.4f} ${stats.sample_stddev(xs):.4f}")\n', "run", "4.5714 2.1381"),
 ("median of an odd count and of one value",
  'import stats\nodd: Array[Double] = (9.0, 1.0, 5.0)\none: Array[Double] = Array(7.0)\nprintln("${stats.median(odd)} ${stats.median(one)} ${stats.variance(one)}")\n', "run", "5.0 7.0 0.0"),
 ("quantiles interpolate and stay inside 0 to 1",
  HEAD + 'println(stats.quantile(xs, 0.25))\nprintln(stats.quantile(xs, 0.0))\nprintln(stats.quantile(xs, 1.0))\nprintln(stats.quantile(xs, 1.5))\n', "run", "Ok(4.0)\nOk(2.0)\nOk(9.0)\nErr(Error(code: 1, message: \"quantile: q must be between 0.0 and 1.0\"))"),
 ("z-scores",
  HEAD + 'println(stats.z_scores(hours))\n', "run", "Ok(Array(-1.414213562373095, -0.7071067811865475, 0.0, 0.7071067811865475, 1.414213562373095))"),
 ("z-scores of values that do not vary are an Err",
  'import stats\nsame: Array[Double] = (3.0, 3.0)\nprintln(stats.z_scores(same))\n', "run", "do not vary"),
 ("covariance and correlation",
  HEAD + 'println("${stats.covariance(hours, score):.4f}")\nprintln(stats.correlation(hours, score))\n', "run", "12.8000\nOk(0.9980525784828885)"),
 ("a list that does not vary has no correlation",
  'import stats\nsame: Array[Double] = (3.0, 3.0, 3.0)\nys: Array[Double] = (1.0, 2.0, 3.0)\nprintln(stats.correlation(same, ys))\n', "run", "no correlation"),
 ("fit a line and predict",
  HEAD + 'when stats.fit_line(hours, score)\n  Err(e) -> println("no line")\n  Ok(line) ->\n    println("${line.slope:.4f} ${line.intercept:.4f} ${line.r_squared:.4f}")\n    println("${stats.predict(line, 6.0):.4f}")\n', "run", "6.4000 45.4000 0.9961\n83.8000"),
 ("a perfect line fits with r_squared 1",
  'import stats\nx: Array[Double] = (1.0, 2.0, 3.0, 4.0)\ny: Array[Double] = (3.0, 5.0, 7.0, 9.0)\nwhen stats.fit_line(x, y)\n  Err(e) -> println("no line")\n  Ok(line) -> println("${line.slope} ${line.intercept} ${line.r_squared} ${stats.predict(line, 10.0)}")\n', "run", "2.0 1.0 1.0 21.0"),
 ("no line fits when every x is the same",
  'import stats\nsame: Array[Double] = (3.0, 3.0, 3.0)\nys: Array[Double] = (1.0, 2.0, 3.0)\nprintln(stats.fit_line(same, ys))\n', "run", "no line to fit"),
 ("predict_all, rmse and mean absolute error",
  HEAD + 'when stats.fit_line(hours, score)\n  Err(e) -> println("no line")\n  Ok(line) ->\n    fitted = stats.predict_all(line, hours)\n    println("${stats.rmse(score, fitted):.4f} ${stats.mean_absolute_error(score, fitted):.4f}")\n', "run", "0.5657 0.4800"),
 ("moving average and exponential smoothing",
  HEAD + 'println(stats.moving_average(score, 3))\nprintln(stats.smooth(score, 0.5))\n', "run", "List(58.333333333333336, 64.33333333333333, 71.0)\n71.5"),
 ("arrays of different lengths are a compile error",
  'import stats\na: Array[Double] = (1.0, 2.0, 3.0)\nb: Array[Double] = (1.0, 2.0)\nprintln(stats.covariance(a, b))\n', "fail", "Array[Double][2]"),
]

fails = []
for name, src, how, word in CASES:
    for gc in (False, True):
        if how == "nogc-fail" and gc:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        want_fail = how in ("fail", "nogc-fail")
        ok = ((r.returncode != 0) if want_fail else (r.returncode == 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:300]}"))
        if not ok:
            fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
