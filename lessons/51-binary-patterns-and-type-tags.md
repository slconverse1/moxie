# Binary patterns, and taking a value apart by its type

Lesson 22 showed patterns for tuples, enums, and lists. This lesson adds two more: patterns that match the *layout of bytes*, and patterns that take apart a value whose type is only known at run time.

## Binary patterns

A byte layout is matched with `Bin(...)` on an `Array[Byte]`. Each element is `name: kind`, read left to right:

| Kind | Meaning |
|---|---|
| `u8`, `i8` | one byte, unsigned or signed |
| `u16be`, `u16le`, `u32be`, `u32le`, `u64be`, `u64le` | unsigned, with the byte order always written |
| `i16be` to `i64le` | the signed forms |
| `bits(n)` | an unsigned field of `n` bits, packed from the high bit (bit fields must add up to whole bytes) |
| `bytes(n)` | a run of bytes; `n` is a number or an earlier field |

A literal byte (`0xCA`) or byte string (`b"MZ"`) must match exactly, `_` skips a field, and `rest: bytes` at the end takes whatever is left:

```moxie
fn describe(packet Array[Byte]) String
  when packet
    Bin(
      0xCA,
      version: bits(4),
      kind: bits(4),
      size: u16be,
      body: bytes(size),
      rest: bytes
    ) -> "v${version} k${kind} size ${size} body ${len(body)} rest ${len(rest)}"
    Bin(a: u8, b: i16le) -> "short ${a} ${b}"
    else "no match"

println(describe(b"\xCA\x21\x00\x02hiXYZ"))
println(describe(b"\xCA\x21\x00\x09hi"))
println(describe(b"\x07\xFE\xFF"))
println(describe(b"\x07"))
```
```output
v2 k1 size 2 body 2 rest 3
no match
short 7 -2
no match
```

A packet that is too short, has a wrong literal, or has bytes left over that no element describes (when the pattern doesn't end in `rest: bytes`) doesn't abort: the arm just fails and the next one is tried. Every field is an ordinary binding, so a guard works (`Bin(...) if size > 0 -> ...`), and `packet is Bin(b"MZ", rest: bytes)` is a Boolean test.

Mistakes: a name that clashes with a prelude function you still need in the arm (a field called `len` hides `len`), bit fields that don't make whole bytes, and a `bytes(n)` that names a field that comes later.

### Building bytes

To go the other way, write `Bin` as an expression with a value in front of each kind. The packet above can be built and read back:

```moxie
fn describe(packet Array[Byte]) String
  when packet
    Bin(0xCA, version: bits(4), kind: bits(4), size: u16be, body: bytes(size), rest: bytes) -> "v${version} k${kind} size ${size} body ${len(body)} rest ${len(rest)}"
    else "no match"

p = Bin(0xCA, 2: bits(4), 1: bits(4), 2: u16be, b"hi": bytes, b"XYZ": bytes)
println(p)
println(describe(p))
```
```output
Array(202, 33, 0, 2, 104, 105, 88, 89, 90)
v2 k1 size 2 body 2 rest 3
```

A value that doesn't fit its kind (`300: u8`) aborts. Arms that cover every length need no `_`: `Bin()`, `Bin(a: u8)`, and `Bin(a: u8, b: u8, rest: bytes)` together do, and the compiler names the first length that no arm covers. An arm with a literal, a guard, or a `bytes(n)` sized by a field earns no credit, so those still need a `_` arm.

## Taking a value apart by its type

A union, or an `any` value, carries a small tag with its type, and `when` reads it. A bare type is an arm (`Int ->`), and `n@Int` also binds the value itself, so `n` is an `Int` in that arm:

```moxie
union type Value = Int | String

fn describe(v Value) String
  when v
    n@Int -> "the number ${n + 1}"
    s@String -> "the text ${s}"

println(describe(41))
println(describe("hi"))
```
```output
the number 42
the text hi
```

A union is exhaustive without a `_` arm. An `any` value is taken apart the same way, with a `_` arm because the full set of types isn't known.

Members with type arguments work the same way. With `type Data = List[Int] | List[String] | Int`, the arms `List[Int] ->` and `xs@List[String] ->` take a `Data` apart, and inside each arm the value has that list type, so `d(0) + 1` is checked as an `Int` addition in the first and rejected in the second. `d is List[Int]` is the same test as a condition.

### With interface values

What a name in the arm refers to depends on how you write it:

```moxie
interface Speaker
  fn speak(self) String

tuple Dog
  name String

tuple Robot deriving show
  serial Int

impl Speaker for Dog
  fn speak(self) String
    "Woof"

impl Speaker for Robot
  fn speak(self) String
    "Beep"

crowd List[any Speaker] = List(Dog(name: "Rex"), Robot(serial: 7))
for s in crowd
  when s
    Dog(name) -> println("a dog named ${name}")
    r@Robot() -> println("a robot, ${r}")
    _ -> println("something else")
```
```output
a dog named Rex
a robot, Robot(serial: 7)
```

- In `Dog(name)`, the parentheses take the dog apart like any tuple pattern, so `name` is the dog's first field (a `String`), not the dog.
- In `r@Robot()`, `r@` names the whole value, so `r` is the `Robot` itself, and the empty parentheses mean no fields are taken.
- `d@Dog(name)` gives both.

Inside an arm, the variable has the narrowed type: in the `Int` arm above, `v` is an `Int`, so `len(v)` there is a compile error, and in the `String` arm `v + 1` is one. The same holds for a parameter typed `any Speaker` inside a `d@Dog() ->` arm, where `d.serial` is a compile error because a `Dog` has no `serial`.

Mistakes: writing `Int(n)` for a scalar (use `n@Int`), and expecting `Dog(d)` to bind the whole `Dog` (it binds the first field).

## What to remember

- `Bin(...)` matches bytes: sized integers with an explicit byte order, `bits(n)`, `bytes(n)`, literals, `rest: bytes`.
- A packet that doesn't fit just fails the arm; nothing aborts.
- `Bin` as an expression builds bytes.
- `n@Int` takes a union or `any` value apart by type and gives `n` the narrowed type.
