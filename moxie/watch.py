"""File watching: watch(path) returns a channel of FileChange values.  Spec 19d.

The watcher is a polling thread (every POLL seconds) that compares directory listings or file stats, so it works on every
platform without extra libraries.  Changes reach the program through the event queue, like signals, and the channel drops
an event when it is full (with a warning at exit).  The thread ends when the reading end is closed or the program ends.
"""
import os
import threading
import time
from .values import *   # noqa
from . import sched as S_
from .prelude import bi, denied, io_error

POLL = 0.1
CAP = 16


def _scan(path):
    """{path: (mtime_ns, size)} for a file, or for the entries directly inside a directory."""
    out = {}
    try:
        if os.path.isdir(path):
            with os.scandir(path) as it:
                for e in it:
                    try:
                        st = e.stat(follow_symlinks=False)
                        # a subdirectory's own stamp changes with what is inside it: report it only as created or deleted
                        out[os.path.join(path, e.name)] = ("dir",) if e.is_dir(follow_symlinks=False) else (st.st_mtime_ns, st.st_size)
                    except OSError:
                        pass
        else:
            st = os.stat(path)
            out[path] = (st.st_mtime_ns, st.st_size)
    except OSError:
        pass
    return out


def diff(old, new):
    """The changes from one scan to the next, sorted by path: (path, kind)."""
    out = []
    for p in sorted(set(old) | set(new)):
        if p not in old:
            out.append((p, "created"))
        elif p not in new:
            out.append((p, "deleted"))
        elif old[p] != new[p]:
            out.append((p, "modified"))
    return out


@bi("watch")
def b_watch(I, a, kw, ta):
    path = a[0]
    if getattr(I, "platform", None) == "browser":
        return err_reserved("MISSING", "file watching is not available here")
    if not I.perms.path_ok("fs.read", path):
        return denied(path, "fs.read")
    if not os.path.exists(path):
        return err_reserved("NOT_FOUND", f"{path}: no such file or directory")
    ch = S_.Chan(CAP)
    ch.pools = I.pools
    I.pools.acquire("Chan")
    r, w = S_.ChanR(ch), S_.ChanW(ch)
    sink = S_.EventSink(w, "watch " + path)
    I.__dict__.setdefault("event_sinks", []).append(sink)
    I.sched.listeners += 1
    I.sched.sig_listeners += 1        # an idle program waits in real time for a change, and sleepers keep time
    sched, mk = I.sched, I

    def run(prev=_scan(path)):
        while True:
            time.sleep(POLL)
            if ch.rcount <= 0:
                sched.post_event(sink, S_.WATCH_STOP)
                return
            cur = _scan(path)
            for p, kind in diff(prev, cur):
                sched.post_event(sink, TupleV([p, Kw(kind)], ["path", "kind"], "FileChange"))
            prev = cur
    threading.Thread(target=run, daemon=True).start()
    return Ok(r)
