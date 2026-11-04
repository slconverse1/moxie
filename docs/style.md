---
layout: default
title: "Moxie Style Guide"
---
# MOXIE STYLE GUIDE

This page is advice on writing moxie that reads well. It covers both dialects, moxie and moxie/gc, because the style rules are the same; where one dialect differs, the text says so. Two kinds of rule appear here. **Enforced** rules are layout, and `moxie fmt` applies them for you. **Advice** is everything else: the compiler accepts the other choice, and this page says which one to prefer and why.

## Layout (enforced by `moxie fmt`)

Run `moxie fmt` and stop thinking about layout. It has no options, so every moxie file looks the same.

- Two spaces per level, no tabs, no trailing spaces.
- Lines break at 80 columns. A long call or list gets one item per line, two spaces deeper, with the closing bracket back at the original level.
- One space around operators and after a comma, none before a comma.
- A lambda's colon touches the closing parenthesis and has one space after it: `(x): x + 1`.
- An inline fiber has a space after `fn`: `run fn (tx)(out): ...`.
- A blank line before each top-level declaration, and no more than two in a row.

## Names

- Functions, variables, and fields are `lower_snake_case`. Types and enum cases start with a capital letter.
- Name a function for what it returns when it is pure (`total`, `letter`), and for what it does when it has an effect (`print_report`, `save_roster`).

## Functions

- Give every function a return type, and write `Unit` for one that returns nothing. The compiler requires it, and the signature then reads as a sentence.
- Write the types of the parameters. They are the documentation that the body can't give.
- Keep a function short enough to read without scrolling. When a block grows a second job, give the second job a name.
- Use the one-line form when the body is one expression: `fn double(x: Int) Int: x * 2`.
- Update with `+=`, `-=`, and `++` rather than `x = x + 1`. A rebinding inside a loop does not leave the loop, so accumulate with a stream terminal such as `reduce` or `sum`, or break out with a value.

## Lambdas

A lambda is a function with no name, written `(params): body`. It is meant to be small, and it is pure.

- **Keep it to one expression, or a few lines.** Past that, declare a function with `fn` and give it a name. A name is documentation.
- **Anything with an effect is a named function.** A lambda can't print, park, or touch a channel, a file, a socket, or SQL. `with_stdin(text, read_total)` and `transaction(conn, move_funds(_, from_id, to_id, amount))` take named functions, and a partial call fills in the rest.
- **Use `_` for the shortest cases.** `xs |> map(_ * 2)` is clearer than `xs |> map((x): x * 2)`. Once the body needs the value twice, or a name would help, write the lambda.
- **Use a partial call instead of a lambda that only forwards.** `log("ERROR", _)` beats `(m): log("ERROR", m)`.
- **Put the lambda after the call when it is the last argument and the body is longer than a few words:**

  ```
  total = scores
    |> to_stream()
    |> filter()(s): s >= 60
    |> sum()
  ```

  Inside the argument list, a short lambda reads fine: `filter((s): s >= 60)`.
- **Spread a pair instead of destructuring it.** `zip(xs, ys) |> map((x, y): x * y)` needs one pair of parentheses. A tuple pattern, `((x, y)): ...`, is legal, but it stacks parentheses, and a nested one such as `(((x, y), z)): ...` is hard to read. Past one level of nesting, bind a named lambda with one parameter and take the tuple apart in its body: `sum3: (((Int, Int), Int)) -> Int = (p):`, then `((a, b), c) = p` on the next line. The name documents it, and no parentheses stack.
- **Bind a lambda with a typed name:** `add: (Int, Int) -> Int = (a, b): a + b`. The type on the name gives the lambda its types, so the lambda writes none. If it needs to call itself or be generic, it is a function, so use `fn`.
- **Parenthesize a lambda at the top level of a condition.** A header's colon belongs to the header, so write `if any(xs, (x): x > 2):`, with the lambda inside the call.

## Pipelines

- One stage per line once a pipeline passes about two stages, each line starting with `|>`.
- Name the stage when it has a meaning of its own: `filter(is_pass)` reads better than a lambda that spells out `s >= 60`, if `is_pass` is used more than once or the rule deserves a name.
- A same-line lambda body runs to the end of the line, so a `|>` after it joins the body. Put each stage on its own line, as above.

## Errors

- Handle a `Result` with `?` when the caller can't do anything useful, and with `when` when it can.
- Discard a result on purpose with `_ =`, so the next reader knows it was deliberate.
- Use assertions and aborts for bugs, never for expected failures such as a missing file or bad input.

## Fibers and channels

- A fiber that does real work is a named function, declared with `fn` (with `fiber[n]` when its count needs a limit). Start it with `run name(args)`.
- Keep an inline `run fn (...)` to a few lines. It is for glue, such as handing a value to a channel.
- Declare each channel's size on purpose. The size is how many values may wait, and so how far a producer can run ahead of its consumer.

## Memory

- **moxie** has fixed capacities. Write the size where the program needs one (`List[Int][100]`), and let a declaration's own value give it where it can. Read the pool report that `moxie pools` prints before you raise a limit.
- **moxie/gc** has no sizes to write. It does have `[memory] heap` in the manifest, and a program that matters should set it, so a runaway program fails with a message and not with a slow machine.

## Comments and documentation

- Comment why, not what. A comment that repeats the code goes stale.
- Put a `///` comment on every exported function. Its examples are checked, so they can't drift from the code.
- Start a file with `//!` that says what the file is for.
