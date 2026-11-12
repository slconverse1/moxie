"""Date and time tests.  Run: python3 tests/run_datetime.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CASES = [
 ("the epoch is 1970", 'println(iso((0s).to_utc()))\n', 0, "1970-01-01T00:00:00"),
 ("a known instant in UTC", 'println(iso((1700000000s).to_utc()))\n', 0, "2023-11-14T22:13:20"),
 ("fields are readable", 'd = (1700000000s).to_utc()\nprintln("${d.year} ${d.month} ${d.day} ${d.hour}")\n', 0, "2023 11 14 22"),
 ("to_instant inverts to_utc", 'd = (1700000000s).to_utc()\nprintln(to_instant(d)? == 1700000000s)\n', 0, "true"),
 ("a Duration of nanoseconds keeps them", 'd = (1500ms).to_utc()\nprintln(d.nano)\nprintln(iso(d))\n', 0, "500000000\n1970-01-01T00:00:01.5"),
 ("a named zone shifts the time", 'd = to_zone(1700000000s, "America/Los_Angeles")?\nprintln(iso(d))\n', 0, "2023-11-14T14:13:20"),
 ("summer time is respected", 'd = to_zone(1690000000s, "America/Los_Angeles")?\nprintln(iso(d))\n', 0, "2023-07-21T21:26:40"),
 ("to_instant honors the zone", 'd = DateTime(2023, 11, 14, 14, 13, 20)\nprintln(to_instant(d, "America/Los_Angeles")? == 1700000000s)\n', 0, "true"),
 ("an unknown zone is NOT_FOUND", 'println(to_zone(0s, "Mars/Base"))\n', 0, "code: 9"),
 ("an impossible date is OUT_OF_RANGE", 'println(to_instant(DateTime(2026, 2, 30)))\n', 0, "code: 6"),
 ("a leap day is fine", 'println(is_ok(to_instant(DateTime(2024, 2, 29))))\nprintln(is_ok(to_instant(DateTime(2025, 2, 29))))\n', 0, "true\nfalse"),
 ("format_time codes", 'd = DateTime(2026, 11, 4, 16, 5, 9)\nprintln(format_time(d, "%Y/%m/%d %H:%M:%S"))\nprintln(format_time(d, "%A, %B %e, %Y"))\nprintln(format_time(d, "%a %b %d %y %j %I:%M %p %%"))\n', 0, "2026/11/04 16:05:09\nWednesday, November  4, 2026\nWed Nov 04 26 308 04:05 PM %"),
 ("an unknown code aborts", 'println(format_time(DateTime(2026, 1, 1), "%Q"))\n', 1, "unknown pattern code %Q"),
 ("format_time rejects an impossible date", 'println(format_time(DateTime(2026, 2, 30), "%d"))\n', 1, "has no day 30"),
 ("parse_time reads what format_time writes", 'd = parse_time("Wed Nov 04 2026 04:05 PM", "%a %b %d %Y %I:%M %p")?\nprintln(iso(d))\n', 0, "2026-11-04T16:05:00"),
 ("parse_time with a day of the year", 'println(iso(parse_time("2024 060", "%Y %j")?))\n', 0, "2024-02-29T00:00:00"),
 ("parse_time with fractional seconds", 'println(parse_time("2026-01-01 00:00:01.25", "%Y-%m-%d %H:%M:%S.%f")?.nano)\n', 0, "250000000"),
 ("parse_time rejects text that does not match", 'println(parse_time("hello", "%Y-%m-%d"))\n', 0, "code: 4"),
 ("parse_time rejects an impossible date", 'println(parse_time("2026-13-01", "%Y-%m-%d"))\n', 0, "code: 6"),
 ("two-digit years pivot at 69", 'println(parse_time("68", "%y")?.year)\nprintln(parse_time("69", "%y")?.year)\n', 0, "2068\n1969"),
 ("parse_iso reads a date", 'println(iso(parse_iso("2026-11-04")?))\n', 0, "2026-11-04T00:00:00"),
 ("parse_iso reads a date and time", 'println(iso(parse_iso("2026-11-04T16:55:30")?))\n', 0, "2026-11-04T16:55:30"),
 ("parse_iso takes a trailing Z", 'println(iso(parse_iso("2026-11-04T16:55:30Z")?))\n', 0, "2026-11-04T16:55:30"),
 ("parse_iso refuses an offset", 'println(parse_iso("2026-11-04T16:55:30+02:00"))\n', 0, "not part of a DateTime"),
 ("parse_iso rejects junk", 'println(parse_iso("next tuesday"))\n', 0, "not an ISO 8601"),
 ("weekday is 1 for Monday", 'println(weekday(DateTime(2026, 11, 2)))\nprintln(weekday(DateTime(2026, 11, 8)))\n', 0, "1\n7"),
 ("day_of_year", 'println(day_of_year(DateTime(2024, 12, 31)))\n', 0, "366"),
 ("days_in_month", 'println(days_in_month(2024, 2))\nprintln(days_in_month(2025, 2))\nprintln(days_in_month(2025, 12))\n', 0, "29\n28\n31"),
 ("date arithmetic goes through instants", 'd = DateTime(2026, 12, 30)\nlater = (to_instant(d)? + 3 * 24h).to_utc()\nprintln(iso(later))\n', 0, "2027-01-02T00:00:00"),
 ("to_local gives a DateTime", 'println(to_local(now()).year >= 2026)\n', 0, "true"),
 ("a Duration is required", 'println(to_utc(5))\n', 2, "`to_utc` can't take (Int); it takes (Duration)"),
 ("to_local is not pure", 'pure fn f() Int = to_local(now()).year\n', 2, "uses the system"),
 ("to_utc is pure", 'pure fn f(t: Duration) Int = to_utc(t).year\nprintln(f(0s))\n', 0, "1970"),
]
fails = []
for name, src, rc_want, out_w in CASES:
    with tempfile.NamedTemporaryFile("w", suffix=".mxi", delete=False) as f:
        f.write(src)
    cmd = "check" if rc_want == 2 else "run"
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, f.name], cwd=ROOT, capture_output=True, timeout=60)
    os.unlink(f.name)
    rc, o = r.returncode, r.stdout.decode() + r.stderr.decode()
    ok = (rc == 1 if rc_want == 2 else rc == rc_want) and out_w in o
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  (rc {rc}) {o[:300]!r}"))
    if not ok:
        fails.append(name)
# a host with no time zone database (a browser, Windows) uses the zones that ship with moxie
code = ("import sys, zoneinfo; sys.path.insert(0, %r); zoneinfo.reset_tzpath(to=[]); "
        "from moxie import system; z, e = system._zone('America/Los_Angeles'); "
        "bad, e2 = system._zone('../etc/passwd'); nope, e3 = system._zone('Mars/Base'); "
        "print(z is not None and e is None and bad is None and nope is None and e3 is not None)") % ROOT
r = subprocess.run([sys.executable, "-c", code], capture_output=True)
ok = r.stdout.decode().strip() == "True"
print(("ok    " if ok else "FAIL  ") + "the bundled zones work without a host database" + ("" if ok else f"  {r.stdout!r} {r.stderr[:200]!r}"))
if not ok:
    fails.append("bundled zones")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)
