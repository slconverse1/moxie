---
layout: default
toc: true
terms: true
title: "strip_suffix · moxie function"
---

# `strip_suffix`

<p class="specref"><a href="../reference.html#fn-strip_suffix">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn strip_suffix(s String, suffix String) Option[String]
```

## Description {#description}

Removes a suffix from a `String`, and tells you whether there was one to remove.

**Parameters**

- `s`: the text.
- `suffix`: the suffix.

**Returns** `Some(rest)`, or `None` if the text does not end with the suffix.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> strip_suffix("a.txt", ".txt")
Some("a")
```

```
> strip_suffix("a.txt", ".md")
None
```

