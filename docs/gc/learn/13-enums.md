---
layout: default
dialect: gc
learn: true
title: "Enums · Learning Guide moxie/gc"
---
<p><small>Data</small></p>

# 15. Enums

A tuple says "a value has *all* of these fields". An *enum* says "a value is *one of* these cases". A traffic light is red, yellow, or green. A shape is a circle with a radius, or a rectangle with a width and height. Enums are how moxie describes data that comes in kinds.

## Plain cases

The simplest enum is a list of named cases:

```moxie
enum Color deriving show, eq
  Red
  Green
  Blue
fav = Color.Blue
println(fav)
println(fav == Color.Red)
println(Color.values())
println(Color.Green.index())
```
**Output:**

```
Color.Blue
false
Array(Color.Red, Color.Green, Color.Blue)
1
```

A case is written with the enum's name, `Color.Blue`. `deriving show, eq` lets you print the values and compare them with `==`. `values()` lists every case, and `index()` is a case's position, starting from zero.

## Cases that carry data

A case can hold values, declared like the fields of a tuple:

```moxie
enum Shape deriving show
  Circle(radius Double),
  Rect(w Double, h Double),
  Empty
println(Shape.Circle(radius: 2.0))
println(Shape.Rect(3.0, 4.0))
println(Shape.Empty)
```
**Output:**

```
Shape.Circle(2.0)
Shape.Rect(3.0, 4.0)
Shape.Empty
```

`Circle` has a radius, `Rect` has two sides, and `Empty` has nothing. Each value is exactly one of the three.

## Taking an enum apart: when

`when` looks at which case a value is, and names the data inside it. This is the main way to use an enum:

```moxie
enum Shape
  Circle(radius Double),
  Rect(w Double, h Double),
  Empty
fn area(s Shape) Double
  when s
    Circle(r) -> 3.14159 * r * r
    Rect(w, h) -> w * h
    Empty -> 0.0
println(area(Shape.Circle(2.0)))
println(area(Shape.Rect(3.0, 4.0)))
println(area(Shape.Empty))
```
**Output:**

```
12.56636
12.0
0.0
```

Inside the `Circle` arm, `r` is the radius. And there is no `else`: a `when` on an enum has to cover **every** case, and the compiler checks it. If you add a fourth case to `Shape` later, every `when` that forgets it becomes a compile error, which is a large part of why enums are worth using:

```moxie
enum Color
  Red
  Green
  Blue
fn name_of(c Color) String
  when c
    Red -> "red"
    Green -> "green"
```
**The compiler says:**

```
error: `when` does not cover `Blue`
```

## Methods: impl

Behavior that belongs to a type goes in an `impl` block. Methods are called with a dot, and inside a method `self` is the value:

```moxie
enum Shape
  Circle(radius Double),
  Rect(w Double, h Double),
  Empty
impl Shape
  fn area() Double
    when self
      Circle(r) -> 3.14159 * r * r
      Rect(w, h) -> w * h
      Empty -> 0.0
  fn is_empty() Bool
    self is Empty
shapes = List(Shape.Circle(1.0), Shape.Rect(2.0, 5.0), Shape.Empty)
for s in shapes
  println("${s.area()} ${s.is_empty()}")
```
**Output:**

```
3.14159 false
10.0 false
0.0 true
```

`self is Empty` is a test that gives a `Bool`; the lesson on patterns shows `is` in full. The same `impl` form works for tuples. Methods live only inside `impl` blocks, never loose in the file.

## Values shared by every case

When every case has the same fields, put them in a header after the enum's name. A classic is a table of planets:

```moxie
enum Planet(mass Double, radius Double)
  MERCURY(mass: 3.303e23, radius: 2.4397e6),
  VENUS(mass: 4.869e24, radius: 6.0518e6),
  EARTH(mass: 5.976e24, radius: 6.3781e6)
impl Planet
  fn surface_gravity() Double
    6.673e-11 * mass / (radius * radius)
println(len(Planet.values()))
println(Planet.EARTH.surface_gravity())
```
**Output:**

```
3
9.802775697614821
```

Inside the methods, `mass` and `radius` are the current case's own values. `Planet.value_of("VENUS")` looks a case up by name and returns a `Result`.

## Bare case names

When only one enum has a case with a given name, you can write the case without the enum's name. If two enums share a name, the compiler asks you to be specific, and `do with` opens one enum's cases for a block:

```moxie
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
**Output:**

```
Light.Red
Signal.Red
Signal.Stop
```

## Cases can be generic

An enum can take a type parameter, which lets one declaration describe a whole family. The two most used enums in moxie are built this way and come with the language, and the next lesson is about them: `Option[T]`, a value or nothing, and `Result[T, E]`, a value or an error.

```moxie
enum Box[A] deriving show
  Full(value A),
  Empty
println(Box.Full(5))
println(Box.Full("five"))
```
**Output:**

```
Box.Full(5)
Box.Full("five")
```

*In the Spec: [6. Tuples, enums, aliases, unions](../spec.html#s6)*

---

[← Tuples](12-tuples.html) · [Contents](./) · [Missing values and failures: Option and Result →](14-missing-and-failed.html)
