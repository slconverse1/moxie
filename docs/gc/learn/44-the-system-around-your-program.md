---
layout: default
dialect: gc
title: "The system around your program · Learning Guide moxie/gc"
---
<p><small>Your program and its machine</small></p>

# 61. The system around your program

A program lives inside a machine. This lesson covers what it is allowed to touch, how it tells time and makes random numbers, how it keeps secrets, how it reacts to Ctrl-C, how it runs other programs, and how it shows dates.

## Permissions

A program that wasn't given a permission can't use it. The permissions are:

| Permission | What it allows |
|---|---|
| `fs.read`, `fs.write` | files and directories, by path |
| `net.connect` | outgoing connections, by `host:port` |
| `net.listen` | listening on ports |
| `ffi` | native libraries |
| `process` | running other programs |
| `stdin`, `env` | reading standard input, reading the environment |

Printing to `stdout` and `stderr` and reading `args` are always allowed. Permissions are granted in the project's `Moxie.toml`:

```moxie
[permissions]
fs.read = ["data/"]
fs.write = ["out/"]
net.connect = ["example.com:443"]
stdin = true
```

or on the command line, which replaces the manifest:

```
$ moxie --allow-read=data --allow-write=out run report.mxi
```

With no `[permissions]` table and no flag, a program is unrestricted, as a script is. Any table or flag restricts it to what is granted, and `--deny-all` grants nothing.

A call outside a grant returns an `Err` with the code `DENIED`, with a message that names the call and the permission. A path that climbs out with `..` is refused too. With `--allow-read=data`, this program reads the first file and is refused the second:

```moxie
println(read_file("data/a.txt"))
println(read_file("other/b.txt"))
```

**Output:**

```
Ok("hi\n")
Err(Error(code: 10, message: "other/b.txt: fs.read is not permitted"))
```

The compiler also follows permissions through function calls, as it follows effects. If `main` can reach `read_file` and nothing grants a file permission, `moxie check` and `moxie run` stop with a compile error such as *`'read_file' needs fs.read or fs.write, which is not granted`*, before anything runs. The same analysis follows calls into imported packages. It checks the *kinds* and the libraries, not the paths, which depend on values and are checked when the call is made.

### Giving a package less

A package can be given less than the program. Add a table named for the package inside `[permissions]`:

```moxie
[permissions]
all = true

[permissions.packages.reader]
fs.read = ["data"]
```

Code written in `reader` can then read only under `data`, whatever the program grants. An empty table gives it nothing, and a package with no table gets what the program has. The rule follows where the code is *written*: a function the program hands to `reader` keeps the program's rights.

Granting `ffi` for convenience is a mistake: a native library runs with all the rights of the process, so permissions guard against mistakes in moxie code, not against hostile C.

## Time

Time is a `Duration`, written with a suffix: `ns`, `us`, `ms`, `s`, `m`, or `h`, as in `250ms` or `90m`. (For a day write `24h`; `d` already marks a Decimal.) A Duration is one count of nanoseconds, so `7s`, `5s + 2s`, and `7000ms` are equal, and they are the same key in a `Dict`.

`monotonic()` never goes back, so use it to *measure*. `now()` is the wall clock, as a `Duration` since 1970. A duration converts out with `nanos`, `millis`, and `seconds`:

```moxie
t0 = monotonic()
sleep(50ms)
elapsed = monotonic() - t0
println("slept at least 50ms: ${elapsed.millis() >= 50}")
println("it is after 2023: ${now().seconds() > 1.7e9}")
```
**Output:**

```
slept at least 50ms: true
it is after 2023: true
```

Don't read `now()` twice to time something: the clock can be set while you measure. `monotonic()` doesn't jump.

## Random numbers

`random()` and `random_int(r)` (which takes a range, as in `random_int(1..6)`) are for games and sampling. `random_bytes(n)` comes from the operating system's secure source, so use it for tokens and keys. `seeded(n)` gives a *reproducible* source that the generator functions from property tests (lesson 32) read:

```moxie
g = seeded(7)
h = seeded(7)
println(gen_int(g, 1, 6) == gen_int(h, 1, 6))
println(len(random_bytes(16)))
```
**Output:**

```
true
16
```

## Secrets

A password or token should be wrapped in a `Secret`, so that it can't reach a log by accident:

```moxie
token = secret(env("MOXIE_LESSON_TOKEN").get_or("none"))
println("using ${token}")
println(secret_eq(token, secret("none")))
```
**Output:**

```
using Secret(***)
true
```

Printing, interpolating, and `show` all give `Secret(***)`. `reveal(token)` is the one way to the real value, so each place it is used shows in the source. `==` on secrets is an error: compare with `secret_eq`, which takes the same time however many characters match. A `Secret[String]` is not a `String`, so a function that takes one can't be handed plain text by mistake.

## Exit and signals

`exit(code)` ends the program with a code from 0 to 255, from any fiber.

`signals()` gives a channel of `#interrupt`, `#terminate`, and `#hangup`, so a program can shut down cleanly when someone presses Ctrl-C. A program that has called `signals` no longer stops on Ctrl-C by itself, so it must read the channel. Here a `select` waits for either a signal or the work to finish:

```moxie
fiber fn work(done ChanW[Int]) Unit
  sleep(100ms)
  \write(done, 1)

rx = signals()
done_r, done_w = Chan[Int][1]()
go work(done_w)
select
  read(rx) -> exit(130)

  read(done_r) -> println("finished")
```
**Output:**

```
finished
```

## Where the program runs

`cwd()`, `home_dir()`, `temp_dir()`, `hostname()`, and `os_name()` describe where the program runs. `is_terminal(stdout)` and `terminal_size()` say whether a person is watching. `lookup_host(name)` resolves a name, and `make_temp_file(prefix)` makes a file in the temporary directory and returns its path. These calls count as *uses the system* for effects, so a `pure fn` can't call them.

## Running other programs

`run_command` runs a program to the end and gives back what it printed. There is no shell, so you pass the program's name and its arguments as a *list*, and nothing in them is ever interpreted:

```moxie
r = run_command("echo", List("hello", "world"))?
println("exit ${r.code}: ${r.stdout.trim()}")
```
**Output:**

```
exit 0: hello world
```

A program that runs and fails is still `Ok`, with the failure in `code`, so check it: `r.code ~= 0`. An `Err` is for a program that couldn't run at all, such as one that isn't installed (`NOT_FOUND`).

Options are named arguments: `stdin:` sends text to the program, `cwd:` picks its directory, `env:` replaces its environment, and `timeout:` kills it after a `Duration`.

```moxie
r = run_command("sort", stdin: "pear\napple\n", timeout: 5s)?
print(r.stdout)
```
**Output:**

```
apple
pear
```

For a program that talks over time, `spawn` starts it and gives you a `Child`. Its input and output are ordinary `Io` values, so the file and socket functions from lesson 37 work on them. Close the input when you're done writing, then wait:

```moxie
c = spawn("sort")?
tx = child_stdin(c)
println(tx, "pear")
println(tx, "apple")
close(tx)
println(read_all(child_stdout(c))?)
println(wait_child(c)?)
close(c)
```
**Output:**

```
apple
pear

0
```

Waiting parks only your fiber, so others keep running. A program needs the `process` permission, written `process = ["git", "sort"]` in `Moxie.toml` or `--allow-run=git,sort` on the command line, and the child gets only the environment your program could see.

Mistakes: building a command line as one string (there's no shell to split it, so pass a list), ignoring `r.code`, and forgetting to close the input before reading from a program that reads until end of file.

## Dates and times

`now()` is a moment. To show one to a person, turn it into a `DateTime`, a plain record of year, month, day, hour, minute, second, and nanosecond. `to_utc` gives UTC, `to_local` gives your computer's zone, and `to_zone` takes a zone name and returns a `Result`, since the name might not exist:

```moxie
t = 1700000000s
println(iso(to_utc(t)))
la = to_zone(t, "America/Los_Angeles")?
println(format_time(la, "%A, %B %e at %I:%M %p"))
```
**Output:**

```
2023-11-14T22:13:20
Tuesday, November 14 at 02:13 PM
```

Going back is `to_instant(dt, zone)`, which gives a `Result` because `DateTime(2026, 2, 30)` isn't a day. A `DateTime` has no zone of its own, so pass the zone when you convert one to a moment.

`parse_time` and `parse_iso` read text, and both return `Err` for text that doesn't fit or a date that doesn't exist:

```moxie
d = parse_time("04/11/2026 16:55", "%d/%m/%Y %H:%M")?
println(iso(d))
println(weekday(d))
println(parse_iso("2026-02-30"))
```
**Output:**

```
2026-11-04T16:55:00
3
Err(Error(code: 6, message: "parse_iso: February 2026 has no day 30"))
```

`weekday` counts Monday as 1, so 3 is Wednesday.

There is no date arithmetic on a `DateTime`. To add days, go through the moment, and remember that a day here is always 24 hours:

```moxie
d = DateTime(2026, 12, 30)
later = (to_instant(d)? + 3 * 24h).to_utc()
println(iso(later))
```
**Output:**

```
2027-01-02T00:00:00
```

All of these are pure except `to_local`, which depends on the computer it runs on. Mistakes: parsing a time with an offset such as `+02:00` with `parse_iso` (it refuses, since a `DateTime` has no zone), using `to_local` where a test needs the same answer everywhere, and adding a month by adding 30 days.

## Reading single keys

`read_line` waits for Enter. A menu, a game, or a pager wants each key as it is pressed, and for that you open the terminal in *raw mode*. This needs a real terminal, so it is shown but not run:

```moxie
init
  t = raw_terminal()?
  println("press keys; Escape quits")
  for true
    when read_key(t)?
      Typed(c) -> println("typed ${c}")
      Ctrl(c) -> println("ctrl-${c}")
      Up -> println("up")
      Down -> println("down")
      Fn(n) -> println("F${n}")
      Escape -> break
      else ()
  close(t)
```

`raw_terminal()` gives you a `Terminal`. Nothing is echoed and there is no line editing, so the program decides what to show. `read_key(t)` waits for one key and returns a `Key`: `Typed(c)` for a character, `Ctrl(c)`, `Alt(c)`, `Fn(n)`, and names such as `Enter`, `Backspace`, `Escape`, the arrows, `Home`, `End`, `PageUp`, and `PageDown`.

In raw mode Ctrl-C is just a key, so a program must choose to quit on it. Call `close(t)` when you're done; the terminal is put back even when the program ends early or aborts. `raw_terminal()` is an `Err` with the code `MISSING` when input isn't a terminal, and it needs the `stdin` permission.

## What to remember

- A program can use only the permissions it was granted; a refused call is an `Err` with code `DENIED`, and many are caught before running.
- `monotonic()` measures, `now()` tells the date, `random_bytes` is for secrets, `seeded(n)` is for repeatable tests.
- Wrap secrets in `Secret`; print and log freely.
- Run other programs with a list of arguments, never a command string; check `r.code`.
- A `DateTime` has no zone; convert through a moment to do arithmetic.

---

[← Contracts: requires, ensures, invariant](55-contracts.html) · [Contents](./) · [Calling C →](54-calling-c.html)
