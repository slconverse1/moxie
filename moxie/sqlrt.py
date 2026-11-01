"""SQL support: `sql(conn):` blocks and `transaction(conn)(tx):` on stdlib sqlite3.

The Spec's checked SQL subset is a compile-time rule; at run time the text goes to sqlite
with `$name` / `${expr}` turned into bound parameters, so there is no injection.
"""
import sqlite3
from .values import *   # noqa
from .core import *   # noqa
from .calls import END
from .streams import StreamV

SQL_CODE = 40   # error code for database errors


class ConnV:
    """A Connection resource. One owner; a transaction handle `tx` is a borrow of it."""
    __slots__ = ("db", "path", "in_tx", "closed", "tx_of")
    tname_ = "Connection"

    def __init__(self, db, path, tx_of=None):
        self.db = db
        self.path = path
        self.in_tx = False
        self.closed = False
        self.tx_of = tx_of

    def drop(self, sched=None):
        if self.tx_of is None and not self.closed:
            self.closed = True
            try:
                self.db.close()
            except Exception:
                pass

    def raw(self):
        return self.tx_of.db if self.tx_of is not None else self.db


def open_connection(path):
    try:
        db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    except sqlite3.Error as e:
        return Err(make_error(SQL_CODE, f"cannot open database: {e}"))
    return Ok(ConnV(db, path))


def to_sql_param(v):
    if v is True:
        return 1
    if v is False:
        return 0
    if v is UNIT or v is None:
        return None
    if isinstance(v, (Char, Kw)):
        return str(v)
    if isinstance(v, Dec):
        return str(v.v)
    if isinstance(v, (int, float, str, bytes)):
        return int(v) if isinstance(v, int) else v
    raise Abort(f"cannot bind a {type_name(v)} as a SQL parameter")


def from_sql(x):
    return UNIT if x is None else x


class SqlIter:
    """A lazy stream over a query's rows; each terminal re-sends the query."""

    def __init__(self, db, text, params):
        self.cur = db.cursor()
        try:
            self.cur.execute(text, params)
        except sqlite3.Error as e:
            raise Abort(f"database error: {e}")
        self.names = [d[0] for d in (self.cur.description or [])]

    def nxt(self):
        try:
            row = self.cur.fetchone()
        except sqlite3.Error as e:
            raise Abort(f"database error mid-stream: {e}")
        if row is None:
            self.cur.close()
            return Done(END)
        return Done(TupleV([from_sql(x) for x in row], list(self.names)))


def sql_op(I, n, env):
    conn = yield from I.ev(n.conn, env)
    if conn.__class__ is not ConnV:
        raise Abort(f"sql(...) needs a Connection, not {type_name(conn)}", n.line)
    if conn.closed:
        raise Abort("the Connection is closed", n.line)
    text = []
    params = []
    for part in n.parts:
        if isinstance(part, tuple):
            v = yield from I.ev(part[1], env)
            text.append("?")
            params.append(to_sql_param(v))
        else:
            text.append(part)
    stmt = "".join(text).strip()
    # a query is a switching point for the scheduler
    yield ("tick",)
    db = conn.raw()
    head = stmt.lstrip("(").split(None, 1)[0].upper() if stmt else ""
    if head in ("SELECT", "WITH", "VALUES"):
        return Ok(StreamV(lambda: SqlIter(db, stmt, params)))
    try:
        cur = db.execute(stmt, params)
        count = cur.rowcount
        cur.close()
    except sqlite3.Error as e:
        return Err(make_error(SQL_CODE, str(e)))
    return Ok(max(count, 0))


def transaction(I, a, kw):
    """transaction(conn)(tx): body. Ok commits; Err (including `?`) rolls back."""
    conn, fn = a[0], a[-1]
    if conn.__class__ is not ConnV or conn.tx_of is not None:
        raise Abort("transaction needs a Connection (transactions don't nest)")
    if conn.in_tx:
        raise Abort("transactions don't nest")
    iso = kw.get("isolation")
    begin = "BEGIN IMMEDIATE" if iso is not None and str(iso).lstrip("#") == "serializable" else "BEGIN"
    try:
        conn.db.execute(begin)
    except sqlite3.Error as e:
        return Err(make_error(SQL_CODE, str(e)))
    conn.in_tx = True
    tx = ConnV(None, conn.path, tx_of=conn)
    try:
        r = yield from I.apply(fn, [tx])
    except BaseException:
        conn.db.execute("ROLLBACK")
        conn.in_tx = False
        raise
    finally:
        tx.closed = True        # `tx` is a borrow valid only inside the lambda
    conn.in_tx = False
    try:
        if isinstance(r, EnumV) and r.et is RESULT_T and r.case == "Ok":
            conn.db.execute("COMMIT")
        else:
            conn.db.execute("ROLLBACK")
    except sqlite3.Error as e:
        return Err(make_error(SQL_CODE, str(e)))
    return r
