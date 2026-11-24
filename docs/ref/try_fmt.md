---
layout: default
toc: true
terms: true
title: "try_fmt · moxie function"
---

# `try_fmt`

<p class="specref"><a href="../reference.html#fn-try_fmt">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn try_fmt(template String, args...) Result[String, Error]
```

## Description {#description}

Like `fmt`, but a template that doesn't match its arguments is a `Result`, not an abort. Use it when the template comes from a file or a user.

**Parameters**

- `template`: the text with `{}` holes.
- `args`: the values to put in.

**Returns** `Ok(text)`, or `Err` with code `BAD_FORMAT` if the number of holes and arguments differ.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> try_fmt("{}-{}", 1, 2)
Ok("1-2")
```

```
> try_fmt(trim("{}-{} "), 1)
Err(Error(code: 13, message: "the template has more fields than arguments"))
```

