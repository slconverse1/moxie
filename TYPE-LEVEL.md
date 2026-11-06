# Full type-level programming for moxie: an investigation

Written 2026-11-05, after type lambdas (`[A] -> T`) were built. Question: should moxie go on to type-level matching and recursion, so a type function can look inside a type and call itself? This note says what that would take and recommends not building it yet.

## Where moxie stands

- **Done:** type lambdas (anonymous, or named by a generic alias), first and higher order, applied by substitution. A lambda can fix any argument of a type, and `[M[_], A] -> StateT[M, Int, A]` is the `T` of `MonadTrans`. They always terminate, because a lambda cannot name itself.
- **Already type-level, on a small scale:** size parameters. `Array[T][N - 1]`, `where N > 0`, and "a result size may combine sizes with `+` and `*`" are arithmetic on types, checked at each instantiation. A parameter `A` can also stand for a whole argument list (`(A) -> R` matches any arity). Moxie has chosen a decidable corner here on purpose.
- **Deliberately out:** operations that split or join tuple types (variadic generics), default type parameters, variance.

## What full type-level programming would add

1. **Type-level `when`**: a type function that matches the shape of its argument.
2. **Recursion**: a type function that calls itself on a smaller type.

Together they give tuple concatenation, `Flatten`, element-type extraction (`Elem[Array[X][N]] = X`), and checks such as "matrix `[M, N]` times `[N, P]`". They also make the type language a programming language: it can loop, it needs a termination rule, and its errors are errors in a program.

## A design that fits moxie, if it were built

```
type alias Elem[T] = when T:
  Array[X][N] -> X
  List[X] -> X
```

This reuses `when`, `->` arms, and pattern variables (`X`, `N`) bound by the match. Recursion would be a type alias that names itself, and the Spec's existing rule for recursive types (a bare name inside its own definition means the same arguments) would have to change to allow other arguments. Termination would need one of:

- **Structural decrease**: each recursive call must be on a strictly smaller piece of the matched argument. Decidable and checkable in one pass, but it rules out some useful functions.
- **A fuel limit** (for example 64 reductions per use): simple, always ends, but an error says "ran out of fuel" instead of what is wrong.

Recommendation if built: structural decrease, with the fuel limit as a backstop.

## What it would cost here

- **The reference interpreter cannot host it yet.** Types are erased at run time; the checker knows scalars, bounded integers, and named types, and checks constructor arity only. Matching on a type needs a real type representation and a unifier, which is the missing piece, not match syntax. Lambdas needed none of that because they are pure substitution.
- **One-pass compilation.** A type function that names itself, or a function whose signature uses one defined later, needs forward references. Aliases are in file order today.
- **Error messages.** A failure deep in a reduction must be reported at the use site with the reduction trace. Without that, type-level code is unusable.
- **Compile time.** Specialization already copies a function per distinct set of types; a type function that builds large types multiplies that.
- **It contradicts a stated decision.** The Spec says there is no operation that splits or joins tuple types, so a wrapper can pass an argument list along but cannot change it. Match types plus recursion are exactly that operation.

## What would justify it

Nothing in the current libraries needs it. `fp.trans` works with lambdas and classes. Where a Haskell program would use a type family (`MonadState`'s state type) moxie writes a second class parameter. Candidates that might: `Flatten` for nested tuples, schema types computed from a SQL string, and matrix-shape checking. Each of those can be a library or a built-in check without opening the type language.

## Recommendation

1. Keep type lambdas as built.
2. Do not add recursion. If a real use appears, add type-level `when` without recursion first; it is useful alone (`Elem`, `Unwrap`) and always terminates.
3. Build the checker's real type representation and unifier before any matching on types, since the Spec's compile-time promises (size checks, effect inference, specialization) need it anyway.
4. Revisit recursion only with a concrete program that cannot be written without it, and then with structural decrease.

## Open questions for the designer

- Is "types are substitution only" a property worth keeping as a headline, like "no subtyping"?
- If match types are added, should size arithmetic (`N - 1`) fold into them or stay a separate sublanguage?
- Should tuple joining stay forbidden even with match types, so variadic generics remain out?
