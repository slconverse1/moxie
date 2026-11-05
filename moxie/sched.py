"""Cooperative scheduler, channels, timers, futures, atoms, select and run."""
import heapq
import time
import queue
import threading
from collections import deque
from .ast import *   # noqa
from .values import *   # noqa
from .core import *   # noqa
from .calls import END, USING, SLOT, NOPIPE
from .streams import StreamV
from . import heap


class ExtFail:
    """Carries an exception raised on an OS helper thread back to the fiber that was waiting."""
    __slots__ = ("exc",)

    def __init__(self, exc):
        self.exc = exc


def park_thread(I, fn):
    """Run `fn()` on an OS helper thread while the calling fiber parks; the other fibers keep running.
    Use as `r = yield from park_thread(I, fn)`.  `fn` must not touch interpreter state."""
    r = yield ("ext", fn)
    if isinstance(r, ExtFail):
        raise r.exc
    return r


class EventSink:
    """A channel write end that a C-kept callback posts to (Spec 19a, Events[T])."""
    __slots__ = ("w", "dropped", "name")

    def __init__(self, w, name):
        self.w, self.dropped, self.name = w, 0, name


class Fiber:
    __slots__ = ("gen", "id", "name", "state", "sendval", "done", "result", "error", "entry", "owned", "wake")

    def __init__(self, gen, fid, name, entry=False):
        self.gen = gen
        self.id = fid
        self.name = name
        self.state = "ready"
        self.sendval = None
        self.done = False
        self.result = None
        self.error = None
        self.entry = entry
        self.owned = []
        self.wake = 0


class Chan:
    def __init__(self, cap):
        self.cap = cap
        self.buf = deque()
        self.readers = deque()      # (fiber)
        self.writers = deque()      # (fiber, value)
        self.sel = []               # fibers waiting in select
        self.wcount = 1
        self.rcount = 1
        self.pools = None           # set by Chan(...) so the observed report can count it
        self.released = False

    def maybe_release(self):
        if self.pools is not None and not self.released and self.rcount <= 0 and self.wcount <= 0:
            self.released = True
            self.pools.release("Chan")


class ChanR:
    tname_ = "ChanR"

    def __init__(self, chan):
        self.chan = chan
        self.dropped = False

    def ready(self):
        c = self.chan
        return bool(c.buf) or bool(c.writers)

    def is_closed(self):
        c = self.chan
        return c.wcount <= 0 and not c.buf and not c.writers

    def take(self, S):
        c = self.chan
        if c.buf:
            v = c.buf.popleft()
            if c.writers:
                wf, wv = c.writers.popleft()
                c.buf.append(wv)
                S.wake(wf, Ok(UNIT))
            return v
        wf, wv = c.writers.popleft()
        S.wake(wf, Ok(UNIT))
        return wv

    def chan_read(self, I):
        S = I.sched
        c = self.chan
        if self.ready():
            v = self.take(S)
            S.notify_sel(c)
            return Done(Ok(v))
        if c.wcount <= 0:
            return Done(err_reserved("CLOSED", "channel closed"))
        return self._block(I)

    def _block(self, I):
        S = I.sched
        c = self.chan
        f = S.cur
        c.readers.append(f)
        r = yield ("block",)
        return r

    def drop(self, S):
        if self.dropped:
            return
        self.dropped = True
        c = self.chan
        c.rcount -= 1
        c.maybe_release()
        if c.rcount <= 0:
            # writers get CLOSED
            while c.writers:
                wf, wv = c.writers.popleft()
                S.wake(wf, err_reserved("CLOSED", "channel closed"))
            S.notify_sel(c)


class ChanW:
    tname_ = "ChanW"

    def __init__(self, chan):
        self.chan = chan
        self.dropped = False

    def write(self, I, v):
        S = I.sched
        c = self.chan
        if c.rcount <= 0:
            return Done(err_reserved("CLOSED", "channel closed"))
        if c.readers:
            rf = c.readers.popleft()
            S.wake(rf, Ok(v))
            return Done(Ok(UNIT))
        if len(c.buf) < c.cap:
            c.buf.append(v)
            S.notify_sel(c)
            return Done(Ok(UNIT))
        return self._block(I, v)

    def _block(self, I, v):
        S = I.sched
        c = self.chan
        c.writers.append((S.cur, v))
        S.notify_sel(c)
        r = yield ("block",)
        return r

    def drop(self, S):
        if self.dropped:
            return
        self.dropped = True
        c = self.chan
        c.wcount -= 1
        c.maybe_release()
        if c.wcount <= 0:
            while c.readers:
                rf = c.readers.popleft()
                S.wake(rf, err_reserved("CLOSED", "channel closed"))
            S.notify_sel(c)


class TimerV:
    tname_ = "Timer"

    def __init__(self):
        self.due = None
        self.every = None
        self.fired = False
        self.readers = []
        self.sel = []
        self.gen = 0

    def ready(self):
        return self.fired

    def is_closed(self):
        return False

    def take(self, S):
        self.fired = False
        return UNIT

    def chan_read(self, I):
        if self.fired:
            self.fired = False
            return Done(Ok(UNIT))
        return self._block(I)

    def _block(self, I):
        S = I.sched
        self.readers.append(S.cur)
        r = yield ("block",)
        return r


class AtomV:
    tname_ = "Atom"

    def __init__(self, v):
        self.atom_value = v


class FutureState:
    def __init__(self):
        self.state = "Pending"
        self.value = None
        self.waiters = []
        self.pools = None
        self.released = False

    def settle_pool(self):
        if self.pools is not None and not self.released:
            self.released = True
            self.pools.release("Future")


class FutureR:
    tname_ = "FutureR"

    def __init__(self, st):
        self.st = st

    def snapshot(self):
        st = self.st
        if st.state == "Pending":
            return EnumV(FUTURE_T, "Pending", [], None)
        if st.state == "Resolved":
            return EnumV(FUTURE_T, "Resolved", [st.value], ["value"])
        return EnumV(FUTURE_T, "Rejected", [st.value], ["error"])


class FutureW:
    tname_ = "FutureW"

    def __init__(self, st):
        self.st = st
        self.dropped = False

    def drop(self, S):
        if self.dropped:
            return
        self.dropped = True
        if self.st.state == "Pending":
            self.st.state = "Rejected"
            self.st.value = make_error(ERR_CODES["ABANDONED"], "abandoned")
        self.st.settle_pool()


class Scheduler:
    def __init__(self, I, realtime=False):
        self.I = I
        self.ready = deque()
        self.sleepers = []
        self.timers = []
        self.now = 0
        self.seq = 0
        self.fibers = []
        self.cur = None
        self.nextid = 1
        self.entry = None
        self.ext = 0                 # helper-thread calls in flight
        self.handlers = 0            # handler fibers running for a C thread that is waiting for the answer
        self.listeners = 0           # C-kept callbacks that may post events at any time
        self.sig_listeners = 0       # signals() channels: while any exist, sleeping waits in real time
        self.extq = queue.Queue()

    def start_ext(self, f, fn):
        self.ext += 1
        q = self.extq

        def work():
            try:
                q.put((f, fn(), None))
            except BaseException as e:      # noqa: reported to the waiting fiber
                q.put((f, None, e))
        threading.Thread(target=work, daemon=True).start()

    def post_event(self, sink, value):
        """Called from any thread: a C-kept callback was called."""
        self.extq.put((("event", sink), value, None))

    def post_call(self, I, fnv, vals, reply):
        """Called from a foreign thread: C wants an answer from a kept callback (Handler[F])."""
        self.extq.put((("call", None), (fnv, vals, reply), None))

    def deliver_call(self, req):
        fnv, vals, reply = req
        I = self.I

        def runner():
            try:
                g = I.apply(fnv, vals, {})
                r = g.v if isinstance(g, Done) else (yield from g)
            except BaseException:
                self.handlers -= 1
                reply.put(("err", None))      # C gets zeros; the abort ends the program as usual
                raise
            self.handlers -= 1
            reply.put(("ok", r))
            return UNIT
        self.handlers += 1
        self.spawn(runner(), "handler")

    def deliver_event(self, sink, v):
        c = sink.w.chan
        if c.rcount <= 0:
            sink.dropped += 1
        elif c.readers:
            self.wake(c.readers.popleft(), Ok(v))
        elif len(c.buf) < c.cap:
            c.buf.append(v)
            self.notify_sel(c)
        else:
            sink.dropped += 1            # a full channel drops the event; C cannot be made to wait

    def next_due(self):
        """The virtual time of the earliest sleeper or live timer, or None."""
        while self.timers and (self.timers[0][3].gen != self.timers[0][2]):
            heapq.heappop(self.timers)
        c = [self.sleepers[0][0]] if self.sleepers else []
        if self.timers:
            c.append(self.timers[0][0])
        return min(c) if c else None

    def drain_ext(self, block, timeout=None):
        """Wake the fibers whose helper-thread calls have finished, and deliver C-kept callback events
        (waiting for the first if `block`)."""
        while self.ext or self.listeners:
            try:
                f, r, e = self.extq.get(block=block, timeout=timeout if block else None)
            except queue.Empty:
                return
            block = False
            if isinstance(f, tuple):
                if f[0] == "call":
                    self.deliver_call(r)
                else:
                    self.deliver_event(f[1], r)
                continue
            self.ext -= 1
            self.wake(f, ExtFail(e) if e is not None else r)

    # -------------------------------------------------------------- spawn / wake
    def spawn(self, gen, name, entry=False):
        f = Fiber(gen, self.nextid, name, entry)
        self.nextid += 1
        self.fibers.append(f)
        self.ready.append(f)
        if entry:
            self.entry = f
        return f

    def wake(self, f, value=None):
        if f.done:
            return
        f.sendval = value
        f.state = "ready"
        self.ready.append(f)

    def notify_sel(self, c):
        if c.sel:
            ws = c.sel
            c.sel = []
            for f in ws:
                if not f.done and f.state == "blocked":
                    self.wake(f, None)

    # -------------------------------------------------------------- timers
    def arm_timer(self, t, ns, every=None):
        t.gen += 1
        t.fired = False
        t.due = self.now + ns
        t.every = every
        self.seq += 1
        heapq.heappush(self.timers, (t.due, self.seq, t.gen, t))

    def disarm(self, t):
        t.gen += 1
        t.due = None
        t.every = None

    def fire_timer(self, t):
        t.fired = True
        if t.readers:
            f = t.readers.pop(0)
            t.fired = False
            self.wake(f, Ok(UNIT))
        else:
            ws = t.sel
            t.sel = []
            for f in ws:
                if not f.done and f.state == "blocked":
                    self.wake(f, None)
        if t.every:
            self.seq += 1
            t.due = self.now + t.every
            heapq.heappush(self.timers, (t.due, self.seq, t.gen, t))

    def advance(self):
        """Move virtual time to the next sleeper or timer. False when there is nothing to wait for."""
        cand = None
        while self.timers and (self.timers[0][3].gen != self.timers[0][2]):
            heapq.heappop(self.timers)
        if self.sleepers:
            cand = self.sleepers[0][0]
        if self.timers:
            td = self.timers[0][0]
            if cand is None or td < cand:
                cand = td
        if cand is None:
            return False
        if cand > self.now:
            self.now = cand
        while self.sleepers and self.sleepers[0][0] <= self.now:
            _, _, f = heapq.heappop(self.sleepers)
            self.wake(f, UNIT)
        while self.timers and self.timers[0][0] <= self.now:
            d, _, g, t = heapq.heappop(self.timers)
            if t.gen == g:
                self.fire_timer(t)
        return True

    # -------------------------------------------------------------- driving
    def run_main(self, gen):
        I = self.I
        main = self.spawn(gen, "main", entry=True)
        I.cur_fiber = main
        while not main.done:
            if self.ext or self.listeners:
                self.drain_ext(False)
            if not self.ready:
                nxt = self.next_due() if (self.sig_listeners and not self.ext) else None
                if nxt is not None:
                    # a signal may arrive while a fiber sleeps: wait in real time, and let that time pass
                    t0 = time.monotonic_ns()
                    self.drain_ext(True, timeout=max(0, nxt - self.now) / 1e9)
                    self.now += time.monotonic_ns() - t0
                    if self.now >= nxt:
                        self.advance()
                    continue
                if (self.ext or self.listeners) and not (self.handlers and self.sleepers):   # real time: wait for an OS helper thread before advancing virtual time
                    self.drain_ext(True)
                    continue
                if not self.advance():
                    raise ProgramExit(1, "deadlock: every fiber is waiting and nothing can wake them")
                continue
            f = self.ready.popleft()
            if f.done:
                continue
            self.step(f)
        if main.error is not None:
            raise main.error
        return main.result

    def step(self, f):
        if self.I.heap_limit is not None:
            heap.tick(self.I)
        self.cur = f
        self.I.cur_fiber = f
        f.state = "running"
        try:
            sv = f.sendval
            f.sendval = None
            req = f.gen.send(sv)
        except StopIteration as s:
            self.finish(f, s.value)
            return
        except ReturnEx as r:
            self.finish(f, r.value)
            return
        except BreakEx as b:
            self.finish(f, UNIT)
            return
        except ProgramExit as e:
            f.done = True
            f.error = e
            self.drop_owned(f)
            if f.entry:
                return
            raise
        except Abort as a:
            self.abort(f, a)
            return
        k = req[0]
        if k == "tick":
            f.state = "ready"
            self.ready.append(f)
        elif k == "sleep":
            f.state = "blocked"
            self.seq += 1
            heapq.heappush(self.sleepers, (self.now + req[1], self.seq, f))
        elif k == "block":
            f.state = "blocked"
        elif k == "ext":
            f.state = "blocked"
            self.start_ext(f, req[1])
        else:
            raise RuntimeError(f"unknown scheduler request {req}")

    def finish(self, f, value):
        f.done = True
        f.result = value
        f.state = "done"
        self.drop_owned(f)

    def abort(self, f, a):
        f.done = True
        f.state = "done"
        self.drop_owned(f)
        msg = f"abort in fiber {f.name}"
        line = a.line or self.I.line
        diag = f"{msg} (line {line}): {a.msg}"
        try:
            self.I.err.write(diag + "\n")
        except Exception:
            pass
        if f.entry:
            f.error = ProgramExit(1, None)
            f.error.printed = True
        else:
            # an abort in any fiber ends the program
            e = ProgramExit(1, None)
            e.printed = True
            raise e

    def drop_owned(self, f):
        for e in f.owned:
            try:
                e.drop(self)
            except Exception:
                pass
        f.owned = []


# ---------------------------------------------------------------- run and select
def run_op(I, n, env):
    S = I.sched
    t = n.target
    if t.__class__ is Lambda:
        # short form: the parameter names are the arguments
        args = []
        for p in t.params:
            v = env.lookup(p.name, I)
            args.append(v)
        clo = I.make_closure(t, env, None)
        callee, pos, named = clo, args, {}
    elif t.__class__ is Call and t.fn.__class__ is Call:
        callee, pos, named = yield from I.ev_Call(t, env, defer=True)
    else:
        if t.__class__ is not Call:
            f = yield from I.ev(t, env)
            callee, pos, named = f, [], {}
        else:
            callee, pos, named = yield from I.ev_Call(t, env, defer=True)
    owned = [a for a in pos if hasattr(a, "drop")] + [a for a in named.values() if hasattr(a, "drop")]
    node = getattr(callee, "node", None)
    name = getattr(node, "name", None) or "fiber"
    limit = fiber_limit(I, node)
    live = S.__dict__.setdefault("live_fibers", {})
    key = id(node)
    if limit is not None and node is not None and live.get(key, 0) >= limit:
        return err_reserved("NO_SLOT", f"fiber function {name}: all {limit} slots are alive")
    cap = getattr(S, "fiber_cap", None)
    if cap is not None and sum(1 for x in S.fibers if not x.done) >= cap:
        raise Abort(f"the fiber blocks are all in use: the pool header allows {cap} fibers")
    gen = I.apply(callee, pos, named)
    counted = limit is not None and node is not None
    if counted:
        live[key] = live.get(key, 0) + 1
    f = S.spawn(_fiber_body(I, gen, live, key if counted else None), name)
    f.owned = owned
    return Ok(UNIT)


def fiber_limit(I, node):
    """The most instances of a fiber function that may be alive: `fiber[n]`, else the manifest's [fibers] limit."""
    for fl in (getattr(node, "flags", None) or ()):
        if isinstance(fl, str) and fl.startswith("fiber:"):
            return int(fl[6:])
    return (getattr(I, "manifest", None) or {}).get("fibers", {}).get("limit")


def _fiber_body(I, gen, live=None, key=None):
    try:
        r = yield from gen
    finally:
        if key is not None:
            live[key] = live.get(key, 1) - 1
    return r


def select_op(I, n, env):
    S = I.sched
    prepared = []
    for arm in n.arms:
        if arm.kind == "default":
            prepared.append(("default", None, arm))
        elif arm.kind == "closed":
            ch = yield from I.ev(arm.expr, env)
            prepared.append(("closed", ch, arm))
        else:
            e = arm.expr
            if e.__class__ is Call and e.args:
                ch = yield from I.ev(e.args[0].expr, env)
            else:
                ch = yield from I.ev(e, env)
            prepared.append(("read", ch, arm))
    while True:
        default = None
        for kind, ch, arm in prepared:
            if kind == "read":
                if ch.ready():
                    v = ch.take(S)
                    if isinstance(ch, ChanR):
                        S.notify_sel(ch.chan)
                    return (yield from _arm_body(I, arm, v, env))
            elif kind == "closed":
                if ch.is_closed():
                    return (yield from _arm_body(I, arm, UNIT, env))
            else:
                default = arm
        if default is not None:
            return (yield from _arm_body(I, default, UNIT, env))
        f = S.cur
        for kind, ch, arm in prepared:
            if kind in ("read", "closed"):
                tgt = ch.chan if isinstance(ch, (ChanR,)) else ch
                tgt.sel.append(f)
        yield ("block",)
        for kind, ch, arm in prepared:
            if kind in ("read", "closed"):
                tgt = ch.chan if isinstance(ch, (ChanR,)) else ch
                while f in tgt.sel:
                    tgt.sel.remove(f)


def _arm_body(I, arm, v, env):
    scope = Env(env)
    b = arm.bind
    if b is not None:
        if isinstance(b, str):
            scope.vars[b] = v
        else:
            bb = {}
            if not I.pmatch(b, v, bb, env):
                raise Abort("select pattern did not match")
            scope.vars.update(bb)
    return (yield from I.ev_body(arm.body, scope))
