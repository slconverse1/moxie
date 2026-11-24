---
layout: default
toc: true
terms: true
title: "split · moxie function"
---

# `split`

<p class="specref"><a href="../reference.html#fn-split">The alphabetical list</a> · <a href="../spec.html#s5">Spec §5</a></p>

## Signature {#signature}

```
fn split(s String, sep String) List[String]
```

## Description {#description}

Cuts a `String` at every occurrence of a separator. Neighbouring separators give empty pieces, and a `String` that does not contain the separator comes back as a one-item list.

**Parameters**

- `s`: the text.
- `sep`: the separator.

**Returns** a `List[String]`.

## Effects {#effects}

None: this function is pure.

## Examples {#examples}

```
> split("a,b,c", ",")
List("a", "b", "c")
```

```
> split("a,,b", ",")
List("a", "", "b")
```

```
> split("abc", ",")
List("abc")
```

