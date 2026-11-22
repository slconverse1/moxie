---
layout: default
title: "Databases with SQL · Learn moxie"
---
<p><small>Data from outside</small></p>

# 42. Databases with SQL

Moxie checks SQL the way it checks everything else: before the program runs. A query is written in place with `sql(conn):` and the SQL indented below, and its result has a type the compiler knows.

A real project names its schema in `Moxie.toml`, and the compiler then checks every query against it, so an unknown column is a compile error:

```moxie
[database]
schema = "schema.sql"
driver = "postgres"
```

The examples in this lesson use a throwaway in-memory database, `Connection.memory()`, and create their tables as they go, so each one is complete and runs on its own. In a real program the entry file opens the connection with `Connection.open(path)`, which returns a `Result[Connection, Error]`, so the usual line is `conn = Connection.open(args(0))?`.

## Writing and reading

A statement that changes data returns a `Result` with the number of rows affected. A `SELECT` returns a `Result` holding a *stream* of rows (lesson 21), and each row is a named tuple of the selected columns:

```moxie
conn = Connection.memory()?
_ = sql(conn):
  CREATE TABLE telemetry (id INTEGER, value REAL, active BOOLEAN)
n = sql(conn):
  INSERT INTO telemetry VALUES (1, 0.9, true), (2, 0.2, true), (3, 0.7, true)
println(n)
rows = sql(conn):
  SELECT id, value FROM telemetry ORDER BY id
for t in rows?
  println("${t.id}: ${t.value}")
```
**Output:**

```
Ok(3)
1: 0.9
2: 0.2
3: 0.7
```

The accepted SQL is a subset: `SELECT` with `WHERE`, `JOIN`, `GROUP BY`, the aggregates `COUNT`, `SUM`, `MIN`, and `MAX`, `ORDER BY`, `LIMIT`, and `OFFSET`, plus `INSERT`, `UPDATE`, and `DELETE`.

## Parameters

A `$name` inside the SQL is a *bound parameter*: moxie sends its value separately from the query text, so there is no way to inject SQL through it.

```moxie
conn = Connection.memory()?
_ = sql(conn):
  CREATE TABLE telemetry (id INTEGER, value REAL, active BOOLEAN)
_ = sql(conn):
  INSERT INTO telemetry VALUES (1, 0.9, true), (2, 0.2, true), (3, 0.7, true)
min_value = 0.5
rows = sql(conn):
  SELECT id, value FROM telemetry
  WHERE value >= $min_value AND active = true
  ORDER BY id
for t in rows?
  println("${t.id}: ${t.value}")
```
**Output:**

```
1: 0.9
3: 0.7
```

A parameter stands for a *value*. A table or column name can't be a parameter (`${table}` as a table name is an error), because that is exactly where injection would sneak in.

## Query functions

A function that returns a query's stream is declared `inline fn`, because the stream is lazy and borrows the connection, so the function must not keep the connection past its own call. Naming the row type gives the rows a name:

```moxie
tuple Telemetry
  id Int,
  value Double

inline fn fetch_active(conn Connection, min_value Double) Result[Stream[Telemetry], Error]
  sql(conn):
    SELECT id, value FROM telemetry
    WHERE value >= $min_value AND active = true
    ORDER BY id

conn = Connection.memory()?
_ = sql(conn):
  CREATE TABLE telemetry (id INTEGER, value REAL, active BOOLEAN)
_ = sql(conn):
  INSERT INTO telemetry VALUES (1, 0.9, true), (2, 0.2, true), (3, 0.7, true)
rows = fetch_active(conn, 0.5)?
for t in rows
  println("${t.id}: ${t.value}")
```
**Output:**

```
1: 0.9
3: 0.7
```

A stream turns into a collection the usual way. Here the rows of a `config` table become a `List`, which can be searched and used long after the query is done:

```moxie
fn load_config(conn Connection) Result[List[(key String, value String)], Error]
  rows = sql(conn):
    SELECT key, value FROM config
  Ok(rows? |> collect())

conn = Connection.memory()?
_ = sql(conn):
  CREATE TABLE config (key TEXT, value TEXT)
_ = sql(conn):
  INSERT INTO config VALUES ('mode', 'fast'), ('level', '3')
cfg = load_config(conn)?
for row in cfg
  println("${row.key} = ${row.value}")
```
**Output:**

```
mode = fast
level = 3
```

## Rows and open types

The rows of a query are labeled tuples, so a function written for an open type (lesson 12) takes them directly, whatever else the query selected:

```moxie
fn adult(r (age Int, ...)) Bool = r.age >= 18
fn greet(r (name String, ...)) String = "hi ${r.name}"

inline fn staff(conn Connection, dept String) Result[Stream[(name String, age Int)], Error]
  sql(conn):
    SELECT name, age FROM staff WHERE dept = $dept ORDER BY id

conn = Connection.memory()?
_ = sql(conn):
  CREATE TABLE staff (id INTEGER, name TEXT, age INTEGER, dept TEXT)
_ = sql(conn):
  INSERT INTO staff VALUES (1, 'Ana', 34, 'eng'), (2, 'Bo', 17, 'eng'), (3, 'Cy', 40, 'ops')
for p in staff(conn, "eng")? |> filter(adult)
  println(greet(p))
```
**Output:**

```
hi Ana
```

The same `greet` works on a query that selects `name, dept`, or on a tuple built in the program, so a report function can be written once and fed from SQL, a file, or a test.

## Transactions

A transaction commits when its function returns `Ok` and rolls back when it returns `Err` or exits through `?`:

```moxie
fn move_funds(tx Connection, from_id Int, to_id Int, amount Int) Result[Unit, Error]
  debit = sql(tx):
    UPDATE accounts SET balance = balance - $amount WHERE id = $from_id
  _ = debit?
  credit = sql(tx):
    UPDATE accounts SET balance = balance + $amount WHERE id = $to_id
  _ = credit?
  Ok(())

fn transfer(conn Connection, from_id Int, to_id Int, amount Int) Result[Unit, Error]
  transaction(conn, move_funds(_, from_id, to_id, amount))

conn = Connection.memory()?
_ = sql(conn):
  CREATE TABLE accounts (id INTEGER, balance INTEGER)
_ = sql(conn):
  INSERT INTO accounts VALUES (1, 100), (2, 50)
println(transfer(conn, 1, 2, 30))
bal = sql(conn):
  SELECT id, balance FROM accounts ORDER BY id
for r in bal?
  println("${r.id} ${r.balance}")
```
**Output:**

```
Ok(())
1 70
2 80
```

If either `UPDATE` failed, `?` would leave the function early and *neither* change would be kept.

## When the SQL is wrong

A statement the database rejects is an `Err`, not a crash:

```moxie
conn = Connection.memory()?
bad = sql(conn):
  SELEKT nonsense
println(bad)
```
**Output:**

```
Err(Error(code: 40, message: "near \"SELEKT\": syntax error"))
```

With a schema in `Moxie.toml`, many mistakes never reach this point: an unknown table or column is a compile error.

## What to remember

- `sql(conn):` with the SQL indented below; `$name` is a bound parameter, never pasted in.
- Writes give the rows affected; a `SELECT` gives a stream of named tuples.
- A function that returns a query's stream is `inline fn`.
- `transaction(conn, f)` commits on `Ok` and rolls back on `Err`.
- Don't nest transactions, send a transaction's connection to a channel, or open a `Connection` inside a loop.
- `sql` is not allowed at module level or in `init`; read configuration in the entry file before `daemon`.

---

[← Units of measure](34-units.html) · [Contents](./) · [Values, purity, and composing functions →](36-purity-and-composition.html)
