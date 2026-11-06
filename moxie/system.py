"""System basics (Spec 19e): the clock, random numbers, exit codes, signals, and facts about the host.

Everything here reaches outside the program, so the effects pass counts a call as "uses the system"
(a `pure fn`, a contract, and a `forall` body may not make one). Only the calls that can leak or
change something sit behind a permission: `lookup_host` (net.connect) and `make_temp_file` and
`make_temp_dir` (fs.write)."""
import os
import re as _re
import random as _random
import socket
import sys
import tempfile
import time
import signal as _signal
from .values import *   # noqa
from .core import ProgramExit, type_name
from . import sched as S_
from .prelude import bi, denied, io_error, StdStream, IoV, GenR, _fs_guard

_T0 = time.monotonic_ns()


# ---------------------------------------------------------------- clock
# The scheduler's clock is virtual: `sleep` moves it forward without waiting. The clocks here add
# that skew to the real one, so a program that sleeps 100ms always sees at least 100ms pass.
@bi("monotonic")
def b_monotonic(I, a, kw, ta):
    return Dur(time.monotonic_ns() - _T0 + int(I.sched.now))


@bi("now")
def b_now(I, a, kw, ta):
    return Dur(time.time_ns() + int(I.sched.now))


# ---------------------------------------------------------------- random
def _rng(I):
    r = I.__dict__.get("sys_rng")
    if r is None:
        r = I.__dict__["sys_rng"] = _random.Random()
    return r


@bi("random")
def b_random(I, a, kw, ta):
    return _rng(I).random()


@bi("random_int")
def b_random_int(I, a, kw, ta):
    lo, hi = int(a[0]), int(a[1])
    if lo > hi:
        raise Abort(f"random_int: the low end {lo} is above the high end {hi}")
    return _rng(I).randint(lo, hi)


@bi("random_bytes")
def b_random_bytes(I, a, kw, ta):
    n = int(a[0])
    if n < 0:
        raise Abort("random_bytes: the count is negative")
    cls = INT_CLASSES.get("Byte")
    return ArrayV([cls(b) if cls else b for b in os.urandom(n)])


@bi("seeded")
def b_seeded(I, a, kw, ta):
    return GenR(_random.Random(int(a[0])), 8, 0)


# ---------------------------------------------------------------- exit and signals
@bi("exit")
def b_exit(I, a, kw, ta):
    code = int(a[0])
    if not 0 <= code <= 255:
        raise Abort(f"exit: the code {code} is outside 0 to 255")
    raise ProgramExit(code, None)


SIGNALS = (("SIGINT", "interrupt"), ("SIGTERM", "terminate"), ("SIGHUP", "hangup"))


@bi("signals")
def b_signals(I, a, kw, ta):
    ch = S_.Chan(8)
    ch.pools = I.pools
    I.pools.acquire("Chan")
    r, w = S_.ChanR(ch), S_.ChanW(ch)
    sink = S_.EventSink(w, "signals")
    I.__dict__.setdefault("event_sinks", []).append(sink)
    I.sched.listeners += 1
    I.sched.sig_listeners += 1      # an idle program waits for a signal instead of reporting a deadlock
    for sig, name in SIGNALS:
        num = getattr(_signal, sig, None)
        if num is None:
            continue
        try:
            _signal.signal(num, lambda s, f, k=Kw(name): I.sched.post_event(sink, k))
        except ValueError:
            raise Abort("signals must be called from the main thread")
    return r


# ---------------------------------------------------------------- the host
@bi("cwd")
def b_cwd(I, a, kw, ta):
    return os.getcwd()


@bi("home_dir")
def b_home_dir(I, a, kw, ta):
    h = os.path.expanduser("~")
    if h == "~" or not os.path.isdir(h):
        return err_reserved("MISSING", "no home directory")
    return Ok(h)


@bi("temp_dir")
def b_temp_dir(I, a, kw, ta):
    return tempfile.gettempdir()


@bi("hostname")
def b_hostname(I, a, kw, ta):
    return socket.gethostname()


@bi("os_name")
def b_os_name(I, a, kw, ta):
    p = sys.platform
    if getattr(I, "platform", None) == "browser" or p == "emscripten":
        return "browser"
    return "linux" if p.startswith("linux") else "macos" if p == "darwin" else "windows" if p == "win32" else p


@bi("is_terminal")
def b_is_terminal(I, a, kw, ta):
    x = a[0]
    if isinstance(x, StdStream):
        try:
            return os.isatty({"stdin": 0, "stdout": 1, "stderr": 2}[x.kind])
        except OSError:
            return False
    if isinstance(x, IoV):
        return False
    raise Abort(f"is_terminal needs stdin, stdout, stderr, or an Io, not {type_name(x)}")


@bi("terminal_size")
def b_terminal_size(I, a, kw, ta):
    size = getattr(os, "get_terminal_size", None)         # Pyodide has none
    for fd in (1, 2, 0) if size else ():
        try:
            sz = size(fd)
            return Ok(TupleV([sz.columns, sz.lines], ["cols", "rows"]))
        except OSError:
            continue
    return err_reserved("MISSING", "not a terminal")


@bi("lookup_host", "first", True)
def b_lookup_host(I, a, kw, ta):
    host = a[0]
    if not I.perms.connect_ok(host, "*"):
        return denied(host, "net.connect")

    def work():
        try:
            seen = []
            for fam, _t, _p, _c, sa in socket.getaddrinfo(host, None):
                if sa[0] not in seen:
                    seen.append(sa[0])
            return seen
        except OSError as e:
            return e
    r = yield from S_.park_thread(I, work)
    if isinstance(r, OSError):
        return err_reserved("NOT_FOUND", f"{host}: name not found")
    return Ok(ListV(r, max(len(r), 1)))


def _temp(I, kind, prefix):
    d = _fs_guard(I, "fs.write", tempfile.gettempdir())
    if d is not None:
        return d
    try:
        if kind == "file":
            fd, p = tempfile.mkstemp(prefix=prefix)
            os.close(fd)
        else:
            p = tempfile.mkdtemp(prefix=prefix)
    except OSError as e:
        return io_error(e, tempfile.gettempdir())
    return Ok(p)


@bi("make_temp_file")
def b_make_temp_file(I, a, kw, ta):
    return _temp(I, "file", a[0] if a else "moxie-")


@bi("make_temp_dir")
def b_make_temp_dir(I, a, kw, ta):
    return _temp(I, "dir", a[0] if a else "moxie-")


# ---------------------------------------------------------------- durations out to numbers
def _dur(a, who):
    if not isinstance(a[0], Dur):
        raise Abort(f"{who} needs a Duration, not {type_name(a[0])}")
    return a[0].ns


@bi("nanos")
def b_nanos(I, a, kw, ta):
    return _dur(a, "nanos")


@bi("millis")
def b_millis(I, a, kw, ta):
    return _dur(a, "millis") // 1_000_000


@bi("seconds")
def b_seconds(I, a, kw, ta):
    return _dur(a, "seconds") / 1e9


# ---------------------------------------------------------------- other programs (Spec 19e)
import subprocess


class ChildV:
    """A program started by `spawn`: a move-only resource. Closing it closes its pipes and ends the program."""
    __slots__ = ("proc", "closed", "I", "ios")
    tname_ = "Child"

    def __init__(self, proc, I):
        self.proc, self.closed, self.I, self.ios = proc, False, I, {}
        I.__dict__.setdefault("live_children", []).append(self)

    def drop(self, sched=None):
        if self.closed:
            return
        self.closed = True
        for io in self.ios.values():
            io.drop()
        try:
            if self.proc.poll() is None:
                self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            pass


def _prep(I, program, args, kw):
    """(argv, env, cwd) or an Err: the permission checks and the environment the program gets."""
    if not I.perms.process_ok(program):
        return None, denied(program, "process")
    cwd = kw.get("cwd")
    if cwd is not None and not I.perms.path_ok("fs.read", cwd):
        return None, denied(cwd, "fs.read")
    e = kw.get("env")
    env = dict(e.d) if e is not None else dict(I.prelude.vars["env"].d)
    return ([str(program)] + [str(x) for x in args.items], env, cwd), None


def _exit_code(rc):
    return 128 - rc if rc < 0 else rc            # killed by signal N reads as 128 + N, as a shell shows it


@bi("run_command", "first", True)
def b_run_command(I, a, kw, ta):
    args = a[1] if len(a) > 1 else ListV([])
    spec, err = _prep(I, a[0], args, kw)
    if err is not None:
        return err
    argv, env, cwd = spec
    data = kw.get("stdin")
    tmo = kw.get("timeout")

    def work():
        try:
            if data is None:
                return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, env=env, cwd=cwd,
                                      timeout=None if tmo is None else tmo.ns / 1e9)
            return subprocess.run(argv, input=data.encode("utf-8"), capture_output=True, env=env, cwd=cwd,
                                  timeout=None if tmo is None else tmo.ns / 1e9)
        except subprocess.TimeoutExpired:
            return "timeout"
        except OSError as e:
            return e
    r = yield from S_.park_thread(I, work)
    if r == "timeout":
        return err_reserved("TIMED_OUT", f"{a[0]}: timed out")
    if isinstance(r, OSError):
        return io_error(r, str(a[0]))
    try:
        out, errt = r.stdout.decode("utf-8"), r.stderr.decode("utf-8")
    except UnicodeDecodeError:
        return err_reserved("BAD_ENCODING", f"{a[0]}: output is not valid UTF-8")
    return Ok(TupleV([_exit_code(r.returncode), out, errt], ["code", "stdout", "stderr"], "Output"))


@bi("spawn")
def b_spawn(I, a, kw, ta):
    args = a[1] if len(a) > 1 else ListV([])
    spec, err = _prep(I, a[0], args, kw)
    if err is not None:
        return err
    argv, env, cwd = spec
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=env, cwd=cwd)
    except OSError as e:
        return io_error(e, str(a[0]))
    return Ok(ChildV(proc, I))


def _child(a, who):
    c = a[0]
    if not isinstance(c, ChildV) or c.closed:
        raise Abort(f"{who} needs an open Child")
    return c


@bi("child_stdout")
def b_child_stdout(I, a, kw, ta):
    c = _child(a, "child_stdout")
    if "out" not in c.ios:
        c.ios["out"] = IoV(I, "socket", c.proc.stdout)
    return c.ios["out"]


@bi("child_stdin")
def b_child_stdin(I, a, kw, ta):
    c = _child(a, "child_stdin")
    if "in" not in c.ios:
        c.ios["in"] = IoV(I, "socket", c.proc.stdin)
    return c.ios["in"]


@bi("wait_child", "first", True)
def b_wait_child(I, a, kw, ta):
    c = _child(a, "wait_child")
    tmo = kw.get("timeout")

    def work():
        try:
            return c.proc.wait(timeout=None if tmo is None else tmo.ns / 1e9)
        except subprocess.TimeoutExpired:
            return None
    r = yield from S_.park_thread(I, work)
    if r is None:
        return err_reserved("TIMED_OUT", "wait_child: timed out")
    return Ok(_exit_code(r))


@bi("kill_child")
def b_kill_child(I, a, kw, ta):
    c = _child(a, "kill_child")
    if c.proc.poll() is None:
        c.proc.kill()
    return UNIT


# ---------------------------------------------------------------- dates and times (Spec 19e)
import datetime as _dtm

_EPOCH = _dtm.datetime(1970, 1, 1, tzinfo=_dtm.timezone.utc)
_DT_FIELDS = ["year", "month", "day", "hour", "minute", "second", "nano"]
_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"]
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _civil(d, nano):
    return TupleV([d.year, d.month, d.day, d.hour, d.minute, d.second, nano], list(_DT_FIELDS), "DateTime")


def _instant_arg(x, who):
    if not isinstance(x, Dur):
        raise Abort(f"{who} needs a Duration since the Unix epoch, not {type_name(x)}")
    return x.ns


def _from_ns(ns, tz, who):
    secs, nano = divmod(int(ns), 1_000_000_000)
    try:
        return _civil((_EPOCH + _dtm.timedelta(seconds=secs)).astimezone(tz), nano)
    except (OverflowError, ValueError, OSError):
        raise Abort(f"{who}: the time is outside the years 1 to 9999")


_ZONE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zoneinfo")


def _zone(name):
    """The zone called `name`: the host's time zone database first, then the copy that ships with moxie
    (a browser or a Windows machine has none)."""
    import zoneinfo
    try:
        return zoneinfo.ZoneInfo(name), None
    except (zoneinfo.ZoneInfoNotFoundError, ValueError, OSError):
        pass
    if _re.fullmatch(r"[A-Za-z0-9_+\-]+(/[A-Za-z0-9_+\-]+)*", name):
        path = os.path.join(_ZONE_DIR, *name.split("/"))
        try:
            with open(path, "rb") as f:
                return zoneinfo.ZoneInfo.from_file(f, key=name), None
        except (OSError, ValueError):
            pass
    return None, err_reserved("NOT_FOUND", f"{name}: unknown time zone")


@bi("to_utc")
def b_to_utc(I, a, kw, ta):
    return _from_ns(_instant_arg(a[0], "to_utc"), _dtm.timezone.utc, "to_utc")


@bi("to_local")
def b_to_local(I, a, kw, ta):
    return _from_ns(_instant_arg(a[0], "to_local"), None, "to_local")


@bi("to_zone")
def b_to_zone(I, a, kw, ta):
    ns = _instant_arg(a[0], "to_zone")
    tz, err = _zone(a[1])
    if err is not None:
        return err
    return Ok(_from_ns(ns, tz, "to_zone"))


def _check_dt(v, who):
    if not isinstance(v, TupleV) or v.tname != "DateTime":
        raise Abort(f"{who} needs a DateTime, not {type_name(v)}")
    return [int(x) for x in v.vals]


def _valid(vals):
    """The datetime for the fields, or a message saying what is wrong with them."""
    y, mo, d, h, mi, s, ns = vals
    if not 1 <= y <= 9999:
        return None, f"the year {y} is outside 1 to 9999"
    if not 1 <= mo <= 12:
        return None, f"the month {mo} is outside 1 to 12"
    try:
        _dtm.date(y, mo, d)
    except ValueError:
        return None, f"{_MONTHS[mo - 1]} {y} has no day {d}"
    if not 0 <= h <= 23 or not 0 <= mi <= 59 or not 0 <= s <= 59:
        return None, f"the time {h}:{mi}:{s} is not a time of day"
    if not 0 <= ns <= 999_999_999:
        return None, f"the nanoseconds {ns} are outside 0 to 999999999"
    return _dtm.datetime(y, mo, d, h, mi, s), None


@bi("to_instant")
def b_to_instant(I, a, kw, ta):
    vals = _check_dt(a[0], "to_instant")
    zone = a[1] if len(a) > 1 else "UTC"
    base, why = _valid(vals)
    if why:
        return err_reserved("OUT_OF_RANGE", why)
    tz, err = (_dtm.timezone.utc, None) if zone == "UTC" else _zone(zone)
    if err is not None:
        return err
    secs = int((base.replace(tzinfo=tz) - _EPOCH).total_seconds())
    return Ok(Dur(secs * 1_000_000_000 + vals[6]))


def _need_valid(vals, who):
    base, why = _valid(vals)
    if why:
        raise Abort(f"{who}: {why}")
    return base


def _loc(I, explicit=None):
    """The locale in force for a date call: an explicit Locale argument, else the one `using` puts in scope, else English."""
    from .values import TupleV
    if isinstance(explicit, TupleV):
        d = {n: x for n, x in zip(explicit.names, explicit.vals)}
    else:
        d = I.find_locale(getattr(I, "call_env", None)) if getattr(I, "call_env", None) is not None else None
    if not d or "months" not in d:
        return None
    return {k: ([x for x in v.items] if hasattr(v, "items") and not isinstance(v, dict) else v) for k, v in d.items()}


def _names(loc):
    if loc is None:
        return _DAYS, [d[:3] for d in _DAYS], _MONTHS, [m[:3] for m in _MONTHS], ["AM", "PM"], "mdy", "/", False
    return (loc["days"], loc["short_days"], loc["months"], loc["short_months"], loc["am_pm"], loc["date_order"],
            loc["date_sep"], loc["hour24"])


def _x_pattern(loc, which):
    days, sd, months, sm, ap, order, sep, h24 = _names(loc)
    if which == "x":
        parts = {"m": "%m", "d": "%d", "y": "%Y"}
        return sep.join(parts[c] for c in order)
    return "%H:%M:%S" if h24 else "%I:%M:%S %p"


def _format(vals, pat, who, loc=None):
    base = _need_valid(vals, who)
    days, sdays, months, smonths, ampm, *_ = _names(loc)
    if "%x" in pat or "%X" in pat:
        pat = pat.replace("%x", _x_pattern(loc, "x")).replace("%X", _x_pattern(loc, "X"))
    y, mo, d, h, mi, s, ns = vals
    out, i = [], 0
    while i < len(pat):
        c = pat[i]
        if c != "%":
            out.append(c)
            i += 1
            continue
        i += 1
        if i >= len(pat):
            raise Abort(f"{who}: the pattern ends with a lone %")
        k = pat[i]
        i += 1
        wd = base.weekday()
        out.append({
            "Y": f"{y:04d}", "m": f"{mo:02d}", "d": f"{d:02d}", "H": f"{h:02d}", "M": f"{mi:02d}", "S": f"{s:02d}",
            "f": f"{ns:09d}", "y": f"{y % 100:02d}", "e": f"{d:2d}", "j": f"{base.timetuple().tm_yday:03d}",
            "a": sdays[wd], "A": days[wd], "b": smonths[mo - 1], "B": months[mo - 1],
            "p": ampm[0] if h < 12 else ampm[1], "I": f"{(h % 12) or 12:02d}", "%": "%",
        }.get(k) if k in "YmdHMSfyejaAbBpI%" else _bad_code(k, who))
    return "".join(out)


def _bad_code(k, who):
    raise Abort(f"{who}: unknown pattern code %{k}")


@bi("format_time")
def b_format_time(I, a, kw, ta):
    return _format(_check_dt(a[0], "format_time"), a[1], "format_time", _loc(I, a[2] if len(a) > 2 else None))


@bi("iso")
def b_iso(I, a, kw, ta):
    vals = _check_dt(a[0], "iso")
    text = _format(vals, "%Y-%m-%dT%H:%M:%S", "iso")
    if vals[6]:
        text += "." + f"{vals[6]:09d}".rstrip("0")
    return text


_PARSE = {"Y": r"(\d{4})", "m": r"(\d{1,2})", "d": r"(\d{1,2})", "H": r"(\d{1,2})", "M": r"(\d{1,2})",
          "S": r"(\d{1,2})", "f": r"(\d{1,9})", "y": r"(\d{2})", "e": r"\s?(\d{1,2})", "j": r"(\d{1,3})",
          "I": r"(\d{1,2})", "p": r"([AaPp][Mm])",
          "a": r"(" + "|".join(d[:3] for d in _DAYS) + r")", "A": r"(" + "|".join(_DAYS) + r")",
          "b": r"(" + "|".join(m[:3] for m in _MONTHS) + r")", "B": r"(" + "|".join(_MONTHS) + r")"}


def _parse(text, pat, who, loc=None):
    days, sdays, months, smonths, ampm, *_ = _names(loc)
    if "%x" in pat or "%X" in pat:
        pat = pat.replace("%x", _x_pattern(loc, "x")).replace("%X", _x_pattern(loc, "X"))
    table = dict(_PARSE)
    esc = lambda xs: "|".join(_re.escape(x) for x in xs)
    table.update({"a": "(" + esc(sdays) + ")", "A": "(" + esc(days) + ")", "b": "(" + esc(smonths) + ")",
                  "B": "(" + esc(months) + ")", "p": "(" + esc(ampm) + ")"})
    rx, codes, i = [], [], 0
    while i < len(pat):
        c = pat[i]
        if c != "%":
            rx.append(_re.escape(c))
            i += 1
            continue
        i += 1
        if i >= len(pat):
            raise Abort(f"{who}: the pattern ends with a lone %")
        k = pat[i]
        i += 1
        if k == "%":
            rx.append("%")
        elif k in table:
            rx.append(table[k])
            codes.append(k)
        else:
            raise Abort(f"{who}: unknown pattern code %{k}")
    m = _re.fullmatch("".join(rx), text, _re.I)
    if m is None:
        return err_reserved("MISSING", f"{who}: the text does not match {pat}")
    y, mo, d, h, mi, s, ns, pm, yday = None, None, None, 0, 0, 0, 0, None, None
    for k, g in zip(codes, m.groups()):
        if k == "Y":
            y = int(g)
        elif k == "y":
            y = 1900 + int(g) if int(g) >= 69 else 2000 + int(g)
        elif k == "m":
            mo = int(g)
        elif k == "b":
            mo = [x.lower() for x in smonths].index(g.lower()) + 1
        elif k == "B":
            mo = [x.lower() for x in months].index(g.lower()) + 1
        elif k in "de":
            d = int(g)
        elif k == "j":
            yday = int(g)
        elif k in "HI":
            h = int(g)
        elif k == "M":
            mi = int(g)
        elif k == "S":
            s = int(g)
        elif k == "f":
            ns = int(g.ljust(9, "0"))
        elif k == "p":
            pm = g.lower() == ampm[1].lower()
    if pm is not None:
        if not 1 <= h <= 12:
            return err_reserved("OUT_OF_RANGE", f"{who}: the hour {h} is not 1 to 12")
        h = (h % 12) + (12 if pm else 0)
    if y is None:
        return err_reserved("MISSING", f"{who}: the pattern has no year (%Y or %y)")
    if yday is not None:
        try:
            dd = _dtm.date(y, 1, 1) + _dtm.timedelta(days=yday - 1)
        except (ValueError, OverflowError):
            return err_reserved("OUT_OF_RANGE", f"{who}: day {yday} of {y} does not exist")
        if dd.year != y:
            return err_reserved("OUT_OF_RANGE", f"{who}: day {yday} is not in {y}")
        mo, d = dd.month, dd.day
    mo = 1 if mo is None else mo
    d = 1 if d is None else d
    base, why = _valid([y, mo, d, h, mi, s, ns])
    if why:
        return err_reserved("OUT_OF_RANGE", f"{who}: {why}")
    return Ok(_civil(base, ns))


@bi("parse_time")
def b_parse_time(I, a, kw, ta):
    return _parse(a[0], a[1], "parse_time", _loc(I, a[2] if len(a) > 2 else None))


@bi("parse_iso")
def b_parse_iso(I, a, kw, ta):
    text = a[0].strip()
    if _re.search(r"[+-]\d\d(:?\d\d)?$", text) and "T" in text.upper() and not _re.fullmatch(r"\d{4}-\d\d-\d\d", text):
        if _re.search(r"[T ]\d\d:\d\d(:\d\d(\.\d+)?)?[+-]\d\d(:?\d\d)?$", text, _re.I):
            return err_reserved("MISSING", "parse_iso: an offset is not part of a DateTime; parse the local time and use to_instant with a zone")
    if text[-1:] in "Zz" and len(text) > 10:
        text = text[:-1]
    for pat in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            r = _parse(text, pat, "parse_iso")
        except Abort:
            continue
        if r.case == "Ok" or r.vals[0].vals[0] != ERR_CODES["MISSING"]:
            return r
    return err_reserved("MISSING", f"parse_iso: {a[0]!r} is not an ISO 8601 date or time")


@bi("weekday")
def b_weekday(I, a, kw, ta):
    return _need_valid(_check_dt(a[0], "weekday"), "weekday").isoweekday()


@bi("day_of_year")
def b_day_of_year(I, a, kw, ta):
    return _need_valid(_check_dt(a[0], "day_of_year"), "day_of_year").timetuple().tm_yday


@bi("days_in_month")
def b_days_in_month(I, a, kw, ta):
    y, m = int(a[0]), int(a[1])
    if not 1 <= y <= 9999 or not 1 <= m <= 12:
        raise Abort("days_in_month needs a year 1 to 9999 and a month 1 to 12")
    import calendar
    return calendar.monthrange(y, m)[1]
