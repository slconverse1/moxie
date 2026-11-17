# moxie

Moxie is a language-design exercise: (mostly) compile-time type-safe, immutable, practical functional programming, Go-style channels and fibers, and, in the plain dialect, no garbage collector and no heap. A second dialect, moxie/gc, adds a collector; the two are kept apart because they make different promises. This repository holds the language documents and a reference interpreter written in plain Python 3.

- **Site:** https://slconverse1.github.io/moxie/ (the Site Intro, Tutorial, Mixer's Guide, Spec, and an in-browser "Try moxie" page)
- **`docs/`** the documents, as the site's source: `index.md` (Site Intro), `tutorial.md`, `guide.md`, `spec.md`, and `gc/` for moxie/gc, the garbage-collected dialect (its Site Intro, Spec, and Guide)
- **`moxie/`** the reference interpreter (standard library only)
- **`examples/`**, **`tests/`**, **`INTERPRETER.md`**, **`FIXLIST.md`** the interpreter's samples, tests, notes, and a list of problems found in the Spec and Guide

## Run a program

    git clone https://github.com/slconverse1/moxie
    cd moxie
    python3 -m moxie run examples/gradebook.mxi
    python3 -m moxie test examples/gradebook.mxi

The interpreter needs Python 3.11 or later (tested on 3.11, 3.12, and 3.13) and nothing else. `INTERPRETER.md` lists what it checks and what it doesn't yet.

## Changes

Newest first.

### 2026-11-16 (data types a la carte)

- **`Has[X]` bounds** (Spec 6, Guide 24n): smart constructors that build in any union that lists the node (`lit[U Has[Lit]](n Int) U`), checked at bindings, result types and explicit type arguments, free at run time. Programs with effects use the freer monad (a GADT of commands plus an existential `Bind`, no `Functor`), the recent simplification of the original encoding, which still runs too. `tests/run_alacarte.py`.

### 2026-11-16 (GADTs completed)

- GADTs are complete: `when self` in methods and `if v is Case(...)` refine type parameters; cases declare their own variables with bounds (`Shown[A Show](v A) Item[String]`); header enums may state result types (`Low(rank: 1) Level[Cold]`, `Num(line: 1)(n Int) Value[Int]`). Guide 24o, Spec 6, tests/run_gadt.py.

### 2026-11-16 (session types)
- **Session types** (`import session`, Spec 23e, Guide 17a): a pair of channel ends whose type is the conversation. `Send`, `Recv`, `Pick`/`Offer` (choices), `End`, recursive aliases for loops, delegation (an endpoint sent over another session), `Peer[S]` for the other end, `connect[S]()`. The checker rejects steps in the wrong order or with the wrong type, a used-up endpoint, a conversation dropped before `End` or never `finish`ed, and the wrong end handed to a function. Built on ordinary channels with the types erased; a program that does not import `session` pays nothing. tests/run_session.py.
- **Checker (found while building it)**: nested generic types are compared (`Endpoint[End]` where `Endpoint[Send[T, S]]` is wanted); a type parameter given two types by two arguments is an error; `f[A](...)` with explicit type arguments has a typed result; a call with `move` arguments still gets its generic result type.

### 2026-11-16 (operator sections)
- **Placeholders and operator sections are typed**: `_`, `_2` and the missing side of `(+ 1)`, `(> "x")`, `(and true)` take the type of the lambda parameter they stand for, so `xs.map((+ 1))` on Strings is an error. tests/run_sections.py.

### 2026-11-16 (lambda and `is` fixes)
- **Untyped lambdas in GADT calls** take their parameter types from the case's field once the other payloads bind its variables (`Packed(Num(1), (b) -> if b ...)` is an error: `b` is an `Int`). tests/run_gadt.py.
- **`is` tests**: generic tuples (`b is Box(x)` on a `Box[Int]` is always true) and tuple patterns with refutable parts (`c is Dog("rex")` on a `Cat` is always false) are judged; a refutable part on the right type is left alone. tests/run_isjudge.py.

### 2026-11-16 (existential GADT cases)
- **Case type variables**: a GADT case may use one-letter type variables of its own. A call infers them from the payloads (`Pair(Num(1), Flag(true))` is a `Value[(Int, Bool)]`), and a `when` arm sees one that the result type does not fix as a fresh rigid type (`A'`), so existentials (`Packed(v Value[A], f (A) -> String) Value[String]`) are checked. Guide 24o, Spec 6, tests/run_gadt.py.

### 2026-11-16 (fix-list pass 2)
- **Nested exhaustiveness**: `when` coverage looks inside nested patterns, tuples, `Bool` and literals (`Some(Circle(r))` without `Some(Tri(_))`); a guarded arm covers nothing; anything not understood ends the check silently (tests/run_nestedcover.py).
- **Refined aliases across packages**: an exported alias whose condition uses only `self` and literals is refined in the importer as `lib.Pos` or `Pos` (tests/run_refinedpkg.py).

### 2026-11-16 (typestate)
- **Guide 24p: typestate.** A phantom type parameter (`File[Open]`, `File[Closed]`) already gives compile-time protocols with no new compiler code; tests/run_typestate.py.

### 2026-11-16 (GADTs)
- **GADTs**: an enum case may state its own result type (`Num(n Int) Value[Int]`). A constructor call has that type, so `Add(Num(1), Flag(true))` is a compile error; a `when` arm learns the type parameter (`T` is `Int` in the `Num` arm); cases the scrutinee's type rules out need no arm, and an arm for one is an error. Types are erased at run time. Spec 6 (Enums), Guide 24o (with the tagless-final and open-data-type comparison), tests/run_gadt.py. 

### 2026-11-16 (extras)
- **Fix-list pass**: `R.f(...)` results compared, `impl` parameters checked against the interface, a warning for an `impl` on a union, and a compile error for a call that omits a type argument its body needs. FIXLIST.md now starts with a grouped list of open items.
- **`update` lines are type-checked**: an unknown field or a value of the wrong type is a compile error, `&` has the field's type, and nested blocks are checked.
- **More compile-time checks** (tests/run_safer.py, tests/run_unionimpl.py): a function's result is compared when it is arithmetic or a local; an `impl` must write every member of its interface (without a default body) and agree on a plain result type; an `if` with no `else` can't end a function that returns a value; `Int | ()` (inline, named, or a field) can't be used in arithmetic until tested; and `Mul(Lit(3), Add(...))` takes its child type from the union that lists `Mul[Union]`.
- **Guide 24n: data types that grow.** The expression problem for inspectable data: generic nodes, one interface per operation, a `type union` per language, dispatch by method call on the union value, rewrites through small projection interfaces. The checker now reports a union member that lacks the method or bound a call needs (tests/run_unionimpl.py).
- **The checker types `R.f(...)` on a bounded type parameter**: a static member of the bound interface is checked like a call, with `Self` (or the constructor parameter, `R[Int]`) replaced by `R`, so a tagless-final program that mixes `R[Int]` and `R[Bool]` is a compile error (tests/run_tparamstatic.py).
- **Guide 24m: tagless final** (one program, many interpreters): an interface of `static fn`s, a generic program `[R Expr]`, interpreters as types, a second interface to add operations, `Both[A, B]` to run two at once, a typed form over `R[_]`, and the way back to a data type. Also fixed: a generic function that passes its own type parameter on (`h2[R](n)`) lost it (tests/run_targforward.py).
- **Generic `deriving dyn`**: `tuple Pair[A, B] deriving dyn` and `enum Tree[T] deriving dyn` work, with type parameters read through the new `json.Dynable` interface (`Pair[Int, String].from_dyn(d)`). Inside a generic impl, `Tree[T]` now names the type `T` is bound to.
- **`proxy` for interfaces from imported packages**: `impl shapes.Shape for W proxy(inner)`, or by name after `import shapes (Shape)`.
- **Refined elements.** `List[Pos]`, `Array[Pos]`, `Set[Pos]` and `Dict[K, Pos]` in a parameter, result, field or binding are now checked when the program runs, as `all((item) -> item > 0, xs)` (tests/run_refinedelems.py).
- **`moxie doc` lists marked functions** (effects, `unsafe` and the like) in a "Marked functions" section and on `**Marked:**` lines (tests/run_docmarks.py).

**2026-11-15: `with` capture layouts are checked everywhere.** A parameter, a result (the closure the body returns, inline or held in a local), a channel element, a tuple field and a collection each hold only closures of the layout written. A function name or a lambda that captures nothing has the empty layout, so it is refused where `with (Int)` is written, and a closure that captures values is refused in a slot written without `with`, whether it is written there or held in a variable. Mismatch messages say which side captures what.

**2026-11-15: `update` lines take commas and `&`; `do` has no `->`.** In `x.update`, a comma ends each line except the last, as in a constructor call (a trailing comma is allowed, and a missing one is a compile error). `&` in a right-hand side is the field's current value, so `retries: & * 2` doubles it without repeating the name; a `&` that is the slot of a pipe stage keeps its pipe meaning. The one-line `x.do -> expr` is gone: `x.do` takes its block on the lines below, since `->` belongs to lambdas, Dict entries and arms. A line that ends in a comma and is followed by a dedent now dedents instead of joining the next statement. Spec 9b and the Guide (8a) updated.

**2026-11-15: closures of one capture layout can be stored (moxie).** A written function type may end in `with (T1, T2)`, the types its closures capture (`(Int) -> Int with (Int)`; the order doesn't matter). Slots written that way (tuple fields, collection elements, bindings, parameters) hold closures with exactly that layout. In a literal with no written type, the first capturing closure sets the layout and the rest must match (a closure that captures a different kind of value is an error), and so does an update like `t("y") = ...`. A type written without `with` still takes plain functions only. Spec 11, the Guide and the intro updated.

**2026-11-15: constants are not captures.** A name bound once, to a value the compiler can work out, is a constant, so a lambda that uses only constants, parameters, and its own locals captures nothing and counts as a plain function (it can be stored in a Dict, List, tuple field or channel in plain moxie). This now holds for locals inside a function, not just module-level names. A name bound more than once, including an entry-file name that is later rebound, is a variable and is a capture. Spec 11 and the Guide updated.

**2026-11-15: anonymous `fn`s have no `->`.** Only a lambda uses `->` in its declaration. An anonymous `fn` is written like a named function with the name left out, `fn (params) Ret`, with the body indented below, and an inline fiber is `run fn (args)(params)` with an indented body (or the short form `run fn (tx)` when each parameter has its argument's name). The old `fn (...) -> body` form is a compile error that points to the new one. Because a block can't sit inside a call's parentheses, an anonymous `fn` is bound on its own line and passed by name. The effects checker now follows a bound anonymous `fn`: calling it, or passing it to a function that calls it, carries its effects (a pure function that calls one that parks is now caught). Tests, Spec, Guides, intros and tutorials updated.

**2026-11-15: capturing closures in collection literals.** A capturing closure written inside a `Dict(...)`, `List(...)`, `Set(...)` or `Array(...)` literal is now the same compile error as in an annotated slot (moxie only; moxie/gc stores it). It used to slip through. Module-level names aren't captures.

**2026-11-15: several Dict entries at once, and tuple keys in literals.** `Dict(...ages, {alice, bob, dave} -> (31, 26, 7))`: braces mark a list of keys, and a tuple of values pairs with them by position, so a count mismatch is a compile error. A tuple on the left of a plain `->` is one key, so `Dict((0, 0) -> "start")` works; before this a tuple-keyed literal silently produced an empty Dict.

**2026-11-15: a Dict spreads into a Dict literal.** `Dict(...ages, alice -> 31, dave -> 7)` copies the old entries first, in order, then applies the new ones: a key already there is replaced in place, a new key goes at the end. Before this, `Dict(...d)` silently dropped the entries of `d`. Also fixed today: a `wait` block (and a `select` with no `default`) crashed the Try page's permission check with `KeyError: 'parks'`.

**2026-11-15: `scope` is now `wait`.** The structured-concurrency block that waits for every fiber started inside it (and can bind a `Cancel` token) is written `wait`, or `wait token`; "scope" now means only the layers of bindings that `name@N` counts. The old spelling `scope` is an error that points to `wait`, and `wait` stays a legal name anywhere that is not a statement-start block.

**2026-11-15: the `in` line.** The first line of a block can be `in total, count`: each becomes a local that starts as the outer value, so `total += x` in a loop body no longer needs `@1` and no longer trips the shadowing error. `in total@2` and `in total@serve` pick a layer or a labeled loop. In a loop the copy happens once; later passes carry the value. The local ends with the block: leave with `break(total)` or `else total`, or write `total@1 = ...`.

**2026-11-15: `name@label`.** A label names the scope that `name@N` would count: `total@serve += x` inside `#serve for ...` writes the `total` bound outside that loop, however many blocks lie between. Works for any labeled loop or `do`; an unknown label is an error. A label starts with a lowercase letter, so `p@Product(...)` stays an as-pattern.

**2026-11-15: `moxie run` prints warnings.** The compiler's warnings (a shadowed name, a dropped `Result`, and the rest) used to appear only under `moxie check`. `run` now prints them on stderr before the program starts, in the same `file:line: warning:` form, and they never change the exit code. `--quiet` and `--release` leave them out. The Try page shows them above the program's output.

**2026-11-15: no more `total = total + x` that quietly does nothing.** In an inner block (a `for` body, an `if`, a `when` arm), a line that defines a name and also reads the same name from outside (`total += x`, `total = total + x`) is now a compile error, since the new `total` would vanish at the end of the block and the outer one would never change. The message says to write `total@1 += x`, or fold with `reduce`. A plain shadowing line like `x = 5` still only warns. Loops may still carry state on purpose: a name their `while` condition reads, one their `break(value)` or `else` hands out, and the state of a `daemon`. A name carried only for the condition and then read after the loop is an error too. Tests in `tests/run_shadow.py` and `tests/run_gimme.py`.

**2026-11-15: `name@N` replaces `gimme.N.name`.** `total@1` is the nearest enclosing block's `total`, to read or to write (`total@1 += x`), and `n@2` is the next one out. The old spelling is now an error that shows the new one, `gimme` is no longer a soft keyword (30 left), and the Spec, Guide and tests use the new form. At the start of a statement, `name@<number>` is this reference, not an as-pattern with a number; `p@Product(...)` is unchanged. Tests in `tests/run_gimme.py`.

**2026-11-14: chained casts.** `[A : B : C](x)` casts to `C` first, then `B`, then `A` (`[Char : Int](65)` is `'A'`). Each step can abort, and a constant that does not fit a step is a compile error. Only in the bracket sugar; `cast[...]` takes one type, and a file may not mix `cast[T](x)` with `[T](x)` (a compile error naming the other line). Tests in `tests/run_castsugar.py`.

**2026-11-14: `[T](x)` for `cast[T](x)`.** A type in brackets followed by an argument in parentheses is sugar for `cast`, with the same abort and the same compile error for a constant that cannot fit. The docs keep spelling out `cast`; `try_cast` and `wrap_to` have no short form. Test: `tests/run_castsugar.py`.

**2026-11-14: refined aliases.** `type alias Pos = Int where self > 0` names a condition. A parameter declared with it (`fn half(n Pos) Int`) is a parameter with that `where`, so each call proves it, and a `Pos` parameter in the caller counts as a fact. Only parameters are checked, since the alias is still an `Int`. Spec 9c, Guide 9c, tests in `tests/run_refined.py`.

**2026-11-14: refined parameters.** A parameter may end with `where cond` (`fn get(xs List[Int], i Int where i >= 0 and i < len(xs)) Int`), and every call must prove the condition. A small built-in solver (integer linear arithmetic, exact) reads the facts the code gives it: the caller's own `where`, `if`/`elif`/`else` tests, early returns, `for i in 0..len(xs)`, names bound to a sum or difference, constants, and bounded integer types. Proved compiles, refuted and unknown are errors that name the condition. The condition is also kept as a `requires`, so a call through a function value is still checked at run time. Spec 9c, Guide chapter 9c, `tests/run_refined.py`. Not yet: refined type aliases, results, and tuple fields.

**2026-11-14: operator sections.** `(+ 1)`, `(10 -)`, `(* 2)`, `(> 2)` and ``(`f` 2)`` are one-parameter functions, the same as the placeholder forms. Subtraction follows whitespace inside the parentheses: `(-4)` is the number and `(- 4)` is the section, so there is no `subtract`. Test: `tests/run_sections.py`. The Spec and both intros no longer say that moxie has no sections.

**2026-11-14: `impl` members can leave out their types.** `fn info(self, msg)` is enough when the interface already says `msg String` and `Unit`; the compiler copies the types. The parameter names must be the interface's (Steve's rule, so a labeled call means the same on the type and through the interface), and a different name is an error. A label that names no parameter of a method is now a compile error, not a run-time abort. Covers your own interfaces and the built-in `Show`, `Read`, `Equatable`, `Ordered`, `Addable` and `Numeric`. Written types are still allowed and checked. Ordinary functions still need theirs. Test: `tests/run_implsig.py`.

**2026-11-14: "Modularity without classes" in both intros, and a `proxy` fix.** A new section before "Moxie's Superpowers" takes Odersky's point that OOP's main gift is modularity and shows the pieces moxie uses for it: interfaces and `impl`s as the boundary, `any` for mixed collections, closures and tuple fields for hidden state, and `proxy` for reuse (the gc intro adds the record-of-closures style, which the no-GC dialect refuses because the captured values would have no owner). Writing the examples found a bug: `proxy` passed an interface member's explicit `self` along as an argument, so forwarding `fn error(self, msg String)` failed at run time. Fixed, with a test.

**2026-11-14: tuples with unnamed fields work.** `tuple Pair(Int, String)` and the block form with one type per line (as the Spec always said) now check and run: construction by position, `p.0`, destructuring, `deriving`, generics, conversion from an anonymous tuple, and an arity error. Mixing named and unnamed fields is an error. `tests/run_postuple.py`.

**2026-11-14: one-line tuples.** `tuple Point(x Int, y Int)` declares the same tuple as the indented block, with `deriving` and defaults as before. A body below it may hold `invariant` lines, not more fields. `tests/run_tuplehead.py`.

**2026-11-14: one code for "not there".** `get(xs, i)` on a List or Array and `Enum.from_index(n)` now give `MISSING` (4), as a Dict key, `first` of nothing and `value_of` already did; they used to give `OUT_OF_RANGE` (6). The rule is in Spec section 6 (the `Error` entry): `MISSING` is an element, key or case the program's own data lacks, `NOT_FOUND` is a thing outside it (file, host, zone), `OUT_OF_RANGE` is a number outside its allowed range. A program that matched `OUT_OF_RANGE` on a failed `get` of a List needs `MISSING`. `tests/run_notfound.py`.

**2026-11-14: constant indexes into Lists.** `xs = List(1, 2, 3)` then `xs(3)` is a compile error (as it already was for an Array), and so is a negative constant index into any List or Array. A List counts only when its name is bound once and never changed through `ref`, a `ref` method or `+=`, so the length is the text's. `xs(i)` stays the element itself and aborts on a bad index; `get(xs, i)` is the version that returns a `Result`. `tests/run_indexcheck.py`.

**2026-11-14: let-else can see the failure.** `Ok(n) = read[Int](t) else Err(e) -> Err(wrap(e))`: the else takes a pattern of its own, so the `Err`'s code and message are in scope (to log, to convert). The two patterns must cover every case together, as in `when`, and the old `else value` form is unchanged. Guide chapter 12, Spec section 1, `tests/run_letelse.py`.

**2026-11-14: `dynamic fn`, `unsafe fn`, `deriving dyn`.** Reading a `Dyn` (`field`, `at`, `as_*`, `from_dyn`) now has to happen in a function marked `dynamic fn`, and calling a foreign function marked `unsafe` (or taking a `Ptr[T]`) in one marked `unsafe fn`; unmarked use is a compile error, top-level script code is exempt, and `dynamic`/`unsafe` stay usable as variable names. Only the function that does the thing is marked, so a checking wrapper can be called from anywhere; `safety = "strict"` under `[program]` in `Moxie.toml` makes callers carry the mark too. `deriving dyn` on a tuple writes `to_dyn()` and a checked `Tuple.from_dyn(d)` (a `Result`, naming the missing key or wrong kind) at compile time from the field types: `Int`, `Float`, `Bool`, `String`, `List` of those, and nested tuples that derive it. Guide chapter on JSON, Spec 23c/23d, `tests/run_safety.py`.

**2026-11-14: `proxy`.** `impl Printer for Logger proxy(printer)` hands a whole interface to a field: the methods the block doesn't write forward to the field, so only the ones that differ are written (Kotlin's class delegation). Guide chapter 9a. Plain methods of an interface declared in the same file only; `static`, `ref`, generic and `Self` members are errors that say to write them by hand.

**2026-11-14: Three more mistakes caught at compile time.** A pattern that can never match its value (`Some(n)` against a `Result`) is an error, in `when`, `is` and let-else. Dropping a `Result` as a statement is a warning (write `\ call()` to drop it on purpose). `cast[UInt8](300)` of a constant that does not fit is an error.

**2026-11-13: Union elements and `elif` chains.** The loop variable over a list of a union is a union (`for x in ids`, then `x + 1` is an error until tested), and so is `ids(i)`; `if ids(0) is Int` narrows that element. An `if`/`elif` chain in which some arms leave now narrows what follows, from the arms that stay.

**2026-11-13: Narrowing after an early exit, and with `not` and `or`.** `if not (v is Int) then return 0` now makes `v` an `Int` on the following lines; `break`, `continue` and the guard forms work the same, as do field paths. `not` and `or` narrow, and a test that leaves several members leaves a union of those. A branch that doesn't leave narrows nothing after it. `==` never narrows.

**2026-11-13: Union values are checked.** A value of a `type union` is one of its members, so using it as one (`v + 1`, `len(v)`) is now a compile error until `is` or a `when` says which. `if v is T` narrows the then-branch, each `elif`, the `else` when one member is left, the right side of `and`, and field paths (`p.f`). `println`, interpolation, `==` and passing the union on need no test. Before this the checker let any use of a union through.

**2026-11-13: Bare tuples.** A function can end with `a, b` (or `return a, b`) instead of `(a, b)`, matching `lo, hi = f()`.

**2026-11-13: `json` package and `Dyn`.** `import json` gives a closed `Dyn` enum with `json.parse(text)`, `d.field(key)`, `d.at(i)`, `as_int()` and friends (all `Result`), and `to_json()`. It is written in moxie, uses no reflection, and works in both dialects. Conversion to and from your own types (`deriving dyn`) and the `dynamic fn` marker are not built yet (FIXLIST).

**2026-11-13: Chained comparisons.** `0 <= x <= 100` means `0 <= x and x <= 100`. Any run of `<`, `<=`, `>`, `>=` and `==` chains (`a == b == c` means all equal); a middle operand is evaluated once and the chain stops at the first false link. `~=` does not chain (an error says to use `and`). `(a < b) == flag` now needs its parentheses.

**2026-11-13: Loop `else` is checked.** The Spec already said a `for` or `while` that uses `break(value)` needs an `else` of its own, but the checker accepted a loop without one (including one whose `else` was indented so it belonged to the `if`). It is now an error. The Guide points out that a loop's `else` lines up with the loop.

**2026-11-13: Chained bindings.** `x = y = z` binds `z` to `y` and then `y` to `x`, and the names may be lined up one per line with each `=` ending its line. The Guide gains a section on binding several names at once (section 1f), and "assignment" is now "binding" or "update" throughout.

**2026-11-13: Wrapped guards.** The condition of a trailing `if` may go on its own indented line under the action, for a condition too long for the line: `action` then `  if cond` means `action if cond`. A guard may also end with `else value`: if the condition fails the action is skipped and the function returns the value, like a let-else (`println("loading") if ok else fail(1, "bad")`).

**2026-11-12: Colonless syntax.** Blocks no longer start with a colon, and declarations put the type after the name (`x Int`, `fn f(x Int) Int = x * 2`). Typed bindings read the same way (`total Int = 0`). Dict entries use `key -> value`. `(:40)` is a one-item tuple, shorthand for `(0: 40)`. A bare name after a named argument is a pun for `name: name`. Colons stay in values: `User(name: "Al")`, `(x: 1, y: 2)`, `update` lines. The old syntax is on the `oldmain` branch.

## License

MIT. See `LICENSE`. It covers the interpreter and the documents.
