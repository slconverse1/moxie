# Patterns

A *pattern* describes the shape of a value and names its parts at the same time. You have used the simplest ones already: `Some(v)` in a `when`, `List(head, ...tail)`, and `a, b = ...` in a binding. This lesson collects them, because the same patterns work everywhere a value is taken apart.

## Where patterns appear

A pattern can stand in a `when` arm, on the left of a binding, in a function parameter, in an `is` test, and in a `for` loop. They all mean the same thing: *does the value have this shape, and if so, what are its parts?*

```moxie
tuple Point(x Int, y Int)
Point(a, b) = Point(3, 4)
println(a + b)
for (name, age) in Dict(ann -> 30, bo -> 25)
  println("$name is $age")
```
```output
7
ann is 30
bo is 25
```

A pattern that can't fail, like a tuple pattern against a tuple, can be used in a plain binding. A pattern that *can* fail (like `Some(v)`) needs somewhere to say what happens when it doesn't match: `when`, `if x is ...`, or a let-else, all shown below.

## Literals, names, and the wildcard

In a `when`, a literal matches that value, a bare name matches anything and binds it, and `_` matches anything without binding:

```moxie
fn describe(n Int) String
  when n
    0 -> "zero"
    1 -> "one"
    other -> "many: $other"
println(describe(0))
println(describe(1))
println(describe(7))
```
```output
zero
one
many: 7
```

Arms are tried from the top, and an arm that matches everything (`other`, `_`, or `else`) ends the list. Anything written after it could never run, and the compiler warns about it.

## Ranges, comparisons, and alternatives

```moxie
fn grade(score Int) String
  when score
    in 90..100 -> "A"
    in 80..89 -> "B"
    >= 60 -> "pass"
    1 | 2 | 3 -> "tiny"
    else "fail"
println(grade(95))
println(grade(85))
println(grade(70))
println(grade(2))
println(grade(40))
```
```output
A
B
pass
tiny
fail
```

`in 90..100` is a range test, `>= 60` compares, and `1 | 2 | 3` is three alternatives sharing one arm. Comparison patterns work for any ordered type, so they work on `Double` and `String` too.

On an integer type with a bounded range, such as `Int[0..100]`, arms that cover the whole range need no `else`.

## Taking a tuple apart

A tuple pattern names the type and the fields, by position or by name. It can name just some fields, and `...` skips the rest:

```moxie
tuple User
  name String
  role String
  age Int
fn label(u User) String
  when u
    User(role: "admin", ...) -> "${u.name} (admin)"
    User(name, _, age) if age < 18 -> "$name (minor)"
    User(name, ...) -> name
println(label(User("ann", "admin", 40)))
println(label(User("bo", "guest", 12)))
println(label(User("cy", "guest", 33)))
```
```output
ann (admin)
bo (minor)
cy
```

Patterns nest: a field's pattern can itself be a pattern.

```moxie
tuple Point(x Int, y Int)
tuple Segment(from Point, to Point)
fn is_horizontal(s Segment) Bool
  when s
    Segment(Point(_, y1), Point(_, y2)) -> y1 == y2
println(is_horizontal(Segment(Point(0, 5), Point(9, 5))))
println(is_horizontal(Segment(Point(0, 5), Point(9, 6))))
```
```output
true
false
```

## Naming the whole value as well: @

`name@pattern` binds the whole value to `name` while also matching its shape:

```moxie
enum Shape
  Circle(r Double)
  Square(side Double)
fn describe(s Shape) String
  when s
    c@Circle(r) if r > 10.0 -> "a big circle"
    Circle(r) -> "a circle of radius $r"
    Square(side) -> "a square"
println(describe(Shape.Circle(20.0)))
println(describe(Shape.Circle(2.0)))
println(describe(Shape.Square(3.0)))
```
```output
a big circle
a circle of radius 2.0
a square
```

## Guards

An arm can add an `if` condition. The arm matches only when the pattern matches *and* the condition holds, and the condition can use the names the pattern bound. The compiler can't know whether guards cover every case, so a `when` that relies on guards needs a final arm without one.

```moxie
n = 25
when
  n < 0 -> println("negative")
  n % 2 == 0 -> println("even")
  else println("odd and positive")
```
```output
odd and positive
```

A `when` with no value in front is just guards in order, and a neat way to write an `elif` chain.

## Comparing with a variable: pins

A name in a pattern *binds*, so it can't also mean "equal to this existing variable". To compare against a variable, pin it with `^`. `^(expr)` pins any expression:

```moxie
limit = 100
fn check(reading Int, limit Int) String
  when reading
    ^limit -> "exactly at the limit"
    ^(limit + 1) -> "just over"
    n -> "reading $n"
println(check(100, limit))
println(check(101, limit))
println(check(50, limit))
```
```output
exactly at the limit
just over
reading 50
```

## Lists

List patterns name the first elements and the rest. A bare `...` skips whatever is left, and `...rest` binds it:

```moxie
fn show(xs List[Int]) String
  when xs
    List() -> "empty"
    List(only) -> "one: $only"
    List(a, b) -> "two: $a and $b"
    List(first, ...rest) -> "$first then ${len(rest)} more"
println(show(List()))
println(show(List(1)))
println(show(List(1, 2)))
println(show(List(1, 2, 3, 4)))
```
```output
empty
one: 1
two: 1 and 2
1 then 3 more
```

## Dicts

A Dict pattern matches a subset of the entries:

```moxie
status = Dict("speed" -> 60, "limit" -> 100)
when status
  Dict("speed" -> current, "limit" -> 100) -> println("moving at $current")
  else println("idle")
```
```output
moving at 60
```

## The is test

`value is Pattern` is an expression that gives a `Bool`, and the names the pattern binds are available in the `then` part. `is not` is the negation, and it binds nothing:

```moxie
enum Reading
  Value(n Int)
  Missing
fn show_reading(r Reading) String
  if r is Value(n) then "value $n" else "missing"
println(show_reading(Reading.Value(7)))
println(show_reading(Reading.Missing))
```
```output
value 7
missing
```

`is` also appears with the right side of `and`: `r is Value(n) and n > 5` is safe, because `n` is bound once the first half is true.

## let-else: leave if it doesn't match

A binding with a pattern that can fail takes an `else`. If the pattern matches, the names are bound and the function continues. If not, the `else` value is what the whole function returns:

```moxie
enum Reading
  Value(n Int)
  Missing
fn times_ten(r Reading) Reading
  Value(n) = r else Reading.Missing
  Reading.Value(n * 10)
println(times_ten(Reading.Value(7)))
println(times_ten(Reading.Missing))
```
```output
Reading.Value(70)
Reading.Missing
```

It keeps the main path of a function flat, with the unusual cases handled at the top, in the same way as an early `return`.

## Completeness

A `when` on an enum or union must cover every case, and the compiler checks nested patterns too. If `Some(Circle(r))`, `Some(Square(s))` and `None` are covered but `Some(Triangle(_))` isn't, it is an error that names the missing case. So adding a case to an enum finds, at compile time, every `when` that needs to learn about it.
