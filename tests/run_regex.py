"""regex: the linear-time engine and its pattern functions (moxie/std/regex.mxi), in both dialects.  Run: python3 tests/run_regex.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(src, gc=False):
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = [sys.executable, "-m", "moxie"] + (["--gc"] if gc else []) + ["run", f.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
    os.unlink(f.name)
    return r.returncode, r.stdout + r.stderr
HEAD = 'import regex(Matches, Finds, CInt, CFloat, CBool, CText, CNone, must, compile, find, full, is_match, find_all, replace_all, split)\n'
def show(src, text):
    return HEAD + f'println(find(must("{src}"), "{text}").map((m) -> m.text))\n'
CASES = [
 ("first match", show("a(b+)c", "xxabbbcyy"), 'Some("abbbc")'),
 ("alternation takes the first branch", show("a|ab", "ab"), 'Some("a")'),
 ("full match backs off to the branch that reaches the end", HEAD + 'println(full(must("a|ab"), "ab").map((m) -> m.text))\n', 'Some("ab")'),
 ("full match fails on extra text", HEAD + 'println(full(must("\\\\d+"), "42 x").map((m) -> m.text))\n', "None"),
 ("greedy", show("a.*b", "aXbYb"), 'Some("aXbYb")'),
 ("lazy", show("a.*?b", "aXbYb"), 'Some("aXb")'),
 ("class and count", show("[a-c]+\\\\d{2,3}", "zzabc1234"), 'Some("abc123")'),
 ("negated class", show("[^a-c]+", "abxyc"), 'Some("xy")'),
 ("word boundary", show("\\\\bfoo\\\\b", "a foo b"), 'Some("foo")'),
 ("no match inside a word", show("\\\\bfoo\\\\b", "afoob"), "None"),
 ("anchors", show("^ab$", "ab"), 'Some("ab")'),
 ("anchor misses", show("^b", "ab"), "None"),
 ("escaped metacharacters", show("a\\\\.b\\\\+", "xa.b+"), 'Some("a.b+")'),
 ("non-capturing group", HEAD + 'println(find(must("(?:ab)+(c)"), "ababc").map((m) -> m.groups))\n', 'Some(List(Cap.CText("c")))'),
 ("unset group is CNone", HEAD + 'println(find(must("a|(b)"), "a").map((m) -> m.groups))\n', "Some(List(Cap.CNone))"),
 ("typed groups arrive read", HEAD + 'println(find(must("(?<y:Int>\\\\d{4})-(?<r:Float>\\\\d+\\\\.\\\\d)-(?<ok:Bool>true|false)"), "2026-3.5-true").map((m) -> m.groups))\n',
  "Some(List(Cap.CInt(2026), Cap.CFloat(3.5), Cap.CBool(true)))"),
 ("named lookup", HEAD + 'when find(must("(?<y:Int>\\\\d+)-(?<tag>\\\\w+)"), "7-ab")\n  Some(m) -> println(m.named("tag"))\n  None -> println("no match")\n', 'Some(Cap.CText("ab"))'),
 ("named lookup of a missing name", HEAD + 'when find(must("(?<y:Int>\\\\d+)"), "7")\n  Some(m) -> println(m.named("zz"))\n  None -> println("no match")\n', "None"),
 ("a typed group whose text does not read makes the match fail", HEAD + 'println(find(must("(?<n:Int>[a-z]+)"), "abc").map((m) -> m.text))\n', "None"),
 ("find_all", HEAD + 'println(find_all(must("\\\\d+"), "1 and 22 and 333").map((m) -> m.text) |> collect())\n', 'List("1", "22", "333")'),
 ("find_all with empty matches", HEAD + 'println(find_all(must("x*"), "ab").map((m) -> m.start) |> collect())\n', "List(0, 1, 2)"),
 ("replace_all", HEAD + 'println(replace_all(must("\\\\d+"), "a1b22", (m) -> "<${m.text}>"))\n', 'a<1>b<22>'),
 ("split", HEAD + 'println(split(must(",\\\\s*"), "a, b,c"))\n', 'List("a", "b", "c")'),
 ("is_match", HEAD + 'println(is_match(must("o+"), "foo"))\nprintln(is_match(must("z"), "foo"))\n', "true\nfalse"),
 ("characters, not bytes", show("é+", "caféé!"), 'Some("éé")'),
 ("a repeated group that can match empty ends on an empty repetition", HEAD + 'println(find(must("(a*)+"), "aaa").map((m) -> m.groups))\n', 'Some(List(Cap.CText("")))'),
 ("repeat of a group", HEAD + 'println(find(must("(ab){2}"), "ababab").map((m) -> m.text))\n', 'Some("abab")'),
 ("optional and counted forms", show("colou?r{1,2}", "colorr"), 'Some("colorr")'),
 ("a pattern that backtracking engines hang on", HEAD + 'text = (0..<300) |> map((_) -> "a") |> join("")\nprintln(is_match(must("(a+)+b"), text))\nprintln(is_match(must("(a+)+b"), text + "b"))\n', "false\ntrue"),
 ("Matches and Finds in a when", HEAD + '''date = must("(?<y:Int>\\\\d{4})-(?<m:Int>\\\\d\\\\d)-(?<d:Int>\\\\d\\\\d)")
mail = must("(\\\\w+)@(\\\\w+)\\\\.com")
fn describe(line String) String
  when line
    Matches(^date, List(CInt(y), CInt(m), CInt(d))) -> "date ${y}/${m}/${d}"
    Finds(^mail, List(CText(user), CText(host))) -> "mail ${user} at ${host}"
    _ -> "other"
println(describe("2026-11-20"))
println(describe("write bob@example.com now"))
println(describe("2026-11-20 and more"))
''', "date 2026/11/20\nmail bob at example\nother"),
 ("a pattern fn in a larger pattern", HEAD + '''date = must("(\\\\d+)-(\\\\d+)")
fn first(x Option[String]) Int
  when x
    Some(Matches(^date, List(CText(a), CText(b)))) -> len(a) + len(b)
    _ -> 0
println(first(Some("12-345")))
println(first(Some("nope")))
println(first(None))
''', "5\n0\n0"),
 ("literal regex: typed names", 'import regex(Matches, Finds)\nfn d(s String) String\n  when s\n    Matches("(?<y:Int>\\\\d{4})-(?<m:Int>\\\\d\\\\d)-(?<d:Int>\\\\d\\\\d)", (y, m, d)) -> "date ${y + 1}/${m}/${d}"\n    _ -> "other"\nprintln(d("2026-11-20"))\nprintln(d("nope"))\n', "date 2027/11/20\nother"),
 ("literal regex: one group is the value itself", 'import regex(Matches)\nfn y(s String) Int\n  when s\n    Matches("v(?<n:Int>\\\\d+)", n) -> n * 2\n    _ -> 0\nprintln(y("v21"))\n', "42"),
 ("literal regex: Float and Bool groups", 'import regex(Matches)\nfn f(s String) String\n  when s\n    Matches("(?<x:Float>\\\\d+\\\\.\\\\d+) (?<ok:Bool>true|false)", (x, ok)) -> "${x * 2.0} ${not ok}"\n    _ -> "-"\nprintln(f("1.5 true"))\n', "3.0 false"),
 ("literal regex: a group that may be absent is an Option", 'import regex(Matches)\nfn o(s String) String\n  when s\n    Matches("a(?<n:Int>\\\\d+)?", n) -> "${n}"\n    _ -> "no"\nprintln(o("a12"))\nprintln(o("a"))\n', "Some(12)\nNone"),
 ("literal regex: no groups just tests", 'import regex(Matches, Finds)\nfn t(s String) String\n  when s\n    Matches("ab+") -> "yes"\n    _ -> "no"\nprintln(t("abbb"))\n', "yes"),
 ("literal regex: Finds searches", 'import regex(Finds)\nfn t(s String) String\n  when s\n    Finds("(\\\\w+)@(\\\\w+)", (u, h)) -> "${u} at ${h}"\n    _ -> "no"\nprintln(t("mail bob@site now"))\n', "bob at site"),
 ("literal regex: wrong type is a compile error", 'import regex(Matches)\nfn b(s String) Int\n  when s\n    Matches("(?<y:Int>\\\\d+)", y) -> y.len()\n    _ -> 0\n', "`len` can't take (Int)"),
 ("literal regex: wrong group count is a compile error", 'import regex(Matches)\nfn b(s String) Int\n  when s\n    Matches("(\\\\d+)-(\\\\d+)", (a, b, c)) -> 1\n    _ -> 0\n', "has 2 groups, but the pattern after it has 3 names"),
 ("literal regex: no groups, names written (compile error)", 'import regex(Matches)\nfn b(s String) Int\n  when s\n    Matches("abc", x) -> 1\n    _ -> 0\n', "has no groups"),
 ("literal regex: bad regex is a compile error", 'import regex(Matches)\nfn b(s String) Int\n  when s\n    Matches("(ab", x) -> 1\n    _ -> 0\n', "missing `)`"),
 ("literal regex: optional group is not an Int (compile error)", 'import regex(Matches)\nfn f(s String) Int\n  when s\n    Matches("a(?<n:Int>\\\\d)?", n) -> n + 1\n    _ -> 0\n', "cannot apply `+` to `Option[Int]`"),
 ("literal regex: one group, two names (compile error)", 'import regex(Finds)\nfn f(s String) Int\n  when s\n    Finds("(\\\\d+)", (a, b)) -> 1\n    _ -> 0\n', "has 1 group, but the pattern after it has 2 names"),
 ("literal regex: a String literal against an Int group (compile error)", 'import regex(Matches)\nfn f(s String) Int\n  when s\n    Matches("(?<n:Int>\\\\d+)", "x") -> 1\n    _ -> 0\n', "it can never match"),
 ("literal regex: an Int literal against an Int group", 'import regex(Matches)\nfn f(s String) String\n  when s\n    Matches("(?<n:Int>\\\\d+)", 7) -> "seven"\n    _ -> "other"\nprintln(f("7"))\nprintln(f("8"))\n', "seven\nother"),
 ("error: a group name used twice", 'import regex\nprintln(regex.compile("(?<a>x)(?<a>y)"))\n', "used twice"),
 ("error: missing paren", 'import regex\nprintln(regex.compile("(a"))\n', "missing `)`"),
 ("error: unmatched close paren", 'import regex\nprintln(regex.compile("a)"))\n', "unmatched `)`"),
 ("error: nothing to repeat", 'import regex\nprintln(regex.compile("*a"))\n', "nothing to repeat"),
 ("error: back-reference", 'import regex\nprintln(regex.compile("(a)\\\\1"))\n', "back-references are not supported"),
 ("error: look-behind", 'import regex\nprintln(regex.compile("(?<=a)b"))\n', "look-behind is not supported"),
 ("error: look-ahead", 'import regex\nprintln(regex.compile("a(?=b)"))\n', "look-around and flags are not supported"),
 ("error: backwards range", 'import regex\nprintln(regex.compile("[z-a]"))\n', "is backwards"),
 ("error: bad group type", 'import regex\nprintln(regex.compile("(?<n:Char>a)"))\n', "a group type is Int, Float, Bool or String"),
 ("error: unknown escape", 'import regex\nprintln(regex.compile("\\\\q"))\n', "unknown escape"),
 ("error: repeat top below bottom", 'import regex\nprintln(regex.compile("a{3,1}"))\n', "below its bottom"),
 ("error: repeat too large", 'import regex\nprintln(regex.compile("a{300}"))\n', "at most 255"),
 ("error: missing bracket", 'import regex\nprintln(regex.compile("[ab"))\n', "missing `]`"),
 ("error: trailing backslash", 'import regex\nprintln(regex.compile("ab\\\\"))\n', "ends with"),
 ("must stops the program on a bad pattern", 'import regex\nprintln(regex.must("(a"))\n', "missing `)`"),
]
fails = []
for name, src, want in CASES:
    for gc in (False, True):
        rc, out = run(src, gc)
        good = want in out and (rc == 0 or name.startswith("must") or "compile error" in name)
        print(("ok    " if good else "FAIL  ") + name + (" (gc)" if gc else "") + ("" if good else f"  -> rc={rc} {out.strip()[:300]!r}"))
        if not good:
            fails.append(name)
print(f"{len(CASES) * 2 - len(fails)} of {len(CASES) * 2} passed")
sys.exit(1 if fails else 0)
