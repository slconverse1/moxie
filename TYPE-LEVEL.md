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

## Why it is hard: what I found in the code (2026-11-05)

I tried it instead of assuming it. Three checks, each a program that should be rejected:

```
b: Box[Int] = Box(v: "not an int")          # a Box of Int holding a String
x: Array[Int][3] = Array(1, 2)              # a size-3 array with two items
y: Int = first(Array("a", "b", "c"))        # first[T](xs: Array[T][3]) T, a String into an Int
```

`moxie check` says `ok` for all three, and they run. The checker (`check.py`, about 2,000 lines) has a type language of scalars, bounded integers, `Secret`, and non-generic named types. For any generic type (`Box[Int]`, `Array[T][N]`, `List[T]`, `Result[A, E]`, a function type) `ty_of_type` returns "unknown", and unknown matches everything. So:

1. **Nothing to match on.** A type-level `when` matches on the shape of a type. The checker has no value for the type of `Array("a", "b", "c")`, so every call site that infers its types is stuck.
2. **Prelude functions have no signatures.** There are 258 built-in functions and stream stages (`map`, `filter`, `reduce`, `flat_map`, `collect`, ...), written in Python with no declared types. An expression that passes through one has an unknown type.
3. **Generic bodies are checked once, abstractly.** Inside `fn f[T](x: T) Elem[T]`, `T` is a parameter, not a type, so `Elem[T]` cannot reduce. It would have to stay symbolic, or the checker would have to check each instantiation separately (which is what specialization does at code generation, not in the checker).
4. **Types are erased at run time.** The interpreter binds a type parameter from a value's type name (`TypeV`), and keeps arguments only where I added them for `M.pure`. It cannot recover `Array[X][N]` from a value.

The part that is easy: matching a written-out type against patterns. A 20-line experiment gets `Elem[Array[Int][3]] = Int`, `Elem[List[String]] = String`, and `Elem[(Bool, Int)] = Bool`, and returns "stuck" for `Box[Int]` (no arm) and for the abstract `T`. So explicit uses work today and inferred and generic uses do not.

**What building the missing piece takes**, in order, each step useful on its own:

1. A real type representation in the checker: applications (`Box[Int]`), function types, tuples, sizes, unions, type parameters. About the size of the existing `ty_of_type` and `compat`, redone. It fixes the three bugs above by itself.
2. Unification with inference at calls, so `first(Array("a", "b", "c"))` has the type `String`.
3. Signatures for the 258 prelude functions (a table; the Spec already states most of them), or a rule that an untyped function gives an unknown result and keeps the check gradual.
4. Checking a generic body per instantiation, or keeping reductions symbolic inside it. Per instantiation is simpler and matches how moxie specializes.
5. Only then match types, and only then recursion.

The first three are overdue whatever happens to type-level programming: they are what makes moxie's "compile-time type-safe" claim true for generic types, and they are why `Box[Int]` holding a `String` slips through today.

## What it would cost here

- **The reference interpreter cannot host it yet** (see the findings above). Matching on a type needs a real type representation and a unifier, which is the missing piece, not match syntax. Lambdas needed none of that because they are pure substitution.
- **One-pass compilation.** A type function that names itself, or a function whose signature uses one defined later, needs forward references. Aliases are in file order today.
- **Error messages.** A failure deep in a reduction must be reported at the use site with the reduction trace. Without that, type-level code is unusable.
- **Compile time.** Specialization already copies a function per distinct set of types; a type function that builds large types multiplies that.
- **It contradicts a stated decision.** The Spec says there is no operation that splits or joins tuple types, so a wrapper can pass an argument list along but cannot change it. Match types plus recursion are exactly that operation.

## What would justify it

Nothing in the current libraries needs it. `fp.trans` works with lambdas and classes. Where a Haskell program would use a type family (`MonadState`'s state type) moxie writes a second class parameter. Candidates that might: `Flatten` for nested tuples, schema types computed from a SQL string, and matrix-shape checking. Each of those can be a library or a built-in check without opening the type language.

## Recommendation

1. Keep type lambdas as built.
2. Do not add recursion. If a real use appears, add type-level `when` without recursion first; it is useful alone (`Elem`, `Unwrap`) and always terminates.
3. Build the checker's real type representation and unifier before any matching on types (steps 1 to 4 above), since the Spec's compile-time promises need it anyway.
4. Revisit recursion only with a concrete program that cannot be written without it, and then with structural decrease.

## Open questions for the designer

- Is "types are substitution only" a property worth keeping as a headline, like "no subtyping"?
- If match types are added, should size arithmetic (`N - 1`) fold into them or stay a separate sublanguage?
- Should tuple joining stay forbidden even with match types, so variadic generics remain out?

## Status (2026-11-05): step 1 done

The checker now has a real type representation for applications, sizes, tuples, and parameters (`moxie/tys.py`), which fixes the three known false negatives. Still open from the plan: unifying function types and inferring lambda arguments, signatures for the prelude builtins (they are unknown today), checking a generic body per instantiation, and anything at the type level that matches or recurses.

Step 2 (2026-11-05): calls infer. Unification with constructor parameters (`F[A]`), lambda parameters typed from the callee's signature, and a lambda's result fixing a type parameter are in, all in a single pass. Not yet: signatures for the prelude builtins, generic bodies checked per instantiation, and lambdas whose body is more than one expression.
