---
layout: default
learn: true
title: "…moxie: the rest of its toolbox · Learner’s Guide moxie"
---
<p><small>Your program and its machine</small></p>

# 65. …moxie: the rest of its toolbox

The earlier lessons teach the language by topic. This page gathers the small things they skipped: a few more numeric functions, some stream and `Result` helpers, a handful of resource and library calls. Nothing here is needed to read the rest of the guide, and you can come back to any of it when a program asks for it. Each section ends with the lesson that covers its neighbourhood.

## Numbers that check themselves

A plain `+` on integers aborts when the result doesn't fit, so overflow is never silent. When you want a different behaviour, ask for it by name. `checked_add`, `checked_sub`, `checked_mul`, and `checked_div` return a `Result`, with an `Err` on overflow or a zero divisor:

```moxie
println(checked_div(7, 2))
println(checked_div(7, 0))
a Int8 = 100
println(checked_add(a, a))
println(checked_add(a, 20))
```
**Output:**

```
Ok(3)
Err(Error(code: 6, message: "division by zero"))
Err(Error(code: 6, message: "overflow"))
Ok(120)
```

`wrapping_add` and its relatives wrap around, which is what hashes and checksums want, and `saturating_add` and its relatives stick at the limit:

```moxie
x UInt8 = 250
println(wrapping_add(x, 10))
println(saturating_add(x, 10))
```
**Output:**

```
4
255
```

To convert between integer types, `try_cast[T]` gives a `Result`, and `wrap_to[T]` keeps the low bits:

```moxie
println(try_cast[UInt8](300))
println(try_cast[UInt8](200))
println(wrap_to[UInt8](300))
```
**Output:**

```
Err(Error(code: 6, message: "does not fit"))
Ok(200)
44
```

Floating-point division by zero doesn't abort. It gives `INF` or `NAN`, and `NAN` is never equal to anything, itself included, so test for it with `is_nan`, and with `is_finite` and `is_inf` for the others:

```moxie
n = 0.0 / 0.0
println(is_nan(n))
println(n == n)
println(is_finite(1.0 / 0.0))
println(is_inf(1.0 / 0.0))
```
**Output:**

```
true
false
false
true
```

Integers also have the bit operators `&`, `|`, `^`, `~`, `<<`, and `>>`, and each has a word form for a reader who would rather not learn the symbols: `bit_and`, `bit_or`, `bit_xor`, `bit_not`, `shl`, and `shr`:

```moxie
println(12 & 10)
println(12 | 10)
println(12 ^ 10)
println(1 << 4)
println(256 >> 4)
println(~0)
println(bit_and(12, 10))
println(shl(1, 4))
println(shr(256, 4))
println(bit_not(0))
```
**Output:**

```
8
14
6
16
16
-1
8
16
16
-1
```

More on numbers is in lesson 5.

## Text and bytes

A character that looks like one thing can be several Unicode scalars. `graphemes` gives a stream with one `String` per character as a reader sees it, and `to_utf8` and `from_utf8` move between text and bytes:

```moxie
println(graphemes("héllo") |> collect())
b = to_utf8("hé")
println(b)
println(from_utf8(b))
```
**Output:**

```
List("h", "é", "l", "l", "o")
Array(104, 195, 169)
Ok("hé")
```

`from_utf8` gives an `Err` with `BAD_ENCODING` when the bytes aren't valid UTF-8. Text is in lesson 6, and bytes in lessons 37 and 63.

## Stream and Result helpers

The stream stages in lessons 25 and 26 have a few more relatives. `filter_map` keeps what a function turns into a `Some`, `find_map` returns the first such value, `drop_last` is the mirror of `take_last`, `sort_by` sorts by a key, and `reduce_right` folds from the right:

```moxie
xs = List(1, 2, 3, 4)
println(xs |> filter_map((x) -> if x % 2 == 0 then Some(x * 10) else None) |> collect())
println(xs |> find_map((x) -> if x > 2 then Some(x * 10) else None))
println(xs |> drop_last(1) |> collect())
println(xs |> reduce_right(0, (x, acc) -> x - acc))
println(List("bb", "a", "ccc") |> sort_by((w) -> len(w)) |> collect())
```
**Output:**

```
List(20, 40)
Ok(30)
List(1, 2, 3)
-2
List("a", "bb", "ccc")
```

For a list of `Result`s, `collect_errors` gives `Ok` of all the values, or `Err` of *all* the errors rather than just the first. `partition_results` splits them, and `ok_or` turns an `Option` into a `Result`:

```moxie
rs = List(Ok(1), Err(Error(1, "a")), Err(Error(2, "b")))
println(collect_errors(rs))
println(collect_errors(List(Ok(1), Ok(2))))
println(partition_results(List(Ok(1), Err(Error(1, "a")), Ok(3))))
println(ok_or(Some(3), Error(1, "none")))
println(ok_or(None, Error(1, "none")))
```
**Output:**

```
Err(List(Error(code: 1, message: "a"), Error(code: 2, message: "b")))
Ok(List(1, 2))
(List(1, 3), List(Error(code: 1, message: "a")))
Ok(3)
Err(Error(code: 1, message: "none"))
```

`flip` swaps the first two arguments of a function, which helps when a function has them in the wrong order for a pipe:

```moxie
f = flip((a, b) -> a - b)
println(f(1, 10))
```
**Output:**

```
9
```

`non_empty` turns a list into a `NonEmpty`, a head and a tail that can never be empty, or gives an `Err` when the list has nothing in it:

```moxie
println(non_empty(List(3, 1, 2)))
println(non_empty(List()))
```
**Output:**

```
Ok(NonEmpty(head: 3, tail: List(1, 2)))
Err(Error(code: 4, message: "empty"))
```

## Ranges are values

A range such as `1..10 step 3` is a value you can keep, print, and ask questions of, with `first`, `last`, and `step`. `last` is the last value the range reaches, and a range can count down:

```moxie
r = 1..10 step 3
println(r)
println(first(r))
println(last(r))
println(step(r))
down = 10..1 step -3
println(down)
println(len(down))
```
**Output:**

```
1..10 step 3
Ok(1)
Ok(10)
3
10..1 step -3
4
```

Ranges are introduced with loops in lesson 9, and they slice text in lesson 6.

## Atoms and timers

`swap_vals` and `reset_vals` do what `swap` and `reset` do and return the pair `(old, new)`, so you can tell what an update replaced. The `@` reads an atom:

```moxie
a = Atom(1)
println(swap_vals(a, (n) -> n + 1))
println(reset_vals(a, 10))
println(@a)
```
**Output:**

```
(1, 2)
(2, 10)
10
```

A `Timer` can fire once with `arm` or repeatedly with `arm_every`, and `disarm` stops it. Reading the timer waits for the next fire:

```moxie
t = Timer()
arm_every(t, 20ms)
println(read(t))
println(read(t))
disarm(t)
println("done")
```
**Output:**

```
Ok(())
Ok(())
done
```

A timer has one owner and never goes to a fiber. Lessons 28 to 30 cover fibers, channels, atoms, and timers.

## Random and reproducible

`random()` and `random_int(1..6)` come from a generator that starts from operating-system entropy. They aren't for secrets: use `random_bytes(n)` for tokens and keys. For tests, `seeded(n)` makes a generator that repeats for the same `n`, and `gen_int`, `gen_bool`, and `gen_pick` draw from it:

```moxie
g1 = seeded(7)
g2 = seeded(7)
println(gen_int(g1, 1, 6) == gen_int(g2, 1, 6))
println(len(random_bytes(4)))
```
**Output:**

```
true
4
```

A property test (lesson 32) uses the same idea to make its inputs.

## Dates

`days_in_month(year, month)` knows leap years:

```moxie
println(days_in_month(2024, 2))
println(days_in_month(2023, 2))
```
**Output:**

```
29
28
```

A `DateTime` also has `weekday` (1 for Monday to 7 for Sunday) and `day_of_year`. There is no date arithmetic, which keeps time zones and calendars out of the language. The system functions around the clock are in lesson 61.

## More that is there

A few more things exist that need a network, a file system, or a permission, so they have no example here:

- Files and sockets (lessons 37 and 42): `read_bytes(io, n)` reads a number of bytes, `open_file` takes a `FileMode`, `connect_tls` is `connect` over TLS with no way to turn the check off, `bind_udp` with `send_to` and `receive` handles datagrams, and `listen_unix` and `connect_unix` talk to another program on the same machine through a file path.
- Directories: `list_dir`, `file_info`, and `path_exists`, and `watch(path)`, which gives a channel of file changes.
- Databases (lesson 44): `transaction(conn, f)` commits when `f` returns `Ok` and rolls back on `Err`, `?` included.
- Permissions (lesson 61): a program says what it may touch with flags such as `--allow-read` and `--allow-connect`, and a manifest can fix them.
- Calling C (lesson 62): `moxie bindgen` writes foreign declarations from a C header.

The Spec has the rest, section by section.

## What to remember

- Arithmetic never fails silently: `checked_*` gives a `Result`, `wrapping_*` wraps, and `saturating_*` sticks at the limit.
- Float division by zero gives `INF` or `NAN`, so use `is_nan`, `is_inf`, and `is_finite`.
- `collect_errors` gives all the errors; `ok_or` turns an `Option` into a `Result`.
- A range is a value with `first`, `last`, and `step`.
- Use `seeded(n)` for reproducible random values and `random_bytes(n)` for secrets.

*In the Spec: [24. Prelude reference](../spec.html#s24)*

---

[← Moxie and moxie/gc side by side](60-the-two-dialects.html) · [Contents](./) · [Where to go next →](64-where-to-go-next.html)
