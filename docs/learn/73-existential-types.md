---
layout: default
learn: true
title: "Existential types · Moxie Mixer’s Guide"
---
# 72. Existential types

An *existential type* says: there is some type here that satisfies an interface, but the code doesn't need to know which one. In moxie you write it as `any` followed by an interface, as in `any Shape`. A value of type `any Shape` can be a `Square`, a `Circle`, or any other type with an `impl` of `Shape`, and the only things you can do with it are the things `Shape` promises.

## Mixing types in one list

A generic function, such as `fn total[S Shape](xs List[S])`, works on any type that is a `Shape`, but every element of its list has the same type. When the list must hold different shapes together, use `any Shape`:

```moxie
interface Shape
  fn area(self) Double

tuple Square
  side Double

tuple Circle
  radius Double

impl Shape for Square
  fn area(self) Double
    self.side * self.side

impl Shape for Circle
  fn area(self) Double
    3.0 * self.radius * self.radius

shapes = List[any Shape][3](Square(side: 2.0), Circle(radius: 1.0), Square(side: 3.0))
for s in shapes
  println(s.area())

fn total(xs List[any Shape][3]) Double
  areas = xs |> map()(s) -> s.area()
  areas |> sum()

println(total(shapes))
```
**Output:**

```
4.0
3.0
9.0
16.0
```

Each element keeps its own type inside the list, and `area` is called on whichever type it holds. The list doesn't know, and doesn't need to know, that it has squares and a circle.

## Functions that take any shape

A parameter typed `any Shape` takes any shape, one at a time. The `total` function above is written once, and it works for every type that will ever be a `Shape`. Its parameter is a list of `any Shape`, so it sums the areas of a mixed list.

## What the type hides

Once a value is `any Shape`, the concrete type is out of sight. You can call what the interface offers, and nothing else:

- You can't read the `side` of a square from an `any Shape`, because `side` isn't part of `Shape`.
- You can't ask the value whether it is a `Circle`. If the program needs that, the interface has to offer a method that answers it.
- Comparing two `any Shape` values works when the interface has no `Self` parameter, as this one doesn't, because they are compared by the same method the interface gives.

This is the trade. The interface says what matters, and everything else is hidden. That hiding is what makes the type *existential*: it says a type exists, and not which one.

## Generics or `any`?

- Use a generic when all the values in a place have one type, and the function should know that type. The compiler checks each call at its own type, with no run-time lookup.
- Use `any` when different types must sit together in one collection or one parameter, and only the interface matters.

## What to remember

- `any Interface` is an existential type: some type that satisfies the interface.
- A list or a parameter of `any Shape` can hold different shapes together.
- Only the interface's methods are visible, so the concrete type stays hidden.
- A generic keeps one type per place. `any` allows different types side by side.

---

[← Iterators and generators](72-iterators-and-generators.html) · [Contents](./) · [Modularity and encapsulation without classes →](74-modularity-and-encapsulation.html)
