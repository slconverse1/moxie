---
layout: default
toc: true
terms: true
title: "split_once · moxie function"
---

# `split_once`

<p class="specref"><a href="../reference.html#fn-split_once">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn split_once(s String, sep String) Option[(String, String)]
```

## Description {#description}

Cuts a `String` at the first occurrence of a separator only, which suits `key=value` text.

**Parameters**

- `s`: the text.
- `sep`: the separator.

**Returns** `Some((before, after))`, or `None` if the separator is not there.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> split_once("k=v=w", "=")
Some(("k", "v=w"))
```

```
> split_once("kv", "=")
None
```

