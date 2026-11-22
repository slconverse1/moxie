---
layout: default
dialect: gc
title: "Data types that grow: the expression problem · Learning Guide moxie/gc"
---
<p><small>Functional programming</small></p>

# 50. Data types that grow: the expression problem

Suppose a library defines arithmetic as data (numbers and `+`) together with a function that evaluates it. You want to add multiplication, and later a function that prints it, **without editing the library**.

With an `enum` this is the **expression problem**: a new *operation* is easy (write a function), but a new *variant* means editing the `enum` and every `when` over it. Tagless final (lesson 49) solves it, but its programs are functions, so you can't look inside one. This lesson shows a way that keeps real data you can inspect, rewrite, and serialize.

## The pieces

- Each kind of node is its own tuple, generic in the type of its children.
- Each operation is an interface with one `impl` per node, and it receives the recursive call as a parameter.
- A **union type** says which nodes make up one language, and a method called on a union value goes to the member's own `impl`.

```moxie
// the library, never edited again
tuple Lit deriving show
  value Int
tuple Add[E] deriving show
  left E
  right E

interface Eval[E]
  fn eval(self, rec (E) -> Int) Int
impl[E] Eval[E] for Lit
  fn eval(self, rec (E) -> Int) Int
    self.value
impl[E] Eval[E] for Add[E]
  fn eval(self, rec (E) -> Int) Int
    rec(self.left) + rec(self.right)

union type Arith = Lit | Add[Arith]
fn eval_arith(e Arith) Int
  e.eval(eval_arith)

// new code: a variant and an operation, added without editing the code above
tuple Mul[E] deriving show
  left E
  right E
impl[E] Eval[E] for Mul[E]
  fn eval(self, rec (E) -> Int) Int
    rec(self.left) * rec(self.right)

interface Pretty[E]
  fn pretty(self, rec (E) -> String) String
impl[E] Pretty[E] for Lit
  fn pretty(self, rec (E) -> String) String
    "${self.value}"
impl[E] Pretty[E] for Add[E]
  fn pretty(self, rec (E) -> String) String
    "(${rec(self.left)} + ${rec(self.right)})"
impl[E] Pretty[E] for Mul[E]
  fn pretty(self, rec (E) -> String) String
    "${rec(self.left)} * ${rec(self.right)}"

union type Full = Lit | Add[Full] | Mul[Full]
fn eval_full(e Full) Int
  e.eval(eval_full)
fn show_full(e Full) String
  e.pretty(show_full)

a Arith = Add[Arith](Lit(1), Lit(2))
f Full = Mul[Full](Lit(3), Add[Full](Lit(1), Lit(2)))
println(eval_arith(a))
println(eval_full(f))
println(show_full(f))
println(f)
```
**Output:**

```
3
9
3 * (1 + 2)
Mul(left: Lit(value: 3), right: Add(left: Lit(value: 1), right: Lit(value: 2)))
```

Nothing above the "new code" comment changed: `Mul` and `Pretty` are new code, the old `Eval` impls are reused for `Lit` and `Add`, and `Full` is a new union. A node of the union is an ordinary tuple, so `f` prints, compares, and pattern-matches like any other, and `deriving dyn` (lesson 39) writes it out as JSON.

In a real project the two halves would be separate files: `import arith` makes the first part available to the second.

Write the recursion once for any union with a bound: `fn eval_any[U Eval[U]](e U) Int` is `e.eval(eval_any)`, and it works for `Arith`, `Full`, and every union you add later.

## The compiler checks the union

If `Full` held a node that has no `Pretty` impl, `show_full` would fail at run time for that node, so the compiler refuses it: *`e may be a Mul, which has no method pretty: write impl Pretty ... for Mul`*. A generic function with a bound (`fn go[U Pretty[U]](e U)`) gets the same check when you pass it a union.

That check is what makes this a solution to the expression problem and not just a convention: adding a variant without covering every operation you use is a compile error, never a surprise.

## Rewriting

A rewrite has to look at a node's children, so it needs one more small interface that says what a child is. Here `AsLit` answers "is this child a number, and which?", and each node answers it in one line:

```moxie
tuple Lit deriving show
  value Int
tuple Add[E] deriving show
  left E
  right E
tuple Mul[E] deriving show
  left E
  right E
union type Full = Lit | Add[Full] | Mul[Full]

interface AsLit
  fn lit_value(self) Result[Int, Error]
impl AsLit for Lit
  fn lit_value(self) Result[Int, Error]
    Ok(self.value)
impl[E] AsLit for Add[E]
  fn lit_value(self) Result[Int, Error]
    Err(Error(code: 1, message: "not a literal"))
impl[E] AsLit for Mul[E]
  fn lit_value(self) Result[Int, Error]
    Err(Error(code: 1, message: "not a literal"))

interface Simp[E]
  fn simp(self, rec (E) -> E) E
impl[E] Simp[E] for Lit
  fn simp(self, rec (E) -> E) E
    self
impl[E AsLit] Simp[E] for Add[E]
  fn simp(self, rec (E) -> E) E
    when self.left.lit_value()
      Ok(0) -> rec(self.right)
      _ -> Add[E](rec(self.left), rec(self.right))
impl[E AsLit] Simp[E] for Mul[E]
  fn simp(self, rec (E) -> E) E
    when self.right.lit_value()
      Ok(1) -> rec(self.left)
      _ -> Mul[E](rec(self.left), rec(self.right))

fn simplify(e Full) Full
  e.simp(simplify)

f Full = Mul[Full](Add[Full](Lit(0), Lit(4)), Lit(1))
println(simplify(f))
```
**Output:**

```
Lit(value: 4)
```

The two rules are written once, for any union whose members answer `AsLit`; a new node adds its own one-line answer and its own rules, and nothing else changes. Each node type implements `AsLit` itself, because a call finds the `impl` of the member the value holds, not an `impl` on the union.

## Building in any language: `Has`

A smart constructor should build a number in whatever language holds numbers, not only in `Arith`. Bound the type parameter with `Has[...]`, which a union type satisfies when it lists that node:

```moxie
tuple Lit deriving show
  value Int
tuple Add[E] deriving show
  left E
  right E
tuple Mul[E] deriving show
  left E
  right E
union type Arith = Lit | Add[Arith]
union type Full = Lit | Add[Full] | Mul[Full]

fn lit[U Has[Lit]](n Int) U = Lit(n)
fn add[U Has[Add[U]]](a U, b U) U = Add[U](a, b)
fn mul[U Has[Mul[U]]](a U, b U) U = Mul[U](a, b)

x Full = add(lit(1), mul(lit(2), lit(3)))
println(x)
y Arith = add(lit(1), lit(2))
println(y)
```
**Output:**

```
Add(left: Lit(value: 1), right: Mul(left: Lit(value: 2), right: Lit(value: 3)))
Add(left: Lit(value: 1), right: Lit(value: 2))
```

The union a call builds into comes from where the result goes (a binding or a result type), or from a written `lit[Full](5)`. `y Arith = mul(lit(1), lit(2))` is a compile error, because `Arith` cannot hold a `Mul`.

A function that calls `lit` for a type parameter of its own must carry the bound: `fn g[V Has[Lit]](n Int) V = lit(n)`. A union is erased at run time, so `Has` costs nothing: building a `Lit` as a `U` is building a `Lit`.

## Which style when

Choose by what you do with the program. Tagless final (lesson 49) runs the program straight into a result and is the lightest way to add interpreters. Growing data types, as here, keep a tree you can print, store, send, count, rewrite, and analyze before running it. Both let you add variants and operations without editing old code, and the two meet in the middle: an `impl` that builds a tree turns a tagless-final program into this kind of data.

## Mistakes

- Forgetting a node's `impl` for a new operation. The compiler names the missing member.
- Writing `Mul(...)` with children of different types when two unions could hold them. Write `Mul[Full](...)` to say which.
- Putting the `impl` on the union instead of on each node.
- Writing the old operation without the `rec` parameter, which ties it to one union.

## What to remember

- Nodes are tuples generic in their children; operations are interfaces with a `rec` parameter; a `union type` is a language.
- A new variant or a new operation is new code only.
- The compiler checks that every node of a union has every operation you call on it.
- `Has[Node]` lets one smart constructor build into any union that holds that node.

---

[← Tagless final: one program, many interpreters](40-tagless-final.html) · [Contents](./) · [Programs with effects as data: the freer monad →](42-freer-monad.html)
