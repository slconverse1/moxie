---
layout: default
title: "Units of measure · Learning Guide moxie"
---
<p><small>Data from outside</small></p>

# 43. Units of measure

A number that means meters should not be addable to a number that means seconds. Moxie lets you say so, and checks it before the program runs. Units are a compile-time check only: at run time a quantity is just the number.

## Declaring units

`unit m` declares a unit. A number followed by a space and a unit, such as `5.0 m`, is a *quantity*, and the checker keeps the unit in the type: `Double[m]`. A function can say what it takes and gives:

```moxie
unit m
unit s

fn speed(d Double[m], t Double[s]) Double[m/s] = d / t

println(speed(100.0 m, 9.58 s))
```
**Output:**

```
10.438413361169102
```

`+`, `-`, and comparisons need the same unit on both sides. A plain number is not a quantity, so `1.0 m + 2.0` is an error; write `2.0 m`.

```moxie
unit m
unit s

x = 1.0 m + 2.0 s
println(x)
```
**The compiler says:**

```
error: cannot add `Double[m]` and `Double[s]`: the units differ (m and s)
```

## Arithmetic carries units along

`*` and `/` combine units: `Double[m] / Double[s]` is `Double[m/s]`, and `m / m` is a plain number. Multiplying by a plain number keeps the unit. Write a power with `^`: `m/s^2`, or `(m/s)^2` in a type.

A derived unit is defined from others, and `Double[N]` and `Double[kg*m/s^2]` are the same type:

```moxie
unit m
unit s
unit kg
unit N = kg * m / s^2

fn force(mass Double[kg], a Double[m/s^2]) Double[N] = mass * a
fn area(w Int[m], h Int[m]) Int[m^2] = w * h

println(force(2.0 kg, 9.8 m/s^2))
println(area(3 m, 4 m))
d = 3.0 m + 4.0 m
println(d * 2.0)
println(d / 2.0 m)
```
**Output:**

```
19.6
12
14.0
3.5
```

Some library functions understand units: `abs`, `min`, `max`, `sum`, `floor`, `ceil`, and `round` keep the unit; `sqrt` halves it (every power must be even); `pow(x, 2)` multiplies it (the exponent must be a constant). `product` of quantities is refused, because the unit would depend on how many there are. `magnitude(q)` gives the bare number, and `x * 1.0 m` attaches a unit to one.

```moxie
unit m

d = 3.0 m + 4.0 m
println(sqrt(4.0 m^2))
println(sum(List(1.0 m, 2.0 m, 3.0 m)))
println(magnitude(d))
```
**Output:**

```
2.0
6.0
7.0
```

A literal takes a unit only if the unit was declared above it, so `5 s` is five seconds only after `unit s`. Written without a space, `5s` is still a `Duration`.

## Scaled units and conversion

A unit can be a multiple of another: `unit km = 1000 m`, `unit mile = 1609.344 m`, `unit h = 3600 s`. A scaled unit has the same dimension as its base, so `Double[km]` and `Double[m]` are the same type and `3.0 km + 500.0 m` is fine.

Every quantity is *stored* in the base unit, so `5.0 km` is `5000.0`, and printing it shows `5000.0`. To get the number a quantity holds in some unit, write `in` and the unit:

```moxie
unit m
unit s
unit km = 1000 m
unit h = 3600 s
unit kmh = km / h

d = 5.0 km + 500.0 m
println(d)
println(d in km)
println(90.0 kmh in m/s)
println(3 km in m)
println("${d in km} km")
```
**Output:**

```
5500.0
5.5
25.0
3000
5.5 km
```

`in` followed by a declared unit is a conversion; anything else after `in` is still a membership test (`x in 1..5`). The unit has to be the same kind as the quantity (`d in s` is a compile error), and the result is a plain number: a `Double`, or an `Int` only when an `Int` quantity is written in its base unit (`3 km in m`). `d / 1.0 km` does the same.

An `Int` amount has to be a whole number of the base unit, so `3 km` is fine and `3 mile` is a compile error; write `3.0 mile`.

Temperatures in Celsius or Fahrenheit are not units here, because their zero points differ from kelvin's. Kelvin is an ordinary unit.

## Functions that work for any unit

Write the unit as a type parameter. Each call fixes it from its arguments:

```moxie
unit m
unit s

fn twice[U](x Double[U]) Double[U] = x + x
fn rate[A, B](a Double[A], b Double[B]) Double[A/B] = a / b
fn sq[U](x Double[U]) Double[U^2] = x * x

println(twice(3.0 m))
v Double[m/s] = rate(6.0 m, 2.0 s)
println(v)
println(sq(3.0 m))
```
**Output:**

```
6.0
3.0
9.0
```

Inside the body, `U` is an unknown but fixed unit, so `x + x` is fine and `x * x` is a `Double[U^2]`, not a `Double[U]`. Two parameters that share one `U` must have the same unit.

## Units across files

A package can export units: write `export unit m` in the package and `import` it, and its units are in scope in your file. In a package of several files, a unit declared in any file is known to all of them.

A dictionary key of `Int[m]` works like any `Int`; a `Double[m]` is not hashable, like a `Double`.

## What to remember

- `unit m` declares one; `5.0 m` is a quantity of type `Double[m]`.
- Adding or comparing different units is a compile error. Multiplying and dividing combine them.
- A scaled unit (`unit km = 1000 m`) is stored in the base unit; `d in km` reads the number out.
- `fn f[U](x Double[U])` works for any unit.
- Units cost nothing at run time.

---

[← Networking, deadlines, and parallel work](33-networking.html) · [Contents](./) · [Databases with SQL →](35-sql.html)
