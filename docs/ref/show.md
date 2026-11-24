---
layout: default
toc: true
terms: true
title: "show · moxie function"
---

# `show`

<p class="specref"><a href="../reference.html#fn-show">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn show[T](x T) String
```

## Description {#description}

Turns any value into text, in the form you would write it in a program, so `show("a")` includes the quotes. `println` and `fmt` use it for you; call it when you need the text itself. A `Secret` shows as `Secret(...)`, never its contents.

**Parameters**

- `x`: any value.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> show(42)
"42"
```

```
> show("a")
"\"a\""
```

```
> show(List(1, 2))
"List(1, 2)"
```

```
> show(Some(1))
"Some(1)"
```

```
> show((1, "a"))
"(1, \"a\")"
```

