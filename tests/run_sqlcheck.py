"""Compile-time SQL checks against the manifest's schema (Spec 21).  Run: python3 tests/run_sqlcheck.py"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = """-- telemetry and accounts
CREATE TABLE telemetry (
  id INTEGER PRIMARY KEY,
  value REAL NOT NULL,
  active BOOLEAN
);
CREATE TABLE accounts (
  id INTEGER PRIMARY KEY,
  balance INTEGER NOT NULL,
  owner TEXT
);
"""
MAN = '[database]\nschema = "schema.sql"\ndriver = "sqlite"\n'
HEAD = 'fn q(conn: Connection, min_value: Double, amount: Int) Result[Unit, Error]:\n'
def prog(body): return HEAD + "".join("  " + l + "\n" for l in body.strip("\n").split("\n")) + "  Ok(())\nprintln(1)\n"
def run(body, manifest=MAN, cmd="check"):
    d = tempfile.mkdtemp()
    if manifest is not None: open(os.path.join(d, "Moxie.toml"), "w").write(manifest)
    open(os.path.join(d, "schema.sql"), "w").write(SCHEMA)
    open(os.path.join(d, "main.mxi"), "w").write(prog(body))
    r = subprocess.run([sys.executable, "-m", "moxie", cmd, os.path.join(d, "main.mxi")], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=ROOT), input="")
    return r.returncode, r.stdout + r.stderr
def sel(sql): return "rows = sql(conn):\n" + "".join("    " + l + "\n" for l in sql.strip().split("\n"))
GOOD = [
 ("a select with where and order", sel("SELECT id, value FROM telemetry\nWHERE value >= $min_value AND active = true\nORDER BY id")),
 ("a join with aliases", sel("SELECT t.id, a.balance FROM telemetry t JOIN accounts a ON t.id = a.id WHERE a.balance > 0")),
 ("aggregates, group by, limit, offset", sel("SELECT owner, COUNT(id), SUM(balance) FROM accounts GROUP BY owner ORDER BY owner LIMIT 5 OFFSET 2")),
 ("an update", "debit = sql(conn):\n    UPDATE accounts SET balance = balance - $amount WHERE id = 1\n"),
 ("an insert", "r = sql(conn):\n    INSERT INTO accounts (id, balance, owner) VALUES (1, 2, 'a')\n"),
 ("a delete", "r = sql(conn):\n    DELETE FROM accounts WHERE balance < $amount\n"),
]
BAD = [
 ("an unknown column", sel("SELECT id, valu FROM telemetry"), "unknown column `valu` (did you mean `value`?)"),
 ("an unknown column in WHERE", sel("SELECT id FROM telemetry WHERE nope = 1"), "unknown column `nope`"),
 ("an unknown table", sel("SELECT id FROM telemetri"), "unknown table `telemetri` (did you mean `telemetry`?)"),
 ("a column from the other table", sel("SELECT balance FROM telemetry"), "unknown column `balance`"),
 ("an unknown qualified column", sel("SELECT t.nope FROM telemetry t"), "unknown column `nope` in table `telemetry`"),
 ("HAVING is outside the subset", sel("SELECT owner FROM accounts GROUP BY owner HAVING COUNT(id) > 1"), "HAVING is not in the accepted SQL subset"),
 ("a subquery is outside the subset", sel("SELECT id FROM accounts WHERE id IN (SELECT id FROM telemetry)"), "subquery"),
 ("AVG is outside the subset", sel("SELECT AVG(balance) FROM accounts"), "AVG is not"),
 ("DROP is outside the subset", "r = sql(conn):\n    DROP TABLE accounts\n", "not in the accepted SQL"),
 ("an unknown column in UPDATE", "r = sql(conn):\n    UPDATE accounts SET balanc = 1 WHERE id = 1\n", "unknown column `balanc`"),
]
fails = []
def report(name, ok, o=""):
    print(("ok    " if ok else "FAIL  ") + name + ("" if ok else f"  -> {o.strip()[:240]}"))
    if not ok: fails.append(name)
for name, body in GOOD:
    rc, o = run(body)
    report(name, rc == 0 and "error" not in o, o)
for name, body, word in BAD:
    rc, o = run(body)
    report(name, rc != 0 and word in o, o)
rc, o = run(BAD[0][1], manifest=None)
report("no [database] table: nothing is checked", rc == 0, o)
rc, o = run(GOOD[0][1], manifest='[database]\nschema = "missing.sql"\n')
report("a missing schema file is reported", rc != 0 and "cannot be read" in o, o)
rc, o = run(GOOD[0][1], manifest='[database]\nschemma = "schema.sql"\n')
report("a typo in the [database] table is suggested", rc != 0 and "did you mean 'schema'" in o, o)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
