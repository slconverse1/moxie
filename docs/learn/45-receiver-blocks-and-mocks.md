---
layout: default
title: "Receiver blocks, interface composition, and mocks · Learn moxie"
---
<p><small>Designing with interfaces</small></p>

# 44. Receiver blocks, interface composition, and mocks

Lesson 20 introduced methods and interfaces. This lesson adds the tools you reach for as programs grow: blocks that run with a value as their receiver, interfaces built from other interfaces, interfaces that require a field, and swapping a real service for a fake one in a test.

## Receiver blocks: `do` and `update`

A block can run with a value as its *receiver*, so the value's fields are in scope without naming the object. `x.do` gives the block's value, with the block on the lines below and no `->`. `x.update` builds a changed copy from `field: value` lines (`=` always means a binding, so it isn't used here). As in a constructor, a comma ends each line except the last, and `&` stands for the field's current value, so `retries: & * 2` doubles it without repeating the name:

```moxie
tuple Limits
  retries Int,
  timeout Int
tuple Config
  host String,
  port Int,
  limits Limits
base = Config(
  host: "localhost",
  port: 80,
  limits: Limits(retries: 3, timeout: 30)
)
label = base.do
  "$host:$port"
secure = base.update
  port: 443,
  limits:
    retries: & * 2
print("$label ${secure.host} ${secure.port} ${secure.limits.retries} ")
println("${secure.limits.timeout} ${base.port}")
```
**Output:**

```
localhost:80 localhost 443 6 30 80
```

`base` is unchanged; `&` inside the nested block is the old `3`; `timeout` is carried over. Every right-hand side sees the *original* value, so the order of the lines doesn't matter.

A `&` that is the slot of a pipe stage (`names: & |> take(2)` or `take(&, 2)`) keeps that meaning, and an update line that needs the current value inside a call can use `&` as the receiver (`names: &.reverse()`) or the field's name.

### Receiver functions and trailing lambdas

A function can take a *receiver function* and call it on a value. The lambda is an argument like any other: its receiver comes from the expected type, so `port` and `self` are the `Config` it is applied to:

```moxie
tuple Limits
  retries Int,
  timeout Int
tuple Config
  host String,
  port Int,
  limits Limits
base = Config(
  host: "localhost",
  port: 80,
  limits: Limits(retries: 3, timeout: 30)
)
fn apply(base Config, change Config.() -> Config) Config
  base.change()
bumped = apply(base, () -> Config(...self, port: port + 1))
println("${bumped.port}")
```
**Output:**

```
81
```

When the last parameter is a function, the lambda may instead go after the call's parentheses, as a **trailing lambda**, which lets its body be a block of lines:

```moxie
tuple Limits
  retries Int,
  timeout Int
tuple Config
  host String,
  port Int,
  limits Limits
base = Config(
  host: "localhost",
  port: 80,
  limits: Limits(retries: 3, timeout: 30)
)
fn apply(base Config, change Config.() -> Config) Config
  base.change()
again = apply(base)() -> self.update
  port: & + 1
println("${again.port}")
```
**Output:**

```
81
```

Here `apply(base)` is the call, and the lambda after it fills the last parameter, `change`.

Name lookup inside a receiver body goes locals first, then the receiver's fields and methods, then the module; `self` is the innermost receiver.

Mistakes: `port = 443` inside an `update` block (that binds a local), a field line in a plain `do` block, a misspelled or repeated field name, a nested block on a field that isn't a declared tuple, and expecting an outer receiver's fields to need `self`.

## Composing interfaces

An interface may embed others by name, and one `impl` supplies all the members:

```moxie
interface Speaker
  fn speak() String
interface Mover
  fn move_by(dx Int) Self
interface Actor
  Speaker,
  Mover
tuple Robot2 deriving show
  name String,
  x Int
impl Actor for Robot2
  fn speak() String
    "$name at $x"
  fn move_by(dx Int) Robot2
    Self(..., x: x + dx)
fn announce(s Speaker) Unit
  println(s.speak())
fn step[A Actor](a A) String
  a.move_by(5).speak()
r = Robot2(name: "R2", x: 1)
announce(r)
println(step(r))
```
**Output:**

```
R2 at 1
R2 at 6
```

`Robot2` satisfies `Actor`, `Speaker`, and `Mover`, which is why `announce` accepts it. Identical signatures from two embedded interfaces merge, and differing ones are a conflict error.

## Extending without editing

You can't edit a type you don't own, but you can still extend: declare your own interface and `impl` it for the old type, or declare your own type and `impl` the old interface for it:

```moxie
interface Describable
  fn describe() String
impl Describable for Int
  fn describe() String
    "the number $self"
println(7.describe())
```
**Output:**

```
the number 7
```

Enums are closed on purpose: adding a case means every `when` must change, and the compiler finds them. For an open collection of unrelated types use `any Interface` (next lesson), and a union type of the known types is the closed alternative.

## Interfaces that require a field

An interface may require a *property*, a read-only field. A type satisfies it by having a field of that name and type, and callers always write `x.name`:

```moxie
interface Named
  name String
tuple User
  id Int,
  name String
tuple Pet
  name String,
  owner String
impl Named for User
impl Named for Pet
fn greet[T Named](x T) String
  "Hello, ${x.name}"
print("${greet(User(id: 1, name: "Ada"))} / ")
println("${greet(Pet(name: "Rex", owner: "Bo"))}")
```
**Output:**

```
Hello, Ada / Hello, Rex
```

An impl with nothing to define has no body. A field with a delegate makes a computed property, and `any Named` works too.

Mistakes: `impl Named for T` where `T` has no `name` field of type `String`, a property satisfied by `fn name() String` (it must be a field), writing `x.name = ...` through a `Named` bound, and an enum whose cases carry different payloads.

## Injection and mocks

Interfaces are compile-time only, so a mock is just another `impl`, and the caller picks it by type. A `ref` receiver in the interface lets one signature serve both a recording mock and a real service:

```moxie
interface Mailer
  fn (ref Self) notify(user_id Int, amount Int) Unit
tuple FakeMailer
  calls Int,
  last_user Int
impl Mailer for FakeMailer
  fn (ref Self) notify(user_id Int, amount Int) Unit
    calls += 1
    last_user = user_id
tuple SmtpMailer
  outbox ChanW[Int]
impl Mailer for SmtpMailer
  fn (ref Self) notify(user_id Int, amount Int) Unit
    \write(outbox, user_id)
fn charge[M Mailer](ref mailer M, user_id Int, amount Int) Int
  fee = amount / 100
  ref mailer.notify(user_id, amount - fee)
  fee
mock = FakeMailer(calls: 0, last_user: 0)
fee = charge(ref mock, 7, 500)
println("$fee ${mock.calls} ${mock.last_user}")
```
**Output:**

```
5 1 7
```

Production code passes an `SmtpMailer` to the same `charge`, and the compiler specializes it for each type, so the choice costs nothing at run time. (`SmtpMailer.notify` never rebinds `self`, but the interface requires the `ref`, so there's no warning.)

The other two styles are a `using` parameter for read-only services such as clocks and configuration (`fn charge(user_id Int, amount Int, using clock Clock) Int`; it can't inject a resource), and a fiber behind a channel that a test replaces with a fake fiber speaking the same protocol.

## What to remember

- `x.do` runs a block with `x` as receiver; `x.update` builds a changed copy, with `&` for the current value.
- A trailing lambda goes after the call's parentheses and can be a block.
- Embed interfaces to build bigger ones; one `impl` supplies everything.
- Extend a foreign type by implementing your own interface for it.
- A mock is another `impl`; the caller picks it by type, and it costs nothing at run time.

---

[← GADTs and typestate](43-gadts-and-typestate.html) · [Contents](./) · [Typeclasses →](46-typeclasses.html)
