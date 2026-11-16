"""`deriving dyn` on enums (and enum fields in tuples).  Run: python3 tests/run_dynenum.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
 ('an enum derives dyn and round-trips', 'import json\nenum Shape deriving show, dyn\n  Circle(r Float)\n  Rect(w Float, h Float)\n  Empty\ns = Shape.Rect(w: 2.0, h: 3.0)\nd = s.to_dyn()\nprintln(d.to_json())\nprintln(Shape.from_dyn(d))\nprintln(Shape.from_dyn(Shape.Empty.to_dyn()))\n', 0, '{"case":"Rect","w":2.0,"h":3.0}\nOk(Shape.Rect(2.0, 3.0))\nOk(Shape.Empty)'),
 ('reading a document', 'import json\nenum Shape deriving show, dyn\n  Circle(r Float)\n  Empty\nprintln(Shape.from_dyn(json.parse("{\\"case\\": \\"Circle\\", \\"r\\": 1.5}")?))\n', 0, 'Ok(Shape.Circle(1.5))'),
 ('an unknown case is an Err', 'import json\nenum Shape deriving show, dyn\n  Circle(r Float)\nr = Shape.from_dyn(json.parse("{\\"case\\": \\"Blob\\"}")?)\nprintln(r)\n', 0, 'unknown case'),
 ('a missing field is an Err', 'import json\nenum Shape deriving show, dyn\n  Circle(r Float)\nprintln(Shape.from_dyn(json.parse("{\\"case\\": \\"Circle\\"}")?))\n', 0, 'no key'),
 ('a tuple holds an enum', 'import json\nenum Color deriving show, dyn\n  Red\n  Rgb(r Int, g Int, b Int)\ntuple Pixel deriving show, dyn\n  x Int\n  c Color\np = Pixel(x: 1, c: Color.Rgb(r: 1, g: 2, b: 3))\nprintln(p.to_dyn().to_json())\nprintln(Pixel.from_dyn(p.to_dyn()))\n', 0, 'Ok(Pixel(x: 1, c: Color.Rgb(1, 2, 3)))'),
 ('an enum holds a list', 'import json\nenum Poly deriving show, dyn\n  Pts(xs List[Int])\nprintln(Poly.from_dyn(Poly.Pts(xs: List(1, 2)).to_dyn()))\n', 0, 'Ok(Poly.Pts(List(1, 2)))'),
 ('unnamed case fields are an error', 'import json\nenum E deriving dyn\n  A(Int)\n', 2, 'unnamed fields'),
 ('a generic enum is an error', 'import json\nenum E[T] deriving dyn\n  A(x T)\n', 2, "generic type can't derive"),
]
fails = []
for name, src, rc_want, word in CASES:
    for gc in (False, True):
        with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
            f.write(src)
        cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["check" if rc_want == 2 else "run", f.name]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        os.unlink(f.name)
        o = r.stdout + r.stderr
        ok = (r.returncode == rc_want or (rc_want == 2 and r.returncode != 0)) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:200]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
