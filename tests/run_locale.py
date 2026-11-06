"""Locale tests: separators, date names, date order, 24-hour time.  Run: python3 tests/run_locale.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = 't = DateTime(2026, 11, 5, 15, 4, 9)\n'
CASES = [
 ("no Locale in scope: English names", T + 'println(format_time(t, "%A %B %p"))\n', 0, "Thursday November PM"),
 ("%x and %X default to US order and 12-hour", T + 'println(format_time(t, "%x %X"))\n', 0, "11/05/2026 03:04:09 PM"),
 ("using a Locale changes the names", T + 'using l = Locale.de_de\nprintln(format_time(t, "%A, %d. %B %Y"))\n', 0, "Donnerstag, 05. November 2026"),
 ("using a Locale changes %x and %X", T + 'using l = Locale.de_de\nprintln(format_time(t, "%x %X"))\n', 0, "05.11.2026 15:04:09"),
 ("numbers use the same Locale", 'using l = Locale.de_de\nprintln("${1234567.891:.2n}")\n', 0, "1.234.567,89"),
 ("an explicit Locale wins", T + 'using l = Locale.de_de\nprintln(format_time(t, "%x", Locale.fr_fr))\n', 0, "05/11/2026"),
 ("short names", T + 'println(format_time(t, "%a %b", Locale.es_es))\n', 0, "jue nov"),
 ("en_gb is day first, 24-hour", T + 'println(format_time(t, "%x %X", Locale.en_gb))\n', 0, "05/11/2026 15:04:09"),
 ("parse_time reads a locale's names", 'using l = Locale.de_de\nd = parse_time("Donnerstag, 5. März 2026", "%A, %d. %B %Y")?\nprintln(iso(d))\n', 0, "2026-03-05T00:00:00"),
 ("parse_time rejects another language's names", 'using l = Locale.de_de\nprintln(is_ok(parse_time("Thursday 5 March 2026", "%A %d %B %Y")))\n', 0, "false"),
 ("a Locale is a tuple with fields", 'println(Locale.fr_fr.group == " ")\nprintln(Locale.de_de.date_sep)\n', 0, "true\n."),
]
fails = []
for name, src, rc_want, out_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    r = subprocess.run([sys.executable, "-m", "moxie", "run", f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    rc, o = r.returncode, r.stdout.decode() + r.stderr.decode()
    ok = rc == rc_want and out_w in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:300]!r}"))
    if not ok:
        fails.append(name)
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
