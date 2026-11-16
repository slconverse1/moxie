"""`deriving dyn` on generic tuples and enums (a type parameter needs `json.Dynable`).  Run: python3 tests/run_dyngeneric.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
HEAD = "import json\n"
PAIR = "tuple Pair[A, B] deriving show, dyn\n  first A\n  second B\n"
PT = "tuple Pt deriving show, dyn\n  x Int\n  y Int\n"
TREE = "enum Tree[T] deriving show, dyn\n  Leaf(v T)\n  Node(l Tree[T], r Tree[T])\n"
CASES = [
 ("a generic tuple writes and reads", HEAD + PAIR + 'p = Pair(first: 1, second: "a")\nprintln(p.to_dyn().to_json())\nprintln(Pair[Int, String].from_dyn(p.to_dyn()))\n', 0, '{"first":1,"second":"a"}\nOk(Pair(first: 1, second: "a"))'),
 ("type arguments that derive dyn and lists", HEAD + PAIR + PT + 'q = Pair(first: Pt(x: 1, y: 2), second: List(true, false))\nprintln(q.to_dyn().to_json())\nprintln(Pair[Pt, List[Bool]].from_dyn(q.to_dyn()))\n', 0, 'Ok(Pair(first: Pt(x: 1, y: 2), second: List(true, false)))'),
 ("a recursive generic enum", HEAD + TREE + 't = Tree.Node(l: Tree.Leaf(v: 1), r: Tree.Leaf(v: 2))\nprintln(t.to_dyn().to_json())\nprintln(Tree[Int].from_dyn(t.to_dyn()))\n', 0, 'Ok(Tree.Node(Tree.Leaf(1), Tree.Leaf(2)))'),
 ("the same enum at another type", HEAD + TREE + 'println(Tree[String].from_dyn(Tree.Leaf(v: "x").to_dyn()))\n', 0, 'Ok(Tree.Leaf("x"))'),
 ("a wrong kind inside is an Err", HEAD + PAIR + 'println(Pair[Int, Int].from_dyn(json.parse("{\\"first\\": 1, \\"second\\": \\"no\\"}")?))\n', 0, "not an Int"),
 ("a non-generic type is still readable", HEAD + PT + 'println(Pt.from_dyn(Pt(x: 3, y: 4).to_dyn()))\n', 0, 'Ok(Pt(x: 3, y: 4))'),
 ("a type with no Dyn form is not a type argument", HEAD + PAIR + 'tuple Raw\n  n Int\nprintln(Pair[Raw, Int].from_dyn(json.Dyn.DNull))\n', 1, ""),
 ("a Dict field is still an error", HEAD + "tuple Bad[T] deriving dyn\n  d Dict[String, T]\n", 2, "no `Dyn` form"),
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
        ok = ((r.returncode != 0) if rc_want else r.returncode == 0) and word in o
        print(("ok    " if ok else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if ok else f"  -> rc={r.returncode} {o.strip()[:240]}"))
        if not ok: fails.append(name)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
