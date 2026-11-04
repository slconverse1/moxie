---
layout: default
title: "Moxie Tutorial"
---
# MOXIE TUTORIAL: build a gradebook

This tutorial grows one small program, a gradebook, a step at a time. Each step adds a few lines to the same file and shows what it prints, so by the end you will have used values, functions, data, patterns, collections, errors, generics, concurrency, and tests. You don't need to know any functional programming. If you do, the notes will tell you where moxie differs from what you expect.

**To follow along,** save the code in a file called `gradebook.mxi`, adding each step's code to the end of the file, and run it with the reference interpreter (plain Python 3, nothing to install):

```
python3 -m moxie run gradebook.mxi
```

The output shown after each step is what the whole file prints at that point, so you can check your work. The Mixer's Guide and the Spec are the places to go when you want the full details.

## Step 1. Say hello

```moxie
class_name = "Moxie 101"
println("Welcome to $class_name")
```

```output
Welcome to Moxie 101
```

`class_name = "Moxie 101"` binds a name to a value. There is no `let` or `var`, and no type to write: the compiler works out that `class_name` is a `String`. A `$name` inside a string drops the value in, and `${...}` does the same for any expression, as in `"${score + 5}"`.

*Note for the curious.* Values in moxie never change. Writing `class_name = "Moxie 102"` later wouldn't alter the old string. It would point the name at a new one. That one rule is why so much of the language is simple.

## Step 2. A function that decides

```moxie
fn letter(score: Int) String:
  when score:
    >= 90 -> "A"
    >= 80 -> "B"
    >= 70 -> "C"
    _ -> "F"

println("${letter(95)} ${letter(83)} ${letter(41)}")
```

```output
Welcome to Moxie 101
A B F
```

Three things to notice:

- **The shape of a function.** `fn name(parameters) ReturnType:` then an indented block. The block's last line is its value, so there is no `return` to write. (You may write one, and a guard like `return x if n < 0` can be handy.)
- **Indentation is the structure.** Two spaces open a block, and there are no braces.
- **`when` picks the first arm that matches.** The patterns can be literals, ranges such as `80..=89`, or comparisons such as `>= 90`. The last arm, `_`, matches anything, and the compiler insists you have one when it can't tell that every value is covered. If you remove the `_` arm, the program won't run.

## Step 3. Data with names

```moxie
tuple Student deriving show, eq:
  name: String,
  score: Int

ada = Student(name: "Ada", score: 95)
bob = Student(name: "Bob", score: 83)
println("$ada")
curved = Student(...bob, score: bob.score + 5)
println("${curved.name} ${curved.score} ${bob == curved}")
```

```output
Welcome to Moxie 101
A B F
Student(name: "Ada", score: 95)
Bob 88 false
```

Moxie has no `struct` or `class`. A `tuple` is the record type: a named list of fields. `deriving show, eq` asks the compiler to write the code that prints a `Student` and compares two of them.

`Student(...bob, score: bob.score + 5)` is how you "change" a field. It builds a new `Student` that copies everything from `bob` and replaces `score`. The original `bob` is untouched, which is why `bob == curved` is `false`.

## Step 4. Many students

```moxie
roster = List(
  ada,
  bob,
  Student(name: "Cy", score: 71),
  Student(name: "Di", score: 58)
)
total = roster |> to_stream() |> map((s): s.score) |> sum()
println("average ${total / len(roster)}")
passing: List[Student][4] = roster
  |> to_stream()
  |> filter((s): s.score >= 60)
  |> collect()
for s in passing:
  println("${s.name}: ${s.score} ${letter(s.score)}")
```

```output
Welcome to Moxie 101
A B F
Student(name: "Ada", score: 95)
Bob 88 false
average 76
Ada: 95 A
Bob: 83 B
Cy: 71 C
```

The `|>` pipe feeds the value on its left into the call on its right, so a calculation reads from left to right, top to bottom. `to_stream()` turns a collection into a stream of elements, `map` and `filter` reshape it, and `sum` and `collect()` end it.

Two moxie-specific details:

- **Collections have a size.** `List[Student][4]` means "a list of at most four students." Moxie has no garbage collector and no heap, so every list is a fixed block, and `collect()` needs to be told which one you want. A list built from `List(...)` is sized for what you gave it.
- **No `total += s.score` in a loop.** Names are rebound at each pass, not accumulated, so a loop can't build up a sum. A stream ending in `sum()` or `reduce` is the idiom, and it is shorter anyway.

## Step 5. When things go wrong

```moxie
fn parse_score(text: String) Result[Int, Error]:
  n = read[Int](text)?
  if n < 0 or n > 100: fail(1, "score out of range") else: Ok(n)

fn make_student(name: String, text: String) Result[Student, Error]:
  score = parse_score(text)?
  Ok(Student(name: name, score: score))

for (name, text) in List(("Eve", "88"), ("Fay", "abc"), ("Gus", "140")):
  when make_student(name, text):
    Ok(s) -> println("added ${s.name} with ${s.score}")
    Err(e) -> println("skipped $name: ${e.message}")
```

```output
Welcome to Moxie 101
A B F
Student(name: "Ada", score: 95)
Bob 88 false
average 76
Ada: 95 A
Bob: 83 B
Cy: 71 C
added Eve with 88
skipped Fay: cannot read
skipped Gus: score out of range
```

Moxie has no exceptions and no `null`. A function that can fail says so in its type: `Result[Int, Error]` is either `Ok(value)` or `Err(error)`. `fail(1, "message")` makes the failing case, and `when` takes the result apart. You can't use the value without handling the failure, because the compiler won't let you.

The `?` is the shortcut. `read[Int](text)?` means: "if this failed, return the error to my caller right now. Otherwise, give me the number." It saves you from nesting a `when` inside a `when` at every step, which is what other languages call the pyramid of doom.

## Step 6. Code that works for any type

```moxie
fn best[T: Ordered](a: T, b: T) T:
  if a < b: b else: a

impl Ordered for Student:
  fn <(other: Student) Bool:
    score < other.score

println("${best(3, 9)} ${best("pear", "fig")} ${best(ada, bob).name}")
```

```output
Welcome to Moxie 101
A B F
Student(name: "Ada", score: 95)
Bob 88 false
average 76
Ada: 95 A
Bob: 83 B
Cy: 71 C
added Eve with 88
skipped Fay: cannot read
skipped Gus: score out of range
9 pear Ada
```

`best[T: Ordered]` is a generic function. The `T` stands for "some type," and `: Ordered` says what that type must be able to do: be compared with `<`. Numbers and strings can already do that, so `best(3, 9)` and `best("pear", "fig")` just work.

A `Student` can't be compared until you say how, and that is what the `impl Ordered for Student` block does: it defines `<` as "lower score." After that, `best(ada, bob)` compiles and picks Ada. Leave the `impl` out, and the compiler stops at the call and tells you that `Student` doesn't implement `Ordered`, instead of failing somewhere inside `best`.

The compiler builds one specialized copy of `best` for each type it's used with, so a generic function costs nothing extra at run time.

## Step 7. Doing several things at once

```moxie
fiber fn grader(s: Student, out: ChanW[Int]) Unit:
  _ = write(out, s.score)

rx, tx = Chan[Int][3]()
_ = run grader(ada, clone(tx))
_ = run grader(bob, clone(tx))
_ = run grader(Student(name: "Cy", score: 71), move tx)
points = read(rx).get_or(0) + read(rx).get_or(0) + read(rx).get_or(0)
println("points $points")
```

```output
Welcome to Moxie 101
A B F
Student(name: "Ada", score: 95)
Bob 88 false
average 76
Ada: 95 A
Bob: 83 B
Cy: 71 C
added Eve with 88
skipped Fay: cannot read
skipped Gus: score out of range
9 pear Ada
points 249
```

A **fiber** is a lightweight task. `run grader(...)` starts one, and the three fibers here each send a student's score down a **channel**. `Chan[Int][3]()` makes the channel (an `Int` per message, room for three waiting) and gives back its two ends: `rx` to read from and `tx` to write to. The main fiber reads three times, and `read` waits until a message is there.

A channel end belongs to one fiber at a time. `clone(tx)` makes another handle to the same channel for the first two graders, and `move tx` hands the last one over. (`_ =` acknowledges the `Result` that `run` returns, because starting a fiber can fail if too many are alive.) There are no locks here, and none are needed: only one fiber runs at any moment, and values never change.

## Step 8. Tests

```moxie
test "letter grades":
  assert_eq(letter(90), "A")
  assert_eq(letter(89), "B")
  assert_eq(letter(12), "F")
```

`test` blocks stay out of the way when you run the program normally. Run them with:

```
python3 -m moxie test gradebook.mxi
```

```output
ok    letter grades
1 passed, 0 failed
```

Each test runs in its own fiber, and a failed `assert_eq` stops that test with a message that shows both values.

## Step 9. Reading and saving

So far the roster was written into the program. A real gradebook reads it, and the same function can read it from anywhere, because the keyboard, a file, and a network connection are all an `Io`:

```moxie
fn parse_line(line: String) Result[Student, Error]:
  parts = split(line, ",")
  name = get(parts, 0)?
  text = get(parts, 1)?
  make_student(name, text)

fn report(input: Io) Result[Unit, Error]:
  for line in lines(input):
    when parse_line(line):
      Ok(s) -> println("${s.name}: ${s.score} ${letter(s.score)}")
      Err(e) -> eprintln("skipped '$line': ${e.message}")
  Ok(())

with_stdin("Ada,95\nBob,83\nEve,abc\nCy,71\n", fn (): report(stdin))?
write_file("roster.csv", "Di,58\nEd,77\n")?
f = open_file("roster.csv", ReadOnly)?
report(f)?
close(f)
```

```output
Ada: 95 A
Bob: 83 B
Cy: 71 C
Di: 58 F
Ed: 77 C
```

(This step prints only its own lines; the skipped line goes to standard error.) `report` never asks where its lines come from. In a real run you would call `report(stdin)` and start the program with `python3 -m moxie run gradebook.mxi < grades.csv`; here `with_stdin` plays the part of the keyboard so the example is complete. `lines(input)` is a stream of lines that ends at the end of the input, `open_file` returns a `Result` because a file may be missing, and `close(f)` gives the file back. Failures are ordinary values, so a missing `roster.csv` would be an `Err` with the code `NOT_FOUND`, not a crash.

If you want to be sure a program only touches what you expect, run it with `--allow-read=data`: any other read comes back as `Err` with the code `DENIED`.

## Where to go next

You have now used most of the language. Here is where each idea goes deeper:

- **Patterns** reach far past `>= 90`. You can take apart enums, lists, nested tuples, and dictionaries, add `if` guards, and pin a value with `^name`. The Guide's chapter 12 has an example of each.
- **Enums** (sum types) let you say "a `Shape` is a `Circle` or a `Rect`," and `when` then insists you handle every case.
- **Pipelines** have more stages: `scan`, `windows`, `chunks`, `group_by`, and more (chapter 13).
- **`for:` comprehensions** chain steps that each might fail, or that each yield several values (chapter 24).
- **Interfaces** (`interface`, `impl`) are moxie's version of typeclasses and traits, and the prelude gives you `Equatable`, `Ordered`, `Hashable`, `Show`, `Read`, `Addable`, and `Numeric` to build on.
- **Daemons, timers, `select`, and futures** are the rest of the concurrency story (chapters 16 and 17).
- **SQL** is checked against your schema when you write `sql(conn):` (chapter 22).
- **Input, files, sockets, permissions, and C libraries** are sections 20a to 20d of the Guide.

When you want a challenge, try these on your gradebook:

1. Add a `Grade` enum (`Pass`, `Fail`) and a function that returns one with a `when`.
2. Make `make_student` reject empty names with `fail`.
3. Add a second channel and have each grader also send the student's letter.
4. Write a test that checks `make_student("Zed", "abc")` is an `Err`.

Welcome to moxie!
