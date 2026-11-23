---
layout: default
dialect: gc
learn: true
title: "JSON and data from outside · Mixer’s Guide moxie/gc"
---
# 39. JSON and data from outside

<div class='specref' markdown='1'>In the Spec: [23c. JSON and data from outside (the `json` package)](../spec.html?from=30-json#s23c), [15. Errors and Results](../spec.html?from=30-json#s15)</div>

Data from outside a program, such as a configuration file or a web response, has a shape the program doesn't know until it arrives. Moxie doesn't look inside your types at run time (there is no reflection), so the standard `json` package gives you an ordinary, closed type for such data. This lesson shows how to read it, how to write it, and how to turn it into your own types and back.

## `Dyn`: a value of unknown shape

`Dyn` is an enum with seven cases: `DNull`, `DBool`, `DInt`, `DFloat`, `DText`, `DList`, and `DMap`. Because it is plain data, there is nothing magic about it: you can `when` on it like any other enum. `json.parse(text)` reads JSON into one, and `to_json()` writes it back:

```moxie
import json

doc = json.parse("[1, 2.5, true, null, \"hi\"]")?
println(doc.to_json())
```
**Output:**

```
[1,2.5,true,null,"hi"]
```

`json.parse` returns a `Result`: text that isn't valid JSON gives an `Err`, never a crash.

```moxie
import json

println(json.parse("[1, 2"))
```
**Output:**

```
Err(Error(code: 1, message: "unterminated list at character 5"))
```

## Reading values out

Reading from a `Dyn` is a lookup that returns a `Result`:

- `field(key)` takes a value out of a map; `at(i)` takes one out of a list;
- `as_text()`, `as_int()`, `as_float()`, `as_bool()`, and `as_list()` take the value out of its wrapper (`as_float` also accepts an `Int`).

A missing key, an index out of range, and a value of the wrong kind are all an `Err`, so a malformed document can't stop your program.

```moxie
import json

text = "{\"name\": \"Al\", \"scores\": [90, 85.5], \"admin\": false}"
doc = json.parse(text)?
name = doc.field("name").flat_map((d) -> d.as_text())?
first = doc.field("scores").flat_map((d) -> d.at(0)).flat_map((d) -> d.as_int())?
println("${name} ${first}")
println(doc.field("email"))
println(doc.field("name").flat_map((d) -> d.as_int()))
println(doc.to_json())
```
**Output:**

```
Al 90
Err(Error(code: 4, message: "no key \"email\""))
Err(Error(code: 1, message: "not an Int"))
{"name":"Al","scores":[90,85.5],"admin":false}
```

Each `flat_map` step passes an `Err` along unchanged, so a chain of lookups fails at the first step that can't be done, and the `?` at the end hands that `Err` to the caller (lesson 16).

A map keeps its entries in the order they were written, so `to_json()` prints them in that order. A number with a `.` or an exponent is a `DFloat`, not an `Int`, so read it with `as_float`.

## Your own types: `deriving dyn`

Walking a `Dyn` by hand gets tedious for a big document. Put `dyn` in a type's `deriving` list and the tuple gets `to_dyn()`, which gives a `Dyn`, and `Type.from_dyn(d)`, which gives a `Result`:

```moxie
import json

tuple Addr deriving dyn, show
  city String,
  zip Int

tuple User deriving dyn, show
  name String,
  tags List[String],
  addr Addr

dynamic fn load(text String) Result[User, Error]
  User.from_dyn(json.parse(text)?)

u = User(name: "Al", tags: List("a", "b"), addr: Addr(city: "Oslo", zip: 150))
println(u.to_dyn().to_json())
println(load(u.to_dyn().to_json()))
println(load("{\"name\": \"Al\", \"tags\": [1]}"))
```
**Output:**

```
{"name":"Al","tags":["a","b"],"addr":{"city":"Oslo","zip":150}}
Ok(User(name: "Al", tags: List("a", "b"), addr: Addr(city: "Oslo", zip: 150)))
Err(Error(code: 1, message: "not a String"))
```

A field may be an `Int`, `Float`, `Bool`, `String`, a `List` of those, or another tuple or enum that derives `dyn`. A missing key or a value of the wrong kind gives an `Err` that says which. A type that doesn't derive `dyn`, a `Dict`, a function, and a closure can't be converted, and the compiler tells you so.

### Enums

An enum becomes a map with the case name under `"case"` and the case's named fields beside it:

```moxie
import json

enum Shape deriving dyn, show
  Circle(r Float)
  Rect(w Float, h Float)
  Empty

dynamic fn parse_shape(text String) Result[Shape, Error]
  Shape.from_dyn(json.parse(text)?)

s = Shape.Rect(w: 2.0, h: 3.0)
println(s.to_dyn().to_json())
println(parse_shape(s.to_dyn().to_json()))
println(parse_shape("{\"case\": \"Blob\"}"))
```
**Output:**

```
{"case":"Rect","w":2.0,"h":3.0}
Ok(Shape.Rect(2.0, 3.0))
Err(Error(code: 1, message: "unknown case \"Blob\" for Shape"))
```

### Generic types

A generic type can derive `dyn` too. Name the type arguments when you read one back:

```moxie
import json

tuple Pair[A, B] deriving dyn, show
  first A
  second B

enum Tree[T] deriving dyn, show
  Leaf(v T)
  Node(l Tree[T], r Tree[T])

p = Pair(first: 1, second: "a")
println(p.to_dyn().to_json())
println(Pair[Int, String].from_dyn(p.to_dyn()))
t = Tree.Node(l: Tree.Leaf(v: 1), r: Tree.Leaf(v: 2))
println(Tree[Int].from_dyn(t.to_dyn()))
```
**Output:**

```
{"first":1,"second":"a"}
Ok(Pair(first: 1, second: "a"))
Ok(Tree.Node(Tree.Leaf(1), Tree.Leaf(2)))
```

## `dynamic fn`

Reading a `Dyn` moves a type check from compile time to run time, so the function that does it says so: write `dynamic` before `fn`. A function that reads a `Dyn` without the word is a compile error. Top-level statements are not functions, so a script can read a `Dyn` directly, as the examples at the start of this lesson do.

A function that calls a foreign function marked `unsafe` needs `unsafe fn` in the same way. The words are soft: `dynamic` and `unsafe` are still fine as variable names.

By default only the function that does the thing is marked, so a wrapper that checks its data (like `load` above) can be called from any function. A project that wants the marks to travel up the call chain sets `safety = "strict"` under `[program]` in `Moxie.toml`.

## What to remember

- `json.parse(text)` gives a `Result[Dyn, Error]`; `to_json()` writes one back.
- Lookups (`field`, `at`, `as_*`) return a `Result`, so a malformed document is an `Err`, not a crash.
- `deriving dyn` gives `to_dyn()` and `Type.from_dyn(d)` for your own tuples and enums.
- Functions that read a `Dyn` are written `dynamic fn`.
- Don't expect a map's keys to come out sorted, or `\u` escapes in strings (not supported yet).

---

[← Builders: a DSL without macros](29-builders-and-blocks.html) · [Contents](./) · [Regular expressions →](31-regex.html)
