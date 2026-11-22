---
layout: default
learn: true
title: "Properties, field delegates, and proxies · Mixer’s Guide moxie"
---
# 58. Properties, field delegates, and proxies

<div class='specref' markdown='1'>In the Spec: [12. Interfaces and `impl` blocks](../spec.html#s12)</div>

Three features let a field do more than hold a value. A *property* runs code when it is read or written. A *field delegate* adds the same behavior to many fields. A *proxy* hands a whole interface to a field, so a type does everything the field does except what you override.

## Properties

A property reads and writes like a field (`a.balance`, `a.balance = 5`), but it can run code when it is read or written. You declare it in a tuple, written like a field with the word `property` in front, and add accessors underneath only when you need them:

```moxie
tuple Account
  owner String,
  property balance Int = 0
    priv set(value)
      assert(value >= 0)
      field = value
    did_set(old)
      println("balance ${old} -> ${field}")
impl Account
  fn (ref Self) deposit(n Int) Unit
    balance = balance + n
a = Account(owner: "Ann", balance: 5)
a.deposit(3)
println(a.balance)
```
**Output:**

```
balance 5 -> 8
8
```

A property with no accessors is a stored field, and `= 0` is its initial value, as for a field. The accessors are `get`, `set(value)`, `will_set(new)`, and `did_set(old)`, indented under the property.

- Inside an accessor, `field` is the stored value: a getter can return it, and a setter stores with `field = value`.
- A bare `get` or `set` with no body means "the default one", so `priv set` keeps the default setter but makes it private to the tuple's own `impl` blocks.
- The constructor runs a value you pass through the setter, so `Account(owner: "Ann", balance: -1)` aborts.
- `did_set` runs only when a write changes the value, and never at construction.
- `will_set(new)` runs just before such a write is stored, with the value on offer, while `field` still holds the old one. The order is `will_set`, then `set`, then `did_set`. It can't veto a write, so validation belongs in `set`.
- Outside a property's own accessors, a bare `balance` in an `impl` goes through the property, as `a.balance` does, so the tuple's own methods can't skip the check.

### A setter that can fail

A setter can reject a value by returning a `Result`. You write the return type after the parameter, and moxie makes a function `set_NAME` that returns the changed tuple, or the `Err`:

```moxie
tuple Account
  owner String,
  property balance Int = 0
    set(value Int) Result[Unit, Error]
      if value < 0
        fail(1, "negative")
      else
        field = value
        Ok(())
when Account(owner: "Ann", balance: 5)
  Err(e) -> println("rejected")
  Ok(a) ->
    when a.set_balance(-1)
      Ok(b) -> println("changed")
      Err(e) -> println("rejected, still ${a.balance}")
    when a.set_balance(9)
      Ok(b) -> println("${b.balance}, was ${a.balance}")
      Err(e) -> println("rejected")
```
**Output:**

```
rejected, still 5
9, was 5
```

The original is never touched, as with any value. Because a write can fail, `a.balance = 9` is a compile error on such a property, and the constructor is a `Result` too (`Account(owner: "Ann", balance: -1)` is an `Err`). A `priv set` can't return a `Result`, since `set_balance` is public.

### Computed properties

A property that stores nothing is a computed one:

```moxie
tuple Rect deriving show
  width Int,
  height Int,
  property area Int
    get
      width * height
    set(value)
      width = value / height
r = Rect(width: 3, height: 4)
println("${r.area} ${r}")
r.area = 24
println("${r.width} ${r.area}")
```
**Output:**

```
12 Rect(width: 3, height: 4)
6 24
```

A property has storage unless it has a `get` body that never uses `field`. `area` has none: it isn't in the tuple's layout, it isn't printed or compared, and it can't have an `= value`. A computed property may have a setter, which writes the other fields. A property that does store a value must store it in its setter (the compiler reports a setter that never uses `field`). Callers can't tell a property from a field.

### `lazy` and `static` properties

`lazy` computes a value once, on its first read. It works for a property and for a local binding. A `static` property belongs to the type and is read through it:

```moxie
tuple Report
  data List[Int],
  lazy property total Int
    get
      data |> sum()
  static property title String = "Weekly"
r = Report(data: List(4, 5, 6))
println("${Report.title}: ${r.total} ${r.total}")
r.data = List(10, 20)
println(r.total)
lazy size = len(r.data) * 100
println("${size}")
```
**Output:**

```
Weekly: 15 15
30
200
```

The expression of a `lazy` property or binding must be pure, because it runs whenever the first read happens, so the compiler rejects one that prints or reads a channel. The result is kept in the value you hold, and `r.data = ...` builds a new value whose cache is empty, which is why the second `r.total` is recomputed. This is different from a `lazy` parameter (lesson 10), which re-runs its argument on every read. A static property is read-only: it takes an `= value` or a `get` body, and shared state that changes belongs in an Atom.

### Properties in interfaces

An interface lists a property the way it lists a field. A field, a property, or a delegate field satisfies it, and callers write `x.name` in every case:

```moxie
interface Named
  name String
interface Wallet
  property balance Int
    get
    set
tuple Person
  given String,
  family String,
  property name String
    get
      "${given} ${family}"
tuple Purse
  property balance Int = 0
impl Named for Person
impl Wallet for Purse
fn greet[T Named](x T) String
  "Hello, ${x.name}"
println(greet(Person(given: "Ada", family: "Lovelace")))
```
**Output:**

```
Hello, Ada Lovelace
```

`name String` asks for something readable. `property balance Int` with `get` and `set` underneath asks for something readable and writable (with neither line, it asks for both). `impl Named for T` is a compile error when `T` has no field or property of that name, or its type differs, or it is read-only where the interface asks for `set`.

### Watching a property

When the tuple is held in an Atom (lesson 30), other code can watch a property, with as many listeners as it likes, such as a database handler and a GUI handler:

```moxie
tuple Account deriving show
  owner String,
  property balance Int = 0
fn save_row(old Int, new Int) Unit
  println("db: ${old} -> ${new}")
shared = Atom[Account](Account(owner: "Ann"))
db = shared.on_change(balance, save_row)
ui = shared.balance +% fn (old Int, new Int) Unit
  println("ui: ${new}")
\swap(shared, (a) -> Account(owner: a.owner, balance: 5))
shared.off_change(ui)
\swap(shared, (a) -> Account(owner: a.owner, balance: 5))
\swap(shared, (a) -> Account(owner: a.owner, balance: 9))
shared.balance -% db
\swap(shared, (a) -> Account(owner: a.owner, balance: 1))
println(@shared)
```
**Output:**

```
db: 0 -> 5
ui: 5
db: 5 -> 9
Account(owner: "Ann", balance: 1)
```

`on_change(shared, balance, handler)` calls `handler(old, new)` whenever a write through the Atom changes `balance`, in the order the handlers subscribed and after the type's own `did_set`. Writing the same value calls nobody. It returns a token, and `off_change(shared, token)` removes the handler. `shared.balance +% handler` and `shared.balance -% token` mean the same two things.

A handler's closure copies what it captures, so it acts through effects: it prints, writes to a channel, or swaps another Atom. A property has room for 8 observers, and `property[16] balance Int` gives it 16. A subscription beyond the limit aborts. Only properties can be watched, not plain fields.

Mistakes with properties: a setter that never stores into `field`, an `= value` on a property that stores nothing, `did_set` or `will_set` on a computed property, writing to a static or computed-only property, a `priv set` written from outside the tuple's `impl`, a `lazy` expression that prints, `on_change` on a plain field, and a property declared on the same line as a one-line tuple (a property goes on its own line).

## Field delegates

A delegate adds behavior to a field's reads and writes, and lets you write that behavior once and reuse it on many fields. Kotlin programmers know the idea as a property delegate (`by`), and Swift programmers as a property wrapper. Use a property when the rule belongs to one field, and a delegate when the same rule belongs to many.

A delegate adds no indirection of its own: its state replaces the field in the layout, and every call is specialized and inlined. What you pay is the delegate's own code, such as the clamp below on every write. A delegate is a declared tuple with one field of the field's type, and it implements `FieldHandler[T]`:

```moxie
tuple Percent
  value Int
impl FieldHandler[Int] for Percent
  fn get_value() Int
    value
  fn (ref Self) set_value(new_value Int) Unit
    value = if new_value < 0 then 0 elif new_value > 100 then 100 else new_value
tuple Gauge
  level Int delegate(Percent)
g = Gauge(level: 150)
println("${g.level}")
g.level = -20
println("${g.level}")
```
**Output:**

```
100
0
```

The constructor runs `150` through the delegate, so it clamps at creation, and each write does too.

A setter may also reject a value by returning a `Result`, as in `fn (ref Self) set_value(new_value Int) Result[Unit, Error]`. Then `Gauge(level: -1)` is a `Result[Gauge, Error]`, and the compiler rejects `g.level = x`, because a field write has nowhere to put a failure. Moxie generates `g.set_level(x)` instead, which returns the changed `Gauge` or the `Err`, as for a property with a `Result` setter.

Mistakes: a delegate on an enum payload or a local (only declared tuple fields), and a delegate field in a tuple used as a `Dict` key.

## Proxies

Sometimes a type should do everything another value does, except for a method or two. Writing a forwarding method for each of the rest is boilerplate, and it goes stale when the interface grows. A **proxy** gives the whole interface to a field and leaves you to write only what differs. Kotlin programmers know it as class delegation. It is not the same as a field delegate, which gives one field its reads and writes.

```moxie
interface Printer
  fn print_message(msg String) Unit,
  fn print_status() Unit

tuple Console
  prefix String

impl Printer for Console
  fn print_message(msg String) Unit
    println("${prefix}: ${msg}")
  fn print_status() Unit
    println("${prefix} is ready")

tuple Logger
  printer Console
  calls Int

impl Printer for Logger proxy(printer)
  fn print_message(msg String) Unit
    println("log: ${calls} earlier calls")
    printer.print_message(msg)

l = Logger(printer: Console(prefix: "console"), calls: 2)
l.print_message("hello")
l.print_status()
```
**Output:**

```
log: 2 earlier calls
console: hello
console is ready
```

The header `impl Printer for Logger proxy(printer)` says that `Logger` is a `Printer` by handing it to its `printer` field. `print_message` is written out, so it runs the logging and then calls the field. `print_status` isn't, so the compiler writes it for you, and it calls `self.printer.print_status()`. If the interface later gains another method, the proxy has it at once. With no methods to override, leave the block off: `impl Printer for Logger proxy(printer)` alone is enough.

The field can hold a concrete type with its own `impl`, or an `any Printer`. A proxy forwards plain methods, and it says why when it can't forward one: a `static` member (there's no value to call it on), a method that changes its receiver, a method that mentions `Self` in its signature (it would be the field's type, not yours), and a generic method. Write those in the block yourself.

The interface has to be declared in the same file, because the compiler needs its method list. `Show` can be proxied too (`impl Show for Pet proxy(dog)`), because the compiler knows its one method, and an interface from an imported package works too. The compiler also checks the field: the name has to be a real field, and a field whose type is declared in the file has to implement the interface.

Mistakes: `proxy` in an `impl` with no `for`, naming a field that doesn't exist or that doesn't implement the interface, and expecting a proxy to forward a `static` or `Self` method.

## What to remember

- `property` adds accessors (`get`, `set`, `will_set`, `did_set`) to one field; `field` is the stored value inside them.
- A setter that returns a `Result` makes `set_NAME` and a `Result` constructor.
- `lazy` computes once; `static property` belongs to the type; properties can be watched through an Atom.
- A delegate (`delegate(Percent)`) shares one rule across many fields.
- `impl I for T proxy(field)` forwards the whole interface to a field except what you write.

---

[← Types that compute](47-types-that-compute.html) · [Contents](./) · [Refined parameters: proofs in the signature →](49-refined-parameters.html)
