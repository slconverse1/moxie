# DRAFT: Higher-kinded types (not yet in the docs)

Examples below were run in both dialects (`own.mx`: Box, List) unless noted.

## Intro superpower (both dialects; one new numbered section)

### N. Functions over containers, not just values

`List[Int]` is a type. `List` by itself is a *type constructor*: give it a type and it makes a type. Most languages let you write a function over any type. Moxie also lets you write one over any type constructor, which Haskell and Scala people call *higher-kinded types*. You write the constructor as a parameter, `F[_]`:

```
fn twice[F[_]: Functor](m: F[Int]) F[Int]:
  m.map((x): x * 2).map((x): x + 1)

println(twice(Box(3)))        // Box(value: 7)
println(twice(List(1, 2, 3))) // List(3, 5, 7)
```

One function, written once, works on every container that is in the `Functor` club. Without this you would write `twice` again for each container. `Functor`, `Applicative`, and `Monad` are ordinary interfaces over type constructors, which is why `for:` comprehensions work on any type with a `Monad` impl.

There is no run-time cost. Each use is compiled for its concrete container (the compiler stamps out a copy for `Box` and another for `List`), so there are no tables and no type information at run time. That is why this works in moxie, which has no GC, as well as in moxie/gc.

## Guide section (after generics, before interfaces' advanced topics)

1. Type constructors as functions on types (`Box`, `List`, `Result[_, E]`).
2. `F[_]` and `F[_, _]`; bounds go after: `[F[_]: Monad]`.
3. The `twice` example above, then "why you can't do this without it" (three copies).
4. Club framing (the set parenthetical is in the membership passage, so only repeat it if this section comes first): `Monad` is a club for type constructors, not for types. `impl Monad[Box]:` has no `for`.
5. Calls with no receiver go through the parameter: `F.pure(x)`.
6. Partly applied constructors: `Result[_, E]` fixes `E`. Type lambdas fix any argument.
7. "Names you may know": higher-kinded types (Scala, Haskell), constructor classes (Haskell).
8. Limits: see below.

## Limits to state honestly (found by testing)

- Partly applied constructors against `M[_]` are not compared by the checker (already Spec 24a).
- **Polymorphic recursion** (a function that calls itself at a different constructor each time, like `nest` with `Pair`): the interpreter accepts and runs it, because it does not specialize. A compiler that specializes per use would never finish. DECIDED (Steve): reject. Done in check.py (`check_poly_rec`), explicit type arguments only; inferred or mutual recursion is not caught. Spec type-constructor bullet updated.
- **Ownership:** not tested. I did not check whether `map` over a container holding resources obeys move/ownership rules in `F[_]` code. The docs should not claim it until a test shows it.
- `Option`'s constructor name is not `Some` in the prelude; check the actual name before using Option in examples.
