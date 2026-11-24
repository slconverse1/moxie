---
layout: default
toc: true
terms: true
title: "fmt · moxie function"
---

# `fmt`

<p class="specref"><a href="../reference.html#fn-fmt">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn fmt(template String, args...) String
```

## Description {#description}

Builds a `String` from a template, with each `{}` replaced by the next argument shown as text. A `{}` with no argument left, or an argument with no `{}`, aborts: the compiler reports it when the template is a literal. Use `try_fmt` for a template that comes from outside. Write `{{` and `}}` for literal braces.

**Parameters**

- `template`: the text with `{}` holes.
- `args`: the values to put in.

**Returns** a `String`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> fmt("{} + {} = {}", 1, 2, 3)
"1 + 2 = 3"
```

```
> fmt("name: {}", "Ada")
"name: Ada"
```

```
> fmt("{{}}")
"{}"
```

