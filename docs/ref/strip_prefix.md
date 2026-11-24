---
layout: default
toc: true
terms: true
title: "strip_prefix · moxie function"
---

# `strip_prefix`

<p class="specref"><a href="../reference.html#fn-strip_prefix">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn strip_prefix(s String, prefix String) Option[String]
```

## Description {#description}

Removes a prefix from a `String`, and tells you whether there was one to remove.

**Parameters**

- `s`: the text.
- `prefix`: the prefix.

**Returns** `Some(rest)`, or `None` if the text does not begin with the prefix.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> strip_prefix("hello", "he")
Some("llo")
```

```
> strip_prefix("hello", "x")
None
```

