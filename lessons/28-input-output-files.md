# Input, output, and files

A program that only prints is a calculator. This lesson is about talking to the outside world: the arguments a program is started with, its environment, standard input and output, and files and directories on disk.

## Arguments and the environment

`args` is an array of the command-line arguments (the words after the program's file name). `args(0)` aborts when there is no argument, so when an argument is optional use `get`, which returns a `Result`:

```moxie
when get(args, 0)
  Ok(first) -> println("first argument ${first}")
  Err(e) -> println("no arguments")
```
```output
no arguments
```

`env("NAME")` reads an environment variable. It returns a `Result`, since the variable may not be set, and `get_or` supplies a default:

```moxie
editor = env("MOXIE_LESSON_EDITOR").get_or("vi")
println("editor ${editor}")
```
```output
editor vi
```

There is no `set_env`. A program's environment is something it receives, not something it changes.

## Standard output and standard error

`println` and `print` write to standard output. `eprintln` and `eprint` write to standard error, which is where messages for the person running the program belong when standard output carries data:

```moxie
println("the answer")
eprintln("a warning, on stderr")
```
```output
the answer
```

`stdout`, `stderr`, and `stdin` are values, of type `Io`. Any function can take one as a parameter, and `println` accepts a stream as its first argument. This is how you write output code that is easy to test: the function does not care where its output goes.

```moxie
fn greet(out Io, name String) Unit
  println(out, "hello, ${name}")

greet(stdout, "mixer")
greet(stderr, "mixer")
```
```output
hello, mixer
```

## Reading input

`read_line()` reads one line, without its newline, and returns a `Result`. `read_all()` reads everything that is left. `stdin_lines()` is a stream of lines, so it goes straight into a pipeline.

The examples below set their input with a `stdin` directive; at a terminal, the input is whatever is typed.

```moxie
//! stdin: Ada
print("name? ")
name = read_line().get_or("nobody")
println("hello, ${name}")
```
```output
name? hello, Ada
```

Reading all the lines as a stream:

```moxie
//! stdin: 3
//! stdin: 4
//! stdin: 5
total = stdin_lines() |> map((s) -> read[Int](s).get_or(0)) |> reduce(0, _1 + _2)
println(total)
```
```output
12
```

When the input ends, `read_line()` does not crash; it returns an `Err` with the code `CLOSED`:

```moxie
when read_line()
  Ok(line) -> println("got ${line}")
  Err(e) -> println("end of input: ${e.message}")
```
```output
end of input: end of input
```

Input is UTF-8. Input that is not gives an `Err` with the code `BAD_ENCODING`.

All of these *park*: while a fiber waits for input, only that fiber is held up. Lesson 22 explains fibers; the point here is that waiting for a person to type does not freeze the rest of the program.

### Feeding a function its input

`with_stdin(text, f)` runs `f` with `text` as its input. It exists so that a test can drive code that reads:

```moxie
fn ask(question String) String
  print("${question} ")
  read_line().get_or("nobody")

asker = fn () String
  ask("name?")
answer = with_stdin("Ada\n", asker)
println("hi ${answer}")
```
```output
name? hi Ada
```

## Files

A file is an `Io` too, so code that reads lines does not care whether it was given a file, a socket, or standard input.

`write_file(path, text)` and `read_file(path)` handle a whole small file in one call. Both return a `Result`, so these examples use `?` to pass a failure up; see lesson 14.

```moxie
write_file("notes.txt", "one\ntwo\n")?
text = read_file("notes.txt")?
print(text)
println("${len(text)} bytes")
```
```output
one
two
8 bytes
```

For a larger file, or to add to one, open it. `open_file(path, mode)` takes a mode: `ReadOnly`, `Create` (start the file empty), `Append`, or `ReadWrite`. Whatever you open you must close.

```moxie
write_file("notes.txt", "one\ntwo\n")?
f = open_file("notes.txt", Append)?
println(f, "three")
close(f)

r = open_file("notes.txt", ReadOnly)?
letters = lines(r) |> map(len) |> reduce(0, _1 + _2)
close(r)
println("${letters} letters, ${len(read_file("notes.txt")?)} bytes")
```
```output
11 letters, 14 bytes
```

Writes to a file are buffered until you call `flush` or `close`. A file left open when the program ends is closed by the runtime, but close it yourself: an open file is a *resource* that one fiber owns (lesson 26 and the memory lesson come back to this).

Paths use `/` on every system.

### When it fails

A missing file, a refused permission, a failing disk: these are ordinary `Err` values, with the reserved codes `NOT_FOUND`, `DENIED`, and `IO_ERROR`:

```moxie
when read_file("missing.txt")
  Ok(t) -> println(t)
  Err(e) -> println("not found: ${e.code == NOT_FOUND}")
```
```output
not found: true
```

## Directories and paths

Functions for directories take `/`-separated paths and return a `Result`, because the system can refuse:

- `make_dir(path)` creates a directory and any missing parents; it is fine if it already exists.
- `list_dir(path)` gives the names inside, sorted, as an `Array[String]`.
- `file_info(path)` gives a record with `kind` (`"file"`, `"dir"`, or `"other"`) and `size`, plus `is_file()` and `is_dir()`.
- `path_exists(path)` gives `Ok(true)` or `Ok(false)`.
- `rename_path(from, to)` moves a file or directory.
- `remove_file(path)` and `remove_dir(path)` delete a file and an *empty* directory.

Five more work on the *text* of a path and touch nothing, so they cannot fail: `path_join`, `path_parent`, `path_name`, `path_stem`, and `path_ext`.

```moxie
make_dir("out/logs")?
write_file(path_join("out", "report.txt"), "done")?
write_file("out/logs/run.log", "ok")?
println(list_dir("out"))
for name in list_dir("out")?
  info = file_info(path_join("out", name))?
  println("${name}: ${info.kind}")
```
```output
Ok(Array("logs", "report.txt"))
logs: dir
report.txt: file
```

The path functions, on their own:

```moxie
p = "out/logs/run.log"
println(path_parent(p))
println(path_name(p))
println(path_stem(p))
println(path_ext(p))
println(path_join("out", "run.old"))
```
```output
out/logs
run.log
run
log
out/run.old
```

Moving and removing:

```moxie
make_dir("tmp_lesson")?
write_file("tmp_lesson/a.txt", "x")?
rename_path("tmp_lesson/a.txt", "tmp_lesson/b.txt")?
println(list_dir("tmp_lesson"))
remove_file("tmp_lesson/b.txt")?
remove_dir("tmp_lesson")?
println(path_exists("tmp_lesson"))
```
```output
Ok(Array("b.txt"))
Ok(false)
```

A name from `list_dir` is only a name, not a path: join it with its directory before you use it, as the example above does with `path_join`. `remove_file` refuses a directory, and `remove_dir` refuses one that is not empty; a missing path is `NOT_FOUND`.

## Permissions

Reading a file or directory needs the `fs.read` permission and changing one needs `fs.write`; the Spec has the details, and a later lesson shows how a program declares what it needs. A program that tries something it was not allowed to do gets the `DENIED` code, not a crash.

## What to remember

- `args` is an array; use `get(args, 0)` for an optional argument. `env("X")` is a `Result`.
- `println(out, ...)` writes to any `Io`; `eprintln` writes to standard error.
- `read_line()`, `read_all()`, and `stdin_lines()` read; end of input is an `Err` with code `CLOSED`.
- Files are `Io` values. Open them, close them, and expect an `Err`.
- Path functions on text never fail; functions that touch the disk always return a `Result`.
