# Formatting and checking: `moxie fmt` and `moxie check`

Two commands do most of the work of keeping a project in good shape. `moxie fmt` rewrites files into one layout. `moxie check` reads the whole program and reports mistakes without running anything. This lesson says what each does, and exactly what `check` can and can't prove.

## `moxie fmt`

`moxie fmt FILE-or-DIR...` rewrites files into one layout, and it has no layout options. It fixes the shape of the file:

- every block is indented two spaces per level, and a continuation line keeps its offset from the statement it continues;
- multi-line strings, SQL bodies, and block comments move together with their text unchanged;
- trailing spaces go; blank lines are limited to two at the top level and one inside a block; the file ends with a single newline;
- a comment takes the level of the code it belongs to;
- inside a line it puts one space around `=`, `==`, `~=`, `<=`, `>=`, `->`, `|>`, and the arithmetic operators, none before a comma and one after;
- it adds a blank line before a top-level `fn`, `type`, `impl`, or `test` that follows a block;
- a line longer than 80 columns is broken at its outermost bracket group, one item to a line, with the closing bracket on a line of its own (nothing is added or removed, so no trailing comma appears); a line with a comment on it is left alone. The width is not an option.

```
$ moxie fmt --check src
would change src/parse.mxi
$ moxie fmt src
formatted src/parse.mxi
```

`--check` changes nothing and exits 1 when a file would change, so it fits a build script. `--stdout` prints the result instead of writing.

### It checks itself

Before a file is written, the formatter checks that the tokens match the original, that every comment is kept with its text unchanged and in order, that the spacing changes left the parsed program the same (otherwise only the layout rules are applied), and that a second run changes nothing. If a check fails it reports the file and leaves it alone. A file with a tab in its indentation or an unterminated string is reported and not touched.

Mistakes: expecting it to join or split lines (it never does, so a long argument list stays as written), or to rewrap long lines (the line width is not settled).

## `moxie check`

`moxie check FILE` reads the whole program and reports mistakes without running anything, and `moxie run` stops on the same errors before the first line executes:

```moxie
x Int = 1 + "a"
println(x)
```
```error
error: cannot apply `+` to `Int` and `String`
```

It follows one rule: it reports only what it can *prove*, so a value whose type it can't work out is never an error.

### What it proves

- **Types.** Every call, operator, index, slice, range, `if` and `when` arm, `?`, return, and annotation agrees with the declared types, including through lambdas, pipes, generic functions, and the prelude. A bare `x(i)` on something that isn't a function, a `Result` used as a number, and a `Stream` interpolated into text are errors.
- **Names and shapes.** Undefined names, unknown types and enum cases, wrong argument counts, missing or extra fields in a constructor, duplicate fields and cases, a `when` that misses a case, a function clause that can never be reached, a pattern that can't match the value's type, and a destructuring of the wrong arity.
- **What a type can do.** `==` and `~=` on a declared tuple or enum need `deriving eq` (or an `impl Equatable`), and `<`, `>`, `<=`, `>=` need `deriving ord`. `sort`, `max`, and `min` need `ord`; `contains` and `distinct` need `eq`; a declared tuple or enum used as a `Dict` key or `Set` element needs `deriving eq, hash`. Printing or interpolating one needs `deriving show`. Nothing is compared or printed by accident.
- **Errors as values.** `?` needs a `Result` operand in a function that returns a `Result` with the same error (or a `From` impl that converts it), so it's an error in a function that returns `Unit` and inside a `daemon` body.
- **Ownership.** Use after move, `ref` and `move` mismatches, and a resource that outlives what it may.
- **Sizes and numbers.** Array and MultiArray shapes, a constant index past the end of an array or of a list whose length the text gives, a negative constant index, a literal that doesn't fit a bounded integer, and division by a constant zero.
- **Shadowing.** A name bound with `=` in a deeper block is a new name that hides the outer one, and the compiler warns. When the line also reads that name (`total += i`), it's an error that points to `total@1`.
- **Effects and permissions.** What a function prints, parks on, or reaches, checked against its declaration and the manifest's grants, through calls and imported packages.

Here is one of the *what a type can do* checks:

```moxie
tuple P
  x Int

println(P(x: 1) == P(x: 1))
```
```error
error: `==` on `P` needs `eq`: write `deriving eq` on its declaration (or an `impl Equatable`)
```

### What it leaves alone

Anything that depends on a value at run time (a `Dict` key that is present, an index only known when the program runs); a function used as a value is checked by its types but not by its arity; a `break` outside a loop; a shift of a value whose width the text doesn't state; and a type name of one or two letters or all capitals is taken to be a type parameter. Those are caught when the code runs, with the same message the checker would have given.

## What to remember

- `moxie fmt` has one layout and no options; `--check` is for build scripts.
- `moxie check` proves types, names, capabilities, ownership, sizes, effects, and permissions before anything runs.
- It reports only what it can prove; what depends on run-time values is caught when the code runs.
