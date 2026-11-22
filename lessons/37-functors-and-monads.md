# Mapping, sequencing, and combining: functors, applicatives, and monads

Lesson 16 chained steps that might fail with `?` and `|>>`. This lesson names the idea behind them. Three small interfaces, over *type constructors* such as `Result[_, E]` or `List[_]`, describe three ways of working with a value inside a container: change it, combine several, or chain steps that each produce a new container. They have the names Haskell programmers expect.

You don't have to know the names to use any of it; `map`, `?`, and `|>>` work without them. They matter when you want to write code that works for *every* container, or to give your own type the same abilities.

## The three interfaces

```moxie-nocheck
interface Functor[F[_]]
  fn fmap[A, B](self F[A], f (A) -> B) F[B]

interface Applicative[F[_]]
  Functor[F]
  static fn pure[A](a A) F[A]
  fn ap[A, B](self F[(A) -> B], x F[A]) F[B]

interface Monad[F[_]]
  Applicative[F]
  fn flat_map[A, B](self F[A], f (A) -> F[B]) F[B]
```

- A **Functor** can have a function applied to what's inside, keeping the shape (`fmap`).
- An **Applicative** can also wrap a plain value (`pure`) and apply a function that is itself inside the container (`ap`), which is how *independent* values are combined.
- A **Monad** can also chain: `flat_map` feeds the value inside into a function that returns a new container, and the first failure or emptiness stops the chain.

The prelude has instances for `Result[_, E]`, `Stream`, `List[_][N]`, and `Array[_][N]`. `fmap` keeps the container: on a `List` it gives a `List`, on an `Array` an `Array`, and on an `Option` or `Result` the same constructor. (The pipeline stage `map` returns a lazy `Stream`; `fmap` is the container-preserving one that generic code uses.)

The operators `<$>`, `<*>`, and `|>>` are the prelude's spellings of `fmap`, `ap`, and `flat_map` for any such type:

| Operator | Meaning | Use it when |
|---|---|---|
| `f <$> x` | change the value inside | one input, a plain function |
| `f <$> x <*> y` | combine independent values | the inputs don't depend on each other |
| `x \|>> f` | chain a step that returns a container | each step needs the previous result |

`<$>` and `<*>` sit in the comparison tier, so parenthesize them next to other operators.

## With `Result`

```moxie
fn pos(n Int) Result[Int, Error]
  if n > 0 then Ok(n) else fail(1, "not positive")

fn under(n Int) Result[Int, Error]
  if n < 10 then Ok(n) else fail(2, "too big")

good = Ok(4) |>> pos |>> under |>> ((v) -> Ok(v * 3))
bad = Ok(40) |>> pos |>> under |>> ((v) -> Ok(v * 3))
println(good)
println(is_err(bad))
```
```output
Ok(12)
true
```

The chain stops at the first `Err`. Combining independent inputs is the applicative style: one function over several values, with the first error winning.

```moxie
fn add(a Int, b Int) Int = a + b

r1 Result[Int, Error] = Ok(1)
r2 Result[Int, Error] = Ok(2)
bad Result[Int, Error] = fail(9, "bad")
println((curry(add) <$> r1) <*> r2)
println(is_err((curry(add) <$> bad) <*> r2))
```
```output
Ok(3)
true
```

## With `List`

For a `List`, `|>>` runs the function on each element and concatenates the results; this is the list monad:

```moxie
dup = (x Int) -> List(x, x)
sq = (x Int) -> x * x

println(List(1, 2) |>> dup)
println(sq <$> (List(1, 2, 3) |>> dup))
```
```output
List(1, 1, 2, 2)
List(1, 1, 4, 4, 9, 9)
```

## Your own type

`Maybe`, `Option`, `Either`, and similar types are never built into the prelude: you define the type and its instance. To give your own type the three abilities, write one `impl`, naming the constructor and no `for`:

```moxie
enum Box[T]
  Full(v T)
  Empty

fn half(n Int) Box[Int]
  if n % 2 == 0 then Box.Full(n / 2) else Box.Empty

impl Monad[Box]
  fn fmap[A, B](self Box[A], f (A) -> B) Box[B]
    when self
      Full(v) -> Box.Full(f(v))
      Empty -> Box.Empty
  static fn pure[A](a A) Box[A]
    Box.Full(a)
  fn ap[A, B](self Box[(A) -> B], x Box[A]) Box[B]
    when self
      Full(g) -> x.fmap(g)
      Empty -> Box.Empty
  fn flat_map[A, B](self Box[A], f (A) -> Box[B]) Box[B]
    when self
      Full(v) -> f(v)
      Empty -> Box.Empty

println(Box.Full(3).map((x) -> x + 1))
println(Box.pure(20).flat_map(half).flat_map(half))
println(Box.pure(6).flat_map(half).flat_map(half))
```
```output
Box.Full(4)
Box.Full(5)
Box.Empty
```

With the impl in scope, the operators work on `Box` too:

```moxie
enum Box[T]
  Full(v T)
  Empty

impl Monad[Box]
  fn fmap[A, B](self Box[A], f (A) -> B) Box[B]
    when self
      Full(v) -> Box.Full(f(v))
      Empty -> Box.Empty
  static fn pure[A](a A) Box[A]
    Box.Full(a)
  fn ap[A, B](self Box[(A) -> B], x Box[A]) Box[B]
    when self
      Full(g) -> x.fmap(g)
      Empty -> Box.Empty
  fn flat_map[A, B](self Box[A], f (A) -> Box[B]) Box[B]
    when self
      Full(v) -> f(v)
      Empty -> Box.Empty

fn add(a Int, b Int) Int = a + b
fn dec(n Int) Box[Int]
  if n > 0 then Box.Full(n - 1) else Box.Empty
sq = (x Int) -> x * x

println(Box.Full(3) |>> dec |>> dec)
println(Box.Full(1) |>> dec |>> dec)
println(sq <$> Box.Full(7))
lifted = curry(add) <$> Box.Full(4)
println(lifted <*> Box.Full(5))
println(lifted <*> Box.Empty)
```
```output
Box.Full(1)
Box.Empty
Box.Full(49)
Box.Full(9)
Box.Empty
```

The compiler doesn't check the monad laws, evaluation is eager, and there is no return-type dispatch: write `Box.pure(42)`, never a bare `pure(42)`. A type that accumulates several errors should implement `Applicative` only, because a monad stops at the first.

## Collecting every error

`traverse` and `|>>` stop at the first error, which is right for a pipeline and wrong for a form. `map_all(f, r1, r2, ...)` combines two to six `Result`s that share an error type, using a function with one parameter for each. If all are `Ok`, you get `Ok(f(values))`; otherwise you get an `Err` holding the list of *every* error, in argument order:

```moxie
tuple User deriving show
  name String
  email String

fn check_name(s String) Result[String, String]
  when s == ""
    true -> Err("name is empty")
    false -> Ok(s)

fn check_email(s String) Result[String, String]
  when s.contains("@")
    true -> Ok(s)
    false -> Err("bad email: ${s}")

fn create(name String, email String) Result[User, List[String]]
  map_all(User, check_name(name), check_email(email))

println(create("ann", "ann@x.org"))
println(create("", "nope"))
```
```output
Ok(User(name: "ann", email: "ann@x.org"))
Err(List("name is empty", "bad email: nope"))
```

The results can also arrive as a tuple, which suits a pipeline: `(check_name(name), check_email(email)) |> map_all(User)`. A function with the wrong number of parameters is a compile error, and every argument must have the same error type (wrap one with `map_err` to line them up).

The checks run one after another. When each one is slow, `par_map_all(f, c1, c2, ..., limit: n)` takes the same function and, in place of the results, a zero-parameter function for each check, such as `fn () = check_name(name)`. It runs them in parallel, at most `n` at a time, and gives the same answer, including every error in argument order.

`tap(x, f)` is one more small helper: it runs `f(x)` for its effect and gives `x` back, which is handy for a log line in the middle of a pipeline.

## What to remember

- `fmap` / `<$>` changes what's inside; `ap` / `<*>` combines independent values; `flat_map` / `|>>` chains dependent steps.
- The first `Err` (or `Empty`) stops a chain; `map_all` collects *all* the errors instead.
- Your own types join in with `impl Monad[Box]`, no `for`.
- Write `Box.pure(42)`, not `pure(42)`, and parenthesize `<$>` and `<*>`.
