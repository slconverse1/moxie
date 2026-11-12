---
layout: default
dialect: gc
title: "moxie/gc Mixer's Guide"
---
# MOXIE/GC MIXER'S GUIDE

These are compact examples, not a tutorial; a longer teaching Guide comes later. This is the Guide for moxie/gc, the garbage-collected dialect of moxie; no-GC moxie is the other dialect and has its own Guide. It is a full copy of the Mixer's Guide in which every passage that differs from no-GC moxie is marked **[gc]**; unmarked text is the same in both languages. The Moxie/gc Spec has the table of differences. Examples that need the collector can't be run by the reference interpreter, which implements no-GC moxie, so their outputs were worked out by hand. Outputs were recomputed by hand. Snippets continue from earlier ones: a name such as `add`, `half`, `Box`, `Point`, or `User` that isn't defined in a snippet comes from the nearest earlier chapter that defines it, and a snippet that follows another in the same section reuses its bindings. Indentation is shown with blank braille characters (two per level) so it survives copying.

**Chapter 1: Bindings, blocks, `if`, loops**

```
x = 5
x += 1
a, b = 1, 2
a, b = b, a
count = 0
count++
println("$x $a $b $count")
```

Output: `6 2 1 1`. A binding in a deeper block hides the name only inside that block (the compiler warns):

```
n = 1
if true
  n = 2
  println("inside $n")
println("outside $n")
```

Output: `inside 2`, then `outside 1`. Everything is an expression, so a block's value can be the binding. A `do` block is a scope that gives its last value:

```
area = do
  w = 4
  h = 5
  w * h
label = if area > 50
  "big"
else
  "small"
println("$label $area")
```

Output: `small 20`. `if` chains with `elif`, in block form or all on one line (a chain is all-inline or all-block):

```
score = 85
grade = if score >= 90 then "A" elif score >= 80 then "B" else "F"
n = 0
word = if n < 0
  "negative"
elif n == 0
  "zero"
else
  "positive"
println("$grade $word")
```

Output: `B zero`. Without a final `else`, every branch must be `Unit`. **Mistakes:** expecting `n = 2` to update the outer `n`, and an `if` with no `else` used for its value.

**1a. Early exit with `return`**

`return value` leaves the function at once (a bare `return` leaves a `Unit` function). It is the usual guard clause:

```
fn grade_of(score: Int) String
  if score < 0
    return "invalid"
  if score >= 90 then "A" else "B"
println("${grade_of(-1)} ${grade_of(95)} ${grade_of(70)}")
```

Output: `invalid A B`. A `Unit` statement can take a trailing `if` instead, which reads well for guard clauses and means exactly the same thing:

```
fn grade_of(score: Int) String
  return "invalid" if score < 0
  if score >= 90 then "A" else "B"
```

The output is the same. A trailing `if` has no `else` and can't follow a binding (`x = 5 if c` is an error), and there is no `unless` (write `if not cond`). `return` follows the same exit rules as `?`: `ref` parameters are copied out, and resources may move only on an exiting path. A `return` on the last line is redundant, and the compiler warns. In the entry file, before `daemon`, `return` (like `?` and let-else) ends the program early: with `()` it exits normally. `return` is not allowed in a `daemon` cycle, and `return` inside a fiber ends that fiber.

**1b. Loops, `break`, `continue`, labels**

`for x in xs` runs once per element, `while cond` tests each time, and `while` alone loops until a `break`. A loop is an expression, and its value comes from its exits:

```
xs = List(4, 8, 15, 16)
found = for x in xs
  if x > 10
    break(x)
else
  -1
println("$found")
```

Output: `15`. With `xs = List(1, 2)` the loop runs out, and `else` supplies `-1`. A bare `break` gives `()`, `break(value)` needs a matching `else`, and a loop with no `break` takes the `else` value or `()`. `continue` starts the next iteration with the top-level bindings as they stand:

```
for n in 1..=6
  if n % 2 == 1
    continue
  println("even $n")
```

Output: `even 2`, `even 4`, `even 6`. A label is written `#name` before a `for`, `while`, or `do`, and used as `break #name`, `break #name(value)`, or `continue #name`:

```
rows = List(List(1, 2), List(3, -1), List(5, 6))
#outer for row in rows
  for cell in row
    if cell < 0
      break #outer
    println("$cell")
```

Output: `1`, `2`, `3`. A `do` block can be labeled too, which gives an early exit with a value:

```
found = #search do
  for x in xs
    if x > 10
      break #search(x)
  -1
```

With `xs` as above, `found` is `15`. `break(outer)` is always a variable, and `break #outer` is always a label. A loop carries its bindings forward like a tail call, so a rebinding inside the body is seen by the next iteration but does not leave the loop (use `break(value)`, `else` (which sees the carried name, so `while j < n` with `j = j + 1` and `else j` returns the final `j`), a stream terminal such as `reduce`, or `gimme.1.name` to write the outer name). A name that is in scope when the loop begins, a parameter or a local, keeps its type: rebinding `n` as a String in the body when it was an Int is an error. **Mistakes:** `break outer` without the `#`, a label used across a function or lambda boundary, and `break(value)` with no `else`.

To skip the rest of the current item use `continue`; to skip to the next item of an outer loop use `continue #outer`:

```
rows = List(List(1, -2), List(3, -1), List(4))
#outer for row in rows
  for cell in row
    if cell < 0
      continue #outer
    println("$cell")
```

Output: `1`, `3`, `4`. Inside a `select`, a bare `break` leaves the select, so leaving a loop from there needs a label (`inbox` and `timeout` as in chapter 17):

```
#serve while
  select
    case n = read(inbox) ->
      if n < 0
        break #serve
      println("got $n")
    case read(timeout) ->
      break #serve
```

(a sketch, no output). A label cannot cross a function or lambda boundary, and `return` inside a lambda leaves that lambda, which is the moxie form of Kotlin's `return@forEach`:

```
clamp = (n: Int) ->
  if n < 0
    return 0
  n
println("${clamp(10)} ${clamp(20)} ${clamp(-5)}")
```

Output: `10 20 0`. There is no `forEach`: use a `for` loop with `continue`, and an unused label is a warning.

**1c. `gimme`: reaching outer bindings**

`gimme.N.name` reaches the binding of `name` that is `N` enclosing layers out. It skips the current block's own binding of the name and counts only the enclosing blocks that bind it. Reading:

```
n = 1
if true
  n = 2
  if true
    n = 3
    println("${n} ${gimme.1.n} ${gimme.2.n}")
```

Output: `3 2 1`. Writing updates the outer binding, which is how a nested block changes a name from outside (like Python's `nonlocal`):

```
total = 0
count = 0
score = 80
if score > 50
  gimme.1.total += score
  gimme.1.count += 1
println("$total $count")
```

Output: `80 1`. Without `gimme`, `total += score` would create a new `total` that disappears at the end of the block. When the block has its own binding of the name, `gimme` still reaches the outer one:

```
n = 1
if true
  n = 2
  gimme.1.n = 10
  println("${n} ${gimme.1.n}")
println("$n")
```

Output: `2 10`, then `10`. A loop is a place where plain rebinding does not leave: `total += score` in a loop body makes a new `total` for the next iteration, and the name outside the loop keeps its old value. `gimme` is how a loop body updates a name bound before the loop:

```
total = 0
count = 0
for score in List(70, 85, 90)
  gimme.1.total += score
  gimme.1.count += 1
println("$total $count")
```

Output: `245 3`. This is the direct way when a loop updates two or three names at once. When the loop computes one value, the more functional way is to let the value carry the state, with `reduce` (or `break(value)` with `else`), and no outer name is written at all:

```
total = List(70, 85, 90) |> to_stream() |> reduce(0, (acc, s) -> acc + s)
println(total)
```

Output: `245`. The rules: a write keeps the type; after an `if`, `when`, `select`, or `do` the outer name has the value from whichever path ran; **functions and closures are boundaries** (a closure copies what it captures), but a loop is not one for `gimme`; there is no `global`; and an outer resource name follows the move rules. **Mistakes:** `gimme.1.x = ...` when no enclosing block binds `x`, and `gimme` inside a function or closure for a name bound outside it.

**1d. Comments**

A `//` comment runs to the end of the line, and it is the one to use almost everywhere: on its own line above the code, or after it for a short note. Say why, not what: a comment that repeats the code is noise. `///` is for documentation; it sits directly above a declaration and `moxie doc` and the doctests read it (section on tooling). A `/* ... */` block comment nests, so it is the right tool for switching off a region of code that may already contain block comments:

```
// The total, with tax.
fn total(price: Int, tax: Int) Int
  price + tax  // tax is in cents
/* println("not run")
   /* nested comments are fine */
   println("also not run")
*/
println(total(100, 8))
```

Output: `108`. Use plain indentation for the lines of a block comment and not a column of `*`; `moxie fmt` moves a block comment as one unit and keeps its text exactly. A comment on its own line takes the indentation of the code it belongs to. **Mistakes:** forgetting to close a `/*` (the error points at the line where it opened), and leaving commented-out code in a file once it is no longer needed.

**Chapter 2: Numbers, text, keywords**

```
small: Int8 = 42
wide: Int32 = small
narrow: Int8 = cast[Int8](wide)
next = cast[Char](cast[UInt32]('A') + 1)
mode = #fast
wait = 5s + 500ms
flags = 0b1100 ^ 0b1010
left = 1 << 3
right = 256 >> 4
println("$next $mode $flags $left $right")
```

Output: `B #fast 6 8 16`. Double quotes make a `String`, single quotes make one `Char`. A string interpolates `$name`, `${expr}`, and `$err.code`, and `\$` is a literal dollar:

```
who = "moxie"
ch = 'x'
println("hi $who, ${1 + 2} \$5 $ch")
```

Output: `hi moxie, 3 $5 x`. A triple-quoted string ends its opening line, and the closing `"""` line sets the margin removed from every line:

```
poem = """
  roses
    "red" and $who
  """
println(poem)
```

Output: `roses`, then `  "red" and moxie`. The closing line's indentation is the margin, quotes need no escape, and the final newline is not included. **Mistakes:** `narrow: Int8 = wide` needs `cast`, `'ab'` (a Char is one scalar), a curly quote in source, and a line indented less than the closing `"""`.

**2a. Raw strings, bytes, and number literals**

A raw string treats `\` and `$` literally. Add `#` marks when it contains a quote:

```
path = r"C:\temp\new"
quote = r#"say "hi""#
println(path)
```

Output: `C:\temp\new`. Byte literals are for protocols: `b"GET /"` is an `Array[Byte]` with `len` 5, and `b'\x7F'` is one `Byte`. Only ASCII and `\xNN`, `\n`, `\t`, `\\` and the quote are allowed. Number literals take `_` separators, `0x`, `0o`, `0b`, and suffixes such as `i8`, `u32`, and `f`. A literal with an exponent (`1e3`) is a `Double`, and a literal that doesn't fit its type is a compile error:

```
println("${1_000_000 + 0xFF} ${0b101} ${1e3}")
```

Output: `1000255 5 1000.0`.

**2b. Format specs**

In `${expr:spec}`, the spec is `[[fill]align][sign][#][0][width][,][.precision][type]`, checked against the type at compile time:

```
price = 12.5
n = 255
name = "Ada"
println("${price:.2f}|${n:08b}|${n:#x}|${name:>6}|${1234567:,}")
```

Output: `12.50|11111111|0xff|   Ada|1,234,567`. Align is `<`, `>`, or `^` with an optional fill (`${name:*^7}` gives `**Ada**`), width counts characters, and the types are `d x X o b f e E %`. `${name:.2f}` on a string is a compile error. Widths and precisions are constants; for a computed width use `pad_left(s, width)` or `pad_right`. If the expression contains a colon (a `Dict` literal, say), parenthesize it first: `${(Dict("a": 1)):>5}`. An inline `if` has no colon, so `${if ok then "yes" else "no"}` needs no care. The type `n` uses the `Locale` found by `using`:

```
using locale = Locale.de_de
println("${1234567.891:.2n}")
```

Output: `1.234.567,89`. Without a `Locale` in scope, `n` is a compile error. `parse_number(text, locale)` reads numbers back and returns a `Result`.

A template that is written apart from its values uses `fmt`: `fmt("{:>8.2f} | {:<5}", price, name)` is `   12.50 | Ann  `. Each `{}` or `{:spec}` takes the next argument and uses the same specs as above, and `{{` and `}}` are literal braces. The template must be a string literal, so the compiler can check the number of fields and each spec against the arguments, and a mismatch is a compile error. For a template that comes from data, such as a message loaded from a file, use `try_fmt`, which takes any template and returns a `Result` (`Err` with `BAD_FORMAT` when the template or the arguments don't fit). Prefer interpolation when the text and the values sit together.

The same `Locale` names the days and months when you format a date: with the `de_de` above, `format_time(t, "%A, %d. %B %Y")` gives `Donnerstag, 05. November 2026`, and `%x` writes the date in the locale's order (`05.11.2026`). Pass a `Locale` as a third argument to override the one in scope, as in `format_time(t, "%x", Locale.fr_fr)`. `parse_time` reads the same names.

**2c. Overflow, division, floats, and big numbers**

Integer arithmetic aborts on overflow (a constant that overflows is a compile error), and division or modulo by zero aborts. The other behaviors are explicit:

```
a: Int8 = 100
b = wrapping_add(a, 100)
c = saturating_add(a, 100)
d = checked_add(a, 100)
println("$b $c ${is_err(d)} ${is_err(checked_div(7, 0))}")
```

Output: `-56 127 true true`. `cast[T]` aborts when the value doesn't fit, `wrap_to[T]` truncates, and `try_cast[T]` returns a `Result`. Floats follow IEEE, with no abort:

```
println("${is_inf(1.0 / 0.0)} ${is_nan(0.0 / 0.0)}")
```

Output: `true true`. `==` on floats gets a warning, and `finite(x)` returns a `Result`. **Bounded integers** state a range in the type, and a `when` that covers the range needs no `_`:

```
type alias Percent = Int[0..=100]
fn describe(p: Percent) String
  when p
    0 -> "empty"
    1..=99 -> "partial"
    100 -> "full"
a: Percent = 40
println(describe(a))
when try_cast[Percent](a + 70)
  Ok(p) -> println(describe(p))
  Err(e) -> println("out of range")
println(describe(100))
```

Output: `partial`, `out of range`, `full`. `BigInt[n]` (n bits, a multiple of 64) is stored inline, in the frame or array that holds it **[gc]**:

```
fn factorial(0, acc: BigInt[128]) BigInt[128] = acc
fn factorial(n, acc: BigInt[128]) BigInt[128] = factorial(n - 1, acc * n)
println("${factorial(25, 1)}")
```

Output: `15511210043330985984000000`. `Decimal[digits, scale]` is exact, and rounding is always explicit:

```
price: Decimal[10, 2] = 19.99d
total = price * 3
tax = round_to[2](total * 0.0825d, #half_even)
println("$total $tax ${total + tax}")
```

Output: `59.97 4.95 64.92`. A pure function with constant arguments runs at compile time where a constant is required, such as a size:

```
fn pow2(0, acc: Int) Int = acc
fn pow2(n, acc: Int) Int = pow2(n - 1, acc * 2)
limit = pow2(10, 1)
ages = Dict[String, Int][limit]()
println("$limit")
```

Output: `1024`. **Mistakes:** assigning a wider integer to a narrower type without `cast`, `b: Percent = 101`, using the `d` suffix for a Double (`d` means Decimal only), and a `Decimal` product you forgot to round.

**Chapter 3: Tuples, enums, `impl`**

```
tuple Point
  x: Float,
  y: Float
tuple Player
  id: Int,
  tag: String
p = Point(x: 1.5, y: 2.0)
q = Point(...p, y: 9.0)
hero = Player(id: 1, tag: "Ada")
println("${q(y)} ${hero.tag} ${p.x * 3}")
```

Output: `9.0 Ada 4.5`. A tuple holds any type; a tuple that holds a resource (a channel end, say) is a resource itself. A declared tuple can print, compare, and read itself with `deriving`:

```
tuple Product deriving show, eq, read
  name: String,
  price: Int
item = Product(name: "Mechanical Keyboard", price: 120)
other = Product(...item, price: 120)
println("$item")
println("${item == other}")
```

Output: `Product(name: "Mechanical Keyboard", price: 120)`, then `true`. Trailing fields can have defaults: any expression the compiler can evaluate at compile time, such as `4000` or `pow2(4, 1)` (from chapter 2c). Omit them by name, or write `UploadOptions()` when all have defaults. A spread supplies every field:

```
tuple UploadOptions
  host: String = "localhost",
  port: Int = 4000,
  retries: Int = 3
fn upload(file: String, opts: UploadOptions) Unit
  println("$file -> ${opts.host}:${opts.port} retries ${opts.retries}")
prod = UploadOptions(host: "production.server", retries: 5)
upload("payload.bin", prod)
upload("backup.tar", UploadOptions())
upload("logs.zip", UploadOptions(...prod, port: 8080))
```

Output: `payload.bin -> production.server:4000 retries 5`, then `backup.tar -> localhost:4000 retries 3`, then `logs.zip -> production.server:8080 retries 5`. An enum has several named cases, methods live in an `impl` block, and a `when` must cover every case:

```
enum Shape
  Circle(radius: Double),
  Rect(w: Double, h: Double),
  Empty
impl Shape
  fn area() Double
    when self
      Circle(r) -> 3.14159 * r * r
      Rect(w, h) -> w * h
      Empty -> 0.0
c = Shape.Circle(radius: 2.0)
r = Shape.Rect(w: 3.0, h: 4.0)
unit: Shape = Circle(radius: 1.0)
println("${c.area()} ${r.area()} ${unit.area()}")
```

Output: `12.56636 12.0 3.14159`. A bare case name works wherever only one enum has it (`unit` above); when two enums share a case name it is an error unless a declared type says which, and `do with` (below) opens one enum's cases for a block. Values shared by every case sit in a header:

```
enum Planet(mass: Double, radius: Double)
  MERCURY(mass: 3.303e23, radius: 2.4397e6),
  VENUS(mass: 4.869e24, radius: 6.0518e6),
  EARTH(mass: 5.976e24, radius: 6.3781e6)
impl Planet
  fn surface_gravity() Double
    6.673e-11 * mass / (radius * radius)
println("${len(Planet.values())} ${Planet.EARTH.index()}")
when Planet.value_of("VENUS")
  Ok(p) -> println("gravity ${p.surface_gravity()}")
  Err(e) -> println("no such planet")
```

Output: `3 2`, then `gravity 8.871391908774457`. **Mistakes:** `fn (Shape) area()` (methods live only in `impl` blocks), a bare `union` (use `enum` or `type union`), a default on a non-trailing field, and a `when` that misses a case.

**`do with`: opening an enum's cases.** `do with Light` makes the case names of `Light` bare inside its block, which is how two enums that share a case name are told apart. `do with A, B` opens several; a case name that both of them have is a compile error, and so is a case name that is also the name of a function or a type.

```
enum Light
  Red
  Green
enum Signal
  Red
  Stop
do with Light
  println(Red)
do with Signal
  println(Red)
  println(Stop)
```

Output: `Light.Red`, then `Signal.Red`, then `Signal.Stop`. A `do with` block is a `do` block, an expression with the value of its last line whose bound names stay inside, that also opens the cases. It rewrites the names in its block to the qualified ones, so patterns work too: inside `do with Shape`, `Circle(r) ->` means `Shape.Circle(r) ->`.

**Chapter 4: Type aliases, unions, data paths**

An alias is the same type under another name, and an opaque type is a new type over a representation, so mixing them up is an error:

```
type alias Meters = Double
type opaque Feet = Double
fn to_feet(m: Meters) Feet
  Feet(m * 3.28084)
println("${to_feet(100.0)}")
```

Output: `328.084`. A generic tuple infers its parameters:

```
tuple Container[T]
  item: T
a = Container(item: 5.59)
b = Container(item: "hello")
println("${a.item} ${b.item}")
```

Output: `5.59 hello`. A union type holds one of several types, converts in implicitly, and is taken apart with `when`:

```
type union Identifier = Int | String
fn describe(id: Identifier) String
  when id
    Int -> "numeric id $id"
    String -> "text id $id"
println(describe(42))
println(describe("Node-04"))
```

Output: `numeric id 42` then `text id Node-04`. A union may list another union, which is flattened: `type union Wide = Identifier | Bool` holds an `Int`, a `String`, or a `Bool`, and a member that appears twice after flattening is an error.

**Mixing types in a collection.** The elements of a `List`, `Set`, or `Array`, and the keys or values of a `Dict`, share one type, so `List(1, "a")` is a compile error: it is usually a typo, and moxie will not guess a type that fits both. To mix on purpose, name a union in the annotation. The elements convert into it, and a `when` takes them apart again. It works the same in both dialects, because a union has a fixed size.

```
xs: List[Int | String] = List(1, "a", 2)
for x in xs
  when x
    Int -> println("number $x")
    String -> println("text $x")
settings: Dict[String, Int | Bool] = Dict("retries": 3, "verbose": true)
println(len(settings))
```

Output: `number 1`, `text a`, `number 2`, then `2`. The union can also come from a parameter, a return type, or a tuple field (`fn take(xs: List[Int | String])`), and an unannotated `mixed = List(1, "a")` is the error.

A **data path** names a spot inside nested tuples. It is a plain function, so it can be stored, passed, and composed:

```
tuple Firm
  name: String,
  floor: Int
tuple User
  id: Int,
  firm: Firm
a = User(id: 1, firm: Firm(name: "Initech", floor: 2))
firm_name = /User/firm/name
b = replace(a, /User/firm/name, "Acme")
c = modify(a, /User/firm/name, (s) -> "$s Ltd")
name_of_user = /User/firm ~> /Firm/name
println("${firm_name(a)} ${a.id} ${(/User/firm/floor)(a)} ${firm_name(b)}")
println("${firm_name(c)} ${name_of_user(a)}")
```

Output: `Initech 1 2 Acme`, then `Initech Ltd Initech`. The first segment is a type name and the rest are fields. `replace` and `modify` need a literal path and rewrite the nested tuples for you (`a` is unchanged). A `/` starts a path only where an operand is expected, and a path has no spaces. **Mistakes:** `type alias` with defaults or `deriving` (aliases are transparent), assigning a `Meters` where a `Feet` is wanted, leaving an arm out of a union `when`, a union that repeats a member after flattening, a path through an enum payload or an array, and a path held in a variable passed to `replace`.

**Chapter 5: Collections**

**5a. Arrays and slices**

```
numbers: Array[Int] = (10, 20, 30, 40, 50)
middle = numbers(1..=3)
fixed = set(middle, 1, 99)
println("${numbers(0)} ${len(numbers)} ${middle(0)} ${fixed(1)} ${middle(1)}")
```

Output: `10 5 20 99 30`. The size `5` is taken from the value, and a slice **[gc]** is an ordinary value, which may share storage with its parent, whose indexes start at 0. With a constant range you can name its elements:

```
(a, b, c) = middle
println("$a $b $c")
```

Output: `20 30 40`. Array patterns work like list patterns:

```
when numbers
  Array(first, ...rest) -> println("first $first")
```

Output: `first 10`. To visit every index, an exclusive range ends at `len`:

```
for i in 0..len(numbers)
  println("$i: ${numbers(i)}")
```

Compound assignment works on elements and fields: `numbers(0) += 1`, `p.score += 10`. **Mistakes:** `numbers(7)` aborts the fiber (and a constant `7` is a compile error), so use `get(numbers, 7)`.

**5b. Lists**

```
base = List(10, 20, 30)
longer = base + 40
combined = longer + List(50, 60)
no_thirty = remove(combined, 30)
no_second = remove_at(combined, 1)
twice = List(1, 2) * 2
println("${len(combined)} ${len(no_thirty)} ${no_second(1)} ${len(twice)}")
```

Output: `6 5 30 4`. Lists are values: `list.push(4)` doesn't exist, so write `list += 4`. **[gc]** A list grows as needed and has no size in its type. A capacity is only an optional hint, as in `List[Int][100]()`, which reserves room and changes nothing else. `+`, `set`, and `remove` build a new version that shares most of its storage with the old one, so each costs O(log n) rather than a copy of the whole list.

**5c. Sets**

```
base = Set(1, 2, 3)
bigger = base + 4
same = base + 3
smaller = remove(bigger, 3)
println("${len(bigger)} ${len(same)} ${99 not in smaller}")
```

Output: `4 3 true`

**5d. Dicts**

```
ages = Dict[String, Int][10]()
ages(alice) = 30
ages(bob) = 25
ages(carol) = 41
ages(alice) = 31
when ages(alice)
  Ok(a) -> println("alice is $a")
  Err(e) -> println("no alice")
for (name, age) in ages
  println("$name is $age")
println("${get_or(ages, "dave", 0)} ${len(remove(ages, "bob"))}")
```

Output: `alice is 31`, then `alice is 31`, `bob is 25`, `carol is 41`, then `0 2`. **[gc]** The `[10]` is an optional capacity hint, and the Dict grows past it; leave it off if you have no estimate. A Dict keeps insertion order, and in `ages(alice)` the bareword is the literal key `"alice"`. To look up with a variable, write `ages($who)`. Keys can be anything key-eligible: integers, `Bool`, `Char`, strings, tuples, arrays (an n-gram window, say), lists, enums and unions of eligible types, and opaque types over them. Floats, Sets, Dicts, functions, resources, streams, and `any` values are not eligible. Tuples work like this:

```
cells = Dict[(Int, Int), String][8]()
cells((0, 0)) = "start"
cells((1, 2)) = "goal"
when cells((0, 0))
  Ok(v) -> println("$v ${len(cells)}")
  Err(e) -> println("missing")
```

Output: `start 2`. Values can be any storable type, including functions and closures **[gc]** (chapter 7). `put(d, k, v)` is the function form of `d(k) = v` and returns the updated Dict **[gc]**; it can't fail for lack of room. **Mistakes:** matching only `Ok`, and a Float key.

**Combining collections.** **[gc]** `union(a, b)` gives the elements of both sets, `merge(a, b)` gives the entries of both dicts (`b`'s value for a key in both), and `merge_with(f, a, b)` gives `f(a's value, b's value)` for such a key. Nothing can be full, so each returns the plain collection, as `put` does, and a program meant to run in both dialects handles the `Result` that no-GC moxie returns.

```
a = Set[Int][8](1, 2)
b = Set[Int][8](2, 3)
println(union(a, b))
d = Dict[String, Int][4]("a": 1, "b": 2)
e = Dict[String, Int][4]("b": 9, "c": 3)
println(merge(d, e))
println(merge_with((x, y) -> x + y, d, e))
```

Output: `Set(1, 2, 3)`, `Dict("a": 1, "b": 9, "c": 3)`, then `Dict("a": 1, "b": 11, "c": 3)`.

**5e. MultiArrays and their slices**

```
grid: MultiArray[Int][2, 3] = (
  10, 20, 30 ;
  40, 50, 60
)
row = grid(1, ..)
kept = grid(1..=1, ..)
col = grid(.., 1)
block = grid(0..=1, 1..=2)
println("${grid(1, 2)} ${row(2)} ${kept(0, 2)} ${col(0)} ${block(1, 1)}")
patched = set(row, 2, 99)
println("${patched(2)} ${grid(1, 2)}")
```

Output: `60 60 60 20 60`, then `99 60`. A bare number drops a dimension, a range keeps it, and `..` is the whole axis. In three dimensions:

```
voxels: MultiArray[Int][2, 2, 3] = (
  1, 2, 3 ; 4, 5, 6 ;;
  7, 8, 9 ; 10, 11, 12
)
layer = voxels(1, .., ..)
line = voxels(1, 0, ..)
println("${voxels(1, 0, 1)} ${layer(1, 2)} ${line(2)}")
```

Output: `8 12 9`. A function can take a grid of any shape with generic sizes:

```
fn row_sum[R, C](grid: MultiArray[Int][R, C], r: Int) Int
  grid(r, ..) |> to_stream() |> reduce(0, _1 + _2)
println("${row_sum(grid, 1)}")
```

Output: `150`. **Mistakes:** a literal with the wrong cell count, and leaving the shape off a MultiArray annotation (only an Array may omit its size). A slice can be returned **[gc]**.

**5f. Ranges and strings**

A `Range` is an opaque value holding a start, a limit, and a step, with accessors `start`, `limit`, and `step`. `1..=10` stands alone as a value. When both bounds are number literals the step is inferred, so `3..=1` counts down; with variables the step is 1 and a range whose start is past its limit is empty. A float range is only for tests:

```
println("${step(1..=10)} ${step(3..=1)} ${2.5 in 1.0..=5.0}")
for i in 3..=1
  println("$i")
```

Output: `1 -1 true`, then `3`, `2`, `1`. An infinite range uses `Range(1.., 1)`, and `take_while` ends it. A string slice **[gc]** is an ordinary `String` that may share storage with the original, indexed by byte offsets in UTF-8:

```
s = "Python"
println("${s(2..)} ${s(..3)} ${s(..=3)} ${s(..)}")
```

Output: `thon Pyt Pyth Python`. A cut inside a multi-byte character aborts (a compile error for constants). **[gc]** A slice can be kept and returned as it is. `len` counts bytes, `char_count` counts characters, and `chars` yields them:

```
t = "naïve"
println("${len(t)} ${char_count(t)} ${t |> chars() |> count()}")
```

Output: `6 5 5`. A `Char` is a Unicode scalar, not a grapheme cluster, and what a person sees as one character can be several scalars. `graphemes` yields one `String` per visible character and `grapheme_count` counts them:

```
s = "e\u{301}\u{1F1FA}\u{1F1F8}a"
println("${char_count(s)} ${grapheme_count(s)}")
for g in graphemes(s)
  println(len(g))
```

Output: `5 3`, then `3`, `8`, `1`. The accent is a second scalar, the flag is two, and each group is one cluster. **Mistakes:** using byte offsets as character positions, and iterating a float range.

**Chapter 6: Functions**

```
fn add(x: Int, y: Int) Int
  x + y
fn make_scaler(factor: Int) (Int) -> Int
  (n) -> n * factor
fn bump(ref counter: Int) Unit
  counter++
fn pick(use_it: Bool, lazy costly: Int) Int
  if use_it
    costly
  else
    0
scale = make_scaler(3)
n = 1
bump(ref n)
println("${add(2, 3)} ${scale(5)} $n ${pick(false, add(1, 1))}")
```

An anonymous function is a function with no name, written `(n) -> n * factor` (many languages call it a lambda, and this guide uses both words for the same thing). It is the missing name that makes it anonymous, not its size: the body can be one expression or a whole indented block, and the parameters and result can be typed. A function with no `fn` in front is a lambda, and a lambda is pure; with `fn` in front, `fn (line) = println(line)`, it is an anonymous function that may have effects. Bind a lambda with a typed name, `add: (Int, Int) -> Int = (a, b) -> a + b`, and the type supplies its parameter and result types. A lambda can't print, park, or touch a channel, a file, a socket, or SQL, and it can't call itself or be generic; for any of that, write `fn (...)` or declare a function with `fn`.

Output: `5 15 2 0`. Every function states its return type. A call may be positional, named, or positional followed by named (named arguments in any order, each parameter supplied once), trailing parameters can have defaults, and a list after the return type renames parameters inside the body:

```
fn transfer(source: Int, dest: Int, count: Int = 10) Int (src, dst, n)
  src - dst + n
print("${transfer(100, 40)} ${transfer(count: 5, dest: 40, source: 100)} ")
println("${transfer(100, dest: 40)}")
```

Output: `70 65 70`. A tuple can fill a parameter list:

```
fn sum_squares(x: Double, y: Double) Double
  x * x + y * y
pt = (x: 3.0, y: 4.0)
println("${sum_squares(pt)} ${sum_squares(...pt)}")
```

Output: `25.0 25.0`. A function type is just its parameter types, so `(Double, Double) -> Double` and `((Double, Double)) -> Double` are the same type, and a function of that type can be called as `f(3.0, 4.0)` or `f(pt)`. A tuple can't fill a `ref` parameter (write `ref n`), it fills a `lazy` parameter eagerly, and with a variadic function the tuple's leftover fields become the variadic arguments. A short function can use placeholders. A trailing lambda names its parameters after the call's arguments:

```
numbers = List(1, 2, 3)
doubled = numbers |> to_stream() |> map(_ * 2)
tripled = numbers |> to_stream() |> map()(x) -> x * 3
total = numbers |> to_stream() |> reduce(0)(acc, x) ->
  acc + x
println("$total")
```

Output: `6`. `map` takes the function first and the stream second. In `stream |> map()(x) -> x * 3` the pipe fills the stream slot, and the lambda fills the last parameter left, which is the function. These three calls are the same: `map((x) -> x * 3, stream)`, `stream |> map((x) -> x * 3)`, and `stream |> map()(x) -> x * 3`. Writing the stream out (`map(fn, stream)`) has no trailing form. A same-line lambda body runs to the end of the line, and a following `|>` line continues the whole pipeline.

When a stream carries tuples, a lambda with two or more parameters takes each tuple apart, and a parameter may be a pattern:

```
xs = List(1, 2, 3)
ys = List(4, 5, 6)
dot = zip(xs, ys) |> map()(x, y) -> x * y
  |> reduce(0, _1 + _2)
named = (name: "Ada", age: 36)
show = ((name: n, age: a)) -> "$n is $a"
println("$dot ${show(named)}")
```

Output: `32 Ada is 36`. A lambda built and called in the same place goes in parentheses, followed by the arguments:

```
double = ((x: Int) -> x * 2)(21)
println("$double")
```

Output: `42`. A variadic parameter takes any number of trailing arguments. **[gc]** Inside the function it is an ordinary `List[Int]`, and the function is compiled once, not once per argument count. Spread any array or list, whatever its length, or name it in a named call:

```
fn total(base: Int, numbers: ...Int) Int
  numbers |> to_stream() |> reduce(base, _1 + _2)
values = Array(10, 20, 30)
println("${total(100, 10, 20, 30)} ${total(100, ...values)} ${total(100)}")
```

Output: `160 160 100`. A **contextual parameter** is filled from the surrounding scope, and a caller may override it:

```
fn greet(msg: String, using who: String) Unit
  println("$who: $msg")
using who = "ada"
greet("hello", using)
greet("hi", "bob")
```

Output: `ada: hello`, then `bob: hi`. A `using` value can't be a channel end, a timer, or a file, because a callee could read or close it out of sight; an `Atom` is fine, so a shared counter can be injected the same way (`fn bump(using hits: Atom[Int])`).

Scala's `summon[T]` fetches the contextual value of type `T` from the scope, which it needs because a parameter written `(using Config)` has no name. Moxie has no `summon`, and every `using` parameter has a name, so a function that wants the value uses the name, and a call that writes `using` passes it along:

```
tuple Config
  url: String
fn connect(using cfg: Config) String
  "connecting to ${cfg.url}"
fn retry(attempts: Int, using cfg: Config) String
  connect(using)
using c = Config(url: "example.com")
println(retry(2, using))
println(connect(using))
```

Output: `connecting to example.com`, then `connecting to example.com`. `retry` hands its `cfg` on to `connect` by writing `using`, which finds the value of the right type. The other use of `summon` in Scala, getting the instance behind a bound like `[T: Ordering]`, has no counterpart either, because in moxie a type does not hand you an instance. Its `impl` supplies methods that you call on a value of the bounded type, `a.combine(b)`, or on the type itself, `T.empty()`, as `mconcat` does in chapter 8d. A missing or ambiguous `using` value is a compile error, so there is no "which instance did the compiler pick" to ask about.

A `todo` stands in for any expression you haven't written yet. The compiler warns and lists it, and running it aborts the fiber:

```
fn later(x: Int) Int
  todo "finish later"
```

**Mistakes:** `bump(n)` without `ref`, a tuple spread into a `ref` parameter, `transfer(100, source: 5)` (a parameter supplied twice), a function with no return type or an untyped parameter, `fn f(x: Int) Unit` ending in `x + 1`, a variadic with a default, spreading a `List` of unknown length, and a trailing lambda on a call that writes the stream out.

**6a. Generics**

A generic function lists type and size parameters in brackets. The compiler fills them in from the arguments and builds one specialized copy per use:

```
fn swap_pair[A, B](p: (A, B)) (B, A)
  (p(1), p(0))
s = swap_pair((1, "one"))
println("${s(0)} ${s(1)}")
```

Output: `one 1`. Inference runs in argument order, so a literal takes its types from what is already known:

```
fn apply_twice[T](x: T, f: (T) -> T) T
  f(f(x))
println("${apply_twice(3, (n) -> n * 2)} ${apply_twice(5, (n) -> n + 8)}")
```

Output: `12 21`. A size parameter is a number that sizes a collection, and it can be read as an `Int`. A `where` clause limits the sizes allowed:

```
fn sum_all[N](a: Array[Int][N]) Int
  a |> to_stream() |> reduce(0, _1 + _2)
fn size_of[N](a: Array[Int][N]) Int
  N
fn dot[N](a: Array[Int][N], b: Array[Int][N]) Int
  zip(a, b) |> map()(x, y) -> x * y
  |> reduce(0, _1 + _2)
fn first_of[T, N where N > 0](a: Array[T][N]) T
  a(0)
x: Array[Int] = (1, 2, 3)
y: Array[Int] = (1, 2, 3, 4, 5)
println("${sum_all(x)} ${sum_all(y)} ${dot(x, x)} ${size_of(y)} ${first_of(x)}")
```

Output: `6 15 14 5 1`. A call with an empty array to `first_of` is a compile error: "`first_of` requires `N > 0`, but `N` is 0 here". A bound limits a parameter to types with an `impl`, and a bare interface name is shorthand for a bounded parameter:

```
fn bigger[T: Ordered](a: T, b: T) T
  if a < b then b else a
println("${bigger(3, 9)} ${bigger("pear", "apple")}")
```

Output: `9 pear`. A parameter may have several bounds, joined with `+`:

```
fn show_max[T: Ordered + Equatable](a: T, b: T) String
  if a == b then "same" else "max is ${if a < b then b else a}"
println("${show_max(3, 9)} ${show_max(4, 4)}")
```

Output: `max is 9 same`. When nothing in the arguments fixes a parameter, write all of them: `read[Point](text)`, `cast[Int8](x)`, `Atom[Int](0)`, `Pair[Int, Int](1, 2)`, or use `_` for the ones the arguments can fix, as in `read[_, Int](text)`. A generic function used as a value needs its parameters fixed, either by writing them (`f = swap_pair[Int, String]`) or by an expected type (`g: (Int) -> Int = identity`). Parameters can range over type constructors too (`F[_]`, chapter 8d). **Mistakes:** `dot(x, y)` (sizes `3` and `5` don't match), a bound the type doesn't implement, passing only some of the explicit parameters, and `f = swap_pair` without parameters.

A type parameter can also stand for a whole argument list. A function type is its parameter types in order, so `(A) -> R` matches `(Int, Int) -> Int` with `A` as `(Int, Int)`, and `(String) -> String` with `A` as `String`. One definition then works for every number of arguments:

```
fn add(x: Int, y: Int) Int
  x + y
fn shout(s: String) String
  "${s}!"
fn call_with[A, R](f: (A) -> R, args: A) R
  f(args)
fn twice[A](f: (A) -> A, args: A) A
  f(f(args))
print("${call_with(add, (3, 4))} ${call_with(shout, "hi")} ")
println("${twice(shout, "yo")}")
```

Output: `7 hi! yo!!`. Field names are ignored when `A` is matched against a function type. A function with a `ref`, `lazy`, `using`, or variadic parameter doesn't match `(A) -> R`, because those modifiers are part of its type. Moxie has no way to take a tuple type apart or join two of them, so a wrapper can pass an argument list along but can't add or remove an argument. **Mistakes:** passing a `ref` function to `call_with`, and a wrapper that tries to split `A` into a first argument and the rest.

The prelude has bounds for the things generic code most often needs: `Equatable`, `Ordered`, `Hashable`, `Show`, `Read`, `Addable`, and `Numeric`. `Numeric` adds `-`, `*`, `/`, and `one` to `Addable`, and a static member is reached through the parameter (`T.one()`, `T.read(text)`):

```
tuple Pixel deriving show, eq, hash
  x: Int,
  y: Int
fn total[T: Numeric](xs: Array[T][3]) T
  xs(0) + xs(1) * xs(2)
fn unit_of[T: Numeric](x: T) T
  T.one()
fn parse[T: Read](text: String) Result[T, Error]
  T.read(text)
fn label[T: Show + Hashable](x: T) String
  "${x.show()} ${x.hash() == x.hash()}"
print("${total(Array(1, 2, 3))} ${total(Array(1.5, 2.0, 3.0))} ${unit_of(7)} ")
println("${unit_of(2.5)}")
println("${parse[Int]("42")} ${parse[Bool]("true")}")
println(label(Pixel(x: 1, y: 2)))
print("${hash(Pixel(x: 1, y: 2)) == hash(Pixel(x: 1, y: 2))} ")
println("${hash(Pixel(x: 1, y: 2)) == hash(Pixel(x: 2, y: 1))}")
```

Output: `7 7.5 1 1.0`, then `Ok(42) Ok(true)`, then `Pixel(x: 1, y: 2) true`, then `true false`. Numbers, `String`, and `Char` implement the bounds that make sense for them (`String` is `Addable`, with `""` as its zero, but not `Numeric`), and a declared type joins with `deriving` (`show`, `eq`, `ord`, `read`, `hash`) or an `impl`. `Hashable` can only be derived, and `deriving hash` needs `eq` in the same header, so equal values always have equal hashes. A type is a Dict key or Set element only when it is `Hashable`. **Mistakes:** `deriving hash` without `eq`, a hand-written `impl Hashable`, and passing a `String` where a `Numeric` is required.

**6b. Passing arguments: value, name, need, reference**

```
fn costly() Int
  println("computing")
  10
fn by_value(x: Int) Int
  x + x
fn by_name(lazy x: Int) Int
  x + x
fn by_need(lazy x: Int) Int
  once = x
  once + once
fn maybe(use_it: Bool, lazy x: Int) Int
  if use_it then x else 0
fn by_ref(ref n: Int) Int
  n += 5
  n * 2
fn by_copy(n: Int) Int
  n += 5
  n * 2
println("value: ${by_value(costly())}")
println("name: ${by_name(costly())}")
println("need: ${by_need(costly())}")
println("skipped: ${maybe(false, costly())}")
n = 1
r = by_ref(ref n)
m = 1
c = by_copy(m)
println("ref: $r $n")
println("copy: $c $m")
```

Output, in order:
- `computing`, then `value: 20`: by value evaluates the argument once, before the call.
- `computing`, `computing`, then `name: 20`: a `lazy` parameter re-runs its argument on every read.
- `computing`, then `need: 20`: nothing is cached for you. Call by need is the recipe above, where you bind the `lazy` value once.
- `skipped: 0`, with no `computing`: a lazy argument that is never read is never evaluated.
- `ref: 12 6`: `by_ref` rebinds the caller's `n` to 6 and also returns 12.
- `copy: 12 1`: `by_copy` changed only its own copy.

`ref` is copy-in and copy-out. Both sides say `ref` (`ref n` at the call, `counter: ref n` in a named call), and the argument is a bare name. Updating a tuple looks the same:

```
tuple Player
  name: String,
  score: Int,
  level: Int
fn level_up(ref p: Player) Unit
  p.level += 1
  p.score = 0
fn add_points(ref p: Player, points: Int) Int
  p = Player(...p, score: p.score + points)
  p.score
hero = Player(name: "Ada", score: 40, level: 1)
level_up(ref hero)
total = add_points(ref hero, 10)
println("${hero.name} ${hero.level} ${hero.score} $total")
```

Output: `Ada 2 10 10`. `p.level = ...` is sugar for rebuilding `p`, and on return the final `p` is rebound to `hero`. The caller's `hero` is untouched while the function runs, and `move` is not involved for plain data. **What can be passed by `ref`:** numbers, `Bool`, `Char`, tuples, enums, unions, collections (copied at their fixed capacity), `static` strings, `String[n]`, plain functions, and resources with tuples that contain them (moved in and moved out). **Not:** views, streams, and runtime-built strings. A fiber can't receive `ref`, a `ref` parameter that is never rebound gets a warning (unless an interface requires it), and a copy-out happens on every return path including `?`, but not after an abort. **Mistakes:** `by_ref(n)` ("parameter `n` is `ref`; write `ref n`"), `by_copy(ref m)`, `ref hero.level` (not a bare name), and passing a large read-only table by `ref` instead of normally.

**Chapter 7: Closures and currying**

A function literal may use the locals around it. **[gc]** Captured values are shared, which is safe because values never change, and any value can be captured except a one-owner resource:

```
factor = 5
scale = (n: Int) -> n * factor
fn make_adder(k: Int) (Int) -> Int
  (n) -> n + k
add_n = make_adder(10)
println("${scale(6)} ${add_n(5)}")
```

Output: `30 15`. The prelude has `curry(f)`, which works for a function of any number of parameters, and pipelines and closures cover the rest. The compiler checks `curry` and `uncurry` when it can see the function: `curry` of a function with fewer than two parameters, or with a `ref`, `lazy`, `using`, or variadic parameter, `uncurry[1]`, and a call such as `curry(add)(1, 2)` (which should be `curry(add)(1)(2)`) are compile errors. These five all give 100:

```
curried = curry(add)
add40 = (y: Int) -> add(40, y)
print("${add(40, 60)} ${curried(40)(60)} ${add40(60)} ${60 |> add(40, &)} ")
println("${((x: Int, y: Int) -> x + y)(40, 60)}")
```

Output: `100 100 100 100 100`.

A call with a `_` where an argument goes is a **partial call**, which is a function literal. The parameter types come from the callee's signature:

```
fn log(level: String, message: String) Unit
  println("[$level] $message")
fn log_error = log("ERROR", _)
fn log_info = log("INFO", _)
handlers = Dict[String, (String) -> Unit]()
handlers(info) = log_info
handlers(error) = log_error
fn dispatch(
  table: Dict[String, (String) -> Unit],
  kind: String,
  msg: String
) Unit
  when table($kind)
    Ok(h) -> h(msg)
    Err(e) -> println("unknown handler")
dispatch(handlers, "info", "Application started.")
dispatch(handlers, "error", "Database connection timed out!")
```

Output: `[INFO] Application started.` then `[ERROR] Database connection timed out!`. `fn log_error = log("ERROR", _)` declares a named function. **[gc]** Every function and closure with the signature `(String) -> Unit` has that one type, so these can sit in a Dict whatever they capture. Numbered placeholders give a multi-argument literal (`connect("localhost", _1, _2)`), names work (`log(level: "DEBUG", message: _)`), and a binding form `warn = log(prefix, _)` captures a runtime `prefix`, giving a closure **[gc]** that you can pass, return, or store. A call that simply leaves an argument out, `log("ERROR")`, is still an error.

Functions compose with `~>` (left to right) and `<~` (right to left):

```
fn inc(x: Int) Int = x + 1
fn twice(x: Int) Int = x * 2
print("${(inc ~> twice)(5)} ${(twice <~ inc)(5)} ${(twice ~> inc)(5)} ")
println("${5 |> (inc ~> twice)()}")
```

Output: `12 12 11 12`. A tuple field of function type is called like a method:

```
tuple Op
  apply: (Int) -> Int
op = Op(apply: (n) -> n * 2)
println("${op.apply(21)}")
```

Output: `42`. A Dict can hold functions **[gc]** and closures alike, which makes a dispatch table:

```
fn sub(x: Int, y: Int) Int = x - y
fn mul(x: Int, y: Int) Int = x * y
ops = Dict[String, (Int, Int) -> Int]()
ops(plus) = add
ops(minus) = sub
ops(times) = mul
fn run_op(
  table: Dict[String, (Int, Int) -> Int],
  name: String,
  a: Int,
  b: Int
) Unit
  when table($name)
    Ok(f) -> println("$name: ${f(a, b)}")
    Err(e) -> println("unknown operation")
run_op(ops, "times", 6, 7)
run_op(ops, "power", 2, 3)
run_op(ops, "plus", 4, 6)
run_op(ops, "minus", 10, 4)
run_op(ops, "times", 2, 8)
```

Output: `times: 42`, `unknown operation`, `plus: 10`, `minus: 6`, `times: 16`. **Mistakes:** `fn warn = log(prefix, _)` with a runtime `prefix` (use the binding form), `log("ERROR")` with no placeholder, `curry(+)` (operators aren't values), and expecting a function to cache its results for you (chapter 14). **[gc]** Because a closure can go anywhere, the next example, which no-GC moxie rejects, is fine:

```
fn pick(flag: Bool, k: Int) (Int) -> Int
  when flag
    true -> (n) -> n + k
    false -> (n) -> n * k
fns = List(pick(true, 3), pick(false, 3))
println("${fns(0)(10)} ${fns(1)(10)}")
```

Output: `13 30`. The two branches return different closures, and they sit side by side in a `List[(Int) -> Int]`.

**Chapter 8: `impl` blocks and interfaces**

```
interface Speaker[T]
  fn speak() String,
  fn update(new_value: T) Self
tuple Dog
  name: String
tuple Robot
  serial: Int
impl Speaker[String] for Dog
  fn speak() String
    "Woof! My name is ${name}"
  fn update(new_name: String) Dog
    Self(..., name: new_name)
impl Speaker[Int] for Robot
  fn speak() String
    "Beep Boep! Serial count is ${serial}"
  fn update(new_serial: Int) Robot
    Self(..., serial: new_serial)
fn make_them_speak(item: Speaker) Unit
  println(item.speak())
fn update_speaker[T, S: Speaker[T]](item: S, new_value: T) S
  item.update(new_value)
my_dog = Dog(name: "Rover")
my_robot = Robot(serial: 101)
make_them_speak(my_dog)
make_them_speak(my_robot)
s1 = update_speaker(my_dog, "Max")
s2 = update_speaker(my_robot, 500)
make_them_speak(s1)
make_them_speak(s2)
```

Output: `Woof! My name is Rover`, `Beep Boep! Serial count is 101`, `Woof! My name is Max`, `Beep Boep! Serial count is 500`. All methods live in `impl` blocks. An array holds one concrete type, so a mixed array uses a union type, and the shared call needs no `when`:

```
type union Entity = Dog | Robot
crowd: Array[Entity] = (Dog(name: "Rex"), Robot(serial: 7))
for e in crowd
  println(e.speak())
```

Output: `Woof! My name is Rex`, then `Beep Boep! Serial count is 7`. An inherent block adds your own methods. A `ref` receiver updates its receiver with bare field names:

```
tuple Counter
  count: Int,
  label: String
impl Counter
  fn (ref Self) increment() Unit
    count += 1
  fn incremented() Counter
    Self(..., count: count + 1)
tally = Counter(count: 0, label: "hits")
ref tally.increment()
next = tally.incremented()
println("${tally.count} ${next.count}")
```

Output: `1 2`. An interface says which methods change their receiver, and a generic function takes the value through a `ref` parameter:

```
interface ProfileManager
  fn age() Int,
  fn (ref Self) set_age(new_age: Int) Unit
tuple Profile
  years: Int
impl ProfileManager for Profile
  fn age() Int
    years
  fn (ref Self) set_age(new_age: Int) Unit
    years = new_age
fn birthday[P: ProfileManager](ref p: P) Unit
  ref p.set_age(p.age() + 1)
me = Profile(years: 30)
birthday(ref me)
println("${me.age()}")
```

Output: `31`. A package that doesn't own `Int` can still add plain functions with an extension block, which never satisfies an interface. An alias gives a method a second name:

```
impl Int
  fn double() Int
    self * 2
impl Counter
  fn bump = incremented
println("${21.double()} ${tally.bump().count}")
```

Output: `42 2`. **Mistakes:** the old `fn (Dog) speak()` form, an `impl` of someone else's interface for someone else's type, an interface `impl` with an extra function (put extras in an inherent block), two impls that give one name different bodies (the call is ambiguous, so write `Speaker.speak(x)`), calling `update` through a union (its arguments differ by member, so use a `when`), and `tally.increment()` without `ref`.

**8a. Receiver blocks**

A block can run with a value as its receiver, so its fields are in scope without the object name. `x.do` gives the block's value, and `x.update` builds a changed copy with `field: value` lines (`=` always means a binding, so it isn't used here):

```
tuple Limits
  retries: Int,
  timeout: Int
tuple Config
  host: String,
  port: Int,
  limits: Limits
base = Config(
  host: "localhost",
  port: 80,
  limits: Limits(retries: 3, timeout: 30)
)
label = base.do -> "$host:$port"
secure = base.update
  port: 443
  limits:
    retries: retries * 2
print("$label ${secure.host} ${secure.port} ${secure.limits.retries} ")
println("${secure.limits.timeout} ${base.port}")
```

Output: `localhost:80 localhost 443 6 30 80`. `base` is unchanged, `retries` inside the nested block is the old `3`, and `timeout` is carried over. Every right-hand side sees the original value, so the order of the lines doesn't matter. A function can take a receiver function and call it on a value:

```
fn apply(base: Config, change: Config.() -> Config) Config
  base.change()
bumped = apply(base)() -> Config(...self, port: port + 1)
println("${bumped.port}")
```

Output: `81`. The lambda can also go inside the call, `apply(base, () -> Config(...self, port: port + 1))`; its receiver comes from the expected type, and there is no `fn Config.()` form. Name lookup inside a receiver body is locals first, then the receiver's fields and methods, then the module; `self` is the innermost receiver. **Mistakes:** `port = 443` inside an `update` block (that binds a local), a field line in a plain `do` block, a misspelled or repeated field name, a nested block on a field that isn't a declared tuple, and expecting an outer receiver's fields to need `self`.

**8b. Composing interfaces, and extending without editing**

An interface may embed others by name, and one `impl` supplies all the members:

```
interface Speaker
  fn speak() String
interface Mover
  fn move_by(dx: Int) Self
interface Actor
  Speaker,
  Mover
tuple Robot2
  name: String,
  x: Int
impl Actor for Robot2
  fn speak() String
    "$name at $x"
  fn move_by(dx: Int) Robot2
    Self(..., x: x + dx)
fn announce(s: Speaker) Unit
  println(s.speak())
fn step[A: Actor](a: A) String
  a.move_by(5).speak()
r = Robot2(name: "R2", x: 1)
announce(r)
println(step(r))
```

Output: `R2 at 1`, then `R2 at 6`. `Robot2` satisfies `Actor`, `Speaker`, and `Mover`, which is why `announce` accepts it. Identical signatures from two embedded interfaces merge, and differing ones are a conflict error. You can't edit a type you don't own, but you can still extend: declare your own interface and `impl` it for the old type, or declare your own type and `impl` the old interface for it:

```
interface Describable
  fn describe() String
impl Describable for Int
  fn describe() String
    "the number $self"
println(7.describe())
```

Output: `the number 7`. Enums are closed on purpose (adding a case means every `when` must change, and the compiler finds them). For an open collection of unrelated types use `any Interface` (chapter 8d), and a `type union` of the known types is the closed alternative.

An interface may also require a **property**, a read-only field. A type satisfies it by having a field of that name and type, and callers always write `x.name`:

```
interface Named
  name: String
tuple User
  id: Int,
  name: String
tuple Pet
  name: String,
  owner: String
impl Named for User
impl Named for Pet
fn greet[T: Named](x: T) String
  "Hello, ${x.name}"
print("${greet(User(id: 1, name: "Ada"))} / ")
println("${greet(Pet(name: "Rex", owner: "Bo"))}")
```

Output: `Hello, Ada / Hello, Rex`. An impl with nothing to define has no body. A field with a delegate makes a computed property, there is no run-time cost, and `any Named` works too. **Mistakes:** `impl Named for T` where `T` has no `name` field of type `String`, a property satisfied by `fn name() String` (it must be a field), writing `x.name = ...` through a `Named` bound, and an enum whose cases carry different payloads.

**8c. Injection and mocks**

Interfaces are compile-time only, so a mock is just another `impl`, and the caller picks it by type. A `ref` receiver in the interface lets one signature serve both a recording mock and a real service:

```
interface Mailer
  fn (ref Self) notify(user_id: Int, amount: Int) Unit
tuple FakeMailer
  calls: Int,
  last_user: Int
impl Mailer for FakeMailer
  fn (ref Self) notify(user_id: Int, amount: Int) Unit
    calls += 1
    last_user = user_id
tuple SmtpMailer
  outbox: ChanW[Int]
impl Mailer for SmtpMailer
  fn (ref Self) notify(user_id: Int, amount: Int) Unit
    \write(outbox, user_id)
fn charge[M: Mailer](ref mailer: M, user_id: Int, amount: Int) Int
  fee = amount / 100
  ref mailer.notify(user_id, amount - fee)
  fee
mock = FakeMailer(calls: 0, last_user: 0)
fee = charge(ref mock, 7, 500)
println("$fee ${mock.calls} ${mock.last_user}")
```

Output: `5 1 7`. Production code passes an `SmtpMailer` to the same `charge`, and the compiler specializes it for each type, so the choice costs nothing at run time. (`SmtpMailer.notify` never rebinds `self`, but the interface requires the `ref`, so there is no warning.) The other two styles are a `using` parameter for read-only services such as clocks and configuration (`fn charge(user_id: Int, amount: Int, using clock: Clock) Int`; it can't inject a resource), and a fiber behind a channel that a test replaces with a fake fiber speaking the same protocol.

**8d. Typeclasses**

The Guide's `interface` and `impl` chapters already cover typeclasses, but this chapter gathers them in one place for Haskell programmers. Moxie has no separate typeclass feature: an `interface` is the class, an `impl` is the instance, and a bound is the constraint. Outputs were computed by hand.

**1. A class, its instances, and a constrained function**

```
interface Semigroup
  fn combine(other: Self) Self
interface Monoid
  Semigroup
  static fn empty() Self
impl Monoid for Int
  fn combine(other: Int) Int
    self + other
  static fn empty() Int
    0
tuple Max
  value: Int
impl Monoid for Max
  fn combine(other: Max) Max
    if value > other.value then self else other
  static fn empty() Max
    Max(value: -1000000)
fn mconcat[T: Monoid, N](xs: Array[T][N]) T
  xs |> to_stream() |> reduce(T.empty(), (a, b) -> a.combine(b))
nums: Array[Int] = (1, 2, 3)
maxes: Array[Max] = (Max(value: 3), Max(value: 9), Max(value: 4))
println("${mconcat(nums)} ${mconcat(maxes).value}")
```

Output: `6 9`. `Monoid` embeds `Semigroup`, which is the superclass relationship, and one `impl Monoid` supplies both members. The prelude already declares `Semigroup` and `Monoid` (chapter 24l) with instances for `String` and `List`; this example writes its own so you can see how an interface is built, and a declaration in your program is the one it uses. A member with no receiver is a `static fn`, reached through the type, so Haskell's `mempty` is `T.empty()`. The compiler specializes `mconcat` for each type, with no tables at run time.

**2. Associated types**

An interface can name a type that each impl chooses, so there is no need for an extra parameter or functional dependencies:

```
interface Container
  type Item
  fn get(i: Int) Result[Item, Error]
  fn size() Int
tuple Names
  items: List[String]
impl Container for Names
  type Item = String
  fn get(i: Int) Result[String, Error]
    get(items, i)
  fn size() Int
    len(items)
fn last_of[C: Container](c: C) Result[C.Item, Error]
  c.get(c.size() - 1)
names = Names(items: List("ada", "bob"))
when last_of(names)
  Ok(n) -> println(n)
  Err(e) -> println("empty")
```

Output: `bob`. A type has exactly one impl of each interface, so `C.Item` is never ambiguous.

**3. Constructor classes**

A class over a type constructor takes `F[_]`, and an instance names the constructor itself. (`List` by itself is a type constructor, and a parameter that stands for one is what Haskell and Scala call a higher-kinded type. Without it, `double_in` below would be written again for every container.) With the prelude's `Functor`, `Applicative`, and `Monad` interfaces and `impl Monad[Box]` from chapter 24, you can write code that works for any monad:

```
fn double_in[F[_]: Monad](m: F[Int]) F[Int]
  m.flat_map((x) -> F.pure(x * 2))
r: Result[Int, Error] = Ok(21)
println("${double_in(Box.Full(21))} ${double_in(r)}")
```

Output: `Box.Full(42) Ok(42)`. And an applicative lift:

```
fn lift2[F[_]: Applicative, A, B, C](f: (A, B) -> C, a: F[A], b: F[B]) F[C]
  a.map(curry(f)).ap(b)
none: Box[Int] = Box.Empty
print("${lift2(add, Box.Full(2), Box.Full(3))} ")
println("${lift2(add, none, Box.Full(3))}")
```

Output: `Box.Full(5) Box.Empty`. Return-type polymorphism needs an explicit type, so write `F.pure(x)` or `Box.pure(x)`; a bare `pure(x)` is not dispatched from context.

**Type lambdas.** A hole fixes only the first argument of a type, so `Result[_, String]` cannot say "a `Result` whose error comes first". A **type lambda** can: `[A] -> Result[String, A]` is a function from a type to a type, written with the brackets, the arrow, and the result. Hand one to a constructor parameter and it becomes the constructor it names:

```
fn one[M[_]: Monad]() M[Int]
  M.pure(1)
type alias Fail[A] = Result[A, String]
println("${one[[A] -> Result[A, String]]()} ${one[Fail]()}")
x: ([A] -> Result[A, String])[Int] = Ok(3)
println(x)
```

Output: `Ok(1) Ok(1)`, then `Ok(3)`. A generic alias such as `Fail` is a type lambda with a name. The lambda is replaced by its body when it is used, so nothing about it exists at run time, and it never loops, because a lambda cannot refer to itself. **Mistakes:** giving a two-parameter lambda where `F[_]` wants one (the compiler reports the arity), and applying a lambda to the wrong number of types.

**Type functions.** A type lambda only substitutes. When a type has to be taken apart, write a type alias whose body is a `when`, with an arm for each shape:

```
type alias Elem[T] = when T
  List[X] -> X
  Array[X][N] -> X

type alias Concat[A, B] = when A
  () -> B
  (H, ...T) -> (H, ...Concat[T, B])

type alias Length[T] = when T
  () -> 0
  (H, ...Rest) -> 1 + Length[Rest]

fn head_of(xs: Array[Int][3]) Elem[Array[Int][3]]
  xs(0)
joined: Concat[(Int, String), (Bool,)] = (1, "a", true)
sized: Array[Int][Length[(Int, String)]] = Array(1, 2)
println("${head_of(Array(7, 8, 9))} ${joined(1)} ${sized(1)}")
```

**Field names at the type level.** Tuple types keep their field names, and an arm can look a field up by name: with `type alias Get[R, K] = when R` and the arms `(K: T, ...Rest) -> T` and `(_: _, ...Rest) -> Get[Rest, K]`, a function `fn get[R, K](row: R, key: K) Get[R, K]` called as `get(user, "name")` returns `String` and as `get(user, "zip")` returns `Int`, and `get(user, "nope")` is an error because no arm matches. A literal argument keeps its own type (`"name"`, `3`) when its parameter is used inside a type function; otherwise it is widened to `String` or `Int` as before.

**Asking what a type can do.** An arm may use a bound as its pattern: `X: Named -> String` matches any type that implements `Named` and binds it to `X`, so `type alias Label[T] = when T` with the arms `X: Named -> String` and `else Int` gives `String` for a type with an `impl Named` and `Int` for the rest. This is the type-level form of `[T: Named]`, and it reuses the `impl` and `deriving` you already wrote.

**Intersections.** `any Named + Aged` is a value that implements both interfaces, written with the `+` that joins bounds (`[T: Equatable + Show]`). `describe(Dog(...))` is a compile error when `Dog` has no `impl Aged`, and a type-function arm can ask the same, `X: Named + Aged -> String`.

**Compile-time evaluation.** A pure function that you declare is also run by the compiler when its arguments are constants and a constant is needed: `a: Array[Int][fib(5)] = Array(1, 2, 3)` is a compile error (`Array[Int][5]` expected, 3 found), `N = fib(6)` makes `N` usable as a size, and `port = parse_port("99999")` fails to compile if `parse_port` aborts on that input. Nothing special is written: there is no keyword, and a function with a print or other effect is simply left until run time. A call that never finishes is stopped (`eval_fuel` in `[program]` sets the step limit).

Output: `7 a 2`. `Elem[Array[Int][3]]` is `Int`, because the first arm that matches wins. A bare name in a pattern that is not a known type (`X`, `N`, `H`) is a variable the match binds, and `...Rest` binds the remaining items of a tuple type, as `...rest` does in a list pattern. Numbers are types, so `Length` counts, and `Array[X][N - 1]` computes a size. An arm may have a guard, `M if M > 3 -> Array[Int][M]`, and a string in quotes is a type too, so a schema can be written `"id" -> Int`, `"name" -> String`. An alias may call itself, so a type function can loop over a tuple type. Because that makes the type language a program, the checker limits it: a use that takes more than 64 reductions (`type_fuel` under `[program]` in `Moxie.toml` changes the number) or a type that grows past 4,000 parts is an error that shows the last few steps, and a function that calls itself on a type that is not a piece of what it matched gets a warning. If no arm matches, the compiler says which type had no arm. Inside a generic function the type is not known yet, so `Elem[T]` waits until the call. A type function exists only while the program is checked. **Mistakes:** an arm that does not shrink (it ends only at the limit), and expecting a pattern name to mean a type you declared later in the file (a name that is already a type is a constant, not a variable).


**4. Conditional instances**

An `impl` may put a bound on its own type parameters:

```
interface Describable
  fn describe() String
impl Describable for Int
  fn describe() String
    "int $self"
tuple Crate[A]
  value: A
impl[A: Describable] Describable for Crate[A]
  fn describe() String
    "crate(${self.value.describe()})"
println(Crate(7).describe())
```

Output: `crate(int 7)`. `Crate[A]` is `Describable` exactly when `A` is.

**5. Interface values** *(approved: `any`)*

When you need a mixed collection and don't control the set of types, `any Voice` holds one of any type that implements `Voice`:

```
interface Voice
  fn speak() String
tuple Dog
  name: String
tuple Robot
  serial: Int
impl Voice for Dog
  fn speak() String
    "Woof! My name is ${name}"
impl Voice for Robot
  fn speak() String
    "Beep Boep! Serial count is ${serial}"
crowd: List[any Voice] = List(Dog(name: "Rex"), Robot(serial: 7))
for s in crowd
  println(s.speak())
```

Output: `Woof! My name is Rex`, then `Beep Boep! Serial count is 7`. **[gc]** An `any` value is a reference to the value plus its type's method table, and a call goes through that table, so only members with a receiver, and `Self` used only as a result, are callable through it. `any` values aren't comparable or usable as keys.

**6. Default method bodies**

A member may have a default body that an `impl` can override:

```
interface Greeter
  fn name() String
  fn greet() String
    "Hello, ${self.name()}"
tuple Pal
  id: String
tuple Boss
  title: String
impl Greeter for Pal
  fn name() String
    id
impl Greeter for Boss
  fn name() String
    title
  fn greet() String
    "Good day, ${self.name()}"
println("${Pal(id: "ada").greet()} / ${Boss(title: "Chief").greet()}")
```

Output: `Hello, ada / Good day, Chief`. The default is specialized for each implementing type.

**7. Haskell to moxie, at a glance**
- `class` and `instance` become `interface` and `impl X for T`; `instance Monad Box` becomes `impl Monad[Box]`.
- Superclasses are embedded interfaces; constraints are bounds like `[T: Monoid]`.
- `deriving` is `deriving show, eq, ord, read`.
- Instances must live with the type or the interface (no orphans).
- Default method bodies and associated types exist. Missing from the language: functional dependencies and type families.

**Mistakes:** an `impl` of someone else's interface for someone else's type, calling `empty()` with no type to say which one, combining two `any Monoid` values (`Self` in a parameter), comparing `any` values with `==` when the interface doesn't list `Equatable` (list `Equatable`, `Ordered`, or `Hashable` inside it and `==`, `<`, `Set`, and `Dict` keys all work), and a bound written twice on one parameter (embed the interfaces instead).

**Chapter 9: Field delegates**

A delegate adds behavior to a field's reads and writes, with no cost at runtime. It is a declared tuple with one field of the field's type, and it implements `FieldHandler[T]`:

```
tuple Percent
  value: Int
impl FieldHandler[Int] for Percent
  fn get_value() Int
    value
  fn (ref Self) set_value(new_value: Int) Unit
    value = if new_value < 0 then 0 elif new_value > 100 then 100 else new_value
tuple Gauge
  level: Int delegate(Percent)
g = Gauge(level: 150)
println("${g.level}")
g.level = -20
println("${g.level}")
```

Output: `100`, then `0`. The constructor runs `150` through the delegate, so it clamps at creation, and each write does too. A setter may also reject a value by returning a `Result`, as in `fn (ref Self) set_value(new_value: Int) Result[Unit, Error]`. Then `Gauge(level: -1)` is a `Result[Gauge, Error]`, and the compiler rejects `g.level = x`, because an assignment has nowhere to put a failure. Moxie generates `g.set_level(x)` instead, which returns the changed `Gauge` or the `Err`, as for a property with a `Result` setter (Chapter 9b). **Mistakes:** a delegate on an enum payload or a local (only declared tuple fields), and a delegate field in a tuple used as a Dict key.

**Chapter 9b: Properties**

A property reads and writes like a field (`a.balance`, `a.balance = 5`), but it can run code when it is read or written. You declare it in a tuple, written like a field with the word `property` in front, and add accessors underneath only when you need them:

```
tuple Account
  owner: String,
  property balance: Int = 0
    priv set(value)
      assert(value >= 0)
      field = value
    did_set(old)
      println("balance ${old} -> ${field}")
impl Account
  fn (ref Self) deposit(n: Int) Unit
    balance = balance + n
a = Account(owner: "Ann", balance: 5)
a.deposit(3)
println(a.balance)
```

Output: `balance 5 -> 8`, then `8`. A property with no accessors is a stored field, and `= 0` is its initial value, as for a field. The accessors are `get`, `set(value)`, `will_set(new)`, and `did_set(old)`, indented under the property. Inside an accessor, `field` is the stored value: a getter can return it, and a setter stores with `field = value`. A bare `get` or `set` with no body means "the default one", so `priv set` keeps the default setter but makes it private to the tuple's own `impl` blocks. The constructor runs a value you pass through the setter, so `Account(owner: "Ann", balance: -1)` aborts. `did_set` runs only when a write changes the value, and never at construction. `will_set(new)` runs just before such a write is stored, with the value on offer, while `field` still holds the old one: the order is `will_set`, then `set`, then `did_set`. It can't veto a write, so validation belongs in `set`. Outside a property's own accessors, a bare `balance` in an `impl` goes through the property, as `a.balance` does, so the tuple's own methods can't skip the check.

A setter can reject a value by returning a `Result`. You write the return type after the parameter, and moxie makes a function `set_NAME` that returns the changed tuple, or the `Err`:

```
tuple Account
  owner: String,
  property balance: Int = 0
    set(value: Int) Result[Unit, Error]
      if value < 0
        fail(1, "negative")
      else
        field = value
        Ok(())
when Account(owner: "Ann", balance: 5)
  Err(e) -> println("rejected")
  Ok(a) ->
    when a.set_balance(-1)
      Ok(b) -> println("changed")
      Err(e) -> println("rejected, still ${a.balance}")
    when a.set_balance(9)
      Ok(b) -> println("${b.balance}, was ${a.balance}")
      Err(e) -> println("rejected")
```

Output: `rejected, still 5`, then `9, was 5`. The original is never touched, as with any value. Because a write can fail, `a.balance = 9` is a compile error on such a property, and the constructor is a `Result` too (`Account(owner: "Ann", balance: -1)` is an `Err`). A `priv set` can't return a `Result`, since `set_balance` is public.

A property that stores nothing is a computed one:

```
tuple Rect
  width: Int,
  height: Int,
  property area: Int
    get
      width * height
    set(value)
      width = value / height
r = Rect(width: 3, height: 4)
println("${r.area} ${r}")
r.area = 24
println("${r.width} ${r.area}")
```

Output: `12 Rect(width: 3, height: 4)`, then `6 24`. A property has storage unless it has a `get` body that never uses `field`. `area` has none: it isn't in the tuple's layout, it isn't printed or compared, and it can't have an `= value`. A computed property may have a setter, which writes the other fields. A property that does store a value must store it in its setter (the compiler reports a setter that never uses `field`). Callers can't tell a property from a field. Use a field delegate (chapter 9) when one rule is shared by many fields, and a property when the rule belongs to one field or needs the others.

`lazy` computes a value once, on its first read. It works for a property and for a local binding. A `static` property belongs to the type and is read through it:

```
tuple Report
  data: List[Int],
  lazy property total: Int
    get
      data |> to_stream() |> sum()
  static property title: String = "Weekly"
r = Report(data: List(4, 5, 6))
println("${Report.title}: ${r.total} ${r.total}")
r.data = List(10, 20)
println(r.total)
lazy size = len(r.data) * 100
println("${size}")
```

Output: `Weekly: 15 15`, then `30`, then `200`. The expression of a `lazy` property or binding must be pure, because it runs whenever the first read happens, so the compiler rejects one that prints or reads a channel. The result is kept in the value you hold, and `r.data = ...` builds a new value whose cache is empty, which is why the second `r.total` is recomputed. A value read out of an Atom is a copy, so read it once and keep the copy if you will ask again. This is different from a `lazy` parameter (chapter 6b), which re-runs its argument on every read. A static property is read-only: it takes an `= value` or a `get` body, and shared state that changes belongs in an Atom.

An interface lists a property the way it lists a field. A field, a property, or a delegate field satisfies it, and callers write `x.name` in every case:

```
interface Named
  name: String
interface Wallet
  property balance: Int
    get
    set
tuple Person
  given: String,
  family: String,
  property name: String
    get
      "${given} ${family}"
tuple Purse
  property balance: Int = 0
impl Named for Person
impl Wallet for Purse
fn greet[T: Named](x: T) String
  "Hello, ${x.name}"
println(greet(Person(given: "Ada", family: "Lovelace")))
```

Output: `Hello, Ada Lovelace`. `name: String` asks for something readable. `property balance: Int` with `get` and `set` underneath asks for something readable and writable (with neither line, it asks for both). `impl Named for T` is a compile error when `T` has no field or property of that name, or its type differs, or it is read-only where the interface asks for `set`.

When the tuple is held in an Atom, other code can watch a property, as many listeners as it likes, such as a database handler and a GUI handler:

```
tuple Account
  owner: String,
  property balance: Int = 0
fn save_row(old: Int, new: Int) Unit
  println("db: ${old} -> ${new}")
shared = Atom[Account](Account(owner: "Ann"))
db = shared.on_change(balance, save_row)
ui = shared.balance +% fn (old, new) -> println("ui: ${new}")
\swap(shared, (a) -> Account(owner: a.owner, balance: 5))
shared.off_change(ui)
\swap(shared, (a) -> Account(owner: a.owner, balance: 5))
\swap(shared, (a) -> Account(owner: a.owner, balance: 9))
shared.balance -% db
\swap(shared, (a) -> Account(owner: a.owner, balance: 1))
println(@shared)
```

Output: `db: 0 -> 5`, `ui: 5`, `db: 5 -> 9`, then `Account(owner: "Ann", balance: 1)`. `on_change(shared, balance, handler)` calls `handler(old, new)` whenever a write through the Atom changes `balance`, in the order the handlers subscribed and after the type's own `did_set`. Writing the same value calls nobody. It returns a token, and `off_change(shared, token)` removes the handler. `shared.balance +% handler` and `shared.balance -% token` mean the same two things. A handler's closure copies what it captures, so it acts through effects: it prints, writes to a channel, or swaps another Atom. A property has room for 8 observers, and `property[16] balance: Int` gives it 16, though the list grows as needed, so the number is only a hint. Only properties can be watched, not plain fields.

**Mistakes:** a setter that never stores into `field`, an `= value` on a property that stores nothing, `did_set` or `will_set` on a computed property, writing to a static or computed-only property, a `priv set` assigned from outside the tuple's `impl`, a `lazy` expression that prints, `on_change` on a plain field, and a property declared on the same line as a one-line tuple (a property goes on its own line).

**Chapter 10: Operators, `|>>`, Results**

An operator is defined in an `impl` block: the receiver is the left operand and the parameter is the right one.

```
tuple Money deriving show
  cents: Int
impl Money
  fn + (other: Money) Money
    Money(cents: cents + other.cents)
  fn < (other: Money) Bool
    cents < other.cents
a = Money(cents: 150)
b = Money(cents: 250)
println("${(a + b).cents} ${a < b} ${b >= a}")
```

Output: `400 true true`. Defining `<` gives you `>`, `<=`, and `>=`, and defining `==` gives you `~=`. An interface may list an operator, and a bound uses it. The prelude's `Addable` lists `+` and `zero`, and numbers and strings already implement it, so only your own types need an `impl`:

```
impl Addable for Money
  fn +(other: Money) Money
    Money(cents: cents + other.cents)
  static fn zero() Money
    Money(cents: 0)
fn sum_two[T: Addable](x: T, y: T) T
  x + y
println("${sum_two(3, 4)} ${sum_two(a, b).cents}")
```

Output: `7 400`. A bound on `Ordered` lets a generic compare (numbers and strings already satisfy it):

```
fn larger[T: Ordered](x: T, y: T) T
  if x < y then y else x
println("${larger(a, b).cents} ${larger(2, 5)}")
```

Output: `250 5`. A type may define its own bind `|>>` in an `impl`, and `Result` has one in the prelude. (Once a type has a `Monad` impl, chapter 24, the prelude's `|>>` works for it without your own.)

```
enum Box[A] deriving show
  Full(value: A),
  Empty
impl[A] Box[A]
  fn |>>[B] (f: (A) -> Box[B]) Box[B]
    when self
      Full(v) -> f(v)
      Empty -> Box.Empty
fn half(n: Int) Box[Int]
  if n % 2 == 0 then Box.Full(n / 2) else Box.Empty
x = Box.Full(20) |>> half |>> half
y = Box.Full(10) |>> half |>> half
println("$x $y")
```

Output: `Box.Full(5) Box.Empty`. (`10 → 5`, then `5` is odd.) Result helpers cover the same ground:

```
fn parse_ok(n: Int) Result[Int, Error]
  if n < 0 then fail(1, "negative") else Ok(n)
r1 = parse_ok(5) |>> ((v) -> Ok(v * 2))
m = map_ok(parse_ok(20), (v) -> v + 1)
bad = map_err(parse_ok(-1), (e) -> e)
println("${is_ok(r1)} ${is_err(bad)} ${m.get_or(-1)}")
```

Output: `true true 21`. The prelude defines `<$>` (map), `<*>` (apply), and `|>>` (bind) for every type with a `Functor`, `Applicative`, or `Monad` impl, `Result` among them. Both `<$>` and `<*>` start with `<`, so parenthesize them with other operators:

```
inc = (x: Int) -> x + 1
two: Result[Int, Error] = Ok(2)
f: Result[(Int) -> Int, Error] = Ok(inc)
println("${(inc <$> two)} ${(f <*> two)}")
```

Output: `Ok(3) Ok(3)`. **Mistakes:** defining `>`, `~=`, or `>=` yourself (they are derived), an operator on two types you don't own, a user operator ending in `=`, and mixing `~>` and `<~` in one chain without parentheses.

**Chapter 11: Pipelines and `seq`**

```
fn add(x: Int, y: Int) Int
  x + y
fn multiply(factor: Int, value: Int) Int
  factor * value
final_score = 10
  |> add(5, &)
  |> multiply(2, &)
fn is_big(n: Int) Bool
  n > 100
fn halve(n: Int) Int
  n / 2
shrunk = 500
  |> seq
    is_big -> halve()
    is_big -> halve()
println("$final_score $shrunk")
```

Output: `30 125`. `|>` tries the first and the last mandatory parameter of the call on its right as the slot for the left value, fills the rest from the explicit arguments in order, and keeps the placement that type-checks. If both work, that is an ambiguity error that asks for `&`, and a slot in the middle needs `&` too. A stage is always a call, and there is no partial application. A `seq` block runs every arm whose condition holds, in order, each seeing the previous result: 500 is big, so it halves to 250, which is still big, so it halves to 125. A `seq` needs piped input and has no default arm. The dot form is the same call, and mixers may use either:

```
numbers = Array(1, 2, 3, 4)
a = numbers |> to_stream() |> map(_ * 2) |> take(3) |> sum()
b = numbers.to_stream().map(_ * 2).take(3).sum()
println("$a $b")
```

Output: `12 12`. A two-argument function can be written between its arguments with backticks:

```
fn calculate_yield(base: Int, factor: Int) Int
  base * factor
```
`println("${100 `calculate_yield` 5}")`

Output: `500`. **Mistake:** `10 |> subtract(3)` is ambiguous because both slots fit, and the compiler asks for `&`:

```
10 |> subtract(&, 3)    // subtract(10, 3), which is 7
10 |> subtract(3, &)    // subtract(3, 10), which is -7
```

A stage with no explicit arguments takes a tuple that fits its whole parameter list, so results flow from one stage to the next:

```
fn fetch_sensor_data(id: Int) (Float, Float, Float)
  (12.5, 45.0, 0.8)
fn calculate_velocity(
  x: Float,
  y: Float,
  z: Float
) (speed: Float, angle: Float)
  (95.2, 14.6)
fn update_physics(speed: Float, angle: Float) Unit
  println("Physics vector updated: speed $speed, angle $angle")
1042
  |> fetch_sensor_data()
  |> calculate_velocity()
  |> update_physics()
```

Output: `Physics vector updated: speed 95.2, angle 14.6`. **Mistakes:** piping a larger tuple into a smaller parameter list (extra fields are an error), and writing a stage without parentheses (`|> update_physics`).

**Chapter 12: Patterns, `is`, let-else**

```
my_list = List(105, 210, 315, 420)
when my_list
  List(head, ...tail) ->
    println("head $head")
    for cell in tail
      println("tail $cell")
  else println("empty")
```

Output: `head 105`, then `tail 210`, `tail 315`, `tail 420`. A guard adds a condition, and `@` names the whole value:

```
tuple Account
  name: String,
  score: Int
player = Account(name: "Bob", score: 150)
when player
  p@Account(name, score) if score > 200 -> println("top tier: $name")
  p@Account(name, score) if score > 100 -> println("elite: ${p.name}")
  else println("standard")
```

Output: `elite: Bob`. A pin compares against a variable:

```
limit = 100
reading = 100
when reading
  ^limit -> println("exactly at the limit")
  ^(limit + 1) -> println("just over")
  n -> println("reading $n")
```

Output: `exactly at the limit`. A relational pattern (`>=`, `>`, `<=`, `<`) matches an open-ended range, for any ordered type, and its operand is a literal or a pin:

```
fn describe(status: Int) String
  when status
    200 -> "Success"
    400..=499 -> "Client Error"
    >= 500 -> "Server Error"
    else "Unknown"
fn grade(score: Double) String
  when score
    >= 90.0 -> "A"
    >= 80.0 -> "B"
    else "C"
print("${describe(200)} ${describe(404)} ${describe(503)} ${describe(302)} ")
println("${grade(85.0)}")
```

Output: `Success Client Error Server Error Unknown B`. On an unbounded type the compiler can't tell whether relational arms cover everything, so the `when` needs a `_` arm; on a bounded integer such as `Int[0..=100]`, `>= 50` and `< 50` together count as covering it. A Dict pattern matches a subset of entries, and a `when` with no value tests conditions in order:

**`else` for the last arm.** The last arm of a `when` (with or without a value to match), of a `select`, and of a `seq` can be written `else` instead of `_ ->`. In a `when` and a `select` it means exactly what `_ ->` means, and its body follows on the same line or indented below it. In a `seq` every arm whose test passes runs in turn, so `else` is the stage that runs only when none of the earlier arms did. It must come last, and in a `select` it is the arm that runs when no channel is ready. It never takes `->`, and in a `select` it is written without `case`. An arm after one that matches everything (`else`, `_`, or a bare name) never runs, and neither does a repeated literal or a repeated enum case: the compiler warns about both.

```
status = Dict("speed": 60, "limit": 100)
when status
  Dict("speed": current, "limit": 100) -> println("moving at $current")
  else println("idle")
number = 25
when
  number < 0 -> println("negative")
  number % 2 == 0 -> println("even")
  else println("odd and positive")
```

Output: `moving at 60`, then `odd and positive`. A function can be defined by several clauses, and tail-recursive ones run in constant stack:

```
fn route_status(200) String = "Success"
fn route_status(404) String = "Not Found"
fn route_status(_) String = "Unknown Error"
fn sum_to(0, total: Int) Int = total
fn sum_to(n, total: Int) Int = sum_to(n - 1, total + n)
println("${route_status(404)} ${sum_to(4, 0)}")
```

Output: `Not Found 10`. A clause can carry an `if` guard before its body, and `tailrec` makes a self-call that isn't a tail call a compile error:

```
fn classify(n: Int) String if n < 0 then "neg"
fn classify(n) if n == 0 then "zero"
fn classify(n) = "pos"
tailrec fn count_up(0, acc: Int) Int = acc
tailrec fn count_up(n, acc) = count_up(n - 1, acc + n)
println("${classify(-1)} ${classify(0)} ${classify(5)} ${count_up(100, 0)}")
```

Output: `neg zero pos 5050`. **Mistake:** a `tailrec fn` whose recursive call sits inside `n * fact(n - 1)`, which is not in tail position. A pattern that can't fail may take a value apart in a binding:

```
Point(x, y) = Point(x: 1.5, y: 2.0)
println("$x $y")
```

Output: `1.5 2.0`. `value is Pattern` is a Boolean test, and its names are visible in the `then` branch (and after `and`, but not under `or` or `not`):

```
enum Reading
  Value(n: Int)
  Missing
fn show_reading(r: Reading) String
  if r is Value(n) then "value $n" else "missing"
println("${show_reading(Reading.Value(7))} ${show_reading(Reading.Missing)}")
```

Output: `value 7 missing`. A **let-else**, `Pattern = expr else value`, leaves the whole function with the else value when the pattern doesn't match:

```
fn times_ten(r: Reading) Reading
  Value(n) = r else Reading.Missing
  Reading.Value(n * 10)
print("${times_ten(Reading.Value(7))} ")
println("${times_ten(Reading.Missing)}")
```

Output: `Reading.Value(70) Reading.Missing` (using `Reading` from above). **Mistakes:** a `when` that doesn't cover every case, a Set pattern (not supported), a let-else with a pattern that can't fail (warning), and using an `is` name under `or`.

**12a. Binary patterns**

A byte layout is matched with `Bin(...)` on an `Array[Byte]`. Each element is `name: kind`, read left to right: `u8`, `i8`, and the sized kinds `u16be`, `u16le`, `u32be`, `u32le`, `u64be`, `u64le` and the signed `i16be` to `i64le` (the byte order is always written), `bits(n)` for an unsigned field of `n` bits packed from the high bit (bit fields must add up to whole bytes), and `bytes(n)` for a run of bytes, where `n` is a number or an earlier field. A literal byte (`0xCA`) or byte string (`b"MZ"`) must match exactly, `_` skips a field, and `rest: bytes` at the end takes whatever is left:

```
fn describe(packet: Array[Byte]) String
  when packet
    Bin(
      0xCA,
      version: bits(4),
      kind: bits(4),
      size: u16be,
      body: bytes(size),
      rest: bytes
    ) -> "v$version k$kind size $size body ${len(body)} rest ${len(rest)}"
    Bin(a: u8, b: i16le) -> "short $a $b"
    else "no match"
println(describe(b"\xCA\x21\x00\x02hiXYZ"))
println(describe(b"\xCA\x21\x00\x09hi"))
println(describe(b"\x07\xFE\xFF"))
println(describe(b"\x07"))
```

Output: `v2 k1 size 2 body 2 rest 3`, then `no match`, then `short 7 -2`, then `no match`. A packet that is too short, has a wrong literal, or has bytes left over that no element describes (when the pattern does not end in `rest: bytes`) does not abort: the arm just fails and the next one is tried. Every field is an ordinary binding, so a guard works (`Bin(...) if size > 0 -> ...`), and `packet is Bin(b"MZ", rest: bytes)` is a Boolean test. **Mistakes:** a name that clashes with a prelude function you still need in the arm (a field called `len` hides `len`), bit fields that don't make whole bytes, and a `bytes(n)` that names a field that comes later.


To go the other way, write `Bin` as an expression with a value in front of each kind. The packet above can be built and read back:

```
p = Bin(0xCA, 2: bits(4), 1: bits(4), 2: u16be, b"hi": bytes, b"XYZ": bytes)
println(p)
println(describe(p))
```

Output: `Array(202, 33, 0, 2, 104, 105, 88, 89, 90)`, then `v2 k1 size 2 body 2 rest 3`. A value that does not fit its kind (`300: u8`) aborts. Arms that cover every length need no `_`: `Bin()`, `Bin(a: u8)`, and `Bin(a: u8, b: u8, rest: bytes)` together do, and the compiler names the first length that no arm covers. An arm with a literal, a guard, or a `bytes(n)` sized by a field earns no credit, so those still need a `_` arm.

**Taking a value apart by its type.** A union, or an `any` value, carries a small tag with its type, and `when` reads it. A bare type is an arm (`Int ->`), and `n@Int` also binds the value itself, so `n` is an `Int` in that arm:

```
type union Value = Int | String
fn describe(v: Value) String
  when v
    n@Int -> "the number ${n + 1}"
    s@String -> "the text ${s}"
println(describe(41))
println(describe("hi"))
```

Output: `the number 42`, then `the text hi`. A union is exhaustive without a `_` arm. An `any` value is taken apart the same way, with a `_` arm because the full set of types isn't known. What a name in the arm refers to depends on how you write it:

Members with type arguments work the same way. With `type union Data = List[Int] | List[String] | Int`, the arms `List[Int] ->` and `xs@List[String] ->` take a `Data` apart, and inside each arm the value has that list type, so `d(0) + 1` is checked as an `Int` addition in the first and rejected in the second. `d is List[Int]` is the same test as a condition.

```
interface Speaker
  fn speak(self) String
tuple Dog
  name: String
tuple Robot
  serial: Int
impl Speaker for Dog
  fn speak(self) String
    "Woof"
impl Speaker for Robot
  fn speak(self) String
    "Beep"
crowd: List[any Speaker] = List(Dog(name: "Rex"), Robot(serial: 7))
for s in crowd
  when s
    Dog(name) -> println("a dog named ${name}")
    r@Robot() -> println("a robot, ${r}")
    _ -> println("something else")
```

Output: `a dog named Rex`, then `a robot, Robot(serial: 7)`. In `Dog(name)`, the parentheses take the dog apart like any tuple pattern, so `name` is the dog's first field (a `String`), not the dog. In `r@Robot()`, `r@` names the whole value, so `r` is the `Robot` itself, and the empty parentheses mean no fields are taken. `d@Dog(name)` gives both. **Mistakes:** writing `Int(n)` for a scalar (use `n@Int`), and expecting `Dog(d)` to bind the whole `Dog` (it binds the first field).

Inside an arm, the variable has the narrowed type: in the `Int` arm above, `v` is an `Int`, so `len(v)` there is a compile error, and in the `String` arm `v + 1` is one. The same holds for a parameter typed `any Speaker` inside a `d@Dog() ->` arm, where `d.serial` is a compile error because a `Dog` has no `serial`.

**Chapter 13: Streams and loops**

```
numbers = Array(10, 20, 30, 40)
for v in numbers |> to_stream() |> map(_ * 2)
  println("$v")
total = numbers |> to_stream() |> reduce(0, _1 + _2)
big: List[Int] = numbers |> to_stream() |> filter(_ > 15) |> collect()
println("$total ${len(big)}")
```

Output: `20`, `40`, `60`, `80`, then `100 3`. The prelude has more stages and terminals:

```
nums = Array(5, 3, 8, 1)
s = nums |> to_stream()
total = s |> sum()
count_big = s |> filter(_ > 4) |> count()
lowest = s |> min()
print("$total $count_big ${lowest.get_or(0)} ${s |> any(_ == 8)} ")
println("${s |> all(_ > 0)}")
```

Output: `17 2 1 true true`. `avg()` gives the mean of numbers as a `Result[Float, Error]` (MISSING when the stream is empty), and `sum()` and `product()` use `+` and `*`, so `sum()` also joins strings and adds your own types that implement `Addable`; the sum of an empty stream is the element type's `zero` (`0`, `0.0`, `""`, or your own type's), and the product's is its `one`. (Each terminal reruns the recipe, so one `s` feeding five terminals is a lint warning; here it is deliberate.) `scan` emits a running value after each element, and `enumerate` pairs each element with its index:

```
running: List[Int] = List(1, 2, 3, 4)
  |> to_stream()
  |> scan(0, _1 + _2)
  |> collect()
println("${running(0)} ${running(1)} ${running(2)} ${running(3)}")
for (i, v) in List(10, 20) |> to_stream() |> enumerate()
  println("$i:$v")
```

Output: `1 3 6 10`, then `0:10`, `1:20`. Sorting needs every element first:

```
ordered: List[Int] = nums |> to_stream() |> sort() |> collect()
flipped: List[Int] = nums |> to_stream() |> reverse() |> collect()
println("${ordered(0)} ${flipped(0)}")
```

Output: `1 1` (the smallest is first when sorted, and `1` is last in `nums`, so first when reversed). **Horizontal and vertical.** Horizontal stages pass one element at a time through the whole chain. A vertical stage like `sort` first collects every element:

```
fn tag_map(x: Int) Int
  println("map $x")
  x * 2
fn tag_keep(y: Int) Bool
  println("keep $y")
  y > 2
src = List(3, 1, 2)
h = src |> to_stream() |> map(tag_map) |> filter(tag_keep) |> count()
v = src |> to_stream() |> map(tag_map) |> sort() |> filter(tag_keep) |> count()
```

The first prints `map 3`, `keep 6`, `map 1`, `keep 2`, `map 2`, `keep 4`, and `h` is `2`. The second prints `map 3`, `map 1`, `map 2`, then `keep 2`, `keep 4`, `keep 6`, and `v` is `2`. **Chunks and windows.** `chunks(n)` yields consecutive groups (each a `List[T]`, the last possibly shorter), and `windows(n)` yields every run of `n` neighbors (each an `Array[T][n]`):

```
nums5 = List(1, 2, 3, 4, 5)
cs: List[List[Int]] = nums5 |> to_stream() |> chunks(2) |> collect()
ws: List[Array[Int][2]] = nums5 |> to_stream() |> windows(2) |> collect()
println("${len(cs)} ${len(cs(0))} ${len(cs(2))}")
println("${len(ws)} ${ws(1)(0)} ${ws(3)(1)}")
```

Output: `3 2 1`, then `4 2 5`. The chunks are `[1, 2]`, `[3, 4]`, `[5]`, and the windows are `[1, 2]`, `[2, 3]`, `[3, 4]`, `[4, 5]`. A moving average:

```
readings = List(3, 6, 9, 12, 15)
avg: List[Int] = readings
  |> to_stream()
  |> windows(3)
  |> map((w) -> (w |> to_stream() |> sum()) / 3)
  |> collect()
println("${avg(0)} ${avg(1)} ${avg(2)}")
```

Output: `6 9 12`. The terminals `partition`, `unzip`, and `group_by` split a stream:

```
(small, big2) = nums5 |> to_stream() |> partition(_ < 3)
println("${len(ws)} ${len(small)} ${len(big2)}")
```

Output: `4 2 3`. `unzip()` turns a stream of pairs into two lists, and `group_by(key)` fills a `Dict` of lists whose type you declare. A collection works directly as a loop source, and a range gives a count:

```
for x in numbers
  println("$x")
for i in Range(0..=10, 2)
  println("step $i")
for i in Range(3..=1, -1)
  println("countdown $i")
```

Two streams pair up with `zip`:

```
names = List("alice", "bob")
ages = List(30, 25)
for (name, age) in zip(names, ages)
  println("$name is $age")
```

Output: `alice is 30`, then `bob is 25`. More stages shape a stream. `distinct()` drops repeats, `intersperse(sep)` puts a separator between elements, `min_by(key)` and `max_by(key)` give a `Result`, and `span(pred)` splits a stream at the first element that fails `pred`:

```
words = List("pear", "fig", "banana", "fig", "kiwi")
println("${words |> to_stream() |> distinct() |> collect()}")
joined = words
  |> to_stream()
  |> distinct()
  |> intersperse("|")
  |> reduce("", _1 + _2)
println("$joined")
print("${words |> to_stream() |> min_by(len)} ")
println("${words |> to_stream() |> max_by(len)}")
(short, rest) = words |> to_stream() |> span((w) -> len(w) < 6)
println("$short ${len(rest)}")
```

Output: `List("pear", "fig", "banana", "kiwi")`, `pear|fig|banana|kiwi`, `Ok("fig") Ok("banana")`, then `List("pear", "fig") 3`. `zip_with`, `flatten`, `cycle`, and `split_at` work the same way, and `distinct_by(key)` (the first element for each key), `zip3(a, b, c)`, `frequencies()` and `count_by(key)` (a `Dict` of counts), and `transpose()` (rows of any lengths to columns) join them:

```
sums = zip_with(_1 + _2, List(1, 2, 3), List(10, 20, 30)) |> collect()
flat = List(List(1, 2), List(3)) |> to_stream() |> flatten() |> collect()
loop3 = List(1, 2) |> to_stream() |> cycle() |> take(5) |> collect()
(head, tail) = List(1, 2, 3, 4) |> to_stream() |> split_at(1)
println("$sums $flat $loop3 $head $tail")
```

Output: `List(11, 22, 33) List(1, 2, 3) List(1, 2, 1, 2, 1) List(1) List(2, 3, 4)`. A generator is a function that returns an `unfold` stream. The step takes the state and returns the value with the next state, or `Err` to end:

```
tuple Fib
  a: Int,
  b: Int
fn fibonacci() Stream[Int]
  unfold(Fib(a: 0, b: 1))(s) ->
    Ok((s.a, Fib(a: s.b, b: s.a + s.b)))
for n in fibonacci() |> take(6)
  println("$n")
```

Output: `0`, `1`, `1`, `2`, `3`, `5`. **[gc]** A stream holds its source, so a helper can build a stream over data you already have and return it like any other value. Only a stream that borrows a resource (a channel end or a database connection) still needs `inline fn`:

```
tuple NetworkBuffer
  packets: List[Packet]
fn stream_packets(buffer: NetworkBuffer) Stream[Packet]
  Stream(buffer.packets, 0..)
```

A loop can return a value, with `break(value)` for an early exit and `else` for when it runs out:

```
i = 0
sum = 0
(last, final) = while i < 10
  sum += i
  i++
  if sum > 20
    break(i, sum)
else
  (i, sum)
println("$last $final")
```

Output: `7 21`. **Mistakes:** one stream feeding two terminals by accident, and building a growing list by rebinding in a loop (use `reduce`).

**Chapter 14: Caching is explicit**

Nothing is memoized unless you ask: the one built-in way is `lazy` on a binding or a property (chapter 9b), which computes a pure expression once, on its first read. For a function of a changing argument, nothing is cached for you, and the usual recipe is a bottom-up `reduce`: start from the base case and carry only what the next step needs, which is the last two values for Fibonacci and the previous row for a table:

```
fn fib(n: Int) Int
  (a, _) = Range(1..=n, 1) |> reduce((0, 1), (s, _) -> (s(1), s(0) + s(1)))
  a
println("${fib(10)}")
```

Output: `55`. A grid of paths (move right or down, count the ways to the far corner) carries one row, and each new row is a `reduce` over the columns:

```
fn next_row(prev: List[Int]) List[Int]
  Range(1..len(prev), 1) |> reduce(List(prev(0)), (acc, j) -> acc + (prev(j) + acc(j - 1)))
fn paths(rows: Int, cols: Int) Int
  first = List(1 for _ in 0..cols)
  last = Range(1..rows, 1) |> reduce(first, (prev, _) -> next_row(prev))
  last(cols - 1)
println("${paths(3, 3)} ${paths(10, 10)}")
```

Output: `6 48620`. The same shape handles the longest common subsequence of two strings: carry the previous row of lengths, and build each new row from it and from the cell to its left:

```
fn step(prev: List[Int], acc: List[Int], ys: List[Char], x: Char, j: Int) Int
  if ys(j - 1) == x
    prev(j - 1) + 1
  else
    max(prev(j), acc(j - 1))
fn lcs_row(prev: List[Int], x: Char, ys: List[Char]) List[Int]
  Range(1..=len(ys), 1) |> reduce(List(0), (acc, j) -> acc + step(prev, acc, ys, x, j))
fn lcs(a: String, b: String) Int
  xs = List(c for c in chars(a))
  ys = List(c for c in chars(b))
  last = xs |> to_stream() |> reduce(List(0 for _ in 0..=len(ys)), (prev, x) -> lcs_row(prev, x, ys))
  last(len(ys))
println("${lcs("ABCBDAB", "BDCABA")}")
```

Output: `4`. Memory is the size of what is carried, not of the whole table, and there is no cache to empty. Reach for the next recipe when the subproblems aren't visited in a fixed order. For a recursion that must share work, thread a `Dict` through it as a `ref` parameter and wrap it in a plain `fib(n)` that starts it empty. For a table many fibers share, let one cache fiber (or an `Atom`) own it and answer over channels.

**Chapter 15: Recursive types**

```
enum Tree[T]
  Leaf,
  Node(left: Tree, value: T, right: Tree)
fn size[T](t: Tree[T]) Int
  when t
    Leaf -> 0
    Node(l, _, r) -> size(l) + 1 + size(r)
small = Tree.Node(
  left: Node(left: Leaf, value: 1, right: Leaf),
  value: 2,
  right: Node(left: Leaf, value: 3, right: Leaf)
)
println("${size(small)}")
```

Output: `3`. A bare `Tree` inside its own definition means the same arguments, and a base case (`Leaf`) is required. **[gc]** A tree is an ordinary heap value, so it can be returned, stored in a Dict or an Atom, sent on a channel, and carried through a loop, with no bound. A new tree built from an old one shares its unchanged subtrees.

**Chapter 16: Atoms, channels, futures**

```
counter = Atom[Int](0)
\swap(counter, _ + 1)
rx, tx = Chan[String][1]()
\write(tx, "hello")
when read(rx)
  Ok(msg) -> println("$msg ${@counter}")
  Err(e) -> println("closed")
r, w = Future[Int]()
resolve(w, 42)
when @r
  Pending -> println("waiting")
  Resolved(v) -> println("answer $v")
  Rejected(e) -> println(e.message)
```

Output: `hello 1`, then `answer 42`. The future's two ends have the types `FutureR[Int]` (the read end, `r`) and `FutureW[Int]` (the write end, `w`), just as a channel's ends are `ChanR` and `ChanW`. In `Chan[String][1]`, the first brackets are the element type and the second is the capacity (how many values can wait). **[gc]** The capacity may be any `Int` expression, and `Chan[String][#unbounded]()` never makes a writer wait, at the price of unbounded growth. `swap` applies a function that must not park to the old value, stores the result, and returns the new value. Extra arguments go in with a placeholder call (using `add` from chapter 6):

**Discarding a result.** `\swap(counter, _ + 1)` and `\write(tx, "hello")` start with `\`, which evaluates the rest of the statement and throws the value away. It is how you say a `Result` (or any value) is deliberately ignored, and it means exactly `_ = swap(counter, _ + 1)`, which still works. `\` is valid only at the start of a statement, with an expression after it; `x = \f()` is an error. (A `\` at the *end* of a line is something else: it continues the statement on the next line, as in Python, though a dangling operator or comma or an open bracket usually does the job better.)

```
hits = Atom[Int](0)
a = swap(hits, _ + 1)
b = swap(hits, add(_, 5))
println("$a $b ${@hits}")
```

Output: `1 6 6`. **A function that `run` starts is declared `fiber fn`** (or `fiber[n] fn` to limit how many can be alive at once); `run` on a plain `fn` is a compile error that says so. A fiber function may use `?`, which ends it at the first failure, but the `Result` it returns goes nowhere, since nothing waits for it. An inline `run fn` has no return type, so `?` is an error there. **Several writers.** A channel end moves by default, and `clone(end)` makes another handle to the same channel. A resource you pass to `run` goes to the new fiber, which closes it when it ends, so the name is gone afterward: `run worker(tx)` and then `write(tx, 1)` is a compile error, and a second fiber needs its own `clone(tx)`. If `run` returns NO_SLOT, no fiber starts, and the resources you passed are released for you. The channel closes for readers when the last write handle is dropped:

```
fiber fn worker(id: Int, out: ChanW[Int]) Unit
  \write(out, id * 10)
rx2, tx2 = Chan[Int][3]()
\run worker(1, clone(tx2))
\run worker(2, clone(tx2))
\run worker(3, move tx2)
a = read(rx2).get_or(0)
b = read(rx2).get_or(0)
c = read(rx2).get_or(0)
println("${a + b + c}")
```

Output: `60`. The workers write 10, 20, and 30 in some order, and the three reads add up to 60 either way. **[gc]** `clone` may be used anywhere, loops included. An Atom can hold any value that isn't a resource, closures and other Atoms among them. A resource (a channel end, a file, a socket, a child program, a terminal) has one owner. Passing it to a function that only uses it lends it for the call, as in `println(f, "hi")` or `read_line(c)`. A function that closes it, moves it on, or returns it takes it over, and then the call says so with `move`: `finish(move c)`. The compiler works out which functions take over, so `finish(c)` is an error that tells you to write `finish(move c)`, and after the call `c` is gone: using it again is `use of moved value`. The same goes after `close(c)` and `c.close()`, so closing twice, or reading after closing, is caught before the program runs. A tuple that holds a resource is a resource, and you put one in with `move`, as in `Conn(io: move f)`. A call like `j.finish()` cannot carry a `move`, so when `finish` takes over `j` the call itself ends it. **Mistakes:** `b = tx` for a channel end (write `b = move tx`), and calling `finish(c)` for a function that closes its parameter.

**Chapter 17: Fibers and daemon**

```
fiber fn feed(tx: ChanW[String], msg: String) Unit
  sleep(1s)
  \write(tx, msg)
fn start_feed() ChanR[String]
  rx, tx = Chan[String][1]()
  \run feed(tx, "hello from a fiber")
  rx
inbox = start_feed()
timeout = after(5s)
counter = 0
daemon
  counter = select
    case msg = read(inbox) ->
      text = "got: $msg"
      println(text)
      break daemon
    case read(timeout) ->
      println("timed out")
      break daemon
    else
      sleep(100ms)
      counter + 1
```

Output, about a second later: `got: hello from a fiber`. **[gc]** The string `text` is built on the heap and becomes garbage when the cycle ends, and the collector reclaims it. Nothing is lost between cycles either: any value can be carried over to the next one.

```
last = "none"
daemon
  last = "tick $counter"
```

A short fiber can be written inline. The short form gives only the arguments, and the body uses those names:

```
fn greet(tx: ChanW[String]) Unit
  \run fn (tx) ->
    \write(tx, "hi")
```

The full form puts the arguments first and the parameters second, so the names inside can differ, and an argument can be a literal:

```
fn start_counter(tx: ChanW[Int], start: Int) Unit
  \run fn (tx, start)(out, first) ->
    \write(out, first + 1)
```

Without `run`, the same shape is a function called on the spot, which takes its parameters first (`(x)(5) -> ...`). To wait for fibers, use a `scope` block (17a), or read a result channel or futures until each has reported. **Mistakes:** `after(5s)` inside the daemon (create timers before the loop), an inline fiber body that ends in a value other than `Unit`, `return` in a daemon cycle (before `daemon` in the entry file it ends the program), and a literal in the short form (`run fn (5) ->` needs the full form, `run fn (5)(x) ->`).

**17a. Cancelling fibers, and waiting for them with `scope`**

A fiber that loops forever, such as a worker or a ticker, needs a way to be told to stop. Moxie gives you a `Cancel` token. You pass it to the fiber like any other argument, and the fiber looks at it when it is ready to: `is_cancelled(c)` says whether `cancel(c)` has been called, and `case cancelled(c) ->` is a `select` arm that fires once it has. Cancelling is a request, not a kill: nothing stops a fiber in the middle of a statement, and a fiber that never looks at the token runs on. A `Cancel` copies like an `Atom` handle, and cancelling twice is harmless.

A `scope` block waits for every fiber started inside it (and every fiber those start) before the block ends. `scope name` also binds `name` to the block's own `Cancel`:

```
fiber fn worker(id: Int, out: ChanW[String], stop: Cancel) Unit
  while true
    select
      case cancelled(stop) ->
        \write(out, "worker ${id} stopping")
        return
      else
        sleep(10ms)
rx, tx = Chan[String][4]()
scope s
  \run worker(1, clone(tx), s)
  \run worker(2, tx, s)
  sleep(50ms)
  cancel(s)
println("scope over")
println(read(rx))
println(read(rx))
```

Output: `scope over`, then `Ok("worker 1 stopping")` and `Ok("worker 2 stopping")`. Leaving the block early, with `?`, `return`, `break`, or `continue`, cancels its token first and then waits, so no fiber outlives the block:

```
fn parse(text: String) Result[Int, Error]
  if text == "" then fail(7, "no input") else Ok(1)
fn job(out: ChanW[String]) Result[Int, Error]
  scope s
    \run worker(1, out, s)
    n = parse("")?
    Ok(n)
```

Here `job` returns the error only after the worker has seen the cancel and finished. Reaching the end of a `scope` normally does not cancel anything, so call `cancel(s)` yourself when a fiber would otherwise run forever. A fiber parked in a plain `read` or `sleep` can't see the token, so for fibers that must stop promptly wait in a `select` with a `cancelled` arm, and use `after(d)` for a sleep that can be cut short. A `scope` parks, so it can't be in a pure function, and an abort in any fiber still ends the whole program.

**Chapter 18: Errors and `?`**

There is no `try`: a failing operation returns a `Result`.

```
fn fetch_first(id: Int) Result[Int, Error]
  if id < 0
    fail(7, "negative id")
  else
    Ok(10)
fn fetch_total(id: Int) Result[Int, Error]
  a = fetch_first(id)?
  b = fetch_first(id + 1)?
  Ok(a + b)
when fetch_total(5)
  Ok(t) -> println("total $t")
  Err(e) -> println("failed: ${e.message}")
fallback = fetch_first(-1).get_or(0)
println("$fallback")
```

Output: `total 20`, then `0`. With `fetch_total(-5)`, the first `?` returns the error, giving `failed: negative id`. A `Result` of a tuple forwards field access, so the error rides along:

```
tuple User
  id: Int,
  name: String
fn find_user(id: Int) Result[User, Error]
  if id == 1 then Ok(User(id: 1, name: "Ada")) else fail(2, "no user")
for id in List(1, 9)
  when find_user(id).name
    Ok(n) -> println(n)
    Err(e) -> println(e.message)
```

Output: `Ada`, then `no user`. **Typed errors.** The error type can be your own enum, and `?` converts from another error type through a visible `From` impl, one hop:

```
enum ParseError deriving show
  Empty,
  BadDigit(ch: Char)
enum AppError deriving show
  Parse(why: ParseError),
  TooOld(limit: Int)
impl From[ParseError] for AppError
  static fn from(e: ParseError) AppError
    Parse(why: e)
fn parse_age(text: String) Result[Int, ParseError]
  if text == "" then Err(Empty) elif text == "ancient" then Ok(150) else Ok(30)
fn check_age(text: String) Result[Int, AppError]
  age = parse_age(text)?
  if age > 99 then Err(TooOld(limit: 99)) else Ok(age)
for t in List("30", "", "ancient")
  when check_age(t)
    Ok(a) -> println("age $a")
    Err(e) -> println("$e")
```

Output: `age 30`, then `AppError.Parse(ParseError.Empty)`, then `AppError.TooOld(99)`. In `check_age`, `parse_age(text)?` has the error type `ParseError`, so the compiler wraps it with `AppError.from` before returning. With no matching impl it is a compile error; when both error types are the same, nothing is converted. In the entry file, before `daemon`, `?` on an `Err` prints the error's diagnostic and exits with a non-zero status. **Mistakes:** `?` in a function that doesn't return a `Result` (or in a fiber or a daemon cycle), matching only `Ok`, and expecting `?` to chain two conversions.

**18a. `Option`: a value or nothing**

Not every miss is an error. The prelude has `Option[T]`, with the cases `Some(value)` and `None`, written bare as `Ok` and `Err` are. `?` works on it the same way: it gives the value of a `Some`, or returns `None` from the function.

```
fn half(n: Int) Option[Int]
  if n % 2 == 0 then Some(n / 2) else None
fn quarter(n: Int) Option[Int]
  h = half(n)?
  half(h)
println(quarter(8))
println(quarter(6))
println(get_or(quarter(3), -1))
for o in List(Some(1), None)
  when o
    Some(v) -> println("got $v")
    None -> println("nothing")
```

Output: `Some(2)`, then `None`, then `-1`, then `got 1`, then `nothing`. A `when` on an `Option` must cover both cases. `?` on an `Option` in a function that returns a `Result` (or the reverse) is a compile error, since nothing converts silently. The helpers are `is_some(o)`, `is_none(o)`, and `get_or(o, default)`; `map`, `flat_map`, and `|>>` come from its `Monad` impl (chapter 8d), so `half(8) |>> half |>> half` is `Some(1)`. It derives `eq`, `show`, and `read`, so `read[Option[Int]]("Some(7)")` works. The standard library keeps returning `Result`; `Option` is for your own code and new libraries. Use `Result` when the miss is a failure the caller should hear about, and `Option` when absence is normal.

**Chapter 19: Packages**

`Moxie.toml`:
```
name = "app"
files = ["util.mxi", "main.mxi"]
entry = "main.mxi"
```

`util.mxi`:
```
export greeting: String = "hello"
internal retry_limit = 3
```

`main.mxi`:
```
import util
println(util.greeting)
```

Output: `hello`. A package of several files has a folder with a `Moxie.toml` that lists them (`files = ["base.mxi", "area.mxi"]`); the files share the package's names in that order, and `import shapes` finds the folder. A single file needs no manifest at all, and in a folder with a `main.mxi` (or a `Moxie.toml` with an `entry`) you can run it with just `moxie run`. Everything is linked statically from source and unreachable code is pruned, a link report lists what each package contributed, and a lockfile records dependency hashes. **Mistake:** `util.retry_limit` from another package is an error, because it is `internal`.

**Chapter 20: Arguments and environment**

```
when get(args, 0)
  Ok(first) -> println("first argument $first")
  Err(e) -> println("no arguments")
editor = env("EDITOR").get_or("vi")
println("editor $editor")
```

`args` is an array, so `args(0)` aborts when no argument was given; `get(args, 0)` returns a `Result`. `env("EDITOR")` returns a `Result` (MISSING when unset), and `.get_or("vi")` supplies a default. With no arguments and no `EDITOR`, the output is `no arguments` and `editor vi`. **Mistake:** `args(0)` without a check, and `set_env` (there is none).

**20a. Standard input and output**

`stdin`, `stdout`, and `stderr` are values the runtime owns. Any function can take one as a parameter, which is how output code gets tested:

```
fn greet(out: Io, name: String) Unit
  println(out, "hello, $name")
greet(stdout, "mixer")
greet(stderr, "mixer")
```

Output: `hello, mixer` on standard output, and the same line on standard error. `print` and `println` with no stream write to `stdout`, and `eprint` and `eprintln` write to `stderr`. Reading is `read_line()`, which returns a `Result` (the line without its newline), `read_all()`, and `stdin_lines()`, a stream of lines. They all `parks`: only the fiber that waits is held up. `with_stdin(text, f)` runs `f` with `text` as the input, so a test can feed a program:

```
fn ask(question: String) String
  print("$question ")
  read_line().get_or("nobody")
answer = with_stdin("Ada\n", fn () -> ask("name?"))
println("hi $answer")
```

Output: `name? hi Ada`. A stream of lines goes through the usual pipeline functions:

```
fn read_total() Int
  stdin_lines() |> map((s) -> read[Int](s).get_or(0)) |> reduce(0, _1 + _2)
total = with_stdin("3\n4\n5\n", read_total)
println(total)
```

Output: `12`. End of input is not a crash. `read_line()` returns `Err` with the code `CLOSED`:

```
when with_stdin("", read_line)
  Ok(line) -> println("got $line")
  Err(e) -> println("end of input: ${e.message}")
```

Output: `end of input: end of input`. Text is UTF-8, and input that is not gives `Err` with `BAD_ENCODING`. **Mistake:** `close(stdout)`, which aborts because closing it would silence every later `println`.

**20b. Files and sockets**

A file and a network connection are the same kind of value, an `Io`, so code that reads lines does not care which it was given. `open_file(path, mode)` takes `ReadOnly`, `Create`, `Append`, or `ReadWrite`; `read_file` and `write_file` do a whole small file in one call:

```
write_file("notes.txt", "one\ntwo\n")?
f = open_file("notes.txt", Append)?
println(f, "three")
close(f)
r = open_file("notes.txt", ReadOnly)?
n = lines(r) |> map(len) |> reduce(0, _1 + _2)
close(r)
println("$n letters, ${len(read_file("notes.txt")?)} bytes")
```

Output: `11 letters, 14 bytes`. Paths use `/` on every system, and a write to a file is buffered until `flush` or `close`. An `Io` must be closed, like any resource, and the runtime closes one that is still open when the program ends. moxie/gc has no pools, so there is nothing to size; the runtime still closes any `Io` or `Listener` left open when the program ends, and `moxie --pools run FILE` still prints the most of each that were open at once. Failures are ordinary `Err` values with the reserved codes `NOT_FOUND`, `DENIED`, and `IO_ERROR`:

```
when read_file("missing.txt")
  Ok(t) -> println(t)
  Err(e) -> println("code ${e.code}, not found: ${e.code == NOT_FOUND}")
```

Output: `code 9, not found: true`. Sockets work the same way: `listen(port)` gives a `Listener` (port 0 picks a free one, and `port_of` says which), `accept` waits for a client, and `connect(host, port)` is the client side. A server and a client can run as two fibers of one program, because `accept` and `read_line` park only their own fiber:

```
fiber fn server(tx: ChanW[Int]) Result[Unit, Error]
  l = listen(0)?
  \write(tx, port_of(l))
  c = accept(l)?
  println(c, "hello from server")
  close(c)
  close(l)
  Ok(())
rx, tx = Chan[Int][1]()
run server(tx)
c = connect("127.0.0.1", read(rx)?)?
println(read_line(c)?)
close(c)
```

Output: `hello from server`. **Mistake:** writing to a file after `close`, which aborts, and forgetting that `connect` can fail: it returns a `Result`.


Directories and paths have their own small set of functions. All of them take `/`-separated `String` paths and return a `Result` when the system can refuse: `make_dir(path)` creates a directory and any missing parents (and is fine if it already exists), `list_dir(path)` gives the names in it as a sorted `Array[String]`, `file_info(path)` gives a `FileInfo` with `kind` (`"file"`, `"dir"`, or `"other"`), `size`, and the methods `is_file()` and `is_dir()`, `path_exists(path)` gives `Ok(true)` or `Ok(false)`, `rename_path(from, to)` moves a file or directory (replacing a file at the target), and `remove_file(path)` and `remove_dir(path)` delete a file and an empty directory. Five functions work on the text of a path and touch nothing, so they need no permission and cannot fail: `path_join(base, rest)`, `path_parent(p)`, `path_name(p)`, `path_stem(p)`, and `path_ext(p)`:

```
make_dir("out/logs")?
write_file(path_join("out", "report.txt"), "done")?
write_file("out/logs/run.log", "ok")?
println(list_dir("out"))
for name in list_dir("out")?
  info = file_info(path_join("out", name))?
  println("${name}: ${info.kind}")
p = "out/logs/run.log"
println("${path_parent(p)} ${path_name(p)} ${path_stem(p)} ${path_ext(p)}")
rename_path(p, "out/run.old")?
println(list_dir("out/logs"))
```

Output: `Ok(Array("logs", "report.txt"))`, then `logs: dir`, `report.txt: file`, then `out/logs run.log run log`, then `Ok(Array())`. Reading a directory needs `fs.read` and changing one needs `fs.write` (a rename needs it for both paths), as for files. `remove_file` refuses a directory and `remove_dir` refuses one that is not empty, with `IO_ERROR`; a missing path is `NOT_FOUND`. **Mistakes:** treating a name from `list_dir` as a path (join it with its directory first), and using `\` as a separator: paths use `/` on every system.


For a connection that must be private, `connect_tls(host, port)` is `connect` over TLS, the protocol behind `https`: the server proves who it is with a certificate, the data is encrypted, and the result is the same `Io`, so `read_line`, `println(io, ...)`, and `close` work as before. The certificate is checked against the system's trusted authorities and against the name you gave, and one that fails is an `Err` (code `IO_ERROR`, with a message such as `certificate not trusted`), never a connection with a warning. To trust a particular certificate, such as your own server's, pass its file with `ca`, which needs `fs.read`. The server side is `listen_tls(port, cert_file, key_file)`, which gives a `Listener` whose `accept` finishes the handshake before it returns the `Io`:

```
// not run: needs a server and its certificate
c = connect_tls("example.com", 443)?
println(c, "GET / HTTP/1.0\r\nHost: example.com\r\n")
println(read_line(c)?)
close(c)

// the server side, with a certificate you made yourself
l = listen_tls(8443, "cert.pem", "key.pem")?
c = accept(l)?
println(c, "hello over tls")
close(c)
close(l)
```

`connect_tls` is checked against `net.connect` as `connect` is, and `listen_tls` against `net.listen`, plus `fs.read` for the certificate and key files. A client that trusts a self-made certificate passes `ca: "cert.pem"`. **Mistakes:** turning to plain `connect` to get around a certificate error (fix the certificate or pass `ca`), and a certificate whose name does not match the host you connect to: the check is on the name, so use the name in the certificate.

**UDP.** TCP gives you a connection and a stream of bytes. UDP gives you separate datagrams: each `send_to` is one packet, each `receive` gets one packet, and packets may arrive out of order, more than once, or not at all. A `Udp` socket comes from `bind_udp(port)` (port 0 picks a free port, and `port_of` says which):

```
// not run: needs a peer
sock = bind_udp(5300)?
p = receive(sock, timeout: 2s)?
println("${p.host}:${p.port} sent ${len(p.data)} bytes")
\send_to(sock, p.host, p.port, p.data)
close(sock)
```

`receive` parks only its own fiber and returns a `Packet` (`host`, `port`, and `data`, an `Array[Byte]`). The `timeout:` argument turns a wait into an `Err` after that long, which is how a program notices a lost packet. `send_to` takes the bytes as an `Array[Byte]` or a `String` (sent as UTF-8), and a datagram holds at most 65507 bytes. `bind_udp` is checked against `net.listen` and `send_to` against `net.connect`. A `Udp` is a resource like an `Io`: close it, or the runtime closes it when the program ends. **Mistakes:** treating a datagram as a stream (one `receive` is one `send_to`, never half of one), waiting with no `timeout:` for a packet that may have been lost, sending more than one datagram can hold, and passing a `Udp` to `read_line`.

**Waiting with a deadline.** Every call that can wait on the outside world takes `timeout:`, a `Duration`: `read(ch, timeout: d)`, `accept`, `connect`, `wait_child`, `read_line` on a socket, and the `receive` and `run_command` above. When the time passes with nothing to show, the call returns `Err` with the reserved code `TIMED_OUT`, so a timeout is never confused with a dropped connection (`IO_ERROR`) and `retry` treats it as worth another try. A timeout gives up waiting; it does not undo anything, so a `run_command` that times out has had its program killed, and a `read` that times out has taken nothing from the channel. `read_line` waits for data to arrive, not for a whole line, and it can't time out on standard input (that is a runtime error); to stop a loop over `lines`, read with `read_line` and a timeout instead.

```
rx, tx = Chan[Int][1]()
println(read(rx, timeout: 50ms))
\write(tx, 7)
println(read(rx, timeout: 50ms))
r = run_command("sleep", List("2"), timeout: 100ms)
when r
  Err(e) -> println("code ${e.code}")
  Ok(_) -> println("finished")
println(retry(3, 10ms, fn () -> read(rx, timeout: 10ms)))
close(tx)
```

Output: `Err(Error(code: 12, message: "read: timed out"))`, `Ok(7)`, `code 12`, then the first line's `Err` again. An anonymous function that parks is written `fn () = ...`, as a plain lambda must be pure.

**Racing and time limits.** `timeout:` covers the calls that wait on the outside world. For your own work, `race(f, g)` runs two functions at once and gives the result of whichever finishes first, and `with_timeout(d, f)` runs `f` and gives `Err` with `TIMED_OUT` if it is still going after `d`. Each function takes a `Cancel` token, because in moxie stopping is a request: when `race` has a winner it sets the token, and when `with_timeout` runs out of time it sets it, and the other function ends only if it looks (`is_cancelled(c)`, or `case cancelled(c) ->` in a `select`). Both are structured, like `scope`: they wait for the slower function to end before they return, so none outlives its call, and a function that never looks at its token delays the return until it finishes. `race` gives whatever finished first, an `Err` included, and the two functions must have the same result type. `with_timeout` takes a function that gives `Result[T, Error]` and gives the same type back, so `TIMED_OUT` joins the reserved errors you already handle (use `race` when your errors have another type). Each call site counts against the program's fibers (2 for `race`, 1 for `with_timeout`), which `moxie pools` shows. A function that waits or prints is written `fn name(c: Cancel) ...`; a plain lambda must be pure.

```
fn polite(c: Cancel) Result[Int, Error]
  while true
    select
      case cancelled(c) ->
        return Err(Error(CLOSED, "cancelled"))
      else
        sleep(5ms)
  Ok(0)
fn quick(c: Cancel) Result[Int, Error]
  sleep(10ms)
  Ok(42)
println(race(polite, quick))
println(with_timeout(1s, quick))
println(with_timeout(50ms, polite))
```

Output: `Ok(42)`, `Ok(42)`, then `Err(Error(code: 12, message: "with_timeout: timed out"))`.

**Doing the work in parallel.** `par_map(f, xs, limit: n)` calls `f` on every item, at most `n` at a time, each call in its own fiber, and gives the results as a `List` in the order of the input, however the calls finish. It pays off when `f` mostly waits (a network call, a file, a program) or when the work spreads across cores; for a quick calculation, plain `map` is faster, because starting a fiber costs more than the work. `limit:` is a number the compiler can see (a literal, or a top-level constant), the same rule as a channel's capacity, and for the same reason: the program's fibers are counted before it runs, and each `par_map` call adds `n` to the count that `moxie pools` shows. `par_traverse(f, xs, limit: n)` is `traverse` for the same job, for an `f` that gives a `Result`. When an item fails it stops starting new items, lets the running ones finish, and gives the `Err` of the earliest failing item, so the answer does not depend on timing: items start in input order, so every item before a failure has run. Both park, and the order of any output the calls print is up to the scheduler. The items and what `f` uses must be plain data: a resource is owned by one fiber.

```
fn slow_double(n: Int) Int
  sleep((6 - n) * 10ms)
  n * 2
fn check(n: Int) Result[Int, String]
  sleep((6 - n) * 10ms)
  when n % 2 == 0
    true -> Err("even ${n}")
    false -> Ok(n)
println(List(1, 2, 3, 4, 5) |> par_map(slow_double, limit: 3))
println(par_traverse(check, List(1, 3, 5), limit: 2))
println(par_traverse(check, List(1, 2, 3, 4, 5), limit: 5))
```

Output: `List(2, 4, 6, 8, 10)`, `Ok(List(1, 3, 5))`, then `Err("even 2")`, though the later items finish first.

**Unix sockets and named pipes.** Programs on the same machine can talk without the network. A Unix socket works like the TCP ones, but the address is a file path:

```
fiber fn serve(l: Listener) Result[Unit, Error]
  c = accept(l)?
  for line in lines(c)
    println(c, "echo $line")
  close(c)
  Ok(())

init
  path = temp_dir() + "/demo.sock"
  l = listen_unix(path)?
  \run serve(move l)
  c = connect_unix(path)?
  println(c, "hi")
  println(read_line(c)?)
  close(c)
```

Output: `echo hi`. `listen_unix` gives a `Listener` and `connect_unix` gives an `Io`, so `accept`, `lines`, `println`, and `close` work as they do on TCP. The socket file appears when you listen and goes away when the `Listener` is closed or the program ends; if a crash left one behind, `listen_unix` says `IO_ERROR` and `remove_file` clears it. Both calls need `fs.write` on the path.

A **named pipe** is a file that two programs open to pass bytes. `make_fifo(path)` creates it, and `open_file` opens one end: `ReadOnly` to read, `Create` to write. Opening waits until the other program opens its end, and only your fiber waits.

```
// not run: needs another program
make_fifo("jobs.pipe")?
r = open_file("jobs.pipe", ReadOnly)?
for line in lines(r)
  println("job: $line")
close(r)
remove_file("jobs.pipe")?
```

A reader sees `CLOSED` when the writer closes its end, so the loop above ends by itself. A write waits when the pipe is full. Neither exists in the browser. Fibers inside one program should use channels, not pipes: a channel is typed, counted, and checked, and a pipe is for talking to another program. A fiber waiting on a socket or pipe does not stop the others, and a `sleep` in another fiber keeps counting down, so a watchdog fiber that sleeps and then calls `exit` works while you wait. **Mistakes:** opening a pipe for reading and writing at once (`ReadWrite` is refused), and forgetting that a reader waits for a writer to open its end.

**Watching files.** To react when something on disk changes, such as a build that reruns on save, ask for a channel of changes:

```
// not run: waits for a change
rx = watch("src")?
for change in rx
  println("${change.kind} ${change.path}")
```

`watch` gives a channel of `FileChange` values. Each has a `path` and a `kind`, which is `#created`, `#modified`, or `#deleted`. A file reports changes to itself, and a directory reports changes to the files directly inside it (a subdirectory shows up when it is created or deleted, not when something inside it changes). The loop waits for the next change and only your fiber waits, so other fibers keep running, and a `sleep` in one of them keeps counting. `close(rx)` stops the watching. Moxie looks every tenth of a second, so a burst of changes arrives together, and a file written twice within that time may report once. If you read more slowly than changes arrive, some are dropped and a warning at exit says how many. It needs `fs.read` on the path, and it is not available in Try moxie. **Mistakes:** expecting a change inside a subdirectory to be reported, and expecting an event per write.

**20c. Permissions**

A program that was not given a permission cannot use it. The permissions are `fs.read` and `fs.write` (paths), `net.connect` (`host:port`), `net.listen` (ports), `ffi` (native libraries), `process` (programs to run), `stdin`, and `env`. Printing to `stdout` and `stderr` and reading `args` are always allowed. They are granted in the manifest:

```
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

With no `[permissions]` table and no flag a program is unrestricted, as a script is; any table or flag restricts it to what is granted, and `--deny-all` grants nothing. A call outside a grant returns `Err` with `DENIED` and a message that names the call and the permission: `read_file("other/b.txt")` under `--allow-read=data` is `Err(Error(code: 10, ...))`, and a path that climbs out with `..` is refused too. The compiler also follows the permissions through function calls, as it does effects. If `main` can reach `read_file` and nothing grants a file permission, `moxie check` and `moxie run` stop with a compile error such as `'read_file' needs fs.read or fs.write, which is not granted (Moxie.toml)`, before anything runs. The same analysis follows calls into imported packages, so `lib.read_config()` counts as a file read in the program that calls it, and a restricted program that reaches it is stopped before it runs; a package function you never call adds nothing. It checks the kinds and the libraries, not the paths, which depend on values and are checked when the call is made. A package can be given less than the program. Add a table named for the package inside `[permissions]`:

```
[permissions]
all = true

[permissions.packages.reader]
fs.read = ["data"]
```

Code written in `reader` can then read only under `data`, whatever the program grants; an empty table gives it nothing, and a package with no table gets what the program has. The rule follows where the code is written: a function the program hands to `reader` keeps the program's rights. A denied call says which package was refused (`... fs.read is not permitted for package reader`), and `moxie check` finds a package that reaches more than its table allows before anything runs, as `package 'reader' (reader.mxi:1): 'read_file' needs fs.read or fs.write, which is not granted to it`. Flags replace the program's grants but not the package tables. **Mistake:** granting `ffi` for convenience: a native library runs with all the rights of the process, so the permissions guard against mistakes in moxie code, not against hostile C.

**20d. Calling C**

A `foreign` block declares C functions by signature. Every function says what it does to the world (`pure`, `prints`, `parks`, or `impure`), because the compiler cannot look inside C, and after that it is called like any function:

```
foreign "m"
  pure fn cos(x: Double) Double
  pure fn pow(x: Double, y: Double) Double
println(cos(0.0))
println(pow(2.0, 10.0))
```

Output: `1.0`, then `1024.0`. A `ref` parameter is a C out-parameter: the value goes in, and the result is copied back when the call returns:

```
foreign "m"
  pure fn frexp(x: Double, ref exp: Int32) Double
e = 0i32
m = frexp(8.0, ref e)
println("$m $e")
```

Output: `0.5 4`. An `Array` of any number type is passed as a pointer. A parameter written `n: UInt = len(base)` is C's length, filled in by the call, and `size: UInt = size_of(base)` is the element size. A parameter of function type is a C callback for the length of the call, and `Ptr[T]` in the callback's type is a `const T *` that arrives as the value. That is enough to declare `qsort` and call it with a closure:

```
foreign "c"
  impure fn qsort(
    ref base: Array[Int32],
    n: UInt = len(base),
    size: UInt = size_of(base),
    cmp: (Ptr[Int32], Ptr[Int32]) -> Int32
  )
xs = Array(5i32, 3i32, 9i32, 1i32, 7i32)
qsort(ref xs, (a, b) -> a - b)
println(xs)
```

Output: `Array(1, 3, 5, 7, 9)`. Text crosses as a `CString`, made by `cstr(text)`. The usual habit is to keep the raw declaration to yourself and export a wrapper that speaks moxie:

```
foreign "c"
  pure fn strlen(s: CString) UInt
fn byte_length(text: String) UInt = strlen(cstr(text))
println(byte_length("héllo"))
```

Output: `6`, because `é` is two bytes in UTF-8. A library that hands back an opaque pointer, such as a database, is declared as a **handle**, with the function that closes it. A handle is a resource: move-only, closed once, and the compiler rejects use after the close. The runtime closes any handle still open when the program ends.

```
foreign "store"
  handle Store closes store_close
  impure fn store_open(path: CString) Result[Store, Error]
  impure fn store_get(s: Store, key: CString) Int32
  impure fn store_close(s: Store)
s = store_open(cstr("data.db"))?
println(store_get(s, cstr("answer")))
store_close(move s)
```

A function that returns `Result[Store, Error]` gives `Err(MISSING)` when C returns NULL. Two more shapes cover the rest of the usual C habits. A callback that C **keeps** and calls later, perhaps from a thread of its own, cannot run moxie code on that thread, so it becomes a message: declare `cb: Events[Int32]` and pass the write end of a channel with `move`, and a fiber reads the events with `read`. If C needs an **answer** from the kept callback, declare `cb: Handler[(Int32) -> Int32]` and pass a function; when C calls from its own thread, the function runs in a fiber of its own (it may sleep or read), and the C thread waits for the result. A foreign function that waits for such a thread must be declared `parks`:

```
foreign "sensor"
  impure fn on_reading(cb: Events[(Int32, Double)])
  impure fn on_query(cb: Handler[(Int32) -> Int32])
rx, tx = Chan[(Int32, Double)][16]()
on_reading(move tx)
on_query((id) -> id * 2i32)
for i in 1..=3
  println(read(rx)?)
```

`moxie bindgen` writes the declarations from a C header, so nobody types them by hand; `--wrap` also writes default wrappers (a `String` for each `CString`, a `Result` for the common `int` status with out-parameters), and `bindgen.toml` holds the corrections:

```
$ moxie bindgen sensor.h --package sensorx --lib sensor --wrap
```

```
[functions.sensor_subscribe]
keeps = ["cb"]
```

**Mistake:** a declaration that does not match the real C signature (an `Int32` where C takes a `Double`) is not detected, because the compiler cannot see C. Wrap every foreign call and test the wrapper. A package may contain `foreign` blocks only when its manifest has a `[native]` section, which lists the libraries it may name and where to look for them: `[native]`, `libs = ["z"]`, `paths = ["native"]`. A missing section, or a library the section does not list, is a compile-time error that says what to add.

**20e. The clock, random numbers, exit, and signals**

Time is a `Duration`. `monotonic()` never goes back, so use it to measure; `now()` is the wall clock as a `Duration` since 1970. A duration converts out with `nanos`, `millis`, and `seconds`:

```
t0 = monotonic()
sleep(50ms)
elapsed = monotonic() - t0
println("slept at least 50ms: ${elapsed.millis() >= 50}")
println("it is after 2023: ${now().seconds() > 1.7e9}")
```

Output: `slept at least 50ms: true`, then `it is after 2023: true`. Random numbers come in two kinds. `random()` and `random_int(lo, hi)` are for games and sampling, and `random_bytes(n)` comes from the operating system's secure source, so use it for tokens and keys. `seeded(n)` gives a reproducible source that the generator functions from property tests (`gen_int`, `gen_pick`, `sample[T]`) read:

```
g = seeded(7)
h = seeded(7)
println(gen_int(g, 1, 6) == gen_int(h, 1, 6))
println(len(random_bytes(16)))
```

Output: `true`, then `16`. A password or token should be wrapped in a `Secret`, so that it can't reach a log by accident:

```
token = secret(env("API_TOKEN").get_or("none"))
println("using ${token}")
println(secret_eq(token, secret("none")))
```

Output: `using Secret(***)`, then `true` when the variable is unset. Printing, interpolating, and `show` all give `Secret(***)`. `reveal(token)` is the one way to the real value, so each place it is used shows in the source, and `==` on secrets is an error: compare with `secret_eq`, which takes the same time however many characters match. A `Secret[String]` is not a `String`, so a function that takes one can't be handed plain text by mistake. `exit(code)` ends the program with a code from 0 to 255, from any fiber, and `signals()` gives a channel of `#interrupt`, `#terminate`, and `#hangup` so a program can shut down cleanly when someone presses Ctrl-C:

```
fiber fn work(done: ChanW[Int]) Unit
  sleep(1s)
  \write(done, 1)

rx = signals()
done_r, done_w = Chan[Int][1]()
\run work(done_w)
select
  case read(rx) -> exit(130)
  case read(done_r) -> println("finished")
```

A program that has called `signals` no longer stops on Ctrl-C by itself, so it must read the channel. `cwd()`, `home_dir()`, `temp_dir()`, `hostname()`, and `os_name()` describe where the program runs, `is_terminal(stdout)` and `terminal_size()` say whether a person is watching, `lookup_host(name)` resolves a name, and `make_temp_file(prefix)` makes a file in the temporary directory and returns its path. These calls count as **uses the system** for effects, so a `pure fn` can't call them. Section 19e of the Spec lists them. **Mistakes:** using `random` for a password or token (use `random_bytes`), reading `now()` twice to time something (use `monotonic`, which does not jump when the clock is set), and a program that calls `signals` and then never reads the channel.

**In Try moxie.** The page on the site runs in a browser, so it has no network, no native libraries, no signals, and files that live in memory only. A program that reaches one is refused when it is checked, with a message such as `'signals' is not available in the browser`, and `moxie --platform=browser check FILE` shows the same answer on your own computer. The clock, random numbers, `exit`, temporary files, and `os_name()` (which says `"browser"` there) all work.

**20f. Running other programs**

`run_command` runs a program to the end and gives back what it printed. There is no shell, so you pass the program's name and its arguments as a list, and nothing in them is ever interpreted:

```
r = run_command("echo", List("hello", "world"))?
println("exit ${r.code}: ${r.stdout.trim()}")
```

Output: `exit 0: hello world`. A program that runs and fails is still `Ok`, with the failure in `code`, so check it: `r.code ~= 0`. `Err` is for a program that could not run at all, such as one that isn't installed (`NOT_FOUND`). `stdin:` sends text to the program, `cwd:` picks its directory, `env:` replaces its environment, and `timeout:` kills it after a `Duration`:

```
r = run_command("sort", stdin: "pear\napple\n", timeout: 5s)?
println(r.stdout)
```

For a program that talks over time, `spawn` starts it and gives you a `Child`. Its input and output are ordinary `Io` values, so the file and socket functions work on them. Close the input when you are done writing, then wait:

```
c = spawn("sort")?
tx = child_stdin(c)
println(tx, "pear")
println(tx, "apple")
close(tx)
println(read_all(child_stdout(c))?)
println(wait_child(c)?)
close(c)
```

Waiting parks only your fiber, so others keep running. A program needs the `process` permission, written `process = ["git", "sort"]` in `Moxie.toml` or `--allow-run=git,sort` on the command line, and the child gets only the environment your program could see. **Mistakes:** building a command line as one string (there is no shell to split it, so pass a list), ignoring `r.code`, forgetting to close the input before reading a program that reads until end of file, and expecting Try moxie to run programs (it can't).

**20g. Dates and times**

`now()` is a moment, a `Duration` since 1970. To show it to a person, turn it into a `DateTime`, a plain record of year, month, day, hour, minute, second, and nanosecond. `to_utc` gives UTC, `to_local` gives your computer's zone, and `to_zone` takes a zone name and returns a `Result`, since the name might not exist:

```
t = 1700000000s
println(iso(to_utc(t)))
la = to_zone(t, "America/Los_Angeles")?
println(format_time(la, "%A, %B %e at %I:%M %p"))
```

Output: `2023-11-14T22:13:20`, then `Tuesday, November 14 at 02:13 PM`. Going back is `to_instant(dt, zone)`, which gives a `Result` because `DateTime(2026, 2, 30)` is not a day. A `DateTime` has no zone of its own, so pass the zone when you convert one to a moment. `parse_time` and `parse_iso` read text, and both return `Err` for text that does not fit or a date that does not exist:

```
d = parse_time("04/11/2026 16:55", "%d/%m/%Y %H:%M")?
println(iso(d))
println(weekday(d))
println(parse_iso("2026-02-30"))
```

Output: `2026-11-04T16:55:00`, `3` (Wednesday; Monday is 1), then an `Err` that says February 2026 has no day 30. There is no date arithmetic on a `DateTime`. To add days, go through the moment, and remember that a day here is always 24 hours:

```
d = DateTime(2026, 12, 30)
later = (to_instant(d)? + 3 * 24h).to_utc()
println(iso(later))
```

Output: `2027-01-02T00:00:00`. All of these are pure except `to_local`, which depends on the computer it runs on. **Mistakes:** parsing a time with an offset such as `+02:00` with `parse_iso` (it refuses, since a `DateTime` has no zone), using `to_local` where a test needs the same answer everywhere, and adding a month by adding 30 days.

**20h. Reading single keys**

`read_line` waits for Enter. A menu, a game, or a pager wants each key as it is pressed, and for that you open the terminal in raw mode:

```
// not run: needs a terminal
init
  t = raw_terminal()?
  println("press keys; Escape quits")
  while
    when read_key(t)?
      Typed(c) -> println("typed \$c")
      Ctrl(c) -> println("ctrl-\$c")
      Up -> println("up")
      Down -> println("down")
      Fn(n) -> println("F\$n")
      Escape -> break
      else ()
  close(t)
```

`raw_terminal()` gives you a `Terminal`. Nothing is echoed and there is no line editing, so the program decides what to show. `read_key(t)` waits for one key and returns a `Key`: `Typed(c)` for a character (accented letters too), `Ctrl(c)` for a Ctrl combination, `Alt(c)`, `Fn(n)`, and names such as `Enter`, `Backspace`, `Escape`, the arrows, `Home`, `End`, `PageUp`, and `PageDown`. Only your fiber waits, so others keep running. In raw mode Ctrl-C is just a key, `Ctrl("c")`, so a program must choose to quit on it. Call `close(t)` when you are done; the terminal is put back even when the program ends early or aborts, so a crash does not leave the mixer's shell without echo.

`raw_terminal()` is `Err` with `MISSING` when input is not a terminal, as when the program runs with piped input, so check for that if it might. It needs `stdin`, and it is not available in Try moxie. **Mistakes:** assuming Ctrl-I, Ctrl-M, and Ctrl-H are separate from `Tab`, `Enter`, and `Backspace` (the terminal sends the same byte), and forgetting that nothing is echoed, so the program must print what the mixer typed.

**Chapter 21: A DSL without macros**

A builder is a set of ordinary functions, and nesting is nested calls. Nominal tuples give type safety. **[gc]** A variadic parameter is a `List`, so `join` takes one:

```
tuple Html
  text: String
tuple Li
  text: String
fn join(parts: List[Html]) String
  parts |> to_stream() |> map(_.text) |> reduce("", _1 + _2)
fn h1(text: String) Html
  Html(text: "<h1>$text</h1>")
fn li(text: String) Li
  Li(text: "<li>$text</li>")
fn ul(items: ...Li) Html
  inner = items |> to_stream() |> map(_.text) |> reduce("", _1 + _2)
  Html(text: "<ul>$inner</ul>")
fn body(children: ...Html) Html
  Html(text: "<body>${join(children)}</body>")
fn html(child: Html) String
  "<html>${child.text}</html>"
page = html(
  body(
    h1("Welcome to moxie"),
    ul(
      li("fast"),
      li("small")
    )
  )
)
println(page)
```

Output: `<html><body><h1>Welcome to moxie</h1><ul><li>fast</li><li>small</li></ul></body></html>`. **Mistake:** `ul(h1("x"))` is a compile error, because `ul` takes only `Li` items. A macro system isn't needed, and moxie has none.

**Chapter 22: SQL**

The manifest names the schema, and the compiler checks every query against it:

```
[database]
schema = "schema.sql"
driver = "postgres"
```

You open a connection in the entry file with `Connection.open(path)`, which returns a `Result[Connection, Error]`, so `conn = Connection.open(args(0))?` is the usual line. `Connection.memory()` opens a throwaway in-memory database, handy in tests. The examples below receive `conn` as a parameter.

```
tuple Telemetry
  id: Int,
  value: Double
inline fn fetch_active_telemetry(
  conn: Connection,
  min_value: Double
) Result[Stream[Telemetry], Error]
  sql(conn):
    SELECT id, value FROM telemetry
    WHERE value >= $min_value AND active = true
    ORDER BY id
rows = fetch_active_telemetry(conn, 0.5)?
for t in rows
  println("${t.id}: ${t.value}")
```

`$min_value` is a bound parameter, so there is no injection. The accepted SQL is a subset: SELECT with WHERE, JOIN, GROUP BY, the aggregates COUNT, SUM, MIN, and MAX, ORDER BY, LIMIT, and OFFSET, plus INSERT, UPDATE, and DELETE. The result is a `Result` of a lazy stream that borrows `conn` (so the helper is `inline fn`), and each row is a named tuple of the selected columns. Writes return the rows affected, and configuration is read in the entry file before `daemon` (`sql` is not allowed at module level or in `init`):

```
fn load_config(conn: Connection) Result[Dict[String, String], Error]
  rows = sql(conn):
    SELECT key, value FROM config
  rows? |> collect()
```

A **transaction** commits when its function returns `Ok` and rolls back on `Err` or `?`:

```
fn move_funds(
  tx: Connection,
  from_id: Int,
  to_id: Int,
  amount: Int
) Result[Unit, Error]
  debit = sql(tx):
    UPDATE accounts SET balance = balance - $amount WHERE id = $from_id
  \debit?
  credit = sql(tx):
    UPDATE accounts SET balance = balance + $amount WHERE id = $to_id
  \credit?
  Ok(())

fn transfer(
  conn: Connection,
  from_id: Int,
  to_id: Int,
  amount: Int
) Result[Unit, Error]
  transaction(conn, move_funds(_, from_id, to_id, amount))
```

**Mistakes:** an unknown column (compile error), `${table}` as a table name (identifiers can't be parameters), nesting transactions, passing a channel to the transaction function, and returning a query stream from a plain `fn`.

**Chapter 23: Tests, assertions, `dbg`**

```
fn double(x: Int) Int
  x * 2
test "double doubles"
  assert_eq(double(4), 8)
  assert(double(0) == 0)
  assert_ne(double(1), 3)
total = dbg(double(2)) * 2
println("$total")
```

`moxie test` runs each `test` block in its own fiber, one after another, without running the entry file; a failed assertion aborts that test with a diagnostic. A normal run type-checks the test blocks but generates no code for them. In a normal run the program prints `8` to the output, and `dbg` prints something like `[main.mxi:7] double(2) = 4` to the error stream (and warns that `dbg` was left in). `dbg(expr)` returns its argument, so it can wrap any sub-expression, or sit in a pipeline as `|> dbg()`. `assert`, `assert_eq`, and `assert_ne` stay on in `--release` builds, while `debug_assert(cond)` is removed there, and its condition must be pure. **Mistakes:** a `debug_assert` whose condition reads a channel, and leaving `dbg` in committed code.

`moxie repl` starts an interactive session. Type an expression and it prints the result with its type, such as `$res1: Int = 3`, and keeps it as `$res1`; the older results move up (`$res2` is the one before), so `$res1 + $res2` adds the last two. Declarations (`fn`, `tuple`, `enum`, `import`, `x = 5`) join the session, so later lines can use them. A line ending in `:` continues until a blank line. If a line has a compile error, you see the error and the session stays as it was. `:type expr` shows a type without running it, `:results` lists the results, `:reset` starts over, and `:quit` leaves.

**Property tests.** A `forall` inside a `test` checks a rule for many values at once, where an `assert` checks it for one. Name the values and their types, and the body runs for 100 generated cases:

```
test "reversing twice changes nothing"
  forall xs: List[Int]
    assert_eq(xs |> to_stream() |> reverse() |> reverse() |> collect(), xs)
```

The values come from the types: whole numbers (with the edge cases mixed in), `Bool`, `Char`, `String`, `Float`, `Double`, lists and arrays of those, tuples, your own tuples, and enums. The run is seeded, so it repeats exactly. When a case fails, moxie shrinks it before reporting, so a failure reads `x = 1000` and not `x = 2030568236571276233`, along with the seed that replays it. `moxie test --seed 7 FILE` replays or varies the run, and `--cases 1000` runs more of them. The body must be pure, so it can't print or read a channel, and `forall` goes directly inside a `test`. A type with a rule needs its own generator, or `forall` would mostly make values the rule forbids. Implement `Generatable`, building a value from the `Gen` it is handed, and optionally list simpler values for shrinking:

```
tuple Pct
  n: Int

impl Generatable for Pct
  static fn generate(g: Gen) Self = Pct(gen_int(g, 0, 100))
  fn shrink() List[Pct]
    when n
      0 -> List()
      else List(Pct(0), Pct(n - 1))
```

`gen_int(g, lo, hi)`, `gen_bool(g)`, and `gen_pick(g, list)` draw values, and `sample[T](g)` draws a `T` the usual way, so a sorted list is `xs = sample[List[Int]](g)` followed by sorting it. A type with an `invariant` does not need an impl for a loose rule: `forall` builds it through its constructor and draws again when the invariant rejects the value, so `invariant len(name) > 0` works as it is. A tight rule, such as sorted order, would reject nearly every draw, so give the type an impl. Once `Pct` has an impl, `forall p: Pct` and even `forall xs: List[Pct]` use it. **Mistakes:** assuming a property holds for every `Int` when `a + b` can overflow (the test will find it), and printing inside the body.

**23a. `moxie fmt`**

`moxie fmt FILE-or-DIR...` rewrites files into one layout and has no layout options. It fixes the shape of the file: every block is indented two spaces per level, a continuation line keeps its offset from the statement it continues, multi-line strings, SQL bodies, and block comments move together with their text unchanged, trailing spaces go, blank lines are limited to two at the top level and one inside a block, and the file ends with a single newline. A comment takes the level of the code it belongs to. Inside a line it puts one space around `=`, `==`, `~=`, `<=`, `>=`, `->`, `|>` and the arithmetic operators, none before a comma and one after, and it adds a blank line before a top-level `fn`, `type`, `impl`, or `test` that follows a block. A line longer than 80 columns is broken at its outermost bracket group, one item to a line, with the closing bracket on a line of its own (nothing is added or removed, so no trailing comma appears); a line with a comment on it is left alone. The width is not an option.

```
$ moxie fmt --check src
would change src/parse.mxi
$ moxie fmt src
formatted src/parse.mxi
```

`--check` changes nothing and exits 1 when a file would change, so it fits a build script; `--stdout` prints the result instead of writing. Before a file is written, the formatter checks that the tokens match the original, that every comment is kept with its text unchanged and in order, that the spacing changes left the parsed program the same (otherwise only the layout rules are applied), and that a second run changes nothing; if a check fails it reports the file and leaves it alone. A file with a tab in its indentation or an unterminated string is reported and not touched. **Mistakes:** expecting it to join or split lines (it never does, so a long argument list stays as written), or to rewrap long lines (the line width is not settled).

**23b. What `moxie check` proves**

`moxie check FILE` reads the whole program and reports mistakes without running anything, and `moxie run` stops on the same errors before the first line executes. It follows one rule: it reports only what it can prove, so a value whose type it cannot work out is never an error. What it proves:

- **Types.** Every call, operator, index, slice, range, `if` and `when` arm, `?`, return, and annotation agrees with the declared types, including through lambdas, pipes (`x |> f(a)` fills the slot the runtime picks, and a call that fits two slots is an error), generic functions, and the prelude (`avg`, `sum`, `map`, `get`, channel ends, collections). A bare `x(i)` on something that is not a function, a `Result` used as a number, and a `Stream` interpolated into text are errors.
- **Names and shapes.** Undefined names, unknown types and enum cases, wrong argument counts, missing or extra fields in a constructor, duplicate fields and cases, a `when` that misses a case, a function clause that can never be reached, a pattern that cannot match the value's type (a `String` literal against an `Int`, `Ok(...)` against a number, a payload of the wrong type), and a destructuring of the wrong arity.
- **What a type can do.** `==` and `~=` on a declared tuple or enum need `deriving eq` (or an `impl Equatable`), and `<`, `>`, `<=`, `>=` need `deriving ord` (or an `impl Ordered`). The same bounds apply to the prelude: `sort`, `max`, and `min` need `ord`, `contains` and `distinct` need `eq`, and a declared tuple or enum used as a Dict key or Set element needs `deriving eq, hash`. Nothing is compared by accident, and a plain `enum Color` is not ordered by its declaration order unless you ask.
- **Errors as values.** `?` needs a `Result` operand in a function that returns a `Result` with the same error (or a `From` impl that converts it), so it is an error in a function that returns `Unit` and inside a `daemon` body (use `when` there), and a `Result` is never used as if it were the value inside.
- **Ownership.** Use after move, `ref` and `move` mismatches, and a resource that outlives what it may.
- **Sizes and numbers.** Array and MultiArray shapes (a literal with the wrong size or ragged rows; a List has no size to check), a constant index past the end of an Array whose size the text gives, a literal that does not fit a bounded integer, and division by a constant zero. The `sum` or `product` of nothing is the element type's zero or one, which the checker supplies.
- **Shadowing (a warning).** A name bound or changed with `=` or `+=` in a deeper block (a loop body, an `if`, a `when` arm) is a new name that hides the outer one until the block ends, so `total += i` in a loop leaves the outer `total` alone; the warning points to `gimme.1.total`.
- **Effects and permissions.** What a function prints, parks on, or reaches, checked against its declaration and the manifest's grants, through calls and imported packages.

What it leaves alone: anything that depends on a value at run time (a Dict key that is present, an index that is only known when the program runs), a function used as a value is checked by its types but not by its arity, a `break` outside a loop, a shift of a value whose width the text doesn't state (such as the result of arithmetic on narrow integers; a shift of an annotated variable or parameter by a constant is checked), a two-argument `put` on a container whose kind the text doesn't state (a lambda argument with no type, say), a lambda with untyped parameters that is bound to a name and used later as a Dict key or Set element, and a type name of one or two letters or all capitals is taken to be a type parameter. Those are caught when the code runs, with the same message the checker would have given.

**Chapter 24: Functional programming**

Moxie's support for functional programming is ordinary prelude code over a few language features: immutable values, higher-order functions, pipelines, `for` comprehensions, and interfaces over type constructors. Outputs were computed by hand, and several snippets reuse names from earlier chapters (`add`, `Box`, `half`, `Tree`, `User`).

**24a. Values never change, and old versions stay valid**

```
old = List(1, 2, 3)
new = old + 4
println("${len(old)} ${len(new)}")
```

Output: `3 4`. Every update gives a new value, and a name is rebound, never mutated. **[gc]** A `List`, `Dict`, or `Set` update shares most of its storage with the old version, so it costs O(log n) and the old version stays valid for as long as anything uses it. An `Array` update copies the array, so use a `List` for something updated one element at a time.

**24b. Pure functions and inferred effects**

The compiler works out which functions can park, print, or use a resource. You can state the intent with `pure fn`, and a violation is a compile error that names the call:

```
pure fn area(w: Int, h: Int) Int
  w * h
pure fn noisy(w: Int) Int
  println("w is $w")    // ERROR: pure fn calls println
  w
```

Using a resource counts too: creating, closing, or changing a channel, timer, future, or atom (and reading an atom with `@`) is not allowed in a `pure fn`, because shared state isn't pure. `swap`, `debug_assert`, and compile-time evaluation require pure functions, with or without the marker. `dbg` and `trace` are exempt: `trace("got here")` writes a message to the error stream, does not count as an effect, and is removed in release builds, while `println` is real output and does count. Compile-time evaluation lets `limit = pow2(10, 1)` size a Dict (chapter 2c).

You are never required to write effects, and you never have to pass them up the call chain: a caller of a function that prints is inferred to print, and you change nothing in the callers when you add a `println` while debugging (or use `dbg`, which is exempt). When you want the compiler to hold you to a statement, declare it before `fn`: `pure`, `prints`, `parks` (both can be given, as in `prints parks fn`), or `impure` for "has some effect". A declaration is an agreement checked both ways. The compiler rejects a body that does an effect you did not declare, and it also rejects a declaration the body no longer earns, so a stale `prints` cannot linger after the print is removed. An interface member can be declared the same way (`prints fn log(self, s: String) Unit`), and then it is an upper bound: an impl may do less, but doing more is a compile error, and code that calls through the interface is checked against the declaration.

**24c. Functions as values: compose, apply, curry**

```
fn inc(x: Int) Int = x + 1
fn twice(x: Int) Int = x * 2
fn square(x: Int) Int = x * x
pipeline = inc ~> twice ~> square
out: List[Int] = List(1, 2, 3) |> to_stream() |> map(pipeline) |> collect()
println("${pipeline(2)} ${out(0)} ${out(1)} ${out(2)}")
```

Output: `36 16 36 64`. `~>` composes left to right, so `pipeline(2)` is `square(twice(inc(2)))`, which is 6 squared. A list of functions can be folded over a value:

```
steps: Array[(Int) -> Int] = (inc, twice, square)
result = steps |> to_stream() |> reduce(0)(acc, f) -> f(acc)
println("$result")
```

Output: `4` (0 becomes 1, then 2, then 4). Currying is a library function, and closures carry data:

```
add5 = curry(add)(5)
make_adder = (k: Int) -> (n: Int) -> n + k
println("${add5(1)} ${make_adder(10)(1)}")
```

Output: `6 11` (`add` from chapter 6). **[gc]** Closures can be passed, returned, and stored in data structures (chapter 7).

**`uncurry[n]`.** `uncurry` is the inverse of `curry`: it turns a function that takes its arguments one at a time into one that takes them all at once, so it can go where a multi-argument function is expected. With `add_c = curry(add)`, `zip_with(uncurry[2](add_c), xs, ys)` pairs up the two lists and adds each pair, and `uncurry[4](curry(add4))(1, 2, 3, 4)` is `add4(1, 2, 3, 4)`. You write the number of arguments in brackets, as `round_to[n]` takes its scale, because from a type like `A -> B -> C` the compiler cannot tell whether `B -> C` is the rest of a chain or a function that a one-parameter function returns. `n` is a constant of 2 or more, with no upper limit, and calling the result with a different number of arguments is an error. You will not need it often, because an argument list and a tuple of the same shape are already the same thing (chapter 6): a two-parameter function is called as `f(a, b)` or `f(pair)`, `f(...pair)` always unpacks, and `(Int, Int) -> Int` is the same type as `((Int, Int)) -> Int`.

**24d. Recursion over data**

```
enum Expr
  Num(n: Int),
  Add(l: Expr, r: Expr),
  Mul(l: Expr, r: Expr)
fn eval(e: Expr) Int
  when e
    Num(n) -> n
    Add(l, r) -> eval(l) + eval(r)
    Mul(l, r) -> eval(l) * eval(r)
e = Expr.Add(l: Num(n: 2), r: Mul(l: Num(n: 3), r: Num(n: 4)))
println("${eval(e)}")
```

Output: `14`. A fold abstracts the recursion. Here a generic fold over the `Tree` of chapter 15 gives a sum and a depth:

```
fn fold_tree[T, R](t: Tree[T], base: R, f: (R, T, R) -> R) R
  when t
    Leaf -> base
    Node(l, v, r) -> f(fold_tree(l, base, f), v, fold_tree(r, base, f))
sum = fold_tree(small, 0, (a, v, b) -> a + v + b)
depth = fold_tree(small, 0, (a, _, b) -> 1 + (if a > b then a else b))
println("$sum $depth")
```

Output: `6 2`. Tail-recursive functions run in constant stack (chapter 12), and a recursive call that isn't a tail call and can't be bounded gets a warning.

**24e. Errors as values: `?`, bind, map, apply**

```
fn positive(n: Int) Result[Int, Error]
  if n > 0 then Ok(n) else fail(1, "not positive")
fn small(n: Int) Result[Int, Error]
  if n < 100 then Ok(n) else fail(2, "too big")
fn check(n: Int) Result[Int, Error]
  positive(n) |>> small
fn check2(n: Int) Result[Int, Error]
  p = positive(n)?
  small(p)
println("${is_ok(check(5))} ${is_ok(check(-1))} ${is_ok(check2(500))}")
when check(500)
  Ok(v) -> println("ok $v")
  Err(e) -> println(e.message)
```

Output: `true false false`, then `too big`. `|>>` and `?` are two spellings of the same sequencing: the first failure stops the chain and is returned. `map_ok` and `<$>` change the value inside, and `<*>` applies a function held in a `Result` (these operators work for any `Functor` or `Applicative`, section 24f):

```
r1: Result[Int, Error] = Ok(1)
r2: Result[Int, Error] = Ok(2)
bad: Result[Int, Error] = fail(9, "bad")
println(
  "${(curry(add) <$> r1) <*> r2} ${is_err((curry(add) <$> bad) <*> r2)}"
)
```

Output: `Ok(3) true`. The parentheses are needed because `<$>` and `<*>` sit in the comparison tier. This is the applicative style: independent inputs combined by one function, with the first error winning. The prelude's `traverse(f, stream)` maps a `Result`-returning function and stops at the first error, and `sequence` turns a stream of `Result`s into a `Result` of a list:

```
all_ok = traverse(check, List(5, 20, 7) |> to_stream())
one_bad = traverse(check, List(5, -1, 7) |> to_stream())
println("${is_ok(all_ok)} ${is_ok(one_bad)}")
```

Output: `true false`. The error type is yours, so the same patterns work with an enum and `From` conversions (chapter 18).

`traverse` stops at the first error, which is right for a pipeline and wrong for a form, where you want every problem at once. `validate(f, xs)` runs `f` on every item and gives `Ok` with the list of results, or `Err` with the list of *all* the errors; `collect_errors(rs)` does the same for a stream of `Result`s you already have. `partition_results(rs)` splits them into `(oks, errs)` and keeps going either way, `recover(r, f)` turns an `Err` into an `Ok` with a fallback computed from the error, and `tap(x, f)` runs `f(x)` for its effect and gives `x` back, which is handy for a log line in the middle of a pipeline (`f` may print, so write it `fn (x) = ...`). `retry(n, delay, f)` calls `f` once and calls it again only if it gave an `Err`, waiting `delay` between tries, up to `n` tries in all; the last `Err` comes back if every try fails. It does not repeat an error that a second try can't change (`NOT_FOUND`, `DENIED`, `BAD_ENCODING`, `OUT_OF_RANGE`, `MISSING`, `TOO_LONG`, `TOO_SHORT`), and `when: (e): ...` replaces that rule with your own. Use it for calls that are safe to repeat (reads, lookups, connecting), because a call that half-worked will half-work again:

```
fn check(n: Int) Result[Int, String]
  when n > 0
    true -> Ok(n)
    false -> Err("bad ${n}")
inputs = List(5, -1, 7, -3)
println(validate(check, inputs))
(good, bad) = partition_results(inputs |> map(check) |> collect())
println("$good $bad")
println(recover(check(-2), (e) -> 0))
tries = Atom[Int](0)
fn flaky() Result[Int, String]
  k = swap(tries, _ + 1)
  when k < 3
    true -> Err("not yet")
    false -> Ok(k)
println(retry(5, 10ms, flaky))
```

Output: `Err(List("bad -1", "bad -3"))`, `List(5, 7) List("bad -1", "bad -3")`, `Ok(0)`, then `Ok(3)`.

**Different checks, one result.** `validate` needs one function over many items. A form is usually the other shape: several independent checks of different types, combined by one function. `map_all(f, r1, r2, ...)` takes two to six `Result`s that share an error type and a function with one parameter for each. If all are `Ok`, you get `Ok(f(values))`; otherwise `Err` with the list of *every* error, in argument order, so the mixer sees all the problems at once.

```
tuple User
  name: String
  email: String

fn check_name(s: String) Result[String, String]
  when s == ""
    true -> Err("name is empty")
    false -> Ok(s)

fn check_email(s: String) Result[String, String]
  when s.contains("@")
    true -> Ok(s)
    false -> Err("bad email: ${s}")

fn create(name: String, email: String) Result[User, List[String]]
  map_all(User, check_name(name), check_email(email))

println(create("ann", "ann@x.org"))
println(create("", "nope"))
```

Output: `Ok(User(name: "ann", email: "ann@x.org"))`, then `Err(List("name is empty", "bad email: nope"))`. The results can also come as a tuple, which suits a pipeline: `(check_name(name), check_email(email)) |> map_all(User)` means `map_all((check_name(name), check_email(email)), User)`. A function with the wrong number of parameters is a compile error. Every argument must have the same error type; wrap one with `map_err` to line them up. The checks run one after another. When each is slow, `par_map_all(f, c1, c2, ..., limit: n)` takes the same function and, in place of the results, a zero-parameter function for each check, such as `fn () = check_name(name)`; it runs them in parallel, at most `n` at a time, and gives the same answer, including every error in argument order. Use `par_traverse` when the items have one type.

**24f. Functor, Applicative, and Monad**

These are prelude interfaces over a type constructor `F[_]` (chapter 8d), with the names Haskell programmers expect:

```
interface Functor[F[_]]
  fn map[A, B](self: F[A], f: (A) -> B) F[B]
interface Applicative[F[_]]
  Functor[F]
  static fn pure[A](a: A) F[A]
  fn ap[A, B](self: F[(A) -> B], x: F[A]) F[B]
interface Monad[F[_]]
  Applicative[F]
  fn flat_map[A, B](self: F[A], f: (A) -> F[B]) F[B]
```

The prelude has instances for `Result[_, E]`, `Stream`, `List[_]` **[gc]**, and `Array[_][N]`. You write one for your own type with no `for`, naming the constructor (`Box` and `half` from chapter 10):

```
impl Monad[Box]
  fn map[A, B](self: Box[A], f: (A) -> B) Box[B]
    when self
      Full(v) -> Box.Full(f(v))
      Empty -> Box.Empty
  static fn pure[A](a: A) Box[A]
    Box.Full(a)
  fn ap[A, B](self: Box[(A) -> B], x: Box[A]) Box[B]
    when self
      Full(g) -> x.map(g)
      Empty -> Box.Empty
  fn flat_map[A, B](self: Box[A], f: (A) -> Box[B]) Box[B]
    when self
      Full(v) -> f(v)
      Empty -> Box.Empty
print("${Box.Full(3).map((x) -> x + 1)} ")
println("${Box.pure(20).flat_map(half).flat_map(half)}")
```

Output: `Box.Full(4) Box.Full(5)`. The operators `<$>`, `<*>`, and `|>>` are the prelude's spellings of `map`, `ap`, and `flat_map` for any such type. Code written once for every monad (`double_in`, `lift2`) is in chapter 8d. The compiler does not check the monad laws, evaluation is eager, and there is no return-type dispatch: write `Box.pure(42)`, never a bare `pure(42)`. A type that accumulates several errors should implement `Applicative` only.

**`map` and `filter` on a List or an Array.** `List` and `Array` have a `Functor` impl, so `xs.map(f)`, `xs |> map(f)`, and `map(f, xs)` are the same call (section 12) and give the same kind of container back (an `Array` keeps its size). A `Stream` gives a `Stream`. `filter` is a stream stage with no `Functor` behind it, so `xs.filter(p)` is a stream: write `xs |> filter(p) |> collect()`. Printing or interpolating a stream is a compile error that says to `collect()` it first. `map` on a List runs `f` on every element at once; when a chain should stay lazy (a `take` that stops early, an `f` with effects), start it with `to_stream()`.

**Sequences with the operators.** With `Box` and its `Monad` impl in scope (they are your code, not the prelude's), `|>>` chains steps that each return a `Box`, `<$>` maps a plain function over the value inside, and `<*>` combines independent values. `Result` and `List` work the same way with no impl of your own, because the prelude supplies them. `Maybe`, `Option`, `Either`, and similar types are never built in: you define the type and its impl.

```
fn dec(n: Int) Box[Int]
  if n > 0 then Box.Full(n - 1) else Box.Empty
sq = (x: Int) -> x * x
dup = (x: Int) -> List(x, x)
fn pos(n: Int) Result[Int, Error]
  if n > 0 then Ok(n) else fail(1, "not positive")
fn under(n: Int) Result[Int, Error]
  if n < 10 then Ok(n) else fail(2, "too big")
println("${Box.Full(3) |>> dec |>> dec} ${Box.Full(1) |>> dec |>> dec}")
println("${sq <$> Box.Full(7)} ${sq <$> Box.Empty}")
lifted = curry(add) <$> Box.Full(4)
println("${lifted <*> Box.Full(5)} ${lifted <*> Box.Empty}")
good = Ok(4) |>> pos |>> under |>> ((v) -> Ok(v * 3))
bad = Ok(40) |>> pos |>> under |>> ((v) -> Ok(v * 3))
println("$good ${is_err(bad)}")
println("${List(1, 2) |>> dup} ${sq <$> (List(1, 2, 3) |>> dup)}")
```

Output, line by line: `Box.Full(1) Box.Empty` (3 steps down to 2 and then 1, while 1 steps down to 0 and then fails); `Box.Full(49) Box.Empty`; `Box.Full(9) Box.Empty`; `Ok(12) true` (the chain stops at the first `Err`); and `List(1, 1, 2, 2) List(1, 1, 4, 4, 9, 9)`. For a `List`, `|>>` runs the function on each element and concatenates the results, which is the list monad. Use `|>>` when each step needs the previous result, `<$>` with `<*>` when the inputs are independent, and parenthesize `<$>` and `<*>` next to other operators.

**24g. `for` comprehensions**

A `for` block is a chain of generators ending in `yield`. It desugars to `flat_map` and `map` through the type's `Monad` impl, so a `Empty` or an `Err` stops it:

```
good = for
  a in Box.Full(20)
  b in half(a)
  c in half(b)
  yield a + c
bad = for
  a in Box.Full(10)
  b in half(a)
  c in half(b)
  yield a + c
println("$good $bad")
```

Output: `Box.Full(25) Box.Empty` (20 halves to 10 and then 5; 10 halves to 5, and 5 is odd). A line `name = expr` binds a value, a **refutable** line uses let-else, and independent generators joined by a leading `and` compile through `ap`, so they need only an `Applicative`. Here is a payroll example in three forms, with `?`, with `for`, and with a batch:

```
enum Rank
  Manager,
  Staff
enum User
  Active(name: String, rank: Rank),
  Retired(name: String)
enum PayError deriving show
  NotFound(id: Int)
fn find_user(id: Int) Result[User, PayError]
  when id
    42 -> Ok(User.Active(name: "Ada", rank: Manager))
    7 -> Ok(User.Active(name: "Bo", rank: Staff))
    9 -> Ok(User.Retired(name: "Cy"))
    else Err(NotFound(id: id))
fn base_pay(rank: Rank) Int
  when rank
    Manager -> 500000
    Staff -> 300000
fn pay_one(id: Int, bonus_pct: Int) Result[Int, PayError]
  user = find_user(id)?
  Active(_, rank) = user else Err(NotFound(id: id))
  base = base_pay(rank)
  cents = if bonus_pct > 0 then base + base * bonus_pct / 100 else base
  Ok(cents)
fn pay_for(id: Int, bonus_pct: Int) Result[Int, PayError]
  for
    user in find_user(id)
    Active(_, rank) = user else Err(NotFound(id: id))
    base = base_pay(rank)
    yield base + base * bonus_pct / 100
fn process_batch(ids: List[Int], bonus_pct: Int) Result[List[Int], PayError]
  ids |> to_stream() |> traverse(pay_one(_, bonus_pct))
println("${pay_one(42, 10)} ${pay_for(42, 10)}")
when process_batch(List(42, 7), 10)
  Ok(all) -> println("${all(0)} ${all(1)}")
  Err(e) -> println("$e")
when process_batch(List(42, 9), 10)
  Ok(all) -> println("${all(0)}")
  Err(e) -> println("$e")
```

Output: `Ok(550000) Ok(550000)`, then `550000 330000`, then `PayError.NotFound(9)` (the first error in the batch wins). Guards are prelude functions: `ensure(cond, err)` for `Result`, `guard(cond)` for a plain condition (`Ok(())`, or `Err` with the code `MISSING`), and `or_else` to recover. An error that carries runtime text must be a typed payload such as `NotFound(id: id)`, since a static-string `Error` cannot. Two generators over `Result` need only `Applicative`:

```
fn both(a: Result[Int, Error], b: Result[Int, Error]) Result[Int, Error]
  for
    x in a
    and y in b
    yield x + y
println("${both(Ok(1), Ok(2))}")
```

Output: `Ok(3)`. The container form is separate (one filter, no nested `for`), and the container's size comes from its declared type:

```
xs = List(1, 2, 3, 4)
squares: List[Int] = List(x * x for x in xs if x > 1)
words = List("ab", "cde")
lens: Dict[String, Int] = Dict(w: len(w) for w in words)
println("${len(squares)} ${squares(0)} ${lens(cde)}")
```

Output: `3 4 Ok(3)`: the squares are 4, 9, and 16, and a Dict lookup returns a `Result`. `Set(...)` is built the same way. Left out on purpose: custom builders, `try`/`with`, `use!`, and loops inside the block. Nested generators over streams work through `Monad[Stream]`, and the result is a stream **[gc]**, which can be returned.

**24h. State, Reader, and Writer**

Recommended for state: `ref` threading, which does the job with the data flow visible at each call:

```
fn push(ref stack: List[Int], x: Int) Unit
  stack += x
fn pop(ref stack: List[Int]) Int
  top = stack(len(stack) - 1)
  stack = remove_at(stack, len(stack) - 1)
  top
s: List[Int] = List()
push(ref s, 3)
push(ref s, 4)
a = pop(ref s)
b = pop(ref s)
println("${a * b} ${len(s)}")
```

Output: `12 0`. Each call returns a value and hands back the updated state, the `(A, S)` pair of a state monad. A real **State monad** can also be defined as a local value, because a closure inside a generic type has one type per signature **[gc]**:

```
tuple State[S, A]
  run: (S) -> (A, S)
fn map_state[S, A, B](m: State[S, A], f: (A) -> B, s: S) (B, S)
  (a, s2) = m.run(s)
  (f(a), s2)
fn bind_state[S, A, B](m: State[S, A], f: (A) -> State[S, B], s: S) (B, S)
  (a, s2) = m.run(s)
  f(a).run(s2)
impl[S] Monad[State[S, _]]
  fn map[A, B](self: State[S, A], f: (A) -> B) State[S, B]
    State(run: (s) -> map_state(self, f, s))
  static fn pure[A](a: A) State[S, A]
    State(run: (s) -> (a, s))
  fn ap[A, B](self: State[S, (A) -> B], x: State[S, A]) State[S, B]
    self.flat_map((g) -> x.map(g))
  fn flat_map[A, B](self: State[S, A], f: (A) -> State[S, B]) State[S, B]
    State(run: (s) -> bind_state(self, f, s))
next_id = State(run: (c: Int) -> (c + 1, c + 1))
two = next_id.flat_map((a) -> next_id.map((b) -> (a, b)))
r = two.run(0)
println("${r(0)(0)} ${r(0)(1)} ${r(1)}")
```

Output: `1 2 2`. **[gc]** None of no-GC moxie's closure limits apply: a closure has one type per signature, branches may return different closures, loops and recursion over runtime-length data work, and a State value can go in a Dict, an Atom, or a channel. `ref` threading remains the simpler way, but if you want the monad ready-made, `import fp.state` gives you this `State` type with its `Monad` impl, plus `get()`, `put(s)`, `modify(f)`, `gets(f)`, `eval(m, s)` (the result), `exec(m, s)` (the final state), and `traverse(xs, f)` (runs `f` on each element in order, threading the state, and collects the results). The package is moxie/gc only, and no-GC moxie refuses the import:

```
import fp.state

fn label(name: String) state.State[Int, String]
  state.modify((n: Int) -> n + 1).flat_map((u) -> state.gets((n: Int) -> "${name}${n}"))
println(state.traverse(List("a", "b", "c"), label).run(0))
```

Output: `(List("a1", "b2", "c3"), 3)`. A **Reader** is a `using` parameter, which the caller can override:

```
fn price(base: Int, using tax: Int) Int
  base + base * tax / 100
using tax = 20
println("${price(100, using)} ${price(100, 5)}")
```

Output: `120 105`. A **Writer** is a function that returns the value together with the log, `(Int, List[String])`, and the caller combines the logs with `+`.

**More monads: List, Reader, Writer, Cont, and Free** **[gc]**

`List[_]` is a monad, so `flat_map` returns a list, `List.pure(x)` is `List(x)`, and a `for` block over lists gives the pairs in order:

```
r = for
  a in List(1, 2)
  b in List(10, 20)
  yield a + b
println(r)
```

Output: `List(11, 21, 12, 22)`. Four packages ship with moxie/gc, each one `import` away (they need closures with one type per signature, so no-GC moxie does not have them). `fp.reader` is a **Reader** monad, `fp.writer` is a **Writer** whose log is a `List`, `fp.cont` is a **continuation** monad with `call_cc`, and `fp.free` is the **free monad** over any functor:

```
import fp.reader
import fp.writer
import fp.cont

greet = reader.asks((n: String) -> "hi ${n}").flat_map((g) -> reader.asks((n: String) -> "${g}!"))
println(reader.run_reader(greet, "bo"))
log = writer.tell("start").flat_map((u) -> writer.tell("end")).map((u) -> 7)
println(writer.run_writer(log))
safe_div = (a: Int, b: Int) -> cont.call_cc((leave) -> if b == 0 then leave(-1) else cont.Cont.pure(a / b))
println("${cont.eval_cont(safe_div(10, 2))} ${cont.eval_cont(safe_div(1, 0))}")
```

Output: `hi bo!`, then `(7, List("start", "end"))`, then `5 -1`. `call_cc` hands its function an escape: calling `leave` abandons the rest of that function and continues from where `call_cc` was. A free monad turns a program into data that you interpret later, as many ways as you like. You write the functor for your instruction set and `fp.free` does the rest:

```
import fp.free

enum Cmd[Next]
  Say(String, Next)
  Ask((String) -> Next)

impl Functor[Cmd]
  fn map[A, B](self: Cmd[A], f: (A) -> B) Cmd[B]
    when self
      Say(s, n) -> Say(s, f(n))
      Ask(k) -> Ask((x) -> f(k(x)))

say = (s: String) -> free.lift_f(Say(s, ()))
ask = free.lift_f(Ask((x) -> x))
prog = say("name?").flat_map((u) -> ask.flat_map((n) -> say("hello ${n}")))
step = (c: Cmd[List[String]]) -> when c
  Say(s, rest) -> List(s) + rest
  Ask(k) -> k("sam")
println(free.fold_free(prog, (u) -> List(), step))
```

Output: `List("name?", "hello sam")`. `fold_free(program, on_done, step)` calls `on_done` with the final value and `step` once per instruction, after the instruction's continuation has been interpreted; a second `step` that counts instructions runs the same `prog` unchanged.

**Transformers and the mtl classes** **[gc]**

A **transformer** adds one capability to any monad underneath it. `import fp.trans` gives `StateT`, `ReaderT`, `WriterT`, and `ExceptT` (each takes the inner monad as its first type argument), `Identity` for the bottom of a stack, and four classes that say what a program needs instead of which stack provides it: `MonadState[S]` (`get`, `put`, `modify`, `gets`), `MonadReader[R]` (`ask`, `asks`, `local`), `MonadWriter[W]` (`tell`, `listen`, `censor`), and `MonadError[E]` (`throw_error`, `catch_error`). You write the program once, with the class members called on `M`, and pick the stack where you call it:

```
import fp.trans

fn tick[M[_]: Monad + MonadState[Int] + MonadError[String]](limit: Int) M[Int]
  M.get().flat_map((n) -> if n >= limit then M.throw_error("too big") else M.put(n + 1)).flat_map((u) -> M.get())

fn state_then_error(s: Int) Result[(Int, Int), String]
  trans.run_identity(trans.run_except_t(trans.run_state_t(tick[trans.StateT[trans.ExceptT[trans.Identity, String, _], Int, _]](5), s)))
fn error_then_state(s: Int) (Result[Int, String], Int)
  trans.run_identity(trans.run_state_t(trans.run_except_t(tick[trans.ExceptT[trans.StateT[trans.Identity, Int, _], String, _]](5)), s))
println("${state_then_error(1)} ${state_then_error(9)}")
println("${error_then_state(1)} ${error_then_state(9)}")
```

Output: `Ok((2, 2)) Err("too big")`, then `(Ok(2), 2) (Err("too big"), 9)`. The same `tick` runs on both stacks, and the stack order decides what a failure costs: with `StateT` over `ExceptT` an error throws the state away, and with `ExceptT` over `StateT` the state survives it. Return-type polymorphism needs the type written out, so the stack goes in `[...]` at the call and `M.` does the rest inside. A class member reaches through every layer above the one that provides it (`M.get()` works on a `ReaderT` over a `StateT`), and each transformer has a `lift_state_t`, `lift_reader_t`, `lift_writer_t`, or `lift_except_t` that runs an action of the inner monad. A stack of `Result` or `List` at the bottom works too, so `StateT[List[_], Int, _]` explores every branch. There is no generic `lift` class: that would be a class over a constructor of constructors, which moxie leaves out, so each transformer has its own `lift_` function.

Two more transformers cover the other monads in this chapter. `ContT` is a continuation transformer, and `MonadCont` gives any stack `M.call_cc`, which reaches through `StateT`, `ReaderT`, `WriterT`, and `ExceptT` (an escape keeps the state as it was at the moment of the jump). `FreeT[F, M, A]` is a free program whose steps run in the monad `M`, and `MonadFree[F]` gives a stack `M.wrap(instruction)` to issue one:

```
import fp.trans

fn find_first[M[_]: Monad + MonadCont](xs: List[Int], want: Int) M[Int]
  M.call_cc((leave) -> xs.reduce(M.pure(-1), (acc, x) -> acc.flat_map((r) -> if x == want then leave(x * 100) else M.pure(r))))
fn go(want: Int) Int
  trans.run_identity(trans.run_cont_t(find_first[trans.ContT[trans.Identity, Int, _]](List(1, 2, 3), want), (a) -> trans.Identity.pure(a)))
println("${go(2)} ${go(9)}")
```

Output: `200 -1`. `fold_free_t(program, on_done, step)` is `fold_free` with `on_done` and `step` returning actions of `M`, so an interpreter can fail or log as it goes. A value that you build yourself with a bare constructor inside a lambda (`ContT(run: ...)`, `FreeT(run: ...)`) does not know its stack's types; build through `M.pure`, `M.wrap`, the class members, and the `lift_` functions, or inside a function that names the return type, and the stack works out its own inner monad.

A type lambda or a generic alias also names a whole transformer stack, so a program can be run on it with one word, and a lambda over a constructor, `[M[_], A] -> StateT[M, Int, A]`, is the `T` of the `MonadTrans` class (`T[_[_], _]`), whose `lift` brings an action of the inner monad up through any transformer:

```
import fp.trans

type alias App[A] = trans.StateT[trans.ExceptT[trans.Identity, String, _], Int, A]

fn tick[M[_]: Monad + MonadState[Int] + MonadError[String]](limit: Int) M[Int]
  M.get().flat_map((n) -> if n >= limit then M.throw_error("too big") else M.put(n + 1)).flat_map((u) -> M.get())
fn go(s: Int) Result[(Int, Int), String]
  trans.run_identity(trans.run_except_t(trans.run_state_t(tick[App](5), s)))
println("${go(1)} ${go(9)}")
up = trans.lift[[M[_], A] -> trans.StateT[M, Int, A], _, _](Ok(1))
println(trans.run_state_t(up, 7))
```

Output: `Ok((2, 2)) Err("too big")`, then `Ok((1, 7))`. Every transformer in `fp.trans` is a `MonadTrans`, and `lift[T, _, _](m)` lifts through any of them (the `_`s are inferred from `m`).

**24i. Lazy and infinite sequences**

Streams are recipes, so an infinite source costs nothing until a terminal runs it:

```
total = Range(1.., 1)
  |> filter(_ % 3 == 0)
  |> map((n) -> n * n)
  |> take(4)
  |> sum()
under_50 = Range(1.., 1) |> map((n) -> n * n) |> take_while(_ < 50) |> count()
println("$total $under_50")
```

Output: `270 7` (9, 36, 81, 144; and the squares 1, 4, 9, 16, 25, 36, 49). `unfold` builds a generator from a seed (chapter 13), and a `lazy` parameter delays an argument, re-running it on every read, so call by need is a one-line `once = x` (chapter 6b). Nothing is cached for you, so shared work needs a recipe from chapter 14.

**24j. Lenses with data paths**

A data path is an ordinary function, so paths compose, pass, and combine with `modify` (using `User` and `Firm` from chapter 4):

```
a = User(id: 1, firm: Firm(name: "Initech", floor: 2))
moved = modify(a, /User/firm/floor, _ + 1)
name_of = /User/firm ~> /Firm/name
println("${(/User/firm/floor)(moved)} ${name_of(moved)}")
```

Output: `3 Initech`. `replace` and `modify` rebuild the nested tuples, and `a` is unchanged. The old value stays valid.

**24k. What moxie leaves out, on purpose**

- **An IO monad.** Effects are inferred, and the compiler enforces them where they matter (`swap`, `debug_assert`, compile-time evaluation).
- **Hidden laziness and memoization.** Laziness is `lazy` and streams, and caching is a recipe you write.
- **Checked monad laws.** The interfaces are conventions, as in Haskell.

**24l. Semigroup and Monoid**

The prelude declares `Semigroup` (`fn combine(self, other: Self) Self`, which must be associative) and `Monoid` (a `Semigroup` plus `static fn empty() Self`, the identity), as in Haskell and Cats. `String` and `List[T]` implement both, with `+` as `combine` and `""` and `List()` as `empty`. For the other combinations that make sense, the prelude has small wrapper tuples with one field, `value`: `Sum[T]` (for any `Addable`), `Product[T]` (any `Numeric`), `All` and `Any` (`Bool`, with `and` and `or`), and, as semigroups only because they have no identity, `Min[T]` and `Max[T]` (any `Ordered`). A number has more than one monoid, so it has none of its own: you pick one by wrapping it. `fold_all(xs)` combines a stream or list of monoid values (Haskell's `mconcat`), and `fold_map(f, xs)` maps each item to a monoid value first (`foldMap`). Your own types join with an `impl`, as in chapter 8d, and nothing needs importing:

```
println(fold_all(List("a", "b", "c")))
println(fold_all(List(List(1), List(2, 3))))
println(fold_all(List(Sum(1), Sum(2), Sum(3))))
println(fold_map(fn (w) -> List(len(w)), List("a", "bb", "ccc")))
println(fold_map(fn (n) -> Min(n), List(4, 2, 8)))
tuple Stats deriving show
  count: Int
  total: Int
impl Semigroup for Stats
  fn combine(self, other: Stats) Stats
    Stats(count: self.count + other.count, total: self.total + other.total)
impl Monoid for Stats
  static fn empty() Stats = Stats(count: 0, total: 0)
println(fold_map(fn (n) -> Stats(count: 1, total: n), List(4, 6, 8)))
println(fold_all[Stats](List()))
```

Output: `abc`, `List(1, 2, 3)`, `Sum(value: 6)`, `List(1, 2, 3)`, `Min(value: 2)`, `Stats(count: 3, total: 18)`, then `Stats(count: 0, total: 0)`. An empty input gives `empty()`, so name the type when nothing else says which one (`fold_all[Stats](List())`). `Dict` and `Set` have no instance, because a merge has to say which side wins and whether a full collection refuses; use `union`, `merge`, and `merge_with` (chapter 6), or write the `impl` you mean for your own wrapper. `a.combine(b)` is the only spelling: there is no operator for it, since `+` already covers strings and lists, and `Addable` covers numbers.

**Chapter 25: Moxie for imperative programmers**

Most habits carry over:
- **Accumulate in a loop:** a loop's rebindings don't leave it, so fold with a stream:

```
xs = List(1, 2, 3)
sum = xs |> to_stream() |> reduce(0, _1 + _2)
println("$sum")
```

Output: `6`.
- **Early exit:** use `return` for guard clauses (chapter 1a), `break(value)` and `else` for loops (1b), and `break #label` from nested loops.
- **Update a field:** `p.score += 10` rebuilds the tuple, and `p.update` changes several fields at once (8a). A function that changes its caller's variable takes `ref` (6b).
- **Swap:** `a, b = b, a`. **Update an element:** `numbers(i) = v` and `numbers(i) += 1` rebind the array. **[gc]** On an `Array` each such update copies it, so a program that changes elements one at a time should use a `List`, whose updates share storage.
- **Push to a list:** `list += 4`. **Null:** there is none; use `Result`, `T | ()`, or an enum of your own.
- **Outer variable from a nested block:** `gimme.1.x += 1` (1c).
- **Pointers and linked structures:** use a recursive enum (chapter 15), a `Dict` of ids, or a fiber that owns the data.
- **Exceptions:** return a `Result` and use `?` (chapter 18). There is no `try`.
The compiler teaches as it goes: `list.push(4)` gives "lists are values; write `list += 4`", a nested-block `x += 1` gives the shadow warning plus the `gimme` hint, and `null` gives "moxie has no null".


**Chapter 26: Memory in moxie/gc** **[gc]**

This chapter exists only in the moxie/gc Guide. The rest of the language is unchanged, and this is what the collector means for a program.

All fibers share one heap. You never size a collection, count a resource, or ask where a string lives. A generational collector reclaims what nothing can reach, in small slices at safe points (an allocation, a park, the top of a loop), so pauses are short. `Moxie.toml` caps the heap, and a `slice` key sets the slice budget, which defaults to a small fraction of a millisecond:

```
[memory]
heap = "256MiB"
```

When the live data passes `heap`, the program stops with an `out of memory` message that gives the limit and the kinds of value that hold the most. The reference interpreter works this out by measuring what the program can still reach, so the figure follows a model of moxie/gc's layout rather than the machine's.

A name that is finished with holds nothing. The collector counts a local only until its last use, so a variable you have finished with doesn't keep its value alive:

```
xs: List[Int] = Range(1..=1000000, 1) |> to_stream() |> collect()
total = xs |> to_stream() |> reduce(0, _1 + _2)
println("$total")
```

Output: `500000500000`. After the `reduce`, nothing can use `xs` again, so the million elements are free to be collected even though `xs` is still in scope.

What the collector can't do is free data the program itself keeps. An Atom that collects every message, a list carried through a loop that only grows, and a Dict that is never trimmed all grow without end:

```
log = Atom[List[String]](List())
fn note(msg: String) Unit
  \swap(log, _ + msg)
```

Every call to `note` makes the list longer, and the list stays reachable through `log`. This is the one way memory leaks in moxie/gc. If you only need recent history, keep a `Ring` instead of a list. `Ring[T](n)` is an immutable buffer that holds at most `n` items, and adding to a full ring drops the oldest:

```
log = Atom[Ring[String]](Ring[String](3))
fn note(msg: String) Unit
  \swap(log, _ + msg)
for i in 1..=5
  note("m$i")
r = @log
println("${len(r)} ${r(0)} ${r(2)}")
```

Output: `3 m3 m5`. The ring never holds more than three messages, however many are written, and `to_stream(r)` yields them oldest first. For a stream, `take_last(n)` keeps just the last `n` elements:

```
last2 = List(1, 2, 3, 4, 5) |> to_stream() |> take_last(2) |> collect()
println("${last2}")
```

Output: `List(4, 5)`. Both are moxie/gc additions to the prelude.

Resources are different from memory. A channel end, write handle, Timer, or connection still has one owner and is dropped at a known point, when its owner goes out of scope or on an abort. That is when a channel closes or a write handle reports ABANDONED. The collector never closes anything for you, and there are no finalizers.

If a fiber needs memory that a full collection can't supply, the program ends with a diagnostic and a nonzero exit. **Mistakes:** relying on the collector to close a resource, a growing Atom or Dict with no limit, and updating one element of a large `Array` at a time (each update copies the array, so use a `List`).


**Chapter 27: Statistics and prediction (the `stats` package)**

The `stats` package is a small library for learning how data turns into numbers, and how those numbers turn into predictions. Everything in it is a short function you can read (it is `moxie/std/stats.mxi`), and it works on an `Array[Double]`. Write `import stats` and call `stats.mean(xs)`. It is a teaching library, not a replacement for a numeric toolkit, and it is written in moxie, so it is slow on large data.

**27a. Describing one list of numbers**

The **mean** is the average and the **median** is the middle value, so a few extreme values move the mean but barely move the median. The **standard deviation** says how far values typically sit from the mean. A **quantile** is the value below which that fraction of the data falls, from `0.0` (the smallest) to `1.0` (the largest):

```
import stats

scores: Array[Double] = (62.0, 71.0, 71.0, 75.0, 80.0, 84.0, 98.0)
println("mean ${stats.mean(scores):.1f}, median ${stats.median(scores):.1f}")
println("spread ${stats.stddev(scores):.2f}")
when stats.quantile(scores, 0.9)
  Ok(q) -> println("90th percentile ${q:.1f}")
  Err(e) -> println("bad quantile")
```

Output: `mean 77.3, median 75.0`, then `spread 10.69`, then `90th percentile 89.6`. `variance` and `stddev` treat the values as the whole population and divide by `n`. When the values are a sample of something larger, use `sample_variance` and `sample_stddev`, which divide by `n - 1`. `quantile` returns a `Result`, because a `q` outside `0.0` to `1.0` has no answer. `z_scores(xs)` gives each value as a number of standard deviations from the mean, and `total`, `covariance`, and `correlation` (below) round out the list.

**27b. Predicting with a straight line**

**Correlation** runs from `-1.0` to `1.0` and says how closely two lists move along a straight line together. `fit_line(xs, ys)` finds the **least-squares line**, the one with the smallest squared errors in `y`, and returns a `Line` with a `slope`, an `intercept`, and an `r_squared`. `predict(line, x)` reads a prediction off the line:

```
import stats

hours: Array[Double] = (1.0, 2.0, 3.0, 4.0, 5.0)
score: Array[Double] = (52.0, 58.0, 65.0, 70.0, 78.0)
when stats.fit_line(hours, score)
  Err(e) -> println("cannot fit: ${e.message}")
  Ok(line) ->
    println("each hour adds ${line.slope:.1f} points, starting from ${line.intercept:.1f}")
    println("r squared ${line.r_squared:.3f}")
    println("6 hours predicts ${stats.predict(line, 6.0):.1f}")
    fitted = stats.predict_all(line, hours)
    println("typical error ${stats.rmse(score, fitted):.2f} points")
```

Output: `each hour adds 6.4 points, starting from 45.4`, then `r squared 0.996`, then `6 hours predicts 83.8`, then `typical error 0.57 points`. **`r_squared`** is the share of the variation in `y` that the line explains: `1.0` is a perfect fit, and `0.0` is no better than always guessing the mean of `y`. `rmse` (the typical size of the errors, with big mistakes counting extra) and `mean_absolute_error` (every error counts the same) measure how far the predictions are from what really happened. Keep two cautions in mind. A prediction far outside the range of the data (`x` of 60 hours) is a guess that the line keeps going, not something the data showed. And a strong correlation says that two things move together, not that one causes the other. `fit_line` returns an `Err` when there is nothing to fit, as when every `x` is the same:

```
import stats

x: Array[Double] = (3.0, 3.0, 3.0)
y: Array[Double] = (1.0, 2.0, 3.0)
when stats.fit_line(x, y)
  Err(e) -> println(e.message)
  Ok(line) -> println("fitted")
```

Output: `fit_line: every x is the same, so there is no line to fit`. The two arrays given to `covariance`, `correlation`, `fit_line`, `rmse`, and `mean_absolute_error` must have the same number of values, and a difference the compiler can see (two arrays of known, different sizes) is a compile error; otherwise the program stops with a failed assertion.

**27c. A series over time**

A **moving average** replaces each value by the average of the last few, which smooths out the ups and downs. **Exponential smoothing** keeps a running level that each new value pulls toward itself by `alpha`: a big `alpha` follows the data closely, and a small one changes slowly. The level after the last value is also a forecast for the next one:

```
import stats

sales: Array[Double] = (20.0, 24.0, 22.0, 28.0, 27.0, 33.0)
println(stats.moving_average(sales, 3))
println("forecast ${stats.smooth(sales, 0.5):.2f}")
println("slow forecast ${stats.smooth(sales, 0.1):.2f}")
```

Output: `List(22.0, 24.666666666666668, 25.666666666666668, 29.333333333333332)`, then `forecast 29.50`, then `slow forecast 22.99`. The slow forecast lags behind a series that is climbing, and that is the trade-off between smoothing the noise and following a real change. **Mistakes:** passing arrays of different lengths, reading a prediction far outside the data as a fact, and treating a high `r_squared` as proof of cause.

**Chapter 28: HTTP (the `http` package)**

`import http` gives you a small HTTP client and server. It is for plain jobs, with text bodies and one request per connection. A server is a function from a `Request` to a `Response`, and `http.serve` calls it for each connection:

```
import http

fn handle(req: http.Request) http.Response
  if req.method == "POST"
    http.text(200, "you said: ${req.body}")
  elif req.path == "/hello"
    http.text(200, "hello, mixer")
  else
    http.text(404, "nothing at ${req.path}")

fiber fn server(l: Listener, count: Int) Unit
  http.serve_n(l, count, handle)

l = listen(0)?
port = port_of(l)
run server(l, 3)
a = http.get("localhost", port, "/hello")?
println("${a.status} ${a.body}")
b = http.post("localhost", port, "/echo", "hello")?
println("${b.status} ${b.body}")
c = http.get("localhost", port, "/nope")?
println("${c.status} ${c.body}")
```

Output: `200 hello, mixer`, then `200 you said: hello`, then `404 nothing at /nope`. `listen(0)` picks a free port and `port_of` says which. `serve_n` handles three connections and returns, and `http.serve(l, handle)` would go on forever. The client calls return a `Result`, so `?` hands a failed connection back to the caller. Headers are a list of `Header(name, value)`, `http.header_value(headers, "Content-Type")` finds one without regard to case, and `http.request(host, port, method, path, headers, body)` is the general form behind `get` and `post`.

**Mistakes:** expecting TLS or chunked bodies (neither is there), sending binary data as the body, forgetting the `net.connect` or `net.listen` permission, and calling the client on the browser platform, which has no network.

