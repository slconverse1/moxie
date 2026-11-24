---
layout: default
dialect: gc
learn: true
title: "Moxie for imperative programmers · Moxie/gc Mixer’s Guide"
---
# 4. Moxie for imperative programmers

In the Spec: [3. Memory model: S-space, T-space, and resets](../spec.html#s3), [18. Fibers, loops, streams](../spec.html#s18)
{: .specref}

If you come from C, Java, Python, or JavaScript, most habits carry over, and a few need a new spelling. This lesson is a translation table with a working example for each habit.

## Accumulate in a loop

A loop's rebindings don't leave it (lesson 9), so fold with a stream:

```moxie
xs = List(1, 2, 3)
total = xs |> reduce(0, _1 + _2)
println(total)
```
**Output:**

```
6
```

## Early exit

Use `return` for guard clauses, `break(value)` and `else` for loops, and `break #label` from nested loops:

```moxie
fn first_negative(xs List[Int]) Int
  for x in xs
    if x < 0
      return x
  0

found = for x in List(3, 8, 12)
  if x > 5 then break(x)
else
  -1
println(first_negative(List(4, -2, 7)))
println(found)
```
**Output:**

```
-2
8
```

## Update a field

`p.score += 10` rebuilds the tuple, and `p.update` changes several fields at once. A function that changes its caller's variable takes `ref`:

```moxie
tuple Player deriving show
  name String
  score Int
  level Int

p = Player(name: "Ann", score: 0, level: 1)
p.score += 10
println(p)
q = p.update
  score: 99,
  level: 2
println(q)

fn bump(ref who Player) Unit
  who.score += 1

bump(ref p)
println(p.score)
```
**Output:**

```
Player(name: "Ann", score: 10, level: 1)
Player(name: "Ann", score: 99, level: 2)
11
```

## Swap, and update an element

Swap is `a, b = b, a`. `numbers(i) = v` and `numbers(i) += 1` rebind the array, and an update that rebinds a name to an update of itself never copies when the old value is dead afterwards (`moxie build --report` lists the exceptions):

```moxie
a = 1
b = 2
a, b = b, a
numbers = Array(10, 20, 30)
numbers(1) = 99
numbers(2) += 1
println("${a} ${b} ${numbers}")
```
**Output:**

```
2 1 Array(10, 99, 31)
```

## Push to a list, and null

`list += 4` pushes. There is no null: use a `Result`, an `Option`, a `T | ()`, or an enum of your own:

```moxie
list = List(1, 2, 3)
list += 4
println(list)
println(get(list, 10))
```
**Output:**

```
List(1, 2, 3, 4)
Err(Error(code: 4, message: "no such element"))
```

## An outer variable from a nested block

`x@1 += 1` reaches the name one block out (lesson 9):

```moxie
count = 0
for i in 1..4
  count@1 += i
println(count)
```
**Output:**

```
10
```

## Pointers and linked structures

Use a recursive enum, a bounded `Dict` of ids, or a fiber that owns the data. A list of numbers as a linked list would be:

```moxie
enum Chain deriving show
  Link(value Int, next Chain)
  End

fn total(c Chain) Int
  when c
    Link(v, rest) -> v + total(rest)
    End -> 0

c = Chain.Link(1, Chain.Link(2, Chain.Link(3, Chain.End)))
println(total(c))
```
**Output:**

```
6
```

## Exceptions

Return a `Result` and use `?` (lesson 16). There is no `try`.

## The compiler teaches as it goes

A habit from another language is usually caught by name, with the fix in the message:

```moxie
list = List(1, 2, 3)
list.push(4)
println(list)
```
**The compiler says:**

```
error: no method or function `push` for a `List[Int]`
```

```moxie
total = 0
for i in 1..3
  total += i
println(total)
```
**The compiler says:**

```
error: `total += ...` reads the outer `total` but defines a new `total` that disappears when this block ends, so the outer one never changes: write `total@1 += ...` to change the outer one (or `reduce` to fold a stream)
```

```moxie
x = null
println(x)
```
**The compiler says:**

```
error: undefined name `null`
```

## What to remember

- Accumulate with `reduce`, or use `name@1` / `mutable` (lesson 19) when a loop must write outward.
- `p.field += 1` and `p.update` rebuild a tuple; `ref` lets a function change its caller's variable.
- `a, b = b, a` swaps; `list += x` pushes; there is no `null`.
- Recursive enums, `Dict`s of ids, and owning fibers replace pointers; `Result` and `?` replace exceptions.

---

[← Values and names](03-values-and-names.html) · [Contents](./) · [Numbers →](04-numbers.html)
