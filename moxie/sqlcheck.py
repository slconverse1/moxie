"""Compile-time check of `sql(conn):` blocks against the schema named in Moxie.toml's [database] table (Spec section 21).

A first version: the accepted SQL subset, and that every table and column named exists.  Column types and row types
are not worked out here."""
import difflib
import os
import re

KEYWORDS = {
    "select", "from", "where", "join", "inner", "on", "group", "by", "order", "limit", "offset", "and", "or", "not", "as",
    "insert", "into", "values", "update", "set", "delete", "asc", "desc", "is", "null", "true", "false", "in", "like",
    "between", "count", "sum", "min", "max", "cross",
}
REJECTED = {"having": "HAVING", "union": "UNION", "intersect": "INTERSECT", "except": "EXCEPT", "with": "WITH", "distinct": "DISTINCT",
            "avg": "AVG", "left": "LEFT JOIN", "right": "RIGHT JOIN", "outer": "OUTER JOIN", "full": "FULL JOIN", "create": "CREATE",
            "drop": "DROP", "alter": "ALTER", "pragma": "PRAGMA", "case": "CASE", "exists": "EXISTS"}
TOKEN = re.compile(r"\s*(?:(?P<str>'(?:[^']|'')*')|(?P<num>\d+(?:\.\d+)?)|(?P<id>[A-Za-z_][A-Za-z_0-9]*)|(?P<op><=|>=|<>|!=|[(),.*=<>+\-/%?;]))")


def load_schema(manifest):
    """{table: {column: type}} from the file named by [database] schema, or None when the manifest names none."""
    db = (manifest or {}).get("database")
    if not db or "schema" not in db:
        return None
    path = os.path.join(os.path.dirname(manifest["path"]), db["schema"])
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        return ("error", f"the schema file {db['schema']!r} named in [database] cannot be read: {e.strerror or e}")
    text = re.sub(r"--[^\n]*", "", text)
    schema = {}
    for m in re.finditer(r"create\s+table\s+(?:if\s+not\s+exists\s+)?(\w+)\s*\((.*?)\)\s*;", text, re.S | re.I):
        cols = {}
        depth, cur, parts = 0, "", []
        for ch in m.group(2):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += ch
        parts.append(cur)
        for part in parts:
            w = part.split()
            if not w or w[0].lower() in ("primary", "foreign", "unique", "check", "constraint"):
                continue
            cols[w[0]] = w[1].upper() if len(w) > 1 else ""
        schema[m.group(1)] = cols
    return schema


def tokens(sql):
    out, i = [], 0
    while i < len(sql):
        m = TOKEN.match(sql, i)
        if not m:
            if sql[i:].strip() == "":
                break
            return None
        i = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


def near(word, choices):
    m = difflib.get_close_matches(word, list(choices), n=1)
    return f" (did you mean `{m[0]}`?)" if m else ""


def check_sql_text(sql, schema):
    """Problems in one statement (a list of messages)."""
    toks = tokens(sql)
    if toks is None:
        return ["this SQL has a character outside the accepted subset"]
    if not toks:
        return ["an empty `sql` block"]
    first = toks[0][1].lower() if toks[0][0] == "id" else ""
    if first not in ("select", "insert", "update", "delete"):
        return [f"`{toks[0][1]}` is not in the accepted SQL: a `sql` block holds SELECT, INSERT, UPDATE, or DELETE"]
    probs = []
    for i, (k, v) in enumerate(toks):
        if k == "id" and v.lower() in REJECTED:
            probs.append(f"{REJECTED[v.lower()]} is not in the accepted SQL subset (SELECT with WHERE, JOIN, GROUP BY, COUNT/SUM/MIN/MAX, ORDER BY, LIMIT, OFFSET, and INSERT, UPDATE, DELETE)")
        if k == "op" and v == "(" and i + 1 < len(toks) and toks[i + 1][1].lower() == "select":
            probs.append("a subquery is not in the accepted SQL subset")
    if probs:
        return probs
    # tables: after FROM, JOIN, INTO, UPDATE; an alias follows (optionally after AS)
    aliases, used = {}, []
    i = 0
    while i < len(toks):
        k, v = toks[i]
        if k == "id" and v.lower() in ("from", "join", "into", "update") and i + 1 < len(toks) and toks[i + 1][0] == "id":
            name = toks[i + 1][1]
            used.append(name)
            alias = name
            j = i + 2
            if j < len(toks) and toks[j][0] == "id" and toks[j][1].lower() == "as" and j + 1 < len(toks):
                j += 1
            if j < len(toks) and toks[j][0] == "id" and toks[j][1].lower() not in KEYWORDS:
                alias = toks[j][1]
            aliases[alias] = name
            aliases.setdefault(name, name)
            i = j
            continue
        i += 1
    for t in used:
        if t not in schema:
            probs.append(f"unknown table `{t}`" + near(t, schema) + f" (the schema has {', '.join(sorted(schema)) or 'no tables'})")
    if probs:
        return probs
    cols = {c for t in used for c in schema[t]}
    select_aliases = set()
    for i, (k, v) in enumerate(toks):
        if k == "id" and v.lower() == "as" and i + 1 < len(toks) and toks[i + 1][0] == "id":
            select_aliases.add(toks[i + 1][1])
    skip = set()
    for i, (k, v) in enumerate(toks):
        if k == "id" and v.lower() in ("from", "join", "into", "update") and i + 1 < len(toks):
            skip.add(i + 1)
            j = i + 2
            if j < len(toks) and toks[j][1].lower() == "as":
                skip.add(j)
                j += 1
            if j < len(toks) and toks[j][0] == "id" and toks[j][1].lower() not in KEYWORDS:
                skip.add(j)
        if k == "id" and v.lower() == "as" and i + 1 < len(toks):
            skip.add(i + 1)
    for i, (k, v) in enumerate(toks):
        if k != "id" or i in skip or v.lower() in KEYWORDS:
            continue
        if i + 1 < len(toks) and toks[i + 1][1] == "(":
            continue                                         # a function call
        if i + 1 < len(toks) and toks[i + 1][1] == "." and i + 2 < len(toks):
            if v not in aliases:
                probs.append(f"unknown table or alias `{v}`")
            else:
                col = toks[i + 2][1]
                tcols = schema[aliases[v]]
                if col != "*" and col not in tcols:
                    probs.append(f"unknown column `{col}` in table `{aliases[v]}`" + near(col, tcols) + f" (its columns are {', '.join(tcols)})")
            skip.add(i + 2)
            continue
        if i > 0 and toks[i - 1][1] == ".":
            continue
        if v in aliases or v in select_aliases:
            continue
        if v not in cols:
            allc = sorted(cols)
            probs.append(f"unknown column `{v}`" + near(v, cols) + f" (in {', '.join(sorted(set(used)))}: {', '.join(allc)})")
    return probs


def sql_diags(prog, manifest):
    """Diag-like (line, message) pairs for every `sql(...)` block in the program."""
    schema = load_schema(manifest)
    if schema is None:
        return []
    out = []
    if isinstance(schema, tuple):
        return [(1, schema[1])]
    from .ast import N, SqlE
    from .effects import _children
    todo = [prog]
    while todo:
        n = todo.pop()
        if n.__class__ is SqlE:
            text = "".join(p if isinstance(p, str) else " ? " for p in n.parts or [])
            for msg in check_sql_text(text, schema):
                out.append((getattr(n, "line", 0), msg))
        todo.extend(_children(n))
    return out
