DOCS = {}
def d(name, text, ex=(), shown=()):
    DOCS[name] = (text, list(ex), list(shown))

d("identity", """Returns its argument unchanged. It is the "do nothing" function, handy as a default where a function is expected.

**Parameters**

- `x`: any value.

**Returns** `x`.""", ["identity(5)", 'List(1, 2) |> map(identity) |> collect()'])
d("const", """Makes a function that ignores its input and always gives the same value.

**Parameters**

- `x`: the value to give back.

**Returns** a function that takes any argument and returns `x`.""", ["const(7)(\"anything\")"])
d("flip", """Makes a version of a two-argument function that takes its arguments in the opposite order.

**Parameters**

- `f`: a function of two arguments.

**Returns** a function `g` with `g(b, a) == f(a, b)`.""", ["flip((a, b) -> a - b)(1, 10)"])
d("tap", """Runs a function on a value for its effect, such as printing, and then gives back the original value, so it can sit in the middle of a `|>` chain.

**Parameters**

- `x`: the value.
- `f`: the function to call with it; its result is ignored.

**Returns** `x`.""", ["tap(5, (x) -> x * 100)"])
d("fold_all", """Combines every item of a source with the type's own `combine`, starting from its `empty`. The item type must be a `Monoid`: a type with an identity and an associative way to combine two values. `String` joins and `List` appends; for numbers, wrap each in `Sum` (or `Product`, `Min`, `Max`), whose `value` field holds the result.

**Parameters**

- `xs`: a source of items of a `Monoid` type.

**Returns** the combined value; `empty` for no items.""", ['fold_all(List("a", "b", "c"))', "fold_all(List(Sum(1), Sum(2), Sum(3)))", "fold_all(List(List(1), List(2, 3)))"])
d("fold_map", """Turns each item into a `Monoid` value and combines the results. It is `map` followed by `fold_all` in one step.

**Parameters**

- `f`: a function from an item to a `Monoid` value.
- `xs`: the items.

**Returns** the combined value.""", ["fold_map((x) -> Sum(x * x), List(1, 2, 3))", 'fold_map((x) -> show(x), List(1, 2, 3))'])
d("hash", """A whole-number fingerprint of any value, equal for equal values. It is stable within a run and shouldn't be stored or relied on across versions; it is not a cryptographic hash.

**Parameters**

- `x`: any value with `==`.

**Returns** an `Int`.""", ['hash("a") == hash("a")', 'hash(List(1, 2)) == hash(List(1, 2))'])
d("index", """The position of an enum case in its declaration, counting from 0.

**Parameters**

- `x`: a value of an enum type.

**Returns** an `Int`.""", ["enum Color\n  Red\n  Green\n  Blue\nprintln(index(Color.Blue))"])
d("secret_eq", """Compares two `Secret` values in constant time, so the time taken doesn't reveal how much of them matched. It is the only way to compare secrets; `==` on a `Secret` is not allowed. The contents are never shown.

**Parameters**

- `a`, `b`: two `Secret`s of one type.

**Returns** a `Bool`.""", [], [("secret_eq(token_a, token_b)", "true or false, in time that does not depend on the contents")])

# ---------------------------------------------------------------- atoms
SW = "Atoms are changed with one call that reads and writes together, so two fibers can't lose each other's updates."
d("swap", """Changes an `Atom` by applying a function to its value, and stores the result. """ + SW + """ The function may run more than once if another fiber changes the atom meanwhile, so it should have no side effects.

**Parameters**

- `a`: the `Atom`.
- `f`: a function from the old value to the new one.

**Returns** the new value.""", ["a = Atom(1)\nprintln(swap(a, (x) -> x + 1))\nprintln(@a)"])
d("reset", """Replaces the value of an `Atom` outright.

**Parameters**

- `a`: the `Atom`.
- `v`: the new value.

**Returns** the new value.""", ["a = Atom(1)\nprintln(reset(a, 9))\nprintln(@a)"])
d("swap_vals", """Like `swap`, but returns both the old and the new value, so you can tell what you replaced.

**Parameters**

- `a`: the `Atom`.
- `f`: a function from the old value to the new one.

**Returns** a pair `(old, new)`.""", ["a = Atom(1)\nprintln(swap_vals(a, (x) -> x + 1))"])
d("reset_vals", """Like `reset`, but returns both the old and the new value.

**Parameters**

- `a`: the `Atom`.
- `v`: the new value.

**Returns** a pair `(old, new)`.""", ["a = Atom(1)\nprintln(reset_vals(a, 9))"])
d("try_swap", """Like `swap`, but if the atom has a validator (`Atom[T](v, valid: f)`) and the new value fails it, you get an `Err` and the atom is unchanged, where `swap` would abort.

**Parameters**

- `a`: the `Atom`.
- `f`: a function from the old value to the new one.

**Returns** `Ok(new value)`, or `Err` with code `OUT_OF_RANGE`.""", ["a = Atom(1)\nprintln(try_swap(a, (x) -> x + 1))"])
d("try_reset", """Like `reset`, but if the atom's validator rejects the new value you get an `Err` instead of an abort, and the atom is unchanged.

**Parameters**

- `a`: the `Atom`.
- `v`: the new value.

**Returns** `Ok(new value)`, or `Err` with code `OUT_OF_RANGE`.""", ["a = Atom(1)\nprintln(try_reset(a, 9))"])

# ---------------------------------------------------------------- channels, futures
d("read", """Takes the next value from a channel, or looks at a future. Reading a channel waits, letting other fibers run, until a value is there; `Err` with code `CLOSED` means it has been closed and drained, so a loop can stop. Reading a future never waits: it tells you the state, which is `Future.Pending`, `Future.Resolved(value)` or `Future.Rejected(error)`, and it can be asked again and again with the same answer once the future is complete.

**Parameters**

- `c`: a `ChanR[T]` (the reading end of a channel), or
- `f`: a `FutureR[T]`.

**Returns** for a channel, `Result[T, Error]`; for a future, its state.""", ["(r, w) = Chan[Int][2]()\nwrite(w, 5)\nprintln(read(r))"])
d("write", """Puts a value into a channel. If the channel's buffer is full, the writer waits until a reader makes room.

**Parameters**

- `w`: a `ChanW[T]` (the writing end of a channel).
- `x`: the value.

**Returns** `Ok(())`, or `Err` with code `CLOSED` if the channel was closed.""", ["(r, w) = Chan[Int][2]()\nprintln(write(w, 5))"])
d("close", """Closes a channel or a resource. Readers get what is already buffered and then `Err` with code `CLOSED`; further writes fail. Closing twice is harmless.

**Parameters**

- `x`: a channel end, or something that holds a resource such as a connection, listener or `Wire`.

**Returns** nothing.""", ["(r, w) = Chan[Int][2]()\nwrite(w, 5)\nclose(w)\nprintln(read(r))\nprintln(read(r))"])
d("resolve", """Completes a future with a value. Everyone who reads the future from then on sees `Future.Resolved(value)`. A future is completed only once, and `resolve` uses up the writing end, so a second call is a compile error.

**Parameters**

- `w`: a `FutureW[T]`.
- `v`: the value.

**Returns** nothing.""", ["(r, w) = Future[Int]()\nresolve(w, 5)\nprintln(read(r))"])
d("reject", """Completes a future with an error. Readers of the future from then on see `Future.Rejected(error)`. Like `resolve`, it uses up the writing end.

**Parameters**

- `w`: a `FutureW[T]`.
- `e`: the `Error`.

**Returns** nothing.""", ["(r, w) = Future[Int]()\nreject(w, Error(5, \"failed\"))\nprintln(read(r))"])
d("cancel", """Asks the work that holds a `Cancel` to stop. Work that is written to check its `Cancel` stops at the next check, and sleeping or waiting inside it is interrupted. Cancelling twice is harmless.

**Parameters**

- `c`: a `Cancel`.

**Returns** nothing.""", [], [("cancel(c)", "the work using `c` stops at its next check")])

# ---------------------------------------------------------------- timers
d("after", """Makes a `Timer`, a channel that receives one value after a delay. It is used with `select`, to wait for something but not forever.

**Parameters**

- `d`: how long to wait, as a `Duration` such as `50ms`.

**Returns** a `Timer`.""", ["t = after(10ms)\nprintln(read(t))"])
d("arm", """Restarts a `Timer` so that it fires once, after the given delay.

**Parameters**

- `t`: the `Timer`.
- `d`: the new delay.

**Returns** nothing.""", ["t = after(1000ms)\narm(t, 10ms)\nprintln(read(t))"])
d("arm_every", """Makes a `Timer` fire repeatedly, once every interval, until it is disarmed.

**Parameters**

- `t`: the `Timer`.
- `d`: the interval.

**Returns** nothing.""", ["t = after(1000ms)\narm_every(t, 5ms)\nread(t)\nread(t)\ndisarm(t)\nprintln(\"ticked twice\")"])
d("disarm", """Stops a `Timer` from firing. A timer that is not running is left as it is.

**Parameters**

- `t`: the `Timer`.

**Returns** nothing.""", ["t = after(1000ms)\ndisarm(t)\nprintln(\"disarmed\")"])
d("sleep", """Pauses the current fiber for a while. Other fibers keep running.

**Parameters**

- `d`: how long, as a `Duration` such as `100ms`.

**Returns** nothing.""", ["sleep(5ms)\nprintln(\"done\")"])
d("race", """Runs two functions at the same time and returns the answer of whichever finishes first. The loser is cancelled through its `Cancel`, so it should check it, and its result is thrown away.

**Parameters**

- `f`, `g`: functions that take a `Cancel` and return a value of one type.

**Returns** the value of the winner.""", ["fn slow(c Cancel) Int\n  sleep(500ms)\n  2\nprintln(race((c) -> 1, slow))"])
d("with_timeout", """Runs a function but gives up after a time limit. The function receives a `Cancel` that is triggered when time runs out.

**Parameters**

- `d`: the time limit.
- `f`: a function from a `Cancel` to a `Result`.

**Returns** the function's `Result`, or `Err` with code `TIMED_OUT` if time ran out first.""", ["with_timeout(500ms, (c) -> Ok(1))", "fn slow(c Cancel) Result[Int, Error]\n  sleep(300ms)\n  Ok(1)\nprintln(with_timeout(20ms, slow))"])
d("par_map", """Applies a function to every item, running up to `limit` calls at the same time, and returns the results in the original order, whatever order they finished in. The `limit` must be a constant number, because in moxie the fibers are counted before the program runs.

**Parameters**

- `f`: a function from an item to a result.
- `xs`: the items.
- `limit:`: how many calls may run at once.

**Returns** a `List` of results, in the order of `xs`.""", ["par_map((x) -> x * x, List(1, 2, 3, 4), limit: 2)"])
d("par_traverse", """Like `par_map`, but for a function that can fail. If a call fails, the others are cancelled and you get that error.

**Parameters**

- `f`: a function from an item to a `Result`.
- `xs`: the items.
- `limit:`: how many calls may run at once.

**Returns** `Ok(list of values)` in order, or the first `Err`.""", ["par_traverse((x) -> Ok(x + 1), List(1, 2, 3), limit: 2)"])
d("retry", """Calls a function that can fail, again and again until it succeeds or `n` tries have been used, waiting between tries.

**Parameters**

- `n`: the most tries to make.
- `delay`: the wait between tries.
- `f`: a function with no arguments that returns a `Result`.

**Returns** the first `Ok`, or the last `Err`.""", ["retry(3, 1ms, () -> Ok(\"ok\"))"])

# ---------------------------------------------------------------- time
d("now", """The current wall-clock time, as a `Duration` since 1970-01-01 00:00 UTC. It can jump when the clock is changed, so it is for stamping events and not for measuring how long something took; use `monotonic` for that. Reading the clock uses the system.

**Parameters** none.

**Returns** a `Duration`.""", [], [("now()", "1.7e9 seconds as a Duration; changes every call")])
d("monotonic", """A clock that only goes forward, for measuring elapsed time. Its zero is arbitrary; only differences between two readings mean anything.

**Parameters** none.

**Returns** a `Duration`.""", [], [("monotonic() - start", "the time that has passed since `start = monotonic()`")])
d("millis", """A `Duration` in whole milliseconds.

**Parameters**

- `d`: a `Duration`.

**Returns** an `Int`.""", ["millis(1500ms)", "millis(2s)"])
d("nanos", """A `Duration` in whole nanoseconds.

**Parameters**

- `d`: a `Duration`.

**Returns** an `Int`.""", ["nanos(2ms)"])
d("seconds", """A `Duration` in seconds, with a fraction.

**Parameters**

- `d`: a `Duration`.

**Returns** a `Double`.""", ["seconds(1500ms)", "seconds(2s)"])
d("weekday", """The day of the week of a date and time.

**Parameters**

- `t`: a `DateTime`.

**Returns** an `Int`, 1 for Monday up to 7 for Sunday.""", ["weekday(parse_iso(\"2026-11-23T10:00:00\") |> unwrap())", "weekday(parse_iso(\"2026-11-22T10:00:00\") |> unwrap())"])
d("day_of_year", """Which day of the year a date is, counting 1 January as 1.

**Parameters**

- `t`: a `DateTime`.

**Returns** an `Int`, 1 to 366.""", ["day_of_year(parse_iso(\"2026-11-23T10:00:00\") |> unwrap())"])
d("days_in_month", """How many days a month has, counting February in a leap year as 29.

**Parameters**

- `y`: the year.
- `m`: the month, 1 to 12.

**Returns** an `Int`.""", ["days_in_month(2026, 2)", "days_in_month(2028, 2)", "days_in_month(2026, 11)"])
d("iso", """Writes a date and time in the ISO 8601 form.

**Parameters**

- `t`: a `DateTime`.

**Returns** a `String` such as `2026-11-23T10:00:00`.""", ["iso(parse_iso(\"2026-11-23T10:00:00\") |> unwrap())"])
d("format_time", """Writes a date and time using a pattern. `%Y` year, `%m` month, `%d` day, `%H` hour, `%M` minute, `%S` second, `%A` the weekday name, `%B` the month name. With a `Locale`, names such as `%A` and `%B` are in that language.

**Parameters**

- `t`: a `DateTime`.
- `fmt`: the pattern.
- `loc` (optional): a `Locale`.

**Returns** a `String`.""", ['format_time(parse_iso("2026-11-23T10:00:00") |> unwrap(), "%d/%m/%Y %H:%M")', 'format_time(parse_iso("2026-11-23T10:00:00") |> unwrap(), "%A %d %B %Y")', 'format_time(parse_iso("2026-11-23T10:00:00") |> unwrap(), "%A %d %B %Y", Locale.de_de)'])
d("parse_iso", """Reads a date and time written in the ISO 8601 form.

**Parameters**

- `s`: the text.

**Returns** `Ok(DateTime)`, or `Err` if the text isn't a valid date and time.""", ['parse_iso("2026-11-23T10:00:00") |> map_ok((t) -> iso(t))', 'parse_iso("tomorrow") |> is_err()'])
d("parse_time", """Reads a date and time written in any pattern, with the same codes that `format_time` writes.

**Parameters**

- `s`: the text.
- `fmt`: the pattern.
- `loc` (optional): a `Locale`, for month and day names.

**Returns** `Ok(DateTime)`, or `Err` if the text doesn't match.""", ['parse_time("23/11/2026", "%d/%m/%Y") |> map_ok((t) -> iso(t))', 'parse_time("nonsense", "%d/%m/%Y") |> is_err()'])
d("to_instant", """Turns a `DateTime` into a point on the time line (a `Duration` since 1970 UTC). A date and time on its own is ambiguous, because "10:00" is a different moment in each zone, so you pass the zone it is in. Without one, UTC is assumed. A time that doesn't exist in that zone, or exists twice (when clocks change), is an `Err`.

**Parameters**

- `t`: a `DateTime`.
- `zone` (optional): a zone name such as `"Europe/Paris"`.

**Returns** `Ok(Duration)`, or `Err`.""", ['to_instant(parse_iso("1970-01-02T00:00:00") |> unwrap())', 'to_instant(parse_iso("2026-11-23T10:00:00") |> unwrap(), "Europe/Paris") |> map_ok((d) -> seconds(d))'])
d("to_utc", """The date and time, as the calendar and clock show it in UTC, for a point on the time line.

**Parameters**

- `d`: a `Duration` since 1970 UTC, such as from `now()`.

**Returns** a `DateTime`.""", ["iso(to_utc(86400s))"])
d("to_local", """The date and time in the computer's own time zone, for a point on the time line.

**Parameters**

- `d`: a `Duration` since 1970 UTC.

**Returns** a `DateTime`.""", [], [("to_local(now())", "the current local date and time")])
d("to_zone", """The date and time in a named zone, for a point on the time line.

**Parameters**

- `d`: a `Duration` since 1970 UTC.
- `zone`: a zone name such as `"Asia/Tokyo"`.

**Returns** `Ok(DateTime)`, or `Err` if the zone is unknown.""", ['to_zone(0s, "Asia/Tokyo") |> map_ok((t) -> iso(t))', 'to_zone(0s, "Nowhere/Land") |> is_err()'])
