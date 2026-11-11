# Draft: "Membership, not inheritance" (for superpower 18, both intros) - NOT yet in the intros

Waiting on Steve's OK. The example below was run and prints:
`a dog called Rex, a dog called Ann` / `a Mini` / `the number 1, the number 2, the number 3` / `Rex says Woof`.

Prose: no type hierarchy and no inheritance; an interface works like a club (a set, in mathematical terms) and an impl says a type belongs to it; a type can join one
club or a hundred and joining adds nothing to the type: no fields, no hidden pointer, no parent; some generic functions say which clubs their type must belong to, and any
member can be used, related or not; membership can be added after the fact and by someone else; a class language would need a common
base class or a wrapper. A non-member is a compile error ("`Dog` doesn't implement `Describable`, which `describe_all` requires of `T`").

```
interface Speaker:
  fn speak(self) String
interface Describable:
  fn describe(self) String
tuple Dog deriving eq, ord:
  name: String
tuple Car:
  model: String
impl Speaker for Dog:
  fn speak(self) String:
    "${self.name} says Woof"
impl Describable for Dog:
  fn describe(self) String:
    "a dog called ${self.name}"
impl Describable for Car:
  fn describe(self) String:
    "a ${self.model}"
impl Describable for Int:
  fn describe(self) String:
    "the number ${self}"
fn describe_all[T: Describable](items: List[T]) String:
  items |> to_stream() |> map((x): x.describe()) |> join(", ")
fn same_voice[T: Speaker + Equatable](a: T, b: T) String:
  if a == b: a.speak() else: "two different voices"
println(describe_all(List(Dog(name: "Rex"), Dog(name: "Ann"))))
println(describe_all(List(Car(model: "Mini"))))
println(describe_all(List(1, 2, 3)))
println(same_voice(Dog(name: "Rex"), Dog(name: "Rex")))
```
