---
layout: default
learn: true
title: "Numbers · Moxie Mixer’s Guide"
---
# 5. Numbers

In the Spec: [5. Scalars, numbers, text, ranges](../spec.html#s5), [10. Operators](../spec.html#s10), [24. Prelude reference](../spec.html#s24)
{: .specref}

Moxie has several number types. Most programs use two of them, `Int` for whole numbers and `Double` for numbers with a fraction, and meet the others only when they need exact sizes, very large numbers, or exact decimals.

## Int and Double

A number written without a point is an `Int`, and one written with a point is a `Double`:

```moxie
whole = 42
fraction = 3.14
println("$whole $fraction")
```
**Output:**

```
42 3.14
```

`Int` is a 64-bit signed integer on current machines, and `Double` is a 64-bit floating-point number. Large literals can use underscores to be readable, and hexadecimal, octal, and binary have prefixes:

```moxie
println(1_000_000)
println(0xFF)
println(0o17)
println(0b1010)
println(1.5e3)
```
**Output:**

```
1000000
255
15
10
1500.0
```

Note that `1.5e3` is a `Double` (1500.0), never an `Int`.

## Arithmetic

The usual operators work: `+`, `-`, `*`, `/`, and `%` for the remainder. On `Int`, `/` drops the fraction and rounds toward zero, and `%` keeps the sign of the left side:

```moxie
println(7 + 2)
println(7 - 2)
println(7 * 2)
println(7 / 2)
println(-7 / 2)
println(7 % 3)
println(-7 % 3)
```
**Output:**

```
9
5
14
3
-3
1
-1
```

On `Double`, `/` keeps the fraction:

```moxie
println(7.0 / 2.0)
println(1.0 / 3.0)
```
**Output:**

```
3.5
0.3333333333333333
```

Operators follow the usual precedence (multiplication before addition), and parentheses group:

```moxie
println(2 + 3 * 4)
println((2 + 3) * 4)
```
**Output:**

```
14
20
```

## Int and Double don't mix silently

Moxie won't turn an `Int` into a `Double` for you when information could be lost, and a 64-bit `Int` can't always be held exactly in a `Double`. Mixing them is an error, and the fix is to say what you mean with `cast`:

```moxie
count = 3
price = 2.5
println(price * count)
```
**The compiler says:**

```
error: cannot apply `*` to `Int` and `Double`: an integer this wide does not fit a `Double` exactly, so convert on purpose (`cast[Double](x)`)
```

```moxie
count = 3
price = 2.5
println(price * cast[Double](count))
```
**Output:**

```
7.5
```

A literal is different: a bare number takes the type of the other side, so `price * 2` works (the `2` is read as a `Double`):

```moxie
price = 2.5
println(price * 2)
```
**Output:**

```
5.0
```

## Math functions

Common functions are always available: `abs`, `min`, `max`, `pow`, `sqrt`, `floor`, `ceil`, and `round`:

```moxie
println(abs(-4))
println(min(3, 9))
println(max(3, 9))
println(pow(2, 10))
println(sqrt(2.0))
println(floor(2.7))
println(ceil(2.1))
println(round(2.5))
```
**Output:**

```
4
3
9
1024
1.4142135623730951
2
3
3
```

`floor`, `ceil`, and `round` of a `Double` give an `Int`.

## When a number goes wrong

Integer arithmetic is checked. An overflow, or a division by zero, doesn't quietly give a wrong answer. If the compiler can see it, it's a compile error:

```moxie
println(10 / 0)
```
**The compiler says:**

```
error: division by a constant zero
```

and if the problem only shows up when the program runs, the running fiber aborts with a diagnostic. Floating-point numbers follow the IEEE rules instead: dividing by zero gives infinity, and nothing aborts:

```moxie
zero = 0.0
println(1.0 / zero)
println(is_inf(1.0 / zero))
```
**Output:**

```
INF
true
```

## Exact sizes

When you need a particular size, write the type: `Int8`, `Int16`, `Int32`, `Int64`, and the unsigned `UInt8` through `UInt64` (`Byte` is another name for `UInt8`). `Float` is a 32-bit float. A literal can carry its type as a suffix:

```moxie
small = 100i8
big = 4_000_000_000u32
ratio = 0.5f
println("$small $big $ratio")
```
**Output:**

```
100 4000000000 0.5
```

A literal that doesn't fit is an error, not a wraparound:

```moxie
x = 300i8
```
**The compiler says:**

```
error: literal 300 does not fit `Int8`
```

Two numbers of different sizes combine when every value of one fits in the other, and the result is the wider type, so `Int8 + Int16` is an `Int16` with no cast:

```moxie
a Int8 = 100
b Int16 = 1000
c = a + b
println(c)
```
**Output:**

```
1100
```

When it doesn't fit (`Int8 + UInt8`, or `Int64 + UInt64`), you say what you want with `cast`. The full table of rules is in the Spec, section 5.

## Wrapping, saturating, and checked arithmetic

Ordinary `+`, `-`, and `*` abort on overflow. When you want something else, ask for it by name:

```moxie
a UInt8 = 250
b UInt8 = 10
println(wrapping_add(a, b))
println(saturating_add(a, b))
println(checked_add(a, b))
println(checked_add(a, 1))
```
**Output:**

```
4
255
Err(Error(code: 6, message: "overflow"))
Ok(251)
```

`wrapping_add` keeps the low bits (useful for hashes), `saturating_add` sticks at the limit, and `checked_add` gives a `Result`: `Ok` with the sum, or `Err` when it overflowed. Results have their own lesson.

## Bounded integers

An integer type can be limited to a range, and the compiler enforces it:

```moxie
type Percent = Int[0..100]
ok Percent = 85
println(ok)
```
**Output:**

```
85
```

```moxie
type Percent = Int[0..100]
bad Percent = 101
```
**The compiler says:**

```
error: `101` is out of range for `Int[0..100]`
```

## Big and exact numbers

For numbers beyond 64 bits there is `BigInt[n]`, a signed integer of `n` bits (a multiple of 64). For money and other exact decimal values there is `Decimal`, written with a `d` suffix, which doesn't round unless you ask:

```moxie
price = 19.99d
qty = 3
total = price * cast[Decimal[2, 0]](qty)
println(total)
println(0.1 + 0.2)
println(0.10d + 0.20d)
```
**Output:**

```
59.97
0.30000000000000004
0.30
```

A `Decimal` prints with exactly its scale, and compares exactly. The ordinary `Double` sum above shows why money is better in `Decimal`.

---

[← Moxie for imperative programmers](58-for-imperative-programmers.html) · [Contents](./) · [Text →](05-text.html)
